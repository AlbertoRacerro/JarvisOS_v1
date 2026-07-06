import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.core.repository import row_to_model, rows_to_models
from app.modules.events.service import log_event, utc_now
from app.modules.memory.models import CalcParameterProposalCreate, MemoryProposalCreate, MemoryRecordRead

_ALLOWED_STATUSES = {"proposed", "accepted", "rejected", "superseded"}
_TABLE_BY_KIND = {
    "assumption": "assumptions",
    "parameter": "parameters",
    "decision": "decisions",
}
_TARGET_BY_KIND = {
    "assumption": "Assumption",
    "parameter": "Parameter",
    "decision": "Decision",
}


def _require_workspace(connection: sqlite3.Connection, workspace_id: str) -> None:
    row = connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    if row is None:
        raise ValueError("Workspace not found.")


def _require_ai_job(connection: sqlite3.Connection, source_ai_job_id: str | None) -> str:
    if source_ai_job_id is None or not source_ai_job_id.strip():
        raise ValueError("source_ai_job_id is required for AI proposals.")
    source_ai_job_id = source_ai_job_id.strip()
    row = connection.execute("SELECT id FROM ai_jobs WHERE id = ?", (source_ai_job_id,)).fetchone()
    if row is None:
        raise ValueError("source_ai_job_id does not reference an existing AI job.")
    return source_ai_job_id


def _normalize_status(status: str) -> str:
    if status in _ALLOWED_STATUSES:
        return status
    return "proposed"


def _select_record_sql(kind: str) -> str:
    if kind == "assumption":
        return """
            SELECT id, 'assumption' AS record_kind, workspace_id,
                CASE WHEN status IN ('proposed', 'accepted', 'rejected', 'superseded') THEN status ELSE 'proposed' END AS status,
                origin, source_ai_job_id, promoted_at, created_at, updated_at,
                NULL AS title, statement, NULL AS decision_text, NULL AS name, source_ref, notes
            FROM assumptions
        """
    if kind == "parameter":
        return """
            SELECT id, 'parameter' AS record_kind, workspace_id,
                CASE WHEN status IN ('proposed', 'accepted', 'rejected', 'superseded') THEN status ELSE 'proposed' END AS status,
                origin, source_ai_job_id, promoted_at, created_at, updated_at,
                NULL AS title, NULL AS statement, NULL AS decision_text, name, source_ref, notes
            FROM parameters
        """
    if kind == "decision":
        return """
            SELECT id, 'decision' AS record_kind, workspace_id,
                CASE WHEN status IN ('proposed', 'accepted', 'rejected', 'superseded') THEN status ELSE 'proposed' END AS status,
                origin, source_ai_job_id, promoted_at, created_at, updated_at,
                title, NULL AS statement, decision_text, NULL AS name, NULL AS source_ref, notes
            FROM decisions
        """
    raise ValueError("Unsupported memory record kind.")


def _get_record(connection: sqlite3.Connection, kind: str, record_id: str) -> MemoryRecordRead | None:
    row = connection.execute(f"{_select_record_sql(kind)} WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        return None
    return row_to_model(row, MemoryRecordRead)


def _log_memory_event(connection: sqlite3.Connection, event_type: str, record: MemoryRecordRead) -> None:
    log_event(
        connection,
        event_type=event_type,
        actor="local-user",
        target_type=_TARGET_BY_KIND[record.record_kind],
        target_id=record.id,
        workspace_id=record.workspace_id,
        payload={"record_kind": record.record_kind, "status": record.status, "origin": record.origin},
    )


def create_proposal(payload: MemoryProposalCreate) -> MemoryRecordRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, payload.workspace_id)
        source_ai_job_id = _require_ai_job(connection, payload.source_ai_job_id)
        if payload.record_kind == "assumption":
            if not payload.statement:
                raise ValueError("statement is required for assumption proposals.")
            connection.execute(
                """
                INSERT INTO assumptions (
                    id, workspace_id, statement, scope, confidence, status, source_ref,
                    created_at, updated_at, notes, origin, source_ai_job_id, promoted_at
                ) VALUES (?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?, 'ai_proposed', ?, NULL)
                """,
                (
                    record_id,
                    payload.workspace_id,
                    payload.statement,
                    payload.scope,
                    payload.confidence if isinstance(payload.confidence, str) else None,
                    payload.source_ref,
                    now,
                    now,
                    payload.notes,
                    source_ai_job_id,
                ),
            )
        elif payload.record_kind == "parameter":
            if not payload.name:
                raise ValueError("name is required for parameter proposals.")
            connection.execute(
                """
                INSERT INTO parameters (
                    id, workspace_id, name, symbol, value, unit, value_status, value_min,
                    value_max, source_ref, confidence, status, created_at, updated_at, notes,
                    origin, source_ai_job_id, promoted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, 'ai_proposed', ?, NULL)
                """,
                (
                    record_id,
                    payload.workspace_id,
                    payload.name,
                    payload.symbol,
                    payload.value,
                    payload.unit,
                    payload.value_status,
                    payload.value_min,
                    payload.value_max,
                    payload.source_ref,
                    payload.confidence if isinstance(payload.confidence, int | float) else None,
                    now,
                    now,
                    payload.notes,
                    source_ai_job_id,
                ),
            )
        elif payload.record_kind == "decision":
            if not payload.title or not payload.decision_text:
                raise ValueError("title and decision_text are required for decision proposals.")
            connection.execute(
                """
                INSERT INTO decisions (
                    id, workspace_id, title, decision_text, rationale, status, linked_run_id,
                    created_at, updated_at, notes, origin, source_ai_job_id, promoted_at
                ) VALUES (?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?, 'ai_proposed', ?, NULL)
                """,
                (
                    record_id,
                    payload.workspace_id,
                    payload.title,
                    payload.decision_text,
                    payload.rationale,
                    payload.linked_run_id,
                    now,
                    now,
                    payload.notes,
                    source_ai_job_id,
                ),
            )
        record = _get_record(connection, payload.record_kind, record_id)
        if record is None:
            raise ValueError("Proposal was not created.")
        _log_memory_event(connection, "MemoryProposalCreated", record)
        connection.commit()
    return record


