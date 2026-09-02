"""CLI/report probes for local Gemma micro-contract evaluation only."""

import argparse
import json
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.local_ai.contracts import (
    MICRO_CONTRACT_SCHEMA_VERSION,
    ContextRequestOutput,
    DecisionExtractionOutput,
    EvidenceSelectionOutput,
    SensitivityCheckOutput,
    TaskClassificationOutput,
    TodoExtractionOutput,
)

DEFAULT_MODEL_NAME = "gemma4:12b-it-qat"
DEFAULT_HEAVY_MODEL_NAME = "gemma4:31b-it-qat"
DEFAULT_NATIVE_ENDPOINT = "http://localhost:11434/api/chat"
DEFAULT_NUM_PREDICT = 512
ALLOWED_NATIVE_PATHS = {"/api/chat"}
LOCAL_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "::1"}

JsonSchema = dict[str, Any]
Evaluator = Callable[[BaseModel], tuple[bool, str | None]]


class ProbeConfigurationError(ValueError):
    """Raised when the local micro-contract probe is configured unsafely."""


class ProbeCase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    contract_name: str
    case_id: str
    prompt: str
    contract_model: type[BaseModel]
    flat_schema: JsonSchema
    evaluator: Evaluator
    schema_variant: str = "flat_v1"


class MicroContractProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str
    contract_name: str
    case_id: str
    attempt: str
    valid_json: bool
    schema_valid: bool
    content_passed: bool
    latency_seconds: float
    done_reason: str | None = None
    eval_count: int | None = None
    prompt_eval_count: int | None = None
    message_content_empty: bool
    message_thinking_empty: bool
    message_content_preview_truncated: str = ""
    message_thinking_preview_truncated: str = ""
    keys_present: list[str] = Field(default_factory=list)
    failure_code: str | None = None
    failure_message_short: str | None = None
    num_predict: int
    schema_variant: str


class MicroContractProbeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime_endpoint: str
    primary_model_name: str
    heavy_model_name: str | None
    case_count: int
    schema_valid_count: int
    content_passed_count: int
    failed_count: int
    timeout_count: int
    invalid_json_count: int
    schema_invalid_count: int
    thinking_budget_exhausted_count: int
    average_latency_seconds: float
    results_by_contract: dict[str, list[MicroContractProbeResult]]
    failure_counts_by_contract: dict[str, int]
    failure_counts_by_failure_code: dict[str, int]


def validate_native_endpoint(endpoint_url: str) -> str:
    parsed = urlparse(endpoint_url)
    if parsed.scheme != "http":
        raise ProbeConfigurationError("Native local endpoint must use http://.")
    if not parsed.hostname or parsed.hostname.lower() not in LOCAL_ENDPOINT_HOSTS:
        raise ProbeConfigurationError("Native local endpoint host must be localhost, 127.0.0.1, or ::1.")
    if parsed.username or parsed.password:
        raise ProbeConfigurationError("Native local endpoint must not include credentials.")
    if parsed.path not in ALLOWED_NATIVE_PATHS:
        raise ProbeConfigurationError("Native local endpoint must use /api/chat.")
    return endpoint_url


def build_native_payload(case: ProbeCase, *, model_name: str, num_predict: int) -> dict[str, Any]:
    assert_flat_schema(case.flat_schema)
    return {
        "model": model_name,
        "messages": [{"role": "user", "content": case.prompt}],
        "stream": False,
        "format": case.flat_schema,
        "options": {"temperature": 0, "num_predict": num_predict},
    }


def assert_flat_schema(schema: JsonSchema) -> None:
    encoded = json.dumps(schema)
    for forbidden in ('"$defs"', '"$ref"', '"anyOf"'):
        if forbidden in encoded:
            raise ProbeConfigurationError(f"Flat schema must not contain {forbidden}.")


