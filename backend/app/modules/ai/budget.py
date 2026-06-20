from app.modules.ai.contracts import AIPolicyMode
from app.modules.ai.models import AISettingsRead, AIStatusRead
from app.modules.secrets.storage import get_effective_scaleway_api_key
from app.modules.ai.providers.deepseek import DeepSeekProvider

SCALEWAY_STUB_IMPLEMENTATION = "stub_no_external_calls"
SCALEWAY_LIVE_IMPLEMENTATION = "live_chat_completions"
DEEPSEEK_PROVIDER_MODE = "deepseek"


def scaleway_api_key_configured() -> bool:
    return get_effective_scaleway_api_key().key_present


def evaluate_ai_status(settings: AISettingsRead, provider_mode: str | None = None) -> AIStatusRead:
    mode = provider_mode or settings.provider_mode
    key_configured = scaleway_api_key_configured()
    blocking_reason: str | None = None
    current_usage = settings.scaleway_input_tokens_month_to_date + settings.scaleway_output_tokens_month_to_date
    policy_disabled = settings.policy_mode == AIPolicyMode.DISABLED

    external_calls_allowed = False
    if policy_disabled:
        blocking_reason = "ai_policy_disabled"
    elif mode == "fake":
        blocking_reason = None
    elif mode == "scaleway":
        if not settings.scaleway_enabled:
            blocking_reason = "scaleway_disabled"
        elif not settings.scaleway_smoke_test_enabled:
            blocking_reason = "scaleway_smoke_test_disabled"
        elif not key_configured:
            blocking_reason = "scaleway_api_key_missing"
        elif not settings.paid_ai_enabled:
            blocking_reason = "paid_ai_disabled"
        elif settings.monthly_api_budget_usd <= 0:
            blocking_reason = "monthly_budget_zero"
        elif settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
            blocking_reason = "monthly_budget_exhausted"
        elif settings.scaleway_monthly_token_cap <= 0:
            blocking_reason = "scaleway_monthly_token_cap_zero"
        elif settings.scaleway_hard_stop_token_cap <= 0:
            blocking_reason = "scaleway_hard_stop_token_cap_zero"
        elif current_usage >= settings.scaleway_monthly_token_cap:
            blocking_reason = "scaleway_monthly_token_cap_exhausted"
        elif current_usage >= settings.scaleway_hard_stop_token_cap:
            blocking_reason = "scaleway_hard_stop_token_cap_exhausted"
        elif settings.scaleway_live_smoke_test_enabled:
            external_calls_allowed = True
            blocking_reason = None
        else:
            blocking_reason = "scaleway_provider_stub_no_external_call"
    elif mode == DEEPSEEK_PROVIDER_MODE:
        if not DeepSeekProvider().status().configured:
            blocking_reason = "deepseek_api_key_missing"
        elif not settings.paid_ai_enabled:
            blocking_reason = "paid_ai_disabled"
        elif settings.monthly_api_budget_usd <= 0:
            blocking_reason = "monthly_budget_zero"
        elif settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
            blocking_reason = "monthly_budget_exhausted"
        else:
            external_calls_allowed = True
            blocking_reason = None
    else:
        blocking_reason = "unsupported_provider_mode"

    return AIStatusRead(
        policy_mode=settings.policy_mode,
        ai_enabled=not policy_disabled,
        active_provider_mode=mode,
        provider_mode=mode,
        provider_id=_provider_id_for_mode(mode),
        adapter_enabled=_adapter_enabled_for_mode(mode, settings),
        fake_provider_enabled=True,
        scaleway_enabled=settings.scaleway_enabled,
        scaleway_api_key_configured=key_configured,
        scaleway_provider_implementation=SCALEWAY_LIVE_IMPLEMENTATION if settings.scaleway_live_smoke_test_enabled else SCALEWAY_STUB_IMPLEMENTATION,
        scaleway_smoke_test_enabled=settings.scaleway_smoke_test_enabled,
        scaleway_live_smoke_test_enabled=settings.scaleway_live_smoke_test_enabled,
        paid_ai_enabled=settings.paid_ai_enabled,
        monthly_api_budget_usd=settings.monthly_api_budget_usd,
        spend_month_to_date_usd=settings.api_spend_month_to_date_usd,
        scaleway_monthly_token_cap=settings.scaleway_monthly_token_cap,
        scaleway_hard_stop_token_cap=settings.scaleway_hard_stop_token_cap,
        scaleway_free_tier_reference_tokens=settings.scaleway_free_tier_reference_tokens,
        scaleway_input_tokens_month_to_date=settings.scaleway_input_tokens_month_to_date,
        scaleway_output_tokens_month_to_date=settings.scaleway_output_tokens_month_to_date,
        usage_total_tokens=current_usage,
        budget_status=_budget_status(settings),
        credential_status=_credential_status(mode, key_configured),
        external_calls_allowed=external_calls_allowed,
        blocking_reason=blocking_reason,
        default_ai_provider=settings.default_ai_provider,
        default_ai_model=settings.default_ai_model,
    )


