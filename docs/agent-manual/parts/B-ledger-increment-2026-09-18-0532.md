# Area B explicit file coverage increment — 2026-09-18 05:32 CEST

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B-only inspection evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership and contains no backend Area-A rows.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/development.ts` | READ | Handwritten Development-domain frontend HTTP/type boundary for roadmap items, calendar allocations, Brainstorm raw/ideas/discussions/reconciliation/supersession/promotions. Roadmap/calendar update/delete and Brainstorm idea transitions carry expected revision guards; creation/reconciliation/discussion/promotion flows carry caller-supplied idempotency keys where exposed. The local `requestJson` wrapper accepts `RequestInit` internally but exported functions expose no `AbortSignal`, so cancellation/stale-response rejection remains consumer responsibility. Error parsing preserves backend detail message when JSON-shaped, otherwise falls back to HTTP status. |

## Failure-mode notes

- Revision-aware writes reduce lost-update risk for roadmap/calendar and existing Brainstorm ideas, but do not make late responses safe to render after workspace/selection changes.
- Brainstorm raw creation is idempotency-keyed, while roadmap/calendar creation functions expose no idempotency key in this client contract; duplicate-submit protection therefore cannot be inferred from this frontend boundary.
- `requestJson` has no exported cancellation seam through these functions. Consumers must bind async results to current workspace/selection/generation before projecting them as current operator truth.

## Reconciliation state

A fresh recursive tracked-tree scan was taken from PR #660 head `32d8e58a311ed8d24d4e9cf2bd7b19f1b2587b2a` before this increment. Exhaustive B-owned reconciliation remains pending; `UNACCOUNTED_FILES: 0` is NOT asserted.
