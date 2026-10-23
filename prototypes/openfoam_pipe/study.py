"""End-to-end validation study: one command builds, runs and checks every case.

    python -m prototypes.openfoam_pipe --work <scratch dir> --out <evidence dir> [--quick]

Cases are defined here as typed contracts only; everything else is generated.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from . import analysis, foam_io
from .casegen import write_case
from .contract import Fluid, Inlet, Mesh, PipeCase, Solver

WATER_20C = Fluid(name="water_20C", density_kg_m3=998.2, dynamic_viscosity_pa_s=1.002e-3)

LAMINAR_D = 0.01
LAMINAR_RES = (100.0, 250.0, 500.0, 1000.0)
LAMINAR_RADIAL_LEVELS = (8, 16, 32)          # refinement ratio 2 in r and x
C1_D, C1_U = 0.046, 0.45
SST_RADIAL_LEVELS = (30, 60, 120)
SST_WALL_CELL_TARGET_M = 4.0e-5              # medium mesh; y+ ~ 1 at Re ~ 2e4


@dataclass(frozen=True)
class Planned:
    case: PipeCase
    window: tuple[float, float]
    profile_x: float
    group: str
    level: int


def laminar_case(re: float, nr: int, level: int) -> Planned:
    d = LAMINAR_D
    u = re * WATER_20C.kinematic_viscosity_m2_s / d
    # The textbook entrance length 0.05 Re D is for the centreline velocity; the local
    # pressure gradient is still ~0.3 % above Hagen-Poiseuille at 0.075 Re D and within
    # 0.01 % only beyond ~0.1 Re D (measured in the first full run). Window: [0.125, 0.2375] Re D.
    length = max(25 * d, 0.25 * re * d)
    nx = int(round(length * nr / (4 * d)))     # dx = 8 dr
    case = PipeCase(
        name=f"lam_Re{int(re)}_r{nr}", diameter_m=d, length_m=length, fluid=WATER_20C,
        inlet=Inlet(mean_velocity_m_s=u), mesh=Mesh(radial_cells=nr, axial_cells=nx),
        turbulence="laminar", solver=Solver(max_iterations=20000, residual_target=1e-9),
    )
    return Planned(case, (0.5 * length, 0.95 * length), 0.95 * length, f"laminar_Re{int(re)}", level)


def radial_grading_for_wall_cell(radius: float, n: int, wall_cell: float) -> float:
    """blockMesh expansion ratio g (= last/first) such that the wall-adjacent cell is ``wall_cell``."""
    lo, hi = 1e-4, 1.0
    for _ in range(200):
        g = math.sqrt(lo * hi)
        q = g ** (1.0 / (n - 1)) if n > 1 else 1.0
        first = radius * (1 - q) / (1 - q**n) if abs(1 - q) > 1e-14 else radius / n
        last = first * q ** (n - 1)
        if last > wall_cell:
            hi = g
        else:
            lo = g
    return g


def c1_case(model: str, nr: int, level: int, grading: float) -> Planned:
    d, u = C1_D, C1_U
    length = 100 * d
    nx = {30: 200, 60: 400, 120: 800}.get(nr, 400) if model == "kOmegaSST" else 400
    case = PipeCase(
        name=f"c1_{model}_r{nr}", diameter_m=d, length_m=length, fluid=WATER_20C,
        inlet=Inlet(mean_velocity_m_s=u, turbulence_intensity=0.05, mixing_length_over_d=0.07),
        mesh=Mesh(radial_cells=nr, axial_cells=nx, radial_grading=grading),
        turbulence=model, solver=Solver(max_iterations=8000, residual_target=1e-6),
    )
    return Planned(case, (60 * d, 95 * d), 95 * d, f"c1_{model}", level)


def plan(quick: bool) -> list[Planned]:
    cases: list[Planned] = []
    levels = LAMINAR_RADIAL_LEVELS[:2] if quick else LAMINAR_RADIAL_LEVELS
    for re in ((500.0,) if quick else LAMINAR_RES):
        cases += [laminar_case(re, nr, i) for i, nr in enumerate(levels)]
    if quick:
        return cases
    g = radial_grading_for_wall_cell(C1_D / 2, SST_RADIAL_LEVELS[1], SST_WALL_CELL_TARGET_M)
    cases += [c1_case("kOmegaSST", nr, i, g) for i, nr in enumerate(SST_RADIAL_LEVELS)]
    cases.append(c1_case("kEpsilon", 8, 0, 1.0))  # uniform; wall-adjacent centre at y+ ~ 35
    return cases


def run_case(planned: Planned, work: Path) -> dict[str, Any]:
    case = planned.case
    case_dir = work / case.name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    manifest = write_case(case, case_dir)
    t0 = time.time()
    foam_io.run(["blockMesh"], case_dir, "log.blockMesh")
    check = foam_io.run(["checkMesh"], case_dir, "log.checkMesh")
    mesh_ok = "Mesh OK." in check
    foam_io.run(["simpleFoam"], case_dir, "log.simpleFoam")
    result = analysis.postprocess(case, case_dir, planned.window, planned.profile_x)
    log = foam_io.parse_solver_log((case_dir / "log.simpleFoam").read_text())
    return {
        "group": planned.group, "level": planned.level, "mesh_ok": mesh_ok,
        "wall_time_s": round(time.time() - t0, 1),
        "contract_sha256": manifest["files"], "contract": manifest["contract"],
        "result": result.as_dict(),
        "residual_history": {k: v[:: max(1, len(v) // 400)] for k, v in log.initial_residuals.items()
                             if k in ("Ux", "Uy", "p", "k", "omega", "epsilon")},
    }


def check_convergence(entry: dict[str, Any]) -> list[str]:
    """Problems that make a run unusable as evidence."""
    res = entry["result"]
    tol = entry["contract"]["solver"]["residual_target"]
    issues = []
    if not entry["mesh_ok"]:
        issues.append("checkMesh failed")
    if not res["converged"]:
        issues.append("SIMPLE residualControl not reached")
    for comp in ("Ux", "Uy"):
        if res["final_residuals"].get(comp, 1.0) > 100 * tol:
            issues.append(f"{comp} residual {res['final_residuals'][comp]:.2e} > 100x target")
    if abs(res["mass_imbalance"]) > 1e-6:
        issues.append(f"mass imbalance {res['mass_imbalance']:.2e}")
    return issues


def _tool_versions() -> dict[str, str]:
    def dpkg(pkg: str) -> str:
        out = subprocess.run(["dpkg-query", "-W", "-f=${Version}", pkg], capture_output=True, text=True,
                             check=False)
        return out.stdout.strip() or "absent"

    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
                         cwd=Path(__file__).parent).stdout.strip()
    return {"openfoam": foam_io.openfoam_version(), "gmsh_package": dpkg("gmsh"),
            "python3-gmsh_package": dpkg("python3-gmsh"), "git_head_at_run": sha or "unknown",
            "note": "Gmsh is installed and recorded but this prototype meshes with blockMesh (structured wedge)."}


def summarise(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_group: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        by_group.setdefault(e["group"], []).append(e)
    summary: dict[str, Any] = {"laminar": [], "turbulent": [], "issues": {}}
    for e in entries:
        problems = check_convergence(e)
        if problems:
            summary["issues"][e["result"]["name"]] = problems
    for group, items in sorted(by_group.items()):
        items.sort(key=lambda e: e["level"])
        case = PipeCase.model_validate(items[-1]["contract"])
        f_vals = [e["result"]["darcy_f"] for e in items]
        gci = analysis.grid_convergence(f_vals, 2.0).as_dict() if len(items) == 3 else None
        fine = items[-1]["result"]
        row: dict[str, Any] = {
            "group": group, "reynolds": case.reynolds, "model": case.turbulence,
            "meshes": [{"name": e["result"]["name"], "cells": e["result"]["cells"],
                        "darcy_f": e["result"]["darcy_f"], "dpdl_pa_m": e["result"]["dpdl_pa_m"],
                        "dpdl_wall_shear_pa_m": e["result"]["dpdl_wall_shear_pa_m"],
                        "iterations": e["result"]["iterations"], "y_plus": e["result"]["y_plus"],
                        "mass_imbalance": e["result"]["mass_imbalance"],
                        "flow_rate_error": e["result"]["flow_rate_error"],
                        "wall_time_s": e["wall_time_s"]} for e in items],
            "grid_convergence_f": gci,
        }
        if case.turbulence == "laminar":
            f_ref = 64.0 / case.reynolds
            row["reference"] = {"name": "Hagen-Poiseuille f=64/Re", "darcy_f": f_ref,
                                "dpdl_pa_m": analysis.hagen_poiseuille_dpdl(case)}
            row["fine_rel_error"] = fine["darcy_f"] / f_ref - 1.0
            row["fine_wall_shear_rel_error"] = fine["dpdl_wall_shear_pa_m"] / analysis.hagen_poiseuille_dpdl(case) - 1
            if gci and gci["extrapolated"] is not None:
                row["extrapolated_rel_error"] = gci["extrapolated"] / f_ref - 1.0
            row["profile_error_fine"] = analysis.parabolic_profile_error(analysis.CaseResult(**fine))
            summary["laminar"].append(row)
        else:
            bl, cb = analysis.blasius(case.reynolds), analysis.colebrook_smooth(case.reynolds)
            row["reference"] = {"blasius_f": bl, "colebrook_smooth_f": cb,
                                "mckeon_2005_f": analysis.mckeon_smooth(case.reynolds)}
            row["rel_error_vs_blasius"] = [m["darcy_f"] / bl - 1 for m in row["meshes"]]
            row["rel_error_vs_colebrook"] = [m["darcy_f"] / cb - 1 for m in row["meshes"]]
            summary["turbulent"].append(row)
    return summary


def reduced_model(summary: dict[str, Any], tools: dict[str, str]) -> dict[str, Any]:
    lam = sorted(summary["laminar"], key=lambda r: r["reynolds"])
    re = np.array([r["reynolds"] for r in lam])
    f = np.array([r["meshes"][-1]["darcy_f"] for r in lam])
    b, log_a = np.polyfit(np.log(re), np.log(f), 1)
    a = float(np.exp(log_a))
    fit_err = f / (a * re**b) - 1.0
    gcis = [r["grid_convergence_f"]["gci_fine"] for r in lam
            if r["grid_convergence_f"] and r["grid_convergence_f"]["gci_fine"] is not None]
    hp_err = [abs(r["fine_rel_error"]) for r in lam]
    model = {
        "model_id": "smooth_straight_pipe.darcy_friction.laminar",
        "status": "prototype (issue #913), not published to Process",
        "form": "f_D = a * Re**b ; dP/L = f_D * rho * U**2 / (2 * D)",
        "coefficients": {"a": a, "b": float(b)},
        "reference_form": "Hagen-Poiseuille: a = 64, b = -1",
        "validity": {
            "reynolds_min": float(re.min()), "reynolds_max": float(re.max()),
            "assumptions": ["Newtonian, incompressible, isothermal", "steady laminar flow",
                            "smooth straight circular pipe", "hydrodynamically fully developed section only "
                            "(entrance pressure loss excluded)"],
        },
        "uncertainty": {
            "max_abs_rel_error_vs_hagen_poiseuille": float(max(hp_err)),
            "max_gci_fine": float(max(gcis)) if gcis else None,
            "max_abs_fit_residual": float(np.max(np.abs(fit_err))),
        },
        "points": [{"reynolds": float(r_), "darcy_f_cfd": float(f_), "darcy_f_hp": 64.0 / r_,
                    "rel_error": float(f_ / (64.0 / r_) - 1)} for r_, f_ in zip(re, f)],
        "turbulent_spot_checks": [
            {"reynolds": t["reynolds"], "model": t["model"], "darcy_f_cfd_finest": t["meshes"][-1]["darcy_f"],
             "blasius_f": t["reference"]["blasius_f"], "colebrook_smooth_f": t["reference"]["colebrook_smooth_f"],
             "note": "outside the validated laminar range; not part of the fitted model"}
            for t in summary["turbulent"]],
        "provenance": tools,
    }
    return model


def export_vtk(case_dir: Path, out: Path) -> dict[str, Any]:
    foam_io.run(["foamToVTK", "-latestTime", "-no-boundary", "-fields", "(U p k omega nut)"], case_dir,
                "log.foamToVTK")
    internal = sorted((case_dir / "VTK").rglob("internal.vt[uk]"))
    target = out / (case_dir.name + internal[0].suffix)
    shutil.copyfile(internal[0], target)
    info: dict[str, Any] = {"file": target.name, "bytes": target.stat().st_size}
    try:
        import pyvista as pv

        grid = pv.read(target)
        info.update({"pyvista": pv.__version__, "n_cells": int(grid.n_cells),
                     "arrays": sorted(grid.array_names)})
    except ImportError:
        info["pyvista"] = "not installed"
    return info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, required=True, help="scratch directory for OpenFOAM cases")
    ap.add_argument("--out", type=Path, required=True, help="directory for results, plots, VTK")
    ap.add_argument("--quick", action="store_true", help="laminar Re=500 on two meshes only")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args(argv)
    if foam_io.foam_env() is None:
        raise SystemExit("OpenFOAM not found (need simpleFoam/blockMesh on PATH)")
    args.work.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    planned = plan(args.quick)
    # Longest cases first so the pool stays busy.
    planned.sort(key=lambda p: -p.case.mesh.radial_cells * p.case.mesh.axial_cells
                 * (5 if p.case.turbulence != "laminar" else 1))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_case, p, args.work) for p in planned]
        entries = []
        for p, fut in zip(planned, futures):
            entry = fut.result()
            print(f"{p.case.name:24s} Re={p.case.reynolds:8.1f} f={entry['result']['darcy_f']:.6f} "
                  f"it={entry['result']['iterations']} t={entry['wall_time_s']}s", flush=True)
            entries.append(entry)
    entries.sort(key=lambda e: (e["group"], e["level"]))
    tools = _tool_versions()
    summary = summarise(entries)
    results = {"tools": tools, "summary": summary, "cases": entries}
    # Smallest turbulent mesh keeps the committed VTK file small.
    vtk_case = next(p for p in planned if p.group == ("laminar_Re500" if args.quick else "c1_kOmegaSST")
                    and p.level == 0)
    results["vtk_export"] = export_vtk(args.work / vtk_case.case.name, args.out)
    (args.out / "results.json").write_text(json.dumps(results, indent=1, sort_keys=True))
    if len(summary["laminar"]) >= 2:
        (args.out / "reduced_model.json").write_text(json.dumps(reduced_model(summary, tools), indent=2))
    try:
        from .plots import make_plots

        make_plots(results, args.out)
    except ImportError as exc:  # matplotlib optional
        print(f"plots skipped: {exc}")
    print(json.dumps({"issues": summary["issues"]}, indent=1))
    return 1 if summary["issues"] else 0
