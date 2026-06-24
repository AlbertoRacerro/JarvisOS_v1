# 1G-B2-F3-B3-R1 - Default Phase B hint bridge malformed-input audit

Start HEAD: `63ade8c7bdf06c1f459b59618b7fc22221331ba4`

## Runtime Patch

Runtime patch required: true.

A5 now structurally validates the builder output before applying the default-on
B1 Phase B hint bridge.

Reason: B1 must not get an opportunity to repair malformed safety-critical
fields into executable-safe values before A5 rejects them.

## Validation Boundary

- pre-B1 validation: structural boundary proving builder or future producer
  output is valid enough to hand to B1.
- B1: advisory Phase B RouterHint bridge, not a production normalizer.
- post-B1 validation: structural check after B1 enrichment and before
  RouterPolicy/A3.

The same private A5 structural validator is used before and after B1. This is
acceptable for the current smoke path because the A5 builder emits a complete
structurally valid `RouterPolicyInput`.

Safety-critical fields include at least:

- Phase A hard-gate booleans
- action execution-risk booleans
- provider/user/budget policy critical fields
- router fields required before B1

Do not treat schema-valid, structurally valid, model-produced, or
Phase-B-enriched output as semantically safe.

Execution still requires deterministic hard gates, operational-intent gates,
`--assume-public-simple` in smoke, validator-valid RouterPolicy decision
output, the A3 safe-local guard, and an injected responder or explicit
`--run-local`.

## Future Live Phase B Boundary

Future live/per-message Phase B producer output must be structurally valid
before B1 consumes it. Malformed live producer output must fail closed before B1
or inside B1.

B1 must not normalize arbitrary raw model output into valid RouterPolicy input.
Qwen/Phase B output is advisory only and must not authorize execution, provider
calls, tool/MCP/browser/terminal actions, memory writes, retrieval, route
selection by itself, or removal of `--assume-public-simple`.

Partial or greedy Phase B output must go through a separate deterministic
adapter/validator layer before reaching B1.

## Anti-Mutation Result

- B1/A5 mutated original malformed input in-place: false
- `_RUN_LOCAL_ROUTE` reached for any malformed case: false
- any malformed input executed: false
- original mutable builder outputs retained corrupted values: true
- deep-copy before/after checks used: true

## Failure Point By Case

| case | reason | failure point | original corrupted value preserved | `_RUN_LOCAL_ROUTE` reached | executed |
|---|---|---|---:|---:|---:|
| malformed action/router | `invalid_router_policy_input` | `pre_bridge_structural_validation_failed` | true | false | false |
| malformed Phase A hard-gate bool | `invalid_router_policy_input` | `pre_bridge_structural_validation_failed` | true | false | false |
| malformed provider policy | `invalid_router_policy_input` | `pre_bridge_structural_validation_failed` | true | false | false |
| malformed Phase B domain tags | `invalid_router_policy_input` | `pre_bridge_structural_validation_failed` | true | false | false |

## Malformed Phase A / Policy Result

- `phase_a_signals.contains_secret_or_credential = "false"`: rejected before
  B1, not executed, `_RUN_LOCAL_ROUTE` not reached, original value preserved.
- `provider_policy.allowed_provider_tiers = "LOCAL_FAST"`: rejected before B1,
  not executed, `_RUN_LOCAL_ROUTE` not reached, original value preserved.

## Tests

- `python -m unittest tests.test_router_policy_message_route_smoke`
- `python -m unittest tests.test_router_policy_hint_bridge_probe`
- `python -m unittest tests.test_router_policy_local_responder`
- `python -m unittest tests.test_router_policy_local_route_probe`
- `python -m unittest tests.test_router_policy_decision_probe`
- `python -m unittest tests.test_router_policy_semantic_validator`
- `python -m unittest discover -s tests`
- `git diff --check`
- focused runtime grep

## Boundary

No model calls, external provider runtime, tool/MCP runtime, browser/terminal
runtime, memory/retrieval runtime, file-write runtime, backend/frontend/DB
changes, workers/hooks, or BlueRev behavior were added.

Recommended next milestone:

```text
1G-B2-F3-B3-R2 - Default Phase B hint bridge audit follow-up
```
