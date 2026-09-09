#!/usr/bin/env python3
"""Fail-closed event bridge for V3.2 E1 continuation wake-ups.

This module owns no roadmap, implementation, review, or merge authority. It only
validates a terminal CI workflow_run against the current PR exact head, collapses
already-recorded identical wakes, optionally dispatches the fixed trusted cloud
delivery bridge for an exact owner-authored durable request, and dispatches the
existing spec-079 continuation workflow with the validated PR/head binding. The
downstream control planes reconstruct their own authority from fresh GitHub state.
"""

from __future__ import annotations

import hashlib
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
CLOUD_DELIVERY_WORKFLOW = "cloud-delivery-bridge.yml"
SUPPORTED_WORKFLOWS = {"CI"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MARKER_RE = re.compile(
    r"<!-- jarvis-e1-wake:v1 workflow=(?P<workflow>[A-Za-z0-9 _.-]+) "
    r"run=(?P<run>\d+) attempt=(?P<attempt>\d+) pr=(?P<pr>\d+) "
    r"head=(?P<head>[0-9a-f]{40}) -->"
)
DELIVERY_REQUEST_RE = re.compile(
    r"<!-- jarvis-cloud-delivery:dispatch:v1 pr=(?P<pr>\d+) "
    r"head=(?P<head>[0-9a-f]{40}) payload_comment_id=(?P<payload>\d+) "
    r"payload_body_sha256=(?P<payload_sha256>[0-9a-f]{64}) -->"
)
DELIVERY_MARKER_RE = re.compile(
    r"<!-- jarvis-cloud-delivery-dispatched:v1 run=(?P<run>\d+) "
    r"attempt=(?P<attempt>\d+) pr=(?P<pr>\d+) head=(?P<head>[0-9a-f]{40}) "
    r"payload_comment_id=(?P<payload>\d+) payload_body_sha256=(?P<payload_sha256>[0-9a-f]{64}) -->"
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


@dataclass(frozen=True)
class DeliveryRequest:
    pr_number: int
    head_sha: str
    payload_comment_id: int
    payload_body_sha256: str


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


def _comment_body_by_id(comments: list[object], comment_id: int) -> str | None:
    for comment in comments:
        if not isinstance(comment, dict):
            raise WakeError("pull-request comment is not an object")
        body, user = comment.get("body"), comment.get("user")
        if not isinstance(body, str) or not isinstance(user, dict):
            raise WakeError("pull-request comment is incomplete")
        if comment.get("id") == comment_id:
            return body
    return None


def requested_delivery(
    comments: list[object], *, repository: str, pr_number: int, head_sha: str
) -> DeliveryRequest | None:
    owner = repository.split("/", 1)[0]
    latest: DeliveryRequest | None = None
    for comment in comments:
        if not isinstance(comment, dict):
            raise WakeError("pull-request comment is not an object")
        body, user = comment.get("body"), comment.get("user")
        if not isinstance(body, str) or not isinstance(user, dict):
            raise WakeError("pull-request comment is incomplete")
        if user.get("login") != owner:
            continue
        match = DELIVERY_REQUEST_RE.fullmatch(body.strip())
        if match is None:
            continue
        payload_comment_id = int(match.group("payload"))
        payload_body_sha256 = match.group("payload_sha256")
        if payload_comment_id < 1 or not SHA256_RE.fullmatch(payload_body_sha256):
            continue
        if int(match.group("pr")) != pr_number or match.group("head") != head_sha:
            continue
        payload_body = _comment_body_by_id(comments, payload_comment_id)
        if payload_body is None:
            continue
        actual_sha256 = hashlib.sha256(payload_body.encode("utf-8")).hexdigest()
        if actual_sha256 != payload_body_sha256:
            continue
        latest = DeliveryRequest(pr_number, head_sha, payload_comment_id, payload_body_sha256)
    return latest


def delivery_marker_text(request: WakeRequest, delivery: DeliveryRequest) -> str:
    return (
        f"<!-- jarvis-cloud-delivery-dispatched:v1 run={request.run_id} "
        f"attempt={request.run_attempt} pr={delivery.pr_number} head={delivery.head_sha} "
        f"payload_comment_id={delivery.payload_comment_id} "
        f"payload_body_sha256={delivery.payload_body_sha256} -->"
    )


def delivery_already_recorded(
    request: WakeRequest, delivery: DeliveryRequest, comments: list[object]
) -> bool:
    expected = (
        str(request.run_id),
        str(request.run_attempt),
        str(delivery.pr_number),
        delivery.head_sha,
        str(delivery.payload_comment_id),
        delivery.payload_body_sha256,
    )
    for comment in comments:
        if not isinstance(comment, dict):
            raise WakeError("pull-request comment is not an object")
        body, user = comment.get("body"), comment.get("user")
        if not isinstance(body, str) or not isinstance(user, dict):
            raise WakeError("pull-request comment is incomplete")
        if user.get("login") != "github-actions[bot]":
            continue
        for match in DELIVERY_MARKER_RE.finditer(body):
            actual = (
                match.group("run"),
                match.group("attempt"),
                match.group("pr"),
                match.group("head"),
                match.group("payload"),
                match.group("payload_sha256"),
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

    def dispatch(self, pr_number: int, head_sha: str) -> None:
        self.request(
            f"/actions/workflows/{TARGET_WORKFLOW}/dispatches",
            method="POST",
            payload={
                "ref": "master",
                "inputs": {
                    "e1_pr_number": str(pr_number),
                    "e1_head_sha": head_sha,
                },
            },
        )

    def dispatch_delivery(self, delivery: DeliveryRequest) -> None:
        self.request(
            f"/actions/workflows/{CLOUD_DELIVERY_WORKFLOW}/dispatches",
            method="POST",
            payload={
                "ref": "master",
                "inputs": {
                    "pr": str(delivery.pr_number),
                    "payload_comment_id": str(delivery.payload_comment_id),
                    "payload_body_sha256": delivery.payload_body_sha256,
                },
            },
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
    wake_done = already_recorded(request, comments)
    delivery = requested_delivery(
        comments,
        repository=repository,
        pr_number=request.pr_number,
        head_sha=request.head_sha,
    )
    delivery_done = bool(
        delivery is not None and delivery_already_recorded(request, delivery, comments)
    )
    if wake_done and (delivery is None or delivery_done):
        return "noop:duplicate"
    pull = client.pull(request.pr_number)
    if not current_pr_matches(request, pull, repository):
        return "noop:stale_head"
    if delivery is not None and not delivery_done:
        client.dispatch_delivery(delivery)
        client.record(request.pr_number, delivery_marker_text(request, delivery))
    if not wake_done:
        client.dispatch(request.pr_number, request.head_sha)
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
