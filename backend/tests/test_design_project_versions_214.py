from fastapi.testclient import TestClient

from app.core.database import initialize_database, open_sqlite_connection
from app.main import app
from app.modules.process_stack import draft


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
