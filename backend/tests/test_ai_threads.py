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


def test_context_binding_fields_must_be_supplied_as_a_pair() -> None:
    digest = "sha256:" + "a" * 64
    selection = {"kinds": ["Assumption"]}

    with pytest.raises(ValidationError):
        AIThreadSubmit(
            request_id="context-selection-only",
            prompt="blocked",
            context_selection=selection,
        )
    with pytest.raises(ValidationError):
        AIThreadSubmit(
            request_id="context-digest-only",
            prompt="blocked",
            expected_context_digest=digest,
        )


def test_context_digest_mismatch_fails_before_reservation_or_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    expected = "sha256:" + "a" * 64
    observed_dispatch = False

    def fake_bundle(_workspace_id, *, selection):
        assert _workspace_id == workspace_id
        assert selection.kinds == ["Assumption"]
        return SimpleNamespace(context_digest="sha256:" + "b" * 64, blocks=[{"text": "changed"}])

    def fake_run_ai_task(**_kwargs):
        nonlocal observed_dispatch
        observed_dispatch = True
        raise AssertionError("context mismatch must not dispatch")

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", fake_bundle)
    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)

    with pytest.raises(AIThreadConflictError, match="context pack changed since preview"):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id="context-mismatch",
                prompt="do not dispatch",
                context_selection={"kinds": ["Assumption"]},
                expected_context_digest=expected,
            ),
        )

    assert observed_dispatch is False
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread.id,),
        ).fetchone()["n"] == 0
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_flows WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()["n"] == 0


def test_matching_context_digest_forwards_exact_server_rebuilt_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    digest = "sha256:" + "c" * 64
    blocks = [{"kind": "Assumption", "text": "bounded server block"}]
    captured: dict[str, object] = {}

    def fake_bundle(_workspace_id, *, selection):
        assert _workspace_id == workspace_id
        assert selection.kinds == ["Assumption"]
        return SimpleNamespace(context_digest=digest, blocks=blocks)

    def fake_run_ai_task(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(response=SimpleNamespace(text="context accepted"))

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", fake_bundle)
    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)

    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(
            request_id="context-match",
            prompt="use inspected context",
            context_selection={"kinds": ["Assumption"]},
            expected_context_digest=digest,
        ),
    ).interaction

    assert captured["context_blocks"] is blocks
    assert captured["existing_flow_id"] == interaction.flow_id
    assert captured["workspace_id"] == workspace_id


def test_no_context_legacy_path_does_not_build_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    captured: dict[str, object] = {}

    def unexpected_bundle(*_args, **_kwargs):
        raise AssertionError("legacy no-context submit must not rebuild a context pack")

    def fake_run_ai_task(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(response=SimpleNamespace(text="legacy"))

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", unexpected_bundle)
    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)

    submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(request_id="legacy-no-context", prompt="legacy"),
    )
    assert captured["context_blocks"] is None


def test_context_duplicate_is_read_before_rebuild_after_record_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    digest = "sha256:" + "d" * 64
    payload = AIThreadSubmit(
        request_id="context-duplicate",
        prompt="one execution",
        context_selection={"kinds": ["Assumption"]},
        expected_context_digest=digest,
    )
    build_calls = 0
    dispatch_calls = 0

    def initial_bundle(_workspace_id, *, selection):
        nonlocal build_calls
        build_calls += 1
        return SimpleNamespace(context_digest=digest, blocks=[{"text": "initial"}])

    def fake_run_ai_task(**_kwargs):
        nonlocal dispatch_calls
        dispatch_calls += 1
        return SimpleNamespace(response=SimpleNamespace(text="once"))

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", initial_bundle)
    monkeypatch.setattr(thread_service, "run_ai_task", fake_run_ai_task)
    first = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction

    def drifted_bundle(*_args, **_kwargs):
        raise AssertionError("durable duplicate must be returned before fresh context rebuild")

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", drifted_bundle)
    duplicate = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction

    assert duplicate.id == first.id
    assert duplicate.flow_id == first.flow_id
    assert build_calls == 1
    assert dispatch_calls == 1


