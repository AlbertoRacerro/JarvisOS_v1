from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_canonical_digest as digest_helper  # noqa: E402
import router_policy_decision_probe as decision_probe  # noqa: E402
import router_policy_message_route_smoke as smoke  # noqa: E402
import router_policy_semantic_validator as validator  # noqa: E402


NOW = "2026-06-27T10:00:00+00:00"


def external_candidate_input(*, external_routing_enabled: bool, external_requires_confirmation: bool) -> dict:
    input_obj = smoke.build_router_policy_input_from_message_for_smoke(
        "Analyze this public scientific task deeply.",
        now=NOW,
        assume_public_simple=True,
    )
    input_obj["phase_a_signals"].update(
        {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "clarification_required": False,
            "hard_reason_codes": ["low_risk"],
            "sensitivity_bucket_proposal": "public",
            "requires_manual_review": False,
        }
    )
    input_obj["router_hint"].update(
        {
            "task_type": "analysis",
            "complexity": "high",
            "domain": "scientific",
            "needs_scientific_depth": True,
            "needs_reasoning": True,
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
        }
    )
    input_obj["provider_policy"] = {
        "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
        "blocked_provider_tiers": ["FRONTIER"],
    }
    input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
    input_obj["user_policy"]["external_routing_enabled"] = external_routing_enabled
    input_obj["user_policy"]["external_requires_confirmation"] = external_requires_confirmation
    return input_obj


def test_confirmation_bearing_public_router_proposal_gets_bound_digest():
    input_obj = external_candidate_input(external_routing_enabled=True, external_requires_confirmation=True)

    decision = decision_probe.decide_router_policy(input_obj, now=NOW)
    recomputed = digest_helper.compute_confirmation_digest(decision)

    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert decision["confirmation_required"] is True
    assert decision["confirmation_payload_required"] is True
    assert decision["confirmation_payload"] is not None
    assert decision["confirmation_options"] == ["allow_once", "deny", "view_details"]
    assert decision["confirmation_digest"] == recomputed["digest"]
    assert recomputed["canonical_envelope"]["digest_purpose"] == "router_confirmation_intent"
    assert recomputed["canonical_envelope"]["digest_version"] == "v1"
    assert decision["provider_call_allowed_now"] is False
    assert decision["external_network_allowed_now"] is False
    assert validator.validate_router_decision_semantics(input_obj, decision, now=NOW) == []


def test_digest_validation_mismatch_blocks_integrity_only_without_mutation():
    input_obj = external_candidate_input(external_routing_enabled=True, external_requires_confirmation=True)
    decision = decision_probe.decide_router_policy(input_obj, now=NOW)
    mutated = copy.deepcopy(decision)
    mutated["confirmation_payload"]["target"] = "external:frontier"
    before = copy.deepcopy(mutated)

    integrity = digest_helper.validate_confirmation_digest_integrity(mutated)
    violations = validator.validate_router_decision_semantics(input_obj, mutated, now=NOW)

    assert integrity["valid"] is False
    assert mutated == before
    assert mutated["provider_call_allowed_now"] is False
    assert mutated["external_network_allowed_now"] is False
    assert any(violation["code"] == "CONFIRMATION_DIGEST_INVALID" for violation in violations)


def test_targetless_finalizer_scrubs_digest_and_confirmation_artifacts():
    input_obj = external_candidate_input(external_routing_enabled=True, external_requires_confirmation=True)
    decision = decision_probe.decide_router_policy(input_obj, now=NOW)
    forced = copy.deepcopy(decision)
    forced["proposed_external_target"] = None

    scrubbed = decision_probe._enforce_external_proposal_flag_invariant(input_obj, forced)

    assert scrubbed["proposed_external_target"] is None
    assert scrubbed["confirmation_required"] is False
    assert scrubbed["confirmation_payload_required"] is False
    assert scrubbed["confirmation_payload"] is None
    assert scrubbed["confirmation_digest"] is None
    assert scrubbed["confirmation_options"] == []


def test_local_fallback_clears_digest_without_public_confirmation_flow():
    input_obj = external_candidate_input(external_routing_enabled=False, external_requires_confirmation=True)

    decision = decision_probe.decide_router_policy(input_obj, now=NOW)

    assert decision["route_action"] == "route_local"
    assert decision["route_tier"] == "LOCAL_FAST"
    assert decision["proposed_external_target"] is None
    assert decision["confirmation_required"] is False
    assert decision["confirmation_payload_required"] is False
    assert decision["confirmation_payload"] is None
    assert decision["confirmation_digest"] is None
    assert decision["confirmation_options"] == []


def test_requires_new_decision_after_confirmation_is_lifecycle_only_in_bound_digest():
    input_obj = external_candidate_input(external_routing_enabled=True, external_requires_confirmation=True)
    decision = decision_probe.decide_router_policy(input_obj, now=NOW)
    toggled = copy.deepcopy(decision)
    toggled["requires_new_decision_after_confirmation"] = False

    original = digest_helper.compute_confirmation_digest(decision)
    changed = digest_helper.compute_confirmation_digest(toggled)

    assert original["canonical_payload"] == changed["canonical_payload"]
    assert original["digest"] == changed["digest"]
