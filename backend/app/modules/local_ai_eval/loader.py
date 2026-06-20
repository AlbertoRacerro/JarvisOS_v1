from collections import Counter

from app.modules.local_ai_eval.fixtures import GOLDEN_CASES
from app.modules.local_ai_eval.models import ContextSufficiency, EvalState, GoldenCategory, GoldenTestCase, Severity


def load_golden_cases() -> list[GoldenTestCase]:
    """Load and validate the static D7 golden set."""

    return [GoldenTestCase.model_validate(item) for item in GOLDEN_CASES]


def category_counts(cases: list[GoldenTestCase] | None = None) -> dict[str, int]:
    selected_cases = cases if cases is not None else load_golden_cases()
    counts = Counter(case.category.value for case in selected_cases)
    return {category.value: counts.get(category.value, 0) for category in GoldenCategory}


def validate_golden_set(cases: list[GoldenTestCase] | None = None) -> None:
    selected_cases = cases if cases is not None else load_golden_cases()
    ids = [case.id for case in selected_cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Golden case ids must be unique.")
    missing_categories = [category for category, count in category_counts(selected_cases).items() if count == 0]
    if missing_categories:
        raise ValueError(f"Golden set is missing categories: {', '.join(missing_categories)}")
    for case in selected_cases:
        if _is_critical_safety_case(case) and case.severity not in {Severity.high, Severity.critical}:
            raise ValueError(f"Critical safety case must be high/critical severity: {case.id}")
        if case.expected.context_sufficiency in {ContextSufficiency.insufficient, ContextSufficiency.partial}:
            if case.expected.expected_state == EvalState.READY_LOCAL_RESPONSE:
                raise ValueError(f"Insufficient/partial context case cannot expect final response: {case.id}")
        if case.expected.expected_requested_context_packages and case.expected.context_sufficiency == ContextSufficiency.not_applicable:
            raise ValueError(f"Context package expectations require context_sufficiency: {case.id}")
        if case.expected.external_call_requested:
            raise ValueError(f"D7/D7B golden cases must not expect executable external calls: {case.id}")
        if case.expected.external_call_allowed_by_model and case.expected.expected_state != EvalState.READY_EXTERNAL_PROMPT:
            raise ValueError(f"External prompt allowance requires READY_EXTERNAL_PROMPT state: {case.id}")


def _is_critical_safety_case(case: GoldenTestCase) -> bool:
    if case.expected.sensitivity.value in {"secret", "sensitive_ip"}:
        return True
    if case.expected.selected_local_action.value == "BLOCKED":
        return True
    if case.expected.forbidden_tool_requests:
        return True
    return case.expected.expected_state.value == "BLOCKED"
