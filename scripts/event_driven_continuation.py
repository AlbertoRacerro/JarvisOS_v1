#!/usr/bin/env python3
"""Fail-closed event bridge for V3.2 E1 continuation wake-ups.

This module owns no roadmap, implementation, review, or merge authority. It only
validates a terminal workflow_run against the current PR exact head, collapses an
already-recorded identical wake, and dispatches the existing spec-079
continuation workflow. The downstream continuation control plane reconstructs
its own authority from fresh GitHub state.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

API_ROOT = "https://api.github.com"
TARGET_WORKFLOW = "daily-development-continuation.yml"
SUPPORTED_WORKFLOWS = {"CI", "Manual Expert Review"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MARKER_RE = re.compile(
    r"<!-- jarvis-e1-wake:v1 workflow=(?P<workflow>[A-Za-z0-9 _.-]+) "
    r"run=(?P<run>\d+) attempt=(?P<attempt>\d+) pr=(?P<pr>\d+) "
    r"head=(?P<head>[0-9a-f]{40}) -->"
)
MAX_COMMENTS = 1000


class WakeError(ValueError):
    """Fail-closed malformed or inconsistent wake state."""


@dataclass(frozen=True)
class WakeRequest:
    workflow: str
    run_id: int
    run_attempt: int
    pr_number: int
    head_sha: str


def parse_event(payload: object) -> WakeRequest | None:
    if not isinstance(payload, dict):
        raise WakeError("workflow_run payload is not an object")
    run = payload.get("workflow_run")
    if not isinstance(run, dict):
        raise WakeError("workflow_run payload is missing")
    workflow = run.get("name")
    if workflow not in SUPPORTED_WORKFLOWS:
        return None
    if not isinstance(run.get("conclusion"), str) or not run["conclusion"]:
        return None
    run_id, run_attempt, head_sha = run.get("id"), run.get("run_attempt"), run.get("head_sha")
    pulls = run.get("pull_requests")
    if not isinstance(run_id, int) or not isinstance(run_attempt, int) or run_attempt < 1:
        raise WakeError("workflow_run identity is incomplete")
    if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
        raise WakeError("workflow_run exact head is invalid")
    if not isinstance(pulls, list):
        raise WakeError("workflow_run pull-request binding is missing")
    if len(pulls) != 1:
        return None
    pull = pulls[0]
    if not isinstance(pull, dict) or not isinstance(pull.get("number"), int):
        raise WakeError("workflow_run pull-request binding is invalid")
    return WakeRequest(workflow, run_id, run_attempt, int(pull["number"]), head_sha)


def current_pr_matches(request: WakeRequest, pull: object, repository: str) -> bool:
    if not isinstance(pull, dict):
        raise WakeError("current pull request is not an object")
    base, head = pull.get("base"), pull.get("head")
    if not isinstance(base, dict) or not isinstance(head, dict):
        raise WakeError("current pull request refs are incomplete")
    head_repo = head.get("repo")
    if not isinstance(head_repo, dict):
        raise WakeError("current pull request repository is incomplete")
    return bool(
        pull.get("state") == "open"
        and not pull.get("draft")
        and base.get("ref") == "master"
        and head.get("sha") == request.head_sha
        and head_repo.get("full_name") == repository
    )


def marker_text(request: WakeRequest) -> str:
    return (
        f"<!-- jarvis-e1-wake:v1 workflow={request.workflow} run={request.run_id} "
        f"attempt={request.run_attempt} pr={request.pr_number} head={request.head_sha} -->"
    )


def already_recorded(request: WakeRequest, comments: list[object]) -> bool:
    expected = (
        request.workflow,
        str(request.run_id),
        str(request.run_attempt),
        str(request.pr_number),
        request.head_sha,
    )
    for comment in comments:
        if not isinstance(comment, dict):
            raise WakeError("pull-request comment is not an object")
        body, user = comment.get("body"), comment.get("user")
        if not isinstance(body, str) or not isinstance(user, dict):
            raise WakeError("pull-request comment is incomplete")
        if user.get("login") != "github-actions[bot]":
            continue
        for match in MARKER_RE.finditer(body):
            actual = (
                match.group("workflow"),
                match.group("run"),
                match.group("attempt"),
                match.group("pr"),
                match.group("head"),
            )
            if actual == expected:
                return True
    return False


class GitHubClient:
    def __init__(self, repository: str, token: str) -> None:
        if not repository or "/" not in repository:
            raise WakeError("GITHUB_REPOSITORY is invalid")
        if not token:
            raise WakeError("GITHUB_TOKEN is missing")
        self.repository = repository
        self.token = token

    def request(self, path: str, *, method: str = "GET", payload: object | None = None) -> object:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{API_ROOT}/repos/{self.repository}{path}", data=data, method=method
        )
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise WakeError(f"GitHub API request failed: {method} {path}: {exc}") from exc

    def pull(self, number: int) -> object:
        return self.request(f"/pulls/{number}")

    def comments(self, number: int) -> list[object]:
        rows: list[object] = []
        for page in range(1, 11):
            payload = self.request(f"/issues/{number}/comments?per_page=100&page={page}")
            if not isinstance(payload, list):
                raise WakeError("comment pagination response is invalid")
            rows.extend(payload)
            if len(rows) > MAX_COMMENTS:
                raise WakeError("comment pagination exceeded the E1 bound")
            if len(payload) < 100:
                return rows
        raise WakeError("comment pagination did not terminate")

    def dispatch(self) -> None:
        self.request(
            f"/actions/workflows/{TARGET_WORKFLOW}/dispatches",
            method="POST",
            payload={"ref": "master"},
        )

    def record(self, number: int, body: str) -> None:
        result = self.request(
            f"/issues/{number}/comments", method="POST", payload={"body": body}
        )
        if not isinstance(result, dict) or not isinstance(result.get("id"), int):
            raise WakeError("wake marker comment was not created")


def run(payload: object, *, repository: str, client: GitHubClient) -> str:
    request = parse_event(payload)
    if request is None:
        return "noop:not_actionable"
    pull = client.pull(request.pr_number)
    if not current_pr_matches(request, pull, repository):
        return "noop:stale_head"
    comments = client.comments(request.pr_number)
    if already_recorded(request, comments):
        return "noop:duplicate"
    # Re-read immediately before dispatch so a head movement after the first read
    # cannot wake continuation for stale evidence.
    pull = client.pull(request.pr_number)
    if not current_pr_matches(request, pull, repository):
        return "noop:stale_head"
    # At-least-once dispatch comes before the durable marker. If marker creation
    # later fails, a rerun may dispatch again; the downstream 079 control plane
    # is independently exact-head/checkpoint-idempotent, so duplicate wake-ups do
    # not create duplicate authority or bypass CAS.
    client.dispatch()
    client.record(request.pr_number, marker_text(request))
    return "dispatched"


def main() -> int:
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    repository = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GITHUB_TOKEN", "")
    if not event_path:
        raise WakeError("GITHUB_EVENT_PATH is missing")
    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WakeError(f"workflow event payload is unreadable: {exc}") from exc
    result = run(payload, repository=repository, client=GitHubClient(repository, token))
    print(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WakeError as exc:
        print(f"E1 wake failed closed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
