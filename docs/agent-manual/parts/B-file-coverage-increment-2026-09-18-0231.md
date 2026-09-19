# Area B explicit file coverage increment — 2026-09-18 02:31 CEST

MAPPING_STATUS: IN_PROGRESS

This is a durable Area-B-only ledger increment for issue #656 / PR #660. It is source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`; it does not assert global-union ownership and does not alter A/C/D scope.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/api/client.ts` | READ | Directly inspected at PR #660 head `7c691bd86c146da0bcc79d984401b29c595f5ed4`. Broad handwritten HTTP/type boundary for health/system/workspaces, Memory/model records, AI settings/status/provider-secret operations, modeling/AI task and smoke-test surfaces plus further legacy/domain endpoints. Generic helpers call `fetch` without `AbortSignal`, collapse non-2xx failures to status-only `Error`, and expose real mutation/secret/AI authority; consumers must therefore provide stale-response identity protection and must not infer safety/authority from the type layer alone. |

## Run reconciliation

- Fresh PR #660 inspection confirmed the required branch and starting head `7c691bd86c146da0bcc79d984401b29c595f5ed4`.
- Fresh recursive tracked-tree inspection was performed from that head before this increment.
- No backend-A rows were added.
- `UNACCOUNTED_FILES: 0` is **not** asserted; exhaustive B reconciliation remains pending.
- The existing canonical `MAPPING_STATUS: COMPLETE` marker is stale/non-authoritative until the literal one-row-per-B-owned-file ledger is consolidated and a fresh tree proves zero unaccounted files.
