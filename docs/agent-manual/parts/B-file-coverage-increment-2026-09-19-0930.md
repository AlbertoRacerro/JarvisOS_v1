# Area B explicit file-coverage increment — 2026-09-19 09:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This increment is durable source evidence for the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert `UNACCOUNTED_FILES: 0`; the canonical file still contains a stale `MAPPING_STATUS: COMPLETE` declaration that must not be treated as defensible completion until a fresh tracked-tree reconciliation proves one explicit row per B-owned file.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/pages/DevelopmentBrainstorm.tsx` | READ | Directly inspected complete component. Workspace-scoped Brainstorm operator surface for immutable RAW capture, recorded discussion provenance, reconciled idea revisions, supersession lineage and proposal-only roadmap/design/coding promotions. Guards projections against workspace drift with `activeWorkspaceRef`/`projectionWorkspaceId`; clears stale projections on workspace change or failed canonical reread. Mutations use payload-fingerprinted client request identities retained across ambiguous failures and cleared only after the mutation call returns; `run()` attempts canonical refresh after both success and failure, preserving the original mutation error and invalidating projection if refresh also fails. Exact attachment owner IDs are server-resolved; speech capture is explicitly unavailable. Promotion controls create proposals, not direct target-domain commits. Detail fetch is workspace-identity guarded. No backend authority is inferred from the UI itself. |

## Failure-mode evidence captured

- A thrown mutation is not evidence of no server-side effect. Retry safety depends on retained request identity plus server idempotency semantics.
- If post-failure canonical refresh also fails, the component sets `projectionWorkspaceId` to null so stale records are hidden rather than presented as canonical.
- Workspace changes clear retry identities, records, selections, expanded detail and busy/error state, preventing previous-workspace projections from remaining actionable.
- `recordBrainstormDiscussion`, reconcile, promotion and supersede are real backend mutations at this frontend boundary; promotion semantics remain proposal-only.
- The two buttons `Revise this idea` and `Use as lineage source` currently perform the same local action (`setEditingIdeaId(idea.id)`); the latter label must not be interpreted as evidence of a distinct lineage-source mechanism.

No Area-A backend rows are added by this increment. Any older combined A+B increment remains historical source only and must not count toward B ownership or global-union coverage.
