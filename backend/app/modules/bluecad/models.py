"""Shared BLUECAD CAD adapter data models."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ErrorCode = Literal["SPEC_INVALID", "PORT_MISMATCH", "KERNEL_ERROR", "EXPORT_ERROR", "TIMEOUT"]
Verdict = Literal["pass", "fail", "error"]


class BluecadError(RuntimeError):
    """Structured BLUECAD adapter error."""

    def __init__(self, code: ErrorCode, detail: dict[str, Any]) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail

    def as_report_error(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail}


@dataclass(frozen=True)
class PortFrame:
    origin: tuple[float, float, float]
    direction: tuple[float, float, float]
    outer_d: float | None = None
    wall_t: float | None = None
    interface: Literal["tube", "pad"] = "tube"
    pad_d: float | None = None

    def transformed(self, rotation_z_rad: float, translation: tuple[float, float, float]) -> PortFrame:
        return PortFrame(
            origin=_transform_point(self.origin, rotation_z_rad, translation),
            direction=_rotate_vector(self.direction, rotation_z_rad),
            outer_d=self.outer_d,
            wall_t=self.wall_t,
            interface=self.interface,
            pad_d=self.pad_d,
        )

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "origin": [round(value, 9) for value in self.origin],
            "direction": [round(value, 9) for value in self.direction],
            "interface": self.interface,
        }
        if self.interface == "tube":
            payload["outer_d"] = round(float(self.outer_d), 9)
            payload["wall_t"] = round(float(self.wall_t), 9)
        else:
            payload["pad_d"] = round(float(self.pad_d), 9)
        return payload


@dataclass(frozen=True)
class BuiltPart:
    part_id: str
    kind: str
    volume_mm3: float
    bbox_mm: tuple[tuple[float, float, float], tuple[float, float, float]]
    ports: dict[str, PortFrame]
    shape: Any = None

    def placed(self, rotation_z_rad: float, translation: tuple[float, float, float]) -> BuiltPart:
        shape = self.shape
        if shape is not None:
            try:
                import build123d as bd
            except ImportError as exc:  # pragma: no cover
                raise BluecadError("KERNEL_ERROR", {"message": "build123d is not installed"}) from exc
            shape = bd.Pos(*translation) * bd.Rot(Z=math.degrees(rotation_z_rad)) * shape
        return BuiltPart(
            part_id=self.part_id,
            kind=self.kind,
            volume_mm3=self.volume_mm3,
            bbox_mm=_transform_bbox(self.bbox_mm, rotation_z_rad, translation),
            ports={name: port.transformed(rotation_z_rad, translation) for name, port in self.ports.items()},
            shape=shape,
        )

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "volume_mm3": round(self.volume_mm3, 9),
            "bbox_mm": {
                "min": [round(value, 9) for value in self.bbox_mm[0]],
                "max": [round(value, 9) for value in self.bbox_mm[1]],
            },
            "ports": {name: port.as_dict() for name, port in sorted(self.ports.items())},
        }


@dataclass(frozen=True)
class BuildResult:
    spec_id: str
    out_dir: Path
    manifest_path: Path | None
    report_path: Path | None
    manifest: dict[str, Any] | None
    report: dict[str, Any]
    verdict: Verdict
    errors: list[dict[str, Any]] = field(default_factory=list)


def _rotate_vector(value: tuple[float, float, float], rotation_z_rad: float) -> tuple[float, float, float]:
    cos_t = math.cos(rotation_z_rad)
    sin_t = math.sin(rotation_z_rad)
    x, y, z = value
    return (cos_t * x - sin_t * y, sin_t * x + cos_t * y, z)


def _transform_point(value: tuple[float, float, float], rotation_z_rad: float, translation: tuple[float, float, float]) -> tuple[float, float, float]:
    rx, ry, rz = _rotate_vector(value, rotation_z_rad)
    return (rx + translation[0], ry + translation[1], rz + translation[2])


def _transform_bbox(bbox: tuple[tuple[float, float, float], tuple[float, float, float]], rotation_z_rad: float, translation: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    mins, maxs = bbox
    corners = [
        (x, y, z)
        for x in (mins[0], maxs[0])
        for y in (mins[1], maxs[1])
        for z in (mins[2], maxs[2])
    ]
    transformed = [_transform_point(corner, rotation_z_rad, translation) for corner in corners]
    return (tuple(min(point[axis] for point in transformed) for axis in range(3)), tuple(max(point[axis] for point in transformed) for axis in range(3)))
