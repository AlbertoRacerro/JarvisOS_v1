from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from app.modules.bluecad.cad_link_topology_m1 import (
    LAYOUT_SCHEMA_VERSION,
    TopologyCadLinkError,
    canonicalize_layout_spec,
    transform_topology_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "bluerev_cad_layout_m1_v0_1.schema.json"


def _input(value: float | int, unit: str) -> dict[str, object]:
    return {"value": value, "unit": unit, "source_parameter_id": f"parameter-{unit}-{value}"}


def _manifest(
    *,
    branch_count: int = 2,
    bend_count: int = 2,
    illuminated_bends: int = 1,
    illuminated_straight_m: float = 10.0,
    dark_straight_m: float = 2.0,
    common_supply_m: float = 1.0,
    common_return_m: float = 1.5,
) -> dict:
    inputs = {
        "parallel_path_count": _input(branch_count, "1"),
        "branch_illuminated_straight_length": _input(illuminated_straight_m, "m"),
        "branch_dark_straight_length": _input(dark_straight_m, "m"),
        "branch_bend_count": _input(bend_count, "1"),
        "branch_illuminated_bend_count": _input(illuminated_bends, "1"),
        "branch_bend_centerline_radius": _input(100.0, "mm"),
        "branch_bend_angle": _input(90.0, "deg"),
        "common_supply_length": _input(common_supply_m, "m"),
        "common_return_length": _input(common_return_m, "m"),
        "branch_tube_inner_diameter": _input(50.0, "mm"),
        "branch_tube_outer_diameter": _input(60.0, "mm"),
        "common_tube_inner_diameter": _input(80.0, "mm"),
        "common_tube_outer_diameter": _input(90.0, "mm"),
        "split_manifold_liquid_volume": _input(5.0, "L"),
        "merge_manifold_liquid_volume": _input(5.0, "L"),
    }
    return {
        "schema_version": "bluerev_process_topology_m1_v0_1",
        "topology_kind": "symmetric_parallel_closed_loop",
        "executed_inputs": inputs,
        "branch_template": {
            "bend_group": {
                "centerline_radius_m": 0.1,
                "angle_deg": 90.0,
            }
        },
        "geometry_totals": {
            "common_supply_length_m": common_supply_m,
            "common_return_length_m": common_return_m,
            "reservoir_liquid_volume_m3": 0.1,
            "total_liquid_inventory_m3": 0.2,
        },
    }


def _layout() -> dict:
    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "layout_kind": "planar_mirrored_parallel_headers",
        "plane": "xy",
        "boundary_policy": "open_common_supply_and_return",
        "split_manifold": {
            "branch_gap_mm": 20.0,
            "end_gap_mm": 25.0,
            "branch_stub_length_mm": 80.0,
            "cap_thickness_mm": 8.0,
        },
        "merge_manifold": {
            "branch_gap_mm": 20.0,
            "end_gap_mm": 30.0,
            "branch_stub_length_mm": 90.0,
            "cap_thickness_mm": 10.0,
        },
        "branch_route": {
            "steps": [
                {"kind": "straight", "length_mm": 10000.0, "illumination": "illuminated"},
                {"kind": "bend", "turn": "left", "illumination": "illuminated"},
                {"kind": "straight", "length_mm": 2000.0, "illumination": "dark"},
                {"kind": "bend", "turn": "right", "illumination": "dark"},
            ]
        },
    }


def _expect_error(code: str, function, *args) -> None:
    with pytest.raises(TopologyCadLinkError) as exc_info:
        function(*args)
    assert exc_info.value.code == code


def test_layout_schema_and_python_contract_match() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == LAYOUT_SCHEMA_VERSION
    assert schema["additionalProperties"] is False
    assert schema["properties"]["branch_route"]["properties"]["steps"]["maxItems"] == 129
    assert set(schema["$defs"]["manifold_layout"]["required"]) == {
        "branch_gap_mm",
        "end_gap_mm",
        "branch_stub_length_mm",
        "cap_thickness_mm",
    }
    assert canonicalize_layout_spec(_layout()) == _layout()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda layout: layout.__setitem__("unknown", 1),
        lambda layout: layout["split_manifold"].__setitem__("unknown", 1),
        lambda layout: layout["branch_route"]["steps"][0].__setitem__("unit", "mm"),
        lambda layout: layout["split_manifold"].__setitem__("branch_gap_mm", 0.0),
        lambda layout: layout["split_manifold"].__setitem__("branch_gap_mm", True),
        lambda layout: layout["split_manifold"].__setitem__("branch_gap_mm", "20"),
        lambda layout: layout["split_manifold"].__setitem__("branch_gap_mm", float("inf")),
        lambda layout: layout.__setitem__("plane", "xz"),
        lambda layout: layout["branch_route"].__setitem__("steps", []),
    ],
)
def test_closed_layout_rejects_unknown_or_invalid_values(mutation) -> None:
    layout = _layout()
    mutation(layout)
    with pytest.raises(TopologyCadLinkError):
        canonicalize_layout_spec(layout)


