from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.modules.runner.process_kernel_047 import (
    MODEL_LABEL,
    bundled_script_path,
    validate_registered_bundle,
)
from app.modules.runner.safety import RunnerSafetyError, preflight_script_policy, sha256_file


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
    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-kernel-047-v1/register"
    response = client.post(endpoint)
    assert response.status_code == 200, response.text
    return response.json()


def _create_and_run(client: TestClient, implementation_id: str) -> dict[str, object]:
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation_id, "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    runner_job = created.json()["runner_job"]
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["runner_job"]["status"] == "succeeded"
    assert body["error"] is None
    return body


def test_registration_preview_and_two_real_runner_jobs_are_stable(client: TestClient) -> None:
    first = _register(client)
    second = _register(client)
    assert second["id"] == first["id"]
    assert first["version_label"] == MODEL_LABEL
    assert first["implementation_kind"] == "calc_v0"
    assert first["script_sha256"] == sha256_file(bundled_script_path())

    model_dir = Path(str(first["script_path"])).parent
    manifest_sha = validate_registered_bundle(model_dir)
    assert len(manifest_sha) == 64

    preview = client.post(
        f"/workspaces/bluerev/model-implementations/{first['id']}/binding-preview",
        json={"bindings": _valid_input()},
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["state"] == "ready"
    assert preview_body["structural_input_dof"] == 9
    assert preview_body["bound_input_dof"] == 9
    assert preview_body["unresolved_input_dof"] == 0

    first_run = _create_and_run(client, str(first["id"]))
    assert first_run["output"]["diagnostics"]["model_id"] == "bluerev_geometry_hydraulics_v0"
    assert first_run["output"]["diagnostics"]["workbook_runtime_dependency"] is False
    assert first_run["runner_job"]["environment_metadata"]["inherited_environment"] is False
    assert first_run["runner_job"]["environment_metadata"]["allowlisted_keys"] == [
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONIOENCODING",
    ]
    assert not (model_dir / "process_kernel" / "__pycache__").exists()
    assert validate_registered_bundle(model_dir) == manifest_sha

    second_run = _create_and_run(client, str(first["id"]))
    assert second_run["output"] == first_run["output"]
    assert validate_registered_bundle(model_dir) == manifest_sha

    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{first_run['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200, artifacts.text
    assert [(row["role"], row["filename"]) for row in artifacts.json()] == [
        ("calc_result_json", "result.json")
    ]


def test_bundle_tamper_is_rejected_before_subprocess(client: TestClient, monkeypatch) -> None:
    implementation = _register(client)
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    runner_job_id = created.json()["runner_job"]["id"]

    from app.modules.runner import service

    calls = 0

    def forbidden_execute(**kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError(f"subprocess must not be invoked: {kwargs}")

    monkeypatch.setattr(service, "execute_python_script", forbidden_execute)
    package_file = Path(str(implementation["script_path"])).parent / "process_kernel" / "blocks.py"
    package_file.write_bytes(package_file.read_bytes() + b"\n# tampered\n")

    response = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert calls == 0


def test_generic_calc_policy_cannot_import_process_kernel(tmp_path: Path) -> None:
    script = tmp_path / "calc_v0.py"
    script.write_text(
        "import process_kernel\n"
        "with open('input.json', encoding='utf-8') as source:\n    source.read()\n"
        "with open('result.json', 'w', encoding='utf-8') as target:\n    target.write('{}')\n",
        encoding="utf-8",
    )
    with pytest.raises(RunnerSafetyError) as exc_info:
        preflight_script_policy(script, ast_policy="calc_v0")
    assert exc_info.value.code == "SANDBOX_VIOLATION"
