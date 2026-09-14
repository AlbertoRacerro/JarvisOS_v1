from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.development.models import CalendarAllocationUpdate, RoadmapItemUpdate


@pytest.mark.parametrize("field", ["title", "item_type", "status", "priority"])
def test_roadmap_required_update_fields_reject_explicit_null(field: str) -> None:
    with pytest.raises(ValidationError):
        RoadmapItemUpdate(
            workspace_id="workspace",
            expected_revision=1,
            actor="tester",
            **{field: None},
        )


@pytest.mark.parametrize("field", ["title", "event_type"])
def test_calendar_required_update_fields_reject_explicit_null(field: str) -> None:
    with pytest.raises(ValidationError):
        CalendarAllocationUpdate(
            workspace_id="workspace",
            expected_revision=1,
            actor="tester",
            **{field: None},
        )


def test_roadmap_done_transition_cannot_atomically_clear_gate() -> None:
    with pytest.raises(ValidationError):
        RoadmapItemUpdate(
            workspace_id="workspace",
            expected_revision=1,
            status="Done",
            done_when=None,
            actor="tester",
        )


def test_roadmap_gate_can_be_cleared_in_separate_update() -> None:
    update = RoadmapItemUpdate(
        workspace_id="workspace",
        expected_revision=1,
        done_when=None,
        actor="tester",
    )
    assert update.status is None
    assert "done_when" in update.model_fields_set
