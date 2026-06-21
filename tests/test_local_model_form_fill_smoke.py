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


if __name__ == "__main__":
    unittest.main()
