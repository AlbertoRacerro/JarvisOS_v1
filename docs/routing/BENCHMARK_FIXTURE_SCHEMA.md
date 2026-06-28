# Benchmark Fixture Schema - A7-PRE-4-R1

This schema is offline-only and benchmark-only. Fixture records are not runtime authority and cannot grant provider, network, or execution permission.

## Required record fields

```text
benchmark_suite_id
suite_version
fixture_id
fixture_version
fixture_record_digest
fixture_set_digest
replay_set_digest
task_type
sensitivity_level
intelligence_level
allowed_route_class
candidate_label
candidate_class
input_digest
input_token_count
output_token_count
total_token_count
estimated_cost
cost_currency
cost_source
cost_status
source_url or source_note when estimated_cost is present
source_checked_at or source_checked_at_note when estimated_cost is present
expected_outcome
observed_outcome
success
success_basis
failure_reason
tests_passed
tests_failed
human_review_required
retry_count
tool_call_count
cache_status
context_size_bucket
history_allowed
created_for_benchmark_only
not_runtime_authority
```

## Hard schema rules

- `created_for_benchmark_only` must be literal `true`.
- `not_runtime_authority` must be literal `true`.
- Boolean fields must be literal booleans, not truthy strings or numbers.
- Identity fields must be non-empty strings.
- Count fields must be finite non-negative integers.
- `estimated_cost` must be finite non-negative number or `null`.
- `total_token_count` must equal `input_token_count + output_token_count`.
- `success_basis` is required and must be one of `stored_replay_label`, `unit_tests`, `human_review`, or `deterministic_rule`.
- `success=true` must not have `failure_reason`.
- `success=false` must have a non-empty `failure_reason`.

## Cost consistency

If `estimated_cost` is `null`:

```text
cost_status == unavailable
```

If `estimated_cost` is not `null`:

```text
cost_currency required
cost_source required
cost_status in verified/estimated/unverified
source_url or source_note required
source_checked_at or source_checked_at_note required
```

Unknown costs remain `null`. This slice must not invent prices, source URLs, model claims, context limits, or exchange rates.

## Digest rules

- `fixture_record_digest` is computed from the full replay record excluding digest fields.
- `fixture_set_digest` is computed from comparable fixture/task/input/expected fields only, excluding candidate/result/cost fields.
- `replay_set_digest` is computed from full replay records excluding digest fields.
- Digests use canonical JSON with sorted keys and stable ordering.
- Filesystem traversal order must not affect digests.

## Fixture comparability

For the same `fixture_id`, every valid candidate record must share an identical comparable fixture projection.

Comparable fixture projection includes:

```text
benchmark_suite_id
suite_version
fixture_id
fixture_version
task_type
sensitivity_level
intelligence_level
allowed_route_class
input_digest
expected_outcome
created_for_benchmark_only
not_runtime_authority
context_size_bucket
history_allowed
```

Comparable fixture projection excludes candidate, result, cost, replay, retry, tool-call, and token-count metadata.

`input_token_count` is replay metadata, not fixture identity, unless a future slice defines and documents canonical fixture-level counting.

A `FIXTURE_DEFINITION_CONFLICT` blocks selection-grade `benchmark_winner`.

## Non-authority boundary

A fixture, replay result, benchmark winner, or cost metric is not provider permission, network permission, or execution permission.
