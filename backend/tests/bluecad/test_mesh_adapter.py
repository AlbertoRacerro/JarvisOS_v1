from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.modules.bluecad.mesh_adapter import mesh_analysis_spec
from app.modules.bluecad.registry import ToolRegistryError, resolve_tool

FAKE_GMSH = Path(__file__).parent / "fixtures" / "fake_gmsh.py"


def _registry(tmp_path: Path, enabled: bool = True) -> Path:
    path = tmp_path / "tools.yaml"
    path.write_text(f"""registry_version: bluecad_tool_registry_v0_1
tools:
  - id: gmsh
    kind: mesher
    integration_mode: subprocess
    version_pin: "fake-1"
    license: {{spdx: GPL-2.0-or-later, boundary: C, verified_date: "2026-07-03"}}
    enabled: {str(enabled).lower()}
    entrypoint: {FAKE_GMSH}
    binary_sha256: {hashlib.sha256(FAKE_GMSH.read_bytes()).hexdigest()}
    provenance_url: file://fake
    capabilities: [step_import, tet_mesh, physical_groups, inp_export]
    health_check: null
""", encoding="utf-8")
    return path


def _analysis(tmp_path: Path) -> dict:
    step = tmp_path / "model.step"
    step.write_text("STEP", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"resolved_ports": {"run1": {"port_a": {"origin": [10, 20, 30], "outer_d": 8}}, "joint1": {"port_b": {"origin": [-1, 2, 3], "outer_d": 4}}}}), encoding="utf-8")
    return {"schema_version": "bluecad_analysis_spec_v0_1", "analysis_id": "a1", "analysis_type": "static", "geometry": {"step_path": str(step), "manifest_path": str(manifest)}, "material": {"name": "steel", "E": 200000, "nu": 0.3, "rho": 7.8e-9, "yield_strength": 250}, "bcs": [{"port_label": "run1.port_a", "kind": "fixed"}], "loads": [{"port_label": "joint1.port_b", "type": "force_total", "force": [1, 0, 0]}], "mesh": {"target_size": 5.0, "refinements": {"run1.port_a": 2.0}}, "pass_criteria": {"max_displacement": 1.0}}


def test_geo_physical_surfaces_and_real_style_inp_happy_path(tmp_path: Path) -> None:
    result = mesh_analysis_spec(_analysis(tmp_path), tmp_path / "mesh", registry_path=_registry(tmp_path))
    geo = (tmp_path / "mesh" / "mesh.geo").read_text(encoding="utf-8")
    assert geo.count("Physical Surface") == 2
    assert 'Physical Surface("BC_run1_port_a") = Surface In BoundingBox {4, 14, 24, 16, 26, 36};' in geo
    assert 'Physical Surface("LOAD_joint1_port_b") = Surface In BoundingBox {-4, -1, 0, 2, 5, 6};' in geo
    assert "Mesh.SaveGroupsOfElements = -1000;" in geo
    assert "Mesh.SaveGroupsOfNodes = -100;" in geo
    assert result["verdict"] == "pass"
    assert result["attempts"][0]["counts"]["physical_groups"] == {
        "BODY": 1,
        "BC_run1_port_a": 3,
        "LOAD_joint1_port_b": 3,
    }
    assert result["attempts"][0]["counts"]["elements_total"] == 1
    assert {"mesh_inp", "mesh_msh", "bluecad_geo", "gmsh_log"} <= set(result["artifacts"])


def test_empty_group_fails(tmp_path: Path) -> None:
    result = mesh_analysis_spec(_analysis(tmp_path), tmp_path / "emptycase", registry_path=_registry(tmp_path))
    assert result["verdict"] == "fail"
    assert result["errors"][0] == {"code": "MESH_GROUP_EMPTY", "detail": {"group": "BC_run1_port_a"}}


def test_mesh_fail_retries_once_with_half_target(tmp_path: Path) -> None:
    result = mesh_analysis_spec(_analysis(tmp_path), tmp_path / "failcase", registry_path=_registry(tmp_path))
    assert result["verdict"] == "fail"
    assert [attempt["target_size"] for attempt in result["attempts"]] == [5.0, 2.5]
    assert result["errors"][0]["code"] == "MESH_FAIL"


def test_injection_rejected_before_write(tmp_path: Path) -> None:
    spec = _analysis(tmp_path)
    spec["bcs"][0]["port_label"] = 'a"; Kill;'
    with pytest.raises(ValueError):
        mesh_analysis_spec(spec, tmp_path / "mesh", registry_path=_registry(tmp_path))
    assert not (tmp_path / "mesh" / "mesh.geo").exists()


def test_analysis_schema_full_static_example_round_trips(tmp_path: Path) -> None:
    schema = json.loads((Path(__file__).parents[3] / "schemas" / "bluecad_analysis_spec_v0_1.schema.json").read_text(encoding="utf-8"))
    spec = _analysis(tmp_path)
    assert spec["schema_version"] == schema["properties"]["schema_version"]["const"]
    assert spec["analysis_type"] in schema["properties"]["analysis_type"]["enum"]
    assert {"material", "bcs", "loads", "pass_criteria"} <= set(spec)


@pytest.mark.bluecad_gmsh
def test_real_gmsh_a3_disabled_registry_skip(tmp_path: Path) -> None:
    with pytest.raises(ToolRegistryError) as excinfo:
        resolve_tool("gmsh", _registry(tmp_path, enabled=False))
    if excinfo.value.code == "TOOL_DISABLED":
        pytest.skip("A3 closure requires maintainer-enabled real gmsh registry entry")
