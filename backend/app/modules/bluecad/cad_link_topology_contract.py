"""Closed deterministic layout contract for the 072 M1 CAD link."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.spec import SpecValidationError, canonicalize_geometry_spec

LAYOUT_SCHEMA_VERSION = "bluerev_cad_layout_m1_v0_1"
LAYOUT_KIND = "planar_mirrored_parallel_headers"
BOUNDARY_POLICY = "open_common_supply_and_return"
TRANSFORMATION_VERSION = "bluerev_072_m1_planar_tubing_v0_1"
IMPLEMENTATION_VERSION = "cad_link_072_v0_1"
GEOMETRY_NAME = "bluerev_072_m1_planar_tubing"
MAX_LAYOUT_STEPS = 129
MAX_RESOLVED_PARTS = 256
LENGTH_ABS_TOL_MM = Decimal("1e-9")
MEASURE_REL_TOL = Decimal("1e-9")

_LAYOUT_KEYS = frozenset(
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


def canonicalize_layout(
    manifest: Mapping[str, Any],
    raw_layout: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and decimal-normalize the closed reviewed layout request."""

    if not isinstance(raw_layout, Mapping) or set(raw_layout) != _LAYOUT_KEYS:
        raise _layout_error("Layout top-level fields do not match the closed schema.")
    if raw_layout.get("schema_version") != LAYOUT_SCHEMA_VERSION:
        raise _layout_error("Layout schema_version is invalid.")
    if raw_layout.get("layout_kind") != LAYOUT_KIND:
        raise _layout_error("Layout kind is invalid.")
    if raw_layout.get("plane") != "xy":
        raise _layout_error("Only the fixed XY planar contract is supported.")
    if raw_layout.get("boundary_policy") != BOUNDARY_POLICY:
        raise _layout_error("Layout boundary policy is invalid.")

    canonical_manifolds: dict[str, dict[str, float]] = {}
    manifold_decimals: dict[str, dict[str, Decimal]] = {}
    for name in ("split_manifold", "merge_manifold"):
        raw_block = raw_layout.get(name)
        if not isinstance(raw_block, Mapping) or set(raw_block) != _MANIFOLD_KEYS:
            raise _layout_error(f"{name} fields do not match the closed schema.")
        normalized = {
            key: _positive_decimal(raw_block[key], f"{name}.{key}")
            for key in sorted(_MANIFOLD_KEYS)
        }
        manifold_decimals[name] = normalized
        canonical_manifolds[name] = {
            key: _finite_float(value) for key, value in normalized.items()
        }

    path_count = input_int(manifest, "parallel_path_count")
    if path_count > 1 and (
        manifold_decimals["split_manifold"]["branch_gap_mm"]
        != manifold_decimals["merge_manifold"]["branch_gap_mm"]
    ):
        raise CadLinkError(
            "cad_link_layout_mismatch",
            "Split and merge branch gaps must be identical for parallel branches.",
            status_code=422,
        )

    raw_route = raw_layout.get("branch_route")
    if not isinstance(raw_route, Mapping) or set(raw_route) != {"steps"}:
        raise _layout_error("branch_route must contain only steps.")
    raw_steps = raw_route.get("steps")
    if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= MAX_LAYOUT_STEPS:
        raise _layout_error("branch_route.steps is outside the bounded non-empty domain.")

    canonical_steps: list[dict[str, Any]] = []
    illuminated_straight_mm = Decimal(0)
    dark_straight_mm = Decimal(0)
    bend_count = 0
    illuminated_bend_count = 0
    previous: dict[str, Any] | None = None
    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, Mapping):
            raise _layout_error(f"branch_route.steps[{index}] must be an object.")
        kind = raw_step.get("kind")
        if kind == "straight":
            if set(raw_step) != {"kind", "length_mm", "illumination"}:
                raise _layout_error(
                    f"branch_route.steps[{index}] straight fields are invalid."
                )
            illumination = raw_step.get("illumination")
            if illumination not in {"illuminated", "dark"}:
                raise _layout_error(
                    f"branch_route.steps[{index}] illumination is invalid."
                )
            length_mm = _positive_decimal(
                raw_step.get("length_mm"),
                f"branch_route.steps[{index}].length_mm",
            )
            if (
                previous is not None
                and previous["kind"] == "straight"
                and previous["illumination"] == illumination
            ):
                raise CadLinkError(
                    "cad_link_layout_mismatch",
                    "Adjacent straight steps with equal illumination are non-canonical.",
                    status_code=422,
                )
            step = {
                "kind": "straight",
                "length_mm": _finite_float(length_mm),
                "illumination": illumination,
            }
            if illumination == "illuminated":
                illuminated_straight_mm += length_mm
            else:
                dark_straight_mm += length_mm
        elif kind == "bend":
            if set(raw_step) != {"kind", "turn", "illumination"}:
                raise _layout_error(
                    f"branch_route.steps[{index}] bend fields are invalid."
                )
            turn = raw_step.get("turn")
            illumination = raw_step.get("illumination")
            if turn not in {"left", "right"}:
                raise _layout_error(f"branch_route.steps[{index}] turn is invalid.")
            if illumination not in {"illuminated", "dark"}:
                raise _layout_error(
                    f"branch_route.steps[{index}] illumination is invalid."
                )
            step = {
                "kind": "bend",
                "turn": turn,
                "illumination": illumination,
            }
            bend_count += 1
            if illumination == "illuminated":
                illuminated_bend_count += 1
        else:
            raise _layout_error(f"branch_route.steps[{index}] kind is invalid.")
        canonical_steps.append(step)
        previous = step

    expected_illuminated_mm = (
        input_decimal(manifest, "branch_illuminated_straight_length")
        * Decimal(1000)
    )
    expected_dark_mm = (
        input_decimal(manifest, "branch_dark_straight_length") * Decimal(1000)
    )
    if not _decimal_close(
        illuminated_straight_mm,
        expected_illuminated_mm,
        LENGTH_ABS_TOL_MM,
        MEASURE_REL_TOL,
    ):
        raise CadLinkError(
            "cad_link_layout_mismatch",
            "Illuminated straight allocation does not match the 072 source.",
            status_code=422,
        )
    if not _decimal_close(
        dark_straight_mm,
        expected_dark_mm,
        LENGTH_ABS_TOL_MM,
        MEASURE_REL_TOL,
    ):
        raise CadLinkError(
            "cad_link_layout_mismatch",
            "Dark straight allocation does not match the 072 source.",
            status_code=422,
        )
    if bend_count != input_int(manifest, "branch_bend_count"):
        raise CadLinkError(
            "cad_link_layout_mismatch",
            "Bend count does not match the 072 source.",
            status_code=422,
        )
    if illuminated_bend_count != input_int(
        manifest, "branch_illuminated_bend_count"
    ):
        raise CadLinkError(
            "cad_link_layout_mismatch",
            "Illuminated bend count does not match the 072 source.",
            status_code=422,
        )

    common_part_count = int(input_decimal(manifest, "common_supply_length") > 0)
    common_part_count += int(input_decimal(manifest, "common_return_length") > 0)
    resolved_part_count = 2 + common_part_count + path_count * len(canonical_steps)
    if resolved_part_count > MAX_RESOLVED_PARTS:
        raise CadLinkError(
            "cad_link_layout_complexity_unsupported",
            "Resolved layout exceeds the 256-part V0 bound.",
            status_code=422,
        )

    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "layout_kind": LAYOUT_KIND,
        "plane": "xy",
        "boundary_policy": BOUNDARY_POLICY,
        "split_manifold": canonical_manifolds["split_manifold"],
        "merge_manifold": canonical_manifolds["merge_manifold"],
        "branch_route": {"steps": canonical_steps},
    }


