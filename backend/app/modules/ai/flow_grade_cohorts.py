from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.modules.ai.flow_grade_cohort_contracts import (
    ACCOUNTING_BASES,
    DISPATCH_QUALITY_BUCKETS,
    DISPATCH_STATES,
    EXECUTION_CLASSES,
    EXECUTION_COMPOSITIONS,
    GRADE_BUCKETS,
    PROVIDER_QUALITY_BUCKETS,
    USAGE_SOURCES,
    decimal_text,
    decimal_value,
    dispatch_quality,
    exclusion_reasons,
    execution_composition,
    provider_quality,
)
from app.modules.ai.flow_grade_cohort_distributions import numeric_distribution
from app.modules.ai.flow_grade_cohort_models import FlowGradeCohortRead
from app.modules.ai.flow_grade_cohort_store import load_cohort_rows

NON_PROVIDER_BASES = {
    "no_execution",
    "synthetic_not_economic",
    "local_compute_unpriced",
    "external_not_sent",
}
CONSERVATIVE_BASES = {
    "conservative_standard_input",
    "conservative_estimated_usage",
}


def get_flow_grade_cohort(
    *,
    workspace_id: str | None = None,
    task_kind: str | None = None,
    limit: int = 1000,
) -> FlowGradeCohortRead:
    rows = load_cohort_rows(
        workspace_id=workspace_id,
        task_kind=task_kind,
        limit=limit,
    )
    state_counts = _counts(
        ("complete", "partial_terminal", "failed_terminal", "cancelled_terminal")
    )
    grade_state_counts = _counts(("gradeable", "graded", "ungraded", "not_gradeable"))
    current_grade_counts = _counts(GRADE_BUCKETS)
    eligible_grade_counts = _counts(GRADE_BUCKETS)
    exclusion_counts: dict[str, int] = {}
    composition_counts = _counts(EXECUTION_COMPOSITIONS)
    dispatch_quality_counts = _counts(DISPATCH_QUALITY_BUCKETS)
    provider_quality_counts = _counts(PROVIDER_QUALITY_BUCKETS)
    execution_metrics = _metrics(EXECUTION_CLASSES)
    dispatch_metrics = _metrics(DISPATCH_STATES)
    usage_metrics = _metrics(USAGE_SOURCES)
    accounting_metrics = _metrics(ACCOUNTING_BASES)
    attempts_by_grade = _counts(GRADE_BUCKETS)
    spend_by_grade = {key: Decimal("0") for key in GRADE_BUCKETS}
    provider_mix: dict[str, int] = {}
    model_mix: dict[str, int] = {}
    route_mix: dict[str, int] = {}
    fallback_counts: dict[str, int] = {}
    continuation_counts: dict[str, int] = {}
    no_execution_reasons: dict[str, int] = {}
    input_token_values: list[int] = []
    output_token_values: list[int] = []
    latency_values: list[int] = []

    total_flow_spend = Decimal("0")
    total_attempt_spend = Decimal("0")
    eligible_spend = Decimal("0")
    eligible_flows = 0
    local_attempts = 0
    local_input_tokens = 0
    local_output_tokens = 0
    local_latency_ms = 0
    flows_with_local = 0
    local_unpriced_flows = 0
    synthetic_flows = 0
    legacy_flows = 0
    no_execution_attempts = 0
    external_not_sent = 0
    external_unknown = 0
    external_not_sent_spend_is_zero = True
    unknown_dispatch_uses_conservative_basis = True
    non_provider_bases_have_zero_external_spend = True

    for flow in rows.flows:
        flow_id = str(flow["id"])
        attempts = rows.attempts_by_flow.get(flow_id, [])
        state_counts[str(flow["state"])] += 1
        subject = rows.current_subject_by_flow.get(flow_id)
        event = (
            rows.latest_event_by_subject.get(str(subject["id"]))
            if subject is not None
            else None
        )
        grade = (
            str(event["grade"])
            if event is not None and event["action"] == "set"
            else "ungraded"
        )
        if grade not in current_grade_counts:
            grade = "ungraded"
        current_grade_counts[grade] += 1
        if subject is None:
            grade_state_counts["not_gradeable"] += 1
        else:
            grade_state_counts["gradeable"] += 1
            grade_state_counts["graded" if grade != "ungraded" else "ungraded"] += 1

        flow_spend = decimal_value(flow["external_provider_spend_usd_decimal"])
        total_flow_spend += flow_spend
        spend_by_grade[grade] += flow_spend
        all_classes = {
            _bucket(attempt["execution_class"], execution_metrics, "legacy_unknown")
            for attempt in attempts
        }
        invoked_classes = {
            _bucket(attempt["execution_class"], execution_metrics, "legacy_unknown")
            for attempt in attempts
            if bool(attempt["adapter_invoked"])
        }
        states = {
            _bucket(attempt["external_dispatch_state"], dispatch_metrics, "unknown")
            for attempt in attempts
        }
        composition_counts[execution_composition(invoked_classes)] += 1
        dispatch_quality_counts[dispatch_quality(states)] += 1
        provider_quality_counts[provider_quality(attempts)] += 1

        reasons = exclusion_reasons(
            flow=flow,
            attempts=attempts,
            current_subject_id=str(subject["id"]) if subject is not None else None,
        )
        for reason in reasons:
            exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
        if not reasons:
            eligible_flows += 1
            eligible_grade_counts[grade] += 1
            eligible_spend += flow_spend

        if "local_compute" in invoked_classes:
            flows_with_local += 1
        if bool(flow["local_compute_cost_unpriced"]):
            local_unpriced_flows += 1
        if bool(flow["synthetic_evidence_present"]) or "synthetic" in all_classes:
            synthetic_flows += 1
        if "legacy_unknown" in all_classes or any(
            attempt["accounting_basis"] == "legacy_unknown" for attempt in attempts
        ):
            legacy_flows += 1

        for attempt in attempts:
            attempts_by_grade[grade] += 1
            execution_class = _bucket(
                attempt["execution_class"], execution_metrics, "legacy_unknown"
            )
            dispatch_state = _bucket(
                attempt["external_dispatch_state"], dispatch_metrics, "unknown"
            )
            usage_source = _bucket(
                attempt["normalized_usage_source"], usage_metrics, "legacy_unknown"
            )
            accounting_basis = _bucket(
                attempt["accounting_basis"], accounting_metrics, "legacy_unknown"
            )
            attempt_spend = decimal_value(
                attempt["accounted_provider_spend_usd_decimal"]
            )
            total_attempt_spend += attempt_spend
            _add_metric(execution_metrics[execution_class], attempt, attempt_spend)
            _add_metric(dispatch_metrics[dispatch_state], attempt, attempt_spend)
            _add_metric(usage_metrics[usage_source], attempt, attempt_spend)
            _add_metric(accounting_metrics[accounting_basis], attempt, attempt_spend)
            input_token_values.append(_count(attempt["input_tokens"]))
            output_token_values.append(_count(attempt["output_tokens"]))
            latency_values.append(_count(attempt["latency_ms"]))

            invoked = bool(attempt["adapter_invoked"])
            if not invoked:
                no_execution_attempts += 1
                reason = str(
                    attempt["outcome_reason"]
                    or attempt["accounting_basis"]
                    or "unspecified"
                )
                no_execution_reasons[reason] = no_execution_reasons.get(reason, 0) + 1
            if execution_class == "local_compute" and invoked:
                local_attempts += 1
                local_input_tokens += _count(attempt["input_tokens"])
                local_output_tokens += _count(attempt["output_tokens"])
                local_latency_ms += _count(attempt["latency_ms"])
            if accounting_basis == "external_not_sent":
                external_not_sent += 1
                external_not_sent_spend_is_zero &= attempt_spend == 0
            if dispatch_state == "unknown":
                external_unknown += 1
                unknown_dispatch_uses_conservative_basis &= (
                    accounting_basis in CONSERVATIVE_BASES
                )
            if accounting_basis in NON_PROVIDER_BASES:
                non_provider_bases_have_zero_external_spend &= attempt_spend == 0
            _increment(provider_mix, attempt["provider_id"])
            _increment(model_mix, attempt["model_id"])
            _increment(route_mix, attempt["selected_route_class"])
            _increment(fallback_counts, attempt["fallback_index"], none_key="none")
            _increment(
                continuation_counts,
                attempt["continuation_index"],
                none_key="none",
            )

    terminal_flows = len(rows.flows)
    attempt_count = sum(len(values) for values in rows.attempts_by_flow.values())
    gradeable = grade_state_counts["gradeable"]
    graded = grade_state_counts["graded"]
    useful = eligible_grade_counts["useful"]
    spend_per_useful = eligible_spend / useful if useful else None
    return FlowGradeCohortRead(
        workspace_id=workspace_id,
        task_kind=task_kind,
        requested_limit=limit,
        truncated=rows.truncated,
        terminal_flow_count=terminal_flows,
        attempt_count=attempt_count,
        flow_state_counts=state_counts,
        grade_state_counts=grade_state_counts,
        current_grade_counts=current_grade_counts,
        grade_coverage=(graded / gradeable) if gradeable else None,
        deterministic_failure_rate=(
    state_counts["failed_terminal"] / terminal_flows
    if terminal_flows
    else None
),
        eligible_flow_count=eligible_flows,
        eligible_grade_counts=eligible_grade_counts,
        exclusion_reason_counts=exclusion_counts,
        execution_composition_counts=composition_counts,
        external_dispatch_quality_counts=dispatch_quality_counts,
        provider_accounting_quality_counts=provider_quality_counts,
        attempt_metrics_by_execution_class=_serialize_metrics(execution_metrics),
        attempt_metrics_by_dispatch_state=_serialize_metrics(dispatch_metrics),
        attempt_metrics_by_usage_source=_serialize_metrics(usage_metrics),
        attempt_metrics_by_accounting_basis=_serialize_metrics(accounting_metrics),
        attempt_counts_by_current_grade=attempts_by_grade,
        external_provider_spend_usd_total=decimal_text(total_flow_spend),
        external_provider_spend_usd_by_current_grade={
            key: decimal_text(value) for key, value in spend_by_grade.items()
        },
        eligible_external_provider_spend_usd_total=decimal_text(eligible_spend),
        external_provider_spend_per_useful_outcome_usd=(
            decimal_text(spend_per_useful) if spend_per_useful is not None else None
        ),
        total_economic_cost_per_useful_outcome_usd=None,
        local_attempt_count=local_attempts,
        local_input_tokens=local_input_tokens,
        local_output_tokens=local_output_tokens,
        local_latency_ms=local_latency_ms,
        flows_with_local_compute=flows_with_local,
        local_cost_unpriced_flow_count=local_unpriced_flows,
        synthetic_flow_count=synthetic_flows,
        legacy_ambiguous_flow_count=legacy_flows,
        no_execution_attempt_count=no_execution_attempts,
        no_execution_reason_counts=no_execution_reasons,
        external_not_sent_attempt_count=external_not_sent,
        external_unknown_attempt_count=external_unknown,
        revision_event_count=rows.revision_event_count,
        withdrawal_event_count=rows.withdrawal_event_count,
        invalid_subject_count=rows.invalid_subject_count,
        provider_mix=provider_mix,
        model_mix=model_mix,
        route_mix=route_mix,
        fallback_index_counts=fallback_counts,
        continuation_index_counts=continuation_counts,
        input_tokens_distribution=numeric_distribution(input_token_values),
        output_tokens_distribution=numeric_distribution(output_token_values),
        latency_ms_distribution=numeric_distribution(latency_values),
        reconciliation={
            "flow_states_match_terminal_flows": sum(state_counts.values())
            == terminal_flows,
            "grade_states_match_terminal_flows": (
                grade_state_counts["graded"]
                + grade_state_counts["ungraded"]
                + grade_state_counts["not_gradeable"]
            )
            == terminal_flows,
            "execution_composition_matches_terminal_flows": sum(
                composition_counts.values()
            )
            == terminal_flows,
            "dispatch_quality_matches_terminal_flows": sum(
                dispatch_quality_counts.values()
            )
            == terminal_flows,
            "provider_quality_matches_terminal_flows": sum(
                provider_quality_counts.values()
            )
            == terminal_flows,
            "execution_class_attempts_match_attempts": _metric_attempts(
                execution_metrics
            )
            == attempt_count,
            "dispatch_state_attempts_match_attempts": _metric_attempts(
                dispatch_metrics
            )
            == attempt_count,
            "usage_source_attempts_match_attempts": _metric_attempts(usage_metrics)
            == attempt_count,
            "accounting_basis_attempts_match_attempts": _metric_attempts(
                accounting_metrics
            )
            == attempt_count,
            "accounting_spend_matches_flow_spend": total_attempt_spend
            == total_flow_spend,
            "external_not_sent_spend_is_zero": external_not_sent_spend_is_zero,
            "unknown_dispatch_uses_conservative_basis": (
                unknown_dispatch_uses_conservative_basis
            ),
            "non_provider_bases_have_zero_external_spend": (
                non_provider_bases_have_zero_external_spend
            ),
        },
    )


