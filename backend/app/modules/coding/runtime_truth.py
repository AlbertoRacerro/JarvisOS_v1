from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from app.modules.coding.repository_truth import RepositoryTruthError, RepositoryTruthResult

RUNTIME_REPOSITORY = "AlbertoRacerro/JarvisOS_v1"
SNAPSHOT_TIMEOUT_SECONDS = 2.0
MAX_PROBE_OUTPUT_BYTES = 65_536
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_BRANCH_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,255}$")

HeadState = Literal["branch", "detached", "unavailable"]
DirtyState = Literal["clean", "dirty", "unknown"]
Provenance = Literal["process_start_observation", "live_worktree_observation"]
AlignmentState = Literal["aligned", "local_behind", "divergent", "unknown"]
ObserverStatus = Literal["ok", "degraded", "unavailable"]

logger = logging.getLogger(__name__)


class RuntimeTruthError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ProbeResult:
    returncode: int
    stdout: bytes
    stderr: bytes


class ProbeRunner(Protocol):
    def __call__(self, argv: tuple[str, ...], cwd: Path, timeout: float) -> ProbeResult: ...


class RepositoryTruthReader(Protocol):
    def repository_ref_truth(self, repository: str, ref: str) -> RepositoryTruthResult: ...

    def compare_truth(
        self, repository: str, base_ref: str, head_ref: str
    ) -> RepositoryTruthResult: ...


@dataclass(frozen=True)
class RuntimeSnapshot:
    root_identity: str
    observed_at: str
    git_available: bool
    git_sha: str | None
    head_state: HeadState
    branch: str | None
    dirty_state: DirtyState
    provenance: Provenance
    failure_code: str | None = None


@dataclass(frozen=True)
class RuntimeTruthResult:
    repository: str
    target_ref: str
    startup: RuntimeSnapshot
    live: RuntimeSnapshot
    remote_sha: str | None
    remote_observed_at: str | None
    alignment: AlignmentState
    reason: str
    worktree_changed_since_start: bool
    observer_status: ObserverStatus
    remote_status: str
    remote_failure_code: str | None
    compare_partial: bool | None
    compare: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class _BoundedPipe:
    stream: object
    data: bytearray
    overflow: bool = False
    error: BaseException | None = None

    def drain(self) -> None:
        try:
            reader = self.stream
            while True:
                chunk = reader.read(8192)  # type: ignore[attr-defined]
                if not chunk:
                    return
                if len(self.data) <= MAX_PROBE_OUTPUT_BYTES:
                    remaining = MAX_PROBE_OUTPUT_BYTES + 1 - len(self.data)
                    self.data.extend(chunk[:remaining])
                if len(self.data) > MAX_PROBE_OUTPUT_BYTES:
                    self.overflow = True
        except BaseException as exc:  # pragma: no cover - defensive pipe failure
            self.error = exc


def _minimal_git_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if source is None else source
    allowed = ("PATH", "SystemRoot", "WINDIR", "PATHEXT", "COMSPEC")
    env = {key: source[key] for key in allowed if key in source}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _terminate_and_reap(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=0.25)


