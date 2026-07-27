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


def _create_job(client: TestClient, implementation_id: object) -> str:
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation_id, "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    return str(created.json()["runner_job"]["id"])


def _create_and_run(client: TestClient, implementation_id: str) -> dict[str, object]:
    runner_job_id = _create_job(client, implementation_id)
    executed = client.post(f"/runner-jobs/{runner_job_id}/run")
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


_PROFILE_IDENTITY_DIMENSIONS = (
    "entrypoint",
    "package_file",
    "schema_version",
    "profile_id",
    "model_label",
    "contract_version",
    "ast_policy_id",
    "registered_entrypoint",
    "contract",
    "semantic_registry",
    "component_catalog",
    "screening_constants",
    "flowsheet",
    "profile_constants",
    "assembler",
    "import_policy",
)


def _tamper_profile_identity(
    identity_dimension: str,
    implementation: dict[str, object],
    monkeypatch,
) -> None:
    from app.modules.runner import process_kernel_047

    model_dir = Path(str(implementation["script_path"])).parent
    if identity_dimension == "entrypoint":
        script_path = Path(str(implementation["script_path"]))
        script_path.write_bytes(script_path.read_bytes() + b"\n# tampered\n")
    elif identity_dimension == "package_file":
        package_file = model_dir / "process_kernel" / "blocks.py"
        package_file.write_bytes(package_file.read_bytes() + b"\n# tampered\n")
    elif identity_dimension == "schema_version":
        monkeypatch.setattr(process_kernel_047, "BUNDLE_SCHEMA_VERSION", 2)
    elif identity_dimension == "profile_id":
        monkeypatch.setattr(process_kernel_047, "PROFILE_ID", "tampered_profile")
    elif identity_dimension == "model_label":
        monkeypatch.setattr(process_kernel_047, "MODEL_LABEL", "tampered-model-label")
    elif identity_dimension == "contract_version":
        monkeypatch.setattr(process_kernel_047, "CONTRACT_VERSION", "tampered_contract")
    elif identity_dimension == "ast_policy_id":
        monkeypatch.setattr(process_kernel_047, "AST_POLICY_ID", "tampered_policy")
    elif identity_dimension == "registered_entrypoint":
        monkeypatch.setattr(process_kernel_047, "REGISTERED_ENTRYPOINT_FILENAME", "tampered.py")
    elif identity_dimension == "contract":
        monkeypatch.setattr(process_kernel_047, "expected_contract_sha256", lambda: "0" * 64)
    elif identity_dimension == "semantic_registry":
        monkeypatch.setattr(process_kernel_047, "semantic_registry_sha256", lambda: "1" * 64)
    elif identity_dimension == "component_catalog":
        monkeypatch.setattr(process_kernel_047, "component_catalog_sha256", lambda: "2" * 64)
    elif identity_dimension == "screening_constants":
        monkeypatch.setattr(process_kernel_047, "screening_mass_constants_sha256", lambda: "3" * 64)
    elif identity_dimension == "flowsheet":
        monkeypatch.setattr(process_kernel_047, "flowsheet_profile_sha256", lambda: "4" * 64)
    elif identity_dimension == "profile_constants":
        monkeypatch.setattr(process_kernel_047, "profile_constants_sha256", lambda: "5" * 64)
    elif identity_dimension == "assembler":
        monkeypatch.setattr(process_kernel_047, "assembler_contract_sha256", lambda: "6" * 64)
    elif identity_dimension == "import_policy":
        monkeypatch.setattr(
            process_kernel_047,
            "ALLOWED_IMPORT_ROOTS",
            ("json", "math", "process_kernel", "statistics"),
        )
    else:  # pragma: no cover - parametrization is a closed set
        raise AssertionError(f"Unhandled identity dimension: {identity_dimension}")


@pytest.mark.parametrize("identity_dimension", _PROFILE_IDENTITY_DIMENSIONS)
def test_complete_profile_tamper_is_rejected_before_subprocess(
    client: TestClient,
    monkeypatch,
    identity_dimension: str,
) -> None:
    implementation = _register(client)
    runner_job_id = _create_job(client, implementation["id"])

    from app.modules.runner import service

    calls = 0

    def forbidden_execute(**kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError(f"subprocess must not be invoked: {kwargs}")

    monkeypatch.setattr(service, "execute_python_script", forbidden_execute)
    _tamper_profile_identity(identity_dimension, implementation, monkeypatch)

    response = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert response.status_code == 400, response.text
    assert response.json()["detail"]["code"] == "RUNNER_SCRIPT_POLICY_VIOLATION"
    assert calls == 0


def test_package_tamper_is_rejected_during_job_creation(client: TestClient, monkeypatch) -> None:
    implementation = _register(client)

    from app.modules.runner import service

    calls = 0

    def forbidden_execute(**kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError(f"subprocess must not be invoked: {kwargs}")

    monkeypatch.setattr(service, "execute_python_script", forbidden_execute)
    _tamper_profile_identity("package_file", implementation, monkeypatch)

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
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
