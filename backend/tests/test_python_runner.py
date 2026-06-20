from collections.abc import Iterator
import json
from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("SCALEWAY_API_KEY", "should-not-enter-runner")

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


def _create_model_spec(client: TestClient) -> str:
    response = client.post(
        "/workspaces/bluerev/model-specs",
        json={
            "title": "Batch Growth V0",
            "engineering_question": "How does biomass grow over a short deterministic batch run?",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_implementation(client: TestClient) -> dict[str, object]:
    model_spec_id = _create_model_spec(client)
    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": model_spec_id,
            "version_label": "batch-growth-v0",
            "implementation_kind": "batch_growth_v0",
        },
    )
    assert response.status_code == 201
    return response.json()


def _valid_input_set() -> dict[str, object]:
    return {
        "schema_version": 1,
        "parameters": {"mu_max": 0.4, "X0": 0.05, "t_final": 2, "dt": 1},
        "input_artifact_ids": [],
    }


def _create_job(
    client: TestClient,
    model_version_id: str,
    timeout_seconds: int = 10,
    input_set: dict[str, object] | None = None,
) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": model_version_id,
            "run_label": "runner-test",
            "timeout_seconds": timeout_seconds,
            "input_set": input_set or _valid_input_set(),
        },
    )
    assert response.status_code == 201
    return response.json()


def _update_script(implementation: dict[str, object], content: str) -> str:
    from app.core.database import open_sqlite_connection
    from app.modules.runner.safety import sha256_file

    script_path = Path(str(implementation["script_path"]))
    script_path.write_text(content, encoding="utf-8")
    digest = sha256_file(script_path)
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE artifacts SET sha256 = ? WHERE id = ?",
            (digest, implementation["implementation_artifact_id"]),
        )
        connection.commit()
    return digest


def _event_types_for_target(target_id: str) -> list[str]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT event_type FROM events WHERE target_id = ? ORDER BY created_at ASC",
            (target_id,),
        ).fetchall()
    return [row["event_type"] for row in rows]


