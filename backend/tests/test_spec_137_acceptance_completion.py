from __future__ import annotations

import importlib.util
import inspect
import io
import json
import subprocess
import sys
import urllib.request
import urllib.response
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest

from app.modules.local_ai_eval import probe_micro_contracts as micro_probe

ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / "scripts" / "check_architecture_enforcement.py"
STRUCTURED_PROBE = ROOT / "scripts" / "local_model_structured_output_probe.py"
ROUTER_RESPONDER = ROOT / "scripts" / "router_policy_local_responder.py"


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_scanner(root: Path) -> subprocess.CompletedProcess[str]:
    config = root / "configs" / "architecture_enforcement.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"exceptions": []}), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--config", str(config)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_ae002_completes_frozen_alias_datagram_and_provider_fixtures(tmp_path: Path) -> None:
    source = tmp_path / "backend/app/frozen_matrix.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "import app.modules.ai.providers.deepseek\n"
        "import socket as sock\n"
        "import urllib.request as ur\n"
        "from aiohttp import ClientSession as Session\n"
        "from http.client import HTTPSConnection as Conn\n"
        "from socket import socket as Socket\n"
        "from urllib.request import build_opener as make_opener\n"
        "from urllib3 import PoolManager as Pool\n"
        "def socket_connect_ex():\n    s = sock.socket(); s.connect_ex(('example.invalid', 443))\n"
        "def socket_sendmsg():\n    s = Socket(); s.sendmsg([b'x'], [], 0, ('example.invalid', 443))\n"
        "def urllib_alias():\n    ur.urlopen('https://example.invalid')\n"
        "def urllib_from_import():\n    opener = make_opener(); opener.open('https://example.invalid')\n"
        "def urllib3_from_import():\n    pool = Pool(); pool.request('GET', 'https://example.invalid')\n"
        "def aiohttp_from_import():\n    client = Session(); client.post('https://example.invalid')\n"
        "def http_client_from_import():\n    client = Conn('example.invalid'); client.request('GET', '/')\n"
        "def provider_dotted_import():\n    app.modules.ai.providers.deepseek.complete('x')\n",
        encoding="utf-8",
    )
    result = _run_scanner(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    for symbol in (
        "socket_connect_ex",
        "socket_sendmsg",
        "urllib_alias",
        "urllib_from_import",
        "urllib3_from_import",
        "aiohttp_from_import",
        "http_client_from_import",
        "provider_dotted_import",
    ):
        assert f"AE002 backend/app/frozen_matrix.py::{symbol}" in result.stdout


class _RedirectHTTPHandler(urllib.request.HTTPHandler):
    handler_order = 100

    def __init__(self, seen: list[str], location: str) -> None:
        super().__init__()
        self._seen = seen
        self._location = location

    def http_open(self, request: Any) -> Any:
        self._seen.append(request.full_url)
        headers = Message()
        headers["Location"] = self._location
        response = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, 302)
        response.msg = "Found"
        return response


def _install_redirect_transport(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    *,
    seen: list[str],
    location: str = "http://example.invalid/escape",
) -> None:
    original_build_opener = urllib.request.build_opener

    def build_opener(*handlers: Any) -> Any:
        proxy_handlers = [handler for handler in handlers if isinstance(handler, urllib.request.ProxyHandler)]
        assert len(proxy_handlers) == 1 and proxy_handlers[0].proxies == {}
        return original_build_opener(*handlers, _RedirectHTTPHandler(seen, location))

    monkeypatch.setattr(module.urllib.request, "build_opener", build_opener)


def test_structured_probe_rejects_real_redirect_before_followup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = _load_module("spec137_structured_redirect", STRUCTURED_PROBE)
    seen: list[str] = []
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.invalid:8080")
    _install_redirect_transport(probe, monkeypatch, seen=seen)

    result = probe.call_ollama_chat(
        model="local-test",
        prompt="{}",
        schema={"type": "object"},
        timeout_seconds=1,
        url="http://127.0.0.1:11434/api/chat",
    )

    assert result["ok"] is False
    assert seen == ["http://127.0.0.1:11434/api/chat"]


def test_router_transport_rejects_real_redirect_before_followup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responder = _load_module("spec137_router_redirect", ROUTER_RESPONDER)
    seen: list[str] = []
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.invalid:8080")
    _install_redirect_transport(responder, monkeypatch, seen=seen)

    with pytest.raises(responder.LocalResponderTransportError):
        responder._stdlib_json_post_client(
            "http://127.0.0.1:11434/api/generate",
            {"prompt": "x"},
            1.0,
        )

    assert seen == ["http://127.0.0.1:11434/api/generate"]


def test_router_transport_rejects_external_endpoint_before_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responder = _load_module("spec137_router_boundary", ROUTER_RESPONDER)

    def fail_request(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("request construction must not occur for rejected endpoint")

    monkeypatch.setattr(responder.urllib.request, "Request", fail_request)
    with pytest.raises(responder.LocalResponderPolicyError):
        responder._stdlib_json_post_client(
            "http://example.invalid/api/generate",
            {"prompt": "x"},
            1.0,
        )


def test_micro_probe_owned_client_disables_proxy_and_redirect_followup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []
    captured_kwargs: list[dict[str, Any]] = []
    original_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(
            302,
            headers={"Location": "http://example.invalid/escape"},
            json={"message": {"content": "{}"}},
        )

    def client_factory(*args: Any, **kwargs: Any) -> httpx.Client:
        captured_kwargs.append(dict(kwargs))
        return original_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.invalid:8080")
    monkeypatch.setattr(micro_probe.httpx, "Client", client_factory)
    case = micro_probe.build_primary_probe_cases()[0]

    micro_probe.run_probe_case(
        case,
        model_name="local-test",
        endpoint_url="http://127.0.0.1:11434/api/chat",
        timeout_seconds=1.0,
        num_predict=16,
    )

    assert seen == ["http://127.0.0.1:11434/api/chat"]
    assert captured_kwargs
    assert captured_kwargs[0]["trust_env"] is False
    assert captured_kwargs[0]["follow_redirects"] is False


@pytest.mark.parametrize(
    "injected_client",
    [
        object(),
        {"proxy": "http://proxy.example.invalid:8080"},
        {"mounts": {"http://": object()}},
        {"transport": object()},
    ],
    ids=["arbitrary-client", "explicit-proxy", "proxy-mount", "custom-transport"],
)
def test_micro_probe_arbitrary_client_injection_surface_is_closed(injected_client: object) -> None:
    assert "client" not in inspect.signature(micro_probe.run_probe_case).parameters
    assert "client" not in inspect.signature(micro_probe.run_probe_suite).parameters
    case = micro_probe.build_primary_probe_cases()[0]
    with pytest.raises(TypeError):
        micro_probe.run_probe_case(
            case,
            model_name="local-test",
            endpoint_url="http://127.0.0.1:11434/api/chat",
            timeout_seconds=1.0,
            num_predict=16,
            client=injected_client,
        )
