from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import app.modules.ai.thread_service as thread_service
from app.core.database import initialize_database, open_sqlite_connection
from app.modules.ai.execution import run_ai_task
from app.modules.ai.settings import ensure_ai_settings
from app.modules.ai.thread_models import AIThreadCreate, AIThreadSubmit
from app.modules.ai.thread_service import (
    AIThreadConflictError,
    AIThreadError,
    AIThreadNotFoundError,
    create_thread,
    get_thread,
    list_threads,
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
    with pytest.raises(AIThreadNotFoundError):
        submit_interaction(
            workspace_id="workspace-b",
            thread_id=thread.id,
            payload=AIThreadSubmit(request_id="request-1", prompt="blocked"),
        )


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
        # 091 adds an idempotency lookup before reservation. The fourth open is
        # still the semantic target: post-execution assistant snapshot capture.
        if open_count == 4:
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


def test_schema_initialization_is_idempotent_and_thread_bounds_are_enforced() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    initialize_database()
    with open_sqlite_connection() as connection:
        names = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'ai_thread%'"
            ).fetchall()
        }
    assert names == {"ai_threads", "ai_thread_interactions"}

    create_thread(AIThreadCreate(workspace_id=workspace_id, title="x" * 120))
    with pytest.raises(ValidationError):
        AIThreadCreate(workspace_id=workspace_id, title="x" * 121)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    with pytest.raises(ValidationError):
        AIThreadSubmit(request_id="request-long", prompt="x" * 12_001)
    with pytest.raises(AIThreadError):
        list_threads(workspace_id=workspace_id, limit=51)
    with pytest.raises(AIThreadError):
        get_thread(workspace_id=workspace_id, thread_id=thread.id, interaction_limit=101)


def test_thread_and_interaction_ordering_and_read_limit_are_deterministic() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    first = create_thread(AIThreadCreate(workspace_id=workspace_id, title="first"))
    second = create_thread(AIThreadCreate(workspace_id=workspace_id, title="second"))
    with open_sqlite_connection() as connection:
        connection.execute(
            "UPDATE ai_threads SET last_activity_at = ? WHERE id = ?",
            ("2026-01-01T00:00:00Z", first.id),
        )
        connection.execute(
            "UPDATE ai_threads SET last_activity_at = ? WHERE id = ?",
            ("2026-01-02T00:00:00Z", second.id),
        )
        connection.commit()
    assert [item.id for item in list_threads(workspace_id=workspace_id).threads[:2]] == [
        second.id,
        first.id,
    ]

    submit_interaction(
        workspace_id=workspace_id,
        thread_id=first.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="one"),
    )
    submit_interaction(
        workspace_id=workspace_id,
        thread_id=first.id,
        payload=AIThreadSubmit(request_id="request-2", prompt="two"),
    )
    detail = get_thread(workspace_id=workspace_id, thread_id=first.id, interaction_limit=1)
    assert detail.has_older is True
    assert len(detail.interactions) == 1
    assert detail.interactions[0].request_id == "request-2"


def test_reservation_and_flow_exist_before_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    observed: dict[str, object] = {}

    def fake_run_ai_task(**kwargs):
        flow_id = str(kwargs["existing_flow_id"])
        with open_sqlite_connection() as connection:
            interaction = connection.execute(
                "SELECT persistence_state, flow_id FROM ai_thread_interactions WHERE thread_id = ?",
                (thread.id,),
            ).fetchone()
            flow = connection.execute(
                "SELECT state, attempt_count FROM ai_flows WHERE id = ?",
                (flow_id,),
            ).fetchone()
        observed["interaction"] = dict(interaction)
        observed["flow"] = dict(flow)
        return SimpleNamespace(response=SimpleNamespace(text="reserved before dispatch"))

    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)
    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="inspect reservation"),
    ).interaction

    assert observed["interaction"] == {
        "persistence_state": "dispatching",
        "flow_id": interaction.flow_id,
    }
    assert observed["flow"] == {"state": "running", "attempt_count": 0}


def test_assistant_snapshot_is_bounded_and_marked_truncated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))

    def fake_run_ai_task(**_kwargs):
        return SimpleNamespace(response=SimpleNamespace(text="x" * 131_073))

    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)
    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="long response"),
    ).interaction
    assert interaction.assistant_text_truncated is True
    assert interaction.assistant_text is not None
    assert len(interaction.assistant_text) == 131_072


def test_proposal_references_are_read_from_canonical_flow_capture() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="capture proposal refs"),
    ).interaction
    assert interaction.terminal_attempt_id is not None
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_flow_record_captures (
                flow_id, terminal_attempt_id, final_output_digest,
                proposal_ids_json, parse_error, created_at
            ) VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (
                interaction.flow_id,
                interaction.terminal_attempt_id,
                "digest-test",
                json.dumps(["proposal-a", "proposal-b"]),
                utc_now(),
            ),
        )
        connection.commit()
    refreshed = get_thread(workspace_id=workspace_id, thread_id=thread.id).interactions[0]
    assert refreshed.proposal_ids == ["proposal-a", "proposal-b"]
    assert refreshed.proposal_count == 2
    assert refreshed.proposals_truncated is False


def test_flow_terminal_states_remain_distinct_in_thread_read_model() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    expected = {
        "confirmation_required": "confirmation",
        "partial_terminal": "partial",
        "failed_terminal": "failed",
        "complete": "complete",
    }
    for index, (state, reason) in enumerate(expected.items()):
        thread = create_thread(AIThreadCreate(workspace_id=workspace_id, title=state))
        interaction = submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(request_id=f"request-{index}", prompt=state),
        ).interaction
        with open_sqlite_connection() as connection:
            connection.execute(
                "UPDATE ai_flows SET state = ?, terminal_reason = ? WHERE id = ?",
                (state, reason, interaction.flow_id),
            )
            connection.commit()
        refreshed = get_thread(workspace_id=workspace_id, thread_id=thread.id).interactions[0]
        assert refreshed.flow_state == state
        assert refreshed.terminal_reason == reason


def test_thread_schema_rollback_does_not_delete_canonical_flow_or_job() -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="request-1", prompt="rollback isolation"),
    ).interaction
    with open_sqlite_connection() as connection:
        job_count_before = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?", (interaction.flow_id,)
        ).fetchone()["n"]
        connection.execute("DROP TABLE ai_thread_interactions")
        connection.execute("DROP TABLE ai_threads")
        flow_count_after = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_flows WHERE id = ?", (interaction.flow_id,)
        ).fetchone()["n"]
        job_count_after = connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?", (interaction.flow_id,)
        ).fetchone()["n"]
        connection.commit()
    assert job_count_before == 1
    assert flow_count_after == 1
    assert job_count_after == 1
