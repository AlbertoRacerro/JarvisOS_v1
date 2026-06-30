from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

LOCAL_OLLAMA_ENDPOINT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
_GENERATE_PATH = "/api/generate"


@dataclass(frozen=True)
class OllamaRuntimeURLs:
    base_url: str
    generate_endpoint: str


def resolve_ollama_runtime_urls() -> OllamaRuntimeURLs:
    generate_endpoint = _normalize_generate_endpoint(
        os.getenv(LOCAL_OLLAMA_ENDPOINT_ENV, f"{DEFAULT_OLLAMA_BASE_URL}{_GENERATE_PATH}")
    )
    return OllamaRuntimeURLs(
        base_url=_derive_base_url(generate_endpoint),
        generate_endpoint=generate_endpoint,
    )


def _normalize_generate_endpoint(raw_endpoint: str) -> str:
    parsed = urlparse(raw_endpoint)
    path = parsed.path or ""
    if path in ("", "/"):
        return urlunparse((parsed.scheme, parsed.netloc, _GENERATE_PATH, "", "", ""))
    return raw_endpoint


def _derive_base_url(generate_endpoint: str) -> str:
    parsed = urlparse(generate_endpoint)
    path = parsed.path or ""
    if path.endswith(_GENERATE_PATH):
        path = path[: -len(_GENERATE_PATH)]
    else:
        path = path.rstrip("/")
    if path == "/":
        path = ""
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