def run_probe_suite(
    *,
    primary_model_name: str = DEFAULT_MODEL_NAME,
    heavy_model_name: str | None = DEFAULT_HEAVY_MODEL_NAME,
    endpoint_url: str = DEFAULT_NATIVE_ENDPOINT,
    timeout_seconds: float = 180,
    num_predict: int = DEFAULT_NUM_PREDICT,
    client: httpx.Client | None = None,
    run_heavy_comparison: bool = True,
) -> MicroContractProbeReport:
    endpoint_url = validate_native_endpoint(endpoint_url)
    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout_seconds)
    results: list[MicroContractProbeResult] = []
    try:
        for case in build_primary_probe_cases():
            first = run_probe_case(
                case,
                model_name=primary_model_name,
                endpoint_url=endpoint_url,
                timeout_seconds=timeout_seconds,
                num_predict=num_predict,
                client=http_client,
                attempt="first",
            )
            results.append(first)
            if first.content_passed:
                results.append(
                    run_probe_case(
                        case,
                        model_name=primary_model_name,
                        endpoint_url=endpoint_url,
                        timeout_seconds=timeout_seconds,
                        num_predict=num_predict,
                        client=http_client,
                        attempt="repeat",
                    )
                )
        if run_heavy_comparison and heavy_model_name:
            for case in build_heavy_probe_cases():
                results.append(
                    run_probe_case(
                        case,
                        model_name=heavy_model_name,
                        endpoint_url=endpoint_url,
                        timeout_seconds=timeout_seconds,
                        num_predict=num_predict,
                        client=http_client,
                        attempt="limited_comparison",
                    )
                )
    finally:
        if owns_client:
            http_client.close()
    return aggregate_report(
        endpoint_url=endpoint_url,
        primary_model_name=primary_model_name,
        heavy_model_name=heavy_model_name if run_heavy_comparison else None,
        results=results,
    )


