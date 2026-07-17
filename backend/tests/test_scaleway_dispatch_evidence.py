from __future__ import annotations

import httpx

from app.modules.ai.contracts import (
    AIExternalDispatchState,
    AIProviderErrorCode,
    AIRequest,
    AITaskType,
)
from app.modules.ai.providers.scaleway import ScalewayChatResult, ScalewayProviderStatus
from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter


class _Provider:
    def __init__(self, *, configured: bool, result=None, error: Exception | None = None):
        self.configured = configured
        self.result = result
        self.error = error
        self.calls = 0

    def status(self) -> ScalewayProviderStatus:
        return ScalewayProviderStatus(
            provider="scaleway",
            configured=self.configured,
            base_url="https://example.test/v1",
            model="scaleway-model",
            implementation="test",
        )

    def model(self) -> str:
        return "scaleway-model"

    def create_work_completion(self, *, prompt: str, estimated_output_tokens: int):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result

    create_live_console_completion = create_work_completion
    create_live_smoke_completion = create_work_completion


def _request(task_type: AITaskType = AITaskType.synthesis) -> AIRequest:
    return AIRequest(task_type=task_type, prompt="harmless test", max_output_tokens=16)


def test_scaleway_missing_credentials_is_not_started() -> None:
    provider = _Provider(configured=False)
    response = ScalewayProviderAdapter(provider=provider).complete(_request())

    assert response.error.code == AIProviderErrorCode.provider_auth_missing
    assert response.external_dispatch_state == AIExternalDispatchState.not_started
    assert response.raw_provider_metadata["external_dispatch_state"] == "not_started"
    assert provider.calls == 0


def test_scaleway_unsupported_task_is_not_started() -> None:
    provider = _Provider(configured=True)
    response = ScalewayProviderAdapter(provider=provider).complete(
        _request(AITaskType.assumption_review)
    )

    assert response.error.code == AIProviderErrorCode.provider_bad_request
    assert response.external_dispatch_state == AIExternalDispatchState.not_started
    assert provider.calls == 0


def test_scaleway_success_is_started() -> None:
    provider = _Provider(
        configured=True,
        result=ScalewayChatResult(
            provider_name="scaleway",
            model="scaleway-model",
            mode="work",
            external_call_attempted=True,
            external_call_succeeded=True,
            response_text="done",
            reported_input_tokens=3,
            reported_output_tokens=2,
            reported_total_tokens=5,
            sanitized_metadata={"finish_reason": "stop"},
        ),
    )
    response = ScalewayProviderAdapter(provider=provider).complete(_request())

    assert response.error is None
    assert response.external_dispatch_state == AIExternalDispatchState.started
    assert response.raw_provider_metadata["external_dispatch_state"] == "started"
    assert provider.calls == 1


def test_scaleway_transport_exception_is_unknown() -> None:
    request = httpx.Request("POST", "https://example.test/v1/chat/completions")
    provider = _Provider(
        configured=True,
        error=httpx.TimeoutException("timeout", request=request),
    )
    response = ScalewayProviderAdapter(provider=provider).complete(_request())

    assert response.error.code == AIProviderErrorCode.provider_timeout
    assert response.external_dispatch_state == AIExternalDispatchState.unknown
    assert response.raw_provider_metadata["external_dispatch_state"] == "unknown"
    assert provider.calls == 1