def test_redundant_adjacent_straights_are_rejected() -> None:
    layout = _layout()
    layout["branch_route"]["steps"] = [
        {"kind": "straight", "length_mm": 4000.0, "illumination": "illuminated"},
        {"kind": "straight", "length_mm": 6000.0, "illumination": "illuminated"},
        {"kind": "bend", "turn": "left", "illumination": "illuminated"},
        {"kind": "straight", "length_mm": 2000.0, "illumination": "dark"},
        {"kind": "bend", "turn": "right", "illumination": "dark"},
    ]
    _expect_error("cad_link_layout_mismatch", canonicalize_layout_spec, layout)


def test_transform_has_exact_order_connections_and_right_bend_traversal() -> None:
    manifest = _manifest()
    layout = _layout()
    manifest_before = deepcopy(manifest)
    layout_before = deepcopy(layout)
    result = transform_topology_manifest(manifest, layout)
    spec = result["resolved_geometry_spec"]

    assert manifest == manifest_before
    assert layout == layout_before
    assert [part["part_id"] for part in spec["parts"]] == [
        "split_manifold",
        "common_supply",
        "branch_1_step_1",
        "branch_1_step_2",
        "branch_1_step_3",
        "branch_1_step_4",
        "branch_2_step_1",
        "branch_2_step_2",
        "branch_2_step_3",
        "branch_2_step_4",
        "merge_manifold",
        "common_return",
    ]
    assert {"from": "common_supply.port_b", "to": "split_manifold.common"} in spec["connections"]
    assert {"from": "common_return.port_b", "to": "merge_manifold.common"} in spec["connections"]
    assert {
        "from": "branch_1_step_3.port_b",
        "to": "branch_1_step_4.port_b",
    } in spec["connections"]
    assert {
        "from": "branch_1_step_4.port_a",
        "to": "merge_manifold.branch_2",
    } in spec["connections"]
    assert {
        "from": "branch_2_step_4.port_a",
        "to": "merge_manifold.branch_1",
    } in spec["connections"]
    assert result["external_boundaries"] == {
        "common_supply_boundary": "common_supply.port_a",
        "common_return_boundary": "common_return.port_a",
    }
    assert result["part_count"] == 12
    assert result["connection_count"] == 12
    assert result["layout_digest"].startswith("sha256:")
    assert result["resolved_spec_digest"] == spec["spec_id"]


def test_zero_common_lengths_omit_parts_and_remap_boundaries() -> None:
    manifest = _manifest(
        branch_count=1,
        bend_count=0,
        illuminated_bends=0,
        dark_straight_m=0.0,
        common_supply_m=0.0,
        common_return_m=0.0,
    )
    layout = _layout()
    layout["merge_manifold"]["branch_gap_mm"] = 25.0
    layout["branch_route"]["steps"] = [
        {"kind": "straight", "length_mm": 10000.0, "illumination": "illuminated"}
    ]
    result = transform_topology_manifest(manifest, layout)
    assert [part["part_id"] for part in result["resolved_geometry_spec"]["parts"]] == [
        "split_manifold",
        "branch_1_step_1",
        "merge_manifold",
    ]
    assert result["external_boundaries"] == {
        "common_supply_boundary": "split_manifold.common",
        "common_return_boundary": "merge_manifold.common",
    }


def test_multi_branch_pitch_must_match_exactly() -> None:
    layout = _layout()
    layout["merge_manifold"]["branch_gap_mm"] = 20.0000001
    _expect_error("cad_link_layout_mismatch", transform_topology_manifest, _manifest(), layout)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda layout: layout["branch_route"]["steps"].pop(),
        lambda layout: layout["branch_route"]["steps"][0].__setitem__("length_mm", 9999.0),
        lambda layout: layout["branch_route"]["steps"][1].__setitem__("illumination", "dark"),
    ],
)
def test_route_aggregates_must_match_manifest(mutator) -> None:
    layout = _layout()
    mutator(layout)
    _expect_error("cad_link_layout_mismatch", transform_topology_manifest, _manifest(), layout)


def test_step_and_resolved_part_complexity_bounds_fail_closed() -> None:
    layout = _layout()
    layout["branch_route"]["steps"] = [
        {"kind": "bend", "turn": "left", "illumination": "dark"}
        for _ in range(130)
    ]
    _expect_error("cad_link_layout_complexity_unsupported", canonicalize_layout_spec, layout)

    manifest = _manifest(
        branch_count=12,
        bend_count=22,
        illuminated_bends=0,
        illuminated_straight_m=0.0,
        dark_straight_m=0.0,
    )
    layout = _layout()
    layout["branch_route"]["steps"] = [
        {"kind": "bend", "turn": "left", "illumination": "dark"}
        for _ in range(22)
    ]
    _expect_error(
        "cad_link_layout_complexity_unsupported",
        transform_topology_manifest,
        manifest,
        layout,
    )
