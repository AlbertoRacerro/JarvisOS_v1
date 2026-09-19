# Area B file-coverage increment — 2026-09-19 run 11

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

This increment is durable source evidence for the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does **not** assert completion or replace fresh-tree reconciliation.

## EXPLICIT FILE COVERAGE LEDGER INCREMENT

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/App.tsx` | READ | Directly inspected from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Root operator composition: resolves routes, bounds query parameters, owns workspace/selection/shell-region/model-version transient state, mounts production/legacy surfaces, derives stable knowledge refs, suppresses Jarvis sidecar in Settings, and composes engineering/Jarvis/analytics shell contributions. Route changes clear selection/shell-region/model-version state. Failure boundary: `routeParams` is constructed from `window.location.search` on render and bounded values are length-limited/allowlisted where applicable, but workspace state is shared across routed surfaces; page correctness therefore depends on child surfaces rejecting stale async results when workspace changes. This file itself performs no backend mutation or authorization checks. |

## Reconciliation note

The canonical Area-B document currently contains an older `MAPPING_STATUS: COMPLETE` claim without the required literal one-row-per-B-owned-file ledger. That claim remains non-defensible. This run intentionally keeps Area B `IN_PROGRESS`; `UNACCOUNTED_FILES: 0` must not be asserted until the fresh tracked `frontend/` plus canonical `docs/design-references/` scope has been set-reconciled against the canonical ledger.

No backend-A rows were added. Any historical A+B increment documents remain source evidence only and must not count as B or global-union ownership.