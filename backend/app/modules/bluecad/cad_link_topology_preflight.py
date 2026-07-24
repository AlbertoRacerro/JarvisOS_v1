"""Bounded in-memory kernel preflight for CAD-LINK-1."""

from __future__ import annotations

import json
import math
import multiprocessing as mp
from collections import Counter
from collections.abc import Callable, Mapping
from itertools import combinations
from typing import Any

from app.modules.bluecad.cad_link import CadLinkError
from app.modules.bluecad.models import BluecadError, BuiltPart, PortFrame
from app.modules.bluecad.spec import canonicalize_geometry_spec

PREFLIGHT_TIMEOUT_SECONDS = 30.0
INTERFERENCE_ABS_TOL_MM3 = 1e-6
COINCIDENCE_ABS_TOL_MM = 1e-6
CONTACT_RADIUS_ABS_TOL_MM = 1e-6
CONTACT_AREA_REL_TOL = 1e-6
CONTACT_AREA_ABS_TOL_MM2 = 1e-6
CONTACT_NEIGHBORHOOD_AXIAL_MM = 1e-4
CONTACT_NEIGHBORHOOD_RADIAL_MM = 1e-4
MAX_CONTACT_TOPOLOGY_ITEMS = 64
MAX_PART_FACE_COUNT = 128
MAX_EVIDENCE_BYTES = 2_000_000
MAX_WIRE_BYTES = 2_100_000
_WORKER_JOIN_GRACE_SECONDS = 1.0

# Test sentinel: spawn starts with the module default, whereas fork inherits parent mutation.
_PREFLIGHT_PARENT_SENTINEL: str | None = None


