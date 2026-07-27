"""Fixed-tolerance process/CAD reconciliation for CAD-LINK-1."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology_contract import input_decimal, input_int

TOLERANCES = {
    "dimension_absolute_mm": 1e-9,
    "dimension_relative": 1e-12,
    "length_absolute_mm": 1e-9,
    "measure_relative": 1e-9,
    "area_absolute_m2": 1e-12,
    "volume_absolute_m3": 1e-12,
}


def reconcile_topology(
    manifest: Mapping[str, Any],
    layout: Mapping[str, Any],
    resolved_spec: Mapping[str, Any],
    preflight: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute CAD measures from the resolved spec and compare them to 072."""

    path_count = input_int(manifest, "parallel_path_count")
    source = _source_values(manifest, path_count)
    cad = _resolve_cad_values(
        layout,
        resolved_spec,
        preflight,
        path_count=path_count,
        source_supply_positive=source["common_supply_length_m"] > 0.0,
        source_return_positive=source["common_return_length_m"] > 0.0,
    )

    checks: list[dict[str, Any]] = []
    checks.extend(_dimension_checks(source, cad))
    checks.extend(_branch_checks(source, cad, path_count))
    checks.extend(_aggregate_checks(source, cad))
    checks.extend(_manifold_checks(manifest, layout, cad, path_count))

    split_cavity_m3 = cad["split_cavity_volume_mm3"] * 1e-9
    merge_cavity_m3 = cad["merge_cavity_volume_mm3"] * 1e-9
    if split_cavity_m3 <= 0.0 or merge_cavity_m3 <= 0.0:
        raise CadLinkError(
            "cad_link_manifold_volume_unrepresentable",
            "Kernel manifold cavity volume is not representable.",
            status_code=422,
        )
    checks.extend(
        [
            _check_volume(
                "split_manifold_cavity",
                float(input_decimal(manifest, "split_manifold_liquid_volume")) * 1e-3,
                split_cavity_m3,
            ),
            _check_volume(
                "merge_manifold_cavity",
                float(input_decimal(manifest, "merge_manifold_liquid_volume")) * 1e-3,
                merge_cavity_m3,
            ),
        ]
    )

    represented_m3 = (
        cad["tube_liquid_volume_total_m3"]
        + split_cavity_m3
        + merge_cavity_m3
    )
    reservoir_m3 = float(input_decimal(manifest, "reservoir_liquid_volume")) * 1e-3
    expected_represented_m3 = source["total_liquid_inventory_m3"] - reservoir_m3
    checks.append(
        _check_volume(
            "represented_fluid_volume",
            expected_represented_m3,
            represented_m3,
        )
    )

    failed = [check["name"] for check in checks if not check["passed"]]
    if failed:
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            "One or more required process/CAD reconciliation checks failed.",
            status_code=422,
        )

    structural_checks = {
        "exact_part_order": True,
        "exact_connection_order": True,
        "branch_copy_count": len(cad["branches"]),
        "split_merge_branch_pitch_equal": (
            True
            if path_count == 1
            else _close(
                cad["split_branch_pitch_mm"],
                cad["merge_branch_pitch_mm"],
                TOLERANCES["dimension_absolute_mm"],
                TOLERANCES["dimension_relative"],
            )
        ),
        "ordered_branch_port_count": {
            "split": cad["split_branch_port_count"],
            "merge": cad["merge_branch_port_count"],
        },
        "branch_turn_sequence": list(cad["turn_sequence"]),
        "branch_step_illumination": list(cad["illumination_sequence"]),
        "external_boundary_count": cad["external_boundary_count"],
        "pair_evaluation": cad["pair_evaluation"],
    }
    if (
        structural_checks["branch_copy_count"] != path_count
        or not structural_checks["split_merge_branch_pitch_equal"]
        or structural_checks["ordered_branch_port_count"]
        != {"split": path_count, "merge": path_count}
        or structural_checks["external_boundary_count"] != 2
    ):
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            "Required structural reconciliation failed.",
            status_code=422,
        )

    return {
        "schema_version": "cad_link_072_reconciliation_v0_1",
        "tolerances": dict(TOLERANCES),
        "checks": checks,
        "structural_checks": structural_checks,
        "represented_fluid_volume_m3": represented_m3,
        "expected_represented_fluid_volume_m3": expected_represented_m3,
        "excluded_fluid_volume_m3": reservoir_m3,
        "cad_only_metrics": {
            "split_manifold_material_volume_mm3": cad[
                "split_manifold_material_volume_mm3"
            ],
            "merge_manifold_material_volume_mm3": cad[
                "merge_manifold_material_volume_mm3"
            ],
            "assembly_material_volume_mm3": cad["assembly_material_volume_mm3"],
            "assembly_bbox_mm": cad["assembly_bbox_mm"],
            "contact_pairs": cad["contact_pairs"],
            "pair_evaluation": cad["pair_evaluation"],
        },
    }


