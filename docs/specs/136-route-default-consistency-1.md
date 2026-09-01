# 136 ROUTE-DEFAULT-CONSISTENCY-1

## Objective

Make omitted `route_class` resolve through one canonical execution-owned rule everywhere that route semantics affect dispatch or exact-ref admission, without changing current route defaults or broadening routing/provider authority.

## Accepted behavior

### AC1 — one canonical effective-route resolver

- The existing execution spine remains the sole owner of task-kind default selection through `TASK_KIND_DEFAULT_ROUTE`.
- A small reusable resolver returns the effective route for `(task_kind, route_class)` using the current explicit-route-or-task-default semantics and the existing `local:fake` unknown-task fallback.
- `run_ai_task` uses this resolver for effective route selection; no second default table is introduced.
- Explicit route values remain unchanged.

### AC2 — exact-ref local-only guard uses the effective route

- Spec-111 added exact-ref Jarvis context remains local-only.
- An explicit external effective route is rejected before reservation/dispatch/provider spend, preserving current behavior.
- If `route_class` is omitted and the canonical task default resolves external, added exact refs are rejected by the same local-only boundary before provider dispatch/spend.
- If `route_class` is omitted and the canonical task default resolves local, added exact refs remain accepted subject to existing preview/digest/staleness checks.
- The guard must call the canonical resolver; it must not inspect a copied routing table or assume omitted means local.

### AC3 — gateway and execution agree on omitted routes

- Gateway preflight must evaluate the same effective route as `run_ai_task` for omitted `route_class`.
- The gateway must not hard-code an independent `request.route_class or "local:fake"` default that can mask task-kind defaults.
- Existing explicit external provider/status/egress/budget preflight remains in force.
- Existing `route_class="auto"` handling remains behaviorally unchanged and continues through the routing bridge; this repair must not reinterpret `auto` as an omitted route or external permission.
- Direct `run_ai_task` callers and gateway callers agree on effective-route selection for omitted routes.

## Implementation constraints

- Prefer one small pure resolver in `backend/app/modules/ai/execution.py` (name may follow local conventions).
- Reuse the resolver from `run_ai_task`, `AIGateway.run_task`, and the exact-ref guard seam that needs effective route semantics.
- Do not move provider preflight out of the gateway or create a new router/service/facade.
- Preserve requested-route observability/accounting semantics unless a fresh test proves a change is required for correctness.
- Preserve safe defaults: paid AI disabled, provider fake, no external call from `auto` without the existing routing/policy spine.

## Deterministic tests

1. resolver returns every current `TASK_KIND_DEFAULT_ROUTE` mapping when route is omitted;
2. resolver preserves explicit local/external routes and existing unknown-task fallback;
3. direct `run_ai_task` and gateway path agree on omitted-route effective selection;
4. explicit external route + added exact-ref context is rejected before dispatch/spend;
5. omitted route + a test-controlled canonical external task default is rejected before dispatch/spend;
6. omitted route + canonical local default accepts exact refs subject to existing context validation;
7. `route_class="auto"` retains existing routing-bridge behavior;
8. focused AI execution/gateway/thread/Jarvis-context tests and repository-required architecture/CI gates remain green.

Tests may temporarily monkeypatch the canonical default map to exercise an external default; production default values are not changed by this spec.

## Failure modes prevented

- policy/guard drift when a task default changes;
- exact-ref context admission based on literal request shape rather than effective execution route;
- gateway masking a task-kind-aware execution default with a second fallback;
- future external dispatch reaching provider preflight after an inconsistent local-only context decision.

## Security and authority invariants

No new provider, account, credential, egress, budget, sensitivity, store or frontend authority. The repair tightens consistency around existing local-only context and dispatch policy. `route_class="auto"` retains the AGENTS invariant that it never directly executes an external provider.

## Non-goals

- changing current task-kind defaults;
- redesigning RouterPolicy/Auto routing;
- adding provider support or spending;
- broad AI module cleanup;
- changing Jarvis context contract beyond using the canonical effective route;
- unrelated test expansion.

## Dependencies

`111 JARVIS-CONTEXT-ACTION-FOUNDATION-1` and `134 MERGE-AUTHORITY-HARDENING-1` must remain merged on the implementation base.