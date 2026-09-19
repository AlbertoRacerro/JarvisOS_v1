# Area B explicit file coverage increment — 2026-09-19 17:32 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

Fresh baseline verified before inspection:
- master/base SHA: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`
- PR #660 prior head: `0978aebaf081cbc60d2a757ebd1e6376749b621f`
- branch: `docs/capability-map-B-frontend-ux`

This increment is Area B only. It does not claim global-union coverage and adds no backend Area-A ownership.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `frontend/src/app/useAppRouter.ts` | READ | Directly inspected in full from fresh master. Browser-history router hook: resolves `window.location.pathname`, canonicalizes redirects with `replaceState`, subscribes to `popstate`, and exposes same-origin SPA navigation preserving destination search/hash. External-origin navigation delegates to `window.location.assign`. No persistence/domain/authorization authority. Failure boundary: `new URL(href, window.location.href)` is unguarded, so a non-parseable supplied href can throw from `navigate`; route state intentionally stores only resolved pathname identity, while query/hash remain in browser location and are consumed elsewhere. |

## Reconciliation note

The canonical `B-frontend-operator-ux.md` still carries an older `MAPPING_STATUS: COMPLETE` capability-level claim but does not yet contain the maintainer-required literal one-row-per-B-owned-file canonical ledger. That claim is therefore not treated as valid completion evidence. This increment remains `IN_PROGRESS`; `UNACCOUNTED_FILES: 0` is not asserted until a fresh tracked-tree set reconciliation is complete and the canonical ledger is consolidated.
