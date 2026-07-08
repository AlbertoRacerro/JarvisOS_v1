#!/usr/bin/env python3
"""Bounded Codex PR autopush actuator for JarvisOS.

This is intentionally small bootstrap tooling: it can validate that a Codex fix
is safe to materialize on an existing PR branch, push the checked-out HEAD to
that branch, and report the final remote branch head plus changed files. It never
merges, force-pushes, deletes branches, or pushes to master.
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

GITHUB_API = "https://api.github.com"
DEFAULT_BRANCHES = {"master", "main"}
SECRET_NAME_RE = re.compile(r"(?i)(^|[._/-])(secret|secrets|token|tokens|credential|credentials|key|keys)([._/-]|$)")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.I)


@dataclass(frozen=True)
class AutopushDecision:
    allowed: bool
    reason: str = ""


def die(message: str) -> None:
    print(f"codex_pr_autopush: {message}", file=sys.stderr)
    sys.exit(1)


def run_git(args: list[str], *, cwd: Path, check: bool = True) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        die(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def gh_request(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, str]:
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
    return name == ".env" or name.startswith(".env.") or SECRET_NAME_RE.search(normalized) is not None


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
        return AutopushDecision(False, f"refusing to push to protected branch {branch!r}")
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


def remote_head(repo_root: Path, remote: str, branch: str) -> str:
    out = run_git(["ls-remote", remote, f"refs/heads/{branch}"], cwd=repo_root)
    if not out:
        return ""
    return out.split()[0]


def changed_files_between(repo_root: Path, before: str, after: str) -> list[str]:
    if not before or before == after:
        return []
    out = run_git(["diff", "--name-only", f"{before}..{after}"], cwd=repo_root)
    return [line for line in out.splitlines() if line]


def format_success_comment(final_sha: str, changed_files: list[str]) -> str:
    files = "\n".join(f"- `{path}`" for path in changed_files) or "- _(no file changes detected)_"
    return (
        "<!-- codex-autopush:success -->\n"
        "### Codex autopush materialized\n\n"
        f"Final remote branch head SHA: `{final_sha}`\n\n"
        "Changed files:\n"
        f"{files}\n\n"
        "CI and automated review remain the authority; human merge authority is unchanged."
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
    status, text = gh_request("POST", f"{GITHUB_API}/repos/{repo}/issues/{pr}/comments", token, {"body": body})
    if status != 201:
        die(f"could not post PR comment (status {status}): {text}")


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
    run_git(["push", remote, f"HEAD:refs/heads/{branch}"], cwd=repo_root)
    final = remote_head(repo_root, remote, branch)
    if not final:
        die("push completed but remote branch head could not be verified")
    return final, bool(before and final != before)


def _self_test_non_materialized_push() -> None:
    """A no-op push must not be classified as materialized work."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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


def _self_test_materialized_push_reports_final_sha() -> None:
    """A real push reports the advanced remote branch head."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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


def self_test() -> None:
    assert not validate_autopush_request(target_branch="master", changed_files=[]).allowed
    assert not validate_autopush_request(target_branch="feature", changed_files=[], force_push=True).allowed
    assert not validate_autopush_request(target_branch="feature", changed_files=[], delete_branch=True).allowed
    assert not validate_autopush_request(target_branch="feature", changed_files=[".github/workflows/ci.yml"]).allowed
    assert validate_autopush_request(target_branch="feature", changed_files=[".github/workflows/ci.yml"], allow_workflow_changes=True).allowed
    for path in [".env", ".env.local", "config/token.txt", "docs/api_key.md", "secrets/value.txt", "creds/credential.json"]:
        assert not validate_autopush_request(target_branch="feature", changed_files=[path]).allowed, path
    assert validate_autopush_request(
        target_branch="feature",
        changed_files=[
            "backend/app/x.py",
            "backend/tests/test_x.py",
            "docs/specs/022-codex-pr-autopush.md",
            "scripts/codex_pr_autopush.py",
        ],
    ).allowed
    success = format_success_comment("a" * 40, ["backend/app/x.py"])
    assert "Final remote branch head SHA" in success and "backend/app/x.py" in success
    non_materialized = format_non_materialized_comment("Codex committed deadbeef locally", "b" * 40)
    assert "deadbeef" in non_materialized and "not materialized" in non_materialized
    _self_test_non_materialized_push()
    _self_test_materialized_push_reports_final_sha()
    # The actuator has no merge/force/delete modes; the only mutating git operation
    # is a normal HEAD-to-refs/heads/<branch> push after policy validation.
    source = Path(__file__).read_text(encoding="utf-8")
    assert "git " + "merge" not in source
    assert ":refs/" + "heads/" not in source.replace("HEAD:refs/" + "heads/", "")
    print("codex_pr_autopush: self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded Codex PR autopush actuator")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo-root", default=os.environ.get("GITHUB_WORKSPACE", "."))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default=os.environ.get("PR_HEAD_BRANCH", ""))
    parser.add_argument("--changed-files", default="", help="newline-separated file list; defaults to git diff remote..HEAD")
    parser.add_argument("--allow-workflow-changes", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reported-text", default="")
    parser.add_argument("--comment", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--pr", type=int, default=int(os.environ.get("PR_NUMBER", "0") or "0"))
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