def run_kernel_preflight(
    resolved_spec: Mapping[str, Any],
    boundaries: Mapping[str, str],
    *,
    timeout_s: float = PREFLIGHT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one spawned, file-free build123d preflight and return bounded JSON evidence."""

    canonical_spec = canonicalize_geometry_spec(resolved_spec)
    canonical_boundaries = _canonical_boundaries(boundaries)
    payload = _run_spawned_json(
        _preflight_payload,
        (canonical_spec, canonical_boundaries),
        timeout_s=timeout_s,
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
        raise _kernel_unavailable("CAD-link kernel preflight returned malformed evidence.")
    if not payload["ok"]:
        status_code = payload.get("status_code")
        if not isinstance(status_code, int) or isinstance(status_code, bool):
            status_code = 503
        raise CadLinkError(
            str(payload.get("code") or "cad_link_kernel_unavailable"),
            str(payload.get("message") or "CAD-link kernel preflight failed."),
            status_code=status_code,
        )
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        raise _kernel_unavailable("CAD-link kernel preflight returned malformed evidence.")
    _assert_finite_json(evidence)
    encoded = _canonical_json_bytes(evidence)
    if len(encoded) > MAX_EVIDENCE_BYTES:
        raise CadLinkError(
            "cad_link_kernel_evidence_too_large",
            "CAD-link kernel evidence exceeds the bounded response size.",
            status_code=503,
        )
    return evidence


def _run_spawned_json(
    target: Callable[..., dict[str, Any]],
    args: tuple[Any, ...],
    *,
    timeout_s: float,
) -> dict[str, Any]:
    """Run a picklable target under spawn and receive one bounded JSON message."""

    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise _kernel_unavailable("CAD-link kernel timeout is invalid.")
    timeout = float(timeout_s)
    if not math.isfinite(timeout) or timeout < 0.0:
        raise _kernel_unavailable("CAD-link kernel timeout is invalid.")

    context = mp.get_context("spawn")
    receive_conn, send_conn = context.Pipe(duplex=False)
    process = context.Process(
        target=_json_worker_entry,
        args=(target, args, send_conn),
        daemon=True,
    )
    try:
        process.start()
    except Exception as exc:
        receive_conn.close()
        send_conn.close()
        raise _kernel_unavailable("CAD-link kernel worker could not start.") from exc
    finally:
        try:
            send_conn.close()
        except OSError:
            pass

    raw: bytes | None = None
    try:
        if receive_conn.poll(timeout):
            try:
                raw = receive_conn.recv_bytes(MAX_WIRE_BYTES)
            except (EOFError, OSError, ValueError) as exc:
                raise _kernel_unavailable(
                    "CAD-link kernel preflight returned malformed evidence."
                ) from exc
        else:
            if process.is_alive():
                process.kill()
                process.join()
                raise CadLinkError(
                    "cad_link_kernel_timeout",
                    "CAD-link kernel preflight timed out.",
                    status_code=504,
                )
            raise _kernel_unavailable(
                "CAD-link kernel preflight exited without bounded evidence."
            )
    finally:
        receive_conn.close()
        process.join(_WORKER_JOIN_GRACE_SECONDS)
        if process.is_alive():
            process.kill()
            process.join()

    if raw is None:
        raise _kernel_unavailable(
            "CAD-link kernel preflight exited without bounded evidence."
        )
    if process.exitcode not in (0, None):
        raise _kernel_unavailable("CAD-link kernel worker crashed.")
    try:
        text = raw.decode("utf-8")
        payload = json.loads(text, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise _kernel_unavailable(
            "CAD-link kernel preflight returned malformed evidence."
        ) from exc
    if not isinstance(payload, dict):
        raise _kernel_unavailable(
            "CAD-link kernel preflight returned malformed evidence."
        )
    _assert_finite_json(payload)
    return payload


def _json_worker_entry(
    target: Callable[..., dict[str, Any]],
    args: tuple[Any, ...],
    send_conn: Any,
) -> None:
    try:
        try:
            payload = target(*args)
            if not isinstance(payload, dict):
                payload = {
                    "ok": False,
                    "code": "cad_link_kernel_unavailable",
                    "message": "CAD-link kernel preflight returned malformed evidence.",
                    "status_code": 503,
                }
        except Exception:
            payload = {
                "ok": False,
                "code": "cad_link_kernel_unavailable",
                "message": "CAD-link kernel preflight failed without safe evidence.",
                "status_code": 503,
            }
        try:
            raw = _canonical_json_bytes(payload)
        except (TypeError, ValueError, CadLinkError):
            raw = _canonical_json_bytes(
                {
                    "ok": False,
                    "code": "cad_link_kernel_unavailable",
                    "message": "CAD-link kernel preflight returned malformed evidence.",
                    "status_code": 503,
                }
            )
        if len(raw) > MAX_EVIDENCE_BYTES:
            raw = _canonical_json_bytes(
                {
                    "ok": False,
                    "code": "cad_link_kernel_evidence_too_large",
                    "message": "CAD-link kernel evidence exceeds the bounded response size.",
                    "status_code": 503,
                }
            )
        send_conn.send_bytes(raw)
    finally:
        send_conn.close()


def _preflight_payload(
    resolved_spec: dict[str, Any],
    boundaries: dict[str, str],
) -> dict[str, Any]:
    if _PREFLIGHT_PARENT_SENTINEL is not None:
        return {
            "ok": False,
            "code": "cad_link_kernel_unavailable",
            "message": "CAD-link kernel worker inherited parent-only state.",
            "status_code": 503,
        }
    try:
        return {
            "ok": True,
            "evidence": _build_preflight_evidence(resolved_spec, boundaries),
        }
    except CadLinkError as exc:
        return {
            "ok": False,
            "code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code,
        }
    except BluecadError as exc:
        return {
            "ok": False,
            "code": (
                "cad_link_layout_not_closable"
                if exc.code == "PORT_MISMATCH"
                else "cad_link_kernel_unavailable"
            ),
            "message": "CAD assembly preflight failed.",
            "status_code": 422 if exc.code == "PORT_MISMATCH" else 503,
        }
    except ImportError:
        return {
            "ok": False,
            "code": "cad_link_kernel_unavailable",
            "message": "The required CAD kernel is unavailable.",
            "status_code": 503,
        }
    except Exception:
        return {
            "ok": False,
            "code": "cad_link_kernel_unavailable",
            "message": "CAD-link kernel preflight failed without safe evidence.",
            "status_code": 503,
        }


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

    kernel_checks: dict[str, dict[str, bool]] = {}
    placed_frames: dict[str, dict[str, Any]] = {}
    kernel_bboxes: dict[
        str, tuple[tuple[float, float, float], tuple[float, float, float]]
    ] = {}
    material_volumes: dict[str, float] = {}
    for part_id, placed in parts.items():
        kernel_checks[part_id] = {
            "brep_valid": _shape_flag(placed.shape, "is_valid"),
            "manifold": _shape_flag(placed.shape, "is_manifold"),
        }
        if not (
            kernel_checks[part_id]["brep_valid"]
            and kernel_checks[part_id]["manifold"]
        ):
            raise CadLinkError(
                "cad_link_geometry_invalid",
                "One or more placed parts failed BREP or manifold validation.",
                status_code=422,
            )
        local = build_part(part_specs[part_id])
        rotation, translation = _infer_placement(local, placed)
        placed_frames[part_id] = {
            "rotation_z_rad": rotation,
            "translation_mm": list(translation),
        }
        kernel_bboxes[part_id] = _kernel_bbox(placed.shape)
        material_volume = _finite(_shape_volume(placed.shape))
        if material_volume <= 0.0:
            raise CadLinkError(
                "cad_link_geometry_invalid",
                "One or more placed parts has non-positive kernel material volume.",
                status_code=422,
            )
        material_volumes[part_id] = material_volume

    cavity_evidence: dict[str, dict[str, Any]] = {}
    for part_id in ("split_manifold", "merge_manifold"):
        kernel = build_capped_manifold_kernel(part_specs[part_id])
        frame = placed_frames[part_id]
        rotation = float(frame["rotation_z_rad"])
        translation = tuple(float(value) for value in frame["translation_mm"])
        placed_void = _place_shape(kernel.void_shape, rotation, translation)
        cavity_volume = _finite(_shape_volume(placed_void))
        cavity_evidence[part_id] = {
            "volume_mm3": cavity_volume,
            "brep_valid": _shape_flag(placed_void, "is_valid"),
        }
        if cavity_volume <= 0.0 or not cavity_evidence[part_id]["brep_valid"]:
            raise CadLinkError(
                "cad_link_manifold_volume_unrepresentable",
                "A manifold fluid cavity is not a positive valid BREP.",
                status_code=422,
            )

    declared_pairs: dict[frozenset[str], list[dict[str, str]]] = {}
    for connection in spec.get("connections", []):
        left_id = connection["from"].split(".", 1)[0]
        right_id = connection["to"].split(".", 1)[0]
        declared_pairs.setdefault(frozenset((left_id, right_id)), []).append(
            connection
        )

    contact_pairs: list[dict[str, Any]] = []
    total_pair_count = 0
    broad_phase_candidate_count = 0
    broad_phase_skipped_count = 0
    zero_contact_candidate_count = 0
    for left_id, right_id in combinations(parts, 2):
        total_pair_count += 1
        left = parts[left_id]
        right = parts[right_id]
        pair_connections = declared_pairs.get(frozenset((left_id, right_id)), [])
        connected = bool(pair_connections)
        if len(pair_connections) > 1:
            raise CadLinkError(
                "cad_link_layout_not_closable",
                "A material-part pair has multiple declared connections.",
                status_code=422,
            )
        if not _bbox_may_contact(
            kernel_bboxes[left_id],
            kernel_bboxes[right_id],
        ):
            broad_phase_skipped_count += 1
            if connected:
                raise CadLinkError(
                    "cad_link_layout_contact_invalid",
                    "Declared connected parts have disjoint material bounds.",
                    status_code=422,
                )
            continue

        broad_phase_candidate_count += 1
        topology = _classify_pair_intersection(left.shape, right.shape)
        minimum_distance = _strict_number(topology.get("minimum_distance_mm"))
        has_topology = any(
            topology[key] > 0 for key in ("face_count", "edge_count", "vertex_count")
        )
        has_contact = minimum_distance <= COINCIDENCE_ABS_TOL_MM or has_topology
        if connected:
            topology.update(
                _validate_declared_contact(parts, pair_connections[0], topology)
            )
        elif has_contact:
            raise CadLinkError(
                "cad_link_layout_contact_invalid",
                "Non-connected parts touch or share a face, edge, or vertex.",
                status_code=422,
            )
        else:
            zero_contact_candidate_count += 1
        if connected or has_contact:
            contact_pairs.append(
                {
                    "part_a": left_id,
                    "part_b": right_id,
                    "declared_connection": connected,
                    **topology,
                }
            )

    bbox_min = [
        min(kernel_bboxes[part_id][0][axis] for part_id in parts)
        for axis in range(3)
    ]
    bbox_max = [
        max(kernel_bboxes[part_id][1][axis] for part_id in parts)
        for axis in range(3)
    ]
    evidence = {
        "worker_timeout_seconds": PREFLIGHT_TIMEOUT_SECONDS,
        "spawn_isolated": True,
        "part_count": len(parts),
        "connection_count": len(spec.get("connections", [])),
        "external_boundaries": boundaries,
        "open_endpoints": open_endpoints,
        "kernel_checks": kernel_checks,
        "manifold_cavities": cavity_evidence,
        "assembly_material_volume_mm3": _finite(sum(material_volumes.values())),
        "assembly_bbox_mm": {"min": bbox_min, "max": bbox_max},
        "placed_parts": {
            part_id: {
                "frame": placed_frames[part_id],
                "bbox_mm": {
                    "min": list(kernel_bboxes[part_id][0]),
                    "max": list(kernel_bboxes[part_id][1]),
                },
                "material_volume_mm3": material_volumes[part_id],
                "ports": {
                    name: port.as_dict()
                    for name, port in sorted(part.ports.items())
                },
            }
            for part_id, part in parts.items()
        },
        "contact_pairs": contact_pairs,
        "pair_evaluation": {
            "total_pair_count": total_pair_count,
            "broad_phase_candidate_count": broad_phase_candidate_count,
            "broad_phase_skipped_count": broad_phase_skipped_count,
            "evaluated_pair_count": broad_phase_candidate_count,
            "zero_contact_candidate_count": zero_contact_candidate_count,
        },
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
    rotation = math.atan2(
        placed_port.direction[1], placed_port.direction[0]
    ) - math.atan2(local_port.direction[1], local_port.direction[0])
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


def _classify_pair_intersection(left_shape: Any, right_shape: Any) -> dict[str, Any]:
    intersection = _shape_intersection(left_shape, right_shape)
    volume = 0.0 if intersection is None else _finite(_shape_volume(intersection))
    if volume > INTERFERENCE_ABS_TOL_MM3:
        raise CadLinkError(
            "cad_link_layout_collision",
            "Placed parts have positive-volume interference.",
            status_code=422,
        )
    minimum_distance = _shape_distance(left_shape, right_shape)
    topology = _intersection_topology(intersection)
    topology["volume_mm3"] = volume
    topology["minimum_distance_mm"] = minimum_distance
    return topology


def _validate_declared_contact(
    parts: Mapping[str, BuiltPart],
    connection: Mapping[str, str],
    topology: Mapping[str, Any],
) -> dict[str, Any]:
    left_id, left_port_name = connection["from"].split(".", 1)
    right_id, right_port_name = connection["to"].split(".", 1)
    left_part = parts[left_id]
    right_part = parts[right_id]
    left_port = left_part.ports[left_port_name]
    right_port = right_part.ports[right_port_name]
    if not _ports_mate(left_port, right_port):
        raise CadLinkError(
            "cad_link_layout_contact_invalid",
            "Declared connection ports are not coincident, opposed, and conformant.",
            status_code=422,
        )
    minimum_distance = _strict_number(topology.get("minimum_distance_mm"))
    if minimum_distance > COINCIDENCE_ABS_TOL_MM:
        raise _contact_error()

    left_face = _terminal_annular_face_evidence(left_part.shape, left_port)
    right_face = _terminal_annular_face_evidence(right_part.shape, right_port)
    residual_distance = _validate_no_extra_contact(
        left_part.shape,
        right_part.shape,
        left_port,
    )
    return {
        "contact_basis": "dual_terminal_annular_faces",
        "left_terminal_face": left_face,
        "right_terminal_face": right_face,
        "residual_minimum_distance_mm": residual_distance,
    }


def _terminal_annular_face_evidence(shape: Any, port: PortFrame) -> dict[str, Any]:
    faces = list(shape.faces()) if hasattr(shape, "faces") else []
    if not faces or len(faces) > MAX_PART_FACE_COUNT:
        raise _contact_error()
    matches: list[dict[str, Any]] = []
    for face in faces:
        try:
            matches.append(_annular_face_evidence(face, port))
        except CadLinkError:
            continue
    if len(matches) != 1:
        raise _contact_error()
    return matches[0]


def _annular_face_evidence(face: Any, port: PortFrame) -> dict[str, Any]:
    outer_radius = float(port.outer_d or 0.0) / 2.0
    inner_radius = outer_radius - float(port.wall_t or 0.0)
    face_item = {
        "area_mm2": _finite(float(getattr(face, "area", 0.0) or 0.0)),
        "center_mm": _shape_center(face),
        "bbox_mm": _bbox_payload(_kernel_bbox(face)),
    }
    _validate_annular_face(
        port,
        face_item,
        inner_radius=inner_radius,
        outer_radius=outer_radius,
    )
    edges = list(face.edges()) if hasattr(face, "edges") else []
    if len(edges) != 2:
        raise _contact_error()
    edge_items = [
        {
            "radius_mm": _shape_number(edge, "radius"),
            "center_mm": _shape_point(edge, "arc_center"),
            "bbox_mm": _bbox_payload(_kernel_bbox(edge)),
        }
        for edge in edges
    ]
    _validate_annular_edges(
        port,
        edge_items,
        inner_radius=inner_radius,
        outer_radius=outer_radius,
    )
    normal = _face_normal(face)
    direction = _unit_vector(port.direction)
    alignment = abs(sum(normal[index] * direction[index] for index in range(3)))
    if not math.isclose(alignment, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise _contact_error()
    return {**face_item, "normal": list(normal), "edges": edge_items}


def _face_normal(face: Any) -> tuple[float, float, float]:
    try:
        normal_at = face.normal_at
        try:
            value = normal_at()
        except TypeError:
            value = normal_at(face.center())
        return _unit_vector(_vector_tuple(value))
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise _contact_error() from exc


def _validate_no_extra_contact(
    left_shape: Any,
    right_shape: Any,
    port: PortFrame,
) -> float:
    allowed = _allowed_contact_neighborhood(port)
    try:
        left_residual = left_shape - allowed
        right_residual = right_shape - allowed
    except Exception as exc:
        raise _contact_error() from exc
    if _shape_volume(left_residual) <= 0.0 or _shape_volume(right_residual) <= 0.0:
        raise _contact_error()
    residual_intersection = _shape_intersection(left_residual, right_residual)
    residual_volume = (
        0.0
        if residual_intersection is None
        else _finite(_shape_volume(residual_intersection))
    )
    if residual_volume > INTERFERENCE_ABS_TOL_MM3:
        raise _contact_error()
    residual_distance = _shape_distance(left_residual, right_residual)
    residual_topology = _intersection_topology(residual_intersection)
    if residual_distance <= COINCIDENCE_ABS_TOL_MM or any(
        residual_topology[key] > 0
        for key in ("face_count", "edge_count", "vertex_count")
    ):
        raise _contact_error()
    return residual_distance


def _allowed_contact_neighborhood(port: PortFrame) -> Any:
    import build123d as bd

    direction = _unit_vector(port.direction)
    if not math.isclose(direction[2], 0.0, abs_tol=1e-9):
        raise _contact_error()
    outer_radius = float(port.outer_d or 0.0) / 2.0
    inner_radius = outer_radius - float(port.wall_t or 0.0)
    if inner_radius <= CONTACT_NEIGHBORHOOD_RADIAL_MM:
        raise _contact_error()
    outer = bd.extrude(
        bd.Plane.YZ
        * bd.Circle(radius=outer_radius + CONTACT_NEIGHBORHOOD_RADIAL_MM),
        amount=2.0 * CONTACT_NEIGHBORHOOD_AXIAL_MM,
    )
    inner = bd.extrude(
        bd.Plane.YZ
        * bd.Circle(radius=inner_radius - CONTACT_NEIGHBORHOOD_RADIAL_MM),
        amount=2.0 * CONTACT_NEIGHBORHOOD_AXIAL_MM,
    )
    local = outer - inner
    angle = math.atan2(direction[1], direction[0])
    start = tuple(
        port.origin[index] - CONTACT_NEIGHBORHOOD_AXIAL_MM * direction[index]
        for index in range(3)
    )
    return bd.Pos(*start) * bd.Rot(Z=math.degrees(angle)) * local


def _validate_port_contact_topology(
    port: PortFrame,
    topology: Mapping[str, Any],
) -> None:
    """Accept only one annular face or its two exact circular boundary edges."""

    outer_radius = float(port.outer_d or 0.0) / 2.0
    wall_t = float(port.wall_t or 0.0)
    inner_radius = outer_radius - wall_t
    if (
        port.interface != "tube"
        or inner_radius <= 0.0
        or outer_radius <= inner_radius
    ):
        raise _contact_error()

    edges = topology.get("edges")
    faces = topology.get("faces")
    vertex_count = topology.get("vertex_count")
    if (
        not isinstance(edges, list)
        or not isinstance(faces, list)
        or not isinstance(vertex_count, int)
        or isinstance(vertex_count, bool)
        or vertex_count != 0
        or len(edges) > MAX_CONTACT_TOPOLOGY_ITEMS
        or len(faces) > MAX_CONTACT_TOPOLOGY_ITEMS
    ):
        raise _contact_error()

    if len(faces) == 1:
        _validate_annular_face(
            port,
            faces[0],
            inner_radius=inner_radius,
            outer_radius=outer_radius,
        )
        if edges:
            _validate_annular_edges(
                port,
                edges,
                inner_radius=inner_radius,
                outer_radius=outer_radius,
            )
        return
    if len(faces) == 0 and len(edges) == 2:
        _validate_annular_edges(
            port,
            edges,
            inner_radius=inner_radius,
            outer_radius=outer_radius,
        )
        return
    raise _contact_error()


def _validate_annular_edges(
    port: PortFrame,
    edges: list[Any],
    *,
    inner_radius: float,
    outer_radius: float,
) -> None:
    if len(edges) != 2:
        raise _contact_error()
    classified: set[str] = set()
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise _contact_error()
        radius = _strict_number(edge.get("radius_mm"))
        center = edge.get("center_mm")
        bbox = edge.get("bbox_mm")
        if not _point_matches(center, port.origin):
            raise _contact_error()
        _validate_planar_round_bbox(
            bbox,
            port,
            radius=radius,
        )
        if math.isclose(
            radius,
            inner_radius,
            rel_tol=CONTACT_AREA_REL_TOL,
            abs_tol=CONTACT_RADIUS_ABS_TOL_MM,
        ):
            classified.add("inner")
        elif math.isclose(
            radius,
            outer_radius,
            rel_tol=CONTACT_AREA_REL_TOL,
            abs_tol=CONTACT_RADIUS_ABS_TOL_MM,
        ):
            classified.add("outer")
        else:
            raise _contact_error()
    if classified != {"inner", "outer"}:
        raise _contact_error()


def _validate_annular_face(
    port: PortFrame,
    face: Any,
    *,
    inner_radius: float,
    outer_radius: float,
) -> None:
    if not isinstance(face, Mapping):
        raise _contact_error()
    area = _strict_number(face.get("area_mm2"))
    center = face.get("center_mm")
    bbox = face.get("bbox_mm")
    expected_area = math.pi * (outer_radius**2 - inner_radius**2)
    if not math.isclose(
        area,
        expected_area,
        rel_tol=CONTACT_AREA_REL_TOL,
        abs_tol=CONTACT_AREA_ABS_TOL_MM2,
    ):
        raise _contact_error()
    if not _point_matches(center, port.origin):
        raise _contact_error()
    _validate_planar_round_bbox(
        bbox,
        port,
        radius=outer_radius,
    )


def _validate_planar_round_bbox(
    bbox: Any,
    port: PortFrame,
    *,
    radius: float,
) -> None:
    if not isinstance(bbox, Mapping):
        raise _contact_error()
    minimum = bbox.get("min")
    maximum = bbox.get("max")
    if not (
        isinstance(minimum, list)
        and isinstance(maximum, list)
        and len(minimum) == 3
        and len(maximum) == 3
    ):
        raise _contact_error()
    direction = _unit_vector(port.direction)
    for axis in range(3):
        extent = radius * math.sqrt(max(0.0, 1.0 - direction[axis] ** 2))
        expected_min = port.origin[axis] - extent
        expected_max = port.origin[axis] + extent
        if not math.isclose(
            _strict_number(minimum[axis]),
            expected_min,
            rel_tol=CONTACT_AREA_REL_TOL,
            abs_tol=COINCIDENCE_ABS_TOL_MM,
        ) or not math.isclose(
            _strict_number(maximum[axis]),
            expected_max,
            rel_tol=CONTACT_AREA_REL_TOL,
            abs_tol=COINCIDENCE_ABS_TOL_MM,
        ):
            raise _contact_error()


def _contact_error() -> CadLinkError:
    return CadLinkError(
        "cad_link_layout_contact_invalid",
        "Declared connection contact is not confined to the intended annular mating boundary.",
        status_code=422,
    )


def _ports_mate(left: PortFrame, right: PortFrame) -> bool:
    return (
        _points_close(left.origin, right.origin)
        and _directions_opposed(left.direction, right.direction)
        and left.interface == right.interface == "tube"
        and math.isclose(
            float(left.outer_d),
            float(right.outer_d),
            rel_tol=1e-12,
            abs_tol=COINCIDENCE_ABS_TOL_MM,
        )
        and math.isclose(
            float(left.wall_t),
            float(right.wall_t),
            rel_tol=1e-12,
            abs_tol=COINCIDENCE_ABS_TOL_MM,
        )
    )


def _ports_match(left: PortFrame, right: PortFrame) -> bool:
    return (
        _points_close(left.origin, right.origin)
        and all(
            math.isclose(
                left.direction[index],
                right.direction[index],
                abs_tol=1e-9,
            )
            for index in range(3)
        )
        and left.interface == right.interface
        and left.outer_d == right.outer_d
        and left.wall_t == right.wall_t
        and left.pad_d == right.pad_d
    )


def _point_matches(value: Any, expected: tuple[float, float, float]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(
            isinstance(value[index], int | float)
            and not isinstance(value[index], bool)
            and math.isclose(
                float(value[index]),
                expected[index],
                abs_tol=COINCIDENCE_ABS_TOL_MM,
            )
            for index in range(3)
        )
    )


def _points_close(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> bool:
    return all(
        math.isclose(
            left[index],
            right[index],
            abs_tol=COINCIDENCE_ABS_TOL_MM,
        )
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


def _unit_vector(
    value: tuple[float, float, float],
) -> tuple[float, float, float]:
    magnitude = math.sqrt(sum(component**2 for component in value))
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise _contact_error()
    return tuple(component / magnitude for component in value)


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


def _shape_volume(shape: Any) -> float:
    value = getattr(shape, "volume", 0.0)
    value = value() if callable(value) else value
    return float(value or 0.0)


def _shape_distance(left: Any, right: Any) -> float:
    try:
        value = left.distance(right)
        value = value() if callable(value) else value
        distance = _finite(float(value))
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise _kernel_unavailable(
            "CAD-link kernel could not compute bounded shape distance."
        ) from exc
    if distance < 0.0:
        raise _kernel_unavailable(
            "CAD-link kernel returned a negative shape distance."
        )
    return distance


def _intersection_topology(intersection: Any) -> dict[str, Any]:
    if intersection is None:
        return {
            "face_count": 0,
            "edge_count": 0,
            "vertex_count": 0,
            "face_area_mm2": 0.0,
            "faces": [],
            "edges": [],
            "representation": "empty",
        }
    faces = list(intersection.faces()) if hasattr(intersection, "faces") else []
    edges = list(intersection.edges()) if hasattr(intersection, "edges") else []
    vertices = list(intersection.vertices()) if hasattr(intersection, "vertices") else []
    if (
        len(faces) > MAX_CONTACT_TOPOLOGY_ITEMS
        or len(edges) > MAX_CONTACT_TOPOLOGY_ITEMS
        or len(vertices) > MAX_CONTACT_TOPOLOGY_ITEMS
    ):
        raise CadLinkError(
            "cad_link_kernel_evidence_too_large",
            "Kernel contact topology exceeds the bounded evidence domain.",
            status_code=503,
        )
    face_items = [
        {
            "area_mm2": _finite(float(getattr(face, "area", 0.0) or 0.0)),
            "center_mm": _shape_center(face),
            "bbox_mm": _bbox_payload(_kernel_bbox(face)),
        }
        for face in faces
    ]
    edge_items = [
        {
            "radius_mm": _shape_number(edge, "radius"),
            "center_mm": _shape_point(edge, "arc_center"),
            "bbox_mm": _bbox_payload(_kernel_bbox(edge)),
        }
        for edge in edges
    ]
    if faces:
        representation = "face"
    elif edges:
        representation = "edge"
    elif vertices:
        representation = "vertex"
    else:
        representation = "empty"
    return {
        "face_count": len(faces),
        "edge_count": len(edges),
        "vertex_count": len(vertices),
        "face_area_mm2": _finite(
            sum(item["area_mm2"] for item in face_items)
        ),
        "faces": face_items,
        "edges": edge_items,
        "representation": representation,
    }


def _kernel_bbox(
    shape: Any,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    try:
        bbox_value = shape.bounding_box
        bbox = bbox_value() if callable(bbox_value) else bbox_value
        minimum = _vector_tuple(bbox.min)
        maximum = _vector_tuple(bbox.max)
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise _kernel_unavailable(
            "CAD-link kernel produced invalid bounding-box evidence."
        ) from exc
    if any(minimum[axis] > maximum[axis] for axis in range(3)):
        raise _kernel_unavailable(
            "CAD-link kernel produced invalid bounding-box evidence."
        )
    return minimum, maximum


def _bbox_payload(
    bbox: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> dict[str, list[float]]:
    return {"min": list(bbox[0]), "max": list(bbox[1])}


def _shape_number(shape: Any, attribute: str) -> float | None:
    try:
        value = getattr(shape, attribute)
        value = value() if callable(value) else value
        return _finite(float(value))
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _shape_point(shape: Any, attribute: str) -> list[float] | None:
    try:
        value = getattr(shape, attribute)
        value = value() if callable(value) else value
        return list(_vector_tuple(value))
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _shape_center(shape: Any) -> list[float] | None:
    try:
        value = shape.center()
        return list(_vector_tuple(value))
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _vector_tuple(value: Any) -> tuple[float, float, float]:
    coordinates: list[float] = []
    for index, attribute in enumerate(("X", "Y", "Z")):
        component = getattr(value, attribute, None)
        if component is None:
            component = value[index]
        coordinates.append(_finite(float(component)))
    return tuple(coordinates)  # type: ignore[return-value]


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


def _strict_number(value: Any) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise _contact_error()
    number = float(value)
    if not math.isfinite(number):
        raise _contact_error()
    return number


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise _kernel_unavailable("CAD-link kernel produced a non-finite value.")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    _assert_finite_json(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"Non-finite JSON constant is forbidden: {value}")


def _kernel_unavailable(message: str) -> CadLinkError:
    return CadLinkError(
        "cad_link_kernel_unavailable",
        message,
        status_code=503,
    )


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
                raise _kernel_unavailable(
                    "CAD-link kernel evidence has non-string object keys."
                )
            _assert_finite_json(item)
        return
    raise _kernel_unavailable(
        "CAD-link kernel evidence contains an unsupported value."
    )
