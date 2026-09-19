# Area B explicit file coverage ledger increment — 2026-09-19 10:31 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: UNKNOWN — literal fresh-tree reconciliation is still required before asserting zero.

This increment is Area-B-only evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not count backend Area-A ownership and does not assert global-union completion.

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/pages/ModelDossier.tsx` | READ | Directly inspected complete file content. Workspace-scoped model/version dossier READ surface. Loads workspaces and dossier index, selects an exact model version, then loads exact detail; async effects use `alive` guards and clear selected/detail state on workspace/version changes. Requested deep-linked version IDs that are absent are surfaced explicitly as unavailable rather than silently substituted. Exposes definition, assumptions, inputs, outputs, runs, artifacts, freshness/evidence and lineage, with technical identifiers behind native details disclosure. Browsing is explicitly context-neutral and the embedded Jarvis composer is disabled; this file performs no dossier mutation or context insertion. Failure boundary: backend/workspace/index/detail read errors are rendered from exception messages; `loading` and `error` are shared across independent effects, so overlapping requests can affect aggregate loading/error presentation even though stale state writes are guarded per effect. |

## Run-end scope status

Fresh PR #660 state was checked before this inspection. `frontend/src/pages/EngineeringWorkspace.tsx` was probed but does not exist on the branch and therefore was not ledgered or inferred. No runtime/product code, STATUS, spec144, Hermes direction, provider secret, or A/C/D-owned document was modified.

`MAPPING_STATUS` remains `IN_PROGRESS`. This increment deliberately does **not** assert `UNACCOUNTED_FILES: 0`; completion requires a fresh tracked-tree enumeration and exact one-row-per-B-owned-file reconciliation in the canonical ledger.
