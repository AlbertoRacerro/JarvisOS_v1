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

import local_model_structured_output_probe as schema_probe  # noqa: E402
import local_policy_gate_overlay_probe as overlay  # noqa: E402


class PolicyGateOverlayReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_hard_gate_v0_1.schema.json"
        cls.holdout_path = ROOT / "docs/holdout/intake_generalization_v0.jsonl"
        cls.schema = schema_probe.load_json(cls.schema_path)
        cls.holdout_cases = overlay.load_holdout_cases(cls.holdout_path)

    def saved_result(self, case_id="HG-007"):
        return {
            "case_id": case_id,
            "json_parse_passed": True,
            "schema_valid": True,
            "parsed_output": {
                "contains_secret_or_credential": False,
                "contains_raw_private_or_ip_sensitive_context": False,
                "mentions_external_provider_or_upload_intent": False,
                "memory_boundary_or_write_authority_claim": False,
                "retrieval_or_source_use_request": False,
                "unresolved_assumption_or_open_decision": False,
                "clarification_required": False,
                "redaction_required": False,
                "external_provider_allowed": False,
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "blocked",
                "lifecycle_status_proposal": "accepted_memory",
                "sensitivity_bucket_proposal": "public",
                "requires_manual_review": True,
                "hard_reason_code": "low_risk",
                "hard_uncertain_fields": [],
            },
            "semantic_comparison": {
                "hard_match_count": 1,
                "hard_compared_count": 3,
                "hard": [],
            },
        }

    def write_saved_result(self, directory, case_id="HG-007"):
        path = directory / f"{case_id}__result.json"
        path.write_text(
            json.dumps(self.saved_result(case_id), indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_replay_saved_result_applies_overlay_and_compares(self):
        saved = self.saved_result("HG-007")
        replayed = overlay.replay_saved_result(
            saved,
            self.holdout_cases["HG-007"],
            self.schema,
        )
        corrected = replayed["corrected_output"]
        self.assertEqual("review_only", corrected["source_policy_for_future_retrieval"])
        self.assertEqual(
            "candidate_discovery_only",
            corrected["allowed_future_retrieval_behavior"],
        )
        self.assertTrue(replayed["schema_valid"])
        self.assertTrue(replayed["semantic_comparison"]["semantic_comparison_performed"])

    def test_replay_summary_counts_baseline_and_corrected(self):
        saved = self.saved_result("HG-007")
        replayed = overlay.replay_saved_result(
            saved,
            self.holdout_cases["HG-007"],
            self.schema,
        )
        summary = overlay.summarize_replay(
            [replayed],
            source_report_dir=Path("source"),
            out_dir=Path("out"),
        )
        self.assertEqual(1, summary["cases_replayed"])
        self.assertEqual({"matches": 1, "compared": 3, "rate": 1 / 3}, summary["baseline_hard_score"])
        self.assertGreater(
            summary["overlay_corrected_hard_score"]["matches"],
            summary["baseline_hard_score"]["matches"],
        )
        self.assertTrue(summary["all_corrected_outputs_schema_valid"])

    def test_run_replay_writes_artifacts_without_overwriting_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            out = tmp_path / "out"
            source.mkdir()
            result_path = self.write_saved_result(source, "HG-007")
            before = result_path.read_text(encoding="utf-8")
            summary = overlay.run_replay(
                replay_report_dir=source,
                holdout_path=self.holdout_path,
                schema_path=self.schema_path,
                out_dir=out,
            )
            self.assertEqual(before, result_path.read_text(encoding="utf-8"))
            self.assertTrue((out / "HG-007__overlay_replay.json").exists())
            self.assertTrue((out / "policy_gate_overlay_replay_summary.json").exists())
            self.assertTrue((out / "policy_gate_overlay_replay_summary.md").exists())
            self.assertEqual(1, summary["cases_replayed"])

    def test_replay_cli_argument_path_uses_temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            out = tmp_path / "out"
            source.mkdir()
            self.write_saved_result(source, "HG-025")
            output = StringIO()
            with redirect_stdout(output):
                exit_code = overlay.main(
                    [
                        "--replay-report-dir",
                        str(source),
                        "--holdout",
                        str(self.holdout_path),
                        "--schema-path",
                        str(self.schema_path),
                        "--out-dir",
                        str(out),
                    ]
                )
            self.assertEqual(0, exit_code)
            self.assertIn("policy_gate_overlay_replay_summary_v0", output.getvalue())
            summary = json.loads(
                (out / "policy_gate_overlay_replay_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(["HG-025"], summary["case_ids"])
            self.assertTrue(
                summary["intended_case_outcomes"]["HG-025"]["checks"][
                    "clarification_required"
                ]
            )

    def test_replay_does_not_call_network_or_model(self):
        with patch.object(schema_probe, "call_ollama_chat") as call_ollama:
            saved = self.saved_result("HG-018")
            replayed = overlay.replay_saved_result(
                saved,
                self.holdout_cases["HG-018"],
                self.schema,
            )
            self.assertTrue(replayed["schema_valid"])
            call_ollama.assert_not_called()


if __name__ == "__main__":
    unittest.main()
