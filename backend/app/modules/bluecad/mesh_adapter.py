"""BLUECAD Gmsh mesh adapter using only the subprocess tool registry."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.modules.bluecad.export import sha256_file
from app.modules.bluecad.registry import ToolRegistryError, run_tool

_LABEL_RE = re.compile(r"^[A-Za-z0-9_]+$")


def mesh_analysis_spec(analysis_spec: dict[str, Any], out_dir: str | Path, *, registry_path: str | Path | None = None, timeout_s: float = 60.0) -> dict[str, Any]:
    """Mesh an AnalysisSpec geometry with Gmsh and return a MeshResult payload."""
    out_path = Path(out_dir)
    geometry = analysis_spec["geometry"]
    step_path = Path(geometry["step_path"])
    manifest_path = Path(geometry["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    refs = _referenced_groups(analysis_spec)
    _validate_labels(refs)
    target_size = float(analysis_spec["mesh"]["target_size"])

    attempts: list[dict[str, Any]] = []
    artifacts: dict[str, Any] = {}
    final_errors: list[dict[str, Any]] = []
    for attempt_no, size in enumerate((target_size, target_size * 0.5), start=1):
        attempt_dir = out_path if attempt_no == 1 else out_path / f"retry_{attempt_no}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        geo_path = attempt_dir / "mesh.geo"
        inp_path = attempt_dir / "mesh.inp"
        msh_path = attempt_dir / "mesh.msh"
        log_path = attempt_dir / "gmsh.log"
        geo_path.write_text(_geo_text(step_path, manifest, refs, size, analysis_spec.get("mesh", {}).get("refinements", {})), encoding="utf-8")
        try:
            run = run_tool("gmsh", ["-3", str(geo_path), "-format", "inp", "-o", str(inp_path), "-save_all"], attempt_dir, timeout_s, registry_path)
        except ToolRegistryError as exc:
            final_errors = [{"code": exc.code, "detail": exc.detail or {"message": exc.message}}]
            attempts.append(_attempt(attempt_no, size, geo_path, inp_path, msh_path, log_path, None, final_errors))
            return _result("error", final_errors, attempts, _artifacts(attempt_dir, artifacts))
        log_path.write_text((run.stdout or "") + (run.stderr or ""), encoding="utf-8")
        if not msh_path.exists():
            msh_path.write_text("", encoding="utf-8")
        errors, counts, warnings = _post_check(run.returncode, inp_path, refs, log_path)
        attempt = _attempt(attempt_no, size, geo_path, inp_path, msh_path, log_path, run.returncode, errors, counts, warnings)
        attempts.append(attempt)
        artifacts = _artifacts(attempt_dir, artifacts)
        if not errors:
            return _result("pass", [], attempts, artifacts)
        final_errors = errors
        if not any(error["code"] == "MESH_FAIL" for error in errors):
            break
        if attempt_no == 2:
            break
    return _result("fail", final_errors, attempts, artifacts)


def _referenced_groups(spec: dict[str, Any]) -> list[tuple[str, str]]:
    return [("BC", item["port_label"]) for item in spec.get("bcs", [])] + [("LOAD", item["port_label"]) for item in spec.get("loads", [])]


def _validate_labels(refs: list[tuple[str, str]]) -> None:
    for _, label in refs:
        if not all(_LABEL_RE.fullmatch(part) for part in label.split(".")):
            raise ValueError(f"Unsafe BLUECAD port label: {label!r}")


def _group_label(label: str) -> str:
    return label.replace(".", "_")


def _port(manifest: dict[str, Any], label: str) -> dict[str, Any]:
    if "." not in label:
        raise ValueError(f"Port label must be '<part>.<port>': {label}")
    part_id, port_id = label.split(".", 1)
    return manifest["resolved_ports"][part_id][port_id]


def _geo_text(step_path: Path, manifest: dict[str, Any], refs: list[tuple[str, str]], target_size: float, refinements: dict[str, Any]) -> str:
    lines = [f'Merge "{step_path.as_posix()}";', f"Mesh.CharacteristicLengthMax = {target_size:.9g};", f"Mesh.CharacteristicLengthMin = {target_size:.9g};"]
    for prefix, label in refs:
        port = _port(manifest, label)
        origin = [float(v) for v in port["origin"]]
        half = 0.75 * float(port.get("outer_d") or port.get("pad_d"))
        box = [origin[0] - half, origin[1] - half, origin[2] - half, origin[0] + half, origin[1] + half, origin[2] + half]
        lines.append(f'Physical Surface("{prefix}_{_group_label(label)}") = Surface In BoundingBox {{{", ".join(f"{v:.9g}" for v in box)}}};')
        if label in refinements:
            lines.append(f"// refinement {label} {float(refinements[label]):.9g}")
    lines.extend(['Physical Volume("BODY") = Volume{:};', 'Mesh 3;', 'Save "mesh.msh";'])
    return "\n".join(lines) + "\n"


def _post_check(returncode: int, inp_path: Path, refs: list[tuple[str, str]], log_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    warnings = [line for line in log_path.read_text(encoding="utf-8").splitlines() if "warning" in line.lower() or "quality" in line.lower()]
    if returncode != 0:
        return ([{"code": "TIMEOUT" if returncode == 124 else "MESH_FAIL", "detail": {"returncode": returncode}}], {}, warnings)
    try:
        text = inp_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ([{"code": "PARSE_ERROR", "detail": {"message": str(exc)}}], {}, warnings)
    try:
        counts = _parse_inp_counts(text, refs)
    except ValueError as exc:
        return ([{"code": "PARSE_ERROR", "detail": {"message": str(exc)}}], {}, warnings)
    errors = []
    if counts["elements_total"] <= 0:
        errors.append({"code": "MESH_FAIL", "detail": {"message": "zero volume elements"}})
    for prefix, label in refs:
        name = f"{prefix}_{_group_label(label)}"
        if counts["physical_groups"].get(name, 0) <= 0:
            errors.append({"code": "MESH_GROUP_EMPTY", "detail": {"group": name}})
    return errors, counts, warnings


def _parse_inp_counts(text: str, refs: list[tuple[str, str]]) -> dict[str, Any]:
    nodes = elements = 0
    groups = {f"{prefix}_{_group_label(label)}": 0 for prefix, label in refs}
    section = None
    active_group = None
    for raw in text.splitlines():
        line = raw.strip()
        low = line.lower()
        if not line or line.startswith("**"):
            continue
        if low.startswith("*node"):
            section, active_group = "node", None
            continue
        if low.startswith("*element"):
            section, active_group = "element", None
            if "elset=" in low:
                active_group = line[low.index("elset=") + 6 :].split(",", 1)[0].strip()
            continue
        if line.startswith("*"):
            section, active_group = None, None
            continue
        if section == "node":
            nodes += 1
        elif section == "element":
            elements += 1
            if active_group in groups:
                groups[active_group] += 1
    return {"nodes_total": nodes, "elements_total": elements, "physical_groups": groups}


def _attempt(attempt_no: int, size: float, geo_path: Path, inp_path: Path, msh_path: Path, log_path: Path, returncode: int | None, errors: list[dict[str, Any]], counts: dict[str, Any] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    return {"attempt_no": attempt_no, "target_size": size, "gmsh_returncode": returncode, "counts": counts or {}, "warnings": warnings or [], "errors": errors, "artifacts": _artifact_map({"bluecad_geo": geo_path, "mesh_inp": inp_path, "mesh_msh": msh_path, "gmsh_log": log_path})}


def _artifact_map(paths: dict[str, Path]) -> dict[str, Any]:
    return {role: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for role, path in paths.items() if path.exists()}


def _artifacts(attempt_dir: Path, previous: dict[str, Any]) -> dict[str, Any]:
    current = _artifact_map({"bluecad_geo": attempt_dir / "mesh.geo", "mesh_inp": attempt_dir / "mesh.inp", "mesh_msh": attempt_dir / "mesh.msh", "gmsh_log": attempt_dir / "gmsh.log"})
    return current or previous


def _result(verdict: str, errors: list[dict[str, Any]], attempts: list[dict[str, Any]], artifacts: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "bluecad_mesh_result_v0_1", "verdict": verdict, "errors": errors, "attempts": attempts, "artifacts": artifacts}
