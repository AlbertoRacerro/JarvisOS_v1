from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.modules.bluecad import cad_link_topology_preflight as preflight_module
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.cad_link_topology_contract import (
    BOUNDARY_POLICY,
    LAYOUT_KIND,
    LAYOUT_SCHEMA_VERSION,
    canonicalize_layout,
    resolve_geometry_spec,
)
from app.modules.bluecad.cad_link_topology_preflight import (
    _classify_pair_intersection,
    _has_topological_contact,
    _kernel_bbox,
    _validate_port_contact_topology,
    run_kernel_preflight,
)
from app.modules.bluecad.models import PortFrame


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


def _circle_bbox(
    center: tuple[float, float, float],
    direction: tuple[float, float, float],
    radius: float,
) -> dict[str, list[float]]:
    magnitude = math.sqrt(sum(value**2 for value in direction))
    normal = tuple(value / magnitude for value in direction)
    extents = tuple(radius * math.sqrt(max(0.0, 1.0 - normal[axis] ** 2)) for axis in range(3))
    return {
        "min": [center[axis] - extents[axis] for axis in range(3)],
        "max": [center[axis] + extents[axis] for axis in range(3)],
    }


def _edge(
    port: PortFrame,
    radius: float,
    *,
    center: tuple[float, float, float] | None = None,
) -> dict[str, object]:
    origin = port.origin if center is None else center
    return {
        "radius_mm": radius,
        "center_mm": list(origin),
        "bbox_mm": _circle_bbox(origin, port.direction, radius),
    }


def _face(port: PortFrame) -> dict[str, object]:
    outer_radius = float(port.outer_d) / 2.0
    inner_radius = outer_radius - float(port.wall_t)
    return {
        "area_mm2": math.pi * (outer_radius**2 - inner_radius**2),
        "center_mm": list(port.origin),
        "bbox_mm": _circle_bbox(port.origin, port.direction, outer_radius),
    }


def test_kernel_preflight_closes_parallel_headers_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("build123d", exc_type=ImportError)
    spec, boundaries = _resolved()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(preflight_module, "_PREFLIGHT_PARENT_SENTINEL", "parent-only")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    evidence = run_kernel_preflight(spec, boundaries)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before
    assert evidence["spawn_isolated"] is True
    assert evidence["part_count"] == 4
    assert evidence["connection_count"] == 4
    assert evidence["open_endpoints"] == sorted(boundaries.values())
    assert evidence["manifold_cavities"]["split_manifold"]["volume_mm3"] > 0.0
    assert evidence["manifold_cavities"]["merge_manifold"]["volume_mm3"] > 0.0
    assert len(evidence["contact_pairs"]) == 4
    assert all(pair["declared_connection"] for pair in evidence["contact_pairs"])
    assert all(check["brep_valid"] and check["manifold"] for check in evidence["kernel_checks"].values())
    assert all(item["material_volume_mm3"] > 0.0 for item in evidence["placed_parts"].values())
    pair_evaluation = evidence["pair_evaluation"]
    assert pair_evaluation["evaluated_pair_count"] == (pair_evaluation["broad_phase_candidate_count"])
    assert pair_evaluation["total_pair_count"] == (
        pair_evaluation["broad_phase_candidate_count"] + pair_evaluation["broad_phase_skipped_count"]
    )


def test_edge_form_annular_contact_is_accepted() -> None:
    port = PortFrame((1.0, 2.0, 3.0), (1.0, 0.0, 0.0), 60.0, 5.0)
    topology = {
        "vertex_count": 0,
        "edges": [_edge(port, 30.0), _edge(port, 25.0)],
        "faces": [],
    }

    _validate_port_contact_topology(port, topology)


def test_face_form_annular_contact_is_accepted() -> None:
    port = PortFrame((1.0, 2.0, 3.0), (0.0, 1.0, 0.0), 60.0, 5.0)
    topology = {
        "vertex_count": 0,
        "edges": [],
        "faces": [_face(port)],
    }

    _validate_port_contact_topology(port, topology)


@pytest.mark.parametrize("mutation", ["extra_radius", "off_center", "vertex", "off_plane"])
def test_invalid_contact_outside_annulus_is_rejected(mutation: str) -> None:
    port = PortFrame((1.0, 2.0, 3.0), (1.0, 0.0, 0.0), 60.0, 5.0)
    edges = [_edge(port, 30.0), _edge(port, 25.0)]
    topology: dict[str, Any] = {
        "vertex_count": 0,
        "edges": edges,
        "faces": [],
    }
    if mutation == "extra_radius":
        edges.append(_edge(port, 35.0))
    elif mutation == "off_center":
        edges[0] = _edge(port, 30.0, center=(1.0, 2.1, 3.0))
    elif mutation == "vertex":
        topology["vertex_count"] = 1
    elif mutation == "off_plane":
        edges[0] = _edge(port, 30.0, center=(1.1, 2.0, 3.0))

    with pytest.raises(CadLinkError) as exc_info:
        _validate_port_contact_topology(port, topology)

    assert exc_info.value.code == "cad_link_layout_contact_invalid"


class _ExplodingTopology:
    volume = 1.0

    def faces(self):
        raise AssertionError("topology must not be enumerated before volume rejection")


class _ShapeWithIntersection:
    def intersect(self, _other):
        return _ExplodingTopology()


def test_positive_volume_collision_is_classified_before_topology_enumeration() -> None:
    with pytest.raises(CadLinkError) as exc_info:
        _classify_pair_intersection(_ShapeWithIntersection(), object())

    assert exc_info.value.code == "cad_link_layout_collision"


class _Vector:
    def __init__(self, x: float, y: float, z: float):
        self.X = x
        self.Y = y
        self.Z = z


class _ShapeWithBounds:
    def __init__(self):
        self._bbox = SimpleNamespace(
            min=_Vector(-10.0, -20.0, -30.0),
            max=_Vector(40.0, 50.0, 60.0),
        )

    def bounding_box(self):
        return self._bbox


def test_kernel_bbox_uses_shape_extrema() -> None:
    assert _kernel_bbox(_ShapeWithBounds()) == (
        (-10.0, -20.0, -30.0),
        (40.0, 50.0, 60.0),
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


def test_positive_submicron_gap_is_not_classified_as_contact() -> None:
    topology = {
        "minimum_distance_mm": 5e-7,
        "face_count": 0,
        "edge_count": 0,
        "vertex_count": 0,
    }

    assert _has_topological_contact(topology) is False


def test_actual_topological_contact_is_classified() -> None:
    topology = {
        "minimum_distance_mm": 0.0,
        "face_count": 0,
        "edge_count": 0,
        "vertex_count": 1,
    }

    assert _has_topological_contact(topology) is True
