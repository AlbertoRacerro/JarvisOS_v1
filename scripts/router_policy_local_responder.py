"""Approved localhost-only Ollama responder adapter for RouterPolicy A4.

The builder is side-effect free. Only the returned callable may perform the
localhost HTTP request, and only when it is explicitly injected by caller code.
"""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any


DEFAULT_MODEL = "qwen3:8b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"
LOCALHOST_HOSTS = {"127.0.0.1", "localhost", "::1"}
TIMING_KEYS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


class LocalResponderError(Exception):
    """Base class for local responder adapter failures."""


class LocalResponderPolicyError(LocalResponderError):
    """Raised when local responder policy or bounds are violated."""


class LocalResponderTransportError(LocalResponderError):
    """Raised when localhost transport fails."""


class LocalResponderResponseError(LocalResponderError):
    """Raised when localhost response content is malformed."""


def _validate_endpoint(endpoint: str) -> None:
    if not isinstance(endpoint, str):
        raise LocalResponderPolicyError("endpoint must be a string")
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http":
        raise LocalResponderPolicyError("endpoint must use http")
    if parsed.hostname not in LOCALHOST_HOSTS:
        raise LocalResponderPolicyError("endpoint host must be localhost")
    if parsed.username is not None or parsed.password is not None:
        raise LocalResponderPolicyError("endpoint must not include credentials")
    if parsed.path != "/api/generate":
        raise LocalResponderPolicyError("endpoint path must be /api/generate")
    if parsed.query or parsed.fragment:
        raise LocalResponderPolicyError("endpoint must not include query or fragment")


def _validate_static_params(
    *,
    model: str,
    endpoint: str,
    timeout_s: float,
    temperature: float,
    max_prompt_chars: int,
    max_output_chars: int,
    client,
) -> None:
    if not isinstance(model, str) or not model:
        raise LocalResponderPolicyError("model must be a non-empty string")
    _validate_endpoint(endpoint)
    if not isinstance(timeout_s, (int, float)) or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise LocalResponderPolicyError("timeout_s must be finite and positive")
    if not isinstance(max_prompt_chars, int) or max_prompt_chars <= 0:
        raise LocalResponderPolicyError("max_prompt_chars must be a positive integer")
    if not isinstance(max_output_chars, int) or max_output_chars <= 0:
        raise LocalResponderPolicyError("max_output_chars must be a positive integer")
    if temperature != 0.0:
        raise LocalResponderPolicyError("temperature must be 0.0")
    if client is not None and not callable(client):
        raise LocalResponderPolicyError("client must be callable")


def _validate_prompt(prompt: str, max_prompt_chars: int) -> None:
    if not isinstance(prompt, str):
        raise LocalResponderPolicyError("prompt must be a string")
    if len(prompt) > max_prompt_chars:
        raise LocalResponderPolicyError("prompt exceeds max_prompt_chars")


def _normalize_num_predict(num_predict: Any) -> int | None:
    if not isinstance(num_predict, int) or isinstance(num_predict, bool) or num_predict <= 0:
        return None
    return num_predict


def _build_generate_payload(
    *,
    model: str,
    prompt: str,
    temperature: float,
    keep_alive: str | None,
    num_predict: int | None,
) -> dict[str, Any]:
    options: dict[str, Any] = {
        "temperature": 0,
    }
    normalized_num_predict = _normalize_num_predict(num_predict)
    if normalized_num_predict is not None:
        options["num_predict"] = normalized_num_predict

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    return payload


def _extract_timing_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_duration_ns": raw.get("total_duration"),
        "load_duration_ns": raw.get("load_duration"),
        "prompt_eval_count": raw.get("prompt_eval_count"),
        "prompt_eval_duration_ns": raw.get("prompt_eval_duration"),
        "eval_count": raw.get("eval_count"),
        "eval_duration_ns": raw.get("eval_duration"),
    }


def _raw_has_timing_metadata(raw: dict[str, Any]) -> bool:
    return any(key in raw for key in TIMING_KEYS)


