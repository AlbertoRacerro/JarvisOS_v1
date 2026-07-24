from __future__ import annotations

import re
from pathlib import Path

PATH = Path("backend/app/modules/bluecad/cad_link_topology_preflight.py")
text = PATH.read_text(encoding="utf-8")


def replace_function(name: str, replacement: str) -> None:
    global text
    pattern = re.compile(rf"(?ms)^def {re.escape(name)}\(.*?(?=^def |\Z)")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"expected one function {name}, found {len(matches)}")
    match = matches[0]
    text = text[: match.start()] + replacement.rstrip() + "\n\n\n" + text[match.end() :]


if "CONTACT_NEIGHBORHOOD_AXIAL_MM" not in text:
    marker = "CONTACT_AREA_ABS_TOL_MM2 = 1e-6\nMAX_CONTACT_TOPOLOGY_ITEMS = 64\n"
    if text.count(marker) != 1:
        raise SystemExit("contact constant marker missing")
    text = text.replace(
        marker,
        "CONTACT_AREA_ABS_TOL_MM2 = 1e-6\n"
        "CONTACT_NEIGHBORHOOD_AXIAL_MM = 1e-4\n"
        "CONTACT_NEIGHBORHOOD_RADIAL_MM = 1e-4\n"
        "MAX_CONTACT_TOPOLOGY_ITEMS = 64\n"
        "MAX_PART_FACE_COUNT = 128\n",
        1,
    )

loop_pattern = re.compile(
    r"(?ms)^        topology = _classify_pair_intersection\(left\.shape, right\.shape\)\n"
    r"        has_contact = any\(\n"
    r".*?^            zero_contact_candidate_count \+= 1\n"
)
loop_matches = list(loop_pattern.finditer(text))
if len(loop_matches) != 1:
    raise SystemExit(f"expected one pair-classification loop block, found {len(loop_matches)}")
loop_replacement = '''        topology = _classify_pair_intersection(left.shape, right.shape)
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
'''
text = loop_pattern.sub(loop_replacement, text, count=1)

replace_function(
    "_classify_pair_intersection",
    '''def _classify_pair_intersection(left_shape: Any, right_shape: Any) -> dict[str, Any]:
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
    return topology''',
)

replace_function(
    "_validate_declared_contact",
    '''def _validate_declared_contact(
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
    return bd.Pos(*start) * bd.Rot(Z=math.degrees(angle)) * local''',
)

replace_function(
    "_shape_volume",
    '''def _shape_volume(shape: Any) -> float:
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
    return distance''',
)

PATH.write_text(text, encoding="utf-8")
