import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as probe  # noqa: E402


class PhaseBSoftReviewHarnessIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hard_gate_schema_path = (
            ROOT / "schemas/fast_secretary_hard_gate_v0_1.schema.json"
        )
        cls.phase_b_schema_path = (
            ROOT / "schemas/fast_secretary_soft_review_v0_1.schema.json"
        )

    def phase_a_object(self):
        return {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": False,
            "retrieval_or_source_use_request": True,
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

    def saved_result(self):
        phase_a = self.phase_a_object()
        return {
            "case_id": "HG-007",
            "model": "qwen3:8b",
            "context_pack_path": None,
            "raw_response_path": "source/raw.json",
            "ollama_ok": True,
            "ollama_status": 200,
            "duration_seconds": 0.0,
            "parsed_output": phase_a,
            "policy_overlay_corrected_output": phase_a,
            "policy_overlay_schema_valid": True,
            "semantic_comparison": {
                "semantic_comparison_performed": True,
                "hard": [],
                "soft_tolerant": [],
                "not_compared": [],
                "hard_match_count": 1,
                "hard_compared_count": 3,
                "soft_tolerant_match_count": 0,
                "soft_tolerant_compared_count": 0,
                "severe_hard_misses": [],
            },
        }

    def test_phase_b_summary_filenames_for_b2(self):
        summary_json, summary_md = probe.summary_filenames(
            Path("reports/local_model_smoke/1G-B2-F2-B2")
        )
        self.assertEqual(
            "phase_b_soft_review_harness_integration_summary.json",
            summary_json,
        )
        self.assertEqual(
            "phase_b_soft_review_harness_integration_summary.md",
            summary_md,
        )

    def test_replay_existing_can_apply_phase_b_soft_review_without_overlay_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            out = tmp_path / "1G-B2-F2-B2"
            holdout = tmp_path / "holdout.jsonl"
            source.mkdir()
            (source / "HG-007__result.json").write_text(
                json.dumps(self.saved_result(), indent=2) + "\n",
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
            with patch.object(probe, "call_ollama_chat") as call_ollama:
                output = StringIO()
                with redirect_stdout(output):
                    result = probe.main(
                        [
                            "--replay-existing-report-dir",
                            str(source),
                            "--apply-phase-b-soft-review",
                            "--holdout",
                            str(holdout),
                            "--schema-path",
                            str(self.hard_gate_schema_path),
                            "--phase-b-schema-path",
                            str(self.phase_b_schema_path),
                            "--report-dir",
                            str(out),
                        ]
                    )
            self.assertEqual(0, result)
            call_ollama.assert_not_called()
            summary_path = out / "phase_b_soft_review_harness_integration_summary.json"
            self.assertTrue(summary_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["phase_b_soft_review"]["integrated_into_harness"])
            self.assertTrue(summary["phase_b_soft_review"]["explicit_opt_in"])
            self.assertEqual(1, summary["phase_b_soft_review"]["schema_valid_count"])
            self.assertEqual(0, summary["phase_b_soft_review"]["monotonicity_violation_count"])
            self.assertFalse(summary["phase_b_soft_review"]["runtime_approved"])
            case_result = json.loads(
                (out / "HG-007__result.json").read_text(encoding="utf-8")
            )
            self.assertTrue(case_result["phase_b_soft_review_requested"])
            self.assertTrue(case_result["phase_b_soft_review_schema_valid"])
            self.assertEqual([], case_result["phase_b_soft_review_monotonicity_violations"])

    def test_replay_existing_requires_at_least_one_replay_transform(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            source.mkdir()
            (source / "HG-007__result.json").write_text(
                json.dumps(self.saved_result(), indent=2) + "\n",
                encoding="utf-8",
            )
            result = probe.main(
                [
                    "--replay-existing-report-dir",
                    str(source),
                    "--schema-path",
                    str(self.hard_gate_schema_path),
                ]
            )
            self.assertEqual(2, result)

    def test_phase_b_soft_review_rejects_nonexistent_phase_b_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            source.mkdir()
            (source / "HG-007__result.json").write_text(
                json.dumps(self.saved_result(), indent=2) + "\n",
                encoding="utf-8",
            )
            result = probe.main(
                [
                    "--replay-existing-report-dir",
                    str(source),
                    "--apply-phase-b-soft-review",
                    "--schema-path",
                    str(self.hard_gate_schema_path),
                    "--phase-b-schema-path",
                    str(tmp_path / "missing.json"),
                ]
            )
            self.assertEqual(2, result)


if __name__ == "__main__":
    unittest.main()
