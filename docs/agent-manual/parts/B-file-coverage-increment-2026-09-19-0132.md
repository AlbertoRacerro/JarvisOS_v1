# Area B explicit file coverage increment — 2026-09-19 01:32 CEST

MAPPING_STATUS: IN_PROGRESS

This is durable source evidence for consolidation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert completion or `UNACCOUNTED_FILES: 0`.

## EXPLICIT FILE COVERAGE LEDGER increment

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/shell/TopBar.tsx` | READ | Directly inspected. Thin shell header: renders caller-supplied current-route title, panel controls, and appearance control in fixed top-bar regions. It owns no navigation, persistence, mutation, authorization, focus behavior, backend I/O, or control semantics; those remain with the supplied controls/parent. |

## Evidence / failure-mode notes

- Direct branch content inspection confirmed `TopBar.tsx` imports only the `ReactNode` type, accepts `title`, `panelControls`, and `appearanceControl`, and renders them without additional state or handlers.
- Therefore the presence of a control in this header is not evidence that the control is wired, authorized, persistent, or backed by server capability.
- Fresh shell-directory enumeration on the working branch confirmed `TopBar.tsx` remains a tracked B-owned file alongside the other shell components.
- The canonical B map still contains a stale `MAPPING_STATUS: COMPLETE` declaration. Until the exhaustive one-row-per-owned-file ledger is consolidated and reconciled against a fresh recursive tracked tree, the defensible status remains `IN_PROGRESS` and `UNACCOUNTED_FILES: 0` MUST NOT be asserted.

No backend-A rows were added. Historical A+B evidence remains historical source only and must not count as B/global-union ownership.