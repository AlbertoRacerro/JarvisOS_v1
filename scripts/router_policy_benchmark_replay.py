"""Offline benchmark fixture replay harness for JarvisOS routing candidates.

This module is intentionally offline-only:
- no provider execution
- no network execution
- no SDK/API imports
- no env/secret loading
- no provider registry/runtime authority

It evaluates stored benchmark replay records only. It does not infer model
quality semantically and it does not grant provider/network/execution permission.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ALLOWED_SENSITIVITY_LEVELS = {"S0", "S1", "S2", "S3", "S4"}
ALLOWED_INTELLIGENCE_LEVELS = {"I0", "I1", "I2", "I3", "I4", "I5"}
ALLOWED_ROUTE_CLASSES = {
    "local",
    "external:cheap",
    "external:scientific_medium",
    "external:frontier",
    "deterministic:no_llm",
    "public_query_only",
    "blocked_or_public_query_only",
}
ALLOWED_CANDIDATE_CLASSES = set(ALLOWED_ROUTE_CLASSES)
ALLOWED_COST_STATUS = {"verified", "estimated", "unverified", "unavailable"}
COST_PRESENT_STATUSES = {"verified", "estimated", "unverified"}
ALLOWED_SUCCESS_BASIS = {
    "stored_replay_label",
    "unit_tests",
    "human_review",
    "deterministic_rule",
}

REQUIRED_FIELDS = {
    "benchmark_suite_id",
    "suite_version",
    "fixture_id",
    "fixture_version",
    "task_type",
    "sensitivity_level",
    "intelligence_level",
    "allowed_route_class",
    "candidate_label",
    "candidate_class",
    "input_digest",
    "input_token_count",
    "output_token_count",
    "total_token_count",
    "estimated_cost",
    "cost_currency",
    "cost_source",
    "cost_status",
    "expected_outcome",
    "observed_outcome",
    "success",
    "success_basis",
    "failure_reason",
    "tests_passed",
    "tests_failed",
    "human_review_required",
    "retry_count",
    "tool_call_count",
    "cache_status",
    "context_size_bucket",
    "history_allowed",
    "created_for_benchmark_only",
    "not_runtime_authority",
}

IDENTITY_STRING_FIELDS = {
    "benchmark_suite_id",
    "suite_version",
    "fixture_id",
    "fixture_version",
    "candidate_label",
    "candidate_class",
    "task_type",
    "sensitivity_level",
    "intelligence_level",
}

STRING_FIELDS = IDENTITY_STRING_FIELDS | {
    "allowed_route_class",
    "input_digest",
    "expected_outcome",
    "observed_outcome",
    "cache_status",
    "context_size_bucket",
}

COUNT_FIELDS = {
    "input_token_count",
    "output_token_count",
    "total_token_count",
    "tests_passed",
    "tests_failed",
    "retry_count",
    "tool_call_count",
}

COMPARABLE_FIXTURE_FIELDS = (
    "benchmark_suite_id",
    "suite_version",
    "fixture_id",
    "fixture_version",
    "task_type",
    "sensitivity_level",
    "intelligence_level",
    "allowed_route_class",
    "input_digest",
    "expected_outcome",
    "created_for_benchmark_only",
    "not_runtime_authority",
    "context_size_bucket",
    "history_allowed",
)

WINNER_BLOCKING_REASON_PRIORITY = (
    "invalid_fixtures",
    "fixture_definition_conflict",
    "mixed_suite_or_version",
    "candidate_fixture_coverage_incomplete",
    "duplicate_fixture_records",
    "mixed_currency_without_conversion",
    "cost_data_incomplete",
    "insufficient_candidate_count",
    "tie_on_cost_per_success",
)


class BenchmarkFixtureError(ValueError):
    """Raised only for malformed fixture files, not for invalid fixture records."""


def _canonical_json_bytes(value: Any) -> bytes:
    """Return stable JSON bytes suitable for deterministic digests."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _without_digest_fields(record: dict[str, Any]) -> dict[str, Any]:
    copied = dict(record)
    copied.pop("fixture_record_digest", None)
    copied.pop("fixture_set_digest", None)
    copied.pop("replay_set_digest", None)
    return copied


