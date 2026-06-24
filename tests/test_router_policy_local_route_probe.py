import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_decision_probe as decision_probe  # noqa: E402
import router_policy_local_route_probe as local_route  # noqa: E402


FIXTURE_PATH = ROOT / "tests/fixtures/router_policy/base_router_policy_fixture.json"
NOW = "2026-06-24T11:00:00+00:00"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class RouterPolicyLocalRouteProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE_PATH)

    def base_input(self):
        return copy.deepcopy(self.fixture["input"])

    def safe_decision(self):
        return decision_probe.decide_router_policy(self.base_input(), now=NOW)

    def run_with_decision(self, input_obj, decision, responder=None, violations=None):
        with patch.object(local_route, "_DECIDE_ROUTER_POLICY", return_value=decision) as decide:
            with patch.object(
                local_route,
                "_VALIDATE_ROUTER_DECISION_SEMANTICS",
                return_value=[] if violations is None else violations,
            ) as validate:
                result = local_route.run_local_route(input_obj, responder=responder, now=NOW)
        decide.assert_called_once_with(input_obj, now=NOW)
        validate.assert_called_once_with(input_obj, decision)
        return result

    def assert_no_execution(self, result, responder):
        self.assertFalse(result["executed"])
        self.assertIsNone(result["response"])
        responder.assert_not_called()

    def make_high_complexity_public(self):
        input_obj = self.base_input()
        input_obj["user_policy"]["external_routing_enabled"] = True
        input_obj["user_policy"]["external_requires_confirmation"] = True
        input_obj["provider_policy"] = {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
            "blocked_provider_tiers": ["FRONTIER"],
        }
        input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
        input_obj["phase_a_signals"]["external_provider_allowed"] = True
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

    def test_a3_001_simple_non_sensitive_local_question_executes_injected_responder(self):
        input_obj = self.base_input()
        responder = Mock(return_value="mock local response")
        result = local_route.run_local_route(input_obj, responder=responder, now=NOW)
        decision = result["decision"]
        self.assertTrue(local_route._is_safe_local_execution(decision))
        responder.assert_called_once_with(input_obj["message_text"])
        self.assertTrue(result["executed"])
        self.assertEqual("local_answer", result["reason"])
        self.assertEqual("mock local response", result["response"])
        self.assertFalse(decision["external_allowed"])
        self.assertFalse(decision["provider_call_allowed_now"])
        self.assertFalse(decision["external_network_allowed_now"])
        self.assertFalse(decision["tool_execution_allowed_now"])
        self.assertFalse(decision["state_change_allowed_now"])

    def test_a3_002_clarification_ambiguous_decision_does_not_execute(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["clarification_required"] = True
        responder = Mock(return_value="should not run")
        result = local_route.run_local_route(input_obj, responder=responder, now=NOW)
        self.assert_no_execution(result, responder)
        self.assertEqual("not_safe_local_route", result["reason"])
        self.assertEqual("ask_clarification", result["decision"]["route_action"])

    def test_a3_003_external_proposal_does_not_execute(self):
        input_obj = self.make_high_complexity_public()
        responder = Mock(return_value="should not run")
        result = local_route.run_local_route(input_obj, responder=responder, now=NOW)
        self.assert_no_execution(result, responder)
        self.assertEqual("not_safe_local_route", result["reason"])
        self.assertEqual("external:scientific_medium", result["decision"]["proposed_external_target"])
        self.assertFalse(result["decision"]["external_allowed"])
        self.assertFalse(str(result["decision"]["provider_candidate"]).startswith("external:"))

    def test_a3_004_secret_private_decision_does_not_execute(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Never expose API key sk-test-secret-12345678."
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "secret"
        responder = Mock(return_value="should not run")
        result = local_route.run_local_route(input_obj, responder=responder, now=NOW)
        self.assert_no_execution(result, responder)
        self.assertEqual("blocked", result["decision"]["route_action"])
        self.assertFalse(result["decision"]["external_allowed"])

    def test_a3_005_guard_is_boolean_based_not_label_based(self):
        unsafe_fields = [
            "external_allowed",
            "provider_call_allowed_now",
            "external_network_allowed_now",
            "tool_execution_allowed_now",
            "state_change_allowed_now",
        ]
        for field in unsafe_fields:
            with self.subTest(field=field):
                decision = self.safe_decision()
                decision[field] = True
                responder = Mock(return_value="should not run")
                self.assertFalse(local_route._is_safe_local_execution(decision))
                result = self.run_with_decision(self.base_input(), decision, responder=responder)
                self.assert_no_execution(result, responder)
                self.assertEqual("not_safe_local_route", result["reason"])

    def test_a3_006_fail_closed_on_semantic_validator_violation(self):
        input_obj = self.base_input()
        decision = self.safe_decision()
        violations = [{"code": "TEST_VIOLATION", "field_path": "$", "message": "bad", "severity": "error"}]
        responder = Mock(return_value="should not run")
        result = self.run_with_decision(input_obj, decision, responder=responder, violations=violations)
        self.assert_no_execution(result, responder)
        self.assertEqual("decision_failed_validation", result["reason"])
        self.assertEqual(violations, result["violations"])

    def test_a3_007_propose_only_does_not_execute(self):
        decision = self.safe_decision()
        decision["allowed_execution_mode"] = "propose_only"
        responder = Mock(return_value="should not run")
        self.assertFalse(local_route._is_safe_local_execution(decision))
        result = self.run_with_decision(self.base_input(), decision, responder=responder)
        self.assert_no_execution(result, responder)

    def test_a3_008_responder_missing_does_not_call_real_model(self):
        input_obj = self.base_input()
        result = local_route.run_local_route(input_obj, responder=None, now=NOW)
        self.assertFalse(result["executed"])
        self.assertIsNone(result["response"])
        self.assertEqual("local_responder_missing", result["reason"])

    def test_a3_009_external_looking_provider_blocks_guard(self):
        decision = self.safe_decision()
        decision["provider_candidate"] = "external:scientific_medium"
        self.assertFalse(local_route._is_safe_local_execution(decision))

    def test_a3_010_missing_message_text_fails_closed(self):
        input_obj = self.base_input()
        input_obj.pop("message_text", None)
        decision = self.safe_decision()
        responder = Mock(return_value="should not run")
        result = self.run_with_decision(input_obj, decision, responder=responder)
        self.assert_no_execution(result, responder)
        self.assertEqual("message_text_missing", result["reason"])

    def test_a3_011_local_only_does_not_execute_in_a3(self):
        decision = self.safe_decision()
        decision["route_tier"] = "LOCAL_ONLY"
        responder = Mock(return_value="should not run")
        self.assertFalse(local_route._is_safe_local_execution(decision))
        result = self.run_with_decision(self.base_input(), decision, responder=responder)
        self.assert_no_execution(result, responder)
        self.assertEqual("not_safe_local_route", result["reason"])


if __name__ == "__main__":
    unittest.main()
