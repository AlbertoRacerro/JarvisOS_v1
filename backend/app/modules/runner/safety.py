import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any

from app.core.paths import build_paths

MAX_INPUT_JSON_BYTES = 64 * 1024
MAX_OUTPUT_JSON_BYTES = 1024 * 1024
MAX_STDOUT_BYTES = 64 * 1024
MAX_STDERR_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 10 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
MAX_TIMEOUT_SECONDS = 60

REQUIRED_BATCH_GROWTH_PARAMETERS = ("mu_max", "X0", "t_final", "dt")
FORBIDDEN_SCRIPT_MARKERS = (
    "import socket",
    "from socket",
    "import requests",
    "from requests",
    "import httpx",
    "from httpx",
    "import urllib",
    "from urllib",
    "import subprocess",
    "from subprocess",
    "from os import system",
    "os.system",
    "os.popen",
    "popen(",
    "shutil.rmtree",
    "os.remove",
    "os.unlink",
    ".unlink(",
    "rmtree(",
    ".env",
    "os.environ",
    "getenv(",
    "environ[",
    "api_key",
    "api key",
    "password",
    "token",
    "secret",
    "private_key",
    "private key",
)


class RunnerSafetyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def canonical_json(data: dict[str, Any]) -> str:
    try:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RunnerSafetyError("runner_input_invalid", "Input set must be finite JSON.") from exc


def validate_batch_growth_input(input_set: dict[str, Any]) -> tuple[str, str]:
    encoded = canonical_json(input_set)
    if len(encoded.encode("utf-8")) > MAX_INPUT_JSON_BYTES:
        raise RunnerSafetyError("runner_input_too_large", "Input JSON exceeds the V0 runner size limit.")

    schema_version = input_set.get("schema_version", 1)
    if isinstance(schema_version, bool):
        raise RunnerSafetyError("runner_input_invalid", "schema_version must be an integer.")
    try:
        schema_version_number = int(schema_version)
    except (TypeError, ValueError) as exc:
        raise RunnerSafetyError("runner_input_invalid", "schema_version must be an integer.") from exc

    parameters = input_set.get("parameters")
    if not isinstance(parameters, dict):
        raise RunnerSafetyError("runner_input_invalid", "Input set must include a parameters object.")

    input_artifact_ids = input_set.get("input_artifact_ids", [])
    if not isinstance(input_artifact_ids, list) or not all(isinstance(item, str) for item in input_artifact_ids):
        raise RunnerSafetyError("runner_input_invalid", "input_artifact_ids must be a list of artifact id strings.")

    normalized: dict[str, float] = {}
    for key in REQUIRED_BATCH_GROWTH_PARAMETERS:
        if key not in parameters:
            raise RunnerSafetyError("runner_input_invalid", f"Missing required parameter: {key}.")
        value = parameters[key]
        if isinstance(value, bool):
            raise RunnerSafetyError("runner_input_invalid", f"{key} must be numeric.")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise RunnerSafetyError("runner_input_invalid", f"{key} must be numeric.") from exc
        if not isfinite(number):
            raise RunnerSafetyError("runner_input_invalid", f"{key} must be finite.")
        normalized[key] = number

    if normalized["dt"] <= 0:
        raise RunnerSafetyError("runner_input_invalid", "dt must be greater than zero.")
    if normalized["mu_max"] < 0:
        raise RunnerSafetyError("runner_input_invalid", "mu_max must be nonnegative.")
    if normalized["X0"] < 0:
        raise RunnerSafetyError("runner_input_invalid", "X0 must be nonnegative.")
    if normalized["t_final"] < 0:
        raise RunnerSafetyError("runner_input_invalid", "t_final must be nonnegative.")
    if normalized["t_final"] / normalized["dt"] > 10000:
        raise RunnerSafetyError("runner_input_invalid", "The requested time grid is too large for V0.")

    normalized_input = {
        "schema_version": schema_version_number,
        "parameters": normalized,
        "input_artifact_ids": input_artifact_ids,
    }
    return canonical_json(normalized_input), canonical_json(normalized)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_within_directory(path: Path, root: Path, code: str = "runner_path_outside_allowed_root") -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RunnerSafetyError(code, "Path is outside the allowed runner directory.") from exc
    return resolved_path


def model_implementation_root(workspace_id: str) -> Path:
    return build_paths().workspaces_dir / workspace_id / "model_implementations"


def run_root(workspace_id: str, simulation_run_id: str) -> Path:
    return build_paths().workspaces_dir / workspace_id / "runs" / simulation_run_id


def validate_script_path(workspace_id: str, script_path: str) -> Path:
    path = ensure_within_directory(
        Path(script_path),
        model_implementation_root(workspace_id),
        code="runner_script_path_outside_allowed_root",
    )
    if path.suffix.lower() != ".py":
        raise RunnerSafetyError("runner_script_not_python", "Runner script must be a Python file.")
    if not path.exists():
        raise RunnerSafetyError("runner_script_artifact_missing", "Runner script artifact is missing.")
    return path


def validate_run_paths(
    workspace_id: str,
    simulation_run_id: str,
    *,
    working_dir: str,
    input_file: str | None,
    output_dir: str,
) -> tuple[Path, Path, Path]:
    root = run_root(workspace_id, simulation_run_id)
    resolved_root = root.resolve()
    resolved_working_dir = ensure_within_directory(
        Path(working_dir),
        root,
        code="runner_working_dir_outside_run_root",
    )
    resolved_output_dir = ensure_within_directory(
        Path(output_dir),
        root,
        code="runner_output_dir_outside_run_root",
    )
    if input_file is None:
        raise RunnerSafetyError("runner_input_file_missing", "Runner input file path is missing.")
    resolved_input_file = ensure_within_directory(
        Path(input_file),
        root,
        code="runner_input_file_outside_run_root",
    )

    if resolved_working_dir != resolved_root:
        raise RunnerSafetyError("runner_working_dir_invalid", "Runner working directory must match the run root.")
    if resolved_output_dir != resolved_root:
        raise RunnerSafetyError("runner_output_dir_invalid", "Runner output directory must match the run root.")
    if resolved_input_file != resolved_root / "input.json":
        raise RunnerSafetyError("runner_input_file_invalid", "Runner input file must be input.json in the run root.")

    return resolved_working_dir, resolved_input_file, resolved_output_dir


def preflight_script_policy(script_path: Path) -> None:
    text = script_path.read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in FORBIDDEN_SCRIPT_MARKERS:
        if marker in lowered:
            raise RunnerSafetyError("runner_policy_blocked", f"Script contains blocked marker: {marker}.")


def safe_artifact_path(output_dir: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise RunnerSafetyError("runner_artifact_path_outside_output_dir", "Artifact path must be relative.")
    return ensure_within_directory(
        output_dir / relative_path,
        output_dir,
        code="runner_artifact_path_outside_output_dir",
    )
