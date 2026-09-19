# Area B explicit file coverage increment — 2026-09-19 16:30 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

This is durable Area-B-only source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership and contains no Area-A rows.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/app/routes.ts` | READ | Directly inspected from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Defines production/legacy route identities, primary/peer/roadmap navigation, pathname normalization, canonical redirects, DEV-only local-chat exposure, and explicit not-found resolution. Failure boundary: `normalizePathname` deliberately leaves non-root-relative or protocol-relative-looking paths unchanged rather than coercing them; `resolveRoute` throws if a configured redirect target is absent, making redirect-table drift fail explicitly rather than silently routing elsewhere. This file is routing/navigation authority only; it provides no backend mutation, persistence, authorization, or domain authority. |

## Reconciliation note

The canonical Area-B document still carries a historical `MAPPING_STATUS: COMPLETE` claim without the maintainer-required literal one-row-per-B-owned-file canonical ledger. That claim remains non-defensible. Do not assert `UNACCOUNTED_FILES: 0` until a fresh tracked-tree set comparison proves every file under `frontend/` plus every B-owned canonical operator design reference is represented exactly once with verified status.
