from __future__ import annotations

import json
from uuid import uuid4

import pytest
import test_token_flow_local_runtime_integration as local
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.flow_grade_cohorts import get_flow_grade_cohort
from app.modules.ai.flow_grade_events import set_flow_grade, withdraw_flow_grade
from app.modules.ai.flow_grade_subjects import ensure_flow_grade_subject
from app.modules.ai.routes import router
from app.modules.events.service import utc_now

initialized_database = local.initialized_database


def _seed_flow(
    *,
    execution_class: str,
    dispatch_state: str,
    accounting_basis: str,
    spend: str,
    task_kind: str = "general",
    status: str = "success",
    usage_source: str = "actual",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> str:
    flow_id = str(uuid4())
    attempt_id = str(uuid4())
    now = utc_now()
    success = status == "success"
    output_digest = canonical_digest({"text": f"output:{flow_id}"}) if success else None
    state = "complete" if success else "failed_terminal"
    reason = "completed" if success else "provider_failed"
    adapter_invoked = int(dispatch_state in {"started", "unknown"} or execution_class != "none")
    if dispatch_state == "not_started":
        adapter_invoked = 0
        input_tokens = 0
        output_tokens = 0
        usage_source = "none"
    execution_counts = {execution_class: 1}
    dispatch_counts = {dispatch_state: 1}
    accounting_counts = {accounting_basis: 1}
    usage_totals = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": 0,
        "reasoning_tokens": 0,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": 100,
        "usage_source_counts": {usage_source: 1},
    }
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_flows (
                id, workspace_id, task_kind, requested_route_class, state,
                terminal_reason, terminal_attempt_id, attempt_count,
                ordered_attempt_ids_json, execution_class_counts_json,
                external_dispatch_counts_json, usage_totals_json,
                accounting_basis_counts_json,
                external_provider_spend_usd_decimal,
                local_compute_cost_unpriced, synthetic_evidence_present,
                final_accounting_digest, final_output_digest,
                created_at, updated_at, completed_at
            ) VALUES (?, NULL, ?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                flow_id,
                task_kind,
                _route(execution_class),
                state,
                reason,
                json.dumps([attempt_id]),
                json.dumps(execution_counts),
                json.dumps(dispatch_counts),
                json.dumps(usage_totals),
                json.dumps(accounting_counts),
                spend,
                int(execution_class == "local_compute"),
                int(execution_class == "synthetic"),
                canonical_digest({"flow": flow_id, "accounting": spend}),
                output_digest,
                now,
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class,
                selected_route_class, provider_id, model_id, route_reason_json,
                output_digest, input_tokens, output_tokens, latency_ms,
                flow_id, flow_attempt_index, fallback_index, continuation_index,
                execution_class, adapter_invoked, external_dispatch_state,
                requested_output_ceiling, effective_output_ceiling,
                normalized_finish_reason, normalized_usage_source,
                cache_read_tokens, reasoning_tokens, accounting_basis,
                accounted_provider_spend_usd_decimal, capability_version,
                pricing_version, accounting_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?, ?, 100, ?, 0, 0, NULL,
                      ?, ?, ?, 64, 64, ?, ?, 0, 0, ?, ?, 'cap-v0', 'price-v0', 'acct-v0')
            """,
            (
                attempt_id,
                now,
                status,
                task_kind,
                _route(execution_class),
                _route(execution_class),
                _provider(execution_class),
                _model(execution_class),
                output_digest,
                input_tokens,
                output_tokens,
                flow_id,
                execution_class,
                adapter_invoked,
                dispatch_state,
                "stop" if success else "error",
                usage_source,
                accounting_basis,
                spend,
            ),
        )
        connection.execute(
            "UPDATE ai_flows SET terminal_attempt_id = ? WHERE id = ?",
            (attempt_id, flow_id),
        )
        connection.commit()
    ensure_flow_grade_subject(flow_id)
    return flow_id


def _grade(flow_id: str, grade: str, key: str, *, expected_head: str | None = None):
    subject = ensure_flow_grade_subject(flow_id)
    return set_flow_grade(
        flow_id=flow_id,
        grade=grade,
        expected_subject_version=int(subject["subject_version"]),
        expected_flow_outcome_digest=str(subject["flow_outcome_digest"]),
        expected_current_grade_event_id=expected_head,
        idempotency_key=key,
        note="private note must not enter cohort output",
    )


def test_empty_cohort_is_explicit_and_reconciled(initialized_database) -> None:
    cohort = get_flow_grade_cohort()

    assert cohort.terminal_flow_count == 0
    assert cohort.attempt_count == 0
    assert cohort.grade_coverage is None
    assert cohort.external_provider_spend_per_useful_outcome_usd is None
    assert cohort.total_economic_cost_per_useful_outcome_usd is None
    assert all(cohort.reconciliation.model_dump().values())


def test_complete_cohort_reconciles_quality_and_economic_evidence(
    initialized_database,
) -> None:
    local_flow = _seed_flow(
        execution_class="local_compute",
        dispatch_state="not_applicable",
        accounting_basis="local_compute_unpriced",
        spend="0",
        usage_source="actual",
    )
    exact_rework = _seed_flow(
        execution_class="external_provider",
        dispatch_state="started",
        accounting_basis="provider_exact",
        spend="2",
    )
    exact_useful = _seed_flow(
        execution_class="external_provider",
        dispatch_state="started",
        accounting_basis="provider_exact",
        spend="3",
    )
    synthetic = _seed_flow(
        execution_class="synthetic",
        dispatch_state="not_applicable",
        accounting_basis="synthetic_not_economic",
        spend="0",
        task_kind="smoke_test",
        usage_source="estimated",
    )
    unknown = _seed_flow(
        execution_class="external_provider",
        dispatch_state="unknown",
        accounting_basis="conservative_estimated_usage",
        spend="4",
        status="provider_error",
        usage_source="estimated",
    )
    not_sent = _seed_flow(
        execution_class="external_provider",
        dispatch_state="not_started",
        accounting_basis="external_not_sent",
        spend="0",
        status="route_unavailable",
        usage_source="none",
    )

    _grade(local_flow, "useful", "local-useful")
    first = _grade(exact_rework, "partly", "exact-partly")
    _grade(
        exact_rework,
        "rework",
        "exact-rework",
        expected_head=str(first["id"]),
    )
    _grade(exact_useful, "useful", "external-useful")
    _grade(synthetic, "useful", "synthetic-useful")
    withdrawn_head = _grade(not_sent, "failed", "not-sent-failed")
    subject = ensure_flow_grade_subject(not_sent)
    withdraw_flow_grade(
        flow_id=not_sent,
        expected_subject_version=int(subject["subject_version"]),
        expected_flow_outcome_digest=str(subject["flow_outcome_digest"]),
        expected_current_grade_event_id=str(withdrawn_head["id"]),
        idempotency_key="not-sent-withdraw",
    )

    cohort = get_flow_grade_cohort()

    assert cohort.terminal_flow_count == 6
    assert cohort.attempt_count == 6
    assert cohort.current_grade_counts == {
        "useful": 3,
        "partly": 0,
        "rework": 1,
        "failed": 0,
        "ungraded": 2,
    }
    assert cohort.grade_state_counts["gradeable"] == 6
    assert cohort.grade_state_counts["graded"] == 4
    assert cohort.grade_state_counts["ungraded"] == 2
    assert cohort.grade_coverage == pytest.approx(4 / 6)
    assert cohort.deterministic_failure_rate == pytest.approx(1 / 6)
    assert cohort.eligible_flow_count == 5
    assert cohort.eligible_grade_counts["useful"] == 2
    assert cohort.exclusion_reason_counts == {
        "synthetic_evidence": 1,
        "non_empirical_task_kind": 1,
    }
    assert cohort.execution_composition_counts == {
        "no_adapter_execution": 1,
        "synthetic_only": 1,
        "local_compute_only": 1,
        "external_provider_only": 3,
        "mixed_executed_classes": 0,
    }
    assert cohort.external_dispatch_quality_counts == {
        "no_external_dispatch": 3,
        "external_started_only": 2,
        "external_unknown_present": 1,
    }
    assert cohort.provider_accounting_quality_counts == {
        "no_external_provider_consumption": 3,
        "provider_exact_only": 2,
        "conservative_only": 1,
        "mixed_provider_basis": 0,
    }
    assert cohort.external_provider_spend_usd_total == "9"
    assert cohort.eligible_external_provider_spend_usd_total == "9"
    assert cohort.external_provider_spend_per_useful_outcome_usd == "4.5"
    assert cohort.external_provider_spend_usd_by_current_grade == {
        "useful": "3",
        "partly": "0",
        "rework": "2",
        "failed": "0",
        "ungraded": "4",
    }
    assert cohort.total_economic_cost_per_useful_outcome_usd is None
    assert cohort.local_attempt_count == 1
    assert cohort.flows_with_local_compute == 1
    assert cohort.local_cost_unpriced_flow_count == 1
    assert cohort.synthetic_flow_count == 1
    assert cohort.external_not_sent_attempt_count == 1
    assert cohort.external_unknown_attempt_count == 1
    assert cohort.no_execution_attempt_count == 1
    assert cohort.no_execution_reason_counts == {"external_not_sent": 1}
    assert cohort.attempt_metrics_by_usage_source["actual"].attempts == 3
    assert cohort.attempt_metrics_by_usage_source["estimated"].attempts == 2
    assert cohort.attempt_metrics_by_usage_source["none"].attempts == 1
    assert cohort.input_tokens_distribution.model_dump() == {
        "count": 6, "minimum": 0, "p50": 10, "p95": 10, "maximum": 10
    }
    assert cohort.output_tokens_distribution.model_dump() == {
        "count": 6, "minimum": 0, "p50": 5, "p95": 5, "maximum": 5
    }
    assert cohort.latency_ms_distribution.model_dump() == {
        "count": 6, "minimum": 100, "p50": 100, "p95": 100, "maximum": 100
    }
    assert cohort.revision_event_count == 1
    assert cohort.withdrawal_event_count == 1
    assert all(cohort.reconciliation.model_dump().values())
    assert unknown


def test_cohort_route_is_bounded_and_never_exports_notes(initialized_database) -> None:
    flow_id = _seed_flow(
        execution_class="local_compute",
        dispatch_state="not_applicable",
        accounting_basis="local_compute_unpriced",
        spend="0",
    )
    _grade(flow_id, "useful", "route-useful")
    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.get("/ai/grade-cohorts?limit=1")
        invalid = client.get("/ai/grade-cohorts?limit=0")

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_limit"] == 1
    assert "note" not in json.dumps(payload)
    assert invalid.status_code == 422


def _route(execution_class: str) -> str:
    return {
        "local_compute": "local:sequence",
        "synthetic": "local:synthetic",
        "external_provider": "external:test",
        "none": "auto",
    }.get(execution_class, "auto")


def _provider(execution_class: str) -> str:
    return "external-test" if execution_class == "external_provider" else execution_class


def _model(execution_class: str) -> str:
    return f"{execution_class}-model"
