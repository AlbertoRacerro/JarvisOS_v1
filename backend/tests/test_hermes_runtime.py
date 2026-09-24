from __future__ import annotations

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

from app.modules.agents.hermes.broker_mcp import _reply
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
from app.modules.agents.hermes.worker_shim import AUXILIARY_TASKS, completion_message, pinned_config
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

NOW = datetime.now(UTC)
SESSION = AgentSessionRef(jarvis_thread_id="thread-1", hermes_session_id="hermes-1",
                          profile_id="profile-1", workspace_id="workspace-1", generation=1,
                          upstream_revision="d337b736aa1e8ebecfab043842d13e4a2d2f48a3")


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE ai_threads (id TEXT PRIMARY KEY, workspace_id TEXT)")
    connection.execute("INSERT INTO ai_threads VALUES ('thread-1', 'workspace-1')")
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
    for route in [config, config["delegation"], *config["auxiliary"].values()]:
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


def test_mcp_protocol_discloses_only_broker_tool() -> None:
    initialized = _reply({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    listed = _reply({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert initialized is not None and initialized["result"]["serverInfo"]["name"] == "jarvis"
    assert listed is not None and [tool["name"] for tool in listed["result"]["tools"]] == ["jarvis_context_preview"]


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
    assert not project_event(connection, AgentEvent(event_id="old-event", session_ref=first,
                                                    sequence=1, kind="turn.completed", occurred_at=NOW))


def test_successful_turn_is_captured_in_ai_thread_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = _connection()
    connection.execute("CREATE TABLE ai_thread_interactions (id TEXT, thread_id TEXT, request_id TEXT, "
                       "request_digest TEXT, interaction_index INTEGER, user_text TEXT, assistant_text TEXT, "
                       "assistant_text_truncated INTEGER, flow_id TEXT, persistence_state TEXT, "
                       "created_at TEXT, updated_at TEXT)")
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
    row = connection.execute("SELECT user_text, assistant_text, flow_id, persistence_state "
                             "FROM ai_thread_interactions").fetchone()
    assert tuple(row) == ("question", "Recorded answer", "flow-1", "captured")


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
        assert json.loads(process.stdout.readline())["type"] == "ack"
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
