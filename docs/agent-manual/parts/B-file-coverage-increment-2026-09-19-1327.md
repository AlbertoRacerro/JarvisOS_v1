# Area B file coverage increment — 2026-09-19 13:27 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

This increment is Area-B-only evidence for issue #656. It does not assert global-union ownership and adds no backend Area-A rows.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / verified failure boundary |
|---|---|---|
| `frontend/src/pages/DomainFoundation.tsx` | READ | Legacy/persistent-core workspace CRUD and bundled BlueRev registration surface. Direct inspection confirms real writes for workspace/model-spec/assumption/parameter/planned-run/decision creation plus direct POST registration of three bundled model implementations. `refreshWorkspaceRecords` fans out six canonical list reads. Important failure boundary: async refreshes and mutations have no generation/context guard; a workspace change while an earlier refresh is in flight can therefore write stale records into the currently displayed state. Bundled registration is sequential and non-transactional: an early registration may succeed before a later POST fails, leaving partial server state until reread/retry. Generic errors are surfaced through one message banner; failed mutations are not proof of no server-side effect. |

## Reconciliation note

Fresh branch directory inspection confirms `DomainFoundation.tsx` is still a tracked B-owned frontend page. Its complete source was inspected in this run; this row is therefore `READ`, not inferred from the pre-existing capability prose.

The canonical `docs/agent-manual/parts/B-frontend-operator-ux.md` still carries a historical `MAPPING_STATUS: COMPLETE` statement while lacking the maintainer-required literal one-row-per-file canonical ledger. That completion statement remains non-defensible until all accumulated B increments are consolidated and a fresh tracked-tree set difference proves zero missing B-owned paths. Do not use this increment to claim `UNACCOUNTED_FILES: 0`.