def test_context_cross_workspace_submit_fails_before_context_rebuild(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    def unexpected_bundle(*_args, **_kwargs):
        raise AssertionError("foreign-workspace thread must fail before context rebuild")

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", unexpected_bundle)
    with pytest.raises(AIThreadNotFoundError):
        submit_interaction(
            workspace_id="workspace-b",
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id="cross-workspace-context",
                prompt="blocked",
                context_selection={"kinds": ["Assumption"]},
                expected_context_digest="sha256:" + "e" * 64,
            ),
        )


def test_context_drift_race_returns_concurrently_reserved_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    expected_digest = "sha256:" + "f" * 64
    payload = AIThreadSubmit(
        request_id="context-race",
        prompt="race safe",
        context_selection={"kinds": ["Assumption"]},
        expected_context_digest=expected_digest,
    )
    request_digest = thread_service.canonical_digest(
        {
            "prompt": payload.prompt,
            "task_kind": payload.task_kind,
            "route_class": payload.route_class,
            "max_tokens": payload.max_tokens,
            "context_selection": payload.context_selection.model_dump(),
            "expected_context_digest": payload.expected_context_digest,
        }
    )
    builder_calls = 0

    def racing_bundle(_workspace_id, *, selection):
        nonlocal builder_calls
        builder_calls += 1
        duplicate = thread_service._reserve_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            request_id=payload.request_id,
            request_digest=request_digest,
            prompt=payload.prompt,
            payload=payload,
        )
        assert duplicate is None
        return SimpleNamespace(
            context_digest="sha256:" + "0" * 64,
            blocks=[{"text": "drifted"}],
        )

    def unexpected_dispatch(**_kwargs):
        raise AssertionError("losing race must reread durable reservation, not dispatch")

    monkeypatch.setattr(thread_service, "build_workspace_context_bundle", racing_bundle)
    monkeypatch.setattr(thread_service, "run_ai_task", unexpected_dispatch)

    result = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=payload,
    ).interaction

    assert result.request_id == payload.request_id
    assert result.persistence_state == "reserved"
    assert builder_calls == 1
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread.id,),
        ).fetchone()["n"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (result.flow_id,),
        ).fetchone()["n"] == 0


def _jarvis_thread_request(workspace_id: str = "workspace-a", *, version: str = "v1"):
    from app.modules.ai.jarvis_context_models import (
        JarvisContextRequest,
        JarvisExactRef,
        JarvisRouteDescriptor,
    )

    return JarvisContextRequest(
        workspace_id=workspace_id,
        route=JarvisRouteDescriptor(
            route_id="memory-project-basis",
            canonical_path="/memory/project-basis",
        ),
        added_context_refs=[
            JarvisExactRef(
                workspace_id=workspace_id,
                owner="test-owner",
                kind="test-kind",
                id="record-1",
                version=version,
            )
        ],
    )


def _assert_zero_dispatch_state(*, workspace_id: str, thread_id: str) -> None:
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()["n"] == 0
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_flows WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()["n"] == 0
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs",
        ).fetchone()["n"] == 0


def test_jarvis_context_binding_fields_must_be_supplied_as_a_pair() -> None:
    request = _jarvis_thread_request()
    digest = "sha256:" + "1" * 64

    with pytest.raises(ValidationError):
        AIThreadSubmit(
            request_id="jarvis-request-only",
            prompt="blocked",
            jarvis_context=request,
        )
    with pytest.raises(ValidationError):
        AIThreadSubmit(
            request_id="jarvis-digest-only",
            prompt="blocked",
            expected_jarvis_context_digest=digest,
        )


