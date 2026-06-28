from __future__ import annotations

import copy
import inspect
import json
import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_benchmark_replay as replay  # noqa: E402


def fixture(
    *,
    fixture_id="fixture-001",
    candidate_label="candidate-a",
    candidate_class="local",
    success=True,
    estimated_cost=1.0,
    cost_currency="USD",
    cost_source="stored_fixture",
    cost_status=None,
    source_note="fixture-local synthetic cost for offline harness test",
    source_checked_at_note="not live; stored fixture only",
    tests_passed=1,
    tests_failed=0,
    benchmark_suite_id="suite-a",
    suite_version="v1",
    input_token_count=100,
    output_token_count=50,
    total_token_count=150,
    failure_reason=None,
    **overrides,
):
    record = {
        "benchmark_suite_id": benchmark_suite_id,
        "suite_version": suite_version,
        "fixture_id": fixture_id,
        "fixture_version": "v1",
        "fixture_record_digest": None,
        "fixture_set_digest": None,
        "replay_set_digest": None,
        "task_type": "patch_review",
        "sensitivity_level": "S1",
        "intelligence_level": "I2",
        "allowed_route_class": "local",
        "candidate_label": candidate_label,
        "candidate_class": candidate_class,
        "input_digest": "sha256:input",
        "input_token_count": input_token_count,
        "output_token_count": output_token_count,
        "total_token_count": total_token_count,
        "estimated_cost": estimated_cost,
        "cost_currency": cost_currency,
        "cost_source": cost_source,
        "cost_status": cost_status if cost_status is not None else ("estimated" if estimated_cost is not None else "unavailable"),
        "source_note": source_note,
        "source_checked_at_note": source_checked_at_note,
        "expected_outcome": "tests pass",
        "observed_outcome": "tests pass" if success else "tests fail",
        "success": success,
        "success_basis": "unit_tests",
        "failure_reason": failure_reason if failure_reason is not None else (None if success else "tests_failed"),
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "human_review_required": False,
        "retry_count": 0,
        "tool_call_count": 0,
        "cache_status": "miss",
        "context_size_bucket": "small",
        "history_allowed": False,
        "created_for_benchmark_only": True,
        "not_runtime_authority": True,
    }
    record.update(overrides)
    return record


def no_cost_fixture(**overrides):
    defaults = {
        "estimated_cost": None,
        "cost_currency": None,
        "cost_source": None,
        "cost_status": "unavailable",
        "source_note": None,
        "source_checked_at_note": None,
    }
    defaults.update(overrides)
    return fixture(**defaults)


def complete_comparable_records():
    return [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", success=True, estimated_cost=1.0),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", success=True, estimated_cost=1.0),
        fixture(fixture_id="fixture-001", candidate_label="candidate-b", success=True, estimated_cost=2.0),
        fixture(fixture_id="fixture-002", candidate_label="candidate-b", success=True, estimated_cost=2.0),
    ]


def test_valid_fixture_replay_and_winner_on_complete_comparable_costs():
    result = replay.replay_benchmark_records(complete_comparable_records())

    assert result["replay_valid"] is True
    assert result["total_fixtures"] == 4
    assert result["valid_fixtures"] == 4
    assert result["invalid_fixtures"] == 0
    assert result["cost_data_complete"] is True
    assert result["candidate_fixture_coverage_complete"] is True
    assert result["candidate_count"] == 2
    assert result["benchmark_winner"] == "candidate-a"
    assert result["benchmark_winner_selection_valid"] is True
    assert result["benchmark_winner_is_provider_permission"] is False
    assert result["provider_permission_granted"] is False


def test_multiple_fixture_aggregation_and_group_metrics():
    result = replay.replay_benchmark_records(complete_comparable_records())

    assert result["success_rate"] == 1.0
    assert result["success_rate_denominator"] == "valid_fixtures"
    assert result["tests_pass_rate"] == 1.0
    assert result["tests_pass_rate_denominator"] == "fixtures_with_test_counts"
    assert result["human_review_required_rate_denominator"] == "valid_fixtures"
    assert set(result["group_metrics"]["candidate_label"]) == {"candidate-a", "candidate-b"}


