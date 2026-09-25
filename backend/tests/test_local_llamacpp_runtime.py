from __future__ import annotations

import hashlib
import threading

import httpx
import pytest

from app.modules.ai.contracts import AIRequest, AITaskType
from app.modules.ai.provider_registry import load_default_provider_registry
from app.modules.ai.providers import local_llamacpp_adapter as adapter_module
from app.modules.ai.providers.local_llamacpp_adapter import LocalLlamaCppAdapter
from app.modules.ai.thread_routes import _llamacpp_route_availability
from app.modules.local_ai.runtime.llama_cpp import (
    LlamaCppRuntimeConfig,
    LlamaCppRuntimeOwner,
    cached_model_sha256,
    request_model_sha256,
    validate_loopback_host,
)


def _config(**overrides: object) -> LlamaCppRuntimeConfig:
    values: dict[str, object] = {
        "binary_path": "/fake/llama-server", "model_path": "/fake/model.gguf",
        "host": "127.0.0.1", "port": 8080, "ctx_size": 4096, "n_gpu_layers": 12,
    }
    values.update(overrides)
    return LlamaCppRuntimeConfig(**values)  # type: ignore[arg-type]


def test_adapter_is_loopback_only_and_sends_route_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, object] = {}
    monkeypatch.setattr(adapter_module, "llama_cpp_runtime_config", lambda: _config())

    def respond(request: httpx.Request) -> httpx.Response:
        sent.update(httpx.QueryParams(request.url.query))
        import json
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {
            "content": "analysis <think>secret reasoning</think> answer",
            "reasoning_content": "private thought", "finish_reason": None,
        }, "finish_reason": "stop"}], "usage": {
            "prompt_tokens": 12, "completion_tokens": 9,
            "completion_tokens_details": {"reasoning_tokens": 4},
        }})

    transport = httpx.MockTransport(respond)
    adapter = LocalLlamaCppAdapter(client_factory=lambda: httpx.Client(transport=transport))
    result = adapter.complete(AIRequest(task_type=AITaskType.synthesis, prompt="hello", max_output_tokens=77))
    assert sent["max_tokens"] == 77
    assert result.provider_id == "local_llamacpp"
    assert result.finish_reason == "stop"
    assert result.text == "analysis  answer"
    assert result.raw_provider_metadata["reasoning_tokens"] == 4
    assert result.usage.output_tokens == 9

    monkeypatch.setattr(adapter_module, "llama_cpp_runtime_config", lambda: _config(host="192.168.1.2"))
    with pytest.raises(ValueError, match="loopback"):
        adapter.complete(AIRequest(task_type=AITaskType.synthesis, prompt="hello"))


@pytest.mark.parametrize(("finish", "expected"), [("stop", "stop"), ("length", "length"), ("error", "error")])
def test_finish_reason_mapping(finish: str, expected: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter_module, "llama_cpp_runtime_config", lambda: _config())
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={
        "choices": [{"message": {"content": "answer"}, "finish_reason": finish}], "usage": {},
    }))
    result = LocalLlamaCppAdapter(client_factory=lambda: httpx.Client(transport=transport)).complete(
        AIRequest(task_type=AITaskType.synthesis, prompt="hello")
    )
    assert result.finish_reason == expected
    assert (result.error is not None) == (expected == "error")


def test_loopback_validation_and_digest_cache(tmp_path) -> None:
    assert validate_loopback_host("127.0.0.1") is None
    assert validate_loopback_host("10.0.0.1") == "LLAMACPP_NON_LOOPBACK_ENDPOINT"
    model = tmp_path / "model.gguf"
    model.write_bytes(b"small deterministic fixture")
    expected = hashlib.sha256(model.read_bytes()).hexdigest()
    assert cached_model_sha256(str(model)) == expected
    assert cached_model_sha256(str(model)) == expected


