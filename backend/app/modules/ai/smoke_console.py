from app.core.database import open_sqlite_connection
from app.modules.ai.budget import evaluate_live_scaleway_smoke_gate
from app.modules.ai.contracts import AIPrivacyClass, AIRequest, AITaskType
from app.modules.ai.models import AISettingsRead, SmokeConsoleRequest, SmokeConsoleResponse, SmokeTestTokenMetadata
from app.modules.ai.privacy import PrivacyPolicyEngine
from app.modules.ai.providers.scaleway_adapter import SCALEWAY_ADAPTER_INTERFACE, ScalewayProviderAdapter
from app.modules.ai.settings import get_ai_settings, record_scaleway_token_usage
from app.modules.ai.token_guard import estimate_tokens, evaluate_token_guard, metadata_with_reported_usage
from app.modules.events.service import log_event, utc_now

SMOKE_CONSOLE_MODE = "live_smoke_console"
SMOKE_CONSOLE_TOKEN_THRESHOLD = 500000
SMOKE_CONSOLE_DEFAULT_OUTPUT_TOKENS = 80
SMOKE_CONSOLE_MAX_OUTPUT_TOKENS = 80
SMOKE_CONSOLE_MAX_PROMPT_LENGTH = 500


def run_smoke_console(request: SmokeConsoleRequest) -> SmokeConsoleResponse:
    settings = get_ai_settings()
    adapter = ScalewayProviderAdapter()
    provider = adapter.provider
    model = provider.model()
    prompt = request.prompt.strip()
    requested_output_tokens = request.max_output_tokens or SMOKE_CONSOLE_DEFAULT_OUTPUT_TOKENS
    estimated_output_tokens = min(requested_output_tokens, SMOKE_CONSOLE_MAX_OUTPUT_TOKENS)
    estimated_input_tokens = estimate_tokens(prompt) if prompt else 0

    _log_console_event(
        "AISmokeConsoleStarted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider=provider.name,
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

    gate_reason = evaluate_live_scaleway_smoke_gate(settings, settings.provider_mode)
    if gate_reason:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class="not_evaluated",
            blocked_reason=gate_reason,
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    if not prompt:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class="unknown",
            blocked_reason="smoke_console_prompt_empty",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source="estimated",
            prompt_length=0,
        )

    if len(prompt) > SMOKE_CONSOLE_MAX_PROMPT_LENGTH:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class="unknown",
            blocked_reason="smoke_console_prompt_too_long",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    if requested_output_tokens > SMOKE_CONSOLE_MAX_OUTPUT_TOKENS:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class="unknown",
            blocked_reason="smoke_console_max_output_tokens_exceeded",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    policy_decision = PrivacyPolicyEngine().decide_for_smoke_console(prompt, policy_mode=settings.policy_mode)
    if not policy_decision.external_allowed:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=policy_decision.blocking_reason or "privacy_policy_blocked",
            external_call_attempted=False,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source="estimated",
            prompt_length=len(prompt),
        )

    token_decision = evaluate_token_guard(
        settings,
        input_text=prompt,
        estimated_output_tokens=estimated_output_tokens,
    )
    if not token_decision.allowed:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=provider.name,
            model=model,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=token_decision.reason or "scaleway_monthly_token_cap_exceeded",
            external_call_attempted=False,
            estimated_input_tokens=token_decision.metadata.estimated_input_tokens,
            estimated_output_tokens=token_decision.metadata.estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source=token_decision.metadata.usage_source,
            prompt_length=len(prompt),
            token_metadata=token_decision.metadata,
        )

    live_response = adapter.complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass(policy_decision.privacy_class),
            prompt=prompt,
            workspace_id=request.workspace_id,
            model_preference=model,
            max_output_tokens=token_decision.metadata.estimated_output_tokens,
            metadata={"mode": SMOKE_CONSOLE_MODE},
        )
    )
    if live_response.error:
        return _blocked_response(
            settings=settings,
            workspace_id=request.workspace_id,
            provider=live_response.provider_id,
            model=live_response.model_id,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=live_response.blocked_reason or "scaleway_live_call_failed",
            external_call_attempted=bool(live_response.raw_provider_metadata.get("external_call_attempted", True)),
            estimated_input_tokens=token_decision.metadata.estimated_input_tokens,
            estimated_output_tokens=token_decision.metadata.estimated_output_tokens,
            actual_input_tokens=None,
            actual_output_tokens=None,
            usage_source=token_decision.metadata.usage_source,
            prompt_length=len(prompt),
            token_metadata=token_decision.metadata,
            error_type=_optional_string(live_response.error.safe_metadata.get("error_type")),
        )

    usage_metadata = metadata_with_reported_usage(
        token_decision.metadata,
        reported_input_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_input_tokens")),
        reported_output_tokens=_reported_token(live_response.raw_provider_metadata.get("reported_output_tokens")),
    )
    input_tokens_to_record = (
        usage_metadata.reported_input_tokens
        if usage_metadata.reported_input_tokens is not None
        else token_decision.metadata.estimated_input_tokens
    )
    output_tokens_to_record = (
        usage_metadata.reported_output_tokens
        if usage_metadata.reported_output_tokens is not None
        else token_decision.metadata.estimated_output_tokens
    )
    settings = record_scaleway_token_usage(
        input_tokens=input_tokens_to_record,
        output_tokens=output_tokens_to_record,
    )

    response = _response(
        settings=settings,
        response_text=live_response.text,
        provider=live_response.provider_id,
        model=live_response.model_id,
        privacy_class=policy_decision.privacy_class,
        blocked_reason=None,
        external_call_attempted=True,
        external_call_succeeded=True,
        estimated_input_tokens=usage_metadata.estimated_input_tokens,
        estimated_output_tokens=usage_metadata.estimated_output_tokens,
        actual_input_tokens=usage_metadata.reported_input_tokens,
        actual_output_tokens=usage_metadata.reported_output_tokens,
        usage_source=usage_metadata.usage_source,
    )
    _log_console_event(
        "AISmokeConsoleCompleted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider=live_response.provider_id,
        model=live_response.model_id,
        privacy_class=policy_decision.privacy_class,
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
    actual_input_tokens: int | None,
    actual_output_tokens: int | None,
    usage_source: str,
    prompt_length: int,
    token_metadata: SmokeTestTokenMetadata | None = None,
    error_type: str | None = None,
) -> SmokeConsoleResponse:
    response = _response(
        settings=settings,
        response_text=None,
        provider=provider,
        model=model,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=False,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=actual_input_tokens,
        actual_output_tokens=actual_output_tokens,
        usage_source=usage_source,
    )
    _log_console_event(
        "AISmokeConsoleBlocked",
        settings=settings,
        workspace_id=workspace_id,
        provider=provider,
        model=model,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=False,
        estimated_input_tokens=response.estimated_input_tokens,
        estimated_output_tokens=response.estimated_output_tokens,
        actual_input_tokens=response.actual_input_tokens,
        actual_output_tokens=response.actual_output_tokens,
        usage_source=response.usage_source,
        prompt_length=prompt_length,
        blocked_by_token_cap=token_metadata.blocked_by_token_cap if token_metadata else False,
        error_type=error_type,
    )
    return response


