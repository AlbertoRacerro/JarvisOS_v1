from __future__ import annotations

import os
from typing import Any

from app.modules.ai.contracts import (
    AIModelCapability,
    AIPrivacyClass,
    AIProviderHealth,
    AIRequest,
    AIResponse,
    AIUsage,
    AIUsageSource,
    ModelRegistryEntry,
)
from app.modules.local_ai.runtime.ollama import resolve_ollama_runtime_urls

LOCAL_OLLAMA_PROVIDER_ID = "local_ollama"
_DEFAULT_MODEL = "gemma3:4b"
_DEFAULT_TIMEOUT_S = 30.0
_DEFAULT_KEEP_ALIVE = "30m"
_MODEL_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_MODEL"
_TIMEOUT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S"
_KEEP_ALIVE_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_KEEP_ALIVE"
_NUM_PREDICT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_NUM_PREDICT"
_LOCAL_CHAT_MAX_PROMPT_CHARS = 32000
_LOCAL_CHAT_MAX_OUTPUT_CHARS = 16000
_CHARS_PER_TOKEN_ESTIMATE = 4


def _prompt_text(request: AIRequest) -> str:
    if request.prompt is not None:
        return request.prompt
    return "\n".join(f"{message.role}: {message.content}" for message in request.messages).strip()


def _resolved_model_name(request: AIRequest) -> str:
    return request.model_preference or _configured_model_name()


def _configured_model_name() -> str:
    return os.getenv("AI_ROUTE_LOCAL_MODEL") or os.getenv(_MODEL_ENV) or _DEFAULT_MODEL


def _resolved_endpoint() -> str:
    return resolve_ollama_runtime_urls().generate_endpoint


def _resolved_timeout_s() -> float:
    raw = os.getenv(_TIMEOUT_ENV)
    if raw is None or not raw.strip():
        return _DEFAULT_TIMEOUT_S
    try:
        parsed = float(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_S
    return parsed if parsed > 0 else _DEFAULT_TIMEOUT_S


def _resolved_keep_alive() -> str:
    raw = os.getenv(_KEEP_ALIVE_ENV)
    if raw is None or not raw.strip():
        return _DEFAULT_KEEP_ALIVE
    return raw


def _resolved_num_predict() -> int | None:
    raw = os.getenv(_NUM_PREDICT_ENV)
    if raw is None or not raw.strip():
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _max_output_chars(request: AIRequest) -> int:
    max_tokens = request.max_output_tokens if request.max_output_tokens is not None else 512
    return min(_LOCAL_CHAT_MAX_OUTPUT_CHARS, max(256, max_tokens * _CHARS_PER_TOKEN_ESTIMATE))


def _estimated_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 1


def _usage_from_metadata(model_id: str, prompt: str, text: str, metadata: dict[str, Any]) -> AIUsage:
    usage = metadata.get("usage")
    if isinstance(usage, dict):
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")
        if all(isinstance(value, int) and value >= 0 for value in (input_tokens, output_tokens)):
            return AIUsage(
                provider_id=LOCAL_OLLAMA_PROVIDER_ID,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens if isinstance(total_tokens, int) and total_tokens >= 0 else None,
                usage_source=AIUsageSource.actual,
            )

    input_tokens = metadata.get("input_tokens")
    output_tokens = metadata.get("output_tokens")
    total_tokens = metadata.get("total_tokens")
    if all(isinstance(value, int) and value >= 0 for value in (input_tokens, output_tokens)):
        return AIUsage(
            provider_id=LOCAL_OLLAMA_PROVIDER_ID,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens if isinstance(total_tokens, int) and total_tokens >= 0 else None,
            usage_source=AIUsageSource.actual,
        )

    return AIUsage(
        provider_id=LOCAL_OLLAMA_PROVIDER_ID,
        model_id=model_id,
        input_tokens=_estimated_tokens(prompt),
        output_tokens=_estimated_tokens(text),
        usage_source=AIUsageSource.estimated,
    )


def _safe_raw_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in (
        "response_truncated",
        "response_char_count_returned",
        "response_char_limit",
        "response_limit_source",
        "local_responder_timing",
        "finish_reason",
    ):
        if key in metadata:
            safe[key] = metadata[key]
    return safe


class LocalOllamaAdapter:
    provider_id = LOCAL_OLLAMA_PROVIDER_ID

    def _load_smoke_adapter(self):
        from app.modules.dev_message_route import smoke_adapter

        return smoke_adapter

    def _load_responder(self):
        return self._load_smoke_adapter().call_local_ollama_generate_with_metadata

    def health(self) -> AIProviderHealth:
        return AIProviderHealth.healthy if _configured_model_name() else AIProviderHealth.degraded

    def list_models(self) -> list[ModelRegistryEntry]:
        model_id = _configured_model_name()
        return [
            ModelRegistryEntry(
                model_id=model_id,
                provider_id=LOCAL_OLLAMA_PROVIDER_ID,
                provider_model_name=model_id,
                display_name=f"Local Ollama {model_id}",
                enabled=True,
                capabilities={AIModelCapability.chat_text, AIModelCapability.low_latency, AIModelCapability.low_cost},
                allowed_privacy_classes={AIPrivacyClass.public, AIPrivacyClass.internal},
                notes="Local Ollama adapter through existing responder seam; no cloud provider.",
            )
        ]

    def complete(self, request: AIRequest) -> AIResponse:
        prompt = _prompt_text(request)
        model_id = _resolved_model_name(request)
        responder = self._load_responder()
        metadata = responder(
            prompt,
            model=model_id,
            endpoint=_resolved_endpoint(),
            timeout_s=_resolved_timeout_s(),
            temperature=0.0,
            max_prompt_chars=_LOCAL_CHAT_MAX_PROMPT_CHARS,
            max_output_chars=_max_output_chars(request),
            keep_alive=_resolved_keep_alive(),
            num_predict=_resolved_num_predict(),
        )
        text = metadata["response"]
        return AIResponse(
            provider_id=LOCAL_OLLAMA_PROVIDER_ID,
            model_id=model_id,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            text=text,
            content=text,
            usage=_usage_from_metadata(model_id, prompt, text, metadata),
            finish_reason=metadata.get("finish_reason"),
            safety_status="allowed",
            raw_provider_metadata=_safe_raw_metadata(metadata),
        )

    def stream(self, request: AIRequest) -> object:
        raise NotImplementedError("Local Ollama adapter streaming is not implemented.")
