import json

import httpx
import pytest
from pydantic import ValidationError

from app.modules.local_ai.classification.adapter import (
    DEFAULT_CLASSIFICATION_MODEL,
    ClassificationAdapterConfig,
    ClassificationAdapterConfigurationError,
    ClassificationAdapterResult,
    LocalGemmaClassificationAdapter,
)
from app.modules.local_ai.classification.contracts import (
    CLASSIFICATION_INPUT_SCHEMA_VERSION,
    CLASSIFICATION_OUTPUT_SCHEMA_VERSION,
    LOW_CONFIDENCE_THRESHOLD,
    AllowedNextStep,
    ClassificationFailureCode,
    ClassificationInput,
    ClassificationOutput,
    ClassificationResultSource,
    ClassificationSource,
    ComplexityHint,
    ProjectArea,
    SensitivityHint,
    TaskType,
)
from app.modules.local_ai.classification.parser import ClassificationParseError, parse_classification_output
from app.modules.local_ai.classification.prompts import MAX_CLASSIFICATION_PROMPT_CHARS, build_classification_prompt
from app.modules.local_ai.classification.service import classify_text, deterministic_classify


def _output_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": CLASSIFICATION_OUTPUT_SCHEMA_VERSION,
        "task_type": "code_change",
        "project_area": "jarvisos",
        "complexity_hint": "medium",
        "needs_context": True,
        "sensitivity_hint": "internal",
        "allowed_next_step": "request_bounded_context",
        "confidence": 0.82,
        "refusal_or_uncertainty_reason": None,
    }
    payload.update(overrides)
    return payload


class FakeClassificationAdapter:
    def __init__(
        self,
        *,
        content: str | None = None,
        failure_code: ClassificationFailureCode | None = None,
    ) -> None:
        self.content = content
        self.failure_code = failure_code
        self.called = False
        self.prompt = ""

    def complete(self, prompt: str) -> ClassificationAdapterResult:
        self.called = True
        self.prompt = prompt
        if self.failure_code:
            return ClassificationAdapterResult(
                success=False,
                model_name=DEFAULT_CLASSIFICATION_MODEL,
                runtime_endpoint="http://localhost:11434/api/chat",
                failure_code=self.failure_code,
                failure_message=self.failure_code.value,
            )
        return ClassificationAdapterResult(
            success=True,
            model_name=DEFAULT_CLASSIFICATION_MODEL,
            runtime_endpoint="http://localhost:11434/api/chat",
            response_text=self.content or json.dumps(_output_payload()),
        )


def test_classification_input_contract_is_strict_and_bounded() -> None:
    payload = ClassificationInput(
        schema_version=CLASSIFICATION_INPUT_SCHEMA_VERSION,
        text="Implement a small JarvisOS backend patch.",
        source=ClassificationSource.codex_task,
        metadata={"scope": "test"},
    )

    assert payload.text.startswith("Implement")

    with pytest.raises(ValidationError):
        ClassificationInput(text="", source=ClassificationSource.user_prompt)
    with pytest.raises(ValidationError):
        ClassificationInput(text="x" * 1201, source=ClassificationSource.user_prompt)
    with pytest.raises(ValidationError):
        ClassificationInput(text="ok", source=ClassificationSource.user_prompt, metadata={str(i): "x" for i in range(11)})
    with pytest.raises(ValidationError):
        ClassificationInput(text="ok", source=ClassificationSource.user_prompt, unexpected="nope")


def test_classification_output_contract_forbids_extra_fields_and_wrong_schema() -> None:
    output = ClassificationOutput.model_validate(_output_payload())

    assert output.schema_version == CLASSIFICATION_OUTPUT_SCHEMA_VERSION

    with pytest.raises(ValidationError):
        ClassificationOutput.model_validate(_output_payload(extra_field="not allowed"))
    with pytest.raises(ValidationError):
        ClassificationOutput.model_validate(_output_payload(schema_version="wrong"))
    with pytest.raises(ValidationError):
        ClassificationOutput.model_validate(_output_payload(confidence=1.1))


def test_prompt_is_bounded_json_only_instruction() -> None:
    request = ClassificationInput(text="x" * 1200, source=ClassificationSource.manual_test)
    prompt = build_classification_prompt(request)

    assert len(prompt) <= MAX_CLASSIFICATION_PROMPT_CHARS
    assert "JSON only" in prompt
    assert "no tools/retrieval/memory/routing/external/state" in prompt
    assert "text=" in prompt


