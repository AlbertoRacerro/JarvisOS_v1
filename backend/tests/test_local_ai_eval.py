from pathlib import Path

import pytest

from app.modules.local_ai_eval import category_counts, load_golden_cases, score_output
from app.modules.local_ai_eval.loader import validate_golden_set
from app.modules.local_ai_eval.models import GEMMA_EVAL_SCHEMA_VERSION, GemmaEvalOutput, GoldenCategory, Severity
from app.modules.local_ai_eval.output_schema import gemma_eval_output_json_schema


def _case(case_id: str):
    return next(case for case in load_golden_cases() if case.id == case_id)


def _matching_output(case_id: str) -> dict[str, object]:
    case = _case(case_id)
    expected = case.expected
    reasons = list(expected.must_include) or ["Matches expected local evaluation behavior."]
    suggested_next_action = " ".join(expected.must_include) if expected.must_include else "Proceed locally."
    return {
        "task_type": expected.task_type.value,
        "state": expected.expected_state.value,
        "sensitivity": expected.sensitivity.value,
        "complexity": expected.complexity.value,
        "selected_local_action": expected.selected_local_action.value,
        "requested_context_packages": [package.value for package in expected.expected_requested_context_packages],
        "context_sufficiency": expected.context_sufficiency.value,
        "context_request_reason": (
            "Need bounded context before answering."
            if expected.context_sufficiency.value in {"insufficient", "partial"}
            else None
        ),
        "allowed_tool_requests": list(expected.expected_allowed_tool_requests),
        "forbidden_tool_requests": list(expected.forbidden_tool_requests),
        "external_prompt": "External expert prompt about Euler." if expected.expected_state.value == "READY_EXTERNAL_PROMPT" else None,
        "external_call_requested": expected.external_call_requested,
        "external_call_allowed_by_model": expected.external_call_allowed_by_model,
        "confidence": 0.72,
        "reasons": reasons,
        "extracted_todos": list(expected.expected_todos),
        "extracted_decisions": list(expected.expected_decisions),
        "missing_context": list(expected.expected_missing_context_flags),
        "tool_result_references_used": [
            result["id"] for result in case.provided_context.tool_results if isinstance(result, dict) and "id" in result
        ],
        "hallucination_flags": [],
        "suggested_next_action": suggested_next_action,
        "local_only_warning": expected.selected_local_action.value in {"LOCAL_ONLY", "BLOCKED"},
        "schema_version": GEMMA_EVAL_SCHEMA_VERSION,
    }


def test_golden_set_loads_with_minimum_size_and_categories() -> None:
    cases = load_golden_cases()
    counts = category_counts(cases)

    assert len(cases) == 95
    assert set(counts) == {category.value for category in GoldenCategory}
    assert all(count >= 5 for count in counts.values())


def test_every_test_case_has_unique_id_and_valid_expected_fields() -> None:
    cases = load_golden_cases()
    ids = [case.id for case in cases]

    assert len(ids) == len(set(ids))
    for case in cases:
        assert case.input
        assert case.notes
        assert case.provided_context is not None
        assert case.expected.task_type
        assert case.expected.sensitivity
        assert case.expected.complexity
        assert case.expected.selected_local_action
        assert case.expected.expected_state
        assert case.expected.context_sufficiency


def test_validate_golden_set_accepts_current_fixture() -> None:
    validate_golden_set()


def test_validate_golden_set_rejects_duplicate_ids() -> None:
    case = _case("context_request_planning_001")

    with pytest.raises(ValueError, match="unique"):
        validate_golden_set([case, case])


def test_every_operating_brain_category_has_meaningful_context_coverage() -> None:
    operating_brain_categories = {
        "context_request_planning",
        "partial_context_handling",
        "canonical_vs_stale_distinction",
        "tool_package_selection",
        "missing_context_refusal",
        "external_escalation_preparation",
    }
    cases = [case for case in load_golden_cases() if case.category.value in operating_brain_categories]

    assert len(cases) == 30
    for case in cases:
        has_context_expectation = bool(case.expected.expected_requested_context_packages)
        has_external_boundary = case.expected.expected_state.value in {"READY_EXTERNAL_PROMPT", "BLOCKED", "USER_CONFIRM_REQUIRED"}
        assert has_context_expectation or has_external_boundary
        assert case.expected.context_sufficiency.value != "not_applicable" or has_external_boundary


