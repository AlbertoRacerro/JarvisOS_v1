import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_message_route_smoke as smoke  # noqa: E402
import router_policy_hint_bridge_probe as bridge  # noqa: E402


NOW = "2026-06-24T13:00:00+00:00"
B2_PHASE_B_REQUIRED_FIELDS = {
    "summary_short",
    "project_bucket",
    "primary_domain",
    "domain_tags",
    "storage_relevance",
    "usefulness_for_future_review",
    "possible_memory_card_type",
    "soft_reason_code",
    "brief_rationale",
    "suggested_followup_question",
    "soft_uncertain_fields",
}


class RouterPolicyMessageRouteSmokeTests(unittest.TestCase):
    def safe_input(self, message="Explain what a pump is"):
        return smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=True,
        )

    def conservative_input(self, message="Explain what a pump is"):
        return smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=False,
        )

    def secret_input(self, message="my API key is sk-test-secret-12345678"):
        return smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=True,
        )

    def clarification_input(self, message="Use the thing we decided last time."):
        return smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=True,
        )

    def external_input(self, message="Send this public scientific problem to Claude."):
        input_obj = smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=True,
        )
        input_obj["phase_a_signals"].update(
            {
                "contains_secret_or_credential": False,
                "contains_raw_private_or_ip_sensitive_context": False,
                "mentions_external_provider_or_upload_intent": False,
                "external_provider_allowed": True,
                "clarification_required": False,
                "hard_reason_codes": ["low_risk"],
                "sensitivity_bucket_proposal": "public",
                "requires_manual_review": False,
            }
        )
        input_obj["router_hint"].update(
            {
                "task_type": "analysis",
                "complexity": "high",
                "domain": "scientific",
                "needs_scientific_depth": True,
                "needs_reasoning": True,
            }
        )
        input_obj["user_policy"]["external_routing_enabled"] = True
        input_obj["provider_policy"] = {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
            "blocked_provider_tiers": ["FRONTIER"],
        }
        input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
        return input_obj

    def run_with_builder(self, message, built_input, responder=None, assume=False, use_phase_b_hints=False):
        builder = Mock(return_value=built_input)
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            input_builder=builder,
            assume_public_simple=assume,
            use_phase_b_hints=use_phase_b_hints,
        )
        builder.assert_called_once_with(message, now=NOW, assume_public_simple=assume)
        return result

    def assert_operational_blocked(
        self,
        message,
        *,
        expected_action_field=None,
        expected_router_field=None,
        use_phase_b_hints=False,
    ):
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            use_phase_b_hints=use_phase_b_hints,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        input_obj = result["input_obj"]
        self.assertNotEqual("answer", input_obj["router_hint"]["task_type"])
        self.assertNotEqual("low", input_obj["router_hint"]["complexity"])
        self.assertFalse(input_obj["context_metadata"]["assume_public_simple_safe_path"])
        self.assertNotEqual(["low_risk"], input_obj["phase_a_signals"]["hard_reason_codes"])
        self.assertTrue(input_obj["context_metadata"]["operational_intent_detected"])
        if expected_action_field is not None:
            self.assertTrue(input_obj["action_hint"][expected_action_field])
        if expected_router_field is not None:
            self.assertTrue(input_obj["router_hint"][expected_router_field])
        return result

    def phase_b_input(self, message, **phase_b_updates):
        input_obj = self.safe_input(message)
        phase_b = copy.deepcopy(input_obj["phase_b_soft_proposal"])
        phase_b.update(phase_b_updates)
        input_obj["phase_b_soft_proposal"] = phase_b
        return input_obj

    def source_candidate_input(self, message):
        return self.phase_b_input(
            message,
            summary_short="Candidate source review request.",
            primary_domain="source",
            domain_tags=["source", "reference"],
            storage_relevance="low",
            usefulness_for_future_review="medium",
            possible_memory_card_type="source_card",
            soft_reason_code="source_candidate",
            brief_rationale="The message asks about source-like context.",
        )

    def test_a5_001_simple_public_message_reaches_injected_responder_through_real_a3(self):
        message = "Explain what a pump is"
        responder = Mock(return_value="A pump moves fluid.")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("local_answer", result["reason"])
        self.assertEqual("A pump moves fluid.", result["response"])
        self.assertEqual("LOCAL_FAST", result["decision"]["route_tier"])
        self.assertEqual("answer_only", result["decision"]["allowed_execution_mode"])
        self.assertEqual(message, result["input_obj"]["message_text"])

    def test_a5_002_responder_missing_remains_offline_safe(self):
        result = smoke.run_message_route_smoke(
            "Explain what a pump is",
            responder=None,
            now=NOW,
            assume_public_simple=True,
        )
        self.assertFalse(result["executed"])
        self.assertEqual("local_responder_missing", result["reason"])

    def test_a5_003_fallback_arbitrary_message_without_assume_public_simple_does_not_execute_real_a3(self):
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            "Explain what a pump is",
            responder=responder,
            now=NOW,
            assume_public_simple=False,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("unknown", result["input_obj"]["phase_a_signals"]["sensitivity_bucket_proposal"])
        self.assertNotEqual("low", result["input_obj"]["router_hint"]["complexity"])
        self.assertNotEqual("answer", result["input_obj"]["router_hint"]["task_type"])

    def test_a5_004_run_local_alone_does_not_make_fallback_input_executable(self):
        fake_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder) as builder:
            with patch("builtins.print") as printed:
                exit_code = smoke.main(["--message", "Explain what a pump is", "--run-local", "--now", NOW])
        self.assertEqual(0, exit_code)
        builder.assert_called_once()
        fake_responder.assert_not_called()
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])

    def test_a5_005_fallback_safe_cli_execution_requires_assume_public_simple_and_run_local(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "Explain what a pump is",
                        "--assume-public-simple",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        fake_responder.assert_called_once_with("Explain what a pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertTrue(cli_result["assume_public_simple_used"])
        self.assertEqual("local answer", cli_result["response"])

    def test_a5_006_assume_public_simple_does_not_override_detected_hard_gate_safety_signal(self):
        message = "my API key is sk-test-secret-12345678"
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["assume_public_simple_used"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["contains_secret_or_credential"])
        self.assertEqual("secret", result["input_obj"]["phase_a_signals"]["sensitivity_bucket_proposal"])

    def test_a5_007_ambiguous_clarification_message_does_not_execute(self):
        message = "Use the thing we decided last time."
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["clarification_required"])

    def test_a5_008_secret_private_message_does_not_execute(self):
        message = "Keep this proprietary BlueRev calculation private."
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"])
        self.assertFalse(result["decision"]["external_allowed"])

    def test_a5_009_external_proposal_does_not_execute(self):
        message = "Analyze this public scientific task deeply."
        responder = Mock(return_value="should not run")
        result = self.run_with_builder(
            message,
            self.external_input(message),
            responder=responder,
            assume=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("external:scientific_medium", result["decision"]["proposed_external_target"])

    def test_a5_010_input_builder_failure_fails_closed(self):
        responder = Mock(return_value="should not run")

        def failing_builder(message_text, *, now=None, assume_public_simple=False):
            raise RuntimeError("boom")

        result = smoke.run_message_route_smoke(
            "hello",
            responder=responder,
            now=NOW,
            input_builder=failing_builder,
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("input_builder_failed", result["reason"])

    def test_a5_011_invalid_router_policy_input_fails_closed(self):
        responder = Mock(return_value="should not run")
        for built in (None, {"message_text": "hello"}):
            with self.subTest(built=built):
                result = smoke.run_message_route_smoke(
                    "hello",
                    responder=responder,
                    now=NOW,
                    input_builder=Mock(return_value=built),
                    assume_public_simple=True,
                )
                self.assertFalse(result["executed"])
                self.assertEqual("invalid_router_policy_input", result["reason"])
        responder.assert_not_called()

    def test_a5_012_malformed_local_route_result_fails_closed(self):
        for local_result in (None, {"reason": "x"}, {"executed": False}):
            with self.subTest(local_result=local_result):
                with patch.object(smoke, "_RUN_LOCAL_ROUTE", return_value=local_result):
                    result = smoke.run_message_route_smoke(
                        "hello",
                        responder=Mock(),
                        now=NOW,
                        input_builder=Mock(return_value=self.safe_input("hello")),
                        assume_public_simple=True,
                    )
                self.assertFalse(result["executed"])
                self.assertEqual("local_route_invalid_result", result["reason"])

    def test_a5_013_message_validation_rejects_invalid_messages(self):
        builder = Mock(return_value=self.safe_input("hello"))
        responder = Mock(return_value="should not run")
        invalid_messages = [123, "", "   ", "x" * (smoke.MAX_MESSAGE_CHARS + 1)]
        for message in invalid_messages:
            with self.subTest(message_type=type(message).__name__):
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    input_builder=builder,
                    assume_public_simple=True,
                )
                self.assertFalse(result["executed"])
                self.assertEqual("invalid_message", result["reason"])
        builder.assert_not_called()
        responder.assert_not_called()

    def test_a5_014_cli_default_does_not_run_real_model(self):
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER") as builder:
            with patch("builtins.print"):
                exit_code = smoke.main(["--message", "Explain what a pump is", "--now", NOW])
        self.assertEqual(0, exit_code)
        builder.assert_not_called()

    def test_a5_015_cli_run_local_does_not_bypass_router_policy(self):
        fake_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch.object(smoke, "_build_router_input_for_cli", return_value=self.external_input()):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        ["--message", "public scientific task", "--run-local", "--assume-public-simple", "--now", NOW]
                    )
        self.assertEqual(0, exit_code)
        fake_responder.assert_not_called()
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])

    def test_a5_016_no_policy_or_audit_internals_sent_to_responder(self):
        message = "Explain what a pump is"
        responder = Mock(return_value="local answer")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        self.assertTrue(result["executed"])
        prompt = responder.call_args.args[0]
        self.assertEqual(message, prompt)
        self.assertNotIn("decision_id", prompt)
        self.assertNotIn("audit_notes", prompt)
        self.assertNotIn("reports/router_policy", prompt)
        self.assertNotIn("{", prompt)

    def test_a5_017_structural_validator_rejects_missing_required_fields_before_responder_call(self):
        broken = copy.deepcopy(self.safe_input("hello"))
        broken.pop("router_hint")
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            "hello",
            responder=responder,
            now=NOW,
            input_builder=Mock(return_value=broken),
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertEqual("invalid_router_policy_input", result["reason"])

    def test_a5_018_structural_validator_rejects_string_booleans_and_invalid_enum_values(self):
        broken = copy.deepcopy(self.safe_input("hello"))
        broken["action_hint"]["needs_provider_call"] = "false"
        broken["router_hint"]["complexity"] = "tiny"
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            "hello",
            responder=responder,
            now=NOW,
            input_builder=Mock(return_value=broken),
            assume_public_simple=True,
        )
        responder.assert_not_called()
        self.assertEqual("invalid_router_policy_input", result["reason"])

    def test_a5_019_cli_output_redaction_on_no_execution(self):
        sensitive = "my API key is sk-test-secret-12345678"
        with patch("builtins.print") as printed:
            exit_code = smoke.main(["--message", sensitive, "--now", NOW])
        self.assertEqual(0, exit_code)
        output = printed.call_args.args[0]
        self.assertNotIn(sensitive, output)
        self.assertNotIn("sk-test-secret-12345678", output)
        self.assertNotIn("input_obj", output)
        self.assertNotIn("audit_notes", output)
        self.assertNotIn("response", json.loads(output))

    def test_a5_020_response_printed_only_when_executed_true_and_bounded(self):
        fake_responder = Mock(return_value="x" * (smoke.MAX_CLI_RESPONSE_CHARS + 50))
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "Explain what a pump is",
                        "--assume-public-simple",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertEqual(smoke.MAX_CLI_RESPONSE_CHARS, len(cli_result["response"]))
        self.assertNotIn("input_obj", cli_result)

    def test_unsupported_overlay_reason_is_mapped_to_conservative_router_policy_reason(self):
        responder = Mock(return_value="should not run")
        overlay = {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "memory_boundary_or_write_authority_claim": False,
            "retrieval_or_source_use_request": False,
            "unresolved_assumption_or_open_decision": False,
            "clarification_required": False,
            "redaction_required": False,
            "external_provider_allowed": False,
            "source_policy_for_future_retrieval": "not_applicable",
            "allowed_future_retrieval_behavior": "none",
            "lifecycle_status_proposal": "raw_input",
            "sensitivity_bucket_proposal": "internal",
            "requires_manual_review": True,
            "hard_reason_code": "overlay_only_code",
            "hard_uncertain_fields": [],
        }
        with patch.object(smoke, "_APPLY_POLICY_OVERLAY", return_value=overlay):
            result = smoke.run_message_route_smoke(
                "Explain what a pump is",
                responder=responder,
                now=NOW,
                assume_public_simple=True,
            )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertNotIn("overlay_only_code", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])
        self.assertIn("manual_review_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r1_001_mcp_tool_intent_does_not_execute_with_assume_public_simple(self):
        for message in ("use MCP to call a tool", "call a tool for this", "invoke tool now"):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message)
                self.assertTrue(result["input_obj"]["phase_a_signals"]["clarification_required"])
                self.assertIn("clarification_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r1_002_terminal_intent_does_not_execute_with_assume_public_simple(self):
        for message in ("run command dir", "execute command in PowerShell", "use subprocess to run this"):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_terminal")
                self.assertTrue(result["input_obj"]["router_hint"]["needs_code_execution"])

    def test_a5_r1_003_memory_intent_does_not_execute_with_assume_public_simple(self):
        for message in ("remember this", "write to memory", "store this in memory"):
            with self.subTest(message=message):
                self.assert_operational_blocked(message, expected_action_field="needs_memory_write")

    def test_a5_r1_004_retrieval_file_intent_does_not_execute_with_assume_public_simple(self):
        for message in (r"read local file C:\secret.txt", "open file .env", "retrieve file credentials.json"):
            with self.subTest(message=message):
                self.assert_operational_blocked(message, expected_router_field="needs_file_context")

    def test_a5_r1_005_browser_search_intent_does_not_execute_with_assume_public_simple(self):
        for message in (
            "browse the web for this",
            "search web for current prices",
            "open browser and look this up",
            "look it up online",
        ):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message)
                self.assertTrue(result["input_obj"]["router_hint"]["needs_current_info"])

    def test_a5_r1_006_provider_upload_intent_does_not_execute_with_assume_public_simple(self):
        for message in ("please upload this to OpenAI", "send this to Claude", "use OpenRouter for this", "call Qwen API"):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_provider_call")
                self.assertIn("provider_or_upload_intent", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r1_007_benign_answer_still_executes_with_assume_public_simple(self):
        message = "Explain what a centrifugal pump is"
        responder = Mock(return_value="A centrifugal pump uses a rotating impeller.")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_called_once_with(result["input_obj"]["message_text"])
        self.assertEqual(message, result["input_obj"]["message_text"])
        self.assertTrue(result["executed"])
        self.assertEqual("A centrifugal pump uses a rotating impeller.", result["response"])

    def test_a5_r1_008_default_without_assume_public_simple_remains_no_execution(self):
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            "Explain what a centrifugal pump is",
            responder=responder,
            now=NOW,
            assume_public_simple=False,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])

    def test_a5_r1_009_cli_assume_public_simple_run_local_does_not_execute_operational_intent(self):
        fake_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "use MCP to call a tool",
                        "--assume-public-simple",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        fake_responder.assert_not_called()
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])
        self.assertNotIn("response", cli_result)
        self.assertNotIn("input_obj", cli_result)

    def test_a5_r1_010_cli_redaction_for_file_secret_like_no_execution_message(self):
        message = r"read local file C:\secret.txt"
        fake_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        message,
                        "--assume-public-simple",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        fake_responder.assert_not_called()
        output = printed.call_args.args[0]
        cli_result = json.loads(output)
        self.assertFalse(cli_result["executed"])
        self.assertNotIn(message, output)
        self.assertNotIn(r"C:\secret.txt", output)
        self.assertNotIn("input_obj", output)
        self.assertNotIn("response", cli_result)

    def test_b2_000_a5_base_phase_b_stub_is_b1_compatible(self):
        built = smoke.build_router_policy_input_from_message_for_smoke(
            "Explain what a pump is",
            now=NOW,
            assume_public_simple=True,
        )
        self.assertTrue(B2_PHASE_B_REQUIRED_FIELDS.issubset(built["phase_b_soft_proposal"]))
        enriched = bridge.apply_phase_b_router_hint(built, now=NOW)
        self.assertEqual("answer", enriched["router_hint"]["task_type"])
        self.assertEqual("answer", enriched["action_hint"]["requested_action_type"])
        self.assertIn(enriched["router_hint"]["confidence"], {"medium", "high"})
        self.assertEqual("high", enriched["context_metadata"]["phase_b_quality_derived"])

    def test_b2_001_default_behavior_unchanged_without_flag(self):
        message = "Explain what a pump is"
        responder = Mock(return_value="A pump moves fluid.")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            use_phase_b_hints=False,
        )
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertFalse(result["use_phase_b_hints_used"])
        self.assertNotIn("phase_b_router_hint_applied", result["input_obj"]["context_metadata"])

    def test_b2_002_use_phase_b_hints_alone_does_not_execute(self):
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            "Explain what a pump is",
            responder=responder,
            now=NOW,
            assume_public_simple=False,
            use_phase_b_hints=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["use_phase_b_hints_used"])
        self.assertEqual("phase_b_blocked_by_hard_gate", result["input_obj"]["context_metadata"]["router_hint_source"])

    def test_b2_003_real_a5_stub_b1_hints_executes_benign_answer(self):
        message = "Explain what a pump is"
        responder = Mock(return_value="A pump moves fluid.")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            use_phase_b_hints=True,
        )
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("local_answer", result["reason"])
        input_obj = result["input_obj"]
        self.assertTrue(B2_PHASE_B_REQUIRED_FIELDS.issubset(input_obj["phase_b_soft_proposal"]))
        self.assertEqual([], smoke._router_policy_input_structural_errors(input_obj, message))
        self.assertEqual("answer", input_obj["router_hint"]["task_type"])
        self.assertEqual("low", input_obj["router_hint"]["complexity"])
        self.assertEqual("answer", input_obj["action_hint"]["requested_action_type"])
        self.assertEqual("none", input_obj["action_hint"]["side_effect_level"])

    def test_b2_004_b1_enriches_technical_scientific_router_hint_under_safe_path(self):
        message = "Explain the mass transfer model for a photobioreactor."
        built = self.phase_b_input(
            message,
            summary_short="Photobioreactor mass transfer question.",
            primary_domain="bioprocess",
            domain_tags=["engineering", "reactor", "modeling"],
            soft_reason_code="contextual_summary",
            brief_rationale="Scientific engineering context affects routing depth.",
        )
        responder = Mock(return_value="A local scientific answer.")
        result = self.run_with_builder(
            message,
            built,
            responder=responder,
            assume=True,
            use_phase_b_hints=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("not_safe_local_route", result["reason"])
        router = result["input_obj"]["router_hint"]
        self.assertEqual("answer", router["task_type"])
        self.assertEqual("medium", router["complexity"])
        self.assertTrue(router["needs_reasoning"])
        self.assertTrue(router["needs_scientific_depth"])

    def test_b2_005_b1_source_candidate_makes_route_more_conservative(self):
        message = "Explain what a pump is"
        responder = Mock(return_value="should not run")
        result = self.run_with_builder(
            message,
            self.source_candidate_input(message),
            responder=responder,
            assume=True,
            use_phase_b_hints=True,
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        router = result["input_obj"]["router_hint"]
        self.assertEqual("review", router["task_type"])
        self.assertTrue(router["needs_current_info"])
        self.assertTrue(router["needs_file_context"])
        self.assertEqual("source_candidate_review", result["input_obj"]["context_metadata"]["phase_b_router_hint_reason"])

    def test_b2_006_hard_gate_dominance_with_phase_b_hints(self):
        blocked_messages = (
            "my API key is sk-test-secret-12345678",
            "Keep this proprietary BlueRev calculation private.",
            "Use the thing we decided last time.",
        )
        for message in blocked_messages:
            with self.subTest(message=message):
                responder = Mock(return_value="should not run")
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    use_phase_b_hints=True,
                )
                responder.assert_not_called()
                self.assertFalse(result["executed"])
                input_obj = result["input_obj"]
                self.assertEqual("phase_b_blocked_by_hard_gate", input_obj["context_metadata"]["router_hint_source"])
                self.assertNotEqual("answer", input_obj["router_hint"]["task_type"])
                self.assertNotEqual("low", input_obj["router_hint"]["complexity"])

    def test_b2_007_operational_gate_dominance_with_phase_b_hints(self):
        cases = (
            ("use MCP to call a tool", None, None),
            ("run command dir", "needs_terminal", None),
            ("write to memory", "needs_memory_write", None),
            (r"read local file C:\secret.txt", None, "needs_file_context"),
            ("browse the web for this", None, "needs_current_info"),
            ("please upload this to OpenAI", "needs_provider_call", None),
        )
        for message, action_field, router_field in cases:
            with self.subTest(message=message):
                result = self.assert_operational_blocked(
                    message,
                    expected_action_field=action_field,
                    expected_router_field=router_field,
                    use_phase_b_hints=True,
                )
                self.assertEqual("phase_b_blocked_by_hard_gate", result["input_obj"]["context_metadata"]["router_hint_source"])

    def test_b2_008_baseline_no_execution_cannot_become_execution(self):
        default_message = "Explain what a pump is"
        source_message = "Review this source for later retrieval."
        no_hint_cases = (
            (
                default_message,
                dict(assume_public_simple=False, input_builder=None),
                dict(assume_public_simple=False, input_builder=None),
            ),
            (
                r"read local file C:\secret.txt",
                dict(assume_public_simple=True, input_builder=None),
                dict(assume_public_simple=True, input_builder=None),
            ),
            (
                source_message,
                dict(assume_public_simple=True, input_builder=Mock(return_value=self.source_candidate_input(source_message))),
                dict(assume_public_simple=True, input_builder=Mock(return_value=self.source_candidate_input(source_message))),
            ),
        )
        for message, base_kwargs, hinted_kwargs in no_hint_cases:
            with self.subTest(message=message):
                baseline_responder = Mock(return_value="should not run")
                hinted_responder = Mock(return_value="should not run")
                baseline = smoke.run_message_route_smoke(
                    message,
                    responder=baseline_responder,
                    now=NOW,
                    use_phase_b_hints=False,
                    **base_kwargs,
                )
                hinted = smoke.run_message_route_smoke(
                    message,
                    responder=hinted_responder,
                    now=NOW,
                    use_phase_b_hints=True,
                    **hinted_kwargs,
                )
                self.assertFalse(baseline["executed"])
                self.assertFalse(hinted["executed"])
                baseline_responder.assert_not_called()
                hinted_responder.assert_not_called()

    def test_b2_009_context_metadata_compatibility(self):
        message = "Explain what a pump is"
        result = smoke.run_message_route_smoke(
            message,
            responder=Mock(return_value="local answer"),
            now=NOW,
            assume_public_simple=True,
            use_phase_b_hints=True,
        )
        input_obj = result["input_obj"]
        metadata = input_obj["context_metadata"]
        self.assertEqual([], smoke._router_policy_input_structural_errors(input_obj, message))
        self.assertTrue(metadata["attached_files_present"] is False)
        self.assertTrue(metadata["conversation_context_available"] is False)
        self.assertTrue(metadata["phase_b_router_hint_applied"])
        self.assertEqual("phase_b_soft_review", metadata["router_hint_source"])
        self.assertEqual("high", metadata["phase_b_quality_derived"])

    def test_b2_010_cli_flag_exposed_and_safe_output_redacted(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "Explain what a pump is",
                        "--assume-public-simple",
                        "--use-phase-b-hints",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        fake_responder.assert_called_once_with("Explain what a pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])
        self.assertEqual("local answer", cli_result["response"])
        self.assertNotIn("input_obj", cli_result)
        self.assertNotIn("audit_notes", cli_result)

        blocked_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=blocked_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "use MCP to call a tool",
                        "--assume-public-simple",
                        "--use-phase-b-hints",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        blocked_responder.assert_not_called()
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])
        self.assertNotIn("response", cli_result)
        self.assertNotIn("input_obj", cli_result)

    def test_b2_011_b1_bridge_failure_fails_closed(self):
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", side_effect=RuntimeError("boom")):
            result = smoke.run_message_route_smoke(
                "Explain what a pump is",
                responder=responder,
                now=NOW,
                assume_public_simple=True,
                use_phase_b_hints=True,
            )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("phase_b_hint_bridge_failed", result["reason"])
        self.assertEqual("RuntimeError", result["error_type"])

        sensitive = "my API key is sk-test-secret-12345678"
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", side_effect=RuntimeError("boom")):
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            sensitive,
                            "--assume-public-simple",
                            "--use-phase-b-hints",
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        self.assertEqual(0, exit_code)
        output = printed.call_args.args[0]
        cli_result = json.loads(output)
        self.assertFalse(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])
        self.assertNotIn(sensitive, output)
        self.assertNotIn("sk-test-secret-12345678", output)
        self.assertNotIn("input_obj", output)
        self.assertNotIn("response", cli_result)


if __name__ == "__main__":
    unittest.main()
