# Area B file-coverage increment — 2026-09-19 18:31 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It is not a claim of global-union coverage and contains no Area-A ownership.

Fresh-tree baseline checked at run start: `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Existing PR #660 branch was used; no branch/PR/runtime-product changes were created.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/app/useAppRouter.ts` | READ | Directly inspected complete source from fresh master. Browser-history/router hook: resolves current pathname through `resolveRoute`; canonicalizes with `replaceState`; synchronizes on `popstate`; same-origin `navigate` preserves destination query/hash and uses push/replace history; external-origin destinations delegate to `window.location.assign`. No persistence/domain/authorization authority. Failure boundary: `new URL(href, window.location.href)` is unguarded, so a non-parseable supplied href can throw from `navigate` rather than degrade to a handled navigation failure. |

## Reconciliation state

The canonical Area-B document still carries a historical `MAPPING_STATUS: COMPLETE` claim but does not yet contain the maintainer-required literal one-row-per-B-owned-file canonical ledger. Therefore that completion claim is not defensible under issue #656's current acceptance rule.

`UNACCOUNTED_FILES: 0` is deliberately **not asserted**. A fresh full tracked-tree set reconciliation remains required before completion, including all tracked `frontend/` files and canonical operator design-reference files/assets under `docs/design-references/` that determine frontend behavior/appearance.
