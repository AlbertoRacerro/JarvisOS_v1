from __future__ import annotations

import importlib.util
import json
import urllib.request
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "local_model_structured_output_probe.py"


def _load_probe() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spec137_structured_probe", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost:11434/api/chat",
        "http://192.0.2.1:11434/api/chat",
        "http://user@localhost:11434/api/chat",
        "http:///api/chat",
        "http://localhost:notaport/api/chat",
    ],
)
def test_call_ollama_chat_rejects_nonlocal_or_malformed_urls_before_request(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    probe = _load_probe()

    def fail_request(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("urllib request construction must not occur for rejected endpoints")

    monkeypatch.setattr(probe.urllib.request, "Request", fail_request)
    monkeypatch.setattr(probe.urllib.request, "urlopen", fail_request)
    monkeypatch.setattr(probe.urllib.request, "build_opener", fail_request)

    with pytest.raises(ValueError):
        probe.call_ollama_chat(
            model="local-test",
            prompt="{}",
            schema={"type": "object"},
            timeout_seconds=1,
            url=url,
        )


def test_call_ollama_chat_uses_proxy_disabled_redirect_rejecting_opener(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_probe()
    captured_handlers: list[Any] = []
    captured_requests: list[Any] = []

    class FakeResponse:
        status = 200

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"message": {"content": "{}"}}).encode("utf-8")

    class FakeOpener:
        def open(self, request: Any, *, timeout: int) -> FakeResponse:
            captured_requests.append((request, timeout))
            return FakeResponse()

    def fake_build_opener(*handlers: Any) -> FakeOpener:
        captured_handlers.extend(handlers)
        return FakeOpener()

    monkeypatch.setattr(probe.urllib.request, "build_opener", fake_build_opener)

    def fail_urlopen(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("raw urlopen must not be used")

    monkeypatch.setattr(probe.urllib.request, "urlopen", fail_urlopen)

    result = probe.call_ollama_chat(
        model="local-test",
        prompt="{}",
        schema={"type": "object"},
        timeout_seconds=3,
        url="http://[::1]:11434/api/chat",
    )

    assert result["ok"] is True
    assert captured_requests and captured_requests[0][1] == 3
    assert any(
        isinstance(handler, urllib.request.ProxyHandler) and handler.proxies == {}
        for handler in captured_handlers
    )
    redirect_handlers = [
        handler
        for handler in captured_handlers
        if isinstance(handler, urllib.request.HTTPRedirectHandler)
    ]
    assert len(redirect_handlers) == 1
    assert redirect_handlers[0].redirect_request(None, None, 302, "Found", {}, "http://example.com") is None