def _source_values(
    manifest: Mapping[str, Any],
    path_count: int,
) -> dict[str, float]:
    totals = _mapping(manifest, "geometry_totals")
    branch_outer_mm = float(input_decimal(manifest, "branch_tube_outer_diameter"))
    branch_inner_mm = float(input_decimal(manifest, "branch_tube_inner_diameter"))
    common_outer_mm = float(input_decimal(manifest, "common_tube_outer_diameter"))
    common_inner_mm = float(input_decimal(manifest, "common_tube_inner_diameter"))
    branch_liquid_total = _number(totals, "branch_liquid_volume_total_m3")
    return {
        "branch_outer_diameter_mm": branch_outer_mm,
        "branch_inner_diameter_mm": branch_inner_mm,
        "branch_wall_thickness_mm": (branch_outer_mm - branch_inner_mm) / 2.0,
        "common_outer_diameter_mm": common_outer_mm,
        "common_inner_diameter_mm": common_inner_mm,
        "common_wall_thickness_mm": (common_outer_mm - common_inner_mm) / 2.0,
        "bend_radius_mm": float(
            input_decimal(manifest, "branch_bend_centerline_radius")
        ),
        "bend_angle_rad": math.radians(
            float(input_decimal(manifest, "branch_bend_angle"))
        ),
        "branch_bend_count": float(input_int(manifest, "branch_bend_count")),
        "branch_illuminated_bend_count": float(
            input_int(manifest, "branch_illuminated_bend_count")
        ),
        "branch_illuminated_straight_mm": float(
            input_decimal(manifest, "branch_illuminated_straight_length")
        )
        * 1000.0,
        "branch_dark_straight_mm": float(
            input_decimal(manifest, "branch_dark_straight_length")
        )
        * 1000.0,
        "common_supply_length_m": float(
            input_decimal(manifest, "common_supply_length")
        ),
        "common_return_length_m": float(
            input_decimal(manifest, "common_return_length")
        ),
        "branch_centerline_length_each_m": _number(
            totals, "branch_centerline_length_each_m"
        ),
        "installed_branch_centerline_length_total_m": _number(
            totals, "installed_branch_centerline_length_total_m"
        ),
        "installed_tube_centerline_length_total_m": _number(
            totals, "installed_tube_centerline_length_total_m"
        ),
        "representative_hydraulic_path_length_m": _number(
            totals, "representative_hydraulic_path_length_m"
        ),
        "branch_liquid_volume_each_m3": branch_liquid_total / path_count,
        "branch_liquid_volume_total_m3": branch_liquid_total,
        "common_supply_liquid_volume_m3": _number(
            totals, "common_supply_liquid_volume_m3"
        ),
        "common_return_liquid_volume_m3": _number(
            totals, "common_return_liquid_volume_m3"
        ),
        "illuminated_branch_external_area_m2": _number(
            totals, "illuminated_branch_external_area_m2"
        ),
        "dark_branch_external_area_m2": _number(
            totals, "dark_branch_external_area_m2"
        ),
        "common_external_area_m2": _number(
            totals, "common_external_area_m2"
        ),
        "tube_external_area_total_m2": _number(
            totals, "tube_external_area_total_m2"
        ),
        "tube_material_volume_proxy_m3": _number(
            totals, "tube_material_volume_proxy_m3"
        ),
        "total_liquid_inventory_m3": _number(
            totals, "total_liquid_inventory_m3"
        ),
    }


