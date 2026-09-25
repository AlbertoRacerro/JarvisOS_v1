from __future__ import annotations

import importlib
import json
import os
import socket
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.modules.agents.hermes.supervisor as hermes_supervisor_module
from app.modules.agents.hermes.broker_mcp import _reply
from app.modules.agents.hermes.session_pool import HermesSessionPool
from app.modules.agents.hermes.supervisor import (
    HermesSupervisor,
    bind_session,
    current_mapping,
    dispatch_tool,
    infer_envelope,
    project_event,
    run_governed_inference,
    worker_environment,
)
from app.modules.agents.hermes.worker_shim import (
    AUXILIARY_TASKS,
    DISABLED_TOOLSETS,
    ENABLED_TOOLSETS,
    completion_message,
    pinned_config,
)
from app.modules.ai.agent_contracts import (
    AgentControlCommand,
    AgentEvent,
    AgentSessionRef,
    CapabilityGrantRef,
    CapabilityScope,
    InferenceEnvelope,
    StructuredToolCall,
    StructuredToolResult,
    check_control_target,
)
from app.modules.ai.context_builder import canonical_digest
from app.modules.ai.jarvis_context_models import SourceRef

NOW = datetime.now(UTC)
SESSION = AgentSessionRef(jarvis_thread_id="thread-1", hermes_session_id="hermes-1",
                          profile_id="profile-1", workspace_id="workspace-1", generation=1,
                          upstream_revision="d337b736aa1e8ebecfab043842d13e4a2d2f48a3")


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE ai_threads (id TEXT PRIMARY KEY, workspace_id TEXT, last_activity_at TEXT)")
    connection.execute("INSERT INTO ai_threads VALUES ('thread-1', 'workspace-1', '2000-01-01T00:00:00+00:00')")
    connection.execute("CREATE TABLE ai_thread_interactions (id TEXT, thread_id TEXT, request_id TEXT, "
                       "request_digest TEXT, interaction_index INTEGER, user_text TEXT, assistant_text TEXT, "
                       "assistant_text_truncated INTEGER, flow_id TEXT, persistence_state TEXT, "
                       "created_at TEXT, updated_at TEXT)")
    connection.execute("CREATE TABLE events (id TEXT PRIMARY KEY, workspace_id TEXT, event_type TEXT, "
                       "actor TEXT, target_type TEXT, target_id TEXT, payload TEXT, created_at TEXT)")
    return connection


def _frame() -> dict[str, Any]:
    return {"type": "relay_request", "id": "request-1", "session_ref": SESSION.model_dump(mode="json"),
            "messages": [{"role": "user", "content": "hello"}], "model_candidate": "other-model"}


def test_stdio_frame_round_trips() -> None:
    frames = [
        {"type": "ready", "upstream_revision": SESSION.upstream_revision},
        {"type": "bind", "id": "bind-1", "session_ref": SESSION.model_dump(mode="json")},
        {"type": "turn", "id": "turn-1", "prompt": "hello"},
        {"type": "interrupt", "id": "interrupt-1"},
        {"type": "resume", "id": "resume-1"},
        {"type": "close", "id": "close-1"},
        {"type": "ack", "id": "bind-1"},
        _frame(),
        {"type": "relay_result", "id": "request-1", "status": "success", "text": "hello"},
        {"type": "tool_call", "id": "tool-1", "session_ref": SESSION.model_dump(mode="json"),
         "arguments": {"grant_id": "grant-1", "request": {}}},
        {"type": "tool_result", "id": "tool-1", "tool_result": {"status": "refused"}},
        {"type": "agent_event", "event": AgentEvent(
            event_id="event-1", session_ref=SESSION, sequence=0,
            kind="turn.started", occurred_at=NOW).model_dump(mode="json")},
        {"type": "turn_result", "id": "turn-1", "status": "success",
         "final_response": "hello", "completed": True},
    ]
    assert [json.loads(json.dumps(frame)) for frame in frames] == frames


