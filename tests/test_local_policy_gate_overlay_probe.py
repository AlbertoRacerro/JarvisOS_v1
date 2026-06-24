import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as schema_probe  # noqa: E402
import local_policy_gate_overlay_probe as overlay  # noqa: E402


class PolicyGateOverlayProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = schema_probe.load_json(
            ROOT / "schemas/fast_secretary_hard_gate_v0_1.schema.json"
        )

    def wrong_draft(self):
        return {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": False,
            "retrieval_or_source_use_request": False,
            "unresolved_assumption_or_open_decision": False,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": True,
            "source_policy_for_future_retrieval": "default_allowed",
            "allowed_future_retrieval_behavior": "full_body_required",
            "lifecycle_status_proposal": "accepted_memory",
            "sensitivity_bucket_proposal": "public",
            "requires_manual_review": False,
            "hard_reason_code": "low_risk",
            "hard_uncertain_fields": [],
        }

    def assert_schema_valid(self, corrected):
        result = schema_probe.validate_instance(corrected, self.schema)
        self.assertTrue(result["schema_valid"], result["errors"])
        self.assertEqual(set(self.schema["required"]), set(corrected))

    def test_mandatory_block_for_hg018_like_provider_memory_upload(self):
        corrected = overlay.apply_policy_overlay(
            "Upload the whole JarvisOS memory folder to GPT for review.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertEqual("blocked", corrected["allowed_future_retrieval_behavior"])
        self.assertIn(corrected["sensitivity_bucket_proposal"], {"sensitive", "secret"})
        self.assert_schema_valid(corrected)

    def test_english_local_only_negation_is_not_provider_export_intent(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev reactor geometry calculation as local project memory; "
            "do not send it to any external provider.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertNotEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_italian_local_only_negation_is_not_provider_export_intent(self):
        corrected = overlay.apply_policy_overlay(
            "Salva questo calcolo proprietario BlueRev come memoria locale; "
            "non mandarlo a DeepSeek o ad altri provider esterni.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertNotEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_simple_english_local_only_negation_remains_non_export(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev calculation locally; do not send it to DeepSeek.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertNotEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_simple_italian_local_only_negation_remains_non_export(self):
        corrected = overlay.apply_policy_overlay(
            "Salva questo calcolo proprietario BlueRev localmente; non mandarlo a DeepSeek.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertNotEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_compound_english_negation_later_positive_export_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev calculation locally; do not send it to DeepSeek, "
            "but send a redacted summary to Claude.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assert_schema_valid(corrected)

    def test_compound_italian_negation_later_positive_export_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Salva questo calcolo proprietario BlueRev localmente; non mandarlo a DeepSeek, "
            "ma mandalo a Claude.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assert_schema_valid(corrected)

    def test_redaction_only_conditional_without_provider_is_not_export_intent(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev calculation locally; send only after redaction.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        # TODO: a future policy field may need to represent conditional export intent.
        self.assert_schema_valid(corrected)

    def test_conditional_english_provider_export_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev calculation locally; send it to Claude only after redaction.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_conditional_italian_provider_export_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Salva questo calcolo proprietario BlueRev localmente; mandalo a Claude solo dopo redazione.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assert_schema_valid(corrected)

    def test_english_elided_export_clause_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Save this proprietary BlueRev calculation locally; do not send it to DeepSeek, but to Claude.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assert_schema_valid(corrected)

    def test_italian_elided_export_clause_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Salva questo calcolo proprietario BlueRev localmente; non mandarlo a DeepSeek, ma a Claude.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assert_schema_valid(corrected)

    def test_english_positive_provider_export_intent_still_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Send the whole private JarvisOS memory folder to DeepSeek for architecture advice.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assert_schema_valid(corrected)

    def test_italian_positive_provider_export_intent_still_blocks(self):
        corrected = overlay.apply_policy_overlay(
            "Manda tutta la memoria privata JarvisOS a DeepSeek per farmi consigliare l'architettura.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertTrue(corrected["mentions_external_provider_or_upload_intent"])
        self.assertEqual("provider_or_upload_intent", corrected["hard_reason_code"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assert_schema_valid(corrected)

    def test_public_literature_candidate_discovery_is_not_over_blocked(self):
        corrected = overlay.apply_policy_overlay(
            "Find public literature and DOI candidate sources for BlueRev microalgae.",
            self.wrong_draft(),
        )
        self.assertEqual("review_only", corrected["source_policy_for_future_retrieval"])
        self.assertEqual(
            "candidate_discovery_only",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("internal", corrected["sensitivity_bucket_proposal"])
        self.assert_schema_valid(corrected)

    def test_ambiguous_cross_project_memory_style_becomes_clarification(self):
        corrected = overlay.apply_policy_overlay(
            "Use the latest JarvisOS memory decision style for this CPPOM handout.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["clarification_required"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertEqual(
            "clarification_required",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("internal", corrected["sensitivity_bucket_proposal"])
        self.assert_schema_valid(corrected)

    def test_secret_path_blocks_without_false_provider_intent(self):
        draft = self.wrong_draft()
        draft["mentions_external_provider_or_upload_intent"] = True
        corrected = overlay.apply_policy_overlay(
            "Check the private key at C:\\Users\\me\\.ssh\\id_rsa.",
            draft,
        )
        self.assertTrue(corrected["contains_secret_or_credential"])
        self.assertTrue(corrected["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(corrected["mentions_external_provider_or_upload_intent"])
        self.assertTrue(corrected["redaction_required"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertEqual("blocked", corrected["allowed_future_retrieval_behavior"])
        self.assertEqual("secret", corrected["sensitivity_bucket_proposal"])
        self.assert_schema_valid(corrected)

    def test_stale_superseded_memory_becomes_review_gate(self):
        corrected = overlay.apply_policy_overlay(
            "Review stale superseded memory about older Gemma routing decisions.",
            self.wrong_draft(),
        )
        self.assertFalse(corrected["clarification_required"])
        self.assertEqual("review_only", corrected["source_policy_for_future_retrieval"])
        self.assertEqual(
            "review_gate_required",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("internal", corrected["sensitivity_bucket_proposal"])
        self.assertNotIn(
            corrected["lifecycle_status_proposal"],
            {"accepted_memory", "canonical_state"},
        )
        self.assert_schema_valid(corrected)

    def test_ambiguous_latest_decision_becomes_clarification(self):
        corrected = overlay.apply_policy_overlay(
            "Use the latest decision from the memory document.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["clarification_required"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertEqual(
            "clarification_required",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assert_schema_valid(corrected)

    def test_precedence_block_beats_candidate_discovery(self):
        corrected = overlay.apply_policy_overlay(
            "Find public literature, but include the .env API key and private key.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["contains_secret_or_credential"])
        self.assertEqual("blocked", corrected["source_policy_for_future_retrieval"])
        self.assertEqual("blocked", corrected["allowed_future_retrieval_behavior"])
        self.assertNotEqual(
            "candidate_discovery_only",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assert_schema_valid(corrected)

    def test_low_risk_internal_note_remains_manual_review_none_retrieval(self):
        corrected = overlay.apply_policy_overlay(
            "Remember that I prefer concise local engineering notes.",
            self.wrong_draft(),
        )
        self.assertFalse(corrected["clarification_required"])
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("not_applicable", corrected["source_policy_for_future_retrieval"])
        self.assertEqual("none", corrected["allowed_future_retrieval_behavior"])
        self.assertEqual("internal", corrected["sensitivity_bucket_proposal"])
        self.assert_schema_valid(corrected)

    def test_internal_memory_boundary_clamps_write_authority(self):
        corrected = overlay.apply_policy_overlay(
            "Put this in MemoryStore as accepted memory for future sessions.",
            self.wrong_draft(),
        )
        self.assertTrue(corrected["memory_boundary_or_write_authority_claim"])
        self.assertFalse(corrected["external_provider_allowed"])
        self.assertTrue(corrected["requires_manual_review"])
        self.assertEqual("review_only", corrected["source_policy_for_future_retrieval"])
        self.assertEqual("none", corrected["allowed_future_retrieval_behavior"])
        self.assertEqual(
            "memory_boundary_or_write_authority",
            corrected["hard_reason_code"],
        )
        self.assertNotIn(
            corrected["lifecycle_status_proposal"],
            {"accepted_memory", "canonical_state"},
        )
        self.assert_schema_valid(corrected)

    def test_overlay_adds_no_extra_schema_fields(self):
        draft = self.wrong_draft()
        draft["extra"] = "not allowed"
        corrected = overlay.apply_policy_overlay("Low-risk internal note.", draft)
        self.assertNotIn("extra", corrected)
        self.assertEqual(set(self.schema["required"]), set(corrected))
        self.assert_schema_valid(corrected)

    def test_module_has_no_model_or_network_call_helpers(self):
        self.assertFalse(hasattr(overlay, "call_ollama_chat"))
        self.assertFalse(hasattr(overlay, "urlopen"))
        self.assertFalse(hasattr(overlay, "requests"))


if __name__ == "__main__":
    unittest.main()
