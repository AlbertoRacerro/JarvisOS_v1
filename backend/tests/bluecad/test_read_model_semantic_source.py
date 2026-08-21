from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable

from fastapi.testclient import TestClient

from app.core.bootstrap import initialize_storage
from app.core.database import open_sqlite_connection
from app.main import create_app
from app.modules.bluecad.cad_link import TRANSFORMATION_VERSION, _digest, _verify_model_identity
from app.modules.bluecad.read_model import (
    BluecadReadDiagnostic,
    _semantic_source_diagnostic,
    get_bluecad_candidate_aggregate,
)
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


def _seed_exact_047_link(candidate_id: str = "candidate-047") -> tuple[str, str, dict[str, dict[str, Any]]]:
    initialize_storage(seed_default=True)
    implementation = register_bundled_bluerev_process0("bluerev")
    run_id = "run-047"
    job_id = "job-047"
    link_id = "link-047"
    snapshot: dict[str, dict[str, Any]] = {
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
    return candidate_id, link_id, snapshot


def _rewrite_snapshot(mutator: Callable[[dict[str, dict[str, Any]]], None]) -> None:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT source_snapshot_json FROM bluecad_cad_links WHERE id = 'link-047'"
        ).fetchone()
        assert row is not None
        snapshot = json.loads(str(row["source_snapshot_json"]))
        mutator(snapshot)
        connection.execute(
            """
            UPDATE bluecad_cad_links
            SET source_snapshot_json = ?, source_snapshot_digest = ?
            WHERE id = 'link-047'
            """,
            (
                json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
                _digest(snapshot),
            ),
        )
        connection.commit()


def _semantic_diagnostics(candidate_id: str) -> list[dict[str, Any]]:
    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert aggregate is not None
    return [
        item.model_dump()
        for item in aggregate.diagnostics
        if item.source == "bluecad.semantic_source"
    ]


def test_exact_047_child_projects_exact_bounded_immutable_semantic_source() -> None:
    candidate_id, _link_id, snapshot = _seed_exact_047_link()

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)

    assert aggregate is not None
    assert aggregate.semantic_source is not None
    expected = {
        "schema_version": 1,
        "kind": "cad_link_047_m0",
        "transformation_version": TRANSFORMATION_VERSION,
        "source_simulation_run_id": "run-047",
        "source_model_version_id": aggregate.semantic_source.source_model_version_id,
        "geometry_bindings": {
            name: {
                "value": float(item["executed_value"]),
                "unit": item["unit"],
                "source_parameter_id": str(item["parameter_ref"]).removeprefix("parameter:"),
            }
            for name, item in snapshot.items()
        },
    }
    assert aggregate.semantic_source.model_dump() == expected
    assert set(aggregate.semantic_source.model_dump()) == {
        "schema_version",
        "kind",
        "transformation_version",
        "source_simulation_run_id",
        "source_model_version_id",
        "geometry_bindings",
    }

    response = TestClient(create_app()).get(f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/aggregate")
    assert response.status_code == 200
    assert response.json()["semantic_source"] == expected

    with open_sqlite_connection() as connection:
        connection.execute("UPDATE parameters SET value = '13', status = 'superseded' WHERE id = 'p-length'")
        connection.commit()
    reread = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert reread is not None and reread.semantic_source is not None
    assert reread.semantic_source.geometry_bindings["tube_length"].value == float(
        snapshot["tube_length"]["executed_value"]
    )


def test_nonlinked_and_wrong_transformation_candidates_remain_limited_without_diagnostic() -> None:
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
    assert not [item for item in ordinary.diagnostics if item.source == "bluecad.semantic_source"]
    assert not [item for item in wrong_transform.diagnostics if item.source == "bluecad.semantic_source"]


def test_missing_canonical_parameter_uses_exact_missing_diagnostic() -> None:
    candidate_id, _link_id, _snapshot = _seed_exact_047_link()
    _rewrite_snapshot(lambda snapshot: snapshot["tube_length"].__setitem__("parameter_ref", "parameter:missing"))

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert aggregate is not None and aggregate.semantic_source is None
    assert _semantic_diagnostics(candidate_id) == [
        {
            "code": "missing_reference",
            "source": "bluecad.semantic_source",
            "reference": f"bluecad_candidate:{candidate_id}",
            "message": "Reviewed-047 semantic source references a missing canonical record.",
        }
    ]


def test_nonfinite_snapshot_value_uses_exact_malformed_diagnostic() -> None:
    candidate_id, _link_id, _snapshot = _seed_exact_047_link()

    def make_nonfinite(snapshot: dict[str, dict[str, Any]]) -> None:
        snapshot["tube_length"]["executed_value"] = "NaN"
        snapshot["tube_length"]["current_value"] = "NaN"

    _rewrite_snapshot(make_nonfinite)

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert aggregate is not None and aggregate.semantic_source is None
    assert _semantic_diagnostics(candidate_id) == [
        {
            "code": "malformed_reference",
            "source": "bluecad.semantic_source",
            "reference": f"bluecad_candidate:{candidate_id}",
            "message": "Reviewed-047 semantic source provenance is malformed or ambiguous.",
        }
    ]


def test_semantic_diagnostic_precedence_and_payload_are_deterministic() -> None:
    diagnostics: list[BluecadReadDiagnostic] = []
    _semantic_source_diagnostic(
        diagnostics,
        "candidate-047",
        {"malformed_reference", "missing_reference", "inaccessible_reference"},
    )
    assert [item.model_dump() for item in diagnostics] == [
        {
            "code": "inaccessible_reference",
            "source": "bluecad.semantic_source",
            "reference": "bluecad_candidate:candidate-047",
            "message": "Reviewed-047 semantic source references data inaccessible in this workspace.",
        }
    ]


def test_malformed_snapshot_fails_closed_and_api_exposes_no_semantic_source() -> None:
    candidate_id, _link_id, _snapshot = _seed_exact_047_link()
    with open_sqlite_connection() as connection:
        connection.execute("UPDATE bluecad_cad_links SET source_snapshot_json = '{}' WHERE id = 'link-047'")
        connection.commit()

    aggregate = get_bluecad_candidate_aggregate("bluerev", candidate_id)
    assert aggregate is not None
    assert aggregate.semantic_source is None
    assert _semantic_diagnostics(candidate_id) == [
        {
            "code": "malformed_reference",
            "source": "bluecad.semantic_source",
            "reference": f"bluecad_candidate:{candidate_id}",
            "message": "Reviewed-047 semantic source provenance is malformed or ambiguous.",
        }
    ]

    response = TestClient(create_app()).get(f"/workspaces/bluerev/bluecad/candidates/{candidate_id}/aggregate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["semantic_source"] is None
    assert [item for item in payload["diagnostics"] if item["source"] == "bluecad.semantic_source"] == [
        {
            "code": "malformed_reference",
            "source": "bluecad.semantic_source",
            "reference": f"bluecad_candidate:{candidate_id}",
            "message": "Reviewed-047 semantic source provenance is malformed or ambiguous.",
        }
    ]
