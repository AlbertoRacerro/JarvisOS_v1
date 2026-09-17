# Area B explicit file coverage ledger increment — 2026-09-18 01:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is a durable Area-B-only increment for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership and contains no backend Area-A rows.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/projectKnowledge.ts` | READ | Directly inspected. Typed Project Knowledge revision/draft/impact/revalidation/approval/reconcile client. Draft approval is bound to both `expected_draft_revision_token` and `expected_preview_digest`; reconcile is bound to expected target snapshot/digest and selected-validation-set digest, with idempotency key and optional known-fail acknowledgement. Revision discard/supersede is a real mutation. Local `requestJson` preserves bounded HTTP/error-detail reporting but exposes no `AbortSignal`, so stale-response suppression remains a consumer responsibility. |

## Failure-mode evidence

`projectKnowledge.ts` is not merely a read projection: it exposes approval, revision-state and reconcile mutations. The strongest concurrency protections are explicit expected digests/tokens on approval/reconcile; the revision state-change call itself carries workspace/action but no expected revision token in this frontend contract. Consumers must therefore avoid presenting a late mutation/read response as current workspace truth.

## Reconciliation state

A fresh recursive tracked-tree scan was taken from PR #660 head `0a8c891ca169aeb956bcb9feb515d37ca507128c` before this increment. Exhaustive literal B-owned reconciliation remains pending; `UNACCOUNTED_FILES: 0` is not claimed. The stale `MAPPING_STATUS: COMPLETE` text currently present in the canonical map is non-authoritative until the required one-row-per-owned-file ledger is consolidated and checked against a fresh tree.
