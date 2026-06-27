"""RouterPolicy v3.1.1 semantic validator.

This module is contract-layer only. It validates RouterPolicy input/decision
objects and returns policy violations. It does not route, execute tools, call
providers, write memory, read runtime state, or perform network operations.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import router_policy_canonical_digest as confirmation_digest_helper


TIER_RANK = {
    "LOCAL_ONLY": 0,
    "LOCAL_FAST": 1,
    "CHEAP_EXTERNAL": 2,
    "SCIENTIFIC_MEDIUM": 3,
    "FRONTIER": 4,
}

EXTERNAL_TIERS = {"CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM", "FRONTIER"}
LOCAL_PROVIDERS = {"local:qwen", "local:gemma", "none"}
EXTERNAL_NETWORK_ACTIONS = {"browser_search", "tool_call", "mcp_call"}
SECRET_ECHO_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|api[_ -]?key\s*[:=]|password\s*[:=]|"
    r"token\s*[:=]|private key|BEGIN [A-Z ]*PRIVATE KEY)",
    re.IGNORECASE,
)

REASON_CODES = {
    "secret_or_credential",
    "local_only_sensitive_context",
    "provider_boundary",
    "ambiguous_external_routing",
    "clarification_required",
    "budget_cap",
    "policy_external_disabled",
    "low_complexity_local",
    "high_complexity_external_candidate",
    "high_side_effect_action",
    "irreversible_action",
    "file_write_requires_dry_run",
    "terminal_requires_preflight",
    "memory_policy_required",
    "browser_search_boundary",
    "redaction_required",
    "redaction_pending",
    "confirmation_required",
    "confirmation_payload_required",
    "stale_confirmation",
    "consent_context_required",
    "external_network_blocked",
    "default_local_fallback",
}


def canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _violation(code: str, message: str, field_path: str, severity: str = "error") -> dict:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "field_path": field_path,
    }


def _add(
    violations: list[dict],
    code: str,
    message: str,
    field_path: str,
    severity: str = "error",
) -> None:
    violations.append(_violation(code, message, field_path, severity))


def _has_secret_signal(input_obj: dict[str, Any]) -> bool:
    phase_a = input_obj.get("phase_a_signals") or {}
    if phase_a.get("contains_secret_or_credential") is True:
        return True
    text = input_obj.get("message_text")
    return isinstance(text, str) and bool(SECRET_ECHO_PATTERN.search(text))


def _is_private_context(input_obj: dict[str, Any]) -> bool:
    phase_a = input_obj.get("phase_a_signals") or {}
    sensitivity = phase_a.get("sensitivity_bucket_proposal")
    return (
        phase_a.get("contains_raw_private_or_ip_sensitive_context") is True
        or sensitivity in {"sensitive", "secret"}
    )


def _input_action(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("action_hint") or {}


def _budget_policy(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("budget_policy") or {}


def _provider_policy(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("provider_policy") or {}


def _phase_a(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("phase_a_signals") or {}


def _is_executable_tier(route_tier: Any) -> bool:
    return route_tier in TIER_RANK


def _check_local_only(decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("route_tier") != "LOCAL_ONLY":
        return
    if decision.get("provider_candidate") not in LOCAL_PROVIDERS:
        _add(
            violations,
            "LOCAL_ONLY_WITH_EXTERNAL_PROVIDER",
            "LOCAL_ONLY route cannot select an external provider.",
            "provider_candidate",
        )
    if decision.get("external_allowed") is not False:
        _add(
            violations,
            "LOCAL_ONLY_WITH_EXTERNAL_PROVIDER",
            "LOCAL_ONLY route must keep external_allowed false.",
            "external_allowed",
        )


def _check_blocked(decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("route_tier") != "BLOCKED" and decision.get("route_action") != "blocked":
        return
    expected = {
        "provider_candidate": "none",
        "allowed_execution_mode": "blocked",
        "provider_call_allowed_now": False,
        "tool_execution_allowed_now": False,
        "external_network_allowed_now": False,
        "state_change_allowed_now": False,
    }
    for field, value in expected.items():
        if decision.get(field) != value:
            _add(
                violations,
                "BLOCKED_BUT_EXECUTABLE",
                "Blocked decisions must not remain executable.",
                field,
            )


def _check_external_candidate(decision: dict[str, Any], violations: list[dict]) -> None:
    provider = decision.get("provider_candidate")
    if decision.get("external_allowed") is True and decision.get("route_action") != "route_external_candidate":
        _add(
            violations,
            "EXTERNAL_ALLOWED_WITHOUT_EXTERNAL_ROUTE_ACTION",
            "external_allowed true requires route_external_candidate route_action.",
            "route_action",
        )
    if decision.get("external_allowed") is False and isinstance(provider, str) and provider.startswith("external:"):
        _add(
            violations,
            "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN",
            "External provider_candidate requires external_allowed true.",
            "provider_candidate",
        )
    if decision.get("route_action") != "route_external_candidate":
        return
    if decision.get("external_allowed") is not True:
        _add(
            violations,
            "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN",
            "External candidate requires external_allowed true.",
            "external_allowed",
        )
    if decision.get("provider_call_allowed_now") is not True:
        _add(
            violations,
            "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN",
            "External candidate requires provider_call_allowed_now true.",
            "provider_call_allowed_now",
        )
    if not (isinstance(provider, str) and provider.startswith("external:")):
        _add(
            violations,
            "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN",
            "External candidate must select an external provider candidate.",
            "provider_candidate",
        )
    if decision.get("route_tier") not in EXTERNAL_TIERS:
        _add(
            violations,
            "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN",
            "External candidate must use an external executable route tier.",
            "route_tier",
        )


def _check_answer_only(decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("allowed_execution_mode") != "answer_only":
        return
    if decision.get("response_allowed_now") is not True:
        _add(violations, "ANSWER_ONLY_WITH_SIDE_EFFECT", "answer_only must allow response.", "response_allowed_now")
    side_effect_fields = [
        "tool_execution_allowed_now",
        "provider_call_allowed_now",
        "external_network_allowed_now",
        "state_change_allowed_now",
    ]
    for field in side_effect_fields:
        if decision.get(field) is not False:
            _add(
                violations,
                "ANSWER_ONLY_WITH_TOOL_PROVIDER_OR_STATE_PERMISSION",
                "answer_only cannot carry tool/provider/network/state permission.",
                field,
            )
    if decision.get("side_effect_level") != "none":
        _add(violations, "ANSWER_ONLY_WITH_SIDE_EFFECT", "answer_only requires no side effect.", "side_effect_level")
    if decision.get("environment_type") != "chat":
        _add(violations, "ANSWER_ONLY_WITH_SIDE_EFFECT", "answer_only requires chat environment.", "environment_type")
    if decision.get("modifies_state") is not False:
        _add(violations, "ANSWER_ONLY_WITH_SIDE_EFFECT", "answer_only cannot modify state.", "modifies_state")


def _check_side_effects(decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("side_effect_level") in {"high", "irreversible"}:
        if decision.get("route_action") not in {"ask_user_confirm", "blocked", "require_preflight"}:
            _add(
                violations,
                "HIGH_EFFECT_WITHOUT_CONFIRM_OR_REVIEW",
                "High or irreversible side effects require confirmation, preflight, or block.",
                "route_action",
            )
        if not (decision.get("confirmation_required") is True or decision.get("manual_review_required") is True):
            _add(
                violations,
                "HIGH_EFFECT_WITHOUT_CONFIRM_OR_REVIEW",
                "High or irreversible side effects require confirmation or manual review.",
                "confirmation_required",
            )
    if decision.get("side_effect_level") == "unknown":
        for field in (
            "provider_call_allowed_now",
            "tool_execution_allowed_now",
            "external_network_allowed_now",
            "state_change_allowed_now",
        ):
            if decision.get(field) is not False:
                _add(
                    violations,
                    "UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE",
                    "Unknown side effects cannot be executable.",
                    field,
                )
        if decision.get("allowed_execution_mode") not in {"propose_only", "blocked"}:
            _add(
                violations,
                "UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE",
                "Unknown side effects must stay propose_only or blocked.",
                "allowed_execution_mode",
            )


def _check_confirmation_payload(decision: dict[str, Any], violations: list[dict]) -> None:
    payload = decision.get("confirmation_payload")
    if decision.get("confirmation_required") is True:
        if decision.get("confirmation_payload_required") is not True or payload is None:
            _add(
                violations,
                "CONFIRMATION_MISSING_PAYLOAD",
                "Confirmation requires a reviewable payload.",
                "confirmation_payload",
            )
        options = decision.get("confirmation_options")
        if not isinstance(options, list) or not {"allow_once", "deny"}.issubset(set(options)):
            _add(
                violations,
                "CONFIRMATION_OPTIONS_INVALID",
                "Confirmation options must include allow_once and deny.",
                "confirmation_options",
            )
        if decision.get("requires_new_decision_after_confirmation") is not True:
            _add(
                violations,
                "CONFIRMATION_OPTIONS_INVALID",
                "Confirmation click must require a new RouterPolicy decision.",
                "requires_new_decision_after_confirmation",
            )
    if payload is not None:
        integrity = confirmation_digest_helper.validate_confirmation_digest_integrity(decision)
        if integrity["valid"] is not True:
            _add(
                violations,
                "CONFIRMATION_DIGEST_INVALID",
                "confirmation_digest must match the canonical confirmation intent digest envelope.",
                "confirmation_digest",
            )
        if payload.get("payload_preview_truncated") is True and payload.get("full_payload_available_for_review") is not True:
            _add(
                violations,
                "CONFIRMATION_MISSING_PAYLOAD",
                "Truncated payload preview requires full payload availability.",
                "confirmation_payload.full_payload_available_for_review",
            )
        if payload.get("scope") in {"file_write", "terminal_command"}:
            if not payload.get("full_diff_digest") or payload.get("full_diff_available_for_review") is not True:
                _add(
                    violations,
                    "CONFIRMATION_MISSING_PAYLOAD",
                    "File/terminal confirmation payloads require full diff digest and reviewability.",
                    "confirmation_payload.full_diff_digest",
                )
        if payload.get("scope") == "terminal_command":
            if not payload.get("terminal_risk_summary"):
                _add(
                    violations,
                    "CONFIRMATION_MISSING_PAYLOAD",
                    "Terminal commands require a terminal risk summary.",
                    "confirmation_payload.terminal_risk_summary",
                )


def validate_confirmation_revalidation_boundary(
    decision: dict[str, Any],
    previous_decision: dict[str, Any] | None,
    *,
    now: str | None = None,
) -> list[dict]:
    violations: list[dict] = []

    if decision.get("lifecycle_stage") != "confirmed_execution":
        return violations
    now_dt = parse_datetime(now) if now is not None else None
    if now_dt is None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution revalidation requires a caller-supplied parseable now timestamp.",
            "now",
        )

    consent = decision.get("consent_context")
    if not isinstance(consent, dict) or previous_decision is None:
        _add(
            violations,
            "CONSENT_CONTEXT_MISSING",
            "confirmed_execution requires consent context and previous decision.",
            "consent_context",
        )
        return violations
    if previous_decision.get("lifecycle_stage") != "awaiting_confirmation":
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution requires a previous awaiting_confirmation decision.",
            "previous_decision.lifecycle_stage",
        )
    if previous_decision.get("confirmation_required") is not True:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Previous decision must require confirmation.",
            "previous_decision.confirmation_required",
        )
    previous_digest = previous_decision.get("confirmation_digest")
    if not isinstance(previous_digest, str) or not previous_digest:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Previous decision must carry a confirmation_digest.",
            "previous_decision.confirmation_digest",
        )
    if consent.get("confirmation_action") != "allow_once":
        _add(
            violations,
            "CONSENT_CONTEXT_MISSING",
            "confirmed_execution consent action must be allow_once.",
            "consent_context.confirmation_action",
        )
    if parse_datetime(consent.get("confirmed_at")) is None:
        _add(
            violations,
            "CONSENT_CONTEXT_MISSING",
            "confirmed_execution requires a valid consent_context.confirmed_at timestamp.",
            "consent_context.confirmed_at",
        )
    if consent.get("confirmed_previous_decision_id") != previous_decision.get("decision_id"):
        _add(
            violations,
            "CONSENT_CONTEXT_MISSING",
            "Consent must reference the exact previous confirmation decision.",
            "consent_context.confirmed_previous_decision_id",
        )
    if consent.get("confirmed_confirmation_digest") != previous_digest:
        _add(
            violations,
            "CONSENT_DIGEST_MISMATCH",
            "Consent digest must match previous decision confirmation digest.",
            "consent_context.confirmed_confirmation_digest",
        )
    previous_integrity = confirmation_digest_helper.validate_confirmation_digest_integrity(previous_decision)
    if previous_integrity["valid"] is not True:
        _add(
            violations,
            "CONSENT_DIGEST_MISMATCH",
            "Previous confirmation digest must still match its bound confirmation intent envelope.",
            "previous_decision.confirmation_digest",
        )
    previous_expires = parse_datetime(previous_decision.get("expires_at"))
    if previous_expires is None or (now_dt is not None and now_dt > previous_expires):
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Previous confirmation decision is missing or expired.",
            "previous_decision.expires_at",
        )
    current_input_digest = decision.get("input_digest")
    previous_input_digest = previous_decision.get("input_digest")
    if not isinstance(current_input_digest, str) or not current_input_digest:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution requires a non-empty current input_digest.",
            "input_digest",
        )
    if not isinstance(previous_input_digest, str) or not previous_input_digest:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Previous confirmation requires a non-empty input_digest.",
            "previous_decision.input_digest",
        )
    if (
        isinstance(current_input_digest, str)
        and current_input_digest
        and isinstance(previous_input_digest, str)
        and previous_input_digest
        and current_input_digest != previous_input_digest
    ):
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Confirmed execution input digest must match the previous confirmation; input drift is rejected at this boundary.",
            "input_digest",
        )
    if decision.get("confirmation_required") is not False:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution must not keep confirmation_required true.",
            "confirmation_required",
        )
    if decision.get("confirmation_payload_required") is not False:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution must not keep confirmation_payload_required true.",
            "confirmation_payload_required",
        )
    if decision.get("confirmation_payload") is not None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution must not retain confirmation_payload.",
            "confirmation_payload",
        )
    if decision.get("confirmation_digest") is not None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution must not retain confirmation_digest; continuity belongs in consent_context.confirmed_confirmation_digest.",
            "confirmation_digest",
        )
    if decision.get("confirmation_options"):
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "confirmed_execution must not retain confirmation_options.",
            "confirmation_options",
        )
    current_target = decision.get("proposed_external_target")
    consent_target = None
    if isinstance(consent, dict):
        consent_target = consent.get("confirmed_external_target")
    if not current_target and isinstance(consent_target, str) and consent_target.startswith("external:"):
        current_target = consent_target
    previous_target = previous_decision.get("proposed_external_target")
    if not current_target:
        provider_candidate = decision.get("provider_candidate")
        if isinstance(provider_candidate, str) and provider_candidate.startswith("external:"):
            current_target = provider_candidate
    if previous_target and not current_target:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Previous external target exists, so confirmed_execution must derive a current external target.",
            "proposed_external_target",
        )
    if current_target and previous_target and current_target != previous_target:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Confirmed execution target must match the previous confirmed external target.",
            "proposed_external_target",
        )

    return violations


def evaluate_confirmed_execution_activation_boundary(
    decision: dict[str, Any],
    previous_decision: dict[str, Any] | None,
    *,
    now: str | None = None,
) -> dict[str, Any]:
    violations: list[dict] = []
    if decision.get("lifecycle_stage") != "confirmed_execution":
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires lifecycle_stage confirmed_execution.",
            "lifecycle_stage",
        )
        return {
            "activation_safe": False,
            "violations": violations,
            "activation_scope": "confirmed_execution_boundary_only",
        }

    revalidation_violations = validate_confirmation_revalidation_boundary(
        decision,
        previous_decision,
        now=now,
    )
    violations.extend(revalidation_violations)

    now_dt = parse_datetime(now) if now is not None else None
    consent = decision.get("consent_context")
    previous_created = None if previous_decision is None else parse_datetime(previous_decision.get("created_at"))
    previous_expires = None if previous_decision is None else parse_datetime(previous_decision.get("expires_at"))
    confirmed_at = parse_datetime(consent.get("confirmed_at")) if isinstance(consent, dict) else None

    if now_dt is None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires a caller-supplied parseable now timestamp.",
            "now",
        )
    if previous_created is None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires a valid previous_decision.created_at timestamp.",
            "previous_decision.created_at",
        )
    if previous_expires is None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires a valid previous_decision.expires_at timestamp.",
            "previous_decision.expires_at",
        )
    if confirmed_at is None:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires a valid consent_context.confirmed_at timestamp.",
            "consent_context.confirmed_at",
        )
    if previous_created is not None and previous_expires is not None and previous_created >= previous_expires:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires previous_decision.created_at to be before previous_decision.expires_at.",
            "previous_decision.expires_at",
        )
    if previous_created is not None and confirmed_at is not None and previous_created > confirmed_at:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires previous_decision.created_at <= consent_context.confirmed_at.",
            "consent_context.confirmed_at",
        )
    if confirmed_at is not None and now_dt is not None and confirmed_at > now_dt:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires consent_context.confirmed_at <= now.",
            "consent_context.confirmed_at",
        )
    if confirmed_at is not None and previous_expires is not None and confirmed_at > previous_expires:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary requires consent_context.confirmed_at <= previous_decision.expires_at.",
            "consent_context.confirmed_at",
        )

    if decision.get("provider_call_allowed_now") is not False:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary is diagnostic only and must not carry provider_call_allowed_now true.",
            "provider_call_allowed_now",
        )
    if decision.get("external_network_allowed_now") is not False:
        _add(
            violations,
            "STALE_CONFIRMATION_DECISION",
            "Activation boundary is diagnostic only and must not carry external_network_allowed_now true.",
            "external_network_allowed_now",
        )

    return {
        "activation_safe": not violations,
        "violations": violations,
        "activation_scope": "confirmed_execution_boundary_only",
    }


def _check_expiry(
    decision: dict[str, Any],
    previous_decision: dict[str, Any] | None,
    now_dt: datetime | None,
    violations: list[dict],
) -> None:
    stage = decision.get("lifecycle_stage")
    created = parse_datetime(decision.get("created_at"))
    expires = parse_datetime(decision.get("expires_at"))
    if stage in {"awaiting_confirmation", "confirmed_execution"}:
        if expires is None:
            _add(
                violations,
                "CONFIRMATION_EXPIRY_MISSING",
                "Confirmation lifecycle decisions require expires_at.",
                "expires_at",
            )
            return
        if created is None or created >= expires:
            _add(
                violations,
                "CONFIRMATION_EXPIRY_MISSING",
                "Confirmation expiry must be after created_at.",
                "expires_at",
            )
        if now_dt is not None and now_dt > expires:
            _add(
                violations,
                "STALE_CONFIRMATION_DECISION",
                "Confirmation decision is expired.",
                "expires_at",
            )
    if stage == "confirmed_execution":
        activation = evaluate_confirmed_execution_activation_boundary(
            decision,
            previous_decision,
            now=now_dt.isoformat() if now_dt is not None else None,
        )
        violations.extend(activation["violations"])


def _check_redaction(input_obj: dict[str, Any], decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("external_network_allowed_now") is True:
        if decision.get("external_allowed") is not True:
            _add(
                violations,
                "EXTERNAL_NETWORK_WITHOUT_EXTERNAL_ALLOWED",
                "External network permission requires external_allowed true.",
                "external_allowed",
            )
        if decision.get("redaction_status") in {"required_pending", "failed"}:
            _add(
                violations,
                "EXTERNAL_NETWORK_WITHOUT_EXTERNAL_ALLOWED",
                "External network permission requires completed or unnecessary redaction.",
                "redaction_status",
            )
    if (
        decision.get("requested_action_type") in EXTERNAL_NETWORK_ACTIONS
        and decision.get("tool_execution_allowed_now") is True
        and decision.get("external_network_allowed_now") is not True
    ):
        _add(
            violations,
            "TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION",
            "Network-capable browser/tool/MCP execution requires external_network_allowed_now true.",
            "external_network_allowed_now",
        )
    if decision.get("redaction_status") in {"required_pending", "failed"}:
        for field in ("external_allowed", "provider_call_allowed_now", "external_network_allowed_now"):
            if decision.get(field) is not False:
                _add(
                    violations,
                    "REDACTION_PENDING_BUT_EXTERNAL_ALLOWED",
                    "Pending or failed redaction blocks external/provider/network access.",
                    field,
                )
        if (
            decision.get("requested_action_type") in EXTERNAL_NETWORK_ACTIONS
            and decision.get("tool_execution_allowed_now") is not False
        ):
            _add(
                violations,
                "REDACTION_PENDING_BUT_EXTERNAL_ALLOWED",
                "Networked tool/browser/MCP actions cannot run while redaction is pending or failed.",
                "tool_execution_allowed_now",
            )
    phase_a = _phase_a(input_obj)
    if phase_a.get("sensitivity_bucket_proposal") == "unknown" and decision.get("requested_action_type") in {
        "provider_call",
        "browser_search",
        "mcp_call",
        "tool_call",
    }:
        for field in ("external_allowed", "provider_call_allowed_now", "external_network_allowed_now"):
            if decision.get(field) is not False:
                _add(
                    violations,
                    "UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE",
                    "Unknown sensitivity cannot allow provider/network execution.",
                    field,
                )


def _check_action_environment(decision: dict[str, Any], violations: list[dict]) -> None:
    action = decision.get("requested_action_type")
    env = decision.get("environment_type")
    scope = decision.get("state_scope")
    if action == "provider_call" and (env != "provider_api" or scope != "external_provider"):
        _add(
            violations,
            "PROVIDER_CALL_ENVIRONMENT_MISMATCH",
            "provider_call requires provider_api environment and external_provider scope.",
            "environment_type",
        )
    if action == "file_write" and (env not in {"file_system", "codebase"} or scope not in {"local_file", "repo"}):
        _add(
            violations,
            "FILE_WRITE_ENVIRONMENT_MISMATCH",
            "file_write requires file_system/codebase environment and local_file/repo scope.",
            "environment_type",
        )
    if action == "terminal_command" and env != "terminal":
        _add(
            violations,
            "TERMINAL_ENVIRONMENT_MISMATCH",
            "terminal_command requires terminal environment.",
            "environment_type",
        )
    if action == "memory_write" and (env != "memory_store" or scope != "memory"):
        _add(
            violations,
            "MEMORY_WRITE_WITHOUT_POLICY",
            "memory_write requires memory_store environment and memory scope.",
            "environment_type",
        )
    if action == "browser_search" and (env != "browser" or scope != "browser"):
        _add(
            violations,
            "PROVIDER_CALL_ENVIRONMENT_MISMATCH",
            "browser_search requires browser environment and browser scope.",
            "environment_type",
        )


def _check_memory_policy(decision: dict[str, Any], violations: list[dict]) -> None:
    if decision.get("requested_action_type") != "memory_write":
        return
    policy = decision.get("memory_policy_result")
    if not isinstance(policy, dict):
        _add(
            violations,
            "MEMORY_WRITE_WITHOUT_POLICY",
            "memory_write requires memory_policy_result.",
            "memory_policy_result",
        )
        return
    if policy.get("passed") is False and decision.get("state_change_allowed_now") is not False:
        _add(
            violations,
            "MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED",
            "Failed memory policy must block state change.",
            "state_change_allowed_now",
        )
    if policy.get("contains_literal_secret") is True:
        if decision.get("state_change_allowed_now") is not False:
            _add(
                violations,
                "MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED",
                "Literal-secret memory policy must block state change.",
                "state_change_allowed_now",
            )
        if decision.get("redaction_required") is not True:
            _add(
                violations,
                "MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED",
                "Literal-secret memory policy requires redaction.",
                "redaction_required",
            )


def _check_provider_policy(input_obj: dict[str, Any], violations: list[dict]) -> None:
    policy = _provider_policy(input_obj)
    allowed = set(policy.get("allowed_provider_tiers") or [])
    blocked = set(policy.get("blocked_provider_tiers") or [])
    if allowed & blocked:
        _add(
            violations,
            "PROVIDER_POLICY_TIER_CONFLICT",
            "Provider policy allowed and blocked tiers must be disjoint.",
            "provider_policy",
        )


def _check_budget(input_obj: dict[str, Any], decision: dict[str, Any], violations: list[dict]) -> None:
    route_tier = decision.get("route_tier")
    max_tier = _budget_policy(input_obj).get("max_tier")
    if _is_executable_tier(route_tier) and max_tier in TIER_RANK:
        if TIER_RANK[route_tier] > TIER_RANK[max_tier]:
            _add(
                violations,
                "BUDGET_CAP_BYPASS",
                "Executable route tier exceeds budget policy max_tier.",
                "route_tier",
            )


def _check_sensitivity(input_obj: dict[str, Any], decision: dict[str, Any], violations: list[dict]) -> None:
    if _has_secret_signal(input_obj):
        if decision.get("external_allowed") is not False or decision.get("provider_call_allowed_now") is not False:
            _add(
                violations,
                "SECRET_WITH_EXTERNAL_ALLOWED",
                "Secret inputs cannot allow external/provider access.",
                "external_allowed",
            )
    if _is_private_context(input_obj):
        if decision.get("external_allowed") is not False or decision.get("provider_call_allowed_now") is not False:
            _add(
                violations,
                "PRIVATE_CONTEXT_WITH_EXTERNAL_ALLOWED",
                "Private/IP-sensitive context cannot allow external/provider access.",
                "external_allowed",
            )


def _check_reason_and_audit(input_obj: dict[str, Any], decision: dict[str, Any], violations: list[dict]) -> None:
    reason_codes = decision.get("reason_codes")
    if not isinstance(reason_codes, list) or not reason_codes:
        _add(violations, "REASON_CODE_MISSING", "Decision requires reason_codes.", "reason_codes")
    else:
        invalid = [code for code in reason_codes if code not in REASON_CODES]
        if invalid:
            _add(
                violations,
                "REASON_CODE_MISSING",
                f"Decision contains unknown reason code(s): {', '.join(map(str, invalid))}.",
                "reason_codes",
            )
    notes = decision.get("audit_notes")
    if not isinstance(notes, list) or not notes:
        _add(violations, "MISSING_AUDIT_NOTE", "Decision requires audit notes.", "audit_notes")
        return
    for index, note in enumerate(notes):
        if isinstance(note, str) and SECRET_ECHO_PATTERN.search(note):
            _add(
                violations,
                "AUDIT_NOTE_CONTAINS_SECRET",
                "Audit notes must not echo literal secrets.",
                f"audit_notes[{index}]",
            )


def validate_router_decision_semantics(
    input_obj: dict,
    decision: dict,
    previous_decision: dict | None = None,
    now: str | None = None,
) -> list[dict]:
    """Return deterministic RouterPolicy v3.1.1 semantic violations."""

    violations: list[dict] = []
    now_dt = parse_datetime(now) if now is not None else None

    _check_local_only(decision, violations)
    _check_blocked(decision, violations)
    _check_external_candidate(decision, violations)
    _check_answer_only(decision, violations)
    _check_side_effects(decision, violations)
    _check_confirmation_payload(decision, violations)
    _check_expiry(decision, previous_decision, now_dt, violations)
    _check_redaction(input_obj, decision, violations)
    _check_action_environment(decision, violations)
    _check_memory_policy(decision, violations)
    _check_provider_policy(input_obj, violations)
    _check_budget(input_obj, decision, violations)
    _check_sensitivity(input_obj, decision, violations)
    _check_reason_and_audit(input_obj, decision, violations)

    return violations


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    print("router_policy_semantic_validator is a library module; import validate_router_decision_semantics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
