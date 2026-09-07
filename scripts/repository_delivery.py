#!/usr/bin/env python3
"""Deterministic repository-delivery safety primitive.

Spec 141 owns the optional local-worker plane, but repository mutation safety is
shared with the existing 022/079 lanes. This module exposes only typed operations
needed by those lanes; it is not a generic Git wrapper.
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import shutil
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
    "scripts/local_worktree_ipc.py",
    "backend/tests/test_repository_delivery.py",
    "backend/tests/test_repository_delivery_config_escape.py",
    "backend/tests/test_local_worktree_actuator.py",
    "backend/tests/test_local_worktree_ipc.py",
}
UNSAFE_CONFIG_KEYS = {
    "core.editor",
    "core.fsmonitor",
    "core.hookspath",
    "core.sshcommand",
    "core.worktree",
    "gpg.program",
    "sequence.editor",
}
UNSAFE_CONFIG_PREFIXES = (
    "credential.",
    "diff.",
    "difftool.",
    "filter.",
    "http.",
    "https.",
    "include.",
    "includeif.",
    "merge.",
    "mergetool.",
    "url.",
)


class DeliveryCode(StrEnum):
    OK = "OK"
    REMOTE_VERIFIED = "REMOTE_VERIFIED"
    LOCAL_CREDENTIAL_UNAVAILABLE = "LOCAL_CREDENTIAL_UNAVAILABLE"
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
    # Deterministic tests use temporary bare repositories. Production callers
    # must never enable this.
    allow_local_path_for_tests: bool = False


@dataclass(frozen=True)
class WindowsGCMAdapter:
    """Server-owned, non-exporting Git Credential Manager selection."""

    helper_name: str
    executable: str

    @classmethod
    def discover(cls) -> WindowsGCMAdapter:
        if os.name != "nt":
            raise DeliveryRefusal(
                DeliveryCode.LOCAL_CREDENTIAL_UNAVAILABLE,
                "Windows GCM adapter is unavailable on this host",
            )
        candidates = (
            ("manager", "git-credential-manager.exe"),
            ("manager-core", "git-credential-manager-core.exe"),
        )
        for helper_name, executable_name in candidates:
            path = shutil.which(executable_name)
            if not path:
                continue
            resolved = Path(path).resolve()
            if not resolved.is_file():
                continue
            return cls(helper_name=helper_name, executable=str(resolved))
        raise DeliveryRefusal(
            DeliveryCode.LOCAL_CREDENTIAL_UNAVAILABLE,
            "approved Git Credential Manager executable was not found",
        )

    def config_value(self) -> str:
        """Return the exact validated executable as the only credential helper."""

        executable = Path(self.executable).resolve()
        if not executable.is_absolute() or not executable.is_file():
            raise DeliveryRefusal(
                DeliveryCode.LOCAL_CREDENTIAL_UNAVAILABLE,
                "validated Git Credential Manager executable is unavailable",
            )
        # Git credential helpers accept an absolute executable path. Quoting is
        # part of the config value so Windows paths containing spaces stay one
        # server-selected command; no request-controlled shell fragment is used.
        value = str(executable).replace("\\", "/").replace('"', '\\"')
        return f'"{value}"'


class GitRunner:
    """Run server-owned Git argv with scrubbed config/environment and no shell."""

    _BLOCKED_ENV = {
        "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH", "GIT_SSH_COMMAND",
        "GIT_PROXY_COMMAND", "GIT_CONFIG", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM", "GIT_OPTIONAL_LOCKS", "HTTP_PROXY", "HTTPS_PROXY",
        "ALL_PROXY", "NO_PROXY", "GITHUB_TOKEN", "GH_TOKEN",
        "GITLAB_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
    }

    def __init__(
        self,
        *,
        trusted_hooks_dir: Path | None = None,
        credential_adapter: WindowsGCMAdapter | None = None,
        server_owned_config: tuple[str, ...] = (),
    ) -> None:
        self.trusted_hooks_dir = trusted_hooks_dir
        self.credential_adapter = credential_adapter
        self.server_owned_config = server_owned_config

    def _env(self) -> dict[str, str]:
        env = {key: value for key, value in os.environ.items() if key not in self._BLOCKED_ENV}
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        env["GIT_CONFIG_SYSTEM"] = os.devnull
        env["GIT_NO_REPLACE_OBJECTS"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def _prefix(self) -> list[str]:
        argv = ["git"]
        if self.trusted_hooks_dir is not None:
            argv.extend(["-c", f"core.hooksPath={self.trusted_hooks_dir}"])
        # Clear any helper inherited through command-specific configuration, then
        # add only the exact server-selected GCM executable when local credentialed
        # Git is explicitly requested. Never re-resolve a helper name after
        # discovery validated a concrete executable.
        argv.extend(["-c", "credential.helper="])
        if self.credential_adapter is not None:
            argv.extend(["-c", f"credential.helper={self.credential_adapter.config_value()}"])
        for item in self.server_owned_config:
            argv.extend(["-c", item])
        return argv

    def run(
        self,
        args: list[str],
        *,
        cwd: Path,
        check: bool = True,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [*self._prefix(), *args],
            cwd=cwd,
            env=self._env(),
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout,
        )
        if check and completed.returncode != 0:
            # Do not reflect stderr/stdout because credential helpers and remote
            # transports are secret-bearing surfaces.
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

    def _git(
        self,
        args: list[str],
        *,
        check: bool = True,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
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

    @staticmethod
    def _config_key(entry: str) -> str:
        return entry.split("\n", 1)[0].split("=", 1)[0].strip().lower()

    def _assert_config_entries_safe(self, output: str) -> None:
        for entry in output.split("\0"):
            if not entry:
                continue
            key = self._config_key(entry)
            if key in UNSAFE_CONFIG_KEYS or key.startswith(UNSAFE_CONFIG_PREFIXES):
                raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, f"unsafe Git config: {key}")

    def assert_safe_config(self) -> None:
        local = self._git(["config", "--local", "--null", "--list"], check=False)
        if local.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, "local Git config unreadable")
        self._assert_config_entries_safe(local.stdout)

        worktree_enabled = self._git(
            ["config", "--local", "--bool", "--get", "extensions.worktreeConfig"],
            check=False,
        )
        if worktree_enabled.returncode == 0 and worktree_enabled.stdout.strip().lower() in {
            "true",
            "yes",
            "on",
            "1",
        }:
            worktree = self._git(["config", "--worktree", "--null", "--list"], check=False)
            if worktree.returncode != 0:
                raise DeliveryRefusal(
                    DeliveryCode.GIT_CONFIG_UNSAFE,
                    "worktree Git config unreadable",
                )
            self._assert_config_entries_safe(worktree.stdout)

        pushurl = self._git(["config", "--get", f"remote.{self.remote}.pushurl"], check=False)
        if pushurl.returncode == 0 and pushurl.stdout.strip():
            raise DeliveryRefusal(DeliveryCode.GIT_CONFIG_UNSAFE, "remote pushurl override refused")

    def common_git_dir(self) -> Path:
        completed = self._git(["rev-parse", "--path-format=absolute", "--git-common-dir"])
        return Path(completed.stdout.strip()).resolve()

    def assert_raw_history(self) -> None:
        refs = self._git(["for-each-ref", "--format=%(refname)", "refs/replace/"], check=False)
        if refs.returncode != 0:
            raise DeliveryRefusal(
                DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED,
                "replace refs unreadable",
            )
        if any(line.strip() for line in refs.stdout.splitlines()):
            raise DeliveryRefusal(
                DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED,
                "replace refs refused",
            )
        grafts = self.common_git_dir() / "info" / "grafts"
        if grafts.exists():
            raise DeliveryRefusal(
                DeliveryCode.GIT_HISTORY_REPLACEMENT_REFUSED,
                "legacy graft metadata refused",
            )

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
            raise DeliveryRefusal(
                DeliveryCode.REMOTE_IDENTITY_MISMATCH,
                "only registered HTTPS GitHub remote is allowed",
            )
        if expected_path and parsed.path.rstrip("/") not in {
            expected_path,
            expected_path.removesuffix(".git"),
        }:
            raise DeliveryRefusal(
                DeliveryCode.REMOTE_IDENTITY_MISMATCH,
                "remote repository identity mismatch",
            )

    def remote_head(self, branch: str) -> str:
        branch = self.assert_branch_allowed(branch)
        completed = self._git(
            ["ls-remote", "--heads", self.remote, f"refs/heads/{branch}"],
            check=False,
        )
        if completed.returncode != 0:
            raise DeliveryRefusal(DeliveryCode.PUSH_RESULT_UNKNOWN, "remote head read failed")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            return ""
        if len(lines) != 1:
            raise DeliveryRefusal(
                DeliveryCode.REMOTE_IDENTITY_MISMATCH,
                "ambiguous remote branch",
            )
        sha = lines[0].split()[0].lower()
        return assert_sha(sha, "remote head")

    def assert_descendant(self, expected: str, intended: str) -> None:
        expected = assert_sha(expected, "expected remote head")
        intended = assert_sha(intended, "intended local commit")
        result = self._git(["merge-base", "--is-ancestor", expected, intended], check=False)
        if result.returncode != 0:
            raise DeliveryRefusal(
                DeliveryCode.NON_FAST_FORWARD_REFUSED,
                "intended commit is not a raw-graph descendant",
            )

    def changed_paths(self, before: str, after: str) -> tuple[str, ...]:
        before = assert_sha(before, "before")
        after = assert_sha(after, "after")
        completed = self._git(
            ["diff", "--name-only", "--no-renames", f"{before}..{after}"]
        )
        return assert_safe_paths(
            [line for line in completed.stdout.splitlines() if line.strip()]
        )

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
            raise DeliveryRefusal(
                DeliveryCode.REMOTE_BRANCH_ABSENT,
                "remote branch creation is outside 141",
            )
        if observed != expected:
            raise DeliveryRefusal(
                DeliveryCode.STALE_REMOTE_HEAD,
                "remote head differs from expected",
            )
        self.assert_descendant(expected, intended)
        changed = self.changed_paths(expected, intended)
        target = f"refs/heads/{branch}"
        lease = f"--force-with-lease={target}:{expected}"
        push = self._git(
            ["push", self.remote, lease, f"{intended}:{target}"],
            check=False,
            timeout=120,
        )
        if push.returncode != 0:
            after = self.remote_head(branch)
            if after != expected:
                raise DeliveryRefusal(
                    DeliveryCode.STALE_REMOTE_HEAD,
                    "atomic expected-head lease rejected",
                )
            raise DeliveryRefusal(
                DeliveryCode.PUSH_REJECTED,
                "guarded fast-forward push rejected",
            )
        after = self.remote_head(branch)
        if after != intended:
            raise DeliveryRefusal(
                DeliveryCode.PUSH_RESULT_UNKNOWN,
                "push effect could not be verified",
            )
        return DeliveryResult(DeliveryCode.REMOTE_VERIFIED, after, changed)


def windows_gcm_runner(*, trusted_hooks_dir: Path | None = None) -> GitRunner:
    """Build the only accepted local credentialed Git runner for 141 MVP."""

    return GitRunner(
        trusted_hooks_dir=trusted_hooks_dir,
        credential_adapter=WindowsGCMAdapter.discover(),
    )


def github_actions_runner(token: str) -> GitRunner:
    """Existing workflow credential adapter for 022/079 compatibility only."""

    if not token:
        raise DeliveryRefusal(
            DeliveryCode.LOCAL_CREDENTIAL_UNAVAILABLE,
            "workflow credential is unavailable",
        )
    encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return GitRunner(
        server_owned_config=(
            f"http.https://github.com/.extraheader=AUTHORIZATION: basic {encoded}",
        )
    )


def _ci_guarded_push(args: argparse.Namespace) -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if "/" not in repository:
        raise DeliveryRefusal(
            DeliveryCode.REMOTE_IDENTITY_MISMATCH,
            "GITHUB_REPOSITORY is invalid",
        )
    owner, repo = repository.split("/", 1)
    delivery = RepositoryDelivery(
        Path(args.repo_root),
        remote=args.remote,
        remote_policy=RemotePolicy(host="github.com", owner=owner, repo=repo),
        runner=github_actions_runner(token),
    )
    result = delivery.guarded_push(
        branch=args.branch,
        intended_local_commit=args.intended,
        expected_remote_head=args.expected,
    )
    # Exact SHA and typed result are non-secret evidence.
    print(f"{result.code.value} {result.remote_head}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="JarvisOS bounded repository delivery")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ci = subparsers.add_parser(
        "ci-guarded-push",
        help="079/022 trusted workflow adapter; no local-worker credential semantics",
    )
    ci.add_argument("--repo-root", default=".")
    ci.add_argument("--remote", default="origin")
    ci.add_argument("--branch", required=True)
    ci.add_argument("--intended", required=True)
    ci.add_argument("--expected", required=True)
    args = parser.parse_args()
    if args.command == "ci-guarded-push":
        return _ci_guarded_push(args)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DeliveryCode",
    "DeliveryRefusal",
    "DeliveryResult",
    "GitRunner",
    "RemotePolicy",
    "RepositoryDelivery",
    "WindowsGCMAdapter",
    "assert_safe_paths",
    "github_actions_runner",
    "is_sensitive_path",
    "windows_gcm_runner",
]
