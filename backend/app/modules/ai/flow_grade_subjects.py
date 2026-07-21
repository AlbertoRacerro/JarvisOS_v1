from __future__ import annotations

import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.flow_grade_contracts import (
    FlowGradeConflictError,
    canonical_json,
    decode_subject,
    safe_id,
)
from app.modules.ai.flow_grade_evidence import (
    build_flow_outcome_payload,
    load_flow_evidence,
)
from app.modules.events.service import utc_now


def ensure_flow_grade_subject(flow_id: str) -> dict[str, object]:
    flow_id = safe_id(flow_id, "flow_id")
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            subject = ensure_flow_grade_subject_in_transaction(
                connection,
                flow_id=flow_id,
            )
            connection.commit()
            return subject
        except Exception:
            connection.rollback()
            raise


def ensure_flow_grade_subject_in_transaction(
    connection: sqlite3.Connection,
    *,
    flow_id: str,
) -> dict[str, object]:
    flow_id = safe_id(flow_id, "flow_id")
    flow, attempts, final_accounting_digest, final_output_digest = load_flow_evidence(
        connection,
        flow_id=flow_id,
    )
    payload = build_flow_outcome_payload(
        flow=flow,
        attempts=attempts,
        final_accounting_digest=final_accounting_digest,
        final_output_digest=final_output_digest,
    )
    outcome_digest = canonical_digest(payload)
    current = connection.execute(
        """
        SELECT *
        FROM ai_flow_grade_subjects
        WHERE flow_id = ? AND valid = 1
        """,
        (flow_id,),
    ).fetchone()
    if current is not None and current["flow_outcome_digest"] == outcome_digest:
        return decode_subject(current)

    now = utc_now()
    if current is not None:
        connection.execute(
            """
            UPDATE ai_flow_grade_subjects
            SET valid = 0, invalidated_at = ?
            WHERE id = ? AND valid = 1
            """,
            (now, current["id"]),
        )
    version_row = connection.execute(
        """
        SELECT COALESCE(MAX(subject_version), 0) + 1 AS next_version
        FROM ai_flow_grade_subjects
        WHERE flow_id = ?
        """,
        (flow_id,),
    ).fetchone()
    subject_version = int(version_row["next_version"])
    old_digest = connection.execute(
        """
        SELECT id
        FROM ai_flow_grade_subjects
        WHERE flow_id = ? AND flow_outcome_digest = ?
        """,
        (flow_id, outcome_digest),
    ).fetchone()
    if old_digest is not None:
        raise FlowGradeConflictError(
            "flow outcome evidence reverted to a previously invalidated subject"
        )

    subject_id = str(uuid4())
    connection.execute(
        """
        INSERT INTO ai_flow_grade_subjects (
            id, flow_id, terminal_attempt_id, subject_version,
            flow_outcome_digest, final_accounting_digest,
            final_output_digest, subject_payload_json,
            valid, invalidated_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, ?)
        """,
        (
            subject_id,
            flow_id,
            flow["terminal_attempt_id"],
            subject_version,
            outcome_digest,
            final_accounting_digest,
            final_output_digest,
            canonical_json(payload),
            now,
        ),
    )
    created = connection.execute(
        "SELECT * FROM ai_flow_grade_subjects WHERE id = ?",
        (subject_id,),
    ).fetchone()
    if created is None:
        raise FlowGradeConflictError("grade subject insert did not persist")
    return decode_subject(created)
