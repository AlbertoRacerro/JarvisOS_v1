# E4-A7-PRE-5-R1 Routing Recommendation Fallback Contract

## Scope

- helper-only: yes
- provider execution: no
- network execution: no
- SDK/API imports: no
- `.env` / secrets / API keys: no
- provider registry runtime: no
- execution gateway: no
- backend runtime wiring: no
- runtime model call: no

## Delivered

- `scripts/router_policy_routing_recommendation_fallback.py`
- `tests/test_router_policy_routing_recommendation_fallback_contract.py`
- `docs/routing/ROUTING_RECOMMENDATION_FALLBACK_CONTRACT.md`

## Contract

- `benchmark_winner` may be null.
- `benchmark_winner` is an audit label, not a route class.
- `benchmark_winner_route_class` must be explicit and validated before a
  selection-grade benchmark winner can become a recommendation.
- `routing_recommendation` is present for non-trivial fallback.
- Non-trivial fallback requires a supplied model adjudication artifact or a
  `request_model_adjudication` recommendation.
- The helper consumes artifact input only; it never generates/calls models.
- `routing_recommendation` is not provider/network/execution permission.
- Model artifact `recommended_route_class` accepts only real route classes.
- Model artifact action recommendations use `recommended_action` with
  `recommended_route_class` null.
- Artifact recommendation is separated from policy-adjusted final recommendation.
- S2/S3/S4 external raw recommendations are blocked or policy-adjusted for
  `external:cheap`, `external:scientific_medium`, and `external:frontier`.
- Confirmation does not grant permission or bypass sensitivity policy.

## R1 fixes

- Fixed selection-grade benchmark winner sensitivity policy bypass.
- Applied sensitivity policy to every external route class.
- Prevented S2/S3/S4 raw external recommendation survival from benchmark winner
  and model artifact paths.
- Enforced explicit benchmark winner route class.
- Enforced route/action separation in model adjudication artifacts.
- Preserved helper-only scope with no provider/network/runtime wiring.

## Verification

R1 validation:

- `python -m pytest tests/test_router_policy_routing_recommendation_fallback_contract.py -q` -> `44 passed`
- `python -m pytest tests/test_router_policy_benchmark_replay_harness.py -q` -> `67 passed`
- `python -m pytest tests/test_router_policy_runtime_authority_chain_dry_run.py -q` -> `12 passed`
- `python -m pytest tests/test_router_policy_economic_execution_policy_boundary.py -q` -> `25 passed`
- `python -m pytest tests/test_router_policy_confirmed_execution_consumption_boundary.py -q` -> `23 passed`
- `python -m pytest tests/test_router_policy_confirmed_execution_activation_boundary.py -q` -> `17 passed`
- `python -m pytest tests/test_router_policy_confirmation_revalidation_boundary.py -q` -> `15 passed`
- `python -m pytest tests/test_router_policy_semantic_validator.py -q` -> `40 passed`
- `python -m pytest tests/test_router_policy_canonical_digest.py -q` -> `14 passed`
- `python -m pytest tests/test_router_policy_confirmation_digest_binding.py -q` -> `5 passed`
- router regression bundle -> `324 passed`
- `python -m json.tool .../summary.json` -> valid before R1 result update
- `git diff --check` -> clean
- greps -> noisy pre-existing repo matches; A7-PRE-5 matches are negative assertions,
  tests, or explanatory text only
