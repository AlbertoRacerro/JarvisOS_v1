#!/usr/bin/env python3
"""Deterministic repository-delivery safety primitive.

Spec 141 owns the optional local-worker plane, but repository mutation safety is
shared with the existing 022/079 lanes.  This module deliberately exposes only
typed operations needed by those lanes; it is not a generic Git wrapper.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_CODE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java",
    ".c", ".cc", ".cpp", ".h", ".hpp",
}
SECRET_PART_RE = re.compile(
    r"(^|[._/-])(secret|secrets|token|tokens|credential|credentials|key|keys)([._/-]|$)",
    re.I,
)
CODEOWNERS_PATHS = {"CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"}
CONTROL_PATHS = {
    "AGENTS.md",
    "scripts/codex_pr_autopush.py",
    "scripts/daily_development_continuation.py",
    "scripts/repository_delivery.py",
    "scripts/local_worktree_actuator.py",
    "backend/tests/test_repository_delivery.py",
    "backend/tests/test_local_worktree_actuator.py",
}
UNSAFE_CONFIG_KEYS = {
    "core.hookspath",
    "core.sshcommand",
    "http.proxy",
    "https.proxy",
    "credential.helper",
    "credential.usehttppath",
}
UNSAFE_CONFIG_PREFIXES = ("url.", "filter.")


class DeliveryCode(StrEnum):
    OK = "OK"
    REMOTE_VERIFIED = "REMOTE_VERIFIED"
    SENSITIVE_PATH_REFUSED = "SENSITIVE_PATH_REFUSED"
    PROTECTED_BRANCH = "PROTECTED_BRANCH"
    GIT_CONFIG_UNSAFE = "GIT_CONFIG_UNSAFE"
    REMOTE_IDENTITY_MISMATCH = "REMOTE_IDENTITY_MISMATCH"
    REMOTE_BRANCH_ABSENT = "REMOTE_BRANCH_ABSENT"
    STALE_REMOTE_HEAD = "STALE_REMOTE_HEAD"
    NON_FAST_FORWARD_REFUSED = "NON_FAST_FORWARD_REFUSED"
    GIT_HISTORY_REPLACEMENT_REFUSED = "GIT_HISTORY_REPLACEMENT_REFUSED"
    PUSH_REJECTED = "PUSH_REJECTED"
    PUSH_RESULT_UNKNOWN = "PUSH_RESULT_UNKNOWN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DeliveryRefusal(RuntimeError):
    def __init__(self, code: DeliveryCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DeliveryResult:
    code: DeliveryCode
    remote_head: str = ""
    changed_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class RemotePolicy:
    host: str = "github.com"
    owner: str = ""
    repo: str = ""
    # Tests use temporary bare repositories. Production callers leave this false.
    allow_local_path_for_tests: bool = False


class GitRunner:
    """Run server-owned Git argv with a scrubbed environment and no shell."""

    _BLOCKED_ENV = {
        "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH", "GIT_SSH_COMMAND",
        "GIT_PROXY_COMMAND", "GIT_CONFIG", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM", "GIT_OPTIONAL_LOCKS", "HTTP_PROXY", "HTTPS_PROXY",
        "ALL_PROXY", "NO_PROXY",
    }

    def __init__(self, *, trusted_hooks_dir: Path | None = None) -> None:
        self.trusted_hooks_dir = trusted_hooks_dir

    def _env(self) -> dict[str, str]:
        env = {key: value for key, value in os.environ.items() if key not in self._BLOCKED_ENV}
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_NO_REPLACE_OBJECTS"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def run(
        self,
        args: list[str],
        *,
        cwd: Path,
        check: bool = True,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
        argv = ["git"]
        if self.trusted_hooks_dir is not None:
            argv.extend(["-c", f"core.hooksPath={self.trusted_hooks_dir}"])
        argv.extend(args)
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=self._env(),
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout,
        )
        if check and completed.returncode != 0:
            raise DeliveryRefusal(
                DeliveryCode.INTERNAL_ERROR,
                f"git operation failed with exit {completed.returncode}",
            )
        return completed


def normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").lstrip("/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def is_sensitive_path(path: str) -> bool:
    normalized = normalize_repo_path(path)
    lower = normalized.lower()
    if lower.startswith(".github/"):
        return True
    if normalized in CODEOWNERS_PATHS or normalized in CONTROL_PATHS:
        return True
    name = Path(normalized).name
    if name == ".env" or name.startswith(".env."):
        return True
    candidate = Path(name)
    if candidate.suffix.lower() in SOURCE_CODE_SUFFIXES:
        return False
    return SECRET_PART_RE.search(normalized) is not None


def assert_safe_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(sorted({normalize_repo_path(path) for path in paths if path.strip()}))
    denied = [path for path in normalized if is_sensitive_path(path)]
    if denied:
        raise DeliveryRefusal(
            DeliveryCode.SENSITIVE_PATH_REFUSED,
            f"sensitive repository path refused: {denied[0]}",
        )
    return normalized


def assert_sha(value: str, label: str) -> str:
    value = value.strip().lower()
    if not SHA_RE.fullmatch(value):
        raise DeliveryRefusal(DeliveryCode.INTERNAL_ERROR, f"{label} must be a full SHA")
    return value


class RepositoryDelivery:
    """Fail-closed exact-head branch delivery over one verified repository."""

    def __init__(
        self,
        repo_root: Path,
        *,
        remote: str = "origin",
        default_branch: str = "master",
        protected_branches: set[str] | None = None,
        remote_policy: RemotePolicy | None = None,
        runner: GitRunner | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.remote = remote
        self.default_branch = default_branch
        self.protected_branches = {default_branch, "master", "main", *(protected_branches or set())}
        self.remote_policy = remote_policy or RemotePolicy()
        self.runner = runner or GitRunner()

    def _git(self, args: list[str], *, check: bool = True, timeout: int = 60) -> subprocess.CompletedProcess[str]:
        return self.runner.run(args, cwd=self.repo_root, check=check, timeout=timeout)

    def assert_branch_allowed(self, branch: str) -> str:
        branch = branch.strip()
        if not branch or branch in self.protected_branches or branch.startswith("-"):
            raise DeliveryRefusal(DeliveryCode.PROTECTED_BRANCH, "default/protected branch refused")
        if branch.startswith("refs/") or ".." in branch or branch.endswith("/"):
            raise DeliveryRefusal(DeliveryCode.PROTECTED_BRANCH, "invalid branch shape")
        checked = self._git(["check-ref-format", "--branch", branch], check=False)
        if checked.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.PROTECTED_BRANCH, "invalid branch")
        return branch

    def assert_safe_config(self) -> None:
        completed = self._git(["config", "--local", "--null", "--list"], check=False)
        if completed.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, "local Git config unreadable")
        for entry in completed.stdout.split("\0"):
            if not entry:
                continue
            key = entry.split("\n", 1)[0].split("=", 1)[0].strip().lower()
            if key in UNSAFE_CONFIG_KEYS or key.startswith(UNSAFE_CONFIG_PREFIXES):
                raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, f"unsafe Git config: {key}")
        pushurl = self._git(["config", "--get", f"remote.{self.remote}.pushurl"], check=False)
        if pushurl.returncode == 0 and pushurl.stdout.strip():
            raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, "remote pushurl override refused")

    def common_git_dir(self) -> Path:
        completed = self._git(["rev-parse", "--path-format=absolute", "--git-common-dir"])
        return Path(completed.stdout.strip()).resolve()

    def assert_raw_history(self) -> None:
        refs = self._git(["for-each-ref", "--format=%(refname)", "refs/replace/"], check=False)
        if refs.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED, "replace refs unreadable")
        if any(line.strip() for line in refs.stdout.splitlines()):
            raise DeliveryRefusal(DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED, "replace refs refused")
        grafts = self.common_git_dir() / "info" / "grafts"
        if grafts.exists():
            raise DeliveryRefusal(DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED, "legacy graft metadata refused")

    def remote_url(self) -> str:
        completed = self._git(["remote", "get-url", self.remote], check=False)
        if completed.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.REMOTE_IDENTITY_MISMATCH, "remote missing")
        return completed.stdout.strip()

    def assert_remote_identity(self) -> None:
        url = self.remote_url()
        policy = self.remote_policy
        if policy.allow_local_path_for_tests and (url.startswith("/") or url.startswith("file://")):
            return
        parsed = urlparse(url)
        expected_path = f"/{policy.owner}/{policy.repo}.git" if policy.owner and policy.repo else ""
        if parsed.scheme != "https" or parsed.hostname != policy.host:
            raise DeliveryRefusal(DeliveryCode.REMOTE_IDENTITY_MISMATCH, "only registered HTTPS GitHub remote is allowed")
        if expected_path and parsed.path.rstrip("/") not in {expected_path, expected_path.removesuffix(".git")}:
            raise DeliveryRefusal(DeliveryCode.REMOTE_IDENTITY_MISMATCH, "remote repository identity mismatch")

    def remote_head(self, branch: str) -> str:
        branch = self.assert_branch_allowed(branch)
        completed = self._git(["ls-remote", "--heads", self.remote, f"refs/heads/{branch}"], check=False)
        if completed.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.PUSH_RESULT_UNKNOWN, "remote head read failed")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            return ""
        if len(lines) != 1:
            raise DeliveryRefusal(DeliveryCode.REMOTE_IDENTITY_MISMATCH, "ambiguous remote branch")
        sha = lines[0].split()[0].lower()
        return assert_sha(sha, "remote head")

    def assert_descendant(self, expected: str, intended: str) -> None:
        expected = assert_sha(expected, "expected remote head")
        intended = assert_sha(intended, "intended local commit")
        result = self._git(["merge-base", "--is-ancestor", expected, intended], check=False)
        if result.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.NON_FAST_FORWARD_REFUSED, "intended commit is not a raw-graph descendant")

    def changed_paths(self, before: str, after: str) -> tuple[str, ...]:
        before = assert_sha(before, "before")
        after = assert_sha(after, "after")
        completed = self._git(["diff", "--name-only", "--no-renames", f"{before}..{after}"])
        return assert_safe_paths([line for line in completed.stdout.splitlines() if line.strip()])

    def guarded_push(
        self,
        *,
        branch: str,
        intended_local_commit: str,
        expected_remote_head: str,
    ) -> DeliveryResult:
        branch = self.assert_branch_allowed(branch)
        intended = assert_sha(intended_local_commit, "intended local commit")
        expected = assert_sha(expected_remote_head, "expected remote head")
        self.assert_safe_config()
        self.assert_remote_identity()
        self.assert_raw_history()
        local_head = self._git(["rev-parse", "HEAD"]).stdout.strip().lower()
        if local_head != intended:
            raise DeliveryRefusal(DeliveryCode.STALE_REMOTE_HEAD, "local HEAD moved")
        observed = self.remote_head(branch)
        if not observed:
            raise DeliveryRefusal(DeliveryCode.REMOTE_BRANCH_ABSENT, "remote branch creation is outside 141")
        if observed != expected:
            raise DeliveryRefusal(DeliveryCode.STALE_REMOTE_HEAD, "remote head differs from expected")
        self.assert_descendant(expected, intended)
        changed = self.changed_paths(expected, intended)
        target = f"refs/heads/{branch}"
        lease = f"--force-with-lease={target}:{expected}"
        push = self._git(["push", self.remote, lease, f"{intended}:{target}"], check=False, timeout=120)
        if push.returncode != 0:
            after = self.remote_head(branch)
            if after != expected:
                raise DeliveryRefusal(DeliveryCode.STALE_REMOTE_HEAD, "atomic expected-head lease rejected")
            raise DeliveryRefusal(DeliveryCode.PUSH_REJECTED, "guarded fast-forward push rejected")
        after = self.remote_head(branch)
        if after != intended:
            raise DeliveryRefusal(DeliveryCode.PUSH_RESULT_UNKNOWN, "push effect could not be verified")
        return DeliveryResult(DeliveryCode.REMOTE_VERIFIED, after, changed)


__all__ = [
    "DeliveryCode",
    "DeliveryRefusal",
    "DeliveryResult",
    "GitRunner",
    "RemotePolicy",
    "RepositoryDelivery",
    "assert_safe_paths",
    "is_sensitive_path",
]
