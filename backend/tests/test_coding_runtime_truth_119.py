from __future__ import annotations

import io
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

import pytest

from app.modules.coding.repository_truth import RepositoryTruthError, RepositoryTruthResult
from app.modules.coding.runtime_truth import (
    RUNTIME_REPOSITORY,
    ProbeResult,
    RuntimeSnapshot,
    _minimal_git_environment,
    _run_git_probe,
    capture_runtime_snapshot,
    observe_runtime_truth,
)

LOCAL_SHA = "a" * 40
TARGET_SHA = "b" * 40
OTHER_SHA = "c" * 40


def snapshot(
    *,
    sha: str | None = LOCAL_SHA,
    dirty: str = "clean",
    head_state: str = "branch",
    branch: str | None = "master",
    provenance: str = "process_start_observation",
    failure: str | None = None,
    root_identity: str = "root-digest",
    git_available: bool = True,
) -> RuntimeSnapshot:
    return RuntimeSnapshot(
        root_identity=root_identity,
        observed_at="2026-09-04T00:00:00+00:00",
        git_available=git_available,
        git_sha=sha,
        head_state=head_state,  # type: ignore[arg-type]
        branch=branch,
        dirty_state=dirty,  # type: ignore[arg-type]
        provenance=provenance,  # type: ignore[arg-type]
        failure_code=failure,
    )


def remote_result(
    sha: str,
    *,
    payload: dict[str, object] | None = None,
    partial: bool = False,
) -> RepositoryTruthResult:
    return RepositoryTruthResult(
        provider="github",
        repository=RUNTIME_REPOSITORY,
        operation="repository_ref_truth" if payload is None else "compare_truth",
        requested_ref="master",
        resolved_sha=sha,
        partial=partial,
        payload=payload or {"sha": sha},
        observed_at="2026-09-04T00:00:01+00:00",
    )


class FakeRepositoryTruth:
    def __init__(
        self,
        targets: list[str] | None = None,
        *,
        compare: RepositoryTruthResult | BaseException | None = None,
        target_error: BaseException | None = None,
    ) -> None:
        self.targets = deque(targets or [TARGET_SHA, TARGET_SHA])
        self.compare_value = compare
        self.target_error = target_error
        self.target_calls = 0
        self.compare_calls: list[tuple[str, str]] = []

    def repository_ref_truth(self, repository: str, ref: str) -> RepositoryTruthResult:
        self.target_calls += 1
        if self.target_error is not None:
            raise self.target_error
        sha = self.targets.popleft()
        return remote_result(sha)

    def compare_truth(
        self, repository: str, base_ref: str, head_ref: str
    ) -> RepositoryTruthResult:
        self.compare_calls.append((base_ref, head_ref))
        if isinstance(self.compare_value, BaseException):
            raise self.compare_value
        if self.compare_value is not None:
            return self.compare_value
        return remote_result(
            head_ref,
            payload={
                "base_sha": base_ref,
                "head_sha": head_ref,
                "status": "ahead",
                "ahead_by": 1,
                "behind_by": 0,
                "files": [],
            },
        )


def observe(
    repo: FakeRepositoryTruth,
    *,
    startup: RuntimeSnapshot | None = None,
    live: RuntimeSnapshot | None = None,
    repository: str = RUNTIME_REPOSITORY,
):
    startup = startup or snapshot()
    live = live or snapshot(provenance="live_worktree_observation")
    return observe_runtime_truth(
        repository=repository,
        target_ref="master",
        configured_repositories=(RUNTIME_REPOSITORY, "owner/other"),
        startup=startup,
        repository_truth=repo,
        live_snapshot_factory=lambda: live,
    )


def test_clean_exact_match_is_aligned_and_target_is_rechecked() -> None:
    repo = FakeRepositoryTruth([LOCAL_SHA, LOCAL_SHA])
    result = observe(repo)
    assert result.alignment == "aligned"
    assert result.reason == "exact_clean_match"
    assert result.remote_sha == LOCAL_SHA
    assert repo.target_calls == 2
    assert repo.compare_calls == []


