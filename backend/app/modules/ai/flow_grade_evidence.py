from __future__ import annotations

import sqlite3

from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.flow_grade_contracts import (
    ACTOR,
    FINAL_ATTEMPT_STATUSES,
    SUBJECT_SCHEMA_VERSION,
    TERMINAL_FLOW_STATES,
    FlowGradeConflictError,
    FlowGradeNotFoundError,
    json_list,
    json_object,
    optional_digest,
    required_digest,
)


def load_flow_evidence(
    connection: sqlite3.Connection,
    *,
    flow_id: str,
) -> tuple[sqlite3.Row, list[sqlite3.Row], str, str | None]:
    flow = connection.execute(
        """
        SELECT id, workspace_id, task_kind, requested_route_class, state,
               terminal_reason, terminal_attempt_id, attempt_count,
               ordered_attempt_ids_json, execution_class_counts_json,
               external_dispatch_counts_json, usage_totals_json,
               accounting_basis_counts_json,
               external_provider_spend_usd_decimal,
               local_compute_cost_unpriced, synthetic_evidence_present,
               config_version, final_accounting_digest, final_output_digest
        FROM ai_flows
        WHERE id = ?
        """,
        (flow_id,),
    ).fetchone()
    if flow is None:
        raise FlowGradeNotFoundError(f"flow {flow_id} does not exist")
    if flow["state"] not in TERMINAL_FLOW_STATES:
        raise FlowGradeConflictError("only terminal flows are gradeable")
    final_accounting_digest = required_digest(
        flow["final_accounting_digest"],
        "final_accounting_digest",
    )
    final_output_digest = optional_digest(
        flow["final_output_digest"],
        "final_output_digest",
    )
    attempts = connection.execute(
        """
        SELECT id, flow_attempt_index, parent_attempt_id, fallback_index,
               continuation_index, status, execution_class, adapter_invoked,
               external_dispatch_state, requested_output_ceiling,
               effective_output_ceiling, normalized_finish_reason,
               normalized_usage_source, input_tokens, output_tokens,
               cache_read_tokens, reasoning_tokens, latency_ms,
               accounting_basis, accounted_provider_spend_usd_decimal,
               output_digest, selected_route_class, provider_id, model_id,
               capability_version, pricing_version, accounting_version
        FROM ai_jobs
        WHERE flow_id = ?
        ORDER BY flow_attempt_index
        """,
        (flow_id,),
    ).fetchall()
    return flow, list(attempts), final_accounting_digest, final_output_digest


def build_flow_outcome_payload(
    *,
    flow: sqlite3.Row,
    attempts: list[sqlite3.Row],
    final_accounting_digest: str,
    final_output_digest: str | None,
) -> dict[str, object]:
    ordered_ids = json_list(
        flow["ordered_attempt_ids_json"],
        "ordered_attempt_ids_json",
    )
    if int(flow["attempt_count"]) != len(attempts):
        raise FlowGradeConflictError(
            "flow attempt count does not match canonical attempts"
        )
    actual_ids = [str(row["id"]) for row in attempts]
    if ordered_ids != actual_ids:
        raise FlowGradeConflictError("ordered attempt identity is not finalized")
    if [row["flow_attempt_index"] for row in attempts] != list(range(len(attempts))):
        raise FlowGradeConflictError("flow attempt indexes are not contiguous")

    attempt_payloads = [_attempt_evidence(row) for row in attempts]
    return {
        "accounting_basis_counts": json_object(
            flow["accounting_basis_counts_json"],
            "accounting_basis_counts_json",
        ),
        "attempt_count": len(attempts),
        "attempts": attempt_payloads,
        "config_version": flow["config_version"],
        "execution_class_counts": json_object(
            flow["execution_class_counts_json"],
            "execution_class_counts_json",
        ),
        "external_dispatch_counts": json_object(
            flow["external_dispatch_counts_json"],
            "external_dispatch_counts_json",
        ),
        "external_provider_spend_usd_decimal": (
            flow["external_provider_spend_usd_decimal"] or "0"
        ),
        "final_accounting_digest": final_accounting_digest,
        "final_output_digest": final_output_digest,
        "flow_id": flow["id"],
        "local_compute_cost_unpriced": bool(flow["local_compute_cost_unpriced"]),
        "operator_identity": ACTOR,
        "requested_route_class": flow["requested_route_class"],
        "schema": SUBJECT_SCHEMA_VERSION,
        "state": flow["state"],
        "synthetic_evidence_present": bool(flow["synthetic_evidence_present"]),
        "task_kind": flow["task_kind"],
        "terminal_attempt_id": flow["terminal_attempt_id"],
        "terminal_reason": flow["terminal_reason"],
        "usage_totals": json_object(
            flow["usage_totals_json"],
            "usage_totals_json",
        ),
        "workspace_id": flow["workspace_id"],
    }


def _attempt_evidence(row: sqlite3.Row) -> dict[str, object]:
    if row["status"] not in FINAL_ATTEMPT_STATUSES:
        raise FlowGradeConflictError("flow contains a non-finalized attempt")
    payload: dict[str, object] = {
        "accounted_provider_spend_usd_decimal": (
            row["accounted_provider_spend_usd_decimal"] or "0"
        ),
        "accounting_basis": row["accounting_basis"],
        "accounting_version": row["accounting_version"],
        "adapter_invoked": bool(row["adapter_invoked"]),
        "cache_read_tokens": row["cache_read_tokens"],
        "capability_version": row["capability_version"],
        "continuation_index": row["continuation_index"],
        "effective_output_ceiling": row["effective_output_ceiling"],
        "execution_class": row["execution_class"],
        "external_dispatch_state": row["external_dispatch_state"],
        "fallback_index": row["fallback_index"],
        "flow_attempt_index": row["flow_attempt_index"],
        "id": row["id"],
        "input_tokens": row["input_tokens"],
        "latency_ms": row["latency_ms"],
        "model_id": row["model_id"],
        "normalized_finish_reason": row["normalized_finish_reason"],
        "normalized_usage_source": row["normalized_usage_source"],
        "output_digest": row["output_digest"],
        "output_tokens": row["output_tokens"],
        "parent_attempt_id": row["parent_attempt_id"],
        "pricing_version": row["pricing_version"],
        "provider_id": row["provider_id"],
        "reasoning_tokens": row["reasoning_tokens"],
        "requested_output_ceiling": row["requested_output_ceiling"],
        "selected_route_class": row["selected_route_class"],
        "status": row["status"],
    }
    payload["attempt_evidence_digest"] = canonical_digest(payload)
    return payload
