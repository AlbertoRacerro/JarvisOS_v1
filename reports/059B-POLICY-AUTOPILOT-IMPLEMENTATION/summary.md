# 059b policy autopilot implementation

## Status

Implementation started from merged definition commit
`bd31dae42c43a2ec052ae614a5a07a0dbdd37d94`.

The branch remains fail-closed. No new external execution is authorized until the
entire implementation contract is complete, reviewed, tested, and merged.

## Delivery order

1. strict egress-policy configuration and concrete provider/model pricing;
2. additive migration and typed persistence for prompt derivatives, packets,
   decisions, reservations, tickets, attempts, audit items, and workspace policy;
3. deterministic policy, digest, sampling, reservation, and ticket services;
4. bounded 059a sanitizer-provenance extension;
5. prompt/manual-context authority and local-only sanitizer orchestration;
6. per-binding shared-spine enforcement and independent fallback evaluation;
7. ticket-ID-only confirmation API and minimal compatibility UI wiring;
8. adversarial, concurrency, migration, regression, and full-suite verification.

## Hard constraints

- no packet body before effective S0/S1 eligibility;
- no model-backed sanitizer outside local-only `run_ai_task` / `ai_jobs`;
- no hidden adapter retries;
- immutable decisions and attempts; mutable reservations only through CAS lifecycle;
- concrete provider/model pricing from the existing provider registry;
- no second gateway, usage ledger, sensitivity authority, worker, vector store,
  conversation engine, or Hermes runtime;
- merged 059a behavior remains backward compatible;
- real project-data external dogfood remains disabled until merge.

## Evidence

This report will be updated with exact changed-file scope, migrations, focused tests,
full backend results, BLUECAD proof, review findings, and final lifecycle state.
