import json
from datetime import UTC, datetime
from pathlib import Path

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
    CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    CLASSIFICATION_INPUT_SCHEMA_VERSION,
    CLASSIFICATION_OUTPUT_SCHEMA_VERSION,
    LOW_CONFIDENCE_THRESHOLD,
    AllowedNextStep,
    ClassificationAttemptDiagnostics,
    ClassificationBudgetPolicy,
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
from app.modules.local_ai.classification.probe_classification_budget import (
    MINIMAL_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    REPORT_SCHEMA_VERSION,
    build_minimal_classification_prompt,
    build_budget_probe_report,
    default_probe_cases,
    minimal_probe_cases,
    parse_minimal_classification_output,
    summary_lines,
    write_probe_report,
)
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


def _diagnostics(
    *,
    prompt: str = "",
    input_chars: int = 0,
    raw_content_empty: bool = False,
    thinking_present: bool | None = None,
    done_reason: str | None = None,
    schema_valid: bool = False,
    fallback_used: bool = False,
    fallback_reason: ClassificationFailureCode | None = None,
) -> ClassificationAttemptDiagnostics:
    return ClassificationAttemptDiagnostics(
        model_name=DEFAULT_CLASSIFICATION_MODEL,
        endpoint="http://localhost:11434/api/chat",
        prompt_chars=len(prompt),
        input_chars=input_chars,
        max_output_tokens=256,
        temperature=0,
        timeout_seconds=15,
        latency_ms=1,
        raw_content_empty=raw_content_empty,
        thinking_present=thinking_present,
        done_reason=done_reason,
        schema_valid=schema_valid,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )


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
        self.config = ClassificationAdapterConfig()

    def complete(self, prompt: str, *, input_chars: int = 0) -> ClassificationAdapterResult:
        self.called = True
        self.prompt = prompt
        content = json.dumps(_output_payload()) if self.content is None else self.content
        if self.failure_code:
            return ClassificationAdapterResult(
                success=False,
                model_name=DEFAULT_CLASSIFICATION_MODEL,
                runtime_endpoint="http://localhost:11434/api/chat",
                diagnostics=_diagnostics(
                    prompt=prompt,
                    input_chars=input_chars,
                    raw_content_empty=True,
                    fallback_used=True,
                    fallback_reason=self.failure_code,
                ),
                failure_code=self.failure_code,
                failure_message=self.failure_code.value,
            )
        return ClassificationAdapterResult(
            success=True,
            model_name=DEFAULT_CLASSIFICATION_MODEL,
            runtime_endpoint="http://localhost:11434/api/chat",
            diagnostics=_diagnostics(prompt=prompt, input_chars=input_chars, raw_content_empty=content.strip() == ""),
            response_text=content,
        )


class FakeProbeAdapter:
    def __init__(self, config: ClassificationAdapterConfig) -> None:
        self.config = config

    def complete(self, prompt: str, *, input_chars: int = 0) -> ClassificationAdapterResult:
        content = json.dumps(
            _output_payload(
                task_type="documentation",
                project_area="documentation",
                complexity_hint="low",
                sensitivity_hint="internal",
                allowed_next_step="request_bounded_context",
                confidence=0.9,
            )
        )
        return ClassificationAdapterResult(
            success=True,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            diagnostics=ClassificationAttemptDiagnostics(
                model_name=self.config.model_name,
                endpoint=self.config.endpoint_url,
                prompt_chars=len(prompt),
                input_chars=input_chars,
                max_output_tokens=self.config.max_output_tokens,
                temperature=self.config.temperature,
                timeout_seconds=self.config.timeout_seconds,
                latency_ms=12,
                raw_content_empty=False,
                thinking_present=False,
                done_reason="stop",
                schema_valid=False,
                fallback_used=False,
                fallback_reason=None,
            ),
            response_text=content,
        )


