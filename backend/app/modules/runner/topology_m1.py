import hashlib
import json
import re
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
CONTRACT_VERSION = "bluerev_process_topology_m1_v0_contract_1"
MANIFEST_FILENAME = "topology_manifest.json"
MANIFEST_ROLE = "bluerev_topology_manifest"
MANIFEST_SCHEMA_VERSION = "bluerev_process_topology_m1_v0_1"


def bundled_script_path() -> Path:
    return Path(__file__).resolve().parent / "examples" / "bluerev_process_topology_m1_v0.py"


def bundled_contract_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "examples"
        / "bluerev_process_topology_m1_v0.contract.json"
    )


def bundled_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "schemas"
        / "bluerev_process_topology_m1_v0_1.schema.json"
    )


def canonical_input_sha256(input_payload: str) -> str:
    parsed = _load_finite_json(input_payload, code="runner_input_invalid")
    if not isinstance(parsed, dict):
        raise RunnerSafetyError("runner_input_invalid", "Topology input payload must be an object.")
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
    *,
    max_bytes: int,
) -> str:
    unresolved_path = output_dir / MANIFEST_FILENAME
    if unresolved_path.is_symlink():
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must be a regular non-symlink file.",
        )
    manifest_path = safe_artifact_path(output_dir, MANIFEST_FILENAME)
    if not manifest_path.exists() or not manifest_path.is_file():
        raise RunnerSafetyError(
            "runner_topology_manifest_missing",
            "Topology model did not produce topology_manifest.json.",
        )
    raw = manifest_path.read_bytes()
    if len(raw) > max_bytes:
        raise RunnerSafetyError(
            "runner_topology_manifest_too_large",
            "Topology manifest exceeds the bounded JSON/artifact limit.",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must be UTF-8 JSON.",
        ) from exc
    manifest = _load_finite_json(text, code="runner_topology_manifest_invalid")
    if not isinstance(manifest, dict):
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology manifest must be an object.",
        )
    canonical_bytes = canonical_json(manifest).encode("utf-8")
    if raw != canonical_bytes:
        raise RunnerSafetyError(
            "runner_topology_manifest_noncanonical",
            "Topology manifest bytes are not the required canonical JSON serialization.",
        )

    schema = _load_finite_json(
        bundled_schema_path().read_text(encoding="utf-8"),
        code="runner_topology_manifest_schema_invalid",
    )
    if not isinstance(schema, dict):
        raise RunnerSafetyError(
            "runner_topology_manifest_schema_invalid",
            "Bundled topology manifest schema must be an object.",
        )
    _validate_schema(manifest, schema)

    expected_inputs = _load_finite_json(input_payload, code="runner_input_invalid")
    if manifest.get("executed_inputs") != expected_inputs:
        raise RunnerSafetyError(
            "runner_topology_manifest_input_mismatch",
            "Topology manifest executed inputs do not match the canonical run input.",
        )
    expected_input_sha = canonical_input_sha256(input_payload)
    if manifest.get("input_payload_sha256") != expected_input_sha:
        raise RunnerSafetyError(
            "runner_topology_manifest_input_mismatch",
            "Topology manifest input digest does not match the canonical run input.",
        )

    model_identity = manifest.get("model_identity")
    if not isinstance(model_identity, dict) or model_identity != {
        "model_id": MODEL_ID,
        "version_label": MODEL_LABEL,
        "input_contract_version": CONTRACT_VERSION,
        "result_schema_version": 1,
    }:
        raise RunnerSafetyError(
            "runner_topology_manifest_identity_mismatch",
            "Topology manifest model or contract identity is invalid.",
        )

    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology result diagnostics are missing.",
        )
    if diagnostics.get("model_id") != MODEL_ID or diagnostics.get("model_label") != MODEL_LABEL:
        raise RunnerSafetyError(
            "runner_topology_manifest_identity_mismatch",
            "Topology result model identity is invalid.",
        )
    if diagnostics.get("input_payload_sha256") != expected_input_sha:
        raise RunnerSafetyError(
            "runner_topology_manifest_input_mismatch",
            "Topology result input digest does not match the canonical run input.",
        )

    raw_sha256 = hashlib.sha256(raw).hexdigest()
    if diagnostics.get("topology_manifest_sha256") != f"sha256:{raw_sha256}":
        raise RunnerSafetyError(
            "runner_topology_manifest_digest_mismatch",
            "Topology result and raw manifest SHA-256 disagree.",
        )
    if diagnostics.get("m0_reduction_status") not in {
        "exact_047_reduction",
        "not_m0_reduction_case",
    }:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology result M0 reduction status is invalid.",
        )
    if diagnostics.get("single_length_projection_status") not in {
        "single_length_representable",
        "not_single_length_representable",
    }:
        raise RunnerSafetyError(
            "runner_topology_manifest_invalid",
            "Topology result single-length projection status is invalid.",
        )
    return raw_sha256


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


def _load_finite_json(text: str, *, code: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"Non-finite JSON constant is forbidden: {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RunnerSafetyError(code, "JSON payload is malformed or non-finite.") from exc


def _validate_schema(instance: object, schema: dict[str, object], path: str = "$") -> None:
    if "const" in schema and instance != schema["const"]:
        _schema_error(path, "value does not match const")
    enum = schema.get("enum")
    if isinstance(enum, list) and instance not in enum:
        _schema_error(path, "value is not in enum")

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _matches_type(instance, expected_type):
        _schema_error(path, f"expected type {expected_type}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in instance]
            if missing:
                _schema_error(path, f"missing required properties: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            _schema_error(path, "schema properties must be an object")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(properties))
            if extra:
                _schema_error(path, f"additional properties are forbidden: {', '.join(extra)}")
        for key, value in instance.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                _validate_schema(value, child_schema, f"{path}.{key}")

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            _schema_error(path, "array is shorter than minItems")
        if isinstance(max_items, int) and len(instance) > max_items:
            _schema_error(path, "array is longer than maxItems")
        if schema.get("uniqueItems") is True:
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(encoded) != len(set(encoded)):
                _schema_error(path, "array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                _validate_schema(value, item_schema, f"{path}[{index}]")

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        pattern = schema.get("pattern")
        if isinstance(min_length, int) and len(instance) < min_length:
            _schema_error(path, "string is shorter than minLength")
        if isinstance(pattern, str) and re.fullmatch(pattern, instance) is None:
            _schema_error(path, "string does not match pattern")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        exclusive_minimum = schema.get("exclusiveMinimum")
        exclusive_maximum = schema.get("exclusiveMaximum")
        if isinstance(minimum, (int, float)) and instance < minimum:
            _schema_error(path, "number is below minimum")
        if isinstance(maximum, (int, float)) and instance > maximum:
            _schema_error(path, "number is above maximum")
        if isinstance(exclusive_minimum, (int, float)) and instance <= exclusive_minimum:
            _schema_error(path, "number is not above exclusiveMinimum")
        if isinstance(exclusive_maximum, (int, float)) and instance >= exclusive_maximum:
            _schema_error(path, "number is not below exclusiveMaximum")


def _matches_type(instance: object, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(instance, dict)
    if expected_type == "array":
        return isinstance(instance, list)
    if expected_type == "string":
        return isinstance(instance, str)
    if expected_type == "boolean":
        return isinstance(instance, bool)
    if expected_type == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected_type == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected_type == "null":
        return instance is None
    return False


def _schema_error(path: str, message: str) -> None:
    raise RunnerSafetyError(
        "runner_topology_manifest_schema_invalid",
        f"Topology manifest schema validation failed at {path}: {message}.",
    )
