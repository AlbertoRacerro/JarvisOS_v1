"""Local model form-fill smoke harness.

Dry-run mode remains the default planning path. Real local mode is explicitly
guarded behind --run-local and is limited to selected installed Ollama models
and selected holdout cases.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_CONFIG = Path("configs/local_model_candidates.example.json")
DEFAULT_REPORT_DIR = Path("reports/local_model_smoke/1G-B1")
EXPECTED_FUTURE_REPORT = (
    "reports/local_model_smoke/1G-B1/local_model_form_fill_smoke_summary.json"
)
DRY_RUN_REQUIRED_MESSAGE = (
    "Pass --dry-run or --run-local. Real local inference requires --run-local."
)
MAX_REAL_CASES = 12
APPROX_CHARS_PER_TOKEN = 4

EXPECTED_OLLAMA_NAMES = [
    "mistral-small3.2:24b",
    "qwen3:14b",
    "qwen3:8b",
    "gemma4:31b-it-qat",
    "gemma4:12b-it-qat",
]

PROJECT_BUCKETS = {
    "jarvisos",
    "bluerev",
    "coursework",
    "personal",
    "general",
    "unknown",
}
DOMAIN_BUCKETS = {
    "local_ai",
    "memory",
    "retrieval",
    "modeling",
    "software",
    "bioprocess",
    "reactor_design",
    "coursework",
    "personal",
    "general",
    "unknown",
}
STORAGE_RELEVANCE = {
    "none",
    "low",
    "medium",
    "high",
}
CANONICAL_LIFECYCLE_STATUSES = {
    "raw_input",
    "fast_intake",
    "proposed_memory",
    "enriched_memory",
    "accepted_memory",
    "canonical_state",
    "superseded",
    "unknown",
}
SENSITIVITY_BUCKETS = {
    "public",
    "internal",
    "sensitive",
    "secret",
    "unknown",
}
SOURCE_CLASS_POLICIES = {
    "default_allowed",
    "review_only",
    "blocked",
    "not_applicable",
}
RETRIEVAL_BEHAVIORS = {
    "none",
    "candidate_discovery_only",
    "full_body_required",
    "review_gate_required",
    "clarification_required",
    "blocked",
}
FINAL_OUTCOMES = {
    "accepted_structurally",
    "accepted_with_review_required",
    "clarification_required",
    "not_decided",
    "blocked",
    "schema_failed",
}

CORE_FIELD_SPECS = {
    "project_bucket": ("expected_project_bucket", PROJECT_BUCKETS),
    "domain_bucket": ("expected_domain_bucket", DOMAIN_BUCKETS),
    "storage_relevance": ("expected_storage_relevance", STORAGE_RELEVANCE),
    "lifecycle_status": (
        "expected_lifecycle_status",
        CANONICAL_LIFECYCLE_STATUSES,
    ),
    "sensitivity_bucket": ("expected_sensitivity_bucket", SENSITIVITY_BUCKETS),
    "source_class_policy": ("expected_source_class_policy", SOURCE_CLASS_POLICIES),
    "retrieval_behavior": ("expected_retrieval_behavior", RETRIEVAL_BEHAVIORS),
    "not_decided": ("expected_not_decided", {True, False}),
    "clarification": ("expected_clarification", {True, False}),
}

SOFT_FIELD_SPECS = {
    "project_bucket": (("project_bucket",), "expected_project_bucket", PROJECT_BUCKETS),
    "primary_domain": (
        ("primary_domain", "domain_bucket"),
        "expected_domain_bucket",
        DOMAIN_BUCKETS | {"security"},
    ),
    "domain_tags": (("domain_tags",), "expected_domain_bucket", None),
    "storage_relevance": (
        ("storage_relevance",),
        "expected_storage_relevance",
        STORAGE_RELEVANCE,
    ),
    "brief_rationale": (("brief_rationale",), None, None),
}

HARD_FIELD_SPECS = {
    "lifecycle_status": (
        ("lifecycle_status_proposal", "lifecycle_status"),
        "expected_lifecycle_status",
        CANONICAL_LIFECYCLE_STATUSES,
    ),
    "sensitivity_bucket": (
        ("sensitivity_bucket_proposal", "sensitivity_bucket"),
        "expected_sensitivity_bucket",
        SENSITIVITY_BUCKETS,
    ),
    "source_class_policy": (
        ("source_class_policy_proposal", "source_class_policy"),
        "expected_source_class_policy",
        SOURCE_CLASS_POLICIES,
    ),
    "retrieval_behavior": (
        ("retrieval_behavior_proposal", "retrieval_behavior"),
        "expected_retrieval_behavior",
        RETRIEVAL_BEHAVIORS,
    ),
    "not_decided": (("not_decided",), "expected_not_decided", {True, False}),
    "clarification_required": (
        ("clarification_required", "clarification"),
        "expected_clarification",
        {True, False},
    ),
    "api_or_model_escalation_recommended": (
        ("api_or_model_escalation_recommended",),
        None,
        {True, False},
    ),
    "reasoning_route_proposal": (
        ("reasoning_route_proposal",),
        None,
        {
            "none",
            "local_fast_model",
            "local_senior_model",
            "external_provider",
            "human_review",
        },
    ),
}

REQUIRED_OUTPUT_FIELDS = {
    "case_id",
    "project_bucket",
    "domain_bucket",
    "storage_relevance",
    "lifecycle_status",
    "sensitivity_bucket",
    "source_class_policy",
    "retrieval_behavior",
    "flags",
    "not_decided",
    "clarification",
    "brief_rationale",
}

RECOMMENDED_SECRETARY_FIELDS = {
    "project_bucket",
    "primary_domain",
    "domain_tags",
    "storage_relevance",
    "lifecycle_status_proposal",
    "sensitivity_bucket_proposal",
    "source_class_policy_proposal",
    "retrieval_behavior_proposal",
    "not_decided",
    "clarification_required",
    "api_or_model_escalation_recommended",
    "reasoning_route_proposal",
    "brief_rationale",
}

REQUIRED_HOLDOUT_FIELDS = {
    "case_id",
    "category",
    "input_text",
    "expected_project_bucket",
    "expected_domain_bucket",
    "expected_storage_relevance",
    "expected_lifecycle_status",
    "expected_sensitivity_bucket",
    "expected_source_class_policy",
    "expected_retrieval_behavior",
    "expected_flags",
    "expected_not_decided",
    "expected_clarification",
    "must_not",
    "rationale",
}

REQUIRED_CANDIDATE_FIELDS = {
    "model_id",
    "ollama_name",
    "family_guess",
    "installed",
    "enabled",
    "notes",
}


def load_jsonl_holdout(path: Path) -> list[dict[str, Any]]:
    """Load JSONL holdout cases without executing model code."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                raise ValueError(f"line {line_number}: blank lines are not allowed")
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"line {line_number}: expected JSON object")
            records.append(record)
    return records


