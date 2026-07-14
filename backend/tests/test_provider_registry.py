import copy

import pytest

from app.modules.ai.provider_registry import (
    load_provider_registry,
    parse_provider_registry,
    registry_bindings,
    resolve_model_pricing,
)


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

    deepseek_price = resolve_model_pricing(registry, "deepseek", "deepseek-v4-pro")
    assert deepseek_price.currency == "USD"
    assert deepseek_price.input_usd_per_1m_tokens == 5.0
    assert deepseek_price.output_usd_per_1m_tokens == 20.0
    assert deepseek_price.pricing_version == "operator-conservative-v1"


def test_exact_external_model_override_uses_canonical_registry_metadata(monkeypatch):
    monkeypatch.setenv("AI_ROUTE_CHEAP_MODEL", "deepseek-v4-pro")
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)

    binding = registry_bindings()["external:cheap"]

    assert binding.provider_id == "deepseek"
    assert binding.model_id == "deepseek-v4-pro"
    assert binding.max_output_tokens == 512
    assert binding.requires_network is True


def test_external_model_override_rejects_provider_model_mismatch(monkeypatch):
    monkeypatch.setenv("AI_ROUTE_CHEAP_MODEL", "glm-5.2")
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)

    with pytest.raises(ValueError, match="must resolve uniquely to a priced model"):
        registry_bindings()


def test_external_model_override_rejects_unknown_model(monkeypatch):
    monkeypatch.setenv("AI_ROUTE_REASONING_MODEL", "unregistered-model")
    monkeypatch.delenv("AI_ROUTE_CHEAP_MODEL", raising=False)

    with pytest.raises(ValueError, match="must resolve uniquely to a priced model"):
        registry_bindings()


def test_local_model_override_retains_existing_behavior(monkeypatch):
    monkeypatch.setenv("AI_ROUTE_FAKE_MODEL", "local-test-override")
    monkeypatch.delenv("AI_ROUTE_CHEAP_MODEL", raising=False)
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)

    binding = registry_bindings()["local:fake"]

    assert binding.provider_id == "fake"
    assert binding.model_id == "local-test-override"
    assert binding.max_output_tokens == 256
    assert binding.requires_network is False


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


def test_registry_rejects_duplicate_routes_within_one_model():
    raw = _minimal_registry()
    raw["providers"]["fake"]["models"]["m"]["route_classes"] = [
        "local:fake",
        "local:fake",
    ]
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


def test_disabled_provider_yields_no_bindings_but_loads_without_pricing():
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
    with pytest.raises(ValueError, match="missing concrete pricing"):
        resolve_model_pricing(registry, "disabled", "disabled-model")


def test_enabled_network_model_requires_concrete_pricing():
    raw = _minimal_network_registry()
    del raw["providers"]["network"]["models"]["model"]["pricing"]
    with pytest.raises(ValueError, match="requires concrete pricing"):
        parse_provider_registry(raw)


def test_network_pricing_is_strict_and_timezone_aware():
    raw = _minimal_network_registry()
    pricing = raw["providers"]["network"]["models"]["model"]["pricing"]
    pricing["currency"] = "EUR"
    with pytest.raises(ValueError, match="currency must be USD"):
        parse_provider_registry(raw)

    raw = _minimal_network_registry()
    pricing = raw["providers"]["network"]["models"]["model"]["pricing"]
    pricing["pricing_effective_at"] = "2026-07-13T00:00:00"
    with pytest.raises(ValueError, match="must include a timezone"):
        parse_provider_registry(raw)

    raw = _minimal_network_registry()
    pricing = raw["providers"]["network"]["models"]["model"]["pricing"]
    pricing["unexpected"] = 1
    with pytest.raises(ValueError, match="unsupported keys"):
        parse_provider_registry(raw)


def test_resolve_model_pricing_fails_for_unknown_or_local_models():
    registry = parse_provider_registry(_minimal_registry())
    with pytest.raises(ValueError, match="unknown concrete model"):
        resolve_model_pricing(registry, "fake", "missing")
    with pytest.raises(ValueError, match="not a network binding"):
        resolve_model_pricing(registry, "fake", "m")


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


def _minimal_network_registry():
    return {
        "version": 1,
        "providers": {
            "network": {
                "kind": "openai_compatible",
                "enabled": True,
                "requires_network": True,
                "base_url": "https://example.test",
                "api_key_ref": "env:NETWORK_API_KEY",
                "models": {
                    "model": {
                        "provider_model_name": "model",
                        "route_classes": ["external:test"],
                        "max_output_tokens": 10,
                        "pricing": {
                            "currency": "USD",
                            "input_usd_per_1m_tokens": 1.0,
                            "output_usd_per_1m_tokens": 2.0,
                            "pricing_version": "test-v1",
                            "pricing_effective_at": "2026-07-13T00:00:00Z",
                        },
                    }
                },
            }
        },
        "fallback_chains": {"external:test": ["network/model"]},
    }
