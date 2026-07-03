"""BLUECAD tool registry loading, resolution, and subprocess execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

REGISTRY_VERSION = "bluecad_tool_registry_v0_1"
_REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_REGISTRY_PATH = _REPO_ROOT / "configs" / "bluecad_tools.yaml"

_TOOL_KEYS = {
    "id",
    "kind",
    "integration_mode",
    "version_pin",
    "license",
    "enabled",
    "entrypoint",
    "binary_sha256",
    "provenance_url",
    "capabilities",
    "health_check",
}
_LICENSE_KEYS = {"spdx", "boundary", "verified_date"}
_KINDS = {"cad_kernel", "mesher", "fem_solver", "cfd_solver", "viewer"}
_MODES = {"in_process", "subprocess", "container"}
_BOUNDARIES = {"A", "B", "C", "D"}
_HASH_MODES = {"subprocess", "container"}
_MINIMAL_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "PYTHONIOENCODING": "utf-8",
}


@dataclass(frozen=True)
class ToolRegistryError(Exception):
    """Structured error raised for fail-closed registry failures."""

    code: str
    message: str
    detail: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class ToolRunResult:
    """Captured tool process result."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    code: str | None = None


ToolEntry = dict[str, Any]
Registry = dict[str, Any]


def _load_raw_registry(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolRegistryError("REGISTRY_NOT_FOUND", f"Registry not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ToolRegistryError("REGISTRY_INVALID", f"Registry is not valid JSON/YAML: {exc}") from exc


def _validate_registry(raw: Any) -> Registry:
    if not isinstance(raw, dict):
        raise ToolRegistryError("REGISTRY_INVALID", "Registry root must be an object")
    unknown_root = set(raw) - {"registry_version", "tools"}
    if unknown_root:
        raise ToolRegistryError("UNKNOWN_FIELD", "Registry contains unknown root fields", {"fields": sorted(unknown_root)})
    if raw.get("registry_version") != REGISTRY_VERSION:
        raise ToolRegistryError("REGISTRY_INVALID", "Registry version is unsupported")
    tools = raw.get("tools")
    if not isinstance(tools, list):
        raise ToolRegistryError("REGISTRY_INVALID", "Registry tools must be a list")

    seen: set[str] = set()
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ToolRegistryError("REGISTRY_INVALID", "Tool entry must be an object", {"index": index})
        unknown = set(tool) - _TOOL_KEYS
        if unknown:
            raise ToolRegistryError("UNKNOWN_FIELD", "Tool entry contains unknown fields", {"index": index, "fields": sorted(unknown)})
        required = {"id", "kind", "integration_mode", "version_pin", "license", "enabled", "entrypoint", "capabilities", "health_check"}
        missing = required - set(tool)
        if missing:
            raise ToolRegistryError("REGISTRY_INVALID", "Tool entry is missing required fields", {"index": index, "fields": sorted(missing)})
        tool_id = tool["id"]
        if not isinstance(tool_id, str) or not tool_id:
            raise ToolRegistryError("REGISTRY_INVALID", "Tool id must be a non-empty string", {"index": index})
        if tool_id in seen:
            raise ToolRegistryError("DUPLICATE_TOOL_ID", "Registry contains duplicate tool ids", {"tool_id": tool_id})
        seen.add(tool_id)
        _validate_tool(tool, index)
    return {"registry_version": raw["registry_version"], "tools": tools}


def _validate_tool(tool: ToolEntry, index: int) -> None:
    if tool["kind"] not in _KINDS:
        raise ToolRegistryError("REGISTRY_INVALID", "Tool kind is unsupported", {"index": index})
    if tool["integration_mode"] not in _MODES:
        raise ToolRegistryError("REGISTRY_INVALID", "Tool integration mode is unsupported", {"index": index})
    if not isinstance(tool["enabled"], bool):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool enabled must be boolean", {"index": index})
    version_pin = tool["version_pin"]
    if not isinstance(version_pin, str) or not version_pin or any(marker in version_pin for marker in "<>=~^*"):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool version_pin must be an exact pin", {"index": index})
    _validate_license(tool["license"], index)
    if tool["entrypoint"] is not None and not isinstance(tool["entrypoint"], str):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool entrypoint must be a string or null", {"index": index})
    if not isinstance(tool["capabilities"], list) or not all(isinstance(item, str) and item for item in tool["capabilities"]):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool capabilities must be non-empty strings", {"index": index})
    if len(tool["capabilities"]) != len(set(tool["capabilities"])):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool capabilities must be unique", {"index": index})
    if tool["health_check"] is not None and not isinstance(tool["health_check"], str):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool health_check must be a string or null", {"index": index})
    if tool["integration_mode"] in _HASH_MODES and tool["enabled"]:
        if not tool["entrypoint"]:
            raise ToolRegistryError("UNHASHED_SUBPROCESS_TOOL", "Enabled subprocess/container tool requires entrypoint", {"tool_id": tool["id"]})
        _validate_hash_field(tool.get("binary_sha256"), tool["id"])
        if not tool.get("provenance_url"):
            raise ToolRegistryError("REGISTRY_INVALID", "Enabled subprocess/container tool requires provenance_url", {"tool_id": tool["id"]})
    elif tool.get("binary_sha256") is not None:
        _validate_hash_field(tool.get("binary_sha256"), tool["id"])


def _validate_license(value: Any, index: int) -> None:
    if not isinstance(value, dict):
        raise ToolRegistryError("REGISTRY_INVALID", "Tool license must be an object", {"index": index})
    unknown = set(value) - _LICENSE_KEYS
    if unknown:
        raise ToolRegistryError("UNKNOWN_FIELD", "Tool license contains unknown fields", {"index": index, "fields": sorted(unknown)})
    missing = _LICENSE_KEYS - set(value)
    if missing:
        raise ToolRegistryError("SPDX_REQUIRED", "Tool license is missing SPDX, boundary, or verified_date", {"index": index, "fields": sorted(missing)})
    if not isinstance(value["spdx"], str) or not value["spdx"]:
        raise ToolRegistryError("SPDX_REQUIRED", "Tool license SPDX must be a non-empty string", {"index": index})
    if value["boundary"] not in _BOUNDARIES:
        raise ToolRegistryError("REGISTRY_INVALID", "Tool license boundary is unsupported", {"index": index})
    try:
        date.fromisoformat(value["verified_date"])
    except (TypeError, ValueError) as exc:
        raise ToolRegistryError("REGISTRY_INVALID", "Tool license verified_date must be an ISO date", {"index": index}) from exc


def _validate_hash_field(value: Any, tool_id: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
        raise ToolRegistryError("UNHASHED_SUBPROCESS_TOOL", "Subprocess/container tool requires a SHA-256 hash", {"tool_id": tool_id})


def load_registry(path: str | Path | None = None) -> Registry:
    """Load and validate a BLUECAD tool registry."""
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    return _validate_registry(_load_raw_registry(registry_path))


def _find_tool(registry: Registry, tool_id: str) -> ToolEntry | None:
    return next((tool for tool in registry["tools"] if tool["id"] == tool_id), None)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_tool(tool_id: str, registry_path: str | Path | None = None) -> ToolEntry:
    """Return an enabled registry entry after fail-closed hash checks."""
    registry = load_registry(registry_path)
    tool = _find_tool(registry, tool_id)
    if tool is None:
        raise ToolRegistryError("TOOL_UNKNOWN", "Tool id is not registered", {"tool_id": tool_id})
    if not tool["enabled"]:
        raise ToolRegistryError("TOOL_DISABLED", "Tool is disabled", {"tool_id": tool_id})
    if tool["integration_mode"] in _HASH_MODES:
        if not tool.get("entrypoint") or not tool.get("binary_sha256"):
            raise ToolRegistryError("UNHASHED_SUBPROCESS_TOOL", "Enabled subprocess/container tool is missing entrypoint or hash", {"tool_id": tool_id})
        entrypoint = Path(tool["entrypoint"])
        if not entrypoint.is_file():
            raise ToolRegistryError("TOOL_BINARY_MISSING", "Tool binary is missing", {"tool_id": tool_id, "entrypoint": str(entrypoint)})
        actual = _sha256_file(entrypoint)
        if actual.lower() != tool["binary_sha256"].lower():
            raise ToolRegistryError("TOOL_HASH_MISMATCH", "Tool binary hash does not match registry", {"tool_id": tool_id})
    return dict(tool)


def run_tool(tool_id: str, args: list[str], cwd: str | Path, timeout: float, registry_path: str | Path | None = None) -> ToolRunResult:
    """Run an enabled subprocess/container registry tool with captured output."""
    tool = resolve_tool(tool_id, registry_path)
    if tool["integration_mode"] not in _HASH_MODES:
        raise ToolRegistryError("TOOL_NOT_SUBPROCESS", "Tool is not configured for subprocess execution", {"tool_id": tool_id})
    command = [tool["entrypoint"], *args]
    try:
        completed = subprocess.run(  # noqa: S603 - command is registry-pinned and hash-verified.
            command,
            cwd=Path(cwd),
            env=_MINIMAL_ENV,
            shell=False,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ToolRunResult(
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            timed_out=True,
            code="TIMEOUT",
        )
    return ToolRunResult(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)


def check_registry(registry_path: str | Path | None = None) -> tuple[int, str]:
    registry = load_registry(registry_path)
    rows = ["tool\tenabled\thash\thealth"]
    exit_code = 0
    for tool in registry["tools"]:
        hash_status = "not-required"
        health_status = "skipped"
        if tool["enabled"]:
            try:
                resolved = resolve_tool(tool["id"], registry_path)
                if resolved["integration_mode"] in _HASH_MODES:
                    hash_status = "ok"
                if resolved.get("health_check"):
                    completed = subprocess.run(  # noqa: S603 - admin-authored registry health check, shell disabled.
                        shlex.split(resolved["health_check"]),
                        env=_MINIMAL_ENV,
                        shell=False,
                        text=True,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                    health_status = "ok" if completed.returncode == 0 else f"failed({completed.returncode})"
                    if completed.returncode != 0:
                        exit_code = 1
                else:
                    health_status = "not-configured"
            except (ToolRegistryError, subprocess.TimeoutExpired, OSError) as exc:
                exit_code = 1
                if isinstance(exc, ToolRegistryError) and exc.code in {"TOOL_HASH_MISMATCH", "TOOL_BINARY_MISSING"}:
                    hash_status = exc.code
                health_status = str(exc)
        rows.append(f"{tool['id']}\t{tool['enabled']}\t{hash_status}\t{health_status}")
    return exit_code, "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BLUECAD tool registry utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check", help="Check registry tool availability")
    check_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    args = parser.parse_args(argv)
    if args.command == "check":
        exit_code, output = check_registry(args.registry)
        print(output)
        return exit_code
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
