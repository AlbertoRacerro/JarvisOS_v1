from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.ai.routing import decision as canonical  # noqa: E402
import router_policy_decision_probe as decision_probe  # noqa: E402
import router_policy_message_route_smoke as smoke  # noqa: E402
from router_policy_external_egress_scope import evaluate_external_egress_scope  # noqa: E402


NOW = "2026-06-27T10:00:00+00:00"
DECISION_SCHEMA_PATH = ROOT / "schemas" / "router_policy_decision_v0_3_1_1.schema.json"
VALID_TARGET = "external:scientific_medium"


def load_decision_schema() -> dict:
    return json.loads(DECISION_SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_errors(value, schema, path="$"):
    errors = []
    schema_type = schema.get("type")
    allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
    if "null" in allowed_types and value is None:
        return errors

    def type_matches(expected_type):
        if expected_type == "object":
            return isinstance(value, dict)
        if expected_type == "array":
            return isinstance(value, list)
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        if expected_type is None:
            return True
        return False

    if allowed_types and not any(type_matches(item) for item in allowed_types):
        errors.append(f"{path}: invalid type")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: invalid const")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: invalid enum")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength")
        if "pattern" in schema and not re.match(schema["pattern"], value):
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: below minimum")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: below minItems")
        if schema.get("uniqueItems") and len(value) != len(set(json.dumps(item, sort_keys=True) for item in value)):
            errors.append(f"{path}: duplicate array values")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(schema_errors(item, item_schema, f"{path}[{index}]"))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{path}.{field}: missing required")
        if schema.get("additionalProperties") is False:
            for field in value:
                if field not in properties:
                    errors.append(f"{path}.{field}: additional property")
        for field, item in value.items():
            if field in properties:
                errors.extend(schema_errors(item, properties[field], f"{path}.{field}"))
    return errors


def assert_schema_valid_decision(decision: dict) -> None:
    assert schema_errors(decision, load_decision_schema()) == []


def safe_input(message: str = "Analyze this public scientific task deeply.") -> dict:
    return smoke.build_router_policy_input_from_message_for_smoke(
        message,
        now=NOW,
        assume_public_simple=True,
    )


def external_candidate_input(flag_value, *, requires_confirmation: bool) -> dict:
    input_obj = safe_input()
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
    input_obj["user_policy"]["external_requires_confirmation"] = requires_confirmation
    if flag_value == "missing":
        input_obj["user_policy"].pop("external_routing_enabled", None)
    else:
        input_obj["user_policy"]["external_routing_enabled"] = flag_value
    return input_obj


def provider_policy_denied_input() -> dict:
    input_obj = external_candidate_input(True, requires_confirmation=True)
    input_obj["provider_policy"] = {
        "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST"],
        "blocked_provider_tiers": [],
    }
    input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
    return input_obj


def budget_policy_denied_input() -> dict:
    input_obj = external_candidate_input(True, requires_confirmation=True)
    input_obj["provider_policy"] = {
        "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
        "blocked_provider_tiers": [],
    }
    input_obj["budget_policy"]["max_tier"] = "LOCAL_FAST"
    return input_obj


def assert_no_actionable_external_artifacts(decision: dict) -> None:
    assert decision["external_allowed"] is False
    assert decision["external_network_allowed_now"] is False
    assert decision["provider_call_allowed_now"] is False
    assert decision["confirmation_required"] is False
    assert decision["confirmation_payload_required"] is False
    assert decision["confirmation_payload"] is None
    assert decision["confirmation_digest"] is None
    assert decision["confirmation_options"] == []


def test_e4_a1_helper_none_target_denied():
    decision = evaluate_external_egress_scope(None, [VALID_TARGET])

    assert decision["allowed"] is False
    assert decision["reason_code"] == "missing_target"


def test_e4_a1_helper_invalid_target_denied():
    decision = evaluate_external_egress_scope("external:test", [VALID_TARGET])

    assert decision["allowed"] is False
    assert decision["reason_code"] == "invalid_target"


def test_e4_a1_helper_valid_target_not_in_allowed_targets_denied():
    decision = evaluate_external_egress_scope(VALID_TARGET, ["external:cheap"])

    assert decision["allowed"] is False
    assert decision["reason_code"] == "target_not_in_allowed_targets"


def test_e4_a1_helper_valid_target_in_allowed_targets_allowed():
    decision = evaluate_external_egress_scope(VALID_TARGET, ["external:cheap", VALID_TARGET])

    assert decision["allowed"] is True
    assert decision["reason_code"] == "target_allowed"


def test_e4_a1_helper_empty_allowed_targets_denied():
    decision = evaluate_external_egress_scope(VALID_TARGET, [])

    assert decision["allowed"] is False
    assert decision["reason_code"] == "target_not_in_allowed_targets"