def validate_holdout_cases(
    cases: list[dict[str, Any]], *, require_full_set: bool = False
) -> None:
    """Validate holdout structure and expected enum fields."""
    if require_full_set and len(cases) != 32:
        raise ValueError(f"expected 32 holdout cases, found {len(cases)}")

    seen: set[str] = set()
    for index, case in enumerate(cases, 1):
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"case {index}: missing or invalid case_id")
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)

        missing = sorted(REQUIRED_HOLDOUT_FIELDS - set(case))
        if missing:
            raise ValueError(f"{case_id}: missing required fields: {missing}")

        lifecycle = case.get("expected_lifecycle_status")
        if lifecycle not in CANONICAL_LIFECYCLE_STATUSES:
            raise ValueError(f"{case_id}: invalid lifecycle status: {lifecycle!r}")

        source_policy = case.get("expected_source_class_policy")
        if source_policy not in SOURCE_CLASS_POLICIES:
            raise ValueError(f"{case_id}: invalid source class policy: {source_policy!r}")

        retrieval_behavior = case.get("expected_retrieval_behavior")
        if retrieval_behavior not in RETRIEVAL_BEHAVIORS:
            raise ValueError(
                f"{case_id}: invalid retrieval behavior: {retrieval_behavior!r}"
            )


def load_candidate_config(path: Path) -> dict[str, Any]:
    """Load candidate config from local JSON only."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("candidate config must be a JSON object")
    return data


def validate_candidate_config(config: dict[str, Any]) -> None:
    """Validate the local candidate config shape."""
    if config.get("schema_version") != "local_model_candidates.v0":
        raise ValueError("candidate config schema_version must be local_model_candidates.v0")
    if config.get("source") != "supplied_ollama_list_2026-06-21":
        raise ValueError("candidate config source does not match supplied list")
    if config.get("ollama_version") != "0.30.10":
        raise ValueError("candidate config ollama_version must be 0.30.10")

    models = config.get("models")
    if not isinstance(models, list):
        raise ValueError("candidate config models must be a list")

    model_ids: set[str] = set()
    ollama_names: list[str] = []
    for index, model in enumerate(models, 1):
        if not isinstance(model, dict):
            raise ValueError(f"candidate {index}: expected JSON object")
        missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(model))
        if missing:
            raise ValueError(f"candidate {index}: missing fields: {missing}")
        model_id = model["model_id"]
        ollama_name = model["ollama_name"]
        if not isinstance(model_id, str) or not model_id:
            raise ValueError(f"candidate {index}: invalid model_id")
        if model_id in model_ids:
            raise ValueError(f"duplicate model_id: {model_id}")
        model_ids.add(model_id)
        if not isinstance(ollama_name, str) or not ollama_name:
            raise ValueError(f"candidate {index}: invalid ollama_name")
        if not isinstance(model["installed"], bool):
            raise ValueError(f"{model_id}: installed must be boolean")
        if not isinstance(model["enabled"], bool):
            raise ValueError(f"{model_id}: enabled must be boolean")
        ollama_names.append(ollama_name)

    if ollama_names != EXPECTED_OLLAMA_NAMES:
        raise ValueError(f"candidate ollama names do not match supplied list: {ollama_names}")


def parse_csv_values(values: str | None, *, flag_name: str) -> list[str] | None:
    if not values:
        return None
    parsed = [value.strip() for value in values.split(",") if value.strip()]
    if not parsed:
        raise ValueError(f"{flag_name} was provided but no values were parsed")
    return parsed


def parse_case_ids(case_ids: str | None) -> list[str] | None:
    return parse_csv_values(case_ids, flag_name="--case-ids")


def select_cases(
    cases: list[dict[str, Any]],
    *,
    case_ids: list[str] | None = None,
    max_cases: int | None = None,
) -> list[dict[str, Any]]:
    """Select cases by explicit IDs and/or max count."""
    if max_cases is not None and max_cases < 1:
        raise ValueError("--max-cases must be greater than 0")

    if case_ids:
        by_id = {case["case_id"]: case for case in cases}
        missing = [case_id for case_id in case_ids if case_id not in by_id]
        if missing:
            raise ValueError(f"unknown case_id values: {missing}")
        selected = [by_id[case_id] for case_id in case_ids]
    else:
        selected = list(cases)

    if max_cases is not None:
        selected = selected[:max_cases]
    return selected


def list_configured_candidates(
    config: dict[str, Any], *, include_disabled: bool = False
) -> list[dict[str, Any]]:
    models = config.get("models", [])
    if include_disabled:
        return list(models)
    return [model for model in models if model.get("enabled") is True]


def enabled_model_count(config: dict[str, Any]) -> int:
    return sum(1 for model in config.get("models", []) if model.get("enabled") is True)


def model_lookup(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for model in config.get("models", []):
        lookup[model["model_id"]] = model
        lookup[model["ollama_name"]] = model
    return lookup


def select_models(config: dict[str, Any], model_values: list[str] | None) -> list[dict[str, Any]]:
    """Select models explicitly by model_id or ollama_name."""
    if not model_values:
        raise ValueError("--models is required for --run-local")
    lookup = model_lookup(config)
    selected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    missing: list[str] = []
    for value in model_values:
        model = lookup.get(value)
        if not model:
            missing.append(value)
            continue
        if model["model_id"] not in seen_ids:
            selected.append(model)
            seen_ids.add(model["model_id"])
    if missing:
        raise ValueError(f"selected models are not in config: {missing}")
    return selected


def validate_real_run_selection(
    *,
    selected_cases: list[dict[str, Any]],
    explicit_case_ids: list[str] | None,
    selected_models: list[dict[str, Any]],
) -> None:
    if not explicit_case_ids:
        raise ValueError("--case-ids is required for --run-local")
    if len(selected_cases) > MAX_REAL_CASES:
        raise ValueError(f"--run-local is limited to {MAX_REAL_CASES} cases")
    if not selected_models:
        raise ValueError("--run-local requires at least one selected model")


def load_context_pack(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "label": None,
            "content": "",
            "char_count": 0,
            "approx_token_estimate": 0,
        }
    content = path.read_text(encoding="utf-8")
    return {
        "path": str(path),
        "label": None,
        "content": content,
        "char_count": len(content),
        "approx_token_estimate": max(1, round(len(content) / APPROX_CHARS_PER_TOKEN)),
    }


def collect_context_packs(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.context_pack and args.context_packs:
        raise ValueError("Use only one of --context-pack or --context-packs")
    if args.pack_label and args.pack_labels:
        raise ValueError("Use only one of --pack-label or --pack-labels")

    if args.context_packs:
        paths = [Path(value) for value in parse_csv_values(
            args.context_packs,
            flag_name="--context-packs",
        ) or []]
        labels = parse_csv_values(args.pack_labels, flag_name="--pack-labels")
        if labels is not None and len(labels) != len(paths):
            raise ValueError("--pack-labels must match --context-packs length")
        packs = []
        for index, path in enumerate(paths):
            pack = load_context_pack(path)
            pack["label"] = labels[index] if labels else default_pack_label(path)
            packs.append(pack)
        return packs

    context_pack_path = Path(args.context_pack) if args.context_pack else None
    pack = load_context_pack(context_pack_path)
    pack["label"] = args.pack_label or default_pack_label(context_pack_path)
    return [pack]


def default_pack_label(path: Path | None) -> str | None:
    if path is None:
        return None
    stem = path.stem
    match = re.search(r"FAST_SECRETARY_([A-Z]+)", stem)
    if match:
        return match.group(1).lower()
    return sanitize_filename(stem).lower()


def sanitize_filename(value: str) -> str:
    allowed = []
    for character in value:
        if character.isalnum() or character in {"-", "_"}:
            allowed.append(character)
        else:
            allowed.append("_")
    sanitized = "".join(allowed).strip("_")
    return sanitized or "unknown"


def strip_json_fences(output: str) -> str:
    stripped = strip_terminal_control(output).strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def strip_terminal_control(output: str) -> str:
    ansi_escape = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    without_ansi = ansi_escape.sub("", output)
    return "".join(
        character
        for character in without_ansi
        if character in {"\n", "\r", "\t"} or ord(character) >= 32
    )


def extract_first_json_object(output: str) -> str | None:
    start = output.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(output)):
        character = output[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return output[start : index + 1]
    return None


def normalize_cli_json_text(json_text: str) -> str:
    normalized: list[str] = []
    in_string = False
    escaped = False
    for character in json_text:
        if in_string:
            if escaped:
                normalized.append(character)
                escaped = False
            elif character == "\\":
                normalized.append(character)
                escaped = True
            elif character == '"':
                normalized.append(character)
                in_string = False
            elif character in {"\n", "\r"}:
                normalized.append(" ")
            else:
                normalized.append(character)
            continue
        normalized.append(character)
        if character == '"':
            in_string = True
    return "".join(normalized)


def parse_model_json_output(output: str) -> tuple[dict[str, Any] | None, str | None]:
    cleaned = strip_json_fences(output)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        extracted = extract_first_json_object(cleaned)
        if extracted is not None:
            try:
                parsed = json.loads(normalize_cli_json_text(extracted))
            except json.JSONDecodeError as extracted_exc:
                return None, str(extracted_exc)
        else:
            return None, str(exc)
    if not isinstance(parsed, dict):
        return None, "parsed output is not a JSON object"
    return parsed, None


def first_present(parsed: dict[str, Any], field_names: tuple[str, ...]) -> Any:
    for field_name in field_names:
        if field_name in parsed:
            return parsed[field_name]
    return None


def compare_scalar_field(
    *,
    parsed: dict[str, Any] | None,
    case: dict[str, Any],
    field_names: tuple[str, ...],
    expected_field: str | None,
    valid_values: set[Any] | None,
) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        actual = None
    else:
        actual = first_present(parsed, field_names)
    expected = case.get(expected_field) if expected_field else None
    valid = True if valid_values is None else actual in valid_values
    if expected_field is None:
        matched = actual is not None and valid
    else:
        matched = actual == expected
    return {
        "actual": actual,
        "expected": expected,
        "valid": valid,
        "matched": matched,
        "field_names": list(field_names),
    }


def score_soft_fields(
    parsed: dict[str, Any] | None, case: dict[str, Any]
) -> dict[str, Any]:
    fields: dict[str, dict[str, Any]] = {}
    for output_field, (field_names, expected_field, valid_values) in SOFT_FIELD_SPECS.items():
        if output_field == "domain_tags":
            tags = first_present(parsed, field_names) if isinstance(parsed, dict) else None
            valid = isinstance(tags, list) and all(isinstance(tag, str) for tag in tags)
            expected = case.get(expected_field) if expected_field else None
            tag_set = set(tags) if valid else set()
            matched = valid and expected in tag_set
            fields[output_field] = {
                "actual": tags,
                "expected": expected,
                "valid": valid,
                "exact_matched": matched,
                "tolerant_matched": matched,
                "matched": matched,
                "field_names": list(field_names),
            }
            continue
        field = compare_scalar_field(
            parsed=parsed,
            case=case,
            field_names=field_names,
            expected_field=expected_field,
            valid_values=valid_values,
        )
        exact_matched = field["matched"]
        tolerant_matched = exact_matched
        if output_field == "primary_domain" and case["case_id"] == "HG-016":
            tags = first_present(parsed, ("domain_tags",)) if isinstance(parsed, dict) else None
            tag_set = set(tags) if isinstance(tags, list) else set()
            gates = critical_gate_checks(parsed, case)
            tolerant_matched = (
                exact_matched
                or (
                    field["actual"] == "security"
                    and not gates["failures"]
                    and bool(tag_set & {"software", "secret_handling"})
                )
            )
        field["exact_matched"] = exact_matched
        field["tolerant_matched"] = tolerant_matched
        fields[output_field] = field
    return {
        "fields": fields,
        "matched": sum(1 for field in fields.values() if field["exact_matched"]),
        "exact_matched": sum(1 for field in fields.values() if field["exact_matched"]),
        "tolerant_matched": sum(
            1 for field in fields.values() if field["tolerant_matched"]
        ),
        "total": len(fields),
    }


def score_hard_fields(
    parsed: dict[str, Any] | None, case: dict[str, Any]
) -> dict[str, Any]:
    fields: dict[str, dict[str, Any]] = {}
    for output_field, (field_names, expected_field, valid_values) in HARD_FIELD_SPECS.items():
        fields[output_field] = compare_scalar_field(
            parsed=parsed,
            case=case,
            field_names=field_names,
            expected_field=expected_field,
            valid_values=valid_values,
        )
    return {
        "fields": fields,
        "matched": sum(1 for field in fields.values() if field["matched"]),
        "total": len(fields),
    }


def critical_gate_checks(
    parsed: dict[str, Any] | None, case: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {
            "failures": ["json_not_parsed"],
            "passed": 0,
            "total": 0,
        }

    sensitivity = first_present(
        parsed,
        ("sensitivity_bucket_proposal", "sensitivity_bucket"),
    )
    source_policy = first_present(
        parsed,
        ("source_class_policy_proposal", "source_class_policy"),
    )
    retrieval_behavior = first_present(
        parsed,
        ("retrieval_behavior_proposal", "retrieval_behavior"),
    )
    lifecycle = first_present(
        parsed,
        ("lifecycle_status_proposal", "lifecycle_status"),
    )
    not_decided = parsed.get("not_decided")
    escalation = parsed.get("api_or_model_escalation_recommended")
    route = parsed.get("reasoning_route_proposal")
    case_id = case["case_id"]

    checks: dict[str, bool] = {}
    if case_id == "HG-016":
        checks["secret_implies_secret_blocked_blocked"] = (
            sensitivity == "secret"
            and source_policy == "blocked"
            and retrieval_behavior == "blocked"
        )
        checks["no_external_provider_for_raw_secret"] = (
            escalation is False and route != "external_provider"
        )
    if case_id == "HG-006":
        checks["unresolved_bluerev_assumption_not_decided"] = not_decided is True
    if case_id in {"HG-001", "HG-006"}:
        checks["useful_non_final_not_accepted_memory"] = lifecycle != "accepted_memory"

    failures = [name for name, passed in checks.items() if not passed]
    return {
        "checks": checks,
        "failures": failures,
        "passed": sum(1 for passed in checks.values() if passed),
        "total": len(checks),
    }


def compare_output_to_expected(
    parsed: dict[str, Any] | None, case: dict[str, Any]
) -> dict[str, Any]:
    missing_required = sorted(REQUIRED_OUTPUT_FIELDS - set(parsed or {}))
    enum_validity: dict[str, bool] = {}
    exact_matches: dict[str, bool] = {}
    field_values: dict[str, dict[str, Any]] = {}
    output_flags = parsed.get("flags") if isinstance(parsed, dict) else None
    flags_valid = isinstance(output_flags, list) and all(
        isinstance(flag, str) for flag in output_flags
    )
    output_flag_set = set(output_flags) if flags_valid else set()
    expected_flags = set(case.get("expected_flags", []))

    if isinstance(parsed, dict):
        for output_field, (expected_field, valid_values) in CORE_FIELD_SPECS.items():
            value = parsed.get(output_field)
            expected = case.get(expected_field)
            enum_validity[output_field] = value in valid_values
            exact_matches[output_field] = value == expected
            field_values[output_field] = {
                "actual": value,
                "expected": expected,
            }
    else:
        for output_field in CORE_FIELD_SPECS:
            enum_validity[output_field] = False
            exact_matches[output_field] = False
            field_values[output_field] = {
                "actual": None,
                "expected": case.get(CORE_FIELD_SPECS[output_field][0]),
            }

    case_id_matches = isinstance(parsed, dict) and parsed.get("case_id") == case["case_id"]
    return {
        "case_id_matches": case_id_matches,
        "missing_required_output_fields": missing_required,
        "enum_validity": enum_validity,
        "core_field_exact_matches": exact_matches,
        "core_field_match_count": sum(1 for matched in exact_matches.values() if matched),
        "core_field_total": len(exact_matches),
        "core_field_values": field_values,
        "flags_valid": flags_valid,
        "expected_flags_present": sorted(expected_flags & output_flag_set),
        "expected_flags_missing": sorted(expected_flags - output_flag_set),
        "unexpected_flags": sorted(output_flag_set - expected_flags),
    }


def score_output(
    parsed: dict[str, Any] | None,
    case: dict[str, Any],
    *,
    secretary_mode: bool = False,
) -> dict[str, Any]:
    legacy_comparison = compare_output_to_expected(parsed, case)
    if isinstance(parsed, dict):
        recommended_missing = sorted(RECOMMENDED_SECRETARY_FIELDS - set(parsed))
    else:
        recommended_missing = sorted(RECOMMENDED_SECRETARY_FIELDS)
    return {
        "legacy_core": legacy_comparison,
        "soft": score_soft_fields(parsed, case),
        "hard": score_hard_fields(parsed, case),
        "critical_gates": critical_gate_checks(parsed, case),
        "recommended_secretary_fields_missing": recommended_missing
        if secretary_mode
        else [],
    }


def validate_fake_output_record(
    record: dict[str, Any], known_case_ids: set[str]
) -> dict[str, Any]:
    """Validate a fake output record for skeleton tests only."""
    errors: list[str] = []
    if not isinstance(record, dict):
        return {"valid": False, "errors": ["record must be a JSON object"]}

    case_id = record.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        errors.append("missing case_id")
    elif case_id not in known_case_ids:
        errors.append(f"unknown case_id: {case_id}")

    final_outcome = record.get("final_outcome")
    if final_outcome is not None and final_outcome not in FINAL_OUTCOMES:
        errors.append(f"invalid final_outcome: {final_outcome!r}")

    return {"valid": not errors, "errors": errors}


def enum_line(name: str, values: set[str]) -> str:
    return f"{name}: " + "|".join(sorted(values))


def build_prompt(case: dict[str, Any], context_pack: dict[str, Any]) -> str:
    context_section = ""
    if context_pack["content"]:
        context_section = f"""
