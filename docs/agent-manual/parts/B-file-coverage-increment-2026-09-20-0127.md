# Area B file coverage increment — 2026-09-20 01:27 Europe/Rome

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_DEFENSIBLY_ZERO

Fresh baseline for this run: `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. This increment is B-only and must be consolidated into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`; it does not assert global-union coverage.

## EXPLICIT FILE COVERAGE LEDGER — inspected increment

| path | status | concise role / reason |
|---|---|---|
| `frontend/src/components/ui/Surface.tsx` | READ | Directly inspected from fresh master. Minimal presentation/container primitive: accepts only `section`, `article`, or `div` through `as` (default `section`), prepends `ui-surface` while preserving caller `className`, forwards ordinary `HTMLAttributes<HTMLElement>`, and renders caller children. It owns no state, persistence, validation, authorization, backend call, focus management, or domain semantics. Semantic correctness therefore remains a caller responsibility: choosing `div`/`section`/`article` does not automatically supply a heading, landmark label, live-region behavior, or domain authority. |

### Failure-mode / authority note

`Surface` is deliberately thin. Its polymorphism is closed to three container elements, so it cannot itself become a button/link/form/dialog; however, callers can still attach arbitrary HTML attributes/events through the forwarded props. The presence or styling of a `Surface` must never be treated as evidence that an operation is wired, authorized, persisted, or semantically announced to assistive technology.

### Run-end reconciliation state

Fresh tracked B scope has **not** yet been exhaustively reconciled against one canonical row-per-file ledger, so completion remains prohibited. The canonical B document currently carries an older `MAPPING_STATUS: COMPLETE`; that status is stale relative to the maintainer's literal-file requirement and must not be used to assert `UNACCOUNTED_FILES: 0` until the full tracked `frontend/` plus canonical operator design-reference set has been mechanically reconciled.

Next coverage target: continue the fresh tracked frontend tree immediately after the shared UI primitives, then reconcile all accumulated B increments into the canonical ledger without importing historical Area-A rows as B/global ownership.
