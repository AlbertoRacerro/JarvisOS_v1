# Area B explicit file coverage ledger — 2026-09-17T2132Z

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_ZERO

Durable Area-B-only increment for issue #656 / PR #660. These rows are based on direct content inspection at branch head `880bff3b193dbca2dde2a5a9552fd2efc72b57de`; they do not claim global-union coverage and add no backend Area-A ownership.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/runs.ts` | READ | Directly inspected. Typed read-only client for workspace simulation-run summaries/details, logs and artifact metadata. URL path segments are encoded; non-2xx responses become `RunsRequestError(status)`. It exposes no run-launch mutation. Requests have no AbortSignal support themselves, so stale-response protection belongs to the consuming workbench. |
| `frontend/src/api/projectSearch.ts` | READ | Directly inspected. Typed workspace project-search client spanning Project Basis, model dossier and literature result kinds. Query is encoded through `URLSearchParams`; result contracts carry stable refs, bounded canonical routes/route params, provenance/source refs and match tier. Accepts `AbortSignal`, allowing callers to cancel superseded searches. |
| `frontend/src/api/modelDossier.ts` | READ | Directly inspected. Typed read-only client for model-dossier index and exact model-version detail, including runs, artifacts and evidence availability. Workspace/version path identities are encoded; non-2xx responses are surfaced as errors. It exposes no model mutation authority and has no AbortSignal parameter, so caller-side generation/identity guards remain necessary. |
| `frontend/src/api/literature.ts` | READ | Directly inspected. Typed read-only literature source/entry client with lifecycle state, provenance, locator, used-by links and backing availability. `literatureContentUrl` returns a content URL only when backing is explicitly available, content is marked available and a content path exists; unsupported/missing/unsafe backing therefore cannot be projected as readable content by this helper. |

## Coverage notes

- Runtime/product source was not modified.
- The canonical map still has a stale `MAPPING_STATUS: COMPLETE`; this increment is authoritative that Area B remains `IN_PROGRESS` until consolidation plus a fresh recursive tracked-tree reconciliation proves literal `UNACCOUNTED_FILES: 0`.
- Historical combined A+B increments remain evidence only and must not count as B/global-union ownership.
- Next coverage should continue through remaining `frontend/src/api/` files and then reconcile every tracked `frontend/` and canonical operator design-reference asset into the single canonical ledger.
