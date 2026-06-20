import os
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.local_ai.errors import LocalGemmaConfigurationError

DEFAULT_LOCAL_GEMMA_ENDPOINT = "http://localhost:11434/v1/chat/completions"
DEFAULT_LOCAL_GEMMA_MODEL = "gemma3:12b"
LOCAL_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "::1"}


class LocalGemmaConfig(BaseModel):
    """Configuration for a dry-run local Gemma-compatible HTTP endpoint."""

    model_config = ConfigDict(extra="forbid")

    endpoint_url: str = DEFAULT_LOCAL_GEMMA_ENDPOINT
    model_name: str = DEFAULT_LOCAL_GEMMA_MODEL
    timeout_seconds: float = Field(default=30, ge=0.1, le=300)
    max_output_tokens: int = Field(default=1200, ge=1, le=8192)
    temperature: float = Field(default=0, ge=0, le=1)

    @field_validator("endpoint_url")
    @classmethod
    def endpoint_must_be_local(cls, value: str) -> str:
        return validate_local_endpoint_url(value)

    @classmethod
    def from_env(cls) -> "LocalGemmaConfig":
        return cls(
            endpoint_url=os.environ.get("JARVISOS_LOCAL_GEMMA_ENDPOINT", DEFAULT_LOCAL_GEMMA_ENDPOINT),
            model_name=os.environ.get("JARVISOS_LOCAL_GEMMA_MODEL", DEFAULT_LOCAL_GEMMA_MODEL),
            timeout_seconds=float(os.environ.get("JARVISOS_LOCAL_GEMMA_TIMEOUT_SECONDS", "30")),
            max_output_tokens=int(os.environ.get("JARVISOS_LOCAL_GEMMA_MAX_OUTPUT_TOKENS", "1200")),
            temperature=float(os.environ.get("JARVISOS_LOCAL_GEMMA_TEMPERATURE", "0")),
        )


def validate_local_endpoint_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http":
        raise LocalGemmaConfigurationError("Local Gemma endpoint must use http:// localhost only.")
    if not parsed.hostname or parsed.hostname.lower() not in LOCAL_ENDPOINT_HOSTS:
        raise LocalGemmaConfigurationError("Local Gemma endpoint host must be localhost, 127.0.0.1, or ::1.")
    if parsed.username or parsed.password:
        raise LocalGemmaConfigurationError("Local Gemma endpoint must not contain credentials.")
    if not parsed.path:
        raise LocalGemmaConfigurationError("Local Gemma endpoint must include an HTTP path.")
    return url
