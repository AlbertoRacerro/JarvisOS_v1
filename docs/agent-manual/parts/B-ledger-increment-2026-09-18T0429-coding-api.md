# Area B explicit ledger increment — coding API

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B-only inspection evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert exhaustive reconciliation or `UNACCOUNTED_FILES: 0`.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/coding.ts` | READ | Handwritten Coding frontend HTTP/type boundary for repository ref/tree/file/search/safe-URL, PR/check/review evidence, runtime truth and pipeline projection plus bounded inspect/context-preview/suggest-modification actions. Defaults repository/ref from Vite env with JarvisOS/master fallbacks. Exact action targets carry workspace/repository/base ref+SHA/target paths; modification suggestions may bind `expected_context_digest` and expected checks. `requestJson` preserves backend `detail.code` or deterministic HTTP fallback but exposes no dedicated cancellation API, so consumers must prevent superseded responses from being presented as current truth. This client is an operator projection/action boundary, not browser-side shell/filesystem/direct-GitHub authority. |

Fresh branch inspection used the existing `docs/capability-map-B-frontend-ux` branch. No backend-A rows were added. Canonical stale `MAPPING_STATUS: COMPLETE` remains non-authoritative until literal file-by-file reconciliation is complete.