# E4-A7-PRE-4-R2 Benchmark Fixture Schema Replay Harness

## Scope

- helper-only: yes
- offline-only: yes
- provider execution: no
- network execution: no
- SDK/API imports: no
- `.env` / secrets / API keys: no
- provider registry: no
- execution gateway: no
- schema/runtime wiring: no

## Delivered

- `scripts/router_policy_benchmark_replay.py`
- `tests/test_router_policy_benchmark_replay_harness.py`
- `tests/fixtures/routing_benchmarks/demo_replay_set.json`
- `docs/routing/BENCHMARK_FIXTURE_SCHEMA.md`
- `docs/routing/BENCHMARK_REPLAY_HARNESS.md`

## Contracts

- benchmark replay result is not provider permission
- benchmark winner is not provider permission
- only literal boolean `true`/`false` are valid booleans in fixtures
- concrete costs require auditable source reference and checked-at evidence
- partial or mixed-cost data cannot yield selection-grade `cost_per_success`
- candidate ranking requires complete comparable fixture coverage
- single-candidate replay cannot produce selection-grade winner
- exact ties produce `benchmark_winner=null`
- fixture and replay digests are deterministic and order-independent
- mixed suite identity is replay-invalid
- same fixture_id across candidates requires identical comparable fixture projection
- input_token_count is replay metadata, not fixture identity, unless canonical fixture-level counting exists
- fixture_definition_conflict blocks selection-grade benchmark_winner
- winner_blocking_reasons reports all winner-blocking reasons
- benchmark_winner_basis follows deterministic severity priority
- R2 does not implement fallback recommendation policy

## Verification

- `python -m pytest tests/test_router_policy_benchmark_replay_harness.py -q` -> `67 passed in 0.19s`
- `python -m pytest tests/test_router_policy_runtime_authority_chain_dry_run.py -q` -> `12 passed in 0.06s`
- `python -m pytest tests/test_router_policy_economic_execution_policy_boundary.py -q` -> `25 passed in 0.09s`
- `python -m pytest tests/test_router_policy_confirmed_execution_consumption_boundary.py -q` -> `23 passed in 0.26s`
- `python -m pytest tests/test_router_policy_confirmed_execution_activation_boundary.py -q` -> `17 passed in 0.08s`
- `python -m pytest tests/test_router_policy_confirmation_revalidation_boundary.py -q` -> `15 passed in 0.08s`
- `python -m pytest tests/test_router_policy_semantic_validator.py -q` -> `40 passed in 0.13s`
- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed in 0.07s`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed in 0.14s`
- `python -m pytest tests/test_router_policy_external_proposal_invariant.py tests/test_router_policy_external_egress_scope.py tests/test_router_policy_message_route_smoke.py tests/test_router_policy_semantic_validator.py tests/test_router_policy_external_egress_gate.py tests/test_router_policy_external_budget_gate.py -q` -> `324 passed in 1.00s`
- `python -m json.tool reports/E4-A7-PRE-4-BENCHMARK-FIXTURE-SCHEMA-REPLAY-HARNESS/summary.json` -> pass
- `git diff --check` -> clean
- `git diff --name-only` -> empty because files are untracked
- `git diff --cached --name-only` -> empty
- `git status --short --untracked-files=all` -> expected seven A7-PRE-4 files only

## Greps

- provider/network grep -> historical docs/tests/probes plus A7-PRE-4 negative assertions; no new runtime provider/network wiring
- env/secrets grep -> historical docs/tests/probes plus A7-PRE-4 report denial text; no new env or secret handling
- permission/runtime grep -> A7-PRE-4 docs/report boundary text plus existing historical docs/tests; no `routing_recommendation` implementation
