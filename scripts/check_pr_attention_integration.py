#!/usr/bin/env python3
"""Deterministic guard for the read-only jarvis-pr-attention integration."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKFLOW = Path(".github/workflows/pr-attention.yml")
PIN = "AlbertoRacerro/jarvis-pr-attention/cycle@c544e2885a69173c58feb2355bb53e8866e627eb"
EXPECTED_HEAD_VALUE = "${{ github.event.pull_request.head.sha }}"
FORBIDDEN_INPUTS = {
    "accepted-head",
    "confirm-accepted-head-authority",
    "accepted-head-source",
    "review-result-file",
    "continuity-result-file",
    "previous-failed-source-file",
}
MUTATING_RUN = re.compile(
    r"\b(?:gh\s+pr\s+(?:merge|review|edit)|gh\s+issue\s+(?:comment|edit)|git\s+push|"
    r"curl\b[^\n]*(?:POST|PATCH|PUT|DELETE))\b",
    re.IGNORECASE,
)
MUTATING_USES = re.compile(r"(?:merge|comment|label|review|status|dispatch|push)", re.IGNORECASE)
UNSAFE_SUMMARY = re.compile(r'echo\s+"[^"\n]*`\$\{\{')


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _key_value(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if stripped.startswith("- "):
        stripped = stripped[2:].lstrip()
    if ":" not in stripped:
        return None
    key, value = stripped.split(":", 1)
    return key.strip(), _unquote(value.strip())


def _block(lines: list[str], header: str, indent: int = 0) -> list[str]:
    prefix = " " * indent + header + ":"
    for index, line in enumerate(lines):
        if line == prefix:
            out: list[str] = []
            for child in lines[index + 1 :]:
                if child.strip() and len(child) - len(child.lstrip()) <= indent:
                    break
                out.append(child)
            return out
    return []


def _steps(lines: list[str]) -> list[dict[str, str]]:
    steps_block = _block(lines, "steps", 4)
    steps: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    collecting_run = False
    run_indent = 0
    for line in steps_block:
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 6 and stripped.startswith("- "):
            if current is not None:
                steps.append(current)
            current = {}
            collecting_run = False
            pair = _key_value(line)
            if pair:
                current[pair[0]] = pair[1]
            continue
        if current is None:
            continue
        if collecting_run and indent > run_indent:
            current["run"] = current.get("run", "") + stripped + "\n"
            continue
        collecting_run = False
        pair = _key_value(line)
        if pair and indent >= 8:
            key, value = pair
            if key == "run" and value in {"|", ">", "|-", ">-"}:
                collecting_run = True
                run_indent = indent
                current["run"] = ""
            elif indent == 8:
                current[key] = value
            elif indent == 10 and "with" in current:
                current[f"with.{key}"] = value
        if stripped == "with:" and indent == 8:
            current["with"] = ""
    if current is not None:
        steps.append(current)
    return steps


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()

    event_block = _block(lines, "on")
    event_keys = {_key_value(line)[0] for line in event_block if _key_value(line) and len(line) - len(line.lstrip()) == 2}
    if "pull_request" not in event_keys or "pull_request_target" in event_keys:
        errors.append("workflow must use pull_request and must not use pull_request_target")

    permissions = _block(lines, "permissions")
    permission_pairs = [_key_value(line) for line in permissions if _key_value(line)]
    if not permission_pairs:
        errors.append("explicit read-only permissions are required")
    for key, value in permission_pairs:
        if value.lower() != "read":
            errors.append(f"permission must be read-only: {key}={value}")

    steps = _steps(lines)
    attention = [step for step in steps if "jarvis-pr-attention" in step.get("uses", "")]
    if len(attention) != 1 or attention[0].get("uses") != PIN:
        errors.append(f"expected exactly one pinned jarvis-pr-attention action: {PIN}")
    elif attention[0].get("with.expected-head") != EXPECTED_HEAD_VALUE:
        errors.append("expected-head must bind directly to pull_request.head.sha")
    if attention:
        supplied = {key.removeprefix("with.") for key in attention[0] if key.startswith("with.")}
        for key in sorted(FORBIDDEN_INPUTS & supplied):
            errors.append(f"semantic-authority input is forbidden in V0: {key}")

    for step in steps:
        uses = step.get("uses", "")
        if uses != PIN and MUTATING_USES.search(uses):
            errors.append(f"mutation-capable downstream action is forbidden: {uses}")
        run = step.get("run", "")
        if MUTATING_RUN.search(run):
            errors.append("repository mutation command is forbidden")
        if UNSAFE_SUMMARY.search(run):
            errors.append("double-quoted echo must not contain Markdown backticks around expressions")

    return errors


def self_test() -> None:
    good = f"""name: x\non:\n  pull_request:\npermissions:\n  contents: read\njobs:\n  evidence:\n    steps:\n      - uses: {PIN}\n        with:\n          expected-head: {EXPECTED_HEAD_VALUE}\n"""
    assert not validate_text(good), validate_text(good)
    cases = {
        "mutable pin": good.replace(PIN, "AlbertoRacerro/jarvis-pr-attention/cycle@main"),
        "write permission": good.replace("contents: read", "contents: write"),
        "quoted write permission": good.replace("contents: read", 'contents: "write"'),
        "quoted admin permission": good.replace("contents: read", "contents: 'admin'"),
        "pull_request_target": good.replace("pull_request:", "pull_request_target:"),
        "missing exact head": good.replace(EXPECTED_HEAD_VALUE, "arbitrary"),
        "mutation consumer": good + "      - run: gh pr merge 1\n",
        "semantic authority": good.replace("expected-head:", "accepted-head: deadbeef\n          expected-head:"),
        "unsafe summary": good + '      - run: |\n          echo "Observed: `${{ steps.attention.outputs.head-sha }}`"\n',
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
