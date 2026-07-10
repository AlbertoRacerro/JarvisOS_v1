"""BLUECAD artifact export and deterministic manifest writing."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.modules.bluecad.assembly import assemble_parts
from app.modules.bluecad.models import BluecadError, BuiltPart
from app.modules.bluecad.spec import canonical_json, canonicalize_geometry_spec

ARTIFACT_NAMES = ("model.step", "model.stl", "model.glb")
_CANONICAL_STEP_TIMESTAMP = "1970-01-01T00:00:00"
_STEP_FILE_NAME_TIMESTAMP_RE = re.compile(r"(FILE_NAME\('[^']*',)'[^']*'")


def build_artifacts(spec_payload: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    spec = canonicalize_geometry_spec(spec_payload)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    parts = assemble_parts(spec)
    try:
        _export_shapes(parts, out_path)
    except Exception as exc:
        if isinstance(exc, BluecadError):
            raise
        raise BluecadError("EXPORT_ERROR", {"message": str(exc)}) from exc
    manifest = _manifest(spec, parts, out_path)
    manifest_path = out_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _export_shapes(parts: dict[str, BuiltPart], out_dir: Path) -> None:
    try:
        import build123d as bd
    except ImportError as exc:  # pragma: no cover
        raise BluecadError("KERNEL_ERROR", {"message": "build123d is not installed"}) from exc
    shapes = [part.shape for part in parts.values()]
    shape = shapes[0] if len(shapes) == 1 else bd.Compound(children=shapes)
    step_path = out_dir / "model.step"
    bd.export_step(shape, step_path)
    _normalize_step_header_timestamp(step_path)
    bd.export_stl(shape, out_dir / "model.stl")
    bd.export_gltf(shape, out_dir / "model.glb", binary=True, linear_deflection=0.001, angular_deflection=0.1)
    for name in ARTIFACT_NAMES:
        path = out_dir / name
        if not path.exists() or path.stat().st_size <= 0:
            raise BluecadError("EXPORT_ERROR", {"artifact": name, "message": "artifact was not written"})


def _normalize_step_header_timestamp(path: Path) -> None:
    """Remove OCCT wall-clock drift without changing STEP geometry data."""
    text = path.read_text(encoding="utf-8")
    normalized, count = _STEP_FILE_NAME_TIMESTAMP_RE.subn(
        lambda match: f"{match.group(1)}'{_CANONICAL_STEP_TIMESTAMP}'",
        text,
        count=1,
    )
    if count != 1:
        raise BluecadError(
            "EXPORT_ERROR",
            {"artifact": path.name, "message": "STEP FILE_NAME timestamp header was not found exactly once"},
        )
    path.write_text(normalized, encoding="utf-8")


def _manifest(spec: dict[str, Any], parts: dict[str, BuiltPart], out_dir: Path) -> dict[str, Any]:
    """Return the canonical geometry manifest.

    Runtime duration is excluded. Exported-file hashes remain part of the public
    manifest integrity contract and are expected to be deterministic for an
    equivalent build under one pinned kernel/tool environment.
    """
    total_bbox = _total_bbox(parts)
    payload: dict[str, Any] = {
        "manifest_version": "bluecad_manifest_v0_1",
        "spec_id": spec["spec_id"],
        "tool_versions": _tool_versions(),
        "parts": {part_id: part.manifest_entry() for part_id, part in sorted(parts.items())},
        "resolved_ports": {
            part_id: {name: port.as_dict() for name, port in sorted(part.ports.items())}
            for part_id, part in sorted(parts.items())
        },
        "assembly": {
            "total_volume_mm3": round(sum(part.volume_mm3 for part in parts.values()), 9),
            "bbox_mm": {
                "min": [round(value, 9) for value in total_bbox[0]],
                "max": [round(value, 9) for value in total_bbox[1]],
            },
            "kernel_checks": _kernel_checks(parts),
        },
        "artifacts": {
            name: {"sha256": sha256_file(out_dir / name), "bytes": (out_dir / name).stat().st_size}
            for name in ARTIFACT_NAMES
        },
    }
    payload["manifest_digest"] = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return payload


def _total_bbox(parts: dict[str, BuiltPart]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    mins = [min(part.bbox_mm[0][axis] for part in parts.values()) for axis in range(3)]
    maxs = [max(part.bbox_mm[1][axis] for part in parts.values()) for axis in range(3)]
    return (tuple(mins), tuple(maxs))


def _kernel_checks(parts: dict[str, BuiltPart]) -> dict[str, Any]:
    return {
        part_id: {
            "brep_valid": bool(getattr(part.shape, "is_valid", False)),
            "manifold": bool(getattr(part.shape, "is_manifold", False)),
        }
        for part_id, part in sorted(parts.items())
    }


def _tool_versions() -> dict[str, str | None]:
    try:
        import build123d as bd
    except ImportError:
        return {"build123d": None}
    return {"build123d": getattr(bd, "__version__", "unknown")}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
