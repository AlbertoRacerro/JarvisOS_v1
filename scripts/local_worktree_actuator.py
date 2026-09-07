#!/usr/bin/env python3
"""Spec-141 local worktree actuator with host-shared worktree ownership guards.

The implementation core is stored under the immutable `.github/` control path.
This compatibility module preserves the public actuator API while binding a
physical persistent worktree to one worker and serializing authority-bearing
operations with a stable cross-process guard shared by every worker on the host.
The durable lease remains interruption metadata; the OS guard is the live
serialization primitive and is never unlinked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

_CORE_PATH = Path(__file__).resolve().parents[1] / ".github" / "local_worktree_actuator_core.py"
_SPEC = importlib.util.spec_from_file_location("_jarvis_local_worktree_actuator_core", _CORE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("local worktree actuator core cannot be loaded")
_core = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _core
_SPEC.loader.exec_module(_core)

STATE_SCHEMA = _core.STATE_SCHEMA
AUDIT_MAX_BYTES = _core.AUDIT_MAX_BYTES
AUDIT_ROTATIONS = _core.AUDIT_ROTATIONS
MAX_WRITE_BYTES = _core.MAX_WRITE_BYTES
ActuatorCode = _core.ActuatorCode
ActuatorRefusal = _core.ActuatorRefusal
Capability = _core.Capability
NamedProfile = _core.NamedProfile
RepositoryRegistration = _core.RepositoryRegistration
RequestContext = _core.RequestContext
WorkerHealth = _core.WorkerHealth
WorkerState = _core.WorkerState
WorktreeRegistration = _core.WorktreeRegistration
zero_worker_cloud_capabilities = _core.zero_worker_cloud_capabilities

# The focused concurrency regression is part of the actuator control surface.
# `assert_safe_paths` is imported by the core from repository_delivery, so its
# global CONTROL_PATHS set is the single runtime policy owner used by the worker.
_control_paths = _core.assert_safe_paths.__globals__.get("CONTROL_PATHS")
if not isinstance(_control_paths, set):
    raise RuntimeError("repository delivery control-path policy is unavailable")
_control_paths.add("backend/tests/test_worktree_writer_guard.py")

_HOST_STATE_OVERRIDE = "JARVISOS_LOCAL_WORKTREE_HOST_STATE_ROOT"


class WriterGuardBusy(RuntimeError):
    """Raised when another process owns a worktree operation guard."""


def _secure_private_directory(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.exists() and candidate.is_symlink():
        raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "host state root may not be a symlink")
    candidate.mkdir(parents=True, exist_ok=True)
    resolved = candidate.resolve()
    if os.name != "nt":
        try:
            resolved.chmod(0o700)
        except OSError as exc:
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "cannot secure host worktree state root",
            ) from exc
        if resolved.stat().st_mode & 0o077:
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "host worktree state root is not private",
            )
    return resolved


def _host_state_root() -> Path:
    override = os.environ.get(_HOST_STATE_OVERRIDE, "").strip()
    if override:
        return _secure_private_directory(Path(override))
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
        if not local_app_data:
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "LOCALAPPDATA is required for host worktree ownership state",
            )
        return _secure_private_directory(
            Path(local_app_data) / "JarvisOS" / "local-worktree-actuator-host"
        )
    xdg_state = os.environ.get("XDG_STATE_HOME", "").strip()
    base = Path(xdg_state) if xdg_state else Path.home() / ".local" / "state"
    return _secure_private_directory(base / "jarvisos" / "local-worktree-actuator-host")


@contextmanager
def _exclusive_writer_guard(
    path: Path,
    *,
    busy_error: Callable[[], BaseException] | None = None,
) -> Iterator[None]:
    """Acquire a stable, non-blocking OS lock released automatically on crash."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    handle = os.fdopen(fd, "r+b", buffering=0)
    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(handle.fileno()).st_size == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            if busy_error is not None:
                raise busy_error() from exc
            raise WriterGuardBusy("worktree writer operation guard is busy") from exc
        yield
    finally:
        if locked:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        else:
            handle.close()


