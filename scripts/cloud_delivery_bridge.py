#!/usr/bin/env python3
"""Cloud-native exact-head delivery bridge for durable model-produced patches.

The payload is untrusted data. This module parses and admits it, applies it in a
bounded checkout, and delegates the only network Git mutation to the existing
repository_delivery guarded-push primitive. GitHub API reads are deliberately
owned by the workflow plane, not by this repository-delivery primitive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from repository_delivery import (
    DeliveryRefusal,
    RemotePolicy,
    RepositoryDelivery,
    assert_safe_paths,
    github_actions_runner,
)

MARKER = "<!-- jarvis-cloud-delivery:v1 -->"
PATCH_OPEN = "```diff\n"
PATCH_CLOSE = "\n```"
JSON_OPEN = "```json\n"
JSON_CLOSE = "\n```"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
PATH_RE = re.compile(r"^[A-Za-z0-9._/+@=-]+$")
MAX_PATCH_BYTES = 60_000
MAX_PATHS = 32
ALLOWED_PROFILES = {"frontend-143", "frontend", "backend", "docs"}
EXTRA_CONTROL_PATHS = {
    ".gitattributes",
    ".gitmodules",
    "scripts/cloud_delivery_bridge.py",
    "backend/tests/test_cloud_delivery_bridge.py",
    ".github/workflows/cloud-delivery-bridge.yml",
}


class BridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Payload:
    pr: int
    base_sha: str
    target_ref: str
    patch_sha256: str
    changed_paths: tuple[str, ...]
    validation_profile: str
    patch: str


def _die(message: str) -> None:
    print(f"cloud_delivery_bridge: {message}", file=sys.stderr)
    raise SystemExit(2)


def _extract_fence(body: str, opening: str, closing: str, *, start: int = 0) -> str:
    begin = body.find(opening, start)
    if begin < 0:
        raise BridgeError(f"missing {opening.strip()} block")
    begin += len(opening)
    end = body.find(closing, begin)
    if end < 0:
        raise BridgeError("unterminated fenced block")
    return body[begin:end]


def _assert_unambiguous_paths(paths: tuple[str, ...]) -> None:
    for raw in paths:
        if not raw or not PATH_RE.fullmatch(raw) or raw.startswith("/"):
            raise BridgeError("changed_paths contain an ambiguous path")
        parts = raw.split("/")
        if any(part in {"", ".", "..", ".git"} for part in parts):
            raise BridgeError("changed_paths contain an ambiguous path")


def _admitted_profiles_for_paths(paths: tuple[str, ...]) -> set[str]:
    known_prefixes = ("frontend/", "backend/", "scripts/", "docs/")
    unknown = [path for path in paths if not path.startswith(known_prefixes)]
    if unknown:
        raise BridgeError(f"unsupported changed-path class: {unknown[0]}")
    has_frontend = any(path.startswith("frontend/") for path in paths)
    has_backend = any(path.startswith(("backend/", "scripts/")) for path in paths)
    if has_frontend and has_backend:
        raise BridgeError("mixed frontend/backend payload has no admitted fixed profile")
    if has_frontend:
        has_143 = "frontend/tests/143-operator-semantic-ux.mjs" in paths
        return {"frontend-143"} if has_143 else {"frontend", "frontend-143"}
    if has_backend:
        return {"backend"}
    return {"docs"}


def _assert_patch_headers(payload: Payload) -> None:
    headers = [line for line in payload.patch.splitlines() if line.startswith("diff --git ")]
    expected = [f"diff --git a/{path} b/{path}" for path in payload.changed_paths]
    if sorted(headers) != sorted(expected) or len(headers) != len(expected):
        raise BridgeError("patch headers differ from admitted changed_paths")


def parse_payload(body: str) -> Payload:
    if MARKER not in body:
        raise BridgeError("delivery marker missing")
    marker_start = body.index(MARKER)
    metadata_text = _extract_fence(body, JSON_OPEN, JSON_CLOSE, start=marker_start)
    try:
        metadata = json.loads(metadata_text)
    except json.JSONDecodeError as exc:
        raise BridgeError("payload metadata is not valid JSON") from exc
    if not isinstance(metadata, dict) or metadata.get("version") != 1:
        raise BridgeError("unsupported payload version")
    try:
        pr = int(metadata["pr"])
        base_sha = str(metadata["base_sha"]).lower()
        target_ref = str(metadata["target_ref"])
        patch_sha256 = str(metadata["patch_sha256"]).lower()
        changed = tuple(str(item) for item in metadata["changed_paths"])
        profile = str(metadata["validation_profile"])
    except (KeyError, TypeError, ValueError) as exc:
        raise BridgeError("payload metadata is incomplete") from exc
    patch = _extract_fence(body, PATCH_OPEN, PATCH_CLOSE, start=marker_start)
    if pr < 1:
        raise BridgeError("invalid PR number")
    if not SHA_RE.fullmatch(base_sha):
        raise BridgeError("base_sha must be a full lowercase SHA")
    if not SHA256_RE.fullmatch(patch_sha256):
        raise BridgeError("patch_sha256 must be a lowercase sha256")
    if not target_ref or target_ref in {"master", "main"} or target_ref.startswith("refs/"):
        raise BridgeError("protected or invalid target_ref")
    if not BRANCH_RE.fullmatch(target_ref) or ".." in target_ref or target_ref.endswith("/"):
        raise BridgeError("invalid target_ref")
    if profile not in ALLOWED_PROFILES:
        raise BridgeError("validation_profile is not admitted")
    if not changed or len(changed) > MAX_PATHS or len(set(changed)) != len(changed):
        raise BridgeError("changed_paths must be a non-empty unique bounded list")
    _assert_unambiguous_paths(changed)
    patch_bytes = patch.encode("utf-8")
    if len(patch_bytes) > MAX_PATCH_BYTES:
        raise BridgeError("patch exceeds bounded payload size")
    if hashlib.sha256(patch_bytes).hexdigest() != patch_sha256:
        raise BridgeError("patch digest mismatch")
    normalized = assert_safe_paths(list(changed))
    if normalized != tuple(sorted(changed)):
        raise BridgeError("changed_paths must be normalized and sorted")
    denied = set(normalized) & EXTRA_CONTROL_PATHS
    if denied:
        raise BridgeError(f"bridge/control path refused: {sorted(denied)[0]}")
    admitted_profiles = _admitted_profiles_for_paths(normalized)
    if profile not in admitted_profiles:
        raise BridgeError("validation_profile is weaker or unrelated for changed_paths")
    payload = Payload(pr, base_sha, target_ref, patch_sha256, normalized, profile, patch)
    _assert_patch_headers(payload)
    return payload


def admit_acquisition(*, repository: str, pr_number: int, acquisition: dict) -> Payload:
    if "/" not in repository:
        raise BridgeError("workflow repository identity unavailable")
    comment = acquisition.get("comment")
    pr = acquisition.get("pr")
    if not isinstance(comment, dict) or not isinstance(pr, dict):
        raise BridgeError("acquisition record is incomplete")
    issue_url = str(comment.get("issue_url", ""))
    if issue_url.rstrip("/").rsplit("/", 1)[-1] != str(pr_number):
        raise BridgeError("payload comment does not belong to requested PR")
    payload = parse_payload(str(comment.get("body", "")))
    if payload.pr != pr_number:
        raise BridgeError("payload PR binding mismatch")
    if pr.get("state") != "open":
        raise BridgeError("target PR is not open")
    head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
    repo = head.get("repo") if isinstance(head.get("repo"), dict) else {}
    if repo.get("full_name") != repository:
        raise BridgeError("cross-repository PR head refused")
    if head.get("ref") != payload.target_ref:
        raise BridgeError("target ref does not match PR head")
    if head.get("sha") != payload.base_sha:
        raise BridgeError("stale remote head")
    return payload


def _git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    blocked = {
        "GITHUB_TOKEN", "GH_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH",
        "GIT_SSH_COMMAND", "GIT_CONFIG", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
    }
    env = {key: value for key, value in os.environ.items() if key not in blocked}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        ["git", "-c", "core.hooksPath=", "-c", "credential.helper=", *args],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
        timeout=120,
    )
    if check and completed.returncode != 0:
        raise BridgeError(f"git operation failed with exit {completed.returncode}")
    return completed


def _diff_paths(repo_root: Path, base_sha: str) -> tuple[str, ...]:
    tracked = _git(repo_root, ["diff", "--name-only", "--no-renames", base_sha, "--"]).stdout
    untracked = _git(repo_root, ["ls-files", "--others", "--exclude-standard", "--"]).stdout
    return assert_safe_paths(
        [line for line in (tracked + untracked).splitlines() if line.strip()]
    )


def _assert_safe_modes(repo_root: Path, base_sha: str) -> None:
    raw = _git(repo_root, ["diff", "--raw", "--no-renames", base_sha, "--"]).stdout
    for line in raw.splitlines():
        if not line.startswith(":"):
            continue
        fields = line[1:].split(None, 5)
        if len(fields) < 5:
            raise BridgeError("unreadable raw diff mode")
        old_mode, new_mode = fields[0], fields[1]
        if old_mode in {"120000", "160000"} or new_mode in {"120000", "160000"}:
            raise BridgeError("symlink/gitlink mode changes are refused")


def apply_and_verify(repo_root: Path, payload: Payload, patch_file: Path) -> None:
    head = _git(repo_root, ["rev-parse", "HEAD"]).stdout.strip().lower()
    if head != payload.base_sha:
        raise BridgeError("checkout HEAD differs from payload base")
    patch_bytes = patch_file.read_bytes()
    if hashlib.sha256(patch_bytes).hexdigest() != payload.patch_sha256:
        raise BridgeError("artifact patch digest mismatch")
    if patch_bytes.decode("utf-8") != payload.patch:
        raise BridgeError("artifact patch content mismatch")
    _assert_patch_headers(payload)
    check = _git(repo_root, ["apply", "--check", "--binary", str(patch_file)], check=False)
    if check.returncode != 0:
        raise BridgeError("patch does not apply cleanly")
    _git(repo_root, ["apply", "--binary", str(patch_file)])
    actual = _diff_paths(repo_root, payload.base_sha)
    if actual != payload.changed_paths:
        raise BridgeError("applied changed-path set differs from admitted payload")
    _assert_safe_modes(repo_root, payload.base_sha)
    for path in actual:
        if (repo_root / path).is_symlink():
            raise BridgeError("symlink changes are refused")
    if _git(repo_root, ["diff", "--check"], check=False).returncode != 0:
        raise BridgeError("applied patch fails git diff --check")


def write_manifest(payload: Payload, path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "pr": payload.pr,
                "base_sha": payload.base_sha,
                "target_ref": payload.target_ref,
                "patch_sha256": payload.patch_sha256,
                "changed_paths": list(payload.changed_paths),
                "validation_profile": payload.validation_profile,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_manifest(path: Path, patch_path: Path) -> Payload:
    data = json.loads(path.read_text(encoding="utf-8"))
    body = (
        MARKER
        + "\n"
        + JSON_OPEN
        + json.dumps(data)
        + JSON_CLOSE
        + "\n"
        + PATCH_OPEN
        + patch_path.read_text(encoding="utf-8")
        + PATCH_CLOSE
    )
    return parse_payload(body)


def materialize(*, repo_root: Path, payload: Payload, patch_file: Path, token: str, repository: str) -> str:
    if "/" not in repository or not token:
        raise BridgeError("write credential/repository identity unavailable")
    owner, repo = repository.split("/", 1)
    delivery = RepositoryDelivery(
        repo_root,
        remote="origin",
        remote_policy=RemotePolicy(host="github.com", owner=owner, repo=repo),
        runner=github_actions_runner(token),
    )
    observed = delivery.remote_head(payload.target_ref)
    if observed != payload.base_sha:
        raise BridgeError("remote head moved after validation")
    apply_and_verify(repo_root, payload, patch_file)
    _git(repo_root, ["config", "user.name", "JarvisOS Cloud Delivery"])
    _git(repo_root, ["config", "user.email", "jarvisos-cloud-delivery@users.noreply.github.com"])
    _git(repo_root, ["add", "--", *payload.changed_paths])
    staged = tuple(
        sorted(
            line
            for line in _git(
                repo_root, ["diff", "--cached", "--name-only", "--no-renames"]
            ).stdout.splitlines()
            if line.strip()
        )
    )
    if staged != payload.changed_paths:
        raise BridgeError("staged path set differs from admitted payload")
    _git(repo_root, ["commit", "-m", f"materialize durable patch for PR #{payload.pr}"])
    intended = _git(repo_root, ["rev-parse", "HEAD"]).stdout.strip().lower()
    result = delivery.guarded_push(
        branch=payload.target_ref,
        intended_local_commit=intended,
        expected_remote_head=payload.base_sha,
    )
    if result.remote_head != intended:
        raise BridgeError("post-push remote verification mismatch")
    return result.remote_head


def main() -> int:
    parser = argparse.ArgumentParser(description="JarvisOS cloud-native trusted delivery bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    admit = sub.add_parser("admit")
    admit.add_argument("--repository", required=True)
    admit.add_argument("--pr", type=int, required=True)
    admit.add_argument("--acquisition", required=True)
    admit.add_argument("--patch-out", required=True)
    admit.add_argument("--manifest-out", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--repo-root", required=True)
    verify.add_argument("--patch", required=True)
    verify.add_argument("--manifest", required=True)
    write = sub.add_parser("materialize")
    write.add_argument("--repo-root", required=True)
    write.add_argument("--patch", required=True)
    write.add_argument("--manifest", required=True)
    write.add_argument("--repository", required=True)
    write.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()
    try:
        if args.command == "admit":
            acquisition = json.loads(Path(args.acquisition).read_text(encoding="utf-8"))
            if not isinstance(acquisition, dict):
                raise BridgeError("acquisition record must be a JSON object")
            payload = admit_acquisition(
                repository=args.repository,
                pr_number=args.pr,
                acquisition=acquisition,
            )
            Path(args.patch_out).write_text(payload.patch, encoding="utf-8")
            write_manifest(payload, Path(args.manifest_out))
            print(
                json.dumps(
                    {
                        "target_ref": payload.target_ref,
                        "base_sha": payload.base_sha,
                        "profile": payload.validation_profile,
                    }
                )
            )
            return 0
        if args.command == "verify":
            payload = load_manifest(Path(args.manifest), Path(args.patch))
            apply_and_verify(Path(args.repo_root), payload, Path(args.patch))
            print(f"VERIFIED {payload.patch_sha256}")
            return 0
        if args.command == "materialize":
            payload = load_manifest(Path(args.manifest), Path(args.patch))
            final = materialize(
                repo_root=Path(args.repo_root),
                payload=payload,
                patch_file=Path(args.patch),
                token=args.token,
                repository=args.repository,
            )
            print(f"REMOTE_VERIFIED {final}")
            return 0
    except (BridgeError, DeliveryRefusal, OSError, ValueError, json.JSONDecodeError) as exc:
        _die(str(exc))
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())