"""Pure-Python tests: contract validation, deterministic generation, references, parsers.
No OpenFOAM needed. Run from the repo root: python -m pytest prototypes/openfoam_pipe/tests -q
"""

from __future__ import annotations

import math

import pytest

from prototypes.openfoam_pipe import analysis, casegen, foam_io
from prototypes.openfoam_pipe.contract import Inlet, Mesh, PipeCase
from prototypes.openfoam_pipe.foam_dict import fmt_scalar


def _case(**kw) -> PipeCase:
    base = dict(name="t", diameter_m=0.01, length_m=0.3, inlet=Inlet(mean_velocity_m_s=0.05),
                mesh=Mesh(radial_cells=8, axial_cells=60))
    base.update(kw)
    return PipeCase(**base)


def test_inlet_requires_exactly_one_of_velocity_or_flow():
    with pytest.raises(ValueError):
        Inlet()
    with pytest.raises(ValueError):
        Inlet(mean_velocity_m_s=1.0, flow_rate_m3_s=1e-3)


def test_flow_rate_and_velocity_are_equivalent():
    a = _case()
    b = _case(inlet=Inlet(flow_rate_m3_s=a.flow_rate_m3_s))
    assert b.mean_velocity_m_s == pytest.approx(a.mean_velocity_m_s, rel=1e-12)
    assert casegen.generate(a)["0/U"] == casegen.generate(b)["0/U"]


def test_regime_and_geometry_guards():
    with pytest.raises(ValueError, match="laminar"):
        _case(inlet=Inlet(mean_velocity_m_s=0.5))          # Re ~ 5000
    with pytest.raises(ValueError, match="RANS"):
        _case(turbulence="kOmegaSST")                       # Re ~ 500
    with pytest.raises(ValueError, match="5 diameters"):
        _case(length_m=0.02)
    with pytest.raises(ValueError):
        _case(extra_field=1)


def test_generation_is_deterministic_and_complete(tmp_path):
    case = _case()
    first, second = casegen.generate(case), casegen.generate(case)
    assert first == second
    assert set(first) == {"0/U", "0/p", "constant/transportProperties", "constant/turbulenceProperties",
                          "system/blockMeshDict", "system/controlDict", "system/fvSchemes", "system/fvSolution"}
    manifest = casegen.write_case(case, tmp_path / "c")
    assert set(manifest["files"]) == set(first)
    with pytest.raises(FileExistsError):
        casegen.write_case(case, tmp_path / "c")


@pytest.mark.parametrize("model,extra", [("kOmegaSST", {"0/k", "0/omega", "0/nut"}),
                                         ("kEpsilon", {"0/k", "0/epsilon", "0/nut"})])
def test_rans_fields(model, extra):
    case = _case(diameter_m=0.046, length_m=1.0, inlet=Inlet(mean_velocity_m_s=0.45), turbulence=model)
    files = casegen.generate(case)
    assert extra <= set(files)
    assert f"RASModel {model};" in files["constant/turbulenceProperties"]
    k = 1.5 * (0.05 * 0.45) ** 2
    assert f"uniform {k:.12g}" in files["0/k"]


def test_wedge_cross_section_preserves_pipe_area():
    case = _case()
    verts = casegen.block_mesh_dict(case)["vertices"]
    _, _, (_x, y, z), *_ = verts
    tri_area = y * abs(z)  # triangle (axis, corner -z, corner +z): 0.5 * base(2|z|) * height(y)
    theta = math.radians(case.mesh.wedge_angle_deg)
    assert tri_area == pytest.approx(theta / 2 * (case.diameter_m / 2) ** 2, rel=1e-12)


def test_foam_scalar_formatting_rejects_bool():
    assert fmt_scalar((1.0, 0, 2.5)) == "(1 0 2.5)"
    with pytest.raises(TypeError):
        fmt_scalar(True)


def test_reference_correlations():
    assert analysis.blasius(1e4) == pytest.approx(0.3164e-1, rel=1e-3)
    # Prandtl–Kármán smooth law, tabulated values (Moody chart / McKeon et al. regime).
    for re, f in ((1e4, 0.03089), (1e5, 0.01799)):
        assert analysis.colebrook_smooth(re) == pytest.approx(f, rel=2e-3)
    fluids = pytest.importorskip("fluids")
    assert analysis.colebrook_smooth(2e4) == pytest.approx(fluids.friction.Colebrook(2e4, 0.0), rel=1e-9)


def test_grid_convergence_recovers_order():
    exact, c = 1.0, 0.3
    vals = [exact + c * h**2 for h in (4.0, 2.0, 1.0)]  # coarse -> fine
    g = analysis.grid_convergence(vals, 2.0)
    assert g.convergence == "monotonic"
    assert g.observed_order == pytest.approx(2.0)
    assert g.extrapolated == pytest.approx(exact)
    assert analysis.grid_convergence([1.0, 1.1, 1.05], 2.0).convergence == "oscillatory"


def test_solver_log_parsing():
    log = """
Time = 1

smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 0.01, No Iterations 2
smoothSolver:  Solving for Uy, Initial residual = 0.5, Final residual = 0.01, No Iterations 2
GAMG:  Solving for p, Initial residual = 1, Final residual = 0.001, No Iterations 4
time step continuity errors : sum local = 1e-05, global = 1e-07, cumulative = 1e-07
ExecutionTime = 0.01 s  ClockTime = 0 s

Time = 2

smoothSolver:  Solving for Ux, Initial residual = 0.1, Final residual = 0.001, No Iterations 2
smoothSolver:  Solving for Uy, Initial residual = 0.05, Final residual = 0.001, No Iterations 2
GAMG:  Solving for p, Initial residual = 0.2, Final residual = 0.001, No Iterations 4
time step continuity errors : sum local = 1e-06, global = 1e-08, cumulative = 1.1e-07

SIMPLE solution converged in 2 iterations
"""
    parsed = foam_io.parse_solver_log(log)
    assert parsed.iterations == 2 and parsed.converged
    assert parsed.initial_residuals["p"] == [1.0, 0.2]
    assert parsed.final_residuals()["Ux"] == 0.1
    assert parsed.continuity_cumulative[-1] == pytest.approx(1.1e-7)


def test_field_parsing_inline_and_multiline(tmp_path):
    text = """FoamFile
{
    class surfaceScalarField;
}
internalField nonuniform List<scalar>
12
(
1
2
3
4
5
6
7
8
9
10
11
12
)
;
boundaryField
{
    inlet
    {
        type calculated;
        value nonuniform List<scalar> 3(-1 -2 -3e-1);
    }
    outlet
    {
        type calculated;
        value uniform 4;
    }
    axis
    {
        type empty;
        value nonuniform List<scalar> 0();
    }
}
"""
    path = tmp_path / "phi"
    path.write_text(text)
    assert foam_io.read_internal(path).sum() == 78
    assert foam_io.read_patch_value(path, "inlet").tolist() == [-1.0, -2.0, -0.3]
    assert foam_io.read_patch_value(path, "outlet").tolist() == [4.0]
    assert foam_io.read_patch_value(path, "axis").size == 0
