from __future__ import annotations

import json
import re
import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai.context_builder import (
    ContextSelectionSpec,
    build_workspace_context_bundle,
    canonical_digest,
)
from app.modules.ai.execution import resolve_effective_route_class, run_ai_task
from app.modules.ai.jarvis_context import (
    JarvisContextConflictError,
    require_dispatchable_preview,
)
from app.modules.ai.settings import ensure_ai_settings
from app.modules.ai.thread_models import (
    AIThreadCreate,
    AIThreadDetail,
    AIThreadInteractionRead,
    AIThreadList,
    AIThreadSubmit,
    AIThreadSubmitRead,
    AIThreadSummary,
)
from app.modules.ai.token_flow_service import create_flow_in_transaction
from app.modules.events.service import utc_now

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_MAX_TITLE = 120
_MAX_PROMPT = 12_000
_MAX_ASSISTANT = 131_072
_MAX_DIAGNOSTIC = 500
_DEFAULT_THREAD_LIMIT = 25
_MAX_THREAD_LIMIT = 50
_DEFAULT_INTERACTION_LIMIT = 50
_MAX_INTERACTION_LIMIT = 100
_MAX_PROPOSAL_IDS = 50


class AIThreadError(ValueError):
    pass


class AIThreadNotFoundError(AIThreadError):
    pass


class AIThreadConflictError(AIThreadError):
    pass


