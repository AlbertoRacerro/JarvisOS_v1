from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


repository_delivery = _load("repository_delivery", "scripts/repository_delivery.py")
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


def test_recovery_is_not_exposed_and_its_source_is_immutable(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)

    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        actuator.dispatch(_ctx("request-a", "session-a"), "recover_interrupted_writer")
    assert exc_info.value.code == actuator_mod.ActuatorCode.CAPABILITY_UNAVAILABLE
    assert repository_delivery.is_sensitive_path(".github/local_worktree_recovery.py")


def test_inspect_revalidates_lease_around_read_only_git_state(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    calls: list[tuple[str, ...]] = []

    class FakeDelivery:
        def _git(self, args):
            calls.append(tuple(args))
            if args == ["rev-parse", "HEAD"]:
                return SimpleNamespace(stdout="a" * 40 + "\n")
            if args == ["status", "--porcelain=v1", "--untracked-files=all"]:
                return SimpleNamespace(stdout=" M preserved-dirty.txt\n")
            raise AssertionError(args)

    tree = SimpleNamespace(durable_commit="c" * 40)
    actuator._lookup = lambda repository_id, current_worktree_id: (object(), tree)  # type: ignore[method-assign]
    actuator._delivery = lambda repo, current_tree: FakeDelivery()  # type: ignore[method-assign]

    inspection = recovery_mod.InterruptedWriterRecovery(actuator).inspect(
        "repo-1",
        worktree_id,
    )
    assert inspection.head_sha == "a" * 40
    assert inspection.durable_commit == "c" * 40
    assert calls == [
        ("rev-parse", "HEAD"),
        ("status", "--porcelain=v1", "--untracked-files=all"),
    ]
    assert actuator._lock_path(worktree_id).exists()


def test_exact_owner_generation_recovery_allows_new_writer(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    successor = _ctx("request-b", "session-b")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    recovery = recovery_mod.InterruptedWriterRecovery(actuator)
    lock = actuator._lock_path(worktree_id)
    lease = recovery._lease_state(lock)
    snapshot = recovery_mod.RecoveryInspection(
        lease_digest=lease.digest,
        lease_generation=lease.generation,
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
            expected_lease_generation=lease.generation,
        )
    assert exc_info.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY
    assert lock.exists()
    assert "request-a" in lock.read_text(encoding="utf-8")

    result = recovery.recover(
        "repo-1",
        worktree_id,
        expected_request_id="request-a",
        expected_session_id="session-a",
        expected_lease_generation=lease.generation,
    )
    assert result == snapshot
    assert not lock.exists()

    actuator.acquire_writer(successor, worktree_id)
    actuator._require_writer(successor, worktree_id)

    audit_rows = [
        json.loads(line)
        for line in state.audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    recovery_rows = [
        row
        for row in audit_rows
        if row.get("operation")
        in {
            "recover_interrupted_writer_intent",
            "recover_interrupted_writer_complete",
        }
    ]
    assert [row["operation"] for row in recovery_rows] == [
        "recover_interrupted_writer_intent",
        "recover_interrupted_writer_complete",
    ]
    for row in recovery_rows:
        assert "request_id" not in row
        assert "session_id" not in row
        serialized = json.dumps(row, sort_keys=True)
        assert "request-a" not in serialized
        assert "session-a" not in serialized


def test_release_reacquire_invalidates_stale_generation(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    recovery = recovery_mod.InterruptedWriterRecovery(actuator)
    lock = actuator._lock_path(worktree_id)
    old_lease = recovery._lease_state(lock)

    actuator.release_writer(owner, worktree_id)
    actuator.acquire_writer(owner, worktree_id)
    new_lease = recovery._lease_state(lock)
    assert new_lease.generation != old_lease.generation

    stale_snapshot = recovery_mod.RecoveryInspection(
        lease_digest=old_lease.digest,
        lease_generation=old_lease.generation,
        head_sha="a" * 40,
        status_digest="b" * 64,
        durable_commit="c" * 40,
    )
    recovery.inspect = lambda repository_id, current_worktree_id: stale_snapshot  # type: ignore[method-assign]

    with pytest.raises(actuator_mod.ActuatorRefusal) as exc_info:
        recovery.recover(
            "repo-1",
            worktree_id,
            expected_request_id="request-a",
            expected_session_id="session-a",
            expected_lease_generation=old_lease.generation,
        )
    assert exc_info.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY
    assert lock.exists()


def test_recovery_guard_blocks_release_and_successor_until_unlink_commit(tmp_path: Path) -> None:
    state = actuator_mod.WorkerState(tmp_path / "state", worker_id="worker")
    actuator = actuator_mod.LocalWorktreeActuator(state)
    owner = _ctx("request-a", "session-a")
    successor = _ctx("request-b", "session-b")
    worktree_id = "worktree-1"
    actuator.acquire_writer(owner, worktree_id)

    recovery = recovery_mod.InterruptedWriterRecovery(actuator)
    lock = actuator._lock_path(worktree_id)
    lease = recovery._lease_state(lock)
    snapshot = recovery_mod.RecoveryInspection(
        lease_digest=lease.digest,
        lease_generation=lease.generation,
        head_sha="a" * 40,
        status_digest="b" * 64,
        durable_commit="c" * 40,
    )
    entered = threading.Event()
    proceed = threading.Event()
    results: list[object] = []
    failures: list[BaseException] = []

    def blocked_inspect(repository_id: str, current_worktree_id: str):
        entered.set()
        assert proceed.wait(timeout=10)
        return snapshot

    recovery.inspect = blocked_inspect  # type: ignore[method-assign]

    def run_recovery() -> None:
        try:
            results.append(
                recovery.recover(
                    "repo-1",
                    worktree_id,
                    expected_request_id="request-a",
                    expected_session_id="session-a",
                    expected_lease_generation=lease.generation,
                )
            )
        except BaseException as exc:  # pragma: no cover - assertion below reports it
            failures.append(exc)

    thread = threading.Thread(target=run_recovery)
    thread.start()
    assert entered.wait(timeout=10)

    with pytest.raises(actuator_mod.ActuatorRefusal) as release_busy:
        actuator.release_writer(owner, worktree_id)
    assert release_busy.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY

    with pytest.raises(actuator_mod.ActuatorRefusal) as acquire_busy:
        actuator.acquire_writer(successor, worktree_id)
    assert acquire_busy.value.code == actuator_mod.ActuatorCode.WORKTREE_BUSY

    proceed.set()
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert failures == []
    assert results == [snapshot]
    assert not lock.exists()

    actuator.acquire_writer(successor, worktree_id)
    actuator._require_writer(successor, worktree_id)
