"""Local Phase B soft-only proposal smoke and expanded panel.

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
DEFAULT_OUT_DIR = Path("reports/local_model_smoke/1G-B2-F2-B4")
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_CASE_IDS = "HG-007,HG-010,HG-013,HG-016,HG-017,HG-018,HG-024,HG-025"
SUMMARY_JSON = "phase_b_expanded_local_soft_review_panel_summary.json"
SUMMARY_MD = "phase_b_expanded_local_soft_review_panel_summary.md"
MAX_CASES = 8

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

SOFT_QUALITY_EXPECTATIONS = {
    "HG-007": {
        "project_bucket_any": ["bluerev"],
        "primary_domain_any": ["retrieval", "bioprocess", "modeling"],
        "domain_tag_any": ["literature", "source", "photobioreactors", "gas-liquid", "kla"],
        "soft_reason_code_any": ["source_candidate", "assumption_candidate", "contextual_summary"],
    },
    "HG-010": {
        "soft_reason_code_any": ["clarification_context", "contextual_summary", "unknown"],
        "followup_question_required": True,
    },
    "HG-013": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory"],
        "soft_reason_code_any": ["clarification_context", "memory_candidate", "contextual_summary", "unknown"],
        "followup_question_required": True,
    },
    "HG-016": {
        "primary_domain_any": ["security"],
        "possible_memory_card_type_any": ["none", "decision_card"],
        "storage_relevance_not": ["high"],
    },
    "HG-017": {
        "primary_domain_any": ["security"],
        "possible_memory_card_type_any": ["none", "decision_card"],
        "storage_relevance_not": ["high"],
    },
    "HG-018": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory", "security", "local_ai"],
        "domain_tag_any": ["memory", "provider", "privacy", "security", "jarvisos"],
        "project_bucket_not": ["unknown"],
        "primary_domain_not": ["unknown"],
    },
    "HG-024": {
        "project_bucket_any": ["jarvisos"],
        "primary_domain_any": ["memory", "local_ai"],
        "possible_memory_card_type_any": ["decision_card", "memory_card"],
        "project_bucket_not": ["coursework", "personal", "unknown"],
    },
    "HG-025": {
        "primary_domain_any": ["memory"],
        "soft_reason_code_any": ["clarification_context", "memory_candidate", "contextual_summary"],
        "followup_question_required": True,
        "project_bucket_not": ["personal"],
    },
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
        raise ValueError(f"Phase B expanded panel is limited to {MAX_CASES} cases")
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


def normalized(value: Any) -> str:
    return str(value).strip().lower()


def contains_any_text(value: Any, options: list[str]) -> bool:
    text = normalized(value)
    return any(normalized(option) in text for option in options)


def list_contains_any(values: Any, options: list[str]) -> bool:
    if not isinstance(values, list):
        return False
    return any(contains_any_text(item, options) for item in values)


def evaluate_soft_quality(case_id: str, proposal: Any) -> dict[str, Any]:
    """Return advisory quality diagnostics only.

    These checks are intentionally not runtime authority. They help decide
    whether the soft proposals are worth semantic review in the next milestone.
    """
    if not isinstance(proposal, dict):
        return {
            "case_id": case_id,
            "quality_compared": False,
            "quality_match_count": 0,
            "quality_compared_count": 0,
            "quality_misses": [{"field": "$", "reason": "soft proposal is not an object"}],
        }
    expectation = SOFT_QUALITY_EXPECTATIONS.get(case_id, {})
    misses: list[dict[str, Any]] = []
    compared = 0
    matched = 0

    def check_any(field: str, expected_values: list[str]) -> None:
        nonlocal compared, matched
        compared += 1
        actual = proposal.get(field)
        ok = normalized(actual) in {normalized(value) for value in expected_values}
        if ok:
            matched += 1
        else:
            misses.append(
                {
                    "field": field,
                    "actual": actual,
                    "expected_any": expected_values,
                    "reason": "advisory soft-quality expectation miss",
                }
            )

    def check_not(field: str, forbidden_values: list[str]) -> None:
        nonlocal compared, matched
        compared += 1
        actual = proposal.get(field)
        ok = normalized(actual) not in {normalized(value) for value in forbidden_values}
        if ok:
            matched += 1
        else:
            misses.append(
                {
                    "field": field,
                    "actual": actual,
                    "forbidden": forbidden_values,
                    "reason": "advisory soft-quality forbidden value",
                }
            )

    if "project_bucket_any" in expectation:
        check_any("project_bucket", expectation["project_bucket_any"])
    if "project_bucket_not" in expectation:
        check_not("project_bucket", expectation["project_bucket_not"])
    if "primary_domain_any" in expectation:
        check_any("primary_domain", expectation["primary_domain_any"])
    if "primary_domain_not" in expectation:
        check_not("primary_domain", expectation["primary_domain_not"])
    if "soft_reason_code_any" in expectation:
        check_any("soft_reason_code", expectation["soft_reason_code_any"])
    if "possible_memory_card_type_any" in expectation:
        check_any("possible_memory_card_type", expectation["possible_memory_card_type_any"])
    if "storage_relevance_not" in expectation:
        check_not("storage_relevance", expectation["storage_relevance_not"])
    if "domain_tag_any" in expectation:
        compared += 1
        if list_contains_any(proposal.get("domain_tags"), expectation["domain_tag_any"]):
            matched += 1
        else:
            misses.append(
                {
                    "field": "domain_tags",
                    "actual": proposal.get("domain_tags"),
                    "expected_any_substring": expectation["domain_tag_any"],
                    "reason": "advisory soft-quality missing useful tag",
                }
            )
    if expectation.get("followup_question_required"):
        compared += 1
        actual = proposal.get("suggested_followup_question")
        if isinstance(actual, str) and actual.strip():
            matched += 1
        else:
            misses.append(
                {
                    "field": "suggested_followup_question",
                    "actual": actual,
                    "expected": "non-empty question",
                    "reason": "ambiguous case should suggest a clarification question",
                }
            )

    return {
        "case_id": case_id,
        "quality_compared": compared > 0,
        "quality_match_count": matched,
        "quality_compared_count": compared,
        "quality_misses": misses,
    }


def build_review_envelope(
    *,
    case_id: str,
    source_result: dict[str, Any],
    soft_proposal: dict[str, Any] | None,
    proposal_validation: dict[str, Any],
    authority_leakage: list[str],
    soft_quality: dict[str, Any],
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
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "soft_quality_diagnostic": soft_quality,
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
    soft_quality = evaluate_soft_quality(case_id, parsed)
    envelope = build_review_envelope(
        case_id=case_id,
        source_result=source_result,
        soft_proposal=parsed,
        proposal_validation=validation,
        authority_leakage=leakage,
        soft_quality=soft_quality,
    )
    return {
        "schema_version": "phase_b_soft_only_local_smoke_result_v0",
        "milestone": "1G-B2-F2-B4",
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
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "soft_quality_diagnostic": soft_quality,
        "review_envelope": envelope,
    }


def soft_quality_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    compared = 0
    matched = 0
    cases_with_misses: list[dict[str, Any]] = []
    for result in results:
        diagnostic = result.get("soft_quality_diagnostic") or {}
        compared += diagnostic.get("quality_compared_count", 0)
        matched += diagnostic.get("quality_match_count", 0)
        misses = diagnostic.get("quality_misses", [])
        if misses:
            cases_with_misses.append({"case_id": result["case_id"], "misses": misses})
    miss_count = compared - matched
    return {
        "soft_quality_review_required": True,
        "soft_quality_truth_scored": False,
        "soft_quality_match_count": matched,
        "soft_quality_compared_count": compared,
        "soft_quality_miss_count": miss_count,
        "soft_quality_match_rate": matched / compared if compared else None,
        "cases_with_soft_quality_misses": cases_with_misses,
        "note": "Diagnostic only: soft-quality checks do not approve runtime behavior or semantic truth.",
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
    quality = soft_quality_summary(results)
    pass_structural = (
        len(results) > 0
        and parse_count == len(results)
        and schema_valid_count == len(results)
        and not leakage_results
    )
    return {
        "schema_version": "phase_b_expanded_local_soft_review_panel_summary_v0",
        "milestone": "1G-B2-F2-B4",
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
        "strong_enough_for_semantic_quality_review": pass_structural,
        "strong_enough_for_runtime": False,
        "soft_quality_summary": quality,
        "recommended_next_milestone": (
            "1G-B2-F2-B5 - Phase B semantic quality review"
            if pass_structural
            else "1G-B2-F2-B4-R - Phase B expanded local soft-review panel repair"
        ),
        "answers": {
            "parseable_json_all_cases": parse_count == len(results),
            "schema_valid_all_cases": schema_valid_count == len(results),
            "authority_field_leakage_count": len(leakage_results),
            "model_facing_schema_has_authority_fields": False,
            "runtime_approved": False,
            "external_provider_calls_made": False,
            "soft_quality_review_required": True,
            "soft_quality_truth_scored": False,
            "strong_enough_for_semantic_quality_review": pass_structural,
        },
    }


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    quality = summary["soft_quality_summary"]
    lines = [
        "# 1G-B2-F2-B4 Phase B Expanded Local Soft-Review Panel Summary",
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
        f"- soft quality review required: {quality['soft_quality_review_required']}",
        f"- soft quality truth scored: {quality['soft_quality_truth_scored']}",
        f"- soft quality diagnostic: {quality['soft_quality_match_count']}/{quality['soft_quality_compared_count']}",
        f"- soft quality miss count: {quality['soft_quality_miss_count']}",
        f"- strong enough for semantic quality review: {summary['strong_enough_for_semantic_quality_review']}",
        f"- recommended next milestone: {summary['recommended_next_milestone']}",
        "",
        "Qwen receives only the soft-only proposal schema and the input text. Phase A hard fields are merged later by deterministic Python into an internal review envelope.",
        "",
        "Soft-quality diagnostics are advisory only. They do not approve runtime behavior, memory writes, retrieval, provider use, tool execution, or semantic truth.",
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
        quality = result["soft_quality_diagnostic"]
        print(
            f"{model} {case_id}: "
            f"parse={result['json_parse_passed']} "
            f"schema_valid={result['schema_valid']} "
            f"authority_leakage={result['authority_field_leakage_count']} "
            f"soft_quality={quality['quality_match_count']}/{quality['quality_compared_count']} "
            f"duration={result['duration_seconds']}"
        )

    summary = summarize_results(results, out_dir)
    write_json(out_dir / SUMMARY_JSON, summary)
    write_summary_markdown(out_dir / SUMMARY_MD, summary)
    print(f"summary json: {out_dir / SUMMARY_JSON}")
    print(f"summary md: {out_dir / SUMMARY_MD}")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase B expanded local soft-review panel.")
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
        print(f"phase b expanded local panel failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
