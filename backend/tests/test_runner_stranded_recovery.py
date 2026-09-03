from __future__ import annotations

import asyncio
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI

from app import main
from app.modules.runner import recovery
from app.modules.runner.local_python import (
    execute_python_script,
    execution_ownership_state,
    prepare_execution_owner,
)


def test_execution_owner_is_live_through_child_completion(tmp_path: Path) -> None:
    working_dir = tmp_path / "run"
    working_dir.mkdir()
    script = working_dir / "script.py"
    script.write_text("print('owner-proof')\n", encoding="utf-8")
    input_file = working_dir / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    output_dir = working_dir / "output"
    output_dir.mkdir()

    assert execution_ownership_state(working_dir) == "unknown"
    with prepare_execution_owner(working_dir):
        assert execution_ownership_state(working_dir) == "live"
        result = execute_python_script(
            script_path=script,
            input_file=input_file,
            output_dir=output_dir,
            working_dir=working_dir,
            timeout_seconds=10,
            max_stdout_bytes=4096,
            max_stderr_bytes=4096,
        )
        assert result.return_code == 0
        assert result.timed_out is False
        assert result.stdout == "owner-proof\n"
        # The owner remains live after the model child exits so durable DB
        # finalization cannot be mistaken for an abandoned execution.
        assert execution_ownership_state(working_dir) == "live"

    assert execution_ownership_state(working_dir) == "gone"


def test_recovery_requires_coherent_running_pair_and_proven_owner_loss(monkeypatch) -> None:
    rows = [
        {
            "runner_job_id": "gone",
            "workspace_id": "w",
            "simulation_run_id": "s-gone",
            "runner_status": "running",
            "simulation_status": "running",
            "working_dir": "/gone",
        },
        {
            "runner_job_id": "live",
            "workspace_id": "w",
            "simulation_run_id": "s-live",
            "runner_status": "running",
            "simulation_status": "running",
            "working_dir": "/live",
        },
        {
            "runner_job_id": "unknown",
            "workspace_id": "w",
            "simulation_run_id": "s-unknown",
            "runner_status": "running",
            "simulation_status": "running",
            "working_dir": "/unknown",
        },
        {
            "runner_job_id": "inconsistent",
            "workspace_id": "w",
            "simulation_run_id": "s-inconsistent",
            "runner_status": "running",
            "simulation_status": "failed",
            "working_dir": "/gone-inconsistent",
        },
    ]

    class _Selection:
        def fetchall(self):
            return rows

    class _Connection:
        def execute(self, _query):
            return _Selection()

    @contextmanager
    def _open_connection():
        yield _Connection()

    states = {
        "/gone": "gone",
        "/live": "live",
        "/unknown": "unknown",
        "/gone-inconsistent": "gone",
    }
    recovered: list[str] = []

    monkeypatch.setattr(recovery, "open_sqlite_connection", _open_connection)
    monkeypatch.setattr(recovery, "execution_ownership_state", lambda path: states[str(path)])
    monkeypatch.setattr(
        recovery,
        "_recover_pair",
        lambda **kwargs: recovered.append(str(kwargs["runner_job_id"])) is None or True,
    )

    assert recovery.reconcile_stranded_runner_jobs() == 1
    assert recovered == ["gone"]


def test_app_lifespan_runs_recovery_after_runtime_startup(monkeypatch) -> None:
    calls: list[str] = []

    class _Lifecycle:
        async def startup(self) -> None:
            calls.append("runtime-startup")

        async def shutdown(self) -> None:
            calls.append("runtime-shutdown")

    monkeypatch.setattr(main, "create_local_ai_runtime_lifecycle_from_env", lambda: _Lifecycle())
    monkeypatch.setattr(main, "reconcile_stranded_runner_jobs", lambda: calls.append("runner-recovery"))

    async def _exercise() -> None:
        app = FastAPI()
        async with main.lifespan(app):
            calls.append("serving")

    asyncio.run(_exercise())
    assert calls == ["runtime-startup", "runner-recovery", "serving", "runtime-shutdown"]
