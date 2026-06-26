import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_external_egress_gate as egress  # noqa: E402


def component(text, *, component_id="current", component_type="current_message"):
    return {"id": component_id, "type": component_type, "text": text}


class RouterPolicyExternalEgressGateTests(unittest.TestCase):
    def assert_denied(self, decision, reason_code):
        self.assertFalse(decision["allowed"])
        self.assertEqual(reason_code, decision["reason_code"])
        self.assertIn(reason_code, decision["reason_codes"])

    def test_e1_clean_unknown_current_message_with_opt_in_allows(self):
        decision = egress.evaluate_external_egress_gate(
            [component("Explain the pump equation in generic terms.")],
            explicit_user_shareability_opt_in=True,
        )

        self.assertTrue(decision["allowed"])
        self.assertEqual("allowed_unknown_clean_with_opt_in", decision["reason_code"])
        self.assertEqual(1, decision["checked_component_count"])
        self.assertEqual(["current"], decision["checked_component_identities"])
        self.assertEqual([], decision["component_results"][0]["positive_danger_signals"])

    def test_e1_clean_unknown_current_message_without_opt_in_denies(self):
        decision = egress.evaluate_external_egress_gate(
            [component("Explain the pump equation in generic terms.")],
            explicit_user_shareability_opt_in=False,
        )

        self.assert_denied(decision, "explicit_shareability_opt_in_required")

    def test_e1_clean_public_or_internal_is_allowed_only_by_opt_in_not_assume_public_simple(self):
        for text in (
            "Explain what BlueRev means at a public high level.",
            "Summarize this internal but non-sensitive project planning sentence.",
        ):
            with self.subTest(text=text):
                decision = egress.evaluate_external_egress_gate(
                    [component(text)],
                    explicit_user_shareability_opt_in=True,
                )

                self.assertTrue(decision["allowed"])
                self.assertEqual("allowed_unknown_clean_with_opt_in", decision["reason_code"])
                self.assertNotIn(
                    "assume_public_simple",
                    " ".join(decision["reason_codes"]),
                )

    def test_e1_clean_public_or_internal_without_opt_in_denies(self):
        for text in (
            "Explain what BlueRev means at a public high level.",
            "Summarize this internal but non-sensitive project planning sentence.",
        ):
            with self.subTest(text=text):
                decision = egress.evaluate_external_egress_gate(
                    [component(text)],
                    explicit_user_shareability_opt_in=False,
                )

                self.assert_denied(decision, "explicit_shareability_opt_in_required")

    def test_e1_positive_secret_and_sensitive_buckets_deny_even_with_opt_in(self):
        cases = (
            ("my API key is sk-test-secret-12345678", "sensitivity_bucket_proposal:secret"),
            ("Keep this proprietary BlueRev calculation private.", "contains_raw_private_or_ip_sensitive_context"),
            ("usa i parametri proprietari BlueRev per dimensionare una pompa", "bluerev_ip_sensitivity_floor"),
            ("salva il token dati proprietari BlueRev abc123", "sensitivity_bucket_proposal:secret"),
        )
        for text, expected_signal in cases:
            with self.subTest(text=text):
                decision = egress.evaluate_external_egress_gate(
                    [component(text)],
                    explicit_user_shareability_opt_in=True,
                )

                self.assert_denied(decision, "positive_danger_signal")
                signals = decision["positive_danger_components"][0]["signals"]
                self.assertIn(expected_signal, signals)

    def test_e1_operational_write_and_credential_save_reasons_deny_even_with_opt_in(self):
        cases = (
            ("remember this project preference for later", "memory_write"),
            ("scrivi nel documento la scelta del materiale", "document_write"),
            ("salva questo token abc123 in memoria", "operational_intent:credential_like_save"),
        )
        for text, expected_signal in cases:
            with self.subTest(text=text):
                decision = egress.evaluate_external_egress_gate(
                    [component(text)],
                    explicit_user_shareability_opt_in=True,
                )

                self.assert_denied(decision, "positive_danger_signal")
                signals = decision["positive_danger_components"][0]["signals"]
                self.assertIn(expected_signal, signals)

    def test_e1_real_manual_review_danger_denies_but_blanket_default_does_not(self):
        clean = egress.evaluate_external_egress_gate(
            [component("Explain a generic pump.")],
            explicit_user_shareability_opt_in=True,
        )
        danger = egress.evaluate_external_egress_gate(
            [component("remember this detail for later")],
            explicit_user_shareability_opt_in=True,
        )

        self.assertTrue(clean["allowed"])
        self.assert_denied(danger, "positive_danger_signal")
        self.assertIn("hard_reason_code:manual_review_required", danger["positive_danger_components"][0]["signals"])

    def test_e1_derivation_failures_fail_closed(self):
        def failing_builder(*args, **kwargs):
            raise RuntimeError("boom")

        cases = (
            ([component("")], "missing_component_text", {}),
            ([component("hello", component_type="attachment")], "unsupported_component_type", {}),
            ([component("hello")], "unable_to_derive_component_safety", {"input_builder": failing_builder}),
        )
        for components, expected_reason, kwargs in cases:
            with self.subTest(expected_reason=expected_reason):
                decision = egress.evaluate_external_egress_gate(
                    components,
                    explicit_user_shareability_opt_in=True,
                    **kwargs,
                )

                self.assert_denied(decision, expected_reason)

    def test_e1_component_not_evaluated_and_payload_divergence_fail_closed(self):
        invalid_provider = egress.evaluate_external_egress_gate(
            [component("hello")],
            explicit_user_shareability_opt_in=True,
            provider_payload_components=[{"id": "extra", "type": "current_message", "text": "hello"}, "bad"],
        )
        mismatch = egress.evaluate_external_egress_gate(
            [component("hello")],
            explicit_user_shareability_opt_in=True,
            provider_payload_components=[component("hello plus extra")],
        )

        self.assert_denied(invalid_provider, "invalid_provider_component_list")
        self.assert_denied(mismatch, "payload_component_mismatch")

    def test_e1_bluerev_public_non_fp_and_ip_floor_cases(self):
        allowed = egress.evaluate_external_egress_gate(
            [component("Spiega pubblicamente cos'e BlueRev senza dettagli proprietari.")],
            explicit_user_shareability_opt_in=True,
        )
        no_opt_in = egress.evaluate_external_egress_gate(
            [component("Spiega pubblicamente cos'e BlueRev senza dettagli proprietari.")],
            explicit_user_shareability_opt_in=False,
        )
        denied_cases = (
            "usa i parametri proprietari BlueRev per dimensionare una pompa",
            "valuta le correlazioni riservate BlueRev senza provider esterni",
            "questa e IP sensibile BlueRev",
            "questo e segreto industriale BlueRev",
        )

        self.assertTrue(allowed["allowed"])
        self.assert_denied(no_opt_in, "explicit_shareability_opt_in_required")
        for text in denied_cases:
            with self.subTest(text=text):
                decision = egress.evaluate_external_egress_gate(
                    [component(text)],
                    explicit_user_shareability_opt_in=True,
                )
                self.assert_denied(decision, "positive_danger_signal")
                self.assertIn("bluerev_ip_sensitivity_floor", decision["positive_danger_components"][0]["signals"])

    def test_e1_history_contamination_denies_when_any_included_component_is_dangerous(self):
        cases = (
            component("Generic current message.", component_id="history-private", component_type="history_turn")
            | {"text": "Keep this proprietary BlueRev calculation private."},
            component("my API key is sk-test-secret-12345678", component_id="history-secret", component_type="history_turn"),
            component("", component_id="history-failed", component_type="history_turn"),
            component("usa i parametri proprietari BlueRev", component_id="history-bluerev", component_type="history_turn"),
        )
        for history in cases:
            with self.subTest(history=history["id"]):
                decision = egress.evaluate_external_egress_gate(
                    [
                        component("Explain a generic pump.", component_id="current"),
                        history,
                    ],
                    explicit_user_shareability_opt_in=True,
                )

                self.assertFalse(decision["allowed"])

    def test_e1_current_clean_with_all_clean_history_allows(self):
        decision = egress.evaluate_external_egress_gate(
            [
                component("Explain a generic pump.", component_id="current"),
                component("A clean prior public note.", component_id="history-1", component_type="history_turn"),
            ],
            explicit_user_shareability_opt_in=True,
        )

        self.assertTrue(decision["allowed"])
        self.assertEqual(2, decision["checked_component_count"])
        self.assertEqual(["current", "history-1"], decision["checked_component_identities"])


if __name__ == "__main__":
    unittest.main()