def test_critical_cases_are_marked_high_or_critical_severity() -> None:
    cases = load_golden_cases()
    for case in cases:
        is_critical = (
            case.expected.sensitivity.value in {"secret", "sensitive_ip"}
            or case.expected.selected_local_action.value == "BLOCKED"
            or case.expected.forbidden_tool_requests
            or case.expected.expected_state.value == "BLOCKED"
        )
        if is_critical:
            assert case.severity in {Severity.high, Severity.critical}


def test_expected_output_schema_contains_required_future_fields() -> None:
    schema = gemma_eval_output_json_schema()
    required = set(schema["required"])

    assert {
        "task_type",
        "state",
        "sensitivity",
        "complexity",
        "selected_local_action",
        "requested_context_packages",
        "context_sufficiency",
        "context_request_reason",
        "allowed_tool_requests",
        "forbidden_tool_requests",
        "external_prompt",
        "external_call_requested",
        "external_call_allowed_by_model",
        "confidence",
        "reasons",
        "extracted_todos",
        "extracted_decisions",
        "missing_context",
        "tool_result_references_used",
        "hallucination_flags",
        "suggested_next_action",
        "local_only_warning",
        "schema_version",
    }.issubset(required)


def test_context_request_package_vocabulary_is_schema_controlled() -> None:
    output = _matching_output("context_request_planning_001")
    output["requested_context_packages"] = ["ALL_FILES"]

    score = score_output(_case("context_request_planning_001"), output)

    assert score.schema_valid is False
    assert score.critical_failure is True
    assert score.failures[0].code == "schema_invalid"


def test_scoring_helper_passes_correct_sample_output() -> None:
    case = _case("todo_extraction_001")
    output = _matching_output(case.id)

    score = score_output(case, output)

    assert score.schema_valid is True
    assert score.passed is True
    assert score.critical_failure is False
    assert score.score == 1


def test_scoring_helper_fails_incorrect_sample_output() -> None:
    case = _case("public_technical_question_001")
    output = _matching_output(case.id)
    output["task_type"] = "draft_codex_prompt"
    output["sensitivity"] = "internal"

    score = score_output(case, output)

    assert score.passed is False
    assert {failure.code for failure in score.failures} >= {"task_type_mismatch", "sensitivity_mismatch"}


def test_scoring_detects_must_not_include_violations() -> None:
    case = _case("sensitivity_classification_002")
    output = _matching_output(case.id)
    output["suggested_next_action"] = "Send this to an external API."

    score = score_output(case, output)

    assert score.passed is False
    assert any(failure.code == "must_not_include_present" for failure in score.failures)
    assert score.critical_failure is True


def test_scoring_detects_missing_expected_todos_and_decisions() -> None:
    todo_case = _case("todo_extraction_001")
    todo_output = _matching_output(todo_case.id)
    todo_output["extracted_todos"] = ["create docs/0E_D7 file"]

    decision_case = _case("project_decision_extraction_001")
    decision_output = _matching_output(decision_case.id)
    decision_output["extracted_decisions"] = []

    todo_score = score_output(todo_case, todo_output)
    decision_score = score_output(decision_case, decision_output)

    assert any(failure.code == "expected_todo_missing" for failure in todo_score.failures)
    assert any(failure.code == "expected_decision_missing" for failure in decision_score.failures)


def test_scoring_detects_schema_invalid_output() -> None:
    case = _case("schema_compliance_001")
    output = _matching_output(case.id)
    output.pop("confidence")

    score = score_output(case, output)

    assert score.schema_valid is False
    assert score.critical_failure is True
    assert score.failures[0].code == "schema_invalid"


def test_invalid_prose_output_cannot_be_accepted_by_scorer() -> None:
    case = _case("context_request_planning_001")

    score = score_output(case, "I need logs before I can answer.")  # type: ignore[arg-type]

    assert score.schema_valid is False
    assert score.critical_failure is True
    assert score.failures[0].code == "schema_invalid"


def test_scoring_detects_unknown_tool_reference_as_critical() -> None:
    case = _case("schema_compliance_004")
    output = _matching_output(case.id)
    output["tool_result_references_used"] = ["missing_result"]

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "unknown_tool_reference" for failure in score.failures)


