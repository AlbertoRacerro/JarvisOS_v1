from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.local_worktree_actuator as actuator_module
from scripts.local_worktree_actuator import (
    ActuatorCode,
    ActuatorRefusal,
    Capability,
    LocalWorktreeActuator,
    RequestContext,
    WriterGuardBusy,
    WorkerState,
    _exclusive_writer_guard,
)


def _ctx(request: str, session: str) -> RequestContext:
    return RequestContext(request, "principal", session, Capability.IMPLEMENTER)


def test_writer_guard_is_stable_and_non_reentrant(tmp_path: Path) -> None:
    guard = tmp_path / "worktree.guard"

    with _exclusive_writer_guard(guard):
        assert guard.exists()
        with pytest.raises(WriterGuardBusy):
            with _exclusive_writer_guard(guard):
                pass

    assert guard.exists()
    with _exclusive_writer_guard(guard):
        pass
    assert guard.exists()


def test_writer_guard_is_released_by_process_death(tmp_path: Path) -> None:
    guard = tmp_path / "worktree.guard"
    marker = tmp_path / "locked"
    code = """
import sys
import time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.local_worktree_actuator import _exclusive_writer_guard
with _exclusive_writer_guard(Path(sys.argv[2])):
    Path(sys.argv[3]).write_text('locked', encoding='utf-8')
    time.sleep(60)
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", code, str(ROOT), str(guard), str(marker)],
        cwd=ROOT,
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"guard child exited early with {proc.returncode}")
            time.sleep(0.02)
        assert marker.exists(), "child did not acquire guard"

        with pytest.raises(WriterGuardBusy):
            with _exclusive_writer_guard(guard):
                pass
    finally:
        proc.kill()
        proc.wait(timeout=10)

    with _exclusive_writer_guard(guard):
        pass
    assert guard.exists()


def test_write_holds_guard_across_owner_check_and_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = WorkerState(tmp_path / "state")
    actuator = LocalWorktreeActuator(state)
    owner = _ctx("owner-request", "owner-session")
    successor = _ctx("successor-request", "successor-session")
    worktree_id = "wt-concurrency"
    actuator.acquire_writer(owner, worktree_id)

    entered = threading.Event()
    proceed = threading.Event()
    result: list[str] = []
    failure: list[BaseException] = []

    def blocked_core_write(self, ctx, repository_id, actual_worktree_id, relative_path, text):
        self._require_writer(ctx, actual_worktree_id)
        entered.set()
        assert proceed.wait(timeout=10)
        return "digest"

    monkeypatch.setattr(
        actuator_module._core.LocalWorktreeActuator,
        "write_text",
        blocked_core_write,
    )

    def run_owner() -> None:
        try:
            result.append(
                actuator.write_text(owner, "repo", worktree_id, "file.txt", "value")
            )
        except BaseException as exc:  # pragma: no cover - assertion below reports it
            failure.append(exc)

    thread = threading.Thread(target=run_owner)
    thread.start()
    assert entered.wait(timeout=10)

    with pytest.raises(ActuatorRefusal) as busy:
        actuator.release_writer(owner, worktree_id)
    assert busy.value.code == ActuatorCode.WORKTREE_BUSY

    with pytest.raises(ActuatorRefusal) as acquire_busy:
        actuator.acquire_writer(successor, worktree_id)
    assert acquire_busy.value.code == ActuatorCode.WORKTREE_BUSY

    proceed.set()
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert failure == []
    assert result == ["digest"]

    actuator.release_writer(owner, worktree_id)
    actuator.acquire_writer(successor, worktree_id)
    with pytest.raises(ActuatorRefusal) as stale:
        actuator.write_text(owner, "repo", worktree_id, "file.txt", "stale")
    assert stale.value.code == ActuatorCode.WORKTREE_BUSY
