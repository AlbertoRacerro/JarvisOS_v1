"""Hermes-venv worker. Deliberately stdlib-only and independent of app imports."""
from __future__ import annotations

import json
import os
import queue
import secrets
import subprocess
import sys
import threading
import traceback
import uuid
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import metadata, util
from pathlib import Path
from typing import Any

UPSTREAM_REVISION = "d337b736aa1e8ebecfab043842d13e4a2d2f48a3"
AUXILIARY_TASKS = (
    "vision", "compression", "skills_hub", "approval", "review", "mcp",
    "title_generation", "memory_query_rewrite", "tts_audio_tags", "triage_specifier",
    "kanban_decomposer", "profile_describer", "goal_judge", "curator", "monitor",
    "background_review", "moa_reference", "moa_aggregator",
)


def completion_message(text: str, tools: Any) -> dict[str, Any]:
    """Promote a bounded text proposal into the one broker tool OpenAI shape."""
    if not isinstance(tools, list) or not tools:
        return {"role": "assistant", "content": text}
    try:
        proposal = json.loads(text)
    except (ValueError, TypeError):
        return {"role": "assistant", "content": text}
    if not isinstance(proposal, dict) or set(proposal) != {"tool_calls"}:
        return {"role": "assistant", "content": text}
    calls = proposal["tool_calls"]
    if not isinstance(calls, list) or not 1 <= len(calls) <= 4:
        return {"role": "assistant", "content": text}
    permitted = {tool.get("function", {}).get("name") for tool in tools if isinstance(tool, dict)}
    promoted = []
    for call in calls:
        if not isinstance(call, dict) or call.get("name") not in permitted or not isinstance(call.get("arguments"), dict):
            return {"role": "assistant", "content": text}
        promoted.append({"id": uuid.uuid4().hex, "type": "function", "function": {
            "name": call["name"], "arguments": json.dumps(call["arguments"], separators=(",", ":"))}})
    return {"role": "assistant", "content": None, "tool_calls": promoted}


