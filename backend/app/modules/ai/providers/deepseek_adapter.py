import httpx

from app.modules.ai.contracts import (
    AIMessage,
    AIModelCapability,
    AIPrivacyClass,
    AIProviderError,
    AIProviderErrorCode,
    AIProviderHealth,
    AIProviderKind,
    AIProviderStatus,
    AIRequest,
    AIResponse,
    AITaskType,
    AIUsage,
    AIUsageSource,
    ModelRegistryEntry,
    ProviderRegistryEntry,
)
from app.modules.ai.providers.deepseek import DeepSeekChatResult, DeepSeekProvider
from app.modules.ai.token_guard import estimate_tokens

DEEPSEEK_PROVIDER_ID = "deepseek"
DEEPSEEK_ADAPTER_INTERFACE = "provider_neutral_openai_compatible"
SAFE_DEEPSEEK_METADATA_KEYS = {
    "implementation",
    "base_url_configured",
    "usage_returned",
    "finish_reason",
}


class DeepSeekProviderAdapter:
    provider_id = DEEPSEEK_PROVIDER_ID

    def __init__(self, provider: DeepSeekProvider | None = None) -> None:
        self.provider = provider or DeepSeekProvider()

    def health(self) -> AIProviderHealth:
        status = self.provider.status()
        return AIProviderHealth.healthy if status.configured else AIProviderHealth.unavailable

    def list_models(self) -> list[ModelRegistryEntry]:
        return [deepseek_model_registry_entry(self.provider)]

    def complete(self, request: AIRequest) -> AIResponse:
        prompt = _prompt_from_request(request)
        estimated_output_tokens = request.max_output_tokens or 160

        if request.task_type != AITaskType.smoke_console_test:
            return self._error_response(
                request,
                prompt=prompt,
                estimated_output_tokens=estimated_output_tokens,
                code=AIProviderErrorCode.provider_bad_request,
                blocked_reason="unsupported_deepseek_task_type",
                message="DeepSeek adapter currently supports provider smoke-console tests only.",
                retryable=False,
            )

        try:
            result = self.provider.create_live_console_completion(
                prompt=prompt,
                estimated_output_tokens=estimated_output_tokens,
            )
        except (RuntimeError, httpx.HTTPError, ValueError, TypeError) as exc:
            return self._error_response(
                request,
                prompt=prompt,
                estimated_output_tokens=estimated_output_tokens,
                code=_error_code_for_exception(exc),
                blocked_reason="deepseek_live_call_failed",
                message="DeepSeek live call failed.",
                retryable=isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)),
                error_type=type(exc).__name__,
            )

        return _response_from_deepseek_result(
            request,
            result,
            prompt=prompt,
            estimated_output_tokens=estimated_output_tokens,
        )

    def stream(self, request: AIRequest) -> object:
        raise NotImplementedError("DeepSeek streaming is not implemented.")

    def _error_response(
        self,
        request: AIRequest,
        *,
        prompt: str,
        estimated_output_tokens: int,
        code: AIProviderErrorCode,
        blocked_reason: str,
        message: str,
        retryable: bool,
        error_type: str | None = None,
    ) -> AIResponse:
        model = request.model_preference or self.provider.model()
        estimated_input_tokens = estimate_tokens(prompt) if prompt else 0
        metadata: dict[str, object] = {
            "adapter_interface": DEEPSEEK_ADAPTER_INTERFACE,
            "external_call_attempted": code
            not in {
                AIProviderErrorCode.provider_auth_missing,
                AIProviderErrorCode.provider_bad_request,
            },
            "external_call_succeeded": False,
        }
        if error_type:
            metadata["error_type"] = error_type
        return AIResponse(
            provider_id=self.provider_id,
            model_id=model,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            text=None,
            content=None,
            usage=AIUsage(
                provider_id=self.provider_id,
                model_id=model,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                usage_source=AIUsageSource.estimated,
            ),
            safety_status="blocked",
            blocked_reason=blocked_reason,
            raw_provider_metadata=metadata,
            error=AIProviderError(
                code=code,
                message=message,
                retryable=retryable,
                safe_metadata={"error_type": error_type} if error_type else {},
            ),
        )


