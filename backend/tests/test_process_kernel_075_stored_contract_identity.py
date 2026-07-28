from __future__ import annotations

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


def _valid_input() -> dict[str, dict[str, object]]:
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


def _register(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-process-kernel-047-v1/register"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _create_job(client: TestClient, implementation_id: object) -> str:
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation_id, "input_set": _valid_input()},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["runner_job"]["id"])


def _corrupt_stored_contract_payload(implementation_id: object) -> None:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT input_contract_payload, input_contract_sha256
            FROM model_versions
            WHERE id = ?
            """,
            (implementation_id,),
        ).fetchone()
        assert row is not None
        original_payload = str(row["input_contract_payload"])
        original_sha = str(row["input_contract_sha256"])
        connection.execute(
            """
            UPDATE model_versions
            SET input_contract_payload = ?
            WHERE id = ?
            """,
            (original_payload + " ", implementation_id),
        )
        connection.commit()
        updated = connection.execute(
            """
            SELECT input_contract_payload, input_contract_sha256
            FROM model_versions
            WHERE id = ?
            """,
            (implementation_id,),
        ).fetchone()
        assert updated is not None
        assert updated["input_contract_payload"] != original_payload
        assert updated["input_contract_sha256"] == original_sha


def test_corrupted_stored_contract_is_rejected_during_job_creation(client: TestClient) -> None:
    implementation = _register(client)
    _corrupt_stored_contract_payload(implementation["id"])

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"


def test_corrupted_stored_contract_is_rejected_before_subprocess(
    client: TestClient,
    monkeypatch,
) -> None:
    implementation = _register(client)
    runner_job_id = _create_job(client, implementation["id"])
    _corrupt_stored_contract_payload(implementation["id"])

    from app.modules.runner import service

    calls = 0

    def forbidden_execute(**kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError(f"subprocess must not be invoked: {kwargs}")

    monkeypatch.setattr(service, "execute_python_script", forbidden_execute)

    response = client.post(f"/runner-jobs/{runner_job_id}/run")

    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert calls == 0