def test_frozen_wire_round_trip_and_relay_boundary() -> None:
    envelope = infer_envelope(_frame())
    assert envelope.agent_session == SESSION
    assert envelope.cancellation_id == SESSION.hermes_session_id
    assert envelope.prompt == '[{"role": "user", "content": "hello"}]'
    assert InferenceEnvelope.model_validate_json(envelope.model_dump_json()) == envelope
    event = AgentEvent(event_id="event-1", session_ref=SESSION, sequence=0,
                       kind="turn.started", occurred_at=NOW)
    assert AgentEvent.model_validate_json(event.model_dump_json()) == event
    call = StructuredToolCall(call_id="call-1", capability_id="jarvis.context_preview", grant_id="grant-1",
                              correlation_id="corr-1", session_ref=SESSION, requested_at=NOW,
                              deadline_at=NOW + timedelta(minutes=1))
    assert StructuredToolCall.model_validate_json(call.model_dump_json()) == call
    result = StructuredToolResult(call_id="call-1", capability_id=call.capability_id,
                                  status="refused", error_code="capability_denied", completed_at=NOW)
    assert StructuredToolResult.model_validate_json(result.model_dump_json()) == result
    command = AgentControlCommand(command_id="cmd-wire", kind="interrupt", correlation_id="corr-1",
                                  jarvis_thread_id="thread-1", workspace_id="workspace-1",
                                  profile_id="profile-1", hermes_session_id="hermes-1",
                                  expected_generation=1, requested_at=NOW,
                                  deadline_at=NOW + timedelta(minutes=1))
    assert AgentControlCommand.model_validate_json(command.model_dump_json()) == command
    grant = CapabilityGrantRef(grant_id="grant-wire", capability_id="jarvis.context_preview",
                               issuer="operator", scope=CapabilityScope(workspace_id="workspace-1"),
                               issued_at=NOW, expires_at=NOW + timedelta(minutes=1))
    assert CapabilityGrantRef.model_validate_json(grant.model_dump_json()) == grant
    for invalid in (_frame() | {"base_url": "https://example.com"},
                    _frame() | {"messages": [{"role": "user", "content": "hi", "provider": "other"}]}):
        with pytest.raises(ValueError):
            infer_envelope(invalid)


def test_all_auxiliary_routes_and_environment_are_pinned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "provider-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "provider-secret")
    config = pinned_config("http://127.0.0.1:39876/v1", "per-process-token")
    assert set(config["auxiliary"]) == set(AUXILIARY_TASKS)
    route = config["model"]
    assert route["base_url"] == "http://127.0.0.1:39876/v1"
    for route in [config["delegation"], *config["auxiliary"].values()]:
        assert route["base_url"].startswith("http://127.0.0.1:39876/v1")
        assert route["api_key"] == "per-process-token"
        assert route["api_mode"] == "chat_completions"
    assert all(route["base_url"].endswith("/aux/" + name)
               for name, route in config["auxiliary"].items())
    env = worker_environment(tmp_path / "home", tmp_path / "backend")
    assert "provider-secret" not in json.dumps(config) + json.dumps(env)
    assert "OPENAI_API_KEY" not in env and "ANTHROPIC_API_KEY" not in env
    assert env["HERMES_DISABLE_LAZY_INSTALLS"] == "1"
    assert list(config["mcp_servers"]) == ["jarvis"]
    assert "delegation" not in ENABLED_TOOLSETS and "delegation" in DISABLED_TOOLSETS
    assert "skills" not in ENABLED_TOOLSETS and "skills" in DISABLED_TOOLSETS


