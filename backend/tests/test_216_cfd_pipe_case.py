"""Spec 216 offline tests: fluid domain, study contract, case generation, mesh check, residuals."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.bluecad.cfd_pipe import casegen, references
from app.modules.bluecad.cfd_pipe.contract import PipeStudyContract, contract_digest
from app.modules.bluecad.cfd_pipe.domain import FluidDomainError, derive_fluid_domain
from app.modules.bluecad.cfd_pipe.foam_dict import FoamDictError, fmt_scalar, render
from app.modules.bluecad.cfd_pipe.mesh_check import (
    CheckMeshReport,
    MeshCheckParseError,
    evaluate_mesh,
    parse_checkmesh,
)
from app.modules.bluecad.cfd_pipe.probe_results import ProbeResultError, laminar_comparison, parse_probes
from app.modules.bluecad.cfd_pipe.residuals import (
    LogParseError,
    ResidualStream,
    converged,
    parse_log,
    required_fields,
)
from app.modules.bluecad.template import TubeTemplateCreate, template_geometry_spec

FIXTURES = Path(__file__).parent / "fixtures" / "cfd_pipe"


def tube_spec(outer_d_mm: float = 50.0, wall_t_mm: float = 2.0, length_mm: float = 2000.0) -> dict:
    return template_geometry_spec(TubeTemplateCreate.model_validate(
        {"template": "tube", "params": {"outer_d_mm": outer_d_mm, "wall_t_mm": wall_t_mm, "length_mm": length_mm}}
    ))


def laminar(**overrides) -> PipeStudyContract:
    payload = {
        "domain": derive_fluid_domain(tube_spec(14.0, 2.0, 1000.0)),
        "inlet": {"mean_velocity_m_s": 0.05}, "regime": "laminar", "wall_treatment": "resolved",
    }
    return PipeStudyContract.model_validate({**payload, **overrides})


def c1_turbulent(**overrides) -> PipeStudyContract:
    payload = {
        "domain": derive_fluid_domain(tube_spec()), "inlet": {"mean_velocity_m_s": 0.45},
        "regime": "turbulent_rans", "turbulence_model": "kOmegaSST", "wall_treatment": "low_re_resolved", "mesh_level": 0,
    }
    return PipeStudyContract.model_validate({**payload, **overrides})


# --- fluid domain -------------------------------------------------------------------------


def test_fluid_domain_is_the_bore_and_digest_tracks_geometry() -> None:
    domain = derive_fluid_domain(tube_spec())
    assert domain.inner_diameter_m == pytest.approx(0.046)
    assert domain.length_m == pytest.approx(2.0)
    assert domain.patches == ("inlet", "outlet", "wall")
    assert derive_fluid_domain(tube_spec()).geometry_digest == domain.geometry_digest
    assert derive_fluid_domain(tube_spec(length_mm=2100.0)).geometry_digest != domain.geometry_digest
    assert derive_fluid_domain(tube_spec(wall_t_mm=3.0)).geometry_digest != domain.geometry_digest


def test_fluid_domain_refuses_non_tube_geometry() -> None:
    spec = tube_spec()
    two_parts = {**spec, "parts": [spec["parts"][0], {**spec["parts"][0], "part_id": "second"}]}
    two_parts.pop("spec_id")
    with pytest.raises(FluidDomainError) as exc:
        derive_fluid_domain(two_parts)
    assert exc.value.code == "geometry_unsupported"
    bend = {"spec_version": "bluecad_geometry_spec_v0_1", "name": "bend", "connections": [], "parts": [
        {"part_id": "b", "kind": "bend", "params": {"outer_d": 50.0, "wall_t": 2.0, "bend_radius": 100.0, "angle": 90.0}}]}
    with pytest.raises(FluidDomainError) as exc:
        derive_fluid_domain(bend)
    assert exc.value.code == "geometry_unsupported"
    with pytest.raises(FluidDomainError) as exc:
        derive_fluid_domain({"spec_version": "nope"})
    assert exc.value.code == "geometry_invalid"


# --- contract -----------------------------------------------------------------------------


def test_contract_derives_c1_reynolds_and_flow_rate_equivalence() -> None:
    by_velocity = c1_turbulent()
    assert by_velocity.reynolds == pytest.approx(0.45 * 0.046 / (1.002e-3 / 998.2))
    assert 2.0e4 < by_velocity.reynolds < 2.1e4
    by_flow = c1_turbulent(inlet={"flow_rate_m3_s": by_velocity.flow_rate_m3_s})
    assert by_flow.mean_velocity_m_s == pytest.approx(0.45)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"inlet": {}}, "exactly one"),
        ({"inlet": {"mean_velocity_m_s": 0.45, "flow_rate_m3_s": 1e-3}}, "exactly one"),
        ({"regime": "laminar", "turbulence_model": None, "wall_treatment": "resolved"}, "laminar regime requested at Re"),
        ({"turbulence_model": None}, "requires a turbulence model"),
        ({"wall_treatment": "resolved"}, "low_re_resolved"),
        ({"turbulence_model": "kEpsilon"}, "only with wall functions"),
        ({"inlet": {"mean_velocity_m_s": 0.05}}, "turbulent_rans requested at Re"),
        ({"domain": derive_fluid_domain(tube_spec(length_mm=1000.0))}, "developed flow"),
        ({"outlet_pressure_pa": float("inf")}, "finite"),
        ({"mesh_level": 5}, "less than or equal"),
        ({"unknown": 1}, "Extra inputs"),
    ],
)
def test_contract_refuses_inconsistent_studies(overrides: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        c1_turbulent(**overrides)


def test_laminar_contract_refuses_model_and_wall_treatment() -> None:
    with pytest.raises(ValidationError, match="no turbulence model"):
        laminar(turbulence_model="kOmegaSST")
    with pytest.raises(ValidationError, match="'resolved'"):
        laminar(wall_treatment="wall_function")
    with pytest.raises(ValidationError, match="Re=2491 > 2000"):
        laminar(inlet={"mean_velocity_m_s": 0.25})


def test_contract_digest_is_stable_and_input_sensitive() -> None:
    assert contract_digest(c1_turbulent()) == contract_digest(c1_turbulent())
    assert contract_digest(c1_turbulent(mesh_level=1)) != contract_digest(c1_turbulent())
    assert contract_digest(c1_turbulent(fluid={"density_kg_m3": 1000.0})) != contract_digest(c1_turbulent())


# --- references ---------------------------------------------------------------------------


def test_references_match_textbook_values() -> None:
    assert references.darcy_laminar(1000) == pytest.approx(0.064)
    assert references.darcy_blasius(1e5) == pytest.approx(0.01777, rel=1e-3)
    # Moody smooth-pipe value at Re = 1e5 is 0.0180.
    assert references.darcy_colebrook_smooth(1e5) == pytest.approx(0.0180, rel=5e-3)
    # Darcy-Weisbach with f = 64/Re is Hagen-Poiseuille 32 mu U / D^2.
    mu = 998.2 * 0.05 * 0.01 / 500
    gradient = references.pressure_gradient_pa_m(references.darcy_laminar(500), 998.2, 0.05, 0.01)
    assert gradient == pytest.approx(32 * mu * 0.05 / 0.01**2)
    assert references.poiseuille_velocity(0.0, 1.0, 1.0) == 2.0
    with pytest.raises(ValueError):
        references.darcy_laminar(0)


# --- foam dictionary serializer -----------------------------------------------------------


@pytest.mark.parametrize("value", ["a;b", "#include \"x\"", "$U", "x // y", "a{b}", 'odd"', "a\nb"])
def test_foam_dict_rejects_unsafe_tokens(value: str) -> None:
    with pytest.raises(FoamDictError):
        fmt_scalar(value)
    with pytest.raises(FoamDictError):
        render("dictionary", "system", "x", {value: 1})


def test_foam_dict_rejects_ambiguous_and_non_finite_values() -> None:
    for value in (True, float("nan"), float("inf"), None, object()):
        with pytest.raises(FoamDictError):
            fmt_scalar(value)


# --- case generation ----------------------------------------------------------------------


def test_case_generation_is_deterministic_and_complete(tmp_path: Path) -> None:
    contract = c1_turbulent()
    files = casegen.generate(contract)
    assert files == casegen.generate(c1_turbulent())
    assert sorted(files) == [
        "0/U", "0/k", "0/nut", "0/omega", "0/p", "constant/transportProperties",
        "constant/turbulenceProperties", "system/blockMeshDict", "system/controlDict",
        "system/fvSchemes", "system/fvSolution",
    ]
    first = casegen.write_case(contract, tmp_path / "a", {"openfoam_simplefoam": "v2412"})
    second = casegen.write_case(contract, tmp_path / "b", {"openfoam_simplefoam": "v2412"})
    assert first == second
    assert casegen.manifest_digest(first) == casegen.manifest_digest(second)
    on_disk = json.loads((tmp_path / "a" / casegen.MANIFEST_NAME).read_text())
    assert on_disk == first
    assert first["geometry_digest"] == contract.domain.geometry_digest
    assert first["contract_digest"] == contract_digest(contract)
    assert first["tool_versions"] == {"openfoam_simplefoam": "v2412"}
    for rel, digest in first["files"].items():
        assert hashlib.sha256((tmp_path / "a" / rel).read_bytes()).hexdigest() == digest
    other = casegen.write_case(contract, tmp_path / "c", {"openfoam_simplefoam": "v2506"})
    assert casegen.manifest_digest(other) != casegen.manifest_digest(first)
    with pytest.raises(FileExistsError):
        casegen.write_case(contract, tmp_path / "a", {})


def test_laminar_case_has_no_turbulence_fields_and_regime_dictionaries() -> None:
    files = casegen.generate(laminar())
    assert set(files) >= {"0/U", "0/p"} and not {"0/k", "0/omega", "0/epsilon", "0/nut"} & set(files)
    assert "simulationType laminar;" in files["constant/turbulenceProperties"]
    kepsilon = casegen.generate(c1_turbulent(turbulence_model="kEpsilon", wall_treatment="wall_function"))
    assert "0/epsilon" in kepsilon and "0/omega" not in kepsilon
    assert "kqRWallFunction" in kepsilon["0/k"] and "nutkWallFunction" in kepsilon["0/nut"]
    sst = casegen.generate(c1_turbulent())
    assert "nutLowReWallFunction" in sst["0/nut"] and "RASModel kOmegaSST;" in sst["constant/turbulenceProperties"]


def test_case_values_come_from_contract() -> None:
    contract = c1_turbulent(outlet_pressure_pa=998.2)
    files = casegen.generate(contract)
    assert "uniform (0.45 0 0)" in files["0/U"]
    assert "uniform 1;" in files["0/p"]  # kinematic: 998.2 Pa / 998.2 kg/m3
    assert f"nu {contract.fluid.kinematic_viscosity_m2_s:.12g};" in files["constant/transportProperties"]
    for text in files.values():
        assert "#" not in text.split("\n", 1)[1] and "$" not in text
    # No solver-side residualControl; the runner judges convergence and stops via controlDict.
    assert "residualControl" not in files["system/fvSolution"]
    assert "runTimeModifiable true;" in files["system/controlDict"]
    assert "type probes;" in files["system/controlDict"]
    assert "probeLocations" in files["system/controlDict"]
    stop = casegen.control_dict(contract, stop_now=True)
    assert "stopAt writeNow;" in stop and "stopAt endTime;" in files["system/controlDict"]


def test_quarter_pipe_geometry_and_exact_flow_rate() -> None:
    contract = c1_turbulent()
    files = casegen.generate(contract)
    mesh = casegen.block_mesh_dict(contract, casegen.mesh_plan(contract))
    assert len(mesh["vertices"]) == 14 and len(mesh["blocks"]) == 3 and len(mesh["edges"]) == 4
    assert {next(iter(item)) for item in mesh["boundary"]} == {"inlet", "outlet", "wall", "symmetry_y", "symmetry_z"}
    wall_points = [mesh["vertices"][index] for index in (4, 5, 6, 11, 12, 13)]
    assert all(math.hypot(y, z) == pytest.approx(0.023, rel=1e-12) for _, y, z in wall_points)
    for field in ("0/U", "0/p", "0/k", "0/omega", "0/nut"):
        assert files[field].count("type symmetryPlane;") == 2
    # A quarter of the exact contract flow rate, independent of the faceted wall area.
    assert f"volumetricFlowRate constant {contract.flow_rate_m3_s / 4:.12g};" in files["0/U"]
    assert "flowRateInletVelocity" in files["0/U"]


def test_real_v2412_probe_samples_report_pressure_and_profile_errors() -> None:
    contract = laminar(mesh_level=0, inlet={"mean_velocity_m_s": 0.01},
                       domain=derive_fluid_domain(tube_spec(14.0, 2.0, 200.0)))
    pressure = (FIXTURES / "laminar_probe_p.txt").read_text()
    velocity = (FIXTURES / "laminar_probe_U.txt").read_text()
    comparison = laminar_comparison(contract, pressure, velocity)
    assert comparison["iteration"] == 300
    assert comparison["pressure_gradient_pa_m"] == pytest.approx(4.01680543857)
    assert comparison["hagen_poiseuille_pa_m"] == pytest.approx(3.2064)
    # This real coarse-mesh result misses the analytic gradient; never mark it validated.
    assert comparison["pressure_gradient_relative_error"] > 0.25
    assert comparison["profile_max_error_over_mean_velocity"] < 0.02


def test_probe_reader_refuses_missing_or_mismatched_samples() -> None:
    pressure = (FIXTURES / "laminar_probe_p.txt").read_text()
    velocity = (FIXTURES / "laminar_probe_U.txt").read_text()
    contract = laminar(mesh_level=0, inlet={"mean_velocity_m_s": 0.01},
                       domain=derive_fluid_domain(tube_spec(14.0, 2.0, 200.0)))
    with pytest.raises(ProbeResultError, match="missing or non-finite"):
        parse_probes(pressure.replace("0.000295641728524", "nan").replace("0.000286136884695", "nan"), vectors=False)
    with pytest.raises(ProbeResultError, match="different iterations"):
        laminar_comparison(contract, pressure, velocity.replace("300 ", "299 "))
    with pytest.raises(ProbeResultError, match="differs from the typed case"):
        laminar_comparison(contract, pressure.replace("0.13 ", "0.12 "), velocity.replace("0.13 ", "0.12 "))


# --- mesh check ---------------------------------------------------------------------------


def test_checkmesh_parsing_from_real_v2412_log() -> None:
    report = parse_checkmesh((FIXTURES / "checkMesh_ok.log").read_text())
    assert report == CheckMeshReport(cells=121800, max_non_orthogonality_deg=26.0357950025, max_skewness=0.53926781269,
                                     max_aspect_ratio=290.510122154, failed_checks=0)
    record = evaluate_mesh(c1_turbulent(), casegen.mesh_plan(c1_turbulent()), report)
    assert record.accepted and record.refusals == ()


def test_checkmesh_failure_forms_are_parsed() -> None:
    log = (FIXTURES / "checkMesh_ok.log").read_text()
    failing = log.replace("Max aspect ratio = 290.510122154 OK.",
                          " ***High aspect ratio cells found, Max aspect ratio: 1500.5, number of cells 3")
    failing = failing.replace("Mesh OK.", "Failed 1 mesh checks.")
    report = parse_checkmesh(failing)
    assert report.max_aspect_ratio == 1500.5 and report.failed_checks == 1
    with pytest.raises(MeshCheckParseError):
        parse_checkmesh("Mesh stats\n    cells: 10\n")
    with pytest.raises(MeshCheckParseError):
        parse_checkmesh(log.replace("Mesh OK.", ""))


def test_mesh_check_refuses_bad_meshes() -> None:
    contract = c1_turbulent()
    plan = casegen.mesh_plan(contract)
    good = parse_checkmesh((FIXTURES / "checkMesh_ok.log").read_text())
    bad = good.model_copy(update={"failed_checks": 2, "max_non_orthogonality_deg": 75.0, "max_skewness": 5.0,
                                  "max_aspect_ratio": 2000.0, "cells": 10})
    record = evaluate_mesh(contract, plan, bad)
    assert not record.accepted
    assert [reason.split(":")[0] for reason in record.refusals] == [
        "checkmesh_failed", "cell_count_mismatch", "non_orthogonality", "skewness", "aspect_ratio"]
    assert evaluate_mesh(contract, plan, None).refusals == ("check_missing: no checkMesh report",)
    coarse_wall = plan.model_copy(update={"estimated_wall_yplus": 3.0})
    assert evaluate_mesh(contract, coarse_wall, good).refusals[0].startswith("wall_yplus")
    wf = c1_turbulent(turbulence_model="kEpsilon", wall_treatment="wall_function", mesh_level=2)
    wf_plan = casegen.mesh_plan(wf)
    assert wf_plan.estimated_wall_yplus < 30  # wall functions cannot be refined into the buffer layer
    assert evaluate_mesh(wf, wf_plan, good.model_copy(update={"cells": wf_plan.cell_count})).refusals[0].startswith("wall_yplus")
    huge = plan.model_copy(update={"cell_count": 3_000_000})
    assert any(reason.startswith("cell_budget") for reason in evaluate_mesh(contract, huge, good).refusals)


# --- residual parsing ---------------------------------------------------------------------


def test_residual_log_from_real_v2412_run() -> None:
    header = "trapFpe: Floating point exception trapping enabled (FOAM_SIGFPE).\n"
    rows = parse_log(header + (FIXTURES / "simpleFoam_kOmegaSST.log").read_text())
    assert [row.iteration for row in rows] == [1, 2, 3, 40]
    last = rows[-1]
    assert set(last.initial) == {"Ux", "Uy", "Uz", "p", "omega", "k"}
    assert last.initial["p"] == pytest.approx(0.000965657617802)
    assert last.continuity_global == pytest.approx(4.82195429026e-06)
    assert last.execution_time_s == pytest.approx(57.55)
    assert last.max_normalized_residual == pytest.approx(0.00475699508039)


def test_residual_stream_is_incremental_across_arbitrary_chunks() -> None:
    text = (FIXTURES / "simpleFoam_kOmegaSST.log").read_text()
    whole = parse_log(text)
    stream = ResidualStream()
    seen = []
    for index in range(0, len(text), 37):
        seen.extend(stream.feed(text[index:index + 37]))
        # Live: an iteration is published once its ExecutionTime line arrives, not at the end.
        if index < len(text) // 2:
            assert len(seen) < len(whole)
    seen.extend(stream.close())
    assert seen == whole
    assert stream.fatal is None and stream.solver_reported_end


def test_residual_stream_flags_fatal_and_rejects_hostile_values() -> None:
    stream = ResidualStream()
    stream.feed("Time = 1\n\n--> FOAM FATAL ERROR: \nsomething\n")
    assert stream.fatal is not None
    with pytest.raises(LogParseError):
        parse_log("Time = 1\nsmoothSolver:  Solving for Ux, Initial residual = nan, Final residual = 1, No Iterations 1\n")
    with pytest.raises(LogParseError):
        parse_log("Time = 1.5\n")
    # A trailing iteration cut off before its ExecutionTime line is not published.
    partial = (FIXTURES / "simpleFoam_kOmegaSST.log").read_text().split("\nEnd")[0].rsplit("ExecutionTime", 1)[0]
    assert [row.iteration for row in parse_log(partial)] == [1, 2, 3]


def test_residual_stream_drops_iteration_missing_execution_time_before_next_time() -> None:
    log = (
        "Time = 1\nSolving for Ux, Initial residual = 0.1, Final residual = 0.01, No Iterations 1\n"
        "Time = 2\nSolving for Ux, Initial residual = 0.02, Final residual = 0.001, No Iterations 1\n"
        "ExecutionTime = 2 s  ClockTime = 2 s\n"
    )
    assert [row.iteration for row in parse_log(log)] == [2]


def test_convergence_requires_every_field_below_target_over_window() -> None:
    def log(values: list[float]) -> str:
        return "".join(
            f"Time = {i}\nsmoothSolver:  Solving for Ux, Initial residual = {v}, Final residual = 0, No Iterations 1\n"
            f"smoothSolver:  Solving for Uy, Initial residual = {v}, Final residual = 0, No Iterations 1\n"
            f"smoothSolver:  Solving for Uz, Initial residual = {v}, Final residual = 0, No Iterations 1\n"
            f"GAMG:  Solving for p, Initial residual = {v}, Final residual = 0, No Iterations 1\n"
            f"ExecutionTime = {i} s  ClockTime = {i} s\n\n" for i, v in enumerate(values, start=1))
    fields = required_fields(())
    assert converged(parse_log(log([1e-3] + [1e-7] * 5)), fields, 1e-6)
    assert not converged(parse_log(log([1e-7] * 4)), fields, 1e-6)  # window not filled
    assert not converged(parse_log(log([1e-7] * 4 + [2e-6])), fields, 1e-6)
    assert not converged(parse_log(log([1e-7] * 6)), required_fields(("k", "omega")), 1e-6)  # missing fields


# --- real tools (skips cleanly when absent) -----------------------------------------------


@pytest.mark.skipif(
    not os.environ.get("JARVISOS_BLUECAD_TOOL_REGISTRY") or shutil.which("true") is None,
    reason="operator tool registry with OpenFOAM is not configured",
)
def test_generated_case_meshes_and_passes_check_with_real_openfoam(tmp_path: Path) -> None:
    from app.modules.bluecad.registry import ToolRegistryError, resolve_tool, run_tool

    try:
        pins = {tool: resolve_tool(tool)["version_pin"] for tool in ("openfoam_blockmesh", "openfoam_checkmesh")}
    except ToolRegistryError as exc:
        pytest.skip(f"OpenFOAM tools unavailable: {exc.code}")
    contract = c1_turbulent()
    case_dir = tmp_path / "case"
    casegen.write_case(contract, case_dir, pins)
    mesh = run_tool("openfoam_blockmesh", [], case_dir, 120)
    assert mesh.returncode == 0, mesh.stdout[-2000:] + mesh.stderr[-2000:]
    check = run_tool("openfoam_checkmesh", [], case_dir, 120)
    record = evaluate_mesh(contract, casegen.mesh_plan(contract), parse_checkmesh(check.stdout))
    assert record.accepted, record.refusals