def run_probe_case(
    case: ProbeCase,
    *,
    model_name: str,
    endpoint_url: str,
    timeout_seconds: float,
    num_predict: int,
    client: httpx.Client,
    attempt: str = "first",
) -> MicroContractProbeResult:
    payload = build_native_payload(case, model_name=model_name, num_predict=num_predict)
    started = time.perf_counter()
    try:
        response = client.post(endpoint_url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        response_json = response.json()
        message = response_json.get("message") if isinstance(response_json.get("message"), dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        thinking = message.get("thinking", "") if isinstance(message, dict) else ""
    except httpx.TimeoutException as exc:
        return _result(
            case,
            model_name=model_name,
            attempt=attempt,
            started=started,
            num_predict=num_predict,
            failure_code="timeout",
            failure_message=f"Local runtime timed out: {type(exc).__name__}",
        )
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        return _result(
            case,
            model_name=model_name,
            attempt=attempt,
            started=started,
            num_predict=num_predict,
            failure_code="runtime_error",
            failure_message=f"Local runtime error: {type(exc).__name__}",
        )

    done_reason = response_json.get("done_reason") if isinstance(response_json.get("done_reason"), str) else None
    eval_count = response_json.get("eval_count") if isinstance(response_json.get("eval_count"), int) else None
    prompt_eval_count = response_json.get("prompt_eval_count") if isinstance(response_json.get("prompt_eval_count"), int) else None
    valid_json, parsed, json_error = _parse_json_object(content)
    if not valid_json:
        failure_code = (
            "thinking_budget_exhausted"
            if content == "" and thinking != "" and done_reason == "length"
            else "invalid_json"
        )
        return _result(
            case,
            model_name=model_name,
            attempt=attempt,
            started=started,
            num_predict=num_predict,
            valid_json=False,
            schema_valid=False,
            content_passed=False,
            done_reason=done_reason,
            eval_count=eval_count,
            prompt_eval_count=prompt_eval_count,
            content=content,
            thinking=thinking,
            failure_code=failure_code,
            failure_message=json_error,
        )

    keys_present = sorted(parsed.keys())
    try:
        output = case.contract_model.model_validate(parsed)
    except ValidationError as exc:
        return _result(
            case,
            model_name=model_name,
            attempt=attempt,
            started=started,
            num_predict=num_predict,
            valid_json=True,
            schema_valid=False,
            content_passed=False,
            done_reason=done_reason,
            eval_count=eval_count,
            prompt_eval_count=prompt_eval_count,
            content=content,
            thinking=thinking,
            keys_present=keys_present,
            failure_code="schema_invalid",
            failure_message=exc.errors()[0]["msg"],
        )

    passed, failure_message = case.evaluator(output)
    return _result(
        case,
        model_name=model_name,
        attempt=attempt,
        started=started,
        num_predict=num_predict,
        valid_json=True,
        schema_valid=True,
        content_passed=passed,
        done_reason=done_reason,
        eval_count=eval_count,
        prompt_eval_count=prompt_eval_count,
        content=content,
        thinking=thinking,
        keys_present=keys_present,
        failure_code=None if passed else "content_failed",
        failure_message=failure_message,
    )


def aggregate_report(
    *,
    endpoint_url: str,
    primary_model_name: str,
    heavy_model_name: str | None,
    results: list[MicroContractProbeResult],
) -> MicroContractProbeReport:
    failure_counts_by_contract: Counter[str] = Counter()
    failure_counts_by_failure_code: Counter[str] = Counter()
    results_by_contract: dict[str, list[MicroContractProbeResult]] = defaultdict(list)
    for result in results:
        results_by_contract[result.contract_name].append(result)
        if not result.content_passed:
            failure_counts_by_contract[result.contract_name] += 1
            failure_counts_by_failure_code[result.failure_code or "unknown"] += 1
    case_count = len(results)
    return MicroContractProbeReport(
        runtime_endpoint=endpoint_url,
        primary_model_name=primary_model_name,
        heavy_model_name=heavy_model_name,
        case_count=case_count,
        schema_valid_count=sum(1 for result in results if result.schema_valid),
        content_passed_count=sum(1 for result in results if result.content_passed),
        failed_count=sum(1 for result in results if not result.content_passed),
        timeout_count=sum(1 for result in results if result.failure_code == "timeout"),
        invalid_json_count=sum(1 for result in results if result.failure_code == "invalid_json"),
        schema_invalid_count=sum(1 for result in results if result.failure_code == "schema_invalid"),
        thinking_budget_exhausted_count=sum(1 for result in results if result.failure_code == "thinking_budget_exhausted"),
        average_latency_seconds=round(sum(result.latency_seconds for result in results) / case_count, 3) if case_count else 0,
        results_by_contract=dict(results_by_contract),
        failure_counts_by_contract=dict(failure_counts_by_contract),
        failure_counts_by_failure_code=dict(failure_counts_by_failure_code),
    )


def build_primary_probe_cases() -> list[ProbeCase]:
    return [
        ProbeCase(
            contract_name="TaskClassificationOutput",
            case_id="task_classification_codex_impl",
            contract_model=TaskClassificationOutput,
            flat_schema=TASK_CLASSIFICATION_FLAT_SCHEMA,
            prompt=_prompt(
                "Classify this request:",
                "Implement a backend test for JarvisOS.",
                "Use task_type code_change, project_area jarvisos, requires_context true, requires_tool false, requires_external_reasoning false.",
            ),
            evaluator=lambda output: _expect_attrs(
                output,
                {
                    "task_type": "code_change",
                    "project_area": "jarvisos",
                    "requires_context": True,
                    "requires_tool": False,
                    "requires_external_reasoning": False,
                },
            ),
        ),
        ProbeCase(
            contract_name="ContextRequestOutput",
            case_id="context_request_codex_report",
            contract_model=ContextRequestOutput,
            flat_schema=CONTEXT_REQUEST_FLAT_SCHEMA,
            prompt=_prompt(
                "Request bounded context packages:",
                "The user asks to continue JarvisOS after a report.",
                "Request CURRENT_MILESTONE and RECENT_DECISIONS.",
            ),
            evaluator=lambda output: _expect_context_packages(output, {"CURRENT_MILESTONE", "RECENT_DECISIONS"}),
        ),
        ProbeCase(
            contract_name="SensitivityCheckOutput",
            case_id="sensitivity_public_engineering",
            contract_model=SensitivityCheckOutput,
            flat_schema=SENSITIVITY_FLAT_SCHEMA,
            prompt=_prompt(
                "Classify sensitivity:",
                "What is Euler integration?",
                "Use sensitivity public, externalization_allowed true, redaction_required false, user_confirmation_required false.",
            ),
            evaluator=lambda output: _expect_attrs(
                output,
                {
                    "sensitivity": "public",
                    "externalization_allowed": True,
                    "redaction_required": False,
                    "user_confirmation_required": False,
                },
            ),
        ),
        ProbeCase(
            contract_name="TodoExtractionOutput",
            case_id="todo_extract_present",
            contract_model=TodoExtractionOutput,
            flat_schema=TODO_EXTRACTION_FLAT_SCHEMA,
            prompt=_prompt(
                "Extract TODOs:",
                "TODO: write D10C report.",
                "Return one todo.",
            ),
            evaluator=lambda output: (len(output.todos) == 1, None if len(output.todos) == 1 else "expected one todo"),
        ),
        ProbeCase(
            contract_name="DecisionExtractionOutput",
            case_id="decision_extract_accepted",
            contract_model=DecisionExtractionOutput,
            flat_schema=DECISION_EXTRACTION_FLAT_SCHEMA,
            prompt=_prompt(
                "Extract decisions:",
                "Accepted decision: use flat schemas for Ollama probes.",
                "Use decision_status accepted.",
            ),
            evaluator=lambda output: _expect_attrs(output, {"decision_status": "accepted"}),
        ),
        ProbeCase(
            contract_name="EvidenceSelectionOutput",
            case_id="evidence_select_relevant",
            contract_model=EvidenceSelectionOutput,
            flat_schema=EVIDENCE_SELECTION_FLAT_SCHEMA,
            prompt=_prompt(
                "Select relevant evidence:",
                "ev_1 says 12B passed flat task classification. ev_2 says unrelated UI colors changed.",
                "Select ev_1 and reject ev_2.",
            ),
            evaluator=lambda output: _expect_evidence(output, selected="ev_1", rejected="ev_2"),
        ),
    ]


def build_heavy_probe_cases() -> list[ProbeCase]:
    primary = {case.contract_name: case for case in build_primary_probe_cases()}
    return [
        primary["TaskClassificationOutput"],
        primary["ContextRequestOutput"],
        primary["SensitivityCheckOutput"],
    ]


def write_report(report: MicroContractProbeReport, *, output_dir: Path | str) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = directory / f"d10c_flat_schema_micro_contract_probe_{timestamp}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True), encoding="utf-8")
    return path


def _prompt(instruction: str, scenario: str, expected_shape: str) -> str:
    return "\n".join(
        [
            "Return exactly one JSON object matching the provided schema.",
            "No prose. No markdown. No code fences.",
            "Do not execute tools, read files, query databases, or call external APIs.",
            f"schema_version must be {MICRO_CONTRACT_SCHEMA_VERSION}.",
            instruction,
            scenario,
            expected_shape,
        ]
    )


def _parse_json_object(content: str) -> tuple[bool, dict[str, Any], str | None]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return False, {}, exc.msg
    if not isinstance(parsed, dict):
        return False, {}, "JSON output must be an object."
    return True, parsed, None


def _result(
    case: ProbeCase,
    *,
    model_name: str,
    attempt: str,
    started: float,
    num_predict: int,
    valid_json: bool = False,
    schema_valid: bool = False,
    content_passed: bool = False,
    done_reason: str | None = None,
    eval_count: int | None = None,
    prompt_eval_count: int | None = None,
    content: str = "",
    thinking: str = "",
    keys_present: list[str] | None = None,
    failure_code: str | None = None,
    failure_message: str | None = None,
) -> MicroContractProbeResult:
    return MicroContractProbeResult(
        model_name=model_name,
        contract_name=case.contract_name,
        case_id=case.case_id,
        attempt=attempt,
        valid_json=valid_json,
        schema_valid=schema_valid,
        content_passed=content_passed,
        latency_seconds=round(time.perf_counter() - started, 3),
        done_reason=done_reason,
        eval_count=eval_count,
        prompt_eval_count=prompt_eval_count,
        message_content_empty=content == "",
        message_thinking_empty=thinking == "",
        message_content_preview_truncated=content[:200],
        message_thinking_preview_truncated=thinking[:200],
        keys_present=keys_present or [],
        failure_code=failure_code,
        failure_message_short=failure_message[:200] if failure_message else None,
        num_predict=num_predict,
        schema_variant=case.schema_variant,
    )


def _value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _expect_attrs(output: BaseModel, expected: dict[str, Any]) -> tuple[bool, str | None]:
    for field, expected_value in expected.items():
        actual = _value(getattr(output, field))
        if actual != expected_value:
            return False, f"{field} expected {expected_value!r}, got {actual!r}"
    return True, None


def _expect_context_packages(output: ContextRequestOutput, expected_packages: set[str]) -> tuple[bool, str | None]:
    actual = {_value(package) for package in output.requested_context_packages}
    if not expected_packages.issubset(actual):
        return False, f"missing context packages {sorted(expected_packages - actual)}"
    return True, None


def _expect_evidence(output: EvidenceSelectionOutput, *, selected: str, rejected: str) -> tuple[bool, str | None]:
    selected_refs = {item.ref_id for item in output.selected_evidence_refs}
    rejected_refs = {item.ref_id for item in output.rejected_evidence_refs}
    if selected not in selected_refs:
        return False, f"expected selected evidence {selected}"
    if rejected not in rejected_refs:
        return False, f"expected rejected evidence {rejected}"
    return True, None


def _string_enum(values: list[str]) -> JsonSchema:
    return {"type": "string", "enum": values}


def _string_array(item_enum: list[str] | None = None) -> JsonSchema:
    item_schema: JsonSchema = {"type": "string"}
    if item_enum:
        item_schema["enum"] = item_enum
    return {"type": "array", "items": item_schema}


TASK_CLASSIFICATION_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "task_type": _string_enum(["code_change", "modeling", "documentation", "unknown"]),
        "project_area": _string_enum(["jarvisos", "bluerev", "unknown"]),
        "requires_context": {"type": "boolean"},
        "requires_tool": {"type": "boolean"},
        "requires_external_reasoning": {"type": "boolean"},
        "confidence": {"type": "number"},
        "reasons": _string_array(),
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": [
        "task_type",
        "project_area",
        "requires_context",
        "requires_tool",
        "requires_external_reasoning",
        "confidence",
        "reasons",
        "schema_version",
    ],
    "additionalProperties": False,
}

