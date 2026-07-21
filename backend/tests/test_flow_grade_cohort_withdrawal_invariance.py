from __future__ import annotations

import pytest
import test_flow_grade_cohorts as cohort_tests

from app.modules.ai.flow_grade_cohort_contracts import execution_composition
from app.modules.ai.flow_grade_cohorts import get_flow_grade_cohort
from app.modules.ai.flow_grade_events import withdraw_flow_grade
from app.modules.ai.flow_grade_subjects import ensure_flow_grade_subject

initialized_database = cohort_tests.initialized_database


def test_withdrawal_preserves_failure_and_economic_denominators(
    initialized_database,
) -> None:
    failed_flow = cohort_tests._seed_flow(
        execution_class="external_provider",
        dispatch_state="started",
        accounting_basis="provider_exact",
        spend="4",
        status="provider_error",
    )
    useful_flow = cohort_tests._seed_flow(
        execution_class="external_provider",
        dispatch_state="started",
        accounting_basis="provider_exact",
        spend="2",
    )
    failed_head = cohort_tests._grade(
        failed_flow,
        "failed",
        "failed-before-withdrawal",
    )
    cohort_tests._grade(useful_flow, "useful", "useful-control")

    before = get_flow_grade_cohort()
    subject = ensure_flow_grade_subject(failed_flow)
    withdraw_flow_grade(
        flow_id=failed_flow,
        expected_subject_version=int(subject["subject_version"]),
        expected_flow_outcome_digest=str(subject["flow_outcome_digest"]),
        expected_current_grade_event_id=str(failed_head["id"]),
        idempotency_key="withdraw-failed-grade",
    )
    after = get_flow_grade_cohort()

    assert before.terminal_flow_count == after.terminal_flow_count == 2
    assert before.deterministic_failure_rate == pytest.approx(0.5)
    assert after.deterministic_failure_rate == before.deterministic_failure_rate
    assert before.eligible_external_provider_spend_usd_total == "6"
    assert after.eligible_external_provider_spend_usd_total == "6"
    assert before.external_provider_spend_per_useful_outcome_usd == "6"
    assert after.external_provider_spend_per_useful_outcome_usd == "6"
    assert before.grade_coverage == pytest.approx(1.0)
    assert after.grade_coverage == pytest.approx(0.5)
    assert after.current_grade_counts["failed"] == 0
    assert after.current_grade_counts["ungraded"] == 1


def test_legacy_execution_is_never_reported_as_no_adapter_execution() -> None:
    assert execution_composition({"legacy_unknown"}) == "mixed_executed_classes"
    assert execution_composition({"local_compute", "legacy_unknown"}) == (
        "mixed_executed_classes"
    )
