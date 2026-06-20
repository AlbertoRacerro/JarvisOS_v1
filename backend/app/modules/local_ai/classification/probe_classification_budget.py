"""Manual CLI-only local classification budget probe.

This module is intentionally not imported by routes or startup code. It calls
only a configured localhost classification endpoint when run manually.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.modules.local_ai.classification.adapter import ClassificationAdapterConfig, LocalGemmaClassificationAdapter
from app.modules.local_ai.classification.contracts import (
    CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    DEFAULT_CLASSIFICATION_ENDPOINT_URL,
    DEFAULT_CLASSIFICATION_MODEL_NAME,
    DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS,
    DEFAULT_CLASSIFICATION_TEMPERATURE,
    AllowedNextStep,
    ClassificationFailureCode,
    ClassificationInput,
    ClassificationServiceResult,
    ClassificationSource,
    ProjectArea,
    SensitivityHint,
    TaskType,
)
from app.modules.local_ai.classification.service import classify_text


REPORT_SCHEMA_VERSION = "classification_budget_probe_report_v1"
REPORT_FILENAME_PREFIX = "classification_budget_probe"


class ClassificationProbeCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    request: ClassificationInput


class ClassificationProbeCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    num_predict: int = Field(ge=1, le=512)
    model_name: str
    endpoint: str
    latency_ms: int | None = Field(default=None, ge=0)
    done_reason: str | None = None
    raw_content_empty: bool
    thinking_present: bool | None = None
    schema_valid: bool
    fallback_used: bool
    fallback_reason: ClassificationFailureCode | None = None
    task_type: TaskType | None = None
    project_area: ProjectArea | None = None
    sensitivity_hint: SensitivityHint | None = None
    allowed_next_step: AllowedNextStep | None = None


class ClassificationBudgetProbeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = REPORT_SCHEMA_VERSION
    created_at_utc: str
    model_name: str
    endpoint: str
    temperature: float = Field(ge=0, le=0)
    timeout_seconds: float = Field(ge=0.1, le=300)
    num_predict_variants: tuple[int, ...]
    case_ids: tuple[str, ...]
    results: list[ClassificationProbeCaseResult]


AdapterFactory = Callable[[ClassificationAdapterConfig], LocalGemmaClassificationAdapter]


def default_probe_cases() -> tuple[ClassificationProbeCase, ...]:
    return (
        _case(
            "jarvisos_code_task",
            "Implement a small JarvisOS backend classification test.",
        ),
        _case(
            "jarvisos_docs_task",
            "Update JarvisOS documentation for the local classification utility.",
        ),
        _case(
            "bluerev_sensitive_request",
            "Review a BlueRev internal planning request and decide whether it needs human review.",
        ),
        _case(
            "generic_engineering_qa",
            "What is Euler integration in generic engineering?",
        ),
        _case(
            "ambiguous_request",
            "help",
        ),
        _case(
            "unsafe_tool_execution_request",
            "A user asks whether an automatic shell command should be treated as unsafe tool execution.",
        ),
    )


def build_budget_probe_report(
    *,
    endpoint_url: str = DEFAULT_CLASSIFICATION_ENDPOINT_URL,
    model_name: str = DEFAULT_CLASSIFICATION_MODEL_NAME,
    timeout_seconds: float = DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS,
    num_predict_variants: Iterable[int] = CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    cases: Iterable[ClassificationProbeCase] | None = None,
    adapter_factory: AdapterFactory = LocalGemmaClassificationAdapter,
    created_at_utc: datetime | None = None,
) -> ClassificationBudgetProbeReport:
    variants = tuple(num_predict_variants)
    if variants != CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES:
        raise ValueError("classification budget probe must use variants 128/256/384/512")
    probe_cases = tuple(cases or default_probe_cases())
    results: list[ClassificationProbeCaseResult] = []
    for num_predict in variants:
        config = ClassificationAdapterConfig(
            endpoint_url=endpoint_url,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
            max_output_tokens=num_predict,
            temperature=DEFAULT_CLASSIFICATION_TEMPERATURE,
        )
        adapter = adapter_factory(config)
        for case in probe_cases:
            result = classify_text(case.request, adapter=adapter)
            results.append(_case_result(case_id=case.case_id, num_predict=num_predict, result=result))
    created_at = created_at_utc or datetime.now(UTC)
    return ClassificationBudgetProbeReport(
        created_at_utc=created_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        model_name=model_name,
        endpoint=ClassificationAdapterConfig(endpoint_url=endpoint_url).endpoint_url,
        temperature=DEFAULT_CLASSIFICATION_TEMPERATURE,
        timeout_seconds=timeout_seconds,
        num_predict_variants=variants,
        case_ids=tuple(case.case_id for case in probe_cases),
        results=results,
    )


def write_probe_report(report: ClassificationBudgetProbeReport, report_dir: Path | None = None) -> Path:
    target_dir = report_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = report.created_at_utc.replace(":", "").replace("-", "").replace("Z", "")
    path = target_dir / f"{REPORT_FILENAME_PREFIX}_{timestamp}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def summary_lines(report: ClassificationBudgetProbeReport, report_path: Path) -> list[str]:
    schema_valid_count = sum(1 for item in report.results if item.schema_valid)
    fallback_count = sum(1 for item in report.results if item.fallback_used)
    empty_count = sum(1 for item in report.results if item.raw_content_empty)
    return [
        f"report={report_path}",
        f"cases={len(report.case_ids)} variants={len(report.num_predict_variants)} results={len(report.results)}",
        f"schema_valid={schema_valid_count} fallback_used={fallback_count} raw_content_empty={empty_count}",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the manual local classification budget probe.")
    parser.add_argument("--endpoint", default=DEFAULT_CLASSIFICATION_ENDPOINT_URL)
    parser.add_argument("--model", default=DEFAULT_CLASSIFICATION_MODEL_NAME)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS)
    parser.add_argument("--report-dir", type=Path, default=default_report_dir())
    args = parser.parse_args(argv)

    report = build_budget_probe_report(
        endpoint_url=args.endpoint,
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    report_path = write_probe_report(report, args.report_dir)
    for line in summary_lines(report, report_path):
        print(line)
    return 0


def _case(case_id: str, text: str) -> ClassificationProbeCase:
    return ClassificationProbeCase(
        case_id=case_id,
        request=ClassificationInput(text=text, source=ClassificationSource.manual_test, metadata={"case_id": case_id}),
    )


def _case_result(
    *,
    case_id: str,
    num_predict: int,
    result: ClassificationServiceResult,
) -> ClassificationProbeCaseResult:
    diagnostics = result.diagnostics
    schema_valid = diagnostics.schema_valid if diagnostics else False
    return ClassificationProbeCaseResult(
        case_id=case_id,
        num_predict=num_predict,
        model_name=diagnostics.model_name if diagnostics else DEFAULT_CLASSIFICATION_MODEL_NAME,
        endpoint=diagnostics.endpoint if diagnostics else DEFAULT_CLASSIFICATION_ENDPOINT_URL,
        latency_ms=diagnostics.latency_ms if diagnostics else None,
        done_reason=diagnostics.done_reason if diagnostics else None,
        raw_content_empty=diagnostics.raw_content_empty if diagnostics else True,
        thinking_present=diagnostics.thinking_present if diagnostics else None,
        schema_valid=schema_valid,
        fallback_used=diagnostics.fallback_used if diagnostics else True,
        fallback_reason=diagnostics.fallback_reason if diagnostics else ClassificationFailureCode.unknown,
        task_type=result.classification.task_type if schema_valid else None,
        project_area=result.classification.project_area if schema_valid else None,
        sensitivity_hint=result.classification.sensitivity_hint if schema_valid else None,
        allowed_next_step=result.classification.allowed_next_step if schema_valid else None,
    )


def default_report_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "local_eval_reports"


if __name__ == "__main__":
    raise SystemExit(main())
