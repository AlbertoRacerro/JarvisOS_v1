# Area B explicit file-coverage increment — 2026-09-20 00:28 CEST

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for later consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It is B-only and MUST NOT be interpreted as global-union coverage.

Fresh baseline checked at run start: master/base `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; PR #660 head before this increment `8baa0f62f29895d21c34045bb3cf23a7523350fa`.

## EXPLICIT FILE COVERAGE LEDGER — incremental evidence

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/ui/StatusBadge.tsx` | READ | Directly inspected from fresh master. Thin `<span>` status-presentation primitive. Requires an explicit `tone` from the closed `StatusTone` union (`info`, `success`, `warning`, `danger`, `neutral`, `proposed`, `stale`, `unavailable`, `synthetic`, `archived`), composes `ui-status-badge` plus tone/caller classes, and forwards native span attributes. It assigns no semantic `role`, live-region behavior, persistence, validation, authorization, or backend authority; therefore badge appearance/tone is presentation supplied by the caller and cannot itself prove the underlying state or capability. |

## Failure-mode note

`StatusBadge` deliberately has no built-in accessibility announcement semantics. A dynamically changing critical status is not automatically announced merely because its visual tone is `danger`; the consuming surface must provide the appropriate semantic/live-region behavior when required. Likewise, caller-supplied `tone` is a visual projection, not deterministic evidence that the represented backend/domain state is true.

UNACCOUNTED_FILES: NOT_YET_DEFENSIBLE

Completion remains blocked on literal fresh-tree reconciliation of every tracked `frontend/` file plus canonical operator design-reference assets. Do not assert `UNACCOUNTED_FILES: 0` from this increment.