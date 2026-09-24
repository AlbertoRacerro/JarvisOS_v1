"""Run a pinned Hermes worker through the Jarvis relay, broker, and event owner.

This qualification uses a deterministic in-process inference stub. It exercises the
real Hermes worker and loopback transport without claiming local-model evidence.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND))

if not os.environ.get("JARVIS_HERMES_VENV"):
    raise SystemExit("set JARVIS_HERMES_VENV to the pinned Hermes 0.21.4 environment")

with tempfile.TemporaryDirectory(prefix="jarvis-hermes-146-") as data_root:
    os.environ["JARVISOS_DATA_ROOT"] = data_root
    from app.core.database import initialize_database, open_sqlite_connection
    from app.modules.ai.agent_contracts import (
        AgentControlCommand,
        CapabilityGrantRef,
        CapabilityScope,
    )
    from app.modules.ai.jarvis_context_models import JarvisContextRequest
    from app.modules.ai.token_flow_service import create_flow
    from app.modules.ai.settings import ensure_ai_settings
    from app.modules.ai.thread_models import AIThreadCreate
    from app.modules.ai.thread_service import create_thread
    from app.modules.agents.hermes.supervisor import HermesSupervisor
    from app.modules.events.service import utc_now

    workspace_id = "qualification-workspace"
    initialize_database()
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            "INSERT INTO workspaces (id, name, slug, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (workspace_id, workspace_id, workspace_id, now, now),
        )
        connection.commit()
    ensure_ai_settings()
    thread = create_thread(AIThreadCreate(workspace_id=workspace_id, title="Hermes qualification"))
    flow_ids = [
        str(create_flow(task_kind="general", workspace_id=workspace_id)["id"])
        for _ in range(24)
    ]
    grant_id = str(uuid4())
    issued_at = datetime.now(UTC)
    grant = CapabilityGrantRef(
        grant_id=grant_id,
        capability_id="jarvis.context_preview",
        issuer="operator",
        scope=CapabilityScope(workspace_id=workspace_id, jarvis_thread_id=thread.id),
        issued_at=issued_at,
        expires_at=issued_at + timedelta(hours=1),
    )

    interrupt_entered = threading.Event()
    interrupt_release = threading.Event()
    inference_count = [0]

    def inference_stub(**kwargs: object) -> SimpleNamespace:
        inference_count[0] += 1
        flow_id = flow_ids[inference_count[0] - 1]
        prompt = str(kwargs["user_prompt"])
        if "interrupt-turn" in prompt:
            interrupt_entered.set()
            if not interrupt_release.wait(timeout=30):
                return SimpleNamespace(status="provider_error", response=None, flow_id=None)
            return SimpleNamespace(
                status="success", response=SimpleNamespace(text="interrupt response"), flow_id=flow_id
            )
        if inference_count[0] == 1:
            request = JarvisContextRequest(
                workspace_id=workspace_id,
                route={"route_id": "ai-threads", "canonical_path": "/ai-threads"},
            )
            proposal = {
                "tool_calls": [{
                    "name": "mcp__jarvis__jarvis_context_preview",
                    "arguments": {"grant_id": grant_id, "request": request.model_dump(mode="json")},
                }]
            }
            answer = json.dumps(proposal)
        else:
            answer = "Deterministic loopback inference stub completed the turn."
        return SimpleNamespace(status="success", response=SimpleNamespace(text=answer), flow_id=flow_id)

    supervisor = HermesSupervisor(
        os.path.join(os.environ["JARVIS_HERMES_VENV"], "bin", "python"),
        backend_root=BACKEND,
        runner=inference_stub,
    )
    supervisor_frames: list[dict[str, object]] = []
    send_frame = supervisor._send

    def capture_send(frame: dict[str, object]) -> None:
        if frame.get("type") in {"relay_result", "tool_result"}:
            supervisor_frames.append({key: frame.get(key) for key in ("type", "status", "id")})
        send_frame(frame)

    supervisor._send = capture_send  # type: ignore[method-assign]
    supervisor.live_grants[grant_id] = grant
    start_time = time.monotonic()

    def command(kind: str, command_id: str) -> AgentControlCommand:
        ref = supervisor.session
        return AgentControlCommand(
            command_id=command_id,
            kind=kind,
            correlation_id=command_id,
            jarvis_thread_id=thread.id,
            workspace_id=workspace_id,
            profile_id="qualification-profile",
            hermes_session_id=ref.hermes_session_id if ref else None,
            expected_generation=ref.generation if ref else 0,
            requested_at=datetime.now(UTC),
            deadline_at=datetime.now(UTC) + timedelta(minutes=2),
        )

    try:
        first_ref = supervisor.control(command("start", "qualification-start"))
        assert first_ref is not None
        first_turn = supervisor.turn("Please use the Jarvis context preview tool.", turn_timeout=60)
        assert first_turn["status"] == "success", first_turn

        interrupted: list[dict[str, object]] = []
        turn_thread = threading.Thread(
            target=lambda: interrupted.append(supervisor.turn("interrupt-turn", turn_timeout=60)), daemon=True
        )
        turn_thread.start()
        if not interrupt_entered.wait(timeout=30):
            raise RuntimeError("interrupt smoke inference did not start")
        supervisor.control(command("interrupt", "qualification-interrupt"))
        interrupt_release.set()
        turn_thread.join(timeout=45)
        if turn_thread.is_alive():
            raise RuntimeError("interrupted Hermes turn did not return")

        assert supervisor.process is not None
        supervisor.process.kill()
        supervisor.process.wait(timeout=10)
        recovered_turn = supervisor.turn("Complete the recovered turn.", turn_timeout=60)
        assert recovered_turn["status"] == "success", recovered_turn
        assert supervisor.session is not None and supervisor.session.generation == 2

        with open_sqlite_connection() as connection:
            projected_events = connection.execute(
                "SELECT event_type, payload FROM events WHERE event_type IN "
                "('hermes.agent_event', 'hermes.tool_result') ORDER BY rowid"
            ).fetchall()
            interactions = connection.execute(
                "SELECT COUNT(*) FROM ai_thread_interactions WHERE thread_id = ?", (thread.id,)
            ).fetchone()[0]
        event_types = [row["event_type"] for row in projected_events]
        evidence = {
            "qualification": "146 Hermes real-worker loopback smoke",
            "inference_mode": "deterministic loopback inference stub; no model or provider",
            "native_tool_disposition": (
                "Delegation and skills toolsets remain disabled until their actions are routed "
                "through the Jarvis capability broker."
            ),
            "hermes_version": "0.21.4",
            "hermes_revision": first_ref.upstream_revision,
            "initial_turn": first_turn["status"],
            "broker_tool_result_projected": "hermes.tool_result" in event_types,
            "agent_events_projected": event_types.count("hermes.agent_event"),
            "interrupt_acknowledged": True,
            "interrupted_turn_returned": bool(interrupted),
            "worker_crash_recovered": supervisor.session.generation == 2,
            "recovered_turn": recovered_turn["status"],
            "ai_thread_interactions": interactions,
            "inference_stub_calls": inference_count[0],
            "elapsed_seconds": round(time.monotonic() - start_time, 3),
            "event_types": event_types,
        }
        if not evidence["broker_tool_result_projected"] or evidence["agent_events_projected"] < 2:
            raise RuntimeError("Jarvis broker or agent-event projection evidence is missing")
        out = Path(__file__).with_name("hermes-smoke.json")
        out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2))
    except BaseException:
        print(json.dumps({
            "debug_inference_calls": inference_count[0],
            "supervisor_status": supervisor.status(),
            "supervisor_frames": supervisor_frames,
        }), file=sys.stderr, flush=True)
        raise
    finally:
        if supervisor.process is not None and supervisor.process.poll() is None:
            supervisor.process.terminate()
            supervisor.process.wait(timeout=10)
