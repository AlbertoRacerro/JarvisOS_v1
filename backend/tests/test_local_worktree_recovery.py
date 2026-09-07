from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("repository_delivery", "scripts/repository_delivery.py")
actuator_mod = _load("local_worktree_actuator", "scripts/local_worktree_actuator.py")
recovery_mod = _load("local_worktree_recovery", ".github/local_worktree_recovery.py")


def _ctx(request_id: str, session_id: str):
    return actuator_mod.RequestContext(
        request_id=request_id,
        principal_id="maintainer-test",
        session_id=session_id,
        capability=actuator_mod.Capability.IMPLEMENTER,
    )


def test_live_writer_still_refuses_second_writer(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    other = _ctx("request-b", "session-b")

    actuator.acquire_writer(owner, "worktree-1")
    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        actuator.acquire_writer(other, "worktree-1")
    assert exc_info.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY


def test_recovery_is_not_exposed_by_model_dispatch(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)

    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        actuator.dispatch(_ctx("request-a", "session-a"), "recover_interrupted_writer")
    assert exc_info.value.code == actuator_mod.ActuatorCode.CAPABILITY_UNAVAILABLE


def test_exact_owner_generation_recovery_preserves_state_and_allows_new_writer(
    tmp_path: Path,
) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    successor = _ctx("request-b", "session-b")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    recovery = recovery_mod.InterruptedWriterRecovery(actuator)
    lock = actuator._lock_path(worktree_id)
    lease_digest = recovery_mod.hashlib.sha256(lock.read_bytes()).hexdigest()
    snapshot = recovery_mod.RecoveryInspection(
        lease_digest=lease_digest,
        head_sha="a" * 40,
        status_digest="b" * 64,
        durable_commit="c" * 40,
    )
    recovery.inspect = lambda repository_id, current_worktree_id: snapshot  # type: ignore[method-assign]

    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        recovery.recover(
            "repo-1",
            worktree_id,
            expected_request_id="wrong-request",
            expected_session_id="session-a",
            expected_lease_digest=lease_digest,
        )
    assert exc_info.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY
    assert lock.exists()
    assert "request-a" in lock.read_text(encoding="utf-8")

    result = recovery.recover(
        "repo-1",
        worktree_id,
        expected_request_id="request-a",
        expected_session_id="session-a",
        expected_lease_digest=lease_digest,
    )
    assert result == snapshot
    assert not lock.exists()

    actuator.acquire_writer(successor, worktree_id)
    actuator._require_writer(successor, worktree_id)

    audit = state.audit_path.read_text(encoding="utf-8")
    assert "recover_interrupted_writer" in audit
    assert "request-a" not in audit
    assert "session-a" not in audit


def test_stale_generation_cannot_clear_newer_lease(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    recovery = recovery_mod.InterruptedWriterRecovery(actuator)
    lock = actuator._lock_path(worktree_id)
    current_digest = recovery_mod.hashlib.sha256(lock.read_bytes()).hexdigest()
    snapshot = recovery_mod.RecoveryInspection(
        lease_digest=current_digest,
        head_sha="a" * 40,
        status_digest="b" * 64,
        durable_commit="c" * 40,
    )
    recovery.inspect = lambda repository_id, current_worktree_id: snapshot  # type: ignore[method-assign]

    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        recovery.recover(
            "repo-1",
            worktree_id,
            expected_request_id="request-a",
            expected_session_id="session-a",
            expected_lease_digest="0" * 64,
        )
    assert exc_info.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY
    assert lock.exists()
