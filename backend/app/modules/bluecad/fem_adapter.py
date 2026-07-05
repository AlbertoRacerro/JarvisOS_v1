"""BLUECAD CalculiX FEM adapter.

The solver deck is assembled only from mesh input plus schema-shaped AnalysisSpec
fields. ``force_total`` loads are approximated in v0 by dividing each component
uniformly across nodes found in the target ``LOAD_<label>`` element set.
Expected units follow BLUECAD v0: geometry in mm, force in N, mass in kg, stress
in MPa; no unit conversion is performed here.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from app.modules.bluecad.export import sha256_file
from app.modules.bluecad.mesh_adapter import _group_label
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool, run_tool

_ERROR_PATTERN = re.compile(r"\*error|error:", re.IGNORECASE)
_DIVERGED_PATTERN = re.compile(r"diverg|non.?conver|no convergence", re.IGNORECASE)
_SUPPORTED_METRICS = {"max_displacement", "max_von_mises"}


def solve_static_analysis(
    analysis_spec: dict[str, Any],
    mesh_result: dict[str, Any],
    out_dir: str | Path,
    *,
    registry_path: str | Path | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Assemble a static CalculiX deck, run registered ccx, and summarize results."""
    if analysis_spec.get("analysis_type") != "static":
        return _error("SOLVE_ERROR", {"message": "only static analysis is supported"}, {})
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Any] = {}
    log_path = out_path / "analysis.log"
    try:
        tool = resolve_tool("calculix", registry_path)
        mesh_path = Path(mesh_result["artifacts"]["mesh_inp"]["path"])
        mesh = _parse_mesh(mesh_path.read_text(encoding="utf-8"))
        inp_path = out_path / "analysis.inp"
        inp_path.write_text(_deck_text(analysis_spec, mesh_path, mesh), encoding="utf-8")
        artifacts.update(_artifact_map({"inp": inp_path}))
        run = run_tool("calculix", [inp_path.stem], out_path, timeout_s or float(analysis_spec.get("timeout_s", 60)), registry_path)
        log_path.write_text((run.stdout or "") + (run.stderr or ""), encoding="utf-8")
        artifacts.update(_artifact_map({"log": log_path}))
        if run.timed_out:
            return _error("TIMEOUT", {"returncode": run.returncode}, artifacts, run.returncode, tool)
        if run.returncode != 0 or _ERROR_PATTERN.search(log_path.read_text(encoding="utf-8")):
            code = "SOLVE_DIVERGED" if _DIVERGED_PATTERN.search(log_path.read_text(encoding="utf-8")) else "SOLVE_ERROR"
            return _error(code, {"returncode": run.returncode}, artifacts, run.returncode, tool)
        frd_path = out_path / "analysis.frd"
        dat_path = out_path / "analysis.dat"
        artifacts.update(_artifact_map({"frd": frd_path, "dat": dat_path}))
        parsed = _parse_outputs(frd_path, dat_path)
    except ToolRegistryError as exc:
        log_path.write_text(str(exc), encoding="utf-8")
        artifacts.update(_artifact_map({"log": log_path}))
        return _error("SOLVE_ERROR", {"registry_code": exc.code, **(exc.detail or {})}, artifacts)
    except (OSError, KeyError, ValueError) as exc:
        artifacts.update(_artifact_map({"log": log_path}))
        return _error("PARSE_ERROR", {"message": str(exc)}, artifacts)
    return {
        "schema_version": "bluecad_result_summary_v0_1",
        "verdict": "pass",
        "errors": [],
        "solver": {"tool_id": "calculix", "version": tool["version_pin"], "returncode": run.returncode},
        "analysis_type": "static",
        **parsed,
        "artifacts": artifacts,
    }


