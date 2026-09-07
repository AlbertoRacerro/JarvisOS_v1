#!/usr/bin/env python3
"""Maintainer-only interrupted-writer recovery for spec 141.

This module lives under `.github/` so the actuator's existing sensitive-path
policy makes it immutable from the assigned-worktree write surface. It is
intentionally absent from LocalWorktreeActuator.dispatch and local_worktree_ipc.
It clears only one exact persisted writer lease after the maintainer has
established that its request/session is gone, and only after fresh read-only Git
reinspection. It never cleans, resets, checks out, commits, pushes, or executes
worktree content.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.local_worktree_actuator import (
        STATE_SCHEMA,
        ActuatorCode,
        ActuatorRefusal,
        LocalWorktreeActuator,
        WorkerState,
    )
except ImportError:  # direct script import from a repository checkout
    from local_worktree_actuator import (  # type: ignore[no-redef]
        STATE_SCHEMA,
        ActuatorCode,
        ActuatorRefusal,
        LocalWorktreeActuator,
        WorkerState,
    )


@dataclass(frozen=True)
class RecoveryInspection:
    lease_digest: str
    lease_generation: str
    head_sha: str
    status_digest: str
    durable_commit: str


@dataclass(frozen=True)
class _LeaseState:
    request_id: str
    session_id: str
    digest: str
    generation: str


class InterruptedWriterRecovery:
    """Bounded maintainer recovery; intentionally absent from model IPC."""

    def __init__(self, actuator: LocalWorktreeActuator) -> None:
        self.actuator = actuator

    @staticmethod
    def _parse_lease(raw: bytes) -> tuple[str, str]:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease is malformed",
            ) from exc
        if not isinstance(payload, dict) or set(payload) != {"request_id", "session_id"}:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease shape is invalid",
            )
        request_id = payload.get("request_id")
        session_id = payload.get("session_id")
        if (
            not isinstance(request_id, str)
            or not request_id
            or not isinstance(session_id, str)
            or not session_id
        ):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease owner is invalid",
            )
        return request_id, session_id

    @classmethod
    def _lease_state(cls, lock: Path) -> _LeaseState:
        try:
            raw = lock.read_bytes()
            stat = lock.stat()
        except OSError as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease is unavailable",
            ) from exc
        request_id, session_id = cls._parse_lease(raw)
        digest = hashlib.sha256(raw).hexdigest()
        generation_payload = json.dumps(
            {
                "dev": stat.st_dev,
                "ino": stat.st_ino,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "ctime_ns": stat.st_ctime_ns,
                "digest": digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return _LeaseState(
            request_id=request_id,
            session_id=session_id,
            digest=digest,
            generation=hashlib.sha256(generation_payload).hexdigest(),
        )

    def inspect(self, repository_id: str, worktree_id: str) -> RecoveryInspection:
        """Return lease CAS evidence plus fresh read-only Git state."""

        lock = self.actuator._lock_path(worktree_id)
        before = self._lease_state(lock)
        repo, tree = self.actuator._lookup(repository_id, worktree_id)
        delivery = self.actuator._delivery(repo, tree)
        head_sha = delivery._git(["rev-parse", "HEAD"]).stdout.strip().lower()
        status = delivery._git(
            ["status", "--porcelain=v1", "--untracked-files=all"]
        ).stdout
        after = self._lease_state(lock)
        if before.generation != after.generation:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease changed during recovery inspection",
            )
        return RecoveryInspection(
            lease_digest=after.digest,
            lease_generation=after.generation,
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
        expected_lease_generation: str,
    ) -> RecoveryInspection:
        """Clear one interrupted lease under the shared OS writer guard."""

        with self.actuator._writer_guard(worktree_id):
            return self._recover_locked(
                repository_id,
                worktree_id,
                expected_request_id=expected_request_id,
                expected_session_id=expected_session_id,
                expected_lease_generation=expected_lease_generation,
            )

    def _recover_locked(
        self,
        repository_id: str,
        worktree_id: str,
        *,
        expected_request_id: str,
        expected_session_id: str,
        expected_lease_generation: str,
    ) -> RecoveryInspection:
        """Recovery body; caller holds the per-worktree operation guard."""

        lock = self.actuator._lock_path(worktree_id)
        inspection = self.inspect(repository_id, worktree_id)
        current = self._lease_state(lock)
        if (
            current.request_id != expected_request_id
            or current.session_id != expected_session_id
            or current.generation != expected_lease_generation
            or inspection.lease_generation != expected_lease_generation
        ):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer recovery owner/generation mismatch",
            )

        owner_digest = hashlib.sha256(
            f"{expected_request_id}\0{expected_session_id}".encode("utf-8")
        ).hexdigest()
        audit_common = {
            "schema": STATE_SCHEMA,
            "timestamp": int(time.time()),
            "worker_id": self.actuator.state.worker_id,
            "repository_id": repository_id,
            "worktree_id": worktree_id,
            "old_owner_digest": owner_digest,
            "lease_digest": inspection.lease_digest,
            "lease_generation": inspection.lease_generation,
            "head_sha": inspection.head_sha,
            "status_digest": inspection.status_digest,
            "durable_commit": inspection.durable_commit,
        }
        self.actuator.state.audit(
            {
                **audit_common,
                "operation": "recover_interrupted_writer_intent",
                "result": "INTENT",
            }
        )

        final_state = self._lease_state(lock)
        if final_state.generation != expected_lease_generation:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease changed before recovery commit",
            )
        try:
            lock.unlink()
        except OSError as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease recovery failed",
            ) from exc

        self.actuator.state.audit(
            {
                **audit_common,
                "timestamp": int(time.time()),
                "operation": "recover_interrupted_writer_complete",
                "result": ActuatorCode.OK.value,
            }
        )
        return inspection


def recover_interrupted_writer(
    state_root: Path,
    repository_id: str,
    worktree_id: str,
    *,
    expected_request_id: str,
    expected_session_id: str,
    expected_lease_generation: str,
) -> RecoveryInspection:
    """Small maintainer API used by host activation/recovery tooling only."""

    state = WorkerState(state_root)
    actuator = LocalWorktreeActuator(state)
    return InterruptedWriterRecovery(actuator).recover(
        repository_id,
        worktree_id,
        expected_request_id=expected_request_id,
        expected_session_id=expected_session_id,
        expected_lease_generation=expected_lease_generation,
    )
