"""Pure deterministic 072 topology-manifest to BLUECAD GeometrySpec transformation."""

from __future__ import annotations

import hashlib
import math
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.bluecad.spec import canonical_json, canonicalize_geometry_spec

LAYOUT_SCHEMA_VERSION = "bluerev_cad_layout_m1_v0_1"
LAYOUT_KIND = "planar_mirrored_parallel_headers"
BOUNDARY_POLICY = "open_common_supply_and_return"
TRANSFORMATION_VERSION = "bluerev_072_m1_planar_tubing_v0_1"
IMPLEMENTATION_VERSION = "cad_link_072_v0_1"
MAX_ROUTE_STEPS = 129
MAX_RESOLVED_PARTS = 256

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "layout_kind",
        "plane",
        "boundary_policy",
        "split_manifold",
        "merge_manifold",
        "branch_route",
    }
)
_MANIFOLD_KEYS = frozenset(
    {
        "branch_gap_mm",
        "end_gap_mm",
        "branch_stub_length_mm",
        "cap_thickness_mm",
    }
)
_ROUTE_KEYS = frozenset({"steps"})
_STRAIGHT_KEYS = frozenset({"kind", "length_mm", "illumination"})
_BEND_KEYS = frozenset({"kind", "turn", "illumination"})


class TopologyCadLinkError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def canonicalize_layout_spec(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and return the closed canonical 074 planar layout object."""

    if not isinstance(raw, dict):
        _fail("cad_link_layout_schema_invalid", "Layout must be a JSON object.")
    _closed(raw, _TOP_LEVEL_KEYS, "layout")
    _const(raw, "schema_version", LAYOUT_SCHEMA_VERSION)
    _const(raw, "layout_kind", LAYOUT_KIND)
    _const(raw, "plane", "xy")
    _const(raw, "boundary_policy", BOUNDARY_POLICY)

    canonical = {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "layout_kind": LAYOUT_KIND,
        "plane": "xy",
        "boundary_policy": BOUNDARY_POLICY,
        "split_manifold": _canonical_manifold(raw.get("split_manifold"), "split_manifold"),
        "merge_manifold": _canonical_manifold(raw.get("merge_manifold"), "merge_manifold"),
        "branch_route": _canonical_route(raw.get("branch_route")),
    }
    return canonical


def layout_digest(layout: dict[str, Any]) -> str:
    return _digest(canonicalize_layout_spec(layout))


def transform_topology_manifest(
    manifest: dict[str, Any],
    layout: dict[str, Any],
) -> dict[str, Any]:
    """Create the exact deterministic GeometrySpec and boundary mapping."""

    source = _source_geometry(manifest)
    canonical_layout = canonicalize_layout_spec(layout)
    _validate_layout_against_source(canonical_layout, source)

    parts: list[dict[str, Any]] = []
    connections: list[dict[str, str]] = []
    branch_count = source["branch_count"]

    parts.append(
        _manifold_part(
            "split_manifold",
            source,
            canonical_layout["split_manifold"],
        )
    )

    if source["common_supply_length_mm"] > 0:
        parts.append(
            _tube_part(
                "common_supply",
                source["common_outer_d_mm"],
                source["common_wall_t_mm"],
                source["common_supply_length_mm"],
            )
        )
        connections.append(
            {"from": "common_supply.port_b", "to": "split_manifold.common"}
        )
        supply_boundary = "common_supply.port_a"
    else:
        supply_boundary = "split_manifold.common"

    canonical_steps = canonical_layout["branch_route"]["steps"]
    for branch_index in range(1, branch_count + 1):
        previous_endpoint = f"split_manifold.branch_{branch_index}"
        for step_index, step in enumerate(canonical_steps, start=1):
            part_id = f"branch_{branch_index}_step_{step_index}"
            if step["kind"] == "straight":
                parts.append(
                    _tube_part(
                        part_id,
                        source["branch_outer_d_mm"],
                        source["branch_wall_t_mm"],
                        step["length_mm"],
                    )
                )
                entry_port, exit_port = "port_a", "port_b"
            else:
                parts.append(
                    _bend_part(
                        part_id,
                        source["branch_outer_d_mm"],
                        source["branch_wall_t_mm"],
                        source["bend_radius_mm"],
                        source["bend_angle_rad"],
                    )
                )
                if step["turn"] == "left":
                    entry_port, exit_port = "port_a", "port_b"
                else:
                    entry_port, exit_port = "port_b", "port_a"
            connections.append(
                {"from": previous_endpoint, "to": f"{part_id}.{entry_port}"}
            )
            previous_endpoint = f"{part_id}.{exit_port}"
        merge_port = branch_count + 1 - branch_index
        connections.append(
            {"from": previous_endpoint, "to": f"merge_manifold.branch_{merge_port}"}
        )

    parts.append(
        _manifold_part(
            "merge_manifold",
            source,
            canonical_layout["merge_manifold"],
        )
    )

    if source["common_return_length_mm"] > 0:
        parts.append(
            _tube_part(
                "common_return",
                source["common_outer_d_mm"],
                source["common_wall_t_mm"],
                source["common_return_length_mm"],
            )
        )
        connections.append(
            {"from": "common_return.port_b", "to": "merge_manifold.common"}
        )
        return_boundary = "common_return.port_a"
    else:
        return_boundary = "merge_manifold.common"

    if len(parts) > MAX_RESOLVED_PARTS:
        _fail(
            "cad_link_layout_complexity_unsupported",
            "Resolved GeometrySpec exceeds the 256-part V0 bound.",
        )

    raw_spec = {
        "spec_version": "bluecad_geometry_spec_v0_1",
        "name": "bluerev_072_m1_planar_tubing",
        "parts": parts,
        "connections": connections,
    }
    resolved_spec = canonicalize_geometry_spec(raw_spec)
    result = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "transformation_version": TRANSFORMATION_VERSION,
        "layout_spec": canonical_layout,
        "layout_digest": _digest(canonical_layout),
        "resolved_geometry_spec": resolved_spec,
        "resolved_spec_digest": resolved_spec["spec_id"],
        "part_count": len(parts),
        "connection_count": len(connections),
        "external_boundaries": {
            "common_supply_boundary": supply_boundary,
            "common_return_boundary": return_boundary,
        },
        "represented_components": [
            "common_tubing",
            "split_manifold",
            "merge_manifold",
            "repeated_branch_tubing",
        ],
        "excluded_components": [
            "pump",
            "reservoir_vessel",
            "supports",
            "floats",
            "anchors",
            "instrumentation",
        ],
        "source_geometry": source,
    }
    return result


def _canonical_manifold(raw: Any, name: str) -> dict[str, float]:
    if not isinstance(raw, dict):
        _fail("cad_link_layout_schema_invalid", f"{name} must be an object.")
    _closed(raw, _MANIFOLD_KEYS, name)
    return {
        key: _positive_float(raw.get(key), f"{name}.{key}")
        for key in (
            "branch_gap_mm",
            "end_gap_mm",
            "branch_stub_length_mm",
            "cap_thickness_mm",
        )
    }


def _canonical_route(raw: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(raw, dict):
        _fail("cad_link_layout_schema_invalid", "branch_route must be an object.")
    _closed(raw, _ROUTE_KEYS, "branch_route")
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        _fail("cad_link_layout_schema_invalid", "branch_route.steps must be non-empty.")
    if len(steps) > MAX_ROUTE_STEPS:
        _fail("cad_link_layout_complexity_unsupported", "Route exceeds the 129-step bound.")

    canonical: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            _fail("cad_link_layout_schema_invalid", "Every route step must be an object.")
        kind = step.get("kind")
        if kind == "straight":
            _closed(step, _STRAIGHT_KEYS, f"branch_route.steps[{index}]")
            illumination = _enum(
                step.get("illumination"),
                {"illuminated", "dark"},
                "illumination",
            )
            current = {
                "kind": "straight",
                "length_mm": _positive_float(
                    step.get("length_mm"),
                    f"branch_route.steps[{index}].length_mm",
                ),
                "illumination": illumination,
            }
            if (
                canonical
                and canonical[-1]["kind"] == "straight"
                and canonical[-1]["illumination"] == illumination
            ):
                _fail(
                    "cad_link_layout_mismatch",
                    "Adjacent straight steps with the same illumination are non-canonical.",
                )
        elif kind == "bend":
            _closed(step, _BEND_KEYS, f"branch_route.steps[{index}]")
            current = {
                "kind": "bend",
                "turn": _enum(step.get("turn"), {"left", "right"}, "turn"),
                "illumination": _enum(
                    step.get("illumination"),
                    {"illuminated", "dark"},
                    "illumination",
                ),
            }
        else:
            _fail("cad_link_layout_schema_invalid", "Unsupported branch route step kind.")
        canonical.append(current)
    return {"steps": canonical}


def _source_geometry(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        _fail("cad_link_topology_manifest_invalid", "Topology manifest must be an object.")
    if manifest.get("schema_version") != "bluerev_process_topology_m1_v0_1":
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest schema is invalid.")
    if manifest.get("topology_kind") != "symmetric_parallel_closed_loop":
        _fail("cad_link_topology_manifest_identity_mismatch", "Topology manifest kind is invalid.")

    inputs = manifest.get("executed_inputs")
    geometry = manifest.get("geometry_totals")
    branch = manifest.get("branch_template")
    if not isinstance(inputs, dict) or not isinstance(geometry, dict) or not isinstance(branch, dict):
        _fail("cad_link_topology_manifest_invalid", "Topology manifest geometry is incomplete.")
    bend_group = branch.get("bend_group")
    if not isinstance(bend_group, dict):
        _fail("cad_link_topology_manifest_invalid", "Topology manifest bend group is missing.")

    branch_count = _input_int(inputs, "parallel_path_count", "1")
    if not 1 <= branch_count <= 12:
        _fail("cad_link_topology_manifest_invalid", "Topology branch count is outside V0 bounds.")

    branch_inner_mm = _input_decimal(inputs, "branch_tube_inner_diameter", "mm")
    branch_outer_mm = _input_decimal(inputs, "branch_tube_outer_diameter", "mm")
    common_inner_mm = _input_decimal(inputs, "common_tube_inner_diameter", "mm")
    common_outer_mm = _input_decimal(inputs, "common_tube_outer_diameter", "mm")
    branch_wall_mm = (branch_outer_mm - branch_inner_mm) / Decimal(2)
    common_wall_mm = (common_outer_mm - common_inner_mm) / Decimal(2)
    if branch_wall_mm <= 0 or common_wall_mm <= 0:
        _fail("cad_link_topology_manifest_invalid", "Topology tube wall thickness is invalid.")

    result = {
        "branch_count": branch_count,
        "branch_illuminated_straight_mm": _input_decimal(
            inputs, "branch_illuminated_straight_length", "m"
        )
        * Decimal(1000),
        "branch_dark_straight_mm": _input_decimal(
            inputs, "branch_dark_straight_length", "m"
        )
        * Decimal(1000),
        "bend_count": _input_int(inputs, "branch_bend_count", "1"),
        "illuminated_bend_count": _input_int(
            inputs, "branch_illuminated_bend_count", "1"
        ),
        "bend_radius_mm": _number_from_mapping(
            bend_group, "centerline_radius_m", "bend radius"
        )
        * Decimal(1000),
        "bend_angle_rad": _number_from_mapping(bend_group, "angle_deg", "bend angle")
        * Decimal(str(math.pi))
        / Decimal(180),
        "branch_inner_d_mm": branch_inner_mm,
        "branch_outer_d_mm": branch_outer_mm,
        "branch_wall_t_mm": branch_wall_mm,
        "common_inner_d_mm": common_inner_mm,
        "common_outer_d_mm": common_outer_mm,
        "common_wall_t_mm": common_wall_mm,
        "common_supply_length_mm": _number_from_mapping(
            geometry, "common_supply_length_m", "common supply length"
        )
        * Decimal(1000),
        "common_return_length_mm": _number_from_mapping(
            geometry, "common_return_length_m", "common return length"
        )
        * Decimal(1000),
        "split_manifold_liquid_volume_m3": _input_decimal(
            inputs, "split_manifold_liquid_volume", "L"
        )
        / Decimal(1000),
        "merge_manifold_liquid_volume_m3": _input_decimal(
            inputs, "merge_manifold_liquid_volume", "L"
        )
        / Decimal(1000),
        "reservoir_liquid_volume_m3": _number_from_mapping(
            geometry, "reservoir_liquid_volume_m3", "reservoir volume"
        ),
        "total_liquid_inventory_m3": _number_from_mapping(
            geometry, "total_liquid_inventory_m3", "total inventory"
        ),
    }
    return {key: (_finite_float(value) if isinstance(value, Decimal) else value) for key, value in result.items()}


def _validate_layout_against_source(layout: dict[str, Any], source: dict[str, Any]) -> None:
    split_gap = _decimal(layout["split_manifold"]["branch_gap_mm"])
    merge_gap = _decimal(layout["merge_manifold"]["branch_gap_mm"])
    if source["branch_count"] > 1 and split_gap != merge_gap:
        _fail("cad_link_layout_mismatch", "Split and merge branch pitch must be identical.")

    steps = layout["branch_route"]["steps"]
    bend_steps = [step for step in steps if step["kind"] == "bend"]
    if len(bend_steps) != source["bend_count"]:
        _fail("cad_link_layout_mismatch", "Bend step count does not match the 072 topology.")
    illuminated_bends = sum(step["illumination"] == "illuminated" for step in bend_steps)
    if illuminated_bends != source["illuminated_bend_count"]:
        _fail("cad_link_layout_mismatch", "Illuminated bend count does not match the 072 topology.")

    illuminated_straight = sum(
        (_decimal(step["length_mm"]) for step in steps if step["kind"] == "straight" and step["illumination"] == "illuminated"),
        Decimal(0),
    )
    dark_straight = sum(
        (_decimal(step["length_mm"]) for step in steps if step["kind"] == "straight" and step["illumination"] == "dark"),
        Decimal(0),
    )
    if illuminated_straight != _decimal(source["branch_illuminated_straight_mm"]):
        _fail("cad_link_layout_mismatch", "Illuminated straight allocation does not match 072.")
    if dark_straight != _decimal(source["branch_dark_straight_mm"]):
        _fail("cad_link_layout_mismatch", "Dark straight allocation does not match 072.")

    part_count = 2 + source["branch_count"] * len(steps)
    part_count += int(source["common_supply_length_mm"] > 0)
    part_count += int(source["common_return_length_mm"] > 0)
    if part_count > MAX_RESOLVED_PARTS:
        _fail("cad_link_layout_complexity_unsupported", "Resolved layout exceeds the 256-part bound.")


def _manifold_part(
    part_id: str,
    source: dict[str, Any],
    layout: dict[str, float],
) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "kind": "capped_manifold",
        "params": {
            "main_outer_d": source["common_outer_d_mm"],
            "main_wall_t": source["common_wall_t_mm"],
            "branch_count": source["branch_count"],
            "branch_outer_d": source["branch_outer_d_mm"],
            "branch_wall_t": source["branch_wall_t_mm"],
            "branch_gap": layout["branch_gap_mm"],
            "end_gap": layout["end_gap_mm"],
            "branch_stub_length": layout["branch_stub_length_mm"],
            "cap_thickness": layout["cap_thickness_mm"],
        },
    }


def _tube_part(part_id: str, outer_d: float, wall_t: float, length: float) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "kind": "tube_run",
        "params": {"outer_d": outer_d, "wall_t": wall_t, "length": length},
    }


def _bend_part(
    part_id: str,
    outer_d: float,
    wall_t: float,
    radius: float,
    angle: float,
) -> dict[str, Any]:
    return {
        "part_id": part_id,
        "kind": "bend",
        "params": {
            "outer_d": outer_d,
            "wall_t": wall_t,
            "bend_radius": radius,
            "angle": angle,
        },
    }


def _input_decimal(inputs: dict[str, Any], name: str, unit: str) -> Decimal:
    item = inputs.get(name)
    if not isinstance(item, dict) or item.get("unit") != unit:
        _fail("cad_link_topology_manifest_invalid", f"Topology input {name} is invalid.")
    return _decimal(item.get("value"))


def _input_int(inputs: dict[str, Any], name: str, unit: str) -> int:
    value = _input_decimal(inputs, name, unit)
    integer = int(value)
    if value != Decimal(integer):
        _fail("cad_link_topology_manifest_invalid", f"Topology input {name} must be integral.")
    return integer


def _number_from_mapping(mapping: dict[str, Any], key: str, label: str) -> Decimal:
    if key not in mapping:
        _fail("cad_link_topology_manifest_invalid", f"Topology {label} is missing.")
    return _decimal(mapping[key])


def _positive_float(value: Any, label: str) -> float:
    number = _decimal(value)
    if number <= 0:
        _fail("cad_link_layout_schema_invalid", f"{label} must be positive.")
    return _finite_float(number)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        _fail("cad_link_numeric_invalid", "Layout and manifest values must be finite JSON numbers.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise TopologyCadLinkError(
            "cad_link_numeric_invalid",
            "Layout and manifest values must be finite JSON numbers.",
        ) from exc
    if not number.is_finite():
        _fail("cad_link_numeric_invalid", "Layout and manifest values must be finite JSON numbers.")
    return number


def _finite_float(value: Decimal) -> float:
    number = float(value)
    if not math.isfinite(number):
        _fail("cad_link_numeric_invalid", "A derived layout value is not representable.")
    return number


def _closed(value: dict[str, Any], allowed: frozenset[str], label: str) -> None:
    extra = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if extra or missing:
        _fail(
            "cad_link_layout_schema_invalid",
            f"{label} has an invalid closed field set.",
        )


def _const(value: dict[str, Any], key: str, expected: str) -> None:
    if value.get(key) != expected:
        _fail("cad_link_layout_schema_invalid", f"{key} must equal {expected}.")


def _enum(value: Any, allowed: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail("cad_link_layout_schema_invalid", f"{label} is invalid.")
    return value


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _fail(code: str, message: str) -> None:
    raise TopologyCadLinkError(code, message)
