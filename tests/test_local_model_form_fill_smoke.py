import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_form_fill_smoke as smoke  # noqa: E402


EXPECTED_OLLAMA_NAMES = [
    "mistral-small3.2:24b",
    "qwen3:14b",
    "qwen3:8b",
    "gemma4:31b-it-qat",
    "gemma4:12b-it-qat",
]


class LocalModelFormFillSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.holdout_path = ROOT / smoke.DEFAULT_HOLDOUT
        cls.config_path = ROOT / smoke.DEFAULT_CONFIG
        cls.cases = smoke.load_jsonl_holdout(cls.holdout_path)
        cls.config = smoke.load_candidate_config(cls.config_path)

    def test_holdout_jsonl_loads_from_real_path(self):
        self.assertTrue(self.holdout_path.exists())
        self.assertGreater(len(self.cases), 0)

    def test_full_holdout_has_32_cases(self):
        smoke.validate_holdout_cases(self.cases, require_full_set=True)
        self.assertEqual(32, len(self.cases))

    def test_case_ids_are_unique(self):
        case_ids = [case["case_id"] for case in self.cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_required_expected_fields_exist(self):
        for case in self.cases:
            missing = smoke.REQUIRED_HOLDOUT_FIELDS - set(case)
            self.assertEqual(set(), missing, case.get("case_id"))

    def test_candidate_config_loads_from_real_path(self):
        self.assertTrue(self.config_path.exists())
        smoke.validate_candidate_config(self.config)

    def test_config_has_exact_supplied_installed_model_names(self):
        names = [model["ollama_name"] for model in self.config["models"]]
        self.assertEqual(EXPECTED_OLLAMA_NAMES, names)

    def test_all_candidates_default_disabled(self):
        self.assertTrue(all(model["enabled"] is False for model in self.config["models"]))

    def test_dry_run_selection_works_for_explicit_case_ids(self):
        selected = smoke.select_cases(
            self.cases,
            case_ids=["HG-001", "HG-006"],
        )
        self.assertEqual(["HG-001", "HG-006"], [case["case_id"] for case in selected])

    def test_fake_output_validation_accepts_minimal_valid_output(self):
        known_case_ids = {case["case_id"] for case in self.cases}
        result = smoke.validate_fake_output_record(
            {"case_id": "HG-001"},
            known_case_ids,
        )
        self.assertTrue(result["valid"])
        self.assertEqual([], result["errors"])

    def test_fake_output_validation_rejects_missing_case_id(self):
        known_case_ids = {case["case_id"] for case in self.cases}
        result = smoke.validate_fake_output_record({}, known_case_ids)
        self.assertFalse(result["valid"])
        self.assertIn("missing case_id", result["errors"])

    def test_fake_output_validation_rejects_unknown_case_id(self):
        known_case_ids = {case["case_id"] for case in self.cases}
        result = smoke.validate_fake_output_record(
            {"case_id": "HG-999"},
            known_case_ids,
        )
        self.assertFalse(result["valid"])
        self.assertIn("unknown case_id: HG-999", result["errors"])

    def test_json_fence_stripping(self):
        wrapped = """```json
{"case_id": "HG-001"}
```"""
        self.assertEqual('{"case_id": "HG-001"}', smoke.strip_json_fences(wrapped))

    def test_output_parser_success(self):
        parsed, error = smoke.parse_model_json_output('{"case_id": "HG-001"}')
        self.assertEqual({"case_id": "HG-001"}, parsed)
        self.assertIsNone(error)

    def test_output_parser_success_with_preamble_and_control_chars(self):
        raw = "Thinking...\nnoise \x1b[2D\x1b[K\n{\"case_id\": \"HG-001\"}\ntrailing"
        parsed, error = smoke.parse_model_json_output(raw)
        self.assertEqual({"case_id": "HG-001"}, parsed)
        self.assertIsNone(error)

    def test_output_parser_success_with_wrapped_string(self):
        raw = '{"case_id": "HG-001", "brief_rationale": "line\nwrapped"}'
        parsed, error = smoke.parse_model_json_output(raw)
        self.assertEqual(
            {"case_id": "HG-001", "brief_rationale": "line wrapped"},
            parsed,
        )
        self.assertIsNone(error)

    def test_output_parser_failure(self):
        parsed, error = smoke.parse_model_json_output("not json")
        self.assertIsNone(parsed)
        self.assertIsInstance(error, str)

    def test_core_field_comparison(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-001")
        parsed = {
            "case_id": "HG-001",
            "project_bucket": case["expected_project_bucket"],
            "domain_bucket": case["expected_domain_bucket"],
            "storage_relevance": case["expected_storage_relevance"],
            "lifecycle_status": case["expected_lifecycle_status"],
            "sensitivity_bucket": case["expected_sensitivity_bucket"],
            "source_class_policy": case["expected_source_class_policy"],
            "retrieval_behavior": case["expected_retrieval_behavior"],
            "flags": list(case["expected_flags"]),
            "not_decided": case["expected_not_decided"],
            "clarification": case["expected_clarification"],
            "brief_rationale": "short reason",
        }
        comparison = smoke.compare_output_to_expected(parsed, case)
        self.assertEqual(9, comparison["core_field_match_count"])
        self.assertEqual([], comparison["expected_flags_missing"])
        self.assertTrue(all(comparison["enum_validity"].values()))

    def test_real_run_case_limit_guard(self):
        selected = self.cases[:4]
        selected_models = smoke.select_models(self.config, ["qwen3:8b"])
        with self.assertRaisesRegex(ValueError, "limited to 3 cases"):
            smoke.validate_real_run_selection(
                selected_cases=selected,
                explicit_case_ids=[case["case_id"] for case in selected],
                selected_models=selected_models,
            )

    def test_selected_model_validation_by_ollama_name(self):
        selected = smoke.select_models(
            self.config,
            ["qwen3:8b", "gemma4:12b-it-qat"],
        )
        self.assertEqual(
            ["qwen3:8b", "gemma4:12b-it-qat"],
            [model["ollama_name"] for model in selected],
        )

    def test_selected_model_validation_rejects_unknown(self):
        with self.assertRaisesRegex(ValueError, "not in config"):
            smoke.select_models(self.config, ["qwen3:14b", "missing:model"])

    def test_report_filename_sanitization(self):
        self.assertEqual("qwen3_8b", smoke.sanitize_filename("qwen3:8b"))
        self.assertEqual(
            "gemma4_12b-it-qat",
            smoke.sanitize_filename("gemma4:12b-it-qat"),
        )

    def test_raw_output_report_format_strips_trailing_whitespace(self):
        self.assertEqual("a\nb\n", smoke.format_raw_output_for_report("a  \nb\t\n\n"))


if __name__ == "__main__":
    unittest.main()
