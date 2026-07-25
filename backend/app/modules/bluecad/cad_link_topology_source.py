"""Exact bundled-072 source authority for CAD-LINK-1."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.core.paths import build_paths
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.spec import SpecValidationError, canonical_json
from app.modules.runner.safety import RunnerSafetyError, sha256_file
from app.modules.runner.service import CALC_V0_IMPLEMENTATION_KIND
from app.modules.runner.topology_m1 import (
    MANIFEST_FILENAME,
    MANIFEST_ROLE,
    MANIFEST_SCHEMA_VERSION,
    is_exact_bundled_profile,
    validate_manifest,
)

GEOMETRY_PARAMETER_INPUTS = (
    "parallel_path_count",
    "branch_illuminated_straight_length",
    "branch_dark_straight_length",
    "branch_bend_count",
    "branch_illuminated_bend_count",
    "branch_bend_centerline_radius",
    "branch_bend_angle",
    "common_supply_length",
    "common_return_length",
    "branch_tube_inner_diameter",
    "branch_tube_outer_diameter",
    "common_tube_inner_diameter",
    "common_tube_outer_diameter",
    "split_manifold_liquid_volume",
    "merge_manifold_liquid_volume",
)
EXPECTED_INPUT_UNITS = {
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


def load_topology_source(
    connection: sqlite3.Connection,
    workspace_id: str,
    simulation_run_id: str,
) -> dict[str, Any]:
    """Load and independently validate the immutable source authority."""

    run = connection.execute(
        "SELECT * FROM simulation_runs WHERE id = ? AND workspace_id = ?",
        (simulation_run_id, workspace_id),
    ).fetchone()
    if run is None:
        raise CadLinkError(
            "cad_link_run_not_found",
            "Source simulation run was not found in the workspace.",
            status_code=404,
        )
    if run["status"] != "succeeded":
        raise CadLinkError(
            "cad_link_run_not_succeeded",
            "Source simulation run is not succeeded.",
            status_code=422,
        )
    _require_fresh(connection, workspace_id, f"simulation_run:{simulation_run_id}")

    jobs = connection.execute(
        "SELECT * FROM runner_jobs WHERE workspace_id = ? AND simulation_run_id = ?",
        (workspace_id, simulation_run_id),
    ).fetchall()
    if len(jobs) != 1 or jobs[0]["status"] != "succeeded":
        raise CadLinkError(
            "cad_link_runner_job_invalid",
            "Source run must own exactly one succeeded runner job.",
            status_code=422,
        )
    job = jobs[0]
    if job["implementation_kind"] != CALC_V0_IMPLEMENTATION_KIND:
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Source runner implementation kind is not the exact bundled topology profile.",
            status_code=422,
        )

    model = connection.execute(
        """
        SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path,
               a.workspace_id AS script_workspace_id, a.status AS script_status
        FROM model_versions mv
        JOIN artifacts a ON a.id = mv.implementation_artifact_id
        WHERE mv.id = ? AND mv.workspace_id = ? AND a.workspace_id = ?
        """,
        (run["model_version_id"], workspace_id, workspace_id),
    ).fetchone()
    if model is None or not is_exact_bundled_profile(model, str(job["script_sha256"])):
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Source model identity or bundled hashes do not match current 072 authority.",
            status_code=422,
        )
    if str(model["script_sha256"]) != str(job["script_sha256"]):
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Source model and runner script identities disagree.",
            status_code=422,
        )
    _validate_model_script_artifact(model)

    artifact_rows = connection.execute(
        """
        SELECT ra.role, ra.artifact_id, a.workspace_id, a.filename, a.stored_path,
               a.artifact_type, a.mime_type, a.sha256, a.source_ref, a.status,
               a.created_at
        FROM run_artifacts ra
        JOIN artifacts a ON a.id = ra.artifact_id
        WHERE ra.workspace_id = ? AND ra.simulation_run_id = ? AND ra.role = ?
        """,
        (workspace_id, simulation_run_id, MANIFEST_ROLE),
    ).fetchall()
    if len(artifact_rows) != 1:
        raise CadLinkError(
            "cad_link_topology_manifest_missing",
            "Source run must own exactly one registered topology manifest.",
            status_code=404 if not artifact_rows else 422,
        )

    manifest, artifact_snapshot = _load_manifest_artifact(
        artifact_rows[0],
        job,
        run,
        workspace_id,
        simulation_run_id,
    )
    parameter_snapshots = _validate_parameter_bindings(
        connection,
        workspace_id,
        manifest,
    )
    _validate_manifest_geometry_agreement(manifest)

    model_identity = {
        "model_version_id": str(model["id"]),
        "implementation_kind": str(model["implementation_kind"]),
        "version_label": str(model["version_label"]),
        "script_sha256": str(model["script_sha256"]),
        "input_contract_sha256": str(model["input_contract_sha256"]),
    }
    source_snapshot = {
        "simulation_run": {
            "id": simulation_run_id,
            "status": str(run["status"]),
            "model_version_id": str(run["model_version_id"]),
            "input_payload_sha256": _digest(
                _json_object(run["input_payload"], "cad_link_topology_manifest_invalid")
            ),
            "output_payload_sha256": _digest(
                _json_object(run["output_payload"], "cad_link_topology_manifest_invalid")
            ),
        },
        "runner_job": {
            "id": str(job["id"]),
            "status": str(job["status"]),
            "implementation_kind": str(job["implementation_kind"]),
            "script_sha256": str(job["script_sha256"]),
        },
        "model_identity": model_identity,
        "topology_manifest": artifact_snapshot,
        "geometry_parameters": parameter_snapshots,
    }
    return {
        "simulation_run_id": simulation_run_id,
        "runner_job_id": str(job["id"]),
        "model_identity": model_identity,
        "manifest_artifact": artifact_snapshot,
        "manifest": manifest,
        "parameter_snapshots": parameter_snapshots,
        "source_snapshot": source_snapshot,
    }


def _load_manifest_artifact(
    artifact: sqlite3.Row,
    job: sqlite3.Row,
    run: sqlite3.Row,
    workspace_id: str,
    simulation_run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        artifact["workspace_id"] != workspace_id
        or artifact["status"] != "registered"
        or artifact["role"] != MANIFEST_ROLE
        or artifact["filename"] != MANIFEST_FILENAME
        or artifact["artifact_type"] != "json"
        or artifact["mime_type"] != "application/json"
        or artifact["source_ref"] != f"simulation_run:{simulation_run_id}"
    ):
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest registration metadata is invalid.",
            status_code=422,
        )

    stored_path = Path(str(artifact["stored_path"]))
    output_dir = Path(str(job["output_dir"]))
    expected_path = output_dir / MANIFEST_FILENAME
    data_root = build_paths().data_root.resolve()
    absolute_stored = stored_path.absolute()
    absolute_output = output_dir.absolute()
    try:
        absolute_stored.relative_to(data_root)
        absolute_output.relative_to(data_root)
        resolved_path = stored_path.resolve(strict=True)
        resolved_output_dir = output_dir.resolve(strict=True)
        resolved_expected_path = expected_path.resolve(strict=True)
        resolved_path.relative_to(data_root)
        resolved_output_dir.relative_to(data_root)
        resolved_expected_path.relative_to(data_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest is outside the trusted runner data root.",
            status_code=422,
        ) from exc
    if (
        stored_path.is_symlink()
        or output_dir.is_symlink()
        or _has_symlink_component(absolute_stored, data_root)
        or _has_symlink_component(absolute_output, data_root)
        or not resolved_path.is_file()
        or resolved_path != resolved_expected_path
    ):
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest path is not the exact immutable runner artifact.",
            status_code=422,
        )

    raw = resolved_path.read_bytes()
    max_bytes = min(int(job["max_output_json_bytes"]), int(job["max_artifact_bytes"]))
    if not raw or len(raw) > max_bytes:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest byte size is outside the trusted bound.",
            status_code=422,
        )
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != str(artifact["sha256"]) or raw_sha != sha256_file(resolved_path):
        raise CadLinkError(
            "cad_link_topology_manifest_digest_mismatch",
            "Topology manifest bytes and registered SHA-256 disagree.",
            status_code=409,
        )

    input_payload = str(run["input_payload"] or "")
    result = _json_object(run["output_payload"], "cad_link_topology_manifest_invalid")
    try:
        validated_sha = validate_manifest(
            resolved_output_dir,
            input_payload,
            result,
            max_bytes=max_bytes,
        )
    except RunnerSafetyError as exc:
        raise _manifest_error(exc) from exc
    if validated_sha != raw_sha:
        raise CadLinkError(
            "cad_link_topology_manifest_digest_mismatch",
            "Topology manifest trusted validator and artifact digest disagree.",
            status_code=409,
        )

    try:
        manifest = json.loads(raw.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest is not finite canonical UTF-8 JSON.",
            status_code=422,
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest schema identity is not the exact bundled 072 schema.",
            status_code=422,
        )

    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology result diagnostics are missing.",
            status_code=422,
        )
    snapshot = {
        "artifact_id": str(artifact["artifact_id"]),
        "role": MANIFEST_ROLE,
        "filename": MANIFEST_FILENAME,
        "byte_size": len(raw),
        "raw_sha256": f"sha256:{raw_sha}",
        "schema_version": manifest["schema_version"],
        "result_diagnostic_digest": diagnostics.get("topology_manifest_sha256"),
        "input_digest": manifest.get("input_payload_sha256"),
        "status": str(artifact["status"]),
        "source_ref": str(artifact["source_ref"]),
    }
    return manifest, snapshot


def _validate_parameter_bindings(
    connection: sqlite3.Connection,
    workspace_id: str,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    inputs = manifest.get("executed_inputs")
    if not isinstance(inputs, Mapping):
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest executed inputs are missing.",
            status_code=422,
        )
    snapshots: dict[str, Any] = {}
    for name in GEOMETRY_PARAMETER_INPUTS:
        item = inputs.get(name)
        if not isinstance(item, Mapping):
            raise CadLinkError(
                "cad_link_parameter_binding_missing",
                f"Geometry input {name} is missing its executed binding.",
                status_code=422,
            )
        source_parameter_id = item.get("source_parameter_id")
        if not isinstance(source_parameter_id, str) or not source_parameter_id:
            raise CadLinkError(
                "cad_link_parameter_binding_missing",
                f"Geometry input {name} requires a source Parameter binding.",
                status_code=422,
            )
        if item.get("unit") != EXPECTED_INPUT_UNITS[name]:
            raise CadLinkError(
                "cad_link_parameter_snapshot_mismatch",
                f"Geometry input {name} has an incompatible executed unit.",
                status_code=409,
            )
        row = connection.execute(
            "SELECT * FROM parameters WHERE id = ? AND workspace_id = ?",
            (source_parameter_id, workspace_id),
        ).fetchone()
        if row is None:
            raise CadLinkError(
                "cad_link_parameter_not_found",
                f"Geometry input {name} references a missing Parameter.",
                status_code=404,
            )
        if row["status"] != "accepted":
            raise CadLinkError(
                "cad_link_parameter_not_accepted",
                f"Geometry input {name} must reference an accepted Parameter.",
                status_code=422,
            )
        _require_fresh(connection, workspace_id, f"parameter:{source_parameter_id}")
        if row["unit"] != item["unit"] or _decimal(row["value"]) != _decimal(item["value"]):
            raise CadLinkError(
                "cad_link_parameter_snapshot_mismatch",
                f"Geometry input {name} no longer matches its Parameter value and unit.",
                status_code=409,
            )
        snapshots[name] = {
            "parameter_id": source_parameter_id,
            "executed_value": _decimal_text(_decimal(item["value"])),
            "current_value": _decimal_text(_decimal(row["value"])),
            "unit": str(row["unit"]),
            "status": str(row["status"]),
            "value_status": str(row["value_status"]),
            "origin": str(row["origin"]),
            "source_ref": row["source_ref"],
            "fresh": True,
        }
    return snapshots


def _validate_model_script_artifact(model: Mapping[str, Any]) -> None:
    script_path = Path(str(model["script_path"]))
    try:
        resolved_path = script_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Bundled topology script artifact is missing or invalid.",
            status_code=422,
        ) from exc
    if (
        model["script_status"] != "registered"
        or script_path.is_symlink()
        or not resolved_path.is_file()
        or sha256_file(resolved_path) != str(model["script_sha256"])
    ):
        raise CadLinkError(
            "cad_link_model_identity_mismatch",
            "Bundled topology script bytes disagree with registered authority.",
            status_code=422,
        )


def _validate_manifest_geometry_agreement(manifest: Mapping[str, Any]) -> None:
    inputs = _mapping(manifest, "executed_inputs")
    symmetry = _mapping(manifest, "symmetry")
    branch = _mapping(manifest, "branch_template")
    illuminated = _mapping(branch, "illuminated_straight")
    dark = _mapping(branch, "dark_straight")
    bends = _mapping(branch, "bend_group")
    totals = _mapping(manifest, "geometry_totals")

    def input_value(name: str) -> float:
        item = inputs.get(name)
        if not isinstance(item, Mapping):
            raise CadLinkError(
                "cad_link_topology_manifest_invalid",
                f"Topology manifest input {name} is missing.",
                status_code=422,
            )
        return float(_decimal(item.get("value")))

    parallel_count_value = input_value("parallel_path_count")
    bend_count_value = input_value("branch_bend_count")
    illuminated_bend_count_value = input_value("branch_illuminated_bend_count")
    if not parallel_count_value.is_integer() or not bend_count_value.is_integer() or not illuminated_bend_count_value.is_integer():
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest integer geometry disagrees with executed inputs.",
            status_code=409,
        )
    parallel_count = int(parallel_count_value)
    bend_count = int(bend_count_value)
    illuminated_bend_count = int(illuminated_bend_count_value)
    dark_bend_count = bend_count - illuminated_bend_count

    illuminated_straight_m = input_value("branch_illuminated_straight_length")
    dark_straight_m = input_value("branch_dark_straight_length")
    bend_radius_m = input_value("branch_bend_centerline_radius") / 1000.0
    bend_angle_deg = input_value("branch_bend_angle")
    bend_arc_each_m = bend_radius_m * math.radians(bend_angle_deg) if bend_count else 0.0
    bend_total_m = bend_count * bend_arc_each_m
    branch_length_each_m = illuminated_straight_m + bend_total_m + dark_straight_m
    common_supply_m = input_value("common_supply_length")
    common_return_m = input_value("common_return_length")
    branch_inner_m = input_value("branch_tube_inner_diameter") / 1000.0
    branch_outer_m = input_value("branch_tube_outer_diameter") / 1000.0
    common_inner_m = input_value("common_tube_inner_diameter") / 1000.0
    common_outer_m = input_value("common_tube_outer_diameter") / 1000.0
    branch_wall_m = (branch_outer_m - branch_inner_m) / 2.0
    common_wall_m = (common_outer_m - common_inner_m) / 2.0

    installed_branch_m = parallel_count * branch_length_each_m
    common_length_m = common_supply_m + common_return_m
    installed_total_m = installed_branch_m + common_length_m
    representative_path_m = common_supply_m + branch_length_each_m + common_return_m
    branch_area_m2 = math.pi * branch_inner_m**2 / 4.0
    common_area_m2 = math.pi * common_inner_m**2 / 4.0
    branch_liquid_total_m3 = parallel_count * branch_area_m2 * branch_length_each_m
    common_supply_volume_m3 = common_area_m2 * common_supply_m
    common_return_volume_m3 = common_area_m2 * common_return_m
    manifold_volume_m3 = (
        input_value("split_manifold_liquid_volume")
        + input_value("merge_manifold_liquid_volume")
    ) / 1000.0
    reservoir_volume_m3 = input_value("reservoir_liquid_volume") / 1000.0
    total_inventory_m3 = (
        branch_liquid_total_m3
        + common_supply_volume_m3
        + common_return_volume_m3
        + manifold_volume_m3
        + reservoir_volume_m3
    )
    illuminated_length_each_m = illuminated_straight_m + illuminated_bend_count * bend_arc_each_m
    dark_length_each_m = dark_straight_m + dark_bend_count * bend_arc_each_m
    illuminated_area_m2 = parallel_count * math.pi * branch_outer_m * illuminated_length_each_m
    dark_area_m2 = parallel_count * math.pi * branch_outer_m * dark_length_each_m
    common_external_area_m2 = math.pi * common_outer_m * common_length_m
    total_external_area_m2 = illuminated_area_m2 + dark_area_m2 + common_external_area_m2
    branch_wall_area_m2 = math.pi * (branch_outer_m**2 - branch_inner_m**2) / 4.0
    common_wall_area_m2 = math.pi * (common_outer_m**2 - common_inner_m**2) / 4.0
    tube_material_volume_m3 = (
        parallel_count * branch_wall_area_m2 * branch_length_each_m
        + common_wall_area_m2 * common_length_m
    )

    exact_counts = (
        (symmetry.get("parallel_path_count"), parallel_count),
        (bends.get("bend_count_each"), bend_count),
        (bends.get("illuminated_bend_count_each"), illuminated_bend_count),
        (bends.get("dark_bend_count_each"), dark_bend_count),
    )
    if any(_decimal(observed) != Decimal(expected) for observed, expected in exact_counts):
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest counts disagree with executed inputs.",
            status_code=409,
        )

    agreements = (
        (illuminated.get("length_m"), illuminated_straight_m),
        (illuminated.get("inner_diameter_m"), branch_inner_m),
        (illuminated.get("outer_diameter_m"), branch_outer_m),
        (illuminated.get("wall_thickness_m"), branch_wall_m),
        (dark.get("length_m"), dark_straight_m),
        (dark.get("inner_diameter_m"), branch_inner_m),
        (dark.get("outer_diameter_m"), branch_outer_m),
        (dark.get("wall_thickness_m"), branch_wall_m),
        (bends.get("centerline_radius_m"), bend_radius_m),
        (bends.get("angle_deg"), bend_angle_deg),
        (bends.get("arc_length_each_m"), bend_arc_each_m),
        (bends.get("total_length_each_m"), bend_total_m),
        (totals.get("branch_centerline_length_each_m"), branch_length_each_m),
        (totals.get("common_supply_length_m"), common_supply_m),
        (totals.get("common_return_length_m"), common_return_m),
        (totals.get("common_inner_diameter_m"), common_inner_m),
        (totals.get("common_outer_diameter_m"), common_outer_m),
        (totals.get("common_wall_thickness_m"), common_wall_m),
        (totals.get("installed_branch_centerline_length_total_m"), installed_branch_m),
        (totals.get("installed_tube_centerline_length_total_m"), installed_total_m),
        (totals.get("representative_hydraulic_path_length_m"), representative_path_m),
        (totals.get("branch_liquid_volume_total_m3"), branch_liquid_total_m3),
        (totals.get("common_supply_liquid_volume_m3"), common_supply_volume_m3),
        (totals.get("common_return_liquid_volume_m3"), common_return_volume_m3),
        (totals.get("manifold_liquid_volume_total_m3"), manifold_volume_m3),
        (totals.get("reservoir_liquid_volume_m3"), reservoir_volume_m3),
        (totals.get("total_liquid_inventory_m3"), total_inventory_m3),
        (totals.get("illuminated_branch_external_area_m2"), illuminated_area_m2),
        (totals.get("dark_branch_external_area_m2"), dark_area_m2),
        (totals.get("common_external_area_m2"), common_external_area_m2),
        (totals.get("tube_external_area_total_m2"), total_external_area_m2),
        (totals.get("tube_material_volume_proxy_m3"), tube_material_volume_m3),
    )
    for observed, expected in agreements:
        actual = float(_decimal(observed))
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15):
            raise CadLinkError(
                "cad_link_topology_manifest_identity_mismatch",
                "Topology manifest geometry disagrees with executed inputs.",
                status_code=409,
            )


def _require_fresh(
    connection: sqlite3.Connection,
    workspace_id: str,
    record_ref: str,
) -> None:
    row = connection.execute(
        "SELECT 1 FROM freshness_marks WHERE workspace_id = ? AND record_ref = ? LIMIT 1",
        (workspace_id, record_ref),
    ).fetchone()
    if row is None:
        return
    code = (
        "cad_link_run_stale"
        if record_ref.startswith("simulation_run:")
        else "cad_link_parameter_stale"
    )
    raise CadLinkError(code, "A required CAD-link source record is stale.", status_code=409)


def _manifest_error(exc: RunnerSafetyError) -> CadLinkError:
    if "missing" in exc.code:
        return CadLinkError(
            "cad_link_topology_manifest_missing",
            "Topology manifest is missing.",
            status_code=404,
        )
    if "digest" in exc.code or "input_mismatch" in exc.code:
        return CadLinkError(
            "cad_link_topology_manifest_digest_mismatch",
            "Topology manifest digests or executed inputs disagree.",
            status_code=409,
        )
    if "identity" in exc.code:
        return CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest identity disagrees with the exact bundled profile.",
            status_code=422,
        )
    return CadLinkError(
        "cad_link_topology_manifest_invalid",
        "Topology manifest failed trusted validation.",
        status_code=422,
    )


def _has_symlink_component(path: Path, root: Path) -> bool:
    current = root
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _json_object(raw: Any, code: str) -> dict[str, Any]:
    try:
        value = json.loads(str(raw), parse_constant=_reject_json_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CadLinkError(
            code,
            "Stored source JSON is malformed or non-finite.",
            status_code=422,
        ) from exc
    if not isinstance(value, dict):
        raise CadLinkError(code, "Stored source JSON must be an object.", status_code=422)
    return value


def _reject_json_constant(value: str) -> object:
    raise ValueError(value)


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            f"Topology manifest field {key} is missing.",
            status_code=422,
        )
    return value


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Source values must be finite numbers.",
            status_code=422,
        )
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Source values must be finite numbers.",
            status_code=422,
        ) from exc
    if not number.is_finite():
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Source values must be finite numbers.",
            status_code=422,
        )
    return number


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def digest(value: Any) -> str:
    try:
        payload = canonical_json(value)
    except SpecValidationError as exc:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Preview evidence contains non-finite or non-JSON values.",
            status_code=422,
        ) from exc
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


_digest = digest
