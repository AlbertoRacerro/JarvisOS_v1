from __future__ import annotations

import sqlite3
from typing import Any

from app.core.database import open_sqlite_connection
from app.core.repository import row_to_model
from app.modules.events.service import log_event, utc_now
from app.modules.flowsheet.service import build_flowsheet_graph_from_connection
from app.modules.modeling.models import ParameterLifecycleCommand, ParameterRead, ParameterUpdate


class ParameterLifecycleError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


_EDIT_FIELDS = (
    "name",
    "symbol",
    "value",
    "unit",
    "value_status",
    "value_min",
    "value_max",
    "source_ref",
    "confidence",
    "notes",
)
_AUTHORITY_FIELDS = {"value", "unit"}
_TARGETS = {
    "activate": {"inactive": "active"},
    "deactivate": {"active": "inactive"},
    "archive": {"active": "archived", "inactive": "archived"},
    "delete": {"active": "deleted", "inactive": "deleted", "archived": "deleted"},
}


def _parameter_row(connection: sqlite3.Connection, workspace_id: str, parameter_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM parameters WHERE id = ? AND workspace_id = ?",
        (parameter_id, workspace_id),
    ).fetchone()
    if row is None:
        raise ParameterLifecycleError("parameter_not_found", "Parameter not found in workspace.")
    return row


def _downstream_refs(connection: sqlite3.Connection, workspace_id: str, parameter_id: str) -> tuple[str, ...]:
    graph = build_flowsheet_graph_from_connection(connection, workspace_id)
    source = f"parameter:{parameter_id}"
    adjacency: dict[str, set[str]] = {}
    for edge in graph.edges:
        if edge.edge_class == "dependency" or edge.relation == "executed_by":
            adjacency.setdefault(edge.upstream_ref, set()).add(edge.downstream_ref)
    seen = {source}
    pending = [source]
    while pending:
        current = pending.pop()
        for downstream in sorted(adjacency.get(current, ())):
            if downstream not in seen:
                seen.add(downstream)
                pending.append(downstream)
    return tuple(sorted(seen - {source}))


def _require_no_downstream_dependents(
    connection: sqlite3.Connection, workspace_id: str, parameter_id: str
) -> None:
    dependents = _downstream_refs(connection, workspace_id, parameter_id)
    if dependents:
        raise ParameterLifecycleError(
            "parameter_lifecycle_dependents_require_reconciliation",
            f"Parameter has {len(dependents)} downstream dependent record(s); use replacement/reconciliation authority.",
        )


def _event_payload(*, operation: str, prior: dict[str, Any], result: dict[str, Any], reason: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"operation": operation, "prior": prior, "result": result}
    if reason:
        payload["reason"] = reason
    return payload


def update_parameter(parameter_id: str, payload: ParameterUpdate) -> ParameterRead:
    updates = payload.model_dump(exclude_unset=True, exclude={"workspace_id", "expected_updated_at"})
    if not updates:
        with open_sqlite_connection() as connection:
            return row_to_model(_parameter_row(connection, payload.workspace_id, parameter_id), ParameterRead)

    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = _parameter_row(connection, payload.workspace_id, parameter_id)
            if row["updated_at"] != payload.expected_updated_at:
                raise ParameterLifecycleError("parameter_stale", "Parameter changed since it was reviewed.")
            if row["lifecycle_state"] != "active":
                raise ParameterLifecycleError("parameter_not_active", "Only an active Parameter may be edited in V0.")
            if _AUTHORITY_FIELDS.intersection(updates) and any(row[field] != updates[field] for field in _AUTHORITY_FIELDS.intersection(updates)):
                _require_no_downstream_dependents(connection, payload.workspace_id, parameter_id)

            merged_min = updates.get("value_min", row["value_min"])
            merged_max = updates.get("value_max", row["value_max"])
            if merged_min is not None and merged_max is not None and merged_min > merged_max:
                raise ParameterLifecycleError("parameter_invalid_bounds", "value_min must be <= value_max.")

            changed = {field: value for field, value in updates.items() if row[field] != value}
            if not changed:
                connection.rollback()
                return row_to_model(row, ParameterRead)

            now = utc_now()
            assignments = ", ".join(f"{field} = ?" for field in changed)
            connection.execute(
                f"UPDATE parameters SET {assignments}, updated_at = ? WHERE id = ? AND workspace_id = ? AND updated_at = ?",
                (*changed.values(), now, parameter_id, payload.workspace_id, payload.expected_updated_at),
            )
            prior = {field: row[field] for field in changed}
            log_event(
                connection,
                event_type="ParameterCanonicalEdited",
                actor="local-user",
                target_type="Parameter",
                target_id=parameter_id,
                workspace_id=payload.workspace_id,
                payload=_event_payload(operation="edit", prior=prior, result=changed),
            )
            connection.commit()
            updated = _parameter_row(connection, payload.workspace_id, parameter_id)
            return row_to_model(updated, ParameterRead)
        except Exception:
            connection.rollback()
            raise


def transition_parameter(parameter_id: str, payload: ParameterLifecycleCommand) -> ParameterRead:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = _parameter_row(connection, payload.workspace_id, parameter_id)
            current = row["lifecycle_state"]
            if row["updated_at"] != payload.expected_updated_at or current != payload.expected_lifecycle_state:
                raise ParameterLifecycleError("parameter_stale", "Parameter lifecycle changed since it was reviewed.")
            target = _TARGETS[payload.action].get(current)
            if target is None:
                raise ParameterLifecycleError(
                    "parameter_lifecycle_transition_invalid",
                    f"Transition {payload.action} is not valid from {current}.",
                )
            if current == "active" and target != "active":
                _require_no_downstream_dependents(connection, payload.workspace_id, parameter_id)

            now = utc_now()
            connection.execute(
                "UPDATE parameters SET lifecycle_state = ?, updated_at = ? WHERE id = ? AND workspace_id = ? AND updated_at = ? AND lifecycle_state = ?",
                (target, now, parameter_id, payload.workspace_id, payload.expected_updated_at, current),
            )
            log_event(
                connection,
                event_type="ParameterLifecycleChanged",
                actor="local-user",
                target_type="Parameter",
                target_id=parameter_id,
                workspace_id=payload.workspace_id,
                payload=_event_payload(
                    operation=payload.action,
                    prior={"lifecycle_state": current},
                    result={"lifecycle_state": target},
                    reason=payload.reason,
                ),
            )
            connection.commit()
            updated = _parameter_row(connection, payload.workspace_id, parameter_id)
            return row_to_model(updated, ParameterRead)
        except Exception:
            connection.rollback()
            raise