def _response(
    *,
    settings: AISettingsRead,
    response_text: str | None,
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
) -> SmokeConsoleResponse:
    current_input = settings.scaleway_input_tokens_month_to_date
    current_output = settings.scaleway_output_tokens_month_to_date
    current_total = current_input + current_output
    return SmokeConsoleResponse(
        response_text=response_text,
        provider=provider,
        model=model,
        mode=SMOKE_CONSOLE_MODE,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=external_call_attempted,
        external_call_succeeded=external_call_succeeded,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        actual_input_tokens=actual_input_tokens,
        actual_output_tokens=actual_output_tokens,
        usage_source=usage_source,
        current_month_input_tokens=current_input,
        current_month_output_tokens=current_output,
        current_month_total_tokens=current_total,
        configured_monthly_token_cap=settings.scaleway_monthly_token_cap,
        token_threshold=SMOKE_CONSOLE_TOKEN_THRESHOLD,
        token_threshold_percent=_threshold_percent(current_total),
        remaining_tokens_to_threshold=max(SMOKE_CONSOLE_TOKEN_THRESHOLD - current_total, 0),
    )


def _threshold_percent(total_tokens: int) -> float:
    return round((total_tokens / SMOKE_CONSOLE_TOKEN_THRESHOLD) * 100, 2)


def _reported_token(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _log_console_event(
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
    blocked_by_token_cap: bool = False,
    error_type: str | None = None,
) -> None:
    current_total = settings.scaleway_input_tokens_month_to_date + settings.scaleway_output_tokens_month_to_date
    payload = {
        "workspace_id": workspace_id,
        "provider": provider,
        "provider_id": provider,
        "model": model,
        "model_id": model,
        "adapter_interface": SCALEWAY_ADAPTER_INTERFACE,
        "mode": SMOKE_CONSOLE_MODE,
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
        "current_month_input_tokens": settings.scaleway_input_tokens_month_to_date,
        "current_month_output_tokens": settings.scaleway_output_tokens_month_to_date,
        "current_month_total_tokens": current_total,
        "configured_monthly_token_cap": settings.scaleway_monthly_token_cap,
        "token_threshold": SMOKE_CONSOLE_TOKEN_THRESHOLD,
        "token_threshold_percent": _threshold_percent(current_total),
        "remaining_tokens_to_threshold": max(SMOKE_CONSOLE_TOKEN_THRESHOLD - current_total, 0),
        "blocked_by_token_cap": blocked_by_token_cap,
        "prompt_length": prompt_length,
        "timestamp": utc_now(),
        "error_type": error_type,
    }
    with open_sqlite_connection() as connection:
        log_event(
            connection,
            event_type=event_type,
            actor="local-user",
            target_type="AISmokeConsole",
            target_id=None,
            workspace_id=workspace_id,
            payload=payload,
        )
        connection.commit()
