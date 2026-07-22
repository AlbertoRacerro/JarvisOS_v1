"""Deterministic fluid-open capped branch-manifold primitive."""

from __future__ import annotations

from typing import Any

from app.modules.bluecad.models import BluecadError, BuiltPart, PortFrame

PART_KIND = "capped_manifold"
PARAM_NAMES = frozenset(
    {
        "main_outer_d",
        "main_wall_t",
        "branch_count",
        "branch_outer_d",
        "branch_wall_t",
        "branch_gap",
        "end_gap",
        "branch_stub_length",
        "cap_thickness",
    }
)


def build_capped_manifold(part: dict[str, Any]) -> BuiltPart:
    """Build one capped header with a common opening and open branch bores."""

    p = part["params"]
    main_outer_d = float(p["main_outer_d"])
    main_wall_t = float(p["main_wall_t"])
    branch_count = int(p["branch_count"])
    branch_outer_d = float(p["branch_outer_d"])
    branch_wall_t = float(p["branch_wall_t"])
    branch_gap = float(p["branch_gap"])
    end_gap = float(p["end_gap"])
    branch_stub_length = float(p["branch_stub_length"])
    cap_thickness = float(p["cap_thickness"])

    branch_pitch = branch_outer_d + branch_gap
    header_length = branch_outer_d + 2.0 * end_gap + branch_pitch * (branch_count - 1)
    main_inner_d = main_outer_d - 2.0 * main_wall_t
    branch_inner_d = branch_outer_d - 2.0 * branch_wall_t
    branch_sweep_length = main_outer_d / 2.0 + branch_stub_length

    try:
        import build123d as bd
    except ImportError as exc:  # pragma: no cover - exercised only where dependency absent
        raise BluecadError("KERNEL_ERROR", {"message": "build123d is not installed"}) from exc

    header_outer = bd.extrude(
        bd.Plane.YZ * bd.Circle(radius=main_outer_d / 2.0),
        amount=header_length,
    )
    header_inner = bd.extrude(
        bd.Plane.YZ * bd.Circle(radius=main_inner_d / 2.0),
        amount=header_length,
    )
    shape = header_outer - header_inner

    cap = bd.Pos(header_length, 0.0, 0.0) * bd.extrude(
        bd.Plane.YZ * bd.Circle(radius=main_outer_d / 2.0),
        amount=cap_thickness,
    )
    shape = shape + cap

    ports: dict[str, PortFrame] = {
        "common": PortFrame(
            (0.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0),
            main_outer_d,
            main_wall_t,
        )
    }
    for index in range(branch_count):
        x = end_gap + branch_outer_d / 2.0 + branch_pitch * index
        branch_outer = (
            bd.Pos(x, 0.0, 0.0)
            * bd.Rot(Z=90)
            * bd.extrude(
                bd.Plane.YZ * bd.Circle(radius=branch_outer_d / 2.0),
                amount=branch_sweep_length,
            )
        )
        branch_bore = (
            bd.Pos(x, 0.0, 0.0)
            * bd.Rot(Z=90)
            * bd.extrude(
                bd.Plane.YZ * bd.Circle(radius=branch_inner_d / 2.0),
                amount=branch_sweep_length,
            )
        )
        shape = (shape + branch_outer) - branch_bore
        ports[f"branch_{index + 1}"] = PortFrame(
            (x, branch_sweep_length, 0.0),
            (0.0, 1.0, 0.0),
            branch_outer_d,
            branch_wall_t,
        )

    main_radius = main_outer_d / 2.0
    branch_radius = branch_outer_d / 2.0
    radius = max(main_radius, branch_radius)
    volume = float(shape.volume)
    if volume <= 0.0:
        raise BluecadError(
            "KERNEL_ERROR",
            {"part_id": part["part_id"], "message": "capped manifold solid has non-positive volume"},
        )
    return BuiltPart(
        part_id=part["part_id"],
        kind=PART_KIND,
        volume_mm3=volume,
        bbox_mm=(
            (0.0, -main_radius, -radius),
            (header_length + cap_thickness, branch_sweep_length, radius),
        ),
        ports=ports,
        shape=shape,
    )