def _run_git_probe(argv: tuple[str, ...], cwd: Path, timeout: float) -> ProbeResult:
    if not argv or argv[0] != "git" or timeout <= 0:
        raise RuntimeTruthError("probe_failed", "invalid fixed Git probe")
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=str(cwd),
            env=_minimal_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeTruthError("git_unavailable", "Git executable is unavailable") from exc
    except OSError as exc:
        raise RuntimeTruthError("probe_failed", "Git probe could not start") from exc

    assert process.stdout is not None
    assert process.stderr is not None
    stdout = _BoundedPipe(process.stdout, bytearray())
    stderr = _BoundedPipe(process.stderr, bytearray())
    threads = [
        threading.Thread(target=stdout.drain, daemon=True),
        threading.Thread(target=stderr.drain, daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_and_reap(process)
        for thread in threads:
            thread.join(timeout=0.25)
        raise RuntimeTruthError("probe_timeout", "Git probe exceeded snapshot deadline") from exc
    finally:
        if process.poll() is None:  # pragma: no cover - defensive child cleanup
            _terminate_and_reap(process)

    for thread in threads:
        thread.join(timeout=0.25)
    if stdout.error is not None or stderr.error is not None:
        raise RuntimeTruthError("probe_failed", "Git probe pipe read failed")
    if stdout.overflow or stderr.overflow:
        raise RuntimeTruthError("probe_output_oversized", "Git probe output exceeded bound")
    return ProbeResult(process.returncode, bytes(stdout.data), bytes(stderr.data))


def _trusted_repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _root_identity(root: Path) -> str:
    normalized = os.path.normcase(str(root.resolve()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _decode_probe(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeTruthError("malformed_probe_output", "Git probe returned invalid UTF-8") from exc


def _remaining(deadline: float, clock: Callable[[], float]) -> float:
    remaining = deadline - clock()
    if remaining <= 0:
        raise RuntimeTruthError("probe_timeout", "Git snapshot deadline exhausted")
    return remaining


def _unavailable_snapshot(
    root: Path,
    provenance: Provenance,
    code: str,
    *,
    git_available: bool = False,
    git_sha: str | None = None,
    head_state: HeadState = "unavailable",
    branch: str | None = None,
) -> RuntimeSnapshot:
    return RuntimeSnapshot(
        root_identity=_root_identity(root),
        observed_at=datetime.now(UTC).isoformat(),
        git_available=git_available,
        git_sha=git_sha,
        head_state=head_state,
        branch=branch,
        dirty_state="unknown",
        provenance=provenance,
        failure_code=code,
    )


def capture_runtime_snapshot(
    provenance: Provenance,
    *,
    root: Path | None = None,
    probe: ProbeRunner = _run_git_probe,
    clock: Callable[[], float] = time.monotonic,
) -> RuntimeSnapshot:
    trusted_root = (root or _trusted_repository_root()).resolve()
    deadline = clock() + SNAPSHOT_TIMEOUT_SECONDS
    git_sha: str | None = None
    head_state: HeadState = "unavailable"
    branch: str | None = None
    try:
        top = probe(
            ("git", "rev-parse", "--show-toplevel"),
            trusted_root,
            _remaining(deadline, clock),
        )
        if top.returncode != 0:
            return _unavailable_snapshot(trusted_root, provenance, "not_git_worktree")
        top_path = Path(_decode_probe(top.stdout).strip()).resolve()
        if top_path != trusted_root:
            return _unavailable_snapshot(
                trusted_root, provenance, "root_mismatch", git_available=True
            )

        head = probe(
            ("git", "rev-parse", "--verify", "HEAD"),
            trusted_root,
            _remaining(deadline, clock),
        )
        if head.returncode != 0:
            return _unavailable_snapshot(
                trusted_root, provenance, "probe_failed", git_available=True
            )
        candidate_sha = _decode_probe(head.stdout).strip().lower()
        if not _SHA_RE.fullmatch(candidate_sha):
            return _unavailable_snapshot(
                trusted_root, provenance, "malformed_probe_output", git_available=True
            )
        git_sha = candidate_sha

        ref = probe(
            ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
            trusted_root,
            _remaining(deadline, clock),
        )
        if ref.returncode == 0:
            candidate_branch = _decode_probe(ref.stdout).strip()
            if not _BRANCH_RE.fullmatch(candidate_branch):
                return _unavailable_snapshot(
                    trusted_root,
                    provenance,
                    "malformed_probe_output",
                    git_available=True,
                    git_sha=git_sha,
                )
            head_state = "branch"
            branch = candidate_branch
        elif ref.returncode == 1:
            head_state = "detached"
        else:
            return _unavailable_snapshot(
                trusted_root,
                provenance,
                "probe_failed",
                git_available=True,
                git_sha=git_sha,
            )

        status = probe(
            ("git", "status", "--porcelain=v1", "--untracked-files=normal"),
            trusted_root,
            _remaining(deadline, clock),
        )
        if status.returncode != 0:
            return _unavailable_snapshot(
                trusted_root,
                provenance,
                "dirty_state_unavailable",
                git_available=True,
                git_sha=git_sha,
                head_state=head_state,
                branch=branch,
            )
        dirty_state: DirtyState = "dirty" if status.stdout else "clean"
        return RuntimeSnapshot(
            root_identity=_root_identity(trusted_root),
            observed_at=datetime.now(UTC).isoformat(),
            git_available=True,
            git_sha=git_sha,
            head_state=head_state,
            branch=branch,
            dirty_state=dirty_state,
            provenance=provenance,
            failure_code=None,
        )
    except RuntimeTruthError as exc:
        return _unavailable_snapshot(
            trusted_root,
            provenance,
            exc.code,
            git_available=exc.code != "git_unavailable",
            git_sha=git_sha,
            head_state=head_state,
            branch=branch,
        )


def startup_snapshot_unavailable() -> RuntimeSnapshot:
    return _unavailable_snapshot(
        _trusted_repository_root(), "process_start_observation", "startup_snapshot_unavailable"
    )


def _worktree_changed(startup: RuntimeSnapshot, live: RuntimeSnapshot) -> bool:
    return any(
        (
            startup.git_sha != live.git_sha,
            startup.dirty_state != live.dirty_state,
            startup.head_state != live.head_state,
            startup.branch != live.branch,
        )
    )


def _observer_status(startup: RuntimeSnapshot, live: RuntimeSnapshot) -> ObserverStatus:
    if not startup.git_available or not live.git_available:
        return "unavailable"
    if startup.failure_code or live.failure_code:
        return "degraded"
    return "ok"


def _remote_sha(result: RepositoryTruthResult) -> str:
    sha = result.resolved_sha
    if not isinstance(sha, str) or not _SHA_RE.fullmatch(sha):
        raise RepositoryTruthError("malformed_provider_response", "remote target SHA is invalid")
    return sha.lower()


def _unknown_result(
    repository: str,
    target_ref: str,
    startup: RuntimeSnapshot,
    live: RuntimeSnapshot,
    *,
    reason: str,
    remote_sha: str | None,
    remote_observed_at: str | None,
    remote_status: str,
    remote_failure_code: str | None = None,
    compare: RepositoryTruthResult | None = None,
) -> RuntimeTruthResult:
    return RuntimeTruthResult(
        repository=repository,
        target_ref=target_ref,
        startup=startup,
        live=live,
        remote_sha=remote_sha,
        remote_observed_at=remote_observed_at,
        alignment="unknown",
        reason=reason,
        worktree_changed_since_start=_worktree_changed(startup, live),
        observer_status=_observer_status(startup, live),
        remote_status=remote_status,
        remote_failure_code=remote_failure_code,
        compare_partial=compare.partial if compare is not None else None,
        compare=dict(compare.payload) if compare is not None else None,
    )


def _validate_relation(compare: RepositoryTruthResult) -> AlignmentState:
    payload = compare.payload
    status = payload.get("status")
    ahead = payload.get("ahead_by")
    behind = payload.get("behind_by")
    if (
        isinstance(ahead, bool)
        or isinstance(behind, bool)
        or not isinstance(ahead, int)
        or not isinstance(behind, int)
        or ahead < 0
        or behind < 0
        or not isinstance(status, str)
    ):
        return "unknown"
    if status == "ahead" and ahead > 0 and behind == 0:
        return "local_behind"
    if status == "behind" and ahead == 0 and behind > 0:
        return "divergent"
    if status == "diverged" and ahead > 0 and behind > 0:
        return "divergent"
    return "unknown"


def observe_runtime_truth(
    *,
    repository: str,
    target_ref: str,
    configured_repositories: Iterable[str],
    startup: RuntimeSnapshot,
    repository_truth: RepositoryTruthReader,
    live_snapshot_factory: Callable[[], RuntimeSnapshot] | None = None,
) -> RuntimeTruthResult:
    configured = frozenset(configured_repositories)
    if repository != RUNTIME_REPOSITORY or repository not in configured:
        live = startup
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="repository_mismatch",
            remote_sha=None,
            remote_observed_at=None,
            remote_status="unavailable",
            remote_failure_code="repository_mismatch",
        )

    try:
        initial_target = repository_truth.repository_ref_truth(repository, target_ref)
        target_sha = _remote_sha(initial_target)
    except RepositoryTruthError as exc:
        live = (live_snapshot_factory or (lambda: capture_runtime_snapshot("live_worktree_observation")))()
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="remote_target_unavailable",
            remote_sha=None,
            remote_observed_at=None,
            remote_status="unavailable",
            remote_failure_code=exc.code,
        )

    live = (live_snapshot_factory or (lambda: capture_runtime_snapshot("live_worktree_observation")))()
    changed = _worktree_changed(startup, live)
    if startup.failure_code or live.failure_code or not startup.git_sha or not live.git_sha:
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason=startup.failure_code or live.failure_code or "runtime_identity_unavailable",
            remote_sha=target_sha,
            remote_observed_at=initial_target.observed_at,
            remote_status="ok",
        )
    if changed:
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="worktree_changed_since_start",
            remote_sha=target_sha,
            remote_observed_at=initial_target.observed_at,
            remote_status="ok",
        )
    if startup.dirty_state != "clean" or live.dirty_state != "clean":
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="dirty_local_state",
            remote_sha=target_sha,
            remote_observed_at=initial_target.observed_at,
            remote_status="ok",
        )

    compare: RepositoryTruthResult | None = None
    candidate: AlignmentState
    reason: str
    if live.git_sha == target_sha:
        candidate = "aligned"
        reason = "exact_clean_match"
    else:
        try:
            compare = repository_truth.compare_truth(repository, live.git_sha, target_sha)
        except RepositoryTruthError as exc:
            return _unknown_result(
                repository,
                target_ref,
                startup,
                live,
                reason="remote_relation_unavailable",
                remote_sha=target_sha,
                remote_observed_at=initial_target.observed_at,
                remote_status="degraded",
                remote_failure_code=exc.code,
            )
        if compare.payload.get("base_sha") != live.git_sha or compare.payload.get("head_sha") != target_sha:
            candidate = "unknown"
        else:
            candidate = _validate_relation(compare)
        if candidate == "unknown":
            return _unknown_result(
                repository,
                target_ref,
                startup,
                live,
                reason="remote_relation_unavailable",
                remote_sha=target_sha,
                remote_observed_at=initial_target.observed_at,
                remote_status="degraded",
                compare=compare,
            )
        reason = "remote_relation_proven"

    try:
        final_target = repository_truth.repository_ref_truth(repository, target_ref)
        final_sha = _remote_sha(final_target)
    except RepositoryTruthError as exc:
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="remote_target_unavailable",
            remote_sha=target_sha,
            remote_observed_at=initial_target.observed_at,
            remote_status="unavailable",
            remote_failure_code=exc.code,
            compare=compare,
        )
    if final_sha != target_sha:
        return _unknown_result(
            repository,
            target_ref,
            startup,
            live,
            reason="remote_target_moved",
            remote_sha=final_sha,
            remote_observed_at=final_target.observed_at,
            remote_status="degraded",
            remote_failure_code="remote_target_moved",
            compare=compare,
        )

    logger.info(
        "coding_runtime_truth repository_digest=%s root_identity=%s alignment=%s dirty=%s compare_partial=%s",
        hashlib.sha256(repository.encode("utf-8")).hexdigest(),
        live.root_identity,
        candidate,
        live.dirty_state,
        compare.partial if compare is not None else None,
    )
    return RuntimeTruthResult(
        repository=repository,
        target_ref=target_ref,
        startup=startup,
        live=live,
        remote_sha=target_sha,
        remote_observed_at=final_target.observed_at,
        alignment=candidate,
        reason=reason,
        worktree_changed_since_start=False,
        observer_status="ok",
        remote_status="ok",
        remote_failure_code=None,
        compare_partial=compare.partial if compare is not None else None,
        compare=dict(compare.payload) if compare is not None else None,
    )
