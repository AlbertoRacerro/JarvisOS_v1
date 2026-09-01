# 136 ROUTE-DEFAULT-CONSISTENCY-1 — definition

Status: planning authority only until the live registry/readiness gate authorizes implementation.

## Problem

Fresh post-135 `master` still derives the effective AI route in more than one place:

1. `execution.py::run_ai_task` owns the task-kind-aware canonical default via `TASK_KIND_DEFAULT_ROUTE`;
2. `gateway.py::AIGateway.run_task` separately substitutes omitted `route_class` with `local:fake` before dispatch;
3. `thread_service.py::_context_blocks_for_new_submit` enforces the spec-111 exact-ref local-only boundary only when a literal `route_class` was supplied, so an omitted route is not checked against its canonical effective route.

Current task defaults happen to be local, but the guard and execution spine are coupled to that incidental snapshot. If a canonical task default becomes external, omitted-route exact-ref context can cross the local-only guard before provider/budget dispatch checks.

This is a bounded correctness repair to the existing AI execution/routing boundary, not new routing authority.

## Scope

- Establish one reusable effective-route resolver owned by the existing execution spine and backed by the existing `TASK_KIND_DEFAULT_ROUTE` table.
- Make `run_ai_task` consume that resolver instead of duplicating its expression inline.
- Make exact-ref Jarvis-context admission evaluate the same effective route before accepting added exact refs.
- Remove or replace the gateway's independent omitted-route fallback so gateway preflight and execution observe the same canonical effective route.
- Preserve explicit route values and the existing `route_class="auto"` bridge semantics.
- Add deterministic regression tests for omitted local/external defaults, explicit routes, `auto`, and the exact-ref local-only boundary.

## Expected affected area

- `backend/app/modules/ai/execution.py`
- `backend/app/modules/ai/gateway.py`
- `backend/app/modules/ai/thread_service.py`
- focused AI execution/gateway/thread/Jarvis-context tests

## Non-goals

- no new routing table, router policy, provider, credential, egress, budget or sensitivity authority;
- no change to current task-kind default values unless required by a separately accepted specification;
- no relaxation of the spec-111 exact-ref local-only boundary;
- no frontend changes;
- no schema/store/migration changes;
- no broad AI execution refactor.

## Dependencies

Hard dependencies: `111` and `134` merged. The repair preserves the existing 090/111 execution/thread contracts rather than reopening them.

## Lifecycle

This definition establishes only the corrective planning identity. Implementation remains forbidden until full specification, readiness, and a live `STATUS.md` state of `ready` are merged.