def test_runner_creates_and_executes_batch_growth_successfully(client: TestClient) -> None:
    implementation = _create_implementation(client)
    assert implementation["script_sha256"]
    assert Path(str(implementation["script_path"])).exists()

    list_response = client.get("/workspaces/bluerev/model-implementations")
    assert list_response.status_code == 200
    assert any(item["id"] == implementation["id"] for item in list_response.json())

    job_response = _create_job(client, str(implementation["id"]))
    runner_job = job_response["runner_job"]
    simulation_run = job_response["simulation_run"]
    assert runner_job["status"] == "queued"
    assert runner_job["script_sha256"] == implementation["script_sha256"]
    assert simulation_run["status"] == "queued"
    assert json.loads(simulation_run["input_payload"])["parameters"]["mu_max"] == 0.4

    run_response = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["runner_job"]["status"] == "succeeded"
    assert body["simulation_run"]["status"] == "succeeded"
    assert body["error"] is None
    output = body["output"]
    assert output["status"] == "succeeded"
    assert output["outputs"]["point_count"] == 3
    assert output["outputs"]["final_biomass_concentration"] > 0.05
    assert "should-not-enter-runner" not in json.dumps(body)
    assert body["runner_job"]["command_metadata"]["shell"] is False
    assert body["runner_job"]["environment_metadata"]["inherited_environment"] is False
    assert body["runner_job"]["environment_metadata"]["allowlisted_keys"] == ["PYTHONIOENCODING"]

    detail_response = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "succeeded"
    assert json.loads(detail["output_payload"])["artifacts"][0]["path"] == "outputs/timeseries.csv"

    logs_response = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run['id']}/logs")
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert any(log["stream"] == "stdout" and "Batch growth completed" in log["content"] for log in logs)

    artifacts_response = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run['id']}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact["workspace_id"] == "bluerev"
    assert artifact["simulation_run_id"] == simulation_run["id"]
    assert artifact["filename"] == "timeseries.csv"
    assert artifact["artifact_type"] == "csv"
    assert artifact["role"] == "csv"
    assert artifact["relative_path"].endswith("outputs\\timeseries.csv") or artifact["relative_path"].endswith("outputs/timeseries.csv")
    assert artifact["stored_path"].startswith(str(Path(str(runner_job["output_dir"]))))
    assert artifact["size_bytes"] > 0
    assert artifact["under_data_root"] is True
    assert artifact["source_module"] == "python_runner_v0"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        run_artifact_count = connection.execute(
            "SELECT COUNT(*) AS count FROM run_artifacts WHERE simulation_run_id = ?",
            (simulation_run["id"],),
        ).fetchone()["count"]
        assert run_artifact_count == 1
        artifact_event_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM events
            WHERE event_type = ? AND payload LIKE ?
            """,
            ("RunArtifactRegistered", f'%"{simulation_run["id"]}"%'),
        ).fetchone()["count"]
        assert artifact_event_count == 1

    assert _event_types_for_target(runner_job["id"]) == [
        "RunnerJobCreated",
        "RunnerJobStarted",
        "RunnerJobSucceeded",
    ]


def test_run_artifacts_endpoint_blocks_wrong_workspace_run_mismatch(client: TestClient) -> None:
    implementation = _create_implementation(client)
    job_response = _create_job(client, str(implementation["id"]))
    simulation_run_id = job_response["simulation_run"]["id"]

    run_response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")
    assert run_response.status_code == 200

    workspace_response = client.post(
        "/workspaces",
        json={
            "name": "Other Workspace",
            "slug": "other-workspace",
            "description": "Used for mismatch test.",
        },
    )
    assert workspace_response.status_code == 201
    other_workspace_id = workspace_response.json()["id"]

    mismatch_response = client.get(f"/workspaces/{other_workspace_id}/simulation-runs/{simulation_run_id}/artifacts")

    assert mismatch_response.status_code == 404
    assert mismatch_response.json()["detail"]["code"] == "runner_simulation_run_not_found"


def test_runner_job_creation_does_not_execute_or_create_run_directory(client: TestClient) -> None:
    implementation = _create_implementation(client)
    job_response = _create_job(client, str(implementation["id"]))
    runner_job = job_response["runner_job"]
    simulation_run = job_response["simulation_run"]

    assert runner_job["status"] == "queued"
    assert simulation_run["status"] == "queued"
    assert Path(str(runner_job["working_dir"])).exists() is False

    logs_response = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run['id']}/logs")
    assert logs_response.status_code == 200
    assert logs_response.json() == []


def test_runner_lifecycle_event_redacts_secret_looking_run_label(client: TestClient) -> None:
    implementation = _create_implementation(client)
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "run_label": "manual smoke password=runner-secret",
            "timeout_seconds": 10,
            "input_set": _valid_input_set(),
        },
    )
    assert response.status_code == 201
    simulation_run_id = response.json()["simulation_run"]["id"]

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        event = connection.execute(
            """
            SELECT payload
            FROM events
            WHERE event_type = ? AND target_id = ?
            """,
            ("SimulationRunCreated", simulation_run_id),
        ).fetchone()

    assert event is not None
    payload_text = event["payload"]
    assert "runner-secret" not in payload_text
    assert "password=[REDACTED]" in payload_text


def test_runner_rejects_repeated_run_without_corrupting_succeeded_run(client: TestClient) -> None:
    implementation = _create_implementation(client)
    job_response = _create_job(client, str(implementation["id"]))
    runner_job_id = job_response["runner_job"]["id"]
    simulation_run_id = job_response["simulation_run"]["id"]

    first_response = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert first_response.status_code == 200
    assert first_response.json()["runner_job"]["status"] == "succeeded"

    second_response = client.post(f"/runner-jobs/{runner_job_id}/run")
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["code"] == "runner_job_not_queued"

    detail_response = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["status"] == "succeeded"
    assert json.loads(detail["output_payload"])["status"] == "succeeded"


def test_runner_invalid_job_id_fails_cleanly(client: TestClient) -> None:
    response = client.post("/runner-jobs/not-a-real-job/run")

    assert response.status_code == 404
    assert response.json()["detail"] == {"code": "runner_job_not_found", "message": "Runner job not found."}


@pytest.mark.parametrize(
    ("override", "expected_message"),
    [
        ({"dt": 0}, "dt must be greater than zero."),
        ({"t_final": -1}, "t_final must be nonnegative."),
        ({"mu_max": -0.1}, "mu_max must be nonnegative."),
        ({"X0": -0.05}, "X0 must be nonnegative."),
        ({"t_final": 10001, "dt": 1}, "The requested time grid is too large for V0."),
    ],
)
def test_runner_rejects_invalid_batch_growth_parameters(
    client: TestClient,
    override: dict[str, object],
    expected_message: str,
) -> None:
    implementation = _create_implementation(client)
    input_set = _valid_input_set()
    parameters = dict(input_set["parameters"])
    parameters.update(override)
    input_set["parameters"] = parameters

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "input_set": input_set,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {"code": "runner_input_invalid", "message": expected_message}


def test_runner_rejects_invalid_input_artifact_ids(client: TestClient) -> None:
    implementation = _create_implementation(client)
    input_set = _valid_input_set()
    input_set["input_artifact_ids"] = ["ok", 3]

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "input_set": input_set,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_input_invalid"


def test_runner_timeout_sets_timed_out_status(client: TestClient) -> None:
    implementation = _create_implementation(client)
    _update_script(
        implementation,
        """
