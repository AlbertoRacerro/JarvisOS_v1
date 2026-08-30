#!/usr/bin/env python3
"""Deterministic guard for the read-only jarvis-pr-attention integration."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKFLOW = Path(".github/workflows/pr-attention.yml")
PIN = "AlbertoRacerro/jarvis-pr-attention/cycle@c544e2885a69173c58feb2355bb53e8866e627eb"
EXPECTED_HEAD = "expected-head: ${{ github.event.pull_request.head.sha }}"
FORBIDDEN_EVENT = "pull_request_target"
WRITE_PERMISSION = re.compile(r"^\s*[A-Za-z-]+:\s*(?:write|admin)\s*$", re.MULTILINE)
MUTATING_USES = re.compile(
    r"^\s*-?\s*uses:\s*[^#\n]*(?:merge|comment|label|review|status|dispatch|push)[^#\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
MUTATING_RUN = re.compile(
    r"\b(?:gh\s+pr\s+(?:merge|review|edit)|gh\s+issue\s+(?:comment|edit)|git\s+push|"
    r"curl\b[^\n]*(?:POST|PATCH|PUT|DELETE))\b",
    re.IGNORECASE,
)


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    uses = [line.strip().removeprefix("- ").removeprefix("uses: ") for line in text.splitlines() if line.strip().startswith(("uses:", "- uses:"))]
    attention_refs = [value for value in uses if "jarvis-pr-attention" in value]
    if attention_refs != [PIN]:
        errors.append(f"expected exactly one pinned jarvis-pr-attention action: {PIN}")
    if FORBIDDEN_EVENT in text:
        errors.append("pull_request_target is forbidden")
    if "on:\n  pull_request:" not in text:
        errors.append("workflow must use pull_request event")
    if WRITE_PERMISSION.search(text):
        errors.append("write/admin workflow permission is forbidden")
    if EXPECTED_HEAD not in text:
        errors.append("expected-head must bind directly to pull_request.head.sha")
    forbidden_inputs = (
        "accepted-head:",
        "confirm-accepted-head-authority:",
        "accepted-head-source:",
        "review-result-file:",
        "continuity-result-file:",
        "previous-failed-source-file:",
    )
    for key in forbidden_inputs:
        if re.search(rf"^\s+{re.escape(key)}", text, re.MULTILINE):
            errors.append(f"semantic-authority input is forbidden in V0: {key}")
    if MUTATING_USES.search(text):
        errors.append("mutation-capable downstream action is forbidden")
    if MUTATING_RUN.search(text):
        errors.append("repository mutation command is forbidden")
    if re.search(r"\$\{\{\s*steps\.attention\.outputs\.merge-candidate\s*\}\}.*(?:gh|curl|uses:)", text, re.IGNORECASE):
        errors.append("merge-candidate must not control a mutation")
    return errors


def self_test() -> None:
    good = f"""on:\n  pull_request:\npermissions:\n  contents: read\njobs:\n  x:\n    steps:\n      - uses: {PIN}\n        with:\n          {EXPECTED_HEAD}\n"""
    assert not validate_text(good), validate_text(good)
    cases = {
        "mutable pin": good.replace(PIN, "AlbertoRacerro/jarvis-pr-attention/cycle@main"),
        "write permission": good.replace("contents: read", "contents: write"),
        "pull_request_target": good.replace("pull_request:", "pull_request_target:"),
        "missing exact head": good.replace(EXPECTED_HEAD, "expected-head: arbitrary"),
        "mutation consumer": good + "      - run: gh pr merge 1\n",
        "semantic authority": good + "          accepted-head: deadbeef\n",
    }
    for name, candidate in cases.items():
        assert validate_text(candidate), f"negative fixture unexpectedly passed: {name}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(WORKFLOW))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("pr-attention integration checker self-test: PASS")
        return 0
    path = Path(args.path)
    if not path.is_file():
        print(f"missing workflow: {path}", file=sys.stderr)
        return 1
    errors = validate_text(path.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"PR_ATTENTION_CONTRACT: {error}", file=sys.stderr)
        return 1
    print("pr-attention integration contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
