"""Deterministic external-egress gate for RouterPolicy E1.

This module only evaluates whether a concrete outbound payload may be considered
for external sharing. It does not execute provider calls, route traffic, mutate
RouterPolicy decisions, or grant future external eligibility.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import router_policy_message_route_smoke as smoke


SUPPORTED_COMPONENT_TYPES = {"current_message", "history_turn"}
POSITIVE_OPERATIONAL_CATEGORIES = {
    "memory_write",
    "document_project_write",
    "credential_like_save",
}
BLANKET_CONSERVATIVE_REASON_CODES = {"manual_review_required", "unknown_sensitivity"}


def _component_identity(component: dict[str, Any], index: int) -> str:
    identity = component.get("id")
    if isinstance(identity, str) and identity.strip():
        return identity
    component_type = component.get("type")
    if isinstance(component_type, str) and component_type.strip():
        return f"{component_type}:{index}"
    return f"component:{index}"


def _canonical_component(component: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": _component_identity(component, index),
        "type": component.get("type"),
        "text": component.get("text"),
    }


def _payload_digest(components: list[dict[str, Any]]) -> str:
    encoded = json.dumps(components, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _component_list(components: Any) -> list[dict[str, Any]] | None:
    if not isinstance(components, list):
        return None
    if not all(isinstance(component, dict) for component in components):
        return None
    return components


def _positive_hard_reason_codes(phase_a: dict[str, Any], operational_categories: set[str]) -> list[str]:
    positive: list[str] = []
    for reason in phase_a.get("hard_reason_codes") or []:
        if reason == "low_risk":
            continue
        if reason in BLANKET_CONSERVATIVE_REASON_CODES and not operational_categories:
            continue
        positive.append(reason)
    return positive


def _derive_component_safety(
    component: dict[str, Any],
    *,
    index: int,
    input_builder=smoke.build_router_policy_input_from_message_for_smoke,
) -> dict[str, Any]:
    identity = _component_identity(component, index)
    component_type = component.get("type")
    if component_type not in SUPPORTED_COMPONENT_TYPES:
        return {
            "identity": identity,
            "evaluated": False,
            "derivation_succeeded": False,
            "reason_code": "unsupported_component_type",
            "positive_danger_signals": [],
        }

    text = component.get("text")
    if not isinstance(text, str) or not text.strip():
        return {
            "identity": identity,
            "evaluated": False,
            "derivation_succeeded": False,
            "reason_code": "missing_component_text",
            "positive_danger_signals": [],
        }

    try:
        input_obj = input_builder(text, assume_public_simple=False)
    except Exception as exc:
        return {
            "identity": identity,
            "evaluated": False,
            "derivation_succeeded": False,
            "reason_code": "unable_to_derive_component_safety",
            "error_type": type(exc).__name__,
            "positive_danger_signals": [],
        }

    input_obj = copy.deepcopy(input_obj)
    phase_a = input_obj.get("phase_a_signals") or {}
    action_hint = input_obj.get("action_hint") or {}
    metadata = input_obj.get("context_metadata") or {}
    operational_categories = set(metadata.get("operational_intent_categories") or [])
    positive_signals: list[str] = []

    if phase_a.get("contains_secret_or_credential") is True:
        positive_signals.append("contains_secret_or_credential_context")
    if phase_a.get("contains_raw_private_or_ip_sensitive_context") is True:
        positive_signals.append("contains_raw_private_or_ip_sensitive_context")

    sensitivity = phase_a.get("sensitivity_bucket_proposal")
    if sensitivity in {"sensitive", "secret"}:
        positive_signals.append(f"sensitivity_bucket_proposal:{sensitivity}")
    if smoke._has_bluerev_ip_sensitive_marker(text) and sensitivity == "sensitive":
        positive_signals.append("bluerev_ip_sensitivity_floor")

    for category in sorted(operational_categories & POSITIVE_OPERATIONAL_CATEGORIES):
        positive_signals.append(f"operational_intent:{category}")
    if action_hint.get("needs_memory_write") is True:
        positive_signals.append("memory_write")
    if action_hint.get("needs_file_write") is True:
        positive_signals.append("document_write")

    for reason in _positive_hard_reason_codes(phase_a, operational_categories):
        positive_signals.append(f"hard_reason_code:{reason}")

    return {
        "identity": identity,
        "evaluated": True,
        "derivation_succeeded": True,
        "reason_code": "ok",
        "positive_danger_signals": sorted(set(positive_signals)),
        "sensitivity_bucket_proposal": sensitivity,
    }


def evaluate_external_egress_gate(
    payload_components: Any,
    *,
    explicit_user_shareability_opt_in: bool,
    provider_payload_components: Any | None = None,
    input_builder=smoke.build_router_policy_input_from_message_for_smoke,
) -> dict[str, Any]:
    """Return structured E1 allow/deny for one exact outbound payload."""

    components = _component_list(payload_components)
    if components is None:
        return {
            "allowed": False,
            "reason_code": "invalid_component_list",
            "reason_codes": ["invalid_component_list"],
            "explicit_user_shareability_opt_in": explicit_user_shareability_opt_in is True,
            "checked_component_count": 0,
            "checked_component_identities": [],
            "component_results": [],
        }

    evaluated_components = [_canonical_component(component, index) for index, component in enumerate(components)]
    provider_components = components if provider_payload_components is None else _component_list(provider_payload_components)
    provider_canonical = (
        None
        if provider_components is None
        else [_canonical_component(component, index) for index, component in enumerate(provider_components)]
    )
    evaluated_digest = _payload_digest(evaluated_components)
    provider_digest = None if provider_canonical is None else _payload_digest(provider_canonical)

    component_results = [
        _derive_component_safety(component, index=index, input_builder=input_builder)
        for index, component in enumerate(components)
    ]
    checked_identities = [
        result["identity"] for result in component_results if result.get("evaluated") is True
    ]
    base = {
        "explicit_user_shareability_opt_in": explicit_user_shareability_opt_in is True,
        "checked_component_count": len(checked_identities),
        "checked_component_identities": checked_identities,
        "component_results": component_results,
        "evaluated_payload_digest": evaluated_digest,
        "provider_payload_digest": provider_digest,
    }

    if provider_canonical is None:
        return {
            **base,
            "allowed": False,
            "reason_code": "invalid_provider_component_list",
            "reason_codes": ["invalid_provider_component_list"],
        }
    if provider_digest != evaluated_digest:
        return {
            **base,
            "allowed": False,
            "reason_code": "payload_component_mismatch",
            "reason_codes": ["payload_component_mismatch"],
        }
    failed = [result for result in component_results if result.get("derivation_succeeded") is not True]
    if failed:
        reason = failed[0].get("reason_code") or "unable_to_derive_component_safety"
        return {**base, "allowed": False, "reason_code": reason, "reason_codes": [reason]}

    positive = [
        {"identity": result["identity"], "signals": result["positive_danger_signals"]}
        for result in component_results
        if result.get("positive_danger_signals")
    ]
    if positive:
        return {
            **base,
            "allowed": False,
            "reason_code": "positive_danger_signal",
            "reason_codes": ["positive_danger_signal"],
            "positive_danger_components": positive,
        }
    if explicit_user_shareability_opt_in is not True:
        return {
            **base,
            "allowed": False,
            "reason_code": "explicit_shareability_opt_in_required",
            "reason_codes": ["explicit_shareability_opt_in_required"],
        }
    return {**base, "allowed": True, "reason_code": "allowed_unknown_clean_with_opt_in", "reason_codes": ["allowed_unknown_clean_with_opt_in"]}