def resolve_geometry_spec(
    manifest: Mapping[str, Any],
    layout: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str], dict[str, list[str]]]:
    """Transform one trusted manifest and canonical layout into GeometrySpec."""

    path_count = input_int(manifest, "parallel_path_count")
    branch_inner_mm = input_decimal(manifest, "branch_tube_inner_diameter")
    branch_outer_mm = input_decimal(manifest, "branch_tube_outer_diameter")
    common_inner_mm = input_decimal(manifest, "common_tube_inner_diameter")
    common_outer_mm = input_decimal(manifest, "common_tube_outer_diameter")
    branch_wall_mm = (branch_outer_mm - branch_inner_mm) / Decimal(2)
    common_wall_mm = (common_outer_mm - common_inner_mm) / Decimal(2)
    bend_radius_mm = input_decimal(manifest, "branch_bend_centerline_radius")
    bend_angle_rad = Decimal(
        str(math.radians(float(input_decimal(manifest, "branch_bend_angle"))))
    )
    supply_length_mm = input_decimal(manifest, "common_supply_length") * Decimal(1000)
    return_length_mm = input_decimal(manifest, "common_return_length") * Decimal(1000)

    def manifold_part(part_id: str, block: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "part_id": part_id,
            "kind": "capped_manifold",
            "params": {
                "main_outer_d": _finite_float(common_outer_mm),
                "main_wall_t": _finite_float(common_wall_mm),
                "branch_count": path_count,
                "branch_outer_d": _finite_float(branch_outer_mm),
                "branch_wall_t": _finite_float(branch_wall_mm),
                "branch_gap": float(block["branch_gap_mm"]),
                "end_gap": float(block["end_gap_mm"]),
                "branch_stub_length": float(block["branch_stub_length_mm"]),
                "cap_thickness": float(block["cap_thickness_mm"]),
            },
        }

    parts: list[dict[str, Any]] = [
        manifold_part("split_manifold", layout["split_manifold"])
    ]
    connections: list[dict[str, str]] = []
    if supply_length_mm > 0:
        parts.append(
            {
                "part_id": "common_supply",
                "kind": "tube_run",
                "params": {
                    "outer_d": _finite_float(common_outer_mm),
                    "wall_t": _finite_float(common_wall_mm),
                    "length": _finite_float(supply_length_mm),
                },
            }
        )
        connections.append(
            {"from": "common_supply.port_b", "to": "split_manifold.common"}
        )

    branch_endpoints: list[tuple[str, str]] = []
    steps = layout["branch_route"]["steps"]
    for branch_index in range(1, path_count + 1):
        previous_endpoint = f"split_manifold.branch_{branch_index}"
        for step_index, step in enumerate(steps, start=1):
            part_id = f"branch_{branch_index}_step_{step_index}"
            if step["kind"] == "straight":
                part = {
                    "part_id": part_id,
                    "kind": "tube_run",
                    "params": {
                        "outer_d": _finite_float(branch_outer_mm),
                        "wall_t": _finite_float(branch_wall_mm),
                        "length": float(step["length_mm"]),
                    },
                }
                entry_port, exit_port = "port_a", "port_b"
            else:
                part = {
                    "part_id": part_id,
                    "kind": "bend",
                    "params": {
                        "outer_d": _finite_float(branch_outer_mm),
                        "wall_t": _finite_float(branch_wall_mm),
                        "bend_radius": _finite_float(bend_radius_mm),
                        "angle": _finite_float(bend_angle_rad),
                    },
                }
                if step["turn"] == "left":
                    entry_port, exit_port = "port_a", "port_b"
                else:
                    entry_port, exit_port = "port_b", "port_a"
            parts.append(part)
            connections.append(
                {"from": previous_endpoint, "to": f"{part_id}.{entry_port}"}
            )
            previous_endpoint = f"{part_id}.{exit_port}"
        branch_endpoints.append(
            (
                previous_endpoint,
                f"merge_manifold.branch_{path_count + 1 - branch_index}",
            )
        )

    parts.append(manifold_part("merge_manifold", layout["merge_manifold"]))
    connections.extend(
        {"from": source, "to": target} for source, target in branch_endpoints
    )
    if return_length_mm > 0:
        parts.append(
            {
                "part_id": "common_return",
                "kind": "tube_run",
                "params": {
                    "outer_d": _finite_float(common_outer_mm),
                    "wall_t": _finite_float(common_wall_mm),
                    "length": _finite_float(return_length_mm),
                },
            }
        )
        connections.append(
            {"from": "common_return.port_b", "to": "merge_manifold.common"}
        )

    raw_spec = {
        "spec_version": "bluecad_geometry_spec_v0_1",
        "name": GEOMETRY_NAME,
        "parts": parts,
        "connections": connections,
    }
    try:
        resolved_spec = canonicalize_geometry_spec(raw_spec)
    except SpecValidationError as exc:
        raise CadLinkError(
            "cad_link_geometry_invalid",
            "Resolved 072 GeometrySpec is invalid.",
            status_code=422,
        ) from exc

    boundaries = {
        "common_supply_boundary": (
            "common_supply.port_a"
            if supply_length_mm > 0
            else "split_manifold.common"
        ),
        "common_return_boundary": (
            "common_return.port_a"
            if return_length_mm > 0
            else "merge_manifold.common"
        ),
    }
    component_inventory = {
        "represented": [
            "common_tubing",
            "split_manifold",
            "merge_manifold",
            "repeated_branch_tubing",
        ],
        "excluded": [
            "pump",
            "reservoir_vessel",
            "supports",
            "floats",
            "anchors",
            "instrumentation",
        ],
        "cad_boundary": ["open_supply_inlet", "open_return_outlet"],
    }
    return resolved_spec, boundaries, component_inventory


