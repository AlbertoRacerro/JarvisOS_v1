# Area B explicit file-coverage increment — 2026-09-19 08:30 CEST

MAPPING_STATUS: IN_PROGRESS

Scope is Area B only: tracked `frontend/` plus canonical operator behavior/appearance references under `docs/design-references/`. Backend Area-A material is excluded from B ownership and union accounting.

## EXPLICIT FILE COVERAGE LEDGER — durable increment

The canonical destination remains `docs/agent-manual/parts/B-frontend-operator-ux.md`. This increment records direct-read evidence that must be folded into that canonical table during safe reconstruction.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/DevelopmentRoadmap.tsx` | READ | Workspace-scoped Roadmap Timeline/Calendar operator surface: loads server-owned items/allocations, provides bounded create/update/delete/status/scheduling mutations, timezone-aware projections and roadmap↔calendar deep links; mutation failure preserves the original error and attempts canonical refresh rather than assuming success/failure state. |

## Direct-read capability / failure-boundary notes

`DevelopmentRoadmap.tsx` was inspected through its complete source range on the current PR branch. It owns transient workspace/view/form/edit state only; durable Roadmap items and Calendar allocations remain backend-owned through `api/development`.

The Timeline and Calendar are distinct projections over the same workspace domain. Calendar filtering is timezone-aware and treats allocation end instants as exclusive for date-overlap projection. Timeline deep links scroll to a requested item when present; Calendar deep links may preselect a matching Roadmap item for scheduling.

Mutations are serialized by local `busy` gating. After each mutation the page rereads both Roadmap items and allocations. If the mutation throws, the original mutation error remains visible while a best-effort refresh is attempted; therefore the UI does not treat a thrown request as proof that no server-side effect occurred. This is an important operator uncertainty boundary.

The component does not itself expose arbitrary scheduler/runtime execution authority: it edits Development Roadmap/Calendar records through the bounded client functions it imports.

## Split-recovery / ownership note

No backend-A row was added. Historical A+B increment material remains source evidence only and MUST NOT count as B ownership or global-union coverage (`HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP`).

## Remaining coverage

Literal completion is not yet proven. The canonical map still carries an older capability-level `MAPPING_STATUS: COMPLETE` header that is superseded by the explicit-ledger work until safe reconstruction and a fresh tracked-tree comparison prove one row per B-owned file. Do not assert `UNACCOUNTED_FILES: 0` yet.

UNACCOUNTED_FILES: NOT_YET_ZERO
