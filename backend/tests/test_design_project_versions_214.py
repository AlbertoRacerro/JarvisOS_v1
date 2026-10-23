from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.core.database import initialize_database, open_sqlite_connection
from app.main import app
from app.modules.process_stack import draft
from app.modules.process_stack.draft_models import DraftOp


def test_design_versions_preserve_legacy_data_and_isolate_new_work() -> None:
    initialize_database()
    with TestClient(app) as client:
        created = client.post("/workspaces", json={"name": "Foundry", "slug": "foundry"})
        assert created.status_code == 201, created.text
        project_id = created.json()["id"]
        original = draft.create_draft(project_id, "Original C1")

        path = f"/workspaces/{project_id}/design-versions"
        first = client.get(path).json()
        assert first["active_version_id"] == project_id
        assert first["versions"][0]["data_workspace_id"] == project_id
        assert first["versions"][0]["starts_empty"] is False

        created_version = client.post(path, json={
            "label": "C1 refinement", "expected_active_version_id": project_id,
        })
        assert created_version.status_code == 201, created_version.text
        candidate = created_version.json()["versions"][1]
        assert candidate["parent_version_id"] == project_id
        assert candidate["starts_empty"] is True
        assert candidate["data_workspace_id"] != project_id
        assert all(row["id"] != candidate["data_workspace_id"] for row in client.get("/workspaces").json())
        other_project = client.post("/workspaces", json={"name": "Other", "slug": "other"}).json()["id"]
        foreign = client.post(f"/workspaces/{other_project}/design-versions/activate", json={
            "version_id": candidate["id"], "expected_active_version_id": other_project,
        })
        assert foreign.status_code == 404

        switched = client.post(f"{path}/activate", json={
            "version_id": candidate["id"], "expected_active_version_id": project_id,
        })
        assert switched.status_code == 200, switched.text
        assert switched.json()["active_version_id"] == candidate["id"]
        assert draft.list_drafts(candidate["data_workspace_id"]) == []
        new_draft = draft.create_draft(candidate["data_workspace_id"], "New context")
        assert [row["draft_id"] for row in draft.list_drafts(project_id)] == [original["draft_id"]]
        assert [row["draft_id"] for row in draft.list_drafts(candidate["data_workspace_id"])] == [new_draft["draft_id"]]

        stale = client.post(f"{path}/activate", json={
            "version_id": project_id, "expected_active_version_id": project_id,
        })
        assert stale.status_code == 409
        stale_create = client.post(path, json={
            "label": "Stale child", "expected_active_version_id": project_id,
        })
        assert stale_create.status_code == 409
        restored = client.post(f"{path}/activate", json={
            "version_id": project_id, "expected_active_version_id": candidate["id"],
        })
        assert restored.status_code == 200
        assert restored.json()["active_version_id"] == project_id


def test_existing_workspace_is_backfilled_without_changing_its_identity() -> None:
    initialize_database()
    with open_sqlite_connection() as connection:
        connection.execute("""
            INSERT INTO workspaces (id, name, slug, status, created_at, updated_at)
            VALUES ('legacy', 'Legacy', 'legacy', 'active', '2025-01-01', '2025-01-01')
        """)
        connection.commit()
    original = draft.create_draft("legacy", "Preserved")

    initialize_database()
    with TestClient(app) as client:
        versions = client.get("/workspaces/legacy/design-versions")
        assert versions.status_code == 200
        assert versions.json()["active_version_id"] == "legacy"
        assert versions.json()["versions"][0]["data_workspace_id"] == "legacy"
        assert draft.list_drafts("legacy")[0]["draft_id"] == original["draft_id"]


def test_component_tree_scopes_identity_and_rejects_cycles_and_stale_edits() -> None:
    initialize_database()
    with TestClient(app) as client:
        project_id = client.post("/workspaces", json={"name": "Tree", "slug": "tree"}).json()["id"]
        base = f"/workspaces/{project_id}/design-versions/{project_id}/components"
        root = client.post(base, json={
            "name": "Plant unit", "expected_active_version_id": project_id,
        })
        assert root.status_code == 201, root.text
        root_id = root.json()["id"]
        parent_id = root_id
        for depth in range(4):
            child = client.post(base, json={
                "name": f"Assembly {depth}", "parent_id": parent_id,
                "expected_active_version_id": project_id,
            })
            assert child.status_code == 201, child.text
            parent_id = child.json()["id"]
        assert len(client.get(base).json()) == 5

        cycle = client.put(f"{base}/{root_id}", json={
            "name": "Plant unit", "parent_id": parent_id, "expected_revision": 1,
            "expected_active_version_id": project_id,
        })
        assert cycle.status_code == 409
        rename = client.put(f"{base}/{root_id}", json={
            "name": "Renamed unit", "parent_id": None, "expected_revision": 1,
            "expected_active_version_id": project_id,
        })
        assert rename.status_code == 200, rename.text
        assert rename.json()["revision"] == 2
        assert client.put(f"{base}/{root_id}", json={
            "name": "Stale", "expected_revision": 1,
            "expected_active_version_id": project_id,
        }).status_code == 409

        versions_path = f"/workspaces/{project_id}/design-versions"
        new_version = client.post(versions_path, json={
            "label": "New", "expected_active_version_id": project_id,
        }).json()["versions"][1]["id"]
        assert client.get(f"{versions_path}/{new_version}/components").json() == []
        assert client.post(f"{versions_path}/{new_version}/components", json={
            "name": "Cross-version child", "parent_id": root_id,
            "expected_active_version_id": project_id,
        }).status_code == 409
        client.post(f"{versions_path}/activate", json={
            "version_id": new_version, "expected_active_version_id": project_id,
        })
        new_base = f"{versions_path}/{new_version}/components"
        assert client.post(new_base, json={
            "name": "Cross-version child", "parent_id": root_id,
            "expected_active_version_id": new_version,
        }).status_code == 404
        assert client.post(base, json={
            "name": "Stale version", "expected_active_version_id": project_id,
        }).status_code == 409


