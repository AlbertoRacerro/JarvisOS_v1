"""Offline Phase B soft-review to RouterPolicy hint bridge for B1.

This module maps existing Phase B/Qwen advisory soft-review output into
RouterPolicy router/action hints. It is deterministic and side-effect free: it
does not call models, providers, responders, tools, memory, retrieval, or A3.
"""

from __future__ import annotations

import copy
from typing import Any


RECOGNIZED_SOFT_REASON_CODES = {
    "contextual_summary",
    "memory_candidate",
    "decision_candidate",
    "assumption_candidate",
    "evidence_candidate",
    "source_candidate",
    "clarification_context",
    "low_value",
    "blocked_by_phase_a",
    "unknown",
}
REQUIRED_PHASE_B_FIELDS = {
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
ROUTE_RELEVANT_UNCERTAINTY_TERMS = {
    "source",
    "target",
    "task",
    "domain",
    "routing",
    "provider",
    "retrieval",
    "file",
    "scope",
    "project",
    "context",
    "phase_b_labels",
}
SCIENTIFIC_DOMAINS = {
    "modeling",
    "bioprocess",
    "reactor_design",
}
SCIENTIFIC_TAGS = {
    "scientific",
    "engineering",
    "chemical",
    "bioprocess",
    "reactor",
    "modeling",
    "simulation",
}
SOFTWARE_DOMAINS = {"software", "local_ai", "memory", "retrieval"}
SOFTWARE_TAGS = {"software", "code", "architecture", "debugging", "memory", "retrieval", "local_ai"}
BENIGN_MEMORY_CARD_TYPES = {"none", "knowledge_card"}


def _phase_a(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("phase_a_signals") or {}


def _router(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("router_hint") or {}


def _action(input_obj: dict[str, Any]) -> dict[str, Any]:
    return input_obj.get("action_hint") or {}


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _has_non_low_reason(phase_a: dict[str, Any]) -> bool:
    reasons = phase_a.get("hard_reason_codes")
    if not isinstance(reasons, list) or not reasons:
        return True
    return any(reason != "low_risk" for reason in reasons)


def _has_hard_gate(input_obj: dict[str, Any]) -> bool:
    phase_a = _phase_a(input_obj)
    action = _action(input_obj)
    router = _router(input_obj)
    return any(
        (
            phase_a.get("contains_secret_or_credential") is True,
            phase_a.get("contains_raw_private_or_ip_sensitive_context") is True,
            phase_a.get("mentions_external_provider_or_upload_intent") is True,
            phase_a.get("clarification_required") is True,
            phase_a.get("requires_manual_review") is True and _has_non_low_reason(phase_a),
            phase_a.get("sensitivity_bucket_proposal") in {"secret", "sensitive", "unknown"},
            _has_non_low_reason(phase_a),
            action.get("needs_terminal") is True,
            action.get("needs_file_write") is True,
            action.get("needs_memory_write") is True,
            action.get("needs_provider_call") is True,
            router.get("needs_current_info") is True,
            router.get("needs_file_context") is True,
            router.get("needs_code_execution") is True,
        )
    )


def _missing_or_malformed_phase_b_fields(phase_b: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_PHASE_B_FIELDS:
        if field not in phase_b:
            missing.append(field)
    if not isinstance(phase_b.get("domain_tags"), list):
        missing.append("domain_tags:type")
    if not isinstance(phase_b.get("soft_uncertain_fields"), list):
        missing.append("soft_uncertain_fields:type")
    if not isinstance(phase_b.get("soft_reason_code"), str):
        missing.append("soft_reason_code:type")
    for field in (
        "summary_short",
        "project_bucket",
        "primary_domain",
        "storage_relevance",
        "usefulness_for_future_review",
        "possible_memory_card_type",
        "brief_rationale",
        "suggested_followup_question",
    ):
        if field in phase_b and not isinstance(phase_b.get(field), str):
            missing.append(f"{field}:type")
    return sorted(set(missing))


def _has_route_relevant_uncertainty(fields: list[str]) -> bool:
    lowered = " ".join(fields).lower()
    return any(term in lowered for term in ROUTE_RELEVANT_UNCERTAINTY_TERMS)


def derive_phase_b_quality(phase_b: dict[str, Any]) -> str:
    """Derive quality from real Phase B fields; Phase B has no confidence field."""

    if not isinstance(phase_b, dict):
        return "low"
    missing = _missing_or_malformed_phase_b_fields(phase_b)
    reason = phase_b.get("soft_reason_code")
    followup = _string(phase_b.get("suggested_followup_question")).strip()
    uncertain = _string_list(phase_b.get("soft_uncertain_fields"))
    if missing or reason not in RECOGNIZED_SOFT_REASON_CODES:
        return "low"
    if followup:
        return "low"
    if reason in {"unknown", "clarification_context", "blocked_by_phase_a"}:
        return "low"
    if _has_route_relevant_uncertainty(uncertain):
        return "low"
    if uncertain:
        return "medium"
    return "high"


def _domain_context(phase_b: dict[str, Any]) -> tuple[str, set[str]]:
    domain = _string(phase_b.get("primary_domain")).strip() or "unknown"
    tags = {tag.lower() for tag in _string_list(phase_b.get("domain_tags"))}
    return domain, tags


def _apply_metadata(output: dict[str, Any], *, applied: bool, reason: str, quality: str) -> None:
    metadata = output.setdefault("context_metadata", {})
    metadata["router_hint_source"] = "phase_b_soft_review" if applied else "phase_b_blocked_by_hard_gate"
    metadata["phase_b_router_hint_applied"] = applied
    metadata["phase_b_router_hint_reason"] = reason
    metadata["phase_b_quality_derived"] = quality


def _set_no_side_effect_action(output: dict[str, Any], *, requested_action_type: str = "answer", confidence: str) -> None:
    action = output.setdefault("action_hint", {})
    action.update(
        {
            "requested_action_type": requested_action_type,
            "modifies_state": False,
            "side_effect_level": "none",
            "reversibility": "reversible",
            "environment_type": "chat",
            "state_scope": "none",
            "needs_terminal": False,
            "needs_file_write": False,
            "needs_memory_write": False,
            "needs_provider_call": False,
            "confidence": confidence,
        }
    )


def _apply_domain_heuristics(router: dict[str, Any], phase_b: dict[str, Any]) -> None:
    domain, tags = _domain_context(phase_b)
    router["domain"] = domain
    if domain in SCIENTIFIC_DOMAINS or tags.intersection(SCIENTIFIC_TAGS):
        router["complexity"] = "medium"
        router["needs_reasoning"] = True
        router["needs_scientific_depth"] = True
    elif domain in SOFTWARE_DOMAINS or tags.intersection(SOFTWARE_TAGS):
        router["complexity"] = "medium"
        router["needs_reasoning"] = True
        router["needs_scientific_depth"] = False
        router["needs_code_execution"] = False
    elif domain in {"general", "personal", "personal_preference", "coursework"}:
        router["complexity"] = "low"
        router["needs_reasoning"] = False
        router["needs_scientific_depth"] = False
    else:
        router["complexity"] = "unknown"
        router["needs_reasoning"] = True
        router["needs_scientific_depth"] = False


def _force_review(output: dict[str, Any], *, quality: str, reason: str, complexity: str = "medium") -> dict[str, Any]:
    router = output.setdefault("router_hint", {})
    router.update(
        {
            "task_type": "review",
            "complexity": complexity,
            "confidence": quality if quality in {"low", "medium"} else "medium",
        }
    )
    _set_no_side_effect_action(output, requested_action_type="unknown", confidence=router["confidence"])
    _apply_metadata(output, applied=True, reason=reason, quality=quality)
    return output


def _force_clarification(output: dict[str, Any], *, quality: str, reason: str) -> dict[str, Any]:
    router = output.setdefault("router_hint", {})
    router.update(
        {
            "task_type": "clarification",
            "complexity": "unknown",
            "confidence": "low",
            "needs_reasoning": True,
        }
    )
    _set_no_side_effect_action(output, requested_action_type="unknown", confidence="low")
    _apply_metadata(output, applied=True, reason=reason, quality=quality)
    return output


def _apply_answer(output: dict[str, Any], phase_b: dict[str, Any], *, quality: str, reason: str) -> dict[str, Any]:
    router = output.setdefault("router_hint", {})
    _apply_domain_heuristics(router, phase_b)
    router.update(
        {
            "task_type": "answer",
            "confidence": "high" if quality == "high" else "medium",
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
        }
    )
    _set_no_side_effect_action(output, requested_action_type="answer", confidence=router["confidence"])
    _apply_metadata(output, applied=True, reason=reason, quality=quality)
    return output


def _memory_candidate_is_benign(phase_b: dict[str, Any], quality: str) -> bool:
    if quality not in {"high", "medium"}:
        return False
    storage = phase_b.get("storage_relevance")
    usefulness = phase_b.get("usefulness_for_future_review")
    card_type = phase_b.get("possible_memory_card_type")
    return bool(
        storage in {"none", "low"}
        and usefulness in {"none", "low"}
        and card_type in BENIGN_MEMORY_CARD_TYPES
    )


def _apply_source_candidate(output: dict[str, Any], *, quality: str) -> dict[str, Any]:
    router = output.setdefault("router_hint", {})
    router.update(
        {
            "task_type": "review",
            "complexity": "medium",
            "confidence": "medium" if quality in {"high", "medium"} else "low",
            "needs_reasoning": True,
            "needs_current_info": True,
            "needs_file_context": True,
            "needs_code_execution": False,
            "needs_scientific_depth": False,
        }
    )
    _set_no_side_effect_action(output, requested_action_type="unknown", confidence=router["confidence"])
    _apply_metadata(output, applied=True, reason="source_candidate_review", quality=quality)
    return output


def _preserve_hard_gate(output: dict[str, Any], *, quality: str) -> dict[str, Any]:
    router = output.setdefault("router_hint", {})
    if router.get("task_type") == "answer":
        router["task_type"] = "review"
    if router.get("complexity") == "low":
        router["complexity"] = "medium"
    router["confidence"] = "low"
    action = output.setdefault("action_hint", {})
    if action.get("requested_action_type") in {"answer", "local_model_call"}:
        action["requested_action_type"] = "unknown"
    action["confidence"] = "low"
    _apply_metadata(output, applied=False, reason="hard_gate_dominates", quality=quality)
    return output


def apply_phase_b_router_hint(
    input_obj: dict,
    *,
    phase_b_soft_proposal: dict | None = None,
    now: str | None = None,
) -> dict:
    """Return a deep-copied RouterPolicy input with Phase B advisory hints.

    `now` is accepted for API symmetry with other probes and intentionally unused.
    """

    del now
    output = copy.deepcopy(input_obj)
    phase_b = copy.deepcopy(phase_b_soft_proposal) if phase_b_soft_proposal is not None else output.get(
        "phase_b_soft_proposal"
    )
    if not isinstance(phase_b, dict):
        phase_b = {}
    output["phase_b_soft_proposal"] = phase_b
    quality = derive_phase_b_quality(phase_b)

    if _has_hard_gate(output):
        return _preserve_hard_gate(output, quality=quality)

    reason = phase_b.get("soft_reason_code")
    followup = _string(phase_b.get("suggested_followup_question")).strip()
    if followup:
        return _force_clarification(output, quality=quality, reason="suggested_followup_required")
    if quality == "low":
        return _force_review(output, quality=quality, reason="low_quality_phase_b", complexity="unknown")
    if reason == "clarification_context":
        return _force_clarification(output, quality=quality, reason="clarification_context")
    if reason in {"source_candidate"}:
        return _apply_source_candidate(output, quality=quality)
    if reason in {"decision_candidate", "assumption_candidate", "evidence_candidate", "blocked_by_phase_a"}:
        return _force_review(output, quality=quality, reason=f"{reason}_review", complexity="medium")
    if reason == "memory_candidate":
        if _memory_candidate_is_benign(phase_b, quality):
            return _apply_answer(output, phase_b, quality=quality, reason="memory_candidate_benign_answer")
        return _force_review(output, quality=quality, reason="memory_candidate_review", complexity="medium")
    if reason in {"contextual_summary", "low_value"}:
        return _apply_answer(output, phase_b, quality=quality, reason=f"{reason}_answer")
    return _force_review(output, quality="low", reason="unknown_soft_reason", complexity="unknown")


def validate_router_policy_input_shape(input_obj: Any) -> list[str]:
    """Small structural check for B1 tests; not full Draft 2020-12 validation."""

    errors: list[str] = []
    if not isinstance(input_obj, dict):
        return ["input is not object"]
    for field in (
        "message_text",
        "phase_a_signals",
        "phase_b_soft_proposal",
        "router_hint",
        "action_hint",
        "user_policy",
        "provider_policy",
        "budget_policy",
        "context_metadata",
    ):
        if field not in input_obj:
            errors.append(f"missing {field}")
    router = input_obj.get("router_hint")
    action = input_obj.get("action_hint")
    phase_a = input_obj.get("phase_a_signals")
    if isinstance(router, dict):
        if router.get("complexity") not in {"low", "medium", "high", "unknown"}:
            errors.append("router complexity invalid")
        if router.get("confidence") not in {"low", "medium", "high", "unknown"}:
            errors.append("router confidence invalid")
        for field in ("task_type", "domain"):
            if not isinstance(router.get(field), str):
                errors.append(f"router {field} invalid")
        for field in (
            "needs_reasoning",
            "needs_current_info",
            "needs_file_context",
            "needs_code_execution",
            "needs_scientific_depth",
        ):
            if field in router and not isinstance(router.get(field), bool):
                errors.append(f"router {field} invalid")
    else:
        errors.append("router_hint invalid")
    if isinstance(action, dict):
        if action.get("requested_action_type") not in {
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
        }:
            errors.append("action requested_action_type invalid")
        if action.get("side_effect_level") not in {"none", "low", "medium", "high", "irreversible", "unknown"}:
            errors.append("action side_effect_level invalid")
        for field in (
            "modifies_state",
            "needs_terminal",
            "needs_file_write",
            "needs_memory_write",
            "needs_provider_call",
        ):
            if not isinstance(action.get(field), bool):
                errors.append(f"action {field} invalid")
    else:
        errors.append("action_hint invalid")
    if isinstance(phase_a, dict):
        reasons = phase_a.get("hard_reason_codes")
        if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
            errors.append("phase_a hard_reason_codes invalid")
    else:
        errors.append("phase_a_signals invalid")
    return errors
