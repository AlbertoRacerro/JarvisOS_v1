# 136 ROUTE-DEFAULT-CONSISTENCY-1 — readiness

## Decision

READY only when this document, the full spec, and a live `docs/specs/STATUS.md` row for 136 are merged with status `ready`, and dependencies `111` and `134` remain `merged`.

This readiness packet does not by itself authorize product implementation while the registry row is absent or non-ready.

## Frozen implementation envelope

Implementation is limited to the accepted behavior in `136-route-default-consistency-1.md`:

1. one execution-owned effective-route resolver backed by the existing `TASK_KIND_DEFAULT_ROUTE` semantics;
2. exact-ref local-only admission uses that resolver for omitted as well as explicit routes;
3. gateway omitted-route preflight and execution selection agree through the same resolver;
4. explicit routes and the existing `auto` bridge remain behaviorally unchanged.

## Pre-implementation revalidation

Before editing product code, the writer must verify on fresh exact master:

- `run_ai_task` still owns task-kind defaults through `TASK_KIND_DEFAULT_ROUTE`;
- `AIGateway.run_task` still has an independent omitted-route fallback or otherwise differs from the execution-owned effective route;
- the exact-ref guard still permits omitted route without evaluating its effective route;
- no newer merged slice already centralizes these semantics.

If fresh code no longer exhibits the defect, do not implement stale work; re-derive or close the repair.

## Required deterministic evidence

- focused resolver tests for omitted/default and explicit routes;
- gateway/direct-execution agreement test for omitted route;
- exact-ref rejection for explicit external and test-controlled omitted→external defaults before provider/spend;
- omitted→local exact-ref acceptance preserving current preview/digest/staleness checks;
- `auto` routing regression coverage;
- relevant AI backend suite and repository-required architecture/CI gates.

## Independent review

The implementation PR is MATERIAL because the repair touches routing/egress-adjacent admission semantics. It requires an independent exact-head semantic review: Claude primary with a consumable exact-head verdict/findings; immediate single manual `@codex review` fallback if Claude terminates without consumable semantic evidence.

## PROUD gate

Merge only when objective gates are green on the exact current head, independent review is acceptable, no material finding remains, and the accepted envelope is complete. Do not broaden this into routing redesign or unrelated cleanup.

## Non-goals

No new routing table, provider, credential, egress/budget authority, schema/store/migration, frontend change, task-default change, or broad AI refactor.