def create_thread(payload: AIThreadCreate) -> AIThreadSummary:
    workspace_id = _safe_id(payload.workspace_id, "workspace_id")
    title = _bounded_optional_text(payload.title, _MAX_TITLE, "title")
    now = utc_now()
    thread_id = str(uuid4())
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _require_workspace(connection, workspace_id)
            connection.execute(
                """
                INSERT INTO ai_threads (id, workspace_id, title, created_at, last_activity_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (thread_id, workspace_id, title, now, now),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return _thread_summary(thread_id, workspace_id)


def list_threads(*, workspace_id: str, limit: int = _DEFAULT_THREAD_LIMIT) -> AIThreadList:
    workspace_id = _safe_id(workspace_id, "workspace_id")
    limit = _bounded_limit(limit, default=_DEFAULT_THREAD_LIMIT, maximum=_MAX_THREAD_LIMIT)
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            """
            SELECT id, workspace_id, title, created_at, last_activity_at
            FROM ai_threads
            WHERE workspace_id = ?
            ORDER BY last_activity_at DESC, id ASC
            LIMIT ?
            """,
            (workspace_id, limit),
        ).fetchall()
    return AIThreadList(threads=[_summary_from_row(row) for row in rows])


def get_thread(
    *,
    workspace_id: str,
    thread_id: str,
    interaction_limit: int = _DEFAULT_INTERACTION_LIMIT,
) -> AIThreadDetail:
    workspace_id = _safe_id(workspace_id, "workspace_id")
    thread_id = _safe_id(thread_id, "thread_id")
    interaction_limit = _bounded_limit(
        interaction_limit,
        default=_DEFAULT_INTERACTION_LIMIT,
        maximum=_MAX_INTERACTION_LIMIT,
    )
    with open_sqlite_connection() as connection:
        thread = _require_thread(connection, workspace_id, thread_id)
        rows = connection.execute(
            _INTERACTION_SELECT + " WHERE interaction.thread_id = ? "
            "ORDER BY interaction.interaction_index DESC LIMIT ?",
            (thread_id, interaction_limit + 1),
        ).fetchall()
    has_older = len(rows) > interaction_limit
    rows = rows[:interaction_limit]
    rows.reverse()
    return AIThreadDetail(
        **_summary_from_row(thread).model_dump(),
        interactions=[_interaction_from_row(row) for row in rows],
        has_older=has_older,
    )


def submit_interaction(
    *,
    workspace_id: str,
    thread_id: str,
    payload: AIThreadSubmit,
) -> AIThreadSubmitRead:
    workspace_id = _safe_id(workspace_id, "workspace_id")
    thread_id = _safe_id(thread_id, "thread_id")
    request_id = _safe_id(payload.request_id, "request_id")
    prompt = _bounded_required_text(payload.prompt, _MAX_PROMPT, "prompt")
    digest_payload: dict[str, object] = {
        "prompt": prompt,
        "task_kind": payload.task_kind,
        "route_class": payload.route_class,
        "max_tokens": payload.max_tokens,
    }
    if payload.context_selection is not None:
        digest_payload["context_selection"] = payload.context_selection.model_dump()
        digest_payload["expected_context_digest"] = payload.expected_context_digest
    if payload.jarvis_context is not None:
        digest_payload["jarvis_context"] = payload.jarvis_context.model_dump(mode="json")
        digest_payload["expected_jarvis_context_digest"] = payload.expected_jarvis_context_digest
    request_digest = canonical_digest(digest_payload)

    duplicate_id = _find_existing_interaction(
        workspace_id=workspace_id,
        thread_id=thread_id,
        request_id=request_id,
        request_digest=request_digest,
    )
    if duplicate_id is not None:
        return AIThreadSubmitRead(
            interaction=_read_interaction(
                workspace_id=workspace_id,
                thread_id=thread_id,
                interaction_id=duplicate_id,
            )
        )

    try:
        context_blocks = _context_blocks_for_new_submit(workspace_id, payload)
    except AIThreadConflictError:
        # A concurrent request with the same immutable request semantics may have
        # reserved while this request rebuilt its context pack. Re-read that
        # durable identity before reporting context drift so retries never spend
        # twice merely because records changed after the first dispatch began.
        duplicate_id = _find_existing_interaction(
            workspace_id=workspace_id,
            thread_id=thread_id,
            request_id=request_id,
            request_digest=request_digest,
        )
        if duplicate_id is not None:
            return AIThreadSubmitRead(
                interaction=_read_interaction(
                    workspace_id=workspace_id,
                    thread_id=thread_id,
                    interaction_id=duplicate_id,
                )
            )
        raise

    ensure_ai_settings()
    duplicate_id = _reserve_interaction(
        workspace_id=workspace_id,
        thread_id=thread_id,
        request_id=request_id,
        request_digest=request_digest,
        prompt=prompt,
        payload=payload,
    )
    if duplicate_id is not None:
        return AIThreadSubmitRead(
            interaction=_read_interaction(
                workspace_id=workspace_id,
                thread_id=thread_id,
                interaction_id=duplicate_id,
            )
        )

    interaction_id, flow_id = _mark_reserved_dispatching(
        workspace_id=workspace_id,
        thread_id=thread_id,
        request_id=request_id,
        request_digest=request_digest,
    )

    outcome = run_ai_task(
        user_prompt=prompt,
        task_kind=payload.task_kind,
        route_class=payload.route_class,
        context_blocks=context_blocks,
        max_output_tokens=payload.max_tokens,
        workspace_id=workspace_id,
        existing_flow_id=flow_id,
    )

    assistant_text = outcome.response.text if outcome.response is not None else None
    bounded_assistant, truncated = _assistant_snapshot(assistant_text)
    try:
        now = utc_now()
        with open_sqlite_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_thread(connection, workspace_id, thread_id)
                updated = connection.execute(
                    """
                    UPDATE ai_thread_interactions
                    SET assistant_text = ?, assistant_text_truncated = ?,
                        persistence_state = 'captured', persistence_error = NULL, updated_at = ?
                    WHERE id = ? AND thread_id = ? AND flow_id = ?
                      AND persistence_state = 'dispatching'
                    """,
                    (
                        bounded_assistant,
                        int(truncated),
                        now,
                        interaction_id,
                        thread_id,
                        flow_id,
                    ),
                )
                if updated.rowcount != 1:
                    raise AIThreadConflictError("interaction capture state changed concurrently")
                connection.execute(
                    "UPDATE ai_threads SET last_activity_at = ? WHERE id = ? AND workspace_id = ?",
                    (now, thread_id, workspace_id),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except Exception as exc:
        _best_effort_mark_capture_failed(interaction_id, flow_id, exc)

    return AIThreadSubmitRead(
        interaction=_read_interaction(
            workspace_id=workspace_id,
            thread_id=thread_id,
            interaction_id=interaction_id,
        )
    )


def _find_existing_interaction(
    *, workspace_id: str, thread_id: str, request_id: str, request_digest: str
) -> str | None:
    with open_sqlite_connection() as connection:
        _require_thread(connection, workspace_id, thread_id)
        row = connection.execute(
            "SELECT id, request_digest FROM ai_thread_interactions WHERE thread_id = ? AND request_id = ?",
            (thread_id, request_id),
        ).fetchone()
    if row is None:
        return None
    if row["request_digest"] != request_digest:
        raise AIThreadConflictError("request_id is already bound to different submit semantics")
    return str(row["id"])


def _context_blocks_for_new_submit(workspace_id: str, payload: AIThreadSubmit) -> list[dict] | None:
    blocks: list[dict] | None = None
    if payload.context_selection is not None:
        selection = ContextSelectionSpec(**payload.context_selection.model_dump())
        try:
            bundle = build_workspace_context_bundle(workspace_id, selection=selection)
        except ValueError as exc:
            raise AIThreadError(str(exc)) from exc
        if bundle.context_digest != payload.expected_context_digest:
            raise AIThreadConflictError("context pack changed since preview")
        # Preserve the exact server-rebuilt legacy block list when Jarvis exact-ref
        # context is absent so spec 090/091 callers retain their established semantics.
        blocks = bundle.blocks

    if payload.jarvis_context is not None:
        if payload.jarvis_context.workspace_id != workspace_id:
            raise AIThreadConflictError("Jarvis context workspace does not match thread workspace")
        if payload.jarvis_context.added_context_refs:
            effective_route_class = resolve_effective_route_class(
                task_kind=payload.task_kind,
                route_class=payload.route_class,
            )
            if not effective_route_class.startswith("local:"):
                raise AIThreadConflictError(
                    "exact-ref Jarvis context is unavailable for external routes in spec 111"
                )
        try:
            preview = require_dispatchable_preview(
                payload.jarvis_context,
                payload.expected_jarvis_context_digest or "",
            )
        except JarvisContextConflictError as exc:
            raise AIThreadConflictError(str(exc)) from exc
        if blocks is None:
            blocks = preview.blocks
        elif preview.blocks:
            blocks = [*blocks, *preview.blocks]

    return blocks or None


def _reserve_interaction(
    *,
    workspace_id: str,
    thread_id: str,
    request_id: str,
    request_digest: str,
    prompt: str,
    payload: AIThreadSubmit,
) -> str | None:
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _require_thread(connection, workspace_id, thread_id)
            duplicate = connection.execute(
                "SELECT id, request_digest FROM ai_thread_interactions WHERE thread_id = ? AND request_id = ?",
                (thread_id, request_id),
            ).fetchone()
            if duplicate is not None:
                if duplicate["request_digest"] != request_digest:
                    raise AIThreadConflictError(
                        "request_id is already bound to different submit semantics"
                    )
                connection.commit()
                return str(duplicate["id"])

            index_row = connection.execute(
                "SELECT COALESCE(MAX(interaction_index), -1) + 1 AS next_index "
                "FROM ai_thread_interactions WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
            flow_id = create_flow_in_transaction(
                connection,
                task_kind=payload.task_kind,
                requested_route_class=payload.route_class,
                workspace_id=workspace_id,
            )
            interaction_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO ai_thread_interactions (
                    id, thread_id, request_id, request_digest, interaction_index,
                    user_text, flow_id, persistence_state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'reserved', ?, ?)
                """,
                (
                    interaction_id,
                    thread_id,
                    request_id,
                    request_digest,
                    int(index_row["next_index"]),
                    prompt,
                    flow_id,
                    now,
                    now,
                ),
            )
            connection.commit()
            return None
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise AIThreadConflictError("thread interaction reservation conflicted") from exc
        except Exception:
            connection.rollback()
            raise


