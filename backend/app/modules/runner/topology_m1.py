import hashlib
import json
from pathlib import Path
from typing import Any

from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.safety import (
    RunnerSafetyError,
    canonical_json,
    safe_artifact_path,
    sha256_file,
)

MODEL_ID = "bluerev_process_topology_m1_v0"
MODEL_LABEL = "bluerev-process-topology-m1-v0.1.0"
MANIFEST_FILENAME = "topology_manifest.json"
MANIFEST_ROLE = "bluerev_topology_manifest"
MANIFEST_SCHEMA_VERSION = "0.1"


def bundled_script_path() -> Path:
    return Path(__file__).resolve().parent / "examples" / "bluerev_process_topology_m1_v0.py"


def bundled_contract_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "examples"
        / "bluerev_process_topology_m1_v0.contract.json"
    )


def canonical_input_sha256(input_payload: str) -> str:
    try:
        parsed = json.loads(input_payload)
    except json.JSONDecodeError as exc:
        raise RunnerSafetyError(
            "runner_input_invalid",
            "Topology input payload is invalid JSON.",
        ) from exc
    encoded = canonical_json(parsed)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def expected_contract_sha256() -> str:
    contract = json.loads(bundled_contract_path().read_text(encoding="utf-8"))
    _, digest, _ = canonicalize_input_contract(contract)
    return digest


def is_exact_bundled_profile(model_version: Any, script_sha256: str) -> bool:
    expected_script_sha = sha256_file(bundled_script_path())
    return (
        model_version["implementation_kind"] == "calc_v0"
        and model_version["version_label"] == MODEL_LABEL
        and script_sha256 == expected_script_sha
        and model_version["script_sha256"] == expected_script_sha
        and model_version["input_contract_sha256"] == expected_contract_sha256()
    )


def validate_manifest(
    output_dir: Path,
    input_payload: str,
    result: dict[str, object],
) -> dict[str, object]:
    manifest_path = safe_artifact_path(output_dir, MANIFEST_FILENAME)
    if not manifest_path.exists() or not manifest_path.is_file():
        raise RunnerSafetyError(
            "runner_topology_manifest_missing",
            "Topology model did not produce topology_manifest.json.",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest is not valid JSON.",
        ) from exc
    if not isinstance(manifest, dict):
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must be an object.",
        )
    required = {
        "schema_version",
        "model_id",
        "model_label",
        "input_sha256",
        "topology",
        "summary",
        "limitations",
        "topology_digest",
    }
    if set(manifest) != required:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest fields do not match the closed schema.",
        )
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest schema version is invalid.",
        )
    if manifest["model_id"] != MODEL_ID or manifest["model_label"] != MODEL_LABEL:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest model identity is invalid.",
        )
    expected_input_sha = canonical_input_sha256(input_payload)
    if manifest["input_sha256"] != expected_input_sha:
        raise RunnerSafetyError(
            "runner_topology_manifest_input_mismatch",
            "Topology manifest input digest does not match the run input.",
        )
    digest = manifest.get("topology_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest digest is invalid.",
        )
    unsigned = dict(manifest)
    unsigned.pop("topology_digest")
    expected_digest = hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()
    if digest != expected_digest:
        raise RunnerSafetyError(
            "runner_topology_manifest_digest_mismatch",
            "Topology manifest digest verification failed.",
        )
    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology result diagnostics are missing.",
        )
    if diagnostics.get("model_id") != MODEL_ID or diagnostics.get("model_label") != MODEL_LABEL:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology result model identity is invalid.",
        )
    if diagnostics.get("input_sha256") != expected_input_sha:
        raise RunnerSafetyError(
            "runner_topology_manifest_input_mismatch",
            "Topology result input digest does not match the run input.",
        )
    if diagnostics.get("topology_digest") != digest:
        raise RunnerSafetyError(
            "runner_topology_manifest_digest_mismatch",
            "Topology result and manifest digests disagree.",
        )
    topology = manifest.get("topology")
    if not isinstance(topology, dict) or topology.get("loop_count") != 1:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must contain exactly one loop.",
        )
    path_count = topology.get("parallel_path_count")
    if (
        isinstance(path_count, bool)
        or not isinstance(path_count, int)
        or not 1 <= path_count <= 12
    ):
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology path count is invalid.",
        )
    components = topology.get("components")
    if not isinstance(components, list) or len(components) != 8:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must contain the fixed eight component records.",
        )
    return manifest


def runner_owned_artifacts() -> list[dict[str, str]]:
    return [
        {
            "path": "result.json",
            "role": "calc_result_json",
            "artifact_type": "json",
            "mime_type": "application/json",
        },
        {
            "path": MANIFEST_FILENAME,
            "role": MANIFEST_ROLE,
            "artifact_type": "json",
            "mime_type": "application/json",
        },
    ]