def test_process_unit_opens_one_version_scoped_component() -> None:
    initialize_database()
    with TestClient(app) as client:
        project_id = client.post("/workspaces", json={"name": "Unit entry", "slug": "unit-entry"}).json()["id"]
        process = draft.create_draft(project_id, "Plant")
        changed = draft.patch(project_id, process["draft_id"], process["revision"], [
            TypeAdapter(DraftOp).validate_python({"op": "add_unit", "id": "pump", "type": "Pump", "tag": "P1", "x": 0, "y": 0})
        ])
        base = f"/workspaces/{project_id}/design-versions/{project_id}/components"
        payload = {"draft_id": process["draft_id"], "unit_id": "pump",
                   "expected_draft_revision": changed["revision"], "expected_active_version_id": project_id}
        first = client.post(f"{base}/from-unit", json=payload)
        assert first.status_code == 200, first.text
        assert first.json()["source_draft_id"] == process["draft_id"]
        assert first.json()["source_unit_id"] == "pump"
        again = client.post(f"{base}/from-unit", json=payload)
        assert again.status_code == 200 and again.json()["id"] == first.json()["id"]
        assert len(client.get(base).json()) == 1
        assert client.post(f"{base}/from-unit", json={**payload, "unit_id": "missing"}).status_code == 404
        assert client.post(f"{base}/from-unit", json={**payload, "expected_draft_revision": "stale"}).status_code == 409

        with open_sqlite_connection() as connection:
            connection.execute(
                "INSERT INTO bluecad_candidates (id, workspace_id, brief_text, brief_digest, status, "
                "origin, loop_config_json, created_at, updated_at) VALUES "
                "('pump-cad', ?, 'pump', 'digest', 'valid', 'template', '{}', '2026-01-01', '2026-01-01')",
                (project_id,),
            )
            connection.commit()
        geometry_path = f"{base}/{first.json()['id']}/geometry"
        geometry_payload = {"candidate_id": "pump-cad", "expected_revision": 1,
                            "expected_active_version_id": project_id}
        assert client.put(geometry_path, json=geometry_payload).status_code == 422
        assert client.put(geometry_path, json={
            **geometry_payload, "expected_draft_revision": "stale",
        }).status_code == 409
        attached = client.put(geometry_path, json={
            **geometry_payload, "expected_draft_revision": changed["revision"],
        })
        assert attached.status_code == 200, attached.text
        assert attached.json()["geometry_source_draft_revision"] == changed["revision"]

        version = client.post(f"/workspaces/{project_id}/design-versions", json={
            "label": "Next", "expected_active_version_id": project_id,
        }).json()["versions"][1]
        client.post(f"/workspaces/{project_id}/design-versions/activate", json={
            "version_id": version["id"], "expected_active_version_id": project_id,
        })
        next_base = f"/workspaces/{project_id}/design-versions/{version['id']}/components"
        assert client.post(f"{next_base}/from-unit", json={
            **payload, "expected_active_version_id": version["id"],
        }).status_code == 404


def test_geometry_attachment_checks_version_candidate_and_component_revision() -> None:
    initialize_database()
    with TestClient(app) as client:
        project_id = client.post("/workspaces", json={"name": "Geometry", "slug": "geometry"}).json()["id"]
        base = f"/workspaces/{project_id}/design-versions/{project_id}/components"
        component = client.post(base, json={
            "name": "Tube", "expected_active_version_id": project_id,
        }).json()
        next_version = client.post(f"/workspaces/{project_id}/design-versions", json={
            "label": "Next", "expected_active_version_id": project_id,
        }).json()["versions"][1]
        with open_sqlite_connection() as connection:
            for candidate_id, workspace_id, status in (
                ("valid-local", project_id, "valid"),
                ("pending-local", project_id, "generating"),
                ("valid-other", next_version["data_workspace_id"], "valid"),
            ):
                connection.execute(
                    "INSERT INTO bluecad_candidates (id, workspace_id, brief_text, brief_digest, status, "
                    "origin, loop_config_json, created_at, updated_at) VALUES (?, ?, 'tube', 'digest', ?, "
                    "'template', '{}', '2026-01-01', '2026-01-01')",
                    (candidate_id, workspace_id, status),
                )
            connection.commit()
        path = f"{base}/{component['id']}/geometry"
        payload = {"candidate_id": "valid-local", "expected_revision": 1,
                   "expected_active_version_id": project_id}
        assert client.put(path, json={**payload, "candidate_id": "valid-other"}).status_code == 404
        assert client.put(path, json={**payload, "candidate_id": "pending-local"}).status_code == 409
        attached = client.put(path, json=payload)
        assert attached.status_code == 200, attached.text
        assert attached.json()["geometry_candidate_id"] == "valid-local"
        assert attached.json()["revision"] == 2
        assert client.get(base).json()[0]["geometry_candidate_id"] == "valid-local"
        assert client.put(path, json=payload).status_code == 409
        client.post(f"/workspaces/{project_id}/design-versions/activate", json={
            "version_id": next_version["id"], "expected_active_version_id": project_id,
        })
        assert client.put(path, json={**payload, "expected_revision": 2}).status_code == 409
