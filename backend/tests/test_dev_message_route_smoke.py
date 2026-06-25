from collections.abc import Iterator
from uuid import UUID
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


DEV_ENDPOINT = "/api/dev/message-route-smoke"
BLOCKED_MESSAGES = (
    "my API key is sk-test-secret-12345678",
    "use MCP to call a tool",
    r"read local file C:\secret.txt",
    "write this to memory",
    "browse the web for this",
    "send this to Claude",
)
UNSUPPORTED_FIELDS = (
    "assume_public_simple",
    "use_phase_b_hints",
    "phase_b_source_kind",
    "phase_b_source_case_id",
    "run_local_phase_b",
    "phase_b_endpoint",
    "phase_b_model",
    "model",
    "endpoint",
    "timeout_s",
    "provider",
    "tool",
    "memory_write",
    "retrieval",
    "browser",
    "terminal",
    "mcp",
    "now",
)


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


def _assert_safe_blocked_body(body: dict[str, object]) -> None:
    assert isinstance(body["trace_id"], str)
    assert body["audit_ref"] is None
    assert body["executed"] is False
    assert "input_obj" not in body
    assert "decision" not in body
    assert "audit_notes" not in body
    assert "response" not in body


def _assert_safe_validation_body(body: dict[str, object]) -> None:
    _assert_safe_blocked_body(body)
    assert body["reason"] == "validation_error"
    assert isinstance(body["error_type"], str)


def _assert_no_validation_leakage(body_text: str) -> None:
    for forbidden in (
        "input_obj",
        "decision",
        "audit_notes",
        "raw prompt",
        "raw_model_output",
        "stack trace",
        "Traceback",
        "pydantic",
        "url",
    ):
        assert forbidden not in body_text


def test_c1_001_endpoint_disabled_by_default(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    smoke_call = Mock(side_effect=AssertionError("smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", smoke_call)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    assert response.status_code == 404
    body = response.json()
    _assert_safe_blocked_body(body)
    assert body["reason"] == "dev_message_route_smoke_disabled"
    smoke_call.assert_not_called()
    responder_builder.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    (
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 12001},
        {"message": 42},
        {"message": "Explain what a pump is.", "assume_public_simple": True},
    ),
)
def test_c1_r1_disabled_endpoint_masks_validation_errors(
    client: TestClient,
    monkeypatch,
    payload: dict[str, object],
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, json=payload)

    assert response.status_code == 404
    body_text = response.text
    body = response.json()
    _assert_safe_blocked_body(body)
    assert body["reason"] == "dev_message_route_smoke_disabled"
    assert "validation_error" not in body_text
    assert "pydantic" not in body_text
    assert "extra_forbidden" not in body_text
    assert "string_too_short" not in body_text
    assert "string_too_long" not in body_text
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


def test_c1_002_default_request_does_not_call_model(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "0")
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    assert response.status_code == 200
    body = response.json()
    _assert_safe_blocked_body(body)
    assert body["reason"] == "not_safe_local_route"
    assert body["assume_public_simple_used"] is False
    assert body["use_phase_b_hints_used"] is True
    assert body["phase_b_source_kind"] == "stub"
    assert body["phase_b_source_used"] is False
    responder_builder.assert_not_called()


def test_c1_003_benign_local_smoke_executes_only_with_server_and_request_gates(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")
    fake_responder = Mock(return_value="A pump moves fluid.")
    responder_builder = Mock(return_value=fake_responder)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "Explain what a pump is.", "run_local_responder": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is True
    assert body["reason"] == "local_answer"
    assert body["response"] == "A pump moves fluid."
    assert body["assume_public_simple_used"] is True
    assert body["use_phase_b_hints_used"] is True
    assert body["phase_b_source_kind"] == "stub"
    assert body["phase_b_source_used"] is False
    assert set(body["decision_summary"]) == {"route_action", "route_tier", "allowed_execution_mode"}
    fake_responder.assert_called_once_with("Explain what a pump is.")
    responder_builder.assert_called_once()


def test_c1_004_run_local_responder_alone_does_not_bypass_policy(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "0")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")
    fake_responder = Mock(return_value="should not run")
    monkeypatch.setattr(smoke_adapter, "build_local_responder", Mock(return_value=fake_responder))

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "Explain what a pump is.", "run_local_responder": True},
    )

    assert response.status_code == 200
    body = response.json()
    _assert_safe_blocked_body(body)
    assert body["reason"] == "not_safe_local_route"
    fake_responder.assert_not_called()


