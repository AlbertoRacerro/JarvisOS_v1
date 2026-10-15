"""Pinned Studio generation references remain visual and fail closed on changed artifacts."""

import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.modules.bluecad.studio_references import (
    ReferenceCreate,
    ReferenceError,
    ReferenceMove,
    add_reference,
    list_references,
    move_reference,
)
from app.modules.runner.safety import model_implementation_root, run_root


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _seed(workspace: str = "bluerev") -> tuple[str, str, dict[str, Path]]:
    initialize_storage(seed_default=True)
    candidate_id, model_id, version_id, run_id, source_id = [str(uuid4()) for _ in range(5)]
    contract = {"category": "geometry", "inputs": [{"name": "radius", "unit": "mm"}]}
    contract_json = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    source = b"def main(inputs): return None\n"
    source_path = model_implementation_root(workspace) / version_id / "studio_geometry.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(source)
    paths = {}
    now = "2026-10-15T00:00:00Z"
    with open_sqlite_connection() as connection:
        connection.execute("""INSERT INTO bluecad_candidates
            (id,workspace_id,brief_text,brief_digest,status,origin,loop_config_json,created_at,updated_at)
            VALUES (?,?, 'Test typed assembly', 'digest', 'valid', 'template', '{}', ?, ?)""",
            (candidate_id, workspace, now, now))
        connection.execute("""INSERT INTO model_specs
            (id,workspace_id,title,engineering_question,created_at,updated_at)
            VALUES (?,?,'Baffle','How does it fit?',?,?)""", (model_id, workspace, now, now))
        connection.execute("""INSERT INTO artifacts
            (id,workspace_id,filename,stored_path,artifact_type,sha256,created_at)
            VALUES (?,?,?,?,?,?,?)""", (source_id, workspace, source_path.name, str(source_path),
                                        "studio_source", _sha(source), now))
        connection.execute("""INSERT INTO model_versions
            (id,workspace_id,model_spec_id,version_label,implementation_artifact_id,implementation_kind,status,created_at)
            VALUES (?,?,?,?,?,'studio_geometry_v1','published',?)""",
            (version_id, workspace, model_id, "v1", source_id, now))
        connection.execute("""INSERT INTO studio_published_versions
            (version_id,model_spec_id,contract_json,source_sha256,contract_sha256,created_at)
            VALUES (?,?,?,?,?,?)""", (version_id, model_id, contract_json, _sha(source),
                                       _sha(contract_json.encode()), now))
        connection.execute("""INSERT INTO simulation_runs
            (id,workspace_id,model_version_id,status,input_payload,created_at)
            VALUES (?,?,?,'succeeded',?,?)""", (run_id, workspace, version_id,
                                                '{"radius":{"value":18,"unit":"mm"}}', now))
        for name in ("model.glb", "model.step", "model.stl"):
            path = run_root(workspace, run_id) / "geometry" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            paths[name] = path
            artifact_id = str(uuid4())
            connection.execute("""INSERT INTO artifacts
                (id,workspace_id,filename,stored_path,artifact_type,sha256,source_ref,created_at)
                VALUES (?,?,?,?,'studio_geometry',?,?,?)""",
                (artifact_id, workspace, name, str(path), _sha(path.read_bytes()), f"simulation_run:{run_id}", now))
            connection.execute("""INSERT INTO run_artifacts
                (id,workspace_id,simulation_run_id,artifact_id,role,created_at)
                VALUES (?,?,?,?,'studio_geometry',?)""", (str(uuid4()), workspace, run_id, artifact_id, now))
        connection.commit()
    return candidate_id, run_id, paths


def test_pinned_geometry_reference_and_integrity(tmp_path: Path) -> None:
    candidate_id, run_id, paths = _seed()
    created = add_reference("bluerev", candidate_id, ReferenceCreate(simulation_run_id=run_id))
    assert created["valid"] and created["glb_url"].endswith(f"/{run_id}/model.glb")
    assert created["inputs"] == {"radius": {"value": 18, "unit": "mm"}}
    assert created["translation_mm"] == [0, 0, 0]
    with pytest.raises(ReferenceError, match="already referenced"):
        add_reference("bluerev", candidate_id, ReferenceCreate(simulation_run_id=run_id))
    with pytest.raises(ReferenceError):
        add_reference("foreign-workspace", candidate_id, ReferenceCreate(simulation_run_id=run_id))
    moved = move_reference("bluerev", candidate_id, created["id"], ReferenceMove(
        expected_revision=1, translation_mm=(5, -2, 10), rotation_deg=(0, 0, 45)))
    assert moved["translation_mm"] == [5, -2, 10] and moved["revision"] == 2
    with pytest.raises(ReferenceError, match="refresh"):
        move_reference("bluerev", candidate_id, created["id"], ReferenceMove(expected_revision=1))
    paths["model.glb"].write_bytes(b"tampered")
    found = list_references("bluerev", candidate_id)[0]
    assert not found["valid"] and found["glb_url"] is None and "changed" in found["finding"]
    with pytest.raises(ReferenceError, match="Invalid reference"):
        move_reference("bluerev", candidate_id, created["id"], ReferenceMove(expected_revision=2))


def test_reference_endpoint_rejects_foreign_and_tampered_generation() -> None:
    candidate_id, run_id, paths = _seed()
    from app.main import create_app

    with TestClient(create_app()) as client:
        base = f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/studio-references"
        assert client.post(base, json={"simulation_run_id": run_id, "translation_mm": [1, 2, 3]}).status_code == 201
        assert client.post(base, json={"simulation_run_id": run_id, "translation_mm": [1, 2]}).status_code == 422
        paths["model.step"].write_bytes(b"changed")
        reference = client.get(base).json()[0]
        assert reference["valid"] is False and reference["glb_url"] is None
