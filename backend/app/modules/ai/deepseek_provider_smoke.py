"""DeepSeek-only provider smoke path.

This is a diagnostic smoke surface, not provider routing or a general AI
gateway policy implementation.
"""

from app.core.database import open_sqlite_connection
from app.modules.ai.contracts import AIPolicyMode, AIPrivacyClass, AIRequest, AITaskType
from app.modules.ai.models import AISettingsRead, ProviderSmokeRequest, ProviderSmokeResponse
from app.modules.ai.privacy import PrivacyPolicyEngine
from app.modules.ai.providers.deepseek_adapter import (
    DEEPSEEK_ADAPTER_INTERFACE,
    DEEPSEEK_PROVIDER_ID,
    DeepSeekProviderAdapter,
)
from app.modules.ai.settings import get_ai_settings
from app.modules.ai.token_guard import estimate_tokens
from app.modules.events.service import log_event, utc_now

PROVIDER_SMOKE_MODE = "strong_provider_smoke"
PROVIDER_SMOKE_DEFAULT_OUTPUT_TOKENS = 120
PROVIDER_SMOKE_MAX_OUTPUT_TOKENS = 160
PROVIDER_SMOKE_MAX_PROMPT_LENGTH = 1000


def run_provider_smoke(request: ProviderSmokeRequest) -> ProviderSmokeResponse:
    settings = get_ai_settings()
    adapter = DeepSeekProviderAdapter()
    provider_status = adapter.provider.status()
    provider = adapter.provider_id
    model = provider_status.model
    prompt = request.prompt.strip()
    requested_output_tokens = request.max_output_tokens or PROVIDER_SMOKE_DEFAULT_OUTPUT_TOKENS
    estimated_output_tokens = min(requested_output_tokens, PROVIDER_SMOKE_MAX_OUTPUT_TOKENS)
    estimated_input_tokens = estimate_tokens(prompt) if prompt else 0

    _log_provider_smoke_event(
        "AIProviderSmokeStarted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider=provider,
        model=model,
        privacy_class="not_evaluated",
        blocked_reason=None,
        external_call_attempted=False,
        external_call_succeeded=False,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=None,
        actual_output_tokens=None,
        usage_source="estimated",
        prompt_length=len(prompt),
    )

    gate_reason = _provider_smoke_gate(settings, key_configured=provider_status.configured)
    if gate_reason:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class="not_evaluated",
            blocked_reason=gate_reason,
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    if not prompt:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class="unknown",
            blocked_reason="provider_smoke_prompt_empty",
            external_call_attempted=False,
            estimated_input_tokens=0,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=0,
        )

    if len(prompt) > PROVIDER_SMOKE_MAX_PROMPT_LENGTH:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class="unknown",
            blocked_reason="provider_smoke_prompt_too_long",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    if requested_output_tokens > PROVIDER_SMOKE_MAX_OUTPUT_TOKENS:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class="unknown",
            blocked_reason="provider_smoke_max_output_tokens_exceeded",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    policy_decision = PrivacyPolicyEngine().decide_for_smoke_console(prompt, policy_mode=settings.policy_mode)
    if not policy_decision.external_allowed:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=policy_decision.blocking_reason or "privacy_policy_blocked",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    if policy_decision.privacy_class not in {"public", "internal"}:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider,
            model=model,
            privacy_class=policy_decision.privacy_class,
            blocked_reason="provider_smoke_privacy_class_not_allowed",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    live_response = adapter.complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass(policy_decision.privacy_class),
            prompt=prompt,
            workspace_id=request.workspace_id,
            model_preference=model,
            max_output_tokens=estimated_output_tokens,
            metadata={"mode": PROVIDER_SMOKE_MODE},
        )
    )
    if live_response.error:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=live_response.provider_id,
            model=live_response.model_id,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=live_response.blocked_reason or "deepseek_live_call_failed",
            external_call_attempted=bool(live_response.raw_provider_metadata.get("external_call_attempted", True)),
            estimated_input_tokens=live_response.usage.input_tokens,
            estimated_output_tokens=live_response.usage.output_tokens,
            usage_source=live_response.usage.usage_source.value,
            prompt_length=len(prompt),
            error_type=_optional_string(live_response.error.safe_metadata.get("error_type")),
        )

    response = ProviderSmokeResponse(
        response_text=live_response.text,
        provider=live_response.provider_id,
        model=live_response.model_id,
        mode=PROVIDER_SMOKE_MODE,
        privacy_class=policy_decision.privacy_class,
        blocked_reason=None,
        external_call_attempted=True,
        external_call_succeeded=True,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_input_tokens")),
        actual_output_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_output_tokens")),
        usage_source=live_response.usage.usage_source.value,
        provider_metadata={
            "adapter_interface": live_response.raw_provider_metadata.get("adapter_interface"),
            "implementation": live_response.raw_provider_metadata.get("implementation"),
            "usage_returned": live_response.raw_provider_metadata.get("usage_returned"),
            "finish_reason": live_response.finish_reason,
        },
    )
    _log_provider_smoke_event(
        "AIProviderSmokeCompleted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider=response.provider,
        model=response.model,
        privacy_class=response.privacy_class,
        blocked_reason=None,
        external_call_attempted=True,
        external_call_succeeded=True,
        estimated_input_tokens=response.estimated_input_tokens,
        estimated_output_tokens=response.estimated_output_tokens,
        actual_input_tokens=response.actual_input_tokens,
        actual_output_tokens=response.actual_output_tokens,
        usage_source=response.usage_source,
        prompt_length=len(prompt),
    )
    return response


