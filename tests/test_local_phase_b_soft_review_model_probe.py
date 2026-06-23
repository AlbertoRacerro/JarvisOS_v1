import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_phase_b_soft_review_model_probe as model_probe  # noqa: E402


class PhaseBSoftReviewModelProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_soft_review_v0_1.schema.json"

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

    def valid_phase_b(self):
        return {
            "phase_a_case_id": "HG-007",
            "summary_short": "Input may support candidate source discovery under review.",
            "project_bucket": "bluerev",
            "primary_domain": "retrieval",
            "domain_tags": ["literature", "bluerev"],
            "storage_relevance": "medium",
            "usefulness_for_future_review": "medium",
            "possible_memory_card_type": "source_card",
            "soft_reason_code": "source_candidate",
            "brief_rationale": "Advisory review context only. Phase A remains authoritative.",
            "suggested_followup_question": "",
            "soft_uncertain_fields": [],
            "phase_a_blocked": False,
            "phase_a_clarification_required": False,
            "phase_a_external_provider_allowed": False,
            "phase_a_requires_manual_review": True,
            "can_override_phase_a": False,
            "recommends_external_provider": False,
            "recommends_retrieval": True,
            "requires_manual_review": True,
        }

    def raw_call(self, output):
        return {
            "ok": True,
            "status": 200,
            "duration_seconds": 0.1,
            "body": {
                "message": {
                    "content": json.dumps(output),
                }
            },
            "error": None,
        }

    def test_build_phase_b_prompt_contains_non_override_rules(self):
        prompt = model_probe.build_phase_b_prompt(
            case_id="HG-007",
            input_text="Find public literature DOI sources for BlueRev microalgae modeling.",
            phase_a=self.phase_a(),
        )
        self.assertIn("can_override_phase_a must be false", prompt)
        self.assertIn("requires_manual_review must be true", prompt)
        self.assertIn("recommends_external_provider must be false", prompt)
        self.assertIn("Case ID: HG-007", prompt)

    def test_model_result_validates_schema_and_monotonicity(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = {"case_id": "HG-007", "policy_overlay_corrected_output": self.phase_a()}
            result = model_probe.build_model_result(
                case_id="HG-007",
                input_text="Find public literature DOI sources for BlueRev microalgae modeling.",
                phase_a_result=source,
                schema=json.loads(self.schema_path.read_text(encoding="utf-8")),
                schema_path=self.schema_path,
                model="qwen3:8b",
                raw_path=tmp_path / "raw.json",
                raw_call=self.raw_call(self.valid_phase_b()),
            )
        self.assertTrue(result["json_parse_passed"])
        self.assertTrue(result["schema_valid"])
        self.assertEqual([], result["monotonicity_violations"])
        self.assertFalse(result["phase_b_can_override_phase_a"])

    def test_summary_marks_runtime_unapproved_even_when_smoke_passes(self):
        result = {
            "case_id": "HG-007",
            "json_parse_passed": True,
            "schema_valid": True,
            "monotonicity_violations": [],
            "phase_b_can_override_phase_a": False,
            "phase_b_requires_manual_review": True,
            "phase_b_recommends_external_provider": False,
        }
        summary = model_probe.summarize_results([result], Path("reports/local_model_smoke/1G-B2-F2-B3"))
        self.assertFalse(summary["runtime_approved"])
        self.assertFalse(summary["accepted_for_runtime"])
        self.assertTrue(summary["strong_enough_for_expanded_phase_b_panel"])

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
                return_value=self.raw_call(self.valid_phase_b()),
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
            self.assertEqual(0, summary["monotonicity_violation_count"])
            self.assertTrue((out / "HG-007__phase_b_model_result.json").exists())
            self.assertTrue((out / model_probe.SUMMARY_JSON).exists())


if __name__ == "__main__":
    unittest.main()
