from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.ai.token_flow_segments import list_protected_segment_metadata
from app.modules.ai.token_flow_service import (
    ID_RE,
    TokenFlowConflictError,
    _safe,
    get_flow,
)


@dataclass(frozen=True, slots=True)
class ContinuationFlowStatus:
    flow_id: str
    state: str
    task_kind: str
    requested_route_class: str | None
    attempt_count: int
    continuation_count: int
    continuation_guard_snapshot: int
    ordered_attempt_ids: tuple[str, ...]
    execution_class_counts: dict[str, int]
    external_dispatch_counts: dict[str, int]
    usage_totals: dict[str, Any]
    accounting_basis_counts: dict[str, int]
    external_provider_spend_usd_decimal: str
    local_compute_cost_unpriced: bool
    synthetic_evidence_present: bool
    segment_count: int
    segment_digests: tuple[str, ...]
    segment_expired: tuple[bool, ...]
    final_output_digest: str | None
    final_accounting_digest: str | None
    terminal_reason: str | None
    created_at: str
    updated_at: str
    completed_at: str | None
    cancelled_at: str | None


def get_continuation_flow_status(
    *,
    flow_id: str,
    workspace_id: str | None,
    now: datetime | None = None,
) -> ContinuationFlowStatus:
    """Return bounded aggregate continuation state without any protected bodies."""

    flow_id = _safe(flow_id, ID_RE, "flow_id")
    flow = get_flow(flow_id)
    if flow["workspace_id"] != workspace_id:
        raise TokenFlowConflictError(
            "continuation status workspace does not match flow"
        )
    segments = list_protected_segment_metadata(
        flow_id=flow_id,
        workspace_id=workspace_id,
        now=now,
    )
    return ContinuationFlowStatus(
        flow_id=flow_id,
        state=str(flow["state"]),
        task_kind=str(flow["task_kind"]),
        requested_route_class=flow["requested_route_class"],
        attempt_count=int(flow["attempt_count"]),
        continuation_count=int(flow["continuation_count"]),
        continuation_guard_snapshot=int(
            flow["max_direct_continuations_snapshot"]
        ),
        ordered_attempt_ids=tuple(flow["ordered_attempt_ids"]),
        execution_class_counts=dict(flow["execution_class_counts"]),
        external_dispatch_counts=dict(flow["external_dispatch_counts"]),
        usage_totals=dict(flow["usage_totals"]),
        accounting_basis_counts=dict(flow["accounting_basis_counts"]),
        external_provider_spend_usd_decimal=str(
            flow["external_provider_spend_usd_decimal"]
        ),
        local_compute_cost_unpriced=bool(
            flow["local_compute_cost_unpriced"]
        ),
        synthetic_evidence_present=bool(
            flow["synthetic_evidence_present"]
        ),
        segment_count=len(segments),
        segment_digests=tuple(item.body_digest for item in segments),
        segment_expired=tuple(item.expired for item in segments),
        final_output_digest=flow["final_output_digest"],
        final_accounting_digest=flow["final_accounting_digest"],
        terminal_reason=flow["terminal_reason"],
        created_at=str(flow["created_at"]),
        updated_at=str(flow["updated_at"]),
        completed_at=flow["completed_at"],
        cancelled_at=flow["cancelled_at"],
    )
