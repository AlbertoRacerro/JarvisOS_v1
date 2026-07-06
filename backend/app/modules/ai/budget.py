from dataclasses import dataclass

from app.core.database import open_sqlite_connection
from app.modules.ai.contracts import AIPolicyMode
from app.modules.ai.models import AISettingsRead, AIStatusRead
from app.modules.ai.providers.deepseek import DeepSeekProvider
from app.modules.secrets.storage import get_effective_scaleway_api_key, resolve_secret_ref

SCALEWAY_STUB_IMPLEMENTATION = "stub_no_external_calls"
SCALEWAY_LIVE_IMPLEMENTATION = "live_chat_completions"
DEEPSEEK_PROVIDER_MODE = "deepseek"


@dataclass(frozen=True)
class ProviderBudgetGate:
    allowed: bool
    blocking_reason: str | None = None
    provider_id: str | None = None
    usage_tokens_month_to_date: int = 0
    cost_month_to_date_usd: float = 0.0


def evaluate_provider_budget_gate(settings: AISettingsRead, provider_id: str) -> ProviderBudgetGate:
    if settings.policy_mode == AIPolicyMode.DISABLED:
        return ProviderBudgetGate(False, "ai_policy_disabled", provider_id)
    if not settings.paid_ai_enabled:
        return ProviderBudgetGate(False, "paid_ai_disabled", provider_id)
    if settings.monthly_api_budget_usd <= 0:
        return ProviderBudgetGate(False, "monthly_budget_zero", provider_id)
    if settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
        return ProviderBudgetGate(False, "monthly_budget_exhausted", provider_id)

    provider = _registry_provider(provider_id)
    if provider is None or not provider.enabled:
        return ProviderBudgetGate(False, f"{provider_id}_disabled", provider_id)
    if provider.api_key_ref and not resolve_secret_ref(provider.api_key_ref).key_present:
        return ProviderBudgetGate(False, f"{provider_id}_api_key_missing", provider_id)

    usage_tokens, cost = provider_month_to_date_usage(provider_id)
    if provider.monthly_token_cap > 0 and usage_tokens >= provider.monthly_token_cap:
        return ProviderBudgetGate(False, f"{provider_id}_monthly_token_cap_exhausted", provider_id, usage_tokens, cost)
    if provider.monthly_cost_cap_usd > 0 and cost >= provider.monthly_cost_cap_usd:
        return ProviderBudgetGate(False, f"{provider_id}_monthly_cost_cap_exhausted", provider_id, usage_tokens, cost)
    return ProviderBudgetGate(True, None, provider_id, usage_tokens, cost)


def provider_month_to_date_usage(provider_id: str) -> tuple[int, float]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)), 0) AS total_tokens,
                COALESCE(SUM(COALESCE(cost_estimate, 0)), 0) AS total_cost
            FROM ai_jobs
            WHERE provider_id = ?
            """,
            (provider_id,),
        ).fetchone()
    return int(row["total_tokens"]), float(row["total_cost"])


def _registry_provider(provider_id: str):
    from app.modules.ai.provider_registry import load_default_provider_registry

    return load_default_provider_registry().providers.get(provider_id)


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
        gate = evaluate_provider_budget_gate(settings, DEEPSEEK_PROVIDER_MODE)
        external_calls_allowed = gate.allowed
        blocking_reason = gate.blocking_reason
    elif _registry_provider(mode) is not None:
        gate = evaluate_provider_budget_gate(settings, mode)
        external_calls_allowed = gate.allowed
        blocking_reason = gate.blocking_reason
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
    if _registry_provider(provider_mode) is not None:
        return provider_mode
    return "unknown"


def _adapter_enabled_for_mode(provider_mode: str, settings: AISettingsRead) -> bool:
    if provider_mode == "fake":
        return True
    if provider_mode == "scaleway":
        return settings.scaleway_enabled
    if provider_mode == DEEPSEEK_PROVIDER_MODE:
        return True
    provider = _registry_provider(provider_mode)
    if provider is not None:
        return provider.enabled
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
        provider = _registry_provider(provider_mode)
        if provider is not None and provider.api_key_ref:
            return "present" if resolve_secret_ref(provider.api_key_ref).key_present else "missing"
        return "present" if DeepSeekProvider().status().configured else "missing"
    provider = _registry_provider(provider_mode)
    if provider is not None and provider.api_key_ref:
        return "present" if resolve_secret_ref(provider.api_key_ref).key_present else "missing"
    if provider_mode == "fake":
        return "not_required"
    return "unknown"
