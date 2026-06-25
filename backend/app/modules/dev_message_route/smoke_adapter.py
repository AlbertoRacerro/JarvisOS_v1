"""Dev-only adapter for the RouterPolicy message-route smoke path.

This module is a narrow import seam from backend code to the existing
evaluation/smoke script. It must not become a production dependency pattern.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from router_policy_local_responder import build_local_responder, call_local_ollama_generate_with_metadata  # noqa: E402
from router_policy_message_route_smoke import (  # noqa: E402
    MAX_MESSAGE_CHARS,
    _safe_cli_result,
    build_router_policy_input_from_message_for_smoke,
    run_message_route_smoke,
)


DEV_GATE_ENV = "JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE"
ASSUME_PUBLIC_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE"
ALLOW_LOCAL_RESPONDER_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER"
MODEL_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_MODEL"
ENDPOINT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_ENDPOINT"
TIMEOUT_ENV = "JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S"

DEFAULT_MODEL = "gemma3:4b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"
DEFAULT_TIMEOUT_S = 30.0
MAX_HISTORY_TURNS = 20
MAX_HISTORY_TURN_CHARS = MAX_MESSAGE_CHARS
LOCAL_CHAT_MAX_PROMPT_CHARS = 32000
LOCAL_CHAT_MAX_OUTPUT_CHARS = 16000


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def dev_message_route_enabled() -> bool:
    return _truthy_env(DEV_GATE_ENV)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timeout_from_env() -> float:
    raw = os.getenv(TIMEOUT_ENV)
    if raw is None or not raw.strip():
        return DEFAULT_TIMEOUT_S
    try:
        parsed = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_S
    return parsed if parsed > 0 else DEFAULT_TIMEOUT_S


def _smoke_result(
    *,
    executed: bool,
    reason: str,
    assume_public_simple_used: bool,
    use_phase_b_hints_used: bool = True,
) -> dict[str, Any]:
    return {
        "executed": executed,
        "reason": reason,
        "input_source": "dev_message_route_endpoint",
        "assume_public_simple_used": assume_public_simple_used,
        "use_phase_b_hints_used": use_phase_b_hints_used,
        "phase_b_source_kind": "stub",
        "phase_b_source_used": False,
    }


def safe_endpoint_response(result: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
    safe = _safe_cli_result(result)
    safe.pop("input_source", None)
    return {
        "trace_id": trace_id,
        "audit_ref": None,
        **safe,
    }


def internal_error_response(*, trace_id: str, error_type: str | None = None) -> dict[str, Any]:
    response = safe_endpoint_response(
        _smoke_result(
            executed=False,
            reason="internal_error",
            assume_public_simple_used=_truthy_env(ASSUME_PUBLIC_ENV),
        ),
        trace_id=trace_id,
    )
    if error_type:
        response["error_type"] = error_type
    return response


def disabled_response(*, trace_id: str) -> tuple[int, dict[str, Any]]:
    assume_public_simple = _truthy_env(ASSUME_PUBLIC_ENV)
    return 404, safe_endpoint_response(
        _smoke_result(
            executed=False,
            reason="dev_message_route_smoke_disabled",
            assume_public_simple_used=assume_public_simple,
        ),
        trace_id=trace_id,
    )


def validation_error_response(
    *,
    trace_id: str,
    error_type: str = "ValidationError",
    validation_error_count: int | None = None,
) -> dict[str, Any]:
    response = safe_endpoint_response(
        _smoke_result(
            executed=False,
            reason="validation_error",
            assume_public_simple_used=_truthy_env(ASSUME_PUBLIC_ENV),
        ),
        trace_id=trace_id,
    )
    response["error_type"] = error_type
    if validation_error_count is not None:
        response["validation_error_count"] = validation_error_count
    return response


def run_dev_message_route_smoke(
    *,
    message: str,
    run_local_responder: bool,
    trace_id: str,
) -> tuple[int, dict[str, Any]]:
    assume_public_simple = _truthy_env(ASSUME_PUBLIC_ENV)

    if not dev_message_route_enabled():
        return disabled_response(trace_id=trace_id)

    responder = None
    if run_local_responder:
        if not _truthy_env(ALLOW_LOCAL_RESPONDER_ENV):
            return 200, safe_endpoint_response(
                _smoke_result(
                    executed=False,
                    reason="local_responder_disabled",
                    assume_public_simple_used=assume_public_simple,
                ),
                trace_id=trace_id,
            )
        responder = build_local_responder(
            model=os.getenv(MODEL_ENV, DEFAULT_MODEL),
            endpoint=os.getenv(ENDPOINT_ENV, DEFAULT_ENDPOINT),
            timeout_s=_timeout_from_env(),
        )

    result = run_message_route_smoke(
        message,
        responder=responder,
        now=utc_now_iso(),
        assume_public_simple=assume_public_simple,
        use_phase_b_hints=True,
        phase_b_source_kind="stub",
    )
    return 200, safe_endpoint_response(result, trace_id=trace_id)


def build_dev_local_responder():
    model = os.getenv(MODEL_ENV, DEFAULT_MODEL)
    endpoint = os.getenv(ENDPOINT_ENV, DEFAULT_ENDPOINT)
    timeout_s = _timeout_from_env()

    def responder(prompt: str) -> str:
        metadata = call_local_ollama_generate_with_metadata(
            prompt,
            model=model,
            endpoint=endpoint,
            timeout_s=timeout_s,
            temperature=0.0,
            max_prompt_chars=LOCAL_CHAT_MAX_PROMPT_CHARS,
            max_output_chars=LOCAL_CHAT_MAX_OUTPUT_CHARS,
        )
        responder.last_metadata = metadata
        return metadata["response"]

    responder.last_metadata = None
    return responder


def scan_history_turn_for_context(content: str) -> str | None:
    try:
        input_obj = build_router_policy_input_from_message_for_smoke(
            content,
            now=utc_now_iso(),
            assume_public_simple=False,
        )
    except Exception:
        return "excluded_unknown_or_conservative"

    phase_a = input_obj.get("phase_a_signals")
    router_hint = input_obj.get("router_hint")
    action_hint = input_obj.get("action_hint")
    context_metadata = input_obj.get("context_metadata")
    if not isinstance(phase_a, dict) or not isinstance(router_hint, dict) or not isinstance(action_hint, dict):
        return "excluded_unknown_or_conservative"
    if not isinstance(context_metadata, dict):
        context_metadata = {}

    if phase_a.get("contains_secret_or_credential") is True:
        return "excluded_sensitive_or_secret"
    if phase_a.get("contains_raw_private_or_ip_sensitive_context") is True:
        return "excluded_private_or_ip_sensitive"
    if phase_a.get("mentions_external_provider_or_upload_intent") is True:
        return "excluded_external_provider_or_upload_intent"

    operational_flags = (
        context_metadata.get("operational_intent_detected") is True,
        action_hint.get("needs_terminal") is True,
        action_hint.get("needs_file_write") is True,
        action_hint.get("needs_memory_write") is True,
        action_hint.get("needs_provider_call") is True,
        router_hint.get("needs_file_context") is True,
        router_hint.get("needs_code_execution") is True,
        router_hint.get("needs_current_info") is True,
    )
    if any(operational_flags):
        return "excluded_operational_or_tool_intent"

    return None


def filter_clean_history(history: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    included: list[dict[str, str]] = []
    reason_counts: dict[str, int] = {}

    for turn in history:
        reason = scan_history_turn_for_context(turn["content"])
        if reason is None:
            included.append({"role": turn["role"], "content": turn["content"]})
        else:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    received = len(history)
    return included, {
        "history_turns_received": received,
        "history_turns_included": len(included),
        "history_turns_excluded": received - len(included),
        "excluded_reason_counts": reason_counts,
    }


def empty_context_filter() -> dict[str, Any]:
    return {
        "history_turns_received": 0,
        "history_turns_included": 0,
        "history_turns_excluded": 0,
        "excluded_reason_counts": {},
    }


def assemble_local_chat_prompt(*, clean_history: list[dict[str, str]], message: str) -> str:
    lines = [
        "You are a local dev assistant. Answer the current user message using only the clean conversation context below. Some previous turns may have been omitted by deterministic safety filtering.",
        "",
        "Clean conversation context:",
    ]
    if clean_history:
        for turn in clean_history:
            label = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{label}: {turn['content']}")
    else:
        lines.append("(none)")
    lines.extend(["", "Current user message:", message])
    return "\n".join(lines)


def select_prompt_history_within_budget(clean_history: list[dict[str, str]], message: str) -> tuple[list[dict[str, str]], int]:
    selected = list(clean_history)
    while selected and len(assemble_local_chat_prompt(clean_history=selected, message=message)) > LOCAL_CHAT_MAX_PROMPT_CHARS:
        selected.pop(0)
    omitted = len(clean_history) - len(selected)
    return selected, omitted


def add_chat_response_metadata(body: dict[str, Any], raw_result: dict[str, Any], responder: Any) -> dict[str, Any]:
    if body.get("executed") is not True:
        return body
    raw_response = raw_result.get("response")
    if not isinstance(raw_response, str):
        return body
    metadata = getattr(responder, "last_metadata", None)
    if not isinstance(metadata, dict):
        body["response"] = raw_response
        body["response_may_be_truncated"] = True
        body["response_truncated_false_semantics"] = "not_sliced_by_jarvisos_not_completion_guarantee"
        return body
    response = metadata.get("response")
    if not isinstance(response, str):
        response = raw_response
    body["response"] = response
    body["response_truncated"] = metadata.get("response_truncated") is True
    body["response_char_count_returned"] = metadata.get("response_char_count_returned", len(response))
    body["response_char_limit"] = metadata.get("response_char_limit", LOCAL_CHAT_MAX_OUTPUT_CHARS)
    body["response_limit_source"] = metadata.get("response_limit_source", "local_responder_max_output_chars")
    body["response_truncated_false_semantics"] = "not_sliced_by_jarvisos_not_completion_guarantee"
    return body


def run_dev_local_chat(
    *,
    message: str,
    history: list[dict[str, str]],
    run_local_responder: bool,
    trace_id: str,
) -> tuple[int, dict[str, Any]]:
    if not dev_message_route_enabled():
        return disabled_response(trace_id=trace_id)

    if not run_local_responder:
        result = run_message_route_smoke(
            message,
            responder=None,
            now=utc_now_iso(),
            assume_public_simple=_truthy_env(ASSUME_PUBLIC_ENV),
            use_phase_b_hints=True,
            phase_b_source_kind="stub",
        )
        body = safe_endpoint_response(result, trace_id=trace_id)
        body["context_filter"] = empty_context_filter()
        return 200, body

    if not _truthy_env(ALLOW_LOCAL_RESPONDER_ENV):
        body = safe_endpoint_response(
            _smoke_result(
                executed=False,
                reason="local_responder_disabled",
                assume_public_simple_used=_truthy_env(ASSUME_PUBLIC_ENV),
            ),
            trace_id=trace_id,
        )
        body["context_filter"] = empty_context_filter()
        return 200, body

    current_gate = run_message_route_smoke(
        message,
        responder=None,
        now=utc_now_iso(),
        assume_public_simple=_truthy_env(ASSUME_PUBLIC_ENV),
        use_phase_b_hints=True,
        phase_b_source_kind="stub",
    )
    if current_gate.get("reason") != "local_responder_missing":
        body = safe_endpoint_response(current_gate, trace_id=trace_id)
        body["context_filter"] = empty_context_filter()
        return 200, body

    clean_history, context_filter = filter_clean_history(history)
    prompt_history, prompt_omitted = select_prompt_history_within_budget(clean_history, message)
    context_filter["history_turns_prompted"] = len(prompt_history)
    context_filter["history_turns_omitted_for_prompt_budget"] = prompt_omitted
    context_filter["prompt_char_limit"] = LOCAL_CHAT_MAX_PROMPT_CHARS
    prompt = assemble_local_chat_prompt(clean_history=prompt_history, message=message)
    responder = build_dev_local_responder()
    response = responder(prompt)
    result = {
        "executed": True,
        "reason": "local_answer",
        "response": response,
        "decision": current_gate.get("decision"),
        "input_source": current_gate.get("input_source", "smoke_builder"),
        "assume_public_simple_used": current_gate.get("assume_public_simple_used") is True,
        "use_phase_b_hints_used": current_gate.get("use_phase_b_hints_used") is True,
        "phase_b_source_kind": current_gate.get("phase_b_source_kind", "stub"),
        "phase_b_source_used": current_gate.get("phase_b_source_used") is True,
    }
    body = safe_endpoint_response(result, trace_id=trace_id)
    body["context_filter"] = context_filter
    add_chat_response_metadata(body, result, responder)
    return 200, body
