# Area B file-coverage increment — 2026-09-18 17:32 CEST

MAPPING_STATUS: IN_PROGRESS

This increment is durable source evidence for the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global completion or `UNACCOUNTED_FILES: 0`.

## EXPLICIT FILE COVERAGE LEDGER INCREMENT

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/components/ui/Field.tsx` | READ | Directly inspected at PR #660 head `3ac671b1c667a94f08303076f0818383cde98d52`. Shared accessible field wrapper: preserves/provides control id, links label via `htmlFor`, merges existing `aria-describedby` with generated hint/error ids, propagates required state, and sets `aria-invalid` when an error is present. Uses `cloneElement`; therefore it depends on the supplied control accepting the injected native/ARIA props and does not itself validate values or provide mutation authority. |

## Split-recovery ownership note

No backend Area-A row was added. Historical A+B increment material remains source evidence only and MUST NOT count as B ownership or global-union coverage; documents carrying such material are to remain marked `HISTORICAL_A_SOURCE_NOT_UNION_OWNERSHIP` until Area A/D confirms absorption.

## Reconciliation state

The canonical B document currently still carries a stale `MAPPING_STATUS: COMPLETE` marker despite the maintainer's literal-file requirement. This increment intentionally keeps `MAPPING_STATUS: IN_PROGRESS`. A fresh full B-owned tree-to-ledger reconciliation is still required before `UNACCOUNTED_FILES: 0` can be asserted.
