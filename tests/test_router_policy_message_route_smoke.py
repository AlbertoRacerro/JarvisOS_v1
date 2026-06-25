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

    def run_with_builder(
        self,
        message,
        built_input,
        responder=None,
        assume=False,
        use_phase_b_hints=False,
        phase_b_source_kind="stub",
        phase_b_source_case_id=None,
        run_local_phase_b=False,
        phase_b_endpoint="http://localhost:11434",
    ):
        builder = Mock(return_value=built_input)
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            input_builder=builder,
            assume_public_simple=assume,
            use_phase_b_hints=use_phase_b_hints,
            phase_b_source_kind=phase_b_source_kind,
            phase_b_source_case_id=phase_b_source_case_id,
            run_local_phase_b=run_local_phase_b,
            phase_b_endpoint=phase_b_endpoint,
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

    def assert_no_new_italian_write_block(self, message):
        input_obj = smoke.build_router_policy_input_from_message_for_smoke(
            message,
            now=NOW,
            assume_public_simple=True,
        )
        self.assertFalse(input_obj["phase_a_signals"]["contains_secret_or_credential"])
        self.assertFalse(input_obj["action_hint"]["needs_memory_write"])
        self.assertFalse(input_obj["action_hint"]["needs_file_write"])
        categories = set(input_obj["context_metadata"].get("operational_intent_categories") or [])
        self.assertFalse({"memory_write", "document_project_write", "credential_like_save"} & categories)
        return input_obj

    def phase_b_input(self, message, **phase_b_updates):
        input_obj = self.safe_input(message)
        phase_b = copy.deepcopy(input_obj["phase_b_soft_proposal"])
        phase_b.update(phase_b_updates)
        input_obj["phase_b_soft_proposal"] = phase_b
        return input_obj

    def valid_live_phase_b(self, case_id="B4-LIVE-BENIGN", **updates):
        del case_id
        phase_b = {
            "summary_short": "Synthetic live Phase B local-answer proposal.",
            "project_bucket": "general",
            "primary_domain": "general",
            "domain_tags": ["smoke", "local_answer"],
            "storage_relevance": "low",
            "usefulness_for_future_review": "low",
            "possible_memory_card_type": "none",
            "soft_reason_code": "contextual_summary",
            "brief_rationale": "Synthetic advisory Phase B proposal for a local-only smoke case.",
            "suggested_followup_question": "",
            "soft_uncertain_fields": [],
        }
        phase_b.update(updates)
        return phase_b

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

    def malformed_failure_point(self, result):
        if result.get("reason") == "phase_b_hint_bridge_failed":
            return "phase_b_hint_bridge_failed"
        if (
            result.get("reason") == "invalid_router_policy_input"
            and result.get("validation_stage") == "pre_phase_b_hint_bridge"
        ):
            return "pre_bridge_structural_validation_failed"
        if result.get("reason") == "invalid_router_policy_input":
            return "post_bridge_structural_validation_failed"
        return "unexpected"

    def assert_malformed_default_rejected_without_mutation(self, message, built):
        malformed_before = copy.deepcopy(built)
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                input_builder=Mock(return_value=built),
                assume_public_simple=True,
            )
        responder.assert_not_called()
        run_local_route.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertIn(result["reason"], {"invalid_router_policy_input", "phase_b_hint_bridge_failed"})
        self.assertEqual(malformed_before, built)
        self.assertIn(
            self.malformed_failure_point(result),
            {
                "phase_b_hint_bridge_failed",
                "pre_bridge_structural_validation_failed",
                "post_bridge_structural_validation_failed",
            },
        )
        return result

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
                    use_phase_b_hints=False,
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
            use_phase_b_hints=False,
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
            use_phase_b_hints=False,
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

    def test_a5_r2_001_italian_memory_write_intent_blocks_end_to_end(self):
        for message in (
            "salva in memoria questa assunzione",
            "salvalo in memoria",
            "salvami in memoria questo valore",
            "memorizza questa informazione",
            "memorizzalo",
            "ricorda che la prevalenza e 8 m",
            "ricordati che la portata e 1 L/min",
            "tienilo a mente",
            "tieni a mente questo parametro",
            "prendi nota di questo valore",
            "annota questo valore",
            "non dimenticare che la prevalenza e 8 m",
            "la prevalenza da salvbare in memoria e di 8 m",
        ):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_memory_write")
                self.assertEqual("memory_store", result["input_obj"]["action_hint"]["environment_type"])
                self.assertEqual("memory_write", result["input_obj"]["action_hint"]["requested_action_type"])
                self.assertIn("manual_review_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r2_002_italian_document_project_write_blocks_end_to_end(self):
        for message in (
            "metti nel brevetto che la prevalenza e 8 m",
            "aggiungi al brevetto questa assunzione",
            "scrivi nel documento questo dato",
            "aggiorna il documento con questo valore",
            "aggiorna il file con questo valore",
            "salva nel progetto questa ipotesi",
            "metti agli atti questo parametro",
            "verbalizza questa decisione",
            "inserisci questa assunzione nella relazione di progetto",
        ):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_file_write")
                self.assertEqual("codebase", result["input_obj"]["action_hint"]["environment_type"])
                self.assertEqual("file_write", result["input_obj"]["action_hint"]["requested_action_type"])
                self.assertTrue(result["input_obj"]["action_hint"]["modifies_state"])
                self.assertIn("manual_review_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r2_003_italian_credential_like_save_blocks_end_to_end(self):
        for message in (
            "salva il codice it4hug",
            "salva questo codice di accesso",
            "memorizza il PIN 1234",
            "ricorda il token abc123",
            "conserva questa credenziale",
            "salva la password w4587wtuif",
        ):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_memory_write")
                self.assertTrue(result["input_obj"]["phase_a_signals"]["contains_secret_or_credential"])
                self.assertEqual("secret", result["input_obj"]["phase_a_signals"]["sensitivity_bucket_proposal"])
                self.assertEqual("memory_store", result["input_obj"]["action_hint"]["environment_type"])
                self.assertIn("secret_or_credential", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])
                self.assertIn("redaction_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

    def test_a5_r2_004_italian_false_positives_do_not_trigger_new_write_blocks(self):
        for message in (
            "cos'e la memoria di un computer?",
            "memoria di calcolo",
            "il modello ha memoria?",
            "ti ricordi cos'e una pompa?",
            "questo mi ricorda una pompa",
            "che cos'e un brevetto?",
            "come si scrive un documento?",
            "scrivimi una spiegazione",
            "scrivimi una poesia",
            "scrivi codice Python per calcolare P = rho*g*Q*H",
            "codice colore",
            "codice Python per calcolare una pompa",
            "parametri del reattore",
            "chiamami Signore",
            "dammi del Lei",
            "usa tono tecnico",
        ):
            with self.subTest(message=message):
                self.assert_no_new_italian_write_block(message)

    def test_a5_r2_005_persistent_preference_memory_write_is_blocked(self):
        for message in (
            "ricordati di chiamarmi Signore",
            "memorizza che mi devi dare del Lei",
            "salva questa preferenza",
        ):
            with self.subTest(message=message):
                result = self.assert_operational_blocked(message, expected_action_field="needs_memory_write")
                self.assertEqual("memory_store", result["input_obj"]["action_hint"]["environment_type"])
                self.assertIn("manual_review_required", result["input_obj"]["phase_a_signals"]["hard_reason_codes"])

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

    def test_b3_001_phase_b_hints_default_on_in_library(self):
        message = "Explain what a centrifugal pump is"
        responder = Mock(return_value="A centrifugal pump uses an impeller.")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                assume_public_simple=True,
            )
        hinted.assert_called_once()
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertTrue(result["use_phase_b_hints_used"])
        self.assertTrue(result["input_obj"]["context_metadata"]["phase_b_router_hint_applied"])

    def test_b3_002_explicit_false_disables_bridge_in_library(self):
        message = "Explain what a centrifugal pump is"
        responder = Mock(return_value="A centrifugal pump uses an impeller.")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                assume_public_simple=True,
                use_phase_b_hints=False,
            )
        hinted.assert_not_called()
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertFalse(result["use_phase_b_hints_used"])
        self.assertNotIn("phase_b_router_hint_applied", result["input_obj"]["context_metadata"])

    def test_b3_003_cli_default_applies_phase_b_hints(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            "Explain what a centrifugal pump is",
                            "--assume-public-simple",
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        self.assertEqual(0, exit_code)
        hinted.assert_called_once()
        fake_responder.assert_called_once_with("Explain what a centrifugal pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])
        self.assertEqual("local answer", cli_result["response"])
        self.assertNotIn("input_obj", cli_result)
        self.assertNotIn("audit_notes", cli_result)

    def test_b3_004_cli_no_phase_b_hints_disables_bridge(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            "Explain what a centrifugal pump is",
                            "--assume-public-simple",
                            "--no-phase-b-hints",
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        self.assertEqual(0, exit_code)
        hinted.assert_not_called()
        fake_responder.assert_called_once_with("Explain what a centrifugal pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertFalse(cli_result["use_phase_b_hints_used"])
        self.assertNotIn("input_obj", cli_result)

    def test_b3_005_benign_execution_still_requires_assume_public_simple(self):
        message = "Explain what a centrifugal pump is"
        blocked_responder = Mock(return_value="should not run")
        blocked = smoke.run_message_route_smoke(
            message,
            responder=blocked_responder,
            now=NOW,
        )
        blocked_responder.assert_not_called()
        self.assertFalse(blocked["executed"])
        self.assertTrue(blocked["use_phase_b_hints_used"])

        responder = Mock(return_value="local answer")
        allowed = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
        )
        responder.assert_called_once_with(allowed["input_obj"]["message_text"])
        self.assertTrue(allowed["executed"])
        self.assertEqual(message, allowed["input_obj"]["message_text"])

    def test_b3_006_run_local_alone_still_does_not_execute(self):
        fake_responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
            with patch("builtins.print") as printed:
                exit_code = smoke.main(
                    [
                        "--message",
                        "Explain what a centrifugal pump is",
                        "--run-local",
                        "--now",
                        NOW,
                    ]
                )
        self.assertEqual(0, exit_code)
        fake_responder.assert_not_called()
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])

    def test_b3_007_hard_gate_and_operational_dominance_preserved_with_default_hints(self):
        blocked_messages = (
            "my API key is sk-test-1234567890",
            "Keep this proprietary BlueRev calculation private.",
            "Use the thing we decided last time.",
            "use MCP to call a tool",
            r"read local file C:\secret.txt",
            "write this to memory",
            "browse the web for this",
            "please upload this to OpenAI",
        )
        for message in blocked_messages:
            with self.subTest(message=message):
                responder = Mock(return_value="should not run")
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                )
                responder.assert_not_called()
                self.assertFalse(result["executed"])
                self.assertTrue(result["use_phase_b_hints_used"])

    def test_b3_008_source_current_info_remains_conservative(self):
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

    def test_b3_009_scientific_depth_remains_subject_to_a3_safe_local_guard(self):
        message = "Explain the mass transfer model for a photobioreactor."
        built = self.phase_b_input(
            message,
            summary_short="Photobioreactor mass transfer question.",
            primary_domain="bioprocess",
            domain_tags=["engineering", "reactor", "modeling"],
            soft_reason_code="contextual_summary",
            brief_rationale="Scientific engineering context affects routing depth.",
        )
        responder = Mock(return_value="should not run")
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
        self.assertTrue(result["input_obj"]["router_hint"]["needs_scientific_depth"])

    def test_b3_010_b1_bridge_failure_still_fails_closed_by_default(self):
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", side_effect=RuntimeError("boom")):
            result = smoke.run_message_route_smoke(
                "Explain what a centrifugal pump is",
                responder=responder,
                now=NOW,
                assume_public_simple=True,
            )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("phase_b_hint_bridge_failed", result["reason"])

        sensitive = "my API key is sk-test-secret-12345678"
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", side_effect=RuntimeError("boom")):
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            sensitive,
                            "--assume-public-simple",
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

    def test_b3_011_use_phase_b_hints_alias_does_not_double_apply_b1(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            "Explain what a centrifugal pump is",
                            "--assume-public-simple",
                            "--use-phase-b-hints",
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        self.assertEqual(0, exit_code)
        hinted.assert_called_once()
        fake_responder.assert_called_once_with("Explain what a centrifugal pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertTrue(cli_result["use_phase_b_hints_used"])

    def test_b3_012_no_phase_b_hints_opt_out_applies_zero_times(self):
        fake_responder = Mock(return_value="local answer")
        with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as hinted:
            with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", return_value=fake_responder):
                with patch("builtins.print") as printed:
                    exit_code = smoke.main(
                        [
                            "--message",
                            "Explain what a centrifugal pump is",
                            "--assume-public-simple",
                            "--no-phase-b-hints",
                            "--run-local",
                            "--now",
                            NOW,
                        ]
                    )
        self.assertEqual(0, exit_code)
        hinted.assert_not_called()
        fake_responder.assert_called_once_with("Explain what a centrifugal pump is")
        cli_result = json.loads(printed.call_args.args[0])
        self.assertTrue(cli_result["executed"])
        self.assertFalse(cli_result["use_phase_b_hints_used"])

    def test_b3_013_conflicting_phase_b_flags_are_rejected(self):
        responder_builder = Mock(return_value=Mock(return_value="should not run"))
        with patch.object(smoke, "_BUILD_LOCAL_RESPONDER", responder_builder):
            with patch("sys.stderr"):
                with self.assertRaises(SystemExit) as raised:
                    smoke.main(
                        [
                            "--message",
                            "Explain what a centrifugal pump is",
                            "--use-phase-b-hints",
                            "--no-phase-b-hints",
                        ]
                    )
        self.assertEqual(2, raised.exception.code)
        responder_builder.assert_not_called()

    def test_b3_r1_001_malformed_action_router_input_is_not_repaired_in_place(self):
        built = self.safe_input("hello")
        built["action_hint"]["needs_provider_call"] = "false"
        built["router_hint"]["complexity"] = "tiny"
        result = self.assert_malformed_default_rejected_without_mutation("hello", built)
        self.assertEqual("false", built["action_hint"]["needs_provider_call"])
        self.assertEqual("tiny", built["router_hint"]["complexity"])
        self.assertEqual("pre_bridge_structural_validation_failed", self.malformed_failure_point(result))

    def test_b3_r1_002_malformed_phase_a_hard_gate_input_is_not_repaired_in_place(self):
        built = self.safe_input("hello")
        built["phase_a_signals"]["contains_secret_or_credential"] = "false"
        result = self.assert_malformed_default_rejected_without_mutation("hello", built)
        self.assertEqual("false", built["phase_a_signals"]["contains_secret_or_credential"])
        self.assertEqual("pre_bridge_structural_validation_failed", self.malformed_failure_point(result))

    def test_b3_r1_003_malformed_provider_policy_input_is_not_repaired_in_place(self):
        built = self.safe_input("hello")
        built["provider_policy"]["allowed_provider_tiers"] = "LOCAL_FAST"
        result = self.assert_malformed_default_rejected_without_mutation("hello", built)
        self.assertEqual("LOCAL_FAST", built["provider_policy"]["allowed_provider_tiers"])
        self.assertEqual("pre_bridge_structural_validation_failed", self.malformed_failure_point(result))

    def test_b3_r1_004_malformed_phase_b_input_is_not_repaired_in_place(self):
        built = self.safe_input("hello")
        built["phase_b_soft_proposal"]["domain_tags"] = "smoke"
        result = self.assert_malformed_default_rejected_without_mutation("hello", built)
        self.assertEqual("smoke", built["phase_b_soft_proposal"]["domain_tags"])
        self.assertEqual("pre_bridge_structural_validation_failed", self.malformed_failure_point(result))

    def test_b4_001_fast_secretary_phase_b_shape_is_b1_compatible(self):
        message = "Explain what a centrifugal pump is."
        built = self.safe_input(message)
        phase_b = smoke._BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW(
            case_id="B4-BENIGN",
            input_text=message,
            phase_a=built["phase_a_signals"],
        )
        self.assertEqual([], smoke._phase_b_b1_compatibility_errors(phase_b))
        self.assertTrue(B2_PHASE_B_REQUIRED_FIELDS.issubset(phase_b))
        self.assertNotIn("confidence", phase_b)

    def test_b4_002_coherent_triple_provenance(self):
        message = "Explain what a centrifugal pump is."
        result = smoke.run_message_route_smoke(
            message,
            responder=Mock(return_value="local answer"),
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-BENIGN",
        )
        metadata = result["input_obj"]["context_metadata"]
        phase_b = result["input_obj"]["phase_b_soft_proposal"]
        self.assertEqual("B4-BENIGN", metadata["phase_b_source_case_id"])
        self.assertEqual("B4-BENIGN", phase_b["phase_a_case_id"])
        self.assertEqual("deterministic_overlay_builder", metadata["phase_a_source"])
        self.assertEqual("deterministic_fast_secretary_soft_review", metadata["phase_b_source_kind"])
        self.assertTrue(metadata["same_case_id_for_phase_a_and_phase_b"])
        self.assertFalse(metadata["cross_case_mix"])

    def test_b4_003_deterministic_phase_b_replaces_stub_only_in_explicit_path(self):
        message = "Explain what a centrifugal pump is."
        default_result = smoke.run_message_route_smoke(
            message,
            responder=Mock(return_value="local answer"),
            now=NOW,
            assume_public_simple=True,
        )
        default_phase_b = default_result["input_obj"]["phase_b_soft_proposal"]
        self.assertEqual("Benign local-answer smoke message.", default_phase_b["summary_short"])
        self.assertNotIn("phase_b_source_kind", default_result["input_obj"]["context_metadata"])

        b4_result = smoke.run_message_route_smoke(
            message,
            responder=Mock(return_value="local answer"),
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-BENIGN",
        )
        b4_phase_b = b4_result["input_obj"]["phase_b_soft_proposal"]
        self.assertNotEqual("Benign local-answer smoke message.", b4_phase_b["summary_short"])
        self.assertEqual("B4-BENIGN", b4_phase_b["phase_a_case_id"])
        self.assertEqual(
            "local_phase_b_soft_review_probe.build_soft_review",
            b4_result["input_obj"]["context_metadata"]["phase_b_source_function"],
        )

    def test_b4_004_benign_deterministic_phase_b_can_enrich_without_bypassing_a3(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="local answer")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-BENIGN",
        )
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertTrue(result["phase_b_source_used"])
        self.assertEqual("answer", result["input_obj"]["router_hint"]["task_type"])
        self.assertEqual("answer", result["input_obj"]["action_hint"]["requested_action_type"])

    def test_b4_005_source_current_info_deterministic_phase_b_remains_conservative(self):
        message = "Find public DOI source for algae modeling."
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-SOURCE",
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        phase_b = result["input_obj"]["phase_b_soft_proposal"]
        router = result["input_obj"]["router_hint"]
        self.assertEqual("source_candidate", phase_b["soft_reason_code"])
        self.assertEqual("review", router["task_type"])
        self.assertTrue(router["needs_current_info"])
        self.assertTrue(router["needs_file_context"])

    def test_b4_006_ambiguity_followup_deterministic_phase_b_remains_non_executable(self):
        message = "Use the thing we decided last time."
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-AMBIGUITY",
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        phase_b = result["input_obj"]["phase_b_soft_proposal"]
        self.assertEqual("blocked_by_phase_a", phase_b["soft_reason_code"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["clarification_required"])
        self.assertNotEqual("answer", result["input_obj"]["router_hint"]["task_type"])

    def test_b4_007_hard_gate_dominates_deterministic_phase_b(self):
        message = "my API key is sk-test-1234567890"
        responder = Mock(return_value="should not run")
        result = smoke.run_message_route_smoke(
            message,
            responder=responder,
            now=NOW,
            assume_public_simple=True,
            phase_b_source_kind="deterministic",
            phase_b_source_case_id="B4-HARD-GATE",
        )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["contains_secret_or_credential"])
        self.assertEqual("blocked_by_phase_a", result["input_obj"]["phase_b_soft_proposal"]["soft_reason_code"])
        self.assertEqual("phase_b_blocked_by_hard_gate", result["input_obj"]["context_metadata"]["router_hint_source"])

    def test_b4_008_malformed_deterministic_phase_b_fails_closed(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        malformed_phase_b = {
            "phase_a_case_id": "B4-MALFORMED",
            "summary_short": "malformed",
        }
        with patch.object(smoke, "_BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW", return_value=malformed_phase_b):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="deterministic",
                    phase_b_source_case_id="B4-MALFORMED",
                )
        responder.assert_not_called()
        run_local_route.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("invalid_deterministic_phase_b", result["reason"])
        self.assertIn("missing B1 phase_b fields", result["validation_errors"])

    def test_b4_009_cross_case_phase_a_phase_b_mix_rejected(self):
        message_a = "Explain what a centrifugal pump is."
        message_b = "Find public DOI source for algae modeling."
        built_b = self.safe_input(message_b)
        phase_b_from_b = smoke._BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW(
            case_id="B4-CASE-B",
            input_text=message_b,
            phase_a=built_b["phase_a_signals"],
        )
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW", return_value=phase_b_from_b):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message_a,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="deterministic",
                    phase_b_source_case_id="B4-CASE-A",
                )
        responder.assert_not_called()
        run_local_route.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("invalid_deterministic_phase_b", result["reason"])
        self.assertIn("phase_b case_id mismatch", result["validation_errors"])

    def test_b4_010_privacy_report_redaction(self):
        report = ROOT / "reports" / "router_policy" / "1G-B2-F3-B4" / (
            "router_policy_message_route_deterministic_phase_b_summary.json"
        )
        if not report.exists():
            self.skipTest("B4 report not generated yet")
        text = report.read_text(encoding="utf-8")
        self.assertIn("synthetic_or_sanitized_only", text)
        self.assertNotIn("BlueRev proprietary", text)
        self.assertNotIn("sk-test-1234567890", text)
        self.assertNotIn("raw_model_output", text)

    def test_b4_live_001_default_path_does_not_call_live_phase_b(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="local answer")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW") as live_builder:
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                assume_public_simple=True,
            )
        live_builder.assert_not_called()
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("stub", result["phase_b_source_kind"])
        self.assertFalse(result["phase_b_source_used"])
        self.assertEqual(
            "Benign local-answer smoke message.",
            result["input_obj"]["phase_b_soft_proposal"]["summary_short"],
        )

    def test_b4_live_002_deterministic_path_unchanged_and_live_not_called(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="local answer")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW") as live_builder:
            with patch.object(
                smoke,
                "_BUILD_DETERMINISTIC_PHASE_B_SOFT_REVIEW",
                wraps=smoke.build_soft_review,
            ) as deterministic_builder:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="deterministic",
                    phase_b_source_case_id="B4-BENIGN",
                )
        live_builder.assert_not_called()
        deterministic_builder.assert_called_once()
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("deterministic", result["phase_b_source_kind"])
        self.assertEqual(
            "local_phase_b_soft_review_probe.build_soft_review",
            result["input_obj"]["context_metadata"]["phase_b_source_function"],
        )

    def test_b4_live_003_explicit_live_path_uses_fake_seam_and_calls_b1_once(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="local answer")
        fake_phase_b = self.valid_live_phase_b("B4-LIVE-BENIGN")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=fake_phase_b) as live_builder:
            with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT", wraps=bridge.apply_phase_b_router_hint) as b1:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-BENIGN",
                    run_local_phase_b=True,
                )
        live_builder.assert_called_once()
        b1.assert_called_once()
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("live_local_qwen", result["phase_b_source_kind"])
        phase_b = result["input_obj"]["phase_b_soft_proposal"]
        self.assertEqual("B4-LIVE-BENIGN", phase_b["phase_a_case_id"])
        for field, value in fake_phase_b.items():
            self.assertEqual(value, phase_b[field])
        metadata = result["input_obj"]["context_metadata"]
        self.assertEqual("live_local_qwen_soft_review", metadata["phase_b_source_kind"])
        self.assertEqual("B4-LIVE-BENIGN", metadata["phase_b_source_case_id"])

    def test_b4_live_r1_real_build_seam_does_not_self_leak_phase_a_case_id(self):
        message = "Explain what a centrifugal pump is."
        phase_a = self.safe_input(message)["phase_a_signals"]
        proposal = self.valid_live_phase_b("B4-LIVE-R1")
        schema_valid = {"schema_valid": True, "errors": []}
        with patch.object(smoke, "_load_live_phase_b_schema", return_value={}):
            with patch.object(
                smoke.live_phase_b.structured_probe,
                "call_ollama_chat",
                return_value={"ok": True, "body": {}},
            ) as ollama_call:
                with patch.object(smoke.live_phase_b, "parse_soft_proposal", return_value=(proposal, None)):
                    with patch.object(smoke.live_phase_b.structured_probe, "validate_instance", return_value=schema_valid):
                        built_phase_b = smoke._build_live_local_phase_b_soft_review(
                            case_id="B4-LIVE-R1",
                            input_text=message,
                            phase_a=phase_a,
                            model=smoke.DEFAULT_PHASE_B_MODEL,
                            endpoint=smoke.DEFAULT_PHASE_B_ENDPOINT,
                            timeout_seconds=180,
                        )
                        responder = Mock(return_value="local answer")
                        result = smoke.run_message_route_smoke(
                            message,
                            responder=responder,
                            now=NOW,
                            assume_public_simple=True,
                            phase_b_source_kind="live_local_qwen",
                            phase_b_source_case_id="B4-LIVE-R1",
                            run_local_phase_b=True,
                        )

        self.assertNotIn("phase_a_case_id", built_phase_b)
        self.assertIn("_live_phase_b_diagnostics", built_phase_b)
        self.assertEqual(
            [],
            smoke.live_phase_b.authority_field_leakage(
                {key: value for key, value in built_phase_b.items() if key != "_live_phase_b_diagnostics"}
            ),
        )
        self.assertGreaterEqual(ollama_call.call_count, 2)
        responder.assert_called_once_with(message)
        self.assertTrue(result["executed"])
        self.assertEqual("local_answer", result["reason"])
        self.assertEqual(
            "B4-LIVE-R1",
            result["input_obj"]["phase_b_soft_proposal"]["phase_a_case_id"],
        )

    def test_b4_live_004_live_requires_explicit_local_phase_b_flag(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW") as live_builder:
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-BENIGN",
                    run_local_phase_b=False,
                )
        live_builder.assert_not_called()
        run_local_route.assert_not_called()
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("phase_b_source_conflict", result["reason"])

    def test_b4_live_005_phase_b_source_conflict_rejected_when_b1_disabled(self):
        message = "Explain what a centrifugal pump is."
        for source_kind, run_local_phase_b in (("deterministic", False), ("live_local_qwen", True)):
            with self.subTest(source_kind=source_kind):
                responder = Mock(return_value="should not run")
                with patch.object(smoke, "_APPLY_PHASE_B_ROUTER_HINT") as b1:
                    with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                        result = smoke.run_message_route_smoke(
                            message,
                            responder=responder,
                            now=NOW,
                            assume_public_simple=True,
                            use_phase_b_hints=False,
                            phase_b_source_kind=source_kind,
                            phase_b_source_case_id="B4-LIVE-CONFLICT",
                            run_local_phase_b=run_local_phase_b,
                        )
                b1.assert_not_called()
                run_local_route.assert_not_called()
                responder.assert_not_called()
                self.assertFalse(result["executed"])
                self.assertEqual("phase_b_source_conflict", result["reason"])

        with patch("builtins.print") as printed:
            exit_code = smoke.main(
                [
                    "--message",
                    message,
                    "--assume-public-simple",
                    "--no-phase-b-hints",
                    "--phase-b-source",
                    "deterministic",
                    "--phase-b-source-case-id",
                    "B4-LIVE-CONFLICT",
                ]
            )
        self.assertEqual(0, exit_code)
        cli_result = json.loads(printed.call_args.args[0])
        self.assertFalse(cli_result["executed"])
        self.assertEqual("phase_b_source_conflict", cli_result["reason"])

    def test_b4_live_006_malformed_live_output_fails_closed_without_stub_fallback(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        malformed_phase_b = {"phase_a_case_id": "B4-LIVE-MALFORMED", "summary_short": "missing fields"}
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=malformed_phase_b):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-MALFORMED",
                    run_local_phase_b=True,
                )
        run_local_route.assert_not_called()
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("invalid_live_phase_b", result["reason"])
        self.assertIn("missing B1 phase_b fields", result["validation_errors"])

    def test_b4_live_007_live_exception_fails_closed(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", side_effect=TimeoutError("timeout")):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-TIMEOUT",
                    run_local_phase_b=True,
                )
        run_local_route.assert_not_called()
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("live_phase_b_source_failed", result["reason"])
        self.assertEqual("TimeoutError", result["error_type"])
        self.assertNotIn("input_obj", result)

    def test_b4_live_008_authority_leakage_rejected(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        leakage_fields = {
            "can_override_phase_a": True,
            "external_provider_allowed": True,
            "recommends_external_provider": True,
            "recommends_retrieval": True,
            "memory_write_allowed": True,
            "tool_execution_allowed": True,
            "runtime_approved": True,
            "redaction_required": False,
        }
        leaked_phase_b = self.valid_live_phase_b("B4-LIVE-LEAK", **leakage_fields)
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=leaked_phase_b):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-LEAK",
                    run_local_phase_b=True,
                )
        run_local_route.assert_not_called()
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("invalid_live_phase_b", result["reason"])
        self.assertIn("live phase_b authority leakage", result["validation_errors"])
        self.assertNotIn("input_obj", result)

    def test_b4_live_009_hard_gate_dominates_live_benign_phase_b(self):
        message = "my API key is sk-test-1234567890"
        responder = Mock(return_value="should not run")
        fake_phase_b = self.valid_live_phase_b("B4-LIVE-HARD-GATE")
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=fake_phase_b):
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                assume_public_simple=True,
                phase_b_source_kind="live_local_qwen",
                phase_b_source_case_id="B4-LIVE-HARD-GATE",
                run_local_phase_b=True,
            )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertTrue(result["input_obj"]["phase_a_signals"]["contains_secret_or_credential"])
        self.assertEqual("phase_b_blocked_by_hard_gate", result["input_obj"]["context_metadata"]["router_hint_source"])

    def test_b4_live_010_source_current_info_remains_conservative(self):
        message = "Find public DOI source for algae modeling."
        responder = Mock(return_value="should not run")
        fake_phase_b = self.valid_live_phase_b(
            "B4-LIVE-SOURCE",
            summary_short="Candidate source review request.",
            primary_domain="source",
            domain_tags=["source", "reference"],
            usefulness_for_future_review="medium",
            possible_memory_card_type="source_card",
            soft_reason_code="source_candidate",
            brief_rationale="The message asks about source-like context.",
        )
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=fake_phase_b):
            result = smoke.run_message_route_smoke(
                message,
                responder=responder,
                now=NOW,
                assume_public_simple=True,
                phase_b_source_kind="live_local_qwen",
                phase_b_source_case_id="B4-LIVE-SOURCE",
                run_local_phase_b=True,
            )
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        router = result["input_obj"]["router_hint"]
        self.assertEqual("review", router["task_type"])
        self.assertTrue(router["needs_current_info"])
        self.assertTrue(router["needs_file_context"])

    def test_b4_live_011_localhost_only_endpoint_rejected_before_live_call(self):
        message = "Explain what a centrifugal pump is."
        rejected_endpoints = (
            "https://api.openai.com",
            "http://192.168.1.10:11434",
            "http://localhost.evil.com:11434",
            "http://user:pass@localhost:11434",
            "http://localhost:11434/api/chat?x=1",
            "http://localhost:11434/#frag",
        )
        for endpoint in rejected_endpoints:
            with self.subTest(endpoint=endpoint):
                responder = Mock(return_value="should not run")
                with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW") as live_builder:
                    with patch.object(smoke.live_phase_b.structured_probe, "call_ollama_chat") as ollama_call:
                        with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                            result = smoke.run_message_route_smoke(
                                message,
                                responder=responder,
                                now=NOW,
                                assume_public_simple=True,
                                phase_b_source_kind="live_local_qwen",
                                phase_b_source_case_id="B4-LIVE-ENDPOINT",
                                run_local_phase_b=True,
                                phase_b_endpoint=endpoint,
                            )
                live_builder.assert_not_called()
                ollama_call.assert_not_called()
                run_local_route.assert_not_called()
                responder.assert_not_called()
                self.assertFalse(result["executed"])
                self.assertEqual("invalid_phase_b_endpoint", result["reason"])

    def test_b4_live_012_effective_passthrough_missing_field_fails_closed(self):
        message = "Explain what a centrifugal pump is."
        responder = Mock(return_value="should not run")
        missing_field = self.valid_live_phase_b("B4-LIVE-MISSING")
        del missing_field["soft_uncertain_fields"]
        with patch.object(smoke, "_BUILD_LIVE_LOCAL_PHASE_B_SOFT_REVIEW", return_value=missing_field):
            with patch.object(smoke, "_RUN_LOCAL_ROUTE") as run_local_route:
                result = smoke.run_message_route_smoke(
                    message,
                    responder=responder,
                    now=NOW,
                    assume_public_simple=True,
                    phase_b_source_kind="live_local_qwen",
                    phase_b_source_case_id="B4-LIVE-MISSING",
                    run_local_phase_b=True,
                )
        run_local_route.assert_not_called()
        responder.assert_not_called()
        self.assertFalse(result["executed"])
        self.assertEqual("invalid_live_phase_b", result["reason"])
        self.assertIn("missing B1 phase_b fields", result["validation_errors"])

    def test_b4_live_013_cli_redaction_privacy_on_live_phase_b_failure(self):
        sensitive = "my API key is sk-test-secret-12345678"
        with patch("builtins.print") as printed:
            exit_code = smoke.main(
                [
                    "--message",
                    sensitive,
                    "--assume-public-simple",
                    "--phase-b-source",
                    "live-local-qwen",
                    "--phase-b-source-case-id",
                    "B4-LIVE-SECRET",
                    "--run-local-phase-b",
                    "--phase-b-endpoint",
                    "https://api.openai.com",
                    "--now",
                    NOW,
                ]
            )
        self.assertEqual(0, exit_code)
        output = printed.call_args.args[0]
        cli_result = json.loads(output)
        self.assertFalse(cli_result["executed"])
        self.assertEqual("invalid_phase_b_endpoint", cli_result["reason"])
        self.assertNotIn(sensitive, output)
        self.assertNotIn("sk-test-secret-12345678", output)
        self.assertNotIn("raw_model_output", output)
        self.assertNotIn("input_obj", output)
        self.assertNotIn("audit_notes", output)


if __name__ == "__main__":
    unittest.main()
