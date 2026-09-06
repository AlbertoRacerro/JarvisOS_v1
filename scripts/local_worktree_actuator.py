#!/usr/bin/env python3
"""Spec-141 local worktree actuator core.

This module is deliberately a local development-plane primitive, not a JarvisOS
product service.  It persists worker/worktree identity, enforces capability and
filesystem boundaries, and delegates network Git mutation to repository_delivery.
Transport activation is host-local and cannot make cloud lanes depend on a host.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

try:  # package-style imports in tests
    from scripts.repository_delivery import (
        DeliveryCode,
        DeliveryRefusal,
        GitRunner,
        RemotePolicy,
        RepositoryDelivery,
        assert_safe_paths,
    )
except ImportError:  # direct `python scripts/local_worktree_actuator.py`
    from repository_delivery import (  # type: ignore[no-redef]
        DeliveryCode,
        DeliveryRefusal,
        GitRunner,
        RemotePolicy,
        RepositoryDelivery,
        assert_safe_paths,
    )

STATE_SCHEMA = 1
AUDIT_MAX_BYTES = 10 * 1024 * 1024
AUDIT_ROTATIONS = 5
SHA_RE_LENGTH = 40


class Capability(StrEnum):
    OBSERVER = "observer"
    REVIEWER = "reviewer"
    IMPLEMENTER = "implementer"


class ActuatorCode(StrEnum):
    OK = "OK"
    WORKER_OFFLINE = "WORKER_OFFLINE"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    LOCAL_CREDENTIAL_UNAVAILABLE = "LOCAL_CREDENTIAL_UNAVAILABLE"
    REVIEWER_READ_ONLY = "REVIEWER_READ_ONLY"
    WORKTREE_BUSY = "WORKTREE_BUSY"
    WORKTREE_IDENTITY_MISMATCH = "WORKTREE_IDENTITY_MISMATCH"
    PATH_ESCAPE = "PATH_ESCAPE"
    GIT_ADMIN_PATH_REFUSED = "GIT_ADMIN_PATH_REFUSED"
    SENSITIVE_PATH_REFUSED = "SENSITIVE_PATH_REFUSED"
    PROTECTED_BRANCH = "PROTECTED_BRANCH"
    LOCAL_TEST_PROFILE_REQUIRES_ISOLATION = "LOCAL_TEST_PROFILE_REQUIRES_ISOLATION"
    UNKNOWN_PROFILE = "UNKNOWN_PROFILE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ActuatorRefusal(RuntimeError):
    def __init__(self, code: ActuatorCode | DeliveryCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RepositoryRegistration:
    repository_id: str
    root: str
    remote_host: str
    owner: str
    repo: str
    common_git_dir: str
    default_branch: str = "master"


@dataclass(frozen=True)
class WorktreeRegistration:
    worktree_id: str
    repository_id: str
    path: str
    branch: str
    worker_id: str
    durable_commit: str = ""


@dataclass(frozen=True)
class WorkerHealth:
    worker_id: str
    status: str
    capabilities: tuple[str, ...]
    repositories: tuple[str, ...]
    worktrees: tuple[str, ...]


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    principal_id: str
    session_id: str
    capability: Capability


@dataclass(frozen=True)
class NamedProfile:
    name: str
    worker_owned: bool
    executes_worktree_content: bool


class WorkerState:
    """Small OS-user-private durable state with atomic registry replacement."""

    def __init__(self, root: Path, *, worker_id: str | None = None) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.json"
        self.worker_path = self.root / "worker.json"
        self.audit_path = self.root / "audit.jsonl"
        self.locks_dir = self.root / "locks"
        self.hooks_dir = self.root / "trusted-hooks"
        self.locks_dir.mkdir(exist_ok=True)
        self.hooks_dir.mkdir(exist_ok=True)
        self._ensure_private_root()
        if self.worker_path.exists():
            payload = self._read_json(self.worker_path)
            if payload.get("schema") != STATE_SCHEMA or not isinstance(payload.get("worker_id"), str):
                raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "worker identity state is corrupt")
            self.worker_id = str(payload["worker_id"])
        else:
            self.worker_id = worker_id or str(uuid.uuid4())
            self._atomic_json(self.worker_path, {"schema": STATE_SCHEMA, "worker_id": self.worker_id})
        if not self.registry_path.exists():
            self._atomic_json(self.registry_path, {"schema": STATE_SCHEMA, "repositories": {}, "worktrees": {}})

    def _ensure_private_root(self) -> None:
        if self.root.is_symlink():
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "worker state root may not be a symlink")
        if os.name != "nt":
            try:
                self.root.chmod(0o700)
            except OSError as exc:
                raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "cannot secure worker state root") from exc
            if self.root.stat().st_mode & 0o077:
                raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "worker state root is not private")

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, f"invalid state file: {path.name}") from exc
        if not isinstance(payload, dict):
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, f"invalid state object: {path.name}")
        return payload

    def registry(self) -> dict[str, Any]:
        payload = self._read_json(self.registry_path)
        if payload.get("schema") != STATE_SCHEMA:
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "unsupported registry schema")
        if not isinstance(payload.get("repositories"), dict) or not isinstance(payload.get("worktrees"), dict):
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "registry shape is invalid")
        return payload

    def _atomic_json(self, path: Path, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.root, text=True)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def replace_registry(self, payload: dict[str, Any]) -> None:
        payload = dict(payload)
        payload["schema"] = STATE_SCHEMA
        self._atomic_json(self.registry_path, payload)

    def _rotate_audit(self) -> None:
        if not self.audit_path.exists() or self.audit_path.stat().st_size < AUDIT_MAX_BYTES:
            return
        oldest = self.root / f"audit.jsonl.{AUDIT_ROTATIONS}"
        oldest.unlink(missing_ok=True)
        for number in range(AUDIT_ROTATIONS - 1, 0, -1):
            src = self.root / f"audit.jsonl.{number}"
            dst = self.root / f"audit.jsonl.{number + 1}"
            if src.exists():
                os.replace(src, dst)
        os.replace(self.audit_path, self.root / "audit.jsonl.1")

    def audit(self, record: dict[str, Any]) -> None:
        self._rotate_audit()
        forbidden = {"token", "secret", "authorization", "credential", "environment", "prompt", "content"}
        if any(key.lower() in forbidden for key in record):
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "audit record contains forbidden field")
        previous_digest = ""
        if self.audit_path.exists() and self.audit_path.stat().st_size:
            try:
                last = self.audit_path.read_text(encoding="utf-8").splitlines()[-1]
                previous = json.loads(last)
                previous_digest = str(previous.get("record_digest", ""))
            except (OSError, json.JSONDecodeError, IndexError):
                raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "audit chain is unreadable")
        body = dict(record)
        body["previous_digest"] = previous_digest
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        body["record_digest"] = hashlib.sha256(canonical).hexdigest()
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


class LocalWorktreeActuator:
    def __init__(self, state: WorkerState, *, online: bool = True) -> None:
        self.state = state
        self.online = online
        self.profiles: dict[str, NamedProfile] = {
            "worker-registry-integrity": NamedProfile(
                "worker-registry-integrity", worker_owned=True, executes_worktree_content=False
            )
        }

    def _require_online(self) -> None:
        if not self.online:
            raise ActuatorRefusal(ActuatorCode.WORKER_OFFLINE, "this local worker is offline")

    @staticmethod
    def _require_role(ctx: RequestContext, *, write: bool = False) -> None:
        if write and ctx.capability != Capability.IMPLEMENTER:
            raise ActuatorRefusal(ActuatorCode.REVIEWER_READ_ONLY, "write capability requires implementer")
        if not write and ctx.capability not in {Capability.OBSERVER, Capability.REVIEWER, Capability.IMPLEMENTER}:
            raise ActuatorRefusal(ActuatorCode.CAPABILITY_UNAVAILABLE, "capability unavailable")

    def _audit(self, ctx: RequestContext, operation: str, result: str, **fields: Any) -> None:
        record = {
            "schema": STATE_SCHEMA,
            "timestamp": int(time.time()),
            "request_id": ctx.request_id,
            "principal_id": ctx.principal_id,
            "session_id": ctx.session_id,
            "worker_id": self.state.worker_id,
            "capability": ctx.capability.value,
            "operation": operation,
            "result": result,
            **fields,
        }
        self.state.audit(record)

    def health(self, ctx: RequestContext) -> WorkerHealth:
        self._require_role(ctx)
        registry = self.state.registry()
        status = "online" if self.online else "offline"
        return WorkerHealth(
            self.state.worker_id,
            status,
            tuple(cap.value for cap in Capability),
            tuple(sorted(registry["repositories"])),
            tuple(sorted(registry["worktrees"])),
        )

    def enroll_repository(self, registration: RepositoryRegistration) -> None:
        """Maintainer activation API; deliberately not request-context addressable."""
        root = Path(registration.root).resolve()
        common = Path(registration.common_git_dir).resolve()
        if root.is_symlink() or not root.exists() or not common.exists():
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "repository identity cannot be proven")
        payload = self.state.registry()
        repositories = dict(payload["repositories"])
        repositories[registration.repository_id] = asdict(registration)
        payload["repositories"] = repositories
        self.state.replace_registry(payload)

    def attach_worktree(self, registration: WorktreeRegistration) -> None:
        """Maintainer/implementation activation; a caller cannot steal another worker's tree."""
        if registration.worker_id != self.state.worker_id:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "worktree belongs to another worker")
        payload = self.state.registry()
        if registration.repository_id not in payload["repositories"]:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "repository is not registered")
        path = Path(registration.path).resolve()
        if not path.exists() or path.is_symlink():
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "worktree path is not durable")
        worktrees = dict(payload["worktrees"])
        existing = worktrees.get(registration.worktree_id)
        if existing and existing.get("worker_id") != self.state.worker_id:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "dirty worktree migration refused")
        worktrees[registration.worktree_id] = asdict(registration)
        payload["worktrees"] = worktrees
        self.state.replace_registry(payload)

    def _lookup(self, repository_id: str, worktree_id: str) -> tuple[RepositoryRegistration, WorktreeRegistration]:
        payload = self.state.registry()
        raw_repo = payload["repositories"].get(repository_id)
        raw_tree = payload["worktrees"].get(worktree_id)
        if not isinstance(raw_repo, dict) or not isinstance(raw_tree, dict):
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "repository/worktree is not registered")
        repo = RepositoryRegistration(**raw_repo)
        tree = WorktreeRegistration(**raw_tree)
        if tree.repository_id != repository_id or tree.worker_id != self.state.worker_id:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "worktree binding mismatch")
        return repo, tree

    def _delivery(self, repo: RepositoryRegistration, tree: WorktreeRegistration) -> RepositoryDelivery:
        worktree = Path(tree.path).resolve()
        runner = GitRunner(trusted_hooks_dir=self.state.hooks_dir)
        delivery = RepositoryDelivery(
            worktree,
            default_branch=repo.default_branch,
            remote_policy=RemotePolicy(repo.remote_host, repo.owner, repo.repo),
            runner=runner,
        )
        common = delivery.common_git_dir()
        if common != Path(repo.common_git_dir).resolve():
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "Git common-dir identity changed")
        branch = delivery._git(["symbolic-ref", "--short", "HEAD"], check=False)
        if branch.returncode != 0 or branch.stdout.strip() != tree.branch:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_IDENTITY_MISMATCH, "branch binding changed")
        return delivery

    def _git_admin_roots(self, delivery: RepositoryDelivery, tree: WorktreeRegistration) -> tuple[Path, ...]:
        worktree = Path(tree.path).resolve()
        common = delivery.common_git_dir()
        git_dir_text = delivery._git(["rev-parse", "--path-format=absolute", "--git-dir"]).stdout.strip()
        git_dir = Path(git_dir_text).resolve()
        return (worktree / ".git", git_dir, common)

    @staticmethod
    def _is_within(candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False

    def validate_write_target(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        relative_path: str,
    ) -> Path:
        self._require_online()
        self._require_role(ctx, write=True)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        root = Path(tree.path).resolve()
        if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "absolute/traversal target refused")
        lexical = root / relative_path
        # Resolve the deepest existing ancestor to catch symlink/junction indirection
        # without requiring the final file to exist.
        ancestor = lexical
        suffix: list[str] = []
        while not ancestor.exists() and ancestor != root:
            suffix.append(ancestor.name)
            ancestor = ancestor.parent
        resolved = ancestor.resolve()
        for part in reversed(suffix):
            resolved = resolved / part
        if not self._is_within(resolved, root):
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "resolved target leaves assigned worktree")
        for admin in self._git_admin_roots(delivery, tree):
            admin_resolved = admin.resolve() if admin.exists() else admin
            if resolved == admin_resolved or self._is_within(resolved, admin_resolved):
                raise ActuatorRefusal(ActuatorCode.GIT_ADMIN_PATH_REFUSED, "Git administrative target refused")
        try:
            assert_safe_paths([relative_path])
        except DeliveryRefusal as exc:
            raise ActuatorRefusal(exc.code, str(exc)) from exc
        return resolved

    def run_named_profile(
        self,
        ctx: RequestContext,
        profile_name: str,
        *,
        repository_id: str,
        worktree_id: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx)
        self._lookup(repository_id, worktree_id)
        profile = self.profiles.get(profile_name)
        if profile is None:
            raise ActuatorRefusal(ActuatorCode.UNKNOWN_PROFILE, "unknown server-owned profile")
        if not profile.worker_owned or profile.executes_worktree_content:
            raise ActuatorRefusal(
                ActuatorCode.LOCAL_TEST_PROFILE_REQUIRES_ISOLATION,
                "mutable worktree execution requires separately authorized isolation",
            )
        # MVP worker-owned validation is intentionally in-process and reads only
        # the worker-private registry. No child process or repository import occurs.
        self.state.registry()
        self._audit(ctx, "named_profile", ActuatorCode.OK.value, profile=profile_name)
        return ActuatorCode.OK.value

    def git_status(self, ctx: RequestContext, repository_id: str, worktree_id: str) -> str:
        self._require_online()
        self._require_role(ctx)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        completed = delivery._git(["status", "--porcelain=v1", "--untracked-files=all"])
        return completed.stdout

    def git_diff(self, ctx: RequestContext, repository_id: str, worktree_id: str) -> str:
        self._require_online()
        self._require_role(ctx)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        completed = delivery._git(["diff", "--no-ext-diff", "--no-textconv", "--"])
        return completed.stdout

    def _lock_path(self, worktree_id: str) -> Path:
        safe = hashlib.sha256(worktree_id.encode()).hexdigest()
        return self.state.locks_dir / f"{safe}.lock"

    def acquire_writer(self, ctx: RequestContext, worktree_id: str) -> None:
        self._require_online()
        self._require_role(ctx, write=True)
        lock = self._lock_path(worktree_id)
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "worktree writer already active") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"request_id": ctx.request_id, "session_id": ctx.session_id}) + "\n")

    def release_writer(self, worktree_id: str) -> None:
        self._lock_path(worktree_id).unlink(missing_ok=True)

    def _require_writer(self, worktree_id: str) -> None:
        if not self._lock_path(worktree_id).exists():
            raise ActuatorRefusal(ActuatorCode.WORKTREE_BUSY, "writer lock required")

    def stage_paths(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        paths: list[str],
    ) -> None:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(worktree_id)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        normalized = assert_safe_paths(paths)
        for path in normalized:
            self.validate_write_target(ctx, repository_id, worktree_id, path)
        delivery.assert_raw_history()
        delivery._git(["add", "--", *normalized])
        staged = delivery._git(["diff", "--cached", "--name-only", "--no-renames"]).stdout.splitlines()
        assert_safe_paths(staged)
        self._audit(ctx, "stage_paths", ActuatorCode.OK.value, repository_id=repository_id, worktree_id=worktree_id, path_count=len(normalized))

    def commit(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        message: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(worktree_id)
        if not message or len(message) > 500 or any(ord(ch) < 32 and ch not in "\t" for ch in message):
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "commit message is invalid")
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        delivery.assert_branch_allowed(tree.branch)
        delivery.assert_safe_config()
        delivery.assert_raw_history()
        staged = delivery._git(["diff", "--cached", "--name-only", "--no-renames"]).stdout.splitlines()
        if not staged:
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "staged diff is empty")
        assert_safe_paths(staged)
        delivery._git(["commit", "-m", message, "--no-verify"])
        sha = delivery._git(["rev-parse", "HEAD"]).stdout.strip().lower()
        payload = self.state.registry()
        raw = dict(payload["worktrees"][worktree_id])
        raw["durable_commit"] = sha
        payload["worktrees"][worktree_id] = raw
        self.state.replace_registry(payload)
        self._audit(ctx, "commit", ActuatorCode.OK.value, repository_id=repository_id, worktree_id=worktree_id, sha_after=sha, path_count=len(staged))
        return sha

    def push_branch(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        *,
        intended_local_commit: str,
        expected_remote_head: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(worktree_id)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        try:
            result = delivery.guarded_push(
                branch=tree.branch,
                intended_local_commit=intended_local_commit,
                expected_remote_head=expected_remote_head,
            )
        except DeliveryRefusal as exc:
            self._audit(ctx, "push_branch", exc.code.value, repository_id=repository_id, worktree_id=worktree_id, expected_remote_sha=expected_remote_head)
            raise ActuatorRefusal(exc.code, str(exc)) from exc
        self._audit(ctx, "push_branch", result.code.value, repository_id=repository_id, worktree_id=worktree_id, expected_remote_sha=expected_remote_head, sha_after=result.remote_head, path_count=len(result.changed_paths))
        return result.remote_head


def zero_worker_cloud_capabilities() -> dict[str, bool]:
    """Explicit availability projection used by orchestration/tests.

    This function has no dependency on worker state by design: worker absence may
    disable local capabilities only, never GitHub/API, Actions, cloud review, or
    separately authorized browser proof.
    """

    return {
        "github_api": True,
        "github_actions": True,
        "cloud_semantic_review": True,
        "exact_head_browser_proof": True,
        "local_worktree": False,
    }


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