def _resolve_cad_values(
    layout: Mapping[str, Any],
    resolved_spec: Mapping[str, Any],
    preflight: Mapping[str, Any],
    *,
    path_count: int,
    source_supply_positive: bool,
    source_return_positive: bool,
) -> dict[str, Any]:
    parts = resolved_spec.get("parts")
    connections = resolved_spec.get("connections", [])
    if not isinstance(parts, list) or not all(
        isinstance(part, Mapping) for part in parts
    ):
        raise _reconciliation_error("Resolved GeometrySpec parts are invalid.")
    if not isinstance(connections, list) or not all(
        isinstance(connection, Mapping) for connection in connections
    ):
        raise _reconciliation_error("Resolved GeometrySpec connections are invalid.")

    steps = _steps(layout)
    expected_ids = ["split_manifold"]
    if source_supply_positive:
        expected_ids.append("common_supply")
    for branch_index in range(1, path_count + 1):
        expected_ids.extend(
            f"branch_{branch_index}_step_{step_index}"
            for step_index in range(1, len(steps) + 1)
        )
    expected_ids.append("merge_manifold")
    if source_return_positive:
        expected_ids.append("common_return")
    actual_ids = [str(part.get("part_id") or "") for part in parts]
    if actual_ids != expected_ids or len(set(actual_ids)) != len(actual_ids):
        raise _reconciliation_error(
            "Resolved GeometrySpec part order or identity is invalid."
        )
    part_map = {str(part["part_id"]): part for part in parts}

    expected_connections = _expected_connections(
        steps,
        path_count=path_count,
        supply_present=source_supply_positive,
        return_present=source_return_positive,
    )
    actual_connections = [
        {"from": str(connection.get("from")), "to": str(connection.get("to"))}
        for connection in connections
    ]
    if actual_connections != expected_connections:
        raise _reconciliation_error(
            "Resolved GeometrySpec connection order or traversal is invalid."
        )

    split = _manifold_values(part_map["split_manifold"], "split_manifold")
    merge = _manifold_values(part_map["merge_manifold"], "merge_manifold")
    if split["branch_count"] != path_count or merge["branch_count"] != path_count:
        raise _reconciliation_error("Resolved manifold branch count is invalid.")

    placed_parts = _mapping(preflight, "placed_parts")
    split_ports = _manifold_ports(placed_parts, "split_manifold", path_count)
    merge_ports = _manifold_ports(placed_parts, "merge_manifold", path_count)
    split_pitch = _port_pitch(split_ports)
    merge_pitch = _port_pitch(merge_ports)
    if path_count > 1:
        expected_split_pitch = split["branch_outer_d"] + split["branch_gap"]
        expected_merge_pitch = merge["branch_outer_d"] + merge["branch_gap"]
        if not all(
            _close(
                pitch,
                expected_split_pitch,
                TOLERANCES["dimension_absolute_mm"],
                TOLERANCES["dimension_relative"],
            )
            for pitch in split_pitch
        ) or not all(
            _close(
                pitch,
                expected_merge_pitch,
                TOLERANCES["dimension_absolute_mm"],
                TOLERANCES["dimension_relative"],
            )
            for pitch in merge_pitch
        ):
            raise _reconciliation_error(
                "Placed manifold branch pitch disagrees with resolved parameters."
            )
        split_pitch_value: float | None = split_pitch[0]
        merge_pitch_value: float | None = merge_pitch[0]
    else:
        split_pitch_value = None
        merge_pitch_value = None

    branch_values: list[dict[str, Any]] = []
    reference_signature: list[tuple[str, tuple[tuple[str, float], ...], str]] | None = None
    turn_sequence = [
        str(step["turn"]) for step in steps if step["kind"] == "bend"
    ]
    illumination_sequence = [str(step["illumination"]) for step in steps]
    for branch_index in range(1, path_count + 1):
        branch = _branch_values(
            part_map,
            steps,
            branch_index=branch_index,
        )
        if reference_signature is None:
            reference_signature = branch["signature"]
        elif branch["signature"] != reference_signature:
            raise _reconciliation_error(
                "Resolved branch copies are not identical."
            )
        branch_values.append(branch)

    supply = _common_values(
        part_map.get("common_supply"),
        expected_present=source_supply_positive,
        part_id="common_supply",
    )
    common_return = _common_values(
        part_map.get("common_return"),
        expected_present=source_return_positive,
        part_id="common_return",
    )

    branch_liquid_total = sum(
        branch["liquid_volume_m3"] for branch in branch_values
    )
    branch_illuminated_area = sum(
        branch["illuminated_external_area_m2"] for branch in branch_values
    )
    branch_dark_area = sum(
        branch["dark_external_area_m2"] for branch in branch_values
    )
    branch_material_total = sum(
        branch["material_volume_m3"] for branch in branch_values
    )
    common_liquid_total = (
        supply["liquid_volume_m3"] + common_return["liquid_volume_m3"]
    )
    common_area_total = (
        supply["external_area_m2"] + common_return["external_area_m2"]
    )
    common_material_total = (
        supply["material_volume_m3"] + common_return["material_volume_m3"]
    )
    common_length_m = supply["length_m"] + common_return["length_m"]
    installed_branch_length_m = sum(
        branch["centerline_length_m"] for branch in branch_values
    )
    first_branch_length = branch_values[0]["centerline_length_m"]

    open_endpoints = preflight.get("open_endpoints")
    if not isinstance(open_endpoints, list) or not all(
        isinstance(value, str) for value in open_endpoints
    ):
        raise _reconciliation_error("Preflight external-boundary evidence is invalid.")
    pair_evaluation = preflight.get("pair_evaluation")
    if not isinstance(pair_evaluation, Mapping):
        raise _reconciliation_error("Preflight pair-evaluation evidence is missing.")

    return {
        "split": split,
        "merge": merge,
        "branches": branch_values,
        "supply": supply,
        "return": common_return,
        "turn_sequence": turn_sequence,
        "illumination_sequence": illumination_sequence,
        "split_branch_pitch_mm": split_pitch_value,
        "merge_branch_pitch_mm": merge_pitch_value,
        "split_branch_port_count": len(split_ports),
        "merge_branch_port_count": len(merge_ports),
        "branch_liquid_volume_total_m3": branch_liquid_total,
        "common_supply_liquid_volume_m3": supply["liquid_volume_m3"],
        "common_return_liquid_volume_m3": common_return["liquid_volume_m3"],
        "tube_liquid_volume_total_m3": branch_liquid_total + common_liquid_total,
        "illuminated_branch_external_area_m2": branch_illuminated_area,
        "dark_branch_external_area_m2": branch_dark_area,
        "common_external_area_m2": common_area_total,
        "tube_external_area_total_m2": (
            branch_illuminated_area + branch_dark_area + common_area_total
        ),
        "tube_material_volume_m3": branch_material_total + common_material_total,
        "installed_branch_centerline_length_total_m": installed_branch_length_m,
        "installed_tube_centerline_length_total_m": (
            installed_branch_length_m + common_length_m
        ),
        "representative_hydraulic_path_length_m": (
            supply["length_m"] + first_branch_length + common_return["length_m"]
        ),
        "split_cavity_volume_mm3": _nested_number(
            _mapping(preflight, "manifold_cavities"),
            "split_manifold",
            "volume_mm3",
        ),
        "merge_cavity_volume_mm3": _nested_number(
            _mapping(preflight, "manifold_cavities"),
            "merge_manifold",
            "volume_mm3",
        ),
        "split_manifold_material_volume_mm3": _required_part_material_volume(
            placed_parts, "split_manifold"
        ),
        "merge_manifold_material_volume_mm3": _required_part_material_volume(
            placed_parts, "merge_manifold"
        ),
        "assembly_material_volume_mm3": _finite_number(
            preflight.get("assembly_material_volume_mm3")
        ),
        "assembly_bbox_mm": _mapping(preflight, "assembly_bbox_mm"),
        "contact_pairs": _required_list(preflight, "contact_pairs"),
        "pair_evaluation": dict(pair_evaluation),
        "external_boundary_count": len(open_endpoints),
    }