class FakeMinimalProbeAdapter:
    def __init__(self, config: ClassificationAdapterConfig) -> None:
        self.config = config

    def complete(self, prompt: str, *, input_chars: int = 0) -> ClassificationAdapterResult:
        content = json.dumps(
            {
                "task_type": "code",
                "project": "jarvisos",
                "sensitivity": "internal",
                "next": "answer",
                "confidence": 0.86,
            }
        )
        return ClassificationAdapterResult(
            success=True,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            diagnostics=ClassificationAttemptDiagnostics(
                model_name=self.config.model_name,
                endpoint=self.config.endpoint_url,
                prompt_chars=len(prompt),
                input_chars=input_chars,
                max_output_tokens=self.config.max_output_tokens,
                temperature=self.config.temperature,
                timeout_seconds=self.config.timeout_seconds,
                latency_ms=7,
                raw_content_empty=False,
                thinking_present=False,
                done_reason="stop",
                schema_valid=False,
                fallback_used=False,
                fallback_reason=None,
            ),
            response_text=content,
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


def test_classification_budget_policy_is_explicit_and_bounded() -> None:
    policy = ClassificationBudgetPolicy()

    assert policy.model_name == DEFAULT_CLASSIFICATION_MODEL
    assert policy.max_input_chars == 1200
    assert policy.max_prompt_chars == MAX_CLASSIFICATION_PROMPT_CHARS
    assert policy.max_output_tokens == 256
    assert policy.diagnostic_num_predict_candidates == CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES
    assert policy.diagnostic_num_predict_candidates == (128, 256, 384, 512)
    assert policy.temperature == 0
    assert policy.timeout_seconds == 15


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
    assert extra_field.value.code == ClassificationFailureCode.extra_fields


def test_parser_rejects_authority_claims_and_impossible_combinations() -> None:
    with pytest.raises(ClassificationParseError) as authority:
        parse_classification_output(
            json.dumps(_output_payload(refusal_or_uncertainty_reason="I will execute the requested tool."))
        )
    assert authority.value.code == ClassificationFailureCode.model_claimed_authority

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
        assert payload["options"]["num_predict"] == 256
        return httpx.Response(200, json={"message": {"content": json.dumps(_output_payload())}}, request=request)

    adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(handler)))
    prompt = build_classification_prompt(ClassificationInput(text="Implement JarvisOS tests."))
    result = adapter.complete(prompt, input_chars=len("Implement JarvisOS tests."))

    assert result.success is True
    assert result.response_text is not None
    assert result.diagnostics.prompt_chars == len(prompt)
    assert result.diagnostics.input_chars == len("Implement JarvisOS tests.")
    assert result.diagnostics.max_output_tokens == 256
    assert result.diagnostics.timeout_seconds == 15
    assert result.diagnostics.raw_content_empty is False
    assert result.diagnostics.schema_valid is False
    assert result.diagnostics.fallback_used is False


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
    assert result.diagnostics.raw_content_empty is True
    assert result.diagnostics.thinking_present is True
    assert result.diagnostics.done_reason == "length"
    assert result.diagnostics.fallback_reason == ClassificationFailureCode.thinking_budget_exhausted


def test_adapter_reports_done_reason_length_without_valid_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"content": ""}, "done_reason": "length"},
            request=request,
        )

    adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = adapter.complete(build_classification_prompt(ClassificationInput(text="Classify this.")))

    assert result.success is False
    assert result.failure_code == ClassificationFailureCode.done_reason_length
    assert result.diagnostics.raw_content_empty is True
    assert result.diagnostics.thinking_present is None
    assert result.diagnostics.done_reason == "length"


