"""Run the spec 216 analytic laminar solver controls with the pinned OpenFOAM tools.

    PYTHONPATH=backend python scripts/qualification/216/solver_controls.py \
      --registry /path/to/operator-registry.yaml --out /path/outside/repo/controls-1

The square duct must match f·Re = 56.908 and the half channel 3 μ U / h², both
within 2%. A failure means the pinned solver path is not fit for a pipe study.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.modules.bluecad.cfd_pipe.contract import PipeStudyContract
from app.modules.bluecad.cfd_pipe.domain import derive_fluid_domain
from app.modules.bluecad.cfd_pipe.probe_results import ProbeResultError
from app.modules.bluecad.cfd_pipe.solver_controls import CONTROL_NAMES, compare_control, generate_control
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool, run_tool
from app.modules.bluecad.template import TubeTemplateCreate, template_geometry_spec

TOOLS = ("openfoam_blockmesh", "openfoam_simplefoam")
_REPO = Path(__file__).resolve().parents[3]


def reference_contract() -> PipeStudyContract:
    """The laminar pipe case whose generated solver dictionaries the controls reuse."""
    tube = template_geometry_spec(TubeTemplateCreate.model_validate(
        {"template": "tube", "params": {"outer_d_mm": 14.0, "wall_t_mm": 2.0, "length_mm": 200.0}}))
    return PipeStudyContract.model_validate({
        "domain": derive_fluid_domain(tube), "inlet": {"mean_velocity_m_s": 0.01}, "regime": "laminar",
        "wall_treatment": "resolved", "mesh_level": 0, "solver": {"max_iterations": 300, "residual_target": 1e-6},
    })


def run(registry: Path, out: Path) -> dict:
    out = out.resolve()
    if out.is_relative_to(_REPO):
        raise ValueError("control output must be outside the repository")
    if out.exists():
        raise FileExistsError(f"control output already exists: {out}")
    try:
        entries = {tool_id: resolve_tool(tool_id, registry) for tool_id in TOOLS}
    except ToolRegistryError as exc:
        return {"status": "unavailable", "reason": str(exc)}
    contract = reference_contract()
    report: dict = {
        "status": "running",
        "tool_versions": {tool_id: entry["version_pin"] for tool_id, entry in entries.items()},
        "tool_binary_sha256": {tool_id: entry["binary_sha256"] for tool_id, entry in entries.items()},
        "registry_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "controls": {},
    }
    out.mkdir(parents=True)
    for control in CONTROL_NAMES:
        case = out / control
        files = generate_control(control, contract)
        for rel, text in files.items():
            (case / rel).parent.mkdir(parents=True, exist_ok=True)
            (case / rel).write_text(text, encoding="utf-8")
        entry: dict = {"files": {rel: hashlib.sha256(text.encode("utf-8")).hexdigest() for rel, text in sorted(files.items())}}
        report["controls"][control] = entry
        for tool_id, timeout in (("openfoam_blockmesh", 120), ("openfoam_simplefoam", 900)):
            result = run_tool(tool_id, ["-case", str(case)], case, timeout, registry)
            (case / f"{tool_id}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
            if result.returncode:
                entry.update(status="failed", stage=tool_id, reason=result.code or f"exit {result.returncode}")
                break
        else:
            try:
                pressure = (case / "postProcessing" / "control_probes" / "0" / "p").read_text()
                entry.update(status="measured", **compare_control(control, contract, pressure).model_dump(mode="json"))
            except (OSError, ProbeResultError) as exc:
                entry.update(status="failed", stage="probe_parse", reason=str(exc))
    measured = [entry for entry in report["controls"].values() if entry["status"] == "measured"]
    report["status"] = ("passed" if len(measured) == len(CONTROL_NAMES) and all(e["passed"] for e in measured)
                        else "failed")
    (out / "controls_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.registry.resolve(), args.out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
