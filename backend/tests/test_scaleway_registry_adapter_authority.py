import pytest

from app.modules.ai.execution import _default_adapters
from app.modules.ai.provider_registry import (
    load_default_provider_registry,
    registry_bindings,
)
from app.modules.ai.providers.openai_compat_adapter import OpenAICompatAdapter
from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

MODEL_ID = "gemma-4-26b-a4b-it"


def test_scaleway_registry_kind_preserves_provider_specific_adapter(monkeypatch) -> None:
    monkeypatch.setenv("SCALEWAY_BASE_URL", "https://scaleway.example.test/v1")
    monkeypatch.setenv("SCALEWAY_MODEL", MODEL_ID)

    registry = load_default_provider_registry()
    adapters = _default_adapters()

    assert registry.providers["scaleway"].kind == "scaleway"
    assert isinstance(adapters["scaleway"], ScalewayProviderAdapter)
    assert not isinstance(adapters["scaleway"], OpenAICompatAdapter)
    assert adapters["scaleway"].provider.base_url() == "https://scaleway.example.test/v1"
    assert adapters["scaleway"].provider.model() == MODEL_ID
    assert isinstance(adapters["deepseek"], OpenAICompatAdapter)


def test_scaleway_default_model_matches_registered_binding(monkeypatch) -> None:
    monkeypatch.delenv("SCALEWAY_MODEL", raising=False)

    binding = registry_bindings()["external:scaleway"]
    adapter = _default_adapters()["scaleway"]

    assert binding.model_id == MODEL_ID
    assert adapter.provider.model() == binding.model_id


def test_scaleway_model_override_must_resolve_to_registered_route_model(
    monkeypatch,
) -> None:
    monkeypatch.setenv("SCALEWAY_MODEL", "unregistered-scaleway-model")

    with pytest.raises(
        ValueError,
        match="model override for external:scaleway must resolve uniquely",
    ):
        registry_bindings()