def input_decimal(manifest: Mapping[str, Any], name: str) -> Decimal:
    inputs = manifest.get("executed_inputs")
    item = inputs.get(name) if isinstance(inputs, Mapping) else None
    if not isinstance(item, Mapping) or "value" not in item or "unit" not in item:
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology manifest executed-input contract is incomplete.",
            status_code=422,
        )
    return _decimal(item["value"])


def input_int(manifest: Mapping[str, Any], name: str) -> int:
    value = input_decimal(manifest, name)
    if value != value.to_integral_value():
        raise CadLinkError(
            "cad_link_topology_manifest_invalid",
            "Topology integer input is invalid.",
            status_code=422,
        )
    return int(value)


def _layout_error(message: str) -> CadLinkError:
    return CadLinkError("cad_link_layout_schema_invalid", message, status_code=422)


def _positive_decimal(value: Any, field: str) -> Decimal:
    number = _decimal(value)
    if number <= 0:
        raise _layout_error(f"{field} must be strictly positive.")
    return number


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Numeric values must be finite JSON numbers.",
            status_code=422,
        )
    if not isinstance(value, (int, float, Decimal)):
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Numeric strings, units, and expressions are forbidden.",
            status_code=422,
        )
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Numeric values must be finite JSON numbers.",
            status_code=422,
        ) from exc
    if not number.is_finite():
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Numeric values must be finite JSON numbers.",
            status_code=422,
        )
    return number


def _decimal_close(
    value: Decimal,
    expected: Decimal,
    absolute_tolerance: Decimal,
    relative_tolerance: Decimal,
) -> bool:
    error = abs(value - expected)
    scale = max(abs(value), abs(expected), Decimal("1e-300"))
    return error <= absolute_tolerance or error / scale <= relative_tolerance


def _finite_float(value: Decimal) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise CadLinkError(
            "cad_link_numeric_invalid",
            "Numeric value is not representable.",
            status_code=422,
        )
    return number
