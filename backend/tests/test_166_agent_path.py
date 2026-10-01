from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.modules.agents.hermes.supervisor import dispatch_tool
from app.modules.ai.agent_contracts import (
    AgentSessionRef,
    CapabilityGrantRef,
    CapabilityScope,
    StructuredToolCall,
)
from app.modules.ai.contracts import AIRequest
from app.modules.ai.providers import local_llamacpp_adapter
from app.modules.ai.providers.local_llamacpp_adapter import LocalLlamaCppAdapter
from app.modules.ai.thread_service import (
    _derive_surface_brief,
    _guard_tool_shaped_output,
    _install_surface_grants,
    _turn_tools,
)
from app.modules.workspace_actions.models import SurfaceBrief, SurfaceRef

SESSION = AgentSessionRef(jarvis_thread_id="thread-166", hermes_session_id="hermes-166",
                          profile_id="default", workspace_id="workspace-166", generation=1,
                          upstream_revision="d337b736aa1e8ebecfab043842d13e4a2d2f48a3")


def test_turn_tools_are_scoped_to_owner_derived_surface() -> None:
    process = _turn_tools("process")
    bluecad = _turn_tools("bluecad")
    none = _turn_tools("none")
    assert "mcp__jarvis__jarvis_process_act" in process
    assert "mcp__jarvis__jarvis_bluecad_act" not in process
    assert "mcp__jarvis__jarvis_bluecad_act" in bluecad
    assert "mcp__jarvis__jarvis_process_act" not in bluecad
    assert not any("workspace" in name for name in none)
    assert all("jarvis_process" not in name and "jarvis_bluecad" not in name for name in none)


def test_surface_brief_falls_back_to_none_with_reason(monkeypatch) -> None:
    from app.modules.workspace_actions import service

    def unavailable(_workspace_id, _ref):
        raise NotImplementedError("executor lane is not merged")

    monkeypatch.setattr(service, "surface_brief", unavailable)
    brief = _derive_surface_brief("workspace-166", SurfaceRef(route_id="process"))
    assert brief.surface == "none"
    assert "executor lane is not merged" in brief.text


def test_surface_grants_and_instructions_are_scoped_to_brief() -> None:
    worker = SimpleNamespace(live_grants={})
    brief = SurfaceBrief(surface="bluecad", route_id="bluecad", workspace_id="workspace-166",
                         base_revision="candidate-1", candidate_id="candidate-1", summary="BLUECAD · tube",
                         text="candidate candidate-1 selected tube", digest="sha256:" + "b" * 64)
    text = _install_surface_grants(worker, "workspace-166", "thread-166",
                                   SurfaceRef(route_id="bluecad", candidate_id="candidate-1"), brief)
    assert {grant.capability_id for grant in worker.live_grants.values()} == {
        "jarvis.bluecad_read", "jarvis.bluecad_act"}
    assert "mcp__jarvis__jarvis_bluecad_act" in text
    assert "mcp__jarvis__jarvis_process_act" not in text
    assert "Monod" not in text
    assert all(grant.constraints["base_revision"] == "candidate-1" for grant in worker.live_grants.values())


def test_guard_hides_tool_protocol_and_bounds_raw_details() -> None:
    visible, details = _guard_tool_shaped_output(
        '{"tool_calls":[{"name":"jarvis_process_act","arguments":{"grant_id":"private-grant"}}]}'
    )
    assert visible == "I couldn't complete that — Jarvis produced an invalid action request, so nothing was changed."
    assert details is not None and len(details) < 8_001 and "private-grant" not in details
    assert _guard_tool_shaped_output("No Monod kinetics are supported.") == ("No Monod kinetics are supported.", None)