def _mark_reserved_dispatching(
    *,
    workspace_id: str,
    thread_id: str,
    request_id: str,
    request_digest: str,
) -> tuple[str, str]:
    with open_sqlite_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _require_thread(connection, workspace_id, thread_id)
            row = connection.execute(
                """
                SELECT id, flow_id, request_digest, persistence_state
                FROM ai_thread_interactions
                WHERE thread_id = ? AND request_id = ?
                """,
                (thread_id, request_id),
            ).fetchone()
            if row is None or row["request_digest"] != request_digest:
                raise AIThreadConflictError("reserved interaction identity changed")
            if row["persistence_state"] != "reserved":
                raise AIThreadConflictError("reserved interaction was already dispatched")
            updated = connection.execute(
                """
                UPDATE ai_thread_interactions
                SET persistence_state = 'dispatching', updated_at = ?
                WHERE id = ? AND persistence_state = 'reserved'
                """,
                (utc_now(), row["id"]),
            )
            if updated.rowcount != 1:
                raise AIThreadConflictError("interaction dispatch state changed concurrently")
            connection.commit()
            return str(row["id"]), str(row["flow_id"])
        except Exception:
            connection.rollback()
            raise


_INTERACTION_SELECT = """
SELECT
    interaction.id,
    interaction.request_id,
    interaction.interaction_index,
    interaction.user_text,
    interaction.assistant_text,
    interaction.assistant_text_truncated,
    interaction.flow_id,
    interaction.persistence_state,
    interaction.persistence_error,
    interaction.created_at,
    interaction.updated_at,
    flow.state AS flow_state,
    flow.terminal_reason,
    flow.attempt_count,
    flow.terminal_attempt_id,
    capture.proposal_ids_json
FROM ai_thread_interactions AS interaction
JOIN ai_flows AS flow ON flow.id = interaction.flow_id
LEFT JOIN ai_flow_record_captures AS capture ON capture.flow_id = interaction.flow_id
"""


