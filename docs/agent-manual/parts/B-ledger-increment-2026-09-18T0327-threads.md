# Area B explicit file-coverage increment — threads API

MAPPING_STATUS: IN_PROGRESS

This is B-only durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership or `UNACCOUNTED_FILES: 0`.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/threads.ts` | READ | Directly inspected at PR #660 head `4c07e9a6316d68b2f8aca1c34b545548787ab878`. Typed AI-thread HTTP boundary: lists/gets/creates durable workspace threads, previews bounded context packs, and submits interactions with caller-provided retry-stable `request_id`; optional context submission carries `expected_context_digest`. Shared `requestJson` accepts `RequestInit` internally but exported calls expose no cancellation signal, so stale-response rejection remains consumer responsibility. Non-2xx errors preserve HTTP status only. |

## Reconciliation note

The canonical Area-B document currently contains a stale `MAPPING_STATUS: COMPLETE` claim while literal file-by-file reconciliation is not yet proven. Treat this increment as authoritative evidence that Area B remains `IN_PROGRESS` until the canonical ledger is consolidated against a fresh recursive B-owned tree and proves `UNACCOUNTED_FILES: 0`.