CONTEXT_REQUEST_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "requested_context_packages": _string_array(["CURRENT_TASK", "CURRENT_MILESTONE", "RECENT_DECISIONS", "RELEVANT_DOCS"]),
        "context_request_reason": {"type": "string"},
        "minimum_needed_context": _string_array(),
        "forbidden_context": _string_array(),
        "confidence": {"type": "number"},
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": [
        "requested_context_packages",
        "context_request_reason",
        "minimum_needed_context",
        "forbidden_context",
        "confidence",
        "schema_version",
    ],
    "additionalProperties": False,
}

SENSITIVITY_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "sensitivity": _string_enum(["public", "internal", "confidential", "sensitive_ip", "secret", "unknown"]),
        "externalization_allowed": {"type": "boolean"},
        "redaction_required": {"type": "boolean"},
        "user_confirmation_required": {"type": "boolean"},
        "reasons": _string_array(),
        "confidence": {"type": "number"},
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": [
        "sensitivity",
        "externalization_allowed",
        "redaction_required",
        "user_confirmation_required",
        "reasons",
        "confidence",
        "schema_version",
    ],
    "additionalProperties": False,
}

TODO_EXTRACTION_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "todos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "source_refs": _string_array()},
                "required": ["text", "source_refs"],
                "additionalProperties": False,
            },
        },
        "source_refs": _string_array(),
        "confidence": {"type": "number"},
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": ["todos", "source_refs", "confidence", "schema_version"],
    "additionalProperties": False,
}

