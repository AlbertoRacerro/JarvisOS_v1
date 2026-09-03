from __future__ import annotations

from pathlib import Path

from app.core.database import open_sqlite_connection
from app.modules.runner import guarded_service as _guarded
from app.modules.runner.local_python import ExecutionOwnerBusy, prepare_execution_owner
from app.modules.runner.models import RunnerJobRunResponse
from app.modules.runner.safety import RunnerSafetyError


def run_runner_job(runner_job_id: str) -> RunnerJobRunResponse:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT working_dir FROM runner_jobs WHERE id = ?",
            (runner_job_id,),
        ).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_job_not_found", "Runner job not found.")

    try:
        with prepare_execution_owner(Path(str(row["working_dir"]))):
            return _guarded.run_runner_job(runner_job_id)
    except ExecutionOwnerBusy as exc:
        raise RunnerSafetyError(
            "runner_job_not_queued",
            "Only one execution owner may claim a queued runner job.",
        ) from exc
