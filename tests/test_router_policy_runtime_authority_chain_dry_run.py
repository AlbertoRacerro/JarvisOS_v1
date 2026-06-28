from __future__ import annotations

import copy
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_semantic_validator as validator  # noqa: E402


def valid_activation() -> dict:
    return {"activation_safe": True}


def valid_consumption() -> dict:
    return {
        "consumption_allowed": True,
        "automatic_execution_eligible": True,
    }


def valid_policy() -> dict:
    return {"execution_policy_allowed": True}


def evaluate(activation, consumption, policy) -> dict:
    return validator.evaluate_runtime_authority_chain_dry_run(activation, consumption, policy)


def codes(result: dict) -> set[str]:
    return {violation["code"] for violation in result["violations"]}


def test_all_four_literal_true_authority_signals_pass_dry_run_only():
    result = evaluate(valid_activation(), valid_consumption(), valid_policy())

    assert result["authority_chain_satisfied"] is True
    assert result["violations"] == []
    assert result["policy_scope"] == "no_provider_runtime_authority_chain_dry_run"
    assert result["provider_permission_granted"] is False
    assert result["network_permission_granted"] is False
    assert result["execution_permission_granted"] is False


def test_positive_noise_fields_do_not_change_authority_boolean():
    activation = {
        "activation_safe": True,
        "route_tier": "FRONTIER",
        "route_action": "route_external_candidate",
    }
    consumption = {
        "consumption_allowed": True,
        "automatic_execution_eligible": True,
        "provider_candidate": "external:frontier",
        "model_candidate": "frontier-model-label",
        "benchmark_candidate": "best-cost-per-success",
    }
    policy = {
        "execution_policy_allowed": True,
        "budget_class": "frontier",
        "max_tokens_allowed": 999999,
        "policy_scope": "economic_execution_precheck_only",
    }

    result = evaluate(activation, consumption, policy)

    assert result["authority_chain_satisfied"] is True
    assert result["violations"] == []


def test_activation_safe_missing_false_and_truthy_string_fail_closed():
    cases = [
        ({}, "ACTIVATION_SAFE_REQUIRED"),
        ({"activation_safe": False}, "ACTIVATION_SAFE_REQUIRED"),
        ({"activation_safe": "true"}, "AUTHORITY_SIGNAL_MALFORMED"),
    ]

    for activation, expected_code in cases:
        result = evaluate(activation, valid_consumption(), valid_policy())

        assert result["authority_chain_satisfied"] is False
        assert expected_code in codes(result)


def test_consumption_allowed_missing_false_and_truthy_int_fail_closed():
    cases = [
        ({"automatic_execution_eligible": True}, "CONSUMPTION_ALLOWED_REQUIRED"),
        ({"consumption_allowed": False, "automatic_execution_eligible": True}, "CONSUMPTION_ALLOWED_REQUIRED"),
        ({"consumption_allowed": 1, "automatic_execution_eligible": True}, "AUTHORITY_SIGNAL_MALFORMED"),
    ]

    for consumption, expected_code in cases:
        result = evaluate(valid_activation(), consumption, valid_policy())

        assert result["authority_chain_satisfied"] is False
        assert expected_code in codes(result)


def test_automatic_execution_eligible_missing_false_and_truthy_string_fail_closed():
    cases = [
        ({"consumption_allowed": True}, "AUTOMATIC_EXECUTION_ELIGIBLE_REQUIRED"),
        ({"consumption_allowed": True, "automatic_execution_eligible": False}, "AUTOMATIC_EXECUTION_ELIGIBLE_REQUIRED"),
        ({"consumption_allowed": True, "automatic_execution_eligible": "yes"}, "AUTHORITY_SIGNAL_MALFORMED"),
    ]

    for consumption, expected_code in cases:
        result = evaluate(valid_activation(), consumption, valid_policy())

        assert result["authority_chain_satisfied"] is False
        assert expected_code in codes(result)


def test_execution_policy_allowed_missing_false_and_truthy_string_fail_closed():
    cases = [
        ({}, "EXECUTION_POLICY_ALLOWED_REQUIRED"),
        ({"execution_policy_allowed": False}, "EXECUTION_POLICY_ALLOWED_REQUIRED"),
        ({"execution_policy_allowed": "true"}, "AUTHORITY_SIGNAL_MALFORMED"),
    ]

    for policy, expected_code in cases:
        result = evaluate(valid_activation(), valid_consumption(), policy)

        assert result["authority_chain_satisfied"] is False
        assert expected_code in codes(result)


