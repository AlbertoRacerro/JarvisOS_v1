from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.modules.coding.repository_truth import RepositoryTruthError, RepositoryTruthResult
from app.modules.coding import runtime_truth as rt

SHA_LOCAL = "1" * 40
SHA_TARGET = "2" * 40
ROOT_ID = "a" * 64


def snapshot(
    *,
    sha: str | None = SHA_LOCAL,
    dirty: rt.DirtyState = "clean",
    head_state: rt.HeadState = "branch",
    branch: str | None = "master",
    provenance: str = "process_start_observation",
    failure: rt.LocalFailureCode | None = None,
    git_available: bool = True,
) -> rt.RuntimeSnapshot:
    return rt.RuntimeSnapshot(
        root_identity=ROOT_ID,
        observed_at="2026-09-04T00:00:00+00:00",
        git_available=git_available,
        git_sha=sha,
        head_state=head_state,
        branch=branch,
        dirty_state=dirty,
        provenance=provenance,  # type: ignore[arg-type]
        failure_code=failure,
    )


def truth(sha: str, *, partial: bool = False, payload: dict[str, object] | None = None):
    return RepositoryTruthResult(
        provider="github",
        repository=rt.CANONICAL_RUNTIME_REPOSITORY,
        operation="repository_ref_truth",
        requested_ref="master",
        resolved_sha=sha,
        partial=partial,
        payload=payload or {"sha": sha},
        observed_at="2026-09-04T00:00:00+00:00",
    )


class FakeRepositoryTruth:
    def __init__(self, targets: list[str], compare: RepositoryTruthResult | Exception | None = None):
        self.targets = list(targets)
        self.compare_result = compare
        self.ref_calls = 0
        self.compare_calls = 0

    def repository_ref_truth(self, repository: str, ref: str) -> RepositoryTruthResult:
        self.ref_calls += 1
        if not self.targets:
            raise AssertionError("unexpected target re-resolution")
        return truth(self.targets.pop(0))

    def compare_truth(self, repository: str, base_ref: str, head_ref: str) -> RepositoryTruthResult:
        self.compare_calls += 1
        if isinstance(self.compare_result, Exception):
            raise self.compare_result
        assert self.compare_result is not None
        return self.compare_result


def relation(status: str, ahead: int, behind: int, *, partial: bool = False):
    return truth(
        SHA_TARGET,
        partial=partial,
        payload={
            "base_sha": SHA_LOCAL,
            "head_sha": SHA_TARGET,
            "status": status,
            "ahead_by": ahead,
            "behind_by": behind,
            "files": [{"filename": "backend/x.py", "status": "modified", "patch": "@@"}],
        },
    )


def inspect(monkeypatch, startup, live, fake):
    monkeypatch.setattr(rt, "capture_runtime_snapshot", lambda **_: live)
    return rt.RuntimeTruthService(fake).inspect(
        repository=rt.CANONICAL_RUNTIME_REPOSITORY,
        target_ref="master",
        startup=startup,
    )


def test_exact_clean_stable_match_is_aligned(monkeypatch):
    fake = FakeRepositoryTruth([SHA_LOCAL, SHA_LOCAL])
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "aligned"
    assert fake.ref_calls == 2
    assert fake.compare_calls == 0


def test_dirty_match_is_unknown_and_short_circuits_compare(monkeypatch):
    fake = FakeRepositoryTruth([SHA_LOCAL])
    live = replace(snapshot(), dirty_state="dirty", provenance="live_worktree_observation")
    result = inspect(monkeypatch, snapshot(dirty="dirty"), live, fake)
    assert result["alignment"] == "unknown"
    assert result["reason"] == "dirty_local_state"
    assert fake.ref_calls == 1
    assert fake.compare_calls == 0


def test_startup_live_change_forces_unknown(monkeypatch):
    fake = FakeRepositoryTruth([SHA_TARGET])
    live = replace(snapshot(), git_sha=SHA_TARGET, provenance="live_worktree_observation")
    result = inspect(monkeypatch, snapshot(), live, fake)
    assert result["alignment"] == "unknown"
    assert result["worktree_changed_since_start"] is True
    assert fake.compare_calls == 0


def test_partial_projection_can_still_prove_local_behind(monkeypatch):
    fake = FakeRepositoryTruth([SHA_TARGET, SHA_TARGET], relation("ahead", 2, 0, partial=True))
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "local_behind"
    assert result["semantic_delta"]["partial"] is True


@pytest.mark.parametrize(
    ("status", "ahead", "behind"),
    [("behind", 0, 2), ("diverged", 2, 1)],
)
def test_valid_non_behind_relation_is_divergent(monkeypatch, status, ahead, behind):
    fake = FakeRepositoryTruth([SHA_TARGET, SHA_TARGET], relation(status, ahead, behind))
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "divergent"


@pytest.mark.parametrize(
    ("status", "ahead", "behind"),
    [("ahead", 1, 1), ("behind", 1, 0), ("identical", 0, 1), ("mystery", 0, 0)],
)
def test_malformed_or_contradictory_relation_is_unknown(monkeypatch, status, ahead, behind):
    fake = FakeRepositoryTruth([SHA_TARGET], relation(status, ahead, behind))
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "unknown"
    assert result["reason"] == "remote_relation_unavailable"


def test_local_only_sha_provider_failure_is_unknown(monkeypatch):
    fake = FakeRepositoryTruth(
        [SHA_TARGET],
        RepositoryTruthError("not_found", "local SHA absent remotely"),
    )
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "unknown"
    assert result["semantic_delta"]["status"] == "unavailable"


