"""Spec 161: Relay-default escalation of a finished Sidecar turn."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app.core.database import open_sqlite_connection
from app.modules.ai.cloud_escalation import text_digest
from app.modules.events.service import utc_now
from app.modules.relay_gateway import service
from app.modules.relay_gateway.service import RelayEscalationApproval, RelayGatewayError
from tests.test_relay_gateway_157 import _wait, gateway  # noqa: F401 - shared fixture

QUESTION = "Explain the difference between plug flow and CSTR residence time distributions."


def _turn(workspace_id: str = "relay-esc", text: str = QUESTION, state: str = "complete") -> tuple[str, str, str]:
    thread_id, interaction_id, flow_id, now = str(uuid4()), str(uuid4()), str(uuid4()), utc_now()
    with open_sqlite_connection() as connection:
        connection.execute("INSERT OR IGNORE INTO workspaces (id, name, slug, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                           (workspace_id, workspace_id, workspace_id, now, now))
        connection.execute("INSERT INTO ai_threads (id, workspace_id, created_at, last_activity_at) VALUES (?, ?, ?, ?)",
                           (thread_id, workspace_id, now, now))
        connection.execute("INSERT INTO ai_flows (id, workspace_id, task_kind, state, created_at, updated_at) VALUES (?, ?, 'general', ?, ?, ?)",
                           (flow_id, workspace_id, state, now, now))
        connection.execute("INSERT INTO ai_thread_interactions (id, thread_id, request_id, request_digest, interaction_index, user_text, flow_id, persistence_state, created_at, updated_at) VALUES (?, ?, ?, 'digest', 0, ?, ?, 'captured', ?, ?)",
                           (interaction_id, thread_id, f"req-{interaction_id}", text, flow_id, now, now))
        connection.commit()
    return workspace_id, thread_id, interaction_id


def _counts() -> tuple[int, int, int]:
    with open_sqlite_connection() as connection:
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # type: ignore[return-value]
                     for table in ("relay_runs", "cloud_escalations", "sanitized_derivatives"))


def _set_model(gateway, model: str | None) -> None:  # noqa: F811
    config = json.loads(gateway["config_path"].read_text(encoding="utf-8"))
    if model is None:
        config["agents"]["claude"].pop("model", None)
    else:
        config["agents"]["claude"]["model"] = model
    gateway["config_path"].write_text(json.dumps(config), encoding="utf-8")


def test_draft_is_side_effect_free_and_names_agent_model_and_subscription(gateway) -> None:  # noqa: F811
    _set_model(gateway, "claude-opus-5-5")
    workspace_id, thread_id, interaction_id = _turn()
    before = _counts()
    draft = service.draft_relay_escalation(workspace_id, thread_id, interaction_id)
    assert draft.status == "ready" and draft.text == QUESTION and draft.text_digest == text_digest(QUESTION)
    assert (draft.agent, draft.model, draft.billing) == ("claude", "claude-opus-5-5", "subscription")
    assert _counts() == before and gateway["launches"] == []


def test_draft_screens_with_the_deterministic_floor(gateway) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn(text="Use api_key=sk-live-1234567890abcdef1234567890 to call it")
    refused = service.draft_relay_escalation(workspace_id, thread_id, interaction_id)
    assert refused.status == "refused" and refused.text == "" and refused.text_digest is None
    workspace_id, thread_id, interaction_id = _turn(text="Summarize the confidential NDA partner pricing sheet")
    restricted = service.draft_relay_escalation(workspace_id, thread_id, interaction_id)
    assert restricted.status == "edit_required"
    edited = service.draft_relay_escalation(workspace_id, thread_id, interaction_id, "Summarize typical pricing models.")
    assert edited.status == "ready"


def test_unknown_foreign_and_running_turns_are_refused(gateway) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    with pytest.raises(LookupError):
        service.draft_relay_escalation(workspace_id, thread_id, str(uuid4()))
    with pytest.raises(LookupError):
        service.draft_relay_escalation("another-workspace", thread_id, interaction_id)
    workspace_id, thread_id, running = _turn(state="running")
    with pytest.raises(RelayGatewayError, match="source_turn_not_finished"):
        service.draft_relay_escalation(workspace_id, thread_id, running)


def test_disabled_gateway_or_missing_login_is_reported_not_hidden(gateway, monkeypatch) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    gateway["config_path"].write_text(json.dumps({**gateway["config"], "enabled": False}), encoding="utf-8")
    monkeypatch.delenv("JARVISOS_RELAY_GATEWAY_ENABLED", raising=False)
    draft = service.draft_relay_escalation(workspace_id, thread_id, interaction_id)
    assert (draft.status, draft.reason_code) == ("unavailable", "relay_gateway_disabled") and draft.reason
    with pytest.raises(RelayGatewayError, match="relay_gateway_disabled"):
        service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                    RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION)))
    gateway["config_path"].write_text(json.dumps(gateway["config"]), encoding="utf-8")
    (gateway["runtime"].root.parent / "home" / ".claude" / ".credentials.json").unlink()
    assert service.draft_relay_escalation(workspace_id, thread_id, interaction_id).reason_code == "relay_agent_login_missing"
    assert _counts()[0] == 0 and gateway["launches"] == []


def test_approval_submits_a_source_bound_advisory_run_with_the_explicit_model(gateway) -> None:  # noqa: F811
    _set_model(gateway, "claude-opus-5-5")
    workspace_id, thread_id, interaction_id = _turn()
    _, escalations_before, derivatives_before = _counts()
    run = service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                      RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION)))
    assert (run.source_interaction_id, run.model, run.prompt_source) == (interaction_id, "claude-opus-5-5", "operator_attested")
    done = _wait(workspace_id, thread_id, run.id)
    assert done.state == "completed" and done.result_text
    argv = gateway["launches"][0]["argv"]
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert argv[argv.index("--max-turns") + 1] == "1"
    task = argv[argv.index("--task") + 1]
    assert "Advisory question" in task and "Do not modify files" in task and task.endswith(QUESTION)
    # Relay never touches the metered 156 path.
    _, escalations_after, derivatives_after = _counts()
    assert (escalations_after, derivatives_after) == (escalations_before, derivatives_before)


def test_approval_refuses_digest_drift_and_unscreened_text(gateway) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    with pytest.raises(RelayGatewayError, match="text_digest_mismatch"):
        service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                    RelayEscalationApproval(text=QUESTION + "!", text_digest=text_digest(QUESTION)))
    restricted = "Summarize the confidential NDA partner pricing sheet"
    with pytest.raises(RelayGatewayError):
        service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                    RelayEscalationApproval(text=restricted, text_digest=text_digest(restricted)))
    assert _counts()[0] == 0 and gateway["launches"] == []


def test_run_without_configured_model_records_none_and_passes_no_model_flag(gateway) -> None:  # noqa: F811
    _set_model(gateway, None)
    workspace_id, thread_id, interaction_id = _turn()
    run = service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                      RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION)))
    _wait(workspace_id, thread_id, run.id)
    assert run.model is None and "--model" not in gateway["launches"][0]["argv"]
