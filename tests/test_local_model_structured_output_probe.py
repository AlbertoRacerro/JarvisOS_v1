import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as probe  # noqa: E402


class StructuredOutputProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_intake_v0_1.schema.json"
        cls.hard_gate_schema_path = (
            ROOT / "schemas/fast_secretary_hard_gate_v0_1.schema.json"
        )
        cls.context_pack_path = (
            ROOT
            / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md"
        )
        cls.schema = probe.load_json(cls.schema_path)
        cls.hard_gate_schema = probe.load_json(cls.hard_gate_schema_path)

    def valid_object(self):
        return {
            "summary_short": "Memory boundary update",
            "project_bucket": "jarvisos",
            "primary_domain": "memory",
            "domain_tags": ["memory", "software"],
            "storage_relevance": "high",
            "lifecycle_status_proposal": "proposed_memory",
            "sensitivity_bucket_proposal": "internal",
            "source_policy_for_future_retrieval": "review_only",
            "allowed_future_retrieval_behavior": "none",
            "not_decided": False,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": False,
            "recommended_reasoning_route": "none",
            "data_package_needed": "none",
            "requires_manual_review": True,
            "brief_reason_code": "memory_boundary",
            "uncertain_fields": [],
        }

    def valid_hard_gate_object(self):
        return {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": True,
            "retrieval_or_source_use_request": False,
            "unresolved_assumption_or_open_decision": False,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": False,
            "source_policy_for_future_retrieval": "review_only",
            "allowed_future_retrieval_behavior": "none",
            "lifecycle_status_proposal": "proposed_memory",
            "sensitivity_bucket_proposal": "internal",
            "requires_manual_review": True,
            "hard_reason_code": "memory_boundary_or_write_authority",
            "hard_uncertain_fields": [],
        }

    def test_schema_file_loads_and_is_closed_object(self):
        self.assertTrue(self.schema_path.exists())
        probe.validate_schema_shape(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("summary_short", self.schema["required"])

    def test_phase_a_schema_file_loads_and_is_closed_object(self):
        self.assertTrue(self.hard_gate_schema_path.exists())
        probe.validate_schema_shape(self.hard_gate_schema)
        self.assertFalse(self.hard_gate_schema["additionalProperties"])
        self.assertNotIn("summary_short", self.hard_gate_schema["required"])
        self.assertIn("contains_secret_or_credential", self.hard_gate_schema["required"])
        self.assertIn("hard_reason_code", self.hard_gate_schema["required"])

    def test_phase_a_validation_accepts_minimal_valid_object(self):
        result = probe.validate_instance(
            self.valid_hard_gate_object(),
            self.hard_gate_schema,
        )
        self.assertTrue(result["schema_valid"])
        self.assertEqual([], result["errors"])

    def test_phase_a_validation_rejects_extra_field_invalid_enum_and_wrong_boolean(self):
        value = self.valid_hard_gate_object()
        value["summary_short"] = "not allowed"
        value["source_policy_for_future_retrieval"] = "maybe"
        value["external_provider_allowed"] = "false"
        result = probe.validate_instance(value, self.hard_gate_schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn(
            {"field": "summary_short", "error": "additional field not allowed"},
            result["errors"],
        )
        self.assertIn(
            {
                "field": "source_policy_for_future_retrieval",
                "error": "invalid enum value",
            },
            result["errors"],
        )
        self.assertIn(
            {"field": "external_provider_allowed", "error": "expected boolean"},
            result["errors"],
        )

    def test_case_id_parsing_and_selection(self):
        cases = probe.load_holdout(ROOT / "docs/holdout/intake_generalization_v0.jsonl")
        selected = probe.select_cases(
            cases,
            case_id=None,
            case_ids="HG-007,HG-018",
        )
        self.assertEqual(["HG-007", "HG-018"], [case["case_id"] for case in selected])

    def test_validation_accepts_minimal_valid_object(self):
        result = probe.validate_instance(self.valid_object(), self.schema)
        self.assertTrue(result["schema_valid"])
        self.assertEqual([], result["errors"])

    def test_validation_rejects_missing_required_field(self):
        value = self.valid_object()
        del value["summary_short"]
        result = probe.validate_instance(value, self.schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn(
            {"field": "summary_short", "error": "missing required field"},
            result["errors"],
        )

    def test_validation_rejects_additional_field(self):
        value = self.valid_object()
        value["extra"] = "nope"
        result = probe.validate_instance(value, self.schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn(
            {"field": "extra", "error": "additional field not allowed"},
            result["errors"],
        )

    def test_validation_rejects_invalid_enum(self):
        value = self.valid_object()
        value["project_bucket"] = "invalid"
        result = probe.validate_instance(value, self.schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn(
            {"field": "project_bucket", "error": "invalid enum value"},
            result["errors"],
        )

    def test_validation_rejects_wrong_boolean_and_array_types(self):
        value = self.valid_object()
        value["not_decided"] = "false"
        value["domain_tags"] = "memory"
        result = probe.validate_instance(value, self.schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn({"field": "not_decided", "error": "expected boolean"}, result["errors"])
        self.assertIn({"field": "domain_tags", "error": "expected array"}, result["errors"])

    def test_dry_run_does_not_call_ollama(self):
        output = StringIO()
        with redirect_stdout(output):
            result = probe.main(
                [
                    "--dry-run",
                    "--case-ids",
                    "HG-007,HG-018",
                    "--schema-path",
                    str(self.schema_path),
                    "--context-pack",
                    str(self.context_pack_path),
                ]
            )
        self.assertEqual(0, result)
        text = output.getvalue()
        self.assertIn("inference disabled in dry-run", text)
        self.assertIn("HG-007, HG-018", text)

    def test_summary_generation_works_without_model_calls(self):
        parsed = self.valid_object()
        result = {
            "case_id": "HG-018",
            "json_parse_passed": True,
            "schema_valid": True,
            "validation_errors": [],
            "parsed_output": parsed,
            "semantic_comparison_performed": True,
            "semantic_comparison": probe.semantic_comparison(
                {
                    "case_id": "HG-018",
                    "category": "provider_intent_block",
                    "expected_project_bucket": "jarvisos",
                    "expected_domain_bucket": "memory",
                    "expected_storage_relevance": "high",
                    "expected_lifecycle_status": "raw_input",
                    "expected_sensitivity_bucket": "sensitive",
                    "expected_source_class_policy": "blocked",
                    "expected_retrieval_behavior": "blocked",
                    "expected_not_decided": False,
                    "expected_clarification": False,
                },
                parsed,
            ),
        }
        summary = probe.summarize_results(
            [result],
            Path("reports/local_model_smoke/test"),
        )
        self.assertEqual(1, summary["parse_count"])
        self.assertEqual(1, summary["schema_valid_count"])
        self.assertTrue(summary["manual_review_required"])
        self.assertFalse(summary["semantic_truth_scored"])
        self.assertIn("recommended_next_milestone", summary)

    def test_parse_model_content_accepts_chat_message_json(self):
        raw = {"message": {"content": json.dumps(self.valid_object())}}
        parsed, error = probe.parse_model_content(raw)
        self.assertIsNone(error)
        self.assertEqual("jarvisos", parsed["project_bucket"])

    def test_semantic_comparison_maps_schema_facing_fields(self):
        case = {
            "case_id": "HG-001",
            "category": "jarvisos_architecture_decision",
            "expected_project_bucket": "jarvisos",
            "expected_domain_bucket": "memory",
            "expected_storage_relevance": "high",
            "expected_lifecycle_status": "proposed_memory",
            "expected_sensitivity_bucket": "internal",
            "expected_source_class_policy": "review_only",
            "expected_retrieval_behavior": "none",
            "expected_not_decided": False,
            "expected_clarification": False,
        }
        comparison = probe.semantic_comparison(case, self.valid_object())
        self.assertTrue(comparison["semantic_comparison_performed"])
        self.assertEqual(9, comparison["hard_match_count"])
        self.assertEqual(9, comparison["hard_compared_count"])
        self.assertEqual(1, comparison["soft_tolerant_match_count"])

    def test_semantic_comparison_records_misses(self):
        case = {
            "case_id": "HG-018",
            "category": "provider_intent_block",
            "expected_project_bucket": "jarvisos",
            "expected_domain_bucket": "memory",
            "expected_storage_relevance": "high",
            "expected_lifecycle_status": "raw_input",
            "expected_sensitivity_bucket": "sensitive",
            "expected_source_class_policy": "blocked",
            "expected_retrieval_behavior": "blocked",
            "expected_not_decided": False,
            "expected_clarification": False,
        }
        value = self.valid_object()
        comparison = probe.semantic_comparison(case, value)
        misses = [item for item in comparison["hard"] if item["status"] == "miss"]
        self.assertTrue(misses)
        self.assertTrue(comparison["severe_hard_misses"])

    def test_semantic_comparison_keeps_ambiguous_fields_not_compared(self):
        comparison = probe.semantic_comparison({}, self.valid_object())
        fields = {item["field"] for item in comparison["not_compared"]}
        self.assertIn("domain_tags", fields)
        self.assertIn("recommended_reasoning_route", fields)
        self.assertIn("data_package_needed", fields)

    def test_f2_summary_generation_includes_semantic_scores(self):
        case = {
            "case_id": "HG-001",
            "category": "jarvisos_architecture_decision",
            "expected_project_bucket": "jarvisos",
            "expected_domain_bucket": "memory",
            "expected_storage_relevance": "high",
            "expected_lifecycle_status": "proposed_memory",
            "expected_sensitivity_bucket": "internal",
            "expected_source_class_policy": "review_only",
            "expected_retrieval_behavior": "none",
            "expected_not_decided": False,
            "expected_clarification": False,
        }
        parsed = self.valid_object()
        comparison = probe.semantic_comparison(case, parsed)
        result = {
            "case_id": "HG-001",
            "json_parse_passed": True,
            "schema_valid": True,
            "validation_errors": [],
            "parsed_output": parsed,
            "semantic_comparison_performed": True,
            "semantic_comparison": comparison,
        }
        summary = probe.summarize_results(
            [result],
            Path("reports/local_model_smoke/1G-B2-F2"),
        )
        self.assertEqual("1G-B2-F2", summary["milestone"])
        self.assertTrue(summary["semantic_comparison_performed"])
        self.assertEqual(9, summary["answers"]["hard_semantic_score"]["matches"])
        self.assertEqual(1, summary["answers"]["soft_tolerant_semantic_score"]["matches"])

    def test_phase_a_comparator_maps_policy_fields(self):
        case = {
            "case_id": "HG-001",
            "category": "jarvisos_architecture_decision",
            "expected_lifecycle_status": "proposed_memory",
            "expected_sensitivity_bucket": "internal",
            "expected_source_class_policy": "review_only",
            "expected_retrieval_behavior": "none",
            "expected_clarification": False,
        }
        comparison = probe.phase_a_hard_gate_comparison(
            case,
            self.valid_hard_gate_object(),
        )
        self.assertTrue(comparison["semantic_comparison_performed"])
        self.assertGreaterEqual(comparison["hard_match_count"], 10)

    def test_phase_a_hg018_blocked_blocked_expectation_is_detected(self):
        case = {
            "case_id": "HG-018",
            "category": "provider_intent_block",
            "expected_lifecycle_status": "raw_input",
            "expected_sensitivity_bucket": "sensitive",
            "expected_source_class_policy": "blocked",
            "expected_retrieval_behavior": "blocked",
            "expected_clarification": False,
        }
        value = self.valid_hard_gate_object()
        value.update(
            {
                "contains_raw_private_or_ip_sensitive_context": True,
                "mentions_external_provider_or_upload_intent": True,
                "retrieval_or_source_use_request": True,
                "source_policy_for_future_retrieval": "blocked",
                "allowed_future_retrieval_behavior": "blocked",
                "lifecycle_status_proposal": "raw_input",
                "sensitivity_bucket_proposal": "sensitive",
                "hard_reason_code": "provider_or_upload_intent",
            }
        )
        comparison = probe.phase_a_hard_gate_comparison(case, value)
        misses = [item for item in comparison["hard"] if item["status"] == "miss"]
        self.assertEqual([], misses)

    def test_apply_policy_overlay_flag_is_accepted(self):
        parser = probe.build_arg_parser()
        args = parser.parse_args(["--apply-policy-overlay"])
        self.assertTrue(args.apply_policy_overlay)

    def test_apply_policy_overlay_rejects_non_hard_gate_schema(self):
        output = StringIO()
        errors = StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            result = probe.main(
                [
                    "--dry-run",
                    "--case-id",
                    "HG-001",
                    "--schema-path",
                    str(self.schema_path),
                    "--apply-policy-overlay",
                ]
            )
        self.assertEqual(2, result)
        self.assertIn("requires the hard-gate schema", errors.getvalue())

    def test_apply_policy_overlay_dry_run_makes_no_model_call(self):
        output = StringIO()
        with patch.object(probe, "call_ollama_chat") as call_ollama:
            with redirect_stdout(output):
                result = probe.main(
                    [
                        "--dry-run",
                        "--case-id",
                        "HG-018",
                        "--schema-path",
                        str(self.hard_gate_schema_path),
                        "--apply-policy-overlay",
                    ]
                )
        self.assertEqual(0, result)
        call_ollama.assert_not_called()
        self.assertIn("policy overlay enabled: True", output.getvalue())

    def test_build_result_with_policy_overlay_preserves_baseline_and_corrected(self):
        cases = probe.load_holdout(ROOT / "docs/holdout/intake_generalization_v0.jsonl")
        case = next(item for item in cases if item["case_id"] == "HG-007")
        raw_call = {
            "ok": True,
            "status": 200,
            "duration_seconds": 0.0,
            "error": None,
            "body": {"message": {"content": json.dumps(self.valid_hard_gate_object())}},
        }
        result = probe.build_result(
            case=case,
            model="qwen3:8b",
            schema_path=self.hard_gate_schema_path,
            context_pack_path=None,
            raw_path=Path("reports/local_model_smoke/1G-B2-F2-P3/HG-007__raw.json"),
            raw_call=raw_call,
            schema=self.hard_gate_schema,
            apply_policy_overlay=True,
        )
        self.assertTrue(result["policy_overlay_applied"])
        self.assertEqual("parsed_output", result["baseline_semantic_comparison"].get("basis", "parsed_output"))
        self.assertEqual(
            "policy_overlay_corrected_output",
            result["semantic_comparison_basis"],
        )
        self.assertEqual(
            "candidate_discovery_only",
            result["policy_overlay_corrected_output"][
                "allowed_future_retrieval_behavior"
            ],
        )
        validation = probe.validate_instance(
            result["policy_overlay_corrected_output"],
            self.hard_gate_schema,
        )
        self.assertTrue(validation["schema_valid"])

    def test_build_result_without_policy_overlay_keeps_existing_shape(self):
        raw_call = {
            "ok": True,
            "status": 200,
            "duration_seconds": 0.0,
            "error": None,
            "body": {"message": {"content": json.dumps(self.valid_hard_gate_object())}},
        }
        result = probe.build_result(
            case={"case_id": "HG-001", "input_text": "JarvisOS memory note"},
            model="qwen3:8b",
            schema_path=self.hard_gate_schema_path,
            context_pack_path=None,
            raw_path=Path("reports/local_model_smoke/1G-B2-F2-A/HG-001__raw.json"),
            raw_call=raw_call,
            schema=self.hard_gate_schema,
        )
        self.assertNotIn("policy_overlay_corrected_output", result)
        self.assertNotIn("baseline_semantic_comparison", result)

    def test_replay_existing_report_dir_writes_p3_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source"
            out = tmp_path / "1G-B2-F2-P3"
            source.mkdir()
            source_result = {
                "case_id": "HG-007",
                "model": "qwen3:8b",
                "context_pack_path": None,
                "raw_response_path": "source/raw.json",
                "ollama_ok": True,
                "ollama_status": 200,
                "duration_seconds": 0.0,
                "parsed_output": self.valid_hard_gate_object(),
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
            source_path = source / "HG-007__result.json"
            source_text = json.dumps(source_result, indent=2) + "\n"
            source_path.write_text(source_text, encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                result = probe.main(
                    [
                        "--replay-existing-report-dir",
                        str(source),
                        "--apply-policy-overlay",
                        "--schema-path",
                        str(self.hard_gate_schema_path),
                        "--report-dir",
                        str(out),
                    ]
                )
            self.assertEqual(0, result)
            self.assertEqual(source_text, source_path.read_text(encoding="utf-8"))
            summary_path = out / "policy_overlay_harness_integration_summary.json"
            self.assertTrue(summary_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["policy_overlay"]["integrated_into_harness"])
            self.assertIn("baseline_hard_score", summary["policy_overlay"])
            self.assertIn("overlay_corrected_hard_score", summary["policy_overlay"])
            self.assertTrue((out / "HG-007__result.json").exists())


if __name__ == "__main__":
    unittest.main()
