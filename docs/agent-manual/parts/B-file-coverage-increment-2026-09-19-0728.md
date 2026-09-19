# Area B file-coverage increment — 2026-09-19 07:28 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This increment is durable Area-B source evidence for later reconciliation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does **not** assert `UNACCOUNTED_FILES: 0`; the canonical file still carries a stale `MAPPING_STATUS: COMPLETE` declaration and literal whole-tree reconciliation remains outstanding.

Fresh run-start evidence: PR #660 head was `6252a9b0ddd7de8c731497f673bd08cd00957fbc` on `docs/capability-map-B-frontend-ux`. A recursive tracked-tree read was performed at that exact head before this increment.

## EXPLICIT FILE COVERAGE LEDGER — incremental rows

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/pages/Dashboard.tsx` | READ | Directly inspected. Legacy/foundation dashboard reads backend health once on mount via `getHealth()` and projects backend status/environment/version plus a static milestone scope list. Failure boundary: any `getHealth()` rejection is collapsed to the caught error message internally while the visible Backend metric becomes `offline`; Environment and Version fall back to `local` and `0.1.0`, so those fallback labels are not evidence of actual backend environment/version when health is unavailable. No mutation or authorization authority. |
| `frontend/src/pages/DevLocalChat.tsx` | READ | Directly inspected. DEV diagnostic local-chat surface posts message plus clean user/assistant history to `/api/dev/local-chat` with `run_local_responder: true`; distinguishes 404/422/5xx/network/blocked/executed states, exposes trace IDs, deterministic context-filter counts, prompt-char budget and adapter response-truncation semantics. Explicitly declares no persistent memory/retrieval/external providers/tools. Failure boundaries: history exists only in component memory; blocked/error turns are excluded from subsequent history; JSON parse failure is normalized to `invalid_json_response`; char budget is not model context; `response_truncated=false` is not completion proof. No production-chat authority should be inferred from this page. |

## Split-recovery ownership rule

No backend Area-A rows were added. Historical A+B increment files remain source evidence only and must not be counted as B ownership or global-union coverage; where such temporary files are later edited safely they require the marker `HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP` until D confirms Area A has absorbed them.

## Next reconciliation target

Continue direct inspection of still-unreconciled tracked `frontend/` files, then fold all verified incremental rows into the canonical ledger. Keep `MAPPING_STATUS: IN_PROGRESS` until a fresh recursive B-scope tree comparison proves exactly one canonical row per owned tracked file and only then assert literal `UNACCOUNTED_FILES: 0`.
