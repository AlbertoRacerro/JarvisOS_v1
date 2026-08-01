#!/usr/bin/env python3
"""Deterministic control plane for spec 079 scheduled continuation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Protocol

API_ROOT = "https://api.github.com"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_JWKS = f"{OIDC_ISSUER}/.well-known/jwks"
MARKER_OIDC_AUDIENCE_PREFIX = "jarvisos-continuation-marker-v1"
COMMIT_OIDC_AUDIENCE_PREFIX = "jarvisos-continuation-commit-v1"
WORKFLOW_PATH = ".github/workflows/daily-development-continuation.yml"
MODES = {"OFF", "SHADOW", "EXECUTE_NO_MERGE"}
ACTIVE_STATUSES = {"in_progress", "in_review"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SPEC_RE = re.compile(r"^\d{3}[a-z]?$", re.I)
PR_RE = re.compile(r"/pull/(\d+)")
SPEC_BINDING_RE = re.compile(r"(?<!\d)(\d{3}[a-z]?)(?!\d)", re.I)
MARKER_RE = re.compile(
    r"<!-- jarvis-continuation:v2 spec=(?P<spec>\d{3}[a-z]?) "
    r"pr=(?P<pr>\d+) input=(?P<input>[0-9a-f]{40}) "
    r"output=(?P<output>[0-9a-f]{40}) result=(?P<result>changed|no_change) "
    r"run=(?P<run>\d+) oidc=(?P<oidc>[A-Za-z0-9._-]+) -->",
    re.I,
)
MAX_OPEN_PULLS = 1000
MAX_COMMENTS = 5000
MAX_CHANGED_FILES = 20
MAX_RECOVERY_COMMITS = 500
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
SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


class ContinuationError(ValueError):
    """Fail-closed authority or integrity error."""


@dataclass(frozen=True)
class RegistryRow:
    spec_id: str
    status: str
    prs: tuple[int, ...]
    name: str
    depends_on: str
    description: str


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
    recovery_output_sha: str = ""


class GitHubReader(Protocol):
    def open_pulls(self) -> list[dict[str, object]]: ...
    def file_text(self, path: str, ref: str) -> str: ...
    def comments(self, number: int) -> list[dict[str, object]]: ...
    def compare(self, base: str, head: str) -> str: ...
    def commit_info(self, sha: str) -> dict[str, object]: ...


class MarkerVerifier(Protocol):
    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool: ...


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

    def commit_info(self, sha: str) -> dict[str, object]:
        payload = self._request(f"{API_ROOT}/repos/{self.repository}/commits/{sha}")
        if not isinstance(payload, dict):
            raise ContinuationError("GitHub commit response is incomplete")
        return payload


def _b64url_decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ContinuationError("OIDC token contains invalid base64url") from exc


def _json_object(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContinuationError(f"OIDC {label} is invalid") from exc
    if not isinstance(value, dict):
        raise ContinuationError(f"OIDC {label} is not an object")
    return value


def _rsa_rs256_valid(signing_input: bytes, signature: bytes, jwk: dict[str, object]) -> bool:
    n_raw, e_raw = jwk.get("n"), jwk.get("e")
    if not isinstance(n_raw, str) or not isinstance(e_raw, str):
        return False
    n = int.from_bytes(_b64url_decode(n_raw), "big")
    e = int.from_bytes(_b64url_decode(e_raw), "big")
    size = (n.bit_length() + 7) // 8
    if len(signature) != size or size < 256:
        return False
    encoded = pow(int.from_bytes(signature, "big"), e, n).to_bytes(size, "big")
    digest_info = SHA256_DIGEST_INFO + hashlib.sha256(signing_input).digest()
    padding_length = size - len(digest_info) - 3
    if padding_length < 8:
        return False
    expected = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + digest_info
    return hmac.compare_digest(encoded, expected)


class GitHubOIDCVerifier:
    def __init__(
        self,
        repository: str,
        *,
        jwks_loader: Callable[[], dict[str, object]] | None = None,
        now: Callable[[], float] = time.time,
    ) -> None:
        self.repository = repository
        self.jwks_loader = jwks_loader or self._load_jwks
        self.now = now
        self.expected_workflow_ref = (
            f"{repository}/{WORKFLOW_PATH}@refs/heads/master"
        )
        self._jwks: dict[str, object] | None = None

    @staticmethod
    def _load_jwks() -> dict[str, object]:
        request = urllib.request.Request(OIDC_JWKS)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise ContinuationError(f"GitHub OIDC JWKS read failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise ContinuationError("GitHub OIDC JWKS response is incomplete")
        return payload

    def verify(
        self,
        token: str,
        *,
        run_id: str,
        audience: str,
        require_fresh: bool = False,
    ) -> bool:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return False
            header = _json_object(_b64url_decode(parts[0]), "header")
            claims = _json_object(_b64url_decode(parts[1]), "claims")
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                return False
            prefixes = (
                f"{MARKER_OIDC_AUDIENCE_PREFIX}-",
                f"{COMMIT_OIDC_AUDIENCE_PREFIX}-",
            )
            if not audience.startswith(prefixes):
                return False
            if self._jwks is None:
                self._jwks = self.jwks_loader()
            payload = self._jwks
            keys = payload.get("keys")
            if not isinstance(keys, list):
                return False
            jwk = next(
                (
                    item
                    for item in keys
                    if isinstance(item, dict)
                    and item.get("kid") == header["kid"]
                    and item.get("kty") == "RSA"
                    and item.get("use") in {None, "sig"}
                ),
                None,
            )
            if jwk is None or not _rsa_rs256_valid(
                f"{parts[0]}.{parts[1]}".encode("ascii"), _b64url_decode(parts[2]), jwk
            ):
                return False
            claim_audience = claims.get("aud")
            audiences = (
                {claim_audience}
                if isinstance(claim_audience, str)
                else set(claim_audience or [])
            )
            required = {
                "iss": OIDC_ISSUER,
                "repository": self.repository,
                "workflow_ref": self.expected_workflow_ref,
                "ref": "refs/heads/master",
                "run_id": str(run_id),
            }
            if any(claims.get(key) != value for key, value in required.items()):
                return False
            if audience not in audiences:
                return False
            if claims.get("event_name") not in {"schedule", "workflow_dispatch"}:
                return False
            iat, nbf, exp = (claims.get(name) for name in ("iat", "nbf", "exp"))
            if not all(isinstance(value, int) for value in (iat, nbf, exp)):
                return False
            if not (iat - 60 <= nbf <= exp and 0 < exp - iat <= 900):
                return False
            if require_fresh:
                now = int(self.now())
                if now < nbf - 30 or now > exp:
                    return False
            return True
        except (ContinuationError, TypeError, ValueError, UnicodeEncodeError):
            return False


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
        spec_id, status, pr_cell, name, depends_on, description = cells
        spec_id = spec_id.lower()
        if not SPEC_RE.fullmatch(spec_id) or spec_id in rows:
            raise ContinuationError("STATUS.md has an invalid or duplicate spec id")
        rows[spec_id] = RegistryRow(
            spec_id,
            status,
            tuple(sorted({int(value) for value in PR_RE.findall(pr_cell)})),
            name,
            depends_on,
            description,
        )
    if not rows:
        raise ContinuationError("STATUS.md registry is missing")
    return rows


def _pull_fields(pull: dict[str, object], repository: str) -> tuple[int, str, str, str, str]:
    number, base, head = pull.get("number"), pull.get("base"), pull.get("head")
    if not isinstance(number, int) or not isinstance(base, dict) or not isinstance(head, dict):
        raise ContinuationError("open pull request response is incomplete")
    base_ref, base_sha = base.get("ref"), base.get("sha")
    head_ref, head_sha, head_repo = head.get("ref"), head.get("sha"), head.get("repo")
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
        binding_text = " ".join(str(pull.get(key) or "") for key in ("title", "body"))
        binding_text += f" {head_ref}"
        bindings = {value.lower() for value in SPEC_BINDING_RE.findall(binding_text)}
        if row.spec_id not in bindings:
            raise ContinuationError(f"PR #{number} does not bind spec {row.spec_id}")
        candidates.append(Candidate(row.spec_id, number, head_ref, head_sha, base_sha))
    if unresolved_active:
        raise ContinuationError("active pre-PR state is not resumable in v0: " + ", ".join(unresolved_active))
    if not candidates:
        return None
    if len(candidates) != 1:
        raise ContinuationError("multiple active implementation PRs were discovered")
    return candidates[0]


def marker_audience(
    spec: str, pr: int, input_head: str, output_head: str
) -> str:
    result = "changed" if input_head != output_head else "no_change"
    canonical = (
        f"v2|spec={spec.lower()}|pr={pr}|input={input_head}|"
        f"output={output_head}|result={result}"
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{MARKER_OIDC_AUDIENCE_PREFIX}-{digest}"


def commit_audience(spec: str, pr: int, input_head: str, tree_sha: str) -> str:
    canonical = (
        f"v1|spec={spec.lower()}|pr={pr}|input={input_head}|"
        f"tree={tree_sha}|result=changed"
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{COMMIT_OIDC_AUDIENCE_PREFIX}-{digest}"


def marker_text(
    spec: str,
    pr: int,
    input_head: str,
    output_head: str,
    run_id: str,
    oidc_token: str,
) -> str:
    result = "changed" if input_head != output_head else "no_change"
    return (
        f"<!-- jarvis-continuation:v2 spec={spec} pr={pr} input={input_head} "
        f"output={output_head} result={result} run={run_id} oidc={oidc_token} -->"
    )


def _verified_markers(
    comments: list[dict[str, object]],
    *,
    spec: str,
    pr: int,
    verifier: MarkerVerifier,
) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    for comment in comments:
        body, user = comment.get("body"), comment.get("user")
        if not isinstance(body, str) or not isinstance(user, dict):
            raise ContinuationError("PR comment response is incomplete")
        for match in MARKER_RE.finditer(body):
            if match.group("spec").lower() != spec or int(match.group("pr")) != pr:
                continue
            if user.get("login") != "github-actions[bot]":
                continue
            audience = marker_audience(
                match.group("spec"),
                int(match.group("pr")),
                match.group("input"),
                match.group("output"),
            )
            if not verifier.verify(
                match.group("oidc"),
                run_id=match.group("run"),
                audience=audience,
            ):
                continue
            result.append(match)
    return result


def checkpoint_for(
    candidate: Candidate,
    comments: list[dict[str, object]],
    *,
    verifier: MarkerVerifier,
) -> tuple[str, bool]:
    matches = _verified_markers(
        comments,
        spec=candidate.spec_id,
        pr=candidate.pr_number,
        verifier=verifier,
    )
    if not matches:
        return candidate.base_sha, False
    changed_edges: dict[str, str] = {}
    no_change_inputs: set[str] = set()
    all_inputs: set[str] = set()
    for match in matches:
        input_head, output_head, result = (
            match.group("input"),
            match.group("output"),
            match.group("result"),
        )
        all_inputs.add(input_head)
        if result == "no_change":
            if output_head != input_head:
                raise ContinuationError("no-change marker changed the checkpoint")
            no_change_inputs.add(input_head)
            continue
        if output_head == input_head:
            raise ContinuationError("changed marker did not advance the checkpoint")
        if input_head in changed_edges and changed_edges[input_head] != output_head:
            raise ContinuationError(
                "incompatible continuation markers share one input head"
            )
        changed_edges[input_head] = output_head
    checkpoint = candidate.base_sha
    seen: set[str] = set()
    while checkpoint in changed_edges:
        if checkpoint in seen:
            raise ContinuationError("continuation marker chain contains a cycle")
        seen.add(checkpoint)
        checkpoint = changed_edges[checkpoint]
    reachable_inputs = seen | {checkpoint}
    if all_inputs - reachable_inputs:
        raise ContinuationError("continuation marker chain is not contiguous")
    terminal = checkpoint in no_change_inputs and checkpoint not in changed_edges
    return checkpoint, terminal and checkpoint == candidate.head_sha


def _continuation_commit(
    payload: dict[str, object],
    candidate: Candidate,
    verifier: MarkerVerifier,
) -> tuple[str, str] | None:
    sha, commit, parents = payload.get("sha"), payload.get("commit"), payload.get("parents")
    author, committer = payload.get("author"), payload.get("committer")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ContinuationError("GitHub commit SHA is incomplete")
    if not isinstance(commit, dict) or not isinstance(parents, list):
        raise ContinuationError("GitHub commit metadata is incomplete")
    if not isinstance(author, dict) or not isinstance(committer, dict):
        return None
    if author.get("login") != "github-actions[bot]" or committer.get("login") != "github-actions[bot]":
        return None
    message, tree = commit.get("message"), commit.get("tree")
    if not isinstance(message, str) or not isinstance(tree, dict):
        raise ContinuationError("GitHub commit message or tree is incomplete")
    actual_tree = tree.get("sha")
    if not isinstance(actual_tree, str) or not SHA_RE.fullmatch(actual_tree):
        raise ContinuationError("GitHub commit tree SHA is incomplete")
    trailers: dict[str, str] = {}
    for line in message.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key.startswith("Jarvis-"):
            if key in trailers and trailers[key] != value:
                raise ContinuationError("continuation commit has conflicting trailers")
            trailers[key] = value
    if trailers.get("Jarvis-Continuation") != "v2":
        return None
    input_head = trailers.get("Jarvis-Input", "")
    tree_sha = trailers.get("Jarvis-Tree", "")
    run_id = trailers.get("Jarvis-Run", "")
    oidc_token = trailers.get("Jarvis-OIDC", "")
    expected = {"Jarvis-Spec": candidate.spec_id, "Jarvis-PR": str(candidate.pr_number)}
    if any(trailers.get(key) != value for key, value in expected.items()):
        return None
    parent_shas = [item.get("sha") for item in parents if isinstance(item, dict)]
    if not SHA_RE.fullmatch(input_head) or parent_shas != [input_head]:
        raise ContinuationError("continuation commit does not have its declared input as sole parent")
    if tree_sha != actual_tree:
        raise ContinuationError("continuation commit tree does not match its authenticated trailer")
    if not run_id.isdigit() or not oidc_token:
        raise ContinuationError("continuation commit OIDC proof is incomplete")
    audience = commit_audience(candidate.spec_id, candidate.pr_number, input_head, tree_sha)
    if not verifier.verify(oidc_token, run_id=run_id, audience=audience):
        return None
    return input_head, sha


def find_unrecorded_continuation(
    candidate: Candidate,
    checkpoint: str,
    reader: GitHubReader,
    verifier: MarkerVerifier,
) -> str | None:
    if candidate.head_sha == checkpoint:
        return None
    pending = [candidate.head_sha]
    visited: set[str] = set()
    recovered: set[str] = set()
    reached_checkpoint = False
    while pending:
        sha = pending.pop()
        if sha in visited:
            continue
        visited.add(sha)
        if len(visited) > MAX_RECOVERY_COMMITS:
            raise ContinuationError("continuation recovery ancestry exceeds the v0 bound")
        if sha == checkpoint:
            reached_checkpoint = True
            continue
        payload = reader.commit_info(sha)
        recovered_edge = _continuation_commit(payload, candidate, verifier)
        if recovered_edge is not None:
            recovered.add(recovered_edge[1])
        parents = payload.get("parents")
        if not isinstance(parents, list) or not parents:
            continue
        eligible = []
        for parent in parents:
            parent_sha = parent.get("sha") if isinstance(parent, dict) else None
            if not isinstance(parent_sha, str) or not SHA_RE.fullmatch(parent_sha):
                raise ContinuationError("GitHub commit parent is incomplete")
            if parent_sha == checkpoint:
                eligible.append(parent_sha)
                continue
            if reader.compare(checkpoint, parent_sha) in {"ahead", "identical"}:
                eligible.append(parent_sha)
        pending.extend(eligible)
    if not reached_checkpoint:
        raise ContinuationError("checkpoint was not reached during recovery walk")
    if len(recovered) > 1:
        raise ContinuationError("multiple unrecorded continuation commits were found")
    return next(iter(recovered), None)


def build_plan(
    *,
    mode: str,
    repository: str,
    reader: GitHubReader,
    token_present: bool,
    verifier: MarkerVerifier,
) -> Plan:
    normalized_mode = mode.strip().upper()
    if normalized_mode not in MODES:
        raise ContinuationError("continuation mode must be OFF, SHADOW, or EXECUTE_NO_MERGE")
    if normalized_mode == "OFF":
        return Plan("noop", normalized_mode, "mode_off")
    candidate = discover_candidate(repository, reader)
    if candidate is None:
        return Plan("noop", normalized_mode, "no_active_front")
    checkpoint, terminal = checkpoint_for(
        candidate,
        reader.comments(candidate.pr_number),
        verifier=verifier,
    )
    if terminal:
        return Plan(
            "noop", normalized_mode, "head_already_processed", candidate.spec_id,
            candidate.pr_number, candidate.head_ref, candidate.head_sha,
            candidate.base_sha, checkpoint,
        )
    if reader.compare(candidate.base_sha, candidate.head_sha) not in {"ahead", "identical"}:
        raise ContinuationError("current PR head does not descend from the PR base")
    if reader.compare(checkpoint, candidate.head_sha) not in {"ahead", "identical"}:
        raise ContinuationError("current PR head does not descend from the checkpoint")
    recovery_output = find_unrecorded_continuation(
        candidate, checkpoint, reader, verifier
    )
    if recovery_output is not None:
        action = "shadow" if normalized_mode == "SHADOW" else "recover"
        return Plan(
            action, normalized_mode, "unrecorded_push_detected", candidate.spec_id,
            candidate.pr_number, candidate.head_ref, candidate.head_sha,
            candidate.base_sha, checkpoint, recovery_output,
        )
    action = "shadow" if normalized_mode == "SHADOW" else "execute"
    if action == "execute" and not token_present:
        raise ContinuationError("CLAUDE_CODE_OAUTH_TOKEN is not configured")
    return Plan(
        action, normalized_mode, "eligible", candidate.spec_id, candidate.pr_number,
        candidate.head_ref, candidate.head_sha, candidate.base_sha, checkpoint,
    )


def _normalized_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def validate_changed_paths(paths: list[str], active_spec: str) -> None:
    if len(paths) > MAX_CHANGED_FILES:
        raise ContinuationError("continuation patch changes too many files")
    for raw_path in paths:
        path = _normalized_path(raw_path)
        if (
            not path
            or path == ".git"
            or path.startswith(".git/")
            or path.startswith(".github/")
            or path in CONTROL_PATHS
        ):
            raise ContinuationError(f"continuation patch changes a protected path: {raw_path}")
        if path.startswith("docs/specs/") and path != "docs/specs/STATUS.md":
            filename = path.removeprefix("docs/specs/")
            if "/" in filename or not filename.startswith(f"{active_spec.lower()}-"):
                raise ContinuationError(
                    f"continuation patch changes a non-active specification: {raw_path}"
                )
        if path.startswith("backend/tests/") and Path(path).name.startswith("test_") and Path(path).name.endswith("_conformance.py"):
            raise ContinuationError(
                f"continuation patch changes a maintainer-owned conformance test: {raw_path}"
            )
        if SENSITIVE_PART_RE.search(path):
            raise ContinuationError(f"continuation patch changes a sensitive path: {raw_path}")


def validate_status_change(
    before: str, after: str, active_spec: str, active_pr: int
) -> None:
    before_rows, after_rows = parse_registry(before), parse_registry(after)
    if set(before_rows) != set(after_rows) or active_spec not in before_rows:
        raise ContinuationError("continuation may not add or remove registry rows")
    active_after = after_rows[active_spec]
    if active_after.status != "in_review" or active_after.prs != (active_pr,):
        raise ContinuationError(
            "active STATUS.md row must remain in_review and bound to the active PR"
        )
    if active_after.depends_on != before_rows[active_spec].depends_on:
        raise ContinuationError(
            "active STATUS.md dependencies may not change during continuation"
        )
    prefix = f"| {active_spec} |"
    before_lines, after_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    before_indexes = [i for i, line in enumerate(before_lines) if line.startswith(prefix)]
    after_indexes = [i for i, line in enumerate(after_lines) if line.startswith(prefix)]
    if len(before_indexes) != 1 or before_indexes != after_indexes:
        raise ContinuationError("active STATUS.md row is missing, duplicated, or moved")
    index = before_indexes[0]
    if before_lines[:index] != after_lines[:index] or before_lines[index + 1 :] != after_lines[index + 1 :]:
        raise ContinuationError("STATUS.md may change only the exact active spec row")


def _post_comment(repository: str, pr: int, token: str, body: str) -> None:
    if not repository or not token:
        raise ContinuationError("repository and token are required to record a marker")
    payload = json.dumps({"body": body}).encode("utf-8")
    last_error: Exception | None = None
    for _ in range(3):
        request = urllib.request.Request(
            f"{API_ROOT}/repos/{repository}/issues/{pr}/comments", data=payload, method="POST"
        )
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 201:
                    return
                last_error = ContinuationError("checkpoint comment was not created")
        except urllib.error.URLError as exc:
            last_error = exc
    raise ContinuationError(f"checkpoint comment failed after retries: {last_error}")


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
    validate.add_argument("--active-pr", type=int, required=True)
    validate.add_argument("--status-before", type=Path)
    validate.add_argument("--status-after", type=Path)
    marker = commands.add_parser("marker")
    marker.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", ""))
    marker.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""))
    marker.add_argument("--oidc-token", default=os.getenv("CONTINUATION_OIDC_TOKEN", ""))
    marker.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", ""))
    marker.add_argument("--spec", required=True)
    marker.add_argument("--pr", type=int, required=True)
    marker.add_argument("--input-head", required=True)
    marker.add_argument("--output-head", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            reader = RestGitHubReader(args.repository, args.token)
            verifier = GitHubOIDCVerifier(args.repository)
            plan = build_plan(
                mode=args.mode,
                repository=args.repository,
                reader=reader,
                token_present=str(args.claude_token_present).lower() == "true",
                verifier=verifier,
            )
            append_outputs(plan, args.github_output)
            return 0
        if args.command == "validate":
            paths = [line for line in args.changed_files.read_text(encoding="utf-8").splitlines() if line]
            validate_changed_paths(paths, args.active_spec.lower())
            if "docs/specs/STATUS.md" in paths:
                if args.status_before is None or args.status_after is None:
                    raise ContinuationError("STATUS validation inputs are required")
                validate_status_change(
                    args.status_before.read_text(encoding="utf-8"),
                    args.status_after.read_text(encoding="utf-8"),
                    args.active_spec.lower(),
                    args.active_pr,
                )
            return 0
        if not SHA_RE.fullmatch(args.input_head) or not SHA_RE.fullmatch(args.output_head):
            raise ContinuationError("marker heads must be full lowercase SHAs")
        if not args.run_id.isdigit():
            raise ContinuationError("marker run id is invalid")
        verifier = GitHubOIDCVerifier(args.repository)
        audience = marker_audience(
            args.spec, args.pr, args.input_head, args.output_head
        )
        if not verifier.verify(
            args.oidc_token,
            run_id=args.run_id,
            audience=audience,
            require_fresh=True,
        ):
            raise ContinuationError("marker OIDC proof is invalid")
        _post_comment(
            args.repository,
            args.pr,
            args.token,
            marker_text(
                args.spec.lower(), args.pr, args.input_head, args.output_head,
                args.run_id, args.oidc_token,
            ),
        )
        return 0
    except (ContinuationError, OSError) as exc:
        print(f"continuation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