def test_dirty_matching_sha_is_unknown_and_short_circuits_relation() -> None:
    repo = FakeRepositoryTruth([LOCAL_SHA, LOCAL_SHA])
    dirty = snapshot(dirty="dirty", provenance="live_worktree_observation")
    result = observe(repo, live=dirty)
    assert result.alignment == "unknown"
    assert result.reason == "worktree_changed_since_start"
    assert result.worktree_changed_since_start is True
    assert repo.target_calls == 1
    assert repo.compare_calls == []


def test_dirty_startup_and_live_is_unknown_without_second_target_read() -> None:
    repo = FakeRepositoryTruth([LOCAL_SHA, LOCAL_SHA])
    start = snapshot(dirty="dirty")
    live = snapshot(dirty="dirty", provenance="live_worktree_observation")
    result = observe(repo, startup=start, live=live)
    assert result.reason == "dirty_local_state"
    assert result.alignment == "unknown"
    assert repo.target_calls == 1


def test_live_sha_change_forces_unknown_even_if_live_matches_target() -> None:
    repo = FakeRepositoryTruth([TARGET_SHA])
    live = snapshot(sha=TARGET_SHA, provenance="live_worktree_observation")
    result = observe(repo, live=live)
    assert result.alignment == "unknown"
    assert result.reason == "worktree_changed_since_start"
    assert result.worktree_changed_since_start is True


def test_partial_compare_can_prove_local_behind_from_top_level_relation() -> None:
    compare = remote_result(
        TARGET_SHA,
        partial=True,
        payload={
            "base_sha": LOCAL_SHA,
            "head_sha": TARGET_SHA,
            "status": "ahead",
            "ahead_by": 3,
            "behind_by": 0,
            "files": [{"filename": "x.py"}],
        },
    )
    repo = FakeRepositoryTruth([TARGET_SHA, TARGET_SHA], compare=compare)
    result = observe(repo)
    assert result.alignment == "local_behind"
    assert result.compare_partial is True
    assert repo.compare_calls == [(LOCAL_SHA, TARGET_SHA)]
    assert repo.target_calls == 2


@pytest.mark.parametrize(
    ("status", "ahead", "behind"),
    [("behind", 0, 2), ("diverged", 2, 1)],
)
def test_valid_nonbehind_relation_is_divergent(
    status: str, ahead: int, behind: int
) -> None:
    compare = remote_result(
        TARGET_SHA,
        payload={
            "base_sha": LOCAL_SHA,
            "head_sha": TARGET_SHA,
            "status": status,
            "ahead_by": ahead,
            "behind_by": behind,
            "files": [],
        },
    )
    result = observe(FakeRepositoryTruth([TARGET_SHA, TARGET_SHA], compare=compare))
    assert result.alignment == "divergent"


@pytest.mark.parametrize(
    ("status", "ahead", "behind"),
    [("ahead", 1, 1), ("identical", 0, 0), ("mystery", 2, 0)],
)
def test_contradictory_or_unknown_relation_is_unknown(
    status: str, ahead: int, behind: int
) -> None:
    compare = remote_result(
        TARGET_SHA,
        payload={
            "base_sha": LOCAL_SHA,
            "head_sha": TARGET_SHA,
            "status": status,
            "ahead_by": ahead,
            "behind_by": behind,
            "files": [],
        },
    )
    result = observe(FakeRepositoryTruth([TARGET_SHA], compare=compare))
    assert result.alignment == "unknown"
    assert result.reason == "remote_relation_unavailable"


def test_compare_exact_pair_mismatch_is_unknown() -> None:
    compare = remote_result(
        TARGET_SHA,
        payload={
            "base_sha": OTHER_SHA,
            "head_sha": TARGET_SHA,
            "status": "ahead",
            "ahead_by": 1,
            "behind_by": 0,
            "files": [],
        },
    )
    result = observe(FakeRepositoryTruth([TARGET_SHA], compare=compare))
    assert result.alignment == "unknown"


