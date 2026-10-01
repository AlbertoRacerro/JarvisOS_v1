"""Spec 161: Relay-default escalation of a finished Sidecar turn."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import open_sqlite_connection
from app.main import create_app
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


def test_secret_source_cannot_be_replaced_with_safe_text(gateway) -> None:  # noqa: F811
    secret = "Use api_key=sk-live-1234567890abcdef1234567890 to call it"
    workspace_id, thread_id, interaction_id = _turn(text=secret)
    draft = service.draft_relay_escalation(workspace_id, thread_id, interaction_id,
                                           "Summarize typical pricing models.")
    assert (draft.status, draft.reason_code, draft.text, draft.text_digest) == (
        "refused", "secret_detected", "", None)
    with pytest.raises(RelayGatewayError, match="secret_detected"):
        service.escalate_with_relay(
            workspace_id, thread_id, interaction_id,
            RelayEscalationApproval(text="Summarize typical pricing models.",
                                    text_digest=text_digest("different reviewed text")),
        )
    assert _counts()[0] == 0 and gateway["launches"] == []


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
    assert "Commit finished work locally" not in task and "--continue" not in argv
    assert run.continued_from_session_id is None
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


def test_approval_replay_returns_same_run_and_conflicting_digest_is_refused(gateway) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    approval = RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION))
    first = service.escalate_with_relay(workspace_id, thread_id, interaction_id, approval)
    completed = _wait(workspace_id, thread_id, first.id)
    replay = service.escalate_with_relay(workspace_id, thread_id, interaction_id, approval)
    assert replay.id == completed.id
    assert len(gateway["launches"]) == 1 and _counts()[0] == 1
    other_text = QUESTION + " Please add one sentence."
    with pytest.raises(RelayGatewayError, match="relay_escalation_digest_conflict"):
        service.escalate_with_relay(
            workspace_id, thread_id, interaction_id,
            RelayEscalationApproval(text=other_text, text_digest=text_digest(other_text)),
        )
    assert len(gateway["launches"]) == 1


def test_escalation_does_not_continue_or_replace_coding_session(gateway) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    coding = _wait(workspace_id, thread_id, service.submit_relay_run(
        workspace_id, thread_id,
        service.RelayRunRequest(prompt="Review the local repository structure.", agent="claude",
                                cloud_safe_attested=True),
    ).id)
    before = coding.relay_session_id
    assert before
    escalation = service.escalate_with_relay(
        workspace_id, thread_id, interaction_id,
        RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION)),
    )
    finished = _wait(workspace_id, thread_id, escalation.id)
    argv = gateway["launches"][1]["argv"]
    assert "--continue" not in argv and finished.continued_from_session_id is None
    assert "Commit finished work locally" not in argv[argv.index("--task") + 1]
    with open_sqlite_connection() as connection:
        session = connection.execute(
            "SELECT relay_session_id FROM relay_workspaces WHERE thread_id = ?", (thread_id,),
        ).fetchone()["relay_session_id"]
    assert session == before


def test_escalation_routes_cover_success_not_found_and_conflicts(gateway, monkeypatch) -> None:  # noqa: F811
    workspace_id, thread_id, interaction_id = _turn()
    other_workspace, _other_thread, foreign_interaction = _turn(workspace_id="relay-other")
    _same_workspace, other_thread, other_thread_interaction = _turn(workspace_id=workspace_id)
    client = TestClient(create_app())
    base = f"/ai/threads/{thread_id}/interactions/{interaction_id}"
    params = {"workspace_id": workspace_id}
    draft_url = f"{base}/relay-escalation-draft"
    approve_url = f"{base}/relay-escalate"
    assert client.post(draft_url, params=params).status_code == 200
    approval = {"text": QUESTION, "text_digest": text_digest(QUESTION)}
    assert client.post(approve_url, params=params, json=approval).status_code == 200

    for missing in (str(uuid4()), foreign_interaction, other_thread_interaction):
        missing_base = f"/ai/threads/{thread_id}/interactions/{missing}"
        assert client.post(f"{missing_base}/relay-escalation-draft", params=params).status_code == 404
        assert client.post(f"{missing_base}/relay-escalate", params=params, json=approval).status_code == 404
    foreign_params = {"workspace_id": other_workspace}
    assert client.post(draft_url, params=foreign_params).status_code == 404
    assert client.post(approve_url, params=foreign_params, json=approval).status_code == 404

    gateway["config"]["enabled"] = False
    gateway["config_path"].write_text(json.dumps(gateway["config"]), encoding="utf-8")
    monkeypatch.delenv("JARVISOS_RELAY_GATEWAY_ENABLED", raising=False)
    launches_before_replay = len(gateway["launches"])
    replay = client.post(approve_url, params=params, json=approval)
    assert replay.status_code == 200 and len(gateway["launches"]) == launches_before_replay
    disabled_interaction = _turn()[2]
    disabled_thread = None
    with open_sqlite_connection() as connection:
        disabled_thread = connection.execute(
            "SELECT thread_id FROM ai_thread_interactions WHERE id = ?", (disabled_interaction,),
        ).fetchone()["thread_id"]
    disabled_url = f"/ai/threads/{disabled_thread}/interactions/{disabled_interaction}/relay-escalate"
    response = client.post(disabled_url, params=params, json=approval)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "relay_gateway_disabled"

    gateway["config"]["enabled"] = True
    gateway["config_path"].write_text(json.dumps(gateway["config"]), encoding="utf-8")
    drift = client.post(approve_url, params=params,
                        json={"text": QUESTION, "text_digest": text_digest(QUESTION + "!")})
    assert drift.status_code == 409 and drift.json()["detail"]["code"] == "text_digest_mismatch"


def test_run_without_configured_model_records_none_and_passes_no_model_flag(gateway) -> None:  # noqa: F811
    _set_model(gateway, None)
    workspace_id, thread_id, interaction_id = _turn()
    run = service.escalate_with_relay(workspace_id, thread_id, interaction_id,
                                      RelayEscalationApproval(text=QUESTION, text_digest=text_digest(QUESTION)))
    _wait(workspace_id, thread_id, run.id)
    assert run.model is None and "--model" not in gateway["launches"][0]["argv"]