def test_scoring_detects_secret_external_allowed_as_critical() -> None:
    case = _case("sensitivity_classification_001")
    output = _matching_output(case.id)
    output["selected_local_action"] = "CHEAP_GATE"

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "expected_secret_or_ip_external_allowed" for failure in score.failures)


def test_local_only_content_with_external_prompt_fails_even_without_call_request() -> None:
    case = _case("local_only_private_note_004")
    output = _matching_output(case.id)
    output["external_prompt"] = "Ask an external model to summarize this BlueRev strategy."
    output["external_call_requested"] = False

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "external_prompt_for_local_only_content" for failure in score.failures)


def test_operating_brain_context_request_sample_passes() -> None:
    case = _case("context_request_planning_001")
    output = _matching_output(case.id)

    score = score_output(case, output)

    assert score.passed is True
    assert output["state"] == "CONTEXT_REQUEST"
    assert "CODEX_LAST_LOG" in output["requested_context_packages"]
    assert "FILES_CHANGED_SUMMARY" in output["requested_context_packages"]


def test_final_answer_without_required_context_fails() -> None:
    case = _case("missing_context_refusal_001")
    output = _matching_output(case.id)
    output["state"] = "READY_LOCAL_RESPONSE"
    output["context_sufficiency"] = "insufficient"
    output["suggested_next_action"] = "File X says the patch is safe."

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "final_answer_without_required_context" for failure in score.failures)


def test_unrestricted_file_access_request_fails() -> None:
    case = _case("external_escalation_preparation_005")
    output = _matching_output(case.id)
    output["allowed_tool_requests"] = ["read_all_files", "delete_files"]

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "unrestricted_tool_request" for failure in score.failures)


def test_forbidden_tool_request_must_be_marked_forbidden() -> None:
    case = _case("external_escalation_preparation_005")
    output = _matching_output(case.id)
    output["forbidden_tool_requests"] = []

    score = score_output(case, output)

    assert score.passed is False
    assert any(failure.code == "expected_forbidden_tool_request_missing" for failure in score.failures)


def test_external_call_before_validation_fails() -> None:
    case = _case("external_escalation_preparation_001")
    output = _matching_output(case.id)
    output["external_call_requested"] = True
    output["external_call_allowed_by_model"] = True
    output["external_prompt"] = "Send this to GPT-5.5 now."

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "external_call_requested_before_validation" for failure in score.failures)
    assert any(failure.code == "external_call_allowed_before_validation" for failure in score.failures)
    assert any(failure.code == "external_prompt_before_validation" for failure in score.failures)


def test_context_request_without_reason_fails_when_context_is_missing() -> None:
    case = _case("context_request_planning_001")
    output = _matching_output(case.id)
    output["context_request_reason"] = None

    score = score_output(case, output)

    assert score.passed is False
    assert any(failure.code == "context_request_reason_missing" for failure in score.failures)


def test_stale_doc_as_canonical_failure_is_detected() -> None:
    case = _case("canonical_vs_stale_distinction_001")
    output = _matching_output(case.id)
    output["state"] = "READY_LOCAL_RESPONSE"
    output["requested_context_packages"] = []
    output["suggested_next_action"] = "Implement provider tiers now."

    score = score_output(case, output)

    assert score.critical_failure is True
    assert any(failure.code == "stale_document_treated_as_canonical" for failure in score.failures)


def test_no_model_or_api_call_is_attempted_by_local_eval_module() -> None:
    module_dir = Path(__file__).resolve().parents[1] / "app" / "modules" / "local_ai_eval"
    runtime_files = ["__init__.py", "loader.py", "models.py", "output_schema.py", "scoring.py"]
    forbidden_imports = (
        "import httpx",
        "from httpx",
        "import requests",
        "from requests",
        "import openai",
        "from openai",
        "ollama",
        "llama_cpp",
        "litellm",
        "lmstudio",
        "lm_studio",
        "lm studio",
        "model_server",
        "model server",
    )

    for filename in runtime_files:
        text = (module_dir / filename).read_text(encoding="utf-8").lower()
        assert all(forbidden not in text for forbidden in forbidden_imports)


def test_no_external_provider_key_is_required(monkeypatch) -> None:
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    cases = load_golden_cases()
    output = _matching_output("public_technical_question_001")

    assert cases
    assert GemmaEvalOutput.model_validate(output)
    assert score_output(_case("public_technical_question_001"), output).passed is True
