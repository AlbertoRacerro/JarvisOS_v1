# Area B explicit file coverage ledger increment — 2026-09-17T1630Z

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

Scope remains strictly the tracked `frontend/` tree plus canonical operator design-reference files/assets. This increment does not count backend Area-A material as B ownership or global-union coverage.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/pages/ModelDossier.tsx` | READ | Directly inspected at PR #660 head `4df4638d8bf3f967f38c45ce055f763e6faa8ce1`. Canonical model-version dossier browser: loads workspaces/index/exact version detail; keeps requested deep-link identity explicit; clears Jarvis model selection before reads; reports unavailable requested versions and backend failures instead of fabricating dossier evidence; exposes runs/artifacts/evidence/lineage and exact IDs under technical disclosure; browsing is explicitly context-neutral and composer is disabled. Async reads use effect-local `alive` cancellation, so unmounted/superseded effects do not project late results, but there is no shared generation token across the three independent effects; exact selected-version detail is additionally constrained by `activeRequestedVersionId` before fetch. |

## Fresh-tree / completion guard

A fresh recursive tracked-tree read was taken from PR #660 head `4df4638d8bf3f967f38c45ce055f763e6faa8ce1` before this increment. Literal B-owned file-by-file union coverage has not yet been proven against that tree. Therefore the stale `MAPPING_STATUS: COMPLETE` currently present in the canonical capability document MUST NOT be treated as authoritative completion, and `UNACCOUNTED_FILES: 0` is not asserted here.

Next coverage should continue through remaining unledgered frontend source/config/tests/assets and canonical `docs/design-references/` assets, then consolidate all verified rows into `docs/agent-manual/parts/B-frontend-operator-ux.md` and perform an exact fresh-tree set difference before changing status to COMPLETE.
