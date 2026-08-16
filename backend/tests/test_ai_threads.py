from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import app.modules.ai.thread_service as thread_service
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.execution import run_ai_task
from app.modules.ai.settings import ensure_ai_settings
from app.modules.ai.thread_models import AIThreadCreate, AIThreadSubmit
from app.modules.ai.thread_service import (
    AIThreadConflictError,
    AIThreadNotFoundError,
    create_thread,
    get_thread,
    submit_interaction,
)
from app.modules.ai.token_flow_service import (
    TokenFlowConflictError,
    create_flow,
    validate_existing_flow_for_execution,
)
from app.modules.events.service import utc_now


def _bootstrap_workspace(workspace_id: str) -> None:
    initialize_database()
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (id, name, slug, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, workspace_id, workspace_id, now, now),
        )
        connection.commit()
    ensure_ai_settings()


def test_thread_submit_local_fake_is_durable_and_idempotent() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id, title="Test thread"))
    payload = AIThreadSubmit(request_id="request-1", prompt="Return a bounded test response.")

    first = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction
    duplicate = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction

    assert first.id == duplicate.id
    assert first.flow_id == duplicate.flow_id
    assert first.persistence_state == "captured"
    assert first.flow_state == "complete"
    assert first.attempt_count == 1
    assert first.assistant_text is not None

    with open_sqlite_connection() as connection:
        interaction_count = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread.id,),
        ).fetchone()["n"]
        job_count = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (first.flow_id,),
        ).fetchone()["n"]
    assert interaction_count == 1
    assert job_count == 1


def test_same_request_id_with_different_semantics_fails_closed() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="first"),
    )

    with pytest.raises(AIThreadConflictError):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(request_id="request-1", prompt="different"),
        )

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread.id,),
        ).fetchone()["n"] == 1


def test_cross_workspace_thread_read_fails_closed() -> None:
    _bootstrap_workspace("workspace-a")
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO workspaces (id, name, slug, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("workspace-b", "workspace-b", "workspace-b", now, now),
        )
        connection.commit()
    thread = create_thread(AIThreadCreate(workspace_id="workspace-a"))

    with pytest.raises(AIThreadNotFoundError):
        get_thread(workspace_id="workspace-b", thread_id=thread.id)


def test_precreated_flow_rejects_identity_drift_and_reuse() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    flow = create_flow(
        task_kind="general",
        requested_route_class="local:fast",
        workspace_id=workspace_id,
    )
    flow_id = str(flow["id"])

    validated = validate_existing_flow_for_execution(
        flow_id,
        task_kind="general",
        requested_route_class="local:fast",
        workspace_id=workspace_id,
    )
    assert validated["attempt_count"] == 0

    with pytest.raises(TokenFlowConflictError):
        validate_existing_flow_for_execution(
            flow_id,
            task_kind="general",
            requested_route_class="local:fast",
            workspace_id="workspace-b",
        )
    with pytest.raises(TokenFlowConflictError):
        validate_existing_flow_for_execution(
            flow_id,
            task_kind="review",
            requested_route_class="local:fast",
            workspace_id=workspace_id,
        )
    with pytest.raises(TokenFlowConflictError):
        validate_existing_flow_for_execution(
            flow_id,
            task_kind="general",
            requested_route_class="local:smart",
            workspace_id=workspace_id,
        )

    outcome = run_ai_task(
        user_prompt="one execution only",
        task_kind="general",
        route_class="local:fast",
        workspace_id=workspace_id,
        existing_flow_id=flow_id,
    )
    assert outcome.flow_id == flow_id

    with pytest.raises(TokenFlowConflictError):
        validate_existing_flow_for_execution(
            flow_id,
            task_kind="general",
            requested_route_class="local:fast",
            workspace_id=workspace_id,
        )

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (flow_id,),
        ).fetchone()["n"] == 1


def test_post_execution_snapshot_failure_never_redispatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    payload = AIThreadSubmit(request_id="request-1", prompt="complete once")
    original_open = thread_service.open_sqlite_connection
    open_count = 0

    @contextmanager
    def flaky_thread_connection():
        nonlocal open_count
        open_count += 1
        if open_count == 3:
            raise sqlite3.OperationalError("forced post-execution thread snapshot failure")
        with original_open() as connection:
            yield connection

    monkeypatch.setattr(thread_service, "open_sqlite_connection", flaky_thread_connection)

    first = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction
    duplicate = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction

    assert first.id == duplicate.id
    assert first.flow_id == duplicate.flow_id
    assert first.flow_state == "complete"
    assert first.attempt_count == 1
    assert first.persistence_state == "capture_failed"
    assert first.assistant_text is None

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (first.flow_id,),
        ).fetchone()["n"] == 1


def test_thread_submit_never_serializes_prior_history_as_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="historical turn"),
    )
    captured: dict[str, object] = {}

    def fake_run_ai_task(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(response=SimpleNamespace(text="bounded mock"))

    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)
    submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-2", prompt="current turn only"),
    )

    assert captured["user_prompt"] == "current turn only"
    assert captured["context_blocks"] is None
    assert "historical turn" not in str(captured)
