from __future__ import annotations

import hashlib
import json
import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.core.errors import WORKSPACE_NOT_FOUND_CODE, WORKSPACE_NOT_FOUND_MESSAGE
from app.modules.development.brainstorm_models import (
    BrainstormDiscussionRecord,
    BrainstormExactRef,
    BrainstormPromotionCreate,
    BrainstormRawCreate,
    BrainstormReconcileCreate,
    BrainstormSupersedeRequest,
)
from app.modules.development.service import DevelopmentError
from app.modules.events.service import log_event, utc_now


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _begin_write(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")


def _workspace_exists(connection: sqlite3.Connection, workspace_id: str) -> None:
    if connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone() is None:
        raise DevelopmentError(WORKSPACE_NOT_FOUND_CODE, WORKSPACE_NOT_FOUND_MESSAGE)


def _raw_row(connection: sqlite3.Connection, workspace_id: str, raw_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM brainstorm_raw_records WHERE workspace_id = ? AND id = ?",
        (workspace_id, raw_id),
    ).fetchone()
    if row is None:
        raise DevelopmentError("brainstorm_raw_not_found", "Brainstorm RAW capture not found.")
    return row


def _idea_row(connection: sqlite3.Connection, workspace_id: str, idea_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM brainstorm_ideas WHERE workspace_id = ? AND id = ?",
        (workspace_id, idea_id),
    ).fetchone()
    if row is None:
        raise DevelopmentError("brainstorm_idea_not_found", "Brainstorm idea not found.")
    return row


def _revision_row(
    connection: sqlite3.Connection, workspace_id: str, idea_id: str, revision: int
) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM brainstorm_revisions WHERE workspace_id = ? AND idea_id = ? AND revision = ?",
        (workspace_id, idea_id, revision),
    ).fetchone()
    if row is None:
        raise DevelopmentError("brainstorm_revision_not_found", "Brainstorm revision not found.")
    return row


def _ref_payload(ref: BrainstormExactRef) -> dict[str, object]:
    return ref.model_dump(mode="json")


