from __future__ import annotations

import sqlite3
from typing import Literal

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.flow_grade_contracts import (
    GRADE_SCHEMA_VERSION,
    GRADES,
    SOURCES,
    FlowGradeConflictError,
    FlowGradeContractError,
    Grade,
    GradeSource,
    decode_event,
    normalize_note,
    normalize_reason_codes,
    required_digest,
    safe_id,
)
from app.modules.ai.flow_grade_event_store import (
    find_replay,
    insert_event,
    latest_event,
)
from app.modules.ai.flow_grade_subjects import (
    ensure_flow_grade_subject_in_transaction,
)


def set_flow_grade(
    *,
    flow_id: str,
    grade: Grade | str,
    expected_subject_version: int,
    expected_flow_outcome_digest: str,
    idempotency_key: str,
    expected_current_grade_event_id: str | None = None,
    reason_codes: list[str] | tuple[str, ...] = (),
    note: str | None = None,
    source: GradeSource | str = "operator_api",
) -> dict[str, object]:
    if grade not in GRADES:
        raise FlowGradeContractError("unsupported grade")
    return _write_event(
        flow_id=flow_id,
        action="set",
        grade=str(grade),
        expected_subject_version=expected_subject_version,
        expected_flow_outcome_digest=expected_flow_outcome_digest,
        expected_current_grade_event_id=expected_current_grade_event_id,
        idempotency_key=idempotency_key,
        reason_codes=normalize_reason_codes(reason_codes),
        note=normalize_note(note),
        source=source,
    )


def withdraw_flow_grade(
    *,
    flow_id: str,
    expected_subject_version: int,
    expected_flow_outcome_digest: str,
    expected_current_grade_event_id: str,
    idempotency_key: str,
    source: GradeSource | str = "operator_api",
) -> dict[str, object]:
    return _write_event(
        flow_id=flow_id,
        action="withdraw",
        grade=None,
        expected_subject_version=expected_subject_version,
        expected_flow_outcome_digest=expected_flow_outcome_digest,
        expected_current_grade_event_id=expected_current_grade_event_id,
        idempotency_key=idempotency_key,
        reason_codes=[],
        note=None,
        source=source,
    )


def _write_event(
    *,
    flow_id: str,
    action: Literal["set", "withdraw"],
    grade: str | None,
    expected_subject_version: int,
    expected_flow_outcome_digest: str,
    expected_current_grade_event_id: str | None,
    idempotency_key: str,
    reason_codes: list[str],
    note: str | None,
    source: GradeSource | str,
) -> dict[str, object]:
    flow_id = safe_id(flow_id, "flow_id")
    idempotency_key = safe_id(idempotency_key, "idempotency_key")
    if source not in SOURCES:
        raise FlowGradeContractError("unsupported grade source")
    if (
        isinstance(expected_subject_version, bool)
        or not isinstance(expected_subject_version, int)
        or expected_subject_version < 1
    ):
        raise FlowGradeContractError("expected_subject_version must be positive")
    expected_flow_outcome_digest = required_digest(
        expected_flow_outcome_digest,
        "expected_flow_outcome_digest",
    )
    if expected_current_grade_event_id is not None:
        expected_current_grade_event_id = safe_id(
            expected_current_grade_event_id,
            "expected_current_grade_event_id",
        )
    request_digest = canonical_digest(
        {
            "action": action,
            "expected_current_grade_event_id": expected_current_grade_event_id,
            "expected_flow_outcome_digest": expected_flow_outcome_digest,
            "expected_subject_version": expected_subject_version,
            "flow_id": flow_id,
            "grade": grade,
            "idempotency_key": idempotency_key,
            "note": note,
            "reason_codes": reason_codes,
            "schema": GRADE_SCHEMA_VERSION,
            "source": source,
        }
    )

    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            subject = ensure_flow_grade_subject_in_transaction(
                connection,
                flow_id=flow_id,
            )
            _check_subject(
                subject,
                expected_subject_version=expected_subject_version,
                expected_flow_outcome_digest=expected_flow_outcome_digest,
            )
            replay = find_replay(
                connection,
                subject_id=str(subject["id"]),
                idempotency_key=idempotency_key,
            )
            if replay is not None:
                if replay["request_digest"] != request_digest:
                    raise FlowGradeConflictError(
                        "idempotency key was reused with a different request"
                    )
                connection.commit()
                result = decode_event(replay)
                result["replayed"] = True
                return result

            latest = latest_event(connection, subject_id=str(subject["id"]))
            current = latest if latest is not None and latest["action"] == "set" else None
            if action == "set":
                _check_set_head(
                    current,
                    expected_current_grade_event_id=expected_current_grade_event_id,
                )
            else:
                _check_withdraw_head(
                    current,
                    expected_current_grade_event_id=expected_current_grade_event_id,
                )
            row = insert_event(
                connection,
                flow_id=flow_id,
                subject=subject,
                latest=latest,
                action=action,
                grade=grade,
                reason_codes=reason_codes,
                note=note,
                source=str(source),
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )
            connection.commit()
            return decode_event(row)
        except Exception:
            connection.rollback()
            raise


def _check_subject(
    subject: dict[str, object],
    *,
    expected_subject_version: int,
    expected_flow_outcome_digest: str,
) -> None:
    if subject["subject_version"] != expected_subject_version:
        raise FlowGradeConflictError("grade subject version is stale")
    if subject["flow_outcome_digest"] != expected_flow_outcome_digest:
        raise FlowGradeConflictError("grade subject digest is stale")


def _check_set_head(
    current: sqlite3.Row | None,
    *,
    expected_current_grade_event_id: str | None,
) -> None:
    if current is None:
        if expected_current_grade_event_id is not None:
            raise FlowGradeConflictError("flow currently has no grade")
        return
    if expected_current_grade_event_id != current["id"]:
        raise FlowGradeConflictError("current grade changed concurrently")


def _check_withdraw_head(
    current: sqlite3.Row | None,
    *,
    expected_current_grade_event_id: str | None,
) -> None:
    if current is None:
        raise FlowGradeConflictError("flow currently has no grade to withdraw")
    if expected_current_grade_event_id != current["id"]:
        raise FlowGradeConflictError("current grade changed concurrently")