def test_adapter_reports_timeout_http_error_and_invalid_endpoint() -> None:
    request = ClassificationInput(text="Implement JarvisOS tests.")
    prompt = build_classification_prompt(request)

    def timeout_handler(http_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow local model", request=http_request)

    timeout_adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(timeout_handler)))
    timeout_result = timeout_adapter.complete(prompt, input_chars=len(request.text))

    assert timeout_result.success is False
    assert timeout_result.failure_code == ClassificationFailureCode.timeout
    assert timeout_result.diagnostics.fallback_reason == ClassificationFailureCode.timeout

    def http_error_handler(http_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "local failure"}, request=http_request)

    http_error_adapter = LocalGemmaClassificationAdapter(client=httpx.Client(transport=httpx.MockTransport(http_error_handler)))
    http_error_result = http_error_adapter.complete(prompt, input_chars=len(request.text))

    assert http_error_result.success is False
    assert http_error_result.failure_code == ClassificationFailureCode.http_error
    assert http_error_result.diagnostics.fallback_reason == ClassificationFailureCode.http_error

    invalid_endpoint_adapter = LocalGemmaClassificationAdapter()
    invalid_endpoint_adapter.config.endpoint_url = "https://localhost:11434/api/chat"
    invalid_endpoint_result = invalid_endpoint_adapter.complete(prompt, input_chars=len(request.text))

    assert invalid_endpoint_result.success is False
    assert invalid_endpoint_result.failure_code == ClassificationFailureCode.invalid_endpoint
    assert invalid_endpoint_result.diagnostics.fallback_reason == ClassificationFailureCode.invalid_endpoint


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
    assert result.diagnostics is not None
    assert result.diagnostics.schema_valid is True
    assert result.diagnostics.fallback_used is False
    assert result.diagnostics.fallback_reason is None
    assert result.diagnostics.raw_content_empty is False
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
    assert invalid.diagnostics is not None
    assert invalid.diagnostics.schema_valid is False
    assert invalid.diagnostics.fallback_used is True
    assert invalid.diagnostics.fallback_reason == ClassificationFailureCode.invalid_json
    assert low_confidence.source == ClassificationResultSource.fallback
    assert low_confidence.fallback_reasons == [ClassificationFailureCode.low_confidence]
    assert low_confidence.classification.allowed_next_step == AllowedNextStep.ask_clarification
    assert low_confidence.diagnostics is not None
    assert low_confidence.diagnostics.schema_valid is True
    assert low_confidence.diagnostics.fallback_reason == ClassificationFailureCode.low_confidence


def test_service_falls_back_on_empty_content_timeout_http_error_and_done_reason_length() -> None:
    empty = classify_text(
        ClassificationInput(text="Implement backend tests for JarvisOS."),
        adapter=FakeClassificationAdapter(content=""),
    )
    timeout = classify_text(
        ClassificationInput(text="Implement backend tests for JarvisOS."),
        adapter=FakeClassificationAdapter(failure_code=ClassificationFailureCode.timeout),
    )
    http_error = classify_text(
        ClassificationInput(text="Implement backend tests for JarvisOS."),
        adapter=FakeClassificationAdapter(failure_code=ClassificationFailureCode.http_error),
    )
    done_reason_length = classify_text(
        ClassificationInput(text="Implement backend tests for JarvisOS."),
        adapter=FakeClassificationAdapter(failure_code=ClassificationFailureCode.done_reason_length),
    )

    assert empty.source == ClassificationResultSource.fallback
    assert empty.fallback_reasons == [ClassificationFailureCode.empty_content]
    assert empty.diagnostics is not None
    assert empty.diagnostics.raw_content_empty is True
    assert empty.diagnostics.fallback_reason == ClassificationFailureCode.empty_content
    assert timeout.fallback_reasons == [ClassificationFailureCode.timeout]
    assert timeout.diagnostics is not None
    assert timeout.diagnostics.fallback_reason == ClassificationFailureCode.timeout
    assert http_error.fallback_reasons == [ClassificationFailureCode.http_error]
    assert http_error.diagnostics is not None
    assert http_error.diagnostics.fallback_reason == ClassificationFailureCode.http_error
    assert done_reason_length.fallback_reasons == [ClassificationFailureCode.done_reason_length]
    assert done_reason_length.diagnostics is not None
    assert done_reason_length.diagnostics.fallback_reason == ClassificationFailureCode.done_reason_length


