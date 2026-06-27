from __future__ import annotations

import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_canonical_digest as digest_helper  # noqa: E402


def base_intent() -> dict:
    return {
        "proposed_external_target": "external:scientific_medium",
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "confirmation_required": True,
        "confirmation_payload_required": True,
        "confirmation_payload": {
            "scope": "external_provider_call",
            "target": "external:scientific_medium",
            "payload_preview": "Redacted summary for provider review.",
            "payload_preview_truncated": False,
            "full_payload_available_for_review": True,
            "payload_digest": "sha256:" + "1" * 64,
            "full_payload_digest": "sha256:" + "2" * 64,
            "redaction_status": "redacted",
            "estimated_tokens": 800,
            "estimated_cost_class": "medium",
            "side_effect_level": "none",
            "reversibility": "reversible",
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
        },
        "confirmation_options": ["allow_once", "deny", "view_details"],
        "confirmation_digest": "sha256:" + "3" * 64,
        "route_action": "ask_user_confirm",
        "route_tier": "USER_CONFIRM",
        "requires_new_decision_after_confirmation": True,
        "reason_codes": ["confirmation_required"],
        "audit_notes": ["Display-only note."],
    }


def test_same_canonical_safety_intent_gives_same_digest_despite_key_order():
    intent_a = base_intent()
    intent_b = {
        "confirmation_options": ["allow_once", "deny", "view_details"],
        "confirmation_payload": {
            "full_payload_digest": "sha256:" + "2" * 64,
            "payload_digest": "sha256:" + "1" * 64,
            "scope": "external_provider_call",
            "target": "external:scientific_medium",
            "payload_preview": "Redacted summary for provider review.",
            "payload_preview_truncated": False,
            "full_payload_available_for_review": True,
            "redaction_status": "redacted",
            "estimated_tokens": 800,
            "estimated_cost_class": "medium",
            "side_effect_level": "none",
            "reversibility": "reversible",
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
        },
        "confirmation_payload_required": True,
        "confirmation_required": True,
        "external_network_allowed_now": False,
        "provider_call_allowed_now": False,
        "proposed_external_target": "external:scientific_medium",
    }

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] == result_b["digest"]
    assert result_a["canonical_payload"] == result_b["canonical_payload"]


def test_different_safety_relevant_target_changes_digest():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["proposed_external_target"] = "external:frontier"

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] != result_b["digest"]


def test_different_confirmation_payload_changes_digest():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["confirmation_payload"]["target"] = "external:frontier"

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] != result_b["digest"]


def test_non_safety_explanatory_text_outside_confirmation_payload_does_not_change_digest():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["audit_notes"] = ["Completely different note."]
    intent_b["reason_codes"] = ["budget_cap", "default_local_fallback"]

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] == result_b["digest"]


def test_digest_excludes_itself():
    intent_without_digest = base_intent()
    intent_with_digest = base_intent()
    intent_with_digest["confirmation_digest"] = "sha256:" + "9" * 64
    intent_with_digest["digest"] = "sha256:" + "8" * 64

    result_a = digest_helper.compute_confirmation_digest(intent_without_digest)
    result_b = digest_helper.compute_confirmation_digest(intent_with_digest)

    assert result_a["digest"] == result_b["digest"]


def test_stable_nested_ordering_inside_digest_relevant_payload():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["confirmation_payload"] = {
        "payload_digest": "sha256:" + "1" * 64,
        "target": "external:scientific_medium",
        "scope": "external_provider_call",
        "payload_preview": "Redacted summary for provider review.",
        "payload_preview_truncated": False,
        "full_payload_available_for_review": True,
        "full_payload_digest": "sha256:" + "2" * 64,
        "redaction_status": "redacted",
        "estimated_tokens": 800,
        "estimated_cost_class": "medium",
        "side_effect_level": "none",
        "reversibility": "reversible",
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

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] == result_b["digest"]


def test_confirmation_options_list_order_is_semantically_meaningful():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["confirmation_options"] = ["deny", "allow_once", "view_details"]

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] != result_b["digest"]


def test_helper_uses_no_runtime_entropy_or_external_state():
    source = inspect.getsource(digest_helper)

    for forbidden in (
        "datetime",
        "time(",
        "uuid",
        "random",
        "os.environ",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "gemini",
        "Path(",
        ".write_text(",
        ".write_bytes(",
        "id(",
    ):
        assert forbidden not in source


def test_route_action_and_route_tier_are_not_actionability_authority_for_digest():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["route_action"] = "blocked"
    intent_b["route_tier"] = "BLOCKED"

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] == result_b["digest"]


def test_requires_new_decision_after_confirmation_is_reserved_for_later_binding():
    intent_a = base_intent()
    intent_b = base_intent()
    intent_b["requires_new_decision_after_confirmation"] = False

    result_a = digest_helper.compute_confirmation_digest(intent_a)
    result_b = digest_helper.compute_confirmation_digest(intent_b)

    assert result_a["digest"] == result_b["digest"]


def test_canonical_payload_contains_only_digest_relevant_fields():
    result = digest_helper.compute_confirmation_digest(base_intent())

    assert tuple(result["canonical_payload"].keys()) == (
        "proposed_external_target",
        "provider_call_allowed_now",
        "external_network_allowed_now",
        "confirmation_required",
        "confirmation_payload_required",
        "confirmation_payload",
        "confirmation_options",
    )
