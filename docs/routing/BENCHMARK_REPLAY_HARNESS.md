# Benchmark Replay Harness - A7-PRE-4-R1

The replay harness evaluates stored offline fixture records only. It does not call models, providers, network services, tools, or runtime registries.

## Responsibilities

The harness computes deterministic replay metrics from fixture data:

- validity counts
- success rates with denominators
- test pass rates with denominators
- cost coverage
- partial non-authoritative cost-per-success
- selection-grade cost-per-success only when cost data is complete and comparable
- candidate coverage
- fixture and replay digests
- benchmark winner only when comparison is valid

## Invalid fixture behavior

Invalid fixture records are excluded from aggregate success/cost/token metrics. If any record is invalid, duplicate, or the replay set mixes suite identities, `replay_valid=false`.

The result reports:

```text
invalid_fixtures
invalid_fixture_ids
duplicate_fixture_records
replay_set_violations
fixture_definition_conflicts
winner_blocking_reasons
```

The same `fixture_id` across candidates requires the same comparable fixture projection. A different `input_digest`, `expected_outcome`, `sensitivity_level`, `task_type`, or other comparable field creates `FIXTURE_DEFINITION_CONFLICT` and blocks winner selection.

`input_token_count` is replay metadata for this slice. Candidate-specific token counting differences alone must not create `FIXTURE_DEFINITION_CONFLICT`.

## Winner rules

`benchmark_winner` may be `null`. This is valid behavior when data does not support selection.

A selection-grade winner requires:

```text
replay_valid == true
cost_data_complete == true
mixed_cost_currencies == false
candidate_fixture_coverage_complete == true
candidate_count >= 2
same benchmark_suite_id
same suite_version
no exact tie on selection metric
```

A single-candidate replay is a baseline, not a comparison, so it cannot produce `benchmark_winner_selection_valid=true`.

Ties must produce `benchmark_winner=null` and `benchmark_winner_selection_valid=false`.

When multiple winner-blocking reasons exist, `winner_blocking_reasons` reports all of them and `benchmark_winner_basis` follows this priority:

```text
invalid_fixtures
fixture_definition_conflict
mixed_suite_or_version
candidate_fixture_coverage_incomplete
duplicate_fixture_records
mixed_currency_without_conversion
cost_data_incomplete
insufficient_candidate_count
tie_on_cost_per_success
```

## Scope boundary

A7-PRE-4-R1 does not implement routing fallback policy. Operational `routing_recommendation` fallback belongs to A7-PRE-5 and must remain separate from benchmark winner selection.

A7-PRE-4-R2 also does not implement fallback recommendation policy.
