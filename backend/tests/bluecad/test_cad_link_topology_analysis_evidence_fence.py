from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.bluecad.evidence import map_mesh_quality_evidence
from app.modules.events.service import utc_now


@pytest.fixture
def initialized_storage(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv(
        "DATABASE_URL",
        "must-not-enter-cad-link-074-analysis-evidence-fence",
    )
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)
    yield
    get_settings.cache_clear()


def _seed_analysis_owner(*, candidate_status: str, run_status: str) -> tuple[str, str, str]:
    candidate_id = str(uuid4())
    attempt_id = str(uuid4())
    run_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'analysis evidence fence probe', ?, ?,
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'analysis evidence fence probe')
            """,
            (candidate_id, "sha256:" + "b" * 64, candidate_status, now, now),
        )
        connection.execute(
            """
            INSERT INTO bluecad_attempts (
                id, candidate_id, attempt_no, route_class,
                proposal_ai_job_id, proposal_outcome, build_outcome,
                validation_verdict, spec_artifact_id, report_artifact_id,
                manifest_artifact_id, started_at, finished_at, error_detail_json
            ) VALUES (?, ?, 1, 'deterministic:cad_link:072', NULL,
                'not_applicable', 'ok', 'pass', NULL, NULL, NULL, ?, ?, '{}')
            """,
            (attempt_id, candidate_id, now, now),
        )
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload,
                started_at, completed_at, created_at, notes
            ) VALUES (?, 'bluerev', NULL, ?, ?, ?, '{}', ?, ?, ?, ?,
                'analysis evidence fence probe')
            """,
            (
                run_id,
                f"bluecad_attempt_{attempt_id}",
                run_status,
                json.dumps(
                    {"candidate_id": candidate_id, "attempt_id": attempt_id},
                    sort_keys=True,
                ),
                json.dumps({"status": run_status})
                if run_status in {"completed", "failed"}
                else None,
                now,
                now if run_status in {"completed", "failed"} else None,
                now,
            ),
        )
        connection.commit()
    return candidate_id, attempt_id, run_id


def _mesh_result() -> dict[str, object]:
    return {
        "schema_version": "bluecad_mesh_result_v0_1",
        "verdict": "error",
        "errors": [],
        "attempts": [
            {
                "attempt_no": 1,
                "target_size": 10.0,
                "counts": {},
                "errors": [],
            }
        ],
        "artifacts": {},
    }


def _persist(
    *,
    candidate_id: str,
    attempt_id: str,
    run_id: str,
    report_path: Path,
) -> tuple[str, str]:
    import app.modules.bluecad.loop as loop_module

    result = _mesh_result()
    return loop_module._persist_sim_evidence(
        "bluerev",
        candidate_id,
        attempt_id,
        run_id,
        report_path,
        result,
        f"bluecad_candidate:{candidate_id}:attempt:1:sim:{run_id}",
        evidence_builder=lambda artifact_id: map_mesh_quality_evidence(
            "bluerev",
            result,
            source_run_id=run_id,
            report_artifact_id=artifact_id,
        ),
        producer_notes="Spec 074 analysis evidence fence test.",
        required_candidate_status="validating",
    )


def test_recovered_analysis_owner_cannot_persist_late_artifact_or_evidence(
    initialized_storage,
    tmp_path,
) -> None:
    candidate_id, attempt_id, run_id = _seed_analysis_owner(
        candidate_status="parked",
        run_status="failed",
    )

    with pytest.raises(RuntimeError, match="no longer owns evidence persistence"):
        _persist(
            candidate_id=candidate_id,
            attempt_id=attempt_id,
            run_id=run_id,
            report_path=tmp_path / "mesh_result.json",
        )

    with open_sqlite_connection() as connection:
        artifact_count = connection.execute(
            "SELECT COUNT(*) FROM artifacts WHERE workspace_id = 'bluerev'"
        ).fetchone()[0]
        evidence_count = connection.execute(
            "SELECT COUNT(*) FROM evidence_records WHERE source_run_id = ?",
            (run_id,),
        ).fetchone()[0]
    assert artifact_count == 0
    assert evidence_count == 0
    artifact_root = build_paths().artifacts_dir / "bluerev" / "bluecad"
    assert not artifact_root.exists() or not any(artifact_root.rglob("*"))


def test_live_analysis_owner_persists_artifact_and_evidence_atomically(
    initialized_storage,
    tmp_path,
) -> None:
    candidate_id, attempt_id, run_id = _seed_analysis_owner(
        candidate_status="validating",
        run_status="running",
    )

    artifact_id, evidence_id = _persist(
        candidate_id=candidate_id,
        attempt_id=attempt_id,
        run_id=run_id,
        report_path=tmp_path / "mesh_result.json",
    )

    with open_sqlite_connection() as connection:
        artifact = connection.execute(
            "SELECT * FROM artifacts WHERE id = ?",
            (artifact_id,),
        ).fetchone()
        evidence = connection.execute(
            "SELECT * FROM evidence_records WHERE id = ?",
            (evidence_id,),
        ).fetchone()
    assert artifact is not None
    assert artifact["artifact_type"] == "bluecad_sim_report"
    assert evidence is not None
    assert evidence["source_run_id"] == run_id
    assert evidence["candidate_id"] == candidate_id
    assert evidence["attempt_id"] == attempt_id
    assert evidence["report_artifact_id"] == artifact_id