def test_unpushed_local_sha_is_unknown_without_local_diff_engine() -> None:
    repo = FakeRepositoryTruth(
        [TARGET_SHA], compare=RepositoryTruthError("not_found", "not remote")
    )
    result = observe(repo)
    assert result.alignment == "unknown"
    assert result.reason == "remote_relation_unavailable"
    assert result.compare is None
    assert result.remote_failure_code == "not_found"


def test_target_move_invalidates_otherwise_aligned_result() -> None:
    repo = FakeRepositoryTruth([LOCAL_SHA, TARGET_SHA])
    result = observe(repo)
    assert result.alignment == "unknown"
    assert result.reason == "remote_target_moved"
    assert result.remote_sha == TARGET_SHA


def test_remote_target_failure_is_typed_unknown() -> None:
    repo = FakeRepositoryTruth(
        target_error=RepositoryTruthError("rate_limited", "limited")
    )
    result = observe(repo)
    assert result.alignment == "unknown"
    assert result.reason == "remote_target_unavailable"
    assert result.remote_failure_code == "rate_limited"


def test_repository_mismatch_never_calls_remote_or_live_observer() -> None:
    repo = FakeRepositoryTruth([TARGET_SHA])
    live_called = False

    def live() -> RuntimeSnapshot:
        nonlocal live_called
        live_called = True
        return snapshot(provenance="live_worktree_observation")

    result = observe_runtime_truth(
        repository="owner/other",
        target_ref="master",
        configured_repositories=(RUNTIME_REPOSITORY, "owner/other"),
        startup=snapshot(),
        repository_truth=repo,
        live_snapshot_factory=live,
    )
    assert result.reason == "repository_mismatch"
    assert repo.target_calls == 0
    assert live_called is False


def test_detached_clean_sha_can_be_aligned_by_sha() -> None:
    start = snapshot(head_state="detached", branch=None)
    live = snapshot(
        head_state="detached", branch=None, provenance="live_worktree_observation"
    )
    result = observe(FakeRepositoryTruth([LOCAL_SHA, LOCAL_SHA]), startup=start, live=live)
    assert result.alignment == "aligned"


class ProbeQueue:
    def __init__(self, results: list[ProbeResult | BaseException]) -> None:
        self.results = deque(results)
        self.calls: list[tuple[tuple[str, ...], Path, float]] = []

    def __call__(self, argv: tuple[str, ...], cwd: Path, timeout: float) -> ProbeResult:
        self.calls.append((argv, cwd, timeout))
        value = self.results.popleft()
        if isinstance(value, BaseException):
            raise value
        return value


def test_capture_clean_snapshot_uses_only_fixed_git_probe_family(tmp_path: Path) -> None:
    probe = ProbeQueue(
        [
            ProbeResult(0, str(tmp_path.resolve()).encode(), b""),
            ProbeResult(0, LOCAL_SHA.encode(), b""),
            ProbeResult(0, b"master\n", b""),
            ProbeResult(0, b"", b""),
        ]
    )
    result = capture_runtime_snapshot(
        "live_worktree_observation", root=tmp_path, probe=probe
    )
    assert result.git_sha == LOCAL_SHA
    assert result.dirty_state == "clean"
    assert result.branch == "master"
    assert [call[0] for call in probe.calls] == [
        ("git", "rev-parse", "--show-toplevel"),
        ("git", "rev-parse", "--verify", "HEAD"),
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        ("git", "status", "--porcelain=v1", "--untracked-files=normal"),
    ]
    assert all(call[1] == tmp_path.resolve() for call in probe.calls)
    assert all(0 < call[2] <= 2.0 for call in probe.calls)


def test_capture_hostile_status_is_only_dirty_boolean(tmp_path: Path) -> None:
    probe = ProbeQueue(
        [
            ProbeResult(0, str(tmp_path.resolve()).encode(), b""),
            ProbeResult(0, LOCAL_SHA.encode(), b""),
            ProbeResult(0, b"master\n", b""),
            ProbeResult(0, b"?? $(touch PWNED);secret.txt\n", b""),
        ]
    )
    result = capture_runtime_snapshot(
        "live_worktree_observation", root=tmp_path, probe=probe
    )
    assert result.dirty_state == "dirty"
    assert "PWNED" not in repr(result)


