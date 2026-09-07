from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


repository_delivery = load_script("repository_delivery")
actuator = load_script("local_worktree_actuator")

ActuatorCode = actuator.ActuatorCode
ActuatorRefusal = actuator.ActuatorRefusal
Capability = actuator.Capability
LocalWorktreeActuator = actuator.LocalWorktreeActuator
NamedProfile = actuator.NamedProfile
RepositoryRegistration = actuator.RepositoryRegistration
RequestContext = actuator.RequestContext
WorkerState = actuator.WorkerState
WorktreeRegistration = actuator.WorktreeRegistration
zero_worker_cloud_capabilities = actuator.zero_worker_cloud_capabilities


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


def fixture_worker(tmp_path: Path) -> tuple[LocalWorktreeActuator, RequestContext, RequestContext, Path, str]:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    worktrees = tmp_path / "worktrees"
    worktrees.mkdir()
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "clone", str(remote), str(work))
    git(work, "config", "user.name", "Repository Config Must Not Own Commit Identity")
    git(work, "config", "user.email", "repo-config@example.invalid")
    (work / "README.md").write_text("base\n", encoding="utf-8")
    git(work, "add", "README.md")
    git(work, "commit", "-m", "base")
    git(work, "branch", "-M", "feature")
    git(work, "push", "origin", "HEAD:refs/heads/feature")
    base = git(work, "rev-parse", "HEAD")
    common = git(work, "rev-parse", "--path-format=absolute", "--git-common-dir")

    state = WorkerState(
        tmp_path / "state",
        worker_id="worker-a",
        commit_author_name="Maintainer Worker",
        commit_author_email="worker@example.invalid",
    )
    worker = LocalWorktreeActuator(state)
    worker.enroll_repository(
        RepositoryRegistration(
            repository_id="repo",
            root=str(work),
            remote_host="github.com",
            owner="owner",
            repo="repo",
            common_git_dir=common,
            default_branch="master",
            worktree_root=str(worktrees),
        )
    )
    # Existing/main worktree attachment is an explicit activation exception to
    # the create-under-root path used for actuator-created worktrees.
    payload = worker.state.registry()
    payload["worktrees"]["tree"] = {
        "worktree_id": "tree",
        "repository_id": "repo",
        "path": str(work),
        "branch": "feature",
        "worker_id": "worker-a",
        "durable_commit": base,
    }
    worker.state.replace_registry(payload)
    worker._claim_physical_worktree("tree")
    implementer = RequestContext("req-i", "principal", "session-i", Capability.IMPLEMENTER)
    reviewer = RequestContext("req-r", "principal", "session-r", Capability.REVIEWER)
    return worker, implementer, reviewer, work, base


def test_zero_worker_only_disables_local_capability() -> None:
    projection = zero_worker_cloud_capabilities()
    assert projection["local_worktree"] is False
    assert projection["github_api"] is True
    assert projection["github_actions"] is True
    assert projection["cloud_semantic_review"] is True
    assert projection["exact_head_browser_proof"] is True