def _counts(values: Iterable[str]) -> dict[str, int]:
    return {value: 0 for value in values}


def _metrics(values: Iterable[str]) -> dict[str, dict[str, object]]:
    return {
        value: {
            "attempts": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "reasoning_tokens": 0,
            "latency_ms": 0,
            "spend": Decimal("0"),
        }
        for value in values
    }


def _add_metric(
    metric: dict[str, object],
    attempt: dict[str, object],
    spend: Decimal,
) -> None:
    metric["attempts"] = int(metric["attempts"]) + 1
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "reasoning_tokens",
        "latency_ms",
    ):
        metric[key] = int(metric[key]) + _count(attempt[key])
    metric["spend"] = decimal_value(metric["spend"]) + spend


def _serialize_metrics(
    metrics: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for key, value in metrics.items():
        result[key] = {
            "attempts": value["attempts"],
            "input_tokens": value["input_tokens"],
            "output_tokens": value["output_tokens"],
            "cache_read_tokens": value["cache_read_tokens"],
            "reasoning_tokens": value["reasoning_tokens"],
            "latency_ms": value["latency_ms"],
            "external_provider_spend_usd_decimal": decimal_text(
                decimal_value(value["spend"])
            ),
        }
    return result


def _metric_attempts(metrics: dict[str, dict[str, object]]) -> int:
    return sum(int(value["attempts"]) for value in metrics.values())


def _count(value: object) -> int:
    return int(value or 0)


def _bucket(
    value: object,
    allowed: dict[str, object],
    fallback: str,
) -> str:
    key = str(value) if value is not None else fallback
    return key if key in allowed else fallback


def _increment(
    counts: dict[str, int],
    value: object,
    *,
    none_key: str | None = None,
) -> None:
    if value is None:
        if none_key is None:
            return
        key = none_key
    else:
        key = str(value)
    counts[key] = counts.get(key, 0) + 1