def test_capture_root_mismatch_stops_after_first_probe(tmp_path: Path) -> None:
    other = tmp_path / "other"
    probe = ProbeQueue([ProbeResult(0, str(other).encode(), b"")])
    result = capture_runtime_snapshot(
        "live_worktree_observation", root=tmp_path, probe=probe
    )
    assert result.failure_code == "root_mismatch"
    assert result.dirty_state == "unknown"
    assert len(probe.calls) == 1
    assert str(tmp_path) not in result.root_identity


def test_capture_git_unavailable_is_typed(tmp_path: Path) -> None:
    probe = ProbeQueue([RuntimeError("should be wrapped by test probe")])
    with pytest.raises(RuntimeError):
        capture_runtime_snapshot(
            "live_worktree_observation", root=tmp_path, probe=probe
        )


def test_capture_probe_timeout_becomes_typed_unknown(tmp_path: Path) -> None:
    from app.modules.coding.runtime_truth import RuntimeTruthError

    probe = ProbeQueue([RuntimeTruthError("probe_timeout", "late")])
    result = capture_runtime_snapshot(
        "live_worktree_observation", root=tmp_path, probe=probe
    )
    assert result.failure_code == "probe_timeout"
    assert result.dirty_state == "unknown"


def test_snapshot_uses_one_shared_monotonic_deadline(tmp_path: Path) -> None:
    values = iter([0.0, 0.25, 0.5, 0.75, 1.0])
    probe = ProbeQueue(
        [
            ProbeResult(0, str(tmp_path.resolve()).encode(), b""),
            ProbeResult(0, LOCAL_SHA.encode(), b""),
            ProbeResult(1, b"", b""),
            ProbeResult(0, b"", b""),
        ]
    )
    result = capture_runtime_snapshot(
        "live_worktree_observation",
        root=tmp_path,
        probe=probe,
        clock=lambda: next(values),
    )
    assert result.head_state == "detached"
    assert [round(call[2], 2) for call in probe.calls] == [1.75, 1.5, 1.25, 1.0]


def test_minimal_git_environment_drops_credentials() -> None:
    env = _minimal_git_environment(
        {
            "PATH": "/bin",
            "SystemRoot": "C:/Windows",
            "GITHUB_TOKEN": "secret",
            "OPENAI_API_KEY": "secret2",
        }
    )
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["PATH"] == "/bin"
    assert "GITHUB_TOKEN" not in env
    assert "OPENAI_API_KEY" not in env


class FakePopen:
    last_kwargs: dict[str, Any] | None = None

    def __init__(self, args: list[str], **kwargs: Any) -> None:
        type(self).last_kwargs = {"args": args, **kwargs}
        self.stdout = io.BytesIO(b"ok\n")
        self.stderr = io.BytesIO(b"")
        self.returncode = 0

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode

    def poll(self) -> int:
        return self.returncode

    def terminate(self) -> None:
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


def test_default_probe_is_shell_free_fixed_cwd_and_noninteractive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    result = _run_git_probe(("git", "rev-parse", "--verify", "HEAD"), tmp_path, 1.0)
    assert result.stdout == b"ok\n"
    kwargs = FakePopen.last_kwargs
    assert kwargs is not None
    assert kwargs["shell"] is False
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
    assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_startup_snapshot_is_not_recomputed_by_alignment_requests() -> None:
    startup = snapshot(sha=LOCAL_SHA)
    changed_live = snapshot(sha=TARGET_SHA, provenance="live_worktree_observation")
    repo = FakeRepositoryTruth([TARGET_SHA, TARGET_SHA])
    first = observe(repo, startup=startup, live=changed_live)
    assert first.alignment == "unknown"
    assert startup.git_sha == LOCAL_SHA
    assert startup.provenance == "process_start_observation"