def _read_interaction(
    *, workspace_id: str, thread_id: str, interaction_id: str
) -> AIThreadInteractionRead:
    with open_sqlite_connection() as connection:
        _require_thread(connection, workspace_id, thread_id)
        row = connection.execute(
            _INTERACTION_SELECT + " WHERE interaction.id = ? AND interaction.thread_id = ?",
            (interaction_id, thread_id),
        ).fetchone()
    if row is None:
        raise AIThreadNotFoundError("thread interaction is not readable")
    return _interaction_from_row(row)


def _thread_summary(thread_id: str, workspace_id: str) -> AIThreadSummary:
    with open_sqlite_connection() as connection:
        row = _require_thread(connection, workspace_id, thread_id)
    return _summary_from_row(row)


def _require_workspace(connection: sqlite3.Connection, workspace_id: str) -> sqlite3.Row:
    row = connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    if row is None:
        raise AIThreadNotFoundError("workspace does not exist")
    return row


def _require_thread(
    connection: sqlite3.Connection, workspace_id: str, thread_id: str
) -> sqlite3.Row:
    _require_workspace(connection, workspace_id)
    row = connection.execute(
        """
        SELECT id, workspace_id, title, created_at, last_activity_at
        FROM ai_threads
        WHERE id = ? AND workspace_id = ?
        """,
        (thread_id, workspace_id),
    ).fetchone()
    if row is None:
        raise AIThreadNotFoundError("thread does not exist in the requested workspace")
    return row


def _summary_from_row(row: sqlite3.Row) -> AIThreadSummary:
    return AIThreadSummary(
        id=str(row["id"]),
        workspace_id=str(row["workspace_id"]),
        title=row["title"],
        created_at=str(row["created_at"]),
        last_activity_at=str(row["last_activity_at"]),
    )


def _interaction_from_row(row: sqlite3.Row) -> AIThreadInteractionRead:
    proposal_ids = _proposal_ids(row["proposal_ids_json"])
    return AIThreadInteractionRead(
        id=str(row["id"]),
        request_id=str(row["request_id"]),
        interaction_index=int(row["interaction_index"]),
        user_text=str(row["user_text"]),
        assistant_text=row["assistant_text"],
        assistant_text_truncated=bool(row["assistant_text_truncated"]),
        flow_id=str(row["flow_id"]),
        persistence_state=str(row["persistence_state"]),
        persistence_error=row["persistence_error"],
        flow_state=str(row["flow_state"]),
        terminal_reason=row["terminal_reason"],
        attempt_count=int(row["attempt_count"]),
        terminal_attempt_id=row["terminal_attempt_id"],
        proposal_ids=proposal_ids[:_MAX_PROPOSAL_IDS],
        proposal_count=len(proposal_ids),
        proposals_truncated=len(proposal_ids) > _MAX_PROPOSAL_IDS,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _proposal_ids(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str):
        raise AIThreadError("canonical proposal capture is malformed")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise AIThreadError("canonical proposal capture is malformed") from exc
    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise AIThreadError("canonical proposal capture is malformed")
    return parsed


def _assistant_snapshot(value: str | None) -> tuple[str | None, bool]:
    if value is None:
        return None, False
    if len(value) <= _MAX_ASSISTANT:
        return value, False
    return value[:_MAX_ASSISTANT], True


def _best_effort_mark_capture_failed(interaction_id: str, flow_id: str, exc: Exception) -> None:
    diagnostic = f"assistant_snapshot_persistence_failed:{type(exc).__name__}"[:_MAX_DIAGNOSTIC]
    try:
        with open_sqlite_connection() as connection:
            connection.execute(
                """
                UPDATE ai_thread_interactions
                SET persistence_state = 'capture_failed', persistence_error = ?, updated_at = ?
                WHERE id = ? AND flow_id = ? AND persistence_state = 'dispatching'
                """,
                (diagnostic, utc_now(), interaction_id, flow_id),
            )
            connection.commit()
    except Exception:
        return


def _safe_id(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID_RE.fullmatch(value):
        raise AIThreadError(f"{field} is malformed")
    return value


def _bounded_required_text(value: object, maximum: int, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise AIThreadError(f"{field} is empty or exceeds {maximum} code points")
    return value


def _bounded_optional_text(value: object, maximum: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > maximum:
        raise AIThreadError(f"{field} exceeds {maximum} code points")
    return value


def _bounded_limit(value: int, *, default: int, maximum: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > maximum:
        raise AIThreadError(f"limit must be between 1 and {maximum}")
    return value