def test_none_empty_dict_and_non_dict_inputs_fail_closed():
    none_result = evaluate(None, None, None)
    empty_result = evaluate({}, {}, {})
    non_dict_result = evaluate("true", 1, [])

    assert none_result["authority_chain_satisfied"] is False
    assert "AUTHORITY_SIGNAL_MALFORMED" in codes(none_result)
    assert empty_result["authority_chain_satisfied"] is False
    assert {
        "ACTIVATION_SAFE_REQUIRED",
        "CONSUMPTION_ALLOWED_REQUIRED",
        "AUTOMATIC_EXECUTION_ELIGIBLE_REQUIRED",
        "EXECUTION_POLICY_ALLOWED_REQUIRED",
    }.issubset(codes(empty_result))
    assert non_dict_result["authority_chain_satisfied"] is False
    assert "AUTHORITY_SIGNAL_MALFORMED" in codes(non_dict_result)


def test_collects_all_missing_false_and_malformed_authority_signal_violations():
    result = evaluate(
        {"activation_safe": "true"},
        {"consumption_allowed": False},
        {},
    )

    assert result["authority_chain_satisfied"] is False
    assert "AUTHORITY_SIGNAL_MALFORMED" in codes(result)
    assert "CONSUMPTION_ALLOWED_REQUIRED" in codes(result)
    assert "AUTOMATIC_EXECUTION_ELIGIBLE_REQUIRED" in codes(result)
    assert "EXECUTION_POLICY_ALLOWED_REQUIRED" in codes(result)


def test_route_provider_model_and_budget_noise_cannot_rescue_failed_chain():
    activation = {
        "activation_safe": False,
        "provider_candidate": "external:frontier",
        "model_candidate": "frontier-model-label",
        "route_tier": "FRONTIER",
        "route_action": "route_external_candidate",
    }
    consumption = {
        "consumption_allowed": True,
        "automatic_execution_eligible": True,
        "provider_candidate": "external:frontier",
        "model_candidate": "frontier-model-label",
        "budget_class": "frontier",
    }
    policy = {
        "execution_policy_allowed": True,
        "provider_candidate": "external:frontier",
        "model_candidate": "frontier-model-label",
        "budget_class": "frontier",
        "max_tokens_allowed": 999999,
    }

    result = evaluate(activation, consumption, policy)

    assert result["authority_chain_satisfied"] is False
    assert "ACTIVATION_SAFE_REQUIRED" in codes(result)


def test_benchmark_candidate_and_route_action_noise_cannot_rescue_failed_chain():
    activation = {
        "activation_safe": True,
        "benchmark_candidate": "best-cost-per-success",
        "route_action": "execute_after_confirm",
    }
    consumption = {
        "consumption_allowed": True,
        "automatic_execution_eligible": False,
        "benchmark_candidate": "best-cost-per-success",
        "route_action": "execute_after_confirm",
    }
    policy = {
        "execution_policy_allowed": True,
        "benchmark_candidate": "best-cost-per-success",
        "route_action": "execute_after_confirm",
    }

    result = evaluate(activation, consumption, policy)

    assert result["authority_chain_satisfied"] is False
    assert "AUTOMATIC_EXECUTION_ELIGIBLE_REQUIRED" in codes(result)


def test_helper_does_not_mutate_inputs_for_passing_or_failing_cases():
    passing_activation = valid_activation()
    passing_consumption = valid_consumption()
    passing_policy = valid_policy()
    failing_activation = {"activation_safe": "true", "route_tier": "FRONTIER"}
    failing_consumption = {"consumption_allowed": 1, "automatic_execution_eligible": "yes"}
    failing_policy = {"execution_policy_allowed": "true", "provider_candidate": "external:frontier"}

    passing_before = (
        copy.deepcopy(passing_activation),
        copy.deepcopy(passing_consumption),
        copy.deepcopy(passing_policy),
    )
    failing_before = (
        copy.deepcopy(failing_activation),
        copy.deepcopy(failing_consumption),
        copy.deepcopy(failing_policy),
    )

    assert evaluate(passing_activation, passing_consumption, passing_policy)["authority_chain_satisfied"] is True
    assert evaluate(failing_activation, failing_consumption, failing_policy)["authority_chain_satisfied"] is False
    assert (passing_activation, passing_consumption, passing_policy) == passing_before
    assert (failing_activation, failing_consumption, failing_policy) == failing_before


def test_helper_contains_no_provider_network_env_or_permission_granting_code():
    source = inspect.getsource(validator.evaluate_runtime_authority_chain_dry_run)

    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source
    assert "anthropic" not in source
    assert "os.environ" not in source
    assert "provider_permission_granted" in source
    assert "network_permission_granted" in source
    assert "execution_permission_granted" in source
