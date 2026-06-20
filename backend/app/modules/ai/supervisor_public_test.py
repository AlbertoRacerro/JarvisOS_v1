"""Backend-only Supervisor public-test slice.

This module backs the existing /ai/supervisor/public-test route and is not the
full Supervisor AI product, chat, memory, retrieval, or routing layer.
"""

from dataclasses import dataclass
from uuid import uuid4

from app.core.database import open_sqlite_connection
from app.modules.ai.contracts import (
    AIPrivacyClass,
    AIRequest,
    AIPolicyMode,
    AIResponse,
    AIUsage,
    AIUsageSource,
    AITaskType,
)
from app.modules.ai.models import AISettingsRead, SupervisorPublicTestRequest, SupervisorPublicTestResponse
from app.modules.ai.privacy import PrivacyPolicyEngine
from app.modules.ai.providers.deepseek_adapter import DeepSeekProviderAdapter
from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter
from app.modules.ai.settings import get_ai_settings, record_scaleway_token_usage
from app.modules.ai.token_guard import estimate_tokens, evaluate_token_guard
from app.modules.events.service import log_event, utc_now

SUPERVISOR_PUBLIC_TEST_MODE = "supervisor_public_test"
SUPERVISOR_DEFAULT_OUTPUT_TOKENS = 180
SUPERVISOR_MAX_OUTPUT_TOKENS = 240
SUPERVISOR_MAX_PROMPT_LENGTH = 2000
SUPERVISOR_ALLOWED_TASK_TYPES = {
    AITaskType.smoke_console_test,
    AITaskType.assumption_review,
    AITaskType.equation_review,
    AITaskType.simulation_result_interpretation,
    AITaskType.runner_error_explanation,
    AITaskType.code_review,
}
SUPERVISOR_LIMITATIONS = [
    "Narrow public/internal technical test endpoint only.",
    "No chat history, memory, file upload, source grounding, runner execution, or BlueRev proprietary workflow.",
    "Provider choice is temporary and internal; DeepSeek is preferred when configured, Scaleway is fallback only when explicitly configured.",
]


@dataclass(frozen=True)
class ProviderSelection:
    provider_id: str
    model_id: str
    adapter: object


