import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.delenv("SCALEWAY_BASE_URL", raising=False)
    monkeypatch.delenv("SCALEWAY_MODEL", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


def _event_payloads(event_type: str) -> list[dict[str, object]]:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import list_events_by_type

    with open_sqlite_connection() as connection:
        rows = list_events_by_type(connection, event_type)
    return [json.loads(row["payload"]) for row in rows]


def test_scaleway_key_can_be_set_without_returning_raw_key(client: TestClient) -> None:
    raw_key = "sk-test-secret-1234abcd"

    response = client.post("/secrets/scaleway/api-key", json={"api_key": raw_key})

    assert response.status_code == 200
    body = response.json()
    assert body["key_present"] is True
    assert body["source"] == "runtime_memory"
    assert body["masked_preview"] == "sk-...abcd"
    assert body["last_updated_at"]
    assert raw_key not in json.dumps(body)

    status_response = client.get("/secrets/scaleway/status")
    assert status_response.status_code == 200
    assert status_response.json()["key_present"] is True
    assert status_response.json()["source"] == "runtime_memory"
    assert raw_key not in json.dumps(status_response.json())

    ai_status = client.get("/ai/status").json()
    assert ai_status["scaleway_api_key_configured"] is True
    assert raw_key not in json.dumps(ai_status)


def test_scaleway_key_delete_removes_app_managed_runtime_key(client: TestClient) -> None:
    client.post("/secrets/scaleway/api-key", json={"api_key": "sk-test-delete-1234abcd"})

    response = client.delete("/secrets/scaleway/api-key")

    assert response.status_code == 200
    body = response.json()
    assert body["key_present"] is False
    assert body["source"] == "none"
    assert body["masked_preview"] is None
    assert client.get("/ai/status").json()["scaleway_api_key_configured"] is False


def test_env_var_source_still_works_and_takes_priority(client: TestClient, monkeypatch) -> None:
    raw_runtime_key = "sk-runtime-secret-1234abcd"
    raw_env_key = "sk-env-secret-5678wxyz"
    client.post("/secrets/scaleway/api-key", json={"api_key": raw_runtime_key})

    monkeypatch.setenv("SCALEWAY_API_KEY", raw_env_key)

    status = client.get("/secrets/scaleway/status").json()
    assert status["key_present"] is True
    assert status["source"] == "env"
    assert status["masked_preview"] == "sk-...wxyz"
    assert raw_env_key not in json.dumps(status)
    assert raw_runtime_key not in json.dumps(status)

    delete_response = client.delete("/secrets/scaleway/api-key")
    assert delete_response.status_code == 200
    assert delete_response.json()["source"] == "env"
    assert delete_response.json()["key_present"] is True


def test_provider_key_resolution_prefers_env_over_runtime_memory(client: TestClient, monkeypatch) -> None:
    from app.modules.secrets.storage import get_effective_scaleway_api_key

    client.post("/secrets/scaleway/api-key", json={"api_key": "sk-runtime-secret-1234abcd"})
    monkeypatch.setenv("SCALEWAY_API_KEY", "sk-env-secret-5678wxyz")

    resolved = get_effective_scaleway_api_key()

    assert resolved.source == "env"
    assert resolved.value == "sk-env-secret-5678wxyz"
    assert "sk-env-secret-5678wxyz" not in repr(resolved)


def test_empty_or_invalid_key_is_rejected_without_event(client: TestClient) -> None:
    empty_response = client.post("/secrets/scaleway/api-key", json={"api_key": "   "})
    invalid_key = "sk-test has-space"
    whitespace_response = client.post("/secrets/scaleway/api-key", json={"api_key": invalid_key})
    too_long_key = "sk-" + ("a" * 5000)
    too_long_response = client.post("/secrets/scaleway/api-key", json={"api_key": too_long_key})

    assert empty_response.status_code == 400
    assert whitespace_response.status_code == 400
    assert too_long_response.status_code == 400
    assert invalid_key not in json.dumps(whitespace_response.json())
    assert too_long_key not in json.dumps(too_long_response.json())
    assert whitespace_response.json()["detail"]["code"] == "scaleway_api_key_invalid"
    assert _event_payloads("ScalewayApiKeySaved") == []


def test_wrong_shaped_key_request_does_not_echo_raw_body(client: TestClient) -> None:
    raw_key = "sk-wrong-shape-secret-1234abcd"

    response = client.post(
        "/secrets/scaleway/api-key",
        content=json.dumps(raw_key),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert raw_key not in response.text
    assert response.json()["detail"]["code"] == "scaleway_api_key_invalid"
    assert _event_payloads("ScalewayApiKeySaved") == []


def test_scaleway_key_is_not_stored_in_ai_settings_table(client: TestClient) -> None:
    raw_key = "sk-settings-secret-1234abcd"

    client.post("/secrets/scaleway/api-key", json={"api_key": raw_key})

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        row = connection.execute("SELECT * FROM ai_settings WHERE id = 'default'").fetchone()
    assert row is not None
    assert raw_key not in json.dumps(dict(row))


def test_secret_events_never_include_raw_key(client: TestClient) -> None:
    raw_key = "sk-event-secret-1234abcd"

    client.post("/secrets/scaleway/api-key", json={"api_key": raw_key})
    client.get("/secrets/scaleway/status")
    client.delete("/secrets/scaleway/api-key")

    payloads = (
        _event_payloads("ScalewayApiKeySaved")
        + _event_payloads("ScalewayApiKeyStatusChecked")
        + _event_payloads("ScalewayApiKeyDeleted")
    )
    assert payloads
    payload_text = json.dumps(payloads)
    assert raw_key not in payload_text
    assert "1234abcd" not in payload_text
    assert all("masked_preview" not in payload for payload in payloads)
    assert {payload["action"] for payload in payloads} == {
        "scaleway_key_saved",
        "scaleway_key_status_checked",
        "scaleway_key_deleted",
    }


def test_existing_smoke_console_can_use_runtime_key_with_mocked_provider(client: TestClient, monkeypatch) -> None:
    from app.modules.ai.providers.scaleway import ScalewayChatResult, ScalewayProvider

    raw_key = "sk-runtime-smoke-secret-1234abcd"
    client.post("/secrets/scaleway/api-key", json={"api_key": raw_key})
    client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": True,
            "monthly_api_budget_usd": 1,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "scaleway_monthly_token_cap": 500000,
            "scaleway_hard_stop_token_cap": 800000,
            "use_fake_provider_when_budget_zero": False,
        },
    )

    def fake_completion(self: ScalewayProvider, *, prompt: str, estimated_output_tokens: int) -> ScalewayChatResult:
        return ScalewayChatResult(
            provider_name="scaleway",
            model="mock-model",
            mode="live_smoke_console",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="Hello.",
            reported_input_tokens=2,
            reported_output_tokens=3,
            reported_total_tokens=5,
            sanitized_metadata={"implementation": "mock"},
        )

    monkeypatch.setattr(ScalewayProvider, "create_live_console_completion", fake_completion)

    response = client.post("/ai/smoke-console/run", json={"prompt": "ciao"})

    assert response.status_code == 200
    body = response.json()
    assert body["external_call_attempted"] is True
    assert body["external_call_succeeded"] is True
    assert body["current_month_total_tokens"] == 5
    assert raw_key not in json.dumps(body)


