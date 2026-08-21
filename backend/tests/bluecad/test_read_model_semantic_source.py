from __future__ import annotations

import json
import sqlite3

from fastapi.testclient import TestClient

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.main import create_app
from app.modules.bluecad.cad_link import TRANSFORMATION_VERSION, _digest, _verify_model_identity
from app.modules.bluecad.read_model import get_bluecad_candidate_aggregate
from app.modules.runner.service import CALC_V0_IMPLEMENTATION_KIND, register_bundled_bluerev_process0

NOW = "2026-08-21T18:00:00+00:00"


def _seed_parameter(connection: sqlite3.Connection, parameter_id: str, name: str, value: str, unit: str) -> None:
    connection.execute(
        """
        INSERT INTO parameters (
            id, workspace_id, name, value, unit, value_status, status, origin,
            created_at, updated_at
        ) VALUES (?, 'bluerev', ?, ?, ?, 'explicit', 'accepted', 'user', ?, ?)
        """,
        (parameter_id, name, value, unit, NOW, NOW),
    )


def _seed_candidate(connection: sqlite3.Connection, candidate_id: str, *, origin: str = "process_linked") -> None:
    connection.execute(
        """
        INSERT INTO bluecad_candidates (
            id, workspace_id, brief_text, brief_digest, status, parked_reason,
            spec_artifact_id, glb_artifact_id, report_artifact_id,
            promoted_decision_id, origin, parent_candidate_id, loop_config_json,
            created_at, updated_at, notes
        ) VALUES (?, 'bluerev', 'fixture', ?, 'valid', NULL, NULL, NULL, NULL, NULL,
                  ?, NULL, '{}', ?, ?, NULL)
        """,
        (candidate_id, "sha256:" + "a" * 64, origin, NOW, NOW),
    )


def _seed_exact_047_link(candidate_id: str = "candidate-047") -> tuple[str, str]:
    initialize_storage(seed_default=True)
    implementation = register_bundled_bluerev_process0("bluerev")
    run_id = "run-047"
    job_id = "job-047"
    link_id = "link-047"
    snapshot = {
        "tube_length": {
            "parameter_ref": "parameter:p-length",
            "name": "Tube length",
            "executed_value": "12",
            "current_value": "12",
            "unit": "m",
            "status": "accepted",
            "origin": "user",
            "source_ref": None,
            "freshness": "fresh",
        },
        "tube_inner_diameter": {
            "parameter_ref": "parameter:p-inner",
            "name": "Tube inner diameter",
            "executed_value": "80",
            "current_value": "80",
            "unit": "mm",
            "status": "accepted",
            "origin": "user",
            "source_ref": None,
            "freshness": "fresh",
        },
        "tube_outer_diameter": {
            "parameter_ref": "parameter:p-outer",
            "name": "Tube outer diameter",
            "executed_value": "100",
            "current_value": "100",
            "unit": "mm",
            "status": "accepted",
            "origin": "user",
            "source_ref": None,
            "freshness": "fresh",
        },
    }
    with open_sqlite_connection() as connection:
        _seed_parameter(connection, "p-length", "Tube length", "12", "m")
        _seed_parameter(connection, "p-inner", "Tube inner diameter", "80", "mm")
        _seed_parameter(connection, "p-outer", "Tube outer diameter", "100", "mm")
        _seed_candidate(connection, candidate_id)
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status, input_payload,
                parameter_payload, output_payload, created_at
            ) VALUES (?, 'bluerev', ?, 'fixture', 'succeeded', '{}', '{}', '{}', ?)
            """,
            (run_id, implementation.id, NOW),
        )
        connection.execute(
            """
            INSERT INTO runner_jobs (
                id, workspace_id, simulation_run_id, runner_type, status,
                script_path, script_sha256, implementation_kind, working_dir,
                output_dir, timeout_seconds, max_stdout_bytes, max_stderr_bytes,
                max_output_json_bytes, max_artifact_bytes, created_at, updated_at
            ) VALUES (?, 'bluerev', ?, 'python_local', 'succeeded', ?, ?, ?, '/tmp', '/tmp',
                      10, 1024, 1024, 1024, 1024, ?, ?)
            """,
            (
                job_id,
                run_id,
                implementation.script_path,
                implementation.script_sha256,
                CALC_V0_IMPLEMENTATION_KIND,
                NOW,
                NOW,
            ),
        )
        model = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.id = ? AND mv.workspace_id = 'bluerev'
            """,
            (implementation.id,),
        ).fetchone()
        job = connection.execute("SELECT * FROM runner_jobs WHERE id = ?", (job_id,)).fetchone()
        assert model is not None and job is not None
        identity = _verify_model_identity(model, job)
        connection.execute(
            """
            INSERT INTO bluecad_cad_links (
                id, workspace_id, source_simulation_run_id, source_runner_job_id,
                child_candidate_id, transformation_version, source_snapshot_json,
                source_snapshot_digest, source_model_identity_json,
                source_model_identity_digest, analysis_contract_digest, preview_digest,
                resolved_spec_digest, reconciliation_json, reconciliation_digest, created_at
            ) VALUES (?, 'bluerev', ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, '{}', ?, ?)
            """,
            (
                link_id,
                run_id,
                job_id,
                candidate_id,
                TRANSFORMATION_VERSION,
                json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
                _digest(snapshot),
                json.dumps(identity, sort_keys=True, separators=(",", ":")),
                _digest(identity),
                "sha256:" + "b" * 64,
                "sha256:" + "c" * 64,
                "sha256:" + "d" * 64,
                NOW,
            ),
        )
        connection.commit()
    return candidate_id, link_id


