from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-archive-fence")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _seed_candidate(status: str) -> str:
    candidate_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'archive fence probe', ?, ?,
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'archive fence probe')
            """,
            (candidate_id, "sha256:" + "a" * 64, status, now, now),
        )
        connection.commit()
    return candidate_id


@pytest.mark.parametrize("status", ["generating", "validating"])
def test_active_cad_link_reservations_cannot_be_archived(
    client: TestClient,
    status: str,
) -> None:
    candidate_id = _seed_candidate(status)

    response = client.post(
        f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/archive"
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == (
        "Active BLUECAD candidates may not be archived."
    )
    with open_sqlite_connection() as connection:
        persisted = connection.execute(
            "SELECT status FROM bluecad_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
    assert persisted is not None
    assert persisted["status"] == status


def test_terminal_candidate_can_still_be_archived(client: TestClient) -> None:
    candidate_id = _seed_candidate("valid")

    response = client.post(
        f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/archive"
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "archived"
