"""POS-1 — positive AI execution spine. Fake/offline only; no network, no secrets."""

from __future__ import annotations

import json

from app.modules.ai.contracts import (
    AIRequest,
    AIResponse,
    AIUsage,
    AIUsageSource,
)


def _isolate_and_init(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "jarvisos-aijobs"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.database import initialize_database

    initialize_database()


def _all_ai_jobs() -> list[dict]:
    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT * FROM ai_jobs ORDER BY created_at ASC").fetchall()
    return [dict(row) for row in rows]


class _RaisingAdapter:
    provider_id = "fake"

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        raise RuntimeError("boom from provider")

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


class _CaptureAdapter:
    provider_id = "local_ollama"

    def __init__(self) -> None:
        self.requests: list[AIRequest] = []

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        text = f"captured:{request.model_preference}"
        return AIResponse(
            provider_id="local_ollama",
            model_id=request.model_preference or "missing-model",
            request_id=request.request_id,
            text=text,
            content=text,
            usage=AIUsage(provider_id="local_ollama", model_id=request.model_preference or "missing-model", input_tokens=1, output_tokens=1),
            safety_status="allowed",
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


def _stub_scaleway_adapter(captured_text: str = "stub cloud answer", provider_id: str = "deepseek"):
    class _StubScaleway:
        def __init__(self) -> None:
            self.provider_id = provider_id

        def health(self):  # pragma: no cover - not used
            ...

        def list_models(self):  # pragma: no cover - not used
            return []

        def complete(self, request: AIRequest) -> AIResponse:
            return AIResponse(
                provider_id=self.provider_id,
                model_id=request.model_preference or "stub-model",
                request_id=request.request_id,
                text=captured_text,
                content=captured_text,
                usage=AIUsage(provider_id=self.provider_id, model_id="stub-model", input_tokens=3, output_tokens=4),
                safety_status="allowed",
            )

        def stream(self, request: AIRequest):  # pragma: no cover - not used
            raise NotImplementedError

    return _StubScaleway()


def _clear_local_route_env(monkeypatch) -> None:
    for env_name in (
        "AI_ROUTE_LOCAL_MODEL",
        "AI_ROUTE_LOCAL_FAST_MODEL",
        "AI_ROUTE_LOCAL_GENERAL_MODEL",
        "AI_ROUTE_LOCAL_CODER_MODEL",
        "AI_ROUTE_LOCAL_CODER_HEAVY_MODEL",
        "JARVISOS_DEV_MESSAGE_ROUTE_MODEL",
    ):
        monkeypatch.delenv(env_name, raising=False)


def test_fake_route_executes_and_writes_ai_job(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="explain a pump", route_class="local:fake")

    assert outcome.status == "success"
    assert outcome.response is not None
    assert outcome.response.text is not None
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "success"
    assert rows[0]["provider_id"] == "fake"
    assert rows[0]["selected_route_class"] == "local:fake"
    assert rows[0]["prompt_digest"].startswith("sha256:")
    assert rows[0]["output_digest"].startswith("sha256:")


def test_malformed_route_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="x", route_class="external reasoning")

    assert outcome.status == "validation_error"
    assert outcome.response is None
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "validation_error"
    assert rows[0]["provider_id"] is None


def test_unbound_route_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="x", route_class="external:vision")

    assert outcome.status == "route_unavailable"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "route_unavailable"
    assert "no binding configured" in json.loads(rows[0]["route_reason_json"])["decision_reason"]


def test_missing_provider_credentials_fails_closed_and_records(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="real work", route_class="external:cheap")

    assert outcome.status == "config_error"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "config_error"
    assert rows[0]["provider_id"] == "deepseek"
    assert rows[0]["error_type"] == "config_error"


def test_synthesis_task_kind_defaults_to_local_fake(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="summarize safely", task_kind="synthesis")

    assert outcome.status == "success"
    assert outcome.selected_route_class == "local:fake"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["selected_route_class"] == "local:fake"
    assert rows[0]["provider_id"] == "fake"


def test_success_writes_exactly_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    run_ai_task(user_prompt="one", route_class="local:fake")
    run_ai_task(user_prompt="two", route_class="local:fake")

    rows = _all_ai_jobs()
    assert len(rows) == 2
    assert all(row["status"] == "success" for row in rows)


def test_provider_error_records_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(
        user_prompt="will fail",
        route_class="local:fake",
        adapters={"fake": _RaisingAdapter()},
    )

    assert outcome.status == "provider_error"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "provider_error"
    assert rows[0]["error_type"] == "RuntimeError"


