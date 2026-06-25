import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_hint_bridge_probe as bridge  # noqa: E402


def base_input() -> dict:
    return {
        "message_text": "Explain what a centrifugal pump is",
        "phase_a_signals": {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "external_provider_allowed": False,
            "clarification_required": False,
            "hard_reason_codes": ["low_risk"],
            "sensitivity_bucket_proposal": "public",
            "requires_manual_review": False,
            "source_policy_for_future_retrieval": "not_applicable",
            "allowed_future_retrieval_behavior": "none",
        },
        "phase_b_soft_proposal": phase_b(
            soft_reason_code="contextual_summary",
            primary_domain="general",
            domain_tags=[],
            storage_relevance="low",
            usefulness_for_future_review="low",
            possible_memory_card_type="none",
        ),
        "router_hint": {
            "task_type": "review",
            "complexity": "medium",
            "domain": "general",
            "confidence": "low",
            "estimated_tokens": 200,
            "needs_reasoning": False,
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
            "needs_scientific_depth": False,
        },
        "action_hint": {
            "requested_action_type": "unknown",
            "modifies_state": False,
            "side_effect_level": "none",
            "reversibility": "reversible",
            "environment_type": "chat",
            "state_scope": "none",
            "needs_terminal": False,
            "needs_file_write": False,
            "needs_memory_write": False,
            "needs_provider_call": False,
            "confidence": "low",
        },
        "user_policy": {
            "external_routing_enabled": False,
            "external_requires_confirmation": True,
            "allow_persistent_auto_allow": False,
        },
        "provider_policy": {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST"],
            "blocked_provider_tiers": ["CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM", "FRONTIER"],
        },
        "budget_policy": {
            "max_tier": "LOCAL_FAST",
            "max_tokens": 2048,
            "require_confirmation_above_tier": "CHEAP_EXTERNAL",
        },
        "context_metadata": {
            "attached_files_present": False,
            "conversation_context_available": False,
        },
    }


def phase_b(
    *,
    soft_reason_code: str,
    primary_domain: str = "general",
    domain_tags: list[str] | None = None,
    storage_relevance: str = "low",
    usefulness_for_future_review: str = "low",
    possible_memory_card_type: str = "none",
    suggested_followup_question: str = "",
    soft_uncertain_fields: list[str] | None = None,
) -> dict:
    return {
        "phase_a_case_id": "B1-test",
        "summary_short": "Short advisory summary.",
        "project_bucket": "general",
        "primary_domain": primary_domain,
        "domain_tags": domain_tags or [],
        "storage_relevance": storage_relevance,
        "usefulness_for_future_review": usefulness_for_future_review,
        "possible_memory_card_type": possible_memory_card_type,
        "soft_reason_code": soft_reason_code,
        "brief_rationale": "Advisory only.",
        "suggested_followup_question": suggested_followup_question,
        "soft_uncertain_fields": soft_uncertain_fields or [],
        "phase_a_blocked": False,
        "phase_a_clarification_required": False,
        "phase_a_external_provider_allowed": False,
        "phase_a_requires_manual_review": True,
        "can_override_phase_a": False,
        "recommends_external_provider": False,
        "recommends_retrieval": False,
        "requires_manual_review": True,
    }


