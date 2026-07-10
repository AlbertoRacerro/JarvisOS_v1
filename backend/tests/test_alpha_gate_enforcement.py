"""Spec 021 — server-owned external-provider execution gate tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.modules.ai.contracts import (
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIUsage,
)
from app.modules.ai.execution_types import ProviderBinding


def _isolate_and_init(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "jarvisos-alpha-gate"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.database import initialize_database

    initialize_database()


def _configure_external_allowed(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("GLM_API_KEY", "glm-test-key")
    from app.modules.ai.models import AISettingsUpdate
    from app.modules.ai.settings import update_ai_settings

    update_ai_settings(AISettingsUpdate(paid_ai_enabled=True, monthly_api_budget_usd=100))


def _all_ai_jobs() -> list[dict]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT * FROM ai_jobs ORDER BY created_at ASC").fetchall()
    return [dict(row) for row in rows]


class _SuccessAdapter:
    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id
        self.requests: list[AIRequest] = []

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        return AIResponse(
            provider_id=self.provider_id,
            model_id=request.model_preference or "test-model",
            request_id=request.request_id,
            text="ok",
            content="ok",
            usage=AIUsage(
                provider_id=self.provider_id,
                model_id=request.model_preference or "test-model",
                input_tokens=1,
                output_tokens=1,
            ),
            safety_status="allowed",
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


class _RetryableAdapter(_SuccessAdapter):
    def complete(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        return AIResponse(
            provider_id=self.provider_id,
            model_id=request.model_preference or "test-model",
            request_id=request.request_id,
            usage=AIUsage(
                provider_id=self.provider_id,
                model_id=request.model_preference or "test-model",
            ),
            safety_status="blocked",
            blocked_reason="provider_failed",
            error=AIProviderError(
                code=AIProviderErrorCode.provider_timeout,
                message="retryable timeout",
                retryable=True,
            ),
        )


def test_alpha_gate_fails_closed_on_missing_server_context() -> None:
    from app.modules.ai.budget import (
        ALPHA_EXTERNAL_PROVIDER_CALL,
        evaluate_alpha_execution_gate,
    )

    decision = evaluate_alpha_execution_gate(
        settings=None,
        provider_id="deepseek",
        operation=ALPHA_EXTERNAL_PROVIDER_CALL,
    )

    assert decision.allowed is False
    assert decision.reason == "alpha_gate_missing_context"


def test_alpha_gate_rejects_unknown_operation_and_missing_provider(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.budget import (
        ALPHA_EXTERNAL_PROVIDER_CALL,
        evaluate_alpha_execution_gate,
    )
    from app.modules.ai.settings import get_ai_settings

    unsupported = evaluate_alpha_execution_gate(
        settings=get_ai_settings(),
        provider_id="deepseek",
        operation="filesystem_write",
    )
    missing_provider = evaluate_alpha_execution_gate(
        settings=get_ai_settings(),
        provider_id=None,
        operation=ALPHA_EXTERNAL_PROVIDER_CALL,
    )

    assert unsupported.allowed is False
    assert unsupported.reason == "alpha_gate_unsupported_operation:filesystem_write"
    assert missing_provider.allowed is False
    assert missing_provider.reason == "alpha_gate_missing_provider"


def test_network_binding_gate_denial_prevents_adapter_call(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.modules.ai import budget
    from app.modules.ai.budget import AlphaGateDecision
    from app.modules.ai.execution import run_ai_task

    calls: list[tuple[str | None, str]] = []

    def _deny(*, settings, provider_id, operation):
        assert settings is not None
        calls.append((provider_id, operation))
        return AlphaGateDecision(False, "alpha_test_denied", operation, provider_id)

    monkeypatch.setattr(budget, "evaluate_alpha_execution_gate", _deny)
    adapter = _SuccessAdapter("test_provider")
    binding = ProviderBinding(
        "external:test",
        "test_provider",
        "test-model",
        True,
        128,
    )

    outcome = run_ai_task(
        user_prompt="must not execute",
        route_class="external:test",
        max_output_tokens=64,
        adapters={"test_provider": adapter},
        bindings={"external:test": binding},
    )

    assert outcome.status == "config_error"
    assert adapter.requests == []
    assert calls == [("test_provider", budget.ALPHA_EXTERNAL_PROVIDER_CALL)]
    row = _all_ai_jobs()[-1]
    reason = json.loads(row["route_reason_json"])["decision_reason"]
    assert "alpha_test_denied" in reason


def test_offline_fixture_binding_bypasses_only_external_gate(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai import budget
    from app.modules.ai.execution import run_ai_task

    def _unexpected_gate_call(**kwargs):
        raise AssertionError(f"offline binding reached external alpha gate: {kwargs}")

    monkeypatch.setattr(budget, "evaluate_alpha_execution_gate", _unexpected_gate_call)
    adapter = _SuccessAdapter("fixture")
    binding = ProviderBinding(
        "external:fixture",
        "fixture",
        "scripted",
        False,
        128,
    )

    outcome = run_ai_task(
        user_prompt="offline fixture",
        route_class="external:fixture",
        adapters={"fixture": adapter},
        bindings={"external:fixture": binding},
    )

    assert outcome.status == "success"
    assert len(adapter.requests) == 1


def test_each_fallback_binding_is_gated_before_its_adapter(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.modules.ai import budget
    from app.modules.ai.budget import AlphaGateDecision
    from app.modules.ai.execution import run_ai_task

    calls: list[str | None] = []

    def _gate(*, settings, provider_id, operation):
        assert settings is not None
        calls.append(provider_id)
        if provider_id == "glm":
            return AlphaGateDecision(False, "alpha_glm_denied", operation, provider_id)
        return AlphaGateDecision(True, "alpha_gate_open", operation, provider_id)

    monkeypatch.setattr(budget, "evaluate_alpha_execution_gate", _gate)
    first = _RetryableAdapter("deepseek")
    second = _SuccessAdapter("glm")

    outcome = run_ai_task(
        user_prompt="retry then deny fallback",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": first, "glm": second},
    )

    assert outcome.status == "config_error"
    assert len(first.requests) == 1
    assert second.requests == []
    assert calls == ["deepseek", "glm"]
    rows = _all_ai_jobs()
    assert [row["provider_id"] for row in rows] == ["deepseek", "glm"]
    second_reason = json.loads(rows[-1]["route_reason_json"])["decision_reason"]
    assert "alpha_glm_denied" in second_reason


@pytest.mark.parametrize(
    "field",
    ["alpha", "confirmed", "force_external_allowed", "side_effectful"],
)
def test_task_payload_fields_cannot_self_authorize(field: str) -> None:
    from app.modules.ai.models import AITaskRunRequest

    with pytest.raises(ValidationError):
        AITaskRunRequest.model_validate({"prompt": "execute", field: True})
