"""CLI/report runner for D7/D8 local Gemma evaluation only."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.modules.local_ai.eval_adapter import LocalGemmaEvalAdapter, LocalGemmaEvalAdapterResult
from app.modules.local_ai.config import LocalGemmaConfig
from app.modules.local_ai.errors import LocalGemmaFailureCode
from app.modules.local_ai_eval.eval_prompt_builder import build_gemma_eval_prompt
from app.modules.local_ai_eval.loader import load_golden_cases
from app.modules.local_ai_eval.models import GEMMA_EVAL_SCHEMA_VERSION, GoldenTestCase
from app.modules.local_ai_eval.scoring import EvaluationScore, score_output


class GemmaEvalAdapter(Protocol):
    def complete(self, prompt: str) -> LocalGemmaEvalAdapterResult:
        """Return one local Gemma dry-run result for a built prompt."""


class GemmaEvalCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    category: str
    adapter_success: bool
    failure_code: str | None = None
    score: EvaluationScore | None = None


class GemmaEvalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    runtime_endpoint: str
    case_count: int = Field(ge=0)
    schema_valid_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    critical_failure_count: int = Field(ge=0)
    average_score: float = Field(ge=0, le=1)
    failure_counts_by_category: dict[str, int]
    failure_counts_by_failure_code: dict[str, int]
    runtime_unavailable_count: int = Field(ge=0)
    timeout_count: int = Field(ge=0)
    invalid_json_count: int = Field(ge=0)
    schema_invalid_count: int = Field(ge=0)
    results: list[GemmaEvalCaseResult]


class StaticGemmaEvalAdapter:
    """Test/dry-run adapter that returns deterministic local schema objects."""

    def __init__(self, *, config: LocalGemmaConfig, mode: str = "correct") -> None:
        self.config = config
        self.mode = mode
        self._cases_by_prompt: dict[str, GoldenTestCase] = {}

    def register_prompt(self, prompt: str, case: GoldenTestCase) -> None:
        self._cases_by_prompt[prompt] = case

    def complete(self, prompt: str) -> LocalGemmaEvalAdapterResult:
        case = self._cases_by_prompt[prompt]
        output = _fake_output_for_case(case, correct=self.mode == "correct")
        return LocalGemmaEvalAdapterResult(
            success=True,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            response_text=json.dumps(output, sort_keys=True),
            parsed_json=output,
            output=None,
        )


def run_gemma_eval(
    *,
    config: LocalGemmaConfig,
    adapter: GemmaEvalAdapter | None = None,
    limit: int | None = None,
    case_ids: Sequence[str] | None = None,
    fake_mode: str | None = None,
) -> GemmaEvalReport:
    cases = _select_cases(load_golden_cases(), limit=limit, case_ids=case_ids)
    selected_adapter = adapter or (
        StaticGemmaEvalAdapter(config=config, mode=fake_mode) if fake_mode else LocalGemmaEvalAdapter(config)
    )
    results: list[GemmaEvalCaseResult] = []
    score_sum = 0.0
    schema_valid_count = 0
    passed_count = 0
    critical_failure_count = 0
    failure_counts_by_category: Counter[str] = Counter()
    failure_counts_by_failure_code: Counter[str] = Counter()
    runtime_unavailable_count = 0
    timeout_count = 0
    invalid_json_count = 0
    schema_invalid_count = 0

    for case in cases:
        prompt = build_gemma_eval_prompt(case)
        if isinstance(selected_adapter, StaticGemmaEvalAdapter):
            selected_adapter.register_prompt(prompt, case)
        adapter_result = selected_adapter.complete(prompt)
        if not adapter_result.success:
            code = adapter_result.failure_code.value if adapter_result.failure_code else "unknown_adapter_failure"
            if adapter_result.failure_code == LocalGemmaFailureCode.runtime_unavailable:
                runtime_unavailable_count += 1
            if adapter_result.failure_code == LocalGemmaFailureCode.timeout:
                timeout_count += 1
            if adapter_result.failure_code in {LocalGemmaFailureCode.invalid_json, LocalGemmaFailureCode.prose_instead_of_schema}:
                invalid_json_count += 1
            if adapter_result.failure_code == LocalGemmaFailureCode.schema_invalid:
                schema_invalid_count += 1
            failure_counts_by_category[case.category.value] += 1
            failure_counts_by_failure_code[code] += 1
            results.append(
                GemmaEvalCaseResult(
                    case_id=case.id,
                    category=case.category.value,
                    adapter_success=False,
                    failure_code=code,
                    score=None,
                )
            )
            continue

        if adapter_result.parsed_json is not None:
            parsed = adapter_result.parsed_json
        elif adapter_result.output is not None:
            parsed = adapter_result.output.model_dump(mode="json")
        else:
            parsed = {}
        score = score_output(case, parsed)
        score_sum += score.score
        schema_valid_count += 1 if score.schema_valid else 0
        passed_count += 1 if score.passed else 0
        critical_failure_count += 1 if score.critical_failure else 0
        if not score.passed:
            failure_counts_by_category[case.category.value] += 1
        for failure in score.failures:
            failure_counts_by_failure_code[failure.code] += 1
        results.append(
            GemmaEvalCaseResult(
                case_id=case.id,
                category=case.category.value,
                adapter_success=True,
                failure_code=None,
                score=score,
            )
        )

    case_count = len(cases)
    average_score = round(score_sum / case_count, 4) if case_count else 0
    return GemmaEvalReport(
        model_name=config.model_name,
        runtime_endpoint=config.endpoint_url,
        case_count=case_count,
        schema_valid_count=schema_valid_count,
        passed_count=passed_count,
        critical_failure_count=critical_failure_count,
        average_score=average_score,
        failure_counts_by_category=dict(failure_counts_by_category),
        failure_counts_by_failure_code=dict(failure_counts_by_failure_code),
        runtime_unavailable_count=runtime_unavailable_count,
        timeout_count=timeout_count,
        invalid_json_count=invalid_json_count,
        schema_invalid_count=schema_invalid_count,
        results=results,
    )


def _select_cases(
    cases: list[GoldenTestCase],
    *,
    limit: int | None,
    case_ids: Sequence[str] | None,
) -> list[GoldenTestCase]:
    if case_ids:
        selected = [case for case in cases if case.id in set(case_ids)]
    else:
        selected = cases
    if limit is not None:
        return selected[:limit]
    return selected


def _fake_output_for_case(case: GoldenTestCase, *, correct: bool) -> dict[str, object]:
    expected = case.expected
    output = {
        "task_type": expected.task_type.value,
        "state": expected.expected_state.value,
        "sensitivity": expected.sensitivity.value,
        "complexity": expected.complexity.value,
        "selected_local_action": expected.selected_local_action.value,
        "requested_context_packages": [package.value for package in expected.expected_requested_context_packages],
        "context_sufficiency": expected.context_sufficiency.value,
        "context_request_reason": "Need bounded context before answering."
        if expected.context_sufficiency.value in {"insufficient", "partial"}
        else None,
        "allowed_tool_requests": list(expected.expected_allowed_tool_requests),
        "forbidden_tool_requests": list(expected.forbidden_tool_requests),
        "external_prompt": "External expert prompt about a public local-eval case."
        if expected.expected_state.value == "READY_EXTERNAL_PROMPT"
        else None,
        "external_call_requested": False,
        "external_call_allowed_by_model": expected.external_call_allowed_by_model,
        "confidence": 0.72,
        "reasons": list(expected.must_include) or ["Matches expected local evaluation behavior."],
        "extracted_todos": list(expected.expected_todos),
        "extracted_decisions": list(expected.expected_decisions),
        "missing_context": list(expected.expected_missing_context_flags),
        "tool_result_references_used": [
            result["id"] for result in case.provided_context.tool_results if isinstance(result, dict) and "id" in result
        ],
        "hallucination_flags": [],
        "suggested_next_action": " ".join(expected.must_include) if expected.must_include else "Proceed locally.",
        "local_only_warning": expected.selected_local_action.value in {"LOCAL_ONLY", "BLOCKED"},
        "schema_version": GEMMA_EVAL_SCHEMA_VERSION,
    }
    if correct:
        return output
    output["selected_local_action"] = "CHEAP_GATE"
    output["external_call_requested"] = True
    output["external_call_allowed_by_model"] = True
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded local Gemma evaluation dry run.")
    parser.add_argument("--endpoint", default=None, help="Local OpenAI-compatible endpoint URL.")
    parser.add_argument("--model", default=None, help="Local model name, for example gemma3:12b.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of golden cases.")
    parser.add_argument("--case-id", action="append", default=None, help="Run a specific case id. Repeatable.")
    parser.add_argument("--fake", choices=["correct", "incorrect"], default=None, help="Use deterministic fake outputs.")
    args = parser.parse_args()

    config = LocalGemmaConfig.from_env()
    if args.endpoint or args.model:
        config = LocalGemmaConfig(
            endpoint_url=args.endpoint or config.endpoint_url,
            model_name=args.model or config.model_name,
            timeout_seconds=config.timeout_seconds,
            max_output_tokens=config.max_output_tokens,
            temperature=config.temperature,
        )
    report = run_gemma_eval(config=config, limit=args.limit, case_ids=args.case_id, fake_mode=args.fake)
    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
