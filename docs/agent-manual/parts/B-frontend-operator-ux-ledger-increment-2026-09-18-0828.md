# Area B explicit file coverage ledger increment — 2026-09-18 08:28 CEST

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert completion or `UNACCOUNTED_FILES: 0`.

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/App.tsx` | READ | Directly inspected at branch head. Root operator composition/routing surface: resolves canonical route, owns transient workspace/selection/shell-region/model-version state, bounds query refs, resets route-sensitive state, dispatches primary stages/pages, derives stable Jarvis knowledge refs, suppresses Jarvis on Settings, and composes Properties/Jarvis/Analytics shell regions. No durable domain authority is created here; real mutations remain delegated to mounted domain components/API clients. |

## Failure-mode notes from direct inspection

- Query-derived record IDs/kinds are bounded to 200 characters and Project Basis kinds are allowlisted before a stable ref is constructed.
- Route changes clear selection, contributed shell regions, shell-region requests, and selected model version, reducing cross-route stale-context leakage.
- Workspace is synchronized from an explicit selected record when its workspace differs.
- Knowledge stable refs are only synthesized for Project Basis, selected model versions, and selected Literature source/entry routes; they are not guessed for unrelated routes.
- Settings explicitly removes the Jarvis sidecar; Runs/Engineering Data/Process selectively add Analytics dock content.
- `PageErrorBoundary` is keyed by canonical path, so navigation remounts the route error boundary rather than carrying an errored route state forward.

## Reconciliation state

A fresh recursive tracked-tree read was taken from the current PR head before this increment. Area B remains `IN_PROGRESS`; exhaustive literal reconciliation of every tracked `frontend/` and canonical operator design-reference file is still required before the canonical document may defensibly say `UNACCOUNTED_FILES: 0`.
