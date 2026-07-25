from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.core.database import open_sqlite_connection
from app.modules.bluecad.cad_link import CadLinkError
from app.modules.events.service import utc_now


@pytest.fixture
def initialized_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-concurrency")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)
    yield
    get_settings.cache_clear()


def test_stuck_concurrent_reservation_fails_bounded(
    initialized_storage,
    monkeypatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id = str(uuid4())
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
            ) VALUES (?, 'bluerev', 'stuck concurrency probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'stuck concurrency probe')
            """,
            (candidate_id, "sha256:" + "2" * 64, now, now),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.0)

    with pytest.raises(CadLinkError) as exc_info:
        execute_module._wait_for_replay_candidate("bluerev", candidate_id)

    assert exc_info.value.code == "cad_link_execution_in_progress"
    assert exc_info.value.status_code == 409
    with open_sqlite_connection() as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM bluecad_candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()[0]
            == 1
        )


def test_lock_contention_replays_the_winning_reservation(monkeypatch) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    preview_digest = "sha256:" + "4" * 64
    payload = execute_module.CadLink072ExecuteRequest(
        source_simulation_run_id="run-lock-probe",
        layout_spec={},
        analysis_spec=None,
        preview_digest=preview_digest,
    )
    monkeypatch.setattr(
        execute_module,
        "_preview_for_execute",
        lambda *_args: {"preview_digest": preview_digest},
    )
    existing_rows = iter([None, {"id": "winning-link"}])
    monkeypatch.setattr(
        execute_module,
        "_load_existing_link",
        lambda *_args: next(existing_rows),
    )
    sentinel = object()
    monkeypatch.setattr(
        execute_module,
        "_replay_response",
        lambda *_args: sentinel,
    )

    class LockedConnection:
        def execute(self, statement: str, *_args: Any):
            assert statement == "BEGIN IMMEDIATE"
            raise execute_module.sqlite3.OperationalError("database is locked")

    @contextmanager
    def locked_connection():
        yield LockedConnection()

    monkeypatch.setattr(execute_module, "open_sqlite_connection", locked_connection)

    assert execute_module.execute_cad_link_072("bluerev", payload) is sentinel


def test_abandoned_reservation_is_parked_and_attempt_is_finished(
    initialized_storage,
    monkeypatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id = str(uuid4())
    attempt_id = str(uuid4())
    old = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'abandoned reservation probe', ?, 'generating',
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'abandoned reservation probe')
            """,
            (candidate_id, "sha256:" + "5" * 64, old, old),
        )
        connection.execute(
            """
            INSERT INTO bluecad_attempts (
                id, candidate_id, attempt_no, route_class,
                proposal_ai_job_id, proposal_outcome, build_outcome,
                validation_verdict, spec_artifact_id, report_artifact_id,
                manifest_artifact_id, started_at, finished_at, error_detail_json
            ) VALUES (?, ?, 1, 'deterministic:cad_link:072', NULL,
                'not_applicable', NULL, NULL, NULL, NULL, NULL, ?, NULL, NULL)
            """,
            (attempt_id, candidate_id, old),
        )
        connection.commit()

    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_ABANDONED_RESERVATION_SECONDS", 1.0)

    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)

    assert candidate.status == "parked"
    assert candidate.parked_reason == "cad_link_failed"
    with open_sqlite_connection() as connection:
        attempt = connection.execute("SELECT * FROM bluecad_attempts WHERE id = ?", (attempt_id,)).fetchone()
        assert attempt is not None
        assert attempt["build_outcome"] == "cad_link_abandoned"
        assert attempt["validation_verdict"] == "fail"
        assert attempt["finished_at"] is not None
