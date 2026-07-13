from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.modules.ai.execution_types import ProviderBinding

PROVIDER_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ROUTE_CLASS_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")
INLINE_SECRET_HINT_RE = re.compile(r"(?i)(sk-|bearer\s+|api[_-]?key|token)")
_PRICING_KEYS = frozenset(
    {
        "currency",
        "input_usd_per_1m_tokens",
        "output_usd_per_1m_tokens",
        "pricing_version",
        "pricing_effective_at",
    }
)


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
class ModelPricing:
    currency: str
    input_usd_per_1m_tokens: float
    output_usd_per_1m_tokens: float
    pricing_version: str
    pricing_effective_at: str


@dataclass(frozen=True)
class ModelConfig:
    provider_id: str
    model_id: str
    provider_model_name: str
    route_classes: tuple[str, ...]
    max_output_tokens: int
    pricing: ModelPricing | None


@dataclass(frozen=True)
class FallbackEntry:
    provider_id: str
    model_id: str


@dataclass(frozen=True)
class ProviderRegistry:
    providers: dict[str, ProviderConfig]
    models: dict[tuple[str, str], ModelConfig]
    bindings: dict[str, ProviderBinding]
    fallback_chains: dict[str, tuple[FallbackEntry, ...]]


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
            if len(set(route_tuple)) != len(route_tuple):
                raise ValueError(f"model {provider_id}/{model_id} has duplicate route_classes")
            for route in route_tuple:
                _validate_route_class(route)
                if route in bindings:
                    raise ValueError(f"duplicate route binding {route}")
            max_tokens = int(model_raw.get("max_output_tokens", 0))
            if max_tokens <= 0:
                raise ValueError(f"model {provider_id}/{model_id} max_output_tokens must be positive")
            pricing = _parse_model_pricing(
                model_raw.get("pricing"), provider=provider, model_id=str(model_id)
            )
            if provider.enabled and provider.requires_network and pricing is None:
                raise ValueError(
                    f"enabled network model {provider_id}/{model_id} requires concrete pricing"
                )
            model = ModelConfig(
                provider_id=provider_id,
                model_id=str(model_id),
                provider_model_name=_required_str(
                    model_raw, "provider_model_name", f"model {provider_id}/{model_id}"
                ),
                route_classes=route_tuple,
                max_output_tokens=max_tokens,
                pricing=pricing,
            )
            models[(provider_id, str(model_id))] = model
            if provider.enabled:
                for route in route_tuple:
                    bindings[route] = ProviderBinding(
                        route,
                        provider_id,
                        str(model_id),
                        provider.requires_network,
                        max_tokens,
                    )

    fallback_chains = _parse_fallback_chains(raw.get("fallback_chains", {}), bindings)
    return ProviderRegistry(
        providers=providers,
        models=models,
        bindings=bindings,
        fallback_chains=fallback_chains,
    )


def registry_bindings() -> dict[str, ProviderBinding]:
    return _bindings_with_env_overrides(load_default_provider_registry().bindings)


def resolve_model_pricing(
    registry: ProviderRegistry, provider_id: str, model_id: str
) -> ModelPricing:
    model = registry.models.get((provider_id, model_id))
    if model is None:
        raise ValueError(f"unknown concrete model {provider_id}/{model_id}")
    provider = registry.providers.get(provider_id)
    if provider is None or not provider.requires_network:
        raise ValueError(f"model {provider_id}/{model_id} is not a network binding")
    if model.pricing is None:
        raise ValueError(f"missing concrete pricing for {provider_id}/{model_id}")
    return model.pricing