def _expected_connections(
    steps: list[Mapping[str, Any]],
    *,
    path_count: int,
    supply_present: bool,
    return_present: bool,
) -> list[dict[str, str]]:
    connections: list[dict[str, str]] = []
    if supply_present:
        connections.append(
            {"from": "common_supply.port_b", "to": "split_manifold.common"}
        )
    branch_ends: list[dict[str, str]] = []
    for branch_index in range(1, path_count + 1):
        previous = f"split_manifold.branch_{branch_index}"
        for step_index, step in enumerate(steps, start=1):
            part_id = f"branch_{branch_index}_step_{step_index}"
            if step["kind"] == "straight":
                entry, exit_port = "port_a", "port_b"
            elif step["turn"] == "left":
                entry, exit_port = "port_a", "port_b"
            else:
                entry, exit_port = "port_b", "port_a"
            connections.append({"from": previous, "to": f"{part_id}.{entry}"})
            previous = f"{part_id}.{exit_port}"
        branch_ends.append(
            {
                "from": previous,
                "to": f"merge_manifold.branch_{path_count + 1 - branch_index}",
            }
        )
    connections.extend(branch_ends)
    if return_present:
        connections.append(
            {"from": "common_return.port_b", "to": "merge_manifold.common"}
        )
    return connections