import time
time.sleep(2)
""".strip(),
    )
    job_response = _create_job(client, str(implementation["id"]), timeout_seconds=1)

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["runner_job"]["status"] == "timed_out"
    assert body["simulation_run"]["status"] == "timed_out"
    assert body["error"]["code"] == "runner_timeout"
    assert _event_types_for_target(job_response["runner_job"]["id"])[-1] == "RunnerJobTimedOut"


def test_runner_failed_script_sets_failed_status(client: TestClient) -> None:
    implementation = _create_implementation(client)
    _update_script(
        implementation,
        """
import sys
print("intentional failure", file=sys.stderr)
raise SystemExit(3)
""".strip(),
    )
    job_response = _create_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["simulation_run"]["status"] == "failed"
    assert body["error"]["code"] == "runner_process_failed"
    logs = client.get(f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/logs").json()
    assert any("intentional failure" in log["content"] for log in logs)
    assert _event_types_for_target(job_response["runner_job"]["id"])[-1] == "RunnerJobFailed"


def test_runner_blocks_invalid_script_path_before_job_creation(client: TestClient, tmp_path) -> None:
    implementation = _create_implementation(client)
    outside_script = tmp_path / "outside.py"
    outside_script.write_text("print('outside')", encoding="utf-8")

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE artifacts SET stored_path = ? WHERE id = ?",
            (str(outside_script), implementation["implementation_artifact_id"]),
        )
        connection.commit()

    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "input_set": {"parameters": {"mu_max": 0.4, "X0": 0.05, "t_final": 1, "dt": 1}},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_script_path_outside_allowed_root"


def test_invalid_model_implementation_does_not_leave_folder(client: TestClient) -> None:
    from app.modules.runner.safety import model_implementation_root

    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": "missing-model-spec",
            "version_label": "bad-implementation",
            "implementation_kind": "batch_growth_v0",
        },
    )

    assert response.status_code == 404
    root = model_implementation_root("bluerev")
    assert not root.exists() or list(root.iterdir()) == []


@pytest.mark.parametrize(
    "script_content",
    [
        "import socket\nprint('blocked')\n",
        "import requests\nprint('blocked')\n",
        "import httpx\nprint('blocked')\n",
        "import urllib.request\nprint('blocked')\n",
        "import subprocess\nprint('blocked')\n",
        "import os\nos.system('echo blocked')\n",
        "import shutil\nshutil.rmtree('somewhere')\n",
        "from pathlib import Path\nPath('.env').read_text()\n",
        "import os\nprint(os.environ.get('SCALEWAY_API_KEY'))\n",
        "print('secret token password')\n",
    ],
)
def test_runner_blocks_obvious_script_policy_markers(client: TestClient, script_content: str) -> None:
    implementation = _create_implementation(client)
    _update_script(implementation, script_content)
    job_response = _create_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_policy_blocked"


def test_runner_blocks_tampered_run_paths_before_execution(client: TestClient, tmp_path) -> None:
    implementation = _create_implementation(client)
    job_response = _create_job(client, str(implementation["id"]))
    runner_job_id = job_response["runner_job"]["id"]
    simulation_run_id = job_response["simulation_run"]["id"]
    outside_dir = tmp_path / "outside-run-root"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE runner_jobs SET working_dir = ?, output_dir = ?, input_file = ? WHERE id = ?",
            (str(outside_dir), str(outside_dir), str(outside_dir / "input.json"), runner_job_id),
        )
        connection.commit()

    response = client.post(f"/runner-jobs/{runner_job_id}/run")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_working_dir_outside_run_root"
    assert outside_dir.exists() is False
    detail = client.get(f"/workspaces/bluerev/simulation-runs/{simulation_run_id}").json()
    assert detail["status"] == "queued"


def test_runner_blocks_artifact_path_traversal(client: TestClient) -> None:
    implementation = _create_implementation(client)
    _update_script(
        implementation,
        """