def append_tier3_checks(report: dict[str, Any], result_summary: dict[str, Any], pass_criteria: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    """Append deterministic Tier 3 checks to a validation report."""
    checks = list(report.get("checks", []))
    errors = list(report.get("errors", []))
    criteria = _criteria_list(pass_criteria)
    for item in criteria:
        metric = item["metric"]
        if metric not in _SUPPORTED_METRICS:
            errors.append({"code": "UNKNOWN_METRIC", "detail": {"metric": metric}})
            checks.append({"id": f"T3_{metric.upper()}", "tier": 3, "status": "error", "detail": {"metric": metric}})
            continue
        actual = float(result_summary[metric]["value"])
        expected = float(item["value"])
        op = item["op"]
        passed = _compare(actual, op, expected)
        checks.append({"id": f"T3_{metric.upper()}", "tier": 3, "status": "pass" if passed else "fail", "detail": {"metric": metric, "op": op, "actual": actual, "value": expected}, "hint": f"{metric} must be {op} {expected:.9g}"})
    verdict = "error" if errors or any(c["status"] == "error" for c in checks) else ("fail" if any(c["status"] == "fail" for c in checks) else report.get("verdict", "pass"))
    return {**report, "checks": checks, "errors": errors, "verdict": verdict}


def _deck_text(spec: dict[str, Any], mesh_path: Path, mesh: dict[str, Any]) -> str:
    material = spec["material"]
    lines = ["** BLUECAD generated static deck", f'*INCLUDE, INPUT={mesh_path.as_posix()}', f'*MATERIAL, NAME={material["name"]}', "*ELASTIC", f'{material["E"]}, {material["nu"]}', "*DENSITY", f'{material["rho"]}', "*BOUNDARY"]
    for bc in spec.get("bcs", []):
        name = f'BC_{_group_label(bc["port_label"])}'
        _require_set(mesh, name)
        if bc.get("kind", "fixed") != "fixed":
            raise ValueError("only fixed boundary conditions are supported")
        lines.append(f"{name}, 1, 6, 0")
    lines.extend(["*STEP", "*STATIC"])
    for load in spec.get("loads", []):
        name = f'LOAD_{_group_label(load["port_label"])}'
        _require_set(mesh, name)
        if load.get("type", "force_total") == "force_total":
            nodes = sorted(mesh["sets"][name])
            force = load.get("force", load.get("vector_n"))
            if not force or not nodes:
                raise ValueError(f"load {name} has no force vector or nodes")
            lines.append("*CLOAD")
            for node in nodes:
                for dof, value in enumerate(force, start=1):
                    if value:
                        lines.append(f"{node}, {dof}, {float(value) / len(nodes):.12g}")
        elif load.get("type") == "pressure":
            lines.extend(["*DLOAD", f"{name}, P, {float(load['pressure']):.12g}"])
        else:
            raise ValueError("unsupported load type")
    lines.extend(["*NODE FILE", "U", "*EL FILE", "S", "*END STEP", ""])
    return "\n".join(lines)


def _parse_mesh(text: str) -> dict[str, Any]:
    nodes: set[int] = set()
    sets: dict[str, set[int]] = {}
    section = None
    active = None
    for raw in text.splitlines():
        line = raw.strip()
        low = line.lower()
        if not line or line.startswith("**"):
            continue
        if low.startswith("*node"):
            section = "node"
            active = None
            continue
        if low.startswith("*element"):
            section = "element"
            active = None
            if "elset=" in low:
                active = line[low.index("elset=") + 6:].split(",", 1)[0].strip()
                sets.setdefault(active, set())
            continue
        if line.startswith("*"):
            section = None
            active = None
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if section == "node":
            nodes.add(int(parts[0]))
        elif section == "element" and active:
            sets[active].update(int(p) for p in parts[1:])
    return {"nodes": nodes, "sets": sets}


def _parse_outputs(frd_path: Path, dat_path: Path) -> dict[str, Any]:
    if not frd_path.exists():
        raise ValueError("missing frd output")
    max_u = {"node_id": None, "value": -1.0}
    max_vm = {"element_id": None, "node_id": None, "value": -1.0}
    for raw in frd_path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if not parts or parts[0].startswith("#"):
            continue
        tag = parts[0].upper()
        if tag == "DISP" and len(parts) == 5:
            value = math.sqrt(sum(float(v) ** 2 for v in parts[2:5]))
            if value > max_u["value"]:
                max_u = {"node_id": int(parts[1]), "value": value}
        elif tag == "STRESS" and len(parts) >= 4:
            value = float(parts[3])
            if value > max_vm["value"]:
                max_vm = {"element_id": int(parts[1]), "node_id": int(parts[2]), "value": value}
    if max_u["node_id"] is None or max_vm["element_id"] is None:
        raise ValueError("frd missing displacement or stress records")
    reactions = []
    if dat_path.exists():
        for raw in dat_path.read_text(encoding="utf-8").splitlines():
            parts = raw.split()
            if parts and parts[0].upper() == "REACTION" and len(parts) == 5:
                reactions.append({"node_id": int(parts[1]), "force": [float(v) for v in parts[2:5]]})
    return {"max_displacement": max_u, "max_von_mises": max_vm, "reactions": reactions}


def _criteria_list(value: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return value
    return [{"metric": metric, "op": "<=", "value": limit} for metric, limit in value.items()]


def _compare(actual: float, op: str, expected: float) -> bool:
    return {"<=": actual <= expected, "<": actual < expected, ">=": actual >= expected, ">": actual > expected, "==": actual == expected}[op]


def _require_set(mesh: dict[str, Any], name: str) -> None:
    if name not in mesh["sets"] or not mesh["sets"][name]:
        raise ValueError(f"mesh set missing or empty: {name}")


def _artifact_map(paths: dict[str, Path]) -> dict[str, Any]:
    return {role: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for role, path in paths.items() if path.exists()}


def _error(code: str, detail: dict[str, Any], artifacts: dict[str, Any], returncode: int | None = None, tool: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"schema_version": "bluecad_result_summary_v0_1", "verdict": "error", "errors": [{"code": code, "detail": detail}], "solver": {"tool_id": "calculix", "version": (tool or {}).get("version_pin"), "returncode": returncode}, "artifacts": artifacts}
