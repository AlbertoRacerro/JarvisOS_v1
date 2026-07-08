import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.core.repository import optional_row_to_model, row_to_model, rows_to_models
from app.modules.events.service import log_event, utc_now
from app.modules.modeling.models import (
    AssumptionCreate,
    AssumptionRead,
    DecisionCreate,
    DecisionRead,
    ModelSpecCreate,
    ModelSpecRead,
    ParameterCreate,
    ParameterRead,
    RequirementCreate,
    RequirementRead,
    RequirementUpdate,
    SimulationRunCreate,
    SimulationRunRead,
)


def _workspace_exists(connection: sqlite3.Connection, workspace_id: str) -> bool:
    row = connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return row is not None


def _require_workspace(connection: sqlite3.Connection, workspace_id: str) -> None:
    if not _workspace_exists(connection, workspace_id):
        raise ValueError("Workspace not found.")


def _log_creation(
    connection: sqlite3.Connection,
    *,
    event_type: str,
    target_type: str,
    target_id: str,
    workspace_id: str,
    payload: dict[str, object],
) -> None:
    log_event(
        connection,
        event_type=event_type,
        actor="local-user",
        target_type=target_type,
        target_id=target_id,
        workspace_id=workspace_id,
        payload=payload,
    )


def create_model_spec(workspace_id: str, payload: ModelSpecCreate) -> ModelSpecRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO model_specs (
                id, workspace_id, title, engineering_question, scope, status,
                maturity_status, assumptions_summary, inputs_summary, outputs_summary,
                raw_payload, schema_version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.title,
                payload.engineering_question,
                payload.scope,
                payload.status,
                payload.maturity_status,
                payload.assumptions_summary,
                payload.inputs_summary,
                payload.outputs_summary,
                payload.raw_payload,
                1,
                now,
                now,
            ),
        )
        _log_creation(
            connection,
            event_type="ModelSpecCreated",
            target_type="ModelSpec",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"title": payload.title},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM model_specs WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, ModelSpecRead)


def list_model_specs(workspace_id: str) -> list[ModelSpecRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM model_specs WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, ModelSpecRead)


def get_model_spec(model_spec_id: str) -> ModelSpecRead | None:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM model_specs WHERE id = ?", (model_spec_id,)).fetchone()
    return optional_row_to_model(row, ModelSpecRead)


def create_assumption(workspace_id: str, payload: AssumptionCreate) -> AssumptionRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO assumptions (
                id, workspace_id, statement, scope, confidence, status,
                source_ref, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.statement,
                payload.scope,
                payload.confidence,
                payload.status,
                payload.source_ref,
                now,
                now,
                payload.notes,
            ),
        )
        _log_creation(
            connection,
            event_type="AssumptionCreated",
            target_type="Assumption",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"statement": payload.statement[:160], "status": payload.status},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM assumptions WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, AssumptionRead)


def list_assumptions(workspace_id: str) -> list[AssumptionRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            """
            SELECT
                id, workspace_id, statement, scope,
                CASE
                    WHEN confidence IN ('low', 'medium', 'high') THEN confidence
                    ELSE NULL
                END AS confidence,
                CASE
                    WHEN status IN ('proposed', 'accepted', 'rejected', 'superseded') THEN status
                    ELSE 'proposed'
                END AS status,
                source_ref, created_at, updated_at, notes
            FROM assumptions
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, AssumptionRead)


def create_parameter(workspace_id: str, payload: ParameterCreate) -> ParameterRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO parameters (
                id, workspace_id, name, symbol, value, unit, value_status, value_min,
                value_max, source_ref, confidence, status, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.name,
                payload.symbol,
                payload.value,
                payload.unit,
                payload.value_status,
                payload.value_min,
                payload.value_max,
                payload.source_ref,
                payload.confidence,
                payload.status,
                now,
                now,
                payload.notes,
            ),
        )
        _log_creation(
            connection,
            event_type="ParameterCreated",
            target_type="Parameter",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"name": payload.name, "symbol": payload.symbol, "unit": payload.unit},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM parameters WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, ParameterRead)


def list_parameters(workspace_id: str) -> list[ParameterRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            """
            SELECT
                id, workspace_id, name, symbol, value,
                COALESCE(unit, 'unspecified') AS unit,
                COALESCE(value_status, 'candidate') AS value_status,
                value_min, value_max, source_ref, confidence, status,
                created_at, updated_at, notes
            FROM parameters
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, ParameterRead)


