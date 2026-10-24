"""Run one typed spec 216 case with pinned tools and record measured evidence.

    PYTHONPATH=backend python scripts/qualification/216/run_case.py \
      --contract /path/to/contract.json --registry /path/to/operator-registry.yaml \
      --out /path/outside/repo/run-1

This qualification command captures final solver logs. It does not present
buffered output as live residuals or publish a reduced model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from app.modules.bluecad.cfd_pipe.casegen import MAX_PROCESSORS, manifest_digest, mesh_plan, write_case
from app.modules.bluecad.cfd_pipe.contract import PipeStudyContract
from app.modules.bluecad.cfd_pipe.mesh_check import evaluate_mesh, parse_checkmesh, plan_refusals
from app.modules.bluecad.cfd_pipe.probe_results import ProbeResultError, laminar_comparison, turbulent_comparison
from app.modules.bluecad.cfd_pipe.residuals import LogParseError, ResidualStream, converged, required_fields
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool, run_tool

TOOLS = ("openfoam_blockmesh", "openfoam_checkmesh", "openfoam_simplefoam")
PARALLEL_TOOLS = ("openfoam_decomposepar", "openfoam_mpiexec", "openfoam_reconstructpar")
_REPO = Path(__file__).resolve().parents[3]
# conda-forge openfoam-2412 links its binaries with RPATH .../lib/sys-mpich, which
# the package does not ship, so they fall back to lib/dummy/libPstream.so and abort
# under MPI. Ranks preload the shipped MPICH Pstream instead (spec 216 requirement 1).
_MPI_PSTREAM = Path("lib") / "mpich-3.3" / "libPstream.so"


def tool_steps(contract: PipeStudyContract) -> tuple[tuple[str, float], ...]:
    """Pinned tools in order with their wall-clock bounds; the solver's comes from the contract."""
    return (("openfoam_blockmesh", 120), ("openfoam_checkmesh", 120),
            ("openfoam_simplefoam", contract.solver.wall_time_limit_s))


def command_steps(contract: PipeStudyContract, case: Path, entries: dict[str, dict],
                  processors: int) -> list[tuple[str, list[str], float]]:
    """(tool id, arguments, wall-clock bound) for a serial or MPI run of ``case``."""
    steps = [(tool_id, ["-case", str(case)], timeout) for tool_id, timeout in tool_steps(contract)]
    if processors == 1:
        return steps
    solver = entries["openfoam_simplefoam"]
    pstream = Path(solver["entrypoint"]).resolve().parent.parent / _MPI_PSTREAM
    mpi_solver = ["-genv", "LD_PRELOAD", str(pstream), "-genv", "WM_PROJECT_VERSION", solver["version_pin"],
                  "-np", str(processors), solver["entrypoint"], "-parallel", "-case", str(case)]
    return [*steps[:2], ("openfoam_decomposepar", ["-case", str(case)], 600),
            ("openfoam_mpiexec", mpi_solver, steps[2][2]),
            ("openfoam_reconstructpar", ["-latestTime", "-case", str(case)], 600)]


def run(contract: PipeStudyContract, registry: Path, out: Path, processors: int = 1) -> dict:
    out = out.resolve()
    if out.is_relative_to(_REPO):
        raise ValueError("qualification output must be outside the repository")
    if out.exists():
        raise FileExistsError(f"qualification output already exists: {out}")
    if not 1 <= processors <= MAX_PROCESSORS:
        raise ValueError(f"processors must be 1 to {MAX_PROCESSORS}")
    plan = mesh_plan(contract)
    refusals = plan_refusals(contract, plan)
    if refusals:
        return {"status": "refused", "refusals": refusals}
    tools = TOOLS + (PARALLEL_TOOLS if processors > 1 else ())
    try:
        entries = {tool_id: resolve_tool(tool_id, registry) for tool_id in tools}
    except ToolRegistryError as exc:
        return {"status": "unavailable", "reason": str(exc)}
    pins = {tool_id: entry["version_pin"] for tool_id, entry in entries.items()}
    case = out / "case"
    steps = command_steps(contract, case, entries, processors)
    pstream = Path(steps[3][1][2]) if processors > 1 else None
    if pstream is not None and not pstream.is_file():
        return {"status": "unavailable", "reason": f"MPI Pstream library missing: {pstream}"}
    out.mkdir(parents=True)
    manifest = write_case(contract, case, pins, processors)
    report: dict = {
        "status": "running", "case_manifest_digest": manifest_digest(manifest),
        "contract_digest": manifest["contract_digest"],
        "geometry_digest": manifest["geometry_digest"], "tool_versions": pins,
        "registry_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "tool_binary_sha256": {tool_id: entry["binary_sha256"] for tool_id, entry in entries.items()},
        "tool_provenance": {tool_id: entry["provenance_url"] for tool_id, entry in entries.items()},
        "tool_licenses": {tool_id: entry["license"] for tool_id, entry in entries.items()},
        "mesh_plan": plan.model_dump(mode="json"), "processors": processors,
    }
    if pstream is not None:
        report["mpi_pstream_sha256"] = hashlib.sha256(pstream.read_bytes()).hexdigest()

    def save() -> None:
        (out / "run_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    save()
    for tool_id, args, timeout in steps:
        result = run_tool(tool_id, args, case, timeout, registry)
        (out / f"{tool_id}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            report.update(status="failed", stage=tool_id, returncode=result.returncode,
                          reason=result.code or f"process exited with {result.returncode}")
            save()
            return report
        if tool_id == "openfoam_checkmesh":
            check = evaluate_mesh(contract, plan, parse_checkmesh(result.stdout))
            report["mesh_check"] = check.model_dump(mode="json")
            if not check.accepted:
                report.update(status="refused", stage="mesh_check", refusals=list(check.refusals))
                save()
                return report
            save()
        if tool_id in ("openfoam_simplefoam", "openfoam_mpiexec"):
            stream = ResidualStream()
            try:
                rows = stream.feed(result.stdout)
                rows.extend(stream.close())
            except LogParseError as exc:
                report.update(status="failed", stage="residual_parse", reason=str(exc))
                save()
                return report
            fields = required_fields(("k", "omega") if contract.turbulence_model == "kOmegaSST" else
                                     ("k", "epsilon") if contract.turbulence_model == "kEpsilon" else ())
            report["iterations_completed"] = len(rows)
            report["residual_converged"] = converged(rows, fields, contract.solver.residual_target)
            report["last_residuals"] = rows[-1].model_dump(mode="json") if rows else None
            if stream.fatal or not stream.solver_reported_end or len(rows) != contract.solver.max_iterations:
                report.update(status="failed", stage="solver_completion", reason=stream.fatal or "solver output is incomplete")
                save()
                return report
            probes = case / "postProcessing" / "pipe_probes" / "0"
            key, compare = (("laminar_comparison", laminar_comparison) if contract.regime == "laminar"
                            else ("turbulent_comparison", turbulent_comparison))
            try:
                report[key] = compare(contract, (probes / "p").read_text(), (probes / "U").read_text())
            except (OSError, ProbeResultError) as exc:
                report.update(status="failed", stage="probe_parse", reason=str(exc))
                save()
                return report
            if processors == 1:
                report["status"] = "measured"
            save()
        if tool_id == "openfoam_reconstructpar":
            report["status"] = "measured"
            save()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--processors", type=int, default=1, help="MPI ranks; 1 runs serially")
    args = parser.parse_args()
    contract = PipeStudyContract.model_validate_json(args.contract.read_text(encoding="utf-8"))
    report = run(contract, args.registry.resolve(), args.out, args.processors)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "measured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
