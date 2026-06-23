import json
from collections.abc import Iterator

import httpx
import pytest

from app.modules.ai.contracts import (
    AIPrivacyClass,
    AIProviderAdapter,
    AIProviderErrorCode,
    AIProviderHealth,
    AIProviderStatus,
    AIRequest,
    AITaskType,
    AIUsageSource,
    ModelRegistry,
    ProviderRegistry,
)
from app.modules.ai.providers.deepseek import DeepSeekChatResult, DeepSeekProvider
from app.modules.ai.providers.deepseek_adapter import (
    DEEPSEEK_ADAPTER_INTERFACE,
    DEEPSEEK_PROVIDER_ID,
    DeepSeekProviderAdapter,
    deepseek_model_registry_entry,
    deepseek_provider_registry_entry,
)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_deepseek_adapter_conforms_to_provider_neutral_interface() -> None:
    adapter: AIProviderAdapter = DeepSeekProviderAdapter()

    assert adapter.provider_id == DEEPSEEK_PROVIDER_ID
    assert adapter.health() == AIProviderHealth.unavailable
    assert adapter.list_models()[0].provider_id == DEEPSEEK_PROVIDER_ID


def test_deepseek_adapter_registry_entries_are_static_and_provider_neutral(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test-secret-1234abcd")
    provider_entry = deepseek_provider_registry_entry()
    model_entry = deepseek_model_registry_entry()

    provider_registry = ProviderRegistry()
    adapter = DeepSeekProviderAdapter()
    provider_registry.register_provider(adapter, provider_entry)
    model_registry = ModelRegistry()
    model_registry.register_model(model_entry)

    assert provider_entry.status == AIProviderStatus.enabled
    assert provider_entry.health == AIProviderHealth.healthy
    assert provider_registry.get_provider("deepseek") is adapter
    assert model_entry.model_id == DeepSeekProvider.default_model
    assert AITaskType.smoke_console_test in model_entry.default_task_types
    assert model_registry.find_models(task_type=AITaskType.smoke_console_test) == [model_entry]


def test_deepseek_provider_maps_openai_compatible_response_without_key_leak(monkeypatch) -> None:
    raw_key = "ds-test-secret-1234abcd"
    captured_headers: dict[str, str] = {}
    monkeypatch.setenv("DEEPSEEK_API_KEY", raw_key)

    def fake_post(*args, **kwargs):
        captured_headers.update(kwargs["headers"])
        return _FakeHTTPResponse(
            {
                "choices": [
                    {
                        "message": {"content": "A mass balance tracks what enters, leaves, and accumulates."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 9, "total_tokens": 20},
            }
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    result = DeepSeekProvider().create_live_console_completion(
        prompt="Explain what a mass balance is in one paragraph.",
        estimated_output_tokens=80,
    )

    assert captured_headers["Authorization"] == f"Bearer {raw_key}"
    assert result.provider_name == "deepseek"
    assert result.model == "deepseek-chat"
    assert result.external_call_attempted is True
    assert result.external_call_succeeded is True
    assert result.reported_input_tokens == 11
    assert result.reported_output_tokens == 9
    assert result.reported_total_tokens == 20
    assert raw_key not in json.dumps(result.sanitized_metadata)


def test_neutral_console_request_maps_to_mocked_deepseek_call(monkeypatch) -> None:
    calls: list[tuple[str, int]] = []

    def fake_completion(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> DeepSeekChatResult:
        calls.append((prompt, estimated_output_tokens))
        return DeepSeekChatResult(
            provider_name="deepseek",
            model="mock-deepseek-model",
            mode="strong_provider_smoke",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="The adapter normalizes requests and responses.",
            reported_input_tokens=8,
            reported_output_tokens=6,
            reported_total_tokens=14,
            sanitized_metadata={
                "implementation": "mock",
                "usage_returned": True,
                "finish_reason": "stop",
                "Authorization": "Bearer should-not-leak",
                "api_key": "should-not-leak",
                "raw_response": {"secret": "should-not-leak"},
            },
        )

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fake_completion)
    monkeypatch.setattr(httpx, "post", _fail_if_network_called)

    response = DeepSeekProviderAdapter().complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass.internal,
            prompt="Summarize what an AI provider adapter does.",
            max_output_tokens=40,
        )
    )

    assert calls == [("Summarize what an AI provider adapter does.", 40)]
    assert response.provider_id == "deepseek"
    assert response.model_id == "mock-deepseek-model"
    assert response.text == "The adapter normalizes requests and responses."
    assert response.usage.input_tokens == 8
    assert response.usage.output_tokens == 6
    assert response.usage.total_tokens == 14
    assert response.usage.usage_source == AIUsageSource.actual
    assert response.raw_provider_metadata["adapter_interface"] == DEEPSEEK_ADAPTER_INTERFACE
    response_text = json.dumps(response.model_dump(mode="json"))
    assert "should-not-leak" not in response_text
    assert "Authorization" not in response_text
    assert "raw_response" not in response_text


def test_missing_deepseek_key_maps_to_safe_error_without_network(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "post", _fail_if_network_called)

    response = DeepSeekProviderAdapter().complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass.public,
            prompt="Explain mass balance briefly.",
            max_output_tokens=30,
        )
    )

    assert response.error is not None
    assert response.error.code == AIProviderErrorCode.provider_auth_missing
    assert response.blocked_reason == "deepseek_live_call_failed"
    assert response.raw_provider_metadata["external_call_attempted"] is False
    assert "DEEPSEEK_API_KEY is required" not in response.model_dump_json()


