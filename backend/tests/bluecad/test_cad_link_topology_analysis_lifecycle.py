from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.database import open_sqlite_connection
from app.modules.events.service import utc_now


@pytest.fixture
def initialized_storage(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-cad-link-074-analysis-lifecycle")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage

    initialize_storage(seed_default=True)
    yield
    get_settings.cache_clear()


def _seed_candidate(
    *,
    status: str,
    updated_at: str | None = None,
    attempt_finished: bool = True,
) -> tuple[str, str]:
    candidate_id = str(uuid4())
    attempt_id = str(uuid4())
    timestamp = updated_at or utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status,
                parked_reason, spec_artifact_id, glb_artifact_id,
                report_artifact_id, promoted_decision_id, origin,
                parent_candidate_id, loop_config_json, created_at,
                updated_at, notes
            ) VALUES (?, 'bluerev', 'analysis lifecycle probe', ?, ?,
                NULL, NULL, NULL, NULL, NULL, 'process_linked', NULL,
                '{}', ?, ?, 'analysis lifecycle probe')
            """,
            (
                candidate_id,
                "sha256:" + "8" * 64,
                status,
                timestamp,
                timestamp,
            ),
        )
        connection.execute(
            """
            INSERT INTO bluecad_attempts (
                id, candidate_id, attempt_no, route_class,
                proposal_ai_job_id, proposal_outcome, build_outcome,
                validation_verdict, spec_artifact_id, report_artifact_id,
                manifest_artifact_id, started_at, finished_at, error_detail_json
            ) VALUES (?, ?, 1, 'deterministic:cad_link:072', NULL,
                'not_applicable', 'ok', 'pass', NULL, NULL, NULL, ?, ?, ?)
            """,
            (
                attempt_id,
                candidate_id,
                timestamp,
                timestamp if attempt_finished else None,
                json.dumps({"preview_digest": "sha256:" + "9" * 64}),
            ),
        )
        connection.commit()
    return candidate_id, attempt_id


def _insert_analysis_run(
    *,
    attempt_id: str,
    status: str,
) -> str:
    run_id = str(uuid4())
    now = utc_now()
    terminal = status in {"completed", "failed"}
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload,
                started_at, completed_at, created_at, notes
            ) VALUES (?, 'bluerev', NULL, ?, ?, '{}', '{}', ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                f"bluecad_attempt_{attempt_id}",
                status,
                json.dumps({"status": status}) if terminal else None,
                now,
                now if terminal else None,
                now,
                "Spec 074 analysis lifecycle probe.",
            ),
        )
        connection.commit()
    return run_id


def test_replay_waits_through_validating_until_terminal(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id, _attempt_id = _seed_candidate(status="validating")
    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 1.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.01)

    def complete_candidate() -> None:
        time.sleep(0.1)
        with open_sqlite_connection() as connection:
            connection.execute(
                "UPDATE bluecad_candidates SET status = 'valid', updated_at = ? WHERE id = ?",
                (utc_now(), candidate_id),
            )
            connection.commit()

    worker = threading.Thread(target=complete_candidate)
    worker.start()
    started = time.monotonic()
    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)
    worker.join()

    assert time.monotonic() - started >= 0.08
    assert candidate.status == "valid"


def test_abandoned_validating_candidate_is_parked_without_losing_attempt_outcomes(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    old = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    candidate_id, attempt_id = _seed_candidate(
        status="validating",
        updated_at=old,
    )
    run_id = _insert_analysis_run(attempt_id=attempt_id, status="running")
    monkeypatch.setattr(execute_module, "_REPLAY_WAIT_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_REPLAY_POLL_SECONDS", 0.0)
    monkeypatch.setattr(execute_module, "_ABANDONED_RESERVATION_SECONDS", 1.0)

    candidate = execute_module._wait_for_replay_candidate("bluerev", candidate_id)

    assert candidate.status == "parked"
    assert candidate.parked_reason == "cad_link_failed"
    assert candidate.notes is not None
    assert "cad_link_abandoned_post_validation" in candidate.notes
    with open_sqlite_connection() as connection:
        attempt = connection.execute(
            "SELECT * FROM bluecad_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        analysis_run = connection.execute(
            "SELECT * FROM simulation_runs WHERE id = ?", (run_id,)
        ).fetchone()
    assert attempt is not None
    assert attempt["build_outcome"] == "ok"
    assert attempt["validation_verdict"] == "pass"
    details = json.loads(attempt["error_detail_json"])
    assert details["preview_digest"] == "sha256:" + "9" * 64
    assert details["reason"] == "post_validation_lease_expired"
    assert analysis_run is not None
    assert analysis_run["status"] == "failed"
    assert analysis_run["completed_at"] is not None


def test_candidate_becomes_valid_only_after_terminal_requested_analysis(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id, attempt_id = _seed_candidate(status="validating")
    observed_statuses: list[str] = []

    def complete_analysis(
        workspace_id: str,
        current_candidate_id: str,
        current_attempt_id: str,
        attempt_no: int,
        analysis_spec: dict[str, object] | None,
        build: dict[str, object],
        *,
        producer_notes: str | None = None,
        required_candidate_status: str | None = None,
    ) -> None:
        del (
            workspace_id,
            attempt_no,
            analysis_spec,
            build,
            producer_notes,
            required_candidate_status,
        )
        with open_sqlite_connection() as connection:
            row = connection.execute(
                "SELECT status FROM bluecad_candidates WHERE id = ?",
                (current_candidate_id,),
            ).fetchone()
        assert row is not None
        observed_statuses.append(str(row["status"]))
        _insert_analysis_run(attempt_id=current_attempt_id, status="completed")

    monkeypatch.setattr(execute_module, "_run_simulation_stage", complete_analysis)

    execute_module._complete_valid_candidate_after_analysis(
        "bluerev",
        candidate_id,
        attempt_id,
        {"schema_version": "probe"},
        {},
    )

    assert observed_statuses == ["validating"]
    with open_sqlite_connection() as connection:
        status = connection.execute(
            "SELECT status FROM bluecad_candidates WHERE id = ?", (candidate_id,)
        ).fetchone()["status"]
    assert status == "valid"


def test_missing_terminal_analysis_evidence_cannot_produce_valid_candidate(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    candidate_id, attempt_id = _seed_candidate(status="validating")
    monkeypatch.setattr(execute_module, "_run_simulation_stage", lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match="exactly one terminal run"):
        execute_module._complete_valid_candidate_after_analysis(
            "bluerev",
            candidate_id,
            attempt_id,
            {"schema_version": "probe"},
            {},
        )

    with open_sqlite_connection() as connection:
        status = connection.execute(
            "SELECT status FROM bluecad_candidates WHERE id = ?", (candidate_id,)
        ).fetchone()["status"]
    assert status == "validating"


def test_recovery_fences_late_analysis_creation_and_completion(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module
    import app.modules.bluecad.loop as loop_module

    old = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    candidate_id, attempt_id = _seed_candidate(
        status="validating",
        updated_at=old,
    )
    run_id = _insert_analysis_run(attempt_id=attempt_id, status="running")
    monkeypatch.setattr(execute_module, "_ABANDONED_RESERVATION_SECONDS", 1.0)

    recovered = execute_module._recover_abandoned_reservation(
        "bluerev",
        candidate_id,
    )
    assert recovered is not None and recovered.status == "parked"

    loop_module._complete_simulation_run(
        run_id,
        {"verdict": "pass"},
        {"verdict": "pass"},
    )
    with pytest.raises(RuntimeError, match="no longer owns"):
        loop_module._create_simulation_run(
            "bluerev",
            candidate_id,
            attempt_id,
            {"schema_version": "probe"},
            required_candidate_status="validating",
        )

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT id, status, output_payload FROM simulation_runs WHERE run_label = ?",
            (f"bluecad_attempt_{attempt_id}",),
        ).fetchall()
        candidate_status = connection.execute(
            "SELECT status FROM bluecad_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()["status"]
    assert len(rows) == 1
    assert rows[0]["id"] == run_id
    assert rows[0]["status"] == "failed"
    assert json.loads(rows[0]["output_payload"])["error"]["code"] == (
        "cad_link_analysis_lease_expired"
    )
    assert candidate_status == "parked"


# Regression: a recovered terminal candidate must surface as ownership loss,
# not as a missing-analysis 500 path.
def test_recovery_before_analysis_creation_preserves_ownership_loss(
    initialized_storage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.modules.bluecad.cad_link_topology_execute as execute_module

    old = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    candidate_id, attempt_id = _seed_candidate(
        status="validating",
        updated_at=old,
    )
    monkeypatch.setattr(execute_module, "_ABANDONED_RESERVATION_SECONDS", 1.0)
    recovered = execute_module._recover_abandoned_reservation(
        "bluerev",
        candidate_id,
    )
    assert recovered is not None and recovered.status == "parked"
    monkeypatch.setattr(
        execute_module,
        "_run_simulation_stage",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(execute_module._ReservationOwnershipLost):
        execute_module._complete_valid_candidate_after_analysis(
            "bluerev",
            candidate_id,
            attempt_id,
            {"schema_version": "probe"},
            {},
        )