def _branch_values(
    part_map: Mapping[str, Mapping[str, Any]],
    steps: list[Mapping[str, Any]],
    *,
    branch_index: int,
) -> dict[str, Any]:
    illuminated_straight_mm = 0.0
    dark_straight_mm = 0.0
    illuminated_length_m = 0.0
    dark_length_m = 0.0
    liquid_volume_m3 = 0.0
    material_volume_m3 = 0.0
    illuminated_area_m2 = 0.0
    dark_area_m2 = 0.0
    signature: list[tuple[str, tuple[tuple[str, float], ...], str]] = []
    bend_count = 0
    illuminated_bend_count = 0
    for step_index, step in enumerate(steps, start=1):
        part_id = f"branch_{branch_index}_step_{step_index}"
        part = part_map.get(part_id)
        if part is None:
            raise _reconciliation_error(f"Resolved GeometrySpec is missing {part_id}.")
        params = _mapping(part, "params")
        expected_kind = "tube_run" if step["kind"] == "straight" else "bend"
        if part.get("kind") != expected_kind:
            raise _reconciliation_error(f"Resolved part {part_id} has the wrong kind.")
        outer_d = _number(params, "outer_d")
        wall_t = _number(params, "wall_t")
        inner_d = outer_d - 2.0 * wall_t
        if inner_d <= 0.0:
            raise _reconciliation_error(f"Resolved part {part_id} has invalid wall geometry.")
        if expected_kind == "tube_run":
            length_mm = _number(params, "length")
            signature_params = (
                ("length", length_mm),
                ("outer_d", outer_d),
                ("wall_t", wall_t),
            )
            if step["illumination"] == "illuminated":
                illuminated_straight_mm += length_mm
            else:
                dark_straight_mm += length_mm
        else:
            radius_mm = _number(params, "bend_radius")
            angle_rad = _number(params, "angle")
            length_mm = radius_mm * angle_rad
            signature_params = (
                ("angle", angle_rad),
                ("bend_radius", radius_mm),
                ("outer_d", outer_d),
                ("wall_t", wall_t),
            )
            bend_count += 1
            if step["illumination"] == "illuminated":
                illuminated_bend_count += 1

        length_m = length_mm / 1000.0
        inner_m = inner_d / 1000.0
        outer_m = outer_d / 1000.0
        liquid_area = math.pi * inner_m**2 / 4.0
        annulus_area = math.pi * (outer_m**2 - inner_m**2) / 4.0
        liquid_volume_m3 += liquid_area * length_m
        material_volume_m3 += annulus_area * length_m
        external_area = math.pi * outer_m * length_m
        if step["illumination"] == "illuminated":
            illuminated_length_m += length_m
            illuminated_area_m2 += external_area
        else:
            dark_length_m += length_m
            dark_area_m2 += external_area
        signature.append(
            (
                expected_kind,
                tuple(sorted(signature_params)),
                str(step["illumination"]),
            )
        )

    return {
        "illuminated_straight_mm": illuminated_straight_mm,
        "dark_straight_mm": dark_straight_mm,
        "illuminated_length_m": illuminated_length_m,
        "dark_length_m": dark_length_m,
        "centerline_length_m": illuminated_length_m + dark_length_m,
        "liquid_volume_m3": liquid_volume_m3,
        "material_volume_m3": material_volume_m3,
        "illuminated_external_area_m2": illuminated_area_m2,
        "dark_external_area_m2": dark_area_m2,
        "bend_count": bend_count,
        "illuminated_bend_count": illuminated_bend_count,
        "signature": signature,
    }


def _common_values(
    part: Mapping[str, Any] | None,
    *,
    expected_present: bool,
    part_id: str,
) -> dict[str, float]:
    if expected_present and part is None:
        raise _reconciliation_error(f"Resolved GeometrySpec is missing {part_id}.")
    if not expected_present and part is not None:
        raise _reconciliation_error(f"Resolved GeometrySpec unexpectedly contains {part_id}.")
    if part is None:
        return {
            "outer_d_mm": 0.0,
            "wall_t_mm": 0.0,
            "inner_d_mm": 0.0,
            "length_m": 0.0,
            "liquid_volume_m3": 0.0,
            "external_area_m2": 0.0,
            "material_volume_m3": 0.0,
        }
    if part.get("kind") != "tube_run":
        raise _reconciliation_error(f"Resolved part {part_id} has the wrong kind.")
    params = _mapping(part, "params")
    outer_d = _number(params, "outer_d")
    wall_t = _number(params, "wall_t")
    inner_d = outer_d - 2.0 * wall_t
    length_m = _number(params, "length") / 1000.0
    if inner_d <= 0.0 or length_m <= 0.0:
        raise _reconciliation_error(f"Resolved part {part_id} has invalid geometry.")
    inner_m = inner_d / 1000.0
    outer_m = outer_d / 1000.0
    return {
        "outer_d_mm": outer_d,
        "wall_t_mm": wall_t,
        "inner_d_mm": inner_d,
        "length_m": length_m,
        "liquid_volume_m3": math.pi * inner_m**2 / 4.0 * length_m,
        "external_area_m2": math.pi * outer_m * length_m,
        "material_volume_m3": (
            math.pi * (outer_m**2 - inner_m**2) / 4.0 * length_m
        ),
    }