def compute_fixture_record_digest(record: dict[str, Any]) -> str:
    """Compute deterministic digest for one full replay record."""
    return _sha256(_without_digest_fields(record))


def _comparable_fixture_projection(record: dict[str, Any]) -> dict[str, Any]:
    return {field: record.get(field) for field in COMPARABLE_FIXTURE_FIELDS}


def compute_fixture_set_digest(records: list[dict[str, Any]]) -> str:
    """Compute digest for comparable fixture inputs independent of candidate results."""
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        projected = _comparable_fixture_projection(record)
        fixture_id = str(projected.get("fixture_id", ""))
        unique[(fixture_id, _sha256(projected))] = projected
    canonical_records = [unique[key] for key in sorted(unique)]
    return _sha256(canonical_records)


def compute_replay_set_digest(records: list[dict[str, Any]]) -> str:
    """Compute digest for full replay records independent of filesystem/input order."""
    canonical_records = [
        _without_digest_fields(record)
        for record in sorted(
            records,
            key=lambda item: (
                str(item.get("fixture_id", "")),
                str(item.get("candidate_label", "")),
            ),
        )
    ]
    return _sha256(canonical_records)


def _violation(code: str, field: str, message: str, fixture_id: str | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "field": field,
        "message": message,
        "fixture_id": fixture_id,
    }


