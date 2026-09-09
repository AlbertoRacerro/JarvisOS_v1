#!/usr/bin/env python3
"""Bounded Codex PR autopush actuator for JarvisOS.

022 retains lane-specific admission/comment semantics. Network Git mutation is
owned by spec-141's shared repository-delivery primitive so there is one CAS,
remote-identity, raw-history and post-push verification implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.repository_delivery import (
        DeliveryCode,
        DeliveryRefusal,
        GitRunner,
        RemotePolicy,
        RepositoryDelivery,
        github_actions_runner,
    )
except ImportError:
    from repository_delivery import (  # type: ignore[no-redef]
        DeliveryCode,
        DeliveryRefusal,
        GitRunner,
        RemotePolicy,
        RepositoryDelivery,
        github_actions_runner,
    )

GITHUB_API = "https://api.github.com"
DEFAULT_BRANCHES = {"master", "main"}
SECRET_NAME_RE = re.compile(
    r"(?i)(^|[._/-])(secret|secrets|token|tokens|credential|credentials|key|keys)([._/-]|$)"
)
SOURCE_CODE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java",
    ".c", ".cc", ".cpp", ".h", ".hpp",
}
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.I)


@dataclass(frozen=True)
class AutopushDecision:
    allowed: bool
    reason: str = ""


def die(message: str) -> None:
    print(f"codex_pr_autopush: {message}", file=sys.stderr)
    sys.exit(1)


def run_git(args: list[str], *, cwd: Path, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if check and completed.returncode != 0:
        # This bootstrap helper is also used for local deterministic self-tests;
        # never reflect command output in production-facing error strings.
        die(f"git operation failed with exit {completed.returncode}")
    return completed.stdout.strip()


def gh_request(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def is_env_or_secret_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    name = normalized.rsplit("/", 1)[-1]
    if name == ".env" or name.startswith(".env."):
        return True
    candidate = Path(name)
    stem = candidate.stem.lower()
    suffix = candidate.suffix.lower()
    sensitive_words = {
        "secret", "secrets", "token", "tokens", "credential", "credentials", "key", "keys"
    }
    if stem in sensitive_words:
        return True
    if suffix in SOURCE_CODE_SUFFIXES:
        return False
    return SECRET_NAME_RE.search(normalized) is not None


def validate_autopush_request(
    *,
    target_branch: str,
    changed_files: list[str],
    force_push: bool = False,
    delete_branch: bool = False,
    allow_workflow_changes: bool = False,
) -> AutopushDecision:
    branch = target_branch.strip()
    if not branch:
        return AutopushDecision(False, "target branch is required")
    if branch in DEFAULT_BRANCHES:
        return AutopushDecision(False, f"refusing protected branch {branch!r}")
    if force_push:
        return AutopushDecision(False, "refusing force-push mode")
    if delete_branch:
        return AutopushDecision(False, "refusing branch deletion")
    for path in changed_files:
        normalized = path.replace("\\", "/").lstrip("/")
        if normalized.startswith(".github/workflows/") and not allow_workflow_changes:
            return AutopushDecision(False, "refusing workflow file changes after bootstrap")
        if is_env_or_secret_path(normalized):
            return AutopushDecision(False, f"refusing env/secret/token/key file change: {path}")
    return AutopushDecision(True)


def _shared_delivery(repo_root: Path, remote: str) -> RepositoryDelivery:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    remote_url = run_git(["remote", "get-url", remote], cwd=repo_root, check=False)
    if remote_url.startswith("/") or remote_url.startswith("file://"):
        return RepositoryDelivery(
            repo_root,
            remote=remote,
            remote_policy=RemotePolicy(allow_local_path_for_tests=True),
            runner=GitRunner(),
        )
    if "/" not in repository or not token:
        raise DeliveryRefusal(
            DeliveryCode.LOCAL_CREDENTIAL_UNAVAILABLE,
            "workflow repository credential is unavailable",
        )
    owner, repo = repository.split("/", 1)
    return RepositoryDelivery(
        repo_root,
        remote=remote,
        remote_policy=RemotePolicy(host="github.com", owner=owner, repo=repo),
        runner=github_actions_runner(token),
    )


def remote_head(repo_root: Path, remote: str, branch: str) -> str:
    try:
        return _shared_delivery(repo_root, remote).remote_head(branch)
    except DeliveryRefusal as exc:
        die(f"shared delivery refused remote read: {exc.code.value}")
    raise AssertionError("unreachable")


def changed_files_between(repo_root: Path, before: str, after: str) -> list[str]:
    if not before or before == after:
        return []
    out = run_git(
        ["-c", "core.hooksPath=", "diff", "--name-only", "--no-renames", f"{before}..{after}"],
        cwd=repo_root,
    )
    return [line for line in out.splitlines() if line]


def format_success_comment(final_sha: str, changed_files: list[str]) -> str:
    files = "\n".join(f"- `{path}`" for path in changed_files) or "- _(no file changes detected)_"
    return (
        "<!-- codex-autopush:success -->\n"
        "### Codex autopush materialized\n\n"
        f"Final remote branch head SHA: `{final_sha}`\n\n"
        "Changed files:\n"
        f"{files}\n\n"
        "CI and automated review remain the authority; merge authority is unchanged."
    )


def format_non_materialized_comment(reported_text: str, final_sha: str) -> str:
    refs = sorted(set(SHA_RE.findall(reported_text)))
    ref_text = ", ".join(f"`{ref}`" for ref in refs) if refs else "_(no commit SHA found)_"
    return (
        "<!-- codex-autopush:non-materialized -->\n"
        "### Codex work was not materialized on the PR branch\n\n"
        f"Reported Codex commit/reference(s): {ref_text}\n\n"
        f"Current remote PR branch head SHA: `{final_sha or 'unknown'}`\n\n"
        "A task-local Codex commit or summary is not sufficient; the GitHub PR branch head must advance."
    )


def post_pr_comment(repo: str, pr: int, token: str, body: str) -> None:
    status, text = gh_request(
        "POST", f"{GITHUB_API}/repos/{repo}/issues/{pr}/comments", token, {"body": body}
    )
    if status != 201:
        die(f"could not post PR comment (status {status})")


def push_current_head(
    repo_root: Path,
    *,
    remote: str,
    branch: str,
    changed_files: list[str],
    allow_workflows: bool,
    before: str = "",
) -> tuple[str, bool]:
    decision = validate_autopush_request(
        target_branch=branch,
        changed_files=changed_files,
        force_push=False,
        delete_branch=False,
        allow_workflow_changes=allow_workflows,
    )
    if not decision.allowed:
        die(decision.reason)
    intended = run_git(["rev-parse", "HEAD"], cwd=repo_root)
    if not before:
        die("existing exact remote head is required; remote branch creation is outside 022/141")
    try:
        result = _shared_delivery(repo_root, remote).guarded_push(
            branch=branch,
            intended_local_commit=intended,
            expected_remote_head=before,
        )
    except DeliveryRefusal as exc:
        die(f"shared delivery refused push: {exc.code.value}")
    return result.remote_head, result.remote_head != before


def _self_test_pair() -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    remote = root / "remote.git"
    work = root / "work"
    run_git(["init", "--bare", str(remote)], cwd=root)
    run_git(["clone", str(remote), str(work)], cwd=root)
    run_git(["config", "user.email", "codex@example.invalid"], cwd=work)
    run_git(["config", "user.name", "Codex Self Test"], cwd=work)
    (work / "README.md").write_text("initial\n", encoding="utf-8")
    run_git(["add", "README.md"], cwd=work)
    run_git(["commit", "-m", "initial"], cwd=work)
    run_git(["checkout", "-b", "feature"], cwd=work)
    run_git(["push", "origin", "HEAD:refs/heads/feature"], cwd=work)
    return tmp, remote, work


def _self_test_non_materialized_push() -> None:
    tmp, _remote, work = _self_test_pair()
    try:
        before = remote_head(work, "origin", "feature")
        final, materialized = push_current_head(
            work,
            remote="origin",
            branch="feature",
            changed_files=["README.md"],
            allow_workflows=False,
            before=before,
        )
        assert final == before
        assert materialized is False
    finally:
        tmp.cleanup()


def _self_test_materialized_push_reports_final_sha() -> None:
    tmp, _remote, work = _self_test_pair()
    try:
        before = remote_head(work, "origin", "feature")
        (work / "README.md").write_text("initial\nnext\n", encoding="utf-8")
        run_git(["commit", "-am", "advance"], cwd=work)
        final, materialized = push_current_head(
            work,
            remote="origin",
            branch="feature",
            changed_files=["README.md"],
            allow_workflows=False,
            before=before,
        )
        assert final != before
        assert materialized is True
        assert final == run_git(["rev-parse", "HEAD"], cwd=work)
        assert final in format_success_comment(final, ["README.md"])
    finally:
        tmp.cleanup()


def _self_test_shared_push_owner() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    push_owner = source.split("def push_current_head(", 1)[1].split("\ndef _self_test_pair(", 1)[0]
    assert 'run_git(["push"' not in push_owner
    assert ".guarded_push(" in push_owner


def self_test() -> None:
    assert not validate_autopush_request(target_branch="master", changed_files=[]).allowed
    assert not validate_autopush_request(
        target_branch="feature", changed_files=[], force_push=True
    ).allowed
    assert not validate_autopush_request(
        target_branch="feature", changed_files=[], delete_branch=True
    ).allowed
    assert not validate_autopush_request(
        target_branch="feature", changed_files=[".github/workflows/ci.yml"]
    ).allowed
    assert validate_autopush_request(
        target_branch="feature",
        changed_files=[".github/workflows/ci.yml"],
        allow_workflow_changes=True,
    ).allowed
    for path in [
        ".env", ".env.local", "config/token.txt", "docs/api_key.md",
        "secrets/value.txt", "creds/credential.json",
    ]:
        assert not validate_autopush_request(
            target_branch="feature", changed_files=[path]
        ).allowed, path
    assert validate_autopush_request(
        target_branch="feature",
        changed_files=[
            "backend/app/x.py",
            "backend/app/modules/ai/token_counter.py",
            "backend/app/modules/ai/api_key_handler.py",
            "backend/app/modules/ai/credentials_validator.py",
            "backend/tests/test_x.py",
            "docs/specs/022-codex-pr-autopush.md",
            "scripts/codex_pr_autopush.py",
        ],
    ).allowed
    success = format_success_comment("a" * 40, ["backend/app/x.py"])
    assert "Final remote branch head SHA" in success and "backend/app/x.py" in success
    non_materialized = format_non_materialized_comment(
        "Codex committed deadbeef locally", "b" * 40
    )
    assert "deadbeef" in non_materialized and "not materialized" in non_materialized
    _self_test_non_materialized_push()
    _self_test_materialized_push_reports_final_sha()
    _self_test_shared_push_owner()
    print("codex_pr_autopush: self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded Codex PR autopush actuator")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo-root", default=os.environ.get("GITHUB_WORKSPACE", "."))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default=os.environ.get("PR_HEAD_BRANCH", ""))
    parser.add_argument(
        "--changed-files",
        default="",
        help="newline-separated file list; defaults to git diff remote..HEAD",
    )
    parser.add_argument("--allow-workflow-changes", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reported-text", default="")
    parser.add_argument("--comment", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument(
        "--pr", type=int, default=int(os.environ.get("PR_NUMBER", "0") or "0")
    )
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    repo_root = Path(args.repo_root)
    if not args.branch:
        die("--branch or PR_HEAD_BRANCH is required")
    before = remote_head(repo_root, args.remote, args.branch)
    changed = [line for line in args.changed_files.splitlines() if line.strip()]
    if not changed:
        changed = changed_files_between(repo_root, before, "HEAD")
    decision = validate_autopush_request(
        target_branch=args.branch,
        changed_files=changed,
        allow_workflow_changes=args.allow_workflow_changes,
    )
    if not decision.allowed:
        die(decision.reason)
    if args.verify_only:
        final = remote_head(repo_root, args.remote, args.branch)
        body = format_non_materialized_comment(args.reported_text, final)
    else:
        final, materialized = push_current_head(
            repo_root,
            remote=args.remote,
            branch=args.branch,
            changed_files=changed,
            allow_workflows=args.allow_workflow_changes,
            before=before,
        )
        if materialized:
            changed = changed_files_between(repo_root, before, final) or changed
            body = format_success_comment(final, changed)
        else:
            body = format_non_materialized_comment(args.reported_text, final)
    print(body)
    if args.comment:
        if not (args.repo and args.pr and args.token):
            die("--comment requires repo, pr, and token")
        post_pr_comment(args.repo, args.pr, args.token, body)
    if not args.verify_only and "materialized" in locals() and not materialized:
        die("push did not advance the remote PR branch head")


if __name__ == "__main__":
    main()