def test_e4_a1_helper_allowed_targets_order_does_not_change_result():
    left = evaluate_external_egress_scope(VALID_TARGET, ["external:cheap", VALID_TARGET, "external:frontier"])
    right = evaluate_external_egress_scope(VALID_TARGET, ["external:frontier", VALID_TARGET, "external:cheap"])

    assert left == right


@pytest.mark.parametrize("flag_value", (False, None, "true", 1))
def test_e4_a1_public_flag_not_exactly_true_still_scrubs_all_external_artifacts(flag_value):
    decision = decision_probe.decide_router_policy(
        external_candidate_input(flag_value, requires_confirmation=True),
        now=NOW,
    )

    assert decision["proposed_external_target"] is None
    assert_no_actionable_external_artifacts(decision)
    assert_schema_valid_decision(decision)


def test_e4_a1_forced_helper_deny_keeps_visible_proposal_but_clears_confirmation(monkeypatch):
    calls = {"count": 0, "args": None}

    def deny_scope(proposed_external_target, allowed_targets):
        calls["count"] += 1
        calls["args"] = (proposed_external_target, tuple(allowed_targets))
        return {
            "allowed": False,
            "proposed_external_target": proposed_external_target,
            "normalized_allowed_targets": tuple(sorted(set(allowed_targets))),
            "reason_code": "target_not_in_allowed_targets",
            "reason_codes": ["target_not_in_allowed_targets"],
        }

    monkeypatch.setattr(canonical, "evaluate_external_egress_scope", deny_scope)

    decision = decision_probe.decide_router_policy(
        external_candidate_input(True, requires_confirmation=True),
        now=NOW,
    )

    assert calls["count"] > 0
    assert calls["args"] == (VALID_TARGET, (VALID_TARGET,))
    assert decision["proposed_external_target"] == VALID_TARGET
    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert_no_actionable_external_artifacts(decision)
    assert_schema_valid_decision(decision)


def test_e4_a1_public_flag_true_natural_egress_denied_by_provider_policy(monkeypatch):
    calls = []
    original = canonical.evaluate_external_egress_scope

    def spy(proposed_external_target, allowed_targets):
        result = original(proposed_external_target, allowed_targets)
        calls.append((proposed_external_target, tuple(allowed_targets), dict(result)))
        return result

    monkeypatch.setattr(canonical, "evaluate_external_egress_scope", spy)

    decision = decision_probe.decide_router_policy(
        provider_policy_denied_input(),
        now=NOW,
    )

    assert calls
    proposed_external_target, allowed_targets, result = calls[-1]
    assert proposed_external_target == VALID_TARGET
    assert VALID_TARGET not in allowed_targets
    assert result["allowed"] is False
    assert result["reason_code"] == "target_not_in_allowed_targets"
    assert decision["proposed_external_target"] == VALID_TARGET
    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert_no_actionable_external_artifacts(decision)
    assert_schema_valid_decision(decision)


def test_e4_a1_public_flag_true_natural_egress_denied_by_budget_policy(monkeypatch):
    calls = []
    original = canonical.evaluate_external_egress_scope

    def spy(proposed_external_target, allowed_targets):
        result = original(proposed_external_target, allowed_targets)
        calls.append((proposed_external_target, tuple(allowed_targets), dict(result)))
        return result

    monkeypatch.setattr(canonical, "evaluate_external_egress_scope", spy)

    decision = decision_probe.decide_router_policy(
        budget_policy_denied_input(),
        now=NOW,
    )

    assert calls
    proposed_external_target, allowed_targets, result = calls[-1]
    assert proposed_external_target == VALID_TARGET
    assert VALID_TARGET not in allowed_targets
    assert result["allowed"] is False
    assert result["reason_code"] == "target_not_in_allowed_targets"
    assert decision["proposed_external_target"] == VALID_TARGET
    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert_no_actionable_external_artifacts(decision)
    assert_schema_valid_decision(decision)


def test_e4_a1_public_flag_true_egress_allowed_remains_proposal_only_without_new_confirmation(monkeypatch):
    calls = {"count": 0, "args": None}
    original = canonical.evaluate_external_egress_scope

    def allow_scope(proposed_external_target, allowed_targets):
        calls["count"] += 1
        calls["args"] = (proposed_external_target, tuple(allowed_targets))
        return original(proposed_external_target, allowed_targets)

    monkeypatch.setattr(canonical, "evaluate_external_egress_scope", allow_scope)

    decision = decision_probe.decide_router_policy(
        external_candidate_input(True, requires_confirmation=False),
        now=NOW,
    )

    assert calls["count"] > 0
    assert calls["args"] == (VALID_TARGET, (VALID_TARGET,))
    assert decision["proposed_external_target"] == VALID_TARGET
    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert_no_actionable_external_artifacts(decision)
    assert_schema_valid_decision(decision)
