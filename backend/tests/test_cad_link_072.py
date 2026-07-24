from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-072")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_cad_link_072_preview_route_is_registered(client: TestClient) -> None:
    routes = {
        (route.path, method)
        for route in client.app.routes
        for method in getattr(route, "methods", set())
    }

    assert (
        "/workspaces/{workspace_id}/bluecad/cad-link/072/preview",
        "POST",
    ) in routes
    assert (
        "/workspaces/{workspace_id}/bluecad/cad-link/072/execute",
        "POST",
    ) not in routes


def test_cad_link_072_preview_missing_run_fails_before_layout_or_kernel(
    client: TestClient,
) -> None:
    response = client.post(
        "/workspaces/bluerev/bluecad/cad-link/072/preview",
        json={
            "source_simulation_run_id": "missing-run",
            "layout_spec": {},
            "analysis_spec": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "cad_link_run_not_found"
