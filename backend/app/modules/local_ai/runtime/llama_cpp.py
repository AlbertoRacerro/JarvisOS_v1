from __future__ import annotations

import hashlib
import json
import os
import platform
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from app.core.paths import build_paths

_CONFIG_ENV = "JARVISOS_LLAMACPP_CONFIG"
_HASH_CACHE: dict[tuple[str, int, int], str] = {}
_HASH_LOCK = threading.Lock()


@dataclass(frozen=True)
class LlamaCppRuntimeConfig:
    binary_path: str = ""
    model_path: str = ""
    model_sha256: str = ""
    model_id: str = "qwen3.8-27b-q4kxl"
    host: str = "127.0.0.1"
    port: int = 8080
    ctx_size: int = 8192
    n_gpu_layers: int = -1
    extra_args: tuple[str, ...] = ()
    pinned_build_id: str = ""
    manage: bool = False
    timeout_s: float = 2.0

    @property
    def origin(self) -> str:
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"http://{host}:{self.port}"

    @property
    def base_url(self) -> str:
        return f"{self.origin}/v1"


@lru_cache(maxsize=1)
def llama_cpp_runtime_config() -> LlamaCppRuntimeConfig:
    path = Path(os.getenv(_CONFIG_ENV, build_paths().data_root / "settings" / "llama_cpp.json"))
    try:
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError):
        raw = {}
    def get(name: str, env: str, default: Any) -> Any:
        value = os.getenv(env)
        return value if value is not None else raw.get(name, default)
    args = get("extra_args", "JARVISOS_LLAMACPP_EXTRA_ARGS", [])
    if isinstance(args, str):
        args = args.split()
    return LlamaCppRuntimeConfig(
        binary_path=str(get("binary_path", "JARVISOS_LLAMACPP_BINARY", "")),
        model_path=str(get("model_path", "JARVISOS_LLAMACPP_MODEL", "")),
        model_sha256=str(get("model_sha256", "JARVISOS_LLAMACPP_MODEL_SHA256", "")),
        model_id=str(get("model_id", "JARVISOS_LLAMACPP_MODEL_ID", "qwen3.8-27b-q4kxl")),
        host=str(get("host", "JARVISOS_LLAMACPP_HOST", "127.0.0.1")),
        port=int(get("port", "JARVISOS_LLAMACPP_PORT", 8080)),
        ctx_size=int(get("ctx_size", "JARVISOS_LLAMACPP_CTX_SIZE", 8192)),
        n_gpu_layers=int(get("n_gpu_layers", "JARVISOS_LLAMACPP_N_GPU_LAYERS", -1)),
        extra_args=tuple(str(arg) for arg in args) if isinstance(args, list) else (),
        pinned_build_id=str(get("pinned_build_id", "JARVISOS_LLAMACPP_BUILD_ID", "")),
        manage=str(get("manage", "JARVISOS_MANAGE_LLAMACPP", "false")).lower() in {"1", "true", "yes"},
        timeout_s=float(get("timeout_s", "JARVISOS_LLAMACPP_TIMEOUT_S", 2.0)),
    )


def clear_llama_cpp_config_cache() -> None:
    llama_cpp_runtime_config.cache_clear()


def validate_loopback_host(host: str) -> str | None:
    if os.getenv("WSL_DISTRO_NAME") and host not in {"127.0.0.1", "localhost", "::1"}:
        return "LLAMACPP_UNSUPPORTED_WINDOWS_WSL_TOPOLOGY"
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return "LLAMACPP_NON_LOOPBACK_ENDPOINT"
    if platform.system() == "Windows" and os.getenv("WSL_DISTRO_NAME"):
        return "LLAMACPP_UNSUPPORTED_WINDOWS_WSL_TOPOLOGY"
    return None


def cached_model_sha256(path: str) -> str | None:
    try:
        stat = Path(path).stat()
    except OSError:
        return None
    key = (str(Path(path).resolve()), stat.st_size, stat.st_mtime_ns)
    with _HASH_LOCK:
        if key in _HASH_CACHE:
            return _HASH_CACHE[key]
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    result = digest.hexdigest()
    with _HASH_LOCK:
        _HASH_CACHE.clear()
        _HASH_CACHE[key] = result
    return result


def request_model_sha256(path: str) -> str | None:
    """Return a cached digest and schedule a cold hash off the status request path."""
    try:
        stat = Path(path).stat()
    except OSError:
        return None
    key = (str(Path(path).resolve()), stat.st_size, stat.st_mtime_ns)
    with _HASH_LOCK:
        cached = _HASH_CACHE.get(key)
        if cached is not None:
            return cached
        if key in _HASH_PENDING:
            return None
        _HASH_PENDING.add(key)
    thread = threading.Thread(target=_hash_model, args=(path, key), daemon=True)
    thread.start()
    return None


_HASH_PENDING: set[tuple[str, int, int]] = set()


def _hash_model(path: str, key: tuple[str, int, int]) -> None:
    try:
        cached_model_sha256(path)
    except OSError:
        pass
    finally:
        with _HASH_LOCK:
            _HASH_PENDING.discard(key)


