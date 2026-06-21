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
MAX_REAL_CASES = 3

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


def build_prompt(case: dict[str, Any]) -> str:
    return f"""You are filling a bounded JarvisOS form for a smoke test.

Model output is advisory only. Valid structure is not semantic truth.
JarvisOS owns validation, review, persistence, retrieval gates, memory gates,
provider gates, tool gates, and final decisions.

Do not invent sources. Use not_decided=true when evidence is insufficient or
the user explicitly says something is tentative or undecided.

Output JSON only. Do not wrap in markdown. Do not include extra keys.

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
  "domain_bucket": "local_ai|memory|retrieval|modeling|software|bioprocess|reactor_design|coursework|personal|general|unknown",
  "storage_relevance": "none|low|medium|high",
  "lifecycle_status": "raw_input|fast_intake|proposed_memory|enriched_memory|accepted_memory|canonical_state|superseded|unknown",
  "sensitivity_bucket": "public|internal|sensitive|secret|unknown",
  "source_class_policy": "default_allowed|review_only|blocked|not_applicable",
  "retrieval_behavior": "none|candidate_discovery_only|full_body_required|review_gate_required|clarification_required|blocked",
  "flags": [],
  "not_decided": false,
  "clarification": false,
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


def result_paths(report_dir: Path, model: dict[str, Any], case_id: str) -> tuple[Path, Path]:
    stem = f"{sanitize_filename(model['ollama_name'])}__{sanitize_filename(case_id)}"
    return report_dir / f"{stem}__raw.txt", report_dir / f"{stem}__result.json"


def build_result_record(
    *,
    model: dict[str, Any],
    case: dict[str, Any],
    raw_path: Path,
    ollama_result: dict[str, Any],
) -> dict[str, Any]:
    parsed, parse_error = parse_model_json_output(ollama_result["stdout"])
    comparison = compare_output_to_expected(parsed, case)
    return {
        "schema_version": "local_model_form_fill_smoke_result_v0",
        "milestone": "1G-B1",
        "model_id": model["model_id"],
        "ollama_name": model["ollama_name"],
        "case_id": case["case_id"],
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


def summarize_results(results: list[dict[str, Any]], report_dir: Path) -> dict[str, Any]:
    exact_by_run = [
        {
            "model": result["ollama_name"],
            "case_id": result["case_id"],
            "exact_matches": result["comparison"]["core_field_match_count"],
            "total": result["comparison"]["core_field_total"],
            "json_parse_passed": result["json_parse_passed"],
            "timed_out": result["timed_out"],
            "returncode": result["returncode"],
        }
        for result in results
    ]
    return {
        "schema_version": "local_model_form_fill_smoke_summary_v0",
        "milestone": "1G-B1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
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


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    rows = [
        "| model | case_id | json_parse | exact_core_matches | timeout | returncode |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in summary["core_field_exact_matches_by_run"]:
        rows.append(
            "| {model} | {case_id} | {json_parse_passed} | {exact_matches}/{total} | "
            "{timed_out} | {returncode} |".format(**item)
        )
    content = "\n".join(
        [
            "# 1G-B1 Local Model Form-Fill Smoke Summary",
            "",
            "Manual review is required. This smoke run does not prove semantic truth.",
            "",
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
    print("inference disabled in dry-run: no model calls were made")
    print(f"expected future report path: {EXPECTED_FUTURE_REPORT}")
    return 0


def run_local(args: argparse.Namespace) -> int:
    if args.timeout_seconds < 1:
        raise ValueError("--timeout-seconds must be greater than 0")

    holdout_path = Path(args.holdout)
    config_path = Path(args.config)
    report_dir = Path(args.report_dir)

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
    for model in selected_models:
        for case in selected_cases:
            raw_path, result_path = result_paths(report_dir, model, case["case_id"])
            prompt = build_prompt(case)
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
            )
            write_json(result_path, result)
            results.append(result)
            print(
                f"{model['ollama_name']} {case['case_id']}: "
                f"parse={result['json_parse_passed']} "
                f"matches={result['comparison']['core_field_match_count']}/"
                f"{result['comparison']['core_field_total']} "
                f"timeout={result['timed_out']}"
            )

    summary = summarize_results(results, report_dir)
    write_json(report_dir / "local_model_form_fill_smoke_summary.json", summary)
    write_summary_markdown(
        report_dir / "local_model_form_fill_smoke_summary.md",
        summary,
    )
    print(f"summary json: {report_dir / 'local_model_form_fill_smoke_summary.json'}")
    print(f"summary md: {report_dir / 'local_model_form_fill_smoke_summary.md'}")
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