def test_service_rejects_over_budget_prompt_without_calling_adapter() -> None:
    adapter = FakeClassificationAdapter()
    request = ClassificationInput(
        text="x" * 1200,
        source=ClassificationSource.manual_test,
        metadata={f"k{i}": "y" * 200 for i in range(10)},
    )

    result = classify_text(request, adapter=adapter)

    assert result.source == ClassificationResultSource.fallback
    assert result.fallback_reasons == [ClassificationFailureCode.over_budget_prompt]
    assert result.diagnostics is not None
    assert result.diagnostics.prompt_chars == 0
    assert result.diagnostics.input_chars == 1200
    assert result.diagnostics.fallback_reason == ClassificationFailureCode.over_budget_prompt
    assert adapter.called is False


def test_diagnostic_metadata_does_not_include_raw_prompt_text() -> None:
    marker = "SENSITIVE_MARKER_123"
    adapter = FakeClassificationAdapter()

    result = classify_text(
        ClassificationInput(text=f"Implement JarvisOS tests with {marker}.", source=ClassificationSource.codex_task),
        adapter=adapter,
    )

    assert result.diagnostics is not None
    assert marker in adapter.prompt
    diagnostics_json = result.diagnostics.model_dump_json()
    assert marker not in diagnostics_json
    assert "Implement JarvisOS tests" not in diagnostics_json


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
    assert result.diagnostics is not None
    assert result.diagnostics.schema_valid is True
    assert result.diagnostics.fallback_used is False
    assert result.diagnostics.fallback_reason == ClassificationFailureCode.deterministic_override


def test_minimal_prompt_and_parser_are_output_only_and_flat() -> None:
    request = ClassificationInput(text="Implement JarvisOS tests.", source=ClassificationSource.manual_test)
    prompt = build_minimal_classification_prompt(request)
    output = parse_minimal_classification_output(
        json.dumps(
            {
                "task_type": "code",
                "project": "jarvisos",
                "sensitivity": "internal",
                "next": "answer",
                "confidence": 0.8,
            }
        )
    )

    assert len(prompt) <= 700
    assert "Return only one JSON object" in prompt
    assert "No reasoning" in prompt
    assert "No markdown" in prompt
    assert output.task_type == "code"
    assert output.project == "jarvisos"


def test_minimal_parser_rejects_invalid_json_extra_fields_and_bad_enum() -> None:
    with pytest.raises(ClassificationParseError) as invalid_json:
        parse_minimal_classification_output("{bad")
    assert invalid_json.value.code == ClassificationFailureCode.invalid_json

    with pytest.raises(ClassificationParseError) as extra_field:
        parse_minimal_classification_output(
            json.dumps(
                {
                    "task_type": "code",
                    "project": "jarvisos",
                    "sensitivity": "internal",
                    "next": "answer",
                    "confidence": 0.8,
                    "extra": "nope",
                }
            )
        )
    assert extra_field.value.code == ClassificationFailureCode.extra_fields

    with pytest.raises(ClassificationParseError) as bad_enum:
        parse_minimal_classification_output(
            json.dumps(
                {
                    "task_type": "invented",
                    "project": "jarvisos",
                    "sensitivity": "internal",
                    "next": "answer",
                    "confidence": 0.8,
                }
            )
        )
    assert bad_enum.value.code == ClassificationFailureCode.schema_invalid


