# Area B explicit file coverage increment — Domain Foundation

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

This increment is B-only evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union coverage and contains no Area-A ownership rows.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/DomainFoundation.tsx` | READ | Directly inspected. Legacy/persistent-core operator page for workspace initialization/creation and workspace-scoped model-spec, assumption, parameter, planned simulation-run, decision, and bundled BlueRev model-registration mutations. Reads implementations and records through `../api/client`. Important failure mode: workspace-record refreshes are not generation/identity guarded, so a late response after `workspaceId` changes can overwrite the currently selected workspace projection; mutation follow-up refreshes also close over mutable component workspace state rather than a request-generation token. Scenario editing/execution is explicitly delegated to the shared Properties sidecar rather than duplicated here. |

## Run evidence

- PR/branch inspected before edit: PR #660 / `docs/capability-map-B-frontend-ux`, prior head `ff64f35391ed7f46db9d131cf4e861017154b326`.
- `frontend/src/pages/DomainFoundation.tsx` content was actually fetched and read before assigning `READ`.
- Fresh recursive tracked-tree evidence was fetched from the prior PR head before this increment; exhaustive B reconciliation is still pending, therefore completion is forbidden.
- No runtime/product code, STATUS, spec144, Hermes direction, provider secrets, or A/C/D-owned documentation was modified.
