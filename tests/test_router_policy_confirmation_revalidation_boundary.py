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


def violation_codes(violations: list[dict]) -> set[str]:
    return {violation["code"] for violation in violations}


def test_valid_confirmed_execution_passes_revalidation_boundary():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert violations == []


def test_missing_now_fails_closed_for_confirmed_execution_revalidation():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    missing_now = validator.validate_confirmation_revalidation_boundary(current, previous, now=None)
    invalid_now = validator.validate_confirmation_revalidation_boundary(current, previous, now="not-a-timestamp")

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(missing_now)
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(invalid_now)


def test_missing_previous_decision_rejected():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    violations = validator.validate_confirmation_revalidation_boundary(current, None, now=NOW)

    assert "CONSENT_CONTEXT_MISSING" in violation_codes(violations)


def test_consent_digest_mismatch_rejected():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_confirmation_digest"] = "sha256:" + "9" * 64

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "CONSENT_DIGEST_MISMATCH" in violation_codes(violations)


def test_missing_confirmed_at_rejected():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_at"] = None

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "CONSENT_CONTEXT_MISSING" in violation_codes(violations)


def test_missing_or_expired_previous_confirmation_rejected():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    previous_missing_expiry = copy.deepcopy(previous)
    previous_missing_expiry["expires_at"] = None
    missing_expiry = validator.validate_confirmation_revalidation_boundary(current, previous_missing_expiry, now=NOW)
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(missing_expiry)

    previous_expired = copy.deepcopy(previous)
    expired = validator.validate_confirmation_revalidation_boundary(
        current,
        previous_expired,
        now="2026-06-24T09:30:00+00:00",
    )
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(expired)


def test_previous_digest_tampering_rejected_by_recomputed_a3_digest():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    tampered_previous = copy.deepcopy(previous)
    tampered_previous["confirmation_payload"]["target"] = "external:frontier"

    violations = validator.validate_confirmation_revalidation_boundary(current, tampered_previous, now=NOW)

    assert "CONSENT_DIGEST_MISMATCH" in violation_codes(violations)


def test_missing_or_drifted_input_digest_fails_closed():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    missing_current = copy.deepcopy(current)
    missing_current["input_digest"] = None
    violations = validator.validate_confirmation_revalidation_boundary(missing_current, previous, now=NOW)
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)

    missing_previous = copy.deepcopy(previous)
    missing_previous["input_digest"] = None
    violations = validator.validate_confirmation_revalidation_boundary(current, missing_previous, now=NOW)
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)

    drifted = copy.deepcopy(current)
    drifted["input_digest"] = "sha256:" + "4" * 64
    violations = validator.validate_confirmation_revalidation_boundary(drifted, previous, now=NOW)
    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_target_drift_rejected_where_representable():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["proposed_external_target"] = "external:frontier"

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_missing_current_target_rejected_when_previous_target_exists():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["proposed_external_target"] = None
    current["provider_candidate"] = "none"

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)

    local_provider = copy.deepcopy(current)
    local_provider["provider_candidate"] = "local:qwen"
    violations = validator.validate_confirmation_revalidation_boundary(local_provider, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_digest_match_does_not_mutate_or_grant_provider_network_permission():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    previous_before = copy.deepcopy(previous)
    current_before = copy.deepcopy(current)

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert violations == []
    assert previous == previous_before
    assert current == current_before
    assert current["provider_call_allowed_now"] is False
    assert current["external_network_allowed_now"] is False


def test_confirmed_execution_cannot_retain_live_confirmation_artifacts():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["confirmation_required"] = True
    current["confirmation_payload_required"] = True
    current["confirmation_payload"] = copy.deepcopy(previous["confirmation_payload"])
    current["confirmation_options"] = ["allow_once", "deny"]

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_confirmed_execution_cannot_retain_confirmation_digest():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["confirmation_digest"] = "sha256:" + "8" * 64

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_route_labels_remain_non_authority_for_revalidation():
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["input_digest"] = "sha256:" + "4" * 64
    current["route_action"] = "answer_local"
    current["route_tier"] = "LOCAL_FAST"

    violations = validator.validate_confirmation_revalidation_boundary(current, previous, now=NOW)

    assert "STALE_CONFIRMATION_DECISION" in violation_codes(violations)


def test_revalidation_helper_uses_caller_supplied_now_only():
    source = inspect.getsource(validator.validate_confirmation_revalidation_boundary)

    assert "datetime.now" not in source
    assert "time.time" not in source
