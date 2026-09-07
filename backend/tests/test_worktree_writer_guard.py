from __future__ import annotations

import importlib.util
import subprocess
import sys
import threading
import time
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


actuator_module = _load("local_worktree_actuator_guard_test", "scripts/local_worktree_actuator.py")
ActuatorCode = actuator_module.ActuatorCode
ActuatorRefusal = actuator_module.ActuatorRefusal
Capability = actuator_module.Capability
LocalWorktreeActuator = actuator_module.LocalWorktreeActuator
RepositoryRegistration = actuator_module.RepositoryRegistration
RequestContext = actuator_module.RequestContext
WorktreeRegistration = actuator_module.WorktreeRegistration
WriterGuardBusy = actuator_module.WriterGuardBusy
WorkerState = actuator_module.WorkerState
_exclusive_writer_guard = actuator_module._exclusive_writer_guard


def _ctx(request: str, session: str):
    return RequestContext(request, "principal", session, Capability.IMPLEMENTER)


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


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


def test_physical_worktree_owner_and_guard_are_shared_across_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "JARVISOS_LOCAL_WORKTREE_HOST_STATE_ROOT",
        str(tmp_path / "host-state"),
    )
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "clone", str(remote), str(work))
    _git(work, "config", "user.name", "Test User")
    _git(work, "config", "user.email", "test@example.invalid")
    (work / "README.md").write_text("base\n", encoding="utf-8")
    _git(work, "add", "README.md")
    _git(work, "commit", "-m", "base")
    _git(work, "branch", "-M", "feature")
    common = _git(work, "rev-parse", "--path-format=absolute", "--git-common-dir")
    head = _git(work, "rev-parse", "HEAD")

    def make_worker(worker_id: str, state_name: str) -> LocalWorktreeActuator:
        worker = LocalWorktreeActuator(WorkerState(tmp_path / state_name, worker_id=worker_id))
        worker.enroll_repository(
            RepositoryRegistration(
                repository_id="repo",
                root=str(work),
                remote_host="github.com",
                owner="owner",
                repo="repo",
                common_git_dir=common,
                default_branch="master",
                worktree_root=str(tmp_path),
            )
        )
        return worker

    worker_a = make_worker("worker-a", "state-a")
    worker_b = make_worker("worker-b", "state-b")
    tree_a = WorktreeRegistration(
        worktree_id="tree-a",
        repository_id="repo",
        path=str(work),
        branch="feature",
        worker_id="worker-a",
        durable_commit=head,
    )
    worker_a.attach_worktree(tree_a)

    tree_b = WorktreeRegistration(
        worktree_id="tree-b",
        repository_id="repo",
        path=str(work),
        branch="feature",
        worker_id="worker-b",
        durable_commit=head,
    )
    with pytest.raises(ActuatorRefusal) as claim:
        worker_b.attach_worktree(tree_b)
    assert claim.value.code == ActuatorCode.WORKTREE_IDENTITY_MISMATCH
    assert "tree-b" not in worker_b.state.registry()["worktrees"]
    assert (work / "README.md").read_text(encoding="utf-8") == "base\n"

    # Even hostile/legacy duplicate registry metadata resolves to one physical
    # guard, so separate WorkerState roots cannot create independent OS locks.
    payload = worker_b.state.registry()
    payload["worktrees"]["tree-b"] = {
        "worktree_id": "tree-b",
        "repository_id": "repo",
        "path": str(work),
        "branch": "feature",
        "worker_id": "worker-b",
        "durable_commit": head,
    }
    worker_b.state.replace_registry(payload)
    guard_a = worker_a._guard_path("tree-a")
    guard_b = worker_b._guard_path("tree-b")
    assert guard_a == guard_b
    with _exclusive_writer_guard(guard_a):
        with pytest.raises(WriterGuardBusy):
            with _exclusive_writer_guard(guard_b):
                pass
    with pytest.raises(ActuatorRefusal) as stale_claim:
        worker_b.acquire_writer(_ctx("b-request", "b-session"), "tree-b")
    assert stale_claim.value.code == ActuatorCode.WORKTREE_IDENTITY_MISMATCH
