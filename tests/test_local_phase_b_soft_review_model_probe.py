import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as structured_probe  # noqa: E402
import local_policy_gate_overlay_probe as overlay_probe  # noqa: E402
import local_phase_b_soft_review_model_probe as model_probe  # noqa: E402


class PhaseBSoftOnlyModelProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_soft_proposal_v0_1.schema.json"
        cls.schema = structured_probe.load_json(cls.schema_path)

    def phase_a(self):
        return {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": False,
            "retrieval_or_source_use_request": True,
            "unresolved_assumption_or_open_decision": True,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": False,
            "source_policy_for_future_retrieval": "review_only",
            "allowed_future_retrieval_behavior": "candidate_discovery_only",
            "lifecycle_status_proposal": "unknown",
            "sensitivity_bucket_proposal": "internal",
            "requires_manual_review": True,
            "hard_reason_code": "retrieval_or_source_request",
            "hard_uncertain_fields": [],
        }

    def source_result(self, phase_a=None):
        return {
            "case_id": "HG-007",
            "policy_overlay_corrected_output": phase_a or self.phase_a(),
        }

    def source_result_from_overlay(self, input_text):
        return self.source_result(overlay_probe.apply_policy_overlay(input_text, self.phase_a()))

    def valid_soft_proposal(self):
        return {
            "summary_short": "Input may support candidate source discovery under review.",
            "project_bucket": "bluerev",
            "primary_domain": "retrieval",
            "domain_tags": ["literature", "bluerev"],
            "storage_relevance": "medium",
            "usefulness_for_future_review": "medium",
            "possible_memory_card_type": "source_card",
            "soft_reason_code": "source_candidate",
            "brief_rationale": "Useful local review context for source discovery.",
            "suggested_followup_question": "",
            "soft_uncertain_fields": [],
        }

    def local_provider_note_proposal(self):
        proposal = dict(self.valid_soft_proposal())
        proposal.update(
            {
                "summary_short": "Local provider pricing comparison note.",
                "project_bucket": "jarvisos",
                "primary_domain": "local_ai",
                "domain_tags": ["provider_pricing", "local_notes"],
                "storage_relevance": "high",
                "usefulness_for_future_review": "high",
                "possible_memory_card_type": "source_card",
                "soft_reason_code": "memory_candidate",
                "brief_rationale": "Useful local review context for provider pricing comparison.",
            }
        )
        return proposal

    def raw_call(self, output):
        return {
            "ok": True,
            "status": 200,
            "duration_seconds": 0.1,
            "body": {"message": {"content": json.dumps(output)}},
            "error": None,
        }

    def test_default_b5a_case_selection_has_eight_cases(self):
        self.assertEqual(
            [
                "HG-007",
                "HG-010",
                "HG-013",
                "HG-016",
                "HG-017",
                "HG-018",
                "HG-024",
                "HG-025",
            ],
            model_probe.select_case_ids(model_probe.DEFAULT_CASE_IDS),
        )

    def test_general_instruction_block_is_not_case_specific(self):
        instruction = model_probe.build_general_instruction_block()
        forbidden_tokens = [
            "HG-007", "HG-010", "HG-013", "HG-016", "HG-017", "HG-018", "HG-024", "HG-025",
            "kLa", "GPT-5.5", ".ssh/id_rsa", "Gemma 12B routing", "memory folder to GPT",
        ]
        for token in forbidden_tokens:
            self.assertNotIn(token, instruction)

    def test_instruction_block_contains_sensitivity_aware_semantic_core(self):
        instruction = model_probe.build_general_instruction_block()
        expected = [
            "local semantic-review component inside JarvisOS",
            "Sensitive does not mean useless",
            "Sensitive means protect boundaries",
            "Secrets and credentials are different",
            "highly valuable local memory",
            "provider-boundary",
            "clarification_context",
        ]
        for phrase in expected:
            self.assertIn(phrase, instruction)
        self.assertNotIn("never promote uncertain or sensitive content as ready memory", instruction)

    def test_case_selection_rejects_more_than_eight_cases(self):
        with self.assertRaises(ValueError):
            model_probe.select_case_ids(
                "HG-001,HG-002,HG-003,HG-004,HG-005,HG-006,HG-007,HG-008,HG-009"
            )

    def test_soft_proposal_schema_is_closed_and_has_no_authority_fields(self):
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual([], model_probe.authority_field_leakage(self.schema["properties"]))
        forbidden = {
            "phase_a_blocked",
            "phase_a_external_provider_allowed",
            "can_override_phase_a",
            "recommends_external_provider",
            "recommends_retrieval",
            "requires_manual_review",
            "source_policy_for_future_retrieval",
            "allowed_future_retrieval_behavior",
        }
        self.assertTrue(forbidden.isdisjoint(set(self.schema["properties"])))

    def test_prompt_does_not_include_phase_a_policy_context(self):
        prompt = model_probe.build_phase_b_prompt(
            case_id="HG-TEST",
            input_text="Summarize this neutral engineering note.",
        )
        forbidden = [
            "phase_a_status",
            "phase_a_reason",
            "source_policy_for_future_retrieval",
            "allowed_future_retrieval_behavior",
            "external_provider_allowed",
            "can_override_phase_a",
        ]
        for token in forbidden:
            self.assertNotIn(token, prompt)

    def test_model_result_wraps_soft_proposal_in_deterministic_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = model_probe.build_model_result(
                case_id="HG-007",
                source_result=self.source_result(),
                schema=self.schema,
                schema_path=self.schema_path,
                model="qwen3:8b",
                raw_path=Path(tmp) / "raw.json",
                raw_call=self.raw_call(self.valid_soft_proposal()),
            )
        self.assertTrue(result["json_parse_passed"])
        self.assertTrue(result["schema_valid"])
        self.assertEqual([], result["authority_field_leakage"])
        self.assertEqual(result["phase_b_soft_proposal_effective"], result["phase_b_soft_proposal"])
        envelope = result["review_envelope"]
        self.assertFalse(envelope["runtime_approved"])
        self.assertTrue(envelope["manual_review_required"])
        self.assertIn("phase_a_hard_gate", envelope)
        self.assertIn("phase_b_soft_proposal", envelope)
        self.assertEqual(envelope["phase_b_soft_proposal_effective"], envelope["phase_b_soft_proposal"])
        self.assertTrue(envelope["soft_quality_review_required"])

    def test_authority_field_in_model_output_is_schema_invalid_and_detected(self):
        output = dict(self.valid_soft_proposal())
        output["can_override_phase_a"] = True
        with tempfile.TemporaryDirectory() as tmp:
            result = model_probe.build_model_result(
                case_id="HG-007",
                source_result=self.source_result(),
                schema=self.schema,
                schema_path=self.schema_path,
                model="qwen3:8b",
                raw_path=Path(tmp) / "raw.json",
                raw_call=self.raw_call(output),
            )
        self.assertFalse(result["schema_valid"])
        self.assertEqual(["can_override_phase_a"], result["phase_b_soft_proposal_model_raw_authority_field_leakage"])
        self.assertEqual(["can_override_phase_a"], result["phase_b_soft_proposal_effective_authority_field_leakage"])
        self.assertEqual(1, result["review_envelope"]["authority_field_leakage_count"])

    def test_soft_quality_diagnostic_flags_known_bad_project_bucket(self):
        proposal = dict(self.valid_soft_proposal())
        proposal.update(
            {
                "project_bucket": "coursework",
                "primary_domain": "local_ai",
                "possible_memory_card_type": "decision_card",
            }
        )
        diagnostic = model_probe.evaluate_soft_quality("HG-024", proposal)
        fields = {miss["field"] for miss in diagnostic["quality_misses"]}
        self.assertIn("project_bucket", fields)
        self.assertGreater(diagnostic["quality_compared_count"], diagnostic["quality_match_count"])

    def test_secret_phase_a_clamps_raw_model_soft_proposal(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "contains_secret_or_credential": True,
                "sensitivity_bucket_proposal": "secret",
                "hard_reason_code": "secret_or_credential",
            }
        )
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "summary_short": "The API key sk-live-example should be remembered.",
                "brief_rationale": "Store sk-live-example for later.",
                "domain_tags": ["api-key", "secret"],
                "suggested_followup_question": "What is the missing private key?",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("security", effective["primary_domain"])
        self.assertEqual("none", effective["possible_memory_card_type"])
        self.assertEqual("none", effective["storage_relevance"])
        self.assertEqual("low", effective["usefulness_for_future_review"])
        self.assertEqual("contextual_summary", effective["soft_reason_code"])
        self.assertTrue(result["soft_proposal_deterministic_clamps"])

    def test_secret_still_clamps_hard(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "contains_secret_or_credential": True,
                "sensitivity_bucket_proposal": "secret",
                "hard_reason_code": "secret_or_credential",
            }
        )
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "summary_short": "Save sk-secret-literal as memory.",
                "storage_relevance": "high",
                "possible_memory_card_type": "memory_card",
                "suggested_followup_question": "What is the full sk-secret-literal value?",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
            input_text="Store this API key: sk-secret-literal.",
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("none", effective["possible_memory_card_type"])
        self.assertIn(effective["storage_relevance"], {"none", "low"})
        self.assertEqual("", effective["suggested_followup_question"])
        self.assertEqual("security", effective["primary_domain"])
        self.assertNotIn("sk-secret-literal", json.dumps(effective))

    def test_provider_private_export_risk_preserves_local_policy_meaning(self):
        input_text = "Send the whole private JarvisOS memory folder to DeepSeek for architecture advice."
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "project_bucket": "jarvisos",
                "primary_domain": "memory",
                "domain_tags": ["memory", "provider"],
                "storage_relevance": "high",
                "usefulness_for_future_review": "high",
                "possible_memory_card_type": "memory_card",
                "soft_reason_code": "memory_candidate",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-018",
            source_result=self.source_result_from_overlay(input_text),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
            input_text=input_text,
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("security", effective["primary_domain"])
        self.assertTrue({"provider_boundary", "private_context"} & set(effective["domain_tags"]))
        self.assertEqual("medium", effective["storage_relevance"])
        self.assertEqual("decision_card", effective["possible_memory_card_type"])
        self.assertRegex(effective["brief_rationale"].lower(), r"(boundary|review|approv)")
        self.assertEqual("", effective["suggested_followup_question"])
        self.assertFalse(result["runtime_approved"])

    def test_provider_as_topic_local_note_does_not_clamp_to_provider_risk(self):
        input_text = (
            "Save locally my notes comparing DeepSeek and Claude pricing; "
            "do not send them anywhere."
        )
        result = model_probe.build_model_result(
            case_id="HG-PROVIDER-TOPIC",
            source_result=self.source_result_from_overlay(input_text),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(self.local_provider_note_proposal()),
            input_text=input_text,
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertNotEqual(
            "provider_or_private_export_risk",
            result["phase_b_sensitive_context_class"],
        )
        self.assertNotEqual("security", effective["primary_domain"])
        self.assertIn(effective["storage_relevance"], {"high", "medium"})
        self.assertNotEqual("decision_card", effective["possible_memory_card_type"])
        self.assertNotEqual("none", effective["possible_memory_card_type"])
        self.assertEqual([], result["soft_proposal_deterministic_clamps"])

    def test_inconsistent_provider_boolean_alone_does_not_force_provider_risk_clamp(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "contains_raw_private_or_ip_sensitive_context": True,
                "mentions_external_provider_or_upload_intent": True,
                "external_provider_allowed": False,
                "hard_reason_code": "low_risk",
                "source_policy_for_future_retrieval": "review_only",
                "allowed_future_retrieval_behavior": "none",
                "sensitivity_bucket_proposal": "internal",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-INCONSISTENT-BOOLEAN",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(self.local_provider_note_proposal()),
            input_text="Save locally my notes comparing DeepSeek and Claude pricing.",
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertNotEqual(
            "provider_or_private_export_risk",
            result["phase_b_sensitive_context_class"],
        )
        self.assertNotEqual("security", effective["primary_domain"])
        self.assertNotEqual("decision_card", effective["possible_memory_card_type"])
        self.assertNotEqual("none", effective["possible_memory_card_type"])

    def assert_local_ip_sensitive_memory_preserved(self, input_text):
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "project_bucket": "bluerev",
                "primary_domain": "reactor_design",
                "domain_tags": ["ip_sensitive", "local_memory", "calculation", "reactor_geometry"],
                "storage_relevance": "high",
                "usefulness_for_future_review": "high",
                "possible_memory_card_type": "assumption_card",
                "soft_reason_code": "assumption_candidate",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-LOCAL",
            source_result=self.source_result_from_overlay(input_text),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
            input_text=input_text,
        )
        effective = result["phase_b_soft_proposal_effective"]
        hard_gate = result["review_envelope"]["phase_a_hard_gate"]
        self.assertTrue(hard_gate["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(hard_gate["mentions_external_provider_or_upload_intent"])
        self.assertFalse(hard_gate["external_provider_allowed"])
        self.assertNotEqual("security", effective["primary_domain"])
        self.assertNotEqual("low", effective["storage_relevance"])
        self.assertNotEqual("none", effective["possible_memory_card_type"])
        self.assertIn(effective["storage_relevance"], {"medium", "high"})
        self.assertEqual(0, result["authority_field_leakage_count"])
        self.assertFalse(result["runtime_approved"])

    def test_local_ip_sensitive_bluerev_design_remains_valuable_local_memory(self):
        self.assert_local_ip_sensitive_memory_preserved(
            "Save this proprietary BlueRev reactor geometry calculation as local project memory; "
            "do not send it to any external provider."
        )

    def test_local_ip_sensitive_bluerev_design_italian_remains_valuable_local_memory(self):
        self.assert_local_ip_sensitive_memory_preserved(
            "Salva questo calcolo proprietario BlueRev come memoria locale; "
            "non mandarlo a DeepSeek o ad altri provider esterni."
        )

    def test_ambiguous_prior_reference_still_clamps_to_clarification(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "clarification_required": True,
                "hard_reason_code": "clarification_needed",
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "clarification_required",
            }
        )
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "storage_relevance": "high",
                "possible_memory_card_type": "memory_card",
                "suggested_followup_question": "",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-025",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
            input_text="Use the thing we decided last time about the material.",
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("low", effective["storage_relevance"])
        self.assertEqual("none", effective["possible_memory_card_type"])
        self.assertTrue(effective["suggested_followup_question"].strip())

    def test_raw_private_phase_a_clamps_raw_model_soft_proposal(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "contains_raw_private_or_ip_sensitive_context": True,
                "mentions_external_provider_or_upload_intent": True,
                "sensitivity_bucket_proposal": "sensitive",
                "hard_reason_code": "provider_or_upload_intent",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-018",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(self.valid_soft_proposal()),
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("security", effective["primary_domain"])
        self.assertEqual("decision_card", effective["possible_memory_card_type"])
        self.assertEqual("medium", effective["storage_relevance"])
        self.assertTrue({"provider_boundary", "private_context"} & set(effective["domain_tags"]))

    def test_phase_a_blocked_clamps_card_and_storage(self):
        phase_a = dict(self.phase_a())
        phase_a.update(
            {
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "blocked",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-007",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(self.valid_soft_proposal()),
        )
        effective = result["phase_b_soft_proposal_effective"]
        self.assertEqual("none", effective["possible_memory_card_type"])
        self.assertEqual("low", effective["storage_relevance"])
        self.assertEqual("retrieval", effective["primary_domain"])

    def test_raw_model_soft_proposal_is_preserved_for_audit(self):
        phase_a = dict(self.phase_a())
        phase_a["contains_secret_or_credential"] = True
        raw = dict(self.valid_soft_proposal())
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
        )
        self.assertEqual(raw, result["phase_b_soft_proposal_model_raw"])
        self.assertNotEqual(raw, result["phase_b_soft_proposal_effective"])
        self.assertEqual(raw, result["review_envelope"]["phase_b_soft_proposal_model_raw"])

    def test_effective_soft_proposal_is_used_in_review_envelope(self):
        phase_a = dict(self.phase_a())
        phase_a["contains_secret_or_credential"] = True
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(self.valid_soft_proposal()),
        )
        envelope = result["review_envelope"]
        self.assertEqual(envelope["phase_b_soft_proposal_effective"], envelope["phase_b_soft_proposal"])
        self.assertEqual(result["phase_b_soft_proposal_effective"], envelope["phase_b_soft_proposal"])

    def test_secret_clamp_redacts_or_replaces_free_text_fields(self):
        phase_a = dict(self.phase_a())
        phase_a["contains_secret_or_credential"] = True
        raw = dict(self.valid_soft_proposal())
        raw.update(
            {
                "summary_short": "Copy sk-secret and C:/private/user-data into memory.",
                "brief_rationale": "The sk-secret value is useful later.",
                "domain_tags": ["sk-secret", "private-path"],
                "suggested_followup_question": "What is the full sk-secret value?",
            }
        )
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
        )
        effective = result["phase_b_soft_proposal_effective"]
        serialized = json.dumps(
            {
                "summary_short": effective["summary_short"],
                "brief_rationale": effective["brief_rationale"],
                "domain_tags": effective["domain_tags"],
                "suggested_followup_question": effective["suggested_followup_question"],
            }
        )
        self.assertNotIn("sk-secret", serialized)
        self.assertNotIn("private-path", serialized)
        self.assertEqual(["security", "sensitive-context"], effective["domain_tags"])

    def test_secret_clamp_always_blanks_followup_question(self):
        phase_a = dict(self.phase_a())
        phase_a["contains_secret_or_credential"] = True
        raw = dict(self.valid_soft_proposal())
        raw["suggested_followup_question"] = "Paste the private key here?"
        result = model_probe.build_model_result(
            case_id="HG-016",
            source_result=self.source_result(phase_a),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
        )
        self.assertEqual("", result["phase_b_soft_proposal_effective"]["suggested_followup_question"])

    def test_clamp_does_not_apply_to_normal_source_case(self):
        raw = self.valid_soft_proposal()
        result = model_probe.build_model_result(
            case_id="HG-007",
            source_result=self.source_result(),
            schema=self.schema,
            schema_path=self.schema_path,
            model="qwen3:8b",
            raw_path=Path("raw.json"),
            raw_call=self.raw_call(raw),
        )
        self.assertEqual([], result["soft_proposal_deterministic_clamps"])
        self.assertEqual(raw, result["phase_b_soft_proposal_effective"])

    def test_summary_does_not_require_clamp_count_to_pass(self):
        result = {
            "case_id": "HG-007",
            "json_parse_passed": True,
            "phase_b_soft_proposal_model_raw_schema_valid": True,
            "phase_b_soft_proposal_effective_schema_valid": True,
            "phase_b_soft_proposal_model_raw_validation_errors": [],
            "phase_b_soft_proposal_effective_validation_errors": [],
            "phase_b_soft_proposal_model_raw_authority_field_leakage": [],
            "phase_b_soft_proposal_effective_authority_field_leakage": [],
            "soft_proposal_deterministic_clamps": [],
            "raw_soft_quality_diagnostic": {
                "quality_match_count": 22,
                "quality_compared_count": 29,
                "quality_misses": [],
            },
            "effective_soft_quality_diagnostic": {
                "quality_match_count": 26,
                "quality_compared_count": 29,
                "quality_misses": [],
            },
        }
        summary = model_probe.summarize_results([result], Path("reports/local_model_smoke/1G-B2-F2-B5-B"))
        self.assertEqual(0, summary["deterministic_soft_clamp_count"])
        self.assertTrue(summary["strong_enough_for_semantic_quality_review"])

    def test_summary_reports_raw_and_effective_quality_separately(self):
        result = {
            "case_id": "HG-007",
            "json_parse_passed": True,
            "phase_b_soft_proposal_model_raw_schema_valid": True,
            "phase_b_soft_proposal_effective_schema_valid": True,
            "phase_b_soft_proposal_model_raw_validation_errors": [],
            "phase_b_soft_proposal_effective_validation_errors": [],
            "phase_b_soft_proposal_model_raw_authority_field_leakage": [],
            "phase_b_soft_proposal_effective_authority_field_leakage": [],
            "soft_proposal_deterministic_clamps": [{"field": "storage_relevance"}],
            "raw_soft_quality_diagnostic": {
                "quality_match_count": 22,
                "quality_compared_count": 29,
                "quality_misses": [],
            },
            "effective_soft_quality_diagnostic": {
                "quality_match_count": 26,
                "quality_compared_count": 29,
                "quality_misses": [],
            },
        }
        summary = model_probe.summarize_results([result], Path("reports/local_model_smoke/1G-B2-F2-B5-B"))
        self.assertFalse(summary["runtime_approved"])
        self.assertFalse(summary["accepted_for_runtime"])
        self.assertTrue(summary["strong_enough_for_semantic_quality_review"])
        self.assertEqual(22, summary["raw_soft_quality_summary"]["soft_quality_match_count"])
        self.assertEqual(26, summary["effective_soft_quality_summary"]["soft_quality_match_count"])
        self.assertTrue(summary["effective_soft_quality_summary"]["improved_over_b5a_baseline"])
        self.assertTrue(summary["soft_quality_summary"]["soft_quality_review_required"])
        self.assertFalse(summary["soft_quality_summary"]["soft_quality_truth_scored"])

    def test_run_local_smoke_uses_mocked_local_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "b2"
            out = tmp_path / "out"
            holdout = tmp_path / "holdout.jsonl"
            source.mkdir()
            source_result = {
                "case_id": "HG-007",
                "policy_overlay_corrected_output": self.phase_a(),
            }
            (source / "HG-007__result.json").write_text(
                json.dumps(source_result, indent=2) + "\n",
                encoding="utf-8",
            )
            holdout.write_text(
                json.dumps(
                    {
                        "case_id": "HG-007",
                        "input_text": "Find public literature DOI sources for BlueRev microalgae modeling.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with patch(
                "local_model_structured_output_probe.call_ollama_chat",
                return_value=self.raw_call(self.valid_soft_proposal()),
            ) as call_model:
                summary = model_probe.run_local_smoke(
                    source_b2_report_dir=source,
                    holdout_path=holdout,
                    schema_path=self.schema_path,
                    out_dir=out,
                    model="qwen3:8b",
                    case_ids="HG-007",
                    timeout_seconds=5,
                )
            call_model.assert_called_once()
            self.assertEqual(1, summary["parse_count"])
            self.assertEqual(1, summary["schema_valid_count"])
            self.assertEqual(0, summary["authority_field_leakage_count"])
            self.assertTrue((out / "HG-007__phase_b_soft_only_result.json").exists())
            self.assertTrue((out / model_probe.SUMMARY_JSON).exists())


if __name__ == "__main__":
    unittest.main()
