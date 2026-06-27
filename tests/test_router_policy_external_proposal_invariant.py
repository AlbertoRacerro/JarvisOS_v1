from __future__ import annotations

import ast
import copy
import json
import re
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_decision_probe as decision_probe  # noqa: E402
import router_policy_message_route_smoke as smoke  # noqa: E402


NOW = "2026-06-27T10:00:00+00:00"
ROUTER_MODULE_PATH = ROOT / "scripts" / "router_policy_decision_probe.py"
DECISION_SCHEMA_PATH = ROOT / "schemas" / "router_policy_decision_v0_3_1_1.schema.json"
VALID_EXTERNAL_TARGET = "external:scientific_medium"
VALID_TARGETS = {"external:cheap", "external:scientific_medium", "external:frontier", None}
EXPECTED_PRODUCERS = {
    "_budget_or_policy_fallback",
    "_external_candidate_proposal",
    "_private_provider_boundary",
    "_unknown_external_pressure",
}
SCRUB_AFTER_PRODUCERS = {"_budget_or_policy_fallback", "_private_provider_boundary"}
SUPPRESS_BEFORE_PRODUCERS = {"_external_candidate_proposal", "_unknown_external_pressure"}
NON_TRUE_FLAGS = ("missing", None, False, 1, "true", "True", [], {})
DIRECT_FINALIZER_NON_TRUE_FLAGS = (False, None, "true", 1)
INTEGRATION_NON_TRUE_FLAGS = (False, None, "true", 1)
SENTINEL_FIELD = "max_tokens_allowed"
SENTINEL_VALUE = 1337
FORCED_EXTERNAL_ARTIFACT_BUNDLE_FIELDS = (
    "proposed_external_target",
    "external_allowed",
    "external_network_allowed_now",
    "provider_call_allowed_now",
    "confirmation_required",
    "confirmation_payload_required",
    "confirmation_payload",
    "confirmation_digest",
    "confirmation_options",
)
ORIGINAL_EXTERNAL_CANDIDATE_PROPOSAL = decision_probe._external_candidate_proposal


def load_decision_schema() -> dict:
    return json.loads(DECISION_SCHEMA_PATH.read_text(encoding="utf-8"))


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


def always_present_external_fields() -> set[str]:
    required = set(load_decision_schema()["required"])
    return {
        field
        for field in (
            "proposed_external_target",
            "external_allowed",
            "external_network_allowed_now",
            "provider_call_allowed_now",
            "confirmation_required",
            "confirmation_payload_required",
            "confirmation_payload",
            "confirmation_digest",
            "confirmation_options",
            "redaction_required",
            "redaction_status",
        )
        if field in required
    }


def _is_non_none_node(node: ast.AST | None) -> bool:
    return not (isinstance(node, ast.Constant) and node.value is None)


def discover_external_target_producers() -> set[str]:
    tree = ast.parse(ROUTER_MODULE_PATH.read_text(encoding="utf-8"))
    producers: set[str] = set()

    class ProducerVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.current_function: str | None = None

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            previous = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = previous

        def _mark(self) -> None:
            if self.current_function is not None:
                producers.add(self.current_function)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "update" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Dict):
                    for key, value in zip(first.keys, first.values):
                        if isinstance(key, ast.Constant) and key.value == "proposed_external_target" and _is_non_none_node(value):
                            self._mark()
            if isinstance(node.func, ast.Name) and node.func.id == "dict":
                for keyword in node.keywords:
                    if keyword.arg == "proposed_external_target" and _is_non_none_node(keyword.value):
                        self._mark()
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    key = target.slice
                    if isinstance(key, ast.Constant) and key.value == "proposed_external_target" and _is_non_none_node(node.value):
                        self._mark()
                if isinstance(target, ast.Attribute) and target.attr == "proposed_external_target" and _is_non_none_node(node.value):
                    self._mark()
            if isinstance(node.value, ast.Dict):
                for key, value in zip(node.value.keys, node.value.values):
                    if isinstance(key, ast.Constant) and key.value == "proposed_external_target" and _is_non_none_node(value):
                        self._mark()
            self.generic_visit(node)

        def visit_Return(self, node: ast.Return) -> None:
            if isinstance(node.value, ast.Dict):
                for key, value in zip(node.value.keys, node.value.values):
                    if isinstance(key, ast.Constant) and key.value == "proposed_external_target" and _is_non_none_node(value):
                        self._mark()
            self.generic_visit(node)

    ProducerVisitor().visit(tree)
    return producers