def test_c1_local_responder_gate_blocks_before_builder(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "0")
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "Explain what a pump is.", "run_local_responder": True},
    )

    assert response.status_code == 200
    body = response.json()
    _assert_safe_blocked_body(body)
    assert body["reason"] == "local_responder_disabled"
    responder_builder.assert_not_called()


def test_c1_005_assume_public_simple_is_not_accepted_from_client(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "Explain what a pump is.", "assume_public_simple": True},
    )

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    assert body["error_type"] == "ValidationError"
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


@pytest.mark.parametrize("field", ("model", "endpoint", "timeout_s"))
def test_c1_006_client_cannot_select_model_endpoint_timeout(
    client: TestClient,
    monkeypatch,
    field: str,
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is.", field: "bad"})

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


@pytest.mark.parametrize("message", BLOCKED_MESSAGES)
def test_c1_007_hard_and_operational_gates_dominate(
    client: TestClient,
    monkeypatch,
    message: str,
) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")
    fake_responder = Mock(return_value="should not run")
    monkeypatch.setattr(smoke_adapter, "build_local_responder", Mock(return_value=fake_responder))

    response = client.post(DEV_ENDPOINT, json={"message": message, "run_local_responder": True})

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    _assert_safe_blocked_body(body)
    fake_responder.assert_not_called()
    assert message not in body_text
    assert "sk-test-secret-12345678" not in body_text
    assert "input_obj" not in body_text
    assert "audit_notes" not in body_text


@pytest.mark.parametrize("field", UNSUPPORTED_FIELDS)
def test_c1_008_unsupported_options_rejected_loudly(
    client: TestClient,
    monkeypatch,
    field: str,
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is.", field: True})

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


def test_c1_009_response_redaction_for_blocked_secret(client: TestClient, monkeypatch) -> None:
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")
    fake_responder = Mock(return_value="should not run")
    monkeypatch.setattr(smoke_adapter, "build_local_responder", Mock(return_value=fake_responder))

    response = client.post(
        DEV_ENDPOINT,
        json={"message": "my API key is sk-test-secret-12345678", "run_local_responder": True},
    )

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    _assert_safe_blocked_body(body)
    assert "my API key" not in body_text
    assert "sk-test-secret-12345678" not in body_text
    assert "raw prompt" not in body_text
    assert "raw_model_output" not in body_text
    assert "full decision" not in body_text
    fake_responder.assert_not_called()


def test_c1_010_no_db_memory_retrieval_side_effects(client: TestClient, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    before_events = _event_count()

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    assert response.status_code == 200
    assert _event_count() == before_events
    assert not list((tmp_path / "JarvisOS" / "artifacts").glob("**/*"))


def test_c1_011_import_safety(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings
    from app.modules.dev_message_route import smoke_adapter

    get_settings.cache_clear()
    smoke_call = Mock(side_effect=AssertionError("smoke path must not run at import/app creation"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built at import/app creation"))
    monkeypatch.setattr(smoke_adapter, "run_message_route_smoke", smoke_call)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    from app.main import create_app

    create_app()

    smoke_call.assert_not_called()
    responder_builder.assert_not_called()
    get_settings.cache_clear()


def test_c1_012_trace_contract(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["trace_id"], str)
    assert body["audit_ref"] is None


def test_c1_internal_exception_returns_safe_500(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    monkeypatch.setattr(route, "run_dev_message_route_smoke", Mock(side_effect=RuntimeError("boom")))

    response = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    assert response.status_code == 500
    body_text = response.text
    body = response.json()
    assert body["executed"] is False
    assert body["reason"] == "internal_error"
    assert body["audit_ref"] is None
    assert body["error_type"] == "RuntimeError"
    assert "boom" not in body_text
    assert "input_obj" not in body_text
    assert "audit_notes" not in body_text


def test_c1_r1_enabled_invalid_message_does_not_echo_sensitive_input(
    client: TestClient,
    monkeypatch,
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)
    secret_message = "sk-test-secret-12345678" + ("x" * 12000)

    response = client.post(DEV_ENDPOINT, json={"message": secret_message})

    assert response.status_code == 422
    body_text = response.text
    body = response.json()
    _assert_safe_validation_body(body)
    assert body["error_type"] == "ValidationError"
    assert body["validation_error_count"] == 1
    assert "sk-test-secret-12345678" not in body_text
    assert secret_message not in body_text
    assert '"input"' not in body_text
    _assert_no_validation_leakage(body_text)
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


def test_c1_r1_enabled_malformed_json_returns_safe_validation_response(
    client: TestClient,
    monkeypatch,
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(
        DEV_ENDPOINT,
        content="not valid json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    body_text = response.text
    body = response.json()
    _assert_safe_validation_body(body)
    assert body["error_type"] == "InvalidJSON"
    assert "not valid json" not in body_text
    _assert_no_validation_leakage(body_text)
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


def test_c1_r1_enabled_empty_body_returns_safe_validation_response(
    client: TestClient,
    monkeypatch,
) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    responder_builder = Mock(side_effect=AssertionError("responder must not be built"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)
    monkeypatch.setattr(smoke_adapter, "build_local_responder", responder_builder)

    response = client.post(DEV_ENDPOINT, content=b"")

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    assert body["error_type"] == "InvalidJSON"
    route_smoke.assert_not_called()
    responder_builder.assert_not_called()


def test_c1_r1_enabled_validation_error_does_not_fall_to_internal_error(
    client: TestClient,
    monkeypatch,
) -> None:
    import app.api.dev_message_route as route

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)

    response = client.post(DEV_ENDPOINT, json={"message": "x" * 12001})

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    assert body["error_type"] == "ValidationError"
    assert body["reason"] != "internal_error"
    route_smoke.assert_not_called()


def test_c1_r1_fixed_trace_id_covers_all_endpoint_paths(client: TestClient, monkeypatch) -> None:
    import app.api.dev_message_route as route
    from app.modules.dev_message_route import smoke_adapter

    fixed = UUID("00000000-0000-0000-0000-000000000123")
    monkeypatch.setattr(route, "uuid4", Mock(return_value=fixed))

    disabled_valid = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})
    disabled_invalid = client.post(DEV_ENDPOINT, json={"message": ""})

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    enabled_invalid_json = client.post(
        DEV_ENDPOINT,
        content="not valid json",
        headers={"content-type": "application/json"},
    )
    enabled_validation_error = client.post(DEV_ENDPOINT, json={"message": ""})
    enabled_valid_default = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE", "1")
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER", "1")
    fake_responder = Mock(return_value="A pump moves fluid.")
    monkeypatch.setattr(smoke_adapter, "build_local_responder", Mock(return_value=fake_responder))
    enabled_fully_gated = client.post(
        DEV_ENDPOINT,
        json={"message": "Explain what a pump is.", "run_local_responder": True},
    )

    monkeypatch.setattr(route, "run_dev_message_route_smoke", Mock(side_effect=RuntimeError("boom")))
    internal_error = client.post(DEV_ENDPOINT, json={"message": "Explain what a pump is."})

    for response in (
        disabled_valid,
        disabled_invalid,
        enabled_invalid_json,
        enabled_validation_error,
        enabled_valid_default,
        enabled_fully_gated,
        internal_error,
    ):
        assert response.json()["trace_id"] == str(fixed)

    assert internal_error.status_code == 500
    assert internal_error.json()["reason"] == "internal_error"


@pytest.mark.parametrize(
    "payload",
    (
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 12001},
        {"message": 42},
    ),
)
def test_c1_message_validation_rejects_invalid_messages(client: TestClient, monkeypatch, payload: dict[str, object]) -> None:
    import app.api.dev_message_route as route

    monkeypatch.setenv("JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE", "1")
    route_smoke = Mock(side_effect=AssertionError("route smoke path must not run"))
    monkeypatch.setattr(route, "run_dev_message_route_smoke", route_smoke)

    response = client.post(DEV_ENDPOINT, json=payload)

    assert response.status_code == 422
    body = response.json()
    _assert_safe_validation_body(body)
    route_smoke.assert_not_called()
