from __future__ import annotations

import ast
import copy
import json
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


def load_decision_schema() -> dict:
    return json.loads(DECISION_SCHEMA_PATH.read_text(encoding="utf-8"))


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


def wrap_producer(monkeypatch: pytest.MonkeyPatch, helper_name: str):
    original = getattr(decision_probe, helper_name)
    calls = {"count": 0}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(decision_probe, helper_name, wrapper)
    return calls


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

