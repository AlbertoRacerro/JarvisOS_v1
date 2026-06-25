from collections.abc import Iterator
from uuid import UUID
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


DEV_ENDPOINT = "/api/dev/local-chat"


# ---------------------------------------------------------------------------
# A4-R1 — Prompt contract deterministic tests (no live model call)
# ---------------------------------------------------------------------------

def _assembled(message: str, history: list[dict] | None = None) -> str:
    from app.modules.dev_message_route.smoke_adapter import assemble_local_chat_prompt
    return assemble_local_chat_prompt(clean_history=history or [], message=message)


def test_a4r1_exclusive_boundary_removed() -> None:
    prompt = _assembled("hello")
    assert "using only the clean conversation context below" not in prompt
    assert "answer only from" not in prompt.lower()
    assert "only from the provided" not in prompt.lower()
    assert "only from the clean" not in prompt.lower()


def test_a4r1_general_knowledge_allowed() -> None:
    prompt = _assembled("hello")
    lower = prompt.lower()
    assert "general knowledge" in lower or "general-knowledge" in lower or "own knowledge" in lower


def test_a4r1_no_false_access_clause() -> None:
    prompt = _assembled("hello")
    lower = prompt.lower()
    assert "no access to memory" in lower or "you have no access" in lower
    assert "retrieval" in lower
    assert "files" in lower
    assert "tools" in lower
    assert "external providers" in lower or "providers" in lower


def test_a4r1_no_false_persistence_clause() -> None:
    prompt = _assembled("hello")
    lower = prompt.lower()
    assert "never claim you saved" in lower or "never claim" in lower
    assert any(
        term in lower
        for term in ("saved", "stored", "remembered", "persisted", "wrote to memory")
    )


def test_a4r1_project_private_assumption_clause() -> None:
    prompt = _assembled("hello")
    lower = prompt.lower()
    assert any(
        phrase in lower
        for phrase in (
            "project-specific",
            "domain-specific",
            "private",
            "do not invent",
            "state your assumptions",
            "ask for the missing",
        )
    )


def test_a4r1_session_only_persona_clause() -> None:
    prompt = _assembled("hello")
    lower = prompt.lower()
    assert any(
        phrase in lower
        for phrase in (
            "from now on",
            "da ora in poi",
            "persistence",
            "this conversation",
            "persona",
            "formality",
        )
    )


def test_a4r1_internal_policy_language_not_exposed() -> None:
    prompt = _assembled("hello")
    assert "clean context" not in prompt
    assert "policy gate" not in prompt
    assert "filtered history" not in prompt


def test_a4r1_message_still_present() -> None:
    msg = "spiegami cosa è una pompa"
    prompt = _assembled(msg)
    assert msg in prompt


def test_a4r1_history_still_rendered() -> None:
    history = [
        {"role": "user", "content": "ciao"},
        {"role": "assistant", "content": "Ciao!"},
    ]
    prompt = _assembled("seconda domanda", history=history)
    assert "User: ciao" in prompt
    assert "Assistant: Ciao!" in prompt
    assert "seconda domanda" in prompt