def _manifold_values(
    part: Mapping[str, Any],
    part_id: str,
) -> dict[str, float | int]:
    if part.get("kind") != "capped_manifold":
        raise _reconciliation_error(f"Resolved part {part_id} has the wrong kind.")
    params = _mapping(part, "params")
    return {
        "main_outer_d": _number(params, "main_outer_d"),
        "main_wall_t": _number(params, "main_wall_t"),
        "main_inner_d": (
            _number(params, "main_outer_d")
            - 2.0 * _number(params, "main_wall_t")
        ),
        "branch_count": _strict_int(params.get("branch_count")),
        "branch_outer_d": _number(params, "branch_outer_d"),
        "branch_wall_t": _number(params, "branch_wall_t"),
        "branch_inner_d": (
            _number(params, "branch_outer_d")
            - 2.0 * _number(params, "branch_wall_t")
        ),
        "branch_gap": _number(params, "branch_gap"),
        "end_gap": _number(params, "end_gap"),
        "branch_stub_length": _number(params, "branch_stub_length"),
        "cap_thickness": _number(params, "cap_thickness"),
    }


def _manifold_ports(
    placed_parts: Mapping[str, Any],
    part_id: str,
    path_count: int,
) -> list[tuple[float, float, float]]:
    item = _mapping(placed_parts, part_id)
    ports = _mapping(item, "ports")
    expected_names = {
        "common",
        *[f"branch_{index}" for index in range(1, path_count + 1)],
    }
    if set(ports) != expected_names:
        raise _reconciliation_error("Placed manifold port inventory is invalid.")
    return [
        _vector(_mapping(ports, f"branch_{index}").get("origin"))
        for index in range(1, path_count + 1)
    ]


def _port_pitch(
    points: list[tuple[float, float, float]],
) -> list[float]:
    return [
        math.sqrt(
            sum(
                (points[index + 1][axis] - points[index][axis]) ** 2
                for axis in range(3)
            )
        )
        for index in range(len(points) - 1)
    ]


