from __future__ import annotations

import httpx

from app.modules.ai.contracts import AIRequest, AITaskType
from app.modules.ai.providers.local_ollama_adapter import LocalOllamaAdapter
from app.modules.local_ai.runtime.ollama import resolve_ollama_runtime_urls
from app.modules.local_ai.runtime.status import (
    LOCAL_RUNTIME_STATUS_TIMEOUT_S,
    get_local_ai_runtime_status,
)


class _FakeClient:
    def __init__(self, routes: dict[str, object]) -> None:
        self.routes = routes
        self.calls: list[tuple[str, float | None]] = []

    def get(self, url: str, timeout: float | None = None) -> httpx.Response:
        self.calls.append((url, timeout))
        path = httpx.URL(url).path
        if path not in self.routes:
            raise AssertionError(f"unexpected GET path: {path}")
        action = self.routes[path]
        request = httpx.Request("GET", url)
        if isinstance(action, Exception):
            raise action
        if isinstance(action, httpx.Response):
            return action
        return httpx.Response(200, json=action, request=request)


def _clear_env(monkeypatch) -> None:
    for env_name in (
        "AI_ROUTE_LOCAL_MODEL",
        "AI_ROUTE_LOCAL_FAST_MODEL",
        "AI_ROUTE_LOCAL_GENERAL_MODEL",
        "AI_ROUTE_LOCAL_CODER_MODEL",
        "AI_ROUTE_LOCAL_CODER_HEAVY_MODEL",
        "JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT",
    ):
        monkeypatch.delenv(env_name, raising=False)


def test_runtime_status_reachable_with_all_models_present(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": {
                "models": [
                    {"name": "qwen3:8b"},
                    {"name": "gemma4:12b-it-qat"},
                    {"model": "deepseek-coder-v2:16b"},
                    {"name": "qwen3-coder:30b"},
                ]
            },
            "/api/ps": {
                "models": [
                    {
                        "name": "qwen3:8b",
                        "model": "qwen3:8b",
                        "size": 100,
                        "size_vram": 100,
                        "processor": "100% GPU",
                        "until": "2026-07-01T12:00:00Z",
                    }
                ]
            },
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is True
    assert status["ollama_version"] == "0.9.6"
    assert status["installed_models"] == [
        "qwen3:8b",
        "gemma4:12b-it-qat",
        "deepseek-coder-v2:16b",
        "qwen3-coder:30b",
    ]
    assert status["missing_models"] == {}
    assert status["loaded_models"] == [
        {
            "name": "qwen3:8b",
            "model": "qwen3:8b",
            "size": 100,
            "size_vram": 100,
            "processor": "100% GPU",
            "until": "2026-07-01T12:00:00Z",
            "spilled": False,
        }
    ]


def test_runtime_status_reports_missing_configured_model(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": {
                "models": [
                    {"name": "qwen3:8b"},
                    {"name": "gemma4:12b-it-qat"},
                    {"name": "deepseek-coder-v2:16b"},
                ]
            },
            "/api/ps": {"models": []},
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is True
    assert status["missing_models"] == {"local:coder_heavy": "qwen3-coder:30b"}


