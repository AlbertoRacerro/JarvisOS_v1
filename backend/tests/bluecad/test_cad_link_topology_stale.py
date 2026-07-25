from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-stale")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _create_parameter(
    client: TestClient,
    *,
    name: str,
    value: str,
    status: str,
    supersedes_parameter_id: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "name": name,
        "value": value,
        "unit": "m",
        "value_status": "accepted" if status == "accepted" else "candidate",
        "status": status,
    }
    if supersedes_parameter_id is not None:
        payload["supersedes_parameter_id"] = supersedes_parameter_id
    response = client.post("/workspaces/bluerev/parameters", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_parameter_replacement_marks_m1_linked_candidate_stale(
    client: TestClient,
) -> None:
    old_parameter_id = _create_parameter(
        client,
        name="Accepted branch length",
        value="0.5",
        status="accepted",
    )
    replacement_parameter_id = _create_parameter(
        client,
        name="Corrected branch length",
        value="0.6",
        status="proposed",
        supersedes_parameter_id=old_parameter_id,
    )
    model_spec_id = str(uuid4())
    implementation_artifact_id = str(uuid4())
    model_version_id = str(uuid4())
    simulation_run_id = str(uuid4())
    runner_job_id = str(uuid4())
    candidate_id = str(uuid4())
    link_id = str(uuid4())
    now = utc_now()
    input_payload = {
        "branch_illuminated_straight_length": {
            "value": 0.5,
            "unit": "m",
            "source_parameter_id": old_parameter_id,
        }
    }
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO model_specs (
                id, workspace_id, title, engineering_question, created_at, updated_at
            ) VALUES (?, 'bluerev', '074 stale fixture', 'Trace M1 stale propagation', ?, ?)
            """,
            (model_spec_id, now, now),
        )
        connection.execute(
            """
            INSERT INTO artifacts (
                id, workspace_id, filename, stored_path, artifact_type, mime_type,
                sha256, status, created_at
            ) VALUES (?, 'bluerev', 'topology.py', '/private/topology.py',
                'python_script', 'text/x-python', ?, 'registered', ?)
            """,
            (implementation_artifact_id, "1" * 64, now),
        )
        connection.execute(
            """
            INSERT INTO model_versions (
                id, workspace_id, model_spec_id, version_label,
                implementation_artifact_id, implementation_kind, status, created_at
            ) VALUES (?, 'bluerev', ?, '074-stale-v0', ?, 'calc_v0', 'ready', ?)
            """,
            (model_version_id, model_spec_id, implementation_artifact_id, now),
        )
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, output_payload, created_at, completed_at
            ) VALUES (?, 'bluerev', ?, '074 stale fixture run', 'succeeded', ?, '{}', ?, ?)
            """,
            (simulation_run_id, model_version_id, json.dumps(input_payload), now, now),
        )
        connection.execute(
            """
            INSERT INTO runner_jobs (
                id, workspace_id, simulation_run_id, runner_type, status,
                script_path, script_sha256, implementation_kind, working_dir,
                input_file, output_dir, timeout_seconds, max_stdout_bytes,
                max_stderr_bytes, max_output_json_bytes, max_artifact_bytes,
                created_at, updated_at
            ) VALUES (?, 'bluerev', ?, 'python_local', 'succeeded',
                '/private/topology.py', ?, 'calc_v0', '/private/work',
                '/private/input.json', '/private/output', 30, 1000, 1000,
                1000, 1000, ?, ?)
            """,
            (runner_job_id, simulation_run_id, "1" * 64, now, now),
        )
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at, updated_at, notes
            ) VALUES (?, 'bluerev', '074 stale linked candidate', ?, 'valid',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'M1 topology candidate')
            """,
            (candidate_id, "sha256:" + "2" * 64, now, now),
        )
        connection.execute(
            """
            INSERT INTO bluecad_cad_links (
                id, workspace_id, source_simulation_run_id,
                source_runner_job_id, child_candidate_id,
                transformation_version, source_snapshot_json,
                source_snapshot_digest, source_model_identity_json,
                source_model_identity_digest, analysis_contract_digest,
                preview_digest, resolved_spec_digest, reconciliation_json,
                reconciliation_digest, created_at
            ) VALUES (?, 'bluerev', ?, ?, ?,
                'bluerev_072_m1_planar_tubing_v0_1', '{}', ?, '{}', ?, NULL,
                ?, ?, '{}', ?, ?)
            """,
            (
                link_id,
                simulation_run_id,
                runner_job_id,
                candidate_id,
                "sha256:" + "3" * 64,
                "sha256:" + "4" * 64,
                "sha256:" + "5" * 64,
                "sha256:" + "6" * 64,
                "sha256:" + "7" * 64,
                now,
            ),
        )
        connection.commit()

    promoted = client.post(
        f"/memory/parameter/{replacement_parameter_id}/promote-replacement"
    )
    assert promoted.status_code == 200, promoted.text

    freshness = client.get(
        f"/workspaces/bluerev/flowsheet/nodes/bluecad_candidate:{candidate_id}/freshness"
    )
    assert freshness.status_code == 200, freshness.text
    body = freshness.json()
    assert body["state"] == "stale"
    assert body["latest_invalidation"]["path"] == [
        f"parameter:{old_parameter_id}",
        f"simulation_run:{simulation_run_id}",
        f"bluecad_candidate:{candidate_id}",
    ]

    with open_sqlite_connection() as connection:
        candidate = connection.execute(
            "SELECT status FROM bluecad_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        assert candidate is not None
        assert candidate["status"] == "valid"
