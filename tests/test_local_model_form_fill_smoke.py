import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
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
        cls.micro_pack_path = (
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_MICRO_v0_1.md"
        )
        cls.micro_rules_pack_path = (
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_MICRO_RULES_v0_2.md"
        )
        cls.lite_rules_pack_path = (
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_LITE_RULES_v0_2.md"
        )
        cls.qwen_pack_paths = [
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_RECIPE_ONLY_v0_3.md",
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_RECIPE_TABLE_v0_3.md",
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_EXAMPLES_v0_3.md",
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_HYBRID_v0_3.md",
            ROOT / "docs/context_packs/JARVISOS_FAST_SECRETARY_QWEN_OUTPUT_STRICT_v0_3.md",
        ]
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
        selected = self.cases[:13]
        selected_models = smoke.select_models(self.config, ["qwen3:8b"])
        with self.assertRaisesRegex(ValueError, "limited to 12 cases"):
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

    def test_v02_pack_files_exist_and_load(self):
        for path in [self.micro_rules_pack_path, self.lite_rules_pack_path]:
            self.assertTrue(path.exists())
            pack = smoke.load_context_pack(path)
            self.assertIn("Case Routing Recipes", pack["content"])
            self.assertIn("Output Discipline", pack["content"])

    def test_qwen_v03_pack_files_exist_and_load(self):
        for path in self.qwen_pack_paths:
            self.assertTrue(path.exists())
            pack = smoke.load_context_pack(path)
            self.assertGreater(pack["char_count"], 0)
            self.assertIn("Qwen", pack["content"])

    def test_context_pack_loading(self):
        pack = smoke.load_context_pack(self.micro_pack_path)
        self.assertGreater(pack["char_count"], 0)
        self.assertIn("Fast Secretary", pack["content"])

    def test_context_pack_metadata(self):
        pack = smoke.load_context_pack(self.micro_pack_path)
        pack["label"] = smoke.default_pack_label(self.micro_pack_path)
        self.assertEqual("micro", pack["label"])
        self.assertEqual(str(self.micro_pack_path), pack["path"])
        self.assertGreater(pack["approx_token_estimate"], 0)

    def test_pack_label_preserved_in_result(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-001")
        model = smoke.select_models(self.config, ["qwen3:8b"])[0]
        pack = smoke.load_context_pack(self.micro_rules_pack_path)
        pack["label"] = "micro_rules_v0_2"
        raw_path = Path("reports/local_model_smoke/test/raw.txt")
        result = smoke.build_result_record(
            model=model,
            case=case,
            raw_path=raw_path,
            ollama_result={
                "stdout": '{"case_id": "HG-001"}',
                "stderr": "",
                "duration_seconds": 0.1,
                "returncode": 0,
                "timed_out": False,
            },
            context_pack=pack,
        )
        self.assertEqual("micro_rules_v0_2", result["context_pack_label"])

    def test_summary_includes_pack_size_and_token_estimate(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-001")
        model = smoke.select_models(self.config, ["qwen3:8b"])[0]
        pack = smoke.load_context_pack(self.qwen_pack_paths[0])
        pack["label"] = "qwen_recipe_only_v0_3"
        result = smoke.build_result_record(
            model=model,
            case=case,
            raw_path=Path("reports/local_model_smoke/test/raw.txt"),
            ollama_result={
                "stdout": json.dumps(
                    {
                        "case_id": "HG-001",
                        "project_bucket": "jarvisos",
                        "primary_domain": "memory",
                        "domain_tags": ["memory", "software", "architecture"],
                        "storage_relevance": "high",
                        "lifecycle_status_proposal": "proposed_memory",
                        "sensitivity_bucket_proposal": "internal",
                        "source_class_policy_proposal": "review_only",
                        "retrieval_behavior_proposal": "none",
                        "not_decided": False,
                        "clarification_required": False,
                        "api_or_model_escalation_recommended": False,
                        "reasoning_route_proposal": "none",
                        "brief_rationale": "memory boundary",
                    }
                ),
                "stderr": "",
                "duration_seconds": 0.1,
                "returncode": 0,
                "timed_out": False,
            },
            context_pack=pack,
        )
        summary = smoke.summarize_ablation([result], Path("reports/local_model_smoke/test"))
        profile = summary["profiles"][0]
        self.assertIn("context_pack_char_count", profile)
        self.assertIn("context_pack_approx_token_estimate", profile)

    def test_score_per_token_diagnostics_exist(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-001")
        model = smoke.select_models(self.config, ["qwen3:8b"])[0]
        pack = smoke.load_context_pack(self.qwen_pack_paths[1])
        pack["label"] = "qwen_recipe_table_v0_3"
        result = smoke.build_result_record(
            model=model,
            case=case,
            raw_path=Path("reports/local_model_smoke/test/raw.txt"),
            ollama_result={
                "stdout": '{"case_id": "HG-001"}',
                "stderr": "",
                "duration_seconds": 0.1,
                "returncode": 0,
                "timed_out": False,
            },
            context_pack=pack,
        )
        profile = smoke.summarize_ablation(
            [result],
            Path("reports/local_model_smoke/test"),
        )["profiles"][0]
        self.assertIn("hard_matches_per_1k_tokens", profile)
        self.assertIn("soft_tolerant_matches_per_1k_tokens", profile)
        self.assertIn("successful_parse_per_1k_tokens", profile)

    def test_soft_hard_score_separation(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-006")
        parsed = {
            "project_bucket": "bluerev",
            "primary_domain": "reactor_design",
            "domain_tags": ["reactor_design", "materials", "not_decided"],
            "storage_relevance": "high",
            "brief_rationale": "tentative material",
            "lifecycle_status_proposal": "proposed_memory",
            "sensitivity_bucket_proposal": "internal",
            "source_class_policy_proposal": "review_only",
            "retrieval_behavior_proposal": "review_gate_required",
            "not_decided": True,
            "clarification_required": False,
            "api_or_model_escalation_recommended": True,
            "reasoning_route_proposal": "local_senior_model",
        }
        score = smoke.score_output(parsed, case, secretary_mode=True)
        self.assertEqual(5, score["soft"]["matched"])
        self.assertEqual(8, score["hard"]["matched"])
        self.assertEqual([], score["critical_gates"]["failures"])

    def test_domain_tags_aware_soft_scoring(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-001")
        parsed = {
            "project_bucket": "jarvisos",
            "primary_domain": "software",
            "domain_tags": ["software", "memory", "architecture"],
            "storage_relevance": "high",
            "brief_rationale": "architecture rule",
        }
        score = smoke.score_soft_fields(parsed, case)
        self.assertFalse(score["fields"]["primary_domain"]["exact_matched"])
        self.assertTrue(score["fields"]["domain_tags"]["tolerant_matched"])

    def test_secret_security_tolerant_soft_scoring(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-016")
        parsed = {
            "project_bucket": "general",
            "primary_domain": "security",
            "domain_tags": ["security", "software", "secret_handling"],
            "storage_relevance": "high",
            "brief_rationale": "secret handling",
            "lifecycle_status_proposal": "raw_input",
            "sensitivity_bucket_proposal": "secret",
            "source_class_policy_proposal": "blocked",
            "retrieval_behavior_proposal": "blocked",
            "api_or_model_escalation_recommended": False,
            "reasoning_route_proposal": "none",
        }
        score = smoke.score_soft_fields(parsed, case)
        self.assertFalse(score["fields"]["primary_domain"]["exact_matched"])
        self.assertTrue(score["fields"]["primary_domain"]["tolerant_matched"])
        self.assertGreater(score["tolerant_matched"], score["exact_matched"])

    def test_exact_and_tolerant_soft_scores_both_reported(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-016")
        score = smoke.score_output(
            {
                "primary_domain": "security",
                "domain_tags": ["software", "secret_handling"],
                "sensitivity_bucket_proposal": "secret",
                "source_class_policy_proposal": "blocked",
                "retrieval_behavior_proposal": "blocked",
                "api_or_model_escalation_recommended": False,
                "reasoning_route_proposal": "none",
            },
            case,
            secretary_mode=True,
        )
        self.assertIn("exact_matched", score["soft"])
        self.assertIn("tolerant_matched", score["soft"])

    def test_legacy_field_compatibility(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-016")
        parsed = {
            "project_bucket": "general",
            "domain_bucket": "software",
            "storage_relevance": "high",
            "lifecycle_status": "raw_input",
            "sensitivity_bucket": "secret",
            "source_class_policy": "blocked",
            "retrieval_behavior": "blocked",
            "not_decided": False,
            "clarification": False,
            "api_or_model_escalation_recommended": False,
            "reasoning_route_proposal": "none",
        }
        score = smoke.score_output(parsed, case)
        self.assertEqual(8, score["hard"]["matched"])
        self.assertEqual([], score["critical_gates"]["failures"])

    def test_critical_gate_check_detection(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-016")
        parsed = {
            "sensitivity_bucket_proposal": "internal",
            "source_class_policy_proposal": "review_only",
            "retrieval_behavior_proposal": "full_body_required",
            "api_or_model_escalation_recommended": True,
            "reasoning_route_proposal": "external_provider",
        }
        gates = smoke.critical_gate_checks(parsed, case)
        self.assertIn("secret_implies_secret_blocked_blocked", gates["failures"])
        self.assertIn("no_external_provider_for_raw_secret", gates["failures"])

    def test_critical_gates_still_fail_when_secret_not_blocked(self):
        case = next(case for case in self.cases if case["case_id"] == "HG-016")
        gates = smoke.critical_gate_checks(
            {
                "sensitivity_bucket_proposal": "secret",
                "source_class_policy_proposal": "review_only",
                "retrieval_behavior_proposal": "full_body_required",
                "api_or_model_escalation_recommended": False,
                "reasoning_route_proposal": "none",
            },
            case,
        )
        self.assertIn("secret_implies_secret_blocked_blocked", gates["failures"])

    def test_dry_run_with_context_pack_still_works(self):
        output = StringIO()
        with redirect_stdout(output):
            result = smoke.main(
                [
                    "--dry-run",
                    "--include-disabled",
                    "--max-cases",
                    "1",
                    "--context-pack",
                    str(self.micro_pack_path),
                    "--pack-label",
                    "micro",
                ]
            )
        self.assertEqual(0, result)
        self.assertIn("context pack label: micro", output.getvalue())

    def test_dry_run_with_v02_context_pack_still_works(self):
        output = StringIO()
        with redirect_stdout(output):
            result = smoke.main(
                [
                    "--dry-run",
                    "--include-disabled",
                    "--max-cases",
                    "1",
                    "--context-pack",
                    str(self.micro_rules_pack_path),
                    "--pack-label",
                    "micro_rules_v0_2",
                ]
            )
        self.assertEqual(0, result)
        self.assertIn("context pack label: micro_rules_v0_2", output.getvalue())

    def test_dry_run_with_new_qwen_pack_still_works(self):
        output = StringIO()
        with redirect_stdout(output):
            result = smoke.main(
                [
                    "--dry-run",
                    "--include-disabled",
                    "--max-cases",
                    "1",
                    "--context-pack",
                    str(self.qwen_pack_paths[3]),
                    "--pack-label",
                    "qwen_hybrid_v0_3",
                ]
            )
        self.assertEqual(0, result)
        self.assertIn("context pack label: qwen_hybrid_v0_3", output.getvalue())

    def test_legacy_v01_report_compatibility_preserved(self):
        report_path = (
            ROOT
            / "reports/local_model_smoke/1G-B2-A/micro__local_model_form_fill_smoke_summary.json"
        )
        data = json.loads(report_path.read_text(encoding="utf-8"))
        row = data["core_field_exact_matches_by_run"][0]
        self.assertIn("exact_matches", row)
        self.assertIn("soft_matches", row)
        self.assertIn("hard_matches", row)


if __name__ == "__main__":
    unittest.main()
