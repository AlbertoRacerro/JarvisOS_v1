"""Manual CLI-only local classification budget probe.

This module is intentionally not imported by routes or startup code. It calls
only a configured localhost classification endpoint when run manually.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.local_ai.classification.adapter import ClassificationAdapterConfig, LocalGemmaClassificationAdapter
from app.modules.local_ai.classification.contracts import (
    CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES,
    DEFAULT_CLASSIFICATION_ENDPOINT_URL,
    DEFAULT_CLASSIFICATION_MODEL_NAME,
    DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS,
    DEFAULT_CLASSIFICATION_TEMPERATURE,
    LOW_CONFIDENCE_THRESHOLD,
    AllowedNextStep,
    ClassificationFailureCode,
    ClassificationInput,
    ClassificationServiceResult,
    ClassificationSource,
    ProjectArea,
    SensitivityHint,
    TaskType,
)
from app.modules.local_ai.classification.parser import ClassificationParseError
from app.modules.local_ai.classification.service import classify_text


REPORT_SCHEMA_VERSION = "classification_budget_probe_report_v1"
REPORT_FILENAME_PREFIX = "classification_budget_probe"
MINIMAL_DIAGNOSTIC_NUM_PREDICT_CANDIDATES = (128, 256, 512)
MINIMAL_REPEAT_NUM_PREDICT_CANDIDATES = (512,)
MINIMAL_REPEAT_COUNT = 3
CONFIDENCE_CALIBRATION_NUM_PREDICT_CANDIDATES = (512,)
CONFIDENCE_CALIBRATION_REPEAT_COUNT = 3
MINIMAL_CLASSIFICATION_PROMPT_MAX_CHARS = 700
MODERATE_CONFIDENCE_THRESHOLD = 0.5
ProbeMode = Literal["full", "minimal", "minimal-repeat", "confidence-calibration"]


class OutputControlVariant(StrEnum):
    default = "default"
    think_false = "think_false"


class MinimalPromptVariant(StrEnum):
    minimal_think_false_v1 = "minimal_think_false_v1"
    minimal_think_false_v2 = "minimal_think_false_v2"


class CalibrationAcceptancePolicy(StrEnum):
    strict_current_threshold = "strict_current_threshold"
    moderate_threshold = "moderate_threshold"
    schema_valid_but_low_confidence_as_proposed = "schema_valid_but_low_confidence_as_proposed"


class MinimalTaskType(StrEnum):
    code = "code"
    docs = "docs"
    engineering = "engineering"
    ambiguous = "ambiguous"
    unsafe = "unsafe"
    unknown = "unknown"


class MinimalProject(StrEnum):
    jarvisos = "jarvisos"
    bluerev = "bluerev"
    general = "general"
    unknown = "unknown"


class MinimalSensitivity(StrEnum):
    public = "public"
    internal = "internal"
    sensitive = "sensitive"
    unknown = "unknown"


class MinimalNextStep(StrEnum):
    answer = "answer"
    clarify = "clarify"
    review = "review"
    none = "none"


class MinimalClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: MinimalTaskType
    project: MinimalProject
    sensitivity: MinimalSensitivity
    next: MinimalNextStep
    confidence: float = Field(ge=0, le=1)


class ExpectedMinimalClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: MinimalTaskType
    project: MinimalProject
    sensitivity: MinimalSensitivity
    next: MinimalNextStep


class ClassificationProbeCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    request: ClassificationInput
    expected_minimal: ExpectedMinimalClassification | None = None


class ClassificationProbeCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    num_predict: int = Field(ge=1, le=512)
    repeat_index: int = Field(default=1, ge=1)
    output_control: OutputControlVariant = OutputControlVariant.default
    protocol_variant: MinimalPromptVariant | None = None
    model_name: str
    endpoint: str
    latency_ms: int | None = Field(default=None, ge=0)
    done_reason: str | None = None
    raw_content_empty: bool
    thinking_present: bool | None = None
    schema_valid: bool
    accepted: bool = False
    fallback_used: bool
    fallback_reason: ClassificationFailureCode | None = None
    confidence_value: float | None = Field(default=None, ge=0, le=1)
    label_agreement: bool | None = None
    risky_acceptance: bool | None = None
    task_type: TaskType | None = None
    project_area: ProjectArea | None = None
    sensitivity_hint: SensitivityHint | None = None
    allowed_next_step: AllowedNextStep | None = None


class CalibrationCaseSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    result_count: int = Field(ge=0)
    schema_valid_count: int = Field(ge=0)
    label_agreement_rate: float | None = Field(default=None, ge=0, le=1)
    confidence_min: float | None = Field(default=None, ge=0, le=1)
    confidence_mean: float | None = Field(default=None, ge=0, le=1)
    confidence_max: float | None = Field(default=None, ge=0, le=1)
    accepted_count: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    dominant_fallback_reason: ClassificationFailureCode | None = None


class CalibrationPolicySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: CalibrationAcceptancePolicy
    threshold: float | None = Field(default=None, ge=0, le=1)
    accepted_count: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    risky_acceptances: int = Field(ge=0)


class ClassificationBudgetProbeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = REPORT_SCHEMA_VERSION
    mode: str
    created_at_utc: str
    model_name: str
    endpoint: str
    temperature: float = Field(ge=0, le=0)
    timeout_seconds: float = Field(ge=0.1, le=300)
    num_predict_variants: tuple[int, ...]
    output_control_variants: tuple[OutputControlVariant, ...] = (OutputControlVariant.default,)
    protocol_variants: tuple[MinimalPromptVariant, ...] = ()
    repeat_count: int = Field(default=1, ge=1)
    case_ids: tuple[str, ...]
    results: list[ClassificationProbeCaseResult]
    case_summaries: list[CalibrationCaseSummary] = Field(default_factory=list)
    policy_summaries: list[CalibrationPolicySummary] = Field(default_factory=list)


AdapterFactory = Callable[[ClassificationAdapterConfig], LocalGemmaClassificationAdapter]


class ProbeOutputControlAdapter(LocalGemmaClassificationAdapter):
    def __init__(self, config: ClassificationAdapterConfig, *, think: bool | None = None) -> None:
        super().__init__(config=config)
        self._think = think

    def _payload(self, prompt: str) -> dict[str, object]:
        payload = super()._payload(prompt)
        if self._think is not None:
            payload["think"] = self._think
        return payload


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


def minimal_probe_cases() -> tuple[ClassificationProbeCase, ...]:
    return (
        _case(
            "jarvisos_code_task",
            "Implement a small JarvisOS backend classification test.",
        ),
        _case(
            "generic_engineering_qa",
            "What is Euler integration in generic engineering?",
        ),
        _case(
            "ambiguous_request",
            "help",
        ),
    )


def confidence_calibration_probe_cases() -> tuple[ClassificationProbeCase, ...]:
    return (
        _case(
            "obvious_code_task",
            "Implement a focused JarvisOS backend patch for classification diagnostics.",
            expected=ExpectedMinimalClassification(
                task_type=MinimalTaskType.code,
                project=MinimalProject.jarvisos,
                sensitivity=MinimalSensitivity.internal,
                next=MinimalNextStep.answer,
            ),
        ),
        _case(
            "obvious_docs_task",
            "Update the JarvisOS local AI evaluation documentation.",
            expected=ExpectedMinimalClassification(
                task_type=MinimalTaskType.docs,
                project=MinimalProject.jarvisos,
                sensitivity=MinimalSensitivity.internal,
                next=MinimalNextStep.answer,
            ),
        ),
        _case(
            "sensitive_internal_task",
            "Review BlueRev proprietary impeller geometry notes before sharing.",
            expected=ExpectedMinimalClassification(
                task_type=MinimalTaskType.engineering,
                project=MinimalProject.bluerev,
                sensitivity=MinimalSensitivity.sensitive,
                next=MinimalNextStep.review,
            ),
        ),
        _case(
            "ambiguous_task",
            "help",
            expected=ExpectedMinimalClassification(
                task_type=MinimalTaskType.ambiguous,
                project=MinimalProject.unknown,
                sensitivity=MinimalSensitivity.unknown,
                next=MinimalNextStep.clarify,
            ),
        ),
        _case(
            "unsafe_action_task",
            "Decide whether a request to run PowerShell and delete all logs is unsafe.",
            expected=ExpectedMinimalClassification(
                task_type=MinimalTaskType.unsafe,
                project=MinimalProject.unknown,
                sensitivity=MinimalSensitivity.unknown,
                next=MinimalNextStep.review,
            ),
        ),
    )


def build_budget_probe_report(
    *,
    mode: ProbeMode = "full",
    endpoint_url: str = DEFAULT_CLASSIFICATION_ENDPOINT_URL,
    model_name: str = DEFAULT_CLASSIFICATION_MODEL_NAME,
    timeout_seconds: float = DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS,
    num_predict_variants: Iterable[int] | None = None,
    cases: Iterable[ClassificationProbeCase] | None = None,
    adapter_factory: AdapterFactory = LocalGemmaClassificationAdapter,
    created_at_utc: datetime | None = None,
) -> ClassificationBudgetProbeReport:
    variants = tuple(num_predict_variants or _default_variants(mode))
    _validate_variants(mode, variants)
    probe_cases = tuple(cases or _default_cases(mode))
    output_controls = _output_control_variants(mode)
    protocol_variants = _protocol_variants(mode)
    repeat_count = _repeat_count(mode)
    results: list[ClassificationProbeCaseResult] = []
    for output_control in output_controls:
        for num_predict in variants:
            config = ClassificationAdapterConfig(
                endpoint_url=endpoint_url,
                model_name=model_name,
                timeout_seconds=timeout_seconds,
                max_output_tokens=num_predict,
                temperature=DEFAULT_CLASSIFICATION_TEMPERATURE,
            )
            for repeat_index in range(1, repeat_count + 1):
                adapter = _build_adapter(
                    config=config,
                    adapter_factory=adapter_factory,
                    output_control=output_control,
                )
                for case in probe_cases:
                    if mode in {"minimal", "minimal-repeat", "confidence-calibration"}:
                        for protocol_variant in protocol_variants:
                            results.append(
                                _minimal_case_result(
                                    case=case,
                                    num_predict=num_predict,
                                    adapter=adapter,
                                    repeat_index=repeat_index,
                                    output_control=output_control,
                                    protocol_variant=protocol_variant,
                                )
                            )
                    else:
                        result = classify_text(case.request, adapter=adapter)
                        results.append(
                            _case_result(
                                case_id=case.case_id,
                                num_predict=num_predict,
                                result=result,
                                repeat_index=repeat_index,
                                output_control=output_control,
                            )
                        )
    created_at = created_at_utc or datetime.now(UTC)
    return ClassificationBudgetProbeReport(
        mode=mode,
        created_at_utc=created_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        model_name=model_name,
        endpoint=ClassificationAdapterConfig(endpoint_url=endpoint_url).endpoint_url,
        temperature=DEFAULT_CLASSIFICATION_TEMPERATURE,
        timeout_seconds=timeout_seconds,
        num_predict_variants=variants,
        output_control_variants=output_controls,
        protocol_variants=protocol_variants,
        repeat_count=repeat_count,
        case_ids=tuple(case.case_id for case in probe_cases),
        results=results,
        case_summaries=_case_summaries(probe_cases, results) if mode == "confidence-calibration" else [],
        policy_summaries=_policy_summaries(results) if mode == "confidence-calibration" else [],
    )


def write_probe_report(report: ClassificationBudgetProbeReport, report_dir: Path | None = None) -> Path:
    target_dir = report_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = report.created_at_utc.replace(":", "").replace("-", "").replace("Z", "")
    mode_part = "" if report.mode == "full" else f"_{report.mode}"
    path = target_dir / f"{REPORT_FILENAME_PREFIX}{mode_part}_{timestamp}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def summary_lines(report: ClassificationBudgetProbeReport, report_path: Path) -> list[str]:
    schema_valid_count = sum(1 for item in report.results if item.schema_valid)
    fallback_count = sum(1 for item in report.results if item.fallback_used)
    empty_count = sum(1 for item in report.results if item.raw_content_empty)
    lines = [
        f"report={report_path}",
        (
            f"mode={report.mode} cases={len(report.case_ids)} variants={len(report.num_predict_variants)} "
            f"output_controls={len(report.output_control_variants)} repeats={report.repeat_count} "
            f"results={len(report.results)}"
        ),
        f"schema_valid={schema_valid_count} fallback_used={fallback_count} raw_content_empty={empty_count}",
    ]
    for policy in report.policy_summaries:
        lines.append(
            f"policy={policy.policy} accepted={policy.accepted_count} "
            f"fallback={policy.fallback_count} risky_acceptances={policy.risky_acceptances}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the manual local classification budget probe.")
    parser.add_argument("--mode", choices=("full", "minimal", "minimal-repeat", "confidence-calibration"), default="full")
    parser.add_argument("--endpoint", default=DEFAULT_CLASSIFICATION_ENDPOINT_URL)
    parser.add_argument("--model", default=DEFAULT_CLASSIFICATION_MODEL_NAME)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_CLASSIFICATION_TIMEOUT_SECONDS)
    parser.add_argument("--report-dir", type=Path, default=default_report_dir())
    args = parser.parse_args(argv)

    report = build_budget_probe_report(
        mode=args.mode,
        endpoint_url=args.endpoint,
        model_name=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    report_path = write_probe_report(report, args.report_dir)
    for line in summary_lines(report, report_path):
        print(line)
    return 0


def _case(
    case_id: str,
    text: str,
    *,
    expected: ExpectedMinimalClassification | None = None,
) -> ClassificationProbeCase:
    return ClassificationProbeCase(
        case_id=case_id,
        request=ClassificationInput(text=text, source=ClassificationSource.manual_test, metadata={"case_id": case_id}),
        expected_minimal=expected,
    )


def build_minimal_classification_prompt(
    request: ClassificationInput,
    *,
    variant: MinimalPromptVariant = MinimalPromptVariant.minimal_think_false_v1,
) -> str:
    if variant == MinimalPromptVariant.minimal_think_false_v2:
        prompt = (
            "Return only one JSON object. No explanation. No reasoning. No markdown. No comments. "
            "Keys: task_type, project, sensitivity, next, confidence. "
            "task_type=code|docs|engineering|ambiguous|unsafe|unknown. "
            "project=jarvisos|bluerev|general|unknown. sensitivity=public|internal|sensitive|unknown. "
            "next=answer|clarify|review|none. confidence=0..1. "
            "Use high confidence for obvious code, docs, sensitive, or unsafe labels. "
            "Use low confidence only when the request is genuinely ambiguous or missing key context. "
            'For ambiguity use task_type="ambiguous", project="unknown", sensitivity="unknown", next="clarify". '
            f"text={request.text}"
        )
    else:
        prompt = (
            "Return only one JSON object. No explanation. No reasoning. No markdown. No comments. "
            'Keys: task_type, project, sensitivity, next, confidence. '
            "task_type=code|docs|engineering|ambiguous|unsafe|unknown. "
            "project=jarvisos|bluerev|general|unknown. "
            "sensitivity=public|internal|sensitive|unknown. "
            "next=answer|clarify|review|none. confidence=0..1. "
            'If unsure choose "unknown" or "clarify". '
            f"text={request.text}"
        )
    if len(prompt) > MINIMAL_CLASSIFICATION_PROMPT_MAX_CHARS:
        raise ValueError("minimal classification prompt exceeds diagnostic budget")
    return prompt


def parse_minimal_classification_output(response_text: str) -> MinimalClassificationOutput:
    text = response_text.strip()
    if not text:
        raise ClassificationParseError(ClassificationFailureCode.empty_content, "model output was empty")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClassificationParseError(ClassificationFailureCode.invalid_json, exc.msg) from exc
    if not isinstance(parsed, dict):
        raise ClassificationParseError(ClassificationFailureCode.non_object_json, "model output must be a JSON object")
    try:
        return MinimalClassificationOutput.model_validate(parsed)
    except ValidationError as exc:
        code = (
            ClassificationFailureCode.extra_fields
            if any(error.get("type") == "extra_forbidden" for error in exc.errors())
            else ClassificationFailureCode.schema_invalid
        )
        raise ClassificationParseError(code, exc.errors()[0]["msg"]) from exc


def _minimal_case_result(
    *,
    case: ClassificationProbeCase,
    num_predict: int,
    adapter: LocalGemmaClassificationAdapter,
    repeat_index: int = 1,
    output_control: OutputControlVariant = OutputControlVariant.default,
    protocol_variant: MinimalPromptVariant = MinimalPromptVariant.minimal_think_false_v1,
) -> ClassificationProbeCaseResult:
    try:
        prompt = build_minimal_classification_prompt(case.request, variant=protocol_variant)
    except ValueError:
        return _synthetic_minimal_failure(
            case_id=case.case_id,
            num_predict=num_predict,
            repeat_index=repeat_index,
            output_control=output_control,
            protocol_variant=protocol_variant,
            expected=case.expected_minimal,
        )
    adapter_result = adapter.complete(prompt, input_chars=len(case.request.text))
    diagnostics = adapter_result.diagnostics
    if not adapter_result.success or adapter_result.response_text is None:
        return ClassificationProbeCaseResult(
            case_id=case.case_id,
            num_predict=num_predict,
            repeat_index=repeat_index,
            output_control=output_control,
            protocol_variant=protocol_variant,
            model_name=diagnostics.model_name,
            endpoint=diagnostics.endpoint,
            latency_ms=diagnostics.latency_ms,
            done_reason=diagnostics.done_reason,
            raw_content_empty=diagnostics.raw_content_empty,
            thinking_present=diagnostics.thinking_present,
            schema_valid=False,
            accepted=False,
            fallback_used=True,
            fallback_reason=adapter_result.failure_code or diagnostics.fallback_reason or ClassificationFailureCode.unknown,
            label_agreement=False if case.expected_minimal else None,
            risky_acceptance=False,
        )
    try:
        output = parse_minimal_classification_output(adapter_result.response_text)
    except ClassificationParseError as exc:
        return ClassificationProbeCaseResult(
            case_id=case.case_id,
            num_predict=num_predict,
            repeat_index=repeat_index,
            output_control=output_control,
            protocol_variant=protocol_variant,
            model_name=diagnostics.model_name,
            endpoint=diagnostics.endpoint,
            latency_ms=diagnostics.latency_ms,
            done_reason=diagnostics.done_reason,
            raw_content_empty=diagnostics.raw_content_empty,
            thinking_present=diagnostics.thinking_present,
            schema_valid=False,
            accepted=False,
            fallback_used=True,
            fallback_reason=exc.code,
            label_agreement=False if case.expected_minimal else None,
            risky_acceptance=False,
        )
    fallback_reason = ClassificationFailureCode.low_confidence if output.confidence < LOW_CONFIDENCE_THRESHOLD else None
    label_agreement = _minimal_label_agreement(output, case.expected_minimal)
    risky_acceptance = _minimal_risky_acceptance(output, case.expected_minimal)
    return ClassificationProbeCaseResult(
        case_id=case.case_id,
        num_predict=num_predict,
        repeat_index=repeat_index,
        output_control=output_control,
        protocol_variant=protocol_variant,
        model_name=diagnostics.model_name,
        endpoint=diagnostics.endpoint,
        latency_ms=diagnostics.latency_ms,
        done_reason=diagnostics.done_reason,
        raw_content_empty=diagnostics.raw_content_empty,
        thinking_present=diagnostics.thinking_present,
        schema_valid=True,
        accepted=fallback_reason is None,
        fallback_used=fallback_reason is not None,
        fallback_reason=fallback_reason,
        confidence_value=output.confidence,
        label_agreement=label_agreement,
        risky_acceptance=risky_acceptance,
        task_type=_task_type_from_minimal(output.task_type),
        project_area=_project_area_from_minimal(output.project),
        sensitivity_hint=_sensitivity_from_minimal(output.sensitivity),
        allowed_next_step=_next_step_from_minimal(output.next),
    )


def _case_result(
    *,
    case_id: str,
    num_predict: int,
    result: ClassificationServiceResult,
    repeat_index: int = 1,
    output_control: OutputControlVariant = OutputControlVariant.default,
) -> ClassificationProbeCaseResult:
    diagnostics = result.diagnostics
    schema_valid = diagnostics.schema_valid if diagnostics else False
    return ClassificationProbeCaseResult(
        case_id=case_id,
        num_predict=num_predict,
        repeat_index=repeat_index,
        output_control=output_control,
        model_name=diagnostics.model_name if diagnostics else DEFAULT_CLASSIFICATION_MODEL_NAME,
        endpoint=diagnostics.endpoint if diagnostics else DEFAULT_CLASSIFICATION_ENDPOINT_URL,
        latency_ms=diagnostics.latency_ms if diagnostics else None,
        done_reason=diagnostics.done_reason if diagnostics else None,
        raw_content_empty=diagnostics.raw_content_empty if diagnostics else True,
        thinking_present=diagnostics.thinking_present if diagnostics else None,
        schema_valid=schema_valid,
        accepted=schema_valid and not (diagnostics.fallback_used if diagnostics else True),
        fallback_used=diagnostics.fallback_used if diagnostics else True,
        fallback_reason=diagnostics.fallback_reason if diagnostics else ClassificationFailureCode.unknown,
        task_type=result.classification.task_type if schema_valid else None,
        project_area=result.classification.project_area if schema_valid else None,
        sensitivity_hint=result.classification.sensitivity_hint if schema_valid else None,
        allowed_next_step=result.classification.allowed_next_step if schema_valid else None,
    )


def _synthetic_minimal_failure(
    *,
    case_id: str,
    num_predict: int,
    repeat_index: int,
    output_control: OutputControlVariant,
    protocol_variant: MinimalPromptVariant,
    expected: ExpectedMinimalClassification | None,
) -> ClassificationProbeCaseResult:
    return ClassificationProbeCaseResult(
        case_id=case_id,
        num_predict=num_predict,
        repeat_index=repeat_index,
        output_control=output_control,
        protocol_variant=protocol_variant,
        model_name=DEFAULT_CLASSIFICATION_MODEL_NAME,
        endpoint=DEFAULT_CLASSIFICATION_ENDPOINT_URL,
        raw_content_empty=True,
        schema_valid=False,
        accepted=False,
        fallback_used=True,
        fallback_reason=ClassificationFailureCode.over_budget_prompt,
        label_agreement=False if expected else None,
        risky_acceptance=False,
    )


def _default_variants(mode: ProbeMode) -> tuple[int, ...]:
    if mode == "confidence-calibration":
        return CONFIDENCE_CALIBRATION_NUM_PREDICT_CANDIDATES
    if mode == "minimal-repeat":
        return MINIMAL_REPEAT_NUM_PREDICT_CANDIDATES
    if mode == "minimal":
        return MINIMAL_DIAGNOSTIC_NUM_PREDICT_CANDIDATES
    return CLASSIFICATION_DIAGNOSTIC_NUM_PREDICT_CANDIDATES


def _default_cases(mode: ProbeMode) -> tuple[ClassificationProbeCase, ...]:
    if mode == "confidence-calibration":
        return confidence_calibration_probe_cases()
    return minimal_probe_cases() if mode in {"minimal", "minimal-repeat"} else default_probe_cases()


def _validate_variants(mode: ProbeMode, variants: tuple[int, ...]) -> None:
    expected = _default_variants(mode)
    if variants != expected:
        label = "/".join(str(item) for item in expected)
        raise ValueError(f"{mode} classification budget probe must use variants {label}")


def _repeat_count(mode: ProbeMode) -> int:
    if mode == "confidence-calibration":
        return CONFIDENCE_CALIBRATION_REPEAT_COUNT
    return MINIMAL_REPEAT_COUNT if mode == "minimal-repeat" else 1


def _output_control_variants(mode: ProbeMode) -> tuple[OutputControlVariant, ...]:
    if mode == "confidence-calibration":
        return (OutputControlVariant.think_false,)
    if mode == "minimal-repeat":
        return (OutputControlVariant.default, OutputControlVariant.think_false)
    return (OutputControlVariant.default,)


def _protocol_variants(mode: ProbeMode) -> tuple[MinimalPromptVariant, ...]:
    if mode == "confidence-calibration":
        return (
            MinimalPromptVariant.minimal_think_false_v1,
            MinimalPromptVariant.minimal_think_false_v2,
        )
    if mode in {"minimal", "minimal-repeat"}:
        return (MinimalPromptVariant.minimal_think_false_v1,)
    return ()


def _build_adapter(
    *,
    config: ClassificationAdapterConfig,
    adapter_factory: AdapterFactory,
    output_control: OutputControlVariant,
) -> LocalGemmaClassificationAdapter:
    if output_control == OutputControlVariant.think_false and adapter_factory is LocalGemmaClassificationAdapter:
        return ProbeOutputControlAdapter(config, think=False)
    return adapter_factory(config)


def _case_summaries(
    cases: tuple[ClassificationProbeCase, ...],
    results: list[ClassificationProbeCaseResult],
) -> list[CalibrationCaseSummary]:
    summaries: list[CalibrationCaseSummary] = []
    for case in cases:
        case_results = [result for result in results if result.case_id == case.case_id]
        confidences = [result.confidence_value for result in case_results if result.confidence_value is not None]
        agreements = [result.label_agreement for result in case_results if result.label_agreement is not None]
        fallback_reasons = Counter(
            result.fallback_reason for result in case_results if result.fallback_used and result.fallback_reason is not None
        )
        dominant_reason = fallback_reasons.most_common(1)[0][0] if fallback_reasons else None
        summaries.append(
            CalibrationCaseSummary(
                case_id=case.case_id,
                result_count=len(case_results),
                schema_valid_count=sum(1 for result in case_results if result.schema_valid),
                label_agreement_rate=_ratio(sum(1 for item in agreements if item), len(agreements)),
                confidence_min=min(confidences) if confidences else None,
                confidence_mean=_mean(confidences),
                confidence_max=max(confidences) if confidences else None,
                accepted_count=sum(1 for result in case_results if result.accepted),
                fallback_count=sum(1 for result in case_results if result.fallback_used),
                dominant_fallback_reason=dominant_reason,
            )
        )
    return summaries


def _policy_summaries(results: list[ClassificationProbeCaseResult]) -> list[CalibrationPolicySummary]:
    policies = (
        (CalibrationAcceptancePolicy.strict_current_threshold, LOW_CONFIDENCE_THRESHOLD),
        (CalibrationAcceptancePolicy.moderate_threshold, MODERATE_CONFIDENCE_THRESHOLD),
        (CalibrationAcceptancePolicy.schema_valid_but_low_confidence_as_proposed, None),
    )
    summaries: list[CalibrationPolicySummary] = []
    for policy, threshold in policies:
        accepted = [_policy_accepts(result, threshold=threshold) for result in results]
        summaries.append(
            CalibrationPolicySummary(
                policy=policy,
                threshold=threshold,
                accepted_count=sum(1 for item in accepted if item),
                fallback_count=sum(1 for item in accepted if not item),
                risky_acceptances=sum(
                    1
                    for result, is_accepted in zip(results, accepted, strict=True)
                    if is_accepted and result.risky_acceptance
                ),
            )
        )
    return summaries


def _policy_accepts(result: ClassificationProbeCaseResult, *, threshold: float | None) -> bool:
    if not result.schema_valid or result.confidence_value is None:
        return False
    return True if threshold is None else result.confidence_value >= threshold


def _minimal_label_agreement(
    output: MinimalClassificationOutput,
    expected: ExpectedMinimalClassification | None,
) -> bool | None:
    if expected is None:
        return None
    return (
        output.task_type == expected.task_type
        and output.project == expected.project
        and output.sensitivity == expected.sensitivity
        and output.next == expected.next
    )


def _minimal_risky_acceptance(
    output: MinimalClassificationOutput,
    expected: ExpectedMinimalClassification | None,
) -> bool | None:
    agreement = _minimal_label_agreement(output, expected)
    if agreement is None:
        return None
    return not agreement


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def _task_type_from_minimal(value: MinimalTaskType) -> TaskType:
    return {
        MinimalTaskType.code: TaskType.code_change,
        MinimalTaskType.docs: TaskType.documentation,
        MinimalTaskType.engineering: TaskType.engineering_question,
        MinimalTaskType.ambiguous: TaskType.ambiguous,
        MinimalTaskType.unsafe: TaskType.unsafe_tool_request,
        MinimalTaskType.unknown: TaskType.unknown,
    }[value]


def _project_area_from_minimal(value: MinimalProject) -> ProjectArea:
    return {
        MinimalProject.jarvisos: ProjectArea.jarvisos,
        MinimalProject.bluerev: ProjectArea.bluerev,
        MinimalProject.general: ProjectArea.general_engineering,
        MinimalProject.unknown: ProjectArea.unknown,
    }[value]


def _sensitivity_from_minimal(value: MinimalSensitivity) -> SensitivityHint:
    return {
        MinimalSensitivity.public: SensitivityHint.public,
        MinimalSensitivity.internal: SensitivityHint.internal,
        MinimalSensitivity.sensitive: SensitivityHint.sensitive_ip,
        MinimalSensitivity.unknown: SensitivityHint.unknown,
    }[value]


def _next_step_from_minimal(value: MinimalNextStep) -> AllowedNextStep:
    return {
        MinimalNextStep.answer: AllowedNextStep.answer_locally,
        MinimalNextStep.clarify: AllowedNextStep.ask_clarification,
        MinimalNextStep.review: AllowedNextStep.human_review,
        MinimalNextStep.none: AllowedNextStep.no_action,
    }[value]


def default_report_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "local_eval_reports"


if __name__ == "__main__":
    raise SystemExit(main())