def run_supervisor_public_test(request: SupervisorPublicTestRequest) -> SupervisorPublicTestResponse:
    settings = get_ai_settings()
    prompt = request.prompt.strip()
    task_type = request.task_type or AITaskType.equation_review
    requested_output_tokens = request.max_output_tokens or SUPERVISOR_DEFAULT_OUTPUT_TOKENS
    estimated_output_tokens = min(requested_output_tokens, SUPERVISOR_MAX_OUTPUT_TOKENS)
    estimated_input_tokens = estimate_tokens(prompt) if prompt else 0
    request_id = str(uuid4())
    correlation_id = str(uuid4())

    _log_supervisor_event(
        "AISupervisorPublicTestStarted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider_id=None,
        model_id=None,
        task_type=task_type,
        privacy_class="not_evaluated",
        blocked_reason=None,
        external_call_attempted=False,
        external_call_succeeded=False,
        usage=None,
        prompt_length=len(prompt),
        request_id=request_id,
        correlation_id=correlation_id,
    )

    block = _preflight_block(
        settings=settings,
        prompt=prompt,
        requested_output_tokens=requested_output_tokens,
        task_type=task_type,
    )
    if block is not None:
        return _blocked_response(
            settings=settings,
            request=request,
            task_type=task_type,
            request_id=request_id,
            correlation_id=correlation_id,
            blocked_reason=block,
            privacy_class="unknown",
            event_type="AISupervisorPublicTestBlocked",
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

    policy_decision = PrivacyPolicyEngine().decide_for_smoke_console(prompt, policy_mode=settings.policy_mode)
    if not policy_decision.external_allowed:
        return _blocked_response(
            settings=settings,
            request=request,
            task_type=task_type,
            request_id=request_id,
            correlation_id=correlation_id,
            blocked_reason=policy_decision.blocking_reason or "privacy_policy_blocked",
            privacy_class=policy_decision.privacy_class,
            event_type="AISupervisorPublicTestBlocked",
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

    if policy_decision.privacy_class not in {"public", "internal"}:
        return _blocked_response(
            settings=settings,
            request=request,
            task_type=task_type,
            request_id=request_id,
            correlation_id=correlation_id,
            blocked_reason="supervisor_privacy_class_not_allowed",
            privacy_class=policy_decision.privacy_class,
            event_type="AISupervisorPublicTestBlocked",
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

    selection, blocked_reason = _select_provider(settings, prompt=prompt, estimated_output_tokens=estimated_output_tokens)
    if selection is None:
        return _blocked_response(
            settings=settings,
            request=request,
            task_type=task_type,
            request_id=request_id,
            correlation_id=correlation_id,
            blocked_reason=blocked_reason or "provider_unavailable",
            privacy_class=policy_decision.privacy_class,
            event_type="AISupervisorPublicTestBlocked",
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

    _log_supervisor_event(
        "AISupervisorPublicTestProviderSelected",
        settings=settings,
        workspace_id=request.workspace_id,
        provider_id=selection.provider_id,
        model_id=selection.model_id,
        task_type=task_type,
        privacy_class=policy_decision.privacy_class,
        blocked_reason=None,
        external_call_attempted=False,
        external_call_succeeded=False,
        usage=None,
        prompt_length=len(prompt),
        request_id=request_id,
        correlation_id=correlation_id,
    )

    ai_response = selection.adapter.complete(
        AIRequest(
            task_type=AITaskType.smoke_console_test,
            privacy_class=AIPrivacyClass(policy_decision.privacy_class),
            prompt=_supervisor_prompt(task_type, prompt),
            workspace_id=request.workspace_id,
            model_preference=selection.model_id,
            max_output_tokens=estimated_output_tokens,
            metadata={
                "mode": SUPERVISOR_PUBLIC_TEST_MODE,
                "supervisor_task_type": task_type.value,
            },
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )
    if ai_response.error:
        event_id = _log_supervisor_event(
            "AISupervisorPublicTestProviderFailed",
            settings=settings,
            workspace_id=request.workspace_id,
            provider_id=ai_response.provider_id,
            model_id=ai_response.model_id,
            task_type=task_type,
            privacy_class=policy_decision.privacy_class,
            blocked_reason=ai_response.blocked_reason or "provider_call_failed",
            external_call_attempted=bool(ai_response.raw_provider_metadata.get("external_call_attempted", True)),
            external_call_succeeded=False,
            usage=ai_response.usage,
            prompt_length=len(prompt),
            request_id=request_id,
            correlation_id=correlation_id,
            error_code=ai_response.error.code.value,
        )
        return SupervisorPublicTestResponse(
            answer=None,
            task_type=task_type,
            policy_mode=settings.policy_mode,
            provider_id=ai_response.provider_id,
            model_id=ai_response.model_id,
            usage=ai_response.usage,
            safety_status="blocked",
            blocked_reason=ai_response.blocked_reason or "provider_call_failed",
            event_id=event_id,
            request_id=request_id,
            correlation_id=correlation_id,
            external_call_attempted=bool(ai_response.raw_provider_metadata.get("external_call_attempted", True)),
            external_call_succeeded=False,
            limitations=SUPERVISOR_LIMITATIONS,
        )

    if ai_response.provider_id == "scaleway":
        _record_scaleway_supervisor_usage(settings, ai_response)

    event_id = _log_supervisor_event(
        "AISupervisorPublicTestCompleted",
        settings=settings,
        workspace_id=request.workspace_id,
        provider_id=ai_response.provider_id,
        model_id=ai_response.model_id,
        task_type=task_type,
        privacy_class=policy_decision.privacy_class,
        blocked_reason=None,
        external_call_attempted=True,
        external_call_succeeded=True,
        usage=ai_response.usage,
        prompt_length=len(prompt),
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return SupervisorPublicTestResponse(
        answer=ai_response.text,
        task_type=task_type,
        policy_mode=settings.policy_mode,
        provider_id=ai_response.provider_id,
        model_id=ai_response.model_id,
        usage=ai_response.usage,
        safety_status="allowed",
        blocked_reason=None,
        event_id=event_id,
        request_id=request_id,
        correlation_id=correlation_id,
        external_call_attempted=True,
        external_call_succeeded=True,
        limitations=SUPERVISOR_LIMITATIONS,
    )


def _preflight_block(
    *,
    settings: AISettingsRead,
    prompt: str,
    requested_output_tokens: int,
    task_type: AITaskType,
) -> str | None:
    if settings.policy_mode != AIPolicyMode.FAST_DEV:
        return "supervisor_public_test_requires_fast_dev_policy"
    if not prompt:
        return "supervisor_prompt_empty"
    if len(prompt) > SUPERVISOR_MAX_PROMPT_LENGTH:
        return "supervisor_prompt_too_long"
    if requested_output_tokens > SUPERVISOR_MAX_OUTPUT_TOKENS:
        return "supervisor_max_output_tokens_exceeded"
    if task_type not in SUPERVISOR_ALLOWED_TASK_TYPES:
        return "supervisor_task_type_not_allowed"
    if _looks_like_file_path_request(prompt):
        return "supervisor_file_paths_not_supported"
    return None


def _select_provider(
    settings: AISettingsRead,
    *,
    prompt: str,
    estimated_output_tokens: int,
) -> tuple[ProviderSelection | None, str | None]:
    deepseek = DeepSeekProviderAdapter()
    deepseek_status = deepseek.provider.status()
    budget_reason = _budget_gate(settings)
    if settings.provider_mode == "deepseek":
        if budget_reason:
            return None, budget_reason
        if not deepseek_status.configured:
            return None, "deepseek_api_key_missing"
        return ProviderSelection("deepseek", deepseek_status.model, deepseek), None

    if settings.provider_mode == "scaleway":
        scaleway = ScalewayProviderAdapter()
        scaleway_status = scaleway.provider.status()
        scaleway_reason = _scaleway_gate(settings, scaleway_configured=scaleway_status.configured)
        if scaleway_reason:
            return None, scaleway_reason
        token_decision = evaluate_token_guard(settings, input_text=prompt, estimated_output_tokens=estimated_output_tokens)
        if not token_decision.allowed:
            return None, token_decision.reason or "scaleway_monthly_token_cap_exceeded"
        return ProviderSelection("scaleway", scaleway_status.model, scaleway), None

    return None, "provider_unavailable"


def _budget_gate(settings: AISettingsRead) -> str | None:
    if not settings.paid_ai_enabled:
        return "paid_ai_disabled"
    if settings.monthly_api_budget_usd <= 0:
        return "monthly_budget_zero"
    if settings.api_spend_month_to_date_usd >= settings.monthly_api_budget_usd:
        return "monthly_budget_exhausted"
    return None


def _scaleway_gate(settings: AISettingsRead, *, scaleway_configured: bool) -> str | None:
    budget_reason = _budget_gate(settings)
    if budget_reason:
        return budget_reason
    if not settings.scaleway_enabled:
        return "scaleway_disabled"
    if not settings.scaleway_smoke_test_enabled:
        return "scaleway_smoke_test_disabled"
    if not settings.scaleway_live_smoke_test_enabled:
        return "scaleway_live_smoke_test_disabled"
    if not scaleway_configured:
        return "scaleway_api_key_missing"
    return None


def _supervisor_prompt(task_type: AITaskType, prompt: str) -> str:
    return (
        "You are JarvisOS Supervisor AI in a narrow public/internal technical test mode. "
        "Answer concisely. Do not ask for or process API keys, Authorization headers, .env files, "
        "private keys, passwords, or secrets. Do not claim to run code or inspect files.\n\n"
        f"Task type: {task_type.value}\n"
        f"User technical prompt:\n{prompt}"
    )


def _looks_like_file_path_request(prompt: str) -> bool:
    lowered = prompt.lower()
    file_markers = ("c:\\", "/", "\\", ".csv", ".xlsx", ".pdf", ".docx", ".py")
    file_verbs = ("open ", "read ", "load ", "parse ", "upload ", "attach ")
    return any(marker in lowered for marker in file_markers) and any(verb in lowered for verb in file_verbs)


def _record_scaleway_supervisor_usage(settings: AISettingsRead, response: AIResponse) -> None:
    input_tokens = _reported_token(response.raw_provider_metadata.get("reported_input_tokens"))
    output_tokens = _reported_token(response.raw_provider_metadata.get("reported_output_tokens"))
    record_scaleway_token_usage(
        input_tokens=input_tokens if input_tokens is not None else response.usage.input_tokens,
        output_tokens=output_tokens if output_tokens is not None else response.usage.output_tokens,
    )


def _blocked_response(
    *,
    settings: AISettingsRead,
    request: SupervisorPublicTestRequest,
    task_type: AITaskType,
    request_id: str,
    correlation_id: str,
    blocked_reason: str,
    privacy_class: str,
    event_type: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
) -> SupervisorPublicTestResponse:
    usage = AIUsage(
        provider_id="none",
        model_id="none",
        input_tokens=estimated_input_tokens,
        output_tokens=estimated_output_tokens,
        usage_source=AIUsageSource.estimated,
    )
    event_id = _log_supervisor_event(
        event_type,
        settings=settings,
        workspace_id=request.workspace_id,
        provider_id=None,
        model_id=None,
        task_type=task_type,
        privacy_class=privacy_class,
        blocked_reason=blocked_reason,
        external_call_attempted=False,
        external_call_succeeded=False,
        usage=usage,
        prompt_length=len(request.prompt.strip()),
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return SupervisorPublicTestResponse(
        answer=None,
        task_type=task_type,
        policy_mode=settings.policy_mode,
        provider_id=None,
        model_id=None,
        usage=usage,
        safety_status="blocked",
        blocked_reason=blocked_reason,
        event_id=event_id,
        request_id=request_id,
        correlation_id=correlation_id,
        external_call_attempted=False,
        external_call_succeeded=False,
        limitations=SUPERVISOR_LIMITATIONS,
    )


def _log_supervisor_event(
    event_type: str,
    *,
    settings: AISettingsRead,
    workspace_id: str | None,
    provider_id: str | None,
    model_id: str | None,
    task_type: AITaskType,
    privacy_class: str,
    blocked_reason: str | None,
    external_call_attempted: bool,
    external_call_succeeded: bool,
    usage: AIUsage | None,
    prompt_length: int,
    request_id: str,
    correlation_id: str,
    error_code: str | None = None,
) -> str:
    payload = {
        "workspace_id": workspace_id,
        "policy_mode": settings.policy_mode.value,
        "mode": SUPERVISOR_PUBLIC_TEST_MODE,
        "task_type": task_type.value,
        "provider_id": provider_id,
        "model_id": model_id,
        "privacy_class": privacy_class,
        "blocked_reason": blocked_reason,
        "external_call_attempted": external_call_attempted,
        "external_call_succeeded": external_call_succeeded,
        "usage": usage.model_dump(mode="json") if usage else None,
        "prompt_length": prompt_length,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "timestamp": utc_now(),
        "error_code": error_code,
    }
    with open_sqlite_connection() as connection:
        event_id = log_event(
            connection,
            event_type=event_type,
            actor="local-user",
            target_type="AISupervisorPublicTest",
            target_id=None,
            workspace_id=workspace_id,
            payload=payload,
        )
        connection.commit()
    return event_id


def _reported_token(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
