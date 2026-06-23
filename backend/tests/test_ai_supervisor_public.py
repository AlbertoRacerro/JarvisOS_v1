import json
from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()


def _latest_event_payload(event_type: str) -> dict[str, object]:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import list_events_by_type

    with open_sqlite_connection() as connection:
        rows = list_events_by_type(connection, event_type)
    assert rows
    return json.loads(rows[-1]["payload"])


def _event_payloads(event_type: str) -> list[dict[str, object]]:
    from app.core.database import open_sqlite_connection
    from app.modules.events.service import list_events_by_type

    with open_sqlite_connection() as connection:
        rows = list_events_by_type(connection, event_type)
    return [json.loads(row["payload"]) for row in rows]


def _enable_deepseek_supervisor(client: TestClient, **overrides: object) -> None:
    payload: dict[str, object] = {
        "provider_mode": "deepseek",
        "default_ai_provider": "deepseek",
        "paid_ai_enabled": True,
        "monthly_api_budget_usd": 1,
        "use_fake_provider_when_budget_zero": False,
    }
    payload.update(overrides)
    response = client.put("/ai/settings", json=payload)
    assert response.status_code == 200


def _enable_scaleway_supervisor(client: TestClient, **overrides: object) -> None:
    payload: dict[str, object] = {
        "provider_mode": "scaleway",
        "default_ai_provider": "scaleway",
        "paid_ai_enabled": True,
        "monthly_api_budget_usd": 1,
        "scaleway_enabled": True,
        "scaleway_smoke_test_enabled": True,
        "scaleway_live_smoke_test_enabled": True,
        "scaleway_monthly_token_cap": 500000,
        "scaleway_hard_stop_token_cap": 800000,
        "scaleway_input_tokens_month_to_date": 0,
        "scaleway_output_tokens_month_to_date": 0,
        "use_fake_provider_when_budget_zero": False,
    }
    payload.update(overrides)
    response = client.put("/ai/settings", json=payload)
    assert response.status_code == 200


