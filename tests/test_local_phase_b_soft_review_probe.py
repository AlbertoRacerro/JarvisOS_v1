import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as structured_probe  # noqa: E402
import local_phase_b_soft_review_probe as phase_b  # noqa: E402


class PhaseBSoftReviewFixtureProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_soft_review_v0_1.schema.json"
        cls.schema = structured_probe.load_json(cls.schema_path)

    def phase_a(self, **updates):
        value = {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": False,
            "retrieval_or_source_use_request": False,
            "unresolved_assumption_or_open_decision": False,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": False,
            "source_policy_for_future_retrieval": "review_only",
            "allowed_future_retrieval_behavior": "candidate_discovery_only",
            "lifecycle_status_proposal": "proposed_memory",
            "sensitivity_bucket_proposal": "internal",
            "requires_manual_review": True,
            "hard_reason_code": "retrieval_or_source_request",
            "hard_uncertain_fields": [],
        }
        value.update(updates)
        return value

    def test_build_soft_review_validates_against_schema(self):
        review = phase_b.build_soft_review(
            case_id="HG-007",
            input_text="Find public literature DOI sources for BlueRev microalgae modeling.",
            phase_a=self.phase_a(),
        )
        validation = structured_probe.validate_instance(review, self.schema)
        self.assertTrue(validation["schema_valid"], validation["errors"])
        self.assertFalse(review["can_override_phase_a"])
        self.assertTrue(review["requires_manual_review"])

    def test_blocked_phase_a_cannot_recommend_provider_or_retrieval(self):
        hard = self.phase_a(
            contains_secret_or_credential=True,
            external_provider_allowed=False,
            source_policy_for_future_retrieval="blocked",
            allowed_future_retrieval_behavior="blocked",
            hard_reason_code="secret_or_credential",
        )
        review = phase_b.build_soft_review(
            case_id="HG-018",
            input_text="Upload the whole memory folder to GPT.",
            phase_a=hard,
        )
        self.assertTrue(review["phase_a_blocked"])
        self.assertFalse(review["can_override_phase_a"])
        self.assertFalse(review["recommends_external_provider"])
        self.assertFalse(review["recommends_retrieval"])
        self.assertEqual([], phase_b.monotonicity_violations(review, hard))

    def test_clarification_phase_a_blocks_retrieval_recommendation(self):
        hard = self.phase_a(
            clarification_required=True,
            source_policy_for_future_retrieval="blocked",
            allowed_future_retrieval_behavior="clarification_required",
        )
        review = phase_b.build_soft_review(
            case_id="HG-025",
            input_text="Use the latest decision from the memory document.",
            phase_a=hard,
        )
        self.assertTrue(review["phase_a_clarification_required"])
        self.assertFalse(review["recommends_retrieval"])
        self.assertIn("Which exact source", review["suggested_followup_question"])

    def test_monotonicity_detects_invalid_override(self):
        hard = self.phase_a(
            external_provider_allowed=False,
            source_policy_for_future_retrieval="blocked",
            allowed_future_retrieval_behavior="blocked",
        )
        review = phase_b.build_soft_review(
            case_id="HG-X",
            input_text="Upload memory to GPT.",
            phase_a=hard,
        )
        review["can_override_phase_a"] = True
        review["recommends_external_provider"] = True
        review["recommends_retrieval"] = True
        violations = phase_b.monotonicity_violations(review, hard)
        self.assertGreaterEqual(len(violations), 3)

    def test_run_fixture_writes_reports_without_model_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "phase_a"
            out = tmp_path / "out"
            holdout = tmp_path / "holdout.jsonl"
            source.mkdir()
            phase_a_result = {
                "case_id": "HG-007",
                "policy_overlay_corrected_output": self.phase_a(),
            }
            (source / "HG-007__result.json").write_text(
                json.dumps(phase_a_result, indent=2) + "\n",
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
            with patch.object(structured_probe, "call_ollama_chat") as call_ollama:
                summary = phase_b.run_fixture(
                    phase_a_report_dir=source,
                    holdout_path=holdout,
                    schema_path=self.schema_path,
                    out_dir=out,
                )
            call_ollama.assert_not_called()
            self.assertEqual(1, summary["schema_valid_count"])
            self.assertEqual(0, summary["monotonicity_violation_count"])
            self.assertTrue((out / "HG-007__phase_b_soft_review.json").exists())
            self.assertTrue((out / phase_b.SUMMARY_JSON).exists())
            self.assertTrue((out / phase_b.SUMMARY_MD).exists())


if __name__ == "__main__":
    unittest.main()
