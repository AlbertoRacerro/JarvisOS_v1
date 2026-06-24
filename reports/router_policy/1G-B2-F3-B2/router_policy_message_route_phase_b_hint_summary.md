# 1G-B2-F3-B2 - Message Route Phase B Hint Bridge Flag

Start HEAD: `af1546995adcd7335ab90de67713789555c80951`

## Integration

Added explicit `--use-phase-b-hints` to the A5 message-route smoke path.

Order:

```text
message
-> A5 smoke builder / Phase A overlay / A5-R1 operational gates
-> optional B1 Phase B RouterHint bridge
-> RouterPolicy decision
-> semantic validator
-> A3 safe-local guard
-> local responder only if safe
```

The bridge is applied after the A5 builder and operational gates, and before
the A5 structural check, RouterPolicy decision, semantic validator, and A3
safe-local guard.

## A5 Stub Compatibility

A5 default `phase_b_soft_proposal` now carries the complete B1-compatible
benign field set:

- `summary_short`
- `project_bucket`
- `primary_domain`
- `domain_tags`
- `storage_relevance`
- `usefulness_for_future_review`
- `possible_memory_card_type`
- `soft_reason_code`
- `brief_rationale`
- `suggested_followup_question`
- `soft_uncertain_fields`

B1 derives `high` quality on the default A5 benign stub and maps it to
`router_hint.task_type="answer"` and `action_hint.requested_action_type="answer"`
with no side effects.

## Observed Behavior

- default behavior without `--use-phase-b-hints`: unchanged
- `--use-phase-b-hints` alone: does not execute
- benign `--assume-public-simple --use-phase-b-hints --run-local`: executes
- technical/scientific Phase B hint: enriched, then blocked by A3 safe-local
  guard when scientific-depth routing is not safe-local executable
- `source_candidate`: becomes more conservative with review/current-info/file-context
- Phase A hard gates: dominate Phase B hints
- A5-R1 operational gates: dominate Phase B hints
- baseline non-executable paths: remain non-executable
- CLI output: includes `use_phase_b_hints_used`, remains redacted
- B1 bridge failure: fails closed with `phase_b_hint_bridge_failed`

## Context Metadata

`context_metadata` extra keys are compatible. The RouterPolicyInput schema
permits additional metadata properties and the A5 structural validator checks
only the required metadata boolean fields.

B1 metadata keys:

- `router_hint_source`
- `phase_b_router_hint_applied`
- `phase_b_router_hint_reason`
- `phase_b_quality_derived`

## Tests

- `python -m unittest tests.test_router_policy_message_route_smoke`
- `python -m unittest tests.test_router_policy_hint_bridge_probe`
- `python -m unittest tests.test_router_policy_local_responder`
- `python -m unittest tests.test_router_policy_local_route_probe`
- `python -m unittest tests.test_router_policy_decision_probe`
- `python -m unittest tests.test_router_policy_semantic_validator`
- `python -m unittest discover -s tests`

All passed.

## Boundary

No production chat, live Qwen/Gemma/Ollama classification, external provider
calls, tools, MCP, browser, terminal, memory runtime, retrieval runtime,
backend routes, frontend UI, DB schema, workers, hooks, or BlueRev modeling.

## Residual Risks

- A5 remains smoke-only, not a production Phase A/B normalizer.
- `--assume-public-simple` remains required for benign local answer smoke.
- B1 routing hints are heuristic and remain subject to A3.
- B1 is a bridge over existing Phase B soft-review fields, not a full routing
  classifier.

Recommended next milestone:

```text
1G-B2-F3-B2-R - Message Route Phase B Hint Bridge Audit
```