def create_requirement(workspace_id: str, payload: RequirementCreate) -> RequirementRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO requirements (
                id, workspace_id, statement, rationale, status, notes,
                schema_version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.statement,
                payload.rationale,
                payload.status,
                payload.notes,
                1,
                now,
                now,
            ),
        )
        _log_creation(
            connection,
            event_type="RequirementCreated",
            target_type="Requirement",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"statement": payload.statement[:160], "status": payload.status},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, RequirementRead)


def get_requirement(requirement_id: str) -> RequirementRead | None:
    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
    return optional_row_to_model(row, RequirementRead)


def list_requirements(workspace_id: str) -> list[RequirementRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM requirements WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, RequirementRead)


def update_requirement(requirement_id: str, payload: RequirementUpdate) -> RequirementRead | None:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return get_requirement(requirement_id)

    now = utc_now()
    assignments = [f"{field} = ?" for field in updates]
    values = list(updates.values())
    values.extend([now, requirement_id])
    with open_sqlite_connection() as connection:
        connection.execute(
            f"UPDATE requirements SET {', '.join(assignments)}, updated_at = ? WHERE id = ?",
            values,
        )
        connection.commit()
        row = connection.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
    return optional_row_to_model(row, RequirementRead)


def create_simulation_run(workspace_id: str, payload: SimulationRunCreate) -> SimulationRunRead:
    record_id = str(uuid4())
    created_at = utc_now()
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload, started_at,
                completed_at, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.model_version_id,
                payload.run_label,
                payload.status,
                payload.input_payload,
                payload.parameter_payload,
                payload.output_payload,
                payload.started_at,
                payload.completed_at,
                created_at,
                payload.notes,
            ),
        )
        _log_creation(
            connection,
            event_type="SimulationRunCreated",
            target_type="SimulationRun",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"run_label": payload.run_label, "status": payload.status},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM simulation_runs WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, SimulationRunRead)


def list_simulation_runs(workspace_id: str) -> list[SimulationRunRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM simulation_runs WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, SimulationRunRead)


def create_decision(workspace_id: str, payload: DecisionCreate) -> DecisionRead:
    now = utc_now()
    record_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO decisions (
                id, workspace_id, title, decision_text, rationale, status,
                linked_run_id, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.title,
                payload.decision_text,
                payload.rationale,
                payload.status,
                payload.linked_run_id,
                now,
                now,
                payload.notes,
            ),
        )
        _log_creation(
            connection,
            event_type="DecisionCreated",
            target_type="Decision",
            target_id=record_id,
            workspace_id=workspace_id,
            payload={"title": payload.title, "status": payload.status},
        )
        connection.commit()
        row = connection.execute("SELECT * FROM decisions WHERE id = ?", (record_id,)).fetchone()
    return row_to_model(row, DecisionRead)


def list_decisions(workspace_id: str) -> list[DecisionRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM decisions WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, DecisionRead)

