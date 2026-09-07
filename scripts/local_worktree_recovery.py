#!/usr/bin/env python3
"""Maintainer-only interrupted-writer recovery for spec 141.

This module is deliberately not registered in LocalWorktreeActuator.dispatch or
local_worktree_ipc. It clears only one exact persisted writer lease after the
maintainer has established that its request/session is gone, and only after a
fresh read-only worktree reinspection. It never cleans, resets, checks out,
commits, pushes, or executes worktree content.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.local_worktree_actuator import (
        ActuatorCode,
        ActuatorRefusal,
        LocalWorktreeActuator,
        WorkerState,
    )
except ImportError:  # direct script import
    from local_worktree_actuator import (  # type: ignore[no-redef]
        ActuatorCode,
        ActuatorRefusal,
        LocalWorktreeActuator,
        WorkerState,
    )


@dataclass(frozen=True)
class RecoveryInspection:
    lease_digest: str
    head_sha: str
    status_digest: str
    durable_commit: str


class InterruptedWriterRecovery:
    """Bounded maintainer recovery; intentionally absent from model IPC."""

    def __init__(self, actuator: LocalWorktreeActuator) -> None:
        self.actuator = actuator

    @staticmethod
    def _parse_lease(raw: bytes) -> tuple[str, str]:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease is malformed") from exc
        if not isinstance(payload, dict) or set(payload) != {"request_id", "session_id"}:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease shape is invalid")
        request_id = payload.get("request_id")
        session_id = payload.get("session_id")
        if not isinstance(request_id, str) or not request_id or not isinstance(session_id, str) or not session_id:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease owner is invalid")
        return request_id, session_id

    def inspect(
        self,
        repository_id: str,
        worktree_id: str,
    ) -> RecoveryInspection:
        """Return a CAS token plus fresh read-only Git state for maintainer review."""

        lock = self.actuator._lock_path(worktree_id)
        try:
            raw = lock.read_bytes()
        except OSError as exc:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease is unavailable") from exc
        self._parse_lease(raw)
        repo, tree = self.actuator._lookup(repository_id, worktree_id)
        delivery = self.actuator._delivery(repo, tree)
        head_sha = delivery._git(["rev-parse", "HEAD"]).stdout.strip().lower()
        status = delivery._git(["status", "--porcelain=v1", "--untracked-files=all"]).stdout
        return RecoveryInspection(
            lease_digest=hashlib.sha256(raw).hexdigest(),
            head_sha=head_sha,
            status_digest=hashlib.sha256(status.encode("utf-8")).hexdigest(),
            durable_commit=tree.durable_commit,
        )

    def recover(
        self,
        repository_id: str,
        worktree_id: str,
        *,
        expected_request_id: str,
        expected_session_id: str,
        expected_lease_digest: str,
    ) -> RecoveryInspection:
        """Clear exactly one interrupted lease after exact-owner/CAS reinspection.

        The caller is the maintainer control plane, not a model request. The
        expected digest is the lease generation: if anything changed since the
        maintainer inspected it, recovery fails closed.
        """

        lock = self.actuator._lock_path(worktree_id)
        guard = lock.with_name(lock.name + ".recovery")
        try:
            guard_fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer recovery already active") from exc
        os.close(guard_fd)
        try:
            inspection = self.inspect(repository_id, worktree_id)
            try:
                raw = lock.read_bytes()
            except OSError as exc:
                raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease disappeared") from exc
            request_id, session_id = self._parse_lease(raw)
            actual_digest = hashlib.sha256(raw).hexdigest()
            if (
                request_id != expected_request_id
                or session_id != expected_session_id
                or actual_digest != expected_lease_digest
                or inspection.lease_digest != expected_lease_digest
            ):
                raise ActuatorRefusal(
                    ActuatorCode.WORKTREE_BUSY,
                    "writer recovery owner/generation mismatch",
                )
            try:
                lock.unlink()
            except OSError as exc:
                raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lease recovery failed") from exc
            owner_digest = hashlib.sha256(
                f"{expected_request_id}\0{expected_session_id}".encode("utf-8")
            ).hexdigest()
            self.actuator.state.audit(
                {
                    "schema": 1,
                    "operation": "recover_interrupted_writer",
                    "result": ActuatorCode.OK.value,
                    "worker_id": self.actuator.state.worker_id,
                    "repository_id": repository_id,
                    "worktree_id": worktree_id,
                    "old_owner_digest": owner_digest,
                    "lease_digest": expected_lease_digest,
                    "head_sha": inspection.head_sha,
                    "status_digest": inspection.status_digest,
                    "durable_commit": inspection.durable_commit,
                }
            )
            return inspection
        finally:
            guard.unlink(missing_ok=True)


def recover_interrupted_writer(
    state_root: Path,
    repository_id: str,
    worktree_id: str,
    *,
    expected_request_id: str,
    expected_session_id: str,
    expected_lease_digest: str,
) -> RecoveryInspection:
    """Small maintainer API used by host activation/recovery tooling only."""

    state = WorkerState(state_root)
    actuator = LocalWorktreeActuator(state)
    return InterruptedWriterRecovery(actuator).recover(
        repository_id,
        worktree_id,
        expected_request_id=expected_request_id,
        expected_session_id=expected_session_id,
        expected_lease_digest=expected_lease_digest,
    )
