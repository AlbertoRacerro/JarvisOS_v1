from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.modules.bluecad.fem_adapter import append_tier3_checks, solve_static_analysis
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool

FAKE_CCX = Path(__file__).parent / "fixtures" / "fake_ccx.py"


def _registry(tmp_path: Path, enabled: bool = True) -> Path:
    path = tmp_path / "tools.yaml"
    path.write_text(f"""registry_version: bluecad_tool_registry_v0_1
tools:
  - id: calculix
    kind: fem_solver
    integration_mode: subprocess
    version_pin: "fake-ccx-1"
    license: {{spdx: GPL-2.0, boundary: C, verified_date: "2026-07-05"}}
    enabled: {str(enabled).lower()}
    entrypoint: {FAKE_CCX}
    binary_sha256: {hashlib.sha256(FAKE_CCX.read_bytes()).hexdigest()}
    provenance_url: file://fake
    capabilities: [static]
    health_check: null
""", encoding="utf-8")
    return path


def _mesh(tmp_path: Path) -> dict:
    mesh = tmp_path / "mesh.inp"
    mesh.write_text("""*NODE
1,0,0,0
2,1,0,0
3,0,1,0
4,0,0,1
*ELEMENT, TYPE=C3D4, ELSET=BODY
1,1,2,3,4
*ELEMENT, TYPE=S3, ELSET=BC_run1_port_a
2,1,2,3
*ELEMENT, TYPE=S3, ELSET=LOAD_joint1_port_b
3,2,3,4
""", encoding="utf-8")
    return {"artifacts": {"mesh_inp": {"path": str(mesh)}}}


def _spec() -> dict:
    return {"schema_version": "bluecad_analysis_spec_v0_1", "analysis_id": "a1", "analysis_type": "static", "geometry": {"step_path": "model.step", "manifest_path": "manifest.json"}, "material": {"name": "steel", "E": 200000.0, "nu": 0.3, "rho": 7.8e-9, "yield_strength": 250.0}, "bcs": [{"port_label": "run1.port_a", "kind": "fixed"}], "loads": [{"port_label": "joint1.port_b", "type": "force_total", "force": [30.0, 0.0, 0.0]}], "mesh": {"target_size": 5.0}, "pass_criteria": [{"metric": "max_von_mises", "op": "<=", "value": 300.0}]}


def test_happy_path_result_summary_and_native_frd_parser(tmp_path: Path) -> None:
    result = solve_static_analysis(_spec(), _mesh(tmp_path), tmp_path / "solve", registry_path=_registry(tmp_path))
    assert result["verdict"] == "pass"
    assert result["max_displacement"] == {"node_id": 2, "value": 5.0}
    assert result["max_von_mises"] == {"element_id": 1, "node_id": 2, "value": 275.0}
    assert result["reactions"] == [{"node_id": 1, "force": [-10.0, 0.0, 0.0]}]
    assert {"inp", "frd", "dat", "log"} <= set(result["artifacts"])
    deck = (tmp_path / "solve" / "analysis.inp").read_text(encoding="utf-8")
    assert "*INCLUDE, INPUT=../mesh.inp" in deck
    assert str(tmp_path.resolve()) not in deck
    assert "*MATERIAL, NAME=steel" in deck
    assert "*SOLID SECTION, ELSET=BODY, MATERIAL=steel" in deck
    assert "BC_run1_port_a, 1, 3, 0" in deck
    assert "2, 1, 10" in deck and "3, 1, 10" in deck and "4, 1, 10" in deck
    assert "LOAD_joint1_port_b" not in deck.split("*STEP", 1)[0]


def test_tier3_pass_fail_and_unknown_metric(tmp_path: Path) -> None:
    result = solve_static_analysis(_spec(), _mesh(tmp_path), tmp_path / "solve", registry_path=_registry(tmp_path))
    report = {"report_version": "bluecad_validation_report_v0_1", "spec_id": "sha256:" + "0" * 64, "manifest_sha256": None, "verdict": "pass", "checks": [], "errors": []}
    passed = append_tier3_checks(report, result, [{"metric": "max_von_mises", "op": "<=", "value": 300.0}])
    failed = append_tier3_checks(report, result, [{"metric": "max_von_mises", "op": "<=", "value": 200.0}])
    unknown = append_tier3_checks(report, result, [{"metric": "bogus", "op": "<=", "value": 1.0}])
    assert passed["checks"][0]["status"] == "pass"
    assert failed["checks"][0]["status"] == "fail" and failed["verdict"] == "fail"
    assert unknown["errors"] == [{"code": "UNKNOWN_METRIC", "detail": {"metric": "bogus"}}]


@pytest.mark.parametrize(("dirname", "code", "timeout"), [("solve_error", "SOLVE_ERROR", 2), ("diverged", "SOLVE_DIVERGED", 2), ("parse_error", "PARSE_ERROR", 2), ("timeout", "TIMEOUT", 0.1)])
def test_error_taxonomy(tmp_path: Path, dirname: str, code: str, timeout: float) -> None:
    result = solve_static_analysis(_spec(), _mesh(tmp_path), tmp_path / dirname, registry_path=_registry(tmp_path), timeout_s=timeout)
    assert result["verdict"] == "error"
    assert result["errors"][0]["code"] == code
    assert "log" in result["artifacts"]


@pytest.mark.bluecad_ccx
def test_real_ccx_a4_disabled_registry_skip(tmp_path: Path) -> None:
    with pytest.raises(ToolRegistryError) as excinfo:
        resolve_tool("calculix", _registry(tmp_path, enabled=False))
    if excinfo.value.code == "TOOL_DISABLED":
        pytest.skip("A4 closure requires maintainer-enabled real CalculiX registry entry")
