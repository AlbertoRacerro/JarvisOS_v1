from collections.abc import Iterator

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


def _baseline() -> dict[str, dict[str, object]]:
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {"value": 30.0, "unit": "mm"},
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": 0.25, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }


def _register(client: TestClient, *, semantic: bool) -> str:
    route = (
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-semantic-v0/register"
        if semantic
        else "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    response = client.post(route)
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def _create_parameter(client: TestClient) -> str:
    response = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": "Tube length source", "value": "20", "unit": "m"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _set_parameter_status(parameter_id: str, status: str) -> None:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET status = ? WHERE id = ?", (status, parameter_id))
        connection.commit()


def _run_counts() -> tuple[int, int]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        runs = int(connection.execute("SELECT COUNT(*) AS count FROM simulation_runs").fetchone()["count"])
        jobs = int(connection.execute("SELECT COUNT(*) AS count FROM runner_jobs").fetchone()["count"])
    return runs, jobs


def _payload(model_version_id: str, input_set: dict[str, object], request_key: str) -> dict[str, object]:
    return {
        "model_version_id": model_version_id,
        "run_label": "semantic-linked-create",
        "input_set": input_set,
        "request_key": request_key,
    }


def test_schema_v3_new_create_rejects_superseded_link_without_rows(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    input_set: dict[str, object] = _baseline()
    input_set["tube_length"] = {
        "value": 20.0,
        "unit": "m",
        "source_parameter_id": parameter_id,
    }
    _set_parameter_status(parameter_id, "superseded")
    before = _run_counts()

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json=_payload(model_version_id, input_set, "semantic-create-stale-0001"),
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == {
        "code": "runner_linked_parameter_unusable",
        "message": "A linked Parameter is no longer usable for this queued run.",
    }
    assert _run_counts() == before


def test_schema_v3_same_key_replay_survives_source_staleness(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    input_set: dict[str, object] = _baseline()
    input_set["tube_length"] = {
        "value": 20.0,
        "unit": "m",
        "source_parameter_id": parameter_id,
    }
    payload = _payload(model_version_id, input_set, "semantic-create-replay-0001")

    first = client.post("/workspaces/bluerev/runner-jobs", json=payload)
    assert first.status_code == 201, first.text
    _set_parameter_status(parameter_id, "superseded")

    replay = client.post("/workspaces/bluerev/runner-jobs", json=payload)

    assert replay.status_code == 201, replay.text
    assert replay.json()["runner_job"]["id"] == first.json()["runner_job"]["id"]
    assert replay.json()["simulation_run"]["id"] == first.json()["simulation_run"]["id"]
    assert _run_counts() == (1, 1)


def test_schema_v1_legacy_source_token_is_not_reinterpreted_as_parameter_fk(client: TestClient) -> None:
    model_version_id = _register(client, semantic=False)
    input_set: dict[str, object] = _baseline()
    input_set["tube_length"] = {
        "value": 20.0,
        "unit": "m",
        "source_parameter_id": "historical-provenance-token",
    }

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json=_payload(model_version_id, input_set, "legacy-source-token-0001"),
    )

    assert response.status_code == 201, response.text
    assert response.json()["runner_job"]["status"] == "queued"
    assert response.json()["simulation_run"]["status"] == "queued"
