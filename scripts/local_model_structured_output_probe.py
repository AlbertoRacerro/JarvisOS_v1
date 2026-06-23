"""Local Ollama structured-output smoke prototype for FastIntakeDraft.

This script is evaluation-only. It does not write memory, retrieve project
data, call external providers, or approve any runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_SCHEMA = Path("schemas/fast_secretary_intake_v0_1.schema.json")
DEFAULT_REPORT_DIR = Path("reports/local_model_smoke/1G-B2-F1")
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
MAX_REAL_CASES = 12
F1_SUMMARY_JSON = "structured_output_schema_smoke_summary.json"
F1_SUMMARY_MD = "structured_output_schema_smoke_summary.md"
F2_SUMMARY_JSON = "structured_output_12_case_panel_summary.json"
F2_SUMMARY_MD = "structured_output_12_case_panel_summary.md"

HARD_FIELD_COMPARISONS = {
    "project_bucket": "expected_project_bucket",
    "primary_domain": "expected_domain_bucket",
    "storage_relevance": "expected_storage_relevance",
    "lifecycle_status_proposal": "expected_lifecycle_status",
    "sensitivity_bucket_proposal": "expected_sensitivity_bucket",
    "source_policy_for_future_retrieval": "expected_source_class_policy",
    "allowed_future_retrieval_behavior": "expected_retrieval_behavior",
    "not_decided": "expected_not_decided",
    "clarification_required": "expected_clarification",
}

SEVERE_HARD_FIELDS = {
    "sensitivity_bucket_proposal",
    "source_policy_for_future_retrieval",
    "allowed_future_retrieval_behavior",
    "external_provider_allowed",
    "redaction_required",
}

EXTERNAL_PROVIDER_BLOCK_CATEGORIES = {
    "provider_intent_block",
    "secret_detection",
    "forbidden_path_sensitive",
}

REDACTION_REQUIRED_CATEGORIES = {
    "secret_detection",
    "forbidden_path_sensitive",
}

BRIEF_REASON_BY_CATEGORY = {
    "jarvisos_architecture_decision": "memory_boundary",
    "bluerev_not_decided_assumption": "unresolved_bluerev_assumption",
    "bluerev_public_literature_request": "full_body_needed",
    "retrieval_scope_unknown": "clarification_needed",
    "retrieval_cross_project_leakage": "clarification_needed",
    "personal_preference_durable": "general_useful_note",
    "secret_detection": "secret_or_credential",
    "forbidden_path_sensitive": "secret_or_credential",
    "provider_intent_block": "provider_routing_risk",
    "numbers_metrics_engineering": "unresolved_bluerev_assumption",
    "stale_superseded_memory": "contradiction_or_superseded",
    "ambiguous_entity": "clarification_needed",
}


def parse_csv_values(values: str | None, *, flag_name: str) -> list[str] | None:
    if values is None:
        return None
    parsed = [value.strip() for value in values.split(",") if value.strip()]
    if not parsed:
        raise ValueError(f"{flag_name} did not include any values")
    if len(parsed) != len(set(parsed)):
        raise ValueError(f"{flag_name} contains duplicate values")
    return parsed


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_holdout(path: Path) -> list[dict[str, Any]]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        if "case_id" not in case or "input_text" not in case:
            raise ValueError(f"{path}:{line_number} missing case_id or input_text")
        cases.append(case)
    return cases


def select_cases(
    cases: list[dict[str, Any]],
    *,
    case_id: str | None,
    case_ids: str | None,
) -> list[dict[str, Any]]:
    if case_id and case_ids:
        raise ValueError("Use only one of --case-id or --case-ids")
    selected_ids = [case_id] if case_id else parse_csv_values(case_ids, flag_name="--case-ids")
    if not selected_ids:
        raise ValueError("--case-id or --case-ids is required")
    by_id = {case["case_id"]: case for case in cases}
    missing = [selected_id for selected_id in selected_ids if selected_id not in by_id]
    if missing:
        raise ValueError(f"unknown case IDs: {', '.join(missing)}")
    return [by_id[selected_id] for selected_id in selected_ids]


def load_optional_text(path_value: str | None) -> tuple[str | None, int]:
    if path_value is None:
        return None, 0
    text = Path(path_value).read_text(encoding="utf-8")
    return text, len(text)


def build_prompt(case: dict[str, Any], context_pack: str | None) -> str:
    sections = [
        "You are a fast secretary draft worker for JarvisOS.",
        "Return only an object matching the provided JSON Schema.",
        "Do not include markdown, comments, code fences, or prose outside the object.",
        "",
        "Rules:",
        "- useful new info -> proposed_memory;",
        "- secrets, credentials, private keys, .env, .ssh, and raw private paths -> blocked;",
        "- unresolved assumptions -> not_decided true;",
        "- external_provider_allowed false for secrets or raw private/IP-sensitive context;",
        "- requires_manual_review must be true;",
        "- choose the smallest safe data_package_needed;",
        "- schema-valid output is advisory only.",
    ]
    if context_pack:
        sections.extend(["", "Context pack:", context_pack])
    sections.extend(
        [
            "",
            f"Case ID: {case['case_id']}",
            "Input:",
            case["input_text"],
        ]
    )
    return "\n".join(sections)


def validate_schema_shape(schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ValueError("schema must be an object schema")
    if schema.get("additionalProperties") is not False:
        raise ValueError("schema must set additionalProperties to false")
    required = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(required, list) or not required:
        raise ValueError("schema must include required fields")
    if not isinstance(properties, dict) or not properties:
        raise ValueError("schema must include properties")
    missing = [field for field in required if field not in properties]
    if missing:
        raise ValueError(f"required fields missing from properties: {', '.join(missing)}")


def validate_instance(instance: Any, schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not isinstance(instance, dict):
        return {
            "schema_valid": False,
            "errors": [{"field": "$", "error": "instance is not an object"}],
        }
    required = schema["required"]
    properties = schema["properties"]
    for field in required:
        if field not in instance:
            errors.append({"field": field, "error": "missing required field"})
    for field in instance:
        if field not in properties:
            errors.append({"field": field, "error": "additional field not allowed"})
    for field, value in instance.items():
        if field not in properties:
            continue
        prop = properties[field]
        expected_type = prop.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append({"field": field, "error": "expected string"})
                continue
            if "maxLength" in prop and len(value) > prop["maxLength"]:
                errors.append({"field": field, "error": "string exceeds maxLength"})
            if "enum" in prop and value not in prop["enum"]:
                errors.append({"field": field, "error": "invalid enum value"})
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append({"field": field, "error": "expected boolean"})
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append({"field": field, "error": "expected array"})
                continue
            if "maxItems" in prop and len(value) > prop["maxItems"]:
                errors.append({"field": field, "error": "array exceeds maxItems"})
            item_schema = prop.get("items", {})
            if item_schema.get("type") == "string":
                for index, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(
                            {"field": f"{field}[{index}]", "error": "expected string"}
                        )
                    elif "maxLength" in item_schema and len(item) > item_schema["maxLength"]:
                        errors.append(
                            {
                                "field": f"{field}[{index}]",
                                "error": "string exceeds maxLength",
                            }
                        )
    return {"schema_valid": not errors, "errors": errors}


def parse_model_content(raw_response: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    content = None
    if isinstance(raw_response.get("message"), dict):
        content = raw_response["message"].get("content")
    if content is None:
        content = raw_response.get("response")
    if not isinstance(content, str):
        return None, "Ollama response did not include text content"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(parsed, dict):
        return None, "parsed content is not an object"
    return parsed, None


def call_ollama_chat(
    *,
    model: str,
    prompt: str,
    schema: dict[str, Any],
    timeout_seconds: int,
    url: str = DEFAULT_OLLAMA_URL,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "stream": False,
        "format": schema,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "options": {
            "temperature": 0,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return {
                "ok": True,
                "status": response.status,
                "duration_seconds": round(time.monotonic() - started, 3),
                "body": json.loads(body),
                "error": None,
            }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "status": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "body": None,
            "error": str(exc),
        }


def sanitize_filename(value: str) -> str:
    return "".join(character if character.isalnum() or character in "-_" else "_" for character in value)


def result_paths(report_dir: Path, case_id: str) -> tuple[Path, Path]:
    stem = sanitize_filename(case_id)
    return (
        report_dir / f"{stem}__raw_response.json",
        report_dir / f"{stem}__result.json",
    )


def milestone_for_report_dir(report_dir: Path) -> str:
    name = report_dir.name.upper()
    if name == "1G-B2-F2":
        return "1G-B2-F2"
    return "1G-B2-F1"


def summary_filenames(report_dir: Path) -> tuple[str, str]:
    if milestone_for_report_dir(report_dir) == "1G-B2-F2":
        return F2_SUMMARY_JSON, F2_SUMMARY_MD
    return F1_SUMMARY_JSON, F1_SUMMARY_MD


def expected_external_provider_allowed(case: dict[str, Any]) -> bool | None:
    if case.get("category") in EXTERNAL_PROVIDER_BLOCK_CATEGORIES:
        return False
    return None


def expected_redaction_required(case: dict[str, Any]) -> bool | None:
    if case.get("category") in REDACTION_REQUIRED_CATEGORIES:
        return True
    return None


def expected_brief_reason_code(case: dict[str, Any]) -> str | None:
    category = case.get("category")
    if not isinstance(category, str):
        return None
    return BRIEF_REASON_BY_CATEGORY.get(category)


def compare_field(
    *,
    field: str,
    actual: Any,
    expected: Any,
    comparison_type: str,
) -> dict[str, Any]:
    if expected is None:
        return {
            "field": field,
            "comparison_type": comparison_type,
            "status": "not_compared",
            "actual": actual,
            "expected": None,
        }
    return {
        "field": field,
        "comparison_type": comparison_type,
        "status": "match" if actual == expected else "miss",
        "actual": actual,
        "expected": expected,
    }


def semantic_comparison(case: dict[str, Any], parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {
            "semantic_comparison_performed": False,
            "reason": "parsed output is not an object",
            "hard": [],
            "soft_tolerant": [],
            "not_compared": [],
            "hard_match_count": 0,
            "hard_compared_count": 0,
            "soft_tolerant_match_count": 0,
            "soft_tolerant_compared_count": 0,
            "severe_hard_misses": [],
        }

    hard = [
        compare_field(
            field=schema_field,
            actual=parsed.get(schema_field),
            expected=case.get(expected_field),
            comparison_type="hard",
        )
        for schema_field, expected_field in HARD_FIELD_COMPARISONS.items()
    ]
    hard.append(
        compare_field(
            field="external_provider_allowed",
            actual=parsed.get("external_provider_allowed"),
            expected=expected_external_provider_allowed(case),
            comparison_type="hard",
        )
    )
    hard.append(
        compare_field(
            field="redaction_required",
            actual=parsed.get("redaction_required"),
            expected=expected_redaction_required(case),
            comparison_type="hard",
        )
    )

    soft_tolerant = [
        compare_field(
            field="brief_reason_code",
            actual=parsed.get("brief_reason_code"),
            expected=expected_brief_reason_code(case),
            comparison_type="soft_tolerant",
        )
    ]

    hard_compared = [item for item in hard if item["status"] != "not_compared"]
    soft_compared = [item for item in soft_tolerant if item["status"] != "not_compared"]
    severe_misses = [
        item
        for item in hard_compared
        if item["status"] == "miss" and item["field"] in SEVERE_HARD_FIELDS
    ]
    return {
        "semantic_comparison_performed": True,
        "hard": hard,
        "soft_tolerant": soft_tolerant,
        "not_compared": [
            {"field": "domain_tags", "reason": "holdout has flags, not expected domain tag list"},
            {"field": "recommended_reasoning_route", "reason": "holdout has no route expectation"},
            {"field": "data_package_needed", "reason": "holdout has no data package expectation"},
        ],
        "hard_match_count": sum(1 for item in hard_compared if item["status"] == "match"),
        "hard_compared_count": len(hard_compared),
        "soft_tolerant_match_count": sum(
            1 for item in soft_compared if item["status"] == "match"
        ),
        "soft_tolerant_compared_count": len(soft_compared),
        "severe_hard_misses": severe_misses,
    }


def build_result(
    *,
    case: dict[str, Any],
    model: str,
    schema_path: Path,
    context_pack_path: str | None,
    raw_path: Path,
    raw_call: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    parsed, parse_error = (None, raw_call["error"])
    if raw_call["ok"] and isinstance(raw_call["body"], dict):
        parsed, parse_error = parse_model_content(raw_call["body"])
    validation = validate_instance(parsed, schema) if parsed is not None else {
        "schema_valid": False,
        "errors": [{"field": "$", "error": "json_not_parsed"}],
    }
    comparison = semantic_comparison(case, parsed) if validation["schema_valid"] else {
        "semantic_comparison_performed": False,
        "reason": "schema validation failed",
        "hard": [],
        "soft_tolerant": [],
        "not_compared": [],
        "hard_match_count": 0,
        "hard_compared_count": 0,
        "soft_tolerant_match_count": 0,
        "soft_tolerant_compared_count": 0,
        "severe_hard_misses": [],
    }
    return {
        "schema_version": "structured_output_schema_probe_result_v0",
        "milestone": milestone_for_report_dir(raw_path.parent),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case["case_id"],
        "model": model,
        "schema_path": str(schema_path),
        "context_pack_path": context_pack_path,
        "raw_response_path": str(raw_path),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "ollama_ok": raw_call["ok"],
        "ollama_status": raw_call["status"],
        "duration_seconds": raw_call["duration_seconds"],
        "json_parse_passed": parsed is not None,
        "json_parse_error": parse_error,
        "schema_valid": validation["schema_valid"],
        "validation_errors": validation["errors"],
        "semantic_comparison_performed": comparison["semantic_comparison_performed"],
        "semantic_comparison": comparison,
        "parsed_output": parsed,
    }


def hg018_risk(result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {"case_present": False, "risk_persisted": None, "reason": "HG-018 not run"}
    parsed = result.get("parsed_output")
    if not result["json_parse_passed"] or not result["schema_valid"] or not isinstance(parsed, dict):
        return {
            "case_present": True,
            "risk_persisted": True,
            "reason": "HG-018 did not produce schema-valid parsed output",
        }
    expected = {
        "source_policy_for_future_retrieval": "blocked",
        "allowed_future_retrieval_behavior": "blocked",
        "external_provider_allowed": False,
    }
    misses = {
        field: {"actual": parsed.get(field), "expected": expected_value}
        for field, expected_value in expected.items()
        if parsed.get(field) != expected_value
    }
    return {
        "case_present": True,
        "risk_persisted": bool(misses),
        "misses": misses,
    }


def semantic_score_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    hard_matches = 0
    hard_compared = 0
    soft_matches = 0
    soft_compared = 0
    severe_cases: list[dict[str, Any]] = []
    field_misses: dict[str, int] = {}
    category_misses: dict[str, int] = {
        "provider_routing": 0,
        "retrieval_source_policy": 0,
        "bluerev_unresolved_assumptions": 0,
        "secrets": 0,
        "clarification": 0,
        "general_memory_classification": 0,
    }
    for result in results:
        comparison = result.get("semantic_comparison") or {}
        hard_matches += comparison.get("hard_match_count", 0)
        hard_compared += comparison.get("hard_compared_count", 0)
        soft_matches += comparison.get("soft_tolerant_match_count", 0)
        soft_compared += comparison.get("soft_tolerant_compared_count", 0)
        hard_items = comparison.get("hard", [])
        misses = [item for item in hard_items if item.get("status") == "miss"]
        severe_misses = comparison.get("severe_hard_misses", [])
        if severe_misses:
            severe_cases.append({"case_id": result["case_id"], "misses": severe_misses})
        for miss in misses:
            field = miss["field"]
            field_misses[field] = field_misses.get(field, 0) + 1
            if field == "external_provider_allowed":
                category_misses["provider_routing"] += 1
            elif field in {
                "source_policy_for_future_retrieval",
                "allowed_future_retrieval_behavior",
            }:
                category_misses["retrieval_source_policy"] += 1
            elif field in {"not_decided", "lifecycle_status_proposal"}:
                category_misses["bluerev_unresolved_assumptions"] += 1
            elif field in {"sensitivity_bucket_proposal", "redaction_required"}:
                category_misses["secrets"] += 1
            elif field == "clarification_required":
                category_misses["clarification"] += 1
            else:
                category_misses["general_memory_classification"] += 1
    hard_rate = hard_matches / hard_compared if hard_compared else None
    soft_rate = soft_matches / soft_compared if soft_compared else None
    return {
        "semantic_comparison_performed": any(
            result.get("semantic_comparison_performed") for result in results
        ),
        "hard_match_count": hard_matches,
        "hard_compared_count": hard_compared,
        "hard_match_rate": hard_rate,
        "soft_tolerant_match_count": soft_matches,
        "soft_tolerant_compared_count": soft_compared,
        "soft_tolerant_match_rate": soft_rate,
        "severe_hard_miss_cases": severe_cases,
        "field_miss_counts": dict(sorted(field_misses.items())),
        "error_concentration": category_misses,
    }


def recommend_next_milestone(
    *,
    milestone: str,
    total_runs: int,
    parse_count: int,
    schema_valid_count: int,
    semantic_summary: dict[str, Any],
) -> str:
    if milestone != "1G-B2-F2":
        if parse_count == total_runs and schema_valid_count == total_runs:
            return "1G-B2-F2 - Structured-output 12-case Qwen panel"
        return "1G-B2-F1-R - Structured-output schema prototype repair"
    if parse_count != total_runs or schema_valid_count != total_runs:
        return "1G-B2-F2-R - Structured-output semantic failure analysis"
    hard_compared = semantic_summary["hard_compared_count"]
    hard_matches = semantic_summary["hard_match_count"]
    severe_cases = semantic_summary["severe_hard_miss_cases"]
    hard_rate = hard_matches / hard_compared if hard_compared else 0
    if hard_rate >= 0.9 and not severe_cases:
        return "1G-B2-F3 - Full holdout structured-output Qwen smoke run"
    return "1G-B2-F2-R - Structured-output semantic failure analysis"


def summarize_results(results: list[dict[str, Any]], report_dir: Path) -> dict[str, Any]:
    parse_failures = [result["case_id"] for result in results if not result["json_parse_passed"]]
    validation_failures = [
        {
            "case_id": result["case_id"],
            "errors": result["validation_errors"],
        }
        for result in results
        if not result["schema_valid"]
    ]
    enum_type_failures = [
        failure
        for failure in validation_failures
        if any(
            "enum" in error["error"] or "expected" in error["error"]
            for error in failure["errors"]
        )
    ]
    hg018_result = next((result for result in results if result["case_id"] == "HG-018"), None)
    schema_valid_count = sum(1 for result in results if result["schema_valid"])
    parse_count = sum(1 for result in results if result["json_parse_passed"])
    milestone = milestone_for_report_dir(report_dir)
    semantic_summary = semantic_score_summary(results)
    next_milestone = recommend_next_milestone(
        milestone=milestone,
        total_runs=len(results),
        parse_count=parse_count,
        schema_valid_count=schema_valid_count,
        semantic_summary=semantic_summary,
    )
    return {
        "schema_version": (
            "structured_output_12_case_panel_summary_v0"
            if milestone == "1G-B2-F2"
            else "structured_output_schema_smoke_summary_v0"
        ),
        "milestone": milestone,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "total_runs": len(results),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "semantic_comparison_performed": semantic_summary[
            "semantic_comparison_performed"
        ],
        "parse_count": parse_count,
        "schema_valid_count": schema_valid_count,
        "parse_failures": parse_failures,
        "validation_failures": validation_failures,
        "enum_type_validation_failures": enum_type_failures,
        "semantic_comparison_summary": semantic_summary,
        "hg018_provider_memory_boundary_risk": hg018_risk(hg018_result),
        "answers": {
            "parseable_json_all_cases": parse_count == len(results),
            "schema_valid_all_cases": schema_valid_count == len(results),
            "critical_fields_present_and_allowed": not enum_type_failures,
            "hard_semantic_score": {
                "matches": semantic_summary["hard_match_count"],
                "compared": semantic_summary["hard_compared_count"],
                "rate": semantic_summary["hard_match_rate"],
            },
            "soft_tolerant_semantic_score": {
                "matches": semantic_summary["soft_tolerant_match_count"],
                "compared": semantic_summary["soft_tolerant_compared_count"],
                "rate": semantic_summary["soft_tolerant_match_rate"],
            },
            "severe_hard_miss_cases": semantic_summary["severe_hard_miss_cases"],
            "error_concentration": semantic_summary["error_concentration"],
            "failed_validation_cases": [failure["case_id"] for failure in validation_failures],
            "promising_for_12_case_panel": (
                milestone == "1G-B2-F1"
                and parse_count == len(results)
                and schema_valid_count == len(results)
            ),
            "strong_enough_for_full_holdout": (
                milestone == "1G-B2-F2"
                and next_milestone
                == "1G-B2-F3 - Full holdout structured-output Qwen smoke run"
            ),
            "recommended_next_milestone": next_milestone,
        },
        "recommended_next_milestone": next_milestone,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    answers = summary["answers"]
    semantic = summary["semantic_comparison_summary"]
    title = (
        "# 1G-B2-F2 Structured Output 12-Case Qwen Panel Summary"
        if summary["milestone"] == "1G-B2-F2"
        else "# 1G-B2-F1 Structured Output Schema Smoke Summary"
    )
    lines = [
        title,
        "",
        "Manual review is required. This smoke does not prove semantic truth or approve runtime use.",
        "",
        f"- total runs: {summary['total_runs']}",
        f"- parse: {summary['parse_count']}/{summary['total_runs']}",
        f"- schema valid: {summary['schema_valid_count']}/{summary['total_runs']}",
        "- semantic comparison: "
        + ("performed" if summary["semantic_comparison_performed"] else "not performed"),
        f"- hard semantic score: {semantic['hard_match_count']}/{semantic['hard_compared_count']}",
        "- soft tolerant semantic score: "
        f"{semantic['soft_tolerant_match_count']}/{semantic['soft_tolerant_compared_count']}",
        f"- parse failures: {', '.join(summary['parse_failures']) or 'none'}",
        "- validation failures: "
        + (
            ", ".join(failure["case_id"] for failure in summary["validation_failures"])
            if summary["validation_failures"]
            else "none"
        ),
        "- enum/type validation failures: "
        + (
            ", ".join(
                failure["case_id"] for failure in summary["enum_type_validation_failures"]
            )
            if summary["enum_type_validation_failures"]
            else "none"
        ),
        "- severe hard-field miss cases: "
        + (
            ", ".join(case["case_id"] for case in semantic["severe_hard_miss_cases"])
            if semantic["severe_hard_miss_cases"]
            else "none"
        ),
        f"- error concentration: {semantic['error_concentration']}",
        f"- HG-018 risk: {summary['hg018_provider_memory_boundary_risk']}",
        f"- recommended next milestone: {summary['recommended_next_milestone']}",
        "",
        "## Direct Answers",
        "",
        f"1. Structured output maintained parse for all cases: {answers['parseable_json_all_cases']}.",
        f"2. Schema validation remained valid for all cases: {answers['schema_valid_all_cases']}.",
        "3. Hard semantic comparison score: "
        f"{answers['hard_semantic_score']['matches']}/{answers['hard_semantic_score']['compared']}.",
        "4. Soft tolerant semantic comparison score: "
        f"{answers['soft_tolerant_semantic_score']['matches']}/{answers['soft_tolerant_semantic_score']['compared']}.",
        "5. HG-018 provider/memory-boundary risk: "
        f"{summary['hg018_provider_memory_boundary_risk']}.",
        "6. Severe hard-field miss cases: "
        + (
            ", ".join(case["case_id"] for case in answers["severe_hard_miss_cases"])
            if answers["severe_hard_miss_cases"]
            else "none"
        )
        + ".",
        f"7. Error concentration: {answers['error_concentration']}.",
        "8. Strong enough for full holdout structured-output smoke: "
        f"{answers['strong_enough_for_full_holdout']}.",
        f"9. Next milestone: {answers['recommended_next_milestone']}.",
        "",
        "## Legacy F1 Answers",
        "",
        "Critical fields present and allowed by schema: "
        f"{answers['critical_fields_present_and_allowed']}.",
        "Failed validation cases: "
        + (
            ", ".join(answers["failed_validation_cases"])
            if answers["failed_validation_cases"]
            else "none"
        )
        + ".",
        "Promising enough for a 12-case structured-output panel: "
        f"{answers['promising_for_12_case_panel']}.",
        "",
        "No memory, retrieval, provider routing, tool execution, backend route, frontend UI, queue, worker, hook, MCP, or BlueRev modeling behavior is added.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_dry_run(args: argparse.Namespace) -> int:
    schema_path = Path(args.schema_path)
    holdout_path = Path(args.holdout)
    schema = load_json(schema_path)
    validate_schema_shape(schema)
    cases = select_cases(
        load_holdout(holdout_path),
        case_id=args.case_id,
        case_ids=args.case_ids,
    )
    context_pack, context_pack_size = load_optional_text(args.context_pack)
    print("Structured output schema smoke dry run")
    print(f"model: {args.model}")
    print(f"schema path: {schema_path}")
    print(f"selected case IDs: {', '.join(case['case_id'] for case in cases)}")
    print(f"context pack path: {args.context_pack or 'none'}")
    print(f"context pack char count: {context_pack_size}")
    print("inference disabled in dry-run: no Ollama call was made")
    if context_pack:
        print("prompt preview:")
        print(build_prompt(cases[0], context_pack)[:600])
    return 0


def run_local(args: argparse.Namespace) -> int:
    if args.timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be greater than 0")
    schema_path = Path(args.schema_path)
    report_dir = Path(args.report_dir)
    schema = load_json(schema_path)
    validate_schema_shape(schema)
    cases = select_cases(
        load_holdout(Path(args.holdout)),
        case_id=args.case_id,
        case_ids=args.case_ids,
    )
    if len(cases) > MAX_REAL_CASES:
        raise ValueError(f"--run-local is limited to {MAX_REAL_CASES} cases")
    context_pack, _context_pack_size = load_optional_text(args.context_pack)
    report_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for case in cases:
        prompt = build_prompt(case, context_pack)
        raw_call = call_ollama_chat(
            model=args.model,
            prompt=prompt,
            schema=schema,
            timeout_seconds=args.timeout_seconds,
        )
        raw_path, result_path = result_paths(report_dir, case["case_id"])
        write_json(raw_path, raw_call)
        result = build_result(
            case=case,
            model=args.model,
            schema_path=schema_path,
            context_pack_path=args.context_pack,
            raw_path=raw_path,
            raw_call=raw_call,
            schema=schema,
        )
        write_json(result_path, result)
        results.append(result)
        print(
            f"{args.model} {case['case_id']}: "
            f"parse={result['json_parse_passed']} "
            f"schema_valid={result['schema_valid']} "
            f"errors={len(result['validation_errors'])} "
            f"duration={result['duration_seconds']}"
        )
    summary = summarize_results(results, report_dir)
    summary_json, summary_md = summary_filenames(report_dir)
    write_json(report_dir / summary_json, summary)
    write_summary_markdown(report_dir / summary_md, summary)
    print(f"summary json: {report_dir / summary_json}")
    print(f"summary md: {report_dir / summary_md}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local-only Ollama structured-output schema smoke prototype."
    )
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--case-ids", default=None)
    parser.add_argument("--schema-path", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--context-pack", default=None)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-local", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.dry_run and args.run_local:
            print("Choose only one of --dry-run or --run-local.", file=sys.stderr)
            return 2
        if args.run_local:
            return run_local(args)
        return run_dry_run(args)
    except ValueError as exc:
        print(f"structured output probe failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
