# 1G-B2-F3-B3-R1 - Default Phase B hint bridge malformed-input audit

Start HEAD: `63ade8c7bdf06c1f459b59618b7fc22221331ba4`

## Runtime Patch

Runtime patch required: true.

A5 now structurally validates the builder output before applying the default-on
B1 Phase B hint bridge.

Reason: B1 must not get an opportunity to repair malformed safety-critical
fields into executable-safe values before A5 rejects them.

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
