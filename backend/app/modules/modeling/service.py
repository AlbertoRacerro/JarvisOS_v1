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
            "SELECT * FROM assumptions WHERE workspace_id = ? ORDER BY created_at DESC",
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
                id, workspace_id, name, symbol, value, unit, source_ref,
                confidence, status, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                workspace_id,
                payload.name,
                payload.symbol,
                payload.value,
                payload.unit,
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
            "SELECT * FROM parameters WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return rows_to_models(rows, ParameterRead)


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