def test_jarvis_owner_identity_drift_fails_before_reservation_or_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.ai.jarvis_context import JarvisContextConflictError

    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))

    def drifted_preview(*_args, **_kwargs):
        raise JarvisContextConflictError("Jarvis context changed since inspected preview")

    def unexpected_dispatch(**_kwargs):
        raise AssertionError("stale inspected Jarvis context must not dispatch")

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", drifted_preview)
    monkeypatch.setattr(thread_service, "run_ai_task", unexpected_dispatch)

    with pytest.raises(AIThreadConflictError, match="changed since inspected preview"):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id="jarvis-drift",
                prompt="blocked",
                route_class="local:fast",
                jarvis_context=_jarvis_thread_request(workspace_id),
                expected_jarvis_context_digest="sha256:" + "2" * 64,
            ),
        )
    _assert_zero_dispatch_state(workspace_id=workspace_id, thread_id=thread.id)


def test_jarvis_context_workspace_mismatch_is_zero_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))

    def unexpected_preview(*_args, **_kwargs):
        raise AssertionError("workspace mismatch must fail before Jarvis preview rebuild")

    def unexpected_dispatch(**_kwargs):
        raise AssertionError("workspace mismatch must not dispatch")

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", unexpected_preview)
    monkeypatch.setattr(thread_service, "run_ai_task", unexpected_dispatch)

    with pytest.raises(AIThreadConflictError, match="workspace does not match"):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id="jarvis-workspace-mismatch",
                prompt="blocked",
                route_class="local:fast",
                jarvis_context=_jarvis_thread_request("workspace-b"),
                expected_jarvis_context_digest="sha256:" + "3" * 64,
            ),
        )
    _assert_zero_dispatch_state(workspace_id=workspace_id, thread_id=thread.id)


@pytest.mark.parametrize("resolution_state", ["unknown", "stale", "unavailable"])
def test_jarvis_noncurrent_exact_ref_is_zero_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    resolution_state: str,
) -> None:
    from app.modules.ai.jarvis_context import JarvisContextConflictError

    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))

    def nondispatchable_preview(*_args, **_kwargs):
        raise JarvisContextConflictError(
            f"Jarvis context contains {resolution_state} exact refs"
        )

    def unexpected_dispatch(**_kwargs):
        raise AssertionError("non-current exact ref must not dispatch")

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", nondispatchable_preview)
    monkeypatch.setattr(thread_service, "run_ai_task", unexpected_dispatch)

    with pytest.raises(AIThreadConflictError, match=resolution_state):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id=f"jarvis-{resolution_state}",
                prompt="blocked",
                route_class="local:fast",
                jarvis_context=_jarvis_thread_request(workspace_id),
                expected_jarvis_context_digest="sha256:" + "4" * 64,
            ),
        )
    _assert_zero_dispatch_state(workspace_id=workspace_id, thread_id=thread.id)


def test_jarvis_added_exact_refs_reject_external_route_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))

    def unexpected_preview(*_args, **_kwargs):
        raise AssertionError("external exact-ref route must fail before preview dispatchability")

    def unexpected_dispatch(**_kwargs):
        raise AssertionError("external exact-ref route must not dispatch")

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", unexpected_preview)
    monkeypatch.setattr(thread_service, "run_ai_task", unexpected_dispatch)

    with pytest.raises(AIThreadConflictError, match="unavailable for external routes"):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=AIThreadSubmit(
                request_id="jarvis-external",
                prompt="blocked",
                route_class="cloud:smart",
                jarvis_context=_jarvis_thread_request(workspace_id),
                expected_jarvis_context_digest="sha256:" + "5" * 64,
            ),
        )
    _assert_zero_dispatch_state(workspace_id=workspace_id, thread_id=thread.id)


