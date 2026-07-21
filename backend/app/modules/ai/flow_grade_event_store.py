from __future__ import annotations

import sqlite3
from uuid import uuid4

from app.modules.ai.flow_grade_contracts import (
    ACTOR,
    GRADE_POLICY_VERSION,
    GRADE_SCHEMA_VERSION,
    FlowGradeConflictError,
    canonical_json,
)
from app.modules.events.service import utc_now


def find_replay(
    connection: sqlite3.Connection,
    *,
    subject_id: str,
    idempotency_key: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM ai_flow_grade_events
        WHERE subject_id = ? AND idempotency_key = ?
        """,
        (subject_id, idempotency_key),
    ).fetchone()


def latest_event(
    connection: sqlite3.Connection,
    *,
    subject_id: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM ai_flow_grade_events
        WHERE subject_id = ?
        ORDER BY event_index DESC
        LIMIT 1
        """,
        (subject_id,),
    ).fetchone()


def list_events(
    connection: sqlite3.Connection,
    *,
    subject_id: str,
) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            """
            SELECT *
            FROM ai_flow_grade_events
            WHERE subject_id = ?
            ORDER BY event_index
            """,
            (subject_id,),
        ).fetchall()
    )


def insert_event(
    connection: sqlite3.Connection,
    *,
    flow_id: str,
    subject: dict[str, object],
    latest: sqlite3.Row | None,
    action: str,
    grade: str | None,
    reason_codes: list[str],
    note: str | None,
    source: str,
    idempotency_key: str,
    request_digest: str,
) -> sqlite3.Row:
    event_id = str(uuid4())
    event_index = 1 if latest is None else int(latest["event_index"]) + 1
    connection.execute(
        """
        INSERT INTO ai_flow_grade_events (
            id, flow_id, subject_id, subject_version,
            flow_outcome_digest, event_index, action, grade,
            reason_codes_json, note_text, actor, source,
            supersedes_event_id, idempotency_key, request_digest,
            created_at, schema_version, policy_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            flow_id,
            subject["id"],
            subject["subject_version"],
            subject["flow_outcome_digest"],
            event_index,
            action,
            grade,
            canonical_json(reason_codes),
            note,
            ACTOR,
            source,
            latest["id"] if latest is not None else None,
            idempotency_key,
            request_digest,
            utc_now(),
            GRADE_SCHEMA_VERSION,
            GRADE_POLICY_VERSION,
        ),
    )
    row = connection.execute(
        "SELECT * FROM ai_flow_grade_events WHERE id = ?",
        (event_id,),
    ).fetchone()
    if row is None:
        raise FlowGradeConflictError("grade event insert did not persist")
    return row
