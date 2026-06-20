import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.modules.local_ai.adapter import LocalGemmaAdapter
from app.modules.local_ai.config import LocalGemmaConfig
from app.modules.local_ai.errors import LocalGemmaConfigurationError, LocalGemmaFailureCode
from app.modules.local_ai.prompt_builder import build_gemma_eval_prompt
from app.modules.local_ai_eval.loader import load_golden_cases
from app.modules.local_ai_eval.run_gemma_eval import run_gemma_eval


def _case(case_id: str):
    return next(case for case in load_golden_cases() if case.id == case_id)


def _mock_client_for_content(content: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_local_endpoint_validation_accepts_localhost() -> None:
    config = LocalGemmaConfig(endpoint_url="http://localhost:11434/v1/chat/completions")

    assert config.endpoint_url == "http://localhost:11434/v1/chat/completions"


def test_local_endpoint_validation_accepts_127_0_0_1() -> None:
    config = LocalGemmaConfig(endpoint_url="http://127.0.0.1:1234/v1/chat/completions")

    assert config.endpoint_url == "http://127.0.0.1:1234/v1/chat/completions"


@pytest.mark.parametrize(
    "url",
    [
        "http://api.example.com/v1/chat/completions",
        "https://localhost:11434/v1/chat/completions",
        "https://api.openai.com/v1/chat/completions",
        "http://192.168.1.10:11434/v1/chat/completions",
        "http://user:pass@localhost:11434/v1/chat/completions",
    ],
)
def test_local_endpoint_validation_rejects_non_local_or_unsafe_urls(url: str) -> None:
    with pytest.raises((LocalGemmaConfigurationError, ValidationError)):
        LocalGemmaConfig(endpoint_url=url)


def test_no_api_key_is_required(monkeypatch) -> None:
    monkeypatch.delenv("SCALEWAY_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = LocalGemmaConfig()

    assert config.endpoint_url.startswith("http://localhost:")
    assert config.model_name


def test_prompt_builder_includes_protocol_case_context_and_schema() -> None:
    case = _case("context_request_planning_001")
    prompt = build_gemma_eval_prompt(case)

    assert "candidate local operating brain" in prompt
    assert case.input in prompt
    assert "provided_context" in prompt
    assert "output_schema" in prompt
    assert "controlled_context_package_vocabulary" in prompt
    assert "JSON" in prompt or "json" in prompt


def test_prompt_builder_does_not_include_golden_expected_answer() -> None:
    case = _case("context_request_planning_001")
    prompt = build_gemma_eval_prompt(case)

    assert '"expected"' not in prompt
    assert "expected_requested_context_packages" not in prompt
    assert "must_include" not in prompt
    assert "must_not_include" not in prompt


def test_adapter_handles_runtime_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("not running", request=request)

    adapter = LocalGemmaAdapter(LocalGemmaConfig(), client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.runtime_unavailable


def test_adapter_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    adapter = LocalGemmaAdapter(LocalGemmaConfig(), client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.timeout


def test_adapter_handles_prose_output() -> None:
    adapter = LocalGemmaAdapter(LocalGemmaConfig(), client=_mock_client_for_content("I need more context first."))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.prose_instead_of_schema


def test_adapter_handles_invalid_json_output() -> None:
    adapter = LocalGemmaAdapter(LocalGemmaConfig(), client=_mock_client_for_content('{"task_type":'))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.invalid_json


def test_adapter_handles_schema_invalid_json() -> None:
    adapter = LocalGemmaAdapter(LocalGemmaConfig(), client=_mock_client_for_content(json.dumps({"task_type": "continue_conversation"})))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.schema_invalid


def test_adapter_revalidates_constructed_config_before_http_call() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]}, request=request)

    config = LocalGemmaConfig.model_construct(
        endpoint_url="http://api.example.com/v1/chat/completions",
        model_name="gemma3:12b",
        timeout_seconds=30,
        max_output_tokens=1200,
        temperature=0,
    )
    adapter = LocalGemmaAdapter(config, client=httpx.Client(transport=httpx.MockTransport(handler)))

    result = adapter.complete("prompt")

    assert result.success is False
    assert result.failure_code == LocalGemmaFailureCode.local_endpoint_invalid
    assert called is False


def test_runner_evaluates_fake_correct_sample_output() -> None:
    report = run_gemma_eval(config=LocalGemmaConfig(), limit=3, fake_mode="correct")

    assert report.case_count == 3
    assert report.schema_valid_count == 3
    assert report.passed_count == 3
    assert report.critical_failure_count == 0
    assert report.average_score == 1


def test_runner_evaluates_fake_incorrect_sample_output() -> None:
    report = run_gemma_eval(
        config=LocalGemmaConfig(),
        case_ids=["sensitivity_classification_001"],
        fake_mode="incorrect",
    )

    assert report.case_count == 1
    assert report.schema_valid_count == 1
    assert report.passed_count == 0
    assert report.critical_failure_count == 1
    assert report.failure_counts_by_category == {"sensitivity_classification": 1}
    assert report.failure_counts_by_failure_code


def test_runner_summary_includes_required_counts() -> None:
    report = run_gemma_eval(config=LocalGemmaConfig(), limit=2, fake_mode="correct")
    payload = report.model_dump(mode="json")

    for key in {
        "model_name",
        "runtime_endpoint",
        "case_count",
        "schema_valid_count",
        "passed_count",
        "critical_failure_count",
        "average_score",
        "failure_counts_by_category",
        "failure_counts_by_failure_code",
        "runtime_unavailable_count",
        "timeout_count",
        "invalid_json_count",
        "schema_invalid_count",
    }:
        assert key in payload


def test_local_ai_module_uses_no_external_provider_or_model_server_imports() -> None:
    module_dir = Path(__file__).resolve().parents[1] / "app" / "modules" / "local_ai"
    forbidden_imports = (
        "import openai",
        "from openai",
        "ollama",
        "llama_cpp",
        "litellm",
        "lmstudio",
        "lm_studio",
        "scaleway",
        "deepseek",
        "anthropic",
        "google.generativeai",
    )

    for file in module_dir.glob("*.py"):
        text = file.read_text(encoding="utf-8").lower()
        assert all(forbidden not in text for forbidden in forbidden_imports)
