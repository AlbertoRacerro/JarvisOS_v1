"""Spec 163: provider-free template candidates and STL/STEP print-handoff exports."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths

TUBE = {"template": "tube", "params": {"outer_d_mm": 40.0, "wall_t_mm": 3.0, "length_mm": 120.0}}
MANIFOLD = {
    "template": "manifold",
    "params": {
        "outer_d_mm": 50.0,
        "wall_t_mm": 3.0,
        "length_mm": 240.0,
        "branch_count": 3,
        "branch_outer_d_mm": 20.0,
    },
}


@pytest.fixture
def client(isolated_data_root) -> TestClient:
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client


def _workspace_id(client: TestClient) -> str:
    return client.get("/workspaces").json()[0]["id"]


def _count(table: str) -> int:
    with open_sqlite_connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])


@pytest.mark.parametrize("payload", [TUBE, MANIFOLD], ids=["tube", "manifold"])
def test_template_candidate_is_valid_with_glb_stl_step_and_no_ai(client: TestClient, payload: dict) -> None:
    workspace_id = _workspace_id(client)
    ai_jobs_before = _count("ai_jobs")

    response = client.post(f"/workspaces/{workspace_id}/bluecad/candidates/from-template", json=payload)

    assert response.status_code == 201, response.text
    candidate = response.json()
    assert candidate["status"] == "valid"
    assert candidate["origin"] == "template"
    assert candidate["glb_artifact_id"] and candidate["report_artifact_id"] and candidate["spec_artifact_id"]
    [attempt] = candidate["attempts"]
    assert attempt["route_class"] == f"deterministic:template:{payload['template']}"
    assert attempt["proposal_ai_job_id"] is None
    assert attempt["proposal_outcome"] == "not_applicable"
    assert attempt["validation_verdict"] == "pass"
    assert _count("ai_jobs") == ai_jobs_before

    aggregate = client.get(f"/workspaces/{workspace_id}/bluecad/candidates/{candidate['id']}/aggregate").json()
    exports = {item["roles"][0]: item for item in aggregate["exports"]}
    assert set(exports) == {"export.stl", "export.step"}
    assert not aggregate["diagnostics"]

    glb = client.get(f"/workspaces/{workspace_id}/bluecad/artifacts/{candidate['glb_artifact_id']}/content")
    assert glb.status_code == 200
    assert glb.headers["content-type"].startswith("model/gltf-binary")
    assert glb.content[:4] == b"glTF"

    short = candidate["id"][:8]
    stl = client.get(exports["export.stl"]["content_url"])
    assert stl.status_code == 200
    assert stl.headers["content-type"].startswith("model/stl")
    assert f'filename="bluecad-{short}-attempt1.stl"' in stl.headers["content-disposition"]
    assert len(stl.content) > 84

    step = client.get(exports["export.step"]["content_url"])
    assert step.status_code == 200
    assert step.headers["content-type"].startswith("model/step")
    assert f'filename="bluecad-{short}-attempt1.step"' in step.headers["content-disposition"]
    assert step.content.startswith(b"ISO-10303-21;")


@pytest.mark.parametrize(
    "payload",
    [
        {"template": "tube", "params": {"outer_d_mm": 10.0, "wall_t_mm": 5.0, "length_mm": 50.0}},
        {"template": "tube", "params": {"outer_d_mm": 10.0, "wall_t_mm": 1.0, "length_mm": 50000.0}},
        {"template": "tube", "params": {"outer_d_mm": 0.0, "wall_t_mm": 1.0, "length_mm": 50.0}},
        {"template": "tube", "params": {"outer_d_mm": 10.0, "wall_t_mm": 1.0}},
        {"template": "tube", "params": {"outer_d_mm": 10.0, "wall_t_mm": 1.0, "length_mm": 50.0, "kind": "bend"}},
        {"template": "tube", "params": {"outer_d_mm": "10", "wall_t_mm": 1.0, "length_mm": 50.0}, "extra": 1},
        {"template": "sphere", "params": {}},
        {**MANIFOLD, "params": {**MANIFOLD["params"], "branch_outer_d_mm": 60.0}},
        {**MANIFOLD, "params": {**MANIFOLD["params"], "branch_count": 20}},
        {**MANIFOLD, "params": {**MANIFOLD["params"], "branch_count": True}},
        {**MANIFOLD, "params": {**MANIFOLD["params"], "length_mm": 60.0}},
    ],
)
def test_invalid_template_parameters_are_refused_before_any_write(client: TestClient, payload: dict) -> None:
    workspace_id = _workspace_id(client)
    before = (_count("bluecad_candidates"), _count("artifacts"))

    response = client.post(f"/workspaces/{workspace_id}/bluecad/candidates/from-template", json=payload)

    assert response.status_code == 422, response.text
    assert (_count("bluecad_candidates"), _count("artifacts")) == before


def test_template_for_unknown_workspace_is_404(client: TestClient) -> None:
    response = client.post("/workspaces/does-not-exist/bluecad/candidates/from-template", json=TUBE)
    assert response.status_code == 404
    assert _count("bluecad_candidates") == 0


def test_export_serving_boundary_is_unchanged(client: TestClient, tmp_path: Path) -> None:
    workspace_id = _workspace_id(client)

    def insert(artifact_type: str, stored_path: Path) -> str:
        stored_path.parent.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(b"solid x\nendsolid x\n")
        artifact_id = str(uuid.uuid4())
        with open_sqlite_connection() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (id, workspace_id, filename, stored_path, artifact_type, mime_type,
                    sha256, source_ref, status, created_at, notes)
                VALUES (?, ?, ?, ?, ?, 'application/octet-stream', NULL, 'test', 'registered', ?, 'fixture')
                """,
                (artifact_id, workspace_id, stored_path.name, str(stored_path), artifact_type, "2026-10-01T00:00:00Z"),
            )
            connection.commit()
        return artifact_id

    outside = insert("bluecad_stl", tmp_path / "outside" / "model.stl")
    foreign = insert("runner_output", build_paths().data_root / "artifacts" / "runner" / "model.stl")
    inside = insert("bluecad_stl", build_paths().data_root / "artifacts" / "bluecad" / "model.stl")

    assert client.get(f"/workspaces/{workspace_id}/bluecad/artifacts/{outside}/content").status_code == 404
    assert client.get(f"/workspaces/{workspace_id}/bluecad/artifacts/{foreign}/content").status_code == 404
    assert client.get(f"/workspaces/other/bluecad/artifacts/{inside}/content").status_code == 404
    served = client.get(f"/workspaces/{workspace_id}/bluecad/artifacts/{inside}/content")
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("model/stl")
    # Without a candidate source_ref the stored filename is kept.
    assert 'filename="model.stl"' in served.headers["content-disposition"]


def test_generation_availability_reports_safe_default_block_without_ai(client: TestClient) -> None:
    workspace_id = _workspace_id(client)
    ai_jobs_before = _count("ai_jobs")

    response = client.get(f"/workspaces/{workspace_id}/bluecad/generation-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["route_class"] == "external:cheap"
    assert body["external_calls_allowed"] is False
    assert body["blocking_reason"]
    assert _count("ai_jobs") == ai_jobs_before


def test_loop_build_registers_stl_and_step_exports(client: TestClient) -> None:
    from app.modules.bluecad.loop import _build_and_register
    from app.modules.bluecad.template import TubeTemplateCreate, template_geometry_spec

    workspace_id = _workspace_id(client)
    candidate_id = str(uuid.uuid4())
    spec = template_geometry_spec(TubeTemplateCreate.model_validate(TUBE))

    _build_and_register(workspace_id, candidate_id, 1, spec)

    with open_sqlite_connection() as connection:
        roles = {
            row["artifact_type"]
            for row in connection.execute(
                "SELECT artifact_type FROM artifacts WHERE source_ref = ?",
                (f"bluecad_candidate:{candidate_id}:attempt:1",),
            )
        }
    assert {"bluecad_glb", "bluecad_stl", "bluecad_step"} <= roles
