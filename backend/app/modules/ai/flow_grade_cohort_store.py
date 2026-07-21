from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.core.database import open_sqlite_connection
from app.modules.ai.flow_grade_contracts import safe_id

TERMINAL_STATES = (
    "complete",
    "partial_terminal",
    "failed_terminal",
    "cancelled_terminal",
)


@dataclass(frozen=True)
class CohortRows:
    flows: list[dict[str, object]]
    attempts_by_flow: dict[str, list[dict[str, object]]]
    current_subject_by_flow: dict[str, dict[str, object]]
    latest_event_by_subject: dict[str, dict[str, object]]
    revision_event_count: int
    withdrawal_event_count: int
    invalid_subject_count: int
    truncated: bool


def load_cohort_rows(
    *,
    workspace_id: str | None,
    task_kind: str | None,
    limit: int,
) -> CohortRows:
    if workspace_id is not None:
        workspace_id = safe_id(workspace_id, "workspace_id")
    if task_kind is not None:
        task_kind = safe_id(task_kind, "task_kind")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
        raise ValueError("limit must be between 1 and 5000")

    clauses = [
        "state IN ('complete', 'partial_terminal', 'failed_terminal', 'cancelled_terminal')"
    ]
    values: list[object] = []
    if workspace_id is not None:
        clauses.append("workspace_id = ?")
        values.append(workspace_id)
    if task_kind is not None:
        clauses.append("task_kind = ?")
        values.append(task_kind)
    values.append(limit + 1)

    with open_sqlite_connection() as connection:
        flow_rows = connection.execute(
            f"""
            SELECT id, workspace_id, task_kind, requested_route_class, state,
                   terminal_reason, terminal_attempt_id, attempt_count,
                   external_provider_spend_usd_decimal,
                   local_compute_cost_unpriced, synthetic_evidence_present,
                   final_accounting_digest, final_output_digest
            FROM ai_flows
            WHERE {' AND '.join(clauses)}
            ORDER BY COALESCE(completed_at, cancelled_at, updated_at), id
            LIMIT ?
            """,
            values,
        ).fetchall()
        truncated = len(flow_rows) > limit
        flows = [dict(row) for row in flow_rows[:limit]]
        flow_ids = [str(row["id"]) for row in flows]
        if not flow_ids:
            return CohortRows(
                flows=[],
                attempts_by_flow={},
                current_subject_by_flow={},
                latest_event_by_subject={},
                revision_event_count=0,
                withdrawal_event_count=0,
                invalid_subject_count=0,
                truncated=truncated,
            )
        placeholders = ",".join("?" for _ in flow_ids)
        attempts = connection.execute(
            f"""
            SELECT id, flow_id, flow_attempt_index, fallback_index,
                   continuation_index, execution_class, adapter_invoked,
                   external_dispatch_state, normalized_usage_source,
                   accounting_basis, accounted_provider_spend_usd_decimal,
                   input_tokens, output_tokens, cache_read_tokens,
                   reasoning_tokens, latency_ms, selected_route_class,
                   provider_id, model_id, outcome_reason
            FROM ai_jobs
            WHERE flow_id IN ({placeholders})
            ORDER BY flow_id, flow_attempt_index
            """,
            flow_ids,
        ).fetchall()
        subjects = connection.execute(
            f"""
            SELECT id, flow_id, subject_version, flow_outcome_digest
            FROM ai_flow_grade_subjects
            WHERE valid = 1 AND flow_id IN ({placeholders})
            """,
            flow_ids,
        ).fetchall()
        subject_ids = [str(row["id"]) for row in subjects]
        latest_events: list[sqlite3.Row] = []
        if subject_ids:
            subject_placeholders = ",".join("?" for _ in subject_ids)
            latest_events = connection.execute(
                f"""
                SELECT event.subject_id, event.action, event.grade
                FROM ai_flow_grade_events AS event
                JOIN (
                    SELECT subject_id, MAX(event_index) AS event_index
                    FROM ai_flow_grade_events
                    WHERE subject_id IN ({subject_placeholders})
                    GROUP BY subject_id
                ) AS head
                  ON head.subject_id = event.subject_id
                 AND head.event_index = event.event_index
                """,
                subject_ids,
            ).fetchall()
        event_counts = connection.execute(
            f"""
            SELECT
                SUM(CASE WHEN action = 'set' AND event_index > 1 THEN 1 ELSE 0 END)
                    AS revisions,
                SUM(CASE WHEN action = 'withdraw' THEN 1 ELSE 0 END)
                    AS withdrawals
            FROM ai_flow_grade_events
            WHERE flow_id IN ({placeholders})
            """,
            flow_ids,
        ).fetchone()
        invalid_subject_count = int(
            connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM ai_flow_grade_subjects
                WHERE valid = 0 AND flow_id IN ({placeholders})
                """,
                flow_ids,
            ).fetchone()["count"]
        )

    attempts_by_flow = {flow_id: [] for flow_id in flow_ids}
    for row in attempts:
        attempts_by_flow[str(row["flow_id"])].append(dict(row))
    return CohortRows(
        flows=flows,
        attempts_by_flow=attempts_by_flow,
        current_subject_by_flow={str(row["flow_id"]): dict(row) for row in subjects},
        latest_event_by_subject={str(row["subject_id"]): dict(row) for row in latest_events},
        revision_event_count=int(event_counts["revisions"] or 0),
        withdrawal_event_count=int(event_counts["withdrawals"] or 0),
        invalid_subject_count=invalid_subject_count,
        truncated=truncated,
    )
