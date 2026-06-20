from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.modules.local_ai.classification.contracts import ClassificationFailureCode
from app.modules.local_ai.classification.parser import extract_response_text, response_indicates_thinking_budget_exhausted
from app.modules.local_ai.classification.prompts import MAX_CLASSIFICATION_PROMPT_CHARS


DEFAULT_CLASSIFICATION_MODEL = "gemma4:12b-it-qat"
DEFAULT_CLASSIFICATION_ENDPOINT = "http://localhost:11434/api/chat"
LOCAL_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ClassificationAdapterConfigurationError(ValueError):
    """Raised when a local classification adapter endpoint is unsafe."""


class ClassificationAdapterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint_url: str = DEFAULT_CLASSIFICATION_ENDPOINT
    model_name: str = DEFAULT_CLASSIFICATION_MODEL
    timeout_seconds: float = Field(default=30, ge=0.1, le=300)
    max_output_tokens: int = Field(default=256, ge=1, le=512)
    temperature: float = Field(default=0, ge=0, le=0)

    @field_validator("endpoint_url")
    @classmethod
    def endpoint_must_be_local(cls, value: str) -> str:
        return validate_classification_endpoint_url(value)


class ClassificationAdapterResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    model_name: str
    runtime_endpoint: str
    response_text: str | None = None
    failure_code: ClassificationFailureCode | None = None
    failure_message: str | None = None


class LocalGemmaClassificationAdapter:
    """Local-only adapter boundary for future Gemma classification calls."""

    def __init__(self, config: ClassificationAdapterConfig | None = None, *, client: httpx.Client | None = None) -> None:
        self.config = config or ClassificationAdapterConfig()
        self._client = client

    def complete(self, prompt: str) -> ClassificationAdapterResult:
        try:
            payload = self._payload(prompt)
        except (ClassificationAdapterConfigurationError, ValidationError, ValueError) as exc:
            return self._failure(ClassificationFailureCode.local_endpoint_invalid, str(exc))

        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=self.config.timeout_seconds)
        try:
            response = client.post(self.config.endpoint_url, json=payload, timeout=self.config.timeout_seconds)
            response.raise_for_status()
            response_json = response.json()
            if response_indicates_thinking_budget_exhausted(response_json):
                return self._failure(
                    ClassificationFailureCode.thinking_budget_exhausted,
                    "local model exhausted output budget before final content",
                )
            return ClassificationAdapterResult(
                success=True,
                model_name=self.config.model_name,
                runtime_endpoint=self.config.endpoint_url,
                response_text=extract_response_text(response_json),
            )
        except httpx.TimeoutException as exc:
            return self._failure(ClassificationFailureCode.timeout, f"local classification timed out: {type(exc).__name__}")
        except httpx.ConnectError as exc:
            return self._failure(
                ClassificationFailureCode.runtime_unavailable,
                f"local classification runtime unavailable: {type(exc).__name__}",
            )
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            return self._failure(
                ClassificationFailureCode.unexpected_local_http_error,
                f"unexpected local classification response: {type(exc).__name__}",
            )
        finally:
            if owns_client:
                client.close()

    def _payload(self, prompt: str) -> dict[str, object]:
        ClassificationAdapterConfig.model_validate(self.config.model_dump())
        if len(prompt) > MAX_CLASSIFICATION_PROMPT_CHARS:
            raise ValueError("classification prompt exceeds bounded prompt budget")
        parsed = urlparse(self.config.endpoint_url)
        if parsed.path == "/api/chat":
            return {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": self.config.temperature, "num_predict": self.config.max_output_tokens},
            }
        return {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "stream": False,
            "response_format": {"type": "json_object"},
        }

    def _failure(self, code: ClassificationFailureCode, message: str) -> ClassificationAdapterResult:
        return ClassificationAdapterResult(
            success=False,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            failure_code=code,
            failure_message=message,
        )


def validate_classification_endpoint_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http":
        raise ClassificationAdapterConfigurationError("classification endpoint must use http:// localhost only")
    if not parsed.hostname or parsed.hostname.lower() not in LOCAL_ENDPOINT_HOSTS:
        raise ClassificationAdapterConfigurationError("classification endpoint host must be localhost, 127.0.0.1, or ::1")
    if parsed.username or parsed.password:
        raise ClassificationAdapterConfigurationError("classification endpoint must not include credentials")
    if not parsed.path:
        raise ClassificationAdapterConfigurationError("classification endpoint must include an HTTP path")
    return url