def safe_input(message: str = "Explain what a pump is") -> dict:
    return smoke.build_router_policy_input_from_message_for_smoke(
        message,
        now=NOW,
        assume_public_simple=True,
    )


def conservative_input(message: str = "Explain what a pump is") -> dict:
    return smoke.build_router_policy_input_from_message_for_smoke(
        message,
        now=NOW,
        assume_public_simple=False,
    )


def set_external_flag(input_obj: dict, flag_value) -> dict:
    if flag_value == "missing":
        input_obj["user_policy"].pop("external_routing_enabled", None)
    else:
        input_obj["user_policy"]["external_routing_enabled"] = flag_value
    return input_obj


def private_provider_boundary_input(flag_value) -> dict:
    input_obj = conservative_input("Send this proprietary BlueRev calculation to an external provider.")
    input_obj["phase_a_signals"].update(
        {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": True,
            "mentions_external_provider_or_upload_intent": True,
            "clarification_required": False,
            "hard_reason_codes": ["local_only_sensitive_context"],
            "sensitivity_bucket_proposal": "sensitive",
            "requires_manual_review": True,
        }
    )
    return set_external_flag(input_obj, flag_value)


def unknown_external_pressure_input(flag_value) -> dict:
    input_obj = conservative_input("Find the latest context before answering this ambiguous request.")
    input_obj["phase_a_signals"].update(
        {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
            "clarification_required": False,
            "hard_reason_codes": ["unknown_sensitivity", "manual_review_required"],
            "sensitivity_bucket_proposal": "unknown",
            "requires_manual_review": True,
        }
    )
    input_obj["router_hint"].update(
        {
            "task_type": "review",
            "complexity": "medium",
            "domain": "general",
            "needs_reasoning": False,
            "needs_current_info": True,
            "needs_file_context": False,
            "needs_code_execution": False,
            "needs_scientific_depth": False,
        }
    )
    input_obj["action_hint"].update(
        {
            "requested_action_type": "answer",
            "needs_provider_call": False,
            "needs_terminal": False,
            "needs_file_write": False,
            "needs_memory_write": False,
        }
    )
    return set_external_flag(input_obj, flag_value)


def budget_fallback_input(flag_value) -> dict:
    input_obj = safe_input("Analyze this public scientific task deeply.")
    input_obj["phase_a_signals"].update(
        {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
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
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
        }
    )
    input_obj["provider_policy"] = {
        "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST"],
        "blocked_provider_tiers": ["SCIENTIFIC_MEDIUM", "FRONTIER"],
    }
    input_obj["budget_policy"]["max_tier"] = "LOCAL_FAST"
    return set_external_flag(input_obj, flag_value)


def external_candidate_input(flag_value) -> dict:
    input_obj = safe_input("Analyze this public scientific task deeply.")
    input_obj["phase_a_signals"].update(
        {
            "contains_secret_or_credential": False,
            "contains_raw_private_or_ip_sensitive_context": False,
            "mentions_external_provider_or_upload_intent": False,
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
            "needs_current_info": False,
            "needs_file_context": False,
            "needs_code_execution": False,
        }
    )
    input_obj["provider_policy"] = {
        "allowed_provider_tiers": ["LOCAL_ONLY", "LOCAL_FAST", "SCIENTIFIC_MEDIUM"],
        "blocked_provider_tiers": ["FRONTIER"],
    }
    input_obj["budget_policy"]["max_tier"] = "SCIENTIFIC_MEDIUM"
    return set_external_flag(input_obj, flag_value)


def assert_no_external_proposal_artifacts(decision: dict) -> None:
    assert decision["proposed_external_target"] is None
    assert decision["external_allowed"] is False
    assert decision["external_network_allowed_now"] is False
    assert decision["provider_call_allowed_now"] is False
    assert decision["confirmation_required"] is False
    assert decision["confirmation_payload_required"] is False
    assert decision["confirmation_payload"] is None
    assert decision["confirmation_digest"] is None
    assert decision["confirmation_options"] == []


def assert_schema_valid_decision(decision: dict) -> None:
    assert schema_errors(decision, load_decision_schema()) == []


def runtime_valid_external_proposal_decision() -> dict:
    input_obj = external_candidate_input(True)
    decision = decision_probe._base_decision(input_obj, NOW)
    decision = ORIGINAL_EXTERNAL_CANDIDATE_PROPOSAL(input_obj, decision)
    decision = decision_probe._enforce_external_proposal_flag_invariant(input_obj, decision)
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(decision)
    return decision


