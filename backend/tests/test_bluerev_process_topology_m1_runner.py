import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.safety import RunnerSafetyError, preflight_script_policy, sha256_file
from app.modules.runner.topology_m1 import (
    MODEL_LABEL,
    bundled_contract_path,
    bundled_script_path,
    is_exact_bundled_profile,
)


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


def _valid_input() -> dict[str, object]:
    fixture = Path(__file__).parent / "fixtures" / "bluerev_process_topology_m1_valid.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_topology_m1_registration_preview_and_run(client: TestClient) -> None:
    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    first = client.post(endpoint)
    second = client.post(endpoint)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    implementation = first.json()
    assert second.json()["id"] == implementation["id"]
    assert implementation["version_label"] == MODEL_LABEL
    assert implementation["script_sha256"] == sha256_file(bundled_script_path())

    preview = client.post(
        f"/workspaces/bluerev/model-implementations/{implementation['id']}/binding-preview",
        json={"bindings": _valid_input()},
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["state"] == "ready"
    assert preview_body["structural_input_dof"] == 26
    assert preview_body["unresolved_input_dof"] == 0

    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    runner_job = created.json()["runner_job"]
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["runner_job"]["status"] == "succeeded"
    assert body["error"] is None
    assert body["output"]["diagnostics"]["model_id"] == "bluerev_process_topology_m1_v0"

    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200, artifacts.text
    rows = artifacts.json()
    assert [(row["role"], row["filename"]) for row in rows] == [
        ("calc_result_json", "result.json"),
        ("bluerev_topology_manifest", "topology_manifest.json"),
    ]
    assert all(row["under_data_root"] for row in rows)
    assert all(row["sha256"] and len(row["sha256"]) == 64 for row in rows)


def test_exact_profile_requires_label_script_and_contract_hash() -> None:
    contract = json.loads(bundled_contract_path().read_text(encoding="utf-8"))
    _, contract_sha, _ = canonicalize_input_contract(contract)
    script_sha = sha256_file(bundled_script_path())
    exact = {
        "implementation_kind": "calc_v0",
        "version_label": MODEL_LABEL,
        "script_sha256": script_sha,
        "input_contract_sha256": contract_sha,
    }
    assert is_exact_bundled_profile(exact, script_sha) is True
    for key, value in (
        ("version_label", "wrong"),
        ("script_sha256", "0" * 64),
        ("input_contract_sha256", "0" * 64),
    ):
        changed = dict(exact)
        changed[key] = value
        assert is_exact_bundled_profile(changed, script_sha) is False


@pytest.mark.parametrize(
    "source",
    [
        "import hashlib\n",
        "with open('topology_manifest.json', 'w', encoding='utf-8') as handle:\n    handle.write('{}')\n",
    ],
)
def test_generic_calc_cannot_activate_topology_surface(tmp_path: Path, source: str) -> None:
    script = tmp_path / "calc_v0.py"
    script.write_text(source, encoding="utf-8")
    with pytest.raises(RunnerSafetyError) as exc_info:
        preflight_script_policy(script, ast_policy="calc_v0")
    assert exc_info.value.code == "SANDBOX_VIOLATION"