CONTEXT_RECORD_KINDS = ("decision", "assumption", "parameter", "requirement")
CONTEXT_KIND_MODELS = {
    "decision": DecisionRead,
    "assumption": AssumptionRead,
    "parameter": ParameterRead,
    "requirement": RequirementRead,
}
CONTEXT_KIND_TABLES = {
    "decision": "decisions",
    "assumption": "assumptions",
    "parameter": "parameters",
    "requirement": "requirements",
}
CONTEXT_KIND_STATUS_COLUMNS = {
    "decision": "status",
    "assumption": "status",
    "parameter": "value_status",
    "requirement": "status",
}
CONTEXT_KIND_LIKE_COLUMNS = {
    "decision": ("title", "decision_text", "rationale", "notes"),
    "assumption": ("statement", "notes"),
    "parameter": ("name", "symbol", "notes"),
    "requirement": ("statement", "rationale", "notes"),
}


def context_pack_fts_available(connection: sqlite3.Connection) -> bool:
    from app.core.database import sqlite_supports_fts5

    if not sqlite_supports_fts5(connection):
        return False
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'context_pack_fts'"
    ).fetchone()
    return row is not None


def _query_ids_for_kind(
    connection: sqlite3.Connection, *, workspace_id: str, kind: str, query: str, fts_available: bool
) -> set[str]:
    if fts_available:
        rows = connection.execute(
            """
            SELECT record_id FROM context_pack_fts
            WHERE workspace_id = ? AND record_kind = ? AND context_pack_fts MATCH ?
            """,
            (workspace_id, kind, query),
        ).fetchall()
        return {row["record_id"] for row in rows}
    table = CONTEXT_KIND_TABLES[kind]
    clauses = [f"COALESCE({column}, '') LIKE ? COLLATE NOCASE" for column in CONTEXT_KIND_LIKE_COLUMNS[kind]]
    pattern = f"%{query}%"
    rows = connection.execute(
        f"SELECT id FROM {table} WHERE workspace_id = ? AND ({' OR '.join(clauses)})",
        [workspace_id, *([pattern] * len(clauses))],
    ).fetchall()
    return {row["id"] for row in rows}


def select_context_records(
    workspace_id: str,
    *,
    kinds: list[str],
    statuses_by_kind: dict[str, list[str]],
    ids: list[str] | None,
    query: str | None,
    max_items_per_kind: int,
) -> dict[str, list[object]]:
    """Select context-pack records ordered updated_at DESC, id ASC.

    Explicit ids bypass status filtering but must belong to an included kind. A
    non-empty query uses trigger-maintained FTS5 when available, otherwise the
    same per-kind columns are searched with LIKE.
    """
    selected_ids = set(ids or [])
    clean_query = query.strip() if query else ""
    result: dict[str, list[object]] = {}
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        fts_available = context_pack_fts_available(connection) if clean_query else False
        for kind in kinds:
            table = CONTEXT_KIND_TABLES[kind]
            status_column = CONTEXT_KIND_STATUS_COLUMNS[kind]
            params: list[object] = [workspace_id]
            where = ["workspace_id = ?"]
            status_values = statuses_by_kind.get(kind, [])
            if selected_ids:
                status_clause = "0"
                if status_values:
                    status_clause = f"{status_column} IN ({','.join('?' for _ in status_values)})"
                    params.extend(status_values)
                id_clause = f"id IN ({','.join('?' for _ in selected_ids)})"
                params.extend(sorted(selected_ids))
                where.append(f"(({status_clause}) OR ({id_clause}))")
            elif status_values:
                where.append(f"{status_column} IN ({','.join('?' for _ in status_values)})")
                params.extend(status_values)
            if clean_query:
                matching_ids = _query_ids_for_kind(
                    connection, workspace_id=workspace_id, kind=kind, query=clean_query, fts_available=fts_available
                )
                if not matching_ids:
                    result[kind] = []
                    continue
                where.append(f"id IN ({','.join('?' for _ in matching_ids)})")
                params.extend(sorted(matching_ids))
            params.append(max_items_per_kind)
            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {' AND '.join(where)} ORDER BY updated_at DESC, id ASC LIMIT ?",
                params,
            ).fetchall()
            result[kind] = rows_to_models(rows, CONTEXT_KIND_MODELS[kind])
    return result
