"""Local Phase B soft-only proposal smoke.

This script is evaluation-only. It asks a local Ollama model to emit only a
soft-review proposal, validates a soft-only model-facing schema, and then builds
a deterministic internal envelope by combining saved Phase A/B2 state with the
soft proposal.

It does not write memory, retrieve runtime project data, call external providers,
execute tools, approve runtime behavior, or change Phase A hard-gate behavior.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_model_structured_output_probe as structured_probe
import local_phase_b_soft_review_probe as phase_b_probe


DEFAULT_SOURCE_B2_REPORT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B2")
DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_SCHEMA = Path("schemas/fast_secretary_soft_proposal_v0_1.schema.json")
DEFAULT_OUT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B3-S")
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_CASE_IDS = "HG-007,HG-018,HG-024,HG-025"
SUMMARY_JSON = "phase_b_soft_only_local_smoke_summary.json"
SUMMARY_MD = "phase_b_soft_only_local_smoke_summary.md"
MAX_CASES = 4

AUTHORITY_FIELD_NAMES = {
    "phase_a_case_id",
    "phase_a_blocked",
    "phase_a_clarification_required",
    "phase_a_external_provider_allowed",
    "phase_a_requires_manual_review",
    "can_override_phase_a",
    "recommends_external_provider",
    "recommends_retrieval",
    "requires_manual_review",
    "external_provider_allowed",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "retrieval_behavior",
    "redaction_required",
    "runtime_approved",
    "memory_write_allowed",
    "tool_execution_allowed",
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_source_results(report_dir: Path) -> dict[str, dict[str, Any]]:
    paths = sorted(report_dir.glob("*__result.json"))
    if not paths:
        raise ValueError(f"no saved result files found in {report_dir}")
    return {path.name.split("__", 1)[0]: structured_probe.load_json(path) for path in paths}


def select_case_ids(case_ids: str) -> list[str]:
    selected = [case_id.strip() for case_id in case_ids.split(",") if case_id.strip()]
    if not selected:
        raise ValueError("--case-ids did not include any case IDs")
    if len(selected) > MAX_CASES:
        raise ValueError(f"B3-S is limited to {MAX_CASES} cases")
    if len(selected) != len(set(selected)):
        raise ValueError("--case-ids contains duplicate case IDs")
    return selected


def compact_hard_envelope(phase_a: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_policy_for_future_retrieval": phase_a.get("source_policy_for_future_retrieval"),
        "allowed_future_retrieval_behavior": phase_a.get("allowed_future_retrieval_behavior"),
        "external_provider_allowed": phase_a.get("external_provider_allowed"),
        "requires_manual_review": phase_a.get("requires_manual_review"),
        "clarification_required": phase_a.get("clarification_required"),
        "redaction_required": phase_a.get("redaction_required"),
        "contains_secret_or_credential": phase_a.get("contains_secret_or_credential"),
        "contains_raw_private_or_ip_sensitive_context": phase_a.get(
            "contains_raw_private_or_ip_sensitive_context"
        ),
        "mentions_external_provider_or_upload_intent": phase_a.get(
            "mentions_external_provider_or_upload_intent"
        ),
        "hard_reason_code": phase_a.get("hard_reason_code"),
        "sensitivity_bucket_proposal": phase_a.get("sensitivity_bucket_proposal"),
    }


def build_phase_b_prompt(*, case_id: str, input_text: str) -> str:
    return "\n".join(
        [
            "You are a local-only soft-review worker.",
            "Return exactly one JSON object matching the supplied JSON Schema.",
            "Fill only the soft-review fields in the schema.",
            "Do not add policy, permission, routing, retrieval, provider, tool, or runtime fields.",
            "Do not include markdown, comments, code fences, or prose outside JSON.",
            "If exact credentials or private keys appear, describe their presence generically instead of copying literal values.",
            "",
            f"Case ID: {case_id}",
            "Input text:",
            input_text,
        ]
    )


def authority_field_leakage(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(field for field in value if field in AUTHORITY_FIELD_NAMES)


def parse_soft_proposal(raw_response: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    return structured_probe.parse_model_content(raw_response)


def build_review_envelope(
    *,
    case_id: str,
    source_result: dict[str, Any],
    soft_proposal: dict[str, Any] | None,
    proposal_validation: dict[str, Any],
    authority_leakage: list[str],
) -> dict[str, Any]:
    phase_a = phase_b_probe.corrected_phase_a_output(source_result)
    return {
        "schema_version": "fast_secretary_review_envelope_v0_1",
        "case_id": case_id,
        "soft_generation_mode": "local_model",
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "external_provider_calls_made": False,
        "local_model_calls_made": True,
        "phase_a_hard_gate": compact_hard_envelope(phase_a),
        "phase_b_soft_proposal": soft_proposal,
        "phase_b_soft_proposal_schema_valid": proposal_validation["schema_valid"],
        "phase_b_soft_proposal_validation_errors": proposal_validation["errors"],
        "authority_field_leakage": authority_leakage,
        "authority_field_leakage_count": len(authority_leakage),
    }


def build_model_result(
    *,
    case_id: str,
    source_result: dict[str, Any],
    schema: dict[str, Any],
    schema_path: Path,
    model: str,
    raw_path: Path,
    raw_call: dict[str, Any],
) -> dict[str, Any]:
    parsed, parse_error = (None, raw_call["error"])
    if raw_call["ok"] and isinstance(raw_call["body"], dict):
        parsed, parse_error = parse_soft_proposal(raw_call["body"])
    validation = structured_probe.validate_instance(parsed, schema) if parsed is not None else {
        "schema_valid": False,
        "errors": [{"field": "$", "error": "json_not_parsed"}],
    }
    leakage = authority_field_leakage(parsed)
    envelope = build_review_envelope(
        case_id=case_id,
        source_result=source_result,
        soft_proposal=parsed,
        proposal_validation=validation,
        authority_leakage=leakage,
    )
    return {
        "schema_version": "phase_b_soft_only_local_smoke_result_v0",
        "milestone": "1G-B2-F2-B3-S",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "model": model,
        "schema_path": str(schema_path),
        "raw_response_path": str(raw_path),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "phase_a_result_source": source_result.get("_source_result_path"),
        "ollama_ok": raw_call["ok"],
        "ollama_status": raw_call["status"],
        "duration_seconds": raw_call["duration_seconds"],
        "json_parse_passed": parsed is not None,
        "json_parse_error": parse_error,
        "schema_valid": validation["schema_valid"],
        "validation_errors": validation["errors"],
        "authority_field_leakage": leakage,
        "authority_field_leakage_count": len(leakage),
        "phase_b_soft_proposal": parsed,
        "review_envelope": envelope,
    }


def summarize_results(results: list[dict[str, Any]], report_dir: Path) -> dict[str, Any]:
    parse_count = sum(1 for result in results if result["json_parse_passed"])
    schema_valid_count = sum(1 for result in results if result["schema_valid"])
    leakage_results = [
        {
            "case_id": result["case_id"],
            "authority_field_leakage": result["authority_field_leakage"],
        }
        for result in results
        if result["authority_field_leakage"]
    ]
    validation_failures = [
        {
            "case_id": result["case_id"],
            "errors": result["validation_errors"],
        }
        for result in results
        if not result["schema_valid"]
    ]
    pass_structural = (
        len(results) > 0
        and parse_count == len(results)
        and schema_valid_count == len(results)
        and not leakage_results
    )
    return {
        "schema_version": "phase_b_soft_only_local_smoke_summary_v0",
        "milestone": "1G-B2-F2-B3-S",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "total_runs": len(results),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "runtime_approved": False,
        "parse_count": parse_count,
        "schema_valid_count": schema_valid_count,
        "schema_valid_all_cases": schema_valid_count == len(results),
        "validation_failures": validation_failures,
        "authority_field_leakage_count": len(leakage_results),
        "authority_field_leakage": leakage_results,
        "model_facing_schema": "fast_secretary_soft_proposal_v0_1.schema.json",
        "model_facing_schema_has_authority_fields": False,
        "local_ollama_calls_made": True,
        "external_provider_calls_made": False,
        "network_calls_made": False,
        "accepted_for_runtime": False,
        "strong_enough_for_expanded_phase_b_panel": pass_structural,
        "recommended_next_milestone": (
            "1G-B2-F2-B4 - Phase B expanded local soft-review panel"
            if pass_structural
            else "1G-B2-F2-B3-S-R - Phase B soft-only schema repair"
        ),
        "answers": {
            "parseable_json_all_cases": parse_count == len(results),
            "schema_valid_all_cases": schema_valid_count == len(results),
            "authority_field_leakage_count": len(leakage_results),
            "model_facing_schema_has_authority_fields": False,
            "runtime_approved": False,
            "external_provider_calls_made": False,
            "strong_enough_for_expanded_phase_b_panel": pass_structural,
        },
    }


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# 1G-B2-F2-B3-S Phase B Soft-Only Local Smoke Summary",
        "",
        "Manual review is required. This smoke does not prove semantic truth or approve runtime use.",
        "",
        f"- total runs: {summary['total_runs']}",
        f"- parse: {summary['parse_count']}/{summary['total_runs']}",
        f"- schema valid: {summary['schema_valid_count']}/{summary['total_runs']}",
        f"- authority field leakage count: {summary['authority_field_leakage_count']}",
        f"- model-facing schema has authority fields: {summary['model_facing_schema_has_authority_fields']}",
        f"- local Ollama calls made: {summary['local_ollama_calls_made']}",
        f"- external provider calls made: {summary['external_provider_calls_made']}",
        f"- runtime approved: {summary['runtime_approved']}",
        f"- strong enough for expanded Phase B panel: {summary['strong_enough_for_expanded_phase_b_panel']}",
        f"- recommended next milestone: {summary['recommended_next_milestone']}",
        "",
        "Qwen receives only the soft-only proposal schema and the input text. Phase A hard fields are merged later by deterministic Python into an internal review envelope.",
        "",
        "No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_local_smoke(
    *,
    source_b2_report_dir: Path,
    holdout_path: Path,
    schema_path: Path,
    out_dir: Path,
    model: str,
    case_ids: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be greater than 0")
    selected_case_ids = select_case_ids(case_ids)
    source_results = load_source_results(source_b2_report_dir)
    holdout = phase_b_probe.load_holdout_cases(holdout_path)
    schema = structured_probe.load_json(schema_path)
    structured_probe.validate_schema_shape(schema)
    if authority_field_leakage(schema.get("properties", {})):
        raise ValueError("model-facing soft proposal schema contains authority fields")
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for case_id in selected_case_ids:
        if case_id not in source_results:
            raise ValueError(f"missing source B2 result for {case_id}")
        if case_id not in holdout:
            raise ValueError(f"missing holdout input for {case_id}")
        source_result = dict(source_results[case_id])
        source_result["_source_result_path"] = str(source_b2_report_dir / f"{case_id}__result.json")
        prompt = build_phase_b_prompt(
            case_id=case_id,
            input_text=holdout[case_id]["input_text"],
        )
        raw_call = structured_probe.call_ollama_chat(
            model=model,
            prompt=prompt,
            schema=schema,
            timeout_seconds=timeout_seconds,
        )
        raw_path = out_dir / f"{case_id}__phase_b_soft_only_raw_response.json"
        result_path = out_dir / f"{case_id}__phase_b_soft_only_result.json"
        write_json(raw_path, raw_call)
        result = build_model_result(
            case_id=case_id,
            source_result=source_result,
            schema=schema,
            schema_path=schema_path,
            model=model,
            raw_path=raw_path,
            raw_call=raw_call,
        )
        write_json(result_path, result)
        results.append(result)
        print(
            f"{model} {case_id}: "
            f"parse={result['json_parse_passed']} "
            f"schema_valid={result['schema_valid']} "
            f"authority_leakage={result['authority_field_leakage_count']} "
            f"duration={result['duration_seconds']}"
        )

    summary = summarize_results(results, out_dir)
    write_json(out_dir / SUMMARY_JSON, summary)
    write_summary_markdown(out_dir / SUMMARY_MD, summary)
    print(f"summary json: {out_dir / SUMMARY_JSON}")
    print(f"summary md: {out_dir / SUMMARY_MD}")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase B soft-only local structured-output smoke.")
    parser.add_argument("--source-b2-report-dir", default=str(DEFAULT_SOURCE_B2_REPORT_DIR))
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--schema-path", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--case-ids", default=DEFAULT_CASE_IDS)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--run-local", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        if not args.run_local:
            raise ValueError("--run-local is required")
        run_local_smoke(
            source_b2_report_dir=Path(args.source_b2_report_dir),
            holdout_path=Path(args.holdout),
            schema_path=Path(args.schema_path),
            out_dir=Path(args.out_dir),
            model=args.model,
            case_ids=args.case_ids,
            timeout_seconds=args.timeout_seconds,
        )
        return 0
    except ValueError as exc:
        print(f"phase b soft-only local smoke failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