def test_dispatch_submits_typed_action_to_workspace_executor(monkeypatch) -> None:
    from app.modules.workspace_actions import service

    captured = {}

    def submit(workspace_id, request, origin):
        captured.update(workspace_id=workspace_id, request=request, origin=origin)
        return SimpleNamespace(state="proposed", summary="Move PFR", reason=None, changes=[],
                               result_revision=None, child_candidate_id=None)

    monkeypatch.setattr(service, "submit", submit)
    now = datetime.now(UTC)
    grant = CapabilityGrantRef(
        grant_id="process-act-grant", capability_id="jarvis.process_act", issuer="jarvis_policy",
        scope=CapabilityScope(workspace_id=SESSION.workspace_id, jarvis_thread_id=SESSION.jarvis_thread_id),
        issued_at=now, expires_at=now + timedelta(minutes=2),
    )
    call = StructuredToolCall(
        call_id="call-166", capability_id="jarvis.process_act", grant_id=grant.grant_id,
        correlation_id="call-166", session_ref=SESSION,
        arguments={"base_revision": "rev-1", "actions": [{"op": "move", "target": "PFR-1", "dx": 1, "dy": 0}]},
        requested_at=now, deadline_at=now + timedelta(minutes=1),
    )
    result = dispatch_tool(call, live_grants={grant.grant_id: grant}, interaction_id="interaction-166")
    assert result.status == "succeeded"
    assert result.result == {"state": "proposed", "summary": "Move PFR", "reason": None,
                             "changes": [], "result_revision": None, "child_candidate_id": None}
    assert captured["workspace_id"] == SESSION.workspace_id
    assert captured["request"].surface == "process"
    assert captured["origin"].interaction_id == "interaction-166"


def test_off_turn_or_wrong_capability_grants_cannot_dispatch(monkeypatch) -> None:
    now = datetime.now(UTC)
    process_grant = CapabilityGrantRef(
        grant_id="process-read", capability_id="jarvis.process_read", issuer="jarvis_policy",
        scope=CapabilityScope(workspace_id=SESSION.workspace_id, jarvis_thread_id=SESSION.jarvis_thread_id),
        issued_at=now, expires_at=now + timedelta(minutes=1),
    )
    call = StructuredToolCall(
        call_id="bluecad-call", capability_id="jarvis.bluecad_act", grant_id=process_grant.grant_id,
        correlation_id="bluecad-call", session_ref=SESSION,
        arguments={"base_revision": "candidate-1", "actions": [{"op": "delete_part", "part": "tube"}]},
        requested_at=now, deadline_at=now + timedelta(seconds=30),
    )
    result = dispatch_tool(call, live_grants={process_grant.grant_id: process_grant})
    assert result.status == "refused"


def test_llama_schema_is_explicit_opt_in_and_uses_response_format(monkeypatch) -> None:
    captured = {}

    class Response:
        is_success = True

        def raise_for_status(self):
            return None

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": '{"answer":"ok"}'}, "finish_reason": "stop"}]}

    class Client:
        def post(self, _url, *, json, **_kwargs):
            captured.update(json)
            return Response()

        @staticmethod
        def close():
            return None

    schema = {"type": "object", "oneOf": [{"required": ["answer"]}]}
    request = AIRequest(task_type="synthesis", structured_output_schema=schema)
    monkeypatch.setattr(local_llamacpp_adapter, "llama_cpp_runtime_config",
                        lambda: SimpleNamespace(base_url="http://127.0.0.1:18081/v1", model_id="local", thinking="off",
                                                request_timeout_s=5))
    monkeypatch.setattr(local_llamacpp_adapter, "get_llama_cpp_runtime_owner",
                        lambda: SimpleNamespace(auth_headers=lambda: {}))
    monkeypatch.delenv("JARVIS_LLAMA_JSON_SCHEMA", raising=False)
    LocalLlamaCppAdapter(client_factory=Client).complete(request)
    assert "response_format" not in captured
    monkeypatch.setenv("JARVIS_LLAMA_JSON_SCHEMA", "true")
    LocalLlamaCppAdapter(client_factory=Client).complete(request)
    assert captured["response_format"] == {"type": "json_schema", "json_schema": {
        "name": "jarvis_agent_response", "strict": True, "schema": schema}}
