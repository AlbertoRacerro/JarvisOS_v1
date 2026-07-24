"""Bounded in-memory kernel preflight for CAD-LINK-1."""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import queue
from collections import Counter
from collections.abc import Mapping
from itertools import combinations
from typing import Any

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.models import BluecadError, BuiltPart, PortFrame
from app.modules.bluecad.spec import canonicalize_geometry_spec

PREFLIGHT_TIMEOUT_SECONDS = 30.0
INTERFERENCE_ABS_TOL_MM3 = 1e-6
COINCIDENCE_ABS_TOL_MM = 1e-6
CONTACT_AREA_REL_TOL = 1e-6
CONTACT_AREA_ABS_TOL_MM2 = 1e-6
MAX_EVIDENCE_BYTES = 2_000_000


def run_kernel_preflight(
    resolved_spec: Mapping[str, Any],
    boundaries: Mapping[str, str],
    *,
    timeout_s: float = PREFLIGHT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one isolated, file-free build123d preflight and return bounded JSON evidence."""

    canonical_spec = canonicalize_geometry_spec(resolved_spec)
    canonical_boundaries = _canonical_boundaries(boundaries)
    result_queue: mp.Queue[dict[str, Any]] = mp.Queue(maxsize=1)
    process = mp.Process(
        target=_preflight_worker,
        args=(canonical_spec, canonical_boundaries, result_queue),
        daemon=True,
    )
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.kill()
        process.join()
        raise CadLinkError(
            "cad_link_kernel_timeout",
            "CAD-link kernel preflight timed out.",
            status_code=504,
        )
    try:
        payload = result_queue.get_nowait()
    except queue.Empty as exc:
        raise CadLinkError(
            "cad_link_kernel_unavailable",
            "CAD-link kernel preflight exited without bounded evidence.",
            status_code=503,
        ) from exc
    if not isinstance(payload, dict) or type(payload.get("ok")) is not bool:
        raise CadLinkError(
            "cad_link_kernel_unavailable",
            "CAD-link kernel preflight returned malformed evidence.",
            status_code=503,
        )
    if not payload["ok"]:
        raise CadLinkError(
            str(payload.get("code") or "cad_link_kernel_unavailable"),
            str(payload.get("message") or "CAD-link kernel preflight failed."),
            status_code=int(payload.get("status_code") or 503),
        )
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        raise CadLinkError(
            "cad_link_kernel_unavailable",
            "CAD-link kernel preflight returned malformed evidence.",
            status_code=503,
        )
    _assert_finite_json(evidence)
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise CadLinkError(
            "cad_link_kernel_evidence_too_large",
            "CAD-link kernel evidence exceeds the bounded response size.",
            status_code=503,
        )
    return evidence


def _preflight_worker(
    resolved_spec: dict[str, Any],
    boundaries: dict[str, str],
    result_queue: mp.Queue[dict[str, Any]],
) -> None:
    try:
        evidence = _build_preflight_evidence(resolved_spec, boundaries)
    except CadLinkError as exc:
        result_queue.put(
            {
                "ok": False,
                "code": exc.code,
                "message": exc.message,
                "status_code": exc.status_code,
            }
        )
    except BluecadError as exc:
        code = (
            "cad_link_layout_not_closable"
            if exc.code == "PORT_MISMATCH"
            else "cad_link_kernel_unavailable"
        )
        result_queue.put(
            {
                "ok": False,
                "code": code,
                "message": "CAD assembly preflight failed.",
                "status_code": 422 if exc.code == "PORT_MISMATCH" else 503,
            }
        )
    except ImportError:
        result_queue.put(
            {
                "ok": False,
                "code": "cad_link_kernel_unavailable",
                "message": "The required CAD kernel is unavailable.",
                "status_code": 503,
            }
        )
    except Exception:
        result_queue.put(
            {
                "ok": False,
                "code": "cad_link_kernel_unavailable",
                "message": "CAD-link kernel preflight failed without safe evidence.",
                "status_code": 503,
            }
        )


def _build_preflight_evidence(
    resolved_spec: dict[str, Any],
    boundaries: dict[str, str],
) -> dict[str, Any]:
    from app.modules.bluecad.assembly import assemble_parts
    from app.modules.bluecad.builders import build_part
    from app.modules.bluecad.capped_manifold import build_capped_manifold_kernel

    spec = canonicalize_geometry_spec(resolved_spec)
    parts = assemble_parts(spec)
    part_specs = {item["part_id"]: item for item in spec["parts"]}
    endpoint_counts = Counter(
        connection[key]
        for connection in spec.get("connections", [])
        for key in ("from", "to")
    )
    all_endpoints = {
        f"{part_id}.{port_name}"
        for part_id, part in parts.items()
        for port_name in part.ports
    }
    unknown_endpoints = sorted(set(endpoint_counts) - all_endpoints)
    if unknown_endpoints or any(count != 1 for count in endpoint_counts.values()):
        raise CadLinkError(
            "cad_link_layout_not_closable",
            "Assembly connection endpoints are not used exactly once.",
            status_code=422,
        )
    open_endpoints = sorted(all_endpoints - set(endpoint_counts))
    if open_endpoints != sorted(boundaries.values()):
        raise CadLinkError(
            "cad_link_layout_not_closable",
            "Assembly does not expose exactly the two declared external boundaries.",
            status_code=422,
        )

    kernel_checks = {
        part_id: {
            "brep_valid": _shape_flag(part.shape, "is_valid"),
            "manifold": _shape_flag(part.shape, "is_manifold"),
        }
        for part_id, part in parts.items()
    }
    if not all(
        item["brep_valid"] and item["manifold"] for item in kernel_checks.values()
    ):
        raise CadLinkError(
            "cad_link_geometry_invalid",
            "One or more placed parts failed BREP or manifold validation.",
            status_code=422,
        )

    placed_frames: dict[str, dict[str, Any]] = {}
    for part_id, placed in parts.items():
        local = build_part(part_specs[part_id])
        rotation, translation = _infer_placement(local, placed)
        placed_frames[part_id] = {
            "rotation_z_rad": rotation,
            "translation_mm": list(translation),
        }

    cavity_evidence: dict[str, dict[str, Any]] = {}
    for part_id in ("split_manifold", "merge_manifold"):
        kernel = build_capped_manifold_kernel(part_specs[part_id])
        rotation = float(placed_frames[part_id]["rotation_z_rad"])
        translation = tuple(
            float(value) for value in placed_frames[part_id]["translation_mm"]
        )
        placed_void = _place_shape(kernel.void_shape, rotation, translation)
        cavity_evidence[part_id] = {
            "volume_mm3": _finite(float(placed_void.volume)),
            "brep_valid": _shape_flag(placed_void, "is_valid"),
        }
        if (
            cavity_evidence[part_id]["volume_mm3"] <= 0.0
            or not cavity_evidence[part_id]["brep_valid"]
        ):
            raise CadLinkError(
                "cad_link_manifold_volume_unrepresentable",
                "A manifold fluid cavity is not a positive valid BREP.",
                status_code=422,
            )

    declared_pairs: dict[frozenset[str], list[dict[str, str]]] = {}
    for connection in spec.get("connections", []):
        left_id = connection["from"].split(".", 1)[0]
        right_id = connection["to"].split(".", 1)[0]
        declared_pairs.setdefault(frozenset((left_id, right_id)), []).append(connection)

    pair_diagnostics: list[dict[str, Any]] = []
    for left_id, right_id in combinations(parts, 2):
        left = parts[left_id]
        right = parts[right_id]
        pair_key = frozenset((left_id, right_id))
        connections = declared_pairs.get(pair_key, [])
        connected = bool(connections)
        if len(connections) > 1:
            raise CadLinkError(
                "cad_link_layout_not_closable",
                "A material-part pair has multiple declared connections.",
                status_code=422,
            )
        if not _bbox_may_contact(left.bbox_mm, right.bbox_mm):
            if connected:
                raise CadLinkError(
                    "cad_link_layout_contact_invalid",
                    "Declared connected parts have disjoint material bounds.",
                    status_code=422,
                )
            continue
        topology = _intersection_evidence(_shape_intersection(left.shape, right.shape))
        if topology["volume_mm3"] > INTERFERENCE_ABS_TOL_MM3:
            raise CadLinkError(
                "cad_link_layout_collision",
                "Placed parts have positive-volume interference.",
                status_code=422,
            )
        has_contact = any(
            topology[key] > 0 for key in ("face_count", "edge_count", "vertex_count")
        )
        if connected:
            _validate_declared_contact(parts, connections[0], topology)
        elif has_contact:
            raise CadLinkError(
                "cad_link_layout_contact_invalid",
                "Non-connected parts share a face, edge, or vertex.",
                status_code=422,
            )
        if connected or has_contact:
            pair_diagnostics.append(
                {
                    "part_a": left_id,
                    "part_b": right_id,
                    "declared_connection": connected,
                    **topology,
                }
            )

    bbox_min = [
        min(part.bbox_mm[0][axis] for part in parts.values()) for axis in range(3)
    ]
    bbox_max = [
        max(part.bbox_mm[1][axis] for part in parts.values()) for axis in range(3)
    ]
    evidence = {
        "worker_timeout_seconds": PREFLIGHT_TIMEOUT_SECONDS,
        "part_count": len(parts),
        "connection_count": len(spec.get("connections", [])),
        "external_boundaries": boundaries,
        "open_endpoints": open_endpoints,
        "kernel_checks": kernel_checks,
        "manifold_cavities": cavity_evidence,
        "assembly_material_volume_mm3": _finite(
            sum(part.volume_mm3 for part in parts.values())
        ),
        "assembly_bbox_mm": {"min": bbox_min, "max": bbox_max},
        "placed_parts": {
            part_id: {
                "frame": placed_frames[part_id],
                "bbox_mm": {
                    "min": list(part.bbox_mm[0]),
                    "max": list(part.bbox_mm[1]),
                },
                "ports": {
                    name: port.as_dict() for name, port in sorted(part.ports.items())
                },
            }
            for part_id, part in parts.items()
        },
        "contact_pairs": pair_diagnostics,
        "positive_interference_tolerance_mm3": INTERFERENCE_ABS_TOL_MM3,
    }
    _assert_finite_json(evidence)
    return evidence


def _canonical_boundaries(boundaries: Mapping[str, str]) -> dict[str, str]:
    expected_keys = {"common_supply_boundary", "common_return_boundary"}
    if not isinstance(boundaries, Mapping) or set(boundaries) != expected_keys:
        raise CadLinkError(
            "cad_link_layout_not_closable",
            "Exactly two semantic external boundaries are required.",
            status_code=422,
        )
    normalized: dict[str, str] = {}
    for key in sorted(expected_keys):
        value = boundaries[key]
        if not isinstance(value, str) or value.count(".") != 1:
            raise CadLinkError(
                "cad_link_layout_not_closable",
                "External boundary endpoints are invalid.",
                status_code=422,
            )
        normalized[key] = value
    if len(set(normalized.values())) != 2:
        raise CadLinkError(
            "cad_link_layout_not_closable",
            "External boundaries must resolve to two distinct ports.",
            status_code=422,
        )
    return normalized


def _infer_placement(
    local: BuiltPart,
    placed: BuiltPart,
) -> tuple[float, tuple[float, float, float]]:
    port_name = sorted(local.ports)[0]
    local_port = local.ports[port_name]
    placed_port = placed.ports[port_name]
    rotation = math.atan2(placed_port.direction[1], placed_port.direction[0]) - math.atan2(
        local_port.direction[1], local_port.direction[0]
    )
    rotated_origin = _rotate(local_port.origin, rotation)
    translation = tuple(
        placed_port.origin[axis] - rotated_origin[axis] for axis in range(3)
    )
    for name, candidate in local.ports.items():
        transformed = candidate.transformed(rotation, translation)
        expected = placed.ports[name]
        if not _ports_match(transformed, expected):
            raise CadLinkError(
                "cad_link_layout_not_closable",
                "Placed part frame could not be reconstructed consistently.",
                status_code=422,
            )
    return _finite(rotation), tuple(_finite(value) for value in translation)


def _place_shape(
    shape: Any,
    rotation_z_rad: float,
    translation: tuple[float, float, float],
) -> Any:
    import build123d as bd

    return bd.Pos(*translation) * bd.Rot(Z=math.degrees(rotation_z_rad)) * shape


def _validate_declared_contact(
    parts: Mapping[str, BuiltPart],
    connection: Mapping[str, str],
    topology: Mapping[str, Any],
) -> None:
    left_id, left_port_name = connection["from"].split(".", 1)
    right_id, right_port_name = connection["to"].split(".", 1)
    left_port = parts[left_id].ports[left_port_name]
    right_port = parts[right_id].ports[right_port_name]
    if not _ports_mate(left_port, right_port):
        raise CadLinkError(
            "cad_link_layout_contact_invalid",
            "Declared connection ports are not coincident, opposed, and conformant.",
            status_code=422,
        )
    outer_d = float(left_port.outer_d or 0.0)
    wall_t = float(left_port.wall_t or 0.0)
    inner_d = outer_d - 2.0 * wall_t
    expected_area = math.pi / 4.0 * (outer_d**2 - inner_d**2)
    if topology["face_count"] < 1 or not math.isclose(
        float(topology["face_area_mm2"]),
        expected_area,
        rel_tol=CONTACT_AREA_REL_TOL,
        abs_tol=CONTACT_AREA_ABS_TOL_MM2,
    ):
        raise CadLinkError(
            "cad_link_layout_contact_invalid",
            "Declared connection contact is not the intended annular mating boundary.",
            status_code=422,
        )


def _ports_mate(left: PortFrame, right: PortFrame) -> bool:
    return (
        _points_close(left.origin, right.origin)
        and _directions_opposed(left.direction, right.direction)
        and left.interface == right.interface == "tube"
        and math.isclose(float(left.outer_d), float(right.outer_d), rel_tol=1e-12)
        and math.isclose(float(left.wall_t), float(right.wall_t), rel_tol=1e-12)
    )


def _ports_match(left: PortFrame, right: PortFrame) -> bool:
    return (
        _points_close(left.origin, right.origin)
        and all(
            math.isclose(left.direction[index], right.direction[index], abs_tol=1e-9)
            for index in range(3)
        )
        and left.interface == right.interface
        and left.outer_d == right.outer_d
        and left.wall_t == right.wall_t
        and left.pad_d == right.pad_d
    )


def _points_close(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> bool:
    return all(
        math.isclose(left[index], right[index], abs_tol=COINCIDENCE_ABS_TOL_MM)
        for index in range(3)
    )


def _directions_opposed(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> bool:
    return all(
        math.isclose(left[index], -right[index], abs_tol=1e-9)
        for index in range(3)
    )


def _rotate(
    value: tuple[float, float, float],
    angle: float,
) -> tuple[float, float, float]:
    cos_t = math.cos(angle)
    sin_t = math.sin(angle)
    return (
        cos_t * value[0] - sin_t * value[1],
        sin_t * value[0] + cos_t * value[1],
        value[2],
    )


def _shape_intersection(left: Any, right: Any) -> Any:
    try:
        return left.intersect(right)
    except (AttributeError, TypeError):
        return left & right


def _intersection_evidence(intersection: Any) -> dict[str, Any]:
    if intersection is None:
        return {
            "volume_mm3": 0.0,
            "face_count": 0,
            "edge_count": 0,
            "vertex_count": 0,
            "face_area_mm2": 0.0,
        }
    faces = list(intersection.faces()) if hasattr(intersection, "faces") else []
    edges = list(intersection.edges()) if hasattr(intersection, "edges") else []
    vertices = list(intersection.vertices()) if hasattr(intersection, "vertices") else []
    return {
        "volume_mm3": _finite(float(getattr(intersection, "volume", 0.0) or 0.0)),
        "face_count": len(faces),
        "edge_count": len(edges),
        "vertex_count": len(vertices),
        "face_area_mm2": _finite(
            sum(float(getattr(face, "area", 0.0) or 0.0) for face in faces)
        ),
    }


def _bbox_may_contact(
    left: tuple[tuple[float, float, float], tuple[float, float, float]],
    right: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> bool:
    return all(
        left[1][axis] + COINCIDENCE_ABS_TOL_MM >= right[0][axis]
        and right[1][axis] + COINCIDENCE_ABS_TOL_MM >= left[0][axis]
        for axis in range(3)
    )


def _shape_flag(shape: Any, attribute: str) -> bool:
    value = getattr(shape, attribute, False)
    return bool(value() if callable(value) else value)


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise CadLinkError(
            "cad_link_kernel_unavailable",
            "CAD-link kernel produced a non-finite value.",
            status_code=503,
        )
    return value


def _assert_finite_json(value: Any) -> None:
    if value is None or isinstance(value, str | bool | int):
        return
    if isinstance(value, float):
        _finite(value)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _assert_finite_json(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CadLinkError(
                    "cad_link_kernel_unavailable",
                    "CAD-link kernel evidence has non-string object keys.",
                    status_code=503,
                )
            _assert_finite_json(item)
        return
    raise CadLinkError(
        "cad_link_kernel_unavailable",
        "CAD-link kernel evidence contains an unsupported value.",
        status_code=503,
    )
