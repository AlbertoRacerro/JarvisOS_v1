import copy
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "router_policy_routing_recommendation_fallback.py"
spec = importlib.util.spec_from_file_location("router_policy_routing_recommendation_fallback", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

evaluate = module.evaluate_routing_recommendation_fallback_contract
context_digest = module.context_digest


def base_benchmark(**overrides):
    data = {
        "benchmark_winner": None,
        "benchmark_winner_selection_valid": False,
        "benchmark_winner_basis": "cost_data_incomplete",
    }
    data.update(overrides)
    return data


def base_task(**overrides):
    data = {
        "task_is_trivial_deterministic": False,
        "requires_strategic_route_choice": True,
        "immediate_recommendation_required": True,
        "public_or_irreversible_action": False,
        "local_model_sufficient": True,
        "uncertainty_reason": "cost_data_incomplete",
    }
    data.update(overrides)
    return data


def base_sensitivity(level="S1", **overrides):
    data = {
        "effective_sensitivity": level,
        "local_secret_handling_allowed": False,
        "history_allowed": False,
        "external_tool_calls_allowed": False,
        "logging_allowed_for_raw_secret": False,
        "external_raw_egress_requested": False,
    }
    data.update(overrides)
    return data


def base_economic(**overrides):
    data = {"budget_risk": "low"}
    data.update(overrides)
    return data


def artifact_for(benchmark, task, sensitivity, economic, **overrides):
    artifact = {
        "artifact_id": "artifact-001",
        "artifact_version": "1",
        "adjudicator_class": "supplied_fixture",
        "recommended_route_class": "external:scientific_medium",
        "recommendation_basis": "supplied offline adjudication fixture",
        "sensitivity_assumption": sensitivity["effective_sensitivity"],
        "uncertainty_reason": benchmark.get("benchmark_winner_basis", "cost_data_incomplete"),
        "created_for_fallback_contract_only": True,
        "not_provider_permission": True,
        "not_execution_permission": True,
        "task_context_digest": context_digest(task),
        "benchmark_result_digest": context_digest(benchmark),
        "sensitivity_context_digest": context_digest(sensitivity),
        "economic_context_digest": context_digest(economic),
    }
    artifact.update(overrides)
    return artifact


def assert_no_permissions(result):
    assert result["provider_permission_granted"] is False
    assert result["network_permission_granted"] is False
    assert result["execution_permission_granted"] is False


def codes(result):
    return {violation["code"] for violation in result["violations"]}


def test_selection_grade_benchmark_winner_used_without_model_adjudication():
    benchmark = base_benchmark(
        benchmark_winner="candidate-local-a",
        benchmark_winner_route_class="local",
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )
    result = evaluate(benchmark, base_task(), base_sensitivity("S1"), base_economic())

    assert result["routing_recommendation"] == "local"
    assert result["recommended_route_class"] == "local"
    assert result["recommended_action"] == "use_benchmark_winner"
    assert result["routing_recommendation_selection_grade"] is True
    assert result["model_adjudication_required"] is False
    assert_no_permissions(result)


@pytest.mark.parametrize("route_class", ["external:cheap", "external:scientific_medium", "external:frontier"])
def test_selection_grade_external_benchmark_winner_s2_policy_adjusted(route_class):
    benchmark = base_benchmark(
        benchmark_winner=f"winner-for-{route_class}",
        benchmark_winner_route_class=route_class,
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )

    result = evaluate(benchmark, base_task(), base_sensitivity("S2"), base_economic())

    assert result["benchmark_winner"] == f"winner-for-{route_class}"
    assert result["recommended_action"] == "produce_sanitized_S1_package"
    assert result["recommended_route_class"] is None
    assert result["requires_sanitized_package"] is True
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert result["policy_adjustment_reason"] == "sensitivity_policy_block"
    assert_no_permissions(result)


@pytest.mark.parametrize("route_class", ["external:cheap", "external:scientific_medium", "external:frontier"])
def test_selection_grade_external_benchmark_winner_s3_policy_adjusted(route_class):
    benchmark = base_benchmark(
        benchmark_winner=f"winner-for-{route_class}",
        benchmark_winner_route_class=route_class,
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )

    result = evaluate(benchmark, base_task(local_model_sufficient=True), base_sensitivity("S3"), base_economic())

    assert result["recommended_action"] == "use_strongest_allowed_local_model"
    assert result["recommended_route_class"] == "local"
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert result["policy_adjustment_reason"] == "sensitivity_policy_block"
    assert_no_permissions(result)


@pytest.mark.parametrize("route_class", ["external:cheap", "external:scientific_medium", "external:frontier"])
def test_selection_grade_external_benchmark_winner_s4_policy_adjusted(route_class):
    benchmark = base_benchmark(
        benchmark_winner=f"winner-for-{route_class}",
        benchmark_winner_route_class=route_class,
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )
    sensitivity = base_sensitivity(
        "S4",
        local_secret_handling_allowed=True,
        history_allowed=False,
        external_tool_calls_allowed=False,
        logging_allowed_for_raw_secret=False,
    )

    result = evaluate(benchmark, base_task(), sensitivity, base_economic())

    assert result["recommended_action"] == "use_strongest_allowed_local_model"
    assert result["recommended_route_class"] == "local"
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert result["policy_adjustment_reason"] == "sensitivity_policy_block"
    assert_no_permissions(result)


def test_s4_external_benchmark_winner_confirmation_does_not_bypass_sensitivity_policy():
    benchmark = base_benchmark(
        benchmark_winner="frontier-candidate",
        benchmark_winner_route_class="external:frontier",
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )
    task = base_task(public_or_irreversible_action=True, local_model_sufficient=False)

    result = evaluate(benchmark, task, base_sensitivity("S4"), base_economic())

    assert result["recommended_action"] == "request_manual_abstraction"
    assert result["recommended_route_class"] is None
    assert result["requires_user_confirmation"] is True
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert "external:" not in str(result["routing_recommendation"])
    assert_no_permissions(result)


def test_benchmark_winner_label_without_explicit_route_class_is_not_used_as_route():
    benchmark = base_benchmark(
        benchmark_winner="local",
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )

    result = evaluate(benchmark, base_task(), base_sensitivity("S1"), base_economic())

    assert result["benchmark_winner"] == "local"
    assert result["recommended_action"] == "request_model_adjudication"
    assert result["recommended_route_class"] is None
    assert result["routing_recommendation_selection_grade"] is False
    assert result["model_adjudication_required"] is True
    assert result["model_adjudication_consumed"] is False
    assert "MISSING_BENCHMARK_WINNER_ROUTE_CLASS" in codes(result)
    assert_no_permissions(result)


def test_unknown_benchmark_winner_route_class_requests_model_adjudication():
    benchmark = base_benchmark(
        benchmark_winner="candidate-a",
        benchmark_winner_route_class="vendor:real-provider",
        benchmark_winner_selection_valid=True,
        benchmark_winner_basis="selection_grade",
    )

    result = evaluate(benchmark, base_task(), base_sensitivity("S1"), base_economic())

    assert result["recommended_action"] == "request_model_adjudication"
    assert result["recommended_route_class"] is None
    assert "MISSING_BENCHMARK_WINNER_ROUTE_CLASS" in codes(result)
    assert_no_permissions(result)


def test_non_selection_grade_missing_artifact_requests_model_adjudication():
    result = evaluate(base_benchmark(), base_task(), base_sensitivity("S1"), base_economic())

    assert result["routing_recommendation"] == "request_model_adjudication"
    assert result["routing_recommendation_kind"] == "request_model_adjudication"
    assert result["recommended_route_class"] is None
    assert result["recommended_action"] == "request_model_adjudication"
    assert result["model_adjudication_required"] is True
    assert result["model_adjudication_consumed"] is False
    assert_no_permissions(result)


def test_valid_model_adjudication_artifact_produces_recommendation():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:scientific_medium")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["model_adjudication_artifact_valid"] is True
    assert result["model_adjudication_consumed"] is True
    assert result["artifact_recommended_route_class"] == "external:scientific_medium"
    assert result["recommended_route_class"] == "external:scientific_medium"
    assert result["routing_recommendation"] == "external:scientific_medium"
    assert result["routing_recommendation_selection_grade"] is False
    assert_no_permissions(result)


def test_truthy_artifact_booleans_fail_closed():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, created_for_fallback_contract_only="true")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["model_adjudication_artifact_valid"] is False
    assert result["model_adjudication_consumed"] is False
    assert result["recommended_action"] == "request_model_adjudication"
    assert "MODEL_ADJUDICATION_ARTIFACT_BOOLEAN_REQUIRED" in codes(result)
    assert_no_permissions(result)