class RouterPolicyHintBridgeProbeTests(unittest.TestCase):
    def assert_structurally_valid(self, produced):
        self.assertEqual([], bridge.validate_router_policy_input_shape(produced))

    def assert_not_safe_answer(self, produced):
        self.assertFalse(
            produced["router_hint"]["task_type"] == "answer"
            and produced["router_hint"]["complexity"] == "low"
        )
        self.assertNotEqual("high", produced["router_hint"]["confidence"])
        self.assertNotEqual("answer", produced["action_hint"]["requested_action_type"])

    def test_b1_001_hard_gate_dominates_phase_b_answer_proposal(self):
        obj = base_input()
        obj["phase_a_signals"].update(
            {
                "contains_secret_or_credential": True,
                "hard_reason_codes": ["secret_or_credential"],
                "sensitivity_bucket_proposal": "secret",
                "requires_manual_review": True,
            }
        )
        produced = bridge.apply_phase_b_router_hint(
            obj,
            phase_b_soft_proposal=phase_b(soft_reason_code="contextual_summary"),
        )
        self.assert_not_safe_answer(produced)
        self.assertFalse(produced["context_metadata"]["phase_b_router_hint_applied"])
        self.assertEqual("phase_b_blocked_by_hard_gate", produced["context_metadata"]["router_hint_source"])
        self.assert_structurally_valid(produced)

    def test_b1_002_operational_hard_gate_dominates_phase_b_answer_proposal(self):
        obj = base_input()
        obj["router_hint"]["needs_code_execution"] = True
        obj["action_hint"]["needs_terminal"] = True
        produced = bridge.apply_phase_b_router_hint(
            obj,
            phase_b_soft_proposal=phase_b(soft_reason_code="contextual_summary"),
        )
        self.assert_not_safe_answer(produced)
        self.assertTrue(produced["router_hint"]["needs_code_execution"])
        self.assertTrue(produced["action_hint"]["needs_terminal"])
        self.assertFalse(produced["context_metadata"]["phase_b_router_hint_applied"])
        self.assert_structurally_valid(produced)

    def test_b1_003_benign_general_answer_maps_to_local_answer_hint(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(soft_reason_code="contextual_summary"),
        )
        self.assertEqual("answer", produced["router_hint"]["task_type"])
        self.assertEqual("low", produced["router_hint"]["complexity"])
        self.assertEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assertEqual("none", produced["action_hint"]["side_effect_level"])
        self.assertFalse(produced["action_hint"]["needs_provider_call"])
        self.assertFalse(produced["action_hint"]["needs_memory_write"])
        self.assert_structurally_valid(produced)

    def test_a5_r3_bucket_only_sensitive_low_risk_does_not_block_phase_b_answer_hint(self):
        obj = base_input()
        obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "sensitive"

        produced = bridge.apply_phase_b_router_hint(
            obj,
            phase_b_soft_proposal=phase_b(soft_reason_code="contextual_summary"),
        )

        self.assertEqual("answer", produced["router_hint"]["task_type"])
        self.assertEqual("low", produced["router_hint"]["complexity"])
        self.assertEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assertEqual("phase_b_soft_review", produced["context_metadata"]["router_hint_source"])
        self.assertTrue(produced["context_metadata"]["phase_b_router_hint_applied"])
        self.assert_structurally_valid(produced)

    def test_b1_004_technical_scientific_answer_maps_to_medium_reasoning(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="contextual_summary",
                primary_domain="bioprocess",
                domain_tags=["engineering", "reactor", "modeling"],
            ),
        )
        self.assertEqual("answer", produced["router_hint"]["task_type"])
        self.assertEqual("medium", produced["router_hint"]["complexity"])
        self.assertTrue(produced["router_hint"]["needs_reasoning"])
        self.assertTrue(produced["router_hint"]["needs_scientific_depth"])
        self.assertEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assertEqual("none", produced["action_hint"]["side_effect_level"])
        self.assert_structurally_valid(produced)

    def test_b1_005_source_current_info_request_does_not_become_answer_low(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(soft_reason_code="source_candidate"),
        )
        self.assertEqual("review", produced["router_hint"]["task_type"])
        self.assertNotEqual("low", produced["router_hint"]["complexity"])
        self.assertTrue(produced["router_hint"]["needs_current_info"])
        self.assertTrue(produced["router_hint"]["needs_file_context"])
        self.assertNotEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assert_structurally_valid(produced)

    def test_b1_006_ambiguity_followup_maps_to_clarification_or_review(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="contextual_summary",
                suggested_followup_question="Which document do you mean?",
            ),
        )
        self.assertIn(produced["router_hint"]["task_type"], {"clarification", "review"})
        self.assertNotEqual("low", produced["router_hint"]["complexity"])
        self.assertEqual("low", produced["router_hint"]["confidence"])
        self.assertNotEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assert_structurally_valid(produced)

    def test_b1_007_low_quality_phase_b_does_not_create_safe_route(self):
        bad_phase_b = phase_b(soft_reason_code="contextual_summary")
        bad_phase_b["soft_reason_code"] = "made_up_reason"
        bad_phase_b.pop("primary_domain")
        produced = bridge.apply_phase_b_router_hint(base_input(), phase_b_soft_proposal=bad_phase_b)
        self.assert_not_safe_answer(produced)
        self.assertEqual("low", produced["router_hint"]["confidence"])
        self.assert_structurally_valid(produced)

    def test_b1_008_no_mutation_of_input_object(self):
        original = base_input()
        before = copy.deepcopy(original)
        bridge.apply_phase_b_router_hint(
            original,
            phase_b_soft_proposal=phase_b(soft_reason_code="contextual_summary"),
        )
        self.assertEqual(before, original)

    def test_b1_009_produced_object_remains_structurally_valid(self):
        cases = [
            phase_b(soft_reason_code="contextual_summary"),
            phase_b(soft_reason_code="low_value"),
            phase_b(soft_reason_code="source_candidate"),
            phase_b(soft_reason_code="clarification_context"),
            phase_b(soft_reason_code="memory_candidate"),
        ]
        for proposal in cases:
            with self.subTest(reason=proposal["soft_reason_code"]):
                self.assert_structurally_valid(
                    bridge.apply_phase_b_router_hint(base_input(), phase_b_soft_proposal=proposal)
                )

    def test_b1_010_no_runtime_import_integrations(self):
        module_names = set(vars(bridge))
        forbidden = {"urlopen", "requests", "httpx", "subprocess", "Popen", "ollama"}
        self.assertTrue(module_names.isdisjoint(forbidden))

    def test_b1_011_no_confidence_field_still_maps_benign_answer(self):
        proposal = phase_b(
            soft_reason_code="contextual_summary",
            primary_domain="general",
            domain_tags=[],
            soft_uncertain_fields=[],
            suggested_followup_question="",
        )
        self.assertNotIn("confidence", proposal)
        produced = bridge.apply_phase_b_router_hint(base_input(), phase_b_soft_proposal=proposal)
        self.assertEqual("answer", produced["router_hint"]["task_type"])
        self.assertIn(produced["router_hint"]["complexity"], {"low", "medium"})
        self.assertIn(produced["router_hint"]["confidence"], {"medium", "high"})
        self.assertEqual("answer", produced["action_hint"]["requested_action_type"])
        self.assertEqual("none", produced["action_hint"]["side_effect_level"])

    def test_b1_012_suggested_followup_overrides_answer_mapping(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="contextual_summary",
                suggested_followup_question="Which document do you mean?",
                soft_uncertain_fields=[],
            ),
        )
        self.assertIn(produced["router_hint"]["task_type"], {"clarification", "review"})
        self.assertNotEqual("low", produced["router_hint"]["complexity"])
        self.assertEqual("low", produced["router_hint"]["confidence"])
        self.assertNotEqual("answer", produced["action_hint"]["requested_action_type"])

    def test_b1_013_soft_uncertain_fields_lowers_quality(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="contextual_summary",
                soft_uncertain_fields=["source ambiguity", "target unclear"],
            ),
        )
        self.assertEqual("review", produced["router_hint"]["task_type"])
        self.assertEqual("low", produced["router_hint"]["confidence"])
        self.assertNotEqual("answer", produced["action_hint"]["requested_action_type"])

    def test_b1_014_soft_reason_code_drives_source_current_info_mapping(self):
        produced = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(soft_reason_code="source_candidate"),
        )
        self.assertEqual("review", produced["router_hint"]["task_type"])
        self.assertNotEqual("low", produced["router_hint"]["complexity"])
        self.assertTrue(produced["router_hint"]["needs_current_info"])
        self.assertTrue(produced["router_hint"]["needs_file_context"])

    def test_b1_015_memory_candidate_uses_storage_card_tie_breakers(self):
        benign = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="memory_candidate",
                storage_relevance="low",
                usefulness_for_future_review="low",
                possible_memory_card_type="none",
            ),
        )
        self.assertEqual("answer", benign["router_hint"]["task_type"])
        self.assertEqual("none", benign["action_hint"]["side_effect_level"])
        self.assertFalse(benign["action_hint"]["needs_memory_write"])

        review = bridge.apply_phase_b_router_hint(
            base_input(),
            phase_b_soft_proposal=phase_b(
                soft_reason_code="memory_candidate",
                storage_relevance="high",
                usefulness_for_future_review="high",
                possible_memory_card_type="decision_card",
            ),
        )
        self.assertEqual("review", review["router_hint"]["task_type"])
        self.assertNotEqual("low", review["router_hint"]["complexity"])
        self.assertNotEqual("answer", review["action_hint"]["requested_action_type"])
        self.assertFalse(review["action_hint"]["needs_memory_write"])


if __name__ == "__main__":
    unittest.main()