def test_cost_per_success_null_when_zero_successes():
    records = [
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-a",
            success=False,
            estimated_cost=1.0,
            tests_passed=0,
            tests_failed=1,
        ),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["successful_fixtures"] == 0
    assert result["cost_per_success"] is None
    assert result["cost_per_success_selection_valid"] is False


def test_partial_cost_coverage_is_non_authoritative_for_selection():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", success=True, estimated_cost=1.0),
        no_cost_fixture(fixture_id="fixture-002", candidate_label="candidate-a", success=True),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["cost_coverage"] == 0.5
    assert result["cost_data_complete"] is False
    assert result["cost_per_success"] is None
    assert result["partial_cost_per_success"] == 0.5
    assert result["partial_cost_per_success_authoritative"] is False
    assert result["cost_per_success_selection_valid"] is False
    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_basis"] == "cost_data_incomplete"
    assert result["winner_blocking_reasons"] == ["cost_data_incomplete", "insufficient_candidate_count"]


def test_mixed_currencies_invalidate_cost_metrics_without_conversion():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0, cost_currency="USD"),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", estimated_cost=1.0, cost_currency="EUR"),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["mixed_cost_currencies"] is True
    assert result["total_estimated_cost"] is None
    assert result["cost_per_success"] is None
    assert result["benchmark_winner"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("not_runtime_authority", "true"),
        ("created_for_benchmark_only", 1),
        ("success", "yes"),
        ("human_review_required", "false"),
        ("history_allowed", 1),
    ],
)
def test_truthy_boolean_values_are_invalid(field, value):
    record = fixture(**{field: value})
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert violations


def test_invalid_missing_not_runtime_authority():
    record = fixture()
    record.pop("not_runtime_authority")

    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert {item["code"] for item in violations} >= {"FIXTURE_FIELD_REQUIRED", "NOT_RUNTIME_AUTHORITY_REQUIRED"}


def test_invalid_created_for_benchmark_only_false():
    valid, violations = replay.validate_fixture_record(fixture(created_for_benchmark_only=False))

    assert valid is False
    assert any(item["code"] == "CREATED_FOR_BENCHMARK_ONLY_REQUIRED" for item in violations)


def test_invalid_negative_token_count_and_negative_cost():
    record = fixture(input_token_count=-1, estimated_cost=-0.1)

    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "NON_NEGATIVE_INTEGER_REQUIRED" for item in violations)
    assert any(item["code"] == "NON_NEGATIVE_COST_OR_NULL_REQUIRED" for item in violations)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("sensitivity_level", "S9", "SENSITIVITY_LEVEL_UNKNOWN"),
        ("intelligence_level", "I9", "INTELLIGENCE_LEVEL_UNKNOWN"),
        ("candidate_class", "cloud:frontier", "CANDIDATE_CLASS_UNKNOWN"),
    ],
)
def test_invalid_unknown_levels_and_candidate_class(field, value, code):
    valid, violations = replay.validate_fixture_record(fixture(**{field: value}))

    assert valid is False
    assert any(item["code"] == code for item in violations)


def test_invalid_missing_success_basis():
    record = fixture()
    record.pop("success_basis")

    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "SUCCESS_BASIS_REQUIRED" for item in violations)


def test_invalid_duplicate_fixture_candidate_record():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a"),
        fixture(fixture_id="fixture-001", candidate_label="candidate-a"),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["replay_valid"] is False
    assert result["duplicate_fixture_records"] == [
        {"fixture_id": "fixture-001", "candidate_label": "candidate-a", "count": "2"}
    ]
    assert result["benchmark_winner"] is None


def test_invalid_fixtures_excluded_from_aggregates_but_replay_invalid():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", success=True),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", success="true"),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["replay_valid"] is False
    assert result["valid_fixtures"] == 1
    assert result["invalid_fixtures"] == 1
    assert result["successful_fixtures"] == 1
    assert "fixture-002" in result["invalid_fixture_ids"]


def test_candidate_ranking_invalid_when_fixture_sets_differ():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(fixture_id="fixture-001", candidate_label="candidate-b", estimated_cost=2.0),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", estimated_cost=1.0),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["candidate_fixture_coverage_complete"] is False
    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_selection_valid"] is False
    assert result["benchmark_winner_basis"] == "candidate_fixture_coverage_incomplete"
    assert "candidate_fixture_coverage_incomplete" in result["winner_blocking_reasons"]