def test_status_digest_hashing_runs_off_request_thread(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    model = tmp_path / "large.gguf"
    model.write_bytes(b"deferred")
    completed = threading.Event()
    caller = threading.get_ident()
    called_from: list[int] = []

    def slow_hash(path: str) -> str:
        called_from.append(threading.get_ident())
        completed.set()
        return "digest"

    monkeypatch.setattr("app.modules.local_ai.runtime.llama_cpp.cached_model_sha256", slow_hash)
    assert request_model_sha256(str(model)) is None
    assert completed.wait(1)
    assert called_from[0] != caller


@pytest.mark.parametrize(
    ("state", "reachable", "installed", "loaded", "reason"),
    [
        ({"configured": True, "runtime_reachable": False, "model_installed": False,
          "model_loaded": False, "reason_code": "LLAMACPP_RUNTIME_UNREACHABLE", "message": "down"},
         False, False, False, "LLAMACPP_RUNTIME_UNREACHABLE"),
        ({"configured": True, "runtime_reachable": True, "model_installed": True,
          "model_loaded": False, "reason_code": "LLAMACPP_MODEL_MISMATCH", "message": "mismatch"},
         True, True, False, "LLAMACPP_MODEL_MISMATCH"),
        ({"configured": True, "runtime_reachable": True, "model_installed": True,
          "model_loaded": True, "reason_code": None, "message": "ready"},
         True, True, True, None),
    ],
)
def test_availability_matrix(monkeypatch: pytest.MonkeyPatch, state, reachable, installed, loaded, reason) -> None:
    class Owner:
        def status(self):
            return state

    monkeypatch.setattr(
        "app.modules.local_ai.runtime.llama_cpp.get_llama_cpp_runtime_owner", lambda: Owner()
    )
    status = _llamacpp_route_availability("local:llamacpp", "qwen3.8-27b-q4kxl")
    assert status.configured is True
    assert status.runtime_reachable is reachable
    assert status.model_installed is installed
    assert status.model_loaded is loaded
    assert status.reason_code == reason


def test_registry_classifies_llamacpp_as_local_compute() -> None:
    registry = load_default_provider_registry()
    provider = registry.providers["local_llamacpp"]
    binding = registry.bindings["local:llamacpp"]
    assert provider.execution_class == "local_compute"
    assert provider.requires_network is False
    assert provider.api_key_ref is None
    assert binding.provider_id == "local_llamacpp"
    assert binding.max_output_tokens == 2048


class _FakeProcess:
    pid = 332211
    def wait(self, timeout: float) -> int:
        return 0
    def kill(self) -> None:
        pass


def test_lifecycle_start_stop_restart_and_existing_instance(tmp_path) -> None:
    binary = tmp_path / "llama-server"
    model = tmp_path / "model.gguf"
    binary.write_text("fake executable")
    model.write_bytes(b"fake model")
    online = False
    spawn_calls: list[list[str]] = []
    killed: list[tuple[int, int]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/health"):
            return httpx.Response(200 if online else 503)
        if request.url.path.endswith("/props"):
            return httpx.Response(200, json={"build_id": "fake-build", "default_generation_settings": {"n_ctx": 4096}})
        if request.url.path.endswith("/v1/models"):
            return httpx.Response(200, json={"data": [{"id": "qwen3.8-27b-q4kxl"}]})
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(respond)
    def popen(args: list[str], **_: object) -> _FakeProcess:
        nonlocal online
        online = True
        spawn_calls.append(args)
        return _FakeProcess()
    owner = LlamaCppRuntimeOwner(
        _config(binary_path=str(binary), model_path=str(model)), popen=popen,
        client_factory=lambda **kwargs: httpx.Client(transport=transport, **kwargs),
        sleep=lambda _: None, kill_group=lambda pid, sig: killed.append((pid, sig)),
    )
    assert owner.start()["model_loaded"] is True
    assert len(spawn_calls) == 1
    assert owner.start()["runtime_reachable"] is True
    assert len(spawn_calls) == 1
    owner.stop()
    assert killed
    online = False
    owner.restart()
    assert len(spawn_calls) == 2

    existing = LlamaCppRuntimeOwner(
        _config(binary_path=str(binary), model_path=str(model)), popen=lambda *_args, **_kwargs: pytest.fail("duplicate spawn"),
        client_factory=lambda **kwargs: httpx.Client(transport=transport, **kwargs),
    )
    online = True
    assert existing.start()["runtime_reachable"] is True
