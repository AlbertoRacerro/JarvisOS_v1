"""BLUECAD v0 assembly placement and port conformity."""

from __future__ import annotations

import math
from typing import Any

from app.modules.bluecad.builders import build_part
from app.modules.bluecad.models import BluecadError, BuiltPart, PortFrame

REL_TOL = 1e-6


def assemble_parts(spec: dict[str, Any]) -> dict[str, BuiltPart]:
    parts = {part.part_id: part for part in (build_part(item) for item in spec["parts"])}
    for connection in spec.get("connections", []):
        left_part_id, left_port_name = _split_endpoint(connection["from"])
        right_part_id, right_port_name = _split_endpoint(connection["to"])
        left = _port(parts, left_part_id, left_port_name)
        right = _port(parts, right_part_id, right_port_name)
        _assert_ports_conform(left, right, connection)
    return parts


def _split_endpoint(endpoint: str) -> tuple[str, str]:
    part_id, port_name = endpoint.split(".", 1)
    return part_id, port_name


def _port(parts: dict[str, BuiltPart], part_id: str, port_name: str) -> PortFrame:
    try:
        return parts[part_id].ports[port_name]
    except KeyError as exc:
        raise BluecadError("PORT_MISMATCH", {"part_id": part_id, "port": port_name, "message": "unknown port"}) from exc


def _assert_ports_conform(left: PortFrame, right: PortFrame, connection: dict[str, str]) -> None:
    if not _rel_close(left.outer_d, right.outer_d) or not _rel_close(left.wall_t, right.wall_t):
        raise BluecadError(
            "PORT_MISMATCH",
            {
                "connection": connection,
                "from": {"outer_d": left.outer_d, "wall_t": left.wall_t},
                "to": {"outer_d": right.outer_d, "wall_t": right.wall_t},
                "message": "connected ports must have matching outer_d and wall_t",
            },
        )


def _rel_close(a: float, b: float) -> bool:
    scale = max(abs(a), abs(b), 1.0)
    return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=REL_TOL * scale)
