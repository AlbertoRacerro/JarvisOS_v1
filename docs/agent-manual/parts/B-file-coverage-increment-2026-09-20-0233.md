# Area B explicit file coverage increment — 2026-09-20 02:33 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This increment is durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global completion or `UNACCOUNTED_FILES: 0`. The canonical document currently still says `MAPPING_STATUS: COMPLETE`; that status is not defensible until literal fresh-tree reconciliation is complete and must not be treated as the current Area-B mapping state.

Fresh PR check: PR #660 is open on `docs/capability-map-B-frontend-ux`, head before this increment `9d9917338c518d45fc7569aff99f72fdcb3ddf45`, base `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/app/AppLink.tsx` | READ | Directly inspected from fresh master. SPA-aware anchor primitive: preserves native anchor behavior for prevented/non-primary/modifier clicks, downloads, non-`_self` targets and cross-origin destinations; intercepts ordinary same-origin clicks and delegates normalized pathname+search+hash to the injected `navigate`. Failure boundary: `new URL(href, window.location.href)` is unguarded, so a malformed/non-parseable `href` can throw during click handling instead of falling back to native navigation. This component supplies navigation mechanics only; it provides no route authorization or destination-capability proof. |

## Reconciliation state

- No backend/Area-A rows were added.
- No runtime/product code was modified.
- `UNACCOUNTED_FILES: 0` is deliberately not asserted.
- Next work: continue direct inspection of remaining tracked `frontend/` files and canonical operator design-reference assets, then perform a fresh-tree set reconciliation before changing canonical status to COMPLETE.
