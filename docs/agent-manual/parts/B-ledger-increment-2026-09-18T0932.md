# Area B explicit ledger increment — 2026-09-18 09:32 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union completion.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/app/AppLink.tsx` | READ | Same-origin SPA link adapter. Preserves modified-click/download/non-self-target browser behavior; intercepts only ordinary same-origin primary clicks and delegates canonical navigation. |
| `frontend/src/app/routes.ts` | READ | Canonical frontend route/nav registry and redirect normalization. Production routes include Design, Memory, Development, Coding, Settings, Runs, Engineering Data, Review, AI Threads and legacy diagnostics; `/legacy/dev-local-chat` is DEV-only. Unknown routes remain explicit not-found. |
| `frontend/src/app/selection.ts` | READ | Typed transient operator-selection contract spanning canonical record refs, ephemeral BLUECAD geometry hits, binding-resolution states, and resolved BLUECAD parts. Distinguishes ephemeral viewer identity from canonical workspace/record identity. |
| `frontend/src/app/useAppRouter.ts` | READ | Browser-history router hook. Canonicalizes paths with replaceState, synchronizes popstate, preserves query/hash, uses push/replace for same-origin navigation, and hands cross-origin destinations to `window.location.assign`. |

Failure-mode notes: route identity is pathname-derived while query/hash are preserved but do not select a different route; selection types are presentation/context contracts and do not themselves confer mutation authority. `AppLink` intentionally does not hijack modified/external/download/targeted navigation.

Next: continue literal inspection of remaining B-owned tracked files and consolidate all increments into the canonical ledger before any COMPLETE claim.
