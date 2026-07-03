"""Shared BLUECAD CAD adapter data models."""

from __future__ import annotations

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
    outer_d: float
    wall_t: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "origin": [round(value, 9) for value in self.origin],
            "direction": [round(value, 9) for value in self.direction],
            "outer_d": round(self.outer_d, 9),
            "wall_t": round(self.wall_t, 9),
        }


@dataclass(frozen=True)
class BuiltPart:
    part_id: str
    kind: str
    volume_mm3: float
    bbox_mm: tuple[tuple[float, float, float], tuple[float, float, float]]
    ports: dict[str, PortFrame]
    shape: Any = None

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