import json
import sys
from pathlib import Path
output_dir = Path(sys.argv[2])
result = {"schema_version": 1, "status": "succeeded", "outputs": {}, "artifacts": [{"path": "../escape.csv", "role": "csv"}]}
(output_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
""".strip(),
    )
    job_response = _create_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["error"]["code"] == "runner_artifact_path_outside_output_dir"


def test_runner_blocks_oversized_result_json(client: TestClient) -> None:
    implementation = _create_implementation(client)
    _update_script(
        implementation,
        """
import json
import sys
from pathlib import Path
output_dir = Path(sys.argv[2])
payload = {"schema_version": 1, "status": "succeeded", "outputs": {"blob": "A" * (1024 * 1024 + 1)}, "artifacts": []}
(output_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
""".strip(),
    )
    job_response = _create_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["simulation_run"]["status"] == "failed"
    assert body["error"]["code"] == "runner_output_too_large"


def test_runner_logs_are_bounded_and_marked_truncated(client: TestClient) -> None:
    implementation = _create_implementation(client)
    _update_script(
        implementation,
        """
import json
import sys
from pathlib import Path
print("A" * 70000)
output_dir = Path(sys.argv[2])
(output_dir / "result.json").write_text(json.dumps({"schema_version": 1, "status": "succeeded", "outputs": {}, "artifacts": []}), encoding="utf-8")
""".strip(),
    )
    job_response = _create_job(client, str(implementation["id"]))

    response = client.post(f"/runner-jobs/{job_response['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    logs = client.get(f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/logs").json()
    stdout_log = next(log for log in logs if log["stream"] == "stdout")
    assert stdout_log["truncated"] is True
    assert len(stdout_log["content"].encode("utf-8")) <= 64 * 1024


def test_local_python_executor_does_not_use_shell_or_inherit_secret_env(monkeypatch, tmp_path) -> None:
    from app.modules.runner.local_python import execute_python_script

    monkeypatch.setenv("SCALEWAY_API_KEY", "must-not-be-in-env")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = execute_python_script(
        script_path=tmp_path / "script.py",
        input_file=tmp_path / "input.json",
        output_dir=tmp_path,
        working_dir=tmp_path,
        timeout_seconds=1,
        max_stdout_bytes=100,
        max_stderr_bytes=100,
    )

    kwargs = captured["kwargs"]
    assert kwargs["shell"] is False
    assert kwargs["env"] == {"PYTHONIOENCODING": "utf-8"}
    assert "SCALEWAY_API_KEY" not in json.dumps(result.environment_metadata)
    assert result.stdout == "ok"
