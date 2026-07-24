"""Zero-write preview for the exact bundled-072 topology CAD link."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology_contract import (
    IMPLEMENTATION_VERSION,
    TRANSFORMATION_VERSION,
    canonicalize_layout,
    input_decimal,
    input_int,
    resolve_geometry_spec,
)
from app.modules.bluecad.cad_link_topology_preflight import run_kernel_preflight
from app.modules.bluecad.models import BluecadLoopConfig
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
TOLERANCES = {
    "dimension_absolute_mm": 1e-9,
    "dimension_relative": 1e-12,
    "length_absolute_mm": 1e-9,
    "measure_relative": 1e-9,
    "area_absolute_m2": 1e-12,
    "volume_absolute_m3": 1e-12,
}


class CadLink072PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_simulation_run_id: str = Field(min_length=1, max_length=256)
    layout_spec: dict[str, Any]
    analysis_spec: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_analysis_spec(self) -> CadLink072PreviewRequest:
        if self.analysis_spec is not None:
            BluecadLoopConfig(analysis_spec=self.analysis_spec)
        return self


def preview_cad_link_072(
    workspace_id: str,
    payload: CadLink072PreviewRequest,
) -> dict[str, Any]:
    """Resolve the exact 072 topology into bounded preview evidence with zero writes."""

    with open_sqlite_connection() as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        try:
            preview = _build_preview(connection, workspace_id, payload)
        finally:
            connection.rollback()
    return preview


def _build_preview(
    connection: sqlite3.Connection,
    workspace_id: str,
    payload: CadLink072PreviewRequest,
) -> dict[str, Any]:
    source = _load_source(
        connection,
        workspace_id,
        payload.source_simulation_run_id,
    )
    layout = canonicalize_layout(source["manifest"], payload.layout_spec)
    resolved_spec, boundaries, component_inventory = resolve_geometry_spec(
        source["manifest"],
        layout,
    )
    preflight = run_kernel_preflight(resolved_spec, boundaries)
    reconciliation = _reconcile(
        source["manifest"],
        layout,
        resolved_spec,
        preflight,
    )
    analysis_contract = _canonical_analysis_contract(payload.analysis_spec)

    source_snapshot_digest = _digest(source["source_snapshot"])
    source_model_identity_digest = _digest(source["model_identity"])
    layout_digest = _digest(layout)
    resolved_spec_digest = str(resolved_spec["spec_id"])
    preflight_digest = _digest(preflight)
    reconciliation_digest = _digest(reconciliation)
    analysis_contract_digest = _digest(analysis_contract)

    preview: dict[str, Any] = {
        "workspace_id": workspace_id,
        "source_simulation_run_id": source["simulation_run_id"],
        "source_runner_job_id": source["runner_job_id"],
        "source_model_identity": source["model_identity"],
        "source_model_identity_digest": source_model_identity_digest,
        "source_topology_manifest": source["manifest_artifact"],
        "source_geometry_parameters": source["parameter_snapshots"],
        "source_snapshot": source["source_snapshot"],
        "source_snapshot_digest": source_snapshot_digest,
        "layout_spec": layout,
        "layout_digest": layout_digest,
        "transformation_version": TRANSFORMATION_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "resolved_spec": resolved_spec,
        "spec_id": resolved_spec["spec_id"],
        "resolved_spec_digest": resolved_spec_digest,
        "resolved_part_count": len(resolved_spec["parts"]),
        "resolved_connection_count": len(resolved_spec.get("connections", [])),
        "external_boundaries": boundaries,
        "component_inventory": component_inventory,
        "kernel_preflight": preflight,
        "kernel_preflight_digest": preflight_digest,
        "tolerances": dict(TOLERANCES),
        "reconciliation": reconciliation,
        "reconciliation_digest": reconciliation_digest,
        "analysis_contract": analysis_contract,
        "analysis_contract_digest": analysis_contract_digest,
    }
    preview["preview_digest"] = _digest(preview)
    return preview


def _load_source(
    connection: sqlite3.Connection,
    workspace_id: str,
    simulation_run_id: str,
) -> dict[str, Any]:
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
               a.workspace_id AS script_workspace_id
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
    artifact = artifact_rows[0]
    manifest, artifact_snapshot = _load_manifest_artifact(
        artifact,
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
            "input_payload_sha256": _digest(_json_object(run["input_payload"], "cad_link_topology_manifest_invalid")),
            "output_payload_sha256": _digest(_json_object(run["output_payload"], "cad_link_topology_manifest_invalid")),
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
    try:
        resolved_path = stored_path.resolve(strict=True)
        resolved_output_dir = output_dir.resolve(strict=True)
        resolved_path.relative_to(data_root)
        resolved_output_dir.relative_to(data_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest is outside the trusted runner data root.",
            status_code=422,
        ) from exc
    if (
        stored_path.is_symlink()
        or not resolved_path.is_file()
        or resolved_path != expected_path.resolve()
        or _has_symlink_component(resolved_path, data_root)
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
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest is not canonical UTF-8 JSON.",
            status_code=422,
        ) from exc
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
        "schema_version": manifest.get("schema_version"),
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


def _validate_manifest_geometry_agreement(manifest: Mapping[str, Any]) -> None:
    branch = _mapping(manifest, "branch_template")
    illuminated = _mapping(branch, "illuminated_straight")
    dark = _mapping(branch, "dark_straight")
    bends = _mapping(branch, "bend_group")
    totals = _mapping(manifest, "geometry_totals")
    agreements = (
        (illuminated.get("inner_diameter_m"), input_decimal(manifest, "branch_tube_inner_diameter") / Decimal(1000)),
        (illuminated.get("outer_diameter_m"), input_decimal(manifest, "branch_tube_outer_diameter") / Decimal(1000)),
        (dark.get("inner_diameter_m"), input_decimal(manifest, "branch_tube_inner_diameter") / Decimal(1000)),
        (dark.get("outer_diameter_m"), input_decimal(manifest, "branch_tube_outer_diameter") / Decimal(1000)),
        (bends.get("centerline_radius_m"), input_decimal(manifest, "branch_bend_centerline_radius") / Decimal(1000)),
        (bends.get("angle_deg"), input_decimal(manifest, "branch_bend_angle")),
        (totals.get("common_inner_diameter_m"), input_decimal(manifest, "common_tube_inner_diameter") / Decimal(1000)),
        (totals.get("common_outer_diameter_m"), input_decimal(manifest, "common_tube_outer_diameter") / Decimal(1000)),
        (totals.get("common_supply_length_m"), input_decimal(manifest, "common_supply_length")),
        (totals.get("common_return_length_m"), input_decimal(manifest, "common_return_length")),
    )
    if any(_decimal(observed) != expected for observed, expected in agreements):
        raise CadLinkError(
            "cad_link_topology_manifest_identity_mismatch",
            "Topology manifest metre geometry disagrees with executed input units.",
            status_code=409,
        )


def _reconcile(
    manifest: Mapping[str, Any],
    layout: Mapping[str, Any],
    resolved_spec: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    path_count = input_int(manifest, "parallel_path_count")
    branch_inner_mm = float(input_decimal(manifest, "branch_tube_inner_diameter"))
    branch_outer_mm = float(input_decimal(manifest, "branch_tube_outer_diameter"))
    common_inner_mm = float(input_decimal(manifest, "common_tube_inner_diameter"))
    common_outer_mm = float(input_decimal(manifest, "common_tube_outer_diameter"))
    branch_wall_mm = (branch_outer_mm - branch_inner_mm) / 2.0
    common_wall_mm = (common_outer_mm - common_inner_mm) / 2.0
    bend_radius_m = float(input_decimal(manifest, "branch_bend_centerline_radius")) / 1000.0
    bend_angle_rad = math.radians(float(input_decimal(manifest, "branch_bend_angle")))
    bend_arc_m = bend_radius_m * bend_angle_rad

    steps = layout["branch_route"]["steps"]
    illuminated_straight_m = sum(
        float(step["length_mm"]) / 1000.0
        for step in steps
        if step["kind"] == "straight" and step["illumination"] == "illuminated"
    )
    dark_straight_m = sum(
        float(step["length_mm"]) / 1000.0
        for step in steps
        if step["kind"] == "straight" and step["illumination"] == "dark"
    )
    bend_count = sum(step["kind"] == "bend" for step in steps)
    illuminated_bends = sum(
        step["kind"] == "bend" and step["illumination"] == "illuminated"
        for step in steps
    )
    illuminated_length_m = illuminated_straight_m + illuminated_bends * bend_arc_m
    dark_length_m = dark_straight_m + (bend_count - illuminated_bends) * bend_arc_m
    branch_length_each_m = illuminated_length_m + dark_length_m
    supply_m = float(input_decimal(manifest, "common_supply_length"))
    return_m = float(input_decimal(manifest, "common_return_length"))
    installed_branch_m = path_count * branch_length_each_m
    installed_total_m = installed_branch_m + supply_m + return_m
    representative_path_m = supply_m + branch_length_each_m + return_m

    branch_inner_area_m2 = math.pi * (branch_inner_mm / 1000.0) ** 2 / 4.0
    common_inner_area_m2 = math.pi * (common_inner_mm / 1000.0) ** 2 / 4.0
    branch_annulus_m2 = math.pi * (
        (branch_outer_mm / 1000.0) ** 2 - (branch_inner_mm / 1000.0) ** 2
    ) / 4.0
    common_annulus_m2 = math.pi * (
        (common_outer_mm / 1000.0) ** 2 - (common_inner_mm / 1000.0) ** 2
    ) / 4.0
    branch_liquid_each_m3 = branch_inner_area_m2 * branch_length_each_m
    branch_liquid_total_m3 = branch_liquid_each_m3 * path_count
    supply_liquid_m3 = common_inner_area_m2 * supply_m
    return_liquid_m3 = common_inner_area_m2 * return_m
    tube_liquid_total_m3 = branch_liquid_total_m3 + supply_liquid_m3 + return_liquid_m3
    illuminated_area_m2 = path_count * math.pi * (branch_outer_mm / 1000.0) * illuminated_length_m
    dark_area_m2 = path_count * math.pi * (branch_outer_mm / 1000.0) * dark_length_m
    common_area_m2 = math.pi * (common_outer_mm / 1000.0) * (supply_m + return_m)
    tube_area_total_m2 = illuminated_area_m2 + dark_area_m2 + common_area_m2
    tube_material_m3 = branch_annulus_m2 * installed_branch_m + common_annulus_m2 * (supply_m + return_m)

    cavities = preflight.get("manifold_cavities")
    if not isinstance(cavities, Mapping):
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            "Kernel preflight manifold cavity evidence is missing.",
            status_code=422,
        )
    split_m3 = _nested_number(cavities, "split_manifold", "volume_mm3") * 1e-9
    merge_m3 = _nested_number(cavities, "merge_manifold", "volume_mm3") * 1e-9
    if split_m3 <= 0.0 or merge_m3 <= 0.0:
        raise CadLinkError(
            "cad_link_manifold_volume_unrepresentable",
            "Kernel manifold cavity volume is not representable.",
            status_code=422,
        )

    totals = _mapping(manifest, "geometry_totals")
    checks = [
        _check("branch_count", path_count, _resolved_branch_count(resolved_spec), "1", 0.0, 0.0),
        _check("branch_inner_diameter", branch_inner_mm, branch_outer_mm - 2.0 * branch_wall_mm, "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("branch_outer_diameter", branch_outer_mm, _part_dimension(resolved_spec, "branch_1_step_1", "outer_d"), "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("branch_wall_thickness", branch_wall_mm, _part_dimension(resolved_spec, "branch_1_step_1", "wall_t"), "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("common_inner_diameter", common_inner_mm, common_outer_mm - 2.0 * common_wall_mm, "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("common_outer_diameter", common_outer_mm, _part_dimension(resolved_spec, "split_manifold", "main_outer_d"), "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("common_wall_thickness", common_wall_mm, _part_dimension(resolved_spec, "split_manifold", "main_wall_t"), "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("branch_bend_count_each", input_int(manifest, "branch_bend_count"), bend_count, "1", 0.0, 0.0),
        _check("branch_illuminated_bend_count_each", input_int(manifest, "branch_illuminated_bend_count"), illuminated_bends, "1", 0.0, 0.0),
        _check("branch_bend_radius", float(input_decimal(manifest, "branch_bend_centerline_radius")), bend_radius_m * 1000.0, "mm", TOLERANCES["dimension_absolute_mm"], TOLERANCES["dimension_relative"]),
        _check("branch_illuminated_straight", float(input_decimal(manifest, "branch_illuminated_straight_length")) * 1000.0, illuminated_straight_m * 1000.0, "mm", TOLERANCES["length_absolute_mm"], TOLERANCES["measure_relative"]),
        _check("branch_dark_straight", float(input_decimal(manifest, "branch_dark_straight_length")) * 1000.0, dark_straight_m * 1000.0, "mm", TOLERANCES["length_absolute_mm"], TOLERANCES["measure_relative"]),
        _check("branch_centerline_length_each", _number(totals, "branch_centerline_length_each_m"), branch_length_each_m, "m", TOLERANCES["length_absolute_mm"] / 1000.0, TOLERANCES["measure_relative"]),
        _check("installed_branch_centerline_length_total", _number(totals, "installed_branch_centerline_length_total_m"), installed_branch_m, "m", TOLERANCES["length_absolute_mm"] / 1000.0, TOLERANCES["measure_relative"]),
        _check("installed_tube_centerline_length_total", _number(totals, "installed_tube_centerline_length_total_m"), installed_total_m, "m", TOLERANCES["length_absolute_mm"] / 1000.0, TOLERANCES["measure_relative"]),
        _check("representative_hydraulic_path_length", _number(totals, "representative_hydraulic_path_length_m"), representative_path_m, "m", TOLERANCES["length_absolute_mm"] / 1000.0, TOLERANCES["measure_relative"]),
        _check("branch_liquid_volume_total", _number(totals, "branch_liquid_volume_total_m3"), branch_liquid_total_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
        _check("common_supply_liquid_volume", _number(totals, "common_supply_liquid_volume_m3"), supply_liquid_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
        _check("common_return_liquid_volume", _number(totals, "common_return_liquid_volume_m3"), return_liquid_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
        _check("illuminated_branch_external_area", _number(totals, "illuminated_branch_external_area_m2"), illuminated_area_m2, "m2", TOLERANCES["area_absolute_m2"], TOLERANCES["measure_relative"]),
        _check("dark_branch_external_area", _number(totals, "dark_branch_external_area_m2"), dark_area_m2, "m2", TOLERANCES["area_absolute_m2"], TOLERANCES["measure_relative"]),
        _check("common_external_area", _number(totals, "common_external_area_m2"), common_area_m2, "m2", TOLERANCES["area_absolute_m2"], TOLERANCES["measure_relative"]),
        _check("tube_external_area_total", _number(totals, "tube_external_area_total_m2"), tube_area_total_m2, "m2", TOLERANCES["area_absolute_m2"], TOLERANCES["measure_relative"]),
        _check("tube_material_volume_proxy", _number(totals, "tube_material_volume_proxy_m3"), tube_material_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
        _check("split_manifold_cavity", float(input_decimal(manifest, "split_manifold_liquid_volume")) * 1e-3, split_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
        _check("merge_manifold_cavity", float(input_decimal(manifest, "merge_manifold_liquid_volume")) * 1e-3, merge_m3, "m3", TOLERANCES["volume_absolute_m3"], TOLERANCES["measure_relative"]),
    ]
    represented_m3 = tube_liquid_total_m3 + split_m3 + merge_m3
    reservoir_m3 = float(input_decimal(manifest, "reservoir_liquid_volume")) * 1e-3
    expected_represented_m3 = _number(totals, "total_liquid_inventory_m3") - reservoir_m3
    checks.append(
        _check(
            "represented_fluid_volume",
            expected_represented_m3,
            represented_m3,
            "m3",
            TOLERANCES["volume_absolute_m3"],
            TOLERANCES["measure_relative"],
        )
    )
    if not all(check["passed"] for check in checks):
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            "One or more required process/CAD reconciliation checks failed.",
            status_code=422,
        )
    return {
        "schema_version": "cad_link_072_reconciliation_v0_1",
        "tolerances": dict(TOLERANCES),
        "checks": checks,
        "structural_checks": {
            "split_merge_branch_pitch_equal": layout["split_manifold"]["branch_gap_mm"]
            == layout["merge_manifold"]["branch_gap_mm"],
            "ordered_branch_port_count": path_count,
            "branch_turn_sequence": [step.get("turn") for step in steps if step["kind"] == "bend"],
            "branch_step_illumination": [step["illumination"] for step in steps],
            "external_boundary_count": len(preflight.get("open_endpoints", [])),
        },
        "represented_fluid_volume_m3": represented_m3,
        "expected_represented_fluid_volume_m3": expected_represented_m3,
        "excluded_fluid_volume_m3": reservoir_m3,
        "cad_only_metrics": {
            "split_manifold_material_volume_mm3": _part_material_volume(preflight, "split_manifold"),
            "merge_manifold_material_volume_mm3": _part_material_volume(preflight, "merge_manifold"),
            "assembly_material_volume_mm3": preflight.get("assembly_material_volume_mm3"),
            "assembly_bbox_mm": preflight.get("assembly_bbox_mm"),
            "contact_pairs": preflight.get("contact_pairs"),
        },
    }


def _canonical_analysis_contract(value: dict[str, Any] | None) -> Any:
    config = BluecadLoopConfig(analysis_spec=value)
    return config.analysis_spec


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
    code = "cad_link_run_stale" if record_ref.startswith("simulation_run:") else "cad_link_parameter_stale"
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
    def reject_constant(value: str) -> object:
        raise ValueError(value)

    try:
        value = json.loads(str(raw), parse_constant=reject_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CadLinkError(code, "Stored source JSON is malformed or non-finite.", status_code=422) from exc
    if not isinstance(value, dict):
        raise CadLinkError(code, "Stored source JSON must be an object.", status_code=422)
    return value


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            f"Topology manifest field {key} is missing.",
            status_code=422,
        )
    return value


def _number(parent: Mapping[str, Any], key: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool):
        raise CadLinkError("cad_link_reconciliation_failed", "Source geometry total is invalid.", status_code=422)
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise CadLinkError("cad_link_reconciliation_failed", "Source geometry total is invalid.", status_code=422) from exc
    if not math.isfinite(number):
        raise CadLinkError("cad_link_reconciliation_failed", "Source geometry total is invalid.", status_code=422)
    return number


def _nested_number(parent: Mapping[str, Any], key: str, child: str) -> float:
    return _number(_mapping(parent, key), child)


def _part_dimension(spec: Mapping[str, Any], part_id: str, key: str) -> float:
    for part in spec.get("parts", []):
        if part.get("part_id") == part_id:
            return _number(_mapping(part, "params"), key)
    raise CadLinkError(
        "cad_link_reconciliation_failed",
        f"Resolved GeometrySpec is missing part {part_id}.",
        status_code=422,
    )


def _resolved_branch_count(spec: Mapping[str, Any]) -> int:
    indices = {
        str(part.get("part_id", "")).split("_", 2)[1]
        for part in spec.get("parts", [])
        if str(part.get("part_id", "")).startswith("branch_")
    }
    return len(indices)


def _part_material_volume(preflight: Mapping[str, Any], part_id: str) -> float | None:
    placed = preflight.get("placed_parts")
    if not isinstance(placed, Mapping) or not isinstance(placed.get(part_id), Mapping):
        return None
    item = placed[part_id]
    value = item.get("material_volume_mm3")
    return None if value is None else float(value)


def _check(
    name: str,
    source_value: float | int,
    cad_value: float | int,
    unit: str,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> dict[str, Any]:
    source = float(source_value)
    cad = float(cad_value)
    absolute_error = abs(cad - source)
    scale = max(abs(cad), abs(source), 1e-300)
    relative_error = absolute_error / scale
    passed = absolute_error <= absolute_tolerance or relative_error <= relative_tolerance
    return {
        "name": name,
        "source_value": source_value,
        "cad_value": cad_value,
        "unit": unit,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "passed": passed,
    }


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CadLinkError("cad_link_numeric_invalid", "Source values must be finite numbers.", status_code=422)
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CadLinkError("cad_link_numeric_invalid", "Source values must be finite numbers.", status_code=422) from exc
    if not number.is_finite():
        raise CadLinkError("cad_link_numeric_invalid", "Source values must be finite numbers.", status_code=422)
    return number


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _digest(value: Any) -> str:
    try:
        payload = canonical_json(value)
    except SpecValidationError as exc:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Preview evidence contains non-finite or non-JSON values.",
            status_code=422,
        ) from exc
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
