import json
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

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


def _create_parameter(client: TestClient, *, name: str = "Tube length source", value: str = "20", unit: str = "m") -> str:
    response = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": name, "value": value, "unit": unit},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _set_parameter_status(parameter_id: str, status: str) -> None:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET status = ? WHERE id = ?", (status, parameter_id))
        connection.commit()


def _mark_parameter_stale(client: TestClient, parameter_id: str) -> None:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import utc_now

    trigger_id = _create_parameter(client, name="Freshness trigger", value="1", unit="1")
    replacement_id = _create_parameter(client, name="Freshness replacement", value="2", unit="1")
    invalidation_id = str(uuid4())
    mark_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO freshness_invalidations (
                id, workspace_id, superseded_parameter_id, replacement_parameter_id,
                source_graph_digest, affected_count, unresolved_diagnostic_count,
                cycle_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invalidation_id,
                "bluerev",
                trigger_id,
                replacement_id,
                "test-source-graph",
                1,
                0,
                0,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO freshness_marks (
                id, workspace_id, invalidation_id, record_ref, record_kind,
                record_id, reason_code, path_json, path_digest, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mark_id,
                "bluerev",
                invalidation_id,
                f"parameter:{parameter_id}",
                "parameter",
                parameter_id,
                "upstream_parameter_superseded",
                "[]",
                "test-path-digest",
                now,
            ),
        )
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


def _linked_input(parameter_id: str) -> dict[str, object]:
    input_set: dict[str, object] = _baseline()
    input_set["tube_length"] = {
        "value": 20.0,
        "unit": "m",
        "source_parameter_id": parameter_id,
    }
    return input_set


def _preview(client: TestClient, model_version_id: str, bindings: dict[str, object]):
    return client.post(
        f"/workspaces/bluerev/model-implementations/{model_version_id}/binding-preview",
        json={"bindings": bindings},
    )


def _runner_event_types(runner_job_id: str) -> list[str]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT event_type FROM events WHERE target_id = ? ORDER BY created_at ASC",
            (runner_job_id,),
        ).fetchall()
    return [str(row["event_type"]) for row in rows]


def test_schema_v3_new_create_rejects_superseded_link_without_rows(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    input_set = _linked_input(parameter_id)
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
    input_set = _linked_input(parameter_id)
    payload = _payload(model_version_id, input_set, "semantic-create-replay-0001")

    first = client.post("/workspaces/bluerev/runner-jobs", json=payload)
    assert first.status_code == 201, first.text
    _set_parameter_status(parameter_id, "superseded")

    replay = client.post("/workspaces/bluerev/runner-jobs", json=payload)

    assert replay.status_code == 201, replay.text
    assert replay.json()["runner_job"]["id"] == first.json()["runner_job"]["id"]
    assert replay.json()["simulation_run"]["id"] == first.json()["simulation_run"]["id"]
    assert _run_counts() == (1, 1)


def test_schema_v3_preview_rejects_superseded_linked_parameter(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    bindings = _linked_input(parameter_id)
    ready = _preview(client, model_version_id, bindings)
    assert ready.status_code == 200, ready.text
    assert ready.json()["state"] == "ready"

    _set_parameter_status(parameter_id, "superseded")
    stale = _preview(client, model_version_id, bindings)

    assert stale.status_code == 200, stale.text
    body = stale.json()
    assert body["state"] == "invalid"
    tube = next(item for item in body["variables"] if item["name"] == "tube_length")
    assert "binding_parameter_not_found" in tube["errors"]
    assert body["normalized_input_set"] is None


def test_schema_v3_preview_rejects_051_stale_non_superseded_parameter(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    bindings = _linked_input(parameter_id)
    _mark_parameter_stale(client, parameter_id)

    response = _preview(client, model_version_id, bindings)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["state"] == "invalid"
    tube = next(item for item in body["variables"] if item["name"] == "tube_length")
    assert "binding_parameter_not_found" in tube["errors"]


def test_schema_v3_run_claim_fails_closed_if_source_becomes_unusable(client: TestClient) -> None:
    model_version_id = _register(client, semantic=True)
    parameter_id = _create_parameter(client)
    input_set = _linked_input(parameter_id)
    create = client.post(
        "/workspaces/bluerev/runner-jobs",
        json=_payload(model_version_id, input_set, "semantic-run-stale-0001"),
    )
    assert create.status_code == 201, create.text
    runner_job = create.json()["runner_job"]
    working_dir = Path(str(runner_job["working_dir"]))
    input_file = Path(str(runner_job["input_file"]))
    assert working_dir.exists() is False

    _set_parameter_status(parameter_id, "superseded")
    response = client.post(f"/runner-jobs/{runner_job['id']}/run")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["simulation_run"]["status"] == "failed"
    assert body["simulation_run"]["started_at"] is None
    assert body["error"] == {
        "code": "runner_linked_parameter_unusable",
        "message": "A linked Parameter is no longer usable for this queued run.",
    }
    persisted = json.loads(body["simulation_run"]["output_payload"])
    assert persisted == {"status": "failed", "error": body["error"]}
    assert working_dir.exists() is False
    assert input_file.exists() is False
    assert _runner_event_types(str(runner_job["id"])) == ["RunnerJobCreated", "RunnerJobFailed"]

    repeated = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "runner_job_not_queued"


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

    run = client.post(f"/runner-jobs/{response.json()['runner_job']['id']}/run")
    assert run.status_code == 200, run.text
    assert run.json()["runner_job"]["status"] == "succeeded"
