from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.modules.ai.execution import ProviderBinding
from app.modules.bluecad.ledger import ScriptedFakeBluecadAdapter
from app.modules.bluecad.loop import create_bluecad_candidate
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadLoopConfig
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool

FIXTURES = Path(__file__).parent / "fixtures"


def _kernel_unavailable_reason() -> str | None:
    if importlib.util.find_spec("build123d") is None:
        return "build123d is not installed"
    try:
        import build123d  # noqa: F401
    except ImportError as exc:
        return f"build123d cannot be imported: {exc}"
    return None


requires_kernel = pytest.mark.skipif(_kernel_unavailable_reason() is not None, reason=_kernel_unavailable_reason() or "build123d unavailable")


def _init() -> None:
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)


def _bindings() -> dict[str, ProviderBinding]:
    return {route: ProviderBinding(route, "scaleway", "scripted", False, 4000) for route in ["external:cheap", "external:reasoning"]}


def _spec(name: str = "minimal_single_tube.json") -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _bad_volume_spec() -> str:
    payload = json.loads(_spec())
    payload["declared"]["total_volume_mm3"]["value"] = 1.0
    return json.dumps(payload)


def _analysis_spec(part_id: str = "run1") -> dict[str, Any]:
    return {
        "schema_version": "bluecad_analysis_spec_v0_1",
        "analysis_id": "a1",
        "analysis_type": "static",
        "material": {"name": "steel", "E": 200000.0, "nu": 0.3, "rho": 7.8e-9, "yield_strength": 250.0},
        "bcs": [{"port_label": f"{part_id}.port_a", "kind": "fixed"}],
        "loads": [{"port_label": f"{part_id}.port_b", "type": "force_total", "force": [1.0, 0.0, 0.0]}],
        "mesh": {"target_size": 5.0},
        "pass_criteria": [{"metric": "max_von_mises", "op": "<=", "value": 300.0}],
    }


def _mesh_pass() -> dict[str, Any]:
    return {
        "schema_version": "bluecad_mesh_result_v0_1",
        "verdict": "pass",
        "errors": [],
        "attempts": [{"attempt_no": 1, "target_size": 5.0, "counts": {"elements_total": 2, "nodes_total": 4}, "errors": []}],
        "artifacts": {"mesh_inp": {"path": "mesh.inp", "sha256": "abc", "bytes": 12}},
    }


def _mesh_fail() -> dict[str, Any]:
    return {
        "schema_version": "bluecad_mesh_result_v0_1",
        "verdict": "fail",
        "errors": [{"code": "MESH_GROUP_EMPTY", "detail": {"group": "LOAD_run1_port_b"}}],
        "attempts": [{"attempt_no": 1, "target_size": 5.0, "counts": {}, "errors": []}],
        "artifacts": {},
    }


def _fem(verdict: str = "pass") -> dict[str, Any]:
    if verdict == "error":
        return {
            "schema_version": "bluecad_result_summary_v0_1",
            "verdict": "error",
            "errors": [{"code": "SOLVE_ERROR", "detail": {"returncode": 1}}],
            "solver": {"tool_id": "calculix", "version": "fake", "returncode": 1},
            "artifacts": {},
        }
    return {
        "schema_version": "bluecad_result_summary_v0_1",
        "verdict": "pass",
        "errors": [],
        "solver": {"tool_id": "calculix", "version": "fake", "returncode": 0},
        "max_displacement": {"node_id": 1, "value": 0.1},
        "max_von_mises": {"element_id": 1, "node_id": 1, "value": 100.0},
        "artifacts": {},
    }


def _evidence() -> list[dict[str, Any]]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT kind, verdict, metrics_json, candidate_id, attempt_id, report_artifact_id, source_run_id FROM evidence_records ORDER BY created_at, id"
        ).fetchall()
    return [dict(row) for row in rows]


def _simulation_run_payloads() -> list[dict[str, Any]]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT parameter_payload FROM simulation_runs ORDER BY created_at, id").fetchall()
    return [json.loads(row["parameter_payload"]) for row in rows]


