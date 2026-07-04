"""Persistence helpers for the BLUECAD candidate and attempt ledger."""

from __future__ import annotations

import hashlib
import sqlite3
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.core.repository import row_to_model, rows_to_models
from app.modules.bluecad.models import BluecadAttemptRead, BluecadCandidateRead, BluecadLoopConfig
from app.modules.events.service import utc_now


def brief_digest(brief_text: str) -> str:
    return "sha256:" + hashlib.sha256(brief_text.encode("utf-8")).hexdigest()


def create_candidate_record(workspace_id: str, brief_text: str, loop_config: BluecadLoopConfig) -> BluecadCandidateRead:
    now = utc_now()
    candidate_id = str(uuid4())
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        connection.execute(
            """
            INSERT INTO bluecad_candidates (
                id, workspace_id, brief_text, brief_digest, status, parked_reason,
                spec_artifact_id, glb_artifact_id, report_artifact_id,
                promoted_decision_id, origin, parent_candidate_id,
                loop_config_json, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, 'generating', NULL, NULL, NULL, NULL, NULL,
                'ai', NULL, ?, ?, ?, NULL)
            """,
            (candidate_id, workspace_id, brief_text, brief_digest(brief_text), loop_config.model_dump_json(), now, now),
        )
        connection.commit()
    return get_candidate(workspace_id, candidate_id)  # type: ignore[return-value]


def park_candidate(candidate_id: str, reason: str, *, notes: str | None = None) -> None:
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE bluecad_candidates
            SET status = 'parked', parked_reason = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (reason, notes, now, candidate_id),
        )
        connection.commit()


def archive_candidate(workspace_id: str, candidate_id: str) -> BluecadCandidateRead | None:
    now = utc_now()
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT id FROM bluecad_candidates WHERE workspace_id = ? AND id = ?",
            (workspace_id, candidate_id),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE bluecad_candidates SET status = 'archived', updated_at = ? WHERE id = ?",
            (now, candidate_id),
        )
        connection.commit()
    return get_candidate(workspace_id, candidate_id)


def mark_promoted(workspace_id: str, candidate_id: str, decision_id: str) -> BluecadCandidateRead:
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE bluecad_candidates SET promoted_decision_id = ?, updated_at = ? WHERE workspace_id = ? AND id = ?",
            (decision_id, now, workspace_id, candidate_id),
        )
        connection.commit()
    return get_candidate(workspace_id, candidate_id)  # type: ignore[return-value]


def list_candidates(workspace_id: str) -> list[BluecadCandidateRead]:
    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        rows = connection.execute(
            "SELECT * FROM bluecad_candidates WHERE workspace_id = ? ORDER BY created_at DESC",
            (workspace_id,),
        ).fetchall()
    return [_with_attempts(row_to_model(row, BluecadCandidateRead)) for row in rows]


def get_candidate(workspace_id: str, candidate_id: str) -> BluecadCandidateRead | None:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT * FROM bluecad_candidates WHERE workspace_id = ? AND id = ?",
            (workspace_id, candidate_id),
        ).fetchone()
    if row is None:
        return None
    return _with_attempts(row_to_model(row, BluecadCandidateRead))


def list_attempts(candidate_id: str) -> list[BluecadAttemptRead]:
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM bluecad_attempts WHERE candidate_id = ? ORDER BY attempt_no ASC",
            (candidate_id,),
        ).fetchall()
    return rows_to_models(rows, BluecadAttemptRead)


def _with_attempts(candidate: BluecadCandidateRead) -> BluecadCandidateRead:
    data = candidate.model_dump()
    data["attempts"] = list_attempts(candidate.id)
    return BluecadCandidateRead(**data)


def _require_workspace(connection: sqlite3.Connection, workspace_id: str) -> None:
    if connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone() is None:
        raise ValueError("Workspace not found.")


class ScriptedFakeBluecadAdapter:
    """Offline stage-1 harness for future loop tests.

    It records prompts and returns scripted response strings without network access.
    Stage 2 wires this through run_ai_task's adapter injection path.
    """

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def next_response(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.responses:
            raise RuntimeError("scripted fake BLUECAD adapter exhausted")
        return self.responses.pop(0)