def test_candidate_ranking_valid_only_with_complete_coverage():
    result = replay.replay_benchmark_records(complete_comparable_records())

    assert result["candidate_fixture_coverage_complete"] is True
    assert result["benchmark_winner_selection_valid"] is True


def test_single_candidate_cannot_produce_selection_grade_winner():
    result = replay.replay_benchmark_records([
        fixture(fixture_id="fixture-001", candidate_label="only", estimated_cost=1.0),
        fixture(fixture_id="fixture-002", candidate_label="only", estimated_cost=1.0),
    ])

    assert result["replay_valid"] is True
    assert result["candidate_count"] == 1
    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_selection_valid"] is False
    assert result["benchmark_winner_basis"] == "insufficient_candidate_count"


def test_tie_does_not_produce_selection_grade_winner():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(fixture_id="fixture-001", candidate_label="candidate-b", estimated_cost=1.0),
        fixture(fixture_id="fixture-002", candidate_label="candidate-b", estimated_cost=1.0),
    ]
    result = replay.replay_benchmark_records(records)

    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_selection_valid"] is False
    assert result["benchmark_winner_basis"] == "tie_on_cost_per_success"
    assert result["winner_blocking_reasons"] == ["tie_on_cost_per_success"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_digest", "sha256:different-input"),
        ("expected_outcome", "different expected outcome"),
        ("sensitivity_level", "S2"),
        ("task_type", "different_task_type"),
    ],
)
def test_same_fixture_id_with_different_comparable_definition_invalidates_replay(field, value):
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(fixture_id="fixture-001", candidate_label="candidate-b", estimated_cost=2.0, **{field: value}),
    ]

    result = replay.replay_benchmark_records(records)

    assert result["replay_valid"] is False
    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_selection_valid"] is False
    assert result["benchmark_winner_basis"] == "fixture_definition_conflict"
    assert "fixture_definition_conflict" in result["winner_blocking_reasons"]
    assert any(item["code"] == "FIXTURE_DEFINITION_CONFLICT" for item in result["replay_set_violations"])
    assert result["fixture_definition_conflicts"] == [
        {
            "fixture_id": "fixture-001",
            "conflicting_fields": [field],
            "candidate_labels": ["candidate-a", "candidate-b"],
        }
    ]


def test_same_fixture_id_with_different_input_token_count_only_stays_comparable():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-b",
            estimated_cost=2.0,
            input_token_count=101,
            total_token_count=151,
        ),
    ]

    result = replay.replay_benchmark_records(records)

    assert result["replay_valid"] is True
    assert result["fixture_definition_conflicts"] == []
    assert "fixture_definition_conflict" not in result["winner_blocking_reasons"]
    assert result["benchmark_winner"] == "candidate-a"
    assert result["benchmark_winner_selection_valid"] is True


def test_fixture_definition_conflict_blocks_winner_even_with_complete_cost_data():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-b",
            estimated_cost=2.0,
            expected_outcome="different expected outcome",
        ),
    ]

    result = replay.replay_benchmark_records(records)

    assert result["cost_data_complete"] is True
    assert result["candidate_fixture_coverage_complete"] is True
    assert result["benchmark_winner"] is None
    assert result["benchmark_winner_selection_valid"] is False
    assert result["benchmark_winner_basis"] == "fixture_definition_conflict"


def test_winner_blocking_basis_uses_severity_priority_with_multiple_reasons():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-b",
            estimated_cost=2.0,
            expected_outcome="different expected outcome",
        ),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", success="true"),
    ]

    result = replay.replay_benchmark_records(records)

    assert "invalid_fixtures" in result["winner_blocking_reasons"]
    assert "fixture_definition_conflict" in result["winner_blocking_reasons"]
    assert result["benchmark_winner_basis"] == "invalid_fixtures"


def test_valid_same_fixture_id_across_candidates_with_identical_projection_passes():
    result = replay.replay_benchmark_records([
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(fixture_id="fixture-001", candidate_label="candidate-b", estimated_cost=2.0),
    ])

    assert result["replay_valid"] is True
    assert result["fixture_definition_conflicts"] == []
    assert result["benchmark_winner"] == "candidate-a"
    assert result["benchmark_winner_selection_valid"] is True


