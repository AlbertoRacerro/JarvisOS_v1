#!/usr/bin/env python3
"""Spec-141 local worktree actuator core.

This module is a local development-plane primitive, not a JarvisOS product
service. It persists worker/worktree identity, enforces role/filesystem/Git
boundaries, and delegates every network Git mutation to repository_delivery.
Worker absence never disables cloud/GitHub lanes.
"""

from __future__ import annotations

import hashlib
import json
import os
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
        windows_gcm_runner,
    )
except ImportError:  # direct `python scripts/local_worktree_actuator.py`
    from repository_delivery import (  # type: ignore[no-redef]
        DeliveryCode,
        DeliveryRefusal,
        GitRunner,
        RemotePolicy,
        RepositoryDelivery,
        assert_safe_paths,
        windows_gcm_runner,
    )

STATE_SCHEMA = 1
AUDIT_MAX_BYTES = 10 * 1024 * 1024
AUDIT_ROTATIONS = 5
MAX_WRITE_BYTES = 2 * 1024 * 1024


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
    worktree_root: str = ""


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

    def __init__(
        self,
        root: Path,
        *,
        worker_id: str | None = None,
        commit_author_name: str | None = None,
        commit_author_email: str | None = None,
    ) -> None:
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
            self.commit_author_name = str(payload.get("commit_author_name", ""))
            self.commit_author_email = str(payload.get("commit_author_email", ""))
        else:
            self.worker_id = worker_id or str(uuid.uuid4())
            self.commit_author_name = (commit_author_name or "").strip()
            self.commit_author_email = (commit_author_email or "").strip()
            self._atomic_json(
                self.worker_path,
                {
                    "schema": STATE_SCHEMA,
                    "worker_id": self.worker_id,
                    "commit_author_name": self.commit_author_name,
                    "commit_author_email": self.commit_author_email,
                },
            )
        if not self.registry_path.exists():
            self._atomic_json(
                self.registry_path,
                {"schema": STATE_SCHEMA, "repositories": {}, "worktrees": {}},
            )

    def _ensure_private_root(self) -> None:
        if self.root.is_symlink():
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "worker state root may not be a symlink")
        if os.name != "nt":
            try:
                self.root.chmod(0o700)
            except OSError as exc:
                raise ActuatorRefusal(
                    ActuatorCode.INTERNAL_ERROR,
                    "cannot secure worker state root",
                ) from exc
            if self.root.stat().st_mode & 0o077:
                raise ActuatorRefusal(
                    ActuatorCode.INTERNAL_ERROR,
                    "worker state root is not private",
                )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                f"invalid state file: {path.name}",
            ) from exc
        if not isinstance(payload, dict):
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                f"invalid state object: {path.name}",
            )
        return payload

    def registry(self) -> dict[str, Any]:
        payload = self._read_json(self.registry_path)
        if payload.get("schema") != STATE_SCHEMA:
            raise ActuatorRefusal(ActuatorCode.INTERNAL_ERROR, "unsupported registry schema")
        if not isinstance(payload.get("repositories"), dict) or not isinstance(
            payload.get("worktrees"), dict
        ):
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
        (self.root / f"audit.jsonl.{AUDIT_ROTATIONS}").unlink(missing_ok=True)
        for number in range(AUDIT_ROTATIONS - 1, 0, -1):
            src = self.root / f"audit.jsonl.{number}"
            dst = self.root / f"audit.jsonl.{number + 1}"
            if src.exists():
                os.replace(src, dst)
        os.replace(self.audit_path, self.root / "audit.jsonl.1")

    def audit(self, record: dict[str, Any]) -> None:
        self._rotate_audit()
        forbidden = {
            "token",
            "secret",
            "authorization",
            "credential",
            "environment",
            "prompt",
            "content",
        }
        if any(key.lower() in forbidden for key in record):
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "audit record contains forbidden field",
            )
        previous_digest = ""
        if self.audit_path.exists() and self.audit_path.stat().st_size:
            try:
                last = self.audit_path.read_text(encoding="utf-8").splitlines()[-1]
                previous = json.loads(last)
                previous_digest = str(previous.get("record_digest", ""))
            except (OSError, json.JSONDecodeError, IndexError) as exc:
                raise ActuatorRefusal(
                    ActuatorCode.INTERNAL_ERROR,
                    "audit chain is unreadable",
                ) from exc
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
                "worker-registry-integrity",
                worker_owned=True,
                executes_worktree_content=False,
            )
        }

    def _require_online(self) -> None:
        if not self.online:
            raise ActuatorRefusal(
                ActuatorCode.WORKER_OFFLINE,
                "this local worker is offline",
            )

    @staticmethod
    def _require_role(ctx: RequestContext, *, write: bool = False) -> None:
        if write and ctx.capability != Capability.IMPLEMENTER:
            raise ActuatorRefusal(
                ActuatorCode.REVIEWER_READ_ONLY,
                "write capability requires implementer",
            )
        if not write and ctx.capability not in {
            Capability.OBSERVER,
            Capability.REVIEWER,
            Capability.IMPLEMENTER,
        }:
            raise ActuatorRefusal(
                ActuatorCode.CAPABILITY_UNAVAILABLE,
                "capability unavailable",
            )

    def _audit(
        self,
        ctx: RequestContext,
        operation: str,
        result: str,
        **fields: Any,
    ) -> None:
        self.state.audit(
            {
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
        )

    def dispatch(self, ctx: RequestContext, operation: str, **kwargs: Any) -> Any:
        """Single model/request boundary with uniform refusal auditing.

        The host-local IPC adapter may expose only this operation table. It cannot
        invent method names, argv, filesystem roots, credentials, or capabilities.
        """

        operations = {
            "health": self.health,
            "worktree_create": self.worktree_create,
            "worktree_inspect": self.worktree_inspect,
            "git_status": self.git_status,
            "git_diff": self.git_diff,
            "run_named_profile": self.run_named_profile,
            "acquire_writer": self.acquire_writer,
            "release_writer": self.release_writer,
            "write_text": self.write_text,
            "stage_paths": self.stage_paths,
            "commit": self.commit,
            "push_branch": self.push_branch,
        }
        target = operations.get(operation)
        if target is None:
            refusal = ActuatorRefusal(
                ActuatorCode.CAPABILITY_UNAVAILABLE,
                "operation is not exposed by the worker protocol",
            )
            self._audit(ctx, operation, refusal.code.value)
            raise refusal
        try:
            return target(ctx, **kwargs)
        except (ActuatorRefusal, DeliveryRefusal) as exc:
            code = exc.code.value if hasattr(exc.code, "value") else str(exc.code)
            self._audit(ctx, operation, code)
            raise

    def health(self, ctx: RequestContext) -> WorkerHealth:
        self._require_role(ctx)
        registry = self.state.registry()
        return WorkerHealth(
            self.state.worker_id,
            "online" if self.online else "offline",
            tuple(cap.value for cap in Capability),
            tuple(sorted(registry["repositories"])),
            tuple(sorted(registry["worktrees"])),
        )

    def enroll_repository(self, registration: RepositoryRegistration) -> None:
        """Maintainer activation API; not request-context addressable."""

        root = Path(registration.root).resolve()
        common = Path(registration.common_git_dir).resolve()
        worktree_root = Path(registration.worktree_root or registration.root).resolve()
        if (
            root.is_symlink()
            or not root.exists()
            or not common.exists()
            or worktree_root.is_symlink()
            or not worktree_root.exists()
        ):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "repository identity cannot be proven",
            )
        payload = self.state.registry()
        repositories = dict(payload["repositories"])
        normalized = asdict(registration)
        normalized["worktree_root"] = str(worktree_root)
        repositories[registration.repository_id] = normalized
        payload["repositories"] = repositories
        self.state.replace_registry(payload)

    def attach_worktree(self, registration: WorktreeRegistration) -> None:
        """Maintainer activation; another worker cannot steal persistent state."""

        if registration.worker_id != self.state.worker_id:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "worktree belongs to another worker",
            )
        payload = self.state.registry()
        raw_repo = payload["repositories"].get(registration.repository_id)
        if not isinstance(raw_repo, dict):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "repository is not registered",
            )
        path = Path(registration.path).resolve()
        allowed_root = Path(str(raw_repo["worktree_root"])).resolve()
        if (
            not path.exists()
            or path.is_symlink()
            or not self._is_within(path, allowed_root)
        ):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "worktree path is outside the registered actuator root",
            )
        worktrees = dict(payload["worktrees"])
        existing = worktrees.get(registration.worktree_id)
        if existing and existing.get("worker_id") != self.state.worker_id:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "dirty worktree migration refused",
            )
        worktrees[registration.worktree_id] = asdict(registration)
        payload["worktrees"] = worktrees
        self.state.replace_registry(payload)

    def worktree_create(
        self,
        ctx: RequestContext,
        repository_id: str,
        *,
        source_sha: str,
        branch: str,
        directory_name: str,
    ) -> WorktreeRegistration:
        """Create an exact-ref linked worktree under the enrolled actuator root."""

        self._require_online()
        self._require_role(ctx, write=True)
        payload = self.state.registry()
        raw_repo = payload["repositories"].get(repository_id)
        if not isinstance(raw_repo, dict):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "repository is not registered",
            )
        repo = RepositoryRegistration(**raw_repo)
        if Path(directory_name).name != directory_name or directory_name in {"", ".", ".."}:
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "worktree directory name is invalid")
        source_root = Path(repo.root).resolve()
        target_root = Path(repo.worktree_root or repo.root).resolve()
        target = (target_root / directory_name).resolve()
        if not self._is_within(target, target_root) or target.exists():
            raise ActuatorRefusal(
                ActuatorCode.PATH_ESCAPE,
                "worktree target must be a new child of the enrolled actuator root",
            )
        runner = GitRunner(trusted_hooks_dir=self.state.hooks_dir)
        delivery = RepositoryDelivery(
            source_root,
            default_branch=repo.default_branch,
            remote_policy=RemotePolicy(repo.remote_host, repo.owner, repo.repo),
            runner=runner,
        )
        delivery.assert_branch_allowed(branch)
        delivery.assert_safe_config()
        delivery.assert_raw_history()
        resolved = delivery._git(["rev-parse", "--verify", f"{source_sha}^{{commit}}"], check=False)
        if resolved.returncode != 0 or resolved.stdout.strip().lower() != source_sha.lower():
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "source ref does not resolve to the requested exact SHA",
            )
        existing = delivery._git(["show-ref", "--verify", f"refs/heads/{branch}"], check=False)
        if existing.returncode == 0:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "local branch already exists",
            )
        delivery._git(["worktree", "add", "-b", branch, str(target), source_sha])
        created = RepositoryDelivery(
            target,
            default_branch=repo.default_branch,
            remote_policy=RemotePolicy(repo.remote_host, repo.owner, repo.repo),
            runner=runner,
        )
        if created.common_git_dir() != Path(repo.common_git_dir).resolve():
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "created worktree has wrong common Git directory",
            )
        if created._git(["rev-parse", "HEAD"]).stdout.strip().lower() != source_sha.lower():
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "created worktree HEAD differs from exact source SHA",
            )
        registration = WorktreeRegistration(
            worktree_id=str(uuid.uuid4()),
            repository_id=repository_id,
            path=str(target),
            branch=branch,
            worker_id=self.state.worker_id,
            durable_commit=source_sha.lower(),
        )
        self.attach_worktree(registration)
        self._audit(
            ctx,
            "worktree_create",
            ActuatorCode.OK.value,
            repository_id=repository_id,
            worktree_id=registration.worktree_id,
            sha_after=source_sha.lower(),
        )
        return registration

    def _lookup(
        self,
        repository_id: str,
        worktree_id: str,
    ) -> tuple[RepositoryRegistration, WorktreeRegistration]:
        payload = self.state.registry()
        raw_repo = payload["repositories"].get(repository_id)
        raw_tree = payload["worktrees"].get(worktree_id)
        if not isinstance(raw_repo, dict) or not isinstance(raw_tree, dict):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "repository/worktree is not registered",
            )
        repo = RepositoryRegistration(**raw_repo)
        tree = WorktreeRegistration(**raw_tree)
        if tree.repository_id != repository_id or tree.worker_id != self.state.worker_id:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "worktree binding mismatch",
            )
        return repo, tree

    def _delivery(
        self,
        repo: RepositoryRegistration,
        tree: WorktreeRegistration,
        *,
        credentialed: bool = False,
    ) -> RepositoryDelivery:
        worktree = Path(tree.path).resolve()
        try:
            runner = (
                windows_gcm_runner(trusted_hooks_dir=self.state.hooks_dir)
                if credentialed
                else GitRunner(trusted_hooks_dir=self.state.hooks_dir)
            )
        except DeliveryRefusal as exc:
            raise ActuatorRefusal(exc.code, str(exc)) from exc
        delivery = RepositoryDelivery(
            worktree,
            default_branch=repo.default_branch,
            remote_policy=RemotePolicy(repo.remote_host, repo.owner, repo.repo),
            runner=runner,
        )
        common = delivery.common_git_dir()
        if common != Path(repo.common_git_dir).resolve():
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "Git common-dir identity changed",
            )
        branch = delivery._git(["symbolic-ref", "--short", "HEAD"], check=False)
        if branch.returncode != 0 or branch.stdout.strip() != tree.branch:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_IDENTITY_MISMATCH,
                "branch binding changed",
            )
        return delivery

    def worktree_inspect(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
    ) -> dict[str, str]:
        self._require_online()
        self._require_role(ctx)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        return {
            "worktree_id": tree.worktree_id,
            "repository_id": tree.repository_id,
            "branch": tree.branch,
            "head_sha": delivery._git(["rev-parse", "HEAD"]).stdout.strip().lower(),
            "durable_commit": tree.durable_commit,
        }

    def _git_admin_roots(
        self,
        delivery: RepositoryDelivery,
        tree: WorktreeRegistration,
    ) -> tuple[Path, ...]:
        worktree = Path(tree.path).resolve()
        common = delivery.common_git_dir()
        git_dir = Path(
            delivery._git(
                ["rev-parse", "--path-format=absolute", "--git-dir"]
            ).stdout.strip()
        ).resolve()
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
        requested = Path(relative_path)
        if requested.is_absolute() or ".." in requested.parts:
            raise ActuatorRefusal(
                ActuatorCode.PATH_ESCAPE,
                "absolute/traversal target refused",
            )
        lexical = root / requested
        ancestor = lexical
        suffix: list[str] = []
        while not ancestor.exists() and ancestor != root:
            suffix.append(ancestor.name)
            ancestor = ancestor.parent
        resolved = ancestor.resolve()
        for part in reversed(suffix):
            resolved = resolved / part
        if not self._is_within(resolved, root):
            raise ActuatorRefusal(
                ActuatorCode.PATH_ESCAPE,
                "resolved target leaves assigned worktree",
            )
        for admin in self._git_admin_roots(delivery, tree):
            admin_resolved = admin.resolve() if admin.exists() else admin
            if resolved == admin_resolved or self._is_within(resolved, admin_resolved):
                raise ActuatorRefusal(
                    ActuatorCode.GIT_ADMIN_PATH_REFUSED,
                    "Git administrative target refused",
                )
        try:
            assert_safe_paths([relative_path])
        except DeliveryRefusal as exc:
            raise ActuatorRefusal(exc.code, str(exc)) from exc
        return resolved

    def write_text(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        relative_path: str,
        text: str,
    ) -> str:
        """Bounded structured UTF-8 write inside the assigned worktree only."""

        self._require_writer(ctx, worktree_id)
        encoded = text.encode("utf-8")
        if len(encoded) > MAX_WRITE_BYTES or "\x00" in text:
            raise ActuatorRefusal(
                ActuatorCode.CAPABILITY_UNAVAILABLE,
                "write payload exceeds bounded UTF-8 file surface",
            )
        target = self.validate_write_target(
            ctx,
            repository_id,
            worktree_id,
            relative_path,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        # Revalidate the parent immediately before atomic replacement. This is a
        # model-path containment guard, not an OS sandbox against another local
        # administrator racing the maintainer process.
        parent = target.parent.resolve()
        root = Path(self._lookup(repository_id, worktree_id)[1].path).resolve()
        if not self._is_within(parent, root):
            raise ActuatorRefusal(ActuatorCode.PATH_ESCAPE, "write parent escaped")
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=parent)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        digest = hashlib.sha256(encoded).hexdigest()
        self._audit(
            ctx,
            "write_text",
            ActuatorCode.OK.value,
            repository_id=repository_id,
            worktree_id=worktree_id,
            path_digest=hashlib.sha256(relative_path.encode()).hexdigest(),
            result_digest=digest,
        )
        return digest

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
            raise ActuatorRefusal(
                ActuatorCode.UNKNOWN_PROFILE,
                "unknown server-owned profile",
            )
        if not profile.worker_owned or profile.executes_worktree_content:
            raise ActuatorRefusal(
                ActuatorCode.LOCAL_TEST_PROFILE_REQUIRES_ISOLATION,
                "mutable worktree execution requires separately authorized isolation",
            )
        # Worker-owned validation is intentionally in-process and reads only the
        # worker-private registry. No child process or repository import occurs.
        self.state.registry()
        self._audit(
            ctx,
            "named_profile",
            ActuatorCode.OK.value,
            profile=profile_name,
        )
        return ActuatorCode.OK.value

    def git_status(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx)
        repo, tree = self._lookup(repository_id, worktree_id)
        return self._delivery(repo, tree)._git(
            ["status", "--porcelain=v1", "--untracked-files=all"]
        ).stdout

    def git_diff(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx)
        repo, tree = self._lookup(repository_id, worktree_id)
        return self._delivery(repo, tree)._git(
            ["diff", "--no-ext-diff", "--no-textconv", "--"]
        ).stdout

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
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "worktree writer already active",
            ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "request_id": ctx.request_id,
                        "session_id": ctx.session_id,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        self._audit(
            ctx,
            "acquire_writer",
            ActuatorCode.OK.value,
            worktree_id=worktree_id,
        )

    def _require_writer(self, ctx: RequestContext, worktree_id: str) -> None:
        lock = self._lock_path(worktree_id)
        try:
            payload = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease missing or malformed",
            ) from exc
        if (
            not isinstance(payload, dict)
            or set(payload) != {"request_id", "session_id"}
            or payload.get("request_id") != ctx.request_id
            or payload.get("session_id") != ctx.session_id
        ):
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease belongs to another request/session",
            )

    def release_writer(self, ctx: RequestContext, worktree_id: str) -> None:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(ctx, worktree_id)
        lock = self._lock_path(worktree_id)
        try:
            lock.unlink()
        except OSError as exc:
            raise ActuatorRefusal(
                ActuatorCode.WORKTREE_BUSY,
                "writer lease could not be released",
            ) from exc
        self._audit(
            ctx,
            "release_writer",
            ActuatorCode.OK.value,
            worktree_id=worktree_id,
        )

    def stage_paths(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        paths: list[str],
    ) -> None:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(ctx, worktree_id)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        normalized = assert_safe_paths(paths)
        for path in normalized:
            self.validate_write_target(ctx, repository_id, worktree_id, path)
        delivery.assert_raw_history()
        delivery._git(["add", "--", *normalized])
        staged = delivery._git(
            ["diff", "--cached", "--name-only", "--no-renames"]
        ).stdout.splitlines()
        assert_safe_paths(staged)
        self._audit(
            ctx,
            "stage_paths",
            ActuatorCode.OK.value,
            repository_id=repository_id,
            worktree_id=worktree_id,
            path_count=len(normalized),
        )

    def commit(
        self,
        ctx: RequestContext,
        repository_id: str,
        worktree_id: str,
        message: str,
    ) -> str:
        self._require_online()
        self._require_role(ctx, write=True)
        self._require_writer(ctx, worktree_id)
        if not message or len(message) > 500 or any(
            ord(ch) < 32 and ch not in "\t" for ch in message
        ):
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "commit message is invalid",
            )
        if not self.state.commit_author_name or not self.state.commit_author_email:
            raise ActuatorRefusal(
                ActuatorCode.CAPABILITY_UNAVAILABLE,
                "maintainer-owned commit author is not activated",
            )
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree)
        delivery.assert_branch_allowed(tree.branch)
        delivery.assert_safe_config()
        delivery.assert_raw_history()
        staged = delivery._git(
            ["diff", "--cached", "--name-only", "--no-renames"]
        ).stdout.splitlines()
        if not staged:
            raise ActuatorRefusal(
                ActuatorCode.INTERNAL_ERROR,
                "staged diff is empty",
            )
        assert_safe_paths(staged)
        delivery._git(
            [
                "-c",
                f"user.name={self.state.commit_author_name}",
                "-c",
                f"user.email={self.state.commit_author_email}",
                "commit",
                "-m",
                message,
                "--no-verify",
            ]
        )
        sha = delivery._git(["rev-parse", "HEAD"]).stdout.strip().lower()
        payload = self.state.registry()
        raw = dict(payload["worktrees"][worktree_id])
        raw["durable_commit"] = sha
        payload["worktrees"][worktree_id] = raw
        self.state.replace_registry(payload)
        self._audit(
            ctx,
            "commit",
            ActuatorCode.OK.value,
            repository_id=repository_id,
            worktree_id=worktree_id,
            sha_after=sha,
            path_count=len(staged),
        )
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
        self._require_writer(ctx, worktree_id)
        repo, tree = self._lookup(repository_id, worktree_id)
        delivery = self._delivery(repo, tree, credentialed=True)
        try:
            result = delivery.guarded_push(
                branch=tree.branch,
                intended_local_commit=intended_local_commit,
                expected_remote_head=expected_remote_head,
            )
        except DeliveryRefusal as exc:
            raise ActuatorRefusal(exc.code, str(exc)) from exc
        self._audit(
            ctx,
            "push_branch",
            result.code.value,
            repository_id=repository_id,
            worktree_id=worktree_id,
            expected_remote_sha=expected_remote_head,
            sha_after=result.remote_head,
            path_count=len(result.changed_paths),
        )
        return result.remote_head


def zero_worker_cloud_capabilities() -> dict[str, bool]:
    """Availability projection with no dependency on any worker process/state."""

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