def test_exact_047_child_projects_bounded_immutable_semantic_source() -> None:
    candidate_id, link_id = _seed_exact_047_link()

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)

    assert aggregate is not None
    assert aggregate.semantic_source is not None
    assert aggregate.semantic_source.kind == "cad_link_047_m0"
    assert aggregate.semantic_source.link_id == link_id
    assert aggregate.semantic_source.transformation_version == TRANSFORMATION_VERSION
    assert aggregate.semantic_source.source_simulation_run_id == "run-047"
    assert aggregate.semantic_source.source_runner_job_id == "job-047"
    assert [(item.name, item.value, item.unit, item.source_parameter_id) for item in aggregate.semantic_source.bindings] == [
        ("tube_length", "12", "m", "p-length"),
        ("tube_inner_diameter", "80", "mm", "p-inner"),
        ("tube_outer_diameter", "100", "mm", "p-outer"),
    ]

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET value = '13', status = 'superseded' WHERE id = 'p-length'")
        connection.commit()
    reread = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert reread is not None and reread.semantic_source is not None
    assert reread.semantic_source.bindings[0].value == "12"


def test_nonlinked_and_wrong_transformation_candidates_do_not_gain_reviewed_047_semantics() -> None:
    _seed_exact_047_link()
    with open_sqlite_connection() as connection:
        _seed_candidate(connection, "candidate-ordinary", origin="ai")
        connection.execute(
            "UPDATE bluecad_cad_links SET transformation_version = 'bluerev_072_topology_v0' WHERE id = 'link-047'"
        )
        connection.commit()

    ordinary = get_bluecad_candidate_aggregate("bluerev", "candidate-ordinary")
    wrong_transform = get_bluecad_candidate_aggregate("bluerev", "candidate-047")
    assert ordinary is not None and ordinary.semantic_source is None
    assert wrong_transform is not None and wrong_transform.semantic_source is None


def test_malformed_snapshot_fails_closed_and_api_exposes_no_semantic_source() -> None:
    candidate_id, _link_id = _seed_exact_047_link()
    with open_sqlite_connection() as connection:
        connection.execute("UPDATE bluecad_cad_links SET source_snapshot_json = '{}' WHERE id = 'link-047'")
        connection.commit()

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert aggregate is not None
    assert aggregate.semantic_source is None
    assert any(item.source == "bluecad.semantic_source" for item in aggregate.diagnostics)

    response = TestClient(create_app()).get(f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/aggregate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["semantic_source"] is None
    assert any(item["source"] == "bluecad.semantic_source" for item in payload["diagnostics"])