class LlamaCppRuntimeOwner:
    """One process owner for a configured local llama-server."""

    def __init__(self, config: LlamaCppRuntimeConfig | None = None, *, popen: Any = subprocess.Popen,
                 client_factory: Any = httpx.Client, sleep: Any = time.sleep,
                 kill_group: Any = os.killpg) -> None:
        self.config = config or llama_cpp_runtime_config()
        self._popen = popen
        self._client_factory = client_factory
        self._sleep = sleep
        self._kill_group = kill_group
        self._process: Any | None = None
        self._lock = threading.RLock()

    def status(self) -> dict[str, Any]:
        config = self.config
        reason = validate_loopback_host(config.host)
        row: dict[str, Any] = {
            "backend": "llama.cpp", "configured": bool(config.binary_path and config.model_path),
            "runtime_reachable": False, "model_installed": bool(config.model_path and Path(config.model_path).is_file()),
            "model_loaded": False, "reason_code": reason,
            "message": "Configure a llama-server binary and GGUF model in data-root/settings/llama_cpp.json.",
            "build_id": config.pinned_build_id or None, "model_file": config.model_path or None,
            "configured_sha256": config.model_sha256 or None,
            "model_sha256": None, "pid": None, "ctx_size": config.ctx_size,
            "n_gpu_layers": config.n_gpu_layers, "vram_bytes": None, "ram_bytes": None,
            "request_slots": None, "spawned_by_jarvis": self._process is not None,
        }
        if reason:
            row["message"] = (
                "Windows-to-WSL llama-server endpoints are unsupported; run Jarvis and llama-server in the same network namespace."
                if reason == "LLAMACPP_UNSUPPORTED_WINDOWS_WSL_TOPOLOGY"
                else "llama-server must use an HTTP loopback address (127.0.0.1, localhost, or ::1)."
            )
            return row
        if config.model_path:
            # A configured digest is authoritative operator evidence. In particular,
            # never re-hash a multi-gigabyte model on the status path when supplied.
            row["model_sha256"] = config.model_sha256 or request_model_sha256(config.model_path)
        if self._process is not None:
            row["pid"] = getattr(self._process, "pid", None)
        if not config.binary_path or not config.model_path:
            row["reason_code"] = row["reason_code"] or "LLAMACPP_NOT_CONFIGURED"
            return row
        try:
            with self._client_factory(timeout=config.timeout_s) as client:
                health = client.get(f"{config.origin}/health")
                row["runtime_reachable"] = health.is_success
                props = client.get(f"{config.origin}/props")
                props.raise_for_status()
                data = props.json()
                row["build_id"] = data.get("build_id") or row["build_id"]
                row["ctx_size"] = data.get("default_generation_settings", {}).get("n_ctx") or row["ctx_size"]
                models_response = client.get(f"{config.origin}/v1/models")
                models_response.raise_for_status()
                model_rows = models_response.json().get("data", [])
                expected = config.model_id
                model_ids = {item.get("id") for item in model_rows if isinstance(item, dict)}
                row["model_loaded"] = bool(model_ids.intersection({expected, Path(config.model_path).name}))
                slots = client.get(f"{config.origin}/slots")
                if slots.is_success and isinstance(slots.json(), list):
                    row["request_slots"] = len(slots.json())
                row["reason_code"] = None if row["model_loaded"] else "LLAMACPP_MODEL_MISMATCH"
                row["message"] = "llama-server is reachable and serving its configured model." if row["model_loaded"] else "llama-server is reachable, but its loaded model does not match the configured model."
        except Exception:
            row["reason_code"] = "LLAMACPP_RUNTIME_UNREACHABLE"
            row["message"] = "llama-server is not reachable at the configured loopback address."
        return row

    def start(self) -> dict[str, Any]:
        with self._lock:
            existing = self.status()
            if existing["runtime_reachable"]:
                return existing
            reason = validate_loopback_host(self.config.host)
            if reason:
                existing["reason_code"] = reason
                return existing
            if not self.config.binary_path or not self.config.model_path:
                existing["reason_code"] = "LLAMACPP_NOT_CONFIGURED"
                return existing
            if not Path(self.config.binary_path).is_file() or not Path(self.config.model_path).is_file():
                existing["reason_code"] = "LLAMACPP_FILE_MISSING"
                existing["message"] = "Configured llama-server binary or GGUF file does not exist."
                return existing
            args = [self.config.binary_path, "--model", self.config.model_path, "--alias", self.config.model_id, "--host", self.config.host,
                    "--port", str(self.config.port), "--ctx-size", str(self.config.ctx_size),
                    "--n-gpu-layers", str(self.config.n_gpu_layers), *self.config.extra_args]
            self._process = self._popen(args, start_new_session=(os.name != "nt"))
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                snapshot = self.status()
                if snapshot["runtime_reachable"]:
                    return snapshot
                self._sleep(0.1)
            return self.status()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            if self._process is not None:
                process, self._process = self._process, None
                try:
                    if os.name != "nt":
                        self._kill_group(process.pid, signal.SIGTERM)
                    else:
                        process.terminate()
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
            return self.status()

    def restart(self) -> dict[str, Any]:
        self.stop()
        return self.start()


_OWNER: LlamaCppRuntimeOwner | None = None
_OWNER_LOCK = threading.Lock()


def get_llama_cpp_runtime_owner() -> LlamaCppRuntimeOwner:
    global _OWNER
    with _OWNER_LOCK:
        if _OWNER is None:
            _OWNER = LlamaCppRuntimeOwner()
        return _OWNER
