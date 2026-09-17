# Area B explicit file coverage ledger increment — 2026-09-17T13:31Z

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

This increment is durable Area-B-only source evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not change ownership boundaries and does not count any backend Area-A file toward B/global-union coverage.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/BlueCAD.tsx` | READ | Legacy BLUECAD candidate workbench page. Direct inspection confirms workspace-scoped candidate list/create/archive/promote flows, GLB artifact viewing, validation-report loading, attempt-history/error-detail disclosure, retry/duplicate brief UX, archived filtering, and explicit parked/promoted states. Promotion is only offered for `valid` candidates without an existing promoted decision. This page performs real backend mutations through the BLUECAD API wrappers and is distinct from the production `ModelStage` presentation-authoring toolbar, whose disabled controls must not be inferred as CAD authoring authority. Failure-mode note: `refreshCandidates(workspaceId)` and validation-report loads are not generation/identity guarded in this page, so a late response after workspace/selection change can project stale data; this is evidence about current frontend behavior, not a request to modify runtime code in this mapping branch. |

## Fresh-state / completion guard

At run start the existing branch `docs/capability-map-B-frontend-ux` and PR #660 were inspected together with the current canonical Area-B map. The canonical map still contains a stale top-level `MAPPING_STATUS: COMPLETE` while it does not yet contain the maintainer-required consolidated one-row-per-B-owned-file ledger. Therefore that marker is not accepted as completion evidence.

A fresh recursive tracked-tree scan remains required after consolidation. Until every tracked file under `frontend/` plus canonical operator design-reference files/assets under `docs/design-references/` has an explicit verified row, `MAPPING_STATUS` remains `IN_PROGRESS` and literal `UNACCOUNTED_FILES: 0` is forbidden.

No backend Area-A rows were added in this increment. Historical combined A+B increment documents remain source evidence only and must continue to be treated as `HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP` where applicable.