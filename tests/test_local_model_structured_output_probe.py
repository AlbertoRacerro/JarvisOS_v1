import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as probe  # noqa: E402


class StructuredOutputProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_intake_v0_1.schema.json"
        cls.context_pack_path = (
            ROOT
            / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_PARSE_SAFE_v0_4.md"
        )
        cls.schema = probe.load_json(cls.schema_path)

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

    def test_schema_file_loads_and_is_closed_object(self):
        self.assertTrue(self.schema_path.exists())
        probe.validate_schema_shape(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("summary_short", self.schema["required"])

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


if __name__ == "__main__":
    unittest.main()
