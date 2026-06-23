import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_structured_output_probe as probe  # noqa: E402


class FastSecretaryPhaseBSoftReviewSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = ROOT / "schemas/fast_secretary_soft_review_v0_1.schema.json"
        cls.schema = probe.load_json(cls.schema_path)

    def valid_soft_review(self):
        return {
            "phase_a_case_id": "HG-007",
            "summary_short": "Public literature request for BlueRev microalgae modeling.",
            "project_bucket": "bluerev",
            "primary_domain": "bioprocess",
            "domain_tags": ["microalgae", "literature", "modeling"],
            "storage_relevance": "medium",
            "usefulness_for_future_review": "medium",
            "possible_memory_card_type": "source_card",
            "soft_reason_code": "source_candidate",
            "brief_rationale": "Useful candidate-source request, but Phase A controls retrieval and review gates.",
            "suggested_followup_question": "",
            "soft_uncertain_fields": ["source_scope"],
            "phase_a_blocked": False,
            "phase_a_clarification_required": False,
            "phase_a_external_provider_allowed": False,
            "phase_a_requires_manual_review": True,
            "can_override_phase_a": False,
            "recommends_external_provider": False,
            "recommends_retrieval": False,
            "requires_manual_review": True,
        }

    def test_phase_b_schema_loads_and_is_closed_object(self):
        self.assertTrue(self.schema_path.exists())
        probe.validate_schema_shape(self.schema)
        self.assertEqual("FastSecretarySoftReviewV0_1", self.schema["title"])
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("can_override_phase_a", self.schema["required"])
        self.assertIn("requires_manual_review", self.schema["required"])

    def test_phase_b_valid_object_passes_local_shape_validation(self):
        result = probe.validate_instance(self.valid_soft_review(), self.schema)
        self.assertTrue(result["schema_valid"], result["errors"])
        self.assertEqual(set(self.schema["required"]), set(self.valid_soft_review()))

    def test_phase_b_rejects_extra_field_and_invalid_enum(self):
        value = self.valid_soft_review()
        value["extra_authority"] = "not allowed"
        value["project_bucket"] = "runtime_memory"
        result = probe.validate_instance(value, self.schema)
        self.assertFalse(result["schema_valid"])
        self.assertIn(
            {"field": "extra_authority", "error": "additional field not allowed"},
            result["errors"],
        )
        self.assertIn(
            {"field": "project_bucket", "error": "invalid enum value"},
            result["errors"],
        )

    def test_phase_b_schema_declares_sticky_non_override_constants(self):
        self.assertEqual(
            False,
            self.schema["properties"]["can_override_phase_a"]["const"],
        )
        self.assertEqual(
            True,
            self.schema["properties"]["requires_manual_review"]["const"],
        )

    def test_phase_b_blocked_sample_does_not_recommend_provider_or_retrieval(self):
        value = self.valid_soft_review()
        value.update(
            {
                "phase_a_case_id": "HG-018",
                "summary_short": "Whole memory folder provider upload request.",
                "project_bucket": "jarvisos",
                "primary_domain": "memory",
                "storage_relevance": "none",
                "usefulness_for_future_review": "low",
                "possible_memory_card_type": "none",
                "soft_reason_code": "blocked_by_phase_a",
                "brief_rationale": "Review context only; Phase A remains blocked.",
                "phase_a_blocked": True,
                "phase_a_clarification_required": False,
                "phase_a_external_provider_allowed": False,
                "can_override_phase_a": False,
                "recommends_external_provider": False,
                "recommends_retrieval": False,
                "requires_manual_review": True,
            }
        )
        result = probe.validate_instance(value, self.schema)
        self.assertTrue(result["schema_valid"], result["errors"])
        self.assertFalse(value["can_override_phase_a"])
        self.assertFalse(value["recommends_external_provider"])
        self.assertFalse(value["recommends_retrieval"])
        self.assertTrue(value["requires_manual_review"])


if __name__ == "__main__":
    unittest.main()
