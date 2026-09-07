#!/usr/bin/env python3
"""Spec-141 local worktree actuator with operation-held writer serialization.

The implementation core is stored under the immutable `.github/` control path.
This compatibility module preserves the public actuator API while adding the
stable cross-process guard required to bind writer-owner validation to each
authority-bearing side effect. The durable lease remains interruption metadata;
the OS guard is the serialization primitive and is never unlinked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

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


class WriterGuardBusy(RuntimeError):
    """Raised when another process owns a worktree operation guard."""


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
    """Core actuator with per-worktree check-and-act serialization."""

    def _guard_path(self, worktree_id: str) -> Path:
        safe = hashlib.sha256(worktree_id.encode()).hexdigest()
        return self.state.locks_dir / f"{safe}.guard"

    def _writer_guard(self, worktree_id: str):
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
