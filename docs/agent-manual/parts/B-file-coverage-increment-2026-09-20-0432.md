# Area B file-coverage increment — 2026-09-20 04:32 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union ownership and contains no Area-A backend rows.

Fresh run baseline: PR #660 open on `docs/capability-map-B-frontend-ux`; fresh master/base SHA `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER — increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/app/routes.ts` | READ | Directly inspected in full from fresh `master`. Defines the closed production route/nav/stage metadata contract, canonical redirects, pathname normalization, DEV-only local-chat route, and explicit not-found fallback. `normalizePathname` strips query/hash and trailing slashes only for normal single-slash absolute paths; protocol-relative/non-absolute inputs are deliberately left unmatched. `resolveRoute` throws if a configured redirect target is absent from `PRODUCTION_ROUTES`, so registry/redirect drift is a hard routing failure rather than silent guessing. Route/type presence is navigation metadata only and does not prove the referenced surface/backend capability is wired or authoritative. |

## Run reconciliation note

The canonical B document currently still says `MAPPING_STATUS: COMPLETE`, but literal B-owned file-by-file reconciliation is not yet defensible; this increment therefore preserves `MAPPING_STATUS: IN_PROGRESS` and does **not** assert `UNACCOUNTED_FILES: 0`. The next consolidation must merge this row into the canonical ledger and compare the ledger path set against a fresh tracked-tree enumeration of all `frontend/` files plus canonical operator design-reference assets.
