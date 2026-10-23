"""Deterministic OpenFOAM case generation from a :class:`PipeCase` contract.

Geometry: 2D-axisymmetric wedge (axis = x, one azimuthal cell, ``wedge`` front/back
patches). A straight pipe with axisymmetric inflow has an axisymmetric steady
solution (laminar exactly; RANS mean flow by construction), so the wedge resolves
the same physics as a 3D pipe at ~1/(nθ) of the cost.

``generate(case)`` returns ``{relative_path: text}``; ``write_case`` writes it plus a
provenance manifest with SHA-256 per file. Same contract -> byte-identical case.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .contract import PipeCase
from .foam_dict import render

PATCHES = ("inlet", "outlet", "wall", "front", "back", "axis")
C_MU = 0.09


def _vec(x: float, y: float, z: float) -> tuple[float, float, float]:
    return (float(x), float(y), float(z))


def block_mesh_dict(case: PipeCase) -> dict[str, Any]:
    theta = math.radians(case.mesh.wedge_angle_deg)
    # Area-preserving corner radius: the flat (triangular) wedge cross-section then has
    # exactly the sector area theta*R^2/2, so the imposed velocity gives the exact Q.
    r = case.diameter_m / 2.0 * math.sqrt(theta / math.sin(theta))
    yc, zs = r * math.cos(theta / 2.0), r * math.sin(theta / 2.0)
    length = case.length_m
    m = case.mesh
    return {
        "convertToMeters": 1.0,
        "vertices": [
            _vec(0, 0, 0),
            _vec(length, 0, 0),
            _vec(length, yc, -zs),
            _vec(0, yc, -zs),
            _vec(length, yc, zs),
            _vec(0, yc, zs),
        ],
        # Collapsed hex: local faces on the axis degenerate to lines -> prisms on the axis.
        "blocks": [
            f"hex (0 1 2 3 0 1 4 5) ({m.axial_cells} {m.radial_cells} 1) "
            f"simpleGrading (1 {m.radial_grading:.12g} 1)"
        ],
        "edges": [],
        "boundary": [
            {"inlet": {"type": "patch", "faces": [(0, 0, 5, 3)]}},
            {"outlet": {"type": "patch", "faces": [(1, 2, 4, 1)]}},
            {"wall": {"type": "wall", "faces": [(3, 5, 4, 2)]}},
            {"front": {"type": "wedge", "faces": [(0, 3, 2, 1)]}},
            {"back": {"type": "wedge", "faces": [(0, 1, 4, 5)]}},
            {"axis": {"type": "empty", "faces": [(0, 1, 1, 0)]}},
        ],
        "mergePatchPairs": [],
    }


def _inlet_turbulence(case: PipeCase) -> dict[str, float]:
    u = case.mean_velocity_m_s
    k = 1.5 * (case.inlet.turbulence_intensity * u) ** 2
    ell = case.inlet.mixing_length_over_d * case.diameter_m
    return {
        "k": k,
        "epsilon": C_MU**0.75 * k**1.5 / ell,
        "omega": math.sqrt(k) / (C_MU**0.25 * ell),
    }


def _field(case: PipeCase, name: str, dims: str, internal: str, patches: dict[str, dict[str, Any]],
           foam_class: str = "volScalarField") -> str:
    boundary = {**patches, "front": {"type": "wedge"}, "back": {"type": "wedge"}, "axis": {"type": "empty"}}
    return render(foam_class, "0", name, {
        "dimensions": dims,
        "internalField": internal,
        "boundaryField": boundary,
    })


def initial_fields(case: PipeCase) -> dict[str, str]:
    u = case.mean_velocity_m_s
    u_in = f"uniform ({u:.12g} 0 0)"
    p_out = f"uniform {case.outlet_pressure_pa / case.fluid.density_kg_m3:.12g}"  # kinematic
    files = {
        "0/U": _field(case, "U", "[0 1 -1 0 0 0 0]", u_in, {
            "inlet": {"type": "fixedValue", "value": u_in},
            "outlet": {"type": "inletOutlet", "inletValue": "uniform (0 0 0)", "value": u_in},
            "wall": {"type": "noSlip"},
        }, foam_class="volVectorField"),
        "0/p": _field(case, "p", "[0 2 -2 0 0 0 0]", p_out, {
            "inlet": {"type": "zeroGradient"},
            "outlet": {"type": "fixedValue", "value": p_out},
            "wall": {"type": "zeroGradient"},
        }),
    }
    if case.turbulence == "laminar":
        return files
    t = _inlet_turbulence(case)
    out = {"type": "inletOutlet"}
    k_in = f"uniform {t['k']:.12g}"
    files["0/k"] = _field(case, "k", "[0 2 -2 0 0 0 0]", k_in, {
        "inlet": {"type": "fixedValue", "value": k_in},
        "outlet": {**out, "inletValue": k_in, "value": k_in},
        # Low-Re (SST, y+~1): k=0 at the wall. Wall functions (kEpsilon): kqRWallFunction.
        "wall": ({"type": "fixedValue", "value": "uniform 1e-15"} if case.turbulence == "kOmegaSST"
                 else {"type": "kqRWallFunction", "value": k_in}),
    })
    if case.turbulence == "kOmegaSST":
        w_in = f"uniform {t['omega']:.12g}"
        files["0/omega"] = _field(case, "omega", "[0 0 -1 0 0 0 0]", w_in, {
            "inlet": {"type": "fixedValue", "value": w_in},
            "outlet": {**out, "inletValue": w_in, "value": w_in},
            "wall": {"type": "omegaWallFunction", "value": w_in},  # viscous-sublayer value at y+<1
        })
        nut_wall = {"type": "nutLowReWallFunction", "value": "uniform 0"}
    else:
        e_in = f"uniform {t['epsilon']:.12g}"
        files["0/epsilon"] = _field(case, "epsilon", "[0 2 -3 0 0 0 0]", e_in, {
            "inlet": {"type": "fixedValue", "value": e_in},
            "outlet": {**out, "inletValue": e_in, "value": e_in},
            "wall": {"type": "epsilonWallFunction", "value": e_in},
        })
        nut_wall = {"type": "nutkWallFunction", "value": "uniform 0"}
    files["0/nut"] = _field(case, "nut", "[0 2 -1 0 0 0 0]", "uniform 0", {
        "inlet": {"type": "calculated", "value": "uniform 0"},
        "outlet": {"type": "calculated", "value": "uniform 0"},
        "wall": nut_wall,
    })
    return files


def system_files(case: PipeCase) -> dict[str, str]:
    turb = case.turbulence != "laminar"
    tol = case.solver.residual_target
    control = {
        "application": "simpleFoam",
        "startFrom": "startTime",
        "startTime": 0,
        "stopAt": "endTime",
        "endTime": case.solver.max_iterations,
        "deltaT": 1,
        "writeControl": "timeStep",
        "writeInterval": case.solver.max_iterations,
        "purgeWrite": 1,
        "writeFormat": "ascii",
        "writePrecision": 12,
        "writeCompression": "off",
        "timeFormat": "general",
        "timePrecision": 8,
        "runTimeModifiable": "false",
        # No function objects: they abort in the Ubuntu 1912 build (see polymesh.py);
        # derived quantities are computed in analysis.py from the written fields.
    }
    div = {
        "default": "none",
        "div(phi,U)": "bounded Gauss linearUpwind grad(U)",
        "div((nuEff*dev2(T(grad(U)))))": "Gauss linear",
    }
    if turb:
        div["div(phi,k)"] = "bounded Gauss limitedLinear 1"
        div["div(phi,omega)"] = "bounded Gauss limitedLinear 1"
        div["div(phi,epsilon)"] = "bounded Gauss limitedLinear 1"
    schemes = {
        "ddtSchemes": {"default": "steadyState"},
        "gradSchemes": {"default": "Gauss linear"},
        "divSchemes": div,
        "laplacianSchemes": {"default": "Gauss linear corrected"},
        "interpolationSchemes": {"default": "linear"},
        "snGradSchemes": {"default": "corrected"},
        "wallDist": {"method": "meshWave"},
    }
    # U is excluded on purpose: on a wedge the out-of-plane Uz component is ~0 and its
    # normalised residual is round-off noise that never decreases. Ux/Uy residuals are
    # checked after the run instead (see study.check_convergence).
    residual = {"p": tol}
    if turb:
        residual['"(k|omega|epsilon)"'] = tol
    solution = {
        "solvers": {
            "p": {"solver": "GAMG", "smoother": "GaussSeidel", "tolerance": tol * 1e-3, "relTol": 0.01},
            '"(U|k|omega|epsilon)"': {"solver": "smoothSolver", "smoother": "symGaussSeidel",
                                      "tolerance": tol * 1e-3, "relTol": 0.05},
        },
        "SIMPLE": {
            "nNonOrthogonalCorrectors": 0,
            "consistent": "yes",
            "residualControl": residual,
        },
        "relaxationFactors": {
            "equations": {"U": 0.9, '".*"': 0.7},
        },
    }
    return {
        "system/blockMeshDict": render("dictionary", "system", "blockMeshDict", block_mesh_dict(case)),
        "system/controlDict": render("dictionary", "system", "controlDict", control),
        "system/fvSchemes": render("dictionary", "system", "fvSchemes", schemes),
        "system/fvSolution": render("dictionary", "system", "fvSolution", solution),
    }


def constant_files(case: PipeCase) -> dict[str, str]:
    transport = {"transportModel": "Newtonian", "nu": f"{case.fluid.kinematic_viscosity_m2_s:.12g}"}
    if case.turbulence == "laminar":
        turbulence: dict[str, Any] = {"simulationType": "laminar"}
    else:
        turbulence = {"simulationType": "RAS",
                      "RAS": {"RASModel": case.turbulence, "turbulence": "on", "printCoeffs": "on"}}
    return {
        "constant/transportProperties": render("dictionary", "constant", "transportProperties", transport),
        "constant/turbulenceProperties": render("dictionary", "constant", "turbulenceProperties", turbulence),
    }


def generate(case: PipeCase) -> dict[str, str]:
    files = {**system_files(case), **constant_files(case), **initial_fields(case)}
    return dict(sorted(files.items()))


def write_case(case: PipeCase, case_dir: Path) -> dict[str, Any]:
    """Write the case and a provenance manifest; refuses to overwrite a non-empty directory."""
    case_dir = Path(case_dir)
    if case_dir.exists() and any(case_dir.iterdir()):
        raise FileExistsError(f"case directory {case_dir} is not empty")
    files = generate(case)
    for rel, text in files.items():
        path = case_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    manifest = {
        "contract": json.loads(case.model_dump_json()),
        "derived": {"reynolds": case.reynolds, "mean_velocity_m_s": case.mean_velocity_m_s,
                    "flow_rate_m3_s": case.flow_rate_m3_s},
        "files": {rel: hashlib.sha256(text.encode()).hexdigest() for rel, text in files.items()},
    }
    (case_dir / "jarvis_case_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest
