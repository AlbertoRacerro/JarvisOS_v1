# Area B literal file coverage increment — Runs workbench

MAPPING_STATUS: IN_PROGRESS

Canonical destination: `docs/agent-manual/parts/B-frontend-operator-ux.md` under `## EXPLICIT FILE COVERAGE LEDGER`. This increment is durable direct-read evidence pending safe consolidation of the large canonical document.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/RunsWorkbench.tsx` | READ | Run-evidence workbench generation/identity-guards workspace/list/detail/log/artifact responses, restores source-run deep links, preserves focus across refresh, and gates previous-run restoration through revision-aware engineering confirmation rather than granting execution authority. |

## Capability/failure-mode evidence

- The page is evidence/inspection UX, not arbitrary run-launch authority: it lists persisted runs, detail, logs and artifacts and can restore a previous successful run only through the supplied engineering-properties controller.
- Workspace/list/detail/log/artifact asynchronous projections use generation plus identity acceptance checks; workspace or selected-run changes invalidate older responses before they can overwrite current operator state.
- Source-run navigation is restored from URL state only when workspace/run identities resolve; unresolved targets are discarded rather than guessed.
- Refresh attempts to preserve focus; if a focused run disappears, focus moves to the replacement selection or search control.
- Previous-run restoration is revision-aware and confirmation-gated when required; changed selection or stale working configuration yields explicit no-replacement messaging.

## Split-recovery boundary

No backend Area-A row is added here. Historical combined A+B evidence remains source-only and MUST NOT count as B ownership or global-union coverage.

## Remaining coverage

Literal Area-B completion remains unproven. `frontend/package-lock.json`, `frontend/public/`, unledgered frontend source/pages/stages/styles/helpers/tests and canonical operator design-reference assets still require direct file accounting and final exhaustive consolidation.

UNACCOUNTED_FILES: NOT_YET_ZERO
