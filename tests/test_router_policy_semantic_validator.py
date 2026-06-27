import copy
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_canonical_digest as digest_helper  # noqa: E402
import router_policy_semantic_validator as validator  # noqa: E402


FIXTURE_PATH = ROOT / "tests/fixtures/router_policy/base_router_policy_fixture.json"
INPUT_SCHEMA_PATH = ROOT / "schemas/router_policy_input_v0_3_1_1.schema.json"
DECISION_SCHEMA_PATH = ROOT / "schemas/router_policy_decision_v0_3_1_1.schema.json"
NOW = "2026-06-24T08:30:00+00:00"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(value, schema, path="$"):
    errors = []
    schema_type = schema.get("type")
    allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
    if "null" in allowed_types and value is None:
        return errors

    def type_matches(expected_type):
        if expected_type == "object":
            return isinstance(value, dict)
        if expected_type == "array":
            return isinstance(value, list)
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        if expected_type is None:
            return True
        return False

    if allowed_types and not any(type_matches(item) for item in allowed_types):
        errors.append(f"{path}: invalid type")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: invalid const")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: invalid enum")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength")
        if "pattern" in schema and not re.match(schema["pattern"], value):
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, int) and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{path}: below minimum")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: below minItems")
        if schema.get("uniqueItems") and len(value) != len(set(json.dumps(item, sort_keys=True) for item in value)):
            errors.append(f"{path}: duplicate array values")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(schema_errors(item, item_schema, f"{path}[{index}]"))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{path}.{field}: missing required")
        if schema.get("additionalProperties") is False:
            for field in value:
                if field not in properties:
                    errors.append(f"{path}.{field}: additional property")
        for field, item in value.items():
            if field in properties:
                errors.extend(schema_errors(item, properties[field], f"{path}.{field}"))
    return errors


class RouterPolicySemanticValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE_PATH)
        cls.input_schema = load_json(INPUT_SCHEMA_PATH)
        cls.decision_schema = load_json(DECISION_SCHEMA_PATH)

    def base_input(self):
        return copy.deepcopy(self.fixture["input"])

    def base_decision(self):
        return copy.deepcopy(self.fixture["decision"])

    def assert_schema_valid(self, value, schema):
        self.assertEqual([], schema_errors(value, schema))

    def assert_no_violations(self, input_obj, decision, previous_decision=None):
        self.assertEqual(
            [],
            validator.validate_router_decision_semantics(
                input_obj,
                decision,
                previous_decision=previous_decision,
                now=NOW,
            ),
        )

    def assert_violation(self, input_obj, decision, code, previous_decision=None):
        violations = validator.validate_router_decision_semantics(
            input_obj,
            decision,
            previous_decision=previous_decision,
            now=NOW,
        )
        codes = {violation["code"] for violation in violations}
        self.assertIn(code, codes, violations)
        for violation in violations:
            self.assertIn("code", violation)
            self.assertIn("severity", violation)
            self.assertIn("message", violation)
            self.assertIn("field_path", violation)

    def with_public_external_policy(self, input_obj):
        input_obj["user_policy"]["external_routing_enabled"] = True
        input_obj["provider_policy"] = {
            "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "CHEAP_EXTERNAL", "SCIENTIFIC_MEDIUM"],
            "blocked_provider_tiers": ["FRONTIER"],
        }
        input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
        input_obj["phase_a_signals"]["external_provider_allowed"] = True
        return input_obj

    def external_candidate_decision(self):
        decision = self.base_decision()
        decision.update(
            {
                "route_action": "route_external_candidate",
                "route_tier": "SCIENTIFIC_MEDIUM",
                "provider_candidate": "external:scientific_medium",
                "proposed_external_target": "external:scientific_medium",
                "external_allowed": True,
                "provider_call_allowed_now": True,
                "environment_type": "provider_api",
                "state_scope": "external_provider",
                "allowed_execution_mode": "dry_run",
                "requested_action_type": "provider_call",
                "budget_class": "medium",
                "reason_codes": ["high_complexity_external_candidate"],
                "audit_notes": ["Public high-complexity request may use eligible external provider tier."],
            }
        )
        return decision

    def confirmation_payload(self):
        return {
            "scope": "external_provider_call",
            "target": "external:scientific_medium",
            "payload_preview": "Redacted summary for provider preflight.",
            "payload_preview_truncated": False,
            "full_payload_available_for_review": True,
            "payload_digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "full_payload_digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "redaction_status": "redacted",
            "estimated_tokens": 800,
            "estimated_cost_class": "medium",
            "side_effect_level": "high",
            "reversibility": "partially_reversible",
            "diff_summary": null_value(),
            "full_diff_available_for_review": False,
            "full_diff_digest": None,
            "file_operations": [],
            "command": None,
            "cwd": None,
            "terminal_risk_summary": None,
            "env_preview_redacted": None,
            "network_access_expected": True,
            "writes_outside_workspace": False,
            "destructive_command_detected": False,
            "file_paths": [],
        }

    def confirmation_decision(self):
        decision = self.base_decision()
        payload = self.confirmation_payload()
        decision.update(
            {
                "expires_at": "2026-06-24T09:00:00+00:00",
                "lifecycle_stage": "awaiting_confirmation",
                "route_action": "ask_user_confirm",
                "route_tier": "USER_CONFIRM",
                "provider_candidate": "none",
                "proposed_external_target": "external:scientific_medium",
                "allowed_execution_mode": "execute_after_confirm",
                "confirmation_required": True,
                "requires_new_decision_after_confirmation": True,
                "confirmation_payload_required": True,
                "confirmation_payload": payload,
                "confirmation_options": ["allow_once", "deny", "view_details"],
                "requested_action_type": "provider_call",
                "side_effect_level": "high",
                "reversibility": "partially_reversible",
                "environment_type": "provider_api",
                "state_scope": "external_provider",
                "reason_codes": ["confirmation_required", "provider_boundary"],
                "audit_notes": ["Provider-boundary action awaits user confirmation for a concrete payload."],
            }
        )
        decision["confirmation_digest"] = digest_helper.compute_confirmation_digest(decision)["digest"]
        return decision

    def blocked_decision(self):
        decision = self.base_decision()
        decision.update(
            {
                "lifecycle_stage": "blocked",
                "route_action": "blocked",
                "route_tier": "BLOCKED",
                "provider_candidate": "none",
                "allowed_execution_mode": "blocked",
                "response_allowed_now": False,
                "reason_codes": ["secret_or_credential"],
                "audit_notes": ["Blocked by RouterPolicy contract."],
            }
        )
        return decision

    def test_schemas_load_and_base_fixture_is_schema_valid(self):
        self.assertEqual("RouterPolicyInputV0311", self.input_schema["title"])
        self.assertEqual("RouterPolicyDecisionV0311", self.decision_schema["title"])
        self.assert_schema_valid(self.base_input(), self.input_schema)
        self.assert_schema_valid(self.base_decision(), self.decision_schema)

    def test_rp001_secret_literal_blocks_external(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Never expose this API key sk-test-secret-12345678."
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "secret"
        decision = self.blocked_decision()
        self.assert_schema_valid(decision, self.decision_schema)
        self.assert_no_violations(input_obj, decision)

    def test_rp002_bluerev_ip_sensitive_never_external(self):
        input_obj = self.base_input()
        input_obj["message_text"] = "Keep this proprietary BlueRev calculation local."
        input_obj["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "sensitive"
        decision = self.base_decision()
        decision["reason_codes"] = ["local_only_sensitive_context"]
        decision["audit_notes"] = ["IP-sensitive project context remains local answer-only."]
        self.assert_no_violations(input_obj, decision)

    def test_rp003_private_memory_folder_external_provider_requires_confirmation(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"] = True
        input_obj["phase_a_signals"]["mentions_external_provider_or_upload_intent"] = True
        input_obj["phase_a_signals"]["sensitivity_bucket_proposal"] = "sensitive"
        decision = self.confirmation_decision()
        self.assert_schema_valid(decision, self.decision_schema)
        self.assert_no_violations(input_obj, decision)

    def test_rp004_ambiguous_external_routing_asks_clarification(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["clarification_required"] = True
        decision = self.base_decision()
        decision.update(
            {
                "route_action": "ask_clarification",
                "allowed_execution_mode": "propose_only",
                "provider_candidate": "none",
                "reason_codes": ["clarification_required", "ambiguous_external_routing"],
                "audit_notes": ["Unclear target requires clarification before routing."],
            }
        )
        self.assert_no_violations(input_obj, decision)

    def test_rp005_non_sensitive_simple_chat_local_answer(self):
        self.assert_no_violations(self.base_input(), self.base_decision())

    def test_rp006_non_sensitive_scientific_external_candidate_if_policy_allows(self):
        input_obj = self.with_public_external_policy(self.base_input())
        input_obj["router_hint"]["needs_scientific_depth"] = True
        decision = self.external_candidate_decision()
        self.assert_schema_valid(decision, self.decision_schema)
        self.assert_no_violations(input_obj, decision)

    def test_rp007_budget_cap_enforced_with_local_valid_route(self):
        input_obj = self.base_input()
        input_obj["budget_policy"]["max_tier"] = "LOCAL_ONLY"
        decision = self.base_decision()
        decision["route_tier"] = "LOCAL_ONLY"
        self.assert_no_violations(input_obj, decision)

    def test_rp008_phase_b_clarification_context_asks_clarification(self):
        input_obj = self.base_input()
        input_obj["phase_b_soft_proposal"]["soft_reason_code"] = "clarification_context"
        decision = self.base_decision()
        decision.update(
            {
                "route_action": "ask_clarification",
                "allowed_execution_mode": "propose_only",
                "provider_candidate": "none",
                "reason_codes": ["clarification_required"],
                "audit_notes": ["Phase B clarification context requires user clarification."],
            }
        )
        self.assert_no_violations(input_obj, decision)

    def test_adv001_local_only_with_external_provider(self):
        decision = self.base_decision()
        decision["provider_candidate"] = "external:cheap"
        self.assert_violation(self.base_input(), decision, "LOCAL_ONLY_WITH_EXTERNAL_PROVIDER")

    def test_adv002_blocked_but_executable(self):
        decision = self.blocked_decision()
        decision["allowed_execution_mode"] = "answer_only"
        self.assert_violation(self.base_input(), decision, "BLOCKED_BUT_EXECUTABLE")

    def test_adv003_answer_only_with_side_effect(self):
        decision = self.base_decision()
        decision["side_effect_level"] = "low"
        self.assert_violation(self.base_input(), decision, "ANSWER_ONLY_WITH_SIDE_EFFECT")

    def test_adv004_high_side_effect_without_confirmation_or_review(self):
        decision = self.base_decision()
        decision.update(
            {
                "allowed_execution_mode": "propose_only",
                "route_action": "answer_local",
                "side_effect_level": "high",
                "manual_review_required": False,
                "confirmation_required": False,
            }
        )
        self.assert_violation(self.base_input(), decision, "HIGH_EFFECT_WITHOUT_CONFIRM_OR_REVIEW")

    def test_adv005_secret_with_external_allowed(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        decision = self.external_candidate_decision()
        self.assert_violation(input_obj, decision, "SECRET_WITH_EXTERNAL_ALLOWED")

    def test_adv006_private_context_with_external_allowed(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["contains_raw_private_or_ip_sensitive_context"] = True
        decision = self.external_candidate_decision()
        self.assert_violation(input_obj, decision, "PRIVATE_CONTEXT_WITH_EXTERNAL_ALLOWED")

    def test_adv007_typo_reason_code(self):
        decision = self.base_decision()
        decision["reason_codes"] = ["low_complexity_lcoal"]
        self.assert_violation(self.base_input(), decision, "REASON_CODE_MISSING")

    def test_adv008_audit_note_contains_secret(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = True
        decision = self.blocked_decision()
        decision["audit_notes"] = ["Do not expose sk-test-secret-12345678."]
        self.assert_violation(input_obj, decision, "AUDIT_NOTE_CONTAINS_SECRET")

    def test_adv009_confirmation_missing_allow_or_deny(self):
        decision = self.confirmation_decision()
        decision["confirmation_options"] = ["view_details"]
        self.assert_violation(self.base_input(), decision, "CONFIRMATION_OPTIONS_INVALID")

    def test_adv010_unknown_side_effect_executable(self):
        decision = self.base_decision()
        decision.update(
            {
                "side_effect_level": "unknown",
                "allowed_execution_mode": "dry_run",
                "tool_execution_allowed_now": True,
            }
        )
        self.assert_violation(self.base_input(), decision, "UNKNOWN_SIDE_EFFECT_TREATED_AS_SAFE")

    def test_adv011_route_tier_exceeds_budget_cap(self):
        input_obj = self.with_public_external_policy(self.base_input())
        input_obj["budget_policy"]["max_tier"] = "LOCAL_FAST"
        decision = self.external_candidate_decision()
        self.assert_violation(input_obj, decision, "BUDGET_CAP_BYPASS")

    def test_adv012_provider_call_environment_type_chat(self):
        decision = self.external_candidate_decision()
        decision["environment_type"] = "chat"
        self.assert_violation(self.with_public_external_policy(self.base_input()), decision, "PROVIDER_CALL_ENVIRONMENT_MISMATCH")

    def test_adv013_redaction_pending_but_external_browser_tool_allowed(self):
        decision = self.base_decision()
        decision.update(
            {
                "redaction_status": "required_pending",
                "requested_action_type": "browser_search",
                "environment_type": "browser",
                "state_scope": "browser",
                "allowed_execution_mode": "dry_run",
                "external_allowed": True,
                "external_network_allowed_now": True,
                "tool_execution_allowed_now": True,
            }
        )
        self.assert_violation(self.base_input(), decision, "REDACTION_PENDING_BUT_EXTERNAL_ALLOWED")

    def test_adv014_confirmation_payload_non_null_missing_or_invalid_digest(self):
        decision = self.confirmation_decision()
        decision["confirmation_digest"] = None
        self.assert_violation(self.base_input(), decision, "CONFIRMATION_DIGEST_INVALID")

    def test_adv015_stale_confirmation_reused_after_context_change(self):
        previous = self.confirmation_decision()
        decision = self.base_decision()
        decision.update(
            {
                "lifecycle_stage": "confirmed_execution",
                "expires_at": "2026-06-24T09:00:00+00:00",
                "input_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
                "consent_context": {
                    "consent_id": "consent-1",
                    "confirmed_previous_decision_id": previous["decision_id"],
                    "confirmed_confirmation_digest": previous["confirmation_digest"],
                    "confirmation_action": "allow_once",
                    "confirmed_at": "2026-06-24T08:10:00+00:00",
                },
                "allowed_execution_mode": "execute_after_confirm",
                "route_action": "route_external_candidate",
                "route_tier": "SCIENTIFIC_MEDIUM",
                "provider_candidate": "external:scientific_medium",
                "requested_action_type": "provider_call",
                "environment_type": "provider_api",
                "state_scope": "external_provider",
                "reason_codes": ["confirmation_required"],
            }
        )
        self.assert_violation(self.base_input(), decision, "STALE_CONFIRMATION_DECISION", previous_decision=previous)

    def test_adv016_confirmed_execution_without_consent_context(self):
        decision = self.base_decision()
        decision.update({"lifecycle_stage": "confirmed_execution", "expires_at": "2026-06-24T09:00:00+00:00"})
        self.assert_violation(self.base_input(), decision, "CONSENT_CONTEXT_MISSING")

    def test_adv017_confirmed_execution_digest_mismatch(self):
        previous = self.confirmation_decision()
        decision = copy.deepcopy(previous)
        decision.update(
            {
                "decision_id": "decision-confirmed-001",
                "lifecycle_stage": "confirmed_execution",
                "confirmation_required": False,
                "confirmation_payload_required": False,
                "confirmation_payload": None,
                "confirmation_digest": None,
                "confirmation_options": [],
                "consent_context": {
                    "consent_id": "consent-2",
                    "confirmed_previous_decision_id": previous["decision_id"],
                    "confirmed_confirmation_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    "confirmation_action": "allow_once",
                    "confirmed_at": "2026-06-24T08:10:00+00:00",
                },
            }
        )
        self.assert_violation(self.base_input(), decision, "CONSENT_DIGEST_MISMATCH", previous_decision=previous)

    def test_adv018_awaiting_confirmation_with_expires_at_null(self):
        decision = self.confirmation_decision()
        decision["expires_at"] = None
        self.assert_violation(self.base_input(), decision, "CONFIRMATION_EXPIRY_MISSING")

    def test_adv019_answer_only_with_provider_tool_network_state_permission_true(self):
        decision = self.base_decision()
        decision["provider_call_allowed_now"] = True
        self.assert_violation(self.base_input(), decision, "ANSWER_ONLY_WITH_TOOL_PROVIDER_OR_STATE_PERMISSION")

    def test_adv020_provider_policy_allowed_blocked_tier_overlap(self):
        input_obj = self.base_input()
        input_obj["provider_policy"]["blocked_provider_tiers"].append("LOCAL_FAST")
        self.assert_violation(input_obj, self.base_decision(), "PROVIDER_POLICY_TIER_CONFLICT")

    def test_adv021_memory_policy_failed_but_state_change_allowed(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "memory_write",
                "environment_type": "memory_store",
                "state_scope": "memory",
                "allowed_execution_mode": "dry_run",
                "state_change_allowed_now": True,
                "memory_policy_result": {
                    "passed": False,
                    "write_type": "create",
                    "sensitivity_bucket": "project_ip",
                    "contains_literal_secret": False,
                    "preview": "Rejected memory write.",
                },
                "reason_codes": ["memory_policy_required"],
            }
        )
        self.assert_violation(self.base_input(), decision, "MEMORY_POLICY_FAILED_BUT_STATE_CHANGE_ALLOWED")

    def test_adv022_external_network_requires_external_allowed(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "browser_search",
                "environment_type": "browser",
                "state_scope": "browser",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "tool_execution_allowed_now": True,
                "external_network_allowed_now": True,
                "external_allowed": False,
                "reason_codes": ["browser_search_boundary"],
                "audit_notes": ["Browser search requires external network policy."],
            }
        )
        self.assert_violation(self.base_input(), decision, "EXTERNAL_NETWORK_WITHOUT_EXTERNAL_ALLOWED")

    def test_adv023_browser_tool_execution_requires_external_network_permission(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "browser_search",
                "environment_type": "browser",
                "state_scope": "browser",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "tool_execution_allowed_now": True,
                "external_network_allowed_now": False,
                "external_allowed": True,
                "reason_codes": ["browser_search_boundary"],
                "audit_notes": ["Browser execution must carry explicit network permission."],
            }
        )
        self.assert_violation(self.base_input(), decision, "TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION")

    def test_adv024_tool_call_execution_requires_external_network_permission(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "tool_call",
                "environment_type": "mcp",
                "state_scope": "mcp",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "tool_execution_allowed_now": True,
                "external_network_allowed_now": False,
                "external_allowed": True,
                "reason_codes": ["external_network_blocked"],
                "audit_notes": ["Tool execution must carry explicit network permission."],
            }
        )
        self.assert_violation(self.base_input(), decision, "TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION")

    def test_adv025_mcp_call_execution_requires_external_network_permission(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "mcp_call",
                "environment_type": "mcp",
                "state_scope": "mcp",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "tool_execution_allowed_now": True,
                "external_network_allowed_now": False,
                "external_allowed": True,
                "reason_codes": ["external_network_blocked"],
                "audit_notes": ["MCP execution must carry explicit network permission."],
            }
        )
        self.assert_violation(self.base_input(), decision, "TOOL_EXECUTION_WITHOUT_EXTERNAL_NETWORK_PERMISSION")

    def test_adv026_external_provider_candidate_forbidden_when_external_not_allowed(self):
        decision = self.base_decision()
        decision.update(
            {
                "route_action": "require_preflight",
                "route_tier": "LOCAL_FAST",
                "provider_candidate": "external:cheap",
                "external_allowed": False,
                "allowed_execution_mode": "dry_run",
                "reason_codes": ["provider_boundary"],
                "audit_notes": ["External provider candidate must wait for external policy allowance."],
            }
        )
        self.assert_violation(self.base_input(), decision, "EXTERNAL_CANDIDATE_WHILE_EXTERNAL_FORBIDDEN")

    def test_adv027_audit_note_secret_rejected_even_when_phase_a_missed_secret(self):
        input_obj = self.base_input()
        input_obj["phase_a_signals"]["contains_secret_or_credential"] = False
        decision = self.base_decision()
        decision["audit_notes"] = ["Generated note includes sk-test-secret-12345678."]
        self.assert_violation(input_obj, decision, "AUDIT_NOTE_CONTAINS_SECRET")

    def test_adv028_memory_write_without_policy(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "memory_write",
                "environment_type": "memory_store",
                "state_scope": "memory",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "memory_policy_result": None,
                "reason_codes": ["memory_policy_required"],
                "audit_notes": ["Memory write requires policy result before state change."],
            }
        )
        self.assert_violation(self.base_input(), decision, "MEMORY_WRITE_WITHOUT_POLICY")

    def test_adv029_file_write_environment_mismatch(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "file_write",
                "environment_type": "chat",
                "state_scope": "repo",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "reason_codes": ["file_write_requires_dry_run"],
                "audit_notes": ["File write preflight must use a file or codebase environment."],
            }
        )
        self.assert_violation(self.base_input(), decision, "FILE_WRITE_ENVIRONMENT_MISMATCH")

    def test_adv030_terminal_environment_mismatch(self):
        decision = self.base_decision()
        decision.update(
            {
                "requested_action_type": "terminal_command",
                "environment_type": "chat",
                "state_scope": "os",
                "allowed_execution_mode": "dry_run",
                "side_effect_level": "low",
                "reason_codes": ["terminal_requires_preflight"],
                "audit_notes": ["Terminal command preflight must use a terminal environment."],
            }
        )
        self.assert_violation(self.base_input(), decision, "TERMINAL_ENVIRONMENT_MISMATCH")

    def test_adv031_external_allowed_requires_external_route_action(self):
        decision = self.base_decision()
        decision.update(
            {
                "route_action": "ask_user_confirm",
                "route_tier": "USER_CONFIRM",
                "provider_candidate": "external:scientific_medium",
                "proposed_external_target": "external:scientific_medium",
                "external_allowed": True,
                "provider_call_allowed_now": False,
                "external_network_allowed_now": False,
                "allowed_execution_mode": "propose_only",
                "reason_codes": ["high_complexity_external_candidate"],
                "audit_notes": ["External proposal requires confirmation before any provider call."],
            }
        )
        self.assert_violation(self.base_input(), decision, "EXTERNAL_ALLOWED_WITHOUT_EXTERNAL_ROUTE_ACTION")


def null_value():
    return None


if __name__ == "__main__":
    unittest.main()
