from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

import glm_worker_harness as harness


# Development-only qualification profile. Keep context small and reserve the
# worker budget for bounded writes and verification rather than broad browsing.
harness.MAX_EVIDENCE_PACKET = 70_000
harness.MAX_TOOL_OUTPUT = 8_000
harness.MODE_EXPLORATION_LIMIT["candidate_patch"] = 1
harness.MODE_WRITE_LIMIT["candidate_patch"] = 16
harness.MODE_VERIFICATION_LIMIT["candidate_patch"] = 10

_ALLOWED_PATHS: tuple[str, ...] = ()
_BASE_REF: str | None = None


def _normalize_repo_path(raw_path: str) -> str:
    normalized = PurePosixPath(raw_path.replace("\\", "/")).as_posix().lstrip("./")
    if not normalized or normalized == "." or normalized.startswith("../"):
        raise ValueError("invalid repository path")
    return normalized


def _path_is_allowed(raw_path: str) -> bool:
    normalized = _normalize_repo_path(raw_path)
    for raw_allowed in _ALLOWED_PATHS:
        allowed = _normalize_repo_path(raw_allowed)
        if normalized == allowed or normalized.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


_original_safe_path = harness._safe_path


def _safe_path_with_allowlist(root: Path, raw_path: str, *, write: bool = False) -> Path:
    path = _original_safe_path(root, raw_path, write=write)
    if write and not _path_is_allowed(raw_path):
        raise ValueError(f"write blocked outside task allowed_paths: {_normalize_repo_path(raw_path)}")
    return path


harness._safe_path = _safe_path_with_allowlist


def _bounded_context_file(root: Path, raw_path: str) -> str:
    path = harness._safe_path(root, raw_path)
    if not path.exists() or not path.is_file():
        return f"===== {raw_path} =====\n[missing at exact target]"

    line_limit = {
        "AGENTS.md": 120,
        "docs/specs/STATUS.md": 75,
    }.get(raw_path, 160)

    text = path.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    lines = all_lines[:line_limit]
    body = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))
    if len(all_lines) > line_limit:
        body += f"\n...[file truncated after {line_limit} lines by bounded entrypoint]"
    return f"===== {raw_path} =====\n{body}"


harness._read_context_file = _bounded_context_file


_original_capture_workspace = harness._capture_workspace


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _changed_inventory(root: Path) -> list[dict[str, object]]:
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-status", "-M", "--"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    inventory: list[dict[str, object]] = []
    for line in result:
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        old_path: str | None = None
        current_path: str | None = None
        if status.startswith("R") and len(parts) >= 3:
            old_path, current_path = parts[1], parts[2]
        elif len(parts) >= 2:
            current_path = parts[1]
        if current_path is None:
            continue
        current = root / current_path
        inventory.append(
            {
                "status": status,
                "old_path": old_path,
                "path": current_path,
                "exists": current.is_file(),
                "sha256": _sha256_file(current) if current.is_file() else None,
                "size": current.stat().st_size if current.is_file() else None,
            }
        )
    return inventory


def _patch_apply_check(root: Path, patch_path: Path) -> dict[str, object]:
    if not patch_path.read_text(encoding="utf-8", errors="replace").strip():
        return {"clean": True, "exit_code": 0, "stderr": "empty patch"}
    with tempfile.TemporaryDirectory(prefix="glm-patch-check-") as tmp:
        clean = Path(tmp) / "clean"
        clone = subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", str(root), str(clean)],
            capture_output=True,
            text=True,
        )
        if clone.returncode != 0:
            return {"clean": False, "exit_code": clone.returncode, "stderr": clone.stderr[-2000:]}
        check = subprocess.run(
            ["git", "-C", str(clean), "apply", "--check", str(patch_path)],
            capture_output=True,
            text=True,
        )
        return {"clean": check.returncode == 0, "exit_code": check.returncode, "stderr": check.stderr[-2000:]}


def _capture_workspace_with_manifest(root: Path, output_dir: Path) -> tuple[str, str]:
    # Ordinary git diff omits untracked files. Mark only task-allowed worker-created
    # paths intent-to-add in the ephemeral checkout so the candidate artifact is
    # complete without creating a commit or remote mutation.
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    untracked = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    for raw_path in untracked:
        harness._safe_path(root, raw_path, write=True)
    if untracked:
        subprocess.run(
            ["git", "-C", str(root), "add", "--intent-to-add", "--", *untracked],
            check=True,
        )

    diff, status = _original_capture_workspace(root, output_dir)
    patch_path = output_dir / "candidate.patch"
    status_path = output_dir / "status.txt"
    target_sha = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = {
        "version": 1,
        "target_sha": target_sha,
        "base_ref": _BASE_REF,
        "allowed_paths": list(_ALLOWED_PATHS),
        "candidate_patch_sha256": _sha256_file(patch_path),
        "status_sha256": _sha256_file(status_path),
        "files": _changed_inventory(root),
        "patch_apply_to_exact_target": _patch_apply_check(root, patch_path),
    }
    (output_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return diff, status


harness._capture_workspace = _capture_workspace_with_manifest


def _terminal_state(output_dir: Path, mode: str, return_code: int) -> dict[str, object]:
    failure_path = output_dir / "failure.json"
    failure: dict[str, object] = {}
    if failure_path.exists():
        failure = json.loads(failure_path.read_text(encoding="utf-8"))
    patch = (output_dir / "candidate.patch").read_text(encoding="utf-8", errors="replace") if (output_dir / "candidate.patch").exists() else ""
    failure_type = str(failure.get("type") or "")
    model_failures = {
        "MaxTurnsExceeded",
        "APITimeoutError",
        "APIConnectionError",
        "RateLimitError",
        "BadRequestError",
        "InternalServerError",
    }
    if return_code == 0 and (mode != "candidate_patch" or patch.strip()):
        state = "candidate_ready"
        reason = "worker completed with captured candidate artifact"
    elif return_code == 0 and mode == "candidate_patch":
        state = "model_failure"
        reason = "candidate_patch task completed without a candidate diff"
    elif failure_type in model_failures:
        state = "model_failure"
        reason = failure_type
    else:
        state = "harness_failure"
        reason = failure_type or "nonzero harness return"
    return {"state": state, "reason": reason, "worker_return_code": return_code, "failure_type": failure_type or None}


async def _main() -> int:
    global _ALLOWED_PATHS, _BASE_REF
    args = harness.parse_args()
    task = json.loads(Path(args.task).read_text(encoding="utf-8"))
    allowed = task.get("allowed_paths")
    if task.get("mode") == "candidate_patch":
        if not isinstance(allowed, list) or not allowed or len(allowed) > 24:
            raise ValueError("candidate_patch task requires allowed_paths list with 1..24 paths")
        _ALLOWED_PATHS = tuple(str(item) for item in allowed)
        for item in _ALLOWED_PATHS:
            _normalize_repo_path(item)
    else:
        _ALLOWED_PATHS = tuple(str(item) for item in (allowed or []))
    _BASE_REF = str(task.get("base_ref")) if task.get("base_ref") else None

    return_code = await harness.run(args)
    output_dir = Path(args.output).resolve()
    terminal = _terminal_state(output_dir, str(task.get("mode", "analysis")), return_code)
    (output_dir / "terminal_state.json").write_text(
        json.dumps(terminal, indent=2, sort_keys=True), encoding="utf-8"
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
