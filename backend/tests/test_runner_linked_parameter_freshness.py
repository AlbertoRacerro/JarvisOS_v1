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


def _register_semantic_model(client: TestClient) -> str:
    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-semantic-v0/register",
        json={},
    )
    assert response.status_code == 200, response.text
    return str(response.json()["id"])


def _create_parameter(client: TestClient, *, name: str, value: str = "20") -> str:
    response = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": name, "value": value, "unit": "m"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _bindings_with_parameter(parameter_id: str) -> dict[str, dict[str, object]]:
    bindings = _baseline()
    bindings["tube_length"]["source_parameter_id"] = parameter_id
    return bindings


def _preview(client: TestClient, model_version_id: str, bindings: dict[str, object]):
    return client.post(
        f"/workspaces/bluerev/model-implementations/{model_version_id}/binding-preview",
        json={"bindings": bindings},
    )


def _mark_parameter_stale(client: TestClient, parameter_id: str) -> None:
    replacement_id = _create_parameter(client, name="Replacement tube length", value="21")

    from app.core.database import open_sqlite_connection
    from app.modules.events.service import utc_now

    invalidation_id = str(uuid4())
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
                parameter_id,
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
                str(uuid4()),
                "bluerev",
                invalidation_id,
                f"parameter:{parameter_id}",
                "parameter",
                parameter_id,
                "source_parameter_superseded",
                "[]",
                "test-path",
                now,
            ),
        )
        connection.commit()


def _run_counts() -> tuple[int, int]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        jobs = int(connection.execute("SELECT COUNT(*) AS count FROM runner_jobs").fetchone()["count"])
        runs = int(connection.execute("SELECT COUNT(*) AS count FROM simulation_runs").fetchone()["count"])
    return jobs, runs


def _event_types(target_id: str) -> list[str]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT event_type FROM events WHERE target_id = ? ORDER BY created_at ASC",
            (target_id,),
        ).fetchall()
    return [str(row["event_type"]) for row in rows]


def test_preview_treats_stale_linked_parameter_as_unusable(client: TestClient) -> None:
    model_version_id = _register_semantic_model(client)
    parameter_id = _create_parameter(client, name="Tube length")
    bindings = _bindings_with_parameter(parameter_id)

    ready = _preview(client, model_version_id, bindings)
    assert ready.status_code == 200, ready.text
    assert ready.json()["state"] == "ready"

    before = _run_counts()
    _mark_parameter_stale(client, parameter_id)
    stale = _preview(client, model_version_id, bindings)

    assert stale.status_code == 200, stale.text
    assert stale.json()["state"] != "ready"
    assert stale.json()["normalized_input_set"] is None
    assert _run_counts() == before


@pytest.mark.parametrize("request_key", [None, "freshness-create-0001"])
def test_new_runner_create_rejects_stale_linked_parameter_atomically(
    client: TestClient,
    request_key: str | None,
) -> None:
    model_version_id = _register_semantic_model(client)
    parameter_id = _create_parameter(client, name="Tube length")
    preview = _preview(client, model_version_id, _bindings_with_parameter(parameter_id))
    assert preview.status_code == 200
    normalized = preview.json()["normalized_input_set"]
    assert normalized is not None

    before = _run_counts()
    _mark_parameter_stale(client, parameter_id)
    payload: dict[str, object] = {
        "model_version_id": model_version_id,
        "run_label": "stale-create",
        "input_set": normalized,
    }
    if request_key is not None:
        payload["request_key"] = request_key

    response = client.post("/workspaces/bluerev/runner-jobs", json=payload)

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "runner_linked_parameter_unusable"
    assert _run_counts() == before


def test_same_key_replay_survives_staleness_but_run_claim_fails_before_side_effects(
    client: TestClient,
) -> None:
    model_version_id = _register_semantic_model(client)
    parameter_id = _create_parameter(client, name="Tube length")
    preview = _preview(client, model_version_id, _bindings_with_parameter(parameter_id))
    normalized = preview.json()["normalized_input_set"]
    assert preview.status_code == 200 and normalized is not None

    payload = {
        "model_version_id": model_version_id,
        "run_label": "stale-after-create",
        "input_set": normalized,
        "request_key": "freshness-replay-0001",
    }
    created = client.post("/workspaces/bluerev/runner-jobs", json=payload)
    assert created.status_code == 201, created.text
    runner_job = created.json()["runner_job"]
    simulation_run_id = created.json()["simulation_run"]["id"]
    working_dir = Path(str(runner_job["working_dir"]))
    assert not working_dir.exists()

    _mark_parameter_stale(client, parameter_id)

    replay = client.post("/workspaces/bluerev/runner-jobs", json=payload)
    assert replay.status_code == 201, replay.text
    assert replay.json()["runner_job"]["id"] == runner_job["id"]
    assert replay.json()["simulation_run"]["id"] == simulation_run_id

    run = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert run.status_code == 200, run.text
    assert run.json()["runner_job"]["status"] == "failed"
    assert run.json()["simulation_run"]["status"] == "failed"
    assert run.json()["simulation_run"]["started_at"] is None
    assert run.json()["error"] == {
        "code": "runner_linked_parameter_unusable",
        "message": "A linked Parameter is no longer usable for this queued run.",
    }
    assert not working_dir.exists()
    assert _event_types(str(runner_job["id"])) == ["RunnerJobCreated", "RunnerJobFailed"]

    repeated = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert repeated.status_code == 409
    assert repeated.json()["detail"]["code"] == "runner_job_not_queued"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        stored = connection.execute(
            "SELECT output_payload FROM simulation_runs WHERE id = ?",
            (simulation_run_id,),
        ).fetchone()
    error_payload = json.loads(stored["output_payload"])
    assert error_payload["error"]["code"] == "runner_linked_parameter_unusable"