def test_unknown_uncertainty_reason_in_artifact_invalid():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, uncertainty_reason="mystery")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert "UNKNOWN_UNCERTAINTY_REASON" in codes(result)
    assert result["recommended_action"] == "request_model_adjudication"


@pytest.mark.parametrize(
    "bad_route_class",
    [
        "produce_sanitized_S1_package",
        "request_more_benchmark",
        "request_model_adjudication",
        "manual_abstraction_required",
    ],
)
def test_artifact_action_values_are_invalid_as_recommended_route_class(bad_route_class):
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class=bad_route_class)

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert "UNKNOWN_ROUTE_CLASS" in codes(result)
    assert result["recommended_action"] == "request_model_adjudication"
    assert_no_permissions(result)


def test_unknown_route_class_invalid():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="vendor:real-provider")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert "UNKNOWN_ROUTE_CLASS" in codes(result)
    assert result["recommended_action"] == "request_model_adjudication"
    assert_no_permissions(result)


def test_action_values_not_used_as_recommended_route_class_for_s2_sanitize():
    result = evaluate(base_benchmark(), base_task(), base_sensitivity("S2"), base_economic())

    assert result["recommended_action"] == "produce_sanitized_S1_package"
    assert result["routing_recommendation_kind"] == "preprocessing_action"
    assert result["recommended_route_class"] is None
    assert result["requires_sanitized_package"] is True
    assert_no_permissions(result)


