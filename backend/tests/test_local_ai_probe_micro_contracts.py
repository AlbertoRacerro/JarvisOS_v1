import json
from pathlib import Path

import httpx
import pytest

from app.modules.local_ai.contracts import MICRO_CONTRACT_SCHEMA_VERSION, TaskClassificationOutput, TaskType
from app.modules.local_ai_eval import probe_micro_contracts
from app.modules.local_ai_eval.probe_micro_contracts import (
    TASK_CLASSIFICATION_FLAT_SCHEMA,
    ProbeCase,
    ProbeConfigurationError,
    aggregate_report,
    assert_flat_schema,
    build_native_payload,
    build_primary_probe_cases,
    run_probe_case,
    run_probe_suite,
    validate_native_endpoint,
)

_REAL_HTTPX_CLIENT = httpx.Client


def _task_case() -> ProbeCase:
    return ProbeCase(
        contract_name="TaskClassificationOutput",
        case_id="task_case",
        prompt="Return one task classification JSON object.",
        contract_model=TaskClassificationOutput,
        flat_schema=TASK_CLASSIFICATION_FLAT_SCHEMA,
        evaluator=lambda output: (output.task_type == TaskType.code_change, None),
    )


def _native_client_for_message(content: str, *, thinking: str = "", done_reason: str = "stop") -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": content, "thinking": thinking},
                "done": True,
                "done_reason": done_reason,
                "eval_count": 7,
                "prompt_eval_count": 11,
            },
            request=request,
        )

    return _REAL_HTTPX_CLIENT(transport=httpx.MockTransport(handler))


def _patch_probe_client(monkeypatch: pytest.MonkeyPatch, client: httpx.Client) -> None:
    monkeypatch.setattr(probe_micro_contracts, "_probe_client", lambda _timeout: client)


def test_flat_schema_contains_no_refs_defs_or_anyof() -> None:
    for case in build_primary_probe_cases():
        assert_flat_schema(case.flat_schema)
        encoded = json.dumps(case.flat_schema)
        assert "$defs" not in encoded
        assert "$ref" not in encoded
        assert "anyOf" not in encoded


def test_native_payload_uses_flat_schema_format() -> None:
    payload = build_native_payload(_task_case(), model_name="gemma4:12b-it-qat", num_predict=512)

    assert payload["model"] == "gemma4:12b-it-qat"
    assert payload["stream"] is False
    assert payload["options"] == {"temperature": 0, "num_predict": 512}
    assert payload["format"] == TASK_CLASSIFICATION_FLAT_SCHEMA


def test_native_endpoint_validation_accepts_localhost() -> None:
    assert validate_native_endpoint("http://localhost:11434/api/chat") == "http://localhost:11434/api/chat"
    assert validate_native_endpoint("http://127.0.0.1:11434/api/chat") == "http://127.0.0.1:11434/api/chat"


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost:11434/api/chat",
        "http://api.example.com/api/chat",
        "http://192.168.1.10:11434/api/chat",
        "http://user:pass@localhost:11434/api/chat",
        "http://localhost:11434/v1/chat/completions",
    ],
)
def test_native_endpoint_validation_rejects_external_or_wrong_urls(url: str) -> None:
    with pytest.raises(ProbeConfigurationError):
        validate_native_endpoint(url)


def test_probe_case_validates_endpoint_before_client_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        probe_micro_contracts,
        "_probe_client",
        lambda _timeout: pytest.fail("client must not be constructed for rejected endpoint"),
    )
    with pytest.raises(ProbeConfigurationError):
        run_probe_case(
            _task_case(),
            model_name="gemma4:12b-it-qat",
            endpoint_url="http://api.example.com/api/chat",
            timeout_seconds=10,
            num_predict=512,
        )


def test_probe_client_is_structurally_proxy_and_redirect_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    fake_client = _native_client_for_message("{}")

    def factory(**kwargs):
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(probe_micro_contracts.httpx, "Client", factory)
    client = probe_micro_contracts._probe_client(10)
    assert client is fake_client
    assert captured["timeout"] == 10
    assert captured["trust_env"] is False
    assert captured["follow_redirects"] is False
    fake_client.close()