class LocalWorktreeActuator(_core.LocalWorktreeActuator):
    """Core actuator with host-shared physical-worktree ownership and serialization."""

    @staticmethod
    def _identity_path(path: Path) -> str:
        return os.path.normcase(str(path.resolve()))

    def _physical_binding(self, worktree_id: str) -> tuple[str, dict[str, str]] | None:
        payload = self.state.registry()
        raw_tree = payload["worktrees"].get(worktree_id)
        if not isinstance(raw_tree, dict):
            return None
        repository_id = raw_tree.get("repository_id")
        raw_repo = payload["repositories"].get(repository_id)
        if not isinstance(repository_id, str) or not isinstance(raw_repo, dict):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "registered physical worktree identity is incomplete",
            )
        repo = RepositoryRegistration(**raw_repo)
        tree = WorktreeRegistration(**raw_tree)
        if tree.worker_id != self.state.worker_id:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "worktree belongs to another worker",
            )
        delivery = self._delivery(repo, tree)
        common_git_dir = self._identity_path(delivery.common_git_dir())
        worktree_path = self._identity_path(Path(tree.path))
        material = json.dumps(
            {
                "common_git_dir": common_git_dir,
                "worktree_path": worktree_path,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        key = hashlib.sha256(material).hexdigest()
        return key, {
            "schema": str(STATE_SCHEMA),
            "worker_id": self.state.worker_id,
            "repository_id": repository_id,
            "worktree_id": worktree_id,
            "common_git_dir": common_git_dir,
            "worktree_path": worktree_path,
        }

    def _ownership_path(self, identity: str) -> Path:
        root = _host_state_root() / "ownership"
        root.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            root.chmod(0o700)
        return root / f"{identity}.json"

    @staticmethod
    def _read_ownership(path: Path) -> dict[str, Any]:
        if path.is_symlink():
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "physical worktree ownership record is not trustworthy",
            )
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "physical worktree ownership record is corrupt",
            ) from exc
        if not isinstance(existing, dict):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "physical worktree ownership record has invalid shape",
            )
        return existing

    def _claim_physical_worktree(self, worktree_id: str) -> None:
        """Maintainer activation helper; request paths only verify this durable claim."""

        binding = self._physical_binding(worktree_id)
        if binding is None:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "physical worktree is not registered",
            )
        identity, expected = binding
        path = self._ownership_path(identity)
        encoded = json.dumps(expected, sort_keys=True, separators=(",", ":")) + "\n"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if self._read_ownership(path) != expected:
                raise ActuatorRefusal(
                    ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                    "physical persistent worktree belongs to another worker",
                )
            return
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

    def _verify_physical_worktree(self, worktree_id: str) -> None:
        binding = self._physical_binding(worktree_id)
        if binding is None:
            return
        identity, expected = binding
        path = self._ownership_path(identity)
        if not path.exists() or self._read_ownership(path) != expected:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "physical persistent worktree ownership is not admitted for this worker",
            )

    def attach_worktree(self, registration: WorktreeRegistration) -> None:
        before = self.state.registry()["worktrees"].get(registration.worktree_id)
        super().attach_worktree(registration)
        try:
            self._claim_physical_worktree(registration.worktree_id)
        except BaseException:
            if before is None:
                payload = self.state.registry()
                current = payload["worktrees"].get(registration.worktree_id)
                if current == _core.asdict(registration):
                    payload["worktrees"].pop(registration.worktree_id, None)
                    self.state.replace_registry(payload)
            raise

    def _guard_path(self, worktree_id: str) -> Path:
        binding = self._physical_binding(worktree_id)
        if binding is None:
            safe = hashlib.sha256(
                f"{self.state.worker_id}\0{worktree_id}".encode()
            ).hexdigest()
        else:
            safe = binding[0]
        root = _host_state_root() / "guards"
        root.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            root.chmod(0o700)
        return root / f"{safe}.guard"

    def _writer_guard(self, worktree_id: str):
        self._verify_physical_worktree(worktree_id)
        return _exclusive_writer_guard(
            self._guard_path(worktree_id),
            busy_error=lambda: ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "worktree writer operation is busy",
            ),
        )

    def acquire_writer(self, ctx: RequestContext, worktree_id: str) -> None:
        with self._writer_guard(worktree_id):
            super().acquire_writer(ctx, worktree_id)

    def release_writer(self, ctx: RequestContext, worktree_id: str) -> None:
        with self._writer_guard(worktree_id):
            super().release_writer(ctx, worktree_id)

    def write_text(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        relative_path: str,
        text: str,
    ) -> str:
        with self._writer_guard(worktree_id):
            return super().write_text(
                ctx,
                repository_id,
                worktree_id,
                relative_path,
                text,
            )

    def stage_paths(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        paths: list[str],
    ) -> None:
        with self._writer_guard(worktree_id):
            super().stage_paths(ctx, repository_id, worktree_id, paths)

    def commit(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        message: str,
    ) -> str:
        with self._writer_guard(worktree_id):
            return super().commit(ctx, repository_id, worktree_id, message)

    def push_branch(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        *,
        intended_local_commit: str,
        expected_remote_head: str,
    ) -> str:
        with self._writer_guard(worktree_id):
            return super().push_branch(
                ctx,
                repository_id,
                worktree_id,
                intended_local_commit=intended_local_commit,
                expected_remote_head=expected_remote_head,
            )


def __getattr__(name: str):
    return getattr(_core, name)


__all__ = [
    "ActuatorCode",
    "ActuatorRefusal",
    "Capability",
    "LocalWorktreeActuator",
    "NamedProfile",
    "RepositoryRegistration",
    "RequestContext",
    "WorkerHealth",
    "WorkerState",
    "WorktreeRegistration",
    "zero_worker_cloud_capabilities",
]