def _artifact_json(artifact_id: str) -> dict[str, Any]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT stored_path FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    assert row is not None
    return json.loads(Path(row["stored_path"]).read_text(encoding="utf-8"))


def test_analysis_spec_rejects_malformed_nested_blocks() -> None:
    for key in ["material", "mesh"]:
        malformed = _analysis_spec()
        malformed[key] = {}
        with pytest.raises(ValidationError):
            BluecadLoopConfig(analysis_spec=malformed)


def test_analysis_spec_rejects_missing_nested_load_contract() -> None:
    malformed = _analysis_spec()
    malformed["loads"] = [{"port_label": "run1.port_b", "force": [1.0, 0.0, 0.0]}]
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=malformed)


def test_analysis_spec_rejects_malformed_load_payloads() -> None:
    missing_pressure = _analysis_spec()
    missing_pressure["loads"] = [{"port_label": "run1.port_b", "type": "pressure"}]
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=missing_pressure)

    missing_force_total = _analysis_spec()
    missing_force_total["loads"] = [{"port_label": "run1.port_b", "type": "force_total"}]
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=missing_force_total)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("material", "E"), "200000.0"),
        (("material", "nu"), "0.3"),
        (("material", "rho"), "7.8e-9"),
        (("material", "yield_strength"), "250.0"),
        (("mesh", "target_size"), "5.0"),
        (("loads", 0, "force", 0), "1.0"),
        (("pass_criteria", 0, "value"), "300.0"),
        (("timeout_s",), "30.0"),
    ],
)
def test_analysis_spec_rejects_string_numeric_values(path: tuple[str | int, ...], value: str) -> None:
    malformed = _analysis_spec()
    target: Any = malformed
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=malformed)


def test_analysis_spec_rejects_caller_supplied_geometry() -> None:
    malformed = _analysis_spec()
    malformed["geometry"] = {"step_path": "caller.step", "manifest_path": "caller.json"}
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=malformed)


