#!/usr/bin/env python3
"""Deterministic control plane for spec 079 scheduled continuation."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

API_ROOT = "https://api.github.com"
MODES = {"OFF", "SHADOW", "EXECUTE_NO_MERGE"}
ACTIVE_STATUSES = {"in_progress", "in_review"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SPEC_RE = re.compile(r"^\d{3}[a-z]?$", re.I)
PR_RE = re.compile(r"/pull/(\d+)")
SPEC_BINDING_RE = re.compile(r"(?<!\d)(\d{3}[a-z]?)(?!\d)", re.I)
MARKER_RE = re.compile(
    r"<!-- jarvis-continuation:v1 spec=(?P<spec>\d{3}[a-z]?) "
    r"pr=(?P<pr>\d+) input=(?P<input>[0-9a-f]{40}) "
    r"output=(?P<output>[0-9a-f]{40}) result=(?P<result>changed|no_change) -->",
    re.I,
)
MAX_OPEN_PULLS = 1000
MAX_COMMENTS = 5000
MAX_CHANGED_FILES = 20
MAX_PATCH_BYTES = 200_000
PROTECTED_BRANCHES = {"master", "main"}
CONTROL_PATHS = {
    "AGENTS.md",
    "CODEOWNERS",
    "scripts/daily_development_continuation.py",
    "backend/tests/test_daily_development_continuation.py",
}
SENSITIVE_PART_RE = re.compile(
    r"(^|[._/-])(env|secret|secrets|token|tokens|credential|credentials|key|keys)([._/-]|$)",
    re.I,
)


class ContinuationError(ValueError):
    """Fail-closed authority or integrity error."""


@dataclass(frozen=True)
class RegistryRow:
    spec_id: str
    status: str
    prs: tuple[int, ...]
    name: str


@dataclass(frozen=True)
class Candidate:
    spec_id: str
    pr_number: int
    head_ref: str
    head_sha: str
    base_sha: str


@dataclass(frozen=True)
class Plan:
    action: str
    mode: str
    reason: str
    spec_id: str = ""
    pr_number: int = 0
    head_ref: str = ""
    head_sha: str = ""
    base_sha: str = ""
    checkpoint_sha: str = ""


class GitHubReader(Protocol):
    def open_pulls(self) -> list[dict[str, object]]: ...

    def file_text(self, path: str, ref: str) -> str: ...

    def comments(self, number: int) -> list[dict[str, object]]: ...

    def compare(self, base: str, head: str) -> str: ...


class RestGitHubReader:
    def __init__(self, repository: str, token: str) -> None:
        if not repository or "/" not in repository:
            raise ContinuationError("GITHUB_REPOSITORY is invalid")
        if not token:
            raise ContinuationError("GITHUB_TOKEN is missing")
        self.repository = repository
        self.token = token

    def _request(self, url: str) -> object:
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ContinuationError(f"GitHub API read failed: {exc}") from exc

    def _pages(self, path: str, *, limit: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for page in range(1, 11):
            separator = "&" if "?" in path else "?"
            payload = self._request(
                f"{API_ROOT}/repos/{self.repository}/{path}{separator}per_page=100&page={page}"
            )
            if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
                raise ContinuationError("GitHub pagination response is incomplete")
            rows.extend(payload)
            if len(rows) > limit:
                raise ContinuationError("GitHub pagination exceeded the v0 bound")
            if len(payload) < 100:
                return rows
        raise ContinuationError("GitHub pagination did not terminate")

    def open_pulls(self) -> list[dict[str, object]]:
        return self._pages("pulls?state=open", limit=MAX_OPEN_PULLS)

    def file_text(self, path: str, ref: str) -> str:
        quoted_path = urllib.parse.quote(path, safe="/")
        quoted_ref = urllib.parse.quote(ref, safe="")
        payload = self._request(
            f"{API_ROOT}/repos/{self.repository}/contents/{quoted_path}?ref={quoted_ref}"
        )
        if not isinstance(payload, dict) or payload.get("encoding") != "base64":
            raise ContinuationError("GitHub file response is incomplete")
        content = payload.get("content")
        if not isinstance(content, str):
            raise ContinuationError("GitHub file content is missing")
        try:
            return base64.b64decode(content, validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ContinuationError("GitHub file content is invalid") from exc

    def comments(self, number: int) -> list[dict[str, object]]:
        return self._pages(f"issues/{number}/comments", limit=MAX_COMMENTS)

    def compare(self, base: str, head: str) -> str:
        payload = self._request(f"{API_ROOT}/repos/{self.repository}/compare/{base}...{head}")
        if not isinstance(payload, dict) or not isinstance(payload.get("status"), str):
            raise ContinuationError("GitHub compare response is incomplete")
        return str(payload["status"])


def parse_registry(text: str) -> dict[str, RegistryRow]:
    rows: dict[str, RegistryRow] = {}
    in_registry = False
    for line in text.splitlines():
        if line.strip() == "## Registry":
            in_registry = True
            continue
        if in_registry and line.startswith("## "):
            break
        if not in_registry or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"Spec", "---"}:
            continue
        if len(cells) != 6:
            raise ContinuationError("STATUS.md has an invalid registry row")
        spec_id, status, pr_cell, name, _, _ = cells
        spec_id = spec_id.lower()
        if not SPEC_RE.fullmatch(spec_id) or spec_id in rows:
            raise ContinuationError("STATUS.md has an invalid or duplicate spec id")
        rows[spec_id] = RegistryRow(
            spec_id=spec_id,
            status=status,
            prs=tuple(sorted({int(value) for value in PR_RE.findall(pr_cell)})),
            name=name,
        )
    if not rows:
        raise ContinuationError("STATUS.md registry is missing")
    return rows


def _pull_fields(pull: dict[str, object], repository: str) -> tuple[int, str, str, str, str]:
    number = pull.get("number")
    base = pull.get("base")
    head = pull.get("head")
    if not isinstance(number, int) or not isinstance(base, dict) or not isinstance(head, dict):
        raise ContinuationError("open pull request response is incomplete")
    base_ref = base.get("ref")
    base_sha = base.get("sha")
    head_ref = head.get("ref")
    head_sha = head.get("sha")
    head_repo = head.get("repo")
    if not all(isinstance(value, str) for value in (base_ref, base_sha, head_ref, head_sha)):
        raise ContinuationError(f"PR #{number} has incomplete refs")
    if not isinstance(head_repo, dict) or head_repo.get("full_name") != repository:
        raise ContinuationError(f"PR #{number} is a fork")
    if base_ref != "master":
        raise ContinuationError(f"PR #{number} base is not master")
    if head_ref in PROTECTED_BRANCHES or not head_ref:
        raise ContinuationError(f"PR #{number} head branch is protected or missing")
    if not SHA_RE.fullmatch(base_sha) or not SHA_RE.fullmatch(head_sha):
        raise ContinuationError(f"PR #{number} has an invalid exact head")
    return number, base_ref, base_sha, head_ref, head_sha


def discover_candidate(repository: str, reader: GitHubReader) -> Candidate | None:
    candidates: list[Candidate] = []
    unresolved_active: list[str] = []
    for pull in reader.open_pulls():
        if pull.get("state") != "open" or bool(pull.get("draft")):
            continue
        number, _, base_sha, head_ref, head_sha = _pull_fields(pull, repository)
        registry = parse_registry(reader.file_text("docs/specs/STATUS.md", head_sha))
        active = [row for row in registry.values() if row.status in ACTIVE_STATUSES]
        if not active:
            continue
        if len(active) != 1:
            raise ContinuationError(f"PR #{number} registry has multiple active fronts")
        row = active[0]
        if row.status != "in_review":
            unresolved_active.append(f"{row.spec_id}={row.status} on PR #{number}")
            continue
        if row.prs != (number,):
            raise ContinuationError(f"PR #{number} registry does not bind itself exactly")
        binding_text = " ".join(str(pull.get(key) or "") for key in ("title", "body")) + f" {head_ref}"
        if row.spec_id not in {value.lower() for value in SPEC_BINDING_RE.findall(binding_text)}:
            raise ContinuationError(f"PR #{number} does not bind spec {row.spec_id}")
        candidates.append(Candidate(row.spec_id, number, head_ref, head_sha, base_sha))
    if unresolved_active:
        raise ContinuationError("active pre-PR state is not resumable in v0: " + ", ".join(unresolved_active))
    if not candidates:
        return None
    if len(candidates) != 1:
        raise ContinuationError("multiple active implementation PRs were discovered")
    return candidates[0]


def marker_text(spec: str, pr: int, input_head: str, output_head: str) -> str:
    result = "changed" if input_head != output_head else "no_change"
    return (
        f"<!-- jarvis-continuation:v1 spec={spec} pr={pr} input={input_head} "
        f"output={output_head} result={result} -->"
    )


def _markers(comments: list[dict[str, object]], spec: str, pr: int) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    for comment in comments:
        body = comment.get("body")
        if not isinstance(body, str):
            raise ContinuationError("PR comment response is incomplete")
        for match in MARKER_RE.finditer(body):
            if match.group("spec").lower() == spec and int(match.group("pr")) == pr:
                result.append(match)
    return result


def checkpoint_for(candidate: Candidate, comments: list[dict[str, object]]) -> tuple[str, bool]:
    matches = _markers(comments, candidate.spec_id, candidate.pr_number)
    if not matches:
        return candidate.base_sha, False
    seen_inputs: dict[str, tuple[str, str]] = {}
    for match in matches:
        key = match.group("input")
        value = (match.group("output"), match.group("result"))
        previous = seen_inputs.setdefault(key, value)
        if previous != value:
            raise ContinuationError("incompatible continuation markers share one input head")
    last = matches[-1]
    output = last.group("output")
    if last.group("result") == "no_change" and output == candidate.head_sha:
        return output, True
    if output != candidate.head_sha:
        raise ContinuationError("continuation marker output did not advance to the current PR head")
    return output, False


def build_plan(*, mode: str, repository: str, reader: GitHubReader, token_present: bool) -> Plan:
    normalized_mode = mode.strip().upper()
    if normalized_mode not in MODES:
        raise ContinuationError("continuation mode must be OFF, SHADOW, or EXECUTE_NO_MERGE")
    if normalized_mode == "OFF":
        return Plan("noop", normalized_mode, "mode_off")
    candidate = discover_candidate(repository, reader)
    if candidate is None:
        return Plan("noop", normalized_mode, "no_active_front")
    comments = reader.comments(candidate.pr_number)
    checkpoint, terminal = checkpoint_for(candidate, comments)
    if terminal:
        return Plan(
            "noop", normalized_mode, "head_already_processed", candidate.spec_id,
            candidate.pr_number, candidate.head_ref, candidate.head_sha,
            candidate.base_sha, checkpoint,
        )
    status = reader.compare(checkpoint, candidate.head_sha)
    if status not in {"ahead", "identical"}:
        raise ContinuationError("current PR head does not descend from the checkpoint")
    action = "shadow" if normalized_mode == "SHADOW" else "execute"
    if action == "execute" and not token_present:
        raise ContinuationError("CLAUDE_CODE_OAUTH_TOKEN is not configured")
    return Plan(
        action, normalized_mode, "eligible", candidate.spec_id, candidate.pr_number,
        candidate.head_ref, candidate.head_sha, candidate.base_sha, checkpoint,
    )


def _normalized_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def validate_changed_paths(paths: list[str]) -> None:
    if len(paths) > MAX_CHANGED_FILES:
        raise ContinuationError("continuation patch changes too many files")
    for raw_path in paths:
        path = _normalized_path(raw_path)
        if not path or path.startswith(".github/") or path in CONTROL_PATHS:
            raise ContinuationError(f"continuation patch changes a protected path: {raw_path}")
        if SENSITIVE_PART_RE.search(path):
            raise ContinuationError(f"continuation patch changes a sensitive path: {raw_path}")


def validate_status_change(before: str, after: str, active_spec: str) -> None:
    before_rows = parse_registry(before)
    after_rows = parse_registry(after)
    if set(before_rows) != set(after_rows):
        raise ContinuationError("continuation may not add or remove registry rows")
    for spec_id in before_rows:
        if spec_id != active_spec and before_rows[spec_id] != after_rows[spec_id]:
            raise ContinuationError("STATUS.md may change only the active spec row")


def _post_comment(repository: str, pr: int, token: str, body: str) -> None:
    if not repository or not token:
        raise ContinuationError("repository and token are required to record a marker")
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        f"{API_ROOT}/repos/{repository}/issues/{pr}/comments", data=payload, method="POST"
    )
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 201:
                raise ContinuationError("checkpoint comment was not created")
    except urllib.error.URLError as exc:
        raise ContinuationError(f"checkpoint comment failed: {exc}") from exc


def append_outputs(plan: Plan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in asdict(plan).items():
            handle.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    plan_parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""))
    plan_parser.add_argument("--mode", default=os.getenv("JARVISOS_CONTINUATION_MODE", "OFF"))
    plan_parser.add_argument("--claude-token-present", default=os.getenv("CLAUDE_TOKEN_PRESENT", "false"))
    plan_parser.add_argument("--github-output", type=Path, default=Path(os.getenv("GITHUB_OUTPUT", "/dev/null")))
    validate = commands.add_parser("validate")
    validate.add_argument("--changed-files", type=Path, required=True)
    validate.add_argument("--active-spec", required=True)
    validate.add_argument("--status-before", type=Path)
    validate.add_argument("--status-after", type=Path)
    marker = commands.add_parser("marker")
    marker.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    marker.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""))
    marker.add_argument("--spec", required=True)
    marker.add_argument("--pr", type=int, required=True)
    marker.add_argument("--input-head", required=True)
    marker.add_argument("--output-head", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            reader = RestGitHubReader(args.repository, args.token)
            result = build_plan(
                mode=args.mode,
                repository=args.repository,
                reader=reader,
                token_present=str(args.claude_token_present).lower() == "true",
            )
            append_outputs(result, args.github_output)
            print(json.dumps(asdict(result), sort_keys=True))
        elif args.command == "validate":
            paths = [
                line.strip()
                for line in args.changed_files.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            validate_changed_paths(paths)
            if "docs/specs/STATUS.md" in paths:
                if args.status_before is None or args.status_after is None:
                    raise ContinuationError("STATUS.md validation requires before and after files")
                validate_status_change(
                    args.status_before.read_text(encoding="utf-8"),
                    args.status_after.read_text(encoding="utf-8"),
                    args.active_spec.lower(),
                )
            print("continuation diff validation: OK")
        else:
            if not SHA_RE.fullmatch(args.input_head) or not SHA_RE.fullmatch(args.output_head):
                raise ContinuationError("marker SHA is invalid")
            _post_comment(
                args.repository,
                args.pr,
                args.token,
                marker_text(args.spec.lower(), args.pr, args.input_head, args.output_head),
            )
        return 0
    except (ContinuationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"daily-development-continuation: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