def test_deepseek_missing_usage_falls_back_to_estimate(monkeypatch) -> None:
    def fake_completion(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> DeepSeekChatResult:
        return DeepSeekChatResult(
            provider_name="deepseek",
            model="mock-deepseek-model",
            mode="strong_provider_smoke",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="OK.",
            reported_input_tokens=None,
            reported_output_tokens=None,
            reported_total_tokens=None,
            sanitized_metadata={"implementation": "mock", "usage_returned": False},
        )

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fake_completion)

    response = DeepSeekProviderAdapter().complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass.public,
            prompt="hello",
            max_output_tokens=12,
        )
    )

    assert response.usage.input_tokens == 2
    assert response.usage.output_tokens == 12
    assert response.usage.usage_source == AIUsageSource.estimated


def test_deepseek_partial_usage_is_marked_mixed(monkeypatch) -> None:
    def fake_completion(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> DeepSeekChatResult:
        return DeepSeekChatResult(
            provider_name="deepseek",
            model="mock-deepseek-model",
            mode="strong_provider_smoke",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="OK.",
            reported_input_tokens=5,
            reported_output_tokens=None,
            reported_total_tokens=None,
            sanitized_metadata={"implementation": "mock", "usage_returned": True},
        )

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fake_completion)

    response = DeepSeekProviderAdapter().complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass.public,
            prompt="hello",
            max_output_tokens=12,
        )
    )

    assert response.usage.input_tokens == 5
    assert response.usage.output_tokens == 12
    assert response.usage.usage_source == AIUsageSource.mixed


def test_unsupported_deepseek_task_type_does_not_call_provider(monkeypatch) -> None:
    def fail(self: DeepSeekProvider, *, prompt: str, estimated_output_tokens: int) -> DeepSeekChatResult:
        raise AssertionError("DeepSeek provider should not be called.")

    monkeypatch.setattr(DeepSeekProvider, "create_live_console_completion", fail)

    response = DeepSeekProviderAdapter().complete(
        AIRequest(
            task_type=AITaskType.model_spec_draft,
            privacy_class=AIPrivacyClass.public,
            prompt="Draft a model spec.",
        )
    )

    assert response.error is not None
    assert response.error.code == AIProviderErrorCode.provider_bad_request
    assert response.blocked_reason == "unsupported_deepseek_task_type"
    assert response.raw_provider_metadata["external_call_attempted"] is False


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


def _fail_if_network_called(*args, **kwargs):
    raise AssertionError("Automated DeepSeek adapter tests must not call the network.")