def _set_violation(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _literal_bool(value: Any) -> bool:
    return value is True or value is False


def _finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _non_negative_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _non_negative_cost_or_null(value: Any) -> bool:
    return value is None or (_finite_number(value) and value >= 0)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _has_text(record: dict[str, Any], field: str) -> bool:
    return _non_empty_string(record.get(field))


def validate_fixture_record(record: Any) -> tuple[bool, list[dict[str, Any]]]:
    """Validate one offline replay fixture."""
    violations: list[dict[str, Any]] = []

    if not isinstance(record, dict):
        return False, [
            _violation(
                "FIXTURE_RECORD_MALFORMED",
                "<record>",
                "fixture record must be a dict",
                None,
            )
        ]

    fixture_id = str(record.get("fixture_id", "<missing>"))

    for field in sorted(REQUIRED_FIELDS):
        if field not in record:
            violations.append(
                _violation("FIXTURE_FIELD_REQUIRED", field, f"{field} is required", fixture_id)
            )

    for field in sorted(STRING_FIELDS):
        if field in record and not isinstance(record.get(field), str):
            violations.append(
                _violation(
                    "STRING_FIELD_REQUIRED",
                    field,
                    f"{field} must be a string",
                    fixture_id,
                )
            )

    for field in sorted(IDENTITY_STRING_FIELDS):
        if field in record and not _non_empty_string(record.get(field)):
            violations.append(
                _violation(
                    "NON_EMPTY_STRING_REQUIRED",
                    field,
                    f"{field} must be a non-empty string",
                    fixture_id,
                )
            )

    if record.get("not_runtime_authority") is not True:
        violations.append(
            _violation(
                "NOT_RUNTIME_AUTHORITY_REQUIRED",
                "not_runtime_authority",
                "not_runtime_authority must be literal true",
                fixture_id,
            )
        )

    if record.get("created_for_benchmark_only") is not True:
        violations.append(
            _violation(
                "CREATED_FOR_BENCHMARK_ONLY_REQUIRED",
                "created_for_benchmark_only",
                "created_for_benchmark_only must be literal true",
                fixture_id,
            )
        )

    for boolean_field in ["success", "human_review_required", "history_allowed"]:
        if not _literal_bool(record.get(boolean_field)):
            violations.append(
                _violation(
                    f"{boolean_field.upper()}_BOOLEAN_REQUIRED",
                    boolean_field,
                    f"{boolean_field} must be literal boolean true or false",
                    fixture_id,
                )
            )

    if record.get("success_basis") not in ALLOWED_SUCCESS_BASIS:
        violations.append(
            _violation(
                "SUCCESS_BASIS_REQUIRED",
                "success_basis",
                f"success_basis must be one of {sorted(ALLOWED_SUCCESS_BASIS)}",
                fixture_id,
            )
        )

    success = record.get("success")
    failure_reason = record.get("failure_reason")
    failure_reason_present = isinstance(failure_reason, str) and failure_reason.strip() != ""
    if success is True and failure_reason_present:
        violations.append(
            _violation(
                "SUCCESS_FAILURE_REASON_CONFLICT",
                "failure_reason",
                "success=true may not have failure_reason",
                fixture_id,
            )
        )
    if success is False and not failure_reason_present:
        violations.append(
            _violation(
                "FAILURE_REASON_REQUIRED",
                "failure_reason",
                "success=false requires non-empty failure_reason",
                fixture_id,
            )
        )

    if record.get("sensitivity_level") not in ALLOWED_SENSITIVITY_LEVELS:
        violations.append(
            _violation(
                "SENSITIVITY_LEVEL_UNKNOWN",
                "sensitivity_level",
                f"sensitivity_level must be one of {sorted(ALLOWED_SENSITIVITY_LEVELS)}",
                fixture_id,
            )
        )

    if record.get("intelligence_level") not in ALLOWED_INTELLIGENCE_LEVELS:
        violations.append(
            _violation(
                "INTELLIGENCE_LEVEL_UNKNOWN",
                "intelligence_level",
                f"intelligence_level must be one of {sorted(ALLOWED_INTELLIGENCE_LEVELS)}",
                fixture_id,
            )
        )

    if record.get("allowed_route_class") not in ALLOWED_ROUTE_CLASSES:
        violations.append(
            _violation(
                "ALLOWED_ROUTE_CLASS_UNKNOWN",
                "allowed_route_class",
                f"allowed_route_class must be one of {sorted(ALLOWED_ROUTE_CLASSES)}",
                fixture_id,
            )
        )

    if record.get("candidate_class") not in ALLOWED_CANDIDATE_CLASSES:
        violations.append(
            _violation(
                "CANDIDATE_CLASS_UNKNOWN",
                "candidate_class",
                f"candidate_class must be one of {sorted(ALLOWED_CANDIDATE_CLASSES)}",
                fixture_id,
            )
        )

    if record.get("cost_status") not in ALLOWED_COST_STATUS:
        violations.append(
            _violation(
                "COST_STATUS_UNKNOWN",
                "cost_status",
                f"cost_status must be one of {sorted(ALLOWED_COST_STATUS)}",
                fixture_id,
            )
        )

    for field in sorted(COUNT_FIELDS):
        if field in record and not _non_negative_integer(record.get(field)):
            violations.append(
                _violation(
                    "NON_NEGATIVE_INTEGER_REQUIRED",
                    field,
                    f"{field} must be a non-negative integer",
                    fixture_id,
                )
            )

    if "estimated_cost" in record and not _non_negative_cost_or_null(record.get("estimated_cost")):
        violations.append(
            _violation(
                "NON_NEGATIVE_COST_OR_NULL_REQUIRED",
                "estimated_cost",
                "estimated_cost must be a finite non-negative number or null",
                fixture_id,
            )
        )

    token_values_are_integers = all(
        _non_negative_integer(record.get(field))
        for field in ("input_token_count", "output_token_count", "total_token_count")
    )
    if token_values_are_integers and (
        record["total_token_count"] != record["input_token_count"] + record["output_token_count"]
    ):
        violations.append(
            _violation(
                "TOKEN_TOTAL_MISMATCH",
                "total_token_count",
                "total_token_count must equal input_token_count + output_token_count",
                fixture_id,
            )
        )

    estimated_cost = record.get("estimated_cost")
    cost_status = record.get("cost_status")
    if estimated_cost is None:
        if cost_status != "unavailable":
            violations.append(
                _violation(
                    "COST_STATUS_UNAVAILABLE_REQUIRED",
                    "cost_status",
                    "estimated_cost=null requires cost_status=unavailable",
                    fixture_id,
                )
            )
    elif _non_negative_cost_or_null(estimated_cost):
        if cost_status not in COST_PRESENT_STATUSES:
            violations.append(
                _violation(
                    "COST_STATUS_CONCRETE_REQUIRED",
                    "cost_status",
                    "estimated_cost present requires verified, estimated, or unverified cost_status",
                    fixture_id,
                )
            )
        if not _has_text(record, "cost_currency"):
            violations.append(
                _violation(
                    "COST_CURRENCY_REQUIRED",
                    "cost_currency",
                    "cost_currency is required when estimated_cost is present",
                    fixture_id,
                )
            )
        if not _has_text(record, "cost_source"):
            violations.append(
                _violation(
                    "COST_SOURCE_REQUIRED",
                    "cost_source",
                    "cost_source is required when estimated_cost is present",
                    fixture_id,
                )
            )
        if not (_has_text(record, "source_url") or _has_text(record, "source_note")):
            violations.append(
                _violation(
                    "COST_SOURCE_AUDIT_REFERENCE_REQUIRED",
                    "source_url/source_note",
                    "source_url or source_note is required when estimated_cost is present",
                    fixture_id,
                )
            )
        if not (_has_text(record, "source_checked_at") or _has_text(record, "source_checked_at_note")):
            violations.append(
                _violation(
                    "COST_SOURCE_CHECKED_AT_REQUIRED",
                    "source_checked_at/source_checked_at_note",
                    "source_checked_at or source_checked_at_note is required when estimated_cost is present",
                    fixture_id,
                )
            )

    return len(violations) == 0, violations


def _load_json_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("fixtures"), list):
        return data["fixtures"]
    raise BenchmarkFixtureError(f"{path} must contain a JSON list or an object with a fixtures list")


