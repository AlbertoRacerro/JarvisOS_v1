"""Deterministic BLUECAD primitive builders.

Stage 2 keeps build123d usage behind lazy imports so non-kernel schema tests can
run where the CAD dependency is absent. The analytic metadata mirrors the solids
and is used for deterministic manifests and validation tolerances.
"""

from __future__ import annotations

import math
from typing import Any

from app.modules.bluecad.models import BluecadError, BuiltPart, PortFrame


def build_part(part: dict[str, Any]) -> BuiltPart:
    kind = part["kind"]
    if kind == "tube_run":
        return _build_tube_run(part)
    if kind == "bend":
        return _build_bend(part)
    if kind == "joint":
        return _build_socket_joint(part)
    raise BluecadError("SPEC_INVALID", {"part_id": part.get("part_id"), "kind": kind, "message": "unsupported part kind"})


def _annulus_area(outer_d: float, wall_t: float) -> float:
    inner_d = outer_d - 2.0 * wall_t
    return math.pi / 4.0 * (outer_d**2 - inner_d**2)


def _tube_shape(outer_d: float, inner_d: float, length: float) -> Any:
    try:
        import build123d as bd
    except ImportError as exc:  # pragma: no cover - exercised only where dependency absent
        raise BluecadError("KERNEL_ERROR", {"message": "build123d is not installed"}) from exc
    outer = bd.extrude(bd.Plane.YZ * bd.Circle(radius=outer_d / 2.0), amount=length)
    inner = bd.extrude(bd.Plane.YZ * bd.Circle(radius=inner_d / 2.0), amount=length)
    return outer - inner


def _bend_shape(outer_d: float, inner_d: float, bend_radius: float, angle_rad: float) -> Any:
    try:
        import build123d as bd
    except ImportError as exc:  # pragma: no cover - exercised only where dependency absent
        raise BluecadError("KERNEL_ERROR", {"message": "build123d is not installed"}) from exc
    path = bd.JernArc(start=(0.0, 0.0), tangent=(1.0, 0.0), radius=bend_radius, arc_size=math.degrees(angle_rad))
    outer = bd.sweep(bd.Plane.YZ * bd.Circle(radius=outer_d / 2.0), path=path)
    inner = bd.sweep(bd.Plane.YZ * bd.Circle(radius=inner_d / 2.0), path=path)
    return outer - inner


def _build_tube_run(part: dict[str, Any]) -> BuiltPart:
    p = part["params"]
    outer_d = float(p["outer_d"])
    wall_t = float(p["wall_t"])
    length = float(p["length"])
    volume = _annulus_area(outer_d, wall_t) * length
    radius = outer_d / 2.0
    shape = _tube_shape(outer_d, outer_d - 2.0 * wall_t, length)
    return BuiltPart(
        part_id=part["part_id"],
        kind="tube_run",
        volume_mm3=volume,
        bbox_mm=((0.0, -radius, -radius), (length, radius, radius)),
        ports={
            "port_a": PortFrame((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), outer_d, wall_t),
            "port_b": PortFrame((length, 0.0, 0.0), (1.0, 0.0, 0.0), outer_d, wall_t),
        },
        shape=shape,
    )


def _build_bend(part: dict[str, Any]) -> BuiltPart:
    p = part["params"]
    outer_d = float(p["outer_d"])
    wall_t = float(p["wall_t"])
    bend_radius = float(p["bend_radius"])
    angle = float(p["angle"])
    volume = _annulus_area(outer_d, wall_t) * bend_radius * angle
    radius = outer_d / 2.0
    shape = _bend_shape(outer_d, outer_d - 2.0 * wall_t, bend_radius, angle)
    end_x = bend_radius * math.sin(angle)
    end_y = bend_radius * (1.0 - math.cos(angle))
    end_dir = (math.cos(angle), math.sin(angle), 0.0)
    return BuiltPart(
        part_id=part["part_id"],
        kind="bend",
        volume_mm3=volume,
        bbox_mm=((min(0.0, end_x) - radius, min(0.0, end_y) - radius, -radius), (max(0.0, end_x) + radius, max(0.0, end_y) + radius, radius)),
        ports={
            "port_a": PortFrame((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), outer_d, wall_t),
            "port_b": PortFrame((end_x, end_y, 0.0), end_dir, outer_d, wall_t),
        },
        shape=shape,
    )


def _build_socket_joint(part: dict[str, Any]) -> BuiltPart:
    p = part["params"]
    mating_outer_d = float(p["outer_d"])
    wall_t = float(p["wall_t"])
    socket_len = float(p["socket_len"])
    sleeve_outer_d = mating_outer_d + 2.0 * wall_t
    volume = math.pi / 4.0 * (sleeve_outer_d**2 - mating_outer_d**2) * socket_len
    radius = sleeve_outer_d / 2.0
    shape = _tube_shape(sleeve_outer_d, mating_outer_d, socket_len)
    return BuiltPart(
        part_id=part["part_id"],
        kind="joint",
        volume_mm3=volume,
        bbox_mm=((0.0, -radius, -radius), (socket_len, radius, radius)),
        ports={
            "port_a": PortFrame((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), mating_outer_d, wall_t),
            "port_b": PortFrame((socket_len, 0.0, 0.0), (1.0, 0.0, 0.0), mating_outer_d, wall_t),
        },
        shape=shape,
    )