def test_mcp_protocol_discloses_only_broker_tool() -> None:
    initialized = _reply({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    listed = _reply({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert initialized is not None and initialized["result"]["serverInfo"]["name"] == "jarvis"
    assert listed is not None and [tool["name"] for tool in listed["result"]["tools"]] == [
        "jarvis_context_preview", "jarvis_retrieval_query"]


def test_text_tool_proposal_requires_the_registered_broker() -> None:
    tools = [{"function": {"name": "mcp__jarvis__jarvis_context_preview"}}]
    proposal = json.dumps({"tool_calls": [{"name": "mcp__jarvis__jarvis_context_preview",
                                           "arguments": {"grant_id": "grant-1"}}]})
    message = completion_message(proposal, tools)
    assert message["content"] is None
    assert message["tool_calls"][0]["function"]["name"] == "mcp__jarvis__jarvis_context_preview"
    assert completion_message(proposal, [])["content"] == proposal
    assert completion_message(json.dumps({"tool_calls": [{"name": "terminal", "arguments": {}}]}),
                              tools)["content"] is not None
    envelope = infer_envelope(_frame() | {"tools": tools})
    assert "mcp__jarvis__jarvis_context_preview" in envelope.prompt
    with pytest.raises(ValueError):
        infer_envelope(_frame() | {"tools": [{"function": {"name": "terminal"}}]})


def test_governed_inference_maps_result_and_cancellation() -> None:
    envelope = infer_envelope(_frame())
    calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: object) -> Any:
        calls.append(kwargs)
        return SimpleNamespace(status="success", response=SimpleNamespace(text="Jarvis answer"))

    assert run_governed_inference(envelope, runner=fake_runner) == {"status": "success", "text": "Jarvis answer"}
    assert calls[0]["user_prompt"] == envelope.prompt
    assert calls[0]["workspace_id"] == SESSION.workspace_id
    assert run_governed_inference(envelope, runner=fake_runner,
                                  cancelled=lambda _id: True) == {"status": "cancelled"}
    assert len(calls) == 1


def test_relay_defaults_to_explicit_llamacpp_and_accepts_only_explicit_local_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[str | None] = []

    def governed(envelope: InferenceEnvelope, **_kwargs: Any) -> dict[str, str]:
        observed.append(envelope.route_class)
        return {"status": "refused"}

    monkeypatch.setattr(hermes_supervisor_module, "run_governed_inference", governed)
    supervisor = HermesSupervisor("unused")
    supervisor.session = SESSION
    monkeypatch.setattr(supervisor, "_send", lambda _frame: None)
    supervisor._handle_relay(_frame())
    assert observed == ["local:llamacpp"]

    supervisor.route_for_task = lambda _task: "local:ollama"
    supervisor._handle_relay(_frame())
    assert observed == ["local:llamacpp", "local:ollama"]

    supervisor.route_for_task = lambda _task: "openai:external"
    supervisor._handle_relay(_frame())
    assert observed == ["local:llamacpp", "local:ollama"]


def test_session_mapping_control_event_order_and_recovery() -> None:
    connection = _connection()
    first = bind_session(connection, thread_id="thread-1", workspace_id="workspace-1",
                         profile_id="profile-1", hermes_session_id="hermes-1")
    assert first == SESSION
    again = bind_session(connection, thread_id="thread-1", workspace_id="workspace-1",
                         profile_id="profile-1", hermes_session_id="hermes-1")
    assert again == first
    assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
    command = AgentControlCommand(command_id="cmd-1", kind="interrupt", correlation_id="corr-1",
                                  jarvis_thread_id="thread-1", workspace_id="workspace-1",
                                  profile_id="profile-1", hermes_session_id="hermes-1",
                                  expected_generation=1, requested_at=NOW,
                                  deadline_at=NOW + timedelta(minutes=1))
    check_control_target(command, first, now=NOW)
    assert project_event(connection, AgentEvent(event_id="event-1", session_ref=first,
                                                sequence=0, kind="turn.started", occurred_at=NOW))
    assert not project_event(connection, AgentEvent(event_id="event-1", session_ref=first,
                                                    sequence=0, kind="turn.started", occurred_at=NOW))
    second = bind_session(connection, thread_id="thread-1", workspace_id="workspace-1",
                          profile_id="profile-1", hermes_session_id="hermes-2")
    assert second.generation == 2 and current_mapping(connection, "thread-1") == second
    with pytest.raises(ValueError):
        check_control_target(command, second, now=NOW)
    assert not project_event(connection, AgentEvent(event_id="event-2", session_ref=first,
                                                    sequence=1, kind="turn.ended", occurred_at=NOW))


def test_worker_loss_rebinds_without_replaying_old_events(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _connection()
    first = bind_session(connection, thread_id="thread-1", workspace_id="workspace-1",
                         profile_id="profile-1", hermes_session_id="hermes-1")
    connection.commit()
    connection.execute(
        "INSERT INTO ai_thread_interactions (id, thread_id, request_id, request_digest, interaction_index, "
        "user_text, assistant_text, assistant_text_truncated, flow_id, persistence_state, created_at, updated_at) "
        "VALUES ('interaction-1', 'thread-1', 'request-1', 'digest', 0, 'prior question', 'prior answer', "
        "0, 'flow-1', 'captured', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')"
    )
    connection.commit()
    monkeypatch.setattr("app.modules.agents.hermes.supervisor.open_sqlite_connection",
                        lambda: _existing_connection(connection))
    supervisor = HermesSupervisor("unused")
    sent: list[dict[str, Any]] = []
    monkeypatch.setattr(supervisor, "start", lambda: None)
    monkeypatch.setattr(supervisor, "_send", sent.append)
    monkeypatch.setattr(supervisor, "_await", lambda _id, **_kwargs: {"type": "ack"})
    supervisor._recover(first)
    assert supervisor.session is not None and supervisor.session.generation == 2
    assert supervisor.session.hermes_session_id != first.hermes_session_id
    assert sent[0]["type"] == "bind" and sent[0]["session_ref"]["generation"] == 2
    assert sent[0]["history"] == [
        {"role": "user", "content": "prior question"},
        {"role": "assistant", "content": "prior answer"},
    ]
    assert not project_event(connection, AgentEvent(event_id="old-event", session_ref=first,
                                                    sequence=1, kind="turn.completed", occurred_at=NOW))


def test_network_isolation_never_silently_falls_back_without_bwrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supervisor = HermesSupervisor("unused", network_isolation=True)
    monkeypatch.setattr("app.modules.agents.hermes.supervisor.shutil.which", lambda _name: None)
    with pytest.raises(RuntimeError, match="requires bubblewrap"):
        supervisor.start()


def test_session_pool_keeps_bounded_per_thread_workers_and_idle_stop() -> None:
    created = []

    class Worker:
        process = None
        session = object()

        def status(self) -> dict[str, Any]:
            return {"state": "stopped"}

    def factory() -> Worker:
        worker = Worker()
        created.append(worker)
        return worker

    pool = HermesSessionPool(factory, maximum=2, idle_seconds=60)
    first = pool.for_thread("thread-a")
    assert pool.for_thread("thread-a") is first
    second = pool.for_thread("thread-b")
    assert second is not first
    pool.for_thread("thread-c")
    assert len(created) == 3 and first.session is None
    assert pool.status()["state"] == "stopped"


def test_tool_refusal_emits_bounded_correlated_event_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _connection()
    connection.commit()
    monkeypatch.setattr("app.modules.agents.hermes.supervisor.open_sqlite_connection",
                        lambda: _existing_connection(connection))
    supervisor = HermesSupervisor("unused")
    supervisor.session = SESSION
    supervisor.active_interaction_id = "interaction-1"
    monkeypatch.setattr(supervisor, "_send", lambda _frame: None)
    supervisor._handle_tool({"id": "tool-call-1", "session_ref": SESSION.model_dump(mode="json"),
                             "arguments": {"tool_name": "jarvis_retrieval_query", "grant_id": "missing",
                                           "query": "pump", "source_scope": ["modeling"],
                                           "api_token": "must-not-persist"}})
    row = connection.execute("SELECT payload FROM events WHERE event_type = 'hermes.tool_result'").fetchone()
    assert row is not None
    payload = json.loads(row["payload"])
    assert payload["call_id"] == "tool-call-1"
    assert payload["interaction_id"] == "interaction-1"
    assert payload["correlation_id"] == "interaction-1"
    assert payload["generation"] == SESSION.generation
    assert payload["status"] == "refused"
    assert "api_token" not in payload["arguments"]
    assert payload["result_digest"].startswith("sha256:")


def test_native_windows_requires_the_configured_wsl_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supervisor = HermesSupervisor("unused", network_isolation=True)
    monkeypatch.setattr("app.modules.agents.hermes.supervisor.os.name", "nt")
    with pytest.raises(RuntimeError, match="requires the configured WSL distro"):
        supervisor.start()


def test_capability_registration_is_safe_on_module_reload() -> None:
    importlib.reload(hermes_supervisor_module)
    importlib.reload(hermes_supervisor_module)


def test_hermes_status_is_exposed_on_agent_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "data"))
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/agents/hermes/status")
    assert response.status_code == 200
    assert response.json() == {
        "worker_pid": None,
        "state": "stopped",
        "upstream_revision": SESSION.upstream_revision,
        "generation": None,
        "last_error": None,
    }


def test_expected_worker_exit_is_not_reported_as_worker_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    supervisor = HermesSupervisor("unused")

    class Exited:
        stdout = object()

    process = Exited()
    supervisor.process = process  # type: ignore[assignment]
    supervisor.expected_worker_exit = True
    monkeypatch.setattr(supervisor, "_read_frames", lambda _process: None)
    supervisor._read_worker(process)  # type: ignore[arg-type]
    assert supervisor.worker_lost is False
    assert supervisor.last_error is None


def test_successful_turn_returns_relay_flow_without_creating_a_second_interaction(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _connection()
    connection.commit()
    monkeypatch.setattr("app.modules.agents.hermes.supervisor.open_sqlite_connection",
                        lambda: _existing_connection(connection))
    supervisor = HermesSupervisor("unused")
    supervisor.session = SESSION

    class Alive:
        def poll(self) -> None:
            return None

    supervisor.process = Alive()  # type: ignore[assignment]
    monkeypatch.setattr(supervisor, "_send", lambda _frame: None)

    def answer(_id: str, **_kwargs: Any) -> dict[str, Any]:
        supervisor.last_flow[SESSION.hermes_session_id] = "flow-1"
        return {"type": "turn_result", "status": "success", "completed": True,
                "final_response": "Recorded answer"}

    monkeypatch.setattr(supervisor, "_await", answer)
    assert supervisor.turn("question")["status"] == "success"
    assert connection.execute("SELECT COUNT(*) FROM ai_thread_interactions").fetchone()[0] == 0


@contextmanager
def _existing_connection(connection: sqlite3.Connection) -> Any:
    yield connection


def test_capability_live_grant_denials() -> None:
    call = StructuredToolCall(call_id="call-1", capability_id="jarvis.context_preview", grant_id="grant-1",
                              correlation_id="corr-1", session_ref=SESSION, requested_at=NOW,
                              deadline_at=NOW + timedelta(minutes=1))
    grant = CapabilityGrantRef(grant_id="grant-1", capability_id=call.capability_id,
                               issuer="operator", scope=CapabilityScope(workspace_id="wrong"),
                               issued_at=NOW - timedelta(minutes=1), expires_at=NOW + timedelta(minutes=1))
    for live in ({}, {"grant-1": grant},
                 {"grant-1": grant.model_copy(update={"scope": CapabilityScope(workspace_id="workspace-1"),
                                                 "expires_at": NOW - timedelta(seconds=1)})},
                 {"grant-1": grant.model_copy(update={"scope": CapabilityScope(workspace_id="workspace-1"),
                                                 "revoked_at": NOW, "revocation_reason": "revoked"})},
                 {"grant-1": grant.model_copy(update={"scope": CapabilityScope(workspace_id="workspace-1"),
                                                 "capability_id": "jarvis.commit"})}):
        assert dispatch_tool(call, live_grants=live).status == "refused"


def test_retrieval_tool_pins_workspace_and_enforces_granted_source_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(UTC)  # the module-level clock can be minutes old in a sharded run
    ref = SourceRef(authority_owner="modeling", object_type="decision", object_id="decision-1",
                    workspace_id=SESSION.workspace_id, revision="1", content_digest=canonical_digest("decision"))
    call = StructuredToolCall(call_id="query-1", capability_id="jarvis.retrieval_query", grant_id="grant-1",
                              correlation_id="query-1", session_ref=SESSION,
                              arguments={"query": "pump", "source_scope": ["modeling"], "limit": 8,
                                         "token_budget": 1024}, requested_at=now,
                              deadline_at=now + timedelta(minutes=1))
    grant = CapabilityGrantRef(grant_id="grant-1", capability_id=call.capability_id,
                               issuer="operator", scope=CapabilityScope(workspace_id=SESSION.workspace_id,
                                                                        object_refs=(ref,)),
                               issued_at=now - timedelta(minutes=1), expires_at=now + timedelta(minutes=1))
    observed: dict[str, Any] = {}

    def query_context(query: str, **kwargs: Any) -> dict[str, Any]:
        observed.update(query=query, **kwargs)
        return {"evidence": []}

    from app.modules.ai import retrieval_query

    monkeypatch.setattr(retrieval_query, "query_context", query_context)
    assert grant.is_active(datetime.now(UTC)) and not call.is_expired(datetime.now(UTC))
    assert call.session_ref == SESSION and grant.scope.workspace_id == SESSION.workspace_id
    assert grant.capability_id == call.capability_id
    assert grant.scope.jarvis_thread_id in (None, SESSION.jarvis_thread_id)
    assert any(item.capability_id == call.capability_id for item in hermes_supervisor_module.PRODUCTION_CAPABILITY_REGISTRY.for_route("ai-threads"))
    result = dispatch_tool(call, live_grants={"grant-1": grant})
    assert result.status == "succeeded" and result.result == {"evidence": []}, result.model_dump()
    assert observed == {"query": "pump", "workspace_id": SESSION.workspace_id,
                        "source_scope": ("modeling",),
                        "allowed_refs": frozenset({("modeling", "decision", "decision-1")}),
                        "limit": 8, "token_budget": 1024}
    denied = call.model_copy(update={"arguments": {"query": "pump", "source_scope": ["literature"]}})
    assert dispatch_tool(denied, live_grants={"grant-1": grant}).status == "refused"
    over_limit = call.model_copy(update={"arguments": call.arguments | {"limit": 9}})
    assert dispatch_tool(over_limit, live_grants={"grant-1": grant}).status == "refused"
    over_budget = call.model_copy(update={"arguments": call.arguments | {"token_budget": 1025}})
    assert dispatch_tool(over_budget, live_grants={"grant-1": grant}).status == "refused"


@pytest.mark.skipif(not os.environ.get("JARVIS_HERMES_VENV"), reason="requires installed Hermes venv")
def test_real_worker_turn_interrupt_relay(tmp_path: Path) -> None:
    """Opt-in integration: real Hermes, fake Jarvis inference, no provider/network dependency."""
    venv = Path(os.environ["JARVIS_HERMES_VENV"])
    python = venv / "bin" / "python"
    assert python.exists()
    if subprocess.run([str(python), "-c", "import run_agent"], capture_output=True, check=False).returncode:
        pytest.skip("Hermes package has not been installed in the selected venv")
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
    except OSError:
        pytest.skip("this environment forbids loopback sockets")
    backend_root = Path(__file__).resolve().parents[1]
    env = worker_environment(tmp_path / "hermes", backend_root)
    process = subprocess.Popen([str(python), "-m", "app.modules.agents.hermes.worker_shim"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, bufsize=1, env=env)
    assert process.stdin and process.stdout
    seen: list[dict[str, Any]] = []
    try:
        ready = json.loads(process.stdout.readline())
        assert ready["type"] == "ready"
        process.stdin.write(json.dumps({"type": "bind", "id": "bind-1", "session_ref": SESSION.model_dump(mode="json")}) + "\n")
        process.stdin.flush()
        bound = json.loads(process.stdout.readline())
        assert bound["type"] == "ack"
        assert bound["tools"]
        assert not {"delegate_task", "skills_list", "skill_view"} & set(bound["tools"])
        assert set(bound["tools"]) <= {
            "mcp__jarvis__jarvis_context_preview", "mcp__jarvis__jarvis_retrieval_query",
            "memory", "session_search",
        }
        process.stdin.write(json.dumps({"type": "turn", "id": "turn-1", "prompt": "Say hello"}) + "\n")
        process.stdin.flush()
        for _ in range(20):
            frame = json.loads(process.stdout.readline())
            if frame["type"] == "relay_request":
                seen.append(frame)
                process.stdin.write(json.dumps({"type": "relay_result", "id": frame["id"],
                                                "status": "success", "text": "Hello."}) + "\n")
                process.stdin.flush()
            elif frame.get("id") == "turn-1":
                assert frame["status"] == "success"
                break
        else:
            pytest.fail("turn did not finish")
        assert seen and all(item["session_ref"] == SESSION.model_dump(mode="json") for item in seen)
        process.stdin.write(json.dumps({"type": "interrupt", "id": "stop-1"}) + "\n")
        process.stdin.flush()
        assert json.loads(process.stdout.readline()) == {"type": "ack", "id": "stop-1"}
    finally:
        process.terminate()
        process.wait(timeout=10)
