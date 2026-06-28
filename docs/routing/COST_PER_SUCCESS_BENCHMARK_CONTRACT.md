# Cost Per Success Benchmark Contract

## Status

This document defines an offline benchmark contract only.

It is not runtime authority.
It does not grant provider permission.
It does not wire provider execution.

## Purpose

Future model or provider-family selection must be informed by benchmarked `cost_per_success`, not by list price alone.

Benchmark selection runs only after:

- sensitivity classification
- deterministic sanitization, if required
- egress policy
- confirmation chain
- allow_once consumption
- economic envelope

## Selection Principle

Token price alone is not selection authority.

Selection authority in this slice is:

- policy pass first
- economic envelope pass second
- offline benchmark `cost_per_success` among the candidate pool third

Policy violations count as failures.

## Minimum Metrics

At minimum, benchmark rows and reports must define:

- `cost_per_success`
- `tokens_to_accepted_patch`
- `tests_pass_after_patch_rate`
- `regression_escape_rate`
- `false_positive_review_rate`
- `retry_count_to_success`
- `human_minutes_saved`
- `cache_sensitivity`
- `context_size_sensitivity`

## Candidate Pools

Candidate pools remain docs-only in this slice.

Examples:

- `cheap_cloud_worker`
- `pre_frontier_cloud`
- `frontier_adjudicator_pool`

Concrete model names may appear only in docs/offline candidate material.

## Envelope Fields

Future envelopes must distinguish at least:

- `max_input_tokens`
- `max_output_tokens`
- `max_context_tokens`
- `max_retrieved_chunks`
- `max_attachment_bytes`
- `history_allowed`
- `retry_cap`
- `tool_call_cap`
- `fallback_allowed`

These are conceptual contract fields here, not runtime code changes.

## Benchmark Row Contract

Each future benchmark row should capture:

- task identifier
- task type
- sensitivity class
- sanitized package identifier, if any
- intelligence level
- expected policy route class
- candidate provider class
- candidate model name
- estimated cost inputs
- benchmark result
- success label
- policy-pass label
- notes on failures or retries

## Baselines

Each benchmark report should compare against:

- always-cheap baseline
- always-frontier baseline
- random baseline when useful
- oracle upper bound

JarvisOS should also compare route-class usage against success and policy-pass outcomes.

## Threshold and Knee Selection

Threshold or knee selection is an offline benchmark activity only.

It may use concepts inspired by Wayfinder and RouteLLM, but it must not become runtime routing authority before policy and consent boundaries.

Chosen operating points should record:

- benchmark dataset version
- candidate pool version
- cost assumptions
- success definition
- policy-pass definition
- selected threshold or knee rationale

## Pricing Data Rules

Pricing and context-limit data must be treated as non-authoritative until rechecked and benchmarked.

If candidate data is stored in JSON:

- unknown numeric fields stay `null`
- `price_status` must explain verification state
- `benchmark_status` must explain whether offline benchmark was run
- `runtime_status` must remain docs-only until a future runtime milestone

## History / Retry / Tool / Fallback Policy

Benchmarks must record the effect of:

- history on or off
- retry caps
- tool-call caps
- fallback allowed or disabled

These settings affect cost and success, so benchmark reports must not collapse them into a single opaque score.

## 1M Context Clarification

If a candidate claims 1M context, document it as maximum model capacity only.

It is not:

- default budget
- default context allocation
- default route authority
- permission to send larger inputs

## Runtime Boundary

This contract does not:

- add provider registry runtime
- add execution gateway runtime
- add API keys or `.env` handling
- add network calls
- add SDK imports
- add A8 or A9 logic