def test_offline_worker_refusal_is_local_only(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, _base = fixture_worker(tmp_path)
    worker.online = False
    with pytest.raises(ActuatorRefusal) as exc:
        worker.git_status(implementer, "repo", "tree")
    assert exc.value.code == ActuatorCode.WORKER_OFFLINE
    assert zero_worker_cloud_capabilities()["github_api"] is True


def test_reviewer_is_read_only(tmp_path: Path) -> None:
    worker, _implementer, reviewer, _work, _base = fixture_worker(tmp_path)
    assert worker.git_status(reviewer, "repo", "tree") == ""
    with pytest.raises(ActuatorRefusal) as exc:
        worker.acquire_writer(reviewer, "tree")
    assert exc.value.code == ActuatorCode.REVIEWER_READ_ONLY


def test_writer_lock_is_single_owner_and_non_destructive(tmp_path: Path) -> None:
    worker, implementer, _reviewer, work, _base = fixture_worker(tmp_path)
    (work / "README.md").write_text("dirty\n", encoding="utf-8")
    worker.acquire_writer(implementer, "tree")
    with pytest.raises(ActuatorRefusal) as exc:
        worker.acquire_writer(
            RequestContext("req-2", "principal", "session-2", Capability.IMPLEMENTER),
            "tree",
        )
    assert exc.value.code == ActuatorCode.WORKTREE_BUSY
    assert (work / "README.md").read_text(encoding="utf-8") == "dirty\n"
    worker.release_writer(implementer, "tree")


def test_writer_lease_rejects_cross_session_mutation_and_release(tmp_path: Path) -> None:
    worker, owner, _reviewer, work, base = fixture_worker(tmp_path)
    intruder = RequestContext("req-x", "principal", "session-x", Capability.IMPLEMENTER)
    worker.acquire_writer(owner, "tree")

    for operation in (
        lambda: worker.write_text(intruder, "repo", "tree", "README.md", "intruder\n"),
        lambda: worker.stage_paths(intruder, "repo", "tree", ["README.md"]),
        lambda: worker.commit(intruder, "repo", "tree", "intruder commit"),
        lambda: worker.push_branch(
            intruder,
            "repo",
            "tree",
            intended_local_commit=base,
            expected_remote_head=base,
        ),
        lambda: worker.release_writer(intruder, "tree"),
    ):
        with pytest.raises(ActuatorRefusal) as exc:
            operation()
        assert exc.value.code == ActuatorCode.WORKTREE_BUSY

    assert (work / "README.md").read_text(encoding="utf-8") == "base\n"
    worker.write_text(owner, "repo", "tree", "README.md", "base\nowner\n")
    worker.stage_paths(owner, "repo", "tree", ["README.md"])
    committed = worker.commit(owner, "repo", "tree", "owner commit")
    assert committed != base
    worker.release_writer(owner, "tree")


def test_malformed_writer_lease_fails_closed(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, _base = fixture_worker(tmp_path)
    worker._lock_path("tree").write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ActuatorRefusal) as exc:
        worker.write_text(implementer, "repo", "tree", "README.md", "blocked\n")
    assert exc.value.code == ActuatorCode.WORKTREE_BUSY


def test_exact_worktree_create_uses_registered_root_and_sha(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, base = fixture_worker(tmp_path)
    created = worker.worktree_create(
        implementer,
        "repo",
        source_sha=base,
        branch="actuator-feature",
        directory_name="candidate-1",
    )
    assert created.worker_id == "worker-a"
    assert Path(created.path).parent == tmp_path / "worktrees"
    assert git(Path(created.path), "rev-parse", "HEAD") == base
    assert git(Path(created.path), "branch", "--show-current") == "actuator-feature"


def test_git_admin_targets_refuse_before_bytes_change(tmp_path: Path) -> None:
    worker, implementer, _reviewer, work, _base = fixture_worker(tmp_path)
    config = Path(git(work, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "config"
    before = config.read_bytes()
    for target in [".git", ".git/config", ".git/HEAD", ".git/info/grafts"]:
        with pytest.raises(ActuatorRefusal) as exc:
            worker.validate_write_target(implementer, "repo", "tree", target)
        assert exc.value.code == ActuatorCode.GIT_ADMIN_PATH_REFUSED
    assert config.read_bytes() == before


def test_path_escape_and_sensitive_paths_refuse(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, _base = fixture_worker(tmp_path)
    with pytest.raises(ActuatorRefusal) as exc:
        worker.validate_write_target(implementer, "repo", "tree", "../outside.txt")
    assert exc.value.code == ActuatorCode.PATH_ESCAPE
    with pytest.raises(ActuatorRefusal) as exc:
        worker.validate_write_target(implementer, "repo", "tree", ".github/workflows/ci.yml")
    assert exc.value.code == repository_delivery.DeliveryCode.SENSITIVE_PATH_REFUSED
    for protected in ["scripts/local_worktree_ipc.py", "backend/tests/test_local_worktree_ipc.py"]:
        with pytest.raises(ActuatorRefusal) as exc:
            worker.validate_write_target(implementer, "repo", "tree", protected)
        assert exc.value.code == repository_delivery.DeliveryCode.SENSITIVE_PATH_REFUSED


def test_symlink_escape_refuses_when_supported(tmp_path: Path) -> None:
    worker, implementer, _reviewer, work, _base = fixture_worker(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = work / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable on this platform")
    with pytest.raises(ActuatorRefusal) as exc:
        worker.validate_write_target(implementer, "repo", "tree", "escape/file.txt")
    assert exc.value.code == ActuatorCode.PATH_ESCAPE


def test_mutable_worktree_profiles_never_launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worker, implementer, reviewer, _work, _base = fixture_worker(tmp_path)
    worker.profiles["pytest"] = NamedProfile("pytest", worker_owned=False, executes_worktree_content=True)
    launched = False

    def forbidden(*_args, **_kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("child process must not launch")

    monkeypatch.setattr(subprocess, "run", forbidden)
    for ctx in [implementer, reviewer]:
        with pytest.raises(ActuatorRefusal) as exc:
            worker.run_named_profile(ctx, "pytest", repository_id="repo", worktree_id="tree")
        assert exc.value.code == ActuatorCode.LOCAL_TEST_PROFILE_REQUIRES_ISOLATION
    assert launched is False


def test_worker_owned_profile_is_in_process(tmp_path: Path) -> None:
    worker, implementer, reviewer, _work, _base = fixture_worker(tmp_path)
    assert worker.run_named_profile(
        implementer, "worker-registry-integrity", repository_id="repo", worktree_id="tree"
    ) == ActuatorCode.OK
    assert worker.run_named_profile(
        reviewer, "worker-registry-integrity", repository_id="repo", worktree_id="tree"
    ) == ActuatorCode.OK


def test_local_commit_survives_requester_and_worker_restart(tmp_path: Path) -> None:
    worker, implementer, _reviewer, work, base = fixture_worker(tmp_path)
    worker.acquire_writer(implementer, "tree")
    worker.write_text(implementer, "repo", "tree", "README.md", "base\nlocal\n")
    worker.stage_paths(implementer, "repo", "tree", ["README.md"])
    committed = worker.commit(implementer, "repo", "tree", "local durable commit")
    assert committed != base
    assert git(work, "show", "-s", "--format=%an <%ae>", committed) == (
        "Maintainer Worker <worker@example.invalid>"
    )
    worker.release_writer(implementer, "tree")

    restarted = LocalWorktreeActuator(WorkerState(tmp_path / "state"))
    registry = restarted.state.registry()
    assert registry["worktrees"]["tree"]["durable_commit"] == committed
    assert git(work, "rev-parse", "HEAD") == committed


def test_wrong_worker_cannot_claim_persistent_worktree(tmp_path: Path) -> None:
    worker, _implementer, _reviewer, work, _base = fixture_worker(tmp_path)
    with pytest.raises(ActuatorRefusal) as exc:
        worker.attach_worktree(
            WorktreeRegistration(
                worktree_id="tree-2",
                repository_id="repo",
                path=str(work),
                branch="feature",
                worker_id="worker-b",
            )
        )
    assert exc.value.code == ActuatorCode.WORKTREE_IDENTITY_MISMATCH


def test_dispatch_exposes_only_bounded_durable_lifecycle(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, base = fixture_worker(tmp_path)
    created = worker.dispatch(
        implementer,
        "worktree_create",
        repository_id="repo",
        source_sha=base,
        branch="ipc-feature",
        directory_name="ipc-candidate",
    )
    worker.dispatch(implementer, "acquire_writer", worktree_id=created.worktree_id)
    worker.dispatch(implementer, "release_writer", worktree_id=created.worktree_id)


def test_dispatch_audits_unknown_refusal_without_secret_fields(tmp_path: Path) -> None:
    worker, implementer, _reviewer, _work, _base = fixture_worker(tmp_path)
    with pytest.raises(ActuatorRefusal) as exc:
        worker.dispatch(implementer, "arbitrary_shell", command="whoami")
    assert exc.value.code == ActuatorCode.CAPABILITY_UNAVAILABLE
    joined = worker.state.audit_path.read_text(encoding="utf-8").lower()
    assert "capability_unavailable" in joined
    assert "authorization" not in joined
    assert "bearer " not in joined
    assert "record_digest" in joined
