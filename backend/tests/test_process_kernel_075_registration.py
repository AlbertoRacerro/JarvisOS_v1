from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.modules.runner.process_kernel_047 import BUNDLE_MANIFEST_FILENAME


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _register(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-process-kernel-047-v1/register"
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_registration_metadata_identifies_server_owned_authority(client: TestClient) -> None:
    implementation = _register(client)

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT mv.changelog, mv.notes AS model_notes, a.notes AS artifact_notes
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.id = ?
            """,
            (implementation["id"],),
        ).fetchone()

    assert row is not None
    assert "server-owned" in row["changelog"].lower()
    assert "server-owned" in row["model_notes"].lower()
    assert "server-owned" in row["artifact_notes"].lower()
    assert "caller-supplied" not in " ".join(str(value).lower() for value in row)


@pytest.mark.parametrize(
    "authority_field",
    [
        "source",
        "script_path",
        "import_roots",
        "environment",
        "profile_constants",
        "semantic_registry",
        "trusted",
    ],
)
def test_registration_rejects_authority_shaped_bodies(
    client: TestClient,
    authority_field: str,
) -> None:
    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-process-kernel-047-v1/register",
        json={authority_field: "caller-controlled"},
    )

    assert response.status_code == 422, response.text
    assert any(
        error["type"] == "extra_forbidden" and error["loc"][-1] == authority_field
        for error in response.json()["detail"]
    )


def test_missing_complete_bundle_is_not_silently_reinstalled(client: TestClient) -> None:
    implementation = _register(client)
    model_dir = Path(str(implementation["script_path"])).parent
    shutil.rmtree(model_dir / "process_kernel")
    (model_dir / BUNDLE_MANIFEST_FILENAME).unlink()

    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-process-kernel-047-v1/register"
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert not (model_dir / "process_kernel").exists()
    assert not (model_dir / BUNDLE_MANIFEST_FILENAME).exists()