def test_probe_case_parses_valid_native_response_with_thinking_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    content = json.dumps(
        {
            "task_type": "code_change",
            "project_area": "jarvisos",
            "requires_context": True,
            "requires_tool": False,
            "requires_external_reasoning": False,
            "reasons": ["Implementation request."],
            "confidence": 0.8,
            "schema_version": MICRO_CONTRACT_SCHEMA_VERSION,
        }
    )
    _patch_probe_client(monkeypatch, _native_client_for_message(content, thinking="plan then answer"))

    result = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    assert result.valid_json is True
    assert result.schema_valid is True
    assert result.content_passed is True
    assert result.message_thinking_empty is False
    assert result.done_reason == "stop"
    assert result.eval_count == 7


def test_probe_case_counts_thinking_budget_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_probe_client(monkeypatch, _native_client_for_message("", thinking="long chain of thought", done_reason="length"))
    result = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    assert result.failure_code == "thinking_budget_exhausted"
    assert result.message_content_empty is True
    assert result.message_thinking_empty is False


def test_probe_case_counts_invalid_json_when_not_budget_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_probe_client(monkeypatch, _native_client_for_message("not json", thinking=""))
    result = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    assert result.failure_code == "invalid_json"
    assert result.valid_json is False


def test_probe_case_counts_schema_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_probe_client(monkeypatch, _native_client_for_message(json.dumps({"task_type": "code_change"})))
    result = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    assert result.failure_code == "schema_invalid"
    assert result.valid_json is True
    assert result.schema_valid is False


def test_probe_case_counts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    _patch_probe_client(monkeypatch, _REAL_HTTPX_CLIENT(transport=httpx.MockTransport(handler)))
    result = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    assert result.failure_code == "timeout"


def test_report_aggregation_counts_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    valid_content = json.dumps(
        {
            "task_type": "code_change",
            "project_area": "jarvisos",
            "requires_context": True,
            "requires_tool": False,
            "requires_external_reasoning": False,
            "reasons": ["Implementation request."],
            "confidence": 0.8,
            "schema_version": MICRO_CONTRACT_SCHEMA_VERSION,
        }
    )
    _patch_probe_client(monkeypatch, _native_client_for_message(valid_content))
    valid = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )
    _patch_probe_client(monkeypatch, _native_client_for_message("", thinking="still thinking", done_reason="length"))
    exhausted = run_probe_case(
        _task_case(),
        model_name="gemma4:12b-it-qat",
        endpoint_url="http://localhost:11434/api/chat",
        timeout_seconds=10,
        num_predict=512,
    )

    report = aggregate_report(
        endpoint_url="http://localhost:11434/api/chat",
        primary_model_name="gemma4:12b-it-qat",
        heavy_model_name=None,
        results=[valid, exhausted],
    )

    assert report.case_count == 2
    assert report.content_passed_count == 1
    assert report.failed_count == 1
    assert report.thinking_budget_exhausted_count == 1


def test_probe_suite_uses_module_owned_mocked_client_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["format"]
        content = {
            "confidence": 0.5,
            "schema_version": MICRO_CONTRACT_SCHEMA_VERSION,
        }
        return httpx.Response(200, json={"message": {"content": json.dumps(content), "thinking": ""}}, request=request)

    monkeypatch.setattr(
        probe_micro_contracts,
        "_probe_client",
        lambda _timeout: _REAL_HTTPX_CLIENT(transport=httpx.MockTransport(handler)),
    )
    report = run_probe_suite(
        timeout_seconds=10,
        run_heavy_comparison=False,
    )

    assert report.case_count == 6
    assert report.schema_invalid_count >= 1


def test_probe_module_uses_no_external_provider_imports() -> None:
    text = (Path(__file__).resolve().parents[1] / "app" / "modules" / "local_ai_eval" / "probe_micro_contracts.py").read_text(
        encoding="utf-8"
    ).lower()
    forbidden_imports = (
        "import openai",
        "from openai",
        "import scaleway",
        "from scaleway",
        "import deepseek",
        "from deepseek",
        "import anthropic",
        "from anthropic",
        "google.generativeai",
    )

    assert all(forbidden not in text for forbidden in forbidden_imports)
