from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.modules.ai.execution import _default_bindings
from app.modules.ai.providers.local_ollama_adapter import LOCAL_OLLAMA_PROVIDER_ID
from app.modules.local_ai.runtime.ollama import resolve_ollama_runtime_urls

LOCAL_RUNTIME_STATUS_TIMEOUT_S = 1.5
_ALLOWED_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def get_local_ai_runtime_status(*, client: Any | None = None) -> dict[str, Any]:
    urls = resolve_ollama_runtime_urls()
    configured_route_models = _configured_local_route_models()
    status = {
        "ollama_reachable": False,
        "ollama_version": None,
        "installed_models": [],
        "loaded_models": [],
        "configured_route_models": configured_route_models,
        "missing_models": dict(configured_route_models),
        "endpoint": urls.base_url,
        "error_type": None,
        "error_message": None,
        "tags_error_type": None,
        "ps_error_type": None,
    }

    invalid_reason = _validate_local_base_url(urls.base_url)
    if invalid_reason is not None:
        status["error_type"] = "invalid_endpoint"
        status["error_message"] = invalid_reason
        return status

    client_obj = client or httpx.Client()
    should_close = client is None
    try:
        try:
            version_response = client_obj.get(
                _api_url(urls.base_url, "/api/version"),
                timeout=LOCAL_RUNTIME_STATUS_TIMEOUT_S,
            )
            version_response.raise_for_status()
            version_payload = version_response.json()
            status["ollama_reachable"] = True
            status["ollama_version"] = (
                version_payload.get("version") if isinstance(version_payload.get("version"), str) else None
            )
        except Exception as exc:
            status["error_type"] = type(exc).__name__
            status["error_message"] = str(exc)
            return status

        try:
            tags_response = client_obj.get(_api_url(urls.base_url, "/api/tags"), timeout=LOCAL_RUNTIME_STATUS_TIMEOUT_S)
            tags_response.raise_for_status()
            status["installed_models"] = _parse_installed_models(tags_response.json())
            installed = set(status["installed_models"])
            status["missing_models"] = {
                route_class: model_id
                for route_class, model_id in configured_route_models.items()
                if model_id not in installed
            }
        except Exception as exc:
            status["tags_error_type"] = type(exc).__name__

        try:
            ps_response = client_obj.get(_api_url(urls.base_url, "/api/ps"), timeout=LOCAL_RUNTIME_STATUS_TIMEOUT_S)
            ps_response.raise_for_status()
            status["loaded_models"] = _parse_loaded_models(ps_response.json())
        except Exception as exc:
            status["ps_error_type"] = type(exc).__name__

        return status
    finally:
        if should_close:
            client_obj.close()


def _configured_local_route_models() -> dict[str, str]:
    configured: dict[str, str] = {}
    for route_class, binding in _default_bindings().items():
        if binding.provider_id == LOCAL_OLLAMA_PROVIDER_ID:
            configured[route_class] = binding.model_id
    return configured


def _validate_local_base_url(base_url: str) -> str | None:
    parsed = urlparse(base_url)
    if parsed.scheme != "http":
        return "endpoint must use http"
    if parsed.username or parsed.password:
        return "endpoint must not include credentials"
    if parsed.hostname not in _ALLOWED_LOCAL_HOSTS:
        return "endpoint host must be localhost-only"
    if parsed.query or parsed.fragment:
        return "endpoint must not include query or fragment"
    return None


def _api_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _parse_installed_models(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        raise ValueError("tags payload must be an object")
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("tags payload missing models list")
    installed: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        value = item.get("name")
        if not isinstance(value, str):
            value = item.get("model")
        if isinstance(value, str) and value not in installed:
            installed.append(value)
    return installed


def _parse_loaded_models(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("ps payload must be an object")
    models = payload.get("models")
    if not isinstance(models, list):
        raise ValueError("ps payload missing models list")
    loaded: list[dict[str, Any]] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        model = item.get("model")
        if not isinstance(name, str):
            name = model if isinstance(model, str) else None
        if not isinstance(name, str):
            continue
        size = _optional_int(item.get("size"))
        size_vram = _optional_int(item.get("size_vram"))
        spilled = None
        if size is not None and size_vram is not None:
            spilled = size_vram < size
        loaded.append(
            {
                "name": name,
                "model": model if isinstance(model, str) else None,
                "size": size,
                "size_vram": size_vram,
                "processor": item.get("processor") if isinstance(item.get("processor"), str) else None,
                "until": item.get("until") if isinstance(item.get("until"), str) else None,
                "spilled": spilled,
            }
        )
    return loaded


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None