def test_existing_live_smoke_tests_can_use_runtime_key_with_mocked_provider(client: TestClient, monkeypatch) -> None:
    from app.modules.ai.providers.scaleway import ScalewayChatResult, ScalewayProvider

    raw_key = "sk-runtime-fixed-smoke-secret-1234abcd"
    client.post("/secrets/scaleway/api-key", json={"api_key": raw_key})
    client.put(
        "/ai/settings",
        json={
            "provider_mode": "scaleway",
            "default_ai_provider": "scaleway",
            "paid_ai_enabled": True,
            "monthly_api_budget_usd": 1,
            "scaleway_enabled": True,
            "scaleway_smoke_test_enabled": True,
            "scaleway_live_smoke_test_enabled": True,
            "scaleway_monthly_token_cap": 500000,
            "scaleway_hard_stop_token_cap": 800000,
            "use_fake_provider_when_budget_zero": False,
        },
    )

    def fake_completion(self: ScalewayProvider, *, prompt: str, estimated_output_tokens: int) -> ScalewayChatResult:
        return ScalewayChatResult(
            provider_name="scaleway",
            model="mock-model",
            mode="live",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="public synthetic classification",
            reported_input_tokens=4,
            reported_output_tokens=2,
            reported_total_tokens=6,
            sanitized_metadata={"implementation": "mock"},
        )

    monkeypatch.setattr(ScalewayProvider, "create_live_smoke_completion", fake_completion)

    response = client.post("/ai/smoke-tests/run", json={"provider_mode": "scaleway", "smoke_mode": "live"})

    assert response.status_code == 200
    body = response.json()
    assert body["external_call_attempted"] is True
    assert body["external_call_succeeded"] is True
    assert len([result for result in body["results"] if result["external_call_succeeded"]]) == 2
    assert raw_key not in json.dumps(body)