def _bindings_with_env_overrides(
    bindings: dict[str, ProviderBinding],
) -> dict[str, ProviderBinding]:
    result = dict(bindings)
    overrides = {
        "local:fake": ("AI_ROUTE_FAKE_MODEL",),
        "local:fast": ("AI_ROUTE_LOCAL_FAST_MODEL",),
        "local:general": ("AI_ROUTE_LOCAL_GENERAL_MODEL", "AI_ROUTE_LOCAL_MODEL"),
        "local:gemma": ("AI_ROUTE_LOCAL_GENERAL_MODEL", "AI_ROUTE_LOCAL_MODEL"),
        "local:coder": ("AI_ROUTE_LOCAL_CODER_MODEL",),
        "local:coder_heavy": ("AI_ROUTE_LOCAL_CODER_HEAVY_MODEL",),
        "external:cheap": ("AI_ROUTE_CHEAP_MODEL",),
        "external:reasoning": ("AI_ROUTE_REASONING_MODEL",),
    }
    for route, names in overrides.items():
        binding = result.get(route)
        if binding is None:
            continue
        for name in names:
            value = os.getenv(name)
            if value:
                result[route] = ProviderBinding(
                    route,
                    binding.provider_id,
                    value,
                    binding.requires_network,
                    binding.max_output_tokens,
                )
                break
    return result


def _parse_model_pricing(
    raw: Any, *, provider: ProviderConfig, model_id: str
) -> ModelPricing | None:
    owner = f"model {provider.provider_id}/{model_id}"
    if raw is None:
        return None
    if not provider.requires_network:
        raise ValueError(f"{owner} cannot define paid pricing for a local binding")
    if not isinstance(raw, dict):
        raise ValueError(f"{owner} pricing must be a mapping")
    keys = frozenset(raw)
    missing = _PRICING_KEYS - keys
    extra = keys - _PRICING_KEYS
    if missing:
        raise ValueError(f"{owner} pricing missing keys: {', '.join(sorted(missing))}")
    if extra:
        raise ValueError(f"{owner} pricing has unsupported keys: {', '.join(sorted(extra))}")
    currency = _required_str(raw, "currency", f"{owner} pricing")
    if currency != "USD":
        raise ValueError(f"{owner} pricing currency must be USD")
    effective_at = _required_str(raw, "pricing_effective_at", f"{owner} pricing")
    _validate_aware_timestamp(effective_at, owner)
    return ModelPricing(
        currency=currency,
        input_usd_per_1m_tokens=_nonnegative_float(
            raw.get("input_usd_per_1m_tokens"),
            f"{owner} input_usd_per_1m_tokens",
        ),
        output_usd_per_1m_tokens=_nonnegative_float(
            raw.get("output_usd_per_1m_tokens"),
            f"{owner} output_usd_per_1m_tokens",
        ),
        pricing_version=_required_str(raw, "pricing_version", f"{owner} pricing"),
        pricing_effective_at=effective_at,
    )


def _parse_fallback_chains(
    raw: Any, bindings: dict[str, ProviderBinding]
) -> dict[str, tuple[FallbackEntry, ...]]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("fallback_chains must be a mapping")
    chains: dict[str, tuple[FallbackEntry, ...]] = {}
    enabled_models = {
        (binding.provider_id, binding.model_id) for binding in bindings.values()
    }
    for route, chain_raw in raw.items():
        route = str(route)
        _validate_route_class(route)
        primary = bindings.get(route)
        if primary is None:
            raise ValueError(f"fallback chain route {route} is not bound")
        if not isinstance(chain_raw, list) or not chain_raw:
            raise ValueError(f"fallback chain {route} must be a non-empty list")
        chain = tuple(_parse_fallback_entry(str(item), route) for item in chain_raw)
        first = chain[0]
        if (first.provider_id, first.model_id) != (
            primary.provider_id,
            primary.model_id,
        ):
            raise ValueError(f"fallback chain {route} first entry must match primary binding")
        for item in chain:
            if (item.provider_id, item.model_id) not in enabled_models:
                raise ValueError(
                    f"fallback chain {route} references unknown or disabled model "
                    f"{item.provider_id}/{item.model_id}"
                )
        chains[route] = chain
    return chains


def _parse_fallback_entry(value: str, route: str) -> FallbackEntry:
    parts = value.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"fallback chain {route} entry must be provider_id/model_id"
        )
    provider_id, model_id = parts
    _validate_provider_id(provider_id)
    return FallbackEntry(provider_id=provider_id, model_id=model_id)


def _required_str(raw: dict[str, Any], key: str, owner: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} requires {key}")
    return value.strip()


def _nonnegative_float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    parsed = float(value)
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def _validate_aware_timestamp(value: str, owner: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{owner} pricing_effective_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{owner} pricing_effective_at must include a timezone")


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
