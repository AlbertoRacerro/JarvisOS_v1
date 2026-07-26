from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client


def _create_spec(client: TestClient, title: str = "Runner cleanup fixture") -> str:
    response = client.post(
        "/workspaces/bluerev/model-specs",
        json={
            "title": title,
            "engineering_question": "Exercise the bundled-only runner boundary.",
        },
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _table_count(table: str) -> int:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


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


def _register_047(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _create_public_job(client: TestClient, model_version_id: str) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": model_version_id,
            "run_label": "runner-cleanup-test",
            "input_set": _baseline_047(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_public_registration_forbids_source_and_trust_fields_without_side_effects(client: TestClient) -> None:
    model_spec_id = _create_spec(client)
    before_versions = _table_count("model_versions")
    before_artifacts = _table_count("artifacts")

    for extra in (
        {"script_text": "print('caller source')"},
        {"trusted": True, "script_sha256": "0" * 64},
    ):
        response = client.post(
            "/workspaces/bluerev/model-implementations",
            json={
                "model_spec_id": model_spec_id,
                "implementation_kind": "batch_growth_v0",
                **extra,
            },
        )
        assert response.status_code == 422

    assert _table_count("model_versions") == before_versions
    assert _table_count("artifacts") == before_artifacts


def test_exact_bundled_calc_registers_and_executes(client: TestClient) -> None:
    implementation = _register_047(client)
    job = _create_public_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job['runner_job']['id']}/run")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["runner_job"]["status"] == "succeeded"
    assert body["output"]["diagnostics"]["model_id"] == "bluerev_geometry_hydraulics_v0"


def test_legacy_non_bundled_rows_remain_readable_but_cannot_create_or_execute_jobs(
    client: TestClient,
) -> None:
    from app.modules.runner import service as legacy_service
    from app.modules.runner.models import ModelImplementationCreate, RunnerJobCreate

    model_spec_id = _create_spec(client, "Legacy runner fixture")
    source = """import json\nwith open(\"input.json\", encoding=\"utf-8\") as handle:\n    inputs = json.load(handle)\nresult = {\"schema_version\": 1, \"status\": \"succeeded\", \"outputs\": {\"x\": inputs[\"x\"]}}\nwith open(\"result.json\", \"w\", encoding=\"utf-8\") as handle:\n    json.dump(result, handle, sort_keys=True, separators=(\",\", \":\"), allow_nan=False)\n"""
    legacy = legacy_service.create_model_implementation(
        "bluerev",
        ModelImplementationCreate(
            model_spec_id=model_spec_id,
            version_label="legacy-non-bundled",
            implementation_kind="calc_v0",
            script_text=source,
        ),
    )

    denied_create = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": legacy.id,
            "run_label": "must-not-create",
            "input_set": {"x": {"value": 1.0, "unit": "1"}},
        },
    )
    assert denied_create.status_code == 400
    assert denied_create.json()["detail"]["code"] == "runner_implementation_not_bundled"

    legacy_job = legacy_service.create_runner_job(
        "bluerev",
        RunnerJobCreate(
            model_version_id=legacy.id,
            run_label="seeded-legacy-job",
            input_set={"x": {"value": 1.0, "unit": "1"}},
        ),
    )
    denied_run = client.post(f"/runner-jobs/{legacy_job.runner_job.id}/run")
    assert denied_run.status_code == 400
    assert denied_run.json()["detail"]["code"] == "runner_implementation_not_bundled"

    listed = client.get("/workspaces/bluerev/model-implementations")
    assert listed.status_code == 200
    assert any(item["id"] == legacy.id for item in listed.json())


def test_bluecad_l2_is_not_instantiable(client: TestClient) -> None:
    model_spec_id = _create_spec(client, "Non-instantiable L2 fixture")

    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": model_spec_id,
            "implementation_kind": "bluecad_l2_v0",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_implementation_kind_non_instantiable"


def test_mutating_runner_routes_enforce_configured_origin_and_allow_native_clients(
    client: TestClient,
) -> None:
    before = _table_count("model_versions")
    denied = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register",
        headers={"Origin": "https://hostile.example"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "runner_origin_forbidden"
    assert _table_count("model_versions") == before

    allowed = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert allowed.status_code == 200, allowed.text

    native = client.post(
        "/workspaces/bluerev/bundled-models/bluerev-geometry-hydraulics-v0/register"
    )
    assert native.status_code == 200, native.text
    assert native.json()["id"] == allowed.json()["id"]


def test_policy_denial_maps_new_error_and_invokes_zero_real_launcher_processes(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.runner import public_service
    from app.modules.runner import service as legacy_service
    from app.modules.runner.safety import RunnerSafetyError

    implementation = _register_047(client)
    job = _create_public_job(client, str(implementation["id"]))
    launches = 0

    def deny_policy(*args, **kwargs) -> None:
        del args, kwargs
        raise RunnerSafetyError("SANDBOX_VIOLATION", "reviewed policy fixture denial")

    def count_launcher(*args, **kwargs):
        nonlocal launches
        del args, kwargs
        launches += 1
        raise AssertionError("The real launcher boundary must not be invoked.")

    monkeypatch.setattr(public_service, "preflight_script_policy", deny_policy)
    monkeypatch.setattr(legacy_service, "execute_python_script", count_launcher)

    response = client.post(f"/runner-jobs/{job['runner_job']['id']}/run")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert launches == 0
