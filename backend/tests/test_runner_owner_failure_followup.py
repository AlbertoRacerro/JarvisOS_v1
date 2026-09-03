from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

from app.modules.runner import resilient_service
from app.modules.runner.local_python import ExecutionOwnerBusy
from app.modules.runner.safety import RunnerSafetyError


def test_owned_invocation_failure_reconciles_after_child_ownership_is_gone(monkeypatch) -> None:
    states = iter(("live", "gone"))
    reconciliations: list[str] = []

    monkeypatch.setattr(
        resilient_service,
        "execution_ownership_state",
        lambda _path: next(states),
    )
    monkeypatch.setattr(resilient_service.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        resilient_service,
        "reconcile_stranded_runner_jobs",
        lambda: reconciliations.append("reconciled") or 1,
    )

    resilient_service._reconcile_after_owned_invocation_exit(
        Path("/owned-run"), poll_seconds=0.0
    )

    assert reconciliations == ["reconciled"]


def test_owned_invocation_failure_retries_transient_reconcile_lock(monkeypatch) -> None:
    attempts: list[str] = []

    monkeypatch.setattr(
        resilient_service,
        "execution_ownership_state",
        lambda _path: "gone",
    )
    monkeypatch.setattr(resilient_service.time, "sleep", lambda _seconds: None)

    def _reconcile() -> int:
        attempts.append("attempt")
        if len(attempts) == 1:
            raise sqlite3.OperationalError("database is locked")
        return 1

    monkeypatch.setattr(resilient_service, "reconcile_stranded_runner_jobs", _reconcile)

    resilient_service._reconcile_after_owned_invocation_exit(
        Path("/owned-run"), poll_seconds=0.0
    )

    assert attempts == ["attempt", "attempt"]


def test_owned_invocation_failure_with_unknown_ownership_fails_closed(monkeypatch) -> None:
    reconciliations: list[str] = []
    monkeypatch.setattr(
        resilient_service,
        "execution_ownership_state",
        lambda _path: "unknown",
    )
    monkeypatch.setattr(
        resilient_service,
        "reconcile_stranded_runner_jobs",
        lambda: reconciliations.append("unexpected") or 1,
    )

    resilient_service._reconcile_after_owned_invocation_exit(Path("/owned-run"))

    assert reconciliations == []


def test_exception_after_owner_entry_registers_bounded_recovery_followup(monkeypatch) -> None:
    working_dir = Path("/run-root")
    followups: list[Path] = []

    class _Selection:
        def fetchone(self):
            return {"working_dir": str(working_dir)}

    class _Connection:
        def execute(self, _query, _params):
            return _Selection()

    @contextmanager
    def _open_connection():
        yield _Connection()

    @contextmanager
    def _owner(_working_dir):
        yield

    monkeypatch.setattr(resilient_service, "open_sqlite_connection", _open_connection)
    monkeypatch.setattr(resilient_service, "prepare_execution_owner", _owner)
    monkeypatch.setattr(
        resilient_service._guarded,
        "run_runner_job",
        lambda _runner_job_id: (_ for _ in ()).throw(RuntimeError("owner helper exited")),
    )
    monkeypatch.setattr(
        resilient_service,
        "_start_owner_failure_followup",
        lambda path: followups.append(path),
    )

    with pytest.raises(RuntimeError, match="owner helper exited"):
        resilient_service.run_runner_job("job-1")

    assert followups == [working_dir]


def test_busy_before_owner_entry_does_not_register_recovery_followup(monkeypatch) -> None:
    followups: list[Path] = []

    class _Selection:
        def fetchone(self):
            return {"working_dir": "/run-root"}

    class _Connection:
        def execute(self, _query, _params):
            return _Selection()

    @contextmanager
    def _open_connection():
        yield _Connection()

    @contextmanager
    def _busy_owner(_working_dir):
        raise ExecutionOwnerBusy("busy")
        yield

    monkeypatch.setattr(resilient_service, "open_sqlite_connection", _open_connection)
    monkeypatch.setattr(resilient_service, "prepare_execution_owner", _busy_owner)
    monkeypatch.setattr(
        resilient_service,
        "_start_owner_failure_followup",
        lambda path: followups.append(path),
    )

    with pytest.raises(RunnerSafetyError) as exc_info:
        resilient_service.run_runner_job("job-1")

    assert exc_info.value.code == "runner_job_not_queued"
    assert followups == []
