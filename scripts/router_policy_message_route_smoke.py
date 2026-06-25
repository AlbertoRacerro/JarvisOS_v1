"""Real-message RouterPolicy local-route smoke bridge for A5.

A5 is not a production Phase A/B normalizer. When no complete production
message normalizer exists, this module uses a conservative smoke-only fallback
builder. Arbitrary messages do not become executable unless
assume_public_simple=True and deterministic hard-gate signals do not fire.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import urllib.parse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import local_policy_gate_overlay_probe as policy_overlay
import local_phase_b_soft_review_model_probe as live_phase_b
from local_phase_b_soft_review_probe import build_soft_review
from router_policy_hint_bridge_probe import apply_phase_b_router_hint
from router_policy_local_responder import LocalResponderError, build_local_responder
from router_policy_local_route_probe import run_local_route


MAX_MESSAGE_CHARS = 12000
MAX_CLI_RESPONSE_CHARS = 1000
DEFAULT_PHASE_B_MODEL = "qwen3:8b"
DEFAULT_PHASE_B_ENDPOINT = "http://localhost:11434"
DEFAULT_PHASE_B_SCHEMA = Path("schemas/fast_secretary_soft_proposal_v0_1.schema.json")
PHASE_B_SOURCE_KINDS = {"stub", "deterministic", "live_local_qwen"}
LOCAL_PHASE_B_HOSTS = {"localhost", "127.0.0.1", "::1"}

_RUN_LOCAL_ROUTE = run_local_route
_BUILD_LOCAL_RESPONDER = build_local_responder
_APPLY_POLICY_OVERLAY = policy_overlay.apply_policy_overlay
_APPLY_PHASE_B_ROUTER_HINT = apply_phase_b_router_hint
_BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW = build_soft_review
_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW = None

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
B1_REQUIRED_PHASE_B_FIELDS = {
    "summary_short",
    "project_bucket",
    "primary_domain",
    "domain_tags",
    "storage_relevance",
    "usefulness_for_future_review",
    "possible_memory_card_type",
    "soft_reason_code",
    "brief_rationale",
    "suggested_followup_question",
    "soft_uncertain_fields",
}
B1_PHASE_B_STRING_FIELDS = {
    "summary_short",
    "project_bucket",
    "primary_domain",
    "storage_relevance",
    "usefulness_for_future_review",
    "possible_memory_card_type",
    "soft_reason_code",
    "brief_rationale",
    "suggested_followup_question",
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
        r"\bsalv\w*\s+in\s+memoria\b",
        r"\bmemorizza(?:lo|la|li|le|mi|ci|te|ti)?\b(?:\s+(?:che|di|quest\w+|il|lo|la|i|gli|le))?",
        r"\bricorda(?:ti)?\s+(?:che|di|quest\w+|il|lo|la|i|gli|le)\b",
        r"\btieni(?:lo)?\s+a\s+mente\b",
        r"\bprendi\s+nota\s+di\b",
        r"\bannota\s+(?:quest\w+|il|lo|la|i|gli|le)\b",
        r"\bnon\s+dimenticare\s+che\b",
        r"\bsalva\s+(?:quest\w+\s+)?preferenz\w*\b",
    ],
    "document_project_write": [
        r"\bmetti\s+nel\s+brevetto\b",
        r"\baggiungi\s+al\s+brevetto\b",
        r"\bscrivi\s+(?:nel|nello|nella|nei|negli|nelle|sul|sullo|sulla|sui|sugli|sulle)\s+(?:documento|file|brevetto|progetto|relazione)\b",
        r"\baggiorna\s+(?:il|lo|la|i|gli|le)\s+(?:documento|file|progetto)\b",
        r"\bsalva\s+nel\s+progetto\b",
        r"\bmetti\s+agli\s+atti\b",
        r"\bverbalizza\s+(?:quest\w+|il|lo|la|i|gli|le)\b",
        r"\binserisci\b.{0,40}\b(?:nel|nello|nella|nei|negli|nelle|al|allo|alla|ai|agli|alle)\s+(?:documento|file|brevetto|progetto|relazione)\b",
    ],
    "credential_like_save": [
        r"\b(?:salva|memorizza(?:lo|la|li|le|mi|ci|te|ti)?|ricorda(?:ti)?|conserva)\b.{0,25}\b(?:codice(?:\s+di\s+accesso)?|pin|token|password|chiave|credenziale)\b",
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
            "summary_short": "Benign local-answer smoke message.",
            "project_bucket": "general",
            "primary_domain": "general",
            "domain_tags": ["smoke"],
            "storage_relevance": "low",
            "usefulness_for_future_review": "low",
            "possible_memory_card_type": "none",
            "soft_reason_code": "contextual_summary",
            "brief_rationale": "Smoke-only default proposal for benign local-answer routing hints.",
            "suggested_followup_question": "",
            "soft_uncertain_fields": [],
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

    if "document_project_write" in categories:
        action_hint["modifies_state"] = True
        action_hint["needs_file_write"] = True
        action_hint["requested_action_type"] = "file_write"
        action_hint["environment_type"] = "codebase"
        action_hint["state_scope"] = "repo"
        _append_hard_reason(phase_a, "manual_review_required")

    if "credential_like_save" in categories:
        phase_a["contains_secret_or_credential"] = True
        phase_a["sensitivity_bucket_proposal"] = "secret"
        action_hint["modifies_state"] = True
        action_hint["needs_memory_write"] = True
        action_hint["requested_action_type"] = "memory_write"
        action_hint["environment_type"] = "memory_store"
        action_hint["state_scope"] = "memory"
        _append_hard_reason(phase_a, "secret_or_credential")
        _append_hard_reason(phase_a, "redaction_required")

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


def _phase_b_b1_compatibility_errors(phase_b: Any) -> list[str]:
    if not isinstance(phase_b, dict):
        return ["phase_b is not object"]
    errors: list[str] = []
    missing = sorted(B1_REQUIRED_PHASE_B_FIELDS - set(phase_b))
    if missing:
        errors.append("missing B1 phase_b fields")
    for field in sorted(B1_PHASE_B_STRING_FIELDS):
        if field in phase_b and not isinstance(phase_b.get(field), str):
            errors.append(f"phase_b {field} invalid")
    if "domain_tags" in phase_b and not _list_values(phase_b.get("domain_tags")):
        errors.append("phase_b domain_tags invalid")
    if "soft_uncertain_fields" in phase_b and not _list_values(phase_b.get("soft_uncertain_fields")):
        errors.append("phase_b soft_uncertain_fields invalid")
    return errors


def _validate_live_phase_b_endpoint(endpoint: str) -> str:
    if not isinstance(endpoint, str):
        raise ValueError("phase_b_endpoint must be a string")
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http":
        raise ValueError("phase_b_endpoint must use http")
    if parsed.hostname not in LOCAL_PHASE_B_HOSTS:
        raise ValueError("phase_b_endpoint host must be localhost")
    if parsed.username or parsed.password:
        raise ValueError("phase_b_endpoint must not include credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("phase_b_endpoint must not include query or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("phase_b_endpoint must not include a path")
    netloc = parsed.netloc
    return urllib.parse.urlunparse(("http", netloc, "/api/chat", "", "", ""))


def _load_live_phase_b_schema(schema_path: Path = DEFAULT_PHASE_B_SCHEMA) -> dict[str, Any]:
    schema = live_phase_b.structured_probe.load_json(schema_path)
    live_phase_b.structured_probe.validate_schema_shape(schema)
    if live_phase_b.authority_field_leakage(schema.get("properties", {})):
        raise ValueError("live Phase B schema contains authority fields")
    return schema


def _build_live_local_phase_b_soft_review(
    *,
    case_id: str,
    input_text: str,
    phase_a: dict[str, Any],
    model: str = DEFAULT_PHASE_B_MODEL,
    endpoint: str = DEFAULT_PHASE_B_ENDPOINT,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    chat_url = _validate_live_phase_b_endpoint(endpoint)
    schema = _load_live_phase_b_schema()
    prompt = live_phase_b.build_phase_b_prompt(case_id=case_id, input_text=input_text)
    raw_call = live_phase_b.structured_probe.call_ollama_chat(
        model=model,
        prompt=prompt,
        schema=schema,
        timeout_seconds=timeout_seconds,
        url=chat_url,
    )
    if not raw_call.get("ok"):
        raise ValueError("live Phase B local model call failed")
    if not isinstance(raw_call.get("body"), dict):
        raise ValueError("live Phase B response body invalid")
    parsed, parse_error = live_phase_b.parse_soft_proposal(raw_call["body"])
    if parsed is None:
        raise ValueError(f"live Phase B parse failed: {parse_error}")
    raw_validation = live_phase_b.structured_probe.validate_instance(parsed, schema)
    if not raw_validation["schema_valid"]:
        raise ValueError("live Phase B raw proposal schema invalid")
    raw_leakage = live_phase_b.authority_field_leakage(parsed)
    if raw_leakage:
        raise ValueError("live Phase B raw proposal authority leakage")
    effective, clamps = live_phase_b.apply_deterministic_soft_clamp(
        phase_a=copy.deepcopy(phase_a),
        raw_proposal=copy.deepcopy(parsed),
        input_text=input_text,
    )
    effective_validation = live_phase_b.structured_probe.validate_instance(effective, schema)
    if not effective_validation["schema_valid"]:
        raise ValueError("live Phase B effective proposal schema invalid")
    effective_leakage = live_phase_b.authority_field_leakage(effective)
    if effective_leakage:
        raise ValueError("live Phase B effective proposal authority leakage")
    phase_b_errors = _phase_b_b1_compatibility_errors(effective)
    if phase_b_errors:
        raise ValueError("live Phase B effective proposal is not B1 compatible")
    output = copy.deepcopy(effective)
    output["_live_phase_b_diagnostics"] = {
        "raw_authority_leakage": raw_leakage,
        "effective_authority_leakage": effective_leakage,
        "deterministic_clamp_count": len(clamps),
    }
    return output


_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW = _build_live_local_phase_b_soft_review


def _apply_deterministic_phase_b_soft_review(
    input_obj: dict[str, Any],
    *,
    case_id: str,
    message_text: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(case_id, str) or not case_id.strip():
        return None, ["phase_b case_id invalid"]
    phase_a = input_obj.get("phase_a_signals")
    if not isinstance(phase_a, dict):
        return None, ["phase_a invalid for deterministic phase_b"]
    phase_b = _BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW(
        case_id=case_id,
        input_text=message_text,
        phase_a=copy.deepcopy(phase_a),
    )
    errors = _phase_b_b1_compatibility_errors(phase_b)
    if isinstance(phase_b, dict) and "phase_a_case_id" in phase_b and phase_b.get("phase_a_case_id") != case_id:
        errors.append("phase_b case_id mismatch")
    if errors:
        return None, errors
    output = copy.deepcopy(input_obj)
    output["phase_b_soft_proposal"] = phase_b
    metadata = output.setdefault("context_metadata", {})
    metadata.update(
        {
            "phase_a_source": "deterministic_overlay_builder",
            "phase_b_source_kind": "deterministic_fast_secretary_soft_review",
            "phase_b_source_case_id": case_id,
            "phase_b_source_function": "local_phase_b_soft_review_probe.build_soft_review",
            "same_case_id_for_phase_a_and_phase_b": True,
            "cross_case_mix": False,
            "synthetic_or_sanitized_message": True,
        }
    )
    return output, []


def _apply_live_local_phase_b_soft_review(
    input_obj: dict[str, Any],
    *,
    case_id: str,
    message_text: str,
    model: str,
    endpoint: str,
    timeout_seconds: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(case_id, str) or not case_id.strip():
        return None, ["phase_b case_id invalid"]
    phase_a = input_obj.get("phase_a_signals")
    if not isinstance(phase_a, dict):
        return None, ["phase_a invalid for live phase_b"]
    raw_phase_b = _BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW(
        case_id=case_id,
        input_text=message_text,
        phase_a=copy.deepcopy(phase_a),
        model=model,
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
    )
    phase_b = copy.deepcopy(raw_phase_b)
    diagnostics = {}
    if isinstance(phase_b, dict):
        diagnostics = phase_b.pop("_live_phase_b_diagnostics", {})
    errors = _phase_b_b1_compatibility_errors(phase_b)
    direct_leakage = live_phase_b.authority_field_leakage(phase_b)
    if direct_leakage:
        errors.append("live phase_b authority leakage")
    if isinstance(phase_b, dict) and "phase_a_case_id" in phase_b and phase_b.get("phase_a_case_id") != case_id:
        errors.append("phase_b case_id mismatch")
    raw_leakage = diagnostics.get("raw_authority_leakage") if isinstance(diagnostics, dict) else None
    effective_leakage = diagnostics.get("effective_authority_leakage") if isinstance(diagnostics, dict) else None
    if raw_leakage:
        errors.append("live phase_b raw authority leakage")
    if effective_leakage:
        errors.append("live phase_b effective authority leakage")
    if errors:
        return None, errors
    phase_b["phase_a_case_id"] = case_id
    output = copy.deepcopy(input_obj)
    output["phase_b_soft_proposal"] = phase_b
    metadata = output.setdefault("context_metadata", {})
    metadata.update(
        {
            "phase_a_source": "deterministic_overlay_builder",
            "phase_b_source_kind": "live_local_qwen_soft_review",
            "phase_b_source_case_id": case_id,
            "phase_b_source_function": (
                "local_phase_b_soft_review_model_probe.build_phase_b_prompt/"
                "local_model_structured_output_probe.call_ollama_chat"
            ),
            "phase_b_model": model,
            "phase_b_endpoint_localhost_only": True,
            "same_case_id_for_phase_a_and_phase_b": True,
            "cross_case_mix": False,
            "synthetic_or_sanitized_message": True,
        }
    )
    if isinstance(diagnostics, dict):
        metadata["live_phase_b_diagnostics"] = {
            "raw_authority_leakage_count": len(diagnostics.get("raw_authority_leakage") or []),
            "effective_authority_leakage_count": len(diagnostics.get("effective_authority_leakage") or []),
            "deterministic_clamp_count": diagnostics.get("deterministic_clamp_count", 0),
        }
    return output, []


def _source_selection_error(
    *,
    phase_b_source_kind: str,
    phase_b_source_case_id: str | None,
    run_local_phase_b: bool,
    use_phase_b_hints: bool,
) -> str | None:
    if phase_b_source_kind not in PHASE_B_SOURCE_KINDS:
        return "invalid_phase_b_source_kind"
    if phase_b_source_kind == "stub":
        if phase_b_source_case_id is not None:
            return "phase_b_source_conflict"
        if run_local_phase_b:
            return "phase_b_source_conflict"
    elif phase_b_source_kind == "deterministic":
        if not phase_b_source_case_id:
            return "phase_b_source_conflict"
        if run_local_phase_b:
            return "phase_b_source_conflict"
        if not use_phase_b_hints:
            return "phase_b_source_conflict"
    elif phase_b_source_kind == "live_local_qwen":
        if not phase_b_source_case_id:
            return "phase_b_source_conflict"
        if not run_local_phase_b:
            return "phase_b_source_conflict"
        if not use_phase_b_hints:
            return "phase_b_source_conflict"
    return None


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
    use_phase_b_hints: bool = True,
    phase_b_source_kind: str = "stub",
    phase_b_source_case_id: str | None = None,
    run_local_phase_b: bool = False,
    phase_b_model: str = DEFAULT_PHASE_B_MODEL,
    phase_b_endpoint: str = DEFAULT_PHASE_B_ENDPOINT,
    phase_b_timeout_seconds: int = 180,
) -> dict:
    source_error = _source_selection_error(
        phase_b_source_kind=phase_b_source_kind,
        phase_b_source_case_id=phase_b_source_case_id,
        run_local_phase_b=run_local_phase_b,
        use_phase_b_hints=use_phase_b_hints,
    )
    if source_error:
        return {
            "executed": False,
            "reason": source_error,
            "input_source": "none",
            "assume_public_simple_used": assume_public_simple,
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": False,
        }
    if phase_b_source_kind == "live_local_qwen":
        try:
            _validate_live_phase_b_endpoint(phase_b_endpoint)
        except ValueError as exc:
            return {
                "executed": False,
                "reason": "invalid_phase_b_endpoint",
                "input_source": "none",
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": use_phase_b_hints,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": False,
                "error_type": type(exc).__name__,
            }
    if not _valid_message(message_text):
        return {
            "executed": False,
            "reason": "invalid_message",
            "input_source": "none",
            "assume_public_simple_used": assume_public_simple,
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": False,
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
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": False,
            "error_type": type(exc).__name__,
        }

    errors = _router_policy_input_structural_errors(input_obj, message_text)
    if errors:
        return {
            "executed": False,
            "reason": "invalid_router_policy_input",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": phase_b_source_kind != "stub",
            "validation_stage": "pre_phase_b_hint_bridge",
            "validation_errors": errors,
        }

    if phase_b_source_kind == "deterministic":
        try:
            input_obj, phase_b_errors = _apply_deterministic_phase_b_soft_review(
                input_obj,
                case_id=phase_b_source_case_id,
                message_text=message_text,
            )
        except Exception as exc:
            return {
                "executed": False,
                "reason": "deterministic_phase_b_source_failed",
                "input_source": source,
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": use_phase_b_hints,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": True,
                "error_type": type(exc).__name__,
            }
        if phase_b_errors:
            return {
                "executed": False,
                "reason": "invalid_deterministic_phase_b",
                "input_source": source,
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": use_phase_b_hints,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": True,
                "validation_errors": phase_b_errors,
            }
    elif phase_b_source_kind == "live_local_qwen":
        try:
            input_obj, phase_b_errors = _apply_live_local_phase_b_soft_review(
                input_obj,
                case_id=phase_b_source_case_id,
                message_text=message_text,
                model=phase_b_model,
                endpoint=phase_b_endpoint,
                timeout_seconds=phase_b_timeout_seconds,
            )
        except Exception as exc:
            return {
                "executed": False,
                "reason": "live_phase_b_source_failed",
                "input_source": source,
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": use_phase_b_hints,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": True,
                "error_type": type(exc).__name__,
            }
        if phase_b_errors:
            return {
                "executed": False,
                "reason": "invalid_live_phase_b",
                "input_source": source,
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": use_phase_b_hints,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": True,
                "validation_errors": phase_b_errors,
            }

    if use_phase_b_hints:
        try:
            input_obj = _APPLY_PHASE_B_ROUTER_HINT(input_obj, now=now)
        except Exception as exc:
            return {
                "executed": False,
                "reason": "phase_b_hint_bridge_failed",
                "input_source": source,
                "assume_public_simple_used": assume_public_simple,
                "use_phase_b_hints_used": True,
                "phase_b_source_kind": phase_b_source_kind,
                "phase_b_source_used": phase_b_source_kind != "stub",
                "error_type": type(exc).__name__,
            }

    errors = _router_policy_input_structural_errors(input_obj, message_text)
    if errors:
        return {
            "executed": False,
            "reason": "invalid_router_policy_input",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": phase_b_source_kind != "stub",
            "validation_errors": errors,
        }

    result = _RUN_LOCAL_ROUTE(input_obj, responder=responder, now=now)
    if not isinstance(result, dict) or "executed" not in result or "reason" not in result:
        return {
            "executed": False,
            "reason": "local_route_invalid_result",
            "input_source": source,
            "assume_public_simple_used": assume_public_simple,
            "use_phase_b_hints_used": use_phase_b_hints,
            "phase_b_source_kind": phase_b_source_kind,
            "phase_b_source_used": phase_b_source_kind != "stub",
        }
    return {
        "executed": result["executed"],
        "reason": result["reason"],
        "response": result.get("response"),
        "decision": result.get("decision"),
        "input_obj": input_obj,
        "input_source": source,
        "assume_public_simple_used": assume_public_simple,
        "use_phase_b_hints_used": use_phase_b_hints,
        "phase_b_source_kind": phase_b_source_kind,
        "phase_b_source_used": phase_b_source_kind != "stub",
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
        "use_phase_b_hints_used": result.get("use_phase_b_hints_used") is True,
        "phase_b_source_kind": result.get("phase_b_source_kind", "stub"),
        "phase_b_source_used": result.get("phase_b_source_used") is True,
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
    parser.set_defaults(use_phase_b_hints=True)
    phase_b_group = parser.add_mutually_exclusive_group()
    phase_b_group.add_argument(
        "--use-phase-b-hints",
        dest="use_phase_b_hints",
        action="store_true",
        help="Enable Phase B RouterHint bridge; default in B3.",
    )
    phase_b_group.add_argument(
        "--no-phase-b-hints",
        dest="use_phase_b_hints",
        action="store_false",
        help="Disable Phase B RouterHint bridge for baseline/debug smoke comparisons.",
    )
    parser.add_argument("--run-local", action="store_true")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434/api/generate")
    parser.add_argument("--timeout-s", type=float, default=30.0)
    parser.add_argument(
        "--phase-b-source",
        choices=["stub", "deterministic", "live-local-qwen"],
        default="stub",
    )
    parser.add_argument("--phase-b-source-case-id", default=None)
    parser.add_argument("--run-local-phase-b", action="store_true")
    parser.add_argument("--phase-b-model", default=DEFAULT_PHASE_B_MODEL)
    parser.add_argument("--phase-b-endpoint", default=DEFAULT_PHASE_B_ENDPOINT)
    parser.add_argument("--phase-b-timeout-seconds", type=int, default=180)
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
                        "use_phase_b_hints_used": args.use_phase_b_hints,
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
            use_phase_b_hints=args.use_phase_b_hints,
            phase_b_source_kind=args.phase_b_source.replace("-", "_"),
            phase_b_source_case_id=args.phase_b_source_case_id,
            run_local_phase_b=args.run_local_phase_b,
            phase_b_model=args.phase_b_model,
            phase_b_endpoint=args.phase_b_endpoint,
            phase_b_timeout_seconds=args.phase_b_timeout_seconds,
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
