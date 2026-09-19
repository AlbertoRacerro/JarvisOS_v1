# Area B frontend/operator UX — explicit file coverage increment

MAPPING_STATUS: IN_PROGRESS

This increment is Area-B-only direct-read evidence for issue #656. It is intended for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `docs/agent-manual/parts/B-frontend-operator-ux.md`. It does not establish global-union ownership and contains no new backend Area-A rows.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/AIThreads.tsx` | READ | AI Threads operator workbench: workspace-scoped list/detail/create/submit UI; generation/context guards discard stale async responses, retries of an unchanged failed submission reuse the same request id, and durable interaction/persistence/proposal/truncation evidence is rendered explicitly. |

## Direct-read capability and failure boundaries

`AIThreads.tsx` was inspected directly at PR #660 head lineage. It resets thread/detail/submission state on workspace changes and uses `threadState` context snapshots before accepting asynchronous list, detail, create, submit, or refresh results. This prevents stale responses from a previous workspace/thread from overwriting the current operator surface.

Submission uses a generated request id and deliberately retains it after a failed submit/confirmation path when both selected thread and prompt are unchanged. The visible error tells the operator that the interaction may not have been submitted or its durable result may not have been confirmed, rather than claiming failure atomically. After a successful submit it re-fetches thread detail before clearing the pending request and prompt.

The surface exposes bounded-history state (`has_older`), canonical flow state, persistence state/error, attempt count, proposal count/truncation, assistant snapshot absence/truncation, and labels assistant output as `Jarvis advisory`. These are presentation/projection semantics only: authority for thread persistence, flow state, proposals, and request idempotency remains in the API/backend contracts, not this page.

Failure boundary: list/detail/create/submit exceptions are intentionally collapsed to bounded operator-facing messages; this page does not expose raw exception/provider detail. It also cannot prove that a failed request had no side effect; the retained request id is the client-side mechanism for safe unchanged-prompt retry, contingent on server idempotency semantics.

## Run-end status

Fresh B-scope completion is not yet proven. Additional tracked `frontend/` files and canonical operator design-reference files/assets remain to be directly inspected and explicitly accounted for. The canonical `B-frontend-operator-ux.md` still has the known safe-write consolidation blocker documented in `B-frontend-operator-ux-ledger-progress.md`: the available connector exposes bounded reads while file replacement is whole-file, so destructive reconstruction from truncated content is not acceptable.

UNACCOUNTED_FILES: NOT_YET_ZERO