def local_complete_decision() -> dict:
    decision = decision_probe.decide_router_policy(safe_input(), now=NOW)
    assert_schema_valid_decision(decision)
    return decision


def build_forced_external_artifact_bundle() -> dict:
    runtime_decision = runtime_valid_external_proposal_decision()
    return {
        field: copy.deepcopy(runtime_decision[field]) for field in FORCED_EXTERNAL_ARTIFACT_BUNDLE_FIELDS
    }


def overlay_forced_external_artifact_bundle(decision: dict) -> tuple[dict, dict]:
    forced = copy.deepcopy(decision)
    bundle = build_forced_external_artifact_bundle()
    forced.update(copy.deepcopy(bundle))
    return forced, bundle


def assert_forced_bundle_present(value: dict, bundle: dict) -> None:
    for field, expected in bundle.items():
        assert value[field] == expected


def assert_sentinel_present(value: dict) -> None:
    assert value[SENTINEL_FIELD] == SENTINEL_VALUE


def wrap_producer(monkeypatch: pytest.MonkeyPatch, helper_name: str):
    original = getattr(decision_probe, helper_name)
    calls = {"count": 0}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(decision_probe, helper_name, wrapper)
    return calls


def wrap_forced_bundle_producer(monkeypatch: pytest.MonkeyPatch, helper_name: str):
    original = getattr(decision_probe, helper_name)
    calls = {"count": 0}
    forced_seen = {"value": None}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        original_result = original(*args, **kwargs)
        forced, bundle = overlay_forced_external_artifact_bundle(original_result)
        forced_seen["value"] = {
            "decision": copy.deepcopy(forced),
            "bundle": copy.deepcopy(bundle),
        }
        return forced

    monkeypatch.setattr(decision_probe, helper_name, wrapper)
    return calls, forced_seen


def wrap_forced_bundle_and_sentinel_producer(monkeypatch: pytest.MonkeyPatch, helper_name: str):
    original = getattr(decision_probe, helper_name)
    calls = {"count": 0}
    forced_seen = {"value": None}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        original_result = original(*args, **kwargs)
        assert SENTINEL_FIELD in original_result
        forced, bundle = overlay_forced_external_artifact_bundle(original_result)
        forced[SENTINEL_FIELD] = SENTINEL_VALUE
        forced_seen["value"] = {
            "decision": copy.deepcopy(forced),
            "bundle": copy.deepcopy(bundle),
        }
        return forced

    monkeypatch.setattr(decision_probe, helper_name, wrapper)
    return calls, forced_seen


def wrap_sentinel_producer(monkeypatch: pytest.MonkeyPatch, helper_name: str):
    original = getattr(decision_probe, helper_name)
    calls = {"count": 0}
    forced_seen = {"value": None}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        original_result = original(*args, **kwargs)
        assert SENTINEL_FIELD in original_result
        forced = copy.deepcopy(original_result)
        forced[SENTINEL_FIELD] = SENTINEL_VALUE
        forced_seen["value"] = copy.deepcopy(forced)
        return forced

    monkeypatch.setattr(decision_probe, helper_name, wrapper)
    return calls, forced_seen


class TestStructuralAstDiscovery:
    def test_invariant_helper_exists(self):
        assert hasattr(decision_probe, "_enforce_external_proposal_flag_invariant")

    def test_ast_discovers_expected_external_target_producers(self):
        assert discover_external_target_producers() == EXPECTED_PRODUCERS

    def test_schema_marks_external_artifact_fields_as_always_present(self):
        assert always_present_external_fields() == {
            "proposed_external_target",
            "external_allowed",
            "external_network_allowed_now",
            "provider_call_allowed_now",
            "confirmation_required",
            "confirmation_payload_required",
            "confirmation_payload",
            "confirmation_digest",
            "confirmation_options",
            "redaction_required",
            "redaction_status",
        }


@pytest.mark.parametrize("flag_value", DIRECT_FINALIZER_NON_TRUE_FLAGS)
def test_forced_bundle_finalizer_scrubs_not_exactly_true_flags(flag_value):
    input_obj = set_external_flag(external_candidate_input(True), flag_value)
    forced_decision, bundle = overlay_forced_external_artifact_bundle(local_complete_decision())
    forced_before = copy.deepcopy(forced_decision)

    result = decision_probe._enforce_external_proposal_flag_invariant(input_obj, forced_decision)

    assert_forced_bundle_present(forced_before, bundle)
    assert_no_external_proposal_artifacts(result)
    assert_schema_valid_decision(result)


