"""Real-message RouterPolicy local-route smoke bridge for A5.

A5 is not a production Phase A/B normalizer. When no complete production
message normalizer exists, this module uses a conservative smoke-only fallback
builder. Arbitrary messages do not become executable unless
assume_public_simple=True and deterministic hard-gate signals do not fire.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from typing import Any

import local_policy_gate_overlay_probe as policy_overlay
from router_policy_local_responder import LocalResponderError, build_local_responder
from router_policy_local_route_probe import run_local_route


MAX_MESSAGE_CHARS = 12000
MAX_CLI_RESPONSE_CHARS = 1000

_RUN_LOCAL_ROUTE = run_local_route
_BUILD_LOCAL_RESPONDER = build_local_responder
_APPLY_POLICY_OVERLAY = policy_overlay.apply_policy_overlay

TOP_LEVEL_REQUIRED = {
    "message_text",
    "phase_a_signals",
    "phase_b_soft_proposal",
    "router_hint",
    "action_hint",
    "user_policy",
    "provider_policy",
    "budget_policy",
    "context_metadata",
}
PHASE_A_BOOL_FIELDS = {
    "contains_secret_or_credential",
    "contains_raw_private_or_ip_sensitive_context",
    "mentions_external_provider_or_upload_intent",
    "external_provider_allowed",
    "clarification_required",
    "requires_manual_review",
}
ACTION_BOOL_FIELDS = {
    "modifies_state",
    "needs_terminal",
    "needs_file_write",
    "needs_memory_write",
    "needs_provider_call",
}
ROUTER_BOOL_FIELDS = {
    "needs_reasoning",
    "needs_current_info",
    "needs_file_context",
    "needs_code_execution",
    "needs_scientific_depth",
}
USER_POLICY_BOOL_FIELDS = {
    "external_routing_enabled",
    "external_requires_confirmation",
    "allow_persistent_auto_allow",
}
CONTEXT_BOOL_FIELDS = {
    "attached_files_present",
    "conversation_context_available",
}
HARD_REASON_CODES = {
    "low_risk",
    "secret_or_credential",
    "local_only_sensitive_context",
    "provider_or_upload_intent",
    "clarification_required",
    "manual_review_required",
    "unknown_sensitivity",
    "redaction_required",
}
SENSITIVITY_BUCKETS = {"public", "internal", "sensitive", "secret", "unknown"}
ROUTER_COMPLEXITY = {"low", "medium", "high", "unknown"}
CONFIDENCE_VALUES = {"low", "medium", "high", "unknown"}
ACTION_TYPES = {
    "answer",
    "local_model_call",
    "provider_call",
    "browser_search",
    "file_write",
    "terminal_command",
    "memory_write",
    "tool_call",
    "mcp_call",
    "unknown",
}
SIDE_EFFECT_LEVELS = {"none", "low", "medium", "high", "irreversible", "unknown"}
REVERSIBILITY_VALUES = {"reversible", "partially_reversible", "irreversible", "unknown"}
ENVIRONMENT_TYPES = {
    "chat",
    "file_system",
    "terminal",
    "codebase",
    "browser",
    "mcp",
    "os",
    "provider_api",
    "memory_store",
    "unknown",
}
STATE_SCOPES = {
    "none",
    "local_file",
    "repo",
    "memory",
    "external_provider",
    "os",
    "browser",
    "mcp",
    "unknown",
}
TIERS = {"LOCAL_ONLY", "LOCAL_FAST", "CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM", "FRONTIER"}
OVERLAY_REASON_MAP = {
    "low_risk": "low_risk",
    "secret_or_credential": "secret_or_credential",
    "provider_or_upload_intent": "provider_or_upload_intent",
    "clarification_needed": "clarification_required",
    "memory_boundary_or_write_authority": "manual_review_required",
    "retrieval_or_source_request": "manual_review_required",
    "contradiction_or_superseded": "manual_review_required",
}
OPERATIONAL_INTENT_PATTERNS = {
    "tool_mcp": [
        r"\buse\s+mcp\b",
        r"\bmcp\s+call\b",
        r"\bmcp_call\b",
        r"\bcall\s+a\s+tool\b",
        r"\buse\s+a\s+tool\b",
        r"\buse\s+tool\b",
        r"\btool\s+call\b",
        r"\binvoke\s+tool\b",
        r"\bexecute\s+tool\b",
    ],
    "terminal": [
        r"\brun\s+command\b",
        r"\bexecute\s+command\b",
        r"\bterminal\b",
        r"\bpowershell\b",
        r"\bshell\b",
        r"\bcmd\.exe\b",
        r"\bsubprocess\b",
        r"\bpopen\b",
        r"\bos\.system\b",
        r"\bbash\b",
    ],
    "memory_write": [
        r"\bwrite\s+to\s+memory\b",
        r"\bsave\s+to\s+memory\b",
        r"\bstore\s+(?:this\s+)?in\s+memory\b",
        r"\bremember\s+this\b",
        r"\badd\s+to\s+memory\b",
        r"\bmemory\s+write\b",
    ],
    "file_retrieval": [
        r"\bread\s+file\b",
        r"\bopen\s+file\b",
        r"\bread\s+local\s+file\b",
        r"\bretrieve\s+file\b",
        r"\bload\s+file\b",
        r"\baccess\s+file\b",
        r"[a-z]:\\",
        r"/home/",
        r"\.env\b",
        r"\bcredentials\b",
    ],
    "browser_search": [
        r"\bbrowse\b",
        r"\bopen\s+browser\b",
        r"\bsearch\s+web\b",
        r"\bweb\s+search\b",
        r"\bgoogle\s+this\b",
        r"\blook\s+it\s+up\s+online\b",
    ],
    "provider_upload": [
        r"\bupload\b.{0,40}\bto\s+openai\b",
        r"\bsend\b.{0,40}\bto\s+openai\b",
        r"\bupload\b.{0,40}\bto\s+gemini\b",
        r"\bsend\b.{0,40}\bto\s+gemini\b",
        r"\bsend\b.{0,40}\bto\s+claude\b",
        r"\bupload\s+to\s+openai\b",
        r"\bsend\s+to\s+openai\b",
        r"\bupload\s+to\s+gemini\b",
        r"\bsend\s+to\s+gemini\b",
        r"\bexternal\s+provider\b",
        r"\bhosted\s+api\b",
        r"\banthropic\b",
        r"\bclaude\b",
        r"\bgrok\b",
        r"\bopenrouter\b",
        r"\bmistral\b",
        r"\bdeepseek\b",
        r"\bqwen\s+api\b",
    ],
}


def _base_router_input(message_text: str) -> dict[str, Any]:
    return {
        "message_text": message_text,
        "phase_a_signals": {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "external_provider_allowed": False,
            "clarification_required": False,
            "hard_reason_codes": ["unknown_sensitivity", "manual_review_required"],
            "sensitivity_bucket_proposal": "unknown",
            "requires_manual_review": True,
            "source_policy_for_future_retrieval": "blocked",
            "allowed_future_retrieval_behavior": "none",
        },
        "phase_b_soft_proposal": {
            "project_bucket": "general",
            "primary_domain": "general",
            "domain_tags": ["smoke"],
            "soft_reason_code": "contextual_summary",
            "suggested_followup_question": "",
        },
        "router_hint": {
            "task_type": "review",
            "complexity": "medium",
            "domain": "general",
            "confidence": "low",
            "estimated_tokens": 200,
            "needs_reasoning": False,
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
            "needs_scientific_depth": False,
        },
        "action_hint": {
            "requested_action_type": "answer",
            "modifies_state": False,
            "side_effect_level": "none",
            "reversibility": "reversible",
            "environment_type": "chat",
            "state_scope": "none",
            "needs_terminal": False,
            "needs_file_write": False,
            "needs_memory_write": False,
            "needs_provider_call": False,
            "confidence": "low",
        },
        "user_policy": {
            "external_routing_enabled": False,
            "external_requires_confirmation": True,
            "allow_persistent_auto_allow": False,
        },
        "provider_policy": {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST"],
            "blocked_provider_tiers": ["CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM", "FRONTIER"],
        },
        "budget_policy": {
            "max_tier": "LOCAL_FAST",
            "max_tokens": 2048,
            "require_confirmation_above_tier": "CHEAP_EXTERNAL",
        },
        "context_metadata": {
            "attached_files_present": False,
            "conversation_context_available": False,
            "input_source": "smoke_builder",
        },
    }


def _mapped_overlay_reason(corrected: dict[str, Any]) -> str:
    raw = corrected.get("hard_reason_code")
    return OVERLAY_REASON_MAP.get(raw, "manual_review_required")


def _apply_conservative_overlay(input_obj: dict[str, Any], corrected: dict[str, Any]) -> None:
    phase_a = input_obj["phase_a_signals"]
    router_hint = input_obj["router_hint"]
    action_hint = input_obj["action_hint"]
    mapped_reason = _mapped_overlay_reason(corrected)

    phase_a["contains_secret_or_credential"] = corrected.get("contains_secret_or_credential") is True
    phase_a["contains_raw_private_or_ip_sensitive_context"] = (
        corrected.get("contains_raw_private_or_ip_sensitive_context") is True
    )
    phase_a["mentions_external_provider_or_upload_intent"] = (
        corrected.get("mentions_external_provider_or_upload_intent") is True
    )
    phase_a["external_provider_allowed"] = False
    phase_a["clarification_required"] = corrected.get("clarification_required") is True
    phase_a["sensitivity_bucket_proposal"] = corrected.get("sensitivity_bucket_proposal")
    if phase_a["sensitivity_bucket_proposal"] not in SENSITIVITY_BUCKETS:
        phase_a["sensitivity_bucket_proposal"] = "unknown"
    phase_a["requires_manual_review"] = True
    phase_a["source_policy_for_future_retrieval"] = corrected.get(
        "source_policy_for_future_retrieval",
        "blocked",
    )
    phase_a["allowed_future_retrieval_behavior"] = corrected.get(
        "allowed_future_retrieval_behavior",
        "none",
    )
    phase_a["hard_reason_codes"] = [mapped_reason]
    if mapped_reason == "secret_or_credential":
        phase_a["hard_reason_codes"].append("redaction_required")
    if mapped_reason == "manual_review_required" and corrected.get("hard_reason_code") not in OVERLAY_REASON_MAP:
        phase_a["hard_reason_codes"].append("unknown_sensitivity")

    if phase_a["contains_secret_or_credential"]:
        phase_a["sensitivity_bucket_proposal"] = "secret"
    elif phase_a["contains_raw_private_or_ip_sensitive_context"]:
        phase_a["sensitivity_bucket_proposal"] = "sensitive"

    if phase_a["mentions_external_provider_or_upload_intent"]:
        action_hint["needs_provider_call"] = True
        router_hint["complexity"] = "high"
        router_hint["task_type"] = "analysis"
        router_hint["needs_reasoning"] = True
    if corrected.get("memory_boundary_or_write_authority_claim") is True:
        action_hint["needs_memory_write"] = True
        router_hint["complexity"] = "high"
        router_hint["task_type"] = "review"
    if corrected.get("retrieval_or_source_use_request") is True:
        router_hint["needs_file_context"] = True
        router_hint["needs_current_info"] = True
        router_hint["complexity"] = "high"
        router_hint["task_type"] = "review"
    if phase_a["clarification_required"]:
        router_hint["complexity"] = "unknown"
        router_hint["task_type"] = "clarification"


def _detect_operational_intent(message_text: str) -> dict[str, Any]:
    """Detect obvious operational intent for smoke-only fail-closed routing."""

    categories: list[str] = []
    matches: dict[str, list[str]] = {}
    for category, patterns in OPERATIONAL_INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_text, flags=re.IGNORECASE):
                categories.append(category)
                matches.setdefault(category, []).append(pattern)
                break
    return {
        "detected": bool(categories),
        "categories": categories,
        "matches": matches,
    }


def _append_hard_reason(phase_a: dict[str, Any], reason: str) -> None:
    if reason not in HARD_REASON_CODES:
        reason = "manual_review_required"
    existing = phase_a.get("hard_reason_codes")
    if not isinstance(existing, list):
        existing = []
    filtered = [item for item in existing if item != "low_risk"]
    if reason not in filtered:
        filtered.append(reason)
    phase_a["hard_reason_codes"] = filtered or ["manual_review_required"]


def _apply_operational_intent_overlay(input_obj: dict[str, Any], operational: dict[str, Any]) -> None:
    if not operational.get("detected"):
        return

    phase_a = input_obj["phase_a_signals"]
    router_hint = input_obj["router_hint"]
    action_hint = input_obj["action_hint"]
    context_metadata = input_obj["context_metadata"]
    categories = set(operational.get("categories") or [])

    phase_a["requires_manual_review"] = True
    phase_a["external_provider_allowed"] = False
    phase_a["source_policy_for_future_retrieval"] = "blocked"
    phase_a["allowed_future_retrieval_behavior"] = "none"
    if phase_a.get("sensitivity_bucket_proposal") == "public":
        phase_a["sensitivity_bucket_proposal"] = "unknown"
    if phase_a.get("sensitivity_bucket_proposal") not in SENSITIVITY_BUCKETS:
        phase_a["sensitivity_bucket_proposal"] = "unknown"
    router_hint["task_type"] = "review"
    router_hint["complexity"] = "high"
    router_hint["confidence"] = "low"
    action_hint["confidence"] = "low"
    context_metadata["assume_public_simple_safe_path"] = False
    context_metadata["operational_intent_detected"] = True
    context_metadata["operational_intent_categories"] = sorted(categories)

    if "provider_upload" in categories:
        phase_a["mentions_external_provider_or_upload_intent"] = True
        action_hint["needs_provider_call"] = True
        router_hint["needs_reasoning"] = True
        _append_hard_reason(phase_a, "provider_or_upload_intent")

    if "terminal" in categories:
        action_hint["needs_terminal"] = True
        action_hint["requested_action_type"] = "terminal_command"
        action_hint["environment_type"] = "terminal"
        action_hint["state_scope"] = "os"
        router_hint["needs_code_execution"] = True
        _append_hard_reason(phase_a, "manual_review_required")

    if "memory_write" in categories:
        action_hint["needs_memory_write"] = True
        action_hint["requested_action_type"] = "memory_write"
        action_hint["environment_type"] = "memory_store"
        action_hint["state_scope"] = "memory"
        _append_hard_reason(phase_a, "manual_review_required")

    if "file_retrieval" in categories:
        router_hint["needs_file_context"] = True
        router_hint["needs_current_info"] = True
        _append_hard_reason(phase_a, "manual_review_required")

    if "browser_search" in categories:
        router_hint["needs_current_info"] = True
        action_hint["requested_action_type"] = "browser_search"
        action_hint["environment_type"] = "browser"
        action_hint["state_scope"] = "browser"
        _append_hard_reason(phase_a, "manual_review_required")

    if "tool_mcp" in categories:
        phase_a["clarification_required"] = True
        router_hint["task_type"] = "clarification"
        router_hint["complexity"] = "unknown"
        _append_hard_reason(phase_a, "clarification_required")


def _has_hard_gate_signal(input_obj: dict[str, Any]) -> bool:
    phase_a = input_obj["phase_a_signals"]
    router_hint = input_obj["router_hint"]
    action_hint = input_obj["action_hint"]
    reason_codes = set(phase_a["hard_reason_codes"])
    return any(
        (
            bool(reason_codes - {"low_risk"}),
            phase_a["contains_secret_or_credential"],
            phase_a["contains_raw_private_or_ip_sensitive_context"],
            phase_a["mentions_external_provider_or_upload_intent"],
            phase_a["clarification_required"],
            action_hint["needs_terminal"],
            action_hint["needs_file_write"],
            action_hint["needs_memory_write"],
            action_hint["needs_provider_call"],
            router_hint["needs_file_context"],
            router_hint["needs_code_execution"],
            router_hint["needs_current_info"],
        )
    )


def build_router_policy_input_from_message_for_smoke(
    message_text: str,
    *,
    now: str | None = None,
    assume_public_simple: bool = False,
) -> dict:
    """Build RouterPolicy input for smoke tests only, not production routing."""

    del now
    input_obj = _base_router_input(message_text)
    corrected = _APPLY_POLICY_OVERLAY(message_text, {})
    _apply_conservative_overlay(input_obj, corrected)
    operational = _detect_operational_intent(message_text)
    _apply_operational_intent_overlay(input_obj, operational)

    hard_gate_detected = _has_hard_gate_signal(input_obj)
    if assume_public_simple and not hard_gate_detected:
        phase_a = input_obj["phase_a_signals"]
        phase_a.update(
            {
                "hard_reason_codes": ["low_risk"],
                "sensitivity_bucket_proposal": "public",
                "requires_manual_review": False,
                "source_policy_for_future_retrieval": "not_applicable",
                "allowed_future_retrieval_behavior": "none",
            }
        )
        input_obj["router_hint"].update(
            {
                "task_type": "answer",
                "complexity": "low",
                "confidence": "high",
                "needs_reasoning": False,
                "needs_current_info": False,
                "needs_file_context": False,
                "needs_code_execution": False,
                "needs_scientific_depth": False,
            }
        )
        input_obj["action_hint"].update(
            {
                "requested_action_type": "answer",
                "modifies_state": False,
                "side_effect_level": "none",
                "reversibility": "reversible",
                "environment_type": "chat",
                "state_scope": "none",
                "needs_terminal": False,
                "needs_file_write": False,
                "needs_memory_write": False,
                "needs_provider_call": False,
                "confidence": "high",
            }
        )
        input_obj["context_metadata"]["assume_public_simple_safe_path"] = True
    else:
        if not hard_gate_detected:
            input_obj["phase_a_signals"].update(
                {
                    "hard_reason_codes": ["unknown_sensitivity", "manual_review_required"],
                    "sensitivity_bucket_proposal": "unknown",
                    "requires_manual_review": True,
                    "source_policy_for_future_retrieval": "blocked",
                    "allowed_future_retrieval_behavior": "none",
                }
            )
        input_obj["context_metadata"]["assume_public_simple_safe_path"] = False
    return input_obj


def _is_bool_map(section: dict[str, Any], fields: set[str]) -> bool:
    return all(isinstance(section.get(field), bool) for field in fields)


def _is_string(value: Any) -> bool:
    return isinstance(value, str)


def _is_int_not_bool(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _list_values(value: Any, allowed: set[str] | None = None) -> bool:
    if not isinstance(value, list):
        return False
    if allowed is None:
        return all(isinstance(item, str) for item in value)
    return all(isinstance(item, str) and item in allowed for item in value)


def _router_policy_input_structural_errors(input_obj: Any, original_message: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(input_obj, dict):
        return ["input is not object"]
    missing = sorted(TOP_LEVEL_REQUIRED - set(input_obj))
    if missing:
        errors.append("missing top-level fields")
    if input_obj.get("message_text") != original_message:
        errors.append("message_text mismatch")
    if not isinstance(input_obj.get("message_text"), str):
        errors.append("message_text invalid")

    phase_a = input_obj.get("phase_a_signals")
    phase_b = input_obj.get("phase_b_soft_proposal")
    router_hint = input_obj.get("router_hint")
    action_hint = input_obj.get("action_hint")
    user_policy = input_obj.get("user_policy")
    provider_policy = input_obj.get("provider_policy")
    budget_policy = input_obj.get("budget_policy")
    context_metadata = input_obj.get("context_metadata")
    for name, section in (
        ("phase_a_signals", phase_a),
        ("phase_b_soft_proposal", phase_b),
        ("router_hint", router_hint),
        ("action_hint", action_hint),
        ("user_policy", user_policy),
        ("provider_policy", provider_policy),
        ("budget_policy", budget_policy),
        ("context_metadata", context_metadata),
    ):
        if not isinstance(section, dict):
            errors.append(f"{name} invalid")

    if isinstance(phase_a, dict):
        if not _is_bool_map(phase_a, PHASE_A_BOOL_FIELDS):
            errors.append("phase_a boolean fields invalid")
        if not _list_values(phase_a.get("hard_reason_codes"), HARD_REASON_CODES):
            errors.append("phase_a hard_reason_codes invalid")
        if phase_a.get("sensitivity_bucket_proposal") not in SENSITIVITY_BUCKETS:
            errors.append("phase_a sensitivity invalid")
    if isinstance(phase_b, dict):
        for field in ("project_bucket", "primary_domain", "soft_reason_code"):
            if not _is_string(phase_b.get(field)):
                errors.append(f"phase_b {field} invalid")
        if not _list_values(phase_b.get("domain_tags")):
            errors.append("phase_b domain_tags invalid")
    if isinstance(router_hint, dict):
        if router_hint.get("complexity") not in ROUTER_COMPLEXITY:
            errors.append("router complexity invalid")
        if router_hint.get("confidence") not in CONFIDENCE_VALUES:
            errors.append("router confidence invalid")
        for field in ("task_type", "domain"):
            if not _is_string(router_hint.get(field)):
                errors.append(f"router {field} invalid")
        if "estimated_tokens" in router_hint and not _is_int_not_bool(router_hint.get("estimated_tokens")):
            errors.append("router estimated_tokens invalid")
        if not _is_bool_map(router_hint, ROUTER_BOOL_FIELDS):
            errors.append("router boolean fields invalid")
    if isinstance(action_hint, dict):
        if action_hint.get("requested_action_type") not in ACTION_TYPES:
            errors.append("action requested_action_type invalid")
        if action_hint.get("side_effect_level") not in SIDE_EFFECT_LEVELS:
            errors.append("action side_effect_level invalid")
        if action_hint.get("reversibility") not in REVERSIBILITY_VALUES:
            errors.append("action reversibility invalid")
        if action_hint.get("environment_type") not in ENVIRONMENT_TYPES:
            errors.append("action environment_type invalid")
        if action_hint.get("state_scope") not in STATE_SCOPES:
            errors.append("action state_scope invalid")
        if action_hint.get("confidence") not in CONFIDENCE_VALUES:
            errors.append("action confidence invalid")
        if not _is_bool_map(action_hint, ACTION_BOOL_FIELDS):
            errors.append("action boolean fields invalid")
    if isinstance(user_policy, dict) and not _is_bool_map(user_policy, USER_POLICY_BOOL_FIELDS):
        errors.append("user_policy boolean fields invalid")
    if isinstance(provider_policy, dict):
        if not _list_values(provider_policy.get("allowed_provider_tiers"), TIERS):
            errors.append("provider allowed tiers invalid")
        if not _list_values(provider_policy.get("blocked_provider_tiers"), TIERS):
            errors.append("provider blocked tiers invalid")
    if isinstance(budget_policy, dict):
        if budget_policy.get("max_tier") not in TIERS:
            errors.append("budget max_tier invalid")
        if budget_policy.get("require_confirmation_above_tier") not in TIERS:
            errors.append("budget require_confirmation_above_tier invalid")
        if not _is_int_not_bool(budget_policy.get("max_tokens")):
            errors.append("budget max_tokens invalid")
    if isinstance(context_metadata, dict) and not _is_bool_map(context_metadata, CONTEXT_BOOL_FIELDS):
        errors.append("context metadata boolean fields invalid")
    return errors


def _valid_message(message_text: Any) -> bool:
    return isinstance(message_text, str) and bool(message_text.strip()) and len(message_text) <= MAX_MESSAGE_CHARS


def run_message_route_smoke(
    message_text: str,
    *,
    responder=None,
    now: str | None = None,
    input_builder=None,
    assume_public_simple: bool = False,
) -> dict:
    if not _valid_message(message_text):
        return {
            "executed": False,
            "reason": "invalid_message",
            "input_source": "none",
            "assume_public_simple_used": assume_public_simple,
        }

    source = "injected_builder" if input_builder is not None else "smoke_builder"
    builder = input_builder or build_router_policy_input_from_message_for_smoke
    try:
        input_obj = builder(
            message_text,
            now=now,
            assume_public_simple=assume_public_simple,
        )
    except Exception as exc:
        return {
            "executed": False,
            "reason": "input_builder_failed",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
            "error_type": type(exc).__name__,
        }

    errors = _router_policy_input_structural_errors(input_obj, message_text)
    if errors:
        return {
            "executed": False,
            "reason": "invalid_router_policy_input",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
            "validation_errors": errors,
        }

    result = _RUN_LOCAL_ROUTE(input_obj, responder=responder, now=now)
    if not isinstance(result, dict) or "executed" not in result or "reason" not in result:
        return {
            "executed": False,
            "reason": "local_route_invalid_result",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
        }
    return {
        "executed": result["executed"],
        "reason": result["reason"],
        "response": result.get("response"),
        "decision": result.get("decision"),
        "input_obj": input_obj,
        "input_source": source,
        "assume_public_simple_used": assume_public_simple,
    }


def _build_local_responder_for_cli(*, model: str, endpoint: str, timeout_s: float):
    return _BUILD_LOCAL_RESPONDER(model=model, endpoint=endpoint, timeout_s=timeout_s)


def _build_router_input_for_cli(
    message_text: str,
    *,
    now: str | None = None,
    assume_public_simple: bool = False,
) -> dict:
    return build_router_policy_input_from_message_for_smoke(
        message_text,
        now=now,
        assume_public_simple=assume_public_simple,
    )


def _safe_cli_result(result: dict[str, Any]) -> dict[str, Any]:
    safe = {
        "executed": result.get("executed") is True,
        "reason": result.get("reason"),
        "input_source": result.get("input_source", "none"),
        "assume_public_simple_used": result.get("assume_public_simple_used") is True,
    }
    decision = result.get("decision")
    if isinstance(decision, dict):
        safe["decision_summary"] = {
            "route_action": decision.get("route_action"),
            "route_tier": decision.get("route_tier"),
            "allowed_execution_mode": decision.get("allowed_execution_mode"),
        }
    if result.get("executed") is True and isinstance(result.get("response"), str):
        safe["response"] = result["response"][:MAX_CLI_RESPONSE_CHARS]
    return safe


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RouterPolicy A5 message-route smoke bridge.")
    parser.add_argument("--message", required=True)
    parser.add_argument("--assume-public-simple", action="store_true")
    parser.add_argument("--run-local", action="store_true")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434/api/generate")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument("--now", default=None)
    args = parser.parse_args(argv)

    responder = None
    if args.run_local:
        try:
            responder = _build_local_responder_for_cli(
                model=args.model,
                endpoint=args.endpoint,
                timeout_s=args.timeout_s,
            )
        except LocalResponderError as exc:
            print(
                json.dumps(
                    {
                        "executed": False,
                        "reason": "local_responder_setup_failed",
                        "error_type": type(exc).__name__,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

    try:
        result = run_message_route_smoke(
            args.message,
            responder=responder,
            now=args.now,
            input_builder=_build_router_input_for_cli,
            assume_public_simple=args.assume_public_simple,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "executed": False,
                    "reason": "unexpected_error",
                    "error_type": type(exc).__name__,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(_safe_cli_result(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