def test_api_key_value_absent_from_ledger(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    secret = "sk-deepseek-supersecret-998877"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    from app.modules.ai.models import AISettingsUpdate
    from app.modules.ai.settings import update_ai_settings

    update_ai_settings(AISettingsUpdate(paid_ai_enabled=True, monthly_api_budget_usd=10))
    from app.modules.ai.execution import run_ai_task

    # Stub external adapter so no real network; key is set in env but must never
    # land in the ledger.
    outcome = run_ai_task(
        user_prompt="route through cloud binding",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": _stub_scaleway_adapter()},
    )

    assert outcome.status == "success"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    serialized = json.dumps(rows[0])
    assert secret not in serialized


def test_fake_path_does_not_touch_network(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)

    def _boom(*args, **kwargs):
        raise AssertionError("no network call allowed in tests")

    monkeypatch.setattr("httpx.post", _boom)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(user_prompt="offline", route_class="local:fake")
    assert outcome.status == "success"


def test_prompt_and_context_digests_are_stable(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task

    context = [{"source": "manual", "content": "JarvisOS positive cloud path"}]
    run_ai_task(user_prompt="same", route_class="local:fake", context_blocks=context)
    run_ai_task(user_prompt="same", route_class="local:fake", context_blocks=context)

    rows = _all_ai_jobs()
    assert rows[0]["prompt_digest"] == rows[1]["prompt_digest"]
    assert rows[0]["context_digest"] == rows[1]["context_digest"]
    assert rows[0]["context_digest"] is not None


def test_default_bindings_and_adapters_include_local_gemma(monkeypatch) -> None:
    _clear_local_route_env(monkeypatch)
    from app.modules.ai.execution import _default_adapters, _default_bindings

    bindings = _default_bindings()
    adapters = _default_adapters()

    assert "local:gemma" in bindings
    assert bindings["local:gemma"].provider_id == "local_ollama"
    assert "local_ollama" in adapters


def test_local_ollama_adapter_default_model_is_qwen3(monkeypatch) -> None:
    _clear_local_route_env(monkeypatch)
    from app.modules.ai.contracts import AITaskType
    from app.modules.ai.providers.local_ollama_adapter import LocalOllamaAdapter

    captured: dict[str, object] = {}

    def _fake_responder(prompt: str, **kwargs):
        captured.update(kwargs)
        return {
            "response": "ok",
            "response_truncated": False,
            "response_char_count_returned": 2,
            "response_char_limit": kwargs["max_output_chars"],
            "response_limit_source": "test",
        }

    adapter = LocalOllamaAdapter()
    monkeypatch.setattr(adapter, "_load_responder", lambda: _fake_responder)

    listed = adapter.list_models()
    response = adapter.complete(AIRequest(task_type=AITaskType.synthesis, prompt="hello"))

    assert adapter.health().value == "healthy"
    assert len(listed) == 1
    assert listed[0].model_id == "qwen3:8b"
    assert listed[0].provider_model_name == "qwen3:8b"
    assert listed[0].display_name == "Local Ollama qwen3:8b"
    assert captured["model"] == "qwen3:8b"
    assert response.model_id == "qwen3:8b"


def test_local_ollama_route_bindings_have_expected_defaults(monkeypatch) -> None:
    _clear_local_route_env(monkeypatch)
    from app.modules.ai.execution import _default_bindings

    bindings = _default_bindings()
    expected = {
        "local:fast": "qwen3:8b",
        "local:general": "gemma4:12b-it-qat",
        "local:gemma": "gemma4:12b-it-qat",
        "local:coder": "deepseek-coder-v2:16b",
        "local:coder_heavy": "qwen3-coder:30b",
    }

    for route_class, model_id in expected.items():
        binding = bindings[route_class]
        assert binding.provider_id == "local_ollama"
        assert binding.model_id == model_id
        assert binding.requires_network is False
        assert binding.max_output_tokens == 512
    assert bindings["local:general"].model_id == bindings["local:gemma"].model_id


def test_local_ollama_route_env_override_precedence(monkeypatch) -> None:
    _clear_local_route_env(monkeypatch)
    monkeypatch.setenv("AI_ROUTE_LOCAL_FAST_MODEL", "fast:test")
    monkeypatch.setenv("AI_ROUTE_LOCAL_GENERAL_MODEL", "general:test")
    monkeypatch.setenv("AI_ROUTE_LOCAL_MODEL", "legacy:test")
    monkeypatch.setenv("AI_ROUTE_LOCAL_CODER_MODEL", "coder:test")
    monkeypatch.setenv("AI_ROUTE_LOCAL_CODER_HEAVY_MODEL", "coder-heavy:test")
    from app.modules.ai.execution import _default_bindings

    bindings = _default_bindings()

    assert bindings["local:fast"].model_id == "fast:test"
    assert bindings["local:general"].model_id == "general:test"
    assert bindings["local:gemma"].model_id == "general:test"
    assert bindings["local:coder"].model_id == "coder:test"
    assert bindings["local:coder_heavy"].model_id == "coder-heavy:test"

    monkeypatch.delenv("AI_ROUTE_LOCAL_GENERAL_MODEL", raising=False)
    bindings = _default_bindings()

    assert bindings["local:general"].model_id == "legacy:test"
    assert bindings["local:gemma"].model_id == "legacy:test"
    assert bindings["local:fast"].model_id == "fast:test"
    assert bindings["local:coder"].model_id == "coder:test"
    assert bindings["local:coder_heavy"].model_id == "coder-heavy:test"


def test_local_ollama_routes_pass_model_preference_to_adapter(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _clear_local_route_env(monkeypatch)
    monkeypatch.setenv("AI_ROUTE_LOCAL_FAST_MODEL", "fast:override")
    monkeypatch.setenv("AI_ROUTE_LOCAL_CODER_MODEL", "coder:override")
    from app.modules.ai.execution import run_ai_task

    adapter = _CaptureAdapter()

    fast = run_ai_task(user_prompt="fast", route_class="local:fast", adapters={"local_ollama": adapter})
    coder = run_ai_task(user_prompt="coder", route_class="local:coder", adapters={"local_ollama": adapter})

    assert fast.status == "success"
    assert coder.status == "success"
    assert [request.model_preference for request in adapter.requests] == ["fast:override", "coder:override"]
    rows = _all_ai_jobs()
    assert [row["selected_route_class"] for row in rows] == ["local:fast", "local:coder"]
    assert [row["provider_id"] for row in rows] == ["local_ollama", "local_ollama"]


def test_local_gemma_route_executes_and_writes_ai_job(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.providers.local_ollama_adapter import LocalOllamaAdapter

    captured: dict[str, object] = {}

    def _fake_responder(prompt: str, **kwargs):
        captured["max_output_chars"] = kwargs["max_output_chars"]
        return {
            "response": f"[gemma] {prompt[:40]}",
            "response_truncated": False,
            "response_char_count_returned": 17,
            "response_char_limit": kwargs["max_output_chars"],
            "response_limit_source": "test",
            "local_responder_timing": {"total_duration_ms": 12},
        }

    monkeypatch.setattr(LocalOllamaAdapter, "_load_responder", lambda self: _fake_responder)

    outcome = run_ai_task(user_prompt="explain a pump", route_class="local:gemma")

    assert outcome.status == "success"
    assert outcome.selected_route_class == "local:gemma"
    assert outcome.response is not None
    assert outcome.response.provider_id == "local_ollama"
    assert outcome.response.text == "[gemma] explain a pump"
    assert outcome.response.usage.usage_source == AIUsageSource.estimated
    assert "response" not in outcome.response.raw_provider_metadata
    assert captured["max_output_chars"] == 2048
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "success"
    assert rows[0]["provider_id"] == "local_ollama"
    assert rows[0]["selected_route_class"] == "local:gemma"


def test_local_gemma_provider_error_records_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.providers.local_ollama_adapter import LocalOllamaAdapter

    def _boom(prompt: str, **kwargs):
        raise RuntimeError("local responder failed")

    monkeypatch.setattr(LocalOllamaAdapter, "_load_responder", lambda self: _boom)

    outcome = run_ai_task(user_prompt="will fail", route_class="local:gemma")

    assert outcome.status == "provider_error"
    assert outcome.error_type == "RuntimeError"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "provider_error"
    assert rows[0]["provider_id"] == "local_ollama"
    assert rows[0]["selected_route_class"] == "local:gemma"
    assert rows[0]["error_type"] == "RuntimeError"


def test_configured_local_ollama_provider_error_records_one_row(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _clear_local_route_env(monkeypatch)
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(
        user_prompt="will fail",
        route_class="local:coder",
        adapters={"local_ollama": _RaisingAdapter()},
    )

    assert outcome.status == "provider_error"
    assert outcome.error_type == "RuntimeError"
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["status"] == "provider_error"
    assert rows[0]["provider_id"] == "local_ollama"
    assert rows[0]["selected_route_class"] == "local:coder"
    assert rows[0]["error_type"] == "RuntimeError"


def test_local_gemma_caps_max_output_chars(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    from app.modules.ai.execution import run_ai_task
    from app.modules.ai.providers.local_ollama_adapter import LocalOllamaAdapter

    captured: dict[str, object] = {}

    def _fake_responder(prompt: str, **kwargs):
        captured["max_output_chars"] = kwargs["max_output_chars"]
        return {
            "response": "ok",
            "response_truncated": False,
            "response_char_count_returned": 2,
            "response_char_limit": kwargs["max_output_chars"],
            "response_limit_source": "test",
        }

    monkeypatch.setattr(LocalOllamaAdapter, "_load_responder", lambda self: _fake_responder)

    outcome = run_ai_task(user_prompt="cap test", route_class="local:gemma", max_output_tokens=99999)

    assert outcome.status == "success"
    assert captured["max_output_chars"] == 16000


def test_provider_registry_default_bindings_for_representative_routes(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("AI_ROUTE_CHEAP_MODEL", raising=False)
    monkeypatch.delenv("AI_ROUTE_REASONING_MODEL", raising=False)
    from app.modules.ai.execution import resolve_binding, run_ai_task

    none_outcome = run_ai_task(user_prompt="default", route_class=None)
    fake_outcome = run_ai_task(user_prompt="fake", route_class="local:fake")
    cheap_binding, cheap_decision = resolve_binding("external:cheap")
    reasoning_binding, reasoning_decision = resolve_binding("external:reasoning")
    cheap_outcome = run_ai_task(user_prompt="cheap", route_class="external:cheap")
    reasoning_outcome = run_ai_task(user_prompt="reason", route_class="external:reasoning")

    assert none_outcome.selected_route_class == "local:fake"
    assert none_outcome.status == "success"
    assert none_outcome.response.provider_id == "fake"
    assert fake_outcome.selected_route_class == "local:fake"
    assert fake_outcome.status == "success"
    assert fake_outcome.response.model_id == "fake-deterministic-v1"
    assert cheap_binding.provider_id == "deepseek"
    assert cheap_binding.model_id == "deepseek-v4-pro"
    assert cheap_binding.max_output_tokens == 512
    assert cheap_decision.provider_id == "deepseek"
    assert reasoning_binding.provider_id == "glm"
    assert reasoning_binding.model_id == "glm-5.2"
    assert reasoning_binding.max_output_tokens == 1024
    assert reasoning_decision.model_id == "glm-5.2"
    assert cheap_outcome.status == "config_error"
    assert reasoning_outcome.status == "config_error"
    rows = _all_ai_jobs()
    assert [row["selected_route_class"] for row in rows] == [
        "local:fake",
        "local:fake",
        "external:cheap",
        "external:reasoning",
    ]
    assert [row["provider_id"] for row in rows] == ["fake", "fake", "deepseek", "glm"]


def _configure_external_allowed(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("GLM_API_KEY", "glm-test-key")
    from app.modules.ai.models import AISettingsUpdate
    from app.modules.ai.settings import update_ai_settings

    update_ai_settings(AISettingsUpdate(paid_ai_enabled=True, monthly_api_budget_usd=100))


class _ErrorAdapter:
    def __init__(self, provider_id: str, code, *, retryable: bool) -> None:
        self.provider_id = provider_id
        self.code = code
        self.retryable = retryable
        self.requests: list[AIRequest] = []

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        from app.modules.ai.contracts import AIProviderError

        self.requests.append(request)
        return AIResponse(
            provider_id=self.provider_id,
            model_id=request.model_preference or "missing-model",
            request_id=request.request_id,
            usage=AIUsage(provider_id=self.provider_id, model_id=request.model_preference or "missing-model"),
            safety_status="blocked",
            blocked_reason="provider_failed",
            error=AIProviderError(code=self.code, message="provider failed", retryable=self.retryable),
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


class _SuccessAdapter:
    def __init__(self, provider_id: str, text: str = "ok") -> None:
        self.provider_id = provider_id
        self.text = text
        self.requests: list[AIRequest] = []

    def health(self):  # pragma: no cover - not used
        ...

    def list_models(self):  # pragma: no cover - not used
        return []

    def complete(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        return AIResponse(
            provider_id=self.provider_id,
            model_id=request.model_preference or "missing-model",
            request_id=request.request_id,
            text=self.text,
            content=self.text,
            usage=AIUsage(provider_id=self.provider_id, model_id=request.model_preference or "missing-model", input_tokens=5, output_tokens=7),
            safety_status="allowed",
        )

    def stream(self, request: AIRequest):  # pragma: no cover - not used
        raise NotImplementedError


def test_provider_token_cap_blocks_before_adapter_call(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.core.database import open_sqlite_connection
    from app.modules.ai.execution import run_ai_task
    from app.modules.events.service import utc_now

    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO ai_jobs (
                id, created_at, status, task_kind, requested_route_class, selected_route_class,
                provider_id, model_id, route_reason_json, input_tokens, output_tokens, latency_ms
            ) VALUES (?, ?, 'success', 'test', 'external:cheap', 'external:cheap', ?, ?, '{}', ?, ?, 1)
            """,
            ("usage-row", utc_now(), "deepseek", "deepseek-v4-pro", 600000, 400000),
        )
        connection.commit()

    fail_adapter = _SuccessAdapter("deepseek")
    outcome = run_ai_task(
        user_prompt="blocked by cap",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": fail_adapter, "glm": _SuccessAdapter("glm")},
    )

    assert outcome.status == "config_error"
    assert fail_adapter.requests == []
    rows = _all_ai_jobs()
    assert len(rows) == 2
    assert rows[-1]["provider_id"] == "deepseek"
    assert "deepseek_monthly_token_cap_exhausted" in json.loads(rows[-1]["route_reason_json"])["decision_reason"]


def test_provider_zero_caps_are_unlimited(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.modules.ai import budget
    from app.modules.ai.provider_registry import ProviderConfig

    monkeypatch.setattr(
        budget,
        "_registry_provider",
        lambda provider_id: ProviderConfig(provider_id, "openai_compatible", True, True, "https://example.test", "env:DEEPSEEK_API_KEY", 20, 0, 0),
    )
    gate = budget.evaluate_provider_budget_gate(__import__("app.modules.ai.settings", fromlist=["get_ai_settings"]).get_ai_settings(), "deepseek")

    assert gate.allowed is True


def test_fallback_chain_retryable_error_advances_and_writes_attempt_rows(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.modules.ai.contracts import AIProviderErrorCode
    from app.modules.ai.execution import run_ai_task

    first = _ErrorAdapter("deepseek", AIProviderErrorCode.provider_timeout, retryable=True)
    second = _SuccessAdapter("glm", text="fallback ok")
    outcome = run_ai_task(
        user_prompt="try fallback",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": first, "glm": second},
    )

    assert outcome.status == "success"
    assert outcome.response.provider_id == "glm"
    assert len(first.requests) == 1
    assert len(second.requests) == 1
    rows = _all_ai_jobs()
    assert [row["provider_id"] for row in rows] == ["deepseek", "glm"]
    first_meta = json.loads(rows[0]["route_reason_json"])
    second_meta = json.loads(rows[1]["route_reason_json"])
    assert first_meta["fallback_attempt_index"] == 0
    assert second_meta["fallback_attempt_index"] == 1
    assert second_meta["prior_retryable_error_code"] == "provider_timeout"


def test_fallback_chain_non_retryable_error_does_not_advance(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    _configure_external_allowed(monkeypatch)
    from app.modules.ai.contracts import AIProviderErrorCode
    from app.modules.ai.execution import run_ai_task

    first = _ErrorAdapter("deepseek", AIProviderErrorCode.provider_bad_request, retryable=False)
    second = _SuccessAdapter("glm")
    outcome = run_ai_task(
        user_prompt="do not fallback",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": first, "glm": second},
    )

    assert outcome.status == "provider_error"
    assert len(first.requests) == 1
    assert second.requests == []
    assert len(_all_ai_jobs()) == 1


def test_credential_block_does_not_fallback(monkeypatch, tmp_path) -> None:
    _isolate_and_init(monkeypatch, tmp_path)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("GLM_API_KEY", "glm-test-key")
    from app.modules.ai.models import AISettingsUpdate
    from app.modules.ai.settings import update_ai_settings

    update_ai_settings(AISettingsUpdate(paid_ai_enabled=True, monthly_api_budget_usd=100))
    second = _SuccessAdapter("glm")
    from app.modules.ai.execution import run_ai_task

    outcome = run_ai_task(
        user_prompt="credential blocked",
        route_class="external:cheap",
        max_output_tokens=64,
        adapters={"deepseek": _SuccessAdapter("deepseek"), "glm": second},
    )

    assert outcome.status == "config_error"
    assert second.requests == []
    rows = _all_ai_jobs()
    assert len(rows) == 1
    assert rows[0]["provider_id"] == "deepseek"
    assert "deepseek_api_key_missing" in json.loads(rows[0]["route_reason_json"])["decision_reason"]