def test_probe_report_uses_fixed_variants_and_omits_raw_case_text() -> None:
    cases = default_probe_cases()
    report = build_budget_probe_report(
        adapter_factory=FakeProbeAdapter,
        created_at_utc=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
    )

    assert report.schema_version == REPORT_SCHEMA_VERSION
    assert report.num_predict_variants == CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES
    assert report.case_ids == tuple(case.case_id for case in cases)
    assert len(report.results) == len(cases) * len(CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES)
    assert {result.num_predict for result in report.results} == set(CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES)
    assert all(result.schema_valid for result in report.results)
    assert all(result.fallback_used is False for result in report.results)
    assert all(result.task_type == TaskType.documentation for result in report.results)

    serialized = report.model_dump_json()
    for case in cases:
        assert case.case_id in serialized
        assert case.request.text not in serialized
    assert "messages" not in serialized
    assert "prompt" not in serialized


def test_minimal_probe_report_uses_small_variants_and_omits_raw_case_text() -> None:
    cases = minimal_probe_cases()
    report = build_budget_probe_report(
        mode="minimal",
        adapter_factory=FakeMinimalProbeAdapter,
        created_at_utc=datetime(2026, 6, 20, 13, 0, tzinfo=UTC),
    )

    assert report.mode == "minimal"
    assert report.num_predict_variants == MINIMAL_DIAGNOSTIC_NUM_PREDICT_CANDIDATES
    assert report.num_predict_variants == (128, 256, 512)
    assert report.case_ids == tuple(case.case_id for case in cases)
    assert len(cases) == 3
    assert len(report.results) == len(cases) * len(MINIMAL_DIAGNOSTIC_NUM_PREDICT_CANDIDATES)
    assert all(result.schema_valid for result in report.results)
    assert all(result.task_type == TaskType.code_change for result in report.results)
    assert all(result.project_area == ProjectArea.jarvisos for result in report.results)
    assert all(result.allowed_next_step == AllowedNextStep.answer_locally for result in report.results)

    serialized = report.model_dump_json()
    for case in cases:
        assert case.case_id in serialized
        assert case.request.text not in serialized
    assert "messages" not in serialized
    assert "prompt" not in serialized


def test_probe_rejects_non_local_endpoint_and_noncanonical_variants() -> None:
    with pytest.raises((ClassificationAdapterConfigurationError, ValidationError)):
        build_budget_probe_report(
            endpoint_url="https://localhost:11434/api/chat",
            adapter_factory=FakeProbeAdapter,
        )

    with pytest.raises(ValueError, match="128/256/384/512"):
        build_budget_probe_report(
            num_predict_variants=(256,),
            adapter_factory=FakeProbeAdapter,
        )

    with pytest.raises(ValueError, match="128/256/512"):
        build_budget_probe_report(
            mode="minimal",
            num_predict_variants=(256,),
            adapter_factory=FakeMinimalProbeAdapter,
        )


def test_probe_writes_timestamped_report_and_summary_without_live_call(tmp_path: Path) -> None:
    report = build_budget_probe_report(
        cases=(default_probe_cases()[0],),
        adapter_factory=FakeProbeAdapter,
        created_at_utc=datetime(2026, 6, 20, 12, 30, tzinfo=UTC),
    )

    path = write_probe_report(report, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = summary_lines(report, path)

    assert path.parent == tmp_path
    assert path.name == "classification_budget_probe_20260620T123000.json"
    assert payload["schema_version"] == REPORT_SCHEMA_VERSION
    assert payload["case_ids"] == ["jarvisos_code_task"]
    assert "results=4" in lines[1]
    assert "schema_valid=4" in lines[2]


def test_minimal_probe_writes_mode_specific_report_name(tmp_path: Path) -> None:
    report = build_budget_probe_report(
        mode="minimal",
        cases=(minimal_probe_cases()[0],),
        adapter_factory=FakeMinimalProbeAdapter,
        created_at_utc=datetime(2026, 6, 20, 13, 30, tzinfo=UTC),
    )

    path = write_probe_report(report, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = summary_lines(report, path)

    assert path.name == "classification_budget_probe_minimal_20260620T133000.json"
    assert payload["mode"] == "minimal"
    assert payload["case_ids"] == ["jarvisos_code_task"]
    assert "mode=minimal" in lines[1]
    assert "results=3" in lines[1]


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