def test_trivial_deterministic_task_uses_deterministic_no_llm_without_adjudication():
    task = base_task(task_is_trivial_deterministic=True, requires_strategic_route_choice=False)

    result = evaluate(base_benchmark(), task, base_sensitivity("S4"), base_economic())

    assert result["recommended_route_class"] == "deterministic:no_llm"
    assert result["model_adjudication_required"] is False
    assert result["recommended_action"] == "use_model_adjudicated_route"
    assert_no_permissions(result)


def test_strategic_route_choice_requires_model_adjudication_without_selection_winner():
    task = base_task(task_is_trivial_deterministic=True, requires_strategic_route_choice=True)

    result = evaluate(base_benchmark(), task, base_sensitivity("S1"), base_economic())

    assert result["model_adjudication_required"] is True
    assert result["recommended_action"] == "request_model_adjudication"


def test_s4_local_model_recommendation_requires_secret_policy_allowed():
    benchmark = base_benchmark()
    task = base_task(local_model_sufficient=True)
    sensitivity = base_sensitivity(
        "S4",
        local_secret_handling_allowed=True,
        history_allowed=False,
        external_tool_calls_allowed=False,
        logging_allowed_for_raw_secret=False,
    )
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="local")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["recommended_route_class"] == "local"
    assert result["recommended_action"] == "use_model_adjudicated_route"
    assert result["model_adjudication_consumed"] is True
    assert_no_permissions(result)


def test_s4_external_artifact_downgraded_to_manual_when_secret_policy_not_allowed():
    benchmark = base_benchmark()
    task = base_task(local_model_sufficient=False)
    sensitivity = base_sensitivity("S4", local_secret_handling_allowed=False, history_allowed=True)
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:frontier")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["artifact_recommended_route_class"] == "external:frontier"
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert result["policy_adjustment_reason"] == "sensitivity_policy_block"
    assert result["recommended_action"] == "request_manual_abstraction"
    assert result["recommended_route_class"] is None
    assert_no_permissions(result)


def test_s3_external_artifact_policy_adjusted_to_local_when_local_sufficient():
    benchmark = base_benchmark()
    task = base_task(local_model_sufficient=True)
    sensitivity = base_sensitivity("S3")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:cheap")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["artifact_recommended_route_class"] == "external:cheap"
    assert result["policy_adjusted_route_class"] == "local"
    assert result["recommended_route_class"] == "local"
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert_no_permissions(result)


def test_s2_external_artifact_policy_adjusted_to_sanitization():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S2")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:cheap")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["recommended_action"] == "produce_sanitized_S1_package"
    assert result["recommended_route_class"] is None
    assert result["requires_sanitized_package"] is True
    assert result["routing_recommendation_adjusted_by_policy"] is True
    assert_no_permissions(result)


def test_artifact_context_binding_mismatch_rejected():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic)
    artifact["task_context_digest"] = "sha256:" + "0" * 64

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["model_adjudication_artifact_valid"] is False
    assert result["model_adjudication_consumed"] is False
    assert "ARTIFACT_CONTEXT_BINDING_MISMATCH" in codes(result)
    assert result["recommended_action"] == "request_model_adjudication"


