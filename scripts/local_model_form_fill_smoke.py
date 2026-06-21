"""Dry-run skeleton for future local model form-fill smoke tests.

1G-A intentionally performs no model inference. It validates local holdout data,
validates a local candidate-model config, selects cases, and prints a dry-run
plan for a later smoke run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_HOLDOUT = Path("docs/holdout/intake_generalization_v0.jsonl")
DEFAULT_CONFIG = Path("configs/local_model_candidates.example.json")
EXPECTED_FUTURE_REPORT = (
    "backend/local_eval_reports/local_model_form_fill_smoke_1g_b_<timestamp>.json"
)
DRY_RUN_REQUIRED_MESSAGE = (
    "Only dry-run mode is implemented in 1G-A; no model inference is available."
)

EXPECTED_OLLAMA_NAMES = [
    "mistral-small3.2:24b",
    "qwen3:14b",
    "qwen3:8b",
    "gemma4:31b-it-qat",
    "gemma4:12b-it-qat",
]

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


def parse_case_ids(case_ids: str | None) -> list[str] | None:
    if not case_ids:
        return None
    parsed = [case_id.strip() for case_id in case_ids.split(",") if case_id.strip()]
    if not parsed:
        raise ValueError("--case-ids was provided but no case IDs were parsed")
    return parsed


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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run skeleton for future local model form-fill smoke tests."
    )
    parser.add_argument("--holdout", default=str(DEFAULT_HOLDOUT))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--case-ids", default=None)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
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
    print("inference disabled in 1G-A: no model calls were made")
    print(f"expected future report path: {EXPECTED_FUTURE_REPORT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(DRY_RUN_REQUIRED_MESSAGE, file=sys.stderr)
        return 2
    try:
        return run_dry_run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"dry-run validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
