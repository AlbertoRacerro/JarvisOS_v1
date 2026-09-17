# Area B explicit file coverage increment — 2026-09-17 20:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

This is a durable Area-B-only increment for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not claim global-union ownership. Any pre-split backend Area-A evidence in older temporary A+B increments remains `HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/Properties.tsx` | READ | Directly inspected. Workspace-scoped model/scenario Properties sidecar: loads model specs and scenarios; creates scenarios; validates/runs the selected scenario through backend API; records returned run identity; refreshes canonical scenario state. Read effects use generation counters for workspace/spec/scenario changes. Mutation-triggered refreshes are not independently identity-bound, so superseded mutation/refresh completion remains a stale-projection risk to preserve in the capability map. Scenario execution is a validated backend action, not local frontend computation. |

## Completion guard

This increment is not completion evidence. A fresh recursive tracked-tree comparison of the entire tracked `frontend/` tree plus canonical operator design-reference files/assets is still required. Keep `MAPPING_STATUS: IN_PROGRESS` until every B-owned tracked path has exactly one canonical disposition and the comparison proves literal `UNACCOUNTED_FILES: 0`.
