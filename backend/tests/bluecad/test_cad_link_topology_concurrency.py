from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

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
    assert candidate.notes is not None
    assert "cad_link_abandoned_reservation" in candidate.notes
    with open_sqlite_connection() as connection:
        attempt = connection.execute(
            "SELECT * FROM bluecad_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        assert attempt is not None
        assert attempt["build_outcome"] == "cad_link_abandoned"
        assert attempt["validation_verdict"] == "fail"
        assert attempt["finished_at"] is not None
        details = json.loads(attempt["error_detail_json"])
        assert details["reason"] == "reservation_lease_expired"


def _analysis_spec(timeout_s: float | None = None) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "schema_version": "bluecad_analysis_spec_v0_1",
        "analysis_id": "replay-wait-probe",
        "analysis_type": "static",
        "material": {
            "name": "Steel",
            "E": 210e9,
            "nu": 0.3,
            "rho": 7850.0,
            "yield_strength": 250e6,
        },
        "bcs": [{"port_label": "part.fixed", "kind": "fixed"}],
        "loads": [
            {
                "port_label": "part.loaded",
                "type": "force_total",
                "force": [1.0, 0.0, 0.0],
            }
        ],
        "mesh": {"target_size": 10.0, "element_order": 1},
        "pass_criteria": [],
    }
    if timeout_s is not None:
        spec["timeout_s"] = timeout_s
    return spec


def test_replay_wait_covers_bounded_optional_analysis() -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    expected_default = (
        execute_module.BUILD_TIMEOUT_SECONDS
        + 2 * 60.0
        + 60.0
        + 30.0
    )
    expected_custom = (
        execute_module.BUILD_TIMEOUT_SECONDS
        + 2 * 60.0
        + 300.0
        + 30.0
    )

    assert execute_module._replay_wait_seconds({"analysis_contract": None}) == (
        execute_module._REPLAY_WAIT_SECONDS
    )
    assert execute_module._replay_wait_seconds(
        {"analysis_contract": _analysis_spec()}
    ) == expected_default
    assert execute_module._replay_wait_seconds(
        {"analysis_contract": _analysis_spec(300.0)}
    ) == expected_custom


def test_analysis_timeout_is_bounded_for_replay_contract() -> None:
    from app.modules.bluecad.models import BluecadLoopConfig

    assert BluecadLoopConfig(analysis_spec=_analysis_spec(300.0)).analysis_spec is not None
    with pytest.raises(ValidationError):
        BluecadLoopConfig(analysis_spec=_analysis_spec(300.0001))
