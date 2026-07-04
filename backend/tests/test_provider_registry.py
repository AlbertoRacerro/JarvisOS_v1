import copy

import pytest

from app.modules.ai.provider_registry import load_provider_registry, parse_provider_registry


def test_default_provider_registry_loads_with_current_scaleway_bindings(monkeypatch):
    monkeypatch.delenv("AI_ROUTE_CHEAP_MODEL", raising=False)
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)
    monkeypatch.delenv("SCALEWAY_MODEL", raising=False)
    registry = load_provider_registry()

    assert registry.bindings["local:fake"].provider_id == "fake"
    assert registry.bindings["local:fake"].model_id == "fake-deterministic-v1"
    assert registry.bindings["local:fake"].max_output_tokens == 256
    assert registry.bindings["external:cheap"].provider_id == "scaleway"
    assert registry.bindings["external:cheap"].model_id == "llama-3.1-8b-instruct"
    assert registry.bindings["external:cheap"].max_output_tokens == 512
    assert registry.bindings["external:reasoning"].model_id == "qwen3-235b-a22b-instruct-2507"
    assert registry.bindings["external:reasoning"].max_output_tokens == 1024
    assert registry.providers["scaleway"].api_key_ref == "env:SCALEWAY_API_KEY"


def test_registry_rejects_missing_required_fields():
    with pytest.raises(ValueError, match="requires providers"):
        parse_provider_registry({"version": 1})


def test_registry_rejects_malformed_route_class():
    raw = _minimal_registry()
    raw["providers"]["fake"]["models"]["m"]["route_classes"] = ["bad route"]
    with pytest.raises(ValueError, match="malformed route class"):
        parse_provider_registry(raw)


def test_registry_rejects_unknown_fallback_target():
    raw = _minimal_registry()
    raw["fallback_chains"] = {"local:fake": ["local:missing"]}
    with pytest.raises(ValueError, match="unknown route"):
        parse_provider_registry(raw)


def test_registry_rejects_inline_looking_secret_values():
    raw = _minimal_registry()
    raw["providers"]["fake"]["api_key_ref"] = "sk-inline-secret"
    with pytest.raises(ValueError, match="api_key_ref must be an env"):
        parse_provider_registry(raw)


def _minimal_registry():
    return copy.deepcopy(
        {
            "version": 1,
            "providers": {
                "fake": {
                    "kind": "fake",
                    "enabled": True,
                    "requires_network": False,
                    "models": {
                        "m": {
                            "provider_model_name": "m",
                            "route_classes": ["local:fake"],
                            "max_output_tokens": 1,
                        }
                    },
                }
            },
            "fallback_chains": {"local:fake": ["local:fake"]},
        }
    )
