# Routing Recommendation Fallback Contract

A7-PRE-5 defines a helper-only, no-provider contract for operational routing
recommendations when `benchmark_winner` is null or non-selection-grade.

## Separation

- `benchmark_winner`: deterministic, benchmark-supported, selection-grade winner
  label for audit.
- `benchmark_winner_route_class`: explicit validated route class for a
  selection-grade benchmark winner.
- `routing_recommendation`: operational recommendation produced from either a
  selection-grade benchmark winner or a supplied model adjudication artifact.
- `provider_permission`: never granted by this contract.

`routing_recommendation` is not provider permission, network permission, or
execution permission.

`benchmark_winner` is not a route class. A selection-grade benchmark winner may
be used only when `benchmark_winner_route_class` or another explicit validated
route-class field is present.

## Model adjudication artifact

The helper consumes a supplied `model_adjudication_artifact`. It never creates,
calls, loads, executes, searches for, or requests a model/adjudicator.

The artifact must bind to the current context using deterministic canonical JSON
digests for:

- `task_context_digest`
- `benchmark_result_digest`
- `sensitivity_context_digest`
- `economic_context_digest`

Digest inputs exclude digest fields and must not include timestamps, filesystem
paths, runtime environment data, or nondeterministic ordering.

## Route class vs action

`recommended_route_class` may only be a real route class:

- `local`
- `external:cheap`
- `external:scientific_medium`
- `external:frontier`
- `deterministic:no_llm`
- `public_query_only`
- `blocked_or_public_query_only`

Request/preprocessing/blocking/manual actions use `recommended_action` and may
set `recommended_route_class` to null. Model adjudication artifacts must not put
action values such as `produce_sanitized_S1_package`,
`request_more_benchmark`, or `request_model_adjudication` into
`recommended_route_class`.

## Sensitivity policy

S2/S3/S4 raw external egress is blocked. Benchmark winner and artifact
recommendations are policy-adjusted before becoming final
`routing_recommendation`.

All external route classes are policy-adjusted for S2/S3/S4 raw contexts:

- `external:cheap`
- `external:scientific_medium`
- `external:frontier`

S4 local model recommendations require local secret policy:

- `local_secret_handling_allowed is true`
- `history_allowed is false`
- `external_tool_calls_allowed is false`
- `logging_allowed_for_raw_secret is false`

## Confirmation

Confirmation is rare and does not grant permission. It is required for
`external:frontier`, high budget risk, public/irreversible action, or raw
external egress request.

Confirmation does not bypass sensitivity policy. S2/S3/S4 raw external
recommendations cannot survive merely because `requires_user_confirmation` is
true.

## Out of scope

- provider execution
- network execution
- SDK/API imports
- `.env`/secrets/API keys
- provider registry runtime
- execution gateway
- runtime model calls
- A8/A9