def _provider_smoke_gate(settings: AISettingsRead, *, key_configured: bool) -> str | None:
    if settings.policy_mode == AIPolicyMode.DISABLED:
        return "ai_policy_disabled"
    if settings.provider_mode != DEEPSEEK_PROVIDER_ID:
        return "deepseek_provider_mode_required"
    if not settings.paid_ai_enabled:
        return "paid_ai_disabled"
    if settings.monthly_api_budget_usd <= 0:
        return "monthly_budget_zero"
    if settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
        return "monthly_budget_exhausted"
    if not key_configured:
        return "deepseek_api_key_missing"
    return None


def _blocked_response(
    *,
    settings: AISettingsRead,
    workspace_id: str | None,
    provider: str,
    model: str,
    privacy_class: str,
    blocked_reason: str,
    external_call_attempted: bool,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    usage_source: str,
    prompt_length: int,
    error_type: str | None = None,
) -> ProviderSmokeResponse:
    response = ProviderSmokeResponse(
        response_text=None,
        provider=provider,
        model=model,
        mode=PROVIDER_SMOKE_MODE,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=False,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=None,
        actual_output_tokens=None,
        usage_source=usage_source,
        provider_metadata=None,
    )
    _log_provider_smoke_event(
        "AIProviderSmokeBlocked",
        settings=settings,
        workspace_id=workspace_id,
        provider=provider,
        model=model,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=False,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=None,
        actual_output_tokens=None,
        usage_source=usage_source,
        prompt_length=prompt_length,
        error_type=error_type,
    )
    return response


def _log_provider_smoke_event(
    event_type: str,
    *,
    settings: AISettingsRead,
    workspace_id: str | None,
    provider: str,
    model: str,
    privacy_class: str,
    blocked_reason: str | None,
    external_call_attempted: bool,
    external_call_succeeded: bool,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    actual_input_tokens: int | None,
    actual_output_tokens: int | None,
    usage_source: str,
    prompt_length: int,
    error_type: str | None = None,
) -> None:
    payload = {
        "workspace_id": workspace_id,
        "provider": provider,
        "provider_id": provider,
        "model": model,
        "model_id": model,
        "adapter_interface": DEEPSEEK_ADAPTER_INTERFACE,
        "mode": PROVIDER_SMOKE_MODE,
        "policy_mode": settings.policy_mode.value,
        "privacy_class": privacy_class,
        "blocked_reason": blocked_reason,
        "external_call_attempted": external_call_attempted,
        "external_call_succeeded": external_call_succeeded,
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "actual_input_tokens": actual_input_tokens,
        "actual_output_tokens": actual_output_tokens,
        "usage_source": usage_source,
        "prompt_length": prompt_length,
        "timestamp": utc_now(),
        "error_type": error_type,
    }
    with open_sqlite_connection() as connection:
        log_event(
            connection,
            event_type=event_type,
            actor="local-user",
            target_type="AIProviderSmoke",
            target_id=None,
            workspace_id=workspace_id,
            payload=payload,
        )
        connection.commit()


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _reported_token(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