def test_fixture_set_digest_includes_all_conflicting_fixture_definitions_deterministically():
    records = [
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0),
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-b",
            estimated_cost=2.0,
            expected_outcome="different expected outcome",
        ),
    ]

    conflict = replay.replay_benchmark_records(records)
    reversed_conflict = replay.replay_benchmark_records(list(reversed(records)))
    first_only = replay.replay_benchmark_records([records[0]])

    assert conflict["fixture_definition_conflicts"]
    assert conflict["fixture_set_digest"] == reversed_conflict["fixture_set_digest"]
    assert conflict["fixture_set_digest"] != first_only["fixture_set_digest"]


def test_deterministic_replay_output_ordering_and_digest_independent_of_input_order():
    records_a = [
        fixture(fixture_id="fixture-002", candidate_label="candidate-b"),
        fixture(fixture_id="fixture-001", candidate_label="candidate-a"),
    ]
    records_b = list(reversed(records_a))

    result_a = replay.replay_benchmark_records(records_a)
    result_b = replay.replay_benchmark_records(records_b)

    assert result_a["records"] == result_b["records"]
    assert result_a["fixture_set_digest"] == result_b["fixture_set_digest"]
    assert result_a["replay_set_digest"] == result_b["replay_set_digest"]
    assert [item["fixture_id"] for item in result_a["records"]] == ["fixture-001", "fixture-002"]


def test_fixture_set_digest_excludes_candidate_result_and_cost_fields():
    records_a = [fixture(fixture_id="fixture-001", candidate_label="candidate-a", estimated_cost=1.0)]
    records_b = [
        fixture(
            fixture_id="fixture-001",
            candidate_label="candidate-b",
            estimated_cost=9.0,
            observed_outcome="different replay result",
        )
    ]

    result_a = replay.replay_benchmark_records(records_a)
    result_b = replay.replay_benchmark_records(records_b)

    assert result_a["fixture_set_digest"] == result_b["fixture_set_digest"]
    assert result_a["replay_set_digest"] != result_b["replay_set_digest"]


def test_canonical_fixture_record_digest_excludes_digest_fields():
    record = fixture()
    first = replay.compute_fixture_record_digest(record)

    record["fixture_record_digest"] = "wrong"
    record["fixture_set_digest"] = "also-wrong"
    record["replay_set_digest"] = "set-wrong"
    second = replay.compute_fixture_record_digest(record)

    assert first == second


def test_metric_denominator_zero_returns_null_not_zero():
    result = replay.replay_benchmark_records([fixture(success="true")])

    assert result["replay_valid"] is False
    assert result["valid_fixtures"] == 0
    assert result["success_rate"] is None
    assert result["tests_pass_rate"] is None
    assert result["human_review_required_rate"] is None


def test_zero_test_counts_do_not_count_as_tests_passing():
    result = replay.replay_benchmark_records([
        fixture(tests_passed=0, tests_failed=0),
    ])

    assert result["valid_fixtures"] == 1
    assert result["fixtures_with_test_counts"] == 0
    assert result["tests_pass_rate"] is None


def test_replay_from_directory_is_filesystem_order_independent(tmp_path):
    left = tmp_path / "b.json"
    right = tmp_path / "a.json"
    left.write_text(json.dumps([fixture(fixture_id="fixture-002", candidate_label="candidate-b")]), encoding="utf-8")
    right.write_text(json.dumps([fixture(fixture_id="fixture-001", candidate_label="candidate-a")]), encoding="utf-8")

    result = replay.replay_fixture_dir(tmp_path)

    assert [item["fixture_id"] for item in result["records"]] == ["fixture-001", "fixture-002"]


def test_no_semantic_similarity_inference_fields_required():
    record = fixture(expected_outcome="patch is fine", observed_outcome="patch is fine")
    record.pop("success_basis")

    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "SUCCESS_BASIS_REQUIRED" for item in violations)


def test_replay_does_not_mutate_input_records():
    records = complete_comparable_records()
    before = copy.deepcopy(records)

    result = replay.replay_benchmark_records(records)

    assert result["replay_valid"] is True
    assert records == before