@requires_kernel
def test_analysis_spec_absent_skips_simulation(monkeypatch: pytest.MonkeyPatch) -> None:
    _init()
    mesh_calls = 0

    def mesh(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal mesh_calls
        mesh_calls += 1
        return _mesh_pass()

    monkeypatch.setattr("app.modules.bluecad.loop.mesh_analysis_spec", mesh)
    candidate = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube"),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    assert candidate.status == "valid"
    assert mesh_calls == 0
    assert [row["kind"] for row in _evidence()] == ["validation_v0"]


@requires_kernel
def test_analysis_spec_mesh_fail_records_evidence_without_solve(monkeypatch: pytest.MonkeyPatch) -> None:
    _init()
    solve_calls = 0
    monkeypatch.setattr("app.modules.bluecad.loop.mesh_analysis_spec", lambda *_args, **_kwargs: _mesh_fail())

    def solve(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal solve_calls
        solve_calls += 1
        return _fem()

    monkeypatch.setattr("app.modules.bluecad.loop.solve_static_analysis", solve)
    candidate = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube", loop_config=BluecadLoopConfig(analysis_spec=_analysis_spec())),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    assert candidate.status == "valid"
    assert solve_calls == 0
    rows = _evidence()
    assert [(row["kind"], row["verdict"]) for row in rows] == [("validation_v0", "pass"), ("mesh_quality_v0", "fail")]
    assert rows[1]["candidate_id"] == candidate.id
    assert rows[1]["attempt_id"] == candidate.attempts[0].id


@requires_kernel
def test_analysis_spec_mesh_pass_solve_error_records_both(monkeypatch: pytest.MonkeyPatch) -> None:
    _init()
    monkeypatch.setattr("app.modules.bluecad.loop.mesh_analysis_spec", lambda *_args, **_kwargs: _mesh_pass())
    monkeypatch.setattr("app.modules.bluecad.loop.solve_static_analysis", lambda *_args, **_kwargs: _fem("error"))
    candidate = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube", loop_config=BluecadLoopConfig(analysis_spec=_analysis_spec())),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    assert candidate.status == "valid"
    rows = _evidence()
    assert [(row["kind"], row["verdict"]) for row in rows] == [("validation_v0", "pass"), ("mesh_quality_v0", "pass"), ("fem_static_v0", "error")]


@requires_kernel
def test_analysis_spec_success_records_artifact_links_and_deterministic_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    _init()
    monkeypatch.setattr("app.modules.bluecad.loop.mesh_analysis_spec", lambda *_args, **_kwargs: _mesh_pass())
    monkeypatch.setattr("app.modules.bluecad.loop.solve_static_analysis", lambda *_args, **_kwargs: _fem())
    first = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube", loop_config=BluecadLoopConfig(analysis_spec=_analysis_spec())),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    rows = _evidence()[1:]
    assert [(row["kind"], row["verdict"]) for row in rows] == [("mesh_quality_v0", "pass"), ("fem_static_v0", "pass")]
    assert all(row["candidate_id"] == first.id and row["attempt_id"] == first.attempts[0].id for row in rows)
    assert all(row["source_run_id"] for row in rows)
    assert all(row["report_artifact_id"] for row in rows)
    run_payloads = _simulation_run_payloads()
    assert len(run_payloads) == 1
    assert run_payloads[0]["geometry"]["step_path"].endswith("model.step")
    assert run_payloads[0]["geometry"]["manifest_path"].endswith("manifest.json")
    fem_artifact = _artifact_json(rows[1]["report_artifact_id"])
    fem_report = fem_artifact["report"]
    assert "schema_version" in fem_report
    assert any(check["tier"] == 0 for check in fem_report["checks"])
    assert any(check["tier"] == 3 for check in fem_report["checks"])
    first_metrics = [(row["kind"], row["metrics_json"]) for row in rows]

    second = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube", loop_config=BluecadLoopConfig(analysis_spec=_analysis_spec())),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    second_rows = [row for row in _evidence() if row["candidate_id"] == second.id and row["kind"] != "validation_v0"]
    assert [(row["kind"], row["metrics_json"]) for row in second_rows] == first_metrics


@requires_kernel
def test_validation_fail_does_not_run_simulation(monkeypatch: pytest.MonkeyPatch) -> None:
    _init()
    mesh_calls = 0

    def mesh(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal mesh_calls
        mesh_calls += 1
        return _mesh_pass()

    monkeypatch.setattr("app.modules.bluecad.loop.mesh_analysis_spec", mesh)
    candidate = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="bad", loop_config=BluecadLoopConfig(max_attempts_per_tier=1, tier_ladder=["external:cheap"], analysis_spec=_analysis_spec())),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_bad_volume_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )
    assert candidate.status == "parked"
    assert mesh_calls == 0
    assert [row["kind"] for row in _evidence()] == ["validation_v0"]


def _require_registry_enabled_real_solver(tool_id: str) -> None:
    try:
        resolve_tool(tool_id)
    except ToolRegistryError as exc:
        pytest.skip(f"{tool_id} real-solver integration requires registry-enabled tool: {exc.code}")


@requires_kernel
@pytest.mark.bluecad_gmsh
@pytest.mark.bluecad_ccx
def test_real_solver_marker_documents_full_chain() -> None:
    _require_registry_enabled_real_solver("gmsh")
    _require_registry_enabled_real_solver("calculix")
    _init()

    candidate = create_bluecad_candidate(
        "bluerev",
        BluecadCandidateCreate(brief_text="single tube", loop_config=BluecadLoopConfig(analysis_spec=_analysis_spec("tube1"))),
        adapters={"scaleway": ScriptedFakeBluecadAdapter([_spec()])},
        bindings=_bindings(),
        force_external_allowed=True,
    )

    assert candidate.status == "valid"
    rows = _evidence()
    assert [row["kind"] for row in rows] == ["validation_v0", "mesh_quality_v0", "fem_static_v0"]
    assert all(row["candidate_id"] == candidate.id and row["attempt_id"] == candidate.attempts[0].id for row in rows)
    assert all(row["source_run_id"] for row in rows[1:])
    assert all(row["report_artifact_id"] for row in rows[1:])
