#!/usr/bin/env python3
"""Validate trusted Codex delivery comments for cloud-delivery dispatch.

This script does not write GitHub state and never applies patches. It only binds an
issue_comment event to the existing cloud-delivery bridge inputs. The actual patch
remains untrusted data and is re-fetched, digested, admitted, validated, and
materialized by `.github/workflows/cloud-delivery-bridge.yml`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

CODEX_MARKER = "<!-- jarvis-codex-result-delivery:v1 -->"
DELIVERY_MARKER = "<!-- jarvis-cloud-delivery:v1 -->"
TRUSTED_ASSOCIATIONS = {"OWNER"}
TRUSTED_BOT_LOGINS = {"chatgpt-codex-connector[bot]"}


class DispatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class DispatchRequest:
    pr: int
    comment_id: int
    payload_body_sha256: str


def request_from_event(event: dict) -> DispatchRequest:
    if event.get("action") != "created":
        raise DispatchError("only newly created comments are eligible")

    issue = event.get("issue")
    comment = event.get("comment")
    if not isinstance(issue, dict) or not isinstance(comment, dict):
        raise DispatchError("issue/comment record missing")
    if not isinstance(issue.get("pull_request"), dict):
        raise DispatchError("comment is not attached to a pull request")

    association = str(comment.get("author_association", ""))
    user = comment.get("user")
    login = str(user.get("login", "")) if isinstance(user, dict) else ""
    trusted_author = association in TRUSTED_ASSOCIATIONS or login in TRUSTED_BOT_LOGINS
    if not trusted_author:
        raise DispatchError("comment author is not an admitted maintainer/Codex actor")

    body = str(comment.get("body", ""))
    if body.count(CODEX_MARKER) != 1:
        raise DispatchError("comment must contain exactly one Codex result marker")
    if body.count(DELIVERY_MARKER) != 1:
        raise DispatchError("comment must contain exactly one cloud delivery marker")

    try:
        pr = int(issue["number"])
        comment_id = int(comment["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DispatchError("invalid PR/comment identity") from exc
    if pr < 1 or comment_id < 1:
        raise DispatchError("invalid PR/comment identity")

    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return DispatchRequest(pr=pr, comment_id=comment_id, payload_body_sha256=digest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Codex result delivery comment")
    parser.add_argument("--event", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    request = request_from_event(event)
    output = Path(args.output)
    output.write_text(
        "\n".join(
            [
                f"pr={request.pr}",
                f"comment_id={request.comment_id}",
                f"payload_body_sha256={request.payload_body_sha256}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