def verify_upstream() -> None:
    """Refuse an installed Hermes build other than the qualified source checkout."""
    if metadata.version("hermes-agent") != "0.21.4":
        raise RuntimeError("Hermes package version is not qualified")
    spec = util.find_spec("run_agent")
    if spec is None or spec.origin is None:
        raise RuntimeError("Hermes source is unavailable")
    result = subprocess.run(["git", "-C", str(Path(spec.origin).parent), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False, timeout=10)
    if result.returncode != 0 or result.stdout.strip() != UPSTREAM_REVISION:
        raise RuntimeError("Hermes source revision is not qualified")


# Only the Jarvis MCP broker is enabled for capabilities. Delegation and skills remain
# disabled until their actions can be presented to, and authorized by, that broker.
ENABLED_TOOLSETS = ["mcp-jarvis", "memory", "session_search"]
DISABLED_TOOLSETS = ["terminal", "file", "code_execution", "browser", "web", "search", "x_search",
                     "connections", "cronjob", "computer_use", "image_gen", "video_gen", "vision",
                     "tts", "kanban", "clarify", "homeassistant", "todo", "project", "coding",
                     "delegation", "skills"]
# Tools removed from the model-visible schema even though their toolset is enabled:
# skill_manage writes new instruction files (persistent prompt injection surface).
WITHHELD_TOOLS = frozenset({"skill_manage"})
# Tool names Jarvis admits in a relayed request; mirrors supervisor.HERMES_TOOL_ALLOWLIST.
ADMITTED_TOOLS = frozenset({"mcp__jarvis__jarvis_context_preview",
                            "mcp__jarvis__jarvis_retrieval_query", "mcp__jarvis__jarvis_decide",
                            "memory", "session_search"})


def pinned_config(base_url: str, token: str, python: str | None = None) -> dict[str, Any]:
    route = {"provider": "custom", "model": "jarvis-relay", "base_url": base_url,
             "api_key": token, "api_mode": "chat_completions"}
    return {
        "model": {**{key: value for key, value in route.items() if key != "model"}, "default": "jarvis-relay"},
        "providers": {}, "custom_providers": [],
        "auxiliary": {name: {**route, "base_url": base_url + "/aux/" + name,
                              **({"model_upgrade_enabled": False} if name == "title_generation" else {})}
                      for name in AUXILIARY_TASKS},
        "delegation": {**route, "base_url": base_url + "/delegation", "fallback_providers": [],
                       "max_spawn_depth": 1, "orchestrator_enabled": False, "max_concurrent_children": 2,
                       "subagent_auto_approve": False, "inherit_mcp_toolsets": True},
        "fallback_providers": [], "credential_pool_strategies": {},
        "moa": {"default_preset": "", "active_preset": "", "presets": {}},
        "skills": {"external_dirs": [], "project_discovery": False, "trusted_project_dirs": [],
                   "auto_load": [], "inline_shell": False, "guard_agent_created": True},
        "memory": {"memory_enabled": True, "user_profile_enabled": False, "provider": "",
                   "write_approval": False, "nudge_interval": 0},
        "mcp_servers": {"jarvis": {
            "command": python or sys.executable,
            # Script path, not ``-m``: Hermes gives MCP children a filtered env without PYTHONPATH.
            "args": [str(Path(__file__).with_name("broker_mcp.py"))],
            "env": {"JARVIS_HERMES_BROKER_URL": base_url + "/jarvis/tool",
                    "JARVIS_HERMES_BROKER_TOKEN": token},
            "tools": {"include": ["jarvis_context_preview", "jarvis_retrieval_query", "jarvis_decide"]},
        }},
        "model_catalog": {"enabled": False}, "updates": {"check": False},
        "telemetry": {"enabled": False, "send": False},
        "toolsets": list(ENABLED_TOOLSETS),
        # No tool_search/tool_call bridge: every model-visible tool must be individually admitted.
        "tools": {"tool_search": {"enabled": "off", "defer": []}},
    }


def withhold_tools(agent: Any) -> list[str]:
    """Drop withheld tools from the model-visible schema; returns the remaining names."""
    agent.tools = [tool for tool in (agent.tools or [])
                   if tool.get("function", {}).get("name") not in WITHHELD_TOOLS]
    names = sorted(tool["function"]["name"] for tool in agent.tools)
    if hasattr(agent, "valid_tool_names"):
        agent.valid_tool_names = set(names)
    if not set(names) <= ADMITTED_TOOLS:
        raise RuntimeError("Hermes exposed tools outside the Jarvis admission set: "
                           + ",".join(sorted(set(names) - ADMITTED_TOOLS)))
    return names


class Worker:
    def __init__(self) -> None:
        self.token = secrets.token_urlsafe(32)
        self.protocol_output = sys.stdout
        self.output_lock = threading.Lock()
        self.pending: dict[str, queue.Queue[dict[str, Any]]] = {}
        self.pending_lock = threading.Lock()
        self.turn_lock = threading.Lock()
        self.agent: Any = None
        self.session_db: Any = None
        self.tool_names: list[str] = []
        self.history: list[dict[str, Any]] = []
        self.session: dict[str, Any] | None = None
        self.sequence = 0
        self.sequences: dict[tuple[str, int], int] = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.base_url = f"http://127.0.0.1:{self.server.server_port}/v1"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def send(self, frame: dict[str, Any]) -> None:
        with self.output_lock:
            self.protocol_output.write(json.dumps(frame, separators=(",", ":")) + "\n")
            self.protocol_output.flush()

    def event(self, kind: str, correlation_id: str) -> None:
        if self.session is None:
            return
        with self.output_lock:
            frame = {"type": "agent_event", "event": {
                "schema_version": "agent_contracts.v1", "event_id": str(uuid.uuid4()),
                "session_ref": self.session, "sequence": self.sequence,
                "kind": kind, "occurred_at": datetime.now(UTC).isoformat(),
                "correlation_id": correlation_id,
            }}
            self.sequence += 1
            self.sequences[(self.session["hermes_session_id"], self.session["generation"])] = self.sequence
            self.protocol_output.write(json.dumps(frame, separators=(",", ":")) + "\n")
            self.protocol_output.flush()

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        worker = self

        class Relay(BaseHTTPRequestHandler):
            def log_message(self, *_args: Any) -> None:
                pass

            def do_POST(self) -> None:  # noqa: N802
                if self.headers.get("Authorization") != f"Bearer {worker.token}":
                    self.send_error(403)
                    return
                if self.path == "/v1/chat/completions":
                    task_kind = "general"
                elif self.path == "/v1/delegation/chat/completions":
                    task_kind = "delegation"
                elif self.path.startswith("/v1/aux/") and self.path.endswith("/chat/completions"):
                    task_kind = self.path.removeprefix("/v1/aux/").removesuffix("/chat/completions")
                    if task_kind not in AUXILIARY_TASKS:
                        self.send_error(403)
                        return
                elif self.path == "/v1/jarvis/tool":
                    task_kind = "tool"
                else:
                    self.send_error(403)
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if size < 1 or size > 2_000_000:
                        raise ValueError("invalid request size")
                    body = json.loads(self.rfile.read(size))
                    if self.path == "/v1/jarvis/tool":
                        if worker.session is None or not isinstance(body, dict):
                            raise ValueError("no active session or malformed tool call")
                        request_id = uuid.uuid4().hex
                        tool_answer: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1)
                        with worker.pending_lock:
                            worker.pending[request_id] = tool_answer
                        worker.send({"type": "tool_call", "id": request_id,
                                     "session_ref": worker.session, "arguments": body})
                        try:
                            result = tool_answer.get(timeout=120)
                        finally:
                            with worker.pending_lock:
                                worker.pending.pop(request_id, None)
                        encoded = json.dumps(result["tool_result"]).encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(encoded)))
                        self.end_headers()
                        self.wfile.write(encoded)
                        return
                    if not isinstance(body, dict) or "base_url" in body or "provider" in body:
                        raise ValueError("unsupported or bypassing request")
                    if worker.session is None:
                        raise ValueError("no active session")
                    request_id = uuid.uuid4().hex
                    answer: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1)
                    with worker.pending_lock:
                        worker.pending[request_id] = answer
                    worker.send({"type": "relay_request", "id": request_id, "session_ref": worker.session,
                                 "task_kind": task_kind,
                                 "messages": body.get("messages"), "model_candidate": body.get("model"),
                                 "tools": body.get("tools"),
                                 "max_output_tokens": body.get("max_completion_tokens", body.get("max_tokens"))})
                    try:
                        result = answer.get(timeout=180)
                    finally:
                        with worker.pending_lock:
                            worker.pending.pop(request_id, None)
                    if result.get("status") != "success":
                        self.send_error(502, "Jarvis inference refused")
                        return
                    message = completion_message(result["text"], body.get("tools"))
                    if body.get("stream") is True:
                        delta = dict(message)
                        if "tool_calls" in delta:
                            delta["tool_calls"] = [dict(call, index=index)
                                                   for index, call in enumerate(delta["tool_calls"])]
                        chunks = [
                            {"id": request_id, "object": "chat.completion.chunk", "model": "jarvis",
                             "choices": [{"index": 0, "finish_reason": None,
                                          "delta": delta}]},
                            {"id": request_id, "object": "chat.completion.chunk", "model": "jarvis",
                             "choices": [{"index": 0,
                                          "finish_reason": "tool_calls" if "tool_calls" in message else "stop",
                                          "delta": {}}]},
                        ]
                        encoded = ("".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
                                   + "data: [DONE]\n\n").encode()
                        content_type = "text/event-stream"
                    else:
                        payload = {"id": request_id, "object": "chat.completion", "model": "jarvis",
                                   "choices": [{"index": 0,
                                                "finish_reason": "tool_calls" if "tool_calls" in message else "stop",
                                                "message": message}]}
                        encoded = json.dumps(payload).encode()
                        content_type = "application/json"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                except (ValueError, KeyError, json.JSONDecodeError):
                    self.send_error(400)
                except queue.Empty:
                    self.send_error(504)

        return Relay

    def session_id(self) -> str:
        assert self.session is not None
        return str(self.session["hermes_session_id"])

    def _build_agent(self) -> Any:
        from hermes_state_registry import acquire
        from run_agent import AIAgent  # Hermes is installed only in its own venv.
        from tools.mcp_tool_discovery import register_mcp_servers

        registered = register_mcp_servers(pinned_config(self.base_url, self.token)["mcp_servers"])
        if not {"mcp__jarvis__jarvis_context_preview", "mcp__jarvis__jarvis_retrieval_query"} <= set(registered):
            raise RuntimeError("Jarvis capability broker unavailable")
        if self.session_db is None:
            # Hermes' own non-canonical session store under the Jarvis-owned HERMES_HOME;
            # it backs session_search. Jarvis ai_thread_interactions stay canonical.
            self.session_db = acquire()
        agent = AIAgent(
            base_url=self.base_url, api_key=self.token, provider="custom",
            api_mode="chat_completions", model="jarvis-relay", session_id=self.session_id(),
            enabled_toolsets=list(ENABLED_TOOLSETS), disabled_toolsets=list(DISABLED_TOOLSETS),
            skip_context_files=True, skip_memory=True, skip_background_review=True,
            load_soul_identity=False, quiet_mode=True, session_db=self.session_db,
            fallback_model=[], checkpoints_enabled=False,
        )
        self.tool_names = withhold_tools(agent)
        return agent

    def run_turn(self, request_id: str, prompt: str) -> None:
        if not self.turn_lock.acquire(blocking=False):
            self.send({"type": "turn_result", "id": request_id, "status": "failed", "error": "turn_busy"})
            return
        self.event("turn.started", request_id)
        try:
            if self.agent is None:
                self.agent = self._build_agent()
            result = self.agent.run_conversation(
                user_message=prompt, conversation_history=list(self.history), task_id=self.session_id())
            self.history = list(result.get("messages") or self.history)
            if result.get("interrupted"):
                self.event("turn.interrupted", request_id)
                self.send({"type": "turn_result", "id": request_id, "status": "interrupted",
                           "final_response": result.get("final_response") or "", "completed": False})
                return
            # Hermes substitutes an explanatory "No reply" text when a turn ends without a
            # model answer; only a text_response exit is a real final answer.
            exit_reason = str(result.get("turn_exit_reason") or "")
            if result.get("failed") or (exit_reason and not exit_reason.startswith("text_response")):
                self.event("turn.failed", request_id)
                self.send({"type": "turn_result", "id": request_id, "status": "failed",
                           "error": f"no_final_answer({exit_reason[:80]})", "completed": False})
                return
            self.event("turn.completed", request_id)
            self.send({"type": "turn_result", "id": request_id, "status": "success",
                       "final_response": result.get("final_response", ""),
                       "completed": result.get("completed", True)})
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            self.event("turn.failed", request_id)
            self.send({"type": "turn_result", "id": request_id, "status": "failed",
                       "error": type(exc).__name__})
        finally:
            self.turn_lock.release()

    def run(self) -> None:
        # Hermes prints progress on stdout even in quiet mode. Keep that output
        # away from the line-delimited control channel.
        sys.stdout = sys.stderr
        home = os.environ["HERMES_HOME"]
        os.makedirs(home, exist_ok=True)
        if os.path.exists(os.path.join(home, ".env")):
            raise RuntimeError("Hermes home contains an unmanaged credential file")
        with open(os.path.join(home, "config.yaml"), "w", encoding="utf-8") as output:
            json.dump(pinned_config(self.base_url, self.token), output)
        verify_upstream()
        self.send({"type": "ready", "upstream_revision": UPSTREAM_REVISION})
        for line in sys.stdin:
            frame: dict[str, Any] = {}
            try:
                frame = json.loads(line)
                if not isinstance(frame, dict):
                    raise ValueError("worker command must be an object")
                kind = frame["type"]
                if kind in {"relay_result", "tool_result"}:
                    with self.pending_lock:
                        pending = self.pending.get(frame["id"])
                    if pending is not None:
                        pending.put_nowait(frame)
                elif kind == "bind":
                    if self.turn_lock.locked():
                        self.send({"type": "error", "id": frame["id"], "error": "turn_busy"})
                    else:
                        if self.agent is not None and (self.session or {}).get("hermes_session_id") != \
                                frame["session_ref"]["hermes_session_id"]:
                            self.agent.close()
                            self.agent = None
                        if self.agent is None:
                            # A new Hermes session starts only from history Jarvis durably recorded.
                            seed = frame.get("history") or []
                            if not isinstance(seed, list) or any(
                                    not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}
                                    or not isinstance(item.get("content"), str) for item in seed):
                                raise ValueError("invalid history seed")
                            self.history = [{"role": item["role"], "content": item["content"]} for item in seed]
                        self.session = frame["session_ref"]
                        self.sequence = self.sequences.get(
                            (self.session["hermes_session_id"], self.session["generation"]), 0)
                        if self.agent is None:
                            # Validate the MCP bridge and the complete model-visible tool set
                            # before acknowledging that this session is ready for turns.
                            self.agent = self._build_agent()
                        self.send({"type": "ack", "id": frame["id"], "tools": self.tool_names,
                                   "history_messages": len(self.history)})
                elif kind == "turn":
                    threading.Thread(target=self.run_turn, args=(frame["id"], frame["prompt"]), daemon=True).start()
                elif kind == "interrupt":
                    if self.agent is not None:
                        self.agent.interrupt(hard_cancel=True)
                    self.send({"type": "ack", "id": frame["id"]})
                elif kind == "resume":
                    if self.agent is not None:
                        self.agent.clear_interrupt()
                    self.send({"type": "ack", "id": frame["id"]})
                elif kind == "close":
                    if self.agent is not None:
                        self.agent.close()
                        self.agent = None
                    self.server.shutdown()
                    self.send({"type": "ack", "id": frame["id"]})
                    return
            except (ValueError, KeyError, json.JSONDecodeError):
                self.send({"type": "protocol_error", "id": frame.get("id")
                           if isinstance(frame, dict) else None})
            except Exception as exc:
                # Keep initialization failures observable without exposing exception text or
                # terminating the stdio control loop. Detailed diagnostics stay on stderr.
                traceback.print_exc(file=sys.stderr)
                self.send({"type": "error", "id": frame.get("id") if isinstance(frame, dict) else None,
                           "error": type(exc).__name__})


if __name__ == "__main__":
    Worker().run()