def _dimension_checks(
    source: Mapping[str, float],
    cad: Mapping[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for manifold_name in ("split", "merge"):
        manifold = cad[manifold_name]
        checks.extend(
            [
                _check_dimension(
                    f"{manifold_name}_main_outer_diameter",
                    source["common_outer_diameter_mm"],
                    manifold["main_outer_d"],
                ),
                _check_dimension(
                    f"{manifold_name}_main_inner_diameter",
                    source["common_inner_diameter_mm"],
                    manifold["main_inner_d"],
                ),
                _check_dimension(
                    f"{manifold_name}_main_wall_thickness",
                    source["common_wall_thickness_mm"],
                    manifold["main_wall_t"],
                ),
                _check_dimension(
                    f"{manifold_name}_branch_outer_diameter",
                    source["branch_outer_diameter_mm"],
                    manifold["branch_outer_d"],
                ),
                _check_dimension(
                    f"{manifold_name}_branch_inner_diameter",
                    source["branch_inner_diameter_mm"],
                    manifold["branch_inner_d"],
                ),
                _check_dimension(
                    f"{manifold_name}_branch_wall_thickness",
                    source["branch_wall_thickness_mm"],
                    manifold["branch_wall_t"],
                ),
            ]
        )
    for branch_index, branch in enumerate(cad["branches"], start=1):
        for step_index, signature in enumerate(branch["signature"], start=1):
            params = dict(signature[1])
            outer_d = params["outer_d"]
            wall_t = params["wall_t"]
            checks.extend(
                [
                    _check_dimension(
                        f"branch_{branch_index}_step_{step_index}_outer_diameter",
                        source["branch_outer_diameter_mm"],
                        outer_d,
                    ),
                    _check_dimension(
                        f"branch_{branch_index}_step_{step_index}_inner_diameter",
                        source["branch_inner_diameter_mm"],
                        outer_d - 2.0 * wall_t,
                    ),
                    _check_dimension(
                        f"branch_{branch_index}_step_{step_index}_wall_thickness",
                        source["branch_wall_thickness_mm"],
                        wall_t,
                    ),
                ]
            )
            if signature[0] == "bend":
                checks.extend(
                    [
                        _check_dimension(
                            f"branch_{branch_index}_step_{step_index}_bend_radius",
                            source["bend_radius_mm"],
                            params["bend_radius"],
                        ),
                        _check(
                            f"branch_{branch_index}_step_{step_index}_bend_angle",
                            source["bend_angle_rad"],
                            params["angle"],
                            "rad",
                            TOLERANCES["dimension_relative"],
                            TOLERANCES["dimension_relative"],
                        ),
                    ]
                )
    for name in ("supply", "return"):
        common = cad[name]
        if common["length_m"] > 0.0:
            checks.extend(
                [
                    _check_dimension(
                        f"common_{name}_outer_diameter",
                        source["common_outer_diameter_mm"],
                        common["outer_d_mm"],
                    ),
                    _check_dimension(
                        f"common_{name}_inner_diameter",
                        source["common_inner_diameter_mm"],
                        common["inner_d_mm"],
                    ),
                    _check_dimension(
                        f"common_{name}_wall_thickness",
                        source["common_wall_thickness_mm"],
                        common["wall_t_mm"],
                    ),
                ]
            )
    return checks


def _branch_checks(
    source: Mapping[str, float],
    cad: Mapping[str, Any],
    path_count: int,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for branch_index, branch in enumerate(cad["branches"], start=1):
        checks.extend(
            [
                _check(
                    f"branch_{branch_index}_bend_count",
                    source["branch_bend_count"],
                    branch["bend_count"],
                    "1",
                    0.0,
                    0.0,
                ),
                _check(
                    f"branch_{branch_index}_illuminated_bend_count",
                    source["branch_illuminated_bend_count"],
                    branch["illuminated_bend_count"],
                    "1",
                    0.0,
                    0.0,
                ),
                _check(
                    f"branch_{branch_index}_illuminated_straight",
                    source["branch_illuminated_straight_mm"],
                    branch["illuminated_straight_mm"],
                    "mm",
                    TOLERANCES["length_absolute_mm"],
                    TOLERANCES["measure_relative"],
                ),
                _check(
                    f"branch_{branch_index}_dark_straight",
                    source["branch_dark_straight_mm"],
                    branch["dark_straight_mm"],
                    "mm",
                    TOLERANCES["length_absolute_mm"],
                    TOLERANCES["measure_relative"],
                ),
                _check_measure(
                    f"branch_{branch_index}_centerline_length",
                    source["branch_centerline_length_each_m"],
                    branch["centerline_length_m"],
                    "m",
                ),
                _check_volume(
                    f"branch_{branch_index}_liquid_volume",
                    source["branch_liquid_volume_each_m3"],
                    branch["liquid_volume_m3"],
                ),
            ]
        )
    checks.append(
        _check(
            "branch_count",
            path_count,
            len(cad["branches"]),
            "1",
            0.0,
            0.0,
        )
    )
    return checks


def _aggregate_checks(
    source: Mapping[str, float],
    cad: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _check_measure(
            "common_supply_length",
            source["common_supply_length_m"],
            cad["supply"]["length_m"],
            "m",
        ),
        _check_measure(
            "common_return_length",
            source["common_return_length_m"],
            cad["return"]["length_m"],
            "m",
        ),
        _check_measure(
            "installed_branch_centerline_length_total",
            source["installed_branch_centerline_length_total_m"],
            cad["installed_branch_centerline_length_total_m"],
            "m",
        ),
        _check_measure(
            "installed_tube_centerline_length_total",
            source["installed_tube_centerline_length_total_m"],
            cad["installed_tube_centerline_length_total_m"],
            "m",
        ),
        _check_measure(
            "representative_hydraulic_path_length",
            source["representative_hydraulic_path_length_m"],
            cad["representative_hydraulic_path_length_m"],
            "m",
        ),
        _check_volume(
            "branch_liquid_volume_total",
            source["branch_liquid_volume_total_m3"],
            cad["branch_liquid_volume_total_m3"],
        ),
        _check_volume(
            "common_supply_liquid_volume",
            source["common_supply_liquid_volume_m3"],
            cad["common_supply_liquid_volume_m3"],
        ),
        _check_volume(
            "common_return_liquid_volume",
            source["common_return_liquid_volume_m3"],
            cad["common_return_liquid_volume_m3"],
        ),
        _check_volume(
            "represented_tube_liquid_volume",
            (
                source["branch_liquid_volume_total_m3"]
                + source["common_supply_liquid_volume_m3"]
                + source["common_return_liquid_volume_m3"]
            ),
            cad["tube_liquid_volume_total_m3"],
        ),
        _check_area(
            "illuminated_branch_external_area",
            source["illuminated_branch_external_area_m2"],
            cad["illuminated_branch_external_area_m2"],
        ),
        _check_area(
            "dark_branch_external_area",
            source["dark_branch_external_area_m2"],
            cad["dark_branch_external_area_m2"],
        ),
        _check_area(
            "common_external_area",
            source["common_external_area_m2"],
            cad["common_external_area_m2"],
        ),
        _check_area(
            "tube_external_area_total",
            source["tube_external_area_total_m2"],
            cad["tube_external_area_total_m2"],
        ),
        _check_volume(
            "tube_material_volume_proxy",
            source["tube_material_volume_proxy_m3"],
            cad["tube_material_volume_m3"],
        ),
    ]


def _manifold_checks(
    manifest: Mapping[str, Any],
    layout: Mapping[str, Any],
    cad: Mapping[str, Any],
    path_count: int,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = [
        _check(
            "split_branch_port_count",
            path_count,
            cad["split_branch_port_count"],
            "1",
            0.0,
            0.0,
        ),
        _check(
            "merge_branch_port_count",
            path_count,
            cad["merge_branch_port_count"],
            "1",
            0.0,
            0.0,
        ),
    ]
    branch_outer = float(input_decimal(manifest, "branch_tube_outer_diameter"))
    if path_count > 1:
        checks.extend(
            [
                _check_dimension(
                    "split_branch_pitch",
                    branch_outer
                    + float(layout["split_manifold"]["branch_gap_mm"]),
                    cad["split_branch_pitch_mm"],
                ),
                _check_dimension(
                    "merge_branch_pitch",
                    branch_outer
                    + float(layout["merge_manifold"]["branch_gap_mm"]),
                    cad["merge_branch_pitch_mm"],
                ),
            ]
        )
    for name in ("split", "merge"):
        block = layout[f"{name}_manifold"]
        manifold = cad[name]
        for layout_key, param_key in (
            ("branch_gap_mm", "branch_gap"),
            ("end_gap_mm", "end_gap"),
            ("branch_stub_length_mm", "branch_stub_length"),
            ("cap_thickness_mm", "cap_thickness"),
        ):
            checks.append(
                _check_dimension(
                    f"{name}_{param_key}",
                    float(block[layout_key]),
                    manifold[param_key],
                )
            )
    return checks


def _steps(layout: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    route = _mapping(layout, "branch_route")
    steps = route.get("steps")
    if not isinstance(steps, list) or not steps or not all(
        isinstance(step, Mapping) for step in steps
    ):
        raise _reconciliation_error("Canonical branch-route steps are invalid.")
    return steps


def _required_part_material_volume(
    placed_parts: Mapping[str, Any],
    part_id: str,
) -> float:
    value = _finite_number(
        _mapping(placed_parts, part_id).get("material_volume_mm3")
    )
    if value <= 0.0:
        raise _reconciliation_error("Kernel part material volume is invalid.")
    return value


def _required_list(parent: Mapping[str, Any], key: str) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        raise _reconciliation_error(f"Preflight field {key} is invalid.")
    return value


def _check_dimension(name: str, source: float, cad: float) -> dict[str, Any]:
    return _check(
        name,
        source,
        cad,
        "mm",
        TOLERANCES["dimension_absolute_mm"],
        TOLERANCES["dimension_relative"],
    )


def _check_measure(name: str, source: float, cad: float, unit: str) -> dict[str, Any]:
    return _check(
        name,
        source,
        cad,
        unit,
        TOLERANCES["length_absolute_mm"] / 1000.0,
        TOLERANCES["measure_relative"],
    )


def _check_area(name: str, source: float, cad: float) -> dict[str, Any]:
    return _check(
        name,
        source,
        cad,
        "m2",
        TOLERANCES["area_absolute_m2"],
        TOLERANCES["measure_relative"],
    )


def _check_volume(name: str, source: float, cad: float) -> dict[str, Any]:
    return _check(
        name,
        source,
        cad,
        "m3",
        TOLERANCES["volume_absolute_m3"],
        TOLERANCES["measure_relative"],
    )


def _mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise _reconciliation_error(f"Required reconciliation field {key} is missing.")
    return value


def _number(parent: Mapping[str, Any], key: str) -> float:
    return _finite_number(parent.get(key))


def _nested_number(parent: Mapping[str, Any], key: str, child: str) -> float:
    return _number(_mapping(parent, key), child)


def _finite_number(value: Any) -> float:
    if isinstance(value, bool):
        raise _reconciliation_error("Reconciliation numeric evidence is invalid.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise _reconciliation_error("Reconciliation numeric evidence is invalid.") from exc
    if not math.isfinite(number):
        raise _reconciliation_error("Reconciliation numeric evidence is invalid.")
    return number


def _strict_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _reconciliation_error("Resolved integer geometry parameter is invalid.")
    return value


def _vector(value: Any) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise _reconciliation_error("Placed port origin is invalid.")
    return tuple(_finite_number(component) for component in value)


def _reconciliation_error(message: str) -> CadLinkError:
    return CadLinkError(
        "cad_link_reconciliation_failed",
        message,
        status_code=422,
    )


def _close(
    left: float,
    right: float,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> bool:
    error = abs(left - right)
    scale = max(abs(left), abs(right), 1e-300)
    return error <= absolute_tolerance or error / scale <= relative_tolerance


def _check(
    name: str,
    source_value: float | int,
    cad_value: float | int,
    unit: str,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> dict[str, Any]:
    source = _finite_number(source_value)
    cad = _finite_number(cad_value)
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
