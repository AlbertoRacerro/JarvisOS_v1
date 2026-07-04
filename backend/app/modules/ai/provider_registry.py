from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.modules.ai.execution_types import ProviderBinding

PROVIDER_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ROUTE_CLASS_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
INLINE_SECRET_HINT_RE = re.compile(r"(?i)(sk-|bearer\s+|api[_-]?key|token)")


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    kind: str
    enabled: bool
    requires_network: bool
    base_url: str | None
    api_key_ref: str | None
    timeout_seconds: float
    monthly_token_cap: int
    monthly_cost_cap_usd: float


@dataclass(frozen=True)
class ModelConfig:
    provider_id: str
    model_id: str
    provider_model_name: str
    route_classes: tuple[str, ...]
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderRegistry:
    providers: dict[str, ProviderConfig]
    models: dict[tuple[str, str], ModelConfig]
    bindings: dict[str, ProviderBinding]
    fallback_chains: dict[str, tuple[str, ...]]


def default_registry_path() -> Path:
    return Path(__file__).resolve().parents[4] / "configs" / "ai_providers.yaml"


def load_provider_registry(path: str | Path | None = None) -> ProviderRegistry:
    config_path = Path(path) if path is not None else default_registry_path()
    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return parse_provider_registry(raw)


@lru_cache(maxsize=1)
def load_default_provider_registry() -> ProviderRegistry:
    return load_provider_registry(default_registry_path())


def parse_provider_registry(raw: dict[str, Any]) -> ProviderRegistry:
    if raw.get("version") != 1:
        raise ValueError("provider registry version must be 1")
    raw_providers = raw.get("providers")
    if not isinstance(raw_providers, dict) or not raw_providers:
        raise ValueError("provider registry requires providers")

    providers: dict[str, ProviderConfig] = {}
    models: dict[tuple[str, str], ModelConfig] = {}
    bindings: dict[str, ProviderBinding] = {}

    for provider_id, provider_raw in raw_providers.items():
        _validate_provider_id(provider_id)
        if not isinstance(provider_raw, dict):
            raise ValueError(f"provider {provider_id} must be a mapping")
        api_key_ref = provider_raw.get("api_key_ref")
        if api_key_ref is not None:
            _validate_api_key_ref(str(api_key_ref))
        provider = ProviderConfig(
            provider_id=provider_id,
            kind=_required_str(provider_raw, "kind", f"provider {provider_id}"),
            enabled=bool(provider_raw.get("enabled", False)),
            requires_network=bool(provider_raw.get("requires_network", False)),
            base_url=_optional_url(provider_raw.get("base_url"), provider_id),
            api_key_ref=str(api_key_ref) if api_key_ref is not None else None,
            timeout_seconds=float(provider_raw.get("timeout_seconds", 20)),
            monthly_token_cap=int(provider_raw.get("monthly_token_cap", 0)),
            monthly_cost_cap_usd=float(provider_raw.get("monthly_cost_cap_usd", 0)),
        )
        providers[provider_id] = provider
        raw_models = provider_raw.get("models")
        if not isinstance(raw_models, dict) or not raw_models:
            raise ValueError(f"provider {provider_id} requires models")
        for model_id, model_raw in raw_models.items():
            if not isinstance(model_raw, dict):
                raise ValueError(f"model {provider_id}/{model_id} must be a mapping")
            routes = model_raw.get("route_classes")
            if not isinstance(routes, list) or not routes:
                raise ValueError(f"model {provider_id}/{model_id} requires route_classes")
            route_tuple = tuple(str(route) for route in routes)
            for route in route_tuple:
                _validate_route_class(route)
                if route in bindings:
                    raise ValueError(f"duplicate route binding {route}")
            max_tokens = int(model_raw.get("max_output_tokens", 0))
            if max_tokens <= 0:
                raise ValueError(f"model {provider_id}/{model_id} max_output_tokens must be positive")
            model = ModelConfig(
                provider_id=provider_id,
                model_id=str(model_id),
                provider_model_name=_required_str(model_raw, "provider_model_name", f"model {provider_id}/{model_id}"),
                route_classes=route_tuple,
                max_output_tokens=max_tokens,
            )
            models[(provider_id, str(model_id))] = model
            for route in route_tuple:
                bindings[route] = ProviderBinding(route, provider_id, str(model_id), provider.requires_network, max_tokens)

    fallback_chains = _parse_fallback_chains(raw.get("fallback_chains", {}), bindings)
    return ProviderRegistry(providers=providers, models=models, bindings=bindings, fallback_chains=fallback_chains)


