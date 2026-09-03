from __future__ import annotations

from pathlib import Path

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now
from app.modules.runner import service as _base
from app.modules.runner.local_python import execution_ownership_state

RECOVERY_ERROR_CODE = "runner_execution_interrupted"
RECOVERY_ERROR_MESSAGE = "Runner execution ownership ended before durable completion."


def reconcile_stranded_runner_jobs() -> int:
    """Fail only coherently-running jobs whose runner-specific owner is provably gone."""

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                rj.id AS runner_job_id,
                rj.workspace_id,
                rj.simulation_run_id,
                rj.status AS runner_status,
                rj.working_dir,
                sr.status AS simulation_status
            FROM runner_jobs rj
            JOIN simulation_runs sr ON sr.id = rj.simulation_run_id
            WHERE rj.status = 'running' OR sr.status = 'running'
            ORDER BY rj.created_at ASC, rj.id ASC
            """
        ).fetchall()

    recovered = 0
    for row in rows:
        if row["runner_status"] != "running" or row["simulation_status"] != "running":
            # Inconsistent pairs have no safe automatic recovery interpretation.
            continue
        if execution_ownership_state(Path(str(row["working_dir"]))) != "gone":
            # live => active child/owner; unknown => no proof of abandonment.
            continue
        if _recover_pair(
            runner_job_id=str(row["runner_job_id"]),
            workspace_id=str(row["workspace_id"]),
            simulation_run_id=str(row["simulation_run_id"]),
        ):
            recovered += 1
    return recovered


def _recover_pair(*, runner_job_id: str, workspace_id: str, simulation_run_id: str) -> bool:
    completed_at = utc_now()
    output_payload = _base.canonical_json(
        {
            "status": "failed",
            "error": {"code": RECOVERY_ERROR_CODE, "message": RECOVERY_ERROR_MESSAGE},
        }
    )
    with open_sqlite_connection() as connection:
        job_cursor = connection.execute(
            """
            UPDATE runner_jobs
            SET status = 'failed', updated_at = ?
            WHERE id = ? AND workspace_id = ? AND simulation_run_id = ? AND status = 'running'
            """,
            (completed_at, runner_job_id, workspace_id, simulation_run_id),
        )
        run_cursor = connection.execute(
            """
            UPDATE simulation_runs
            SET status = 'failed', output_payload = ?, completed_at = ?
            WHERE id = ? AND workspace_id = ? AND status = 'running'
            """,
            (output_payload, completed_at, simulation_run_id, workspace_id),
        )
        if job_cursor.rowcount != 1 or run_cursor.rowcount != 1:
            connection.rollback()
            return False
        _base._log_event(
            connection,
            event_type="RunnerJobFailed",
            target_type="RunnerJob",
            target_id=runner_job_id,
            workspace_id=workspace_id,
            payload={
                "simulation_run_id": simulation_run_id,
                "status": "failed",
                "error_code": RECOVERY_ERROR_CODE,
                "recovered_after_owner_loss": True,
            },
        )
        connection.commit()
    return True
