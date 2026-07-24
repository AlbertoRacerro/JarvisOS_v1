"""Read-only authority checks for the 072 M1 topology CAD link."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.core.paths import build_paths
from app.modules.bluecad.cad_link_topology_m1 import TopologyCadLinkError
from app.modules.bluecad.spec import canonical_json
from app.modules.runner.safety import sha256_file
from app.modules.runner.topology_m1 import (
    CONTRACT_VERSION,
    MANIFEST_ROLE,
    MANIFEST_SCHEMA_VERSION,
    MODEL_ID,
    MODEL_LABEL,
    _load_finite_json,
    _validate_schema,
    bundled_schema_path,
    bundled_script_path,
    canonical_input_sha256,
    expected_contract_sha256,
)

GEOMETRY_INPUT_UNITS = {
    "parallel_path_count": "1",
    "branch_illuminated_straight_length": "m",
    "branch_dark_straight_length": "m",
    "branch_bend_count": "1",
    "branch_illuminated_bend_count": "1",
    "branch_bend_centerline_radius": "mm",
    "branch_bend_angle": "deg",
    "common_supply_length": "m",
    "common_return_length": "m",
    "branch_tube_inner_diameter": "mm",
    "branch_tube_outer_diameter": "mm",
    "common_tube_inner_diameter": "mm",
    "common_tube_outer_diameter": "mm",
    "split_manifold_liquid_volume": "L",
    "merge_manifold_liquid_volume": "L",
}


def load_verified_topology_source(
    connection: sqlite3.Connection,
    workspace_id: str,
    simulation_run_id: str,
) -> dict[str, Any]:
    """Load one exact fresh bundled-072 run and its immutable manifest authority."""

    if connection.execute(
        "SELECT id FROM workspaces WHERE id = ?", (workspace_id,)
    ).fetchone() is None:
        _fail("cad_link_run_not_found", "Workspace or source run was not found.")

    run = connection.execute(
        "SELECT * FROM simulation_runs WHERE id = ? AND workspace_id = ?",
        (simulation_run_id, workspace_id),
    ).fetchone()
    if run is None:
        _fail("cad_link_run_not_found", "Source simulation run was not found.")
    if str(run["status"]) != "succeeded":
        _fail("cad_link_run_not_succeeded", "Source simulation run must have succeeded.")
    _require_fresh(connection, workspace_id, f"simulation_run:{simulation_run_id}")

    jobs = connection.execute(
        """
        SELECT * FROM runner_jobs
        WHERE simulation_run_id = ? AND workspace_id = ?
        ORDER BY created_at ASC
        """,
        (simulation_run_id, workspace_id),
    ).fetchall()
    if len(jobs) != 1 or str(jobs[0]["status"]) != "succeeded":
        _fail(
            "cad_link_runner_job_invalid",
            "Source run must have exactly one succeeded runner job.",
        )
    job = jobs[0]

    model = connection.execute(
        """
        SELECT mv.*, a.sha256 AS script_sha256
        FROM model_versions mv
        JOIN artifacts a ON a.id = mv.implementation_artifact_id
        WHERE mv.id = ? AND mv.workspace_id = ?
        """,
        (run["model_version_id"], workspace_id),
    ).fetchone()
    if model is None:
        _fail("cad_link_model_identity_mismatch", "Bundled-072 model identity is missing.")
    model_identity = _verify_model_identity(model, job)

    input_payload = _json_object(run["input_payload"], "cad_link_topology_manifest_invalid")
    output_payload = _json_object(run["output_payload"], "cad_link_topology_manifest_invalid")

    artifact_rows = connection.execute(
        """
        SELECT ra.role, a.*
        FROM run_artifacts ra
        JOIN artifacts a ON a.id = ra.artifact_id
        WHERE ra.workspace_id = ?
          AND ra.simulation_run_id = ?
          AND ra.role = ?
        ORDER BY a.created_at ASC
        """,
        (workspace_id, simulation_run_id, MANIFEST_ROLE),
    ).fetchall()
    if len(artifact_rows) != 1:
        _fail(
            "cad_link_topology_manifest_missing",
            "Source run must own exactly one topology manifest artifact.",
        )
    artifact = artifact_rows[0]
    manifest, artifact_metadata = _validate_manifest_artifact(
        artifact,
        simulation_run_id=simulation_run_id,
        input_payload=input_payload,
        output_payload=output_payload,
        max_bytes=int(job["max_artifact_bytes"]),
    )
    parameter_snapshot = _validate_parameter_bindings(
        connection,
        workspace_id,
        input_payload,
    )

    source_snapshot = {
        "source_simulation_run_id": simulation_run_id,
        "source_runner_job_id": str(job["id"]),
        "model_identity": model_identity,
        "topology_manifest": artifact_metadata,
        "geometry_parameters": parameter_snapshot,
        "input_payload_digest": _digest(input_payload),
        "output_payload_digest": _digest(output_payload),
    }
    return {
        "source_simulation_run_id": simulation_run_id,
        "source_runner_job_id": str(job["id"]),
        "model_identity": model_identity,
        "manifest": manifest,
        "manifest_artifact": artifact_metadata,
        "parameter_snapshot": parameter_snapshot,
        "source_snapshot": source_snapshot,
        "source_snapshot_digest": _digest(source_snapshot),
        "input_payload": input_payload,
        "output_payload": output_payload,
    }


def _verify_model_identity(model: sqlite3.Row, job: sqlite3.Row) -> dict[str, Any]:
    expected_script_sha = sha256_file(bundled_script_path())
    identity = {
        "model_version_id": str(model["id"]),
        "model_id": MODEL_ID,
        "version_label": str(model["version_label"]),
        "implementation_kind": str(model["implementation_kind"]),
        "script_sha256": str(model["script_sha256"]),
        "input_contract_sha256": model["input_contract_sha256"],
        "input_contract_version": CONTRACT_VERSION,
    }
    valid = (
        identity["version_label"] == MODEL_LABEL
        and identity["implementation_kind"] == "calc_v0"
        and identity["script_sha256"] == expected_script_sha
        and identity["input_contract_sha256"] == expected_contract_sha256()
        and str(job["implementation_kind"]) == "calc_v0"
        and str(job["script_sha256"]) == expected_script_sha
    )
    if not valid:
        _fail(
            "cad_link_model_identity_mismatch",
            "Source run is not the current verified bundled-072 implementation.",
        )
    return identity


def _validate_manifest_artifact(
    artifact: sqlite3.Row,
    *,
    simulation_run_id: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    max_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if str(artifact["source_ref"]) != f"simulation_run:{simulation_run_id}":
        _fail(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest artifact is not associated with the exact source run.",
        )
    if str(artifact["artifact_type"]) != "json" or str(artifact["mime_type"]) != "application/json":
        _fail("cad_link_topology_manifest_invalid", "Topology manifest artifact type is invalid.")

    unresolved = Path(str(artifact["stored_path"]))
    if unresolved.is_symlink():
        _fail("cad_link_topology_manifest_invalid", "Topology manifest must not be a symlink.")
    path = unresolved.resolve()
    data_root = build_paths().data_root.resolve()
    try:
        path.relative_to(data_root)
    except ValueError as exc:
        raise TopologyCadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest is outside the managed data root.",
        ) from exc
    if not path.exists() or not path.is_file():
        _fail("cad_link_topology_manifest_missing", "Topology manifest file is missing.")

    raw = path.read_bytes()
    if len(raw) > max_bytes:
        _fail("cad_link_topology_manifest_invalid", "Topology manifest exceeds the runner bound.")
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != str(artifact["sha256"]):
        _fail(
            "cad_link_topology_manifest_digest_mismatch",
            "Topology manifest bytes do not match artifact metadata.",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TopologyCadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest must be UTF-8 JSON.",
        ) from exc
    parsed = _load_finite_json(text, code="cad_link_topology_manifest_invalid")
    if not isinstance(parsed, dict):
        _fail("cad_link_topology_manifest_invalid", "Topology manifest must be an object.")
    if raw != canonical_json(parsed).encode("utf-8"):
        _fail("cad_link_topology_manifest_invalid", "Topology manifest bytes are non-canonical.")

    schema = _load_finite_json(
        bundled_schema_path().read_text(encoding="utf-8"),
        code="cad_link_topology_manifest_invalid",
    )
    if not isinstance(schema, dict):
        _fail("cad_link_topology_manifest_invalid", "Bundled topology schema is invalid.")
    try:
        _validate_schema(parsed, schema)
    except Exception as exc:
        raise TopologyCadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest does not match the bundled schema.",
        ) from exc

    if parsed.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest schema identity is invalid.")
    if parsed.get("topology_kind") != "symmetric_parallel_closed_loop":
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest topology identity is invalid.")
    if parsed.get("executed_inputs") != input_payload:
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest inputs differ from the source run.")
    expected_input_sha = canonical_input_sha256(canonical_json(input_payload))
    if parsed.get("input_payload_sha256") != expected_input_sha:
        _fail("cad_link_topology_manifest_digest_mismatch", "Topology manifest input digest is invalid.")
    if parsed.get("model_identity") != {
        "model_id": MODEL_ID,
        "version_label": MODEL_LABEL,
        "input_contract_version": CONTRACT_VERSION,
        "result_schema_version": 1,
    }:
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest model identity is invalid.")

    diagnostics = output_payload.get("diagnostics")
    if not isinstance(diagnostics, dict):
        _fail("cad_link_topology_manifest_invalid", "Topology result diagnostics are missing.")
    if diagnostics.get("topology_manifest_sha256") != f"sha256:{raw_sha}":
        _fail("cad_link_topology_manifest_digest_mismatch", "Topology result digest differs from the manifest.")
    if diagnostics.get("input_payload_sha256") != expected_input_sha:
        _fail("cad_link_topology_manifest_digest_mismatch", "Topology result input digest is invalid.")
    if diagnostics.get("model_id") != MODEL_ID or diagnostics.get("model_label") != MODEL_LABEL:
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology result model identity is invalid.")

    metadata = {
        "artifact_id": str(artifact["id"]),
        "role": MANIFEST_ROLE,
        "filename": str(artifact["filename"]),
        "artifact_type": str(artifact["artifact_type"]),
        "mime_type": str(artifact["mime_type"]),
        "size_bytes": len(raw),
        "raw_sha256": raw_sha,
        "artifact_sha256": str(artifact["sha256"]),
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "input_payload_sha256": expected_input_sha,
        "result_manifest_digest": str(diagnostics["topology_manifest_sha256"]),
        "source_ref": str(artifact["source_ref"]),
    }
    return parsed, metadata


def _validate_parameter_bindings(
    connection: sqlite3.Connection,
    workspace_id: str,
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for name, expected_unit in GEOMETRY_INPUT_UNITS.items():
        item = input_payload.get(name)
        if not isinstance(item, dict):
            _fail("cad_link_parameter_binding_missing", f"Geometry input {name} is missing.")
        parameter_id = item.get("source_parameter_id")
        if not isinstance(parameter_id, str) or not parameter_id:
            _fail(
                "cad_link_parameter_binding_missing",
                f"Geometry input {name} is not backed by a canonical Parameter.",
            )
        if item.get("unit") != expected_unit:
            _fail("cad_link_parameter_snapshot_mismatch", f"Geometry input {name} has an invalid unit.")

        parameter = connection.execute(
            "SELECT * FROM parameters WHERE id = ? AND workspace_id = ?",
            (parameter_id, workspace_id),
        ).fetchone()
        if parameter is None:
            _fail("cad_link_parameter_not_found", f"Source Parameter for {name} was not found.")
        if str(parameter["status"]) != "accepted":
            _fail("cad_link_parameter_not_accepted", f"Source Parameter for {name} is not accepted.")
        _require_fresh(connection, workspace_id, f"parameter:{parameter_id}")

        executed = _decimal(item.get("value"))
        current = _decimal(parameter["value"])
        if current != executed or str(parameter["unit"]) != expected_unit:
            _fail(
                "cad_link_parameter_snapshot_mismatch",
                f"Source Parameter for {name} differs from the executed snapshot.",
            )
        snapshot[name] = {
            "parameter_ref": f"parameter:{parameter_id}",
            "name": str(parameter["name"]),
            "executed_value": _decimal_text(executed),
            "current_value": _decimal_text(current),
            "unit": expected_unit,
            "status": str(parameter["status"]),
            "origin": str(parameter["origin"]),
            "source_ref": parameter["source_ref"],
            "freshness": "fresh",
        }
    return snapshot


def _require_fresh(connection: sqlite3.Connection, workspace_id: str, record_ref: str) -> None:
    if connection.execute(
        "SELECT 1 FROM freshness_marks WHERE workspace_id = ? AND record_ref = ? LIMIT 1",
        (workspace_id, record_ref),
    ).fetchone() is not None:
        code = "cad_link_run_stale" if record_ref.startswith("simulation_run:") else "cad_link_parameter_stale"
        _fail(code, "A CAD-link source record is stale.")


def _json_object(raw: Any, code: str) -> dict[str, Any]:
    try:
        parsed = json.loads(str(raw), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TopologyCadLinkError(code, "Stored source JSON is invalid.") from exc
    if not isinstance(parsed, dict):
        _fail(code, "Stored source JSON must be an object.")
    return parsed


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        _fail("cad_link_parameter_snapshot_mismatch", "Parameter values must be finite numbers.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TopologyCadLinkError(
            "cad_link_parameter_snapshot_mismatch",
            "Parameter values must be finite numbers.",
        ) from exc
    if not number.is_finite():
        _fail("cad_link_parameter_snapshot_mismatch", "Parameter values must be finite numbers.")
    return number


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _fail(code: str, message: str) -> None:
    raise TopologyCadLinkError(code, message)
