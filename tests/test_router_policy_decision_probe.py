import copy
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_decision_probe as probe  # noqa: E402
import router_policy_semantic_validator as validator  # noqa: E402


FIXTURE_PATH = ROOT / "tests/fixtures/router_policy/base_router_policy_fixture.json"
DECISION_SCHEMA_PATH = ROOT / "schemas/router_policy_decision_v0_3_1_1.schema.json"
NOW = "2026-06-24T10:00:00+00:00"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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


class RouterPolicyDecisionProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE_PATH)
        cls.decision_schema = load_json(DECISION_SCHEMA_PATH)

    def base_input(self):
        return copy.deepcopy(self.fixture["input"])

    def assert_valid_decision(self, input_obj, decision):
        self.assertEqual([], schema_errors(decision, self.decision_schema))
        self.assertEqual([], validator.validate_router_decision_semantics(input_obj, decision, now=NOW))
        self.assertEqual("router_policy_v0_3_1_1", decision["policy_version"])
        self.assertEqual("router_policy_decision_v0_3_1_1", decision["schema_version"])
        self.assertEqual(validator.canonical_json_digest(input_obj), decision["input_digest"])
        self.assertFalse(decision["tool_execution_allowed_now"])
        if decision["requested_action_type"] in {"browser_search", "tool_call", "mcp_call"}:
            self.assertFalse(decision["tool_execution_allowed_now"])
        if decision["external_allowed"] is False:
            self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))
        self.assertFalse(
            decision["external_network_allowed_now"] is True and decision["external_allowed"] is False,
            decision,
        )
        for note in decision["audit_notes"]:
            self.assertNotRegex(note, validator.SECRET_ECHO_PATTERN)

    def decide(self, input_obj):
        decision = probe.decide_router_policy(input_obj, now=NOW)
        self.assert_valid_decision(input_obj, decision)
        return decision

    def enable_external_policy(self, input_obj):
        input_obj["user_policy"]["external_routing_enabled"] = True
        input_obj["user_policy"]["external_requires_confirmation"] = True
        input_obj["provider_policy"] = {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
            "blocked_provider_tiers": ["FRONTIER"],
        }
        input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
        input_obj["phase_a_signals"]["external_provider_allowed"] = True
        return input_obj

    def make_high_complexity_public(self):
        input_obj = self.enable_external_policy(self.base_input())
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "public"
        input_obj["router_hint"].update(
            {
                "task_type": "analysis",
                "complexity": "high",
                "domain": "scientific",
                "needs_scientific_depth": True,
                "needs_reasoning": True,
            }
        )
        return input_obj

    def test_a2_001_secret_literal_blocks_external(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Do not expose API key sk-test-secret-12345678."
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "secret"
        decision = self.decide(input_obj)
        self.assertEqual("blocked", decision["route_action"])
        self.assertEqual("BLOCKED", decision["route_tier"])
        self.assertFalse(decision["external_allowed"])
        self.assertFalse(decision["external_network_allowed_now"])
        self.assertFalse(decision["provider_call_allowed_now"])
        self.assertFalse(decision["tool_execution_allowed_now"])
        self.assertFalse(decision["state_change_allowed_now"])

    def test_a2_002_bluerev_ip_sensitive_stays_local_only(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Keep this proprietary BlueRev growth calculation local."
        input_obj["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "sensitive"
        decision = self.decide(input_obj)
        self.assertIn(decision["route_tier"], {"LOCAL_ONLY", "USER_CONFIRM"})
        self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))
        self.assertFalse(decision["external_allowed"])

    def test_a2_003_private_memory_external_provider_intent_requires_review(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Send my JarvisOS memory folder to Claude for architecture advice."
        input_obj["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"] = True
        input_obj["phase_a_signals"]["mentions_external_provider_or_upload_intent"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "sensitive"
        decision = self.decide(input_obj)
        self.assertIn(decision["route_action"], {"ask_user_confirm", "blocked"})
        self.assertIn(decision["route_tier"], {"USER_CONFIRM", "BLOCKED"})
        self.assertEqual("external:scientific_medium", decision["proposed_external_target"])
        self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))
        self.assertFalse(decision["external_allowed"])

    def test_a2_004_clarification_context_asks_clarification(self):
        input_obj = self.base_input()
        input_obj["phase_b_soft_proposal"]["soft_reason_code"] = "clarification_context"
        decision = self.decide(input_obj)
        self.assertEqual("ask_clarification", decision["route_action"])
        self.assertEqual("USER_CONFIRM", decision["route_tier"])
        self.assertFalse(decision["external_allowed"])

    def test_a2_005_simple_non_sensitive_question_answers_locally(self):
        input_obj = self.base_input()
        input_obj["router_hint"]["task_type"] = "general_question"
        input_obj["router_hint"]["complexity"] = "low"
        decision = self.decide(input_obj)
        self.assertEqual("LOCAL_FAST", decision["route_tier"])
        self.assertIn(decision["provider_candidate"], {"local:qwen", "local:gemma"})
        self.assertEqual("answer_only", decision["allowed_execution_mode"])

    def test_a2_006_high_complexity_public_external_policy_gets_candidate_proposal(self):
        input_obj = self.make_high_complexity_public()
        decision = self.decide(input_obj)
        self.assertEqual("SCIENTIFIC_MEDIUM", decision["route_tier"])
        self.assertEqual("external:scientific_medium", decision["provider_candidate"])
        self.assertEqual("external:scientific_medium", decision["proposed_external_target"])
        self.assertTrue(decision["external_allowed"])
        self.assertFalse(decision["provider_call_allowed_now"])
        self.assertFalse(decision["external_network_allowed_now"])
        self.assertTrue(decision["confirmation_required"])

    def test_a2_007_budget_max_local_fast_blocks_external_tier(self):
        input_obj = self.make_high_complexity_public()
        input_obj["budget_policy"]["max_tier"] = "LOCAL_FAST"
        decision = self.decide(input_obj)
        self.assertIn(decision["route_tier"], {"LOCAL_FAST", "USER_CONFIRM"})
        self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))
        self.assertFalse(decision["external_allowed"])

    def test_a2_008_unknown_sensitivity_external_hint_stays_non_external(self):
        input_obj = self.enable_external_policy(self.base_input())
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "unknown"
        input_obj["action_hint"]["needs_provider_call"] = True
        decision = self.decide(input_obj)
        self.assertIn(decision["route_tier"], {"USER_CONFIRM", "LOCAL_ONLY"})
        self.assertFalse(decision["external_allowed"])
        self.assertFalse(decision["external_network_allowed_now"])

    def test_a2_009_secret_overrides_high_complexity_external_candidate(self):
        input_obj = self.make_high_complexity_public()
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "secret"
        decision = self.decide(input_obj)
        self.assertEqual("blocked", decision["route_action"])
        self.assertEqual("BLOCKED", decision["route_tier"])
        self.assertFalse(decision["external_allowed"])

    def test_a2_010_high_complexity_external_disabled_falls_back_safely(self):
        input_obj = self.make_high_complexity_public()
        input_obj["user_policy"]["external_routing_enabled"] = False
        decision = self.decide(input_obj)
        self.assertEqual("USER_CONFIRM", decision["route_tier"])
        self.assertFalse(decision["external_allowed"])
        self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))

    def test_a2_011_unknown_high_complexity_external_enabled_is_not_external(self):
        input_obj = self.make_high_complexity_public()
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "unknown"
        decision = self.decide(input_obj)
        self.assertIn(decision["route_tier"], {"USER_CONFIRM", "LOCAL_ONLY"})
        self.assertFalse(decision["external_allowed"])
        self.assertFalse(str(decision["provider_candidate"]).startswith("external:"))

    def test_decision_serialization_is_deterministic_json(self):
        input_obj = self.base_input()
        decision = self.decide(input_obj)
        rendered = probe.decision_to_json(decision)
        self.assertTrue(rendered.endswith("\n"))
        self.assertIn('"schema_version": "router_policy_decision_v0_3_1_1"', rendered)