def registry_bindings() -> dict[str, ProviderBinding]:
    return _bindings_with_env_overrides(load_default_provider_registry().bindings)


def _bindings_with_env_overrides(bindings: dict[str, ProviderBinding]) -> dict[str, ProviderBinding]:
    result = dict(bindings)
    overrides = {
        "local:fake": ("AI_ROUTE_FAKE_MODEL",),
        "local:fast": ("AI_ROUTE_LOCAL_FAST_MODEL",),
        "local:general": ("AI_ROUTE_LOCAL_GENERAL_MODEL", "AI_ROUTE_LOCAL_MODEL"),
        "local:gemma": ("AI_ROUTE_LOCAL_GENERAL_MODEL", "AI_ROUTE_LOCAL_MODEL"),
        "local:coder": ("AI_ROUTE_LOCAL_CODER_MODEL",),
        "local:coder_heavy": ("AI_ROUTE_LOCAL_CODER_HEAVY_MODEL",),
        "external:cheap": ("AI_ROUTE_CHEAP_MODEL", "SCALEWAY_MODEL"),
        "external:reasoning": ("AI_ROUTE_REASONING_MODEL",),
    }
    for route, names in overrides.items():
        binding = result.get(route)
        if binding is None:
            continue
        for name in names:
            value = os.getenv(name)
            if value:
                result[route] = ProviderBinding(route, binding.provider_id, value, binding.requires_network, binding.max_output_tokens)
                break
    return result


def _parse_fallback_chains(raw: Any, bindings: dict[str, ProviderBinding]) -> dict[str, tuple[str, ...]]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("fallback_chains must be a mapping")
    chains: dict[str, tuple[str, ...]] = {}
    for route, chain_raw in raw.items():
        route = str(route)
        _validate_route_class(route)
        if route not in bindings:
            raise ValueError(f"fallback chain route {route} is not bound")
        if not isinstance(chain_raw, list) or not chain_raw:
            raise ValueError(f"fallback chain {route} must be a non-empty list")
        chain = tuple(str(item) for item in chain_raw)
        for item in chain:
            _validate_route_class(item)
            if item not in bindings:
                raise ValueError(f"fallback chain {route} references unknown route {item}")
        chains[route] = chain
    return chains


def _required_str(raw: dict[str, Any], key: str, owner: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} requires {key}")
    return value.strip()


def _optional_url(value: Any, provider_id: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().rstrip("/")
    if INLINE_SECRET_HINT_RE.search(text):
        raise ValueError(f"provider {provider_id} base_url looks like a secret")
    if not text.startswith(("http://", "https://")):
        raise ValueError(f"provider {provider_id} base_url must be http(s)")
    return text


def _validate_provider_id(provider_id: str) -> None:
    if not PROVIDER_ID_RE.match(str(provider_id)):
        raise ValueError(f"malformed provider id {provider_id}")


def _validate_route_class(route_class: str) -> None:
    if not ROUTE_CLASS_RE.match(route_class):
        raise ValueError(f"malformed route class {route_class}")


def _validate_api_key_ref(api_key_ref: str) -> None:
    if not api_key_ref.startswith("env:"):
        raise ValueError("api_key_ref must be an env: reference")
    env_name = api_key_ref.removeprefix("env:")
    if not re.match(r"^[A-Z][A-Z0-9_]*$", env_name):
        raise ValueError("api_key_ref has malformed env var name")
    if INLINE_SECRET_HINT_RE.search(env_name.removesuffix("_API_KEY")):
        raise ValueError("api_key_ref looks like an inline secret")
