import copy

import pytest

from app.modules.ai.provider_registry import load_provider_registry, parse_provider_registry


def test_default_provider_registry_loads_with_deepseek_glm_bindings(monkeypatch):
    monkeypatch.delenv("AI_ROUTE_CHEAP_MODEL", raising=False)
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)
    registry = load_provider_registry()

    assert registry.bindings["local:fake"].provider_id == "fake"
    assert registry.bindings["local:fake"].model_id == "fake-deterministic-v1"
    assert registry.bindings["local:fake"].max_output_tokens == 256
    assert "scaleway" not in registry.providers
    assert registry.bindings["external:cheap"].provider_id == "deepseek"
    assert registry.bindings["external:cheap"].model_id == "deepseek-v4-pro"
    assert registry.bindings["external:cheap"].max_output_tokens == 512
    assert registry.bindings["external:reasoning"].provider_id == "glm"
    assert registry.bindings["external:reasoning"].model_id == "glm-5.2"
    assert registry.bindings["external:reasoning"].max_output_tokens == 1024
    assert registry.providers["deepseek"].api_key_ref == "env:DEEPSEEK_API_KEY"
    assert registry.providers["glm"].api_key_ref == "env:GLM_API_KEY"
    assert "external:kimi" not in registry.bindings


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
    raw["fallback_chains"] = {"local:fake": ["fake/m", "fake/missing"]}
    with pytest.raises(ValueError, match="unknown or disabled model"):
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
            "fallback_chains": {"local:fake": ["fake/m"]},
        }
    )


def test_registry_rejects_duplicate_routes_within_one_model():
    raw = _minimal_registry()
    raw["providers"]["fake"]["models"]["m"]["route_classes"] = ["local:fake", "local:fake"]
    with pytest.raises(ValueError, match="duplicate route_classes"):
        parse_provider_registry(raw)


def test_registry_rejects_fallback_first_entry_mismatch():
    raw = _minimal_registry()
    raw["providers"]["other"] = {
        "kind": "fake",
        "enabled": True,
        "requires_network": False,
        "models": {
            "other-model": {
                "provider_model_name": "other-model",
                "route_classes": ["local:other"],
                "max_output_tokens": 1,
            }
        },
    }
    raw["fallback_chains"] = {"local:fake": ["other/other-model", "fake/m"]}
    with pytest.raises(ValueError, match="first entry must match primary binding"):
        parse_provider_registry(raw)


def test_disabled_provider_yields_no_bindings_but_loads():
    raw = _minimal_registry()
    raw["providers"]["disabled"] = {
        "kind": "openai_compatible",
        "enabled": False,
        "requires_network": True,
        "base_url": "https://example.test",
        "api_key_ref": "env:KIMI_API_KEY",
        "models": {
            "disabled-model": {
                "provider_model_name": "disabled-model",
                "route_classes": ["external:disabled"],
                "max_output_tokens": 10,
            }
        },
    }
    registry = parse_provider_registry(raw)
    assert "disabled" in registry.providers
    assert "external:disabled" not in registry.bindings
