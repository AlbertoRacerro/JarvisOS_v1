import hashlib
import json
import subprocess
import sys
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
    validate_manifest,
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


def _register_and_create_job(client: TestClient):
    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    registered = client.post(endpoint)
    assert registered.status_code == 200, registered.text
    implementation = registered.json()
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    return implementation, created.json()["runner_job"]


def test_topology_m1_registration_preview_run_and_artifacts(client: TestClient) -> None:
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
    assert preview_body["bound_input_dof"] == 26
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
    diagnostics = body["output"]["diagnostics"]
    assert diagnostics["model_id"] == "bluerev_process_topology_m1_v0"

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
    manifest_row = next(row for row in rows if row["role"] == "bluerev_topology_manifest")
    assert diagnostics["topology_manifest_sha256"] == f"sha256:{manifest_row['sha256']}"

    repeated = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert repeated.status_code == 409


def test_exact_profile_requires_kind_label_script_and_contract_hash() -> None:
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
        ("implementation_kind", "bluecad_l2_v0"),
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


def test_exact_profile_allows_only_fixed_manifest_write(tmp_path: Path) -> None:
    valid = tmp_path / "valid.py"
    valid.write_text(
        "import hashlib\n"
        "with open('input.json', encoding='utf-8') as source:\n    source.read()\n"
        "with open('topology_manifest.json', 'w', encoding='utf-8') as target:\n    target.write('{}')\n"
        "with open('result.json', 'w', encoding='utf-8') as target:\n    target.write('{}')\n",
        encoding="utf-8",
    )
    preflight_script_policy(valid, ast_policy="calc_v0_topology_m1")

    for source in (
        "with open('other.json', 'w') as handle:\n    handle.write('{}')\n",
        "with open('topology_manifest.json', 'a') as handle:\n    handle.write('{}')\n",
    ):
        invalid = tmp_path / f"invalid-{hashlib.sha256(source.encode()).hexdigest()}.py"
        invalid.write_text(source, encoding="utf-8")
        with pytest.raises(RunnerSafetyError):
            preflight_script_policy(invalid, ast_policy="calc_v0_topology_m1")


def _direct_model_run(tmp_path: Path):
    payload = _valid_input()
    (tmp_path / "input.json").write_text(json.dumps(payload), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(bundled_script_path())],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    return payload, result


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("missing", "runner_topology_manifest_missing"),
        ("malformed", "runner_topology_manifest_invalid"),
        ("noncanonical", "runner_topology_manifest_noncanonical"),
        ("schema", "runner_topology_manifest_schema_invalid"),
        ("input", "runner_topology_manifest_input_mismatch"),
        ("digest", "runner_topology_manifest_digest_mismatch"),
    ],
)
def test_manifest_failure_matrix(tmp_path: Path, mutation: str, code: str) -> None:
    payload, result = _direct_model_run(tmp_path)
    path = tmp_path / "topology_manifest.json"
    if mutation == "missing":
        path.unlink()
    elif mutation == "malformed":
        path.write_text("{", encoding="utf-8")
    else:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "schema":
            manifest["topology_kind"] = "wrong"
        elif mutation == "input":
            manifest["executed_inputs"]["liquid_density"]["value"] = 999.0
        raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if mutation == "noncanonical":
            raw = json.dumps(manifest, indent=2, sort_keys=True)
        path.write_text(raw, encoding="utf-8")
        if mutation in {"schema", "input"}:
            result["diagnostics"]["topology_manifest_sha256"] = (
                f"sha256:{hashlib.sha256(raw.encode()).hexdigest()}"
            )
        if mutation == "digest":
            result["diagnostics"]["topology_manifest_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_manifest(
            tmp_path,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
            result,
            max_bytes=1024 * 1024,
        )
    assert exc_info.value.code == code


def test_invalid_manifest_fails_run_before_artifact_registration(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.runner import service

    original_execute = service.execute_python_script

    def corrupt_manifest(**kwargs):
        execution = original_execute(**kwargs)
        (Path(kwargs["output_dir"]) / "topology_manifest.json").write_text(
            "{",
            encoding="utf-8",
        )
        return execution

    monkeypatch.setattr(service, "execute_python_script", corrupt_manifest)
    _, runner_job = _register_and_create_job(client)
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200
    body = executed.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["error"]["code"] == "runner_topology_manifest_invalid"
    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200
    assert artifacts.json() == []


def test_caller_artifact_declaration_is_rejected_before_registration(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.runner import service

    original_execute = service.execute_python_script

    def declare_artifact(**kwargs):
        execution = original_execute(**kwargs)
        result_path = Path(kwargs["output_dir"]) / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["artifacts"] = []
        result_path.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return execution

    monkeypatch.setattr(service, "execute_python_script", declare_artifact)
    _, runner_job = _register_and_create_job(client)
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200
    body = executed.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["error"]["code"] == "runner_topology_artifact_declaration_forbidden"