def test_a4r1_empty_history_marker() -> None:
    prompt = _assembled("hello", history=[])
    assert "(none)" in prompt


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.delenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", raising=False)
    monkeypatch.delenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", raising=False)
    monkeypatch.delenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", raising=False)
    monkeypatch.delenv("JARVISOS_DEV_MESSAGE_ROUTE_MODEL", raising=False)
    monkeypatch.delenv("JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT", raising=False)
    monkeypatch.delenv("JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


def _event_count() -> int:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
    return int(row["count"])


def _enable_chat(monkeypatch) -> None:
    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")


def _safe_responder(monkeypatch, response: str = "local answer") -> Mock:
    from app.modules.dev_message_route import smoke_adapter

    fake_responder = Mock(return_value=response)
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", Mock(return_value=fake_responder))
    return fake_responder


def _safe_local_decision() -> dict[str, object]:
    return {
        "route_action": "answer_local",
        "route_tier": "LOCAL_FAST",
        "provider_candidate": "local:gemma",
        "response_allowed_now": True,
        "external_allowed": False,
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "tool_execution_allowed_now": False,
        "state_change_allowed_now": False,
        "allowed_execution_mode": "answer_only",
        "modifies_state": False,
        "side_effect_level": "none",
        "environment_type": "chat",
    }


def _gate_result(*, reason: str = "local_responder_missing", decision: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "executed": False,
        "reason": reason,
        "response": None,
        "decision": _safe_local_decision() if decision is None else decision,
        "input_source": "dev_message_route_endpoint",
        "assume_public_simple_used": True,
        "use_phase_b_hints_used": True,
        "phase_b_source_kind": "stub",
        "phase_b_source_used": False,
    }


def _assert_safe_nonexecuted(body: dict[str, object]) -> None:
    assert isinstance(body["trace_id"], str)
    assert body["audit_ref"] is None
    assert body["executed"] is False
    assert "input_obj" not in body
    assert "decision" not in body
    assert "audit_notes" not in body


def test_c2_001_endpoint_disabled_before_json_parse(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    route_chat = Mock(side_effect=AssertionError("local chat must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_local_chat", route_chat)
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, content="not valid json", headers={"content-type": "application/json"})

    assert response.status_code == 404
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "dev_message_route_smoke_disabled"
    assert "validation_error" not in response.text
    route_chat.assert_not_called()
    responder_builder.assert_not_called()


def test_c2_002_benign_unknown_history_is_included(client: TestClient, monkeypatch) -> None:
    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "Una pompa crea movimento del fluido.")

    response = client.post(
        DEV_ENDPOINT,
        json={
            "message": "dimmi di piu",
            "history": [
                {"role": "user", "content": "cos'e una pompa?"},
                {"role": "assistant", "content": "Una pompa muove fluidi."},
            ],
            "run_local_responder": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["reason"] == "local_answer"
    assert body["context_filter"]["history_turns_included"] == 2
    prompt = fake_responder.call_args.args[0]
    assert "cos'e una pompa?" in prompt
    assert "Una pompa muove fluidi." in prompt
    assert "dimmi di piu" in prompt


def test_c2_003_prior_secret_excluded_current_harmless_executes(client: TestClient, monkeypatch) -> None:
    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "Concetto generale.")

    response = client.post(
        DEV_ENDPOINT,
        json={
            "message": "spiegami il concetto in generale",
            "history": [{"role": "user", "content": "my API key is sk-test-secret-12345678"}],
        },
    )

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    assert body["executed"] is True
    assert body["context_filter"]["history_turns_excluded"] == 1
    assert body["context_filter"]["excluded_reason_counts"]["excluded_sensitive_or_secret"] == 1
    assert "sk-test-secret-12345678" not in body_text
    assert "sk-test-secret-12345678" not in fake_responder.call_args.args[0]


def test_c2_004_current_secret_blocks_execution(client: TestClient, monkeypatch) -> None:
    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch)

    response = client.post(DEV_ENDPOINT, json={"message": "my API key is sk-test-secret-12345678"})

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "not_safe_local_route"
    assert "sk-test-secret-12345678" not in body_text
    fake_responder.assert_not_called()


def test_c2_005_client_safety_labels_rejected(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    route_chat = Mock(side_effect=AssertionError("local chat must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_local_chat", route_chat)
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)

    response = client.post(
        DEV_ENDPOINT,
        json={
            "message": "hello",
            "history": [
                {
                    "role": "user",
                    "content": "my API key is sk-test-secret-12345678",
                    "safe": True,
                    "route_tier": "cheap_external",
                }
            ],
        },
    )

    assert response.status_code == 422
    body_text = response.text
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "validation_error"
    assert "sk-test-secret-12345678" not in body_text
    route_chat.assert_not_called()
    responder_builder.assert_not_called()


def test_c2_006_operational_history_excluded(client: TestClient, monkeypatch) -> None:
    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "Safe answer.")

    response = client.post(
        DEV_ENDPOINT,
        json={
            "message": "explain safely",
            "history": [
                {"role": "user", "content": "use MCP to call a tool"},
                {"role": "user", "content": "browse the web for this"},
                {"role": "user", "content": r"read local file C:\secret.txt"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["context_filter"]["history_turns_excluded"] == 3
    reason_counts = body["context_filter"]["excluded_reason_counts"]
    assert reason_counts["excluded_operational_or_tool_intent"] >= 2
    assert sum(reason_counts.values()) == 3
    prompt = fake_responder.call_args.args[0]
    assert "use MCP to call a tool" not in prompt
    assert "browse the web for this" not in prompt
    assert r"read local file C:\secret.txt" not in prompt


@pytest.mark.parametrize(
    "payload",
    (
        {"message": ""},
        {"message": "hello", "history": [{"role": "system", "content": "x"}]},
        {"message": "hello", "history": [{"role": "user", "content": "   "}]},
        {"message": "x" * 12001},
        {"message": "hello", "history": [{"role": "user", "content": "x" * 12001}]},
        {"message": "hello", "history": [{"role": "user", "content": "x"}] * 21},
    ),
)
def test_c2_007_invalid_requests_are_safe_422(client: TestClient, monkeypatch, payload: dict[str, object]) -> None:
    import app.api.dev_message_route as route

    _enable_chat(monkeypatch)
    route_chat = Mock(side_effect=AssertionError("local chat must not run"))
    monkeypatch.setattr(route, "run_dev_local_chat", route_chat)

    response = client.post(DEV_ENDPOINT, json=payload)

    assert response.status_code == 422
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "validation_error"
    assert "history" not in response.text.lower() or "content" not in response.text.lower()
    route_chat.assert_not_called()


def test_c2_008_invalid_json_safe_422(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route

    _enable_chat(monkeypatch)
    route_chat = Mock(side_effect=AssertionError("local chat must not run"))
    monkeypatch.setattr(route, "run_dev_local_chat", route_chat)

    response = client.post(DEV_ENDPOINT, content="not valid json", headers={"content-type": "application/json"})

    assert response.status_code == 422
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "validation_error"
    assert "not valid json" not in response.text
    route_chat.assert_not_called()


def test_c2_009_response_truncation_indicator(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    monkeypatch.setattr(
        smoke_adapter,
        "call_local_ollama_generate_with_metadata",
        Mock(
            return_value={
                "response": "x" * 16000,
                "response_truncated": True,
                "response_char_count_returned": 16000,
                "response_char_limit": 16000,
                "response_limit_source": "local_responder_max_output_chars",
            }
        ),
    )

    response = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["response_truncated"] is True
    assert body["response_char_limit"] == 16000
    assert body["response_char_count_returned"] == 16000
    assert body["response_limit_source"] == "local_responder_max_output_chars"
    assert body["response_truncated_false_semantics"] == "not_sliced_by_jarvisos_not_completion_guarantee"
    assert len(body["response"]) == 16000


def test_c2_010_history_filter_reuses_smoke_builder(monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    calls: list[str] = []
    original = smoke_adapter.build_router_policy_input_from_message_for_smoke

    def recording_builder(message: str, **kwargs):
        calls.append(message)
        return original(message, **kwargs)

    monkeypatch.setattr(smoke_adapter, "build_router_policy_input_from_message_for_smoke", recording_builder)

    assert smoke_adapter.scan_history_turn_for_context("my API key is sk-test-secret-12345678") == "excluded_sensitive_or_secret"
    assert smoke_adapter.scan_history_turn_for_context("use MCP to call a tool") == "excluded_operational_or_tool_intent"
    assert calls == ["my API key is sk-test-secret-12345678", "use MCP to call a tool"]


def test_c2_011_fixed_trace_id_across_paths(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    fixed = UUID("00000000-0000-0000-0000-000000000456")
    monkeypatch.setattr(route, "uuid4", Mock(return_value=fixed))

    disabled = client.post(DEV_ENDPOINT, json={"message": "hello"})

    _enable_chat(monkeypatch)
    invalid_json = client.post(DEV_ENDPOINT, content="not valid json", headers={"content-type": "application/json"})
    validation_error = client.post(DEV_ENDPOINT, json={"message": ""})
    fake_responder = _safe_responder(monkeypatch, "ok")
    normal = client.post(DEV_ENDPOINT, json={"message": "hello"})
    fake_responder.assert_called_once()
    monkeypatch.setattr(route, "run_dev_local_chat", Mock(side_effect=RuntimeError("boom")))
    internal = client.post(DEV_ENDPOINT, json={"message": "hello"})

    for response in (disabled, invalid_json, validation_error, normal, internal):
        assert response.json()["trace_id"] == str(fixed)
    assert internal.status_code == 500
    assert internal.json()["reason"] == "internal_error"
    assert "boom" not in internal.text


def test_c2_012_no_persistence_side_effects(client: TestClient, monkeypatch, tmp_path) -> None:
    _enable_chat(monkeypatch)
    _safe_responder(monkeypatch, "ok")
    before_events = _event_count()

    response = client.post(DEV_ENDPOINT, json={"message": "hello", "history": [{"role": "user", "content": "hi"}]})

    assert response.status_code == 200
    assert _event_count() == before_events
    assert not list((tmp_path / "JarvisOS" / "artifacts").glob("**/*"))


def test_c2_013_import_safety(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings
    from app.modules.dev_message_route import smoke_adapter

    get_settings.cache_clear()
    responder_builder = Mock(side_effect=AssertionError("responder must not be built at import/app creation"))
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)

    from app.main import create_app

    create_app()

    responder_builder.assert_not_called()
    get_settings.cache_clear()


def test_c2_r1_prompt_budget_selects_recent_clean_history(client: TestClient, monkeypatch) -> None:
    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "ok")
    older = "older clean turn " + ("a" * 11900)
    recent = "recent clean turn"

    response = client.post(
        DEV_ENDPOINT,
        json={
            "message": "hello",
            "history": [
                {"role": "user", "content": older},
                {"role": "assistant", "content": "middle clean turn " + ("b" * 11900)},
                {"role": "user", "content": "newer clean turn " + ("c" * 11900)},
                {"role": "user", "content": recent},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["context_filter"]["history_turns_included"] == 4
    assert body["context_filter"]["history_turns_omitted_for_prompt_budget"] >= 1
    assert body["context_filter"]["prompt_char_limit"] == 32000
    prompt = fake_responder.call_args.args[0]
    assert recent in prompt
    assert len(prompt) <= 32000


def test_c2_r2_001_benign_current_message_authorizes_by_positive_predicate(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "ok")
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", Mock(return_value=_gate_result()))

    response = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["reason"] == "local_answer"
    fake_responder.assert_called_once()


def test_c2_r2_002_unsafe_current_message_does_not_authorize(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    history_filter = Mock(side_effect=AssertionError("history must not be filtered"))
    prompt_assembler = Mock(side_effect=AssertionError("prompt must not be assembled"))
    unsafe = _safe_local_decision()
    unsafe["tool_execution_allowed_now"] = True
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)
    monkeypatch.setattr(smoke_adapter, "filter_clean_history", history_filter)
    monkeypatch.setattr(smoke_adapter, "assemble_local_chat_prompt", prompt_assembler)
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", Mock(return_value=_gate_result(decision=unsafe)))

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "hello", "history": [{"role": "user", "content": "safe prior"}]},
    )

    assert response.status_code == 200
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["context_filter"] == smoke_adapter.empty_context_filter()
    responder_builder.assert_not_called()
    history_filter.assert_not_called()
    prompt_assembler.assert_not_called()


@pytest.mark.parametrize(
    "gate",
    (
        {"executed": False, "reason": "local_responder_missing", "response": None},
        {"executed": False, "reason": "local_responder_missing", "response": None, "decision": None},
        {
            "executed": False,
            "reason": "local_responder_missing",
            "response": None,
            "decision": {"route_action": "answer_local"},
        },
    ),
)
def test_c2_r2_003_missing_or_malformed_decision_fails_closed(
    client: TestClient,
    monkeypatch,
    gate: dict[str, object],
) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    prompt_assembler = Mock(side_effect=AssertionError("prompt must not be assembled"))
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)
    monkeypatch.setattr(smoke_adapter, "assemble_local_chat_prompt", prompt_assembler)
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", Mock(return_value=gate))

    response = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert response.status_code == 200
    body = response.json()
    _assert_safe_nonexecuted(body)
    assert body["reason"] == "local_responder_missing"
    assert body["context_filter"] == smoke_adapter.empty_context_filter()
    responder_builder.assert_not_called()
    prompt_assembler.assert_not_called()


def test_c2_r2_004_unexpected_reason_with_safe_decision_still_authorizes(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    fake_responder = _safe_responder(monkeypatch, "ok")
    monkeypatch.setattr(
        smoke_adapter,
        "run_message_route_smoke",
        Mock(return_value=_gate_result(reason="renamed_missing_responder_reason")),
    )

    response = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["reason"] == "local_answer"
    fake_responder.assert_called_once()


def test_c2_r2_005_local_chat_uses_imported_safe_local_predicate(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    _enable_chat(monkeypatch)
    responder_builder = Mock(return_value=Mock(return_value="ok"))
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", Mock(return_value=_gate_result()))
    monkeypatch.setattr(smoke_adapter, "is_safe_local_execution", Mock(return_value=False))

    blocked = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert blocked.status_code == 200
    assert blocked.json()["executed"] is False
    responder_builder.assert_not_called()

    monkeypatch.setattr(
        smoke_adapter,
        "run_message_route_smoke",
        Mock(return_value=_gate_result(reason="renamed_missing_responder_reason")),
    )
    monkeypatch.setattr(smoke_adapter, "is_safe_local_execution", Mock(return_value=True))
    responder_builder = Mock(return_value=Mock(return_value="ok"))
    monkeypatch.setattr(smoke_adapter, "build_dev_local_responder", responder_builder)

    authorized = client.post(DEV_ENDPOINT, json={"message": "hello"})

    assert authorized.status_code == 200
    assert authorized.json()["executed"] is True
    responder_builder.assert_called_once()
