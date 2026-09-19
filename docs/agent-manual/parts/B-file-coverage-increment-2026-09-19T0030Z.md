# Area B explicit file coverage increment — 2026-09-19T00:30Z

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_DEFENSIBLY_ZERO

This increment is durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not broaden Area B ownership beyond the tracked `frontend/` tree and canonical operator design references.

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/shell/LegacyDiagnosticSurface.tsx` | READ | Directly inspected. Presentation-only wrapper for transition/legacy diagnostic routes: labels the supplied title and caller-provided children, and visibly marks the surface stale via `StatusBadge`. No navigation, fetching, persistence, mutation, authorization, focus management, or backend authority. |
| `frontend/src/components/shell/MigrationPendingSurface.tsx` | READ | Directly inspected. Explicit migration/unavailable placeholder: renders supplied title/description, changes eyebrow/notice tone from migration-pending to unavailable, and optionally exposes related-route `AppLink`s through injected navigation. It does not infer availability, fetch data, persist state, mutate backend state, authorize actions, or fabricate capability. |

Fresh branch evidence at run start: PR #660 open, head `73f5c72b23c1917631d50d5a9cb8b03698a4bc36`; base/master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Shell directory enumeration verified both paths as tracked B-owned files before inspection.

Completion remains blocked on literal reconciliation of every B-owned tracked path into the canonical ledger; do not interpret prior capability-level `MAPPING_STATUS: COMPLETE` prose as file-coverage completion.