def load_replay_fixtures(fixture_dir: Path) -> list[dict[str, Any]]:
    """Load fixtures from JSON files in deterministic path order."""
    records: list[dict[str, Any]] = []
    for path in sorted(Path(fixture_dir).glob("*.json")):
        records.extend(_load_json_file(path))
    return records


def _safe_ratio(numerator: float, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _group_key(record: dict[str, Any], field: str) -> str:
    return str(record.get(field, "<missing>"))


def _compute_basic_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid_fixtures = len(records)
    successful_fixtures = sum(1 for record in records if record.get("success") is True)
    failed_fixtures = valid_fixtures - successful_fixtures

    fixtures_with_test_counts = sum(
        1
        for record in records
        if _non_negative_integer(record.get("tests_passed"))
        and _non_negative_integer(record.get("tests_failed"))
        and (record["tests_passed"] + record["tests_failed"] > 0)
    )
    fixtures_with_tests_passing = sum(
        1
        for record in records
        if _non_negative_integer(record.get("tests_passed"))
        and _non_negative_integer(record.get("tests_failed"))
        and (record["tests_passed"] + record["tests_failed"] > 0)
        and record["tests_failed"] == 0
    )

    fixtures_with_cost = sum(1 for record in records if record.get("estimated_cost") is not None)
    fixtures_without_cost = valid_fixtures - fixtures_with_cost
    cost_coverage = _safe_ratio(float(fixtures_with_cost), valid_fixtures)
    cost_data_complete = valid_fixtures > 0 and fixtures_without_cost == 0

    currencies = {
        record.get("cost_currency")
        for record in records
        if record.get("estimated_cost") is not None
    }
    mixed_currencies = len(currencies) > 1

    known_cost_total = sum(
        float(record.get("estimated_cost"))
        for record in records
        if record.get("estimated_cost") is not None
    )

    if mixed_currencies:
        total_estimated_cost = None
        partial_cost_per_success = None
        cost_per_success = None
        cost_per_success_selection_valid = False
    else:
        total_estimated_cost = known_cost_total if fixtures_with_cost > 0 else None
        partial_cost_per_success = (
            known_cost_total / successful_fixtures
            if successful_fixtures > 0 and fixtures_with_cost > 0 and not cost_data_complete
            else None
        )
        cost_per_success_selection_valid = (
            cost_data_complete and successful_fixtures > 0 and valid_fixtures > 0
        )
        cost_per_success = (
            known_cost_total / successful_fixtures if cost_per_success_selection_valid else None
        )

    human_review_required_count = sum(
        1 for record in records if record.get("human_review_required") is True
    )

    total_input = sum(record.get("input_token_count") for record in records)
    total_output = sum(record.get("output_token_count") for record in records)
    total_tokens = sum(record.get("total_token_count") for record in records)
    total_retries = sum(record.get("retry_count") for record in records)
    tool_call_count_total = sum(record.get("tool_call_count") for record in records)

    return {
        "valid_fixtures": valid_fixtures,
        "successful_fixtures": successful_fixtures,
        "failed_fixtures": failed_fixtures,
        "success_rate": _safe_ratio(float(successful_fixtures), valid_fixtures),
        "success_rate_denominator": "valid_fixtures",
        "fixtures_with_test_counts": fixtures_with_test_counts,
        "tests_pass_rate": _safe_ratio(
            float(fixtures_with_tests_passing), fixtures_with_test_counts
        ),
        "tests_pass_rate_denominator": "fixtures_with_test_counts",
        "fixtures_with_cost": fixtures_with_cost,
        "fixtures_without_cost": fixtures_without_cost,
        "cost_coverage": cost_coverage,
        "cost_coverage_denominator": "valid_fixtures",
        "cost_data_complete": cost_data_complete,
        "mixed_cost_currencies": mixed_currencies,
        "cost_currency": next(iter(currencies)) if len(currencies) == 1 else None,
        "total_estimated_cost": total_estimated_cost,
        "partial_cost_per_success": partial_cost_per_success,
        "partial_cost_per_success_authoritative": False,
        "cost_per_success": cost_per_success,
        "cost_per_success_selection_valid": cost_per_success_selection_valid,
        "average_input_tokens": _safe_ratio(float(total_input), valid_fixtures),
        "average_output_tokens": _safe_ratio(float(total_output), valid_fixtures),
        "average_total_tokens": _safe_ratio(float(total_tokens), valid_fixtures),
        "average_retry_count": _safe_ratio(float(total_retries), valid_fixtures),
        "tool_call_count_total": tool_call_count_total,
        "human_review_required_rate": _safe_ratio(
            float(human_review_required_count), valid_fixtures
        ),
        "human_review_required_rate_denominator": "valid_fixtures",
    }


def _group_metrics(records: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(_group_key(record, field), []).append(record)
    return {key: _compute_basic_metrics(value) for key, value in sorted(grouped.items())}


def _duplicate_records(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: dict[tuple[str, str], int] = {}
    duplicates: list[dict[str, str]] = []
    for record in records:
        key = (str(record.get("fixture_id", "")), str(record.get("candidate_label", "")))
        seen[key] = seen.get(key, 0) + 1
    for (fixture_id, candidate_label), count in sorted(seen.items()):
        if count > 1:
            duplicates.append(
                {
                    "fixture_id": fixture_id,
                    "candidate_label": candidate_label,
                    "count": str(count),
                }
            )
    return duplicates


def _candidate_coverage(records: list[dict[str, Any]]) -> tuple[bool, dict[str, list[str]]]:
    all_fixture_ids = {str(record.get("fixture_id")) for record in records}
    candidate_to_fixture_ids: dict[str, set[str]] = {}
    for record in records:
        candidate_to_fixture_ids.setdefault(str(record.get("candidate_label")), set()).add(
            str(record.get("fixture_id"))
        )
    complete = (
        len(records) > 0
        and len(candidate_to_fixture_ids) > 0
        and all(ids == all_fixture_ids for ids in candidate_to_fixture_ids.values())
    )
    return complete, {key: sorted(value) for key, value in sorted(candidate_to_fixture_ids.items())}


def _fixture_definition_conflicts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get("fixture_id")), []).append(record)

    conflicts: list[dict[str, Any]] = []
    for fixture_id, items in sorted(grouped.items()):
        projections = [_comparable_fixture_projection(record) for record in items]
        first = projections[0] if projections else {}
        conflicting_fields = sorted(
            field
            for field in COMPARABLE_FIXTURE_FIELDS
            if any(projection.get(field) != first.get(field) for projection in projections[1:])
        )
        if conflicting_fields:
            conflicts.append(
                {
                    "fixture_id": fixture_id,
                    "conflicting_fields": conflicting_fields,
                    "candidate_labels": sorted(str(record.get("candidate_label")) for record in items),
                }
            )
    return conflicts


def _primary_winner_basis(reasons: list[str]) -> str | None:
    reason_set = set(reasons)
    for reason in WINNER_BLOCKING_REASON_PRIORITY:
        if reason in reason_set:
            return reason
    return None


def replay_benchmark_records(records: list[Any]) -> dict[str, Any]:
    """Replay stored offline benchmark records and compute deterministic metrics."""
    immutable_input = copy.deepcopy(list(records))

    sorted_records = sorted(
        list(records),
        key=lambda item: (
            str(item.get("fixture_id", "")) if isinstance(item, dict) else "",
            str(item.get("candidate_label", "")) if isinstance(item, dict) else "",
        ),
    )

    validation_results: list[dict[str, Any]] = []
    candidate_valid_records: list[dict[str, Any]] = []

    for record in sorted_records:
        is_valid, violations = validate_fixture_record(record)
        fixture_id = record.get("fixture_id") if isinstance(record, dict) else None
        candidate_label = record.get("candidate_label") if isinstance(record, dict) else None
        validation_results.append(
            {
                "fixture_id": fixture_id,
                "candidate_label": candidate_label,
                "valid": is_valid,
                "violations": violations,
            }
        )
        if is_valid and isinstance(record, dict):
            copied = dict(record)
            copied["fixture_record_digest"] = compute_fixture_record_digest(copied)
            candidate_valid_records.append(copied)

    duplicates = _duplicate_records(candidate_valid_records)
    duplicate_keys = {
        (item["fixture_id"], item["candidate_label"])
        for item in duplicates
    }

    valid_records = [
        record
        for record in candidate_valid_records
        if (str(record.get("fixture_id")), str(record.get("candidate_label"))) not in duplicate_keys
    ]
    fixture_definition_conflicts = _fixture_definition_conflicts(valid_records)

    invalid_fixture_ids = sorted(
        {
            str(result.get("fixture_id"))
            for result in validation_results
            if not result["valid"] and result.get("fixture_id") is not None
        }
        | {item["fixture_id"] for item in duplicates}
    )

    suite_ids = {record.get("benchmark_suite_id") for record in valid_records}
    suite_versions = {record.get("suite_version") for record in valid_records}
    benchmark_suite_id = next(iter(suite_ids)) if len(suite_ids) == 1 else None
    suite_version = next(iter(suite_versions)) if len(suite_versions) == 1 else None
    comparable_suite = len(suite_ids) <= 1 and len(suite_versions) <= 1

    replay_set_violations: list[dict[str, str]] = []
    if len(suite_ids) > 1:
        replay_set_violations.append(
            _set_violation("MIXED_BENCHMARK_SUITE_ID", "replay set has mixed benchmark_suite_id values")
        )
    if len(suite_versions) > 1:
        replay_set_violations.append(
            _set_violation("MIXED_SUITE_VERSION", "replay set has mixed suite_version values")
        )
    if duplicates:
        replay_set_violations.append(
            _set_violation("DUPLICATE_FIXTURE_RECORDS", "replay set has duplicate fixture/candidate records")
        )
    if fixture_definition_conflicts:
        replay_set_violations.append(
            _set_violation("FIXTURE_DEFINITION_CONFLICT", "same fixture_id has conflicting comparable definitions")
        )

    replay_valid = len(invalid_fixture_ids) == 0 and not replay_set_violations

    fixture_set_digest = compute_fixture_set_digest(valid_records)
    replay_set_digest = compute_replay_set_digest(valid_records)

    basic = _compute_basic_metrics(valid_records)
    total_fixtures = len(records)
    invalid_fixtures = total_fixtures - len(valid_records)

    candidate_fixture_coverage_complete, candidate_fixture_coverage = _candidate_coverage(valid_records)
    candidate_count = len(candidate_fixture_coverage)

    cost_based_winner_valid = (
        replay_valid
        and basic["cost_data_complete"] is True
        and basic["mixed_cost_currencies"] is False
        and candidate_fixture_coverage_complete
        and comparable_suite
        and candidate_count >= 2
    )

    candidate_metrics = _group_metrics(valid_records, "candidate_label")
    winner_blocking_reasons: list[str] = []
    if invalid_fixture_ids:
        winner_blocking_reasons.append("invalid_fixtures")
    if fixture_definition_conflicts:
        winner_blocking_reasons.append("fixture_definition_conflict")
    if not comparable_suite:
        winner_blocking_reasons.append("mixed_suite_or_version")
    if not candidate_fixture_coverage_complete:
        winner_blocking_reasons.append("candidate_fixture_coverage_incomplete")
    if duplicates:
        winner_blocking_reasons.append("duplicate_fixture_records")
    if basic["mixed_cost_currencies"] is True:
        winner_blocking_reasons.append("mixed_currency_without_conversion")
    if basic["cost_data_complete"] is not True:
        winner_blocking_reasons.append("cost_data_incomplete")
    if candidate_count < 2:
        winner_blocking_reasons.append("insufficient_candidate_count")

    benchmark_winner: str | None = None
    benchmark_winner_basis: str | None = _primary_winner_basis(winner_blocking_reasons)
    benchmark_winner_selection_valid = False

    if cost_based_winner_valid:
        eligible = {
            label: metrics
            for label, metrics in candidate_metrics.items()
            if metrics.get("cost_per_success_selection_valid") is True
            and metrics.get("cost_per_success") is not None
        }
        if eligible:
            sorted_eligible = sorted(eligible)
            best_cost = min(eligible[label]["cost_per_success"] for label in sorted_eligible)
            tied = [label for label in sorted_eligible if eligible[label]["cost_per_success"] == best_cost]
            if len(tied) == 1:
                benchmark_winner = tied[0]
                benchmark_winner_basis = "lowest_cost_per_success_on_complete_comparable_fixture_set"
                benchmark_winner_selection_valid = True
            else:
                benchmark_winner = None
                if "tie_on_cost_per_success" not in winner_blocking_reasons:
                    winner_blocking_reasons.append("tie_on_cost_per_success")
                benchmark_winner_basis = _primary_winner_basis(winner_blocking_reasons)
                benchmark_winner_selection_valid = False

    result = {
        "benchmark_suite_id": benchmark_suite_id,
        "suite_version": suite_version,
        "fixture_set_digest": fixture_set_digest,
        "replay_set_digest": replay_set_digest,
        "replay_valid": replay_valid,
        "replay_set_violations": replay_set_violations,
        "total_fixtures": total_fixtures,
        "invalid_fixtures": invalid_fixtures,
        "invalid_fixture_ids": invalid_fixture_ids,
        "duplicate_fixture_records": duplicates,
        "fixture_definition_conflicts": fixture_definition_conflicts,
        **basic,
        "candidate_count": candidate_count,
        "candidate_fixture_coverage": candidate_fixture_coverage,
        "candidate_fixture_coverage_complete": candidate_fixture_coverage_complete,
        "benchmark_winner": benchmark_winner,
        "benchmark_winner_basis": benchmark_winner_basis,
        "winner_blocking_reasons": winner_blocking_reasons,
        "benchmark_winner_selection_valid": benchmark_winner_selection_valid,
        "benchmark_winner_is_provider_permission": False,
        "benchmark_replay_result_is_runtime_route_permission": False,
        "provider_permission_granted": False,
        "network_permission_granted": False,
        "execution_permission_granted": False,
        "records": sorted(
            [
                {
                    "fixture_id": record.get("fixture_id"),
                    "candidate_label": record.get("candidate_label"),
                    "success": record.get("success"),
                    "fixture_record_digest": record.get("fixture_record_digest"),
                }
                for record in valid_records
            ],
            key=lambda item: (str(item["fixture_id"]), str(item["candidate_label"])),
        ),
        "validation_results": validation_results,
        "group_metrics": {
            "candidate_label": candidate_metrics,
            "candidate_class": _group_metrics(valid_records, "candidate_class"),
            "task_type": _group_metrics(valid_records, "task_type"),
            "sensitivity_level": _group_metrics(valid_records, "sensitivity_level"),
            "intelligence_level": _group_metrics(valid_records, "intelligence_level"),
        },
    }

    if immutable_input != list(records):
        raise RuntimeError("replay_benchmark_records mutated input records")

    return result


def replay_fixture_dir(fixture_dir: Path) -> dict[str, Any]:
    return replay_benchmark_records(load_replay_fixtures(fixture_dir))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay offline JarvisOS routing benchmark fixtures."
    )
    parser.add_argument("fixture_dir", type=Path)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)

    result = replay_fixture_dir(args.fixture_dir)
    rendered = json.dumps(result, indent=2, sort_keys=True)

    if args.output_json:
        args.output_json.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 0 if result.get("replay_valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
