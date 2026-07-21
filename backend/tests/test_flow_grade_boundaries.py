from __future__ import annotations

import pytest
import test_token_flow_local_runtime_integration as local

from app.core.database import open_sqlite_connection
from app.modules.ai.flow_grade_contracts import FlowGradeConflictError
from app.modules.ai.flow_grade_read import get_flow_grade_state
from app.modules.ai.token_flow_service import create_flow, transition_flow_state

initialized_database = local.initialized_database


def test_running_flow_is_not_gradeable(initialized_database) -> None:
    flow = create_flow(task_kind="synthesis", requested_route_class="local:sequence")

    with pytest.raises(FlowGradeConflictError, match="only terminal flows"):
        get_flow_grade_state(str(flow["id"]))


def test_cancelled_flow_without_attempts_has_stable_subject_but_no_auto_grade(
    initialized_database,
) -> None:
    flow = create_flow(task_kind="synthesis", requested_route_class="local:sequence")
    terminal = transition_flow_state(
        flow_id=str(flow["id"]),
        new_state="cancelled_terminal",
        terminal_reason="cancelled_by_operator",
    )

    assert terminal["state"] == "cancelled_terminal"
    first = get_flow_grade_state(str(flow["id"]))
    second = get_flow_grade_state(str(flow["id"]))
    assert first["subject"] == second["subject"]
    assert first["subject"]["final_output_digest"] is None
    assert first["history"] == []

    with open_sqlite_connection() as connection:
        subject_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_flow_grade_subjects WHERE flow_id = ?",
            (flow["id"],),
        ).fetchone()["count"]
        event_count = connection.execute(
            "SELECT COUNT(*) AS count FROM ai_flow_grade_events WHERE flow_id = ?",
            (flow["id"],),
        ).fetchone()["count"]
    assert subject_count == 1
    assert event_count == 0
