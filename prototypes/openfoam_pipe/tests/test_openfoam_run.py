"""Runs a real (coarse) laminar case. Skips cleanly when OpenFOAM is not installed."""

from __future__ import annotations

import math

import pytest

from prototypes.openfoam_pipe import analysis, foam_io, polymesh, study

pytestmark = pytest.mark.skipif(foam_io.foam_env() is None, reason="OpenFOAM (simpleFoam/blockMesh) not installed")


def test_coarse_laminar_pipe_matches_hagen_poiseuille(tmp_path):
    planned = study.laminar_case(200.0, 8, 0)
    entry = study.run_case(planned, tmp_path)
    assert study.check_convergence(entry) == []
    res = analysis.CaseResult(**entry["result"])
    case = planned.case

    # Geometry: the wedge holds exactly the pipe volume share.
    geo = polymesh.read_geometry(tmp_path / case.name)
    expected = math.pi * (case.diameter_m / 2) ** 2 * case.length_m * case.mesh.wedge_angle_deg / 360
    assert geo.cell_volumes.sum() == pytest.approx(expected, rel=1e-9)

    # Coarse mesh (8 radial cells): stated tolerances, well above what the study's finer meshes reach.
    assert res.darcy_f == pytest.approx(64 / case.reynolds, rel=0.02)
    assert res.dpdl_wall_shear_pa_m == pytest.approx(analysis.hagen_poiseuille_dpdl(case), rel=0.02)
    assert analysis.parabolic_profile_error(res)["max_abs"] < 0.02
    assert abs(res.mass_imbalance) < 1e-8
    assert abs(res.flow_rate_error) < 1e-8