def test_artifact_sensitivity_downgrade_rejected():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S3")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, sensitivity_assumption="S1")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert "ARTIFACT_SENSITIVITY_DOWNGRADE" in codes(result)
    assert result["model_adjudication_consumed"] is False
    assert result["recommended_action"] == "request_model_adjudication"


def test_external_frontier_requires_confirmation_but_not_permission():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:frontier")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["recommended_route_class"] == "external:frontier"
    assert result["requires_user_confirmation"] is True
    assert_no_permissions(result)


def test_high_budget_requires_confirmation_but_not_permission():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic(budget_risk="high")
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:scientific_medium")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["requires_user_confirmation"] is True
    assert_no_permissions(result)


def test_public_irreversible_requires_confirmation_but_not_permission():
    benchmark = base_benchmark()
    task = base_task(public_or_irreversible_action=True)
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="local")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["requires_user_confirmation"] is True
    assert_no_permissions(result)


def test_cost_data_incomplete_has_recommendation_present():
    result = evaluate(base_benchmark(benchmark_winner_basis="cost_data_incomplete"), base_task(), base_sensitivity("S1"), base_economic())

    assert result["benchmark_winner"] is None
    assert result["routing_recommendation"] is not None
    assert result["recommended_action"] == "request_model_adjudication"


def test_benchmark_non_comparable_has_recommendation_present():
    result = evaluate(base_benchmark(benchmark_winner_basis="benchmark_non_comparable"), base_task(), base_sensitivity("S1"), base_economic())

    assert result["benchmark_winner"] is None
    assert result["routing_recommendation"] is not None


@pytest.mark.parametrize(
    "action, expected_kind",
    [
        ("produce_sanitized_S1_package", "preprocessing_action"),
        ("request_more_benchmark", "request_more_benchmark"),
        ("request_model_adjudication", "request_model_adjudication"),
    ],
)
def test_artifact_action_only_recommendations_keep_route_class_null(action, expected_kind):
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class=None, recommended_action=action)

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["model_adjudication_artifact_valid"] is True
    assert result["model_adjudication_consumed"] is True
    assert result["artifact_recommended_route_class"] is None
    assert result["recommended_route_class"] is None
    assert result["recommended_action"] == action
    assert result["routing_recommendation_kind"] == expected_kind
    assert_no_permissions(result)


def test_tie_or_low_margin_requests_more_benchmark_with_artifact_action():
    benchmark = base_benchmark(benchmark_winner_basis="tie_or_low_margin")
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class=None, recommended_action="request_more_benchmark")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["requires_more_benchmark"] is True
    assert result["recommended_action"] == "request_more_benchmark"
    assert result["recommended_route_class"] is None
    assert_no_permissions(result)


def test_artifact_recommendation_recorded_separately_from_policy_adjusted_route():
    benchmark = base_benchmark()
    task = base_task(local_model_sufficient=True)
    sensitivity = base_sensitivity("S3")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic, recommended_route_class="external:frontier")

    result = evaluate(benchmark, task, sensitivity, economic, artifact)

    assert result["artifact_recommended_route_class"] == "external:frontier"
    assert result["policy_adjusted_route_class"] == "local"
    assert result["routing_recommendation"] == "local"
    assert result["routing_recommendation_adjusted_by_policy"] is True


def test_context_digest_is_stable_and_excludes_digest_fields():
    one = {"b": 2, "a": 1, "task_context_digest": "sha256:ignored"}
    two = {"a": 1, "b": 2}
    assert context_digest(one) == context_digest(two)


def test_helper_does_not_mutate_inputs():
    benchmark = base_benchmark()
    task = base_task()
    sensitivity = base_sensitivity("S1")
    economic = base_economic()
    artifact = artifact_for(benchmark, task, sensitivity, economic)

    original = copy.deepcopy((benchmark, task, sensitivity, economic, artifact))
    evaluate(benchmark, task, sensitivity, economic, artifact)
    assert (benchmark, task, sensitivity, economic, artifact) == original


def test_source_contains_no_runtime_model_or_network_call_tokens():
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden = [
        "requests.",
        "httpx",
        "urllib",
        "aiohttp",
        "openai",
        "anthropic",
        "gemini",
        "mistral",
        "cohere",
        "groq",
        "openrouter",
        "together",
        "fireworks",
        "deepseek",
        "kimi",
        "minimax",
        "perplexity",
        "os.environ",
        "dotenv",
        "api_key",
        "access_token",
        "bearer ",
        "git rev-parse",
        "subprocess",
    ]
    for token in forbidden:
        assert token not in source
