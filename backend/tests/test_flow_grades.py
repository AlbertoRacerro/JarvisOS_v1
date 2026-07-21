from __future__ import annotations

import pytest
import test_token_flow_local_runtime_integration as local
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.cad_link_schema import CAD_LINK_SCHEMA_MIGRATION_RECORD
from app.core.database import get_current_schema_migration, open_sqlite_connection
from app.core.grade_schema import GRADE_SCHEMA_MIGRATION_ID
from app.modules.ai.execution import run_ai_task
from app.modules.ai.flow_grade_contracts import FlowGradeConflictError
from app.modules.ai.flow_grade_events import set_flow_grade, withdraw_flow_grade
from app.modules.ai.flow_grade_read import get_flow_grade_state
from app.modules.ai.routes import router

initialized_database = local.initialized_database


def _complete_local_flow() -> str:
    adapter = local._SequenceAdapter(local._ResponseSpec("gradeable answer", "stop"))
    outcome = run_ai_task(
        user_prompt="Produce one gradeable answer.",
        task_kind="synthesis",
        route_class="local:sequence",
        max_output_tokens=64,
        adapters={"sequence": adapter},
        bindings={"local:sequence": local._binding()},
    )
    assert outcome.status == "success"
    assert outcome.flow_id is not None
    return str(outcome.flow_id)


def test_grade_schema_remains_applied_and_required(initialized_database) -> None:
    migration = get_current_schema_migration()
    assert migration.migration_id == CAD_LINK_SCHEMA_MIGRATION_RECORD["migration_id"]
    with open_sqlite_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        grade_migration = connection.execute(
            "SELECT status FROM schema_migrations WHERE migration_id = ?",
            (GRADE_SCHEMA_MIGRATION_ID,),
        ).fetchone()
    assert grade_migration is not None
    assert grade_migration["status"] == "applied"
    assert {"ai_flow_grade_subjects", "ai_flow_grade_events"} <= tables


def test_terminal_flow_creates_immutable_grade_subject(initialized_database) -> None:
    flow_id = _complete_local_flow()
    state = get_flow_grade_state(flow_id)

    assert state["current_grade_event"] is None
    assert state["history"] == []
    subject = state["subject"]
    assert subject["flow_id"] == flow_id
    assert subject["subject_version"] == 1
    assert str(subject["flow_outcome_digest"]).startswith("sha256:")
    assert str(subject["final_accounting_digest"]).startswith("sha256:")
    assert str(subject["final_output_digest"]).startswith("sha256:")

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT id, subject_payload_json FROM ai_flow_grade_subjects WHERE flow_id = ?",
            (flow_id,),
        ).fetchall()
    assert len(rows) == 1
    assert "gradeable answer" not in rows[0]["subject_payload_json"]


def test_set_replay_revise_and_withdraw_are_append_only(initialized_database) -> None:
    flow_id = _complete_local_flow()
    subject = get_flow_grade_state(flow_id)["subject"]
    common = {
        "flow_id": flow_id,
        "expected_subject_version": int(subject["subject_version"]),
        "expected_flow_outcome_digest": str(subject["flow_outcome_digest"]),
    }

    first = set_flow_grade(
        **common,
        grade="partly",
        idempotency_key="grade-one",
        reason_codes=["minor_edits"],
        note="Needs one bounded correction.",
    )
    replay = set_flow_grade(
        **common,
        grade="partly",
        idempotency_key="grade-one",
        reason_codes=["minor_edits"],
        note="Needs one bounded correction.",
    )
    assert replay["id"] == first["id"]
    assert replay["replayed"] is True

    second = set_flow_grade(
        **common,
        grade="useful",
        idempotency_key="grade-two",
        expected_current_grade_event_id=str(first["id"]),
        reason_codes=["correct_complete"],
    )
    withdrawn = withdraw_flow_grade(
        **common,
        expected_current_grade_event_id=str(second["id"]),
        idempotency_key="grade-withdraw",
    )

    state = get_flow_grade_state(flow_id)
    assert state["current_grade_event"] is None
    assert state["latest_event"]["id"] == withdrawn["id"]
    assert [event["action"] for event in state["history"]] == [
        "set",
        "set",
        "withdraw",
    ]
    assert [event["event_index"] for event in state["history"]] == [1, 2, 3]
    assert state["history"][1]["supersedes_event_id"] == first["id"]
    assert state["history"][2]["supersedes_event_id"] == second["id"]


def test_stale_head_and_idempotency_mismatch_fail_closed(initialized_database) -> None:
    flow_id = _complete_local_flow()
    subject = get_flow_grade_state(flow_id)["subject"]
    common = {
        "flow_id": flow_id,
        "expected_subject_version": int(subject["subject_version"]),
        "expected_flow_outcome_digest": str(subject["flow_outcome_digest"]),
    }
    first = set_flow_grade(
        **common,
        grade="partly",
        idempotency_key="same-key",
    )

    with pytest.raises(FlowGradeConflictError, match="different request"):
        set_flow_grade(
            **common,
            grade="failed",
            idempotency_key="same-key",
            expected_current_grade_event_id=str(first["id"]),
        )
    with pytest.raises(FlowGradeConflictError, match="changed concurrently"):
        set_flow_grade(
            **common,
            grade="useful",
            idempotency_key="stale-head",
        )
    with pytest.raises(FlowGradeConflictError, match="digest is stale"):
        set_flow_grade(
            flow_id=flow_id,
            grade="useful",
            expected_subject_version=int(subject["subject_version"]),
            expected_flow_outcome_digest="sha256:" + "0" * 64,
            idempotency_key="stale-subject",
            expected_current_grade_event_id=str(first["id"]),
        )


def test_grade_api_round_trip_and_conflict_codes(initialized_database) -> None:
    flow_id = _complete_local_flow()
    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        read = client.get(f"/ai/flows/{flow_id}/grade")
        assert read.status_code == 200
        subject = read.json()["subject"]
        write = client.put(
            f"/ai/flows/{flow_id}/grade",
            json={
                "grade": "useful",
                "expected_subject_version": subject["subject_version"],
                "expected_flow_outcome_digest": subject["flow_outcome_digest"],
                "idempotency_key": "api-grade",
                "reason_codes": ["correct_complete"],
            },
        )
        assert write.status_code == 200
        event = write.json()
        stale = client.put(
            f"/ai/flows/{flow_id}/grade",
            json={
                "grade": "failed",
                "expected_subject_version": subject["subject_version"],
                "expected_flow_outcome_digest": subject["flow_outcome_digest"],
                "idempotency_key": "api-stale",
            },
        )
        assert stale.status_code == 409
        withdraw = client.post(
            f"/ai/flows/{flow_id}/grade/withdraw",
            json={
                "expected_subject_version": subject["subject_version"],
                "expected_flow_outcome_digest": subject["flow_outcome_digest"],
                "expected_current_grade_event_id": event["id"],
                "idempotency_key": "api-withdraw",
            },
        )
        assert withdraw.status_code == 200
        final_read = client.get(f"/ai/flows/{flow_id}/grade")

    assert final_read.status_code == 200
    assert final_read.json()["current_grade_event"] is None
    assert len(final_read.json()["history"]) == 2
