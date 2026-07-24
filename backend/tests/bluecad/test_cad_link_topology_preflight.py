from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology_contract import (
    BOUNDARY_POLICY,
    LAYOUT_KIND,
    LAYOUT_SCHEMA_VERSION,
    canonicalize_layout,
    resolve_geometry_spec,
)
from app.modules.bluecad.cad_link_topology_preflight import run_kernel_preflight


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "bluerev_process_topology_m1_v0_1",
        "topology_kind": "symmetric_parallel_closed_loop",
        "executed_inputs": {
            "parallel_path_count": {"value": 2, "unit": "1"},
            "branch_illuminated_straight_length": {"value": 0.5, "unit": "m"},
            "branch_dark_straight_length": {"value": 0.0, "unit": "m"},
            "branch_bend_count": {"value": 0, "unit": "1"},
            "branch_illuminated_bend_count": {"value": 0, "unit": "1"},
            "branch_bend_centerline_radius": {"value": 0.0, "unit": "mm"},
            "branch_bend_angle": {"value": 0.0, "unit": "deg"},
            "common_supply_length": {"value": 0.0, "unit": "m"},
            "common_return_length": {"value": 0.0, "unit": "m"},
            "branch_tube_inner_diameter": {"value": 50.0, "unit": "mm"},
            "branch_tube_outer_diameter": {"value": 60.0, "unit": "mm"},
            "common_tube_inner_diameter": {"value": 80.0, "unit": "mm"},
            "common_tube_outer_diameter": {"value": 90.0, "unit": "mm"},
            "split_manifold_liquid_volume": {"value": 1.0, "unit": "L"},
            "merge_manifold_liquid_volume": {"value": 1.0, "unit": "L"},
        },
    }


def _layout() -> dict[str, object]:
    manifold = {
        "branch_gap_mm": 20.0,
        "end_gap_mm": 20.0,
        "branch_stub_length_mm": 80.0,
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
                    "length_mm": 500.0,
                    "illumination": "illuminated",
                }
            ]
        },
    }


def _resolved() -> tuple[dict[str, object], dict[str, str]]:
    manifest = _manifest()
    layout = canonicalize_layout(manifest, _layout())
    spec, boundaries, _ = resolve_geometry_spec(manifest, layout)
    return spec, boundaries


def test_kernel_preflight_closes_parallel_headers_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("build123d", exc_type=ImportError)
    spec, boundaries = _resolved()
    monkeypatch.chdir(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    evidence = run_kernel_preflight(spec, boundaries)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before
    assert evidence["part_count"] == 4
    assert evidence["connection_count"] == 4
    assert evidence["open_endpoints"] == sorted(boundaries.values())
    assert evidence["manifold_cavities"]["split_manifold"]["volume_mm3"] > 0.0
    assert evidence["manifold_cavities"]["merge_manifold"]["volume_mm3"] > 0.0
    assert len(evidence["contact_pairs"]) == 4
    assert all(pair["declared_connection"] for pair in evidence["contact_pairs"])
    assert all(
        check["brep_valid"] and check["manifold"]
        for check in evidence["kernel_checks"].values()
    )


def test_kernel_preflight_rejects_duplicate_boundary() -> None:
    spec, boundaries = _resolved()
    invalid = deepcopy(boundaries)
    invalid["common_return_boundary"] = invalid["common_supply_boundary"]

    with pytest.raises(CadLinkError) as exc_info:
        run_kernel_preflight(spec, invalid)

    assert exc_info.value.code == "cad_link_layout_not_closable"


def test_kernel_preflight_timeout_fails_closed() -> None:
    pytest.importorskip("build123d", exc_type=ImportError)
    spec, boundaries = _resolved()

    with pytest.raises(CadLinkError) as exc_info:
        run_kernel_preflight(spec, boundaries, timeout_s=0.0)

    assert exc_info.value.code in {
        "cad_link_kernel_timeout",
        "cad_link_kernel_unavailable",
    }