def test_runtime_status_unreachable_skips_tags_and_ps(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": httpx.ConnectError("not running"),
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is False
    assert status["installed_models"] == []
    assert status["loaded_models"] == []
    assert status["error_type"] == "ConnectError"
    assert set(status["missing_models"]) == {
        "local:fast",
        "local:general",
        "local:gemma",
        "local:coder",
        "local:coder_heavy",
    }
    assert [httpx.URL(url).path for url, _ in client.calls] == ["/api/version"]


def test_runtime_status_tags_failure_keeps_ps(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": httpx.ReadTimeout("too slow"),
            "/api/ps": {"models": []},
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is True
    assert status["installed_models"] == []
    assert status["tags_error_type"] == "ReadTimeout"
    assert status["loaded_models"] == []
    assert set(status["missing_models"]) == {
        "local:fast",
        "local:general",
        "local:gemma",
        "local:coder",
        "local:coder_heavy",
    }
    assert [httpx.URL(url).path for url, _ in client.calls] == ["/api/version", "/api/tags", "/api/ps"]


def test_runtime_status_ps_failure_does_not_crash(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": {"models": [{"name": "qwen3:8b"}]},
            "/api/ps": httpx.ConnectError("ps unavailable"),
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is True
    assert status["installed_models"] == ["qwen3:8b"]
    assert status["loaded_models"] == []
    assert status["ps_error_type"] == "ConnectError"


def test_runtime_status_parses_loaded_model_spill_fields(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": {"models": []},
            "/api/ps": {
                "models": [
                    {"name": "fit", "model": "fit", "size": 100, "size_vram": 100},
                    {"name": "spill", "model": "spill", "size": 200, "size_vram": 100},
                    {"model": "unknown-size"},
                ]
            },
        }
    )

    status = get_local_ai_runtime_status(client=client)

    assert status["loaded_models"] == [
        {
            "name": "fit",
            "model": "fit",
            "size": 100,
            "size_vram": 100,
            "processor": None,
            "until": None,
            "spilled": False,
        },
        {
            "name": "spill",
            "model": "spill",
            "size": 200,
            "size_vram": 100,
            "processor": None,
            "until": None,
            "spilled": True,
        },
        {
            "name": "unknown-size",
            "model": "unknown-size",
            "size": None,
            "size_vram": None,
            "processor": None,
            "until": None,
            "spilled": None,
        },
    ]


def test_runtime_status_rejects_non_local_endpoint_without_http(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT", "http://example.com:11434/api/generate")
    client = _FakeClient({})

    status = get_local_ai_runtime_status(client=client)

    assert status["ollama_reachable"] is False
    assert status["error_type"] == "invalid_endpoint"
    assert status["installed_models"] == []
    assert status["loaded_models"] == []
    assert set(status["missing_models"]) == {
        "local:fast",
        "local:general",
        "local:gemma",
        "local:coder",
        "local:coder_heavy",
    }
    assert client.calls == []


def test_runtime_status_uses_short_timeout(monkeypatch) -> None:
    _clear_env(monkeypatch)
    client = _FakeClient(
        {
            "/api/version": {"version": "0.9.6"},
            "/api/tags": {"models": []},
            "/api/ps": {"models": []},
        }
    )

    get_local_ai_runtime_status(client=client)

    assert client.calls
    assert all(timeout == LOCAL_RUNTIME_STATUS_TIMEOUT_S for _, timeout in client.calls)


def test_status_and_adapter_share_endpoint_resolver(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT", "http://localhost:11434/api/generate")
    captured: dict[str, str] = {}

    def _fake_responder(prompt: str, **kwargs):
        captured["endpoint"] = kwargs["endpoint"]
        return {"response": "ok", "response_truncated": False, "response_char_count_returned": 2, "response_char_limit": 4, "response_limit_source": "test"}

    adapter = LocalOllamaAdapter()
    monkeypatch.setattr(adapter, "_load_responder", lambda: _fake_responder)

    response = adapter.complete(AIRequest(task_type=AITaskType.synthesis, prompt="hello", model_preference="qwen3:8b"))
    status = get_local_ai_runtime_status(client=_FakeClient({"/api/version": {"version": "0.9.6"}, "/api/tags": {"models": []}, "/api/ps": {"models": []}}))

    assert captured["endpoint"] == resolve_ollama_runtime_urls().generate_endpoint
    assert status["endpoint"] == resolve_ollama_runtime_urls().base_url
    assert response.model_id == "qwen3:8b"


def test_status_and_adapter_support_base_url_endpoint_env(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT", "http://127.0.0.1:11434")
    captured: dict[str, str] = {}

    def _fake_responder(prompt: str, **kwargs):
        captured["endpoint"] = kwargs["endpoint"]
        return {
            "response": "ok",
            "response_truncated": False,
            "response_char_count_returned": 2,
            "response_char_limit": 4,
            "response_limit_source": "test",
        }

    adapter = LocalOllamaAdapter()
    monkeypatch.setattr(adapter, "_load_responder", lambda: _fake_responder)

    urls = resolve_ollama_runtime_urls()
    status = get_local_ai_runtime_status(
        client=_FakeClient(
            {"/api/version": {"version": "0.9.6"}, "/api/tags": {"models": []}, "/api/ps": {"models": []}}
        )
    )
    adapter.complete(AIRequest(task_type=AITaskType.synthesis, prompt="hello", model_preference="qwen3:8b"))

    assert urls.base_url == "http://127.0.0.1:11434"
    assert urls.generate_endpoint == "http://127.0.0.1:11434/api/generate"
    assert status["endpoint"] == "http://127.0.0.1:11434"
    assert captured["endpoint"] == "http://127.0.0.1:11434/api/generate"


def test_runtime_status_reflects_route_model_env_overrides(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("AI_ROUTE_LOCAL_FAST_MODEL", "fast:override")
    monkeypatch.setenv("AI_ROUTE_LOCAL_GENERAL_MODEL", "general:override")
    monkeypatch.setenv("AI_ROUTE_LOCAL_CODER_MODEL", "coder:override")
    monkeypatch.setenv("AI_ROUTE_LOCAL_CODER_HEAVY_MODEL", "heavy:override")

    status = get_local_ai_runtime_status(client=_FakeClient({"/api/version": {"version": "0.9.6"}, "/api/tags": {"models": []}, "/api/ps": {"models": []}}))

    assert status["configured_route_models"] == {
        "local:fast": "fast:override",
        "local:general": "general:override",
        "local:gemma": "general:override",
        "local:coder": "coder:override",
        "local:coder_heavy": "heavy:override",
    }
