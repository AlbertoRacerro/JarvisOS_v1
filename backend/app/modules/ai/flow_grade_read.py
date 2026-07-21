from __future__ import annotations

from app.core.database import open_sqlite_connection
from app.modules.ai.flow_grade_contracts import decode_event, safe_id
from app.modules.ai.flow_grade_event_store import list_events
from app.modules.ai.flow_grade_subjects import ensure_flow_grade_subject


def get_flow_grade_state(flow_id: str) -> dict[str, object]:
    flow_id = safe_id(flow_id, "flow_id")
    subject = ensure_flow_grade_subject(flow_id)
    with open_sqlite_connection() as connection:
        rows = list_events(connection, subject_id=str(subject["id"]))
    history = [decode_event(row) for row in rows]
    latest = history[-1] if history else None
    current = latest if latest is not None and latest["action"] == "set" else None
    return {
        "flow_id": flow_id,
        "subject": subject,
        "current_grade_event": current,
        "latest_event": latest,
        "history": history,
    }
