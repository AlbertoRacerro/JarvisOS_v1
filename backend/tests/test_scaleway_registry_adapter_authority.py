import pytest

from app.modules.ai.contracts import AIRequest, AITaskType
from app.modules.ai.execution import _default_adapters
from app.modules.ai.provider_registry import (
    load_default_provider_registry,
    registry_bindings,
)
from app.modules.ai.providers.openai_compat_adapter import OpenAICompatAdapter
from app.modules.ai.providers.scaleway import ScalewayChatResult, ScalewayProvider
from app.modules.ai.providers.scaleway_adapter import ScalewayProviderAdapter

MODEL_ID = "gemma-4-26b-a4b-it"
LEGACY_SMOKE_MODEL = "llama-3.1-8b-instruct"


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


def test_direct_smoke_default_is_preserved_while_route_uses_binding_model(
    monkeypatch,
) -> None:
    monkeypatch.delenv("SCALEWAY_MODEL", raising=False)
    binding = registry_bindings()["external:scaleway"]
    captured: dict[str, object] = {}

    class CapturingProvider(ScalewayProvider):
        def create_work_completion(
            self,
            *,
            prompt: str,
            estimated_output_tokens: int,
            model: str | None = None,
        ) -> ScalewayChatResult:
            captured.update(
                prompt=prompt,
                estimated_output_tokens=estimated_output_tokens,
                model=model,
            )
            return ScalewayChatResult(
                provider_name="scaleway",
                model=model or self.model(),
                mode="work",
                external_call_attempted=True,
                external_call_succeeded=True,
                response_text="OK",
                reported_input_tokens=None,
                reported_output_tokens=None,
                reported_total_tokens=None,
                sanitized_metadata={},
            )

    provider = CapturingProvider()
    adapter = ScalewayProviderAdapter(provider)
    response = adapter.complete(
        AIRequest(
            task_type=AITaskType.decision_support,
            prompt="Reply OK.",
            model_preference=binding.model_id,
            max_output_tokens=8,
        )
    )

    assert provider.model() == LEGACY_SMOKE_MODEL
    assert binding.model_id == MODEL_ID
    assert captured["model"] == MODEL_ID
    assert response.model_id == MODEL_ID
    assert response.text == "OK"


def test_scaleway_model_override_must_resolve_to_registered_route_model(
    monkeypatch,
) -> None:
    monkeypatch.setenv("SCALEWAY_MODEL", "unregistered-scaleway-model")

    with pytest.raises(
        ValueError,
        match="model override for external:scaleway must resolve uniquely",
    ):
        registry_bindings()