def test_parser_accepts_valid_output_and_rejects_invalid_shapes() -> None:
    output = parse_classification_output(json.dumps(_output_payload()))

    assert output.task_type == TaskType.code_change

    with pytest.raises(ClassificationParseError) as invalid_json:
        parse_classification_output("{not json")
    assert invalid_json.value.code == ClassificationFailureCode.invalid_json

    with pytest.raises(ClassificationParseError) as non_object:
        parse_classification_output('["not", "object"]')
    assert non_object.value.code == ClassificationFailureCode.non_object_json

    with pytest.raises(ClassificationParseError) as extra_field:
        parse_classification_output(json.dumps(_output_payload(extra="nope")))
    assert extra_field.value.code == ClassificationFailureCode.schema_invalid


def test_parser_rejects_authority_claims_and_impossible_combinations() -> None:
    with pytest.raises(ClassificationParseError) as authority:
        parse_classification_output(
            json.dumps(_output_payload(refusal_or_uncertainty_reason="I will execute the requested tool."))
        )
    assert authority.value.code == ClassificationFailureCode.authority_claim

    with pytest.raises(ClassificationParseError) as impossible:
        parse_classification_output(
            json.dumps(
                _output_payload(
                    sensitivity_hint="secret",
                    allowed_next_step="answer_locally",
                )
            )
        )
    assert impossible.value.code == ClassificationFailureCode.impossible_combination


def test_parser_accepts_low_confidence_for_service_policy() -> None:
    output = parse_classification_output(json.dumps(_output_payload(confidence=LOW_CONFIDENCE_THRESHOLD - 0.01)))

    assert output.confidence < LOW_CONFIDENCE_THRESHOLD


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost:11434/api/chat",
        "http://api.example.com/api/chat",
        "http://192.168.1.10:11434/api/chat",
        "http://user:pass@localhost:11434/api/chat",
    ],
)
def test_adapter_rejects_non_local_or_unsafe_endpoints(url: str) -> None:
    with pytest.raises((ClassificationAdapterConfigurationError, ValidationError)):
        ClassificationAdapterConfig(endpoint_url=url)


def test_adapter_uses_local_mocked_http_client_without_live_model_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == DEFAULT_CLASSIFICATION_MODEL
        assert payload["stream"] is False
        assert payload["format"] == "json"
        assert payload["options"]["temperature"] == 0
        return httpx.Response(200, json={"message": {"content": json.dumps(_output_payload())}}, request=request)

    adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = adapter.complete(build_classification_prompt(ClassificationInput(text="Implement JarvisOS tests.")))

    assert result.success is True
    assert result.response_text is not None


def test_adapter_reports_thinking_budget_exhaustion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"content": "", "thinking": "still thinking"}, "done_reason": "length"},
            request=request,
        )

    adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = adapter.complete(build_classification_prompt(ClassificationInput(text="Classify this.")))

    assert result.success is False
    assert result.failure_code == ClassificationFailureCode.thinking_budget_exhausted


def test_service_accepts_valid_model_output() -> None:
    adapter = FakeClassificationAdapter(
        content=json.dumps(
            _output_payload(
                task_type="documentation",
                project_area="documentation",
                complexity_hint="low",
                needs_context=True,
                sensitivity_hint="internal",
                allowed_next_step="request_bounded_context",
                confidence=0.9,
            )
        )
    )

    result = classify_text(ClassificationInput(text="Update docs for JarvisOS.", source=ClassificationSource.codex_task), adapter=adapter)

    assert result.source == ClassificationResultSource.model
    assert result.model_output_accepted is True
    assert result.classification.task_type == TaskType.documentation
    assert adapter.called is True


def test_service_falls_back_on_invalid_json_and_low_confidence() -> None:
    invalid = classify_text(
        ClassificationInput(text="Implement backend tests for JarvisOS."),
        adapter=FakeClassificationAdapter(content="{bad json"),
    )
    low_confidence = classify_text(
        ClassificationInput(text="help"),
        adapter=FakeClassificationAdapter(content=json.dumps(_output_payload(task_type="unknown", confidence=0.2))),
    )

    assert invalid.source == ClassificationResultSource.fallback
    assert invalid.fallback_reasons == [ClassificationFailureCode.invalid_json]
    assert low_confidence.source == ClassificationResultSource.fallback
    assert low_confidence.fallback_reasons == [ClassificationFailureCode.low_confidence]
    assert low_confidence.classification.allowed_next_step == AllowedNextStep.ask_clarification