def _stdlib_json_post_client(endpoint: str, payload: dict, timeout_s: float) -> dict:
    encoded = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            status = getattr(response, "status", response.getcode())
            if status < 200 or status >= 300:
                raise LocalResponderTransportError(f"localhost Ollama returned HTTP {status}")
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise LocalResponderTransportError(f"localhost Ollama returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LocalResponderTransportError(str(exc)) from exc
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LocalResponderResponseError("localhost Ollama returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise LocalResponderResponseError("localhost Ollama response must be an object")
    return decoded


def _call_local_ollama_generate_result(
    prompt: str,
    *,
    model: str,
    endpoint: str,
    timeout_s: float,
    temperature: float,
    max_prompt_chars: int,
    max_output_chars: int,
    keep_alive: str | None = None,
    num_predict: int | None = None,
    client=None,
) -> dict[str, Any]:
    _validate_static_params(
        model=model,
        endpoint=endpoint,
        timeout_s=timeout_s,
        temperature=temperature,
        max_prompt_chars=max_prompt_chars,
        max_output_chars=max_output_chars,
        client=client,
    )
    _validate_prompt(prompt, max_prompt_chars)
    payload = _build_generate_payload(
        model=model,
        prompt=prompt,
        temperature=temperature,
        keep_alive=keep_alive,
        num_predict=num_predict,
    )
    post_client = client or _stdlib_json_post_client
    raw = post_client(endpoint, payload, float(timeout_s))
    if not isinstance(raw, dict):
        raise LocalResponderResponseError("localhost Ollama response must be an object")
    response_text = raw.get("response")
    if not isinstance(response_text, str):
        raise LocalResponderResponseError("localhost Ollama response missing string response")
    bounded = response_text[:max_output_chars]
    result = {
        "response": bounded,
        "response_truncated": len(response_text) > max_output_chars,
        "response_char_count_returned": len(bounded),
        "response_char_limit": max_output_chars,
        "response_limit_source": "local_responder_max_output_chars",
    }
    if _raw_has_timing_metadata(raw):
        result["local_responder_timing"] = _extract_timing_metadata(raw)
    return result


def call_local_ollama_generate(
    prompt: str,
    *,
    model: str,
    endpoint: str,
    timeout_s: float,
    temperature: float,
    max_prompt_chars: int,
    max_output_chars: int,
    keep_alive: str | None = None,
    num_predict: int | None = None,
    client=None,
) -> str:
    """Call localhost Ollama /api/generate and return bounded response text."""

    return _call_local_ollama_generate_result(
        prompt,
        model=model,
        endpoint=endpoint,
        timeout_s=timeout_s,
        temperature=temperature,
        max_prompt_chars=max_prompt_chars,
        max_output_chars=max_output_chars,
        keep_alive=keep_alive,
        num_predict=num_predict,
        client=client,
    )["response"]


def call_local_ollama_generate_with_metadata(
    prompt: str,
    *,
    model: str,
    endpoint: str,
    timeout_s: float,
    temperature: float,
    max_prompt_chars: int,
    max_output_chars: int,
    keep_alive: str | None = None,
    num_predict: int | None = None,
    client=None,
) -> dict[str, Any]:
    """Call localhost Ollama /api/generate and return bounded text plus slice metadata."""

    return _call_local_ollama_generate_result(
        prompt,
        model=model,
        endpoint=endpoint,
        timeout_s=timeout_s,
        temperature=temperature,
        max_prompt_chars=max_prompt_chars,
        max_output_chars=max_output_chars,
        keep_alive=keep_alive,
        num_predict=num_predict,
        client=client,
    )


def build_local_responder(
    *,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout_s: float = 30.0,
    temperature: float = 0.0,
    max_prompt_chars: int = 12000,
    max_output_chars: int = 4000,
    keep_alive: str | None = None,
    num_predict: int | None = None,
    client=None,
) -> Callable[[str], str]:
    """Build a side-effect-free local responder callable."""

    _validate_static_params(
        model=model,
        endpoint=endpoint,
        timeout_s=timeout_s,
        temperature=temperature,
        max_prompt_chars=max_prompt_chars,
        max_output_chars=max_output_chars,
        client=client,
    )

    def responder(prompt: str) -> str:
        return call_local_ollama_generate(
            prompt,
            model=model,
            endpoint=endpoint,
            timeout_s=timeout_s,
            temperature=temperature,
            max_prompt_chars=max_prompt_chars,
            max_output_chars=max_output_chars,
            keep_alive=keep_alive,
            num_predict=num_predict,
            client=client,
        )

    return responder