def test_forced_bundle_finalizer_preserves_valid_target_when_flag_true():
    input_obj = external_candidate_input(True)
    forced_decision, bundle = overlay_forced_external_artifact_bundle(local_complete_decision())
    forced_before = copy.deepcopy(forced_decision)

    result = decision_probe._enforce_external_proposal_flag_invariant(input_obj, forced_decision)

    assert_forced_bundle_present(forced_before, bundle)
    assert result["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(result)


@pytest.mark.parametrize(
    ("helper_name", "input_builder"),
    [
        ("_private_provider_boundary", private_provider_boundary_input),
        ("_budget_or_policy_fallback", budget_fallback_input),
    ],
)
def test_scrub_after_producers_fire_with_flag_off_and_output_is_scrubbed(monkeypatch, helper_name, input_builder):
    calls = wrap_producer(monkeypatch, helper_name)
    decision = decision_probe.decide_router_policy(input_builder(False), now=NOW)

    assert calls["count"] > 0
    assert_no_external_proposal_artifacts(decision)


@pytest.mark.parametrize(
    ("helper_name", "input_builder"),
    [
        ("_unknown_external_pressure", unknown_external_pressure_input),
        ("_external_candidate_proposal", external_candidate_input),
    ],
)
def test_suppress_before_producers_do_not_fire_with_flag_off_and_output_is_safe(monkeypatch, helper_name, input_builder):
    calls = wrap_producer(monkeypatch, helper_name)
    decision = decision_probe.decide_router_policy(input_builder(False), now=NOW)

    assert calls["count"] == 0
    assert_no_external_proposal_artifacts(decision)


@pytest.mark.parametrize(
    ("helper_name", "input_builder", "expect_redaction"),
    [
        ("_private_provider_boundary", private_provider_boundary_input, True),
        ("_budget_or_policy_fallback", budget_fallback_input, False),
        ("_unknown_external_pressure", unknown_external_pressure_input, False),
        ("_external_candidate_proposal", external_candidate_input, False),
    ],
)
def test_flag_true_positive_paths_preserve_valid_external_target(monkeypatch, helper_name, input_builder, expect_redaction):
    calls = wrap_producer(monkeypatch, helper_name)
    decision = decision_probe.decide_router_policy(input_builder(True), now=NOW)

    assert calls["count"] > 0
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert decision["proposed_external_target"] in VALID_TARGETS
    assert decision["external_allowed"] is False
    if expect_redaction:
        assert decision["redaction_required"] is True
        assert decision["redaction_status"] == "required_pending"
    else:
        assert decision["redaction_status"] in {"not_required", "required_pending"}


@pytest.mark.parametrize(
    "flag_value",
    NON_TRUE_FLAGS,
)
@pytest.mark.parametrize(
    ("case_name", "input_builder"),
    [
        ("unknown_external_pressure", unknown_external_pressure_input),
        ("budget_fallback", budget_fallback_input),
        ("private_provider_boundary", private_provider_boundary_input),
        ("external_candidate", external_candidate_input),
    ],
)
def test_behavioral_matrix_non_true_flags_never_expose_external_proposal_artifacts(flag_value, case_name, input_builder):
    decision = decision_probe.decide_router_policy(input_builder(flag_value), now=NOW)

    assert_no_external_proposal_artifacts(decision)
    assert decision["route_action"] == "route_local"
    assert decision["route_tier"] == "LOCAL_FAST"
    assert decision["allowed_execution_mode"] == "propose_only"
    assert "default_local_fallback" in decision["reason_codes"]


@pytest.mark.parametrize(
    ("case_name", "input_builder", "expected_reason"),
    [
        ("unknown_external_pressure", unknown_external_pressure_input, "ambiguous_external_routing"),
        ("budget_fallback", budget_fallback_input, "budget_cap"),
        ("private_provider_boundary", private_provider_boundary_input, "provider_boundary"),
        ("external_candidate", external_candidate_input, "high_complexity_external_candidate"),
    ],
)
def test_behavioral_matrix_flag_true_preserves_existing_positive_path_markers(case_name, input_builder, expected_reason):
    decision = decision_probe.decide_router_policy(input_builder(True), now=NOW)

    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert decision["route_action"] == "ask_user_confirm"
    assert decision["route_tier"] == "USER_CONFIRM"
    assert expected_reason in decision["reason_codes"]


def test_private_provider_boundary_flag_off_clears_external_redaction_and_confirmation_artifacts(monkeypatch):
    calls = wrap_producer(monkeypatch, "_private_provider_boundary")
    decision = decision_probe.decide_router_policy(private_provider_boundary_input(False), now=NOW)

    assert calls["count"] > 0
    assert_no_external_proposal_artifacts(decision)
    assert decision["redaction_required"] is False
    assert decision["redaction_status"] == "not_required"
    assert decision["manual_review_required"] is True


def test_budget_or_policy_fallback_flag_off_sentinel_baseline_survives_public_output(monkeypatch):
    calls, forced_seen = wrap_sentinel_producer(monkeypatch, "_budget_or_policy_fallback")
    decision = decision_probe.decide_router_policy(budget_fallback_input(False), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_sentinel_present(forced_seen["value"])
    assert_sentinel_present(decision)
    assert_schema_valid_decision(decision)


def test_private_provider_boundary_flag_off_sentinel_baseline_survives_public_output(monkeypatch):
    calls, forced_seen = wrap_sentinel_producer(monkeypatch, "_private_provider_boundary")
    decision = decision_probe.decide_router_policy(private_provider_boundary_input(False), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_sentinel_present(forced_seen["value"])
    assert_sentinel_present(decision)
    assert_schema_valid_decision(decision)


@pytest.mark.parametrize("flag_value", INTEGRATION_NON_TRUE_FLAGS)
def test_forced_budget_or_policy_fallback_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed(
    monkeypatch, flag_value
):
    calls, forced_seen = wrap_forced_bundle_and_sentinel_producer(monkeypatch, "_budget_or_policy_fallback")

    decision = decision_probe.decide_router_policy(budget_fallback_input(flag_value), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert_sentinel_present(forced_seen["value"]["decision"])
    assert_sentinel_present(decision)
    assert_no_external_proposal_artifacts(decision)
    assert_schema_valid_decision(decision)


@pytest.mark.parametrize("flag_value", INTEGRATION_NON_TRUE_FLAGS)
def test_forced_private_provider_boundary_bundle_scrubbed_when_external_flag_not_true_and_forced_return_consumed(
    monkeypatch, flag_value
):
    calls, forced_seen = wrap_forced_bundle_and_sentinel_producer(monkeypatch, "_private_provider_boundary")

    decision = decision_probe.decide_router_policy(private_provider_boundary_input(flag_value), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert_sentinel_present(forced_seen["value"]["decision"])
    assert_sentinel_present(decision)
    assert_no_external_proposal_artifacts(decision)
    assert decision["redaction_required"] is False
    assert decision["redaction_status"] == "not_required"
    assert_schema_valid_decision(decision)


def test_forced_budget_or_policy_fallback_bundle_preserved_when_external_flag_true(monkeypatch):
    calls, forced_seen = wrap_forced_bundle_producer(monkeypatch, "_budget_or_policy_fallback")
    decision = decision_probe.decide_router_policy(budget_fallback_input(True), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(decision)


def test_forced_private_provider_boundary_bundle_preserved_when_external_flag_true(monkeypatch):
    calls, forced_seen = wrap_forced_bundle_producer(monkeypatch, "_private_provider_boundary")
    decision = decision_probe.decide_router_policy(private_provider_boundary_input(True), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(decision)


def test_forced_unknown_external_pressure_bundle_preserved_when_external_flag_true(monkeypatch):
    calls, forced_seen = wrap_forced_bundle_producer(monkeypatch, "_unknown_external_pressure")
    decision = decision_probe.decide_router_policy(unknown_external_pressure_input(True), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(decision)


def test_forced_external_candidate_bundle_preserved_when_external_flag_true(monkeypatch):
    calls, forced_seen = wrap_forced_bundle_producer(monkeypatch, "_external_candidate_proposal")
    decision = decision_probe.decide_router_policy(external_candidate_input(True), now=NOW)

    assert calls["count"] > 0
    assert forced_seen["value"] is not None
    assert_forced_bundle_present(forced_seen["value"]["decision"], forced_seen["value"]["bundle"])
    assert decision["proposed_external_target"] == VALID_EXTERNAL_TARGET
    assert_schema_valid_decision(decision)
