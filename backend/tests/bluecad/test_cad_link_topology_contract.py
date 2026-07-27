import copy
import json
from pathlib import Path

import pytest

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology_contract import (
    BOUNDARY_POLICY,
    GEOMETRY_NAME,
    LAYOUT_KIND,
    LAYOUT_SCHEMA_VERSION,
    canonicalize_layout,
    resolve_geometry_spec,
)


def _manifest() -> dict[str, object]:
    fixture = (
        Path(__file__).parents[1]
        / "fixtures"
        / "bluerev_process_topology_m1_valid.json"
    )
    return {
        "schema_version": "bluerev_process_topology_m1_v0_1",
        "topology_kind": "symmetric_parallel_closed_loop",
        "executed_inputs": json.loads(fixture.read_text(encoding="utf-8")),
    }


def _layout() -> dict[str, object]:
    manifold = {
        "branch_gap_mm": 25.0,
        "end_gap_mm": 15.0,
        "branch_stub_length_mm": 20.0,
        "cap_thickness_mm": 8.0,
    }
    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "layout_kind": LAYOUT_KIND,
        "plane": "xy",
        "boundary_policy": BOUNDARY_POLICY,
        "split_manifold": dict(manifold),
        "merge_manifold": dict(manifold),
        "branch_route": {
            "steps": [
                {
                    "kind": "straight",
                    "length_mm": 10000.0,
                    "illumination": "illuminated",
                },
                {"kind": "bend", "turn": "left", "illumination": "illuminated"},
                {
                    "kind": "straight",
                    "length_mm": 2000.0,
                    "illumination": "dark",
                },
                {"kind": "bend", "turn": "right", "illumination": "dark"},
            ]
        },
    }


def test_layout_resolves_exact_part_order_connections_and_boundaries() -> None:
    manifest = _manifest()
    canonical = canonicalize_layout(manifest, _layout())
    spec, boundaries, inventory = resolve_geometry_spec(manifest, canonical)

    assert spec["name"] == GEOMETRY_NAME
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
    assert {
        "from": "branch_1_step_4.port_a",
        "to": "merge_manifold.branch_2",
    } in spec["connections"]
    assert {
        "from": "branch_2_step_4.port_a",
        "to": "merge_manifold.branch_1",
    } in spec["connections"]
    assert boundaries == {
        "common_supply_boundary": "common_supply.port_a",
        "common_return_boundary": "common_return.port_a",
    }
    assert inventory["excluded"] == [
        "pump",
        "reservoir_vessel",
        "supports",
        "floats",
        "anchors",
        "instrumentation",
    ]


def test_right_bend_uses_reverse_existing_port_traversal() -> None:
    manifest = _manifest()
    canonical = canonicalize_layout(manifest, _layout())
    spec, _, _ = resolve_geometry_spec(manifest, canonical)

    assert {
        "from": "branch_1_step_3.port_b",
        "to": "branch_1_step_4.port_b",
    } in spec["connections"]
    assert {
        "from": "branch_1_step_4.port_a",
        "to": "merge_manifold.branch_2",
    } in spec["connections"]


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("extra", "cad_link_layout_schema_invalid"),
        ("pitch", "cad_link_layout_mismatch"),
        ("straight_total", "cad_link_layout_mismatch"),
        ("bend_count", "cad_link_layout_mismatch"),
        ("boolean", "cad_link_numeric_invalid"),
        ("string", "cad_link_numeric_invalid"),
        ("adjacent", "cad_link_layout_mismatch"),
    ],
)
def test_layout_fails_closed(mutation: str, code: str) -> None:
    manifest = _manifest()
    layout = _layout()
    if mutation == "extra":
        layout["unexpected"] = True
    elif mutation == "pitch":
        layout["merge_manifold"]["branch_gap_mm"] = 30.0
    elif mutation == "straight_total":
        layout["branch_route"]["steps"][0]["length_mm"] = 9999.0
    elif mutation == "bend_count":
        layout["branch_route"]["steps"].pop()
    elif mutation == "boolean":
        layout["split_manifold"]["end_gap_mm"] = True
    elif mutation == "string":
        layout["split_manifold"]["end_gap_mm"] = "15 mm"
    elif mutation == "adjacent":
        layout["branch_route"]["steps"].insert(
            1,
            {
                "kind": "straight",
                "length_mm": 1.0,
                "illumination": "illuminated",
            },
        )

    with pytest.raises(CadLinkError) as exc_info:
        canonicalize_layout(manifest, layout)
    assert exc_info.value.code == code


def test_zero_common_lengths_remap_boundaries_and_omit_parts() -> None:
    manifest = _manifest()
    manifest["executed_inputs"]["common_supply_length"]["value"] = 0.0
    manifest["executed_inputs"]["common_return_length"]["value"] = 0.0
    canonical = canonicalize_layout(manifest, _layout())
    spec, boundaries, _ = resolve_geometry_spec(manifest, canonical)

    assert "common_supply" not in {part["part_id"] for part in spec["parts"]}
    assert "common_return" not in {part["part_id"] for part in spec["parts"]}
    assert boundaries == {
        "common_supply_boundary": "split_manifold.common",
        "common_return_boundary": "merge_manifold.common",
    }


def test_resolved_part_bound_fails_without_simplification() -> None:
    manifest = _manifest()
    inputs = manifest["executed_inputs"]
    inputs["parallel_path_count"]["value"] = 12
    inputs["branch_bend_count"]["value"] = 22
    inputs["branch_illuminated_bend_count"]["value"] = 11
    layout = _layout()
    layout["branch_route"]["steps"] = [
        {
            "kind": "straight",
            "length_mm": 10000.0,
            "illumination": "illuminated",
        },
        {
            "kind": "straight",
            "length_mm": 2000.0,
            "illumination": "dark",
        },
    ] + [
        {
            "kind": "bend",
            "turn": "left" if index % 2 == 0 else "right",
            "illumination": "illuminated" if index < 11 else "dark",
        }
        for index in range(22)
    ]

    with pytest.raises(CadLinkError) as exc_info:
        canonicalize_layout(manifest, layout)
    assert exc_info.value.code == "cad_link_layout_complexity_unsupported"


def test_canonicalization_does_not_mutate_manifest_or_request() -> None:
    manifest = _manifest()
    layout = _layout()
    original_manifest = copy.deepcopy(manifest)
    original_layout = copy.deepcopy(layout)

    canonicalize_layout(manifest, layout)

    assert manifest == original_manifest
    assert layout == original_layout
