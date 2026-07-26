from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv(
        "JARVISOS_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _create_spec(client: TestClient, title: str = "Runner boundary test") -> str:
    response = client.post(
        "/workspaces/bluerev/model-specs",
        json={"title": title, "engineering_question": "Verify bundled-only runner authority."},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _baseline_047() -> dict[str, dict[str, object]]:
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


def _seed_legacy_calc(client: TestClient) -> dict[str, object]:
    from app.modules.runner.models import ModelImplementationCreate
    from app.modules.runner.service import create_model_implementation

    spec_id = _create_spec(client, "Legacy non-bundled calc")
    return create_model_implementation(
        "bluerev",
        ModelImplementationCreate(
            model_spec_id=spec_id,
            version_label="legacy-caller-calc",
            implementation_kind="calc_v0",
            script_text=(
                "import json\n"
                "with open('result.json', 'w', encoding='utf-8') as handle:\n"
                "    json.dump({'schema_version': 1, 'status': 'succeeded', 'outputs': {}}, handle)\n"
            ),
        ),
    ).model_dump(mode="json")


def test_public_request_forbids_executable_and_trust_fields(client: TestClient) -> None:
    spec_id = _create_spec(client)
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        before_versions = connection.execute("SELECT COUNT(*) AS count FROM model_versions").fetchone()["count"]
        before_artifacts = connection.execute("SELECT COUNT(*) AS count FROM artifacts").fetchone()["count"]

    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": spec_id,
            "implementation_kind": "calc_v0",
            "script_text": "print('caller code')",
            "trusted": True,
        },
    )
    assert response.status_code == 422

    with open_sqlite_connection() as connection:
        after_versions = connection.execute("SELECT COUNT(*) AS count FROM model_versions").fetchone()["count"]
        assert after_versions == before_versions
        assert connection.execute("SELECT COUNT(*) AS count FROM artifacts").fetchone()["count"] == before_artifacts


def test_exact_bundled_047_registers_and_runs(client: TestClient) -> None:
    registered = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    assert registered.status_code == 200, registered.text

    job = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": registered.json()["id"],
            "run_label": "bundled-boundary",
            "input_set": _baseline_047(),
        },
    )
    assert job.status_code == 201, job.text
    run = client.post(f"/runner-jobs/{job.json()['runner_job']['id']}/run")
    assert run.status_code == 200, run.text
    assert run.json()["runner_job"]["status"] == "succeeded"


def test_legacy_non_bundled_row_is_readable_but_not_executable(client: TestClient) -> None:
    legacy = _seed_legacy_calc(client)

    listed = client.get("/workspaces/bluerev/model-implementations")
    assert listed.status_code == 200
    assert legacy["id"] in {item["id"] for item in listed.json()}

    denied = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": legacy["id"],
            "run_label": "must-not-run",
            "input_set": {},
        },
    )
    assert denied.status_code == 400
    assert denied.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"


def test_bluecad_l2_is_not_instantiable(client: TestClient) -> None:
    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": _create_spec(client, "L2 disabled"),
            "implementation_kind": "bluecad_l2_v0",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_implementation_kind_unsupported"


def test_origin_guard_rejects_unconfigured_browser_origin(client: TestClient) -> None:
    path = "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"

    denied = client.post(path, headers={"Origin": "https://hostile.example"})
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "runner_origin_forbidden"

    allowed = client.post(path, headers={"Origin": "http://127.0.0.1:5173"})
    assert allowed.status_code == 200, allowed.text

    originless = client.post(path)
    assert originless.status_code == 200, originless.text
    assert originless.json()["id"] == allowed.json()["id"]


def test_denial_reaches_zero_real_launcher_calls(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _seed_legacy_calc(client)
    calls = 0

    def forbidden_launcher(**_: object) -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("launcher must not be reached")

    monkeypatch.setattr(
        "app.modules.runner.service.execute_python_script",
        forbidden_launcher,
    )
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": legacy["id"],
            "run_label": "zero-child",
            "input_set": {},
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert calls == 0
