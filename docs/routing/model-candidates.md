# Model Candidates

## Status

This file is docs-only.

It is not runtime authority.
It is not provider permission.
It is not a registry.

## Candidate Roles

Concrete names below are offline benchmark candidates only.

They may appear in docs and future offline candidate files.
They must not enter runtime authority logic in this slice.

## DeepSeek Entry Policy

`deepseek-v4-flash`

- candidate role: cheap sanitized cloud worker/reviewer
- allowed data class: `S0` / `S1` after deterministic redaction
- runtime status: docs/benchmark candidate only

`deepseek-v4-pro`

- candidate role: pre-frontier cost reducer for large sanitized reasoning/coding
- allowed data class: `S0` / `S1` after deterministic redaction
- runtime status: docs/benchmark candidate only

## Candidate Pools

### cheap_cloud_worker

- `deepseek-v4-flash`
- `kimi-k2.7-code`

### pre_frontier_cloud

- `deepseek-v4-pro`
- `glm-5.2`
- `kimi-k2.7-code`

### frontier_adjudicator_pool

- `claude-opus-4.8`
- `gpt-5.5`

## Pool Rules

- no single `frontier_primary` is frozen in this slice
- frontier selection requires explicit escalation
- frontier selection requires confirmed economic envelope
- frontier selection requires benchmark-supported selection
- benchmark winner alone is not provider permission
- list price alone is not selection authority

## Abstract Runtime Mapping

Runtime classes remain abstract only:

- `local`
- `external:cheap`
- `external:scientific_medium`
- `external:frontier`

Concrete candidates map into those abstract classes only after future benchmark and runtime milestones.

## Data and Pricing Status

No concrete price, context-limit, or benchmark-success value is introduced here.

Until sourced and benchmarked, candidate pricing and capacity remain:

- docs-only
- non-authoritative
- subject to re-benchmark

## Inclusion Notes

- Wayfinder is included as an offline routing architecture reference.
- RouteLLM is included as an offline economic routing and threshold-evaluation reference.
- DeepSparkInference is included as a local inference capability and benchmark-reporting reference.
- None of these references is vendored or wired into runtime.