def evaluate_live_scaleway_smoke_gate(settings: AISettingsRead, provider_mode: str) -> str | None:
    if settings.policy_mode == AIPolicyMode.DISABLED:
        return "ai_policy_disabled"
    if provider_mode != "scaleway":
        return "scaleway_provider_mode_required"
    if not settings.paid_ai_enabled:
        return "paid_ai_disabled"
    if settings.monthly_api_budget_usd <= 0:
        return "monthly_budget_zero"
    if settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
        return "monthly_budget_exhausted"
    if not settings.scaleway_enabled:
        return "scaleway_disabled"
    if not settings.scaleway_smoke_test_enabled:
        return "scaleway_smoke_test_disabled"
    if not settings.scaleway_live_smoke_test_enabled:
        return "scaleway_live_smoke_test_disabled"
    if not scaleway_api_key_configured():
        return "scaleway_api_key_missing"
    if settings.scaleway_monthly_token_cap <= 0:
        return "scaleway_monthly_token_cap_zero"
    if settings.scaleway_hard_stop_token_cap <= 0:
        return "scaleway_hard_stop_token_cap_zero"
    current_usage = settings.scaleway_input_tokens_month_to_date + settings.scaleway_output_tokens_month_to_date
    if current_usage >= settings.scaleway_monthly_token_cap:
        return "scaleway_monthly_token_cap_exhausted"
    if current_usage >= settings.scaleway_hard_stop_token_cap:
        return "scaleway_hard_stop_token_cap_exhausted"
    return None


def _provider_id_for_mode(provider_mode: str) -> str:
    if provider_mode in {"fake", "scaleway", DEEPSEEK_PROVIDER_MODE}:
        return provider_mode
    return "unknown"


def _adapter_enabled_for_mode(provider_mode: str, settings: AISettingsRead) -> bool:
    if provider_mode == "fake":
        return True
    if provider_mode == "scaleway":
        return settings.scaleway_enabled
    if provider_mode == DEEPSEEK_PROVIDER_MODE:
        return True
    return False


def _budget_status(settings: AISettingsRead) -> str:
    if settings.policy_mode == AIPolicyMode.DISABLED:
        return "ai_policy_disabled"
    if not settings.paid_ai_enabled:
        return "paid_ai_disabled"
    if settings.monthly_api_budget_usd <= 0:
        return "monthly_budget_zero"
    if settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
        return "monthly_budget_exhausted"
    return "available"


def _credential_status(provider_mode: str, key_configured: bool) -> str:
    if provider_mode == "scaleway":
        return "present" if key_configured else "missing"
    if provider_mode == DEEPSEEK_PROVIDER_MODE:
        return "present" if DeepSeekProvider().status().configured else "missing"
    if provider_mode == "fake":
        return "not_required"
    return "unknown"