def test_concrete_cost_requires_auditable_source_reference_and_checked_at():
    record = fixture(source_note=None, source_url=None)
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "COST_SOURCE_AUDIT_REFERENCE_REQUIRED" for item in violations)

    record = fixture(source_checked_at=None, source_checked_at_note=None)
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "COST_SOURCE_CHECKED_AT_REQUIRED" for item in violations)


@pytest.mark.parametrize(
    "record,expected_code",
    [
        (no_cost_fixture(cost_status="estimated"), "COST_STATUS_UNAVAILABLE_REQUIRED"),
        (fixture(estimated_cost=1.0, cost_status="unavailable"), "COST_STATUS_CONCRETE_REQUIRED"),
    ],
)
def test_cost_status_consistency(record, expected_code):
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == expected_code for item in violations)


def test_token_total_mismatch_is_invalid():
    valid, violations = replay.validate_fixture_record(fixture(total_token_count=151))

    assert valid is False
    assert any(item["code"] == "TOKEN_TOTAL_MISMATCH" for item in violations)


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_token_count", 1.5),
        ("output_token_count", "50"),
        ("total_token_count", math.inf),
        ("tests_passed", 1.0),
        ("tests_failed", "0"),
        ("retry_count", -1),
        ("tool_call_count", -1),
    ],
)
def test_invalid_integer_count_fields(field, value):
    record = fixture(**{field: value})
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "NON_NEGATIVE_INTEGER_REQUIRED" for item in violations)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "1.0", True, -0.01])
def test_invalid_estimated_cost_finite_non_negative_or_null(value):
    record = fixture(estimated_cost=value)
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "NON_NEGATIVE_COST_OR_NULL_REQUIRED" for item in violations)


@pytest.mark.parametrize("field", ["fixture_id", "candidate_label", "benchmark_suite_id", "suite_version"])
def test_identity_fields_must_be_non_empty_strings(field):
    record = fixture(**{field: ""})
    valid, violations = replay.validate_fixture_record(record)

    assert valid is False
    assert any(item["code"] == "NON_EMPTY_STRING_REQUIRED" for item in violations)


def test_mixed_benchmark_suite_id_invalidates_replay():
    result = replay.replay_benchmark_records([
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", benchmark_suite_id="suite-a"),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", benchmark_suite_id="suite-b"),
    ])

    assert result["replay_valid"] is False
    assert any(item["code"] == "MIXED_BENCHMARK_SUITE_ID" for item in result["replay_set_violations"])


def test_mixed_suite_version_invalidates_replay():
    result = replay.replay_benchmark_records([
        fixture(fixture_id="fixture-001", candidate_label="candidate-a", suite_version="v1"),
        fixture(fixture_id="fixture-002", candidate_label="candidate-a", suite_version="v2"),
    ])

    assert result["replay_valid"] is False
    assert any(item["code"] == "MIXED_SUITE_VERSION" for item in result["replay_set_violations"])


def test_success_failure_reason_consistency():
    valid, violations = replay.validate_fixture_record(fixture(success=True, failure_reason="should-not-exist"))
    assert valid is False
    assert any(item["code"] == "SUCCESS_FAILURE_REASON_CONFLICT" for item in violations)

    valid, violations = replay.validate_fixture_record(fixture(success=False, failure_reason=""))
    assert valid is False
    assert any(item["code"] == "FAILURE_REASON_REQUIRED" for item in violations)


def test_unknown_success_basis_is_invalid():
    valid, violations = replay.validate_fixture_record(fixture(success_basis="semantic_similarity"))

    assert valid is False
    assert any(item["code"] == "SUCCESS_BASIS_REQUIRED" for item in violations)


def test_demo_fixture_has_no_cost_and_no_selection_grade_winner():
    fixture_dir = ROOT / "tests" / "fixtures" / "routing_benchmarks"
    if fixture_dir.exists():
        result = replay.replay_fixture_dir(fixture_dir)
        assert result["replay_valid"] is True
        assert result["cost_data_complete"] is False
        assert result["benchmark_winner"] is None
        assert result["benchmark_winner_selection_valid"] is False


def test_no_network_provider_env_usage_in_source():
    source = inspect.getsource(replay)

    forbidden = [
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "gemini",
        "os.environ",
        "dotenv",
        "API_KEY",
        "Bearer",
    ]
    for token in forbidden:
        assert token not in source