DECISION_EXTRACTION_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "status": _string_enum(["proposed", "accepted", "superseded", "rejected", "unknown"]),
                    "source_refs": _string_array(),
                    "supersedes": _string_array(),
                },
                "required": ["text", "status", "source_refs", "supersedes"],
                "additionalProperties": False,
            },
        },
        "decision_status": _string_enum(["proposed", "accepted", "superseded", "rejected", "unknown"]),
        "source_refs": _string_array(),
        "supersedes": _string_array(),
        "confidence": {"type": "number"},
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": ["decisions", "decision_status", "source_refs", "supersedes", "confidence", "schema_version"],
    "additionalProperties": False,
}

EVIDENCE_SELECTION_FLAT_SCHEMA: JsonSchema = {
    "type": "object",
    "properties": {
        "selected_evidence_refs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"ref_id": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["ref_id", "reason"],
                "additionalProperties": False,
            },
        },
        "rejected_evidence_refs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"ref_id": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["ref_id", "reason"],
                "additionalProperties": False,
            },
        },
        "reasoning_summary": {"type": "string"},
        "missing_evidence": _string_array(),
        "confidence": {"type": "number"},
        "schema_version": _string_enum([MICRO_CONTRACT_SCHEMA_VERSION]),
    },
    "required": [
        "selected_evidence_refs",
        "rejected_evidence_refs",
        "reasoning_summary",
        "missing_evidence",
        "confidence",
        "schema_version",
    ],
    "additionalProperties": False,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run flat-schema local Gemma micro-contract probes.")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--heavy-model", default=DEFAULT_HEAVY_MODEL_NAME)
    parser.add_argument("--endpoint", default=DEFAULT_NATIVE_ENDPOINT)
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--num-predict", type=int, default=DEFAULT_NUM_PREDICT)
    parser.add_argument("--skip-heavy", action="store_true")
    parser.add_argument("--output-dir", default=str(Path.cwd() / "local_eval_reports"))
    args = parser.parse_args()

    report = run_probe_suite(
        primary_model_name=args.model,
        heavy_model_name=args.heavy_model,
        endpoint_url=args.endpoint,
        timeout_seconds=args.timeout_seconds,
        num_predict=args.num_predict,
        run_heavy_comparison=not args.skip_heavy,
    )
    path = write_report(report, output_dir=args.output_dir)
    print(path)


if __name__ == "__main__":
    main()
