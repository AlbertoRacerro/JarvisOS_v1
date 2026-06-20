"""Evaluation-only local Gemma adapter for D8 schema dry runs.

This module is not an approved local AI runtime, router, chat surface, or
gatekeeper. It exists only to feed local model output into evaluation harnesses.
"""

import json
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.modules.local_ai.config import LocalGemmaConfig
from app.modules.local_ai.errors import LocalGemmaConfigurationError, LocalGemmaFailureCode
from app.modules.local_ai_eval.models import GemmaEvalOutput


class LocalGemmaEvalAdapterResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    model_name: str
    runtime_endpoint: str
    response_text: str | None = None
    output: GemmaEvalOutput | None = None
    parsed_json: dict[str, Any] | None = None
    failure_code: LocalGemmaFailureCode | None = None
    failure_message: str | None = None


class LocalGemmaEvalAdapter:
    """Small local-only OpenAI-compatible adapter for D8 evaluation dry runs."""

    def __init__(self, config: LocalGemmaConfig, *, client: httpx.Client | None = None) -> None:
        self.config = config
        self._client = client

    def complete(self, prompt: str) -> LocalGemmaEvalAdapterResult:
        try:
            payload = self._payload(prompt)
        except (LocalGemmaConfigurationError, ValidationError) as exc:
            return self._failure(LocalGemmaFailureCode.local_endpoint_invalid, str(exc))

        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=self.config.timeout_seconds)
        try:
            response = client.post(self.config.endpoint_url, json=payload)
            response.raise_for_status()
            response_json = response.json()
            response_text = _extract_text(response_json)
            return self._parse_response_text(response_text)
        except httpx.TimeoutException as exc:
            return self._failure(LocalGemmaFailureCode.timeout, f"Local Gemma runtime timed out: {type(exc).__name__}")
        except httpx.ConnectError as exc:
            return self._failure(
                LocalGemmaFailureCode.runtime_unavailable,
                f"Local Gemma runtime unavailable: {type(exc).__name__}",
            )
        except httpx.NetworkError as exc:
            return self._failure(
                LocalGemmaFailureCode.runtime_unavailable,
                f"Local Gemma runtime network error: {type(exc).__name__}",
            )
        except (httpx.HTTPStatusError, httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            return self._failure(
                LocalGemmaFailureCode.unexpected_local_http_error,
                f"Unexpected local Gemma HTTP response: {type(exc).__name__}",
            )
        finally:
            if owns_client:
                client.close()

    def _payload(self, prompt: str) -> dict[str, object]:
        # Re-validate at call time so manually constructed configs cannot bypass endpoint safety.
        LocalGemmaConfig.model_validate(self.config.model_dump())
        return {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "stream": False,
            "response_format": {"type": "json_object"},
        }

    def _parse_response_text(self, response_text: str) -> LocalGemmaEvalAdapterResult:
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as exc:
            code = LocalGemmaFailureCode.prose_instead_of_schema if _looks_like_prose(response_text) else LocalGemmaFailureCode.invalid_json
            return self._failure(code, f"Local Gemma returned non-schema JSON text: {exc.msg}", response_text=response_text)

        if not isinstance(parsed, dict):
            return self._failure(
                LocalGemmaFailureCode.schema_invalid,
                "Local Gemma JSON output must be an object.",
                response_text=response_text,
                parsed_json=None,
            )
        try:
            output = GemmaEvalOutput.model_validate(parsed)
        except ValidationError as exc:
            return self._failure(
                LocalGemmaFailureCode.schema_invalid,
                f"Local Gemma JSON failed GemmaEvalOutput validation: {exc.errors()[0]['msg']}",
                response_text=response_text,
                parsed_json=parsed,
            )
        return LocalGemmaEvalAdapterResult(
            success=True,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            response_text=response_text,
            parsed_json=parsed,
            output=output,
        )

    def _failure(
        self,
        code: LocalGemmaFailureCode,
        message: str,
        *,
        response_text: str | None = None,
        parsed_json: dict[str, Any] | None = None,
    ) -> LocalGemmaEvalAdapterResult:
        return LocalGemmaEvalAdapterResult(
            success=False,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            response_text=response_text,
            parsed_json=parsed_json,
            failure_code=code,
            failure_message=message,
        )


def _extract_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Missing choices in local runtime response.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("Missing message.content in local runtime response.")
    return message["content"]


def _looks_like_prose(text: str) -> bool:
    stripped = text.lstrip()
    return not stripped.startswith("{") and not stripped.startswith("[")
