from collections.abc import Iterator
import json

import pytest
from fastapi.testclient import TestClient


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


def _event_count(event_type: str) -> int:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import count_events_by_type

    with open_sqlite_connection() as connection:
        return count_events_by_type(connection, event_type)


def _latest_event_payload(event_type: str) -> dict[str, object]:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import list_events_by_type

    with open_sqlite_connection() as connection:
        events = list_events_by_type(connection, event_type)

    assert events
    return json.loads(events[-1]["payload"])


def test_database_initialization_and_default_workspace(client: TestClient) -> None:
    info = client.get("/system/info").json()

    assert info["database"]["initialized"] is True
    assert info["database"]["ready"] is True

    response = client.get("/workspaces")

    assert response.status_code == 200
    workspaces = response.json()
    assert any(workspace["id"] == "bluerev" for workspace in workspaces)

    init_again = client.post("/system/initialize")
    assert init_again.status_code == 200

    workspaces_after_second_init = client.get("/workspaces").json()
    assert [workspace["id"] for workspace in workspaces_after_second_init].count("bluerev") == 1
    assert _event_count("WorkspaceCreated") == 1


def test_create_and_list_workspaces(client: TestClient) -> None:
    response = client.post(
        "/workspaces",
        json={
            "name": "Test Workspace",
            "slug": "test-workspace",
            "description": "Created by tests.",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["slug"] == "test-workspace"

    list_response = client.get("/workspaces")
    assert any(workspace["id"] == created["id"] for workspace in list_response.json())
    get_response = client.get(f"/workspaces/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]
    assert _event_count("WorkspaceCreated") >= 2


def test_create_and_list_model_specs(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/model-specs",
        json={
            "title": "Floating PBR Buoyancy Estimate",
            "engineering_question": "How much buoyancy margin is required?",
            "scope": "Early sizing",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["schema_version"] == 1

    list_response = client.get("/workspaces/bluerev/model-specs")
    assert any(item["id"] == created["id"] for item in list_response.json())
    get_response = client.get(f"/model-specs/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]
    assert _event_count("ModelSpecCreated") == 1
    assert _latest_event_payload("ModelSpecCreated")["title"] == "Floating PBR Buoyancy Estimate"


def test_create_and_list_assumptions(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/assumptions",
        json={"statement": "Water density is approximately 1025 kg/m3.", "confidence": 0.7},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["statement"].startswith("Water density")

    list_response = client.get("/workspaces/bluerev/assumptions")
    assert any(item["id"] == created["id"] for item in list_response.json())
    assert _event_count("AssumptionCreated") == 1
    assert "Water density" in str(_latest_event_payload("AssumptionCreated")["statement"])


def test_create_and_list_parameters(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": "Seawater density", "symbol": "rho", "value": "1025", "unit": "kg/m3"},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["symbol"] == "rho"

    list_response = client.get("/workspaces/bluerev/parameters")
    assert any(item["id"] == created["id"] for item in list_response.json())
    assert _event_count("ParameterCreated") == 1
    assert _latest_event_payload("ParameterCreated")["symbol"] == "rho"


def test_create_and_list_simulation_runs(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/simulation-runs",
        json={"run_label": "scratch-001", "status": "planned", "input_payload": "{}"},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["run_label"] == "scratch-001"

    list_response = client.get("/workspaces/bluerev/simulation-runs")
    assert any(item["id"] == created["id"] for item in list_response.json())
    assert _event_count("SimulationRunCreated") == 1
    assert _latest_event_payload("SimulationRunCreated")["run_label"] == "scratch-001"


def test_create_and_list_decisions(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/decisions",
        json={
            "title": "Use SQLite for early local persistence",
            "decision_text": "Keep the first database local and simple.",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["title"].startswith("Use SQLite")

    list_response = client.get("/workspaces/bluerev/decisions")
    assert any(item["id"] == created["id"] for item in list_response.json())
    assert _event_count("DecisionCreated") == 1
    assert _latest_event_payload("DecisionCreated")["title"] == "Use SQLite for early local persistence"