def _fail_if_deepseek_provider_called(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ai.providers.deepseek import DeepSeekProvider

    def fail(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> object:
        raise AssertionError("DeepSeek provider should not have been called.")

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fail)


def _mock_deepseek_provider(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from app.modules.ai.providers.deepseek import DeepSeekChatResult, DeepSeekProvider

    prompts: list[str] = []

    def fake_completion(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> DeepSeekChatResult:
        prompts.append(prompt)
        assert estimated_output_tokens == 180
        return DeepSeekChatResult(
            provider_name="deepseek",
            model="mock-deepseek-model",
            mode="strong_provider_smoke",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="The exponential equation assumes constant growth rate and unlimited resources.",
            reported_input_tokens=12,
            reported_output_tokens=9,
            reported_total_tokens=21,
            sanitized_metadata={"implementation": "mock", "usage_returned": True, "finish_reason": "stop"},
        )

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fake_completion)
    return prompts


def test_supervisor_rejects_empty_prompt_before_provider(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post("/ai/supervisor/public-test", json={"prompt": "   "})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked_reason"] == "supervisor_prompt_empty"
    assert body["external_call_attempted"] is False


def test_supervisor_bounds_prompt_length_before_provider(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post("/ai/supervisor/public-test", json={"prompt": "x" * 2001})

    assert response.status_code == 200
    assert response.json()["blocked_reason"] == "supervisor_prompt_too_long"
    assert response.json()["external_call_attempted"] is False


def test_supervisor_fast_dev_allows_public_internal_toy_prompt_with_deepseek(
    client: TestClient,
    monkeypatch,
) -> None:
    raw_key = "ds-test-secret-1234abcd"
    monkeypatch.setenv("DEEPSEEK_API_KEY", raw_key)
    _enable_deepseek_supervisor(client)
    prompts = _mock_deepseek_provider(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={
            "prompt": "Review this toy equation and identify obvious modeling limitations: X = X0 exp(mu t)",
            "task_type": "equation_review",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["task_type"] == "equation_review"
    assert body["policy_mode"] == "FAST_DEV"
    assert body["provider_id"] == "deepseek"
    assert body["model_id"] == "mock-deepseek-model"
    assert body["usage"]["input_tokens"] == 12
    assert body["usage"]["output_tokens"] == 9
    assert body["usage"]["usage_source"] == "actual"
    assert body["safety_status"] == "allowed"
    assert body["blocked_reason"] is None
    assert body["external_call_attempted"] is True
    assert body["external_call_succeeded"] is True
    assert body["event_id"]
    assert body["request_id"]
    assert body["correlation_id"]
    assert body["limitations"]
    assert raw_key not in json.dumps(body)
    assert "Authorization" not in json.dumps(body)
    assert "Task type: equation_review" in prompts[0]

    completed_payload = _latest_event_payload("AISupervisorPublicTestCompleted")
    payload_text = json.dumps(completed_payload)
    assert completed_payload["provider_id"] == "deepseek"
    assert completed_payload["usage"]["total_tokens"] == 21
    assert raw_key not in payload_text
    assert "X0 exp" not in payload_text


def test_supervisor_request_cannot_force_provider_or_model(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={
            "prompt": "Summarize what an AI provider adapter does.",
            "provider_id": "scaleway",
            "model_id": "fake-user-model",
        },
    )

    assert response.status_code == 422


def test_supervisor_metadata_cannot_force_provider_or_model(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _mock_deepseek_provider(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={
            "prompt": "Summarize what an AI provider adapter does.",
            "metadata": {
                "provider_id": "scaleway",
                "model_id": "fake-user-model",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_id"] == "deepseek"
    assert body["model_id"] == "mock-deepseek-model"


def test_supervisor_returns_provider_unavailable_when_no_provider_configured(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": "Explain what a mass balance is."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["blocked_reason"] == "provider_unavailable"
    assert body["provider_id"] is None
    assert body["external_call_attempted"] is False


def test_supervisor_blocks_structural_secret_without_provider_call(client: TestClient, monkeypatch) -> None:
    raw_key = "ds-test-secret-1234abcd"
    monkeypatch.setenv("DEEPSEEK_API_KEY", raw_key)
    _enable_deepseek_supervisor(client)
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": f"Authorization: Bearer {raw_key}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["blocked_reason"] == "privacy_policy_secret_blocked"
    assert body["external_call_attempted"] is False
    payload_text = json.dumps(_latest_event_payload("AISupervisorPublicTestBlocked"))
    assert raw_key not in payload_text
    assert "Authorization" not in payload_text


def test_supervisor_normalizes_provider_error(client: TestClient, monkeypatch) -> None:
    from app.modules.ai.providers.deepseek import DeepSeekProvider

    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)

    def fail(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> object:
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fail)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": "Explain what a mass balance is."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_id"] == "deepseek"
    assert body["blocked_reason"] == "deepseek_live_call_failed"
    assert body["safety_status"] == "blocked"
    assert body["external_call_attempted"] is True
    assert body["external_call_succeeded"] is False
    failed_payload = _latest_event_payload("AISupervisorPublicTestProviderFailed")
    assert failed_payload["error_code"] == "provider_timeout"


def test_supervisor_falls_back_to_scaleway_when_explicitly_configured(client: TestClient, monkeypatch) -> None:
    from app.modules.ai.providers.scaleway import ScalewayChatResult, ScalewayProvider

    monkeypatch.setenv("SCALEWAY_API_KEY", "test-only-scaleway-key")
    _enable_scaleway_supervisor(client)

    def fake_completion(self: ScalewayProvider, *, prompt: str, estimated_output_tokens: int) -> ScalewayChatResult:
        return ScalewayChatResult(
            provider_name="scaleway",
            model="mock-scaleway-model",
            mode="live_smoke_console",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="The runner error suggests checking input parameters.",
            reported_input_tokens=7,
            reported_output_tokens=5,
            reported_total_tokens=12,
            sanitized_metadata={"implementation": "mock", "usage_returned": True, "finish_reason": "stop"},
        )

    monkeypatch.setattr(ScalewayProvider, "create_live_console_completion", fake_completion)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": "Explain this generic runner error: invalid dt", "task_type": "runner_error_explanation"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_id"] == "scaleway"
    assert body["model_id"] == "mock-scaleway-model"
    assert body["usage"]["input_tokens"] == 7
    assert body["usage"]["output_tokens"] == 5
    settings = client.get("/ai/settings").json()
    assert settings["scaleway_input_tokens_month_to_date"] == 7
    assert settings["scaleway_output_tokens_month_to_date"] == 5


def test_supervisor_non_fast_dev_policy_blocks_without_provider(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client, policy_mode="STRICT_IP")
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": "Explain what a mass balance is."},
    )

    assert response.status_code == 200
    assert response.json()["blocked_reason"] == "supervisor_public_test_requires_fast_dev_policy"


def test_supervisor_rejects_file_path_prompt_before_provider(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _fail_if_deepseek_provider_called(monkeypatch)

    response = client.post(
        "/ai/supervisor/public-test",
        json={"prompt": "Read C:\\secret\\model.py and summarize it."},
    )

    assert response.status_code == 200
    assert response.json()["blocked_reason"] == "supervisor_file_paths_not_supported"


def test_supervisor_events_do_not_store_prompt_text(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    _enable_deepseek_supervisor(client)
    _mock_deepseek_provider(monkeypatch)

    prompt = "Summarize what an AI provider adapter does."
    response = client.post("/ai/supervisor/public-test", json={"prompt": prompt})

    assert response.status_code == 200
    event_text = json.dumps(
        _event_payloads("AISupervisorPublicTestStarted")
        + _event_payloads("AISupervisorPublicTestProviderSelected")
        + _event_payloads("AISupervisorPublicTestCompleted")
    )
    assert prompt not in event_text
    assert "prompt_length" in event_text
