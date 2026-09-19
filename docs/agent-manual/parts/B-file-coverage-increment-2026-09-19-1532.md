# Area B file coverage increment — 2026-09-19 15:32 CEST

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

Scope remains strictly Area B: tracked `frontend/` plus canonical operator design references under `docs/design-references/`. This increment is durable source evidence for later consolidation into the required canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`; it does not make a global-union or zero-unaccounted claim.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/app/AppLink.tsx` | READ | Internal-link adapter around a real `<a>`: invokes caller `onClick` first, preserves browser behavior for prevented/default-non-primary/modifier clicks, downloads, non-`_self` targets and cross-origin destinations, and intercepts only same-origin primary navigation to call the app router with pathname+search+hash. No persistence, backend mutation or authorization authority. |

## Failure-mode notes

- Same-origin classification is computed with `new URL(href, window.location.href)` and interception is deliberately bypassed for external origins; this prevents the SPA router from swallowing external navigation.
- Modified clicks and non-primary mouse buttons are deliberately left to native anchor behavior, preserving new-tab/window workflows.
- Caller `onClick` executes before interception and can cancel routing with `preventDefault()`; consumers therefore retain explicit control over navigation suppression.
- The component trusts the supplied `navigate` callback after same-origin parsing. It does not itself validate route existence, authorization, or semantic destination validity; those guarantees must come from the router/route-resolution layer.
- `new URL(...)` is not guarded locally. An invalid `href` capable of throwing would fail the click handler rather than falling back to native navigation; current callers therefore should provide URL-parseable hrefs.

## Reconciliation state

Fresh PR #660 head at run start: `df0327c3f71b74948dd436b33dfd02de478996f3`; fresh base/master recorded by the PR remains `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

The canonical Area-B document still contains a historical `MAPPING_STATUS: COMPLETE` while the required literal one-row-per-owned-file canonical ledger has not yet been consolidated. That claim remains non-defensible and must not be used as completion evidence. This increment therefore remains `IN_PROGRESS`; `UNACCOUNTED_FILES: 0` is explicitly not asserted.

No backend-A rows were added. Historical A+B increment evidence remains non-union ownership evidence until Area A absorption is confirmed.