def test_target_move_invalidates_non_unknown_classification(monkeypatch):
    fake = FakeRepositoryTruth([SHA_LOCAL, SHA_TARGET])
    result = inspect(monkeypatch, snapshot(), replace(snapshot(), provenance="live_worktree_observation"), fake)
    assert result["alignment"] == "unknown"
    assert result["reason"] == "remote_target_moved"


def test_detached_head_is_classified_by_sha(monkeypatch):
    start = snapshot(head_state="detached", branch=None)
    live = replace(start, provenance="live_worktree_observation")
    fake = FakeRepositoryTruth([SHA_LOCAL, SHA_LOCAL])
    result = inspect(monkeypatch, start, live, fake)
    assert result["alignment"] == "aligned"
    assert result["live"]["branch"] is None


def test_repository_mismatch_never_calls_remote(monkeypatch):
    fake = FakeRepositoryTruth([])
    monkeypatch.setattr(rt, "capture_runtime_snapshot", lambda **_: replace(snapshot(), provenance="live_worktree_observation"))
    result = rt.RuntimeTruthService(fake).inspect(
        repository="example/other",
        target_ref="master",
        startup=snapshot(),
    )
    assert result["alignment"] == "unknown"
    assert result["reason"] == "repository_mismatch"
    assert fake.ref_calls == 0


def test_startup_snapshot_object_is_never_recomputed(monkeypatch):
    startup = snapshot()
    live = replace(snapshot(), provenance="live_worktree_observation")
    fake = FakeRepositoryTruth([SHA_LOCAL, SHA_LOCAL, SHA_LOCAL, SHA_LOCAL])
    monkeypatch.setattr(rt, "capture_runtime_snapshot", lambda **_: live)
    service = rt.RuntimeTruthService(fake)
    first = service.inspect(repository=rt.CANONICAL_RUNTIME_REPOSITORY, target_ref="master", startup=startup)
    live = replace(live, dirty_state="dirty")
    second = service.inspect(repository=rt.CANONICAL_RUNTIME_REPOSITORY, target_ref="master", startup=startup)
    assert startup.dirty_state == "clean"
    assert first["startup"] == second["startup"]


def test_probe_environment_is_minimal_and_disables_optional_locks(monkeypatch):
    monkeypatch.setenv("JARVISOS_FAKE_SECRET", "do-not-forward")
    env = rt._minimal_git_environment()
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert "JARVISOS_FAKE_SECRET" not in env


def test_snapshot_uses_shared_deadline(monkeypatch, tmp_path: Path):
    calls: list[float] = []
    outputs = [
        rt.ProbeResult(0, str(tmp_path).encode(), b""),
        rt.ProbeResult(0, SHA_LOCAL.encode(), b""),
        rt.ProbeResult(1, b"", b""),
        rt.ProbeResult(0, b"", b""),
    ]

    def fake_probe(root, args, timeout):
        calls.append(timeout)
        return outputs.pop(0)

    ticks = iter([10.0, 10.0, 10.4, 10.8, 11.2])
    monkeypatch.setattr(rt.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(rt, "_run_git_probe", fake_probe)
    result = rt.capture_runtime_snapshot(provenance="live_worktree_observation", root=tmp_path)
    assert result.failure_code is None
    assert calls == pytest.approx([2.0, 1.6, 1.2, 0.8])


def test_git_unavailable_is_typed(monkeypatch, tmp_path: Path):
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(rt, "_run_git_probe", missing)
    result = rt.capture_runtime_snapshot(provenance="live_worktree_observation", root=tmp_path)
    assert result.git_available is False
    assert result.failure_code == "git_unavailable"
    assert result.git_sha is None


def test_root_mismatch_stops_after_first_probe(monkeypatch, tmp_path: Path):
    calls = 0

    def fake_probe(root, args, timeout):
        nonlocal calls
        calls += 1
        return rt.ProbeResult(0, str(tmp_path / "other").encode(), b"")

    monkeypatch.setattr(rt, "_run_git_probe", fake_probe)
    result = rt.capture_runtime_snapshot(provenance="live_worktree_observation", root=tmp_path)
    assert result.failure_code == "root_mismatch"
    assert calls == 1


def test_malformed_sha_is_typed_without_raw_output(monkeypatch, tmp_path: Path):
    outputs = [
        rt.ProbeResult(0, str(tmp_path).encode(), b""),
        rt.ProbeResult(0, b"not-a-sha", b"secret stderr"),
    ]
    monkeypatch.setattr(rt, "_run_git_probe", lambda *args, **kwargs: outputs.pop(0))
    result = rt.capture_runtime_snapshot(provenance="live_worktree_observation", root=tmp_path)
    assert result.failure_code == "malformed_probe_output"
    assert "secret" not in repr(result)


def test_worktree_change_detects_ref_and_dirty_changes():
    startup = snapshot()
    assert rt.worktree_changed_since_start(startup, replace(startup, branch="feature"))
    assert rt.worktree_changed_since_start(startup, replace(startup, dirty_state="dirty"))


@pytest.mark.asyncio
async def test_blocking_snapshot_can_run_off_event_loop(monkeypatch):
    thread_seen = False

    def blocking_capture(**kwargs):
        nonlocal thread_seen
        import threading
        thread_seen = threading.current_thread() is not threading.main_thread()
        return snapshot()

    result = await asyncio.to_thread(blocking_capture, provenance="process_start_observation")
    assert result.git_sha == SHA_LOCAL
    assert thread_seen
