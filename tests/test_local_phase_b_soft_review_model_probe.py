import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as structured_probe  # noqa: E402
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

    def raw_call(self, output):
        return {
            "ok": True,
            "status": 200,
            "duration_seconds": 0.1,
            "body": {"message": {"content": json.dumps(output)}},
            "error": None,
        }

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
                source_result={"case_id": "HG-007", "policy_overlay_corrected_output": self.phase_a()},
                schema=self.schema,
                schema_path=self.schema_path,
                model="qwen3:8b",
                raw_path=Path(tmp) / "raw.json",
                raw_call=self.raw_call(self.valid_soft_proposal()),
            )
        self.assertTrue(result["json_parse_passed"])
        self.assertTrue(result["schema_valid"])
        self.assertEqual([], result["authority_field_leakage"])
        envelope = result["review_envelope"]
        self.assertFalse(envelope["runtime_approved"])
        self.assertTrue(envelope["manual_review_required"])
        self.assertIn("phase_a_hard_gate", envelope)
        self.assertIn("phase_b_soft_proposal", envelope)

    def test_authority_field_in_model_output_is_schema_invalid_and_detected(self):
        output = dict(self.valid_soft_proposal())
        output["can_override_phase_a"] = True
        with tempfile.TemporaryDirectory() as tmp:
            result = model_probe.build_model_result(
                case_id="HG-007",
                source_result={"case_id": "HG-007", "policy_overlay_corrected_output": self.phase_a()},
                schema=self.schema,
                schema_path=self.schema_path,
                model="qwen3:8b",
                raw_path=Path(tmp) / "raw.json",
                raw_call=self.raw_call(output),
            )
        self.assertFalse(result["schema_valid"])
        self.assertEqual(["can_override_phase_a"], result["authority_field_leakage"])
        self.assertEqual(1, result["review_envelope"]["authority_field_leakage_count"])

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
