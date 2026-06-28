"""No-provider routing recommendation fallback contract.

This module is intentionally helper-only. It validates supplied benchmark and
model-adjudication artifacts and returns a deterministic routing recommendation
contract result. It never calls models, providers, networks, tools, git, or env.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping


POLICY_SCOPE = "routing_recommendation_fallback_contract_no_provider_permission"

ALLOWED_ROUTE_CLASSES = {
    "local",
    "external:cheap",
    "external:scientific_medium",
    "external:frontier",
    "deterministic:no_llm",
    "public_query_only",
    "blocked_or_public_query_only",
}

ALLOWED_ACTIONS = {
    "use_benchmark_winner",
    "use_model_adjudicated_route",
    "produce_sanitized_S1_package",
    "use_strongest_allowed_local_model",
    "request_manual_abstraction",
    "request_more_benchmark",
    "request_user_confirmation",
    "request_model_adjudication",
    "blocked_by_sensitivity_policy",
}

ALLOWED_UNCERTAINTY_REASONS = {
    "security_uncertainty",
    "intelligence_uncertainty",
    "cost_data_incomplete",
    "benchmark_non_comparable",
    "tie_or_low_margin",
    "no_valid_benchmark",
    "explicit_user_escalation",
}

ALLOWED_RECOMMENDATION_KINDS = {
    "route_class",
    "preprocessing_action",
    "request_more_benchmark",
    "request_model_adjudication",
    "manual_abstraction_required",
    "blocked",
}

ALLOWED_EVIDENCE_QUALITY = {
    "none",
    "partial",
    "model_adjudicated",
    "comparable",
    "selection_grade",
}

ALLOWED_ADJUDICATOR_CLASSES = {
    "local",
    "sanitized_external_candidate",
    "supplied_fixture",
}

ALLOWED_ARTIFACT_ACTIONS = {
    "produce_sanitized_S1_package",
    "request_more_benchmark",
    "request_model_adjudication",
    "request_manual_abstraction",
    "blocked_by_sensitivity_policy",
}

SENSITIVITY_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4}

NON_ROUTE_ACTIONS = {
    "produce_sanitized_S1_package",
    "request_model_adjudication",
    "request_more_benchmark",
    "request_manual_abstraction",
    "blocked_by_sensitivity_policy",
}

DIGEST_EXCLUDED_KEYS = {
    "task_context_digest",
    "benchmark_result_digest",
    "sensitivity_context_digest",
    "economic_context_digest",
    "digest",
    "context_digest",
}


def canonical_json(value: Any) -> str:
    """Return deterministic JSON for digesting contract inputs."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def strip_digest_fields(value: Any) -> Any:
    """Remove digest fields recursively before computing binding digests."""
    if isinstance(value, Mapping):
        return {
            str(key): strip_digest_fields(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in DIGEST_EXCLUDED_KEYS and not str(key).endswith("_digest")
        }
    if isinstance(value, list):
        return [strip_digest_fields(item) for item in value]
    return value


def context_digest(value: Any) -> str:
    """Compute a deterministic sha256 digest over canonical JSON.

    The input must not include timestamps, filesystem paths, runtime environment
    data, or nondeterministic ordering. This helper only computes; callers own the
    semantic choice of fields.
    """
    payload = canonical_json(strip_digest_fields(value)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _literal_true(value: Any) -> bool:
    return value is True


def _literal_false(value: Any) -> bool:
    return value is False


def _get(mapping: Mapping[str, Any], key: str, default: Any = None) -> Any:
    if not isinstance(mapping, Mapping):
        return default
    return mapping.get(key, default)


def _sensitivity_rank(value: Any) -> int | None:
    if value not in SENSITIVITY_ORDER:
        return None
    return SENSITIVITY_ORDER[value]


def _effective_sensitivity(sensitivity_context: Mapping[str, Any]) -> str | None:
    for key in ("effective_sensitivity", "sensitivity_level", "data_sensitivity"):
        value = _get(sensitivity_context, key)
        if value in SENSITIVITY_ORDER:
            return value
    return None


def _has_valid_local_secret_policy(sensitivity_context: Mapping[str, Any]) -> bool:
    return (
        _get(sensitivity_context, "local_secret_handling_allowed") is True
        and _get(sensitivity_context, "history_allowed") is False
        and _get(sensitivity_context, "external_tool_calls_allowed") is False
        and _get(sensitivity_context, "logging_allowed_for_raw_secret") is False
    )


def _base_result(
    *,
    benchmark_winner: Any,
    benchmark_winner_selection_valid: bool,
    uncertainty_reason: str,
) -> dict[str, Any]:
    return {
        "benchmark_winner": benchmark_winner,
        "benchmark_winner_selection_valid": benchmark_winner_selection_valid,
        "routing_recommendation": None,
        "routing_recommendation_kind": None,
        "routing_recommendation_basis": None,
        "routing_recommendation_selection_grade": False,
        "recommended_route_class": None,
        "recommended_action": None,
        "uncertainty_reason": uncertainty_reason,
        "model_adjudication_required": False,
        "model_adjudication_consumed": False,
        "model_adjudication_source": "none",
        "model_adjudication_artifact_valid": False,
        "artifact_recommended_route_class": None,
        "policy_adjusted_route_class": None,
        "routing_recommendation_adjusted_by_policy": False,
        "policy_adjustment_reason": None,
        "requires_user_confirmation": False,
        "requires_sanitized_package": False,
        "requires_more_benchmark": False,
        "evidence_quality": "none",
        "provider_permission_granted": False,
        "network_permission_granted": False,
        "execution_permission_granted": False,
        "violations": [],
        "policy_scope": POLICY_SCOPE,
    }


def _violate(result: dict[str, Any], code: str, field: str | None = None) -> None:
    violation = {"code": code}
    if field is not None:
        violation["field"] = field
    result["violations"].append(violation)


def _set_request_model_adjudication(result: dict[str, Any], basis: str) -> None:
    result.update(
        {
            "routing_recommendation": "request_model_adjudication",
            "routing_recommendation_kind": "request_model_adjudication",
            "routing_recommendation_basis": basis,
            "routing_recommendation_selection_grade": False,
            "recommended_route_class": None,
            "recommended_action": "request_model_adjudication",
            "model_adjudication_required": True,
            "model_adjudication_consumed": False,
            "model_adjudication_source": "none",
            "model_adjudication_artifact_valid": False,
            "evidence_quality": "partial",
        }
    )


def _set_non_route_action(
    result: dict[str, Any],
    *,
    action: str,
    kind: str,
    basis: str,
    recommendation: str | None = None,
) -> None:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    if kind not in ALLOWED_RECOMMENDATION_KINDS:
        raise ValueError(f"unknown kind {kind!r}")
    result.update(
        {
            "routing_recommendation": recommendation or action,
            "routing_recommendation_kind": kind,
            "routing_recommendation_basis": basis,
            "routing_recommendation_selection_grade": False,
            "recommended_route_class": None,
            "recommended_action": action,
        }
    )


def _set_route(
    result: dict[str, Any],
    *,
    route_class: str,
    action: str,
    kind: str,
    basis: str,
    selection_grade: bool,
    evidence_quality: str,
) -> None:
    if route_class not in ALLOWED_ROUTE_CLASSES:
        _violate(result, "UNKNOWN_ROUTE_CLASS", "recommended_route_class")
        _set_request_model_adjudication(result, "unknown_route_class")
        return
    result.update(
        {
            "routing_recommendation": route_class,
            "routing_recommendation_kind": kind,
            "routing_recommendation_basis": basis,
            "routing_recommendation_selection_grade": selection_grade,
            "recommended_route_class": route_class,
            "recommended_action": action,
            "evidence_quality": evidence_quality,
        }
    )


def _selected_benchmark_route_class(benchmark_result: Mapping[str, Any]) -> str | None:
    for key in ("benchmark_winner_route_class", "benchmark_winner_candidate_class"):
        value = benchmark_result.get(key)
        if isinstance(value, str) and value in ALLOWED_ROUTE_CLASSES:
            return value
    return None


def _reject_missing_benchmark_route_class(result: dict[str, Any]) -> None:
    _violate(result, "MISSING_BENCHMARK_WINNER_ROUTE_CLASS", "benchmark_winner_route_class")
    _set_request_model_adjudication(result, "missing_benchmark_winner_route_class")


def _confirmation_required(
    *,
    route_class: str | None,
    action: str | None,
    task_context: Mapping[str, Any],
    sensitivity_context: Mapping[str, Any],
    economic_context: Mapping[str, Any],
) -> bool:
    return (
        route_class == "external:frontier"
        or action == "request_user_confirmation"
        or _get(economic_context, "budget_risk") == "high"
        or _get(task_context, "public_or_irreversible_action") is True
        or _get(sensitivity_context, "external_raw_egress_requested") is True
    )


def _validate_artifact_binding(
    artifact: Mapping[str, Any],
    *,
    benchmark_result: Mapping[str, Any],
    task_context: Mapping[str, Any],
    sensitivity_context: Mapping[str, Any],
    economic_context: Mapping[str, Any],
    result: dict[str, Any],
) -> bool:
    expected = {
        "task_context_digest": context_digest(task_context),
        "benchmark_result_digest": context_digest(benchmark_result),
        "sensitivity_context_digest": context_digest(sensitivity_context),
        "economic_context_digest": context_digest(economic_context),
    }
    ok = True
    for key, expected_digest in expected.items():
        if artifact.get(key) != expected_digest:
            ok = False
            _violate(result, "ARTIFACT_CONTEXT_BINDING_MISMATCH", key)
    return ok


def _validate_model_adjudication_artifact(
    artifact: Any,
    *,
    benchmark_result: Mapping[str, Any],
    task_context: Mapping[str, Any],
    sensitivity_context: Mapping[str, Any],
    economic_context: Mapping[str, Any],
    result: dict[str, Any],
) -> bool:
    if artifact is None:
        _violate(result, "MODEL_ADJUDICATION_ARTIFACT_REQUIRED", "model_adjudication_artifact")
        return False
    if not _is_dict(artifact):
        _violate(result, "MODEL_ADJUDICATION_ARTIFACT_MALFORMED", "model_adjudication_artifact")
        return False

    required = {
        "artifact_id",
        "artifact_version",
        "adjudicator_class",
        "recommendation_basis",
        "sensitivity_assumption",
        "uncertainty_reason",
        "created_for_fallback_contract_only",
        "not_provider_permission",
        "not_execution_permission",
        "task_context_digest",
        "benchmark_result_digest",
        "sensitivity_context_digest",
        "economic_context_digest",
    }
    ok = True
    for field in sorted(required):
        if field not in artifact:
            ok = False
            _violate(result, "MODEL_ADJUDICATION_ARTIFACT_FIELD_REQUIRED", field)

    for field in (
        "created_for_fallback_contract_only",
        "not_provider_permission",
        "not_execution_permission",
    ):
        if field in artifact and not _literal_true(artifact[field]):
            ok = False
            _violate(result, "MODEL_ADJUDICATION_ARTIFACT_BOOLEAN_REQUIRED", field)

    if artifact.get("adjudicator_class") not in ALLOWED_ADJUDICATOR_CLASSES:
        ok = False
        _violate(result, "UNKNOWN_ADJUDICATOR_CLASS", "adjudicator_class")

    route_class = artifact.get("recommended_route_class")
    action = artifact.get("recommended_action")
    has_route_class = route_class is not None
    has_action = action is not None

    if not has_route_class and not has_action:
        ok = False
        _violate(result, "MODEL_ADJUDICATION_ARTIFACT_FIELD_REQUIRED", "recommended_route_class")

    if has_route_class and route_class not in ALLOWED_ROUTE_CLASSES:
        ok = False
        _violate(result, "UNKNOWN_ROUTE_CLASS", "recommended_route_class")

    if has_action and action not in ALLOWED_ARTIFACT_ACTIONS:
        ok = False
        _violate(result, "UNKNOWN_RECOMMENDED_ACTION", "recommended_action")

    if artifact.get("uncertainty_reason") not in ALLOWED_UNCERTAINTY_REASONS:
        ok = False
        _violate(result, "UNKNOWN_UNCERTAINTY_REASON", "uncertainty_reason")

    effective = _effective_sensitivity(sensitivity_context)
    artifact_sensitivity = artifact.get("sensitivity_assumption")
    effective_rank = _sensitivity_rank(effective)
    artifact_rank = _sensitivity_rank(artifact_sensitivity)
    if effective_rank is None:
        ok = False
        _violate(result, "UNKNOWN_SENSITIVITY_LEVEL", "effective_sensitivity")
    elif artifact_rank is None:
        ok = False
        _violate(result, "UNKNOWN_SENSITIVITY_LEVEL", "sensitivity_assumption")
    elif artifact_rank < effective_rank:
        ok = False
        _violate(result, "ARTIFACT_SENSITIVITY_DOWNGRADE", "sensitivity_assumption")

    if not _validate_artifact_binding(
        artifact,
        benchmark_result=benchmark_result,
        task_context=task_context,
        sensitivity_context=sensitivity_context,
        economic_context=economic_context,
        result=result,
    ):
        ok = False

    return ok


def _policy_adjust_route_class(
    route_class: str,
    *,
    result: dict[str, Any],
    task_context: Mapping[str, Any],
    sensitivity_context: Mapping[str, Any],
) -> tuple[str | None, str, str]:
    sensitivity = _effective_sensitivity(sensitivity_context)

    if sensitivity == "S2" and route_class.startswith("external:"):
        result["requires_sanitized_package"] = True
        return None, "produce_sanitized_S1_package", "sensitivity_policy_block"

    if sensitivity == "S3" and route_class.startswith("external:"):
        if _get(task_context, "local_model_sufficient") is True:
            return "local", "use_strongest_allowed_local_model", "sensitivity_policy_block"
        return None, "request_manual_abstraction", "sensitivity_policy_block"

    if sensitivity == "S4" and route_class.startswith("external:"):
        if _get(task_context, "task_is_trivial_deterministic") is True and _get(task_context, "requires_strategic_route_choice") is False:
            return "deterministic:no_llm", "use_model_adjudicated_route", "sensitivity_policy_block"
        if _has_valid_local_secret_policy(sensitivity_context):
            return "local", "use_strongest_allowed_local_model", "sensitivity_policy_block"
        return None, "request_manual_abstraction", "sensitivity_policy_block"

    if route_class in ALLOWED_ROUTE_CLASSES:
        return route_class, "use_model_adjudicated_route", ""

    if route_class == "produce_sanitized_S1_package":
        result["requires_sanitized_package"] = True
        return None, "produce_sanitized_S1_package", ""

    if route_class == "request_more_benchmark":
        result["requires_more_benchmark"] = True
        return None, "request_more_benchmark", ""

    if route_class in {"manual_abstraction_required", "request_model_adjudication"}:
        return None, (
            "request_manual_abstraction"
            if route_class == "manual_abstraction_required"
            else "request_model_adjudication"
        ), ""

    return None, "request_model_adjudication", "unknown_route_class"


def _apply_route_policy_result(
    result: dict[str, Any],
    *,
    route_class: str,
    task_context: Mapping[str, Any],
    sensitivity_context: Mapping[str, Any],
    basis: str,
    adjusted_basis: str,
    unadjusted_action: str,
    selection_grade: bool,
    evidence_quality: str,
) -> None:
    adjusted_route, action, policy_reason = _policy_adjust_route_class(
        route_class,
        result=result,
        task_context=task_context,
        sensitivity_context=sensitivity_context,
    )

    if policy_reason:
        result["routing_recommendation_adjusted_by_policy"] = True
        result["policy_adjustment_reason"] = policy_reason

    if adjusted_route is not None:
        result["policy_adjusted_route_class"] = adjusted_route
        _set_route(
            result,
            route_class=adjusted_route,
            action=action if policy_reason else unadjusted_action,
            kind="route_class",
            basis=adjusted_basis if policy_reason else basis,
            selection_grade=selection_grade,
            evidence_quality=evidence_quality,
        )
        return

    result["policy_adjusted_route_class"] = None
    if action == "produce_sanitized_S1_package":
        _set_non_route_action(
            result,
            action=action,
            kind="preprocessing_action",
            basis=adjusted_basis if policy_reason else basis,
        )
    elif action == "request_manual_abstraction":
        _set_non_route_action(
            result,
            action=action,
            kind="manual_abstraction_required",
            basis=adjusted_basis if policy_reason else basis,
            recommendation="manual_abstraction_required",
        )
    elif action == "request_more_benchmark":
        result["requires_more_benchmark"] = True
        _set_non_route_action(
            result,
            action=action,
            kind="request_more_benchmark",
            basis=basis,
        )
    else:
        _set_request_model_adjudication(result, adjusted_basis if policy_reason else basis)


def _apply_artifact_action_result(result: dict[str, Any], action: str) -> None:
    if action == "produce_sanitized_S1_package":
        result["requires_sanitized_package"] = True
        _set_non_route_action(
            result,
            action=action,
            kind="preprocessing_action",
            basis="model_adjudication_artifact",
        )
    elif action == "request_more_benchmark":
        result["requires_more_benchmark"] = True
        _set_non_route_action(
            result,
            action=action,
            kind="request_more_benchmark",
            basis="model_adjudication_artifact",
        )
    elif action == "request_manual_abstraction":
        _set_non_route_action(
            result,
            action=action,
            kind="manual_abstraction_required",
            basis="model_adjudication_artifact",
            recommendation="manual_abstraction_required",
        )
    elif action == "blocked_by_sensitivity_policy":
        _set_non_route_action(
            result,
            action=action,
            kind="blocked",
            basis="model_adjudication_artifact",
            recommendation="blocked_by_sensitivity_policy",
        )
    else:
        _set_request_model_adjudication(result, "model_adjudication_artifact")
    result["model_adjudication_artifact_valid"] = True
    result["model_adjudication_consumed"] = True


def evaluate_routing_recommendation_fallback_contract(
    benchmark_result: dict[str, Any],
    task_context: dict[str, Any],
    sensitivity_context: dict[str, Any],
    economic_context: dict[str, Any],
    model_adjudication_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate the no-provider routing recommendation fallback contract.

    This helper is pure and deterministic. It consumes a supplied artifact; it
    never creates, loads, calls, executes, searches for, or requests a model.
    """
    original_inputs = (
        copy.deepcopy(benchmark_result),
        copy.deepcopy(task_context),
        copy.deepcopy(sensitivity_context),
        copy.deepcopy(economic_context),
        copy.deepcopy(model_adjudication_artifact),
    )

    benchmark_result = benchmark_result if isinstance(benchmark_result, dict) else {}
    task_context = task_context if isinstance(task_context, dict) else {}
    sensitivity_context = sensitivity_context if isinstance(sensitivity_context, dict) else {}
    economic_context = economic_context if isinstance(economic_context, dict) else {}

    benchmark_winner = benchmark_result.get("benchmark_winner")
    benchmark_selection_valid = benchmark_result.get("benchmark_winner_selection_valid") is True
    uncertainty_reason = benchmark_result.get("benchmark_winner_basis") or task_context.get("uncertainty_reason") or "no_valid_benchmark"
    if uncertainty_reason not in ALLOWED_UNCERTAINTY_REASONS:
        uncertainty_reason = "no_valid_benchmark"

    result = _base_result(
        benchmark_winner=benchmark_winner,
        benchmark_winner_selection_valid=benchmark_selection_valid,
        uncertainty_reason=uncertainty_reason,
    )

    effective_sensitivity = _effective_sensitivity(sensitivity_context)
    if effective_sensitivity is None:
        _violate(result, "UNKNOWN_SENSITIVITY_LEVEL", "effective_sensitivity")
        _set_request_model_adjudication(result, "unknown_sensitivity_level")
        return result

    task_is_trivial = task_context.get("task_is_trivial_deterministic") is True
    strategic_choice = task_context.get("requires_strategic_route_choice") is True
    non_trivial_fallback = not (task_is_trivial and not strategic_choice)

    if benchmark_selection_valid:
        benchmark_route_class = _selected_benchmark_route_class(benchmark_result)
        if benchmark_route_class is None:
            _reject_missing_benchmark_route_class(result)
            return result

        _apply_route_policy_result(
            result,
            route_class=benchmark_route_class,
            task_context=task_context,
            sensitivity_context=sensitivity_context,
            basis="selection_grade_benchmark_winner",
            adjusted_basis="selection_grade_benchmark_winner_policy_adjusted",
            unadjusted_action="use_benchmark_winner",
            selection_grade=True,
            evidence_quality="selection_grade",
        )
        result["requires_user_confirmation"] = _confirmation_required(
            route_class=result["recommended_route_class"],
            action=result["recommended_action"],
            task_context=task_context,
            sensitivity_context=sensitivity_context,
            economic_context=economic_context,
        )
        assert (
            benchmark_result,
            task_context,
            sensitivity_context,
            economic_context,
            model_adjudication_artifact,
        ) == original_inputs
        return result

    if task_is_trivial and not strategic_choice:
        _set_route(
            result,
            route_class="deterministic:no_llm",
            action="use_model_adjudicated_route",
            kind="route_class",
            basis="trivial_deterministic_task",
            selection_grade=False,
            evidence_quality="partial",
        )
        result["model_adjudication_required"] = False
        result["requires_user_confirmation"] = _confirmation_required(
            route_class=result["recommended_route_class"],
            action=result["recommended_action"],
            task_context=task_context,
            sensitivity_context=sensitivity_context,
            economic_context=economic_context,
        )
        assert (
            benchmark_result,
            task_context,
            sensitivity_context,
            economic_context,
            model_adjudication_artifact,
        ) == original_inputs
        return result

    result["model_adjudication_required"] = non_trivial_fallback

    if model_adjudication_artifact is None:
        # Sensitivity-preserving no-artifact recommendations may still be more
        # useful than null while explicitly requesting adjudication.
        if effective_sensitivity == "S2":
            _set_non_route_action(
                result,
                action="produce_sanitized_S1_package",
                kind="preprocessing_action",
                basis="s2_raw_requires_sanitization_before_model_adjudication",
            )
            result["requires_sanitized_package"] = True
            result["model_adjudication_consumed"] = False
        elif effective_sensitivity in {"S3", "S4"}:
            _set_request_model_adjudication(result, "allowed_local_or_manual_model_adjudication_required")
        else:
            _set_request_model_adjudication(result, "model_adjudication_artifact_missing")
        return result

    artifact_valid = _validate_model_adjudication_artifact(
        model_adjudication_artifact,
        benchmark_result=benchmark_result,
        task_context=task_context,
        sensitivity_context=sensitivity_context,
        economic_context=economic_context,
        result=result,
    )
    result["model_adjudication_artifact_valid"] = artifact_valid
    result["model_adjudication_source"] = (
        model_adjudication_artifact.get("adjudicator_class")
        if isinstance(model_adjudication_artifact, dict)
        else "none"
    )

    if not artifact_valid:
        _set_request_model_adjudication(result, "model_adjudication_artifact_invalid")
        return result

    artifact_route = model_adjudication_artifact.get("recommended_route_class")
    result["artifact_recommended_route_class"] = artifact_route

    if artifact_route is not None:
        _apply_route_policy_result(
            result,
            route_class=artifact_route,
            task_context=task_context,
            sensitivity_context=sensitivity_context,
            basis="model_adjudication_artifact",
            adjusted_basis="model_adjudication_artifact_policy_adjusted",
            unadjusted_action="use_model_adjudicated_route",
            selection_grade=False,
            evidence_quality="model_adjudicated",
        )
        result["model_adjudication_consumed"] = True
    else:
        _apply_artifact_action_result(result, model_adjudication_artifact["recommended_action"])

    result["requires_user_confirmation"] = _confirmation_required(
        route_class=result["recommended_route_class"],
        action=result["recommended_action"],
        task_context=task_context,
        sensitivity_context=sensitivity_context,
        economic_context=economic_context,
    )

    # Invariant: confirmation and recommendation are not permission.
    result["provider_permission_granted"] = False
    result["network_permission_granted"] = False
    result["execution_permission_granted"] = False

    assert (
        benchmark_result,
        task_context,
        sensitivity_context,
        economic_context,
        model_adjudication_artifact,
    ) == original_inputs
    return result