def test_jarvis_local_safe_route_reuses_ai_execution_and_thread_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    request = _jarvis_thread_request(workspace_id)
    digest = "sha256:" + "6" * 64
    blocks = [
        {
            "source": "jarvis:test-owner:test-kind",
            "type": "jarvis_exact_ref",
            "id": "record-1",
            "content": '{"value":"inspected"}',
        }
    ]
    preview_calls = 0

    def current_preview(context_request, expected_digest):
        nonlocal preview_calls
        preview_calls += 1
        assert context_request == request
        assert expected_digest == digest
        return SimpleNamespace(blocks=blocks)

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", current_preview)

    interaction = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=AIThreadSubmit(
            request_id="jarvis-local-safe",
            prompt="use inspected exact ref",
            route_class="local:fake",
            jarvis_context=request,
            expected_jarvis_context_digest=digest,
        ),
    ).interaction

    assert preview_calls == 1
    assert interaction.persistence_state == "captured"
    assert interaction.flow_state == "complete"
    assert interaction.attempt_count == 1
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (interaction.flow_id,),
        ).fetchone()["n"] == 1


def test_jarvis_unchanged_retry_is_durable_and_dispatches_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    request = _jarvis_thread_request(workspace_id)
    digest = "sha256:" + "7" * 64
    preview_calls = 0

    def current_preview(_request, _digest):
        nonlocal preview_calls
        preview_calls += 1
        return SimpleNamespace(
            blocks=[
                {
                    "source": "jarvis:test-owner:test-kind",
                    "type": "jarvis_exact_ref",
                    "id": "record-1",
                    "content": "current",
                }
            ]
        )

    monkeypatch.setattr(thread_service, "require_dispatchable_preview", current_preview)
    payload = AIThreadSubmit(
        request_id="jarvis-idempotent",
        prompt="one dispatch",
        route_class="local:fast",
        jarvis_context=request,
        expected_jarvis_context_digest=digest,
    )

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

    assert duplicate.id == first.id
    assert duplicate.flow_id == first.flow_id
    assert preview_calls == 1
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (first.flow_id,),
        ).fetchone()["n"] == 1


@pytest.mark.parametrize("changed_semantics", ["route", "ref", "digest"])
def test_jarvis_request_id_rejects_changed_bound_semantics(
    monkeypatch: pytest.MonkeyPatch,
    changed_semantics: str,
) -> None:
    workspace_id = "workspace-a"
    _bootstrap_workspace(workspace_id)
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id))
    request = _jarvis_thread_request(workspace_id, version="v1")
    digest = "sha256:" + "8" * 64

    monkeypatch.setattr(
        thread_service,
        "require_dispatchable_preview",
        lambda *_args, **_kwargs: SimpleNamespace(
            blocks=[
                {
                    "source": "jarvis:test-owner:test-kind",
                    "type": "jarvis_exact_ref",
                    "id": "record-1",
                    "content": "current",
                }
            ]
        ),
    )
    first_payload = AIThreadSubmit(
        request_id="jarvis-immutable",
        prompt="immutable semantics",
        route_class="local:fast",
        jarvis_context=request,
        expected_jarvis_context_digest=digest,
    )
    first = submit_interaction(
        workspace_id=workspace_id,
        thread_id=thread.id,
        payload=first_payload,
    ).interaction

    changed_route = "local:smart" if changed_semantics == "route" else "local:fast"
    changed_request = (
        _jarvis_thread_request(workspace_id, version="v2")
        if changed_semantics == "ref"
        else request
    )
    changed_digest = "sha256:" + "9" * 64 if changed_semantics == "digest" else digest
    second_payload = AIThreadSubmit(
        request_id="jarvis-immutable",
        prompt="immutable semantics",
        route_class=changed_route,
        jarvis_context=changed_request,
        expected_jarvis_context_digest=changed_digest,
    )

    with pytest.raises(AIThreadConflictError, match="different submit semantics"):
        submit_interaction(
            workspace_id=workspace_id,
            thread_id=thread.id,
            payload=second_payload,
        )
    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_thread_interactions WHERE thread_id = ?",
            (thread.id,),
        ).fetchone()["n"] == 1
        assert connection.execute(
            "SELECT COUNT(*) AS n FROM ai_jobs WHERE flow_id = ?",
            (first.flow_id,),
        ).fetchone()["n"] == 1
