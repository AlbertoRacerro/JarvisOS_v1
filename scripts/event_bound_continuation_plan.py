#!/usr/bin/env python3
"""Exact-front adapter for E1 workflow_dispatch continuation wakes.

The scheduled/manual spec-079 path keeps its existing single-front discovery.
Only E1 dispatches carrying both an expected PR and exact head use this adapter,
which narrows the existing reader before invoking the canonical planner.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAILY_SCRIPT = ROOT / "scripts" / "daily_development_continuation.py"
SPEC = importlib.util.spec_from_file_location("daily_development_continuation", DAILY_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("daily continuation module cannot be loaded")
daily = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = daily
SPEC.loader.exec_module(daily)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class BoundReader:
    def __init__(self, delegate: object, expected_pr: int, expected_head: str) -> None:
        self.delegate = delegate
        self.expected_pr = expected_pr
        self.expected_head = expected_head

    def open_pulls(self) -> list[dict[str, object]]:
        pulls = self.delegate.open_pulls()
        result: list[dict[str, object]] = []
        for pull in pulls:
            if not isinstance(pull, dict) or pull.get("number") != self.expected_pr:
                continue
            head = pull.get("head")
            if not isinstance(head, dict) or head.get("sha") != self.expected_head:
                return []
            result.append(pull)
        if len(result) > 1:
            raise daily.ContinuationError("E1 binding resolved duplicate PR rows")
        return result

    def file_text(self, path: str, ref: str) -> str:
        return self.delegate.file_text(path, ref)

    def comments(self, number: int) -> list[dict[str, object]]:
        return self.delegate.comments(number)

    def compare(self, base: str, head: str) -> str:
        return self.delegate.compare(base, head)

    def commit_info(self, sha: str) -> dict[str, object]:
        return self.delegate.commit_info(sha)


def parse_binding(pr_raw: str, head_raw: str) -> tuple[int, str]:
    if not pr_raw or not head_raw:
        raise daily.ContinuationError("E1 PR/head binding must be supplied together")
    try:
        pr = int(pr_raw)
    except ValueError as exc:
        raise daily.ContinuationError("E1 PR binding is invalid") from exc
    if pr < 1 or not SHA_RE.fullmatch(head_raw):
        raise daily.ContinuationError("E1 PR/head binding is invalid")
    return pr, head_raw


def main() -> int:
    repository = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GITHUB_TOKEN", "")
    mode = os.getenv("JARVISOS_CONTINUATION_MODE", "OFF")
    token_present = os.getenv("CLAUDE_TOKEN_PRESENT", "false").lower() == "true"
    output = Path(os.getenv("GITHUB_OUTPUT", "/dev/null"))
    try:
        expected_pr, expected_head = parse_binding(
            os.getenv("E1_PR_NUMBER", ""), os.getenv("E1_HEAD_SHA", "")
        )
        reader = BoundReader(daily.RestGitHubReader(repository, token), expected_pr, expected_head)
        verifier = daily.GitHubOIDCVerifier(repository)
        plan = daily.build_plan(
            mode=mode,
            repository=repository,
            reader=reader,
            token_present=token_present,
            verifier=verifier,
        )
        daily.append_outputs(plan, output)
        return 0
    except (daily.ContinuationError, OSError) as exc:
        print(f"continuation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
