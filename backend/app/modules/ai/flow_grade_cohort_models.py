from __future__ import annotations

from pydantic import BaseModel, Field


class GradeAttemptMetricRead(BaseModel):
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    reasoning_tokens: int = 0
    latency_ms: int = 0
    external_provider_spend_usd_decimal: str = "0"


class NumericDistributionRead(BaseModel):
    count: int = 0
    minimum: int | None = None
    p50: int | None = None
    p95: int | None = None
    maximum: int | None = None


class GradeCohortReconciliationRead(BaseModel):
    flow_states_match_terminal_flows: bool
    grade_states_match_terminal_flows: bool
    execution_composition_matches_terminal_flows: bool
    dispatch_quality_matches_terminal_flows: bool
    provider_quality_matches_terminal_flows: bool
    execution_class_attempts_match_attempts: bool
    dispatch_state_attempts_match_attempts: bool
    usage_source_attempts_match_attempts: bool
    accounting_basis_attempts_match_attempts: bool
    accounting_spend_matches_flow_spend: bool
    external_not_sent_spend_is_zero: bool
    unknown_dispatch_uses_conservative_basis: bool
    non_provider_bases_have_zero_external_spend: bool


class FlowGradeCohortRead(BaseModel):
    workspace_id: str | None = None
    task_kind: str | None = None
    requested_limit: int
    truncated: bool
    terminal_flow_count: int
    attempt_count: int
    flow_state_counts: dict[str, int] = Field(default_factory=dict)
    grade_state_counts: dict[str, int] = Field(default_factory=dict)
    current_grade_counts: dict[str, int] = Field(default_factory=dict)
    grade_coverage: float | None = None
    current_failed_grade_rate: float | None = None
    eligible_flow_count: int
    eligible_grade_counts: dict[str, int] = Field(default_factory=dict)
    exclusion_reason_counts: dict[str, int] = Field(default_factory=dict)
    execution_composition_counts: dict[str, int] = Field(default_factory=dict)
    external_dispatch_quality_counts: dict[str, int] = Field(default_factory=dict)
    provider_accounting_quality_counts: dict[str, int] = Field(default_factory=dict)
    attempt_metrics_by_execution_class: dict[str, GradeAttemptMetricRead] = Field(
        default_factory=dict
    )
    attempt_metrics_by_dispatch_state: dict[str, GradeAttemptMetricRead] = Field(
        default_factory=dict
    )
    attempt_metrics_by_usage_source: dict[str, GradeAttemptMetricRead] = Field(
        default_factory=dict
    )
    attempt_metrics_by_accounting_basis: dict[str, GradeAttemptMetricRead] = Field(
        default_factory=dict
    )
    attempt_counts_by_current_grade: dict[str, int] = Field(default_factory=dict)
    external_provider_spend_usd_total: str
    external_provider_spend_usd_by_current_grade: dict[str, str] = Field(
        default_factory=dict
    )
    eligible_external_provider_spend_usd_total: str
    external_provider_spend_per_useful_outcome_usd: str | None = None
    total_economic_cost_per_useful_outcome_usd: None = None
    local_attempt_count: int
    local_input_tokens: int
    local_output_tokens: int
    local_latency_ms: int
    flows_with_local_compute: int
    local_cost_unpriced_flow_count: int
    synthetic_flow_count: int
    legacy_ambiguous_flow_count: int
    no_execution_attempt_count: int
    no_execution_reason_counts: dict[str, int] = Field(default_factory=dict)
    external_not_sent_attempt_count: int
    external_unknown_attempt_count: int
    revision_event_count: int
    withdrawal_event_count: int
    invalid_subject_count: int
    provider_mix: dict[str, int] = Field(default_factory=dict)
    model_mix: dict[str, int] = Field(default_factory=dict)
    route_mix: dict[str, int] = Field(default_factory=dict)
    fallback_index_counts: dict[str, int] = Field(default_factory=dict)
    continuation_index_counts: dict[str, int] = Field(default_factory=dict)
    input_tokens_distribution: NumericDistributionRead
    output_tokens_distribution: NumericDistributionRead
    latency_ms_distribution: NumericDistributionRead
    reconciliation: GradeCohortReconciliationRead