def _validate_refs(
    connection: sqlite3.Connection,
    workspace_id: str,
    refs: list[BrainstormExactRef],
    *,
    attachment_only: bool = False,
) -> None:
    for ref in refs:
        if ref.ref_type == "raw" and not attachment_only:
            if ref.revision is not None:
                raise DevelopmentError("brainstorm_ref_invalid", "RAW references do not accept a revision.")
            _raw_row(connection, workspace_id, ref.ref_id)
        elif ref.ref_type == "brainstorm_revision" and not attachment_only:
            if ref.revision is None:
                raise DevelopmentError("brainstorm_ref_invalid", "Brainstorm revision references require a revision.")
            _revision_row(connection, workspace_id, ref.ref_id, ref.revision)
        elif ref.ref_type == "ai_thread_message" and not attachment_only:
            if ref.revision is not None:
                raise DevelopmentError("brainstorm_ref_invalid", "AI-thread references do not accept a revision.")
            row = connection.execute(
                """
                SELECT 1
                FROM ai_thread_interactions AS interaction
                JOIN ai_threads AS thread ON thread.id = interaction.thread_id
                WHERE interaction.id = ? AND thread.workspace_id = ?
                """,
                (ref.ref_id, workspace_id),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_ref_not_found", "Referenced AI-thread interaction was not found in this workspace.")
        elif ref.ref_type == "run_artifact":
            if ref.revision is not None:
                raise DevelopmentError("brainstorm_ref_invalid", "Attachment/source reference does not accept a revision.")
            row = connection.execute(
                """
                SELECT 1
                FROM artifacts AS a
                JOIN run_artifacts AS ra ON ra.artifact_id = a.id
                JOIN simulation_runs AS sr ON sr.id = ra.simulation_run_id
                WHERE a.id = ?
                  AND a.workspace_id = ?
                  AND ra.workspace_id = ?
                  AND sr.workspace_id = ?
                """,
                (ref.ref_id, workspace_id, workspace_id, workspace_id),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_ref_not_found", "Referenced run artifact was not found in this workspace.")
        elif ref.ref_type == "generic_artifact":
            if ref.revision is not None:
                raise DevelopmentError("brainstorm_ref_invalid", "Attachment/source reference does not accept a revision.")
            row = connection.execute(
                "SELECT 1 FROM artifacts WHERE workspace_id = ? AND id = ?",
                (workspace_id, ref.ref_id),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_ref_not_found", "Referenced artifact was not found in this workspace.")
        elif ref.ref_type == "literature_entry":
            if ref.revision is not None:
                raise DevelopmentError("brainstorm_ref_invalid", "Attachment/source reference does not accept a revision.")
            row = connection.execute(
                "SELECT 1 FROM literature_entries WHERE workspace_id = ? AND id = ?",
                (workspace_id, ref.ref_id),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_ref_not_found", "Referenced literature entry was not found in this workspace.")
        else:
            raise DevelopmentError("brainstorm_ref_invalid", f"Unsupported Brainstorm reference type: {ref.ref_type}.")


def _idempotent_result(
    connection: sqlite3.Connection,
    workspace_id: str,
    key: str,
    operation: str,
    payload_digest: str,
) -> sqlite3.Row | None:
    row = connection.execute(
        "SELECT * FROM brainstorm_idempotency WHERE workspace_id = ? AND idempotency_key = ?",
        (workspace_id, key),
    ).fetchone()
    if row is None:
        return None
    if str(row["operation"]) != operation or str(row["payload_digest"]) != payload_digest:
        raise DevelopmentError(
            "brainstorm_idempotency_mismatch",
            "Idempotency key was already used with a different Brainstorm request.",
        )
    return row


def _record_idempotency(
    connection: sqlite3.Connection,
    *,
    workspace_id: str,
    key: str,
    operation: str,
    payload_digest: str,
    result_type: str,
    result_id: str,
    result_revision: int | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO brainstorm_idempotency (
            workspace_id, idempotency_key, operation, payload_digest,
            result_type, result_id, result_revision, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workspace_id,
            key,
            operation,
            payload_digest,
            result_type,
            result_id,
            result_revision,
            utc_now(),
        ),
    )


def _discussion_payload(row: sqlite3.Row) -> dict[str, object]:
    value = dict(row)
    value["source_refs"] = json.loads(str(value.pop("source_refs_json")))
    return value


def _raw_payload(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, object]:
    value = dict(row)
    value["attachment_refs"] = json.loads(str(value.pop("attachment_refs_json")))
    discussion_rows = connection.execute(
        """
        SELECT * FROM brainstorm_discussions
        WHERE workspace_id = ? AND target_type = 'raw' AND target_id = ?
        ORDER BY created_at, id
        """,
        (str(row["workspace_id"]), str(row["id"])),
    ).fetchall()
    value["discussions"] = [_discussion_payload(discussion) for discussion in discussion_rows]
    return value


def _revision_payload(row: sqlite3.Row) -> dict[str, object]:
    value = dict(row)
    value["source_refs"] = json.loads(str(value.pop("source_refs_json")))
    return value


def _discussion_ids_for_sources(
    connection: sqlite3.Connection,
    workspace_id: str,
    refs: list[BrainstormExactRef],
) -> list[str]:
    discussion_ids: set[str] = set()
    for ref in refs:
        if ref.ref_type == "raw":
            rows = connection.execute(
                """
                SELECT id FROM brainstorm_discussions
                WHERE workspace_id = ? AND target_type = 'raw' AND target_id = ?
                ORDER BY created_at, id
                """,
                (workspace_id, ref.ref_id),
            ).fetchall()
        elif ref.ref_type == "brainstorm_revision" and ref.revision is not None:
            rows = connection.execute(
                """
                SELECT id FROM brainstorm_discussions
                WHERE workspace_id = ? AND target_type = 'idea'
                  AND target_id = ? AND target_revision = ?
                ORDER BY created_at, id
                """,
                (workspace_id, ref.ref_id, ref.revision),
            ).fetchall()
        else:
            continue
        discussion_ids.update(str(row["id"]) for row in rows)
    return sorted(discussion_ids)


def _idea_payload(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, object]:
    value = dict(row)
    revision = _revision_row(connection, str(row["workspace_id"]), str(row["id"]), int(row["current_revision"]))
    value["current"] = _revision_payload(revision)
    return value


def create_raw(payload: BrainstormRawCreate) -> dict[str, object]:
    request = payload.model_dump(mode="json")
    request_digest = _digest(request)
    with open_sqlite_connection() as connection:
        _begin_write(connection)
        _workspace_exists(connection, payload.workspace_id)
        existing = _idempotent_result(
            connection, payload.workspace_id, payload.idempotency_key, "raw.create", request_digest
        )
        if existing is not None:
            return _raw_payload(connection, _raw_row(connection, payload.workspace_id, str(existing["result_id"])))
        _validate_refs(connection, payload.workspace_id, payload.attachment_refs, attachment_only=True)
        raw_id = str(uuid4())
        now = utc_now()
        refs = [_ref_payload(ref) for ref in payload.attachment_refs]
        connection.execute(
            """
            INSERT INTO brainstorm_raw_records (
                id, workspace_id, content, attachment_refs_json, lineage_state, created_by, created_at
            ) VALUES (?, ?, ?, ?, 'NEW', ?, ?)
            """,
            (raw_id, payload.workspace_id, payload.content, _canonical(refs), payload.created_by, now),
        )
        _record_idempotency(
            connection,
            workspace_id=payload.workspace_id,
            key=payload.idempotency_key,
            operation="raw.create",
            payload_digest=request_digest,
            result_type="raw",
            result_id=raw_id,
        )
        log_event(
            connection,
            event_type="development.brainstorm.raw_created",
            actor=payload.created_by,
            target_type="brainstorm_raw",
            target_id=raw_id,
            workspace_id=payload.workspace_id,
            payload={"state": "NEW", "attachment_ref_count": len(refs), "content_digest": _digest(payload.content)},
        )
        row = _raw_row(connection, payload.workspace_id, raw_id)
        connection.commit()
        return _raw_payload(connection, row)


def list_raw(workspace_id: str) -> list[dict[str, object]]:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN")
        _workspace_exists(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM brainstorm_raw_records WHERE workspace_id = ? ORDER BY created_at DESC, id",
            (workspace_id,),
        ).fetchall()
        return [_raw_payload(connection, row) for row in rows]


def get_raw(workspace_id: str, raw_id: str) -> dict[str, object]:
    """Read one immutable RAW capture and its owner-mediated discussions."""
    with open_sqlite_connection() as connection:
        _workspace_exists(connection, workspace_id)
        return _raw_payload(connection, _raw_row(connection, workspace_id, raw_id))


def get_discussion(workspace_id: str, discussion_id: str) -> dict[str, object]:
    with open_sqlite_connection() as connection:
        _workspace_exists(connection, workspace_id)
        row = connection.execute(
            "SELECT * FROM brainstorm_discussions WHERE workspace_id=? AND id=?",
            (workspace_id, discussion_id),
        ).fetchone()
    if row is None:
        raise DevelopmentError("brainstorm_discussion_not_found", "Brainstorm discussion not found.")
    return _discussion_payload(row)


def record_discussion(payload: BrainstormDiscussionRecord) -> dict[str, object]:
    request = payload.model_dump(mode="json")
    request_digest = _digest(request)
    with open_sqlite_connection() as connection:
        _begin_write(connection)
        _workspace_exists(connection, payload.workspace_id)
        existing = _idempotent_result(
            connection, payload.workspace_id, payload.idempotency_key, "discussion.record", request_digest
        )
        if existing is not None:
            row = connection.execute(
                "SELECT * FROM brainstorm_discussions WHERE workspace_id = ? AND id = ?",
                (payload.workspace_id, str(existing["result_id"])),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_discussion_not_found", "Brainstorm discussion not found.")
            return _discussion_payload(row)
        _validate_refs(connection, payload.workspace_id, payload.source_refs)
        if payload.target_type == "raw":
            if payload.expected_revision is not None:
                raise DevelopmentError("brainstorm_revision_invalid", "RAW discussion does not accept expected_revision.")
            _raw_row(connection, payload.workspace_id, payload.target_id)
        else:
            idea = _idea_row(connection, payload.workspace_id, payload.target_id)
            if payload.expected_revision is None or int(idea["current_revision"]) != payload.expected_revision:
                raise DevelopmentError("brainstorm_idea_stale", "Brainstorm idea revision is stale.")
            if str(idea["lineage_state"]) == "SUPERSEDED":
                raise DevelopmentError("brainstorm_idea_superseded", "Superseded Brainstorm idea cannot accept discussion mutation.")
        discussion_id = str(uuid4())
        now = utc_now()
        refs = [_ref_payload(ref) for ref in payload.source_refs]
        connection.execute(
            """
            INSERT INTO brainstorm_discussions (
                id, workspace_id, target_type, target_id, target_revision,
                source_refs_json, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                discussion_id,
                payload.workspace_id,
                payload.target_type,
                payload.target_id,
                payload.expected_revision,
                _canonical(refs),
                payload.actor,
                now,
            ),
        )
        if payload.target_type == "raw":
            connection.execute(
                "UPDATE brainstorm_raw_records SET lineage_state = 'DISCUSSED' WHERE workspace_id = ? AND id = ? AND lineage_state = 'NEW'",
                (payload.workspace_id, payload.target_id),
            )
        _record_idempotency(
            connection,
            workspace_id=payload.workspace_id,
            key=payload.idempotency_key,
            operation="discussion.record",
            payload_digest=request_digest,
            result_type="discussion",
            result_id=discussion_id,
            result_revision=payload.expected_revision,
        )
        log_event(
            connection,
            event_type="development.brainstorm.discussion_recorded",
            actor=payload.actor,
            target_type=f"brainstorm_{payload.target_type}",
            target_id=payload.target_id,
            workspace_id=payload.workspace_id,
            payload={"source_ref_count": len(refs), "target_revision": payload.expected_revision},
        )
        row = connection.execute(
            "SELECT * FROM brainstorm_discussions WHERE workspace_id = ? AND id = ?",
            (payload.workspace_id, discussion_id),
        ).fetchone()
        if row is None:
            raise DevelopmentError("brainstorm_discussion_not_found", "Brainstorm discussion not found.")
        connection.commit()
        return _discussion_payload(row)


def reconcile(payload: BrainstormReconcileCreate) -> dict[str, object]:
    request = payload.model_dump(mode="json")
    request_digest = _digest(request)
    with open_sqlite_connection() as connection:
        _begin_write(connection)
        _workspace_exists(connection, payload.workspace_id)
        existing = _idempotent_result(
            connection, payload.workspace_id, payload.idempotency_key, "idea.reconcile", request_digest
        )
        if existing is not None:
            return _idea_payload(connection, _idea_row(connection, payload.workspace_id, str(existing["result_id"])))
        _validate_refs(connection, payload.workspace_id, payload.source_refs)
        now = utc_now()
        if payload.idea_id is None:
            if payload.expected_revision is not None:
                raise DevelopmentError("brainstorm_revision_invalid", "New Brainstorm idea must not provide expected_revision.")
            idea_id = str(uuid4())
            revision = 1
            connection.execute(
                """
                INSERT INTO brainstorm_ideas (
                    id, workspace_id, current_revision, lineage_state, created_by, created_at, updated_at
                ) VALUES (?, ?, 1, 'RECONCILED', ?, ?, ?)
                """,
                (idea_id, payload.workspace_id, payload.actor, now, now),
            )
        else:
            idea_id = payload.idea_id
            current = _idea_row(connection, payload.workspace_id, idea_id)
            if payload.expected_revision is None or int(current["current_revision"]) != payload.expected_revision:
                raise DevelopmentError("brainstorm_idea_stale", "Brainstorm idea revision is stale.")
            if str(current["lineage_state"]) == "SUPERSEDED":
                raise DevelopmentError("brainstorm_idea_superseded", "Superseded Brainstorm idea cannot be reconciled.")
            revision = payload.expected_revision + 1
            changed = connection.execute(
                """
                UPDATE brainstorm_ideas
                SET current_revision = ?, lineage_state = 'RECONCILED', updated_at = ?
                WHERE workspace_id = ? AND id = ? AND current_revision = ? AND lineage_state <> 'SUPERSEDED'
                """,
                (revision, now, payload.workspace_id, idea_id, payload.expected_revision),
            )
            if changed.rowcount != 1:
                raise DevelopmentError("brainstorm_idea_stale", "Brainstorm idea revision changed concurrently.")
        refs = [_ref_payload(ref) for ref in payload.source_refs]
        discussion_ids = _discussion_ids_for_sources(connection, payload.workspace_id, payload.source_refs)
        connection.execute(
            """
            INSERT INTO brainstorm_revisions (
                idea_id, workspace_id, revision, title, takeaway, synthesis,
                source_refs_json, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea_id,
                payload.workspace_id,
                revision,
                payload.title.strip(),
                payload.takeaway.strip(),
                payload.synthesis.strip(),
                _canonical(refs),
                payload.actor,
                now,
            ),
        )
        connection.executemany(
            """
            INSERT INTO brainstorm_revision_discussions (
                idea_id, workspace_id, revision, discussion_id
            ) VALUES (?, ?, ?, ?)
            """,
            [(idea_id, payload.workspace_id, revision, discussion_id) for discussion_id in discussion_ids],
        )
        for ref in payload.source_refs:
            if ref.ref_type == "raw":
                connection.execute(
                    "UPDATE brainstorm_raw_records SET lineage_state = 'RECONCILED' WHERE workspace_id = ? AND id = ? AND lineage_state <> 'SUPERSEDED'",
                    (payload.workspace_id, ref.ref_id),
                )
        _record_idempotency(
            connection,
            workspace_id=payload.workspace_id,
            key=payload.idempotency_key,
            operation="idea.reconcile",
            payload_digest=request_digest,
            result_type="idea",
            result_id=idea_id,
            result_revision=revision,
        )
        log_event(
            connection,
            event_type="development.brainstorm.reconciled",
            actor=payload.actor,
            target_type="brainstorm_idea",
            target_id=idea_id,
            workspace_id=payload.workspace_id,
            payload={
                "revision": revision,
                "source_ref_count": len(refs),
                "discussion_ref_count": len(discussion_ids),
                "synthesis_digest": _digest(payload.synthesis),
            },
        )
        row = _idea_row(connection, payload.workspace_id, idea_id)
        connection.commit()
        return _idea_payload(connection, row)


def list_ideas(workspace_id: str) -> list[dict[str, object]]:
    with open_sqlite_connection() as connection:
        _workspace_exists(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM brainstorm_ideas WHERE workspace_id = ? ORDER BY updated_at DESC, id",
            (workspace_id,),
        ).fetchall()
        return [_idea_payload(connection, row) for row in rows]


def get_idea(workspace_id: str, idea_id: str) -> dict[str, object]:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN")
        _workspace_exists(connection, workspace_id)
        idea = _idea_payload(connection, _idea_row(connection, workspace_id, idea_id))
        revisions = connection.execute(
            "SELECT * FROM brainstorm_revisions WHERE workspace_id = ? AND idea_id = ? ORDER BY revision DESC",
            (workspace_id, idea_id),
        ).fetchall()
        idea["revisions"] = [_revision_payload(row) for row in revisions]
        discussion_rows = connection.execute(
            """
            SELECT binding.revision AS bound_revision, discussion.*
            FROM brainstorm_revision_discussions AS binding
            JOIN brainstorm_discussions AS discussion
              ON discussion.id = binding.discussion_id
             AND discussion.workspace_id = binding.workspace_id
            WHERE binding.workspace_id = ? AND binding.idea_id = ?
            ORDER BY binding.revision, discussion.created_at, discussion.id
            """,
            (workspace_id, idea_id),
        ).fetchall()
        idea["discussions"] = [_discussion_payload(row) for row in discussion_rows]
        return idea


def supersede(payload: BrainstormSupersedeRequest) -> dict[str, object]:
    request = payload.model_dump(mode="json")
    request_digest = _digest(request)
    with open_sqlite_connection() as connection:
        _begin_write(connection)
        _workspace_exists(connection, payload.workspace_id)
        existing = _idempotent_result(
            connection, payload.workspace_id, payload.idempotency_key, "idea.supersede", request_digest
        )
        if existing is not None:
            return _idea_payload(connection, _idea_row(connection, payload.workspace_id, payload.idea_id))
        if payload.idea_id == payload.successor_idea_id:
            raise DevelopmentError("brainstorm_lineage_self", "Brainstorm idea cannot supersede itself.")
        source = _idea_row(connection, payload.workspace_id, payload.idea_id)
        successor = _idea_row(connection, payload.workspace_id, payload.successor_idea_id)
        if int(source["current_revision"]) != payload.expected_revision:
            raise DevelopmentError("brainstorm_idea_stale", "Brainstorm idea revision is stale.")
        if str(source["lineage_state"]) == "SUPERSEDED":
            raise DevelopmentError("brainstorm_idea_superseded", "Brainstorm idea is already superseded.")
        if int(successor["current_revision"]) != payload.successor_revision:
            raise DevelopmentError("brainstorm_successor_stale", "Successor Brainstorm revision is stale.")
        _revision_row(connection, payload.workspace_id, payload.successor_idea_id, payload.successor_revision)
        cursor = successor
        visited: set[str] = {payload.idea_id}
        while cursor["successor_idea_id"] is not None:
            next_id = str(cursor["successor_idea_id"])
            if next_id in visited:
                raise DevelopmentError("brainstorm_lineage_cycle", "Brainstorm supersession would create a cycle.")
            visited.add(next_id)
            cursor = _idea_row(connection, payload.workspace_id, next_id)
        now = utc_now()
        changed = connection.execute(
            """
            UPDATE brainstorm_ideas
            SET lineage_state = 'SUPERSEDED', successor_idea_id = ?, successor_revision = ?, updated_at = ?
            WHERE workspace_id = ? AND id = ? AND current_revision = ? AND lineage_state <> 'SUPERSEDED'
            """,
            (
                payload.successor_idea_id,
                payload.successor_revision,
                now,
                payload.workspace_id,
                payload.idea_id,
                payload.expected_revision,
            ),
        )
        if changed.rowcount != 1:
            raise DevelopmentError("brainstorm_idea_stale", "Brainstorm idea changed concurrently.")
        _record_idempotency(
            connection,
            workspace_id=payload.workspace_id,
            key=payload.idempotency_key,
            operation="idea.supersede",
            payload_digest=request_digest,
            result_type="idea",
            result_id=payload.idea_id,
            result_revision=payload.expected_revision,
        )
        log_event(
            connection,
            event_type="development.brainstorm.superseded",
            actor=payload.actor,
            target_type="brainstorm_idea",
            target_id=payload.idea_id,
            workspace_id=payload.workspace_id,
            payload={"revision": payload.expected_revision, "successor_id": payload.successor_idea_id, "successor_revision": payload.successor_revision},
        )
        row = _idea_row(connection, payload.workspace_id, payload.idea_id)
        connection.commit()
        return _idea_payload(connection, row)


def create_promotion(payload: BrainstormPromotionCreate) -> dict[str, object]:
    request = payload.model_dump(mode="json")
    if len(_canonical(payload.payload)) > 50_000:
        raise DevelopmentError("brainstorm_promotion_oversized", "Brainstorm promotion payload is too large.")
    request_digest = _digest(request)
    with open_sqlite_connection() as connection:
        _begin_write(connection)
        _workspace_exists(connection, payload.workspace_id)
        existing = _idempotent_result(
            connection, payload.workspace_id, payload.idempotency_key, "promotion.create", request_digest
        )
        if existing is not None:
            row = connection.execute(
                "SELECT * FROM brainstorm_promotions WHERE workspace_id = ? AND id = ?",
                (payload.workspace_id, str(existing["result_id"])),
            ).fetchone()
            if row is None:
                raise DevelopmentError("brainstorm_promotion_not_found", "Brainstorm promotion not found.")
            return dict(row)
        idea = _idea_row(connection, payload.workspace_id, payload.idea_id)
        if str(idea["lineage_state"]) == "SUPERSEDED":
            raise DevelopmentError("brainstorm_promotion_superseded", "Superseded Brainstorm idea cannot be promoted.")
        if int(idea["current_revision"]) != payload.source_revision:
            raise DevelopmentError("brainstorm_promotion_stale", "Promotion source revision is stale.")
        _revision_row(connection, payload.workspace_id, payload.idea_id, payload.source_revision)
        promotion_id = str(uuid4())
        now = utc_now()
        payload_json = _canonical(payload.payload)
        payload_digest = _digest(payload.payload)
        connection.execute(
            """
            INSERT INTO brainstorm_promotions (
                id, workspace_id, idea_id, source_revision, target, payload_json,
                payload_digest, state, downstream_handoff_id, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
            """,
            (
                promotion_id,
                payload.workspace_id,
                payload.idea_id,
                payload.source_revision,
                payload.target,
                payload_json,
                payload_digest,
                payload.actor,
                now,
            ),
        )
        _record_idempotency(
            connection,
            workspace_id=payload.workspace_id,
            key=payload.idempotency_key,
            operation="promotion.create",
            payload_digest=request_digest,
            result_type="promotion",
            result_id=promotion_id,
            result_revision=payload.source_revision,
        )
        log_event(
            connection,
            event_type="development.brainstorm.promotion_proposed",
            actor=payload.actor,
            target_type="brainstorm_promotion",
            target_id=promotion_id,
            workspace_id=payload.workspace_id,
            payload={"idea_id": payload.idea_id, "source_revision": payload.source_revision, "target": payload.target, "payload_digest": payload_digest, "state": "pending"},
        )
        connection.commit()
        return {
            "id": promotion_id,
            "workspace_id": payload.workspace_id,
            "idea_id": payload.idea_id,
            "source_revision": payload.source_revision,
            "target": payload.target,
            "payload": payload.payload,
            "payload_digest": payload_digest,
            "state": "pending",
            "downstream_handoff_id": None,
            "created_by": payload.actor,
            "created_at": now,
        }


def list_promotions(workspace_id: str, idea_id: str | None = None) -> list[dict[str, object]]:
    with open_sqlite_connection() as connection:
        _workspace_exists(connection, workspace_id)
        if idea_id is None:
            rows = connection.execute(
                "SELECT * FROM brainstorm_promotions WHERE workspace_id = ? ORDER BY created_at DESC, id",
                (workspace_id,),
            ).fetchall()
        else:
            _idea_row(connection, workspace_id, idea_id)
            rows = connection.execute(
                "SELECT * FROM brainstorm_promotions WHERE workspace_id = ? AND idea_id = ? ORDER BY created_at DESC, id",
                (workspace_id, idea_id),
            ).fetchall()
        result: list[dict[str, object]] = []
        for row in rows:
            value = dict(row)
            value["payload"] = json.loads(str(value.pop("payload_json")))
            result.append(value)
        return result


def get_promotion(workspace_id: str, promotion_id: str) -> dict[str, object]:
    with open_sqlite_connection() as connection:
        _workspace_exists(connection, workspace_id)
        row = connection.execute(
            "SELECT * FROM brainstorm_promotions WHERE workspace_id=? AND id=?",
            (workspace_id, promotion_id),
        ).fetchone()
    if row is None:
        raise DevelopmentError("brainstorm_promotion_not_found", "Brainstorm promotion proposal not found.")
    value = dict(row)
    value["payload"] = json.loads(str(value.pop("payload_json")))
    return value