Fast secretary context pack:
```text
{context_pack["content"]}
```
"""
    return f"""You are filling a bounded JarvisOS form for a smoke test.

Model output is advisory only. Valid structure is not semantic truth.
JarvisOS owns validation, review, persistence, retrieval gates, memory gates,
provider gates, tool gates, and final decisions.

Do not invent sources. Use not_decided=true when evidence is insufficient or
the user explicitly says something is tentative or undecided.

Output JSON only. Do not wrap in markdown.
{context_section}

Input text:
{case["input_text"]}

Allowed enums:
{enum_line("project_bucket", PROJECT_BUCKETS)}
{enum_line("domain_bucket", DOMAIN_BUCKETS)}
{enum_line("storage_relevance", STORAGE_RELEVANCE)}
{enum_line("lifecycle_status", CANONICAL_LIFECYCLE_STATUSES)}
{enum_line("sensitivity_bucket", SENSITIVITY_BUCKETS)}
{enum_line("source_class_policy", SOURCE_CLASS_POLICIES)}
{enum_line("retrieval_behavior", RETRIEVAL_BEHAVIORS)}

Required JSON shape:
{{
  "case_id": "{case["case_id"]}",
  "project_bucket": "jarvisos|bluerev|coursework|personal|general|unknown",
  "summary": "short summary",
  "primary_domain": "memory|software|retrieval|local_ai|modeling|bioprocess|reactor_design|coursework|personal|security|general|unknown",
  "domain_tags": [],
  "domain_bucket": "local_ai|memory|retrieval|modeling|software|bioprocess|reactor_design|coursework|personal|general|unknown",
  "storage_relevance": "none|low|medium|high",
  "lifecycle_status_proposal": "raw_input|fast_intake|proposed_memory|enriched_memory|accepted_memory|canonical_state|superseded|unknown",
  "lifecycle_status": "raw_input|fast_intake|proposed_memory|enriched_memory|accepted_memory|canonical_state|superseded|unknown",
  "sensitivity_bucket_proposal": "public|internal|sensitive|secret|unknown",
  "sensitivity_bucket": "public|internal|sensitive|secret|unknown",
  "source_class_policy_proposal": "default_allowed|review_only|blocked|not_applicable",
  "source_class_policy": "default_allowed|review_only|blocked|not_applicable",
  "retrieval_behavior_proposal": "none|candidate_discovery_only|full_body_required|review_gate_required|clarification_required|blocked",
  "retrieval_behavior": "none|candidate_discovery_only|full_body_required|review_gate_required|clarification_required|blocked",
  "flags": [],
  "not_decided": false,
  "clarification_required": false,
  "clarification": false,
  "api_or_model_escalation_recommended": false,
  "reasoning_route_proposal": "none|local_fast_model|local_senior_model|external_provider|human_review",
  "brief_rationale": "short reason"
}}
"""


def run_ollama(model_name: str, prompt: str, timeout_seconds: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - started
        return {
            "timed_out": True,
            "duration_seconds": round(duration, 3),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"timeout after {timeout_seconds} seconds",
        }
    duration = time.perf_counter() - started
    return {
        "timed_out": False,
        "duration_seconds": round(duration, 3),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_raw_output_for_report(output: str) -> str:
    lines = [line.rstrip() for line in output.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def result_paths(
    report_dir: Path,
    model: dict[str, Any],
    case_id: str,
    pack_label: str | None = None,
) -> tuple[Path, Path]:
    parts = []
    if pack_label:
        parts.append(sanitize_filename(pack_label))
    parts.extend([sanitize_filename(model["ollama_name"]), sanitize_filename(case_id)])
    stem = "__".join(parts)
    return report_dir / f"{stem}__raw.txt", report_dir / f"{stem}__result.json"


def build_result_record(
    *,
    model: dict[str, Any],
    case: dict[str, Any],
    raw_path: Path,
    ollama_result: dict[str, Any],
    context_pack: dict[str, Any],
    milestone: str | None = None,
) -> dict[str, Any]:
    parsed, parse_error = parse_model_json_output(ollama_result["stdout"])
    comparison = score_output(
        parsed,
        case,
        secretary_mode=bool(context_pack["path"]),
    )
    return {
        "schema_version": "local_model_form_fill_smoke_result_v0",
        "milestone": milestone or ("1G-B2-A" if context_pack["path"] else "1G-B1"),
        "model_id": model["model_id"],
        "ollama_name": model["ollama_name"],
        "case_id": case["case_id"],
        "context_pack_path": context_pack["path"],
        "context_pack_label": context_pack["label"],
        "context_pack_char_count": context_pack["char_count"],
        "context_pack_approx_token_estimate": context_pack[
            "approx_token_estimate"
        ],
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "raw_output_path": str(raw_path),
        "duration_seconds": ollama_result["duration_seconds"],
        "returncode": ollama_result["returncode"],
        "timed_out": ollama_result["timed_out"],
        "stderr": ollama_result["stderr"],
        "json_parse_passed": parsed is not None,
        "json_parse_error": parse_error,
        "parsed_output": parsed,
        "comparison": comparison,
    }


def summarize_results(
    results: list[dict[str, Any]],
    report_dir: Path,
    context_pack: dict[str, Any],
    milestone: str | None = None,
) -> dict[str, Any]:
    exact_by_run = [
        {
            "model": result["ollama_name"],
            "case_id": result["case_id"],
            "context_pack_label": result["context_pack_label"],
            "exact_matches": result["comparison"]["legacy_core"][
                "core_field_match_count"
            ],
            "total": result["comparison"]["legacy_core"]["core_field_total"],
            "soft_exact_matches": result["comparison"]["soft"]["exact_matched"],
            "soft_tolerant_matches": result["comparison"]["soft"][
                "tolerant_matched"
            ],
            "soft_matches": result["comparison"]["soft"]["tolerant_matched"],
            "soft_total": result["comparison"]["soft"]["total"],
            "hard_matches": result["comparison"]["hard"]["matched"],
            "hard_total": result["comparison"]["hard"]["total"],
            "critical_gate_failures": result["comparison"]["critical_gates"][
                "failures"
            ],
            "json_parse_passed": result["json_parse_passed"],
            "timed_out": result["timed_out"],
            "returncode": result["returncode"],
        }
        for result in results
    ]
    return {
        "schema_version": "local_model_form_fill_smoke_summary_v0",
        "milestone": milestone or ("1G-B2-A" if context_pack["path"] else "1G-B1"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "context_pack_path": context_pack["path"],
        "context_pack_label": context_pack["label"],
        "context_pack_char_count": context_pack["char_count"],
        "context_pack_approx_token_estimate": context_pack[
            "approx_token_estimate"
        ],
        "total_runs": len(results),
        "json_parse_passes": sum(1 for result in results if result["json_parse_passed"]),
        "json_parse_failures": sum(
            1 for result in results if not result["json_parse_passed"]
        ),
        "timeouts": sum(1 for result in results if result["timed_out"]),
        "errors": sum(
            1
            for result in results
            if result["returncode"] not in (0, None) or result["timed_out"]
        ),
        "manual_review_required": True,
        "semantic_truth_scored": False,
        "models": sorted({result["ollama_name"] for result in results}),
        "case_ids": sorted({result["case_id"] for result in results}),
        "core_field_exact_matches_by_run": exact_by_run,
    }


def summarize_ablation(
    results: list[dict[str, Any]],
    report_dir: Path,
    milestone: str = "1G-B2-B",
) -> dict[str, Any]:
    profiles: dict[tuple[str, str], dict[str, Any]] = {}
    for result in results:
        key = (result["context_pack_label"], result["ollama_name"])
        profile = profiles.setdefault(
            key,
            {
                "context_pack_label": result["context_pack_label"],
                "context_pack_path": result["context_pack_path"],
                "context_pack_char_count": result["context_pack_char_count"],
                "context_pack_approx_token_estimate": result[
                    "context_pack_approx_token_estimate"
                ],
                "model": result["ollama_name"],
                "runs": 0,
                "json_parse_passes": 0,
                "timeouts": 0,
                "hard_matches": 0,
                "hard_total": 0,
                "soft_exact_matches": 0,
                "soft_tolerant_matches": 0,
                "soft_total": 0,
                "critical_gate_failures": 0,
                "manual_review_required": True,
            },
        )
        profile["runs"] += 1
        profile["json_parse_passes"] += int(result["json_parse_passed"])
        profile["timeouts"] += int(result["timed_out"])
        profile["hard_matches"] += result["comparison"]["hard"]["matched"]
        profile["hard_total"] += result["comparison"]["hard"]["total"]
        profile["soft_exact_matches"] += result["comparison"]["soft"]["exact_matched"]
        profile["soft_tolerant_matches"] += result["comparison"]["soft"][
            "tolerant_matched"
        ]
        profile["soft_total"] += result["comparison"]["soft"]["total"]
        profile["critical_gate_failures"] += len(
            result["comparison"]["critical_gates"]["failures"]
        )

    profile_rows = sorted(
        profiles.values(),
        key=lambda item: (
            item["context_pack_label"] or "",
            item["model"],
        ),
    )
    for profile in profile_rows:
        token_k = max(1, profile["context_pack_approx_token_estimate"]) / 1000
        profile["hard_matches_per_1k_tokens"] = round(
            profile["hard_matches"] / token_k,
            3,
        )
        profile["soft_tolerant_matches_per_1k_tokens"] = round(
            profile["soft_tolerant_matches"] / token_k,
            3,
        )
        profile["successful_parse_per_1k_tokens"] = round(
            profile["json_parse_passes"] / token_k,
            3,
        )

    def best_by(key: str) -> dict[str, Any] | None:
        if not profile_rows:
            return None
        return max(
            profile_rows,
            key=lambda item: (
                item[key] / item["runs"]
                if key in {"json_parse_passes"} and item["runs"]
                else item[key] / max(1, item.get(key.replace("matches", "total"), 1)),
                -item["critical_gate_failures"],
            ),
        )

    def best_ratio(match_key: str, total_key: str) -> dict[str, Any] | None:
        if not profile_rows:
            return None
        return max(
            profile_rows,
            key=lambda item: (
                item[match_key] / max(1, item[total_key]),
                item["json_parse_passes"] / max(1, item["runs"]),
                -item["critical_gate_failures"],
            ),
        )

    def pack_totals(label: str) -> dict[str, Any]:
        rows = [row for row in profile_rows if row["context_pack_label"] == label]
        return {
            "label": label,
            "runs": sum(row["runs"] for row in rows),
            "json_parse_passes": sum(row["json_parse_passes"] for row in rows),
            "hard_matches": sum(row["hard_matches"] for row in rows),
            "hard_total": sum(row["hard_total"] for row in rows),
            "soft_exact_matches": sum(row["soft_exact_matches"] for row in rows),
            "soft_tolerant_matches": sum(row["soft_tolerant_matches"] for row in rows),
            "soft_total": sum(row["soft_total"] for row in rows),
            "critical_gate_failures": sum(row["critical_gate_failures"] for row in rows),
        }

    pack_comparisons = {
        "micro_rules_v0_2_over_micro_v0_1": {
            "baseline": pack_totals("micro_v0_1"),
            "candidate": pack_totals("micro_rules_v0_2"),
        },
        "lite_rules_v0_2_over_lite_v0_1": {
            "baseline": pack_totals("lite_v0_1"),
            "candidate": pack_totals("lite_rules_v0_2"),
        },
    }

    best_parse = best_by("json_parse_passes")
    best_hard = best_ratio("hard_matches", "hard_total")
    best_soft_tolerant = best_ratio("soft_tolerant_matches", "soft_total")
    best_critical_gate = min(
        profile_rows,
        key=lambda item: (
            item["critical_gate_failures"],
            -item["json_parse_passes"] / max(1, item["runs"]),
            -item["hard_matches"] / max(1, item["hard_total"]),
        ),
    ) if profile_rows else None
    best_score_per_token = max(
        profile_rows,
        key=lambda item: (
            item["hard_matches_per_1k_tokens"],
            item["soft_tolerant_matches_per_1k_tokens"],
            item["successful_parse_per_1k_tokens"],
            -item["critical_gate_failures"],
        ),
    ) if profile_rows else None
    recommended = None
    if profile_rows:
        recommended = max(
            profile_rows,
            key=lambda item: (
                item["json_parse_passes"] / max(1, item["runs"]),
                item["hard_matches"] / max(1, item["hard_total"]),
                item["soft_tolerant_matches"] / max(1, item["soft_total"]),
                -item["critical_gate_failures"],
            ),
        )

    return {
        "schema_version": "local_model_form_fill_recipe_ablation_summary_v0",
        "milestone": milestone,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "semantic_truth_scored": False,
        "manual_review_required": True,
        "total_runs": len(results),
        "profiles": profile_rows,
        "pack_comparisons": pack_comparisons,
        "best_parse_stability_profile": best_parse,
        "best_hard_score_profile": best_hard,
        "best_soft_tolerant_score_profile": best_soft_tolerant,
        "best_critical_gate_profile": best_critical_gate,
        "best_score_per_token_profile": best_score_per_token,
        "known_error_reduction_notes": {
            "bluerev_unresolved_assumption": "review per HG-006 hard/not_decided fields",
            "memory_boundary_too_broad": "review per HG-001 hard/soft scores",
            "secret_soft_domain_mismatch": "primary_domain=security tolerated only with software or secret_handling tags and passing hard secret gates",
            "external_provider_risk_for_secret": "tracked by no_external_provider_for_raw_secret critical gate",
        },
        "recommended_next_expanded_profile": recommended,
    }


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    rows = [
        "| pack | model | case_id | json_parse | legacy_core | soft | hard | gate_failures | timeout | returncode |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in summary["core_field_exact_matches_by_run"]:
        rows.append(
            "| {context_pack_label} | {model} | {case_id} | {json_parse_passed} | "
            "{exact_matches}/{total} | {soft_exact_matches}/{soft_total} exact, "
            "{soft_tolerant_matches}/{soft_total} tolerant | "
            "{hard_matches}/{hard_total} | {critical_gate_failures} | "
            "{timed_out} | {returncode} |".format(**item)
        )
    content = "\n".join(
        [
            f"# {summary['milestone']} Local Model Form-Fill Smoke Summary",
            "",
            "Manual review is required. This smoke run does not prove semantic truth.",
            "",
            f"- context pack: {summary['context_pack_label']}",
            f"- context pack path: {summary['context_pack_path']}",
            f"- context pack chars: {summary['context_pack_char_count']}",
            f"- context pack approx tokens: {summary['context_pack_approx_token_estimate']}",
            f"- total runs: {summary['total_runs']}",
            f"- JSON parse passes: {summary['json_parse_passes']}",
            f"- JSON parse failures: {summary['json_parse_failures']}",
            f"- timeouts: {summary['timeouts']}",
            f"- errors: {summary['errors']}",
            "",
            *rows,
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")


def write_ablation_markdown(path: Path, summary: dict[str, Any]) -> None:
    rows = [
        "| pack | model | tokens | parse | hard | soft exact | soft tolerant | gate failures | hard/1k tok | soft tol/1k tok | parse/1k tok |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for profile in summary["profiles"]:
        rows.append(
            "| {context_pack_label} | {model} | {context_pack_approx_token_estimate} | {json_parse_passes}/{runs} | "
            "{hard_matches}/{hard_total} | {soft_exact_matches}/{soft_total} | "
            "{soft_tolerant_matches}/{soft_total} | {critical_gate_failures} | "
            "{hard_matches_per_1k_tokens} | {soft_tolerant_matches_per_1k_tokens} | "
            "{successful_parse_per_1k_tokens} |".format(
                **profile
            )
        )
    recommended = summary["recommended_next_expanded_profile"] or {}
    content = "\n".join(
        [
            f"# {summary['milestone']} Fast Secretary Recipe Ablation Summary",
            "",
            "Manual review is required. This ablation does not prove semantic truth.",
            "",
            f"- total runs: {summary['total_runs']}",
            "- MICRO_RULES v0.2 over MICRO v0.1: see pack_comparisons in JSON",
            "- LITE_RULES v0.2 over LITE v0.1: see pack_comparisons in JSON",
            f"- best parse stability: {summary['best_parse_stability_profile']}",
            f"- best hard score: {summary['best_hard_score_profile']}",
            f"- best soft tolerant score: {summary['best_soft_tolerant_score_profile']}",
            f"- best critical gate performance: {summary['best_critical_gate_profile']}",
            f"- best score per approximate token: {summary['best_score_per_token_profile']}",
            f"- recommended next expanded profile: {recommended}",
            "",
            *rows,
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run and local-only form-fill smoke harness."
    )
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--case-ids", default=None)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--models", default=None)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--context-pack", default=None)
    parser.add_argument("--context-packs", default=None)
    parser.add_argument("--pack-label", default=None)
    parser.add_argument("--pack-labels", default=None)
    parser.add_argument("--ablation-summary-stem", default="recipe_ablation_summary")
    parser.add_argument("--report-milestone", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-local", action="store_true")
    return parser


def run_dry_run(args: argparse.Namespace) -> int:
    holdout_path = Path(args.holdout)
    config_path = Path(args.config)

    cases = load_jsonl_holdout(holdout_path)
    validate_holdout_cases(cases, require_full_set=True)

    config = load_candidate_config(config_path)
    validate_candidate_config(config)
    context_packs = collect_context_packs(args)

    selected_cases = select_cases(
        cases,
        case_ids=parse_case_ids(args.case_ids),
        max_cases=args.max_cases,
    )
    candidates = list_configured_candidates(
        config, include_disabled=args.include_disabled
    )

    print("Local model form-fill smoke harness dry run")
    print(f"holdout path: {holdout_path}")
    print(f"config path: {config_path}")
    print(f"loaded holdout case count: {len(cases)}")
    print(
        "selected case IDs: "
        + ", ".join(case["case_id"] for case in selected_cases)
    )
    print("configured candidate models:")
    if candidates:
        for model in candidates:
            print(
                f"- {model['model_id']} ({model['ollama_name']}) "
                f"enabled={str(model['enabled']).lower()}"
            )
    else:
        print("- none selected; pass --include-disabled to list disabled candidates")
    print(f"enabled model count: {enabled_model_count(config)}")
    for context_pack in context_packs:
        if context_pack["path"]:
            print(f"context pack path: {context_pack['path']}")
            print(f"context pack label: {context_pack['label']}")
            print(f"context pack char count: {context_pack['char_count']}")
            print(
                "context pack approx token estimate: "
                f"{context_pack['approx_token_estimate']}"
            )
    print("inference disabled in dry-run: no model calls were made")
    print(f"expected future report path: {EXPECTED_FUTURE_REPORT}")
    return 0


def run_local(args: argparse.Namespace) -> int:
    if args.timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be greater than 0")

    holdout_path = Path(args.holdout)
    config_path = Path(args.config)
    report_dir = Path(args.report_dir)
    context_packs = collect_context_packs(args)

    cases = load_jsonl_holdout(holdout_path)
    validate_holdout_cases(cases, require_full_set=True)
    config = load_candidate_config(config_path)
    validate_candidate_config(config)

    explicit_case_ids = parse_case_ids(args.case_ids)
    selected_cases = select_cases(cases, case_ids=explicit_case_ids)
    selected_models = select_models(
        config,
        parse_csv_values(args.models, flag_name="--models"),
    )
    validate_real_run_selection(
        selected_cases=selected_cases,
        explicit_case_ids=explicit_case_ids,
        selected_models=selected_models,
    )

    report_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for context_pack in context_packs:
        pack_results: list[dict[str, Any]] = []
        for model in selected_models:
            for case in selected_cases:
                raw_path, result_path = result_paths(
                    report_dir,
                    model,
                    case["case_id"],
                    context_pack["label"],
                )
                prompt = build_prompt(case, context_pack)
                ollama_result = run_ollama(
                    model["ollama_name"],
                    prompt,
                    args.timeout_seconds,
                )
                raw_path.write_text(
                    format_raw_output_for_report(ollama_result["stdout"]),
                    encoding="utf-8",
                )
                result = build_result_record(
                    model=model,
                    case=case,
                    raw_path=raw_path,
                    ollama_result=ollama_result,
                    context_pack=context_pack,
                    milestone=args.report_milestone,
                )
                write_json(result_path, result)
                pack_results.append(result)
                results.append(result)
                print(
                    f"{context_pack['label']} {model['ollama_name']} {case['case_id']}: "
                    f"parse={result['json_parse_passed']} "
                    f"soft_exact={result['comparison']['soft']['exact_matched']}/"
                    f"{result['comparison']['soft']['total']} "
                    f"soft_tolerant={result['comparison']['soft']['tolerant_matched']}/"
                    f"{result['comparison']['soft']['total']} "
                    f"hard={result['comparison']['hard']['matched']}/"
                    f"{result['comparison']['hard']['total']} "
                    f"gates={len(result['comparison']['critical_gates']['failures'])} "
                    f"timeout={result['timed_out']}"
                )

        summary = summarize_results(
            pack_results,
            report_dir,
            context_pack,
            args.report_milestone,
        )
        summary_stem = "local_model_form_fill_smoke_summary"
        if context_pack["label"]:
            summary_stem = f"{sanitize_filename(context_pack['label'])}__{summary_stem}"
        write_json(report_dir / f"{summary_stem}.json", summary)
        write_summary_markdown(
            report_dir / f"{summary_stem}.md",
            summary,
        )
        print(f"summary json: {report_dir / f'{summary_stem}.json'}")
        print(f"summary md: {report_dir / f'{summary_stem}.md'}")

    if len(context_packs) > 1:
        ablation_summary = summarize_ablation(
            results,
            report_dir,
            args.report_milestone or "1G-B2-B",
        )
        summary_stem = sanitize_filename(args.ablation_summary_stem)
        write_json(report_dir / f"{summary_stem}.json", ablation_summary)
        write_ablation_markdown(
            report_dir / f"{summary_stem}.md",
            ablation_summary,
        )
        print(f"ablation summary json: {report_dir / f'{summary_stem}.json'}")
        print(f"ablation summary md: {report_dir / f'{summary_stem}.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.dry_run and args.run_local:
        print("Choose only one of --dry-run or --run-local.", file=sys.stderr)
        return 2
    if not args.dry_run and not args.run_local:
        print(DRY_RUN_REQUIRED_MESSAGE, file=sys.stderr)
        return 2
    try:
        if args.dry_run:
            return run_dry_run(args)
        return run_local(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"local model smoke harness failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