def create_calc_parameter_proposals(payloads: list[CalcParameterProposalCreate]) -> list[MemoryRecordRead]:
    if not payloads:
        return []
    now = utc_now()
    created: list[tuple[str, str]] = []
    with open_sqlite_connection() as connection:
        for payload in payloads:
            _require_workspace(connection, payload.workspace_id)
            record_id = str(uuid4())
            source_ref = f"runner_job:{payload.runner_job_id}"
            connection.execute(
                """
                INSERT INTO parameters (
                    id, workspace_id, name, symbol, value, unit, value_status, value_min,
                    value_max, source_ref, confidence, status, created_at, updated_at, notes,
                    origin, source_ai_job_id, promoted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, 'calc', NULL, NULL)
                """,
                (
                    record_id,
                    payload.workspace_id,
                    payload.name,
                    payload.symbol,
                    payload.value,
                    payload.unit,
                    payload.value_status,
                    payload.value_min,
                    payload.value_max,
                    source_ref,
                    payload.confidence,
                    now,
                    now,
                    payload.notes,
                ),
            )
            created.append((record_id, payload.workspace_id))
        records = [_get_record(connection, "parameter", record_id) for record_id, _ in created]
        result = [record for record in records if record is not None]
        for record in result:
            _log_memory_event(connection, "MemoryProposalCreated", record)
        connection.commit()
    return result


def _transition(kind: str, record_id: str, target_status: str) -> MemoryRecordRead:
    if kind not in _TABLE_BY_KIND:
        raise ValueError("Unsupported memory record kind.")
    with open_sqlite_connection() as connection:
        record = _get_record(connection, kind, record_id)
        if record is None:
            raise ValueError("Memory record not found.")
        current_status = _normalize_status(record.status)
        if current_status != "proposed":
            raise ValueError(f"Cannot transition {current_status} record to {target_status}.")
        now = utc_now()
        promoted_at = now if target_status == "accepted" else record.promoted_at
        connection.execute(
            f"UPDATE {_TABLE_BY_KIND[kind]} SET status = ?, promoted_at = ?, updated_at = ? WHERE id = ?",
            (target_status, promoted_at, now, record_id),
        )
        updated = _get_record(connection, kind, record_id)
        if updated is None:
            raise ValueError("Memory record not found.")
        _log_memory_event(connection, f"MemoryProposal{target_status.title()}", updated)
        connection.commit()
    return updated


def promote_record(kind: str, record_id: str) -> MemoryRecordRead:
    return _transition(kind, record_id, "accepted")


def reject_record(kind: str, record_id: str) -> MemoryRecordRead:
    return _transition(kind, record_id, "rejected")


def list_proposals(workspace_id: str, status: str | None = None) -> list[MemoryRecordRead]:
    if status is not None and status not in _ALLOWED_STATUSES:
        raise ValueError("Unsupported memory status.")
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        union_sql = " UNION ALL ".join(_select_record_sql(kind) for kind in ("assumption", "parameter", "decision"))
        params: list[str] = [workspace_id]
        where = "WHERE workspace_id = ?"
        if status is not None:
            where += " AND status = ?"
            params.append(status)
        rows = connection.execute(
            f"SELECT * FROM ({union_sql}) {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
    return rows_to_models(rows, MemoryRecordRead)
