# Area B explicit file-coverage increment — 2026-09-19 00:27 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for incorporation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union completion and contains no Area-A ownership rows.

## EXPLICIT FILE COVERAGE LEDGER INCREMENT

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/shell/Rail.tsx` | READ | Directly inspected. Primary-navigation rail: renders JarvisOS workspace identity and maps the canonical `PRIMARY_NAV_ITEMS` registry into `AppLink` entries, marking the current primary destination with `aria-current="page"`. Navigation is delegated through the caller-provided `navigate` function. No backend fetch, persistence, mutation, authorization, provider/secret handling, engineering-runtime, or AI authority exists in this file. |

## Failure-mode notes

- The rail does not own route truth: item membership/hrefs come from `app/routes.ts`, while navigation behavior comes from `AppLink` and the injected `navigate` callback. A visible rail entry therefore must not be treated as evidence that the destination backend capability exists.
- Current-page semantics depend on the caller supplying the correct `PrimaryNavId`; this component does not derive or validate route state itself.

## Reconciliation state

Fresh PR head before this increment was `833ee27e7352f30debbeeb0a8ec4281127f0a641`; PR #660 remained open on `docs/capability-map-B-frontend-ux`, with base/master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. The tracked shell directory was re-enumerated from that head before inspection.

Canonical `B-frontend-operator-ux.md` still contains a stale `MAPPING_STATUS: COMPLETE` declaration and does not yet defensibly prove literal one-row-per-owned-file reconciliation. Therefore Area B remains `IN_PROGRESS`; `UNACCOUNTED_FILES: 0` is deliberately not asserted.