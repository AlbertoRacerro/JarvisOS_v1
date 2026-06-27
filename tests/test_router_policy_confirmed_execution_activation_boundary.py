from __future__ import annotations

import copy
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_canonical_digest as digest_helper  # noqa: E402
import router_policy_semantic_validator as validator  # noqa: E402


NOW = "2026-06-24T08:30:00+00:00"


def base_confirmation_payload() -> dict:
    return {
        "scope": "external_provider_call",
        "target": "external:scientific_medium",
        "payload_preview": "Redacted summary for provider preflight.",
        "payload_preview_truncated": False,
        "full_payload_available_for_review": True,
        "payload_digest": "sha256:" + "1" * 64,
        "full_payload_digest": "sha256:" + "2" * 64,
        "redaction_status": "redacted",
        "estimated_tokens": 800,
        "estimated_cost_class": "medium",
        "side_effect_level": "high",
        "reversibility": "partially_reversible",
        "diff_summary": None,
        "full_diff_available_for_review": False,
        "full_diff_digest": None,
        "file_operations": [],
        "command": None,
        "cwd": None,
        "terminal_risk_summary": None,
        "env_preview_redacted": None,
        "network_access_expected": True,
        "writes_outside_workspace": False,
        "destructive_command_detected": False,
        "file_paths": [],
    }


def awaiting_confirmation_decision() -> dict:
    decision = {
        "decision_id": "decision-awaiting-001",
        "input_digest": "sha256:" + "3" * 64,
        "created_at": "2026-06-24T08:00:00+00:00",
        "expires_at": "2026-06-24T09:00:00+00:00",
        "lifecycle_stage": "awaiting_confirmation",
        "route_action": "ask_user_confirm",
        "route_tier": "USER_CONFIRM",
        "provider_candidate": "none",
        "proposed_external_target": "external:scientific_medium",
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "confirmation_required": True,
        "confirmation_payload_required": True,
        "confirmation_payload": base_confirmation_payload(),
        "confirmation_options": ["allow_once", "deny", "view_details"],
        "requires_new_decision_after_confirmation": True,
    }
    decision["confirmation_digest"] = digest_helper.compute_confirmation_digest(decision)["digest"]
    return decision


def confirmed_execution_decision(previous: dict) -> dict:
    return {
        "decision_id": "decision-confirmed-001",
        "input_digest": previous["input_digest"],
        "created_at": "2026-06-24T08:10:00+00:00",
        "expires_at": "2026-06-24T08:50:00+00:00",
        "lifecycle_stage": "confirmed_execution",
        "route_action": "route_external_candidate",
        "route_tier": "SCIENTIFIC_MEDIUM",
        "provider_candidate": "external:scientific_medium",
        "proposed_external_target": "external:scientific_medium",
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "confirmation_required": False,
        "confirmation_payload_required": False,
        "confirmation_payload": None,
        "confirmation_digest": None,
        "confirmation_options": [],
        "consent_context": {
            "consent_id": "consent-1",
            "confirmed_previous_decision_id": previous["decision_id"],
            "confirmed_confirmation_digest": previous["confirmation_digest"],
            "confirmation_action": "allow_once",
            "confirmed_at": "2026-06-24T08:10:00+00:00",
        },
    }


def activation_result(current: dict, previous: dict | None, *, now: str | None = NOW) -> dict:
    return validator.evaluate_confirmed_execution_activation_boundary(current, previous, now=now)


def codes(result: dict) -> set[str]:
    return {violation["code"] for violation in result["violations"]}


def test_valid_confirmed_execution_passes_activation_boundary_without_mutation():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current_before = copy.deepcopy(current)
    previous_before = copy.deepcopy(previous)

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is True
    assert result["violations"] == []
    assert result["activation_scope"] == "confirmed_execution_boundary_only"
    assert current == current_before
    assert previous == previous_before


def test_non_confirmed_lifecycle_fails_closed():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["lifecycle_stage"] = "awaiting_confirmation"

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_a4_revalidation_violation_makes_activation_fail():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["input_digest"] = "sha256:" + "4" * 64

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_missing_now_fails_closed():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    result = activation_result(current, previous, now=None)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_invalid_now_fails_closed():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    result = activation_result(current, previous, now="not-a-timestamp")

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_confirmed_at_before_previous_created_at_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_at"] = "2026-06-24T07:50:00+00:00"

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_confirmed_at_after_now_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_at"] = "2026-06-24T08:40:00+00:00"

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_confirmed_at_after_previous_expires_at_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_at"] = "2026-06-24T09:10:00+00:00"

    result = activation_result(current, previous, now="2026-06-24T09:20:00+00:00")

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_previous_created_at_missing_or_invalid_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    missing = copy.deepcopy(previous)
    missing["created_at"] = None
    result = activation_result(current, missing, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)

    invalid = copy.deepcopy(previous)
    invalid["created_at"] = "bad-time"
    result = activation_result(current, invalid, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_previous_expires_at_missing_or_invalid_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    missing = copy.deepcopy(previous)
    missing["expires_at"] = None
    result = activation_result(current, missing, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)

    invalid = copy.deepcopy(previous)
    invalid["expires_at"] = "bad-time"
    result = activation_result(current, invalid, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_action_not_allow_once_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmation_action"] = "deny"

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "CONSENT_CONTEXT_MISSING" in codes(result)


def test_target_drift_or_missing_current_target_fails():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["proposed_external_target"] = "external:frontier"

    result = activation_result(current, previous, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)

    missing = confirmed_execution_decision(previous)
    missing["proposed_external_target"] = None
    missing["provider_candidate"] = "none"
    result = activation_result(missing, previous, now=NOW)
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_current_live_confirmation_artifacts_fail_including_confirmation_digest():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["confirmation_required"] = True
    current["confirmation_payload_required"] = True
    current["confirmation_payload"] = copy.deepcopy(previous["confirmation_payload"])
    current["confirmation_digest"] = "sha256:" + "8" * 64
    current["confirmation_options"] = ["allow_once", "deny"]

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_activation_pass_does_not_grant_provider_call_allowed_now():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current_before = copy.deepcopy(current)

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is True
    assert current["provider_call_allowed_now"] is False
    assert current == current_before


def test_activation_pass_does_not_grant_external_network_allowed_now():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current_before = copy.deepcopy(current)

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is True
    assert current["external_network_allowed_now"] is False
    assert current == current_before


def test_route_action_route_tier_relabeling_does_not_rescue_invalid_activation():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["input_digest"] = "sha256:" + "4" * 64
    current["route_action"] = "answer_local"
    current["route_tier"] = "LOCAL_FAST"

    result = activation_result(current, previous, now=NOW)

    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)


def test_helper_uses_caller_supplied_now_only_and_contains_no_wall_clock_calls():
    source = inspect.getsource(validator.evaluate_confirmed_execution_activation_boundary)

    assert "datetime.now" not in source
    assert "time.time" not in source
    assert "utcnow(" not in source