def deepseek_provider_registry_entry(provider: DeepSeekProvider | None = None) -> ProviderRegistryEntry:
    deepseek = provider or DeepSeekProvider()
    status = deepseek.status()
    return ProviderRegistryEntry(
        provider_id=DEEPSEEK_PROVIDER_ID,
        kind=AIProviderKind.openai_compatible,
        display_name="DeepSeek",
        status=AIProviderStatus.enabled if status.configured else AIProviderStatus.missing_credentials,
        health=AIProviderHealth.healthy if status.configured else AIProviderHealth.unavailable,
        enabled=True,
        credential_required=True,
        supports_streaming=False,
        supports_structured_output=False,
        supports_vision=False,
        locality="external",
        notes="Provider-neutral adapter for a narrow env-var-only DeepSeek provider smoke path.",
    )


def deepseek_model_registry_entry(provider: DeepSeekProvider | None = None) -> ModelRegistryEntry:
    deepseek = provider or DeepSeekProvider()
    model = deepseek.model()
    return ModelRegistryEntry(
        model_id=model,
        provider_id=DEEPSEEK_PROVIDER_ID,
        provider_model_name=model,
        display_name=f"DeepSeek {model}",
        enabled=True,
        capabilities={AIModelCapability.chat_text, AIModelCapability.high_reasoning},
        default_task_types={AITaskType.smoke_console_test},
        max_output_tokens=160,
        latency_class="unknown",
        reasoning_class="strong",
        allowed_privacy_classes={AIPrivacyClass.public, AIPrivacyClass.internal},
        notes="Static env-configured model for the DeepSeek provider smoke path; no routing or model discovery.",
    )


def _prompt_from_request(request: AIRequest) -> str:
    if request.prompt is not None:
        return request.prompt
    return "\n".join(_message_to_line(message) for message in request.messages).strip()


def _message_to_line(message: AIMessage) -> str:
    return f"{message.role}: {message.content}"


def _response_from_deepseek_result(
    request: AIRequest,
    result: DeepSeekChatResult,
    *,
    prompt: str,
    estimated_output_tokens: int,
) -> AIResponse:
    reported_input = result.reported_input_tokens
    reported_output = result.reported_output_tokens
    input_tokens = reported_input if reported_input is not None else estimate_tokens(prompt)
    output_tokens = reported_output if reported_output is not None else estimated_output_tokens
    usage_source = _usage_source_for_reported_tokens(reported_input, reported_output)
    metadata = {
        **_safe_deepseek_metadata(result.sanitized_metadata),
        "adapter_interface": DEEPSEEK_ADAPTER_INTERFACE,
        "mode": result.mode,
        "external_call_attempted": result.external_call_attempted,
        "external_call_succeeded": result.external_call_succeeded,
        "reported_input_tokens": reported_input,
        "reported_output_tokens": reported_output,
        "reported_total_tokens": result.reported_total_tokens,
    }
    return AIResponse(
        provider_id=DEEPSEEK_PROVIDER_ID,
        model_id=result.model,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        text=result.response_text,
        content=result.response_text,
        usage=AIUsage(
            provider_id=DEEPSEEK_PROVIDER_ID,
            model_id=result.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_source=usage_source,
        ),
        finish_reason=_optional_string(result.sanitized_metadata.get("finish_reason")),
        safety_status="allowed",
        blocked_reason=None,
        raw_provider_metadata=metadata,
        error=None,
    )


def _usage_source_for_reported_tokens(
    reported_input: int | None,
    reported_output: int | None,
) -> AIUsageSource:
    if reported_input is None and reported_output is None:
        return AIUsageSource.estimated
    if reported_input is not None and reported_output is not None:
        return AIUsageSource.actual
    return AIUsageSource.mixed


def _safe_deepseek_metadata(metadata: dict[str, object]) -> dict[str, object]:
    return {key: metadata[key] for key in SAFE_DEEPSEEK_METADATA_KEYS if key in metadata}


def _error_code_for_exception(exc: Exception) -> AIProviderErrorCode:
    if isinstance(exc, RuntimeError) and "DEEPSEEK_API_KEY" in str(exc):
        return AIProviderErrorCode.provider_auth_missing
    if isinstance(exc, httpx.TimeoutException):
        return AIProviderErrorCode.provider_timeout
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 403}:
        return AIProviderErrorCode.provider_auth_failed
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return AIProviderErrorCode.provider_rate_limited
    if isinstance(exc, httpx.HTTPStatusError) and 400 <= exc.response.status_code < 500:
        return AIProviderErrorCode.provider_bad_request
    if isinstance(exc, httpx.HTTPError):
        return AIProviderErrorCode.provider_unavailable
    return AIProviderErrorCode.provider_unknown_error


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
