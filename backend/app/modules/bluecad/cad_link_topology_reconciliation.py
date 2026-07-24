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
    """Return every required comparison and fail if any authority disagrees."""

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
    illuminated_area_m2 = (
        path_count * math.pi * (branch_outer_mm / 1000.0) * illuminated_length_m
    )
    dark_area_m2 = path_count * math.pi * (branch_outer_mm / 1000.0) * dark_length_m
    common_area_m2 = math.pi * (common_outer_mm / 1000.0) * (supply_m + return_m)
    tube_area_total_m2 = illuminated_area_m2 + dark_area_m2 + common_area_m2
    tube_material_m3 = branch_annulus_m2 * installed_branch_m + common_annulus_m2 * (
        supply_m + return_m
    )

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
        _check(
            "branch_inner_diameter",
            branch_inner_mm,
            branch_outer_mm - 2.0 * branch_wall_mm,
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "branch_outer_diameter",
            branch_outer_mm,
            _part_dimension(resolved_spec, "branch_1_step_1", "outer_d"),
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "branch_wall_thickness",
            branch_wall_mm,
            _part_dimension(resolved_spec, "branch_1_step_1", "wall_t"),
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "common_inner_diameter",
            common_inner_mm,
            common_outer_mm - 2.0 * common_wall_mm,
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "common_outer_diameter",
            common_outer_mm,
            _part_dimension(resolved_spec, "split_manifold", "main_outer_d"),
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "common_wall_thickness",
            common_wall_mm,
            _part_dimension(resolved_spec, "split_manifold", "main_wall_t"),
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "branch_bend_count_each",
            input_int(manifest, "branch_bend_count"),
            bend_count,
            "1",
            0.0,
            0.0,
        ),
        _check(
            "branch_illuminated_bend_count_each",
            input_int(manifest, "branch_illuminated_bend_count"),
            illuminated_bends,
            "1",
            0.0,
            0.0,
        ),
        _check(
            "branch_bend_radius",
            float(input_decimal(manifest, "branch_bend_centerline_radius")),
            bend_radius_m * 1000.0,
            "mm",
            TOLERANCES["dimension_absolute_mm"],
            TOLERANCES["dimension_relative"],
        ),
        _check(
            "branch_illuminated_straight",
            float(input_decimal(manifest, "branch_illuminated_straight_length")) * 1000.0,
            illuminated_straight_m * 1000.0,
            "mm",
            TOLERANCES["length_absolute_mm"],
            TOLERANCES["measure_relative"],
        ),
        _check(
            "branch_dark_straight",
            float(input_decimal(manifest, "branch_dark_straight_length")) * 1000.0,
            dark_straight_m * 1000.0,
            "mm",
            TOLERANCES["length_absolute_mm"],
            TOLERANCES["measure_relative"],
        ),
        _check_measure(
            "branch_centerline_length_each",
            _number(totals, "branch_centerline_length_each_m"),
            branch_length_each_m,
            "m",
        ),
        _check_measure(
            "installed_branch_centerline_length_total",
            _number(totals, "installed_branch_centerline_length_total_m"),
            installed_branch_m,
            "m",
        ),
        _check_measure(
            "installed_tube_centerline_length_total",
            _number(totals, "installed_tube_centerline_length_total_m"),
            installed_total_m,
            "m",
        ),
        _check_measure(
            "representative_hydraulic_path_length",
            _number(totals, "representative_hydraulic_path_length_m"),
            representative_path_m,
            "m",
        ),
        _check_volume(
            "branch_liquid_volume_total",
            _number(totals, "branch_liquid_volume_total_m3"),
            branch_liquid_total_m3,
        ),
        _check_volume(
            "common_supply_liquid_volume",
            _number(totals, "common_supply_liquid_volume_m3"),
            supply_liquid_m3,
        ),
        _check_volume(
            "common_return_liquid_volume",
            _number(totals, "common_return_liquid_volume_m3"),
            return_liquid_m3,
        ),
        _check_area(
            "illuminated_branch_external_area",
            _number(totals, "illuminated_branch_external_area_m2"),
            illuminated_area_m2,
        ),
        _check_area(
            "dark_branch_external_area",
            _number(totals, "dark_branch_external_area_m2"),
            dark_area_m2,
        ),
        _check_area(
            "common_external_area",
            _number(totals, "common_external_area_m2"),
            common_area_m2,
        ),
        _check_area(
            "tube_external_area_total",
            _number(totals, "tube_external_area_total_m2"),
            tube_area_total_m2,
        ),
        _check_volume(
            "tube_material_volume_proxy",
            _number(totals, "tube_material_volume_proxy_m3"),
            tube_material_m3,
        ),
        _check_volume(
            "split_manifold_cavity",
            float(input_decimal(manifest, "split_manifold_liquid_volume")) * 1e-3,
            split_m3,
        ),
        _check_volume(
            "merge_manifold_cavity",
            float(input_decimal(manifest, "merge_manifold_liquid_volume")) * 1e-3,
            merge_m3,
        ),
    ]

    represented_m3 = tube_liquid_total_m3 + split_m3 + merge_m3
    reservoir_m3 = float(input_decimal(manifest, "reservoir_liquid_volume")) * 1e-3
    expected_represented_m3 = _number(totals, "total_liquid_inventory_m3") - reservoir_m3
    checks.append(
        _check_volume(
            "represented_fluid_volume",
            expected_represented_m3,
            represented_m3,
        )
    )
    if not all(check["passed"] for check in checks):
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            "One or more required process/CAD reconciliation checks failed.",
            status_code=422,
        )

    structural_checks = {
        "split_merge_branch_pitch_equal": layout["split_manifold"]["branch_gap_mm"]
        == layout["merge_manifold"]["branch_gap_mm"],
        "ordered_branch_port_count": path_count,
        "branch_turn_sequence": [
            step["turn"] for step in steps if step["kind"] == "bend"
        ],
        "branch_step_illumination": [step["illumination"] for step in steps],
        "external_boundary_count": len(preflight.get("open_endpoints", [])),
    }
    if (
        not structural_checks["split_merge_branch_pitch_equal"]
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
            "split_manifold_material_volume_mm3": _part_material_volume(
                preflight, "split_manifold"
            ),
            "merge_manifold_material_volume_mm3": _part_material_volume(
                preflight, "merge_manifold"
            ),
            "assembly_material_volume_mm3": preflight.get(
                "assembly_material_volume_mm3"
            ),
            "assembly_bbox_mm": preflight.get("assembly_bbox_mm"),
            "contact_pairs": preflight.get("contact_pairs"),
        },
    }


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
        raise CadLinkError(
            "cad_link_reconciliation_failed",
            f"Source reconciliation field {key} is missing.",
            status_code=422,
        )
    return value


def _number(parent: Mapping[str, Any], key: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool):
        raise _invalid_number()
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise _invalid_number() from exc
    if not math.isfinite(number):
        raise _invalid_number()
    return number


def _invalid_number() -> CadLinkError:
    return CadLinkError(
        "cad_link_reconciliation_failed",
        "Source geometry total is invalid.",
        status_code=422,
    )


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
    if not isinstance(placed, Mapping):
        return None
    item = placed.get(part_id)
    if not isinstance(item, Mapping):
        return None
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