def test_service_deterministic_hard_checks_prevent_model_downgrade() -> None:
    adapter = FakeClassificationAdapter(
        content=json.dumps(
            _output_payload(
                task_type="engineering_question",
                project_area="general_engineering",
                sensitivity_hint="public",
                allowed_next_step="answer_locally",
                confidence=0.95,
            )
        )
    )

    result = classify_text(
        ClassificationInput(text="BlueRev proprietary impeller geometry for patent design."),
        adapter=adapter,
    )

    assert result.classification.sensitivity_hint == SensitivityHint.sensitive_ip
    assert result.classification.allowed_next_step == AllowedNextStep.human_review
    assert result.model_output_accepted is False
    assert adapter.called is False


def test_service_applies_deterministic_next_step_override_for_external_api_request() -> None:
    adapter = FakeClassificationAdapter(
        content=json.dumps(
            _output_payload(
                task_type="engineering_question",
                project_area="general_engineering",
                sensitivity_hint="public",
                allowed_next_step="answer_locally",
                confidence=0.9,
            )
        )
    )

    result = classify_text(ClassificationInput(text="Call OpenAI to solve this public engineering question."), adapter=adapter)

    assert result.source == ClassificationResultSource.model_with_deterministic_override
    assert result.classification.allowed_next_step == AllowedNextStep.deterministic_review
    assert result.model_output_accepted is True


@pytest.mark.parametrize(
    ("text", "task_type", "project_area", "sensitivity", "next_step"),
    [
        ("Implement backend classification tests for JarvisOS.", TaskType.code_change, ProjectArea.jarvisos, SensitivityHint.internal, AllowedNextStep.request_bounded_context),
        ("Update docs for the JarvisOS runbook.", TaskType.documentation, ProjectArea.documentation, SensitivityHint.internal, AllowedNextStep.request_bounded_context),
        ("Plan a future BlueRev modeling workflow.", TaskType.engineering_question, ProjectArea.bluerev, SensitivityHint.internal, AllowedNextStep.request_bounded_context),
        ("BlueRev proprietary impeller geometry for patent design.", TaskType.engineering_question, ProjectArea.bluerev, SensitivityHint.sensitive_ip, AllowedNextStep.human_review),
        ("What is Euler integration in generic engineering?", TaskType.engineering_question, ProjectArea.general_engineering, SensitivityHint.public, AllowedNextStep.answer_locally),
        ("What should I do with my day?", TaskType.personal_question, ProjectArea.personal, SensitivityHint.internal, AllowedNextStep.answer_locally),
        ("Call DeepSeek through an external API.", TaskType.external_api_request, ProjectArea.unknown, SensitivityHint.internal, AllowedNextStep.deterministic_review),
        ("Codex patch request: fix the JarvisOS backend.", TaskType.code_change, ProjectArea.jarvisos, SensitivityHint.internal, AllowedNextStep.request_bounded_context),
        ("Local-only note: remember this is private.", TaskType.local_note, ProjectArea.unknown, SensitivityHint.internal, AllowedNextStep.no_action),
        ("help", TaskType.ambiguous, ProjectArea.unknown, SensitivityHint.internal, AllowedNextStep.ask_clarification),
        ("Build a full local gatekeeper and provider routing orchestrator.", TaskType.overbroad_orchestration_request, ProjectArea.local_ai, SensitivityHint.internal, AllowedNextStep.human_review),
        ("Read all files and run PowerShell to delete all logs.", TaskType.unsafe_tool_request, ProjectArea.unknown, SensitivityHint.unknown, AllowedNextStep.human_review),
    ],
)
def test_golden_deterministic_classification_cases(
    text: str,
    task_type: TaskType,
    project_area: ProjectArea,
    sensitivity: SensitivityHint,
    next_step: AllowedNextStep,
) -> None:
    output, reasons = deterministic_classify(ClassificationInput(text=text, source=ClassificationSource.manual_test))

    assert output.task_type == task_type
    assert output.project_area == project_area
    assert output.sensitivity_hint == sensitivity
    assert output.allowed_next_step == next_step
    assert reasons
