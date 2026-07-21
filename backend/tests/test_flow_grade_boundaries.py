from __future__ import annotations

import pytest
import test_token_flow_local_runtime_integration as local

from app.modules.ai.flow_grade_contracts import FlowGradeConflictError
from app.modules.ai.flow_grade_read import get_flow_grade_state
from app.modules.ai.token_flow_service import create_flow, transition_flow_state

initialized_database = local.initialized_database


def test_running_flow_is_not_gradeable(initialized_database) -> None:
    flow = create_flow(task_kind="synthesis", requested_route_class="local:sequence")

    with pytest.raises(FlowGradeConflictError, match="only terminal flows"):
        get_flow_grade_state(str(flow["id"]))


def test_cancelled_flow_without_attempts_has_stable_subject(initialized_database) -> None:
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
