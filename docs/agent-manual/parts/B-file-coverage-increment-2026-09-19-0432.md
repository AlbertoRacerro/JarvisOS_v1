# Area B explicit file-coverage increment — 2026-09-19 04:32 Europe/Rome

MAPPING_STATUS: IN_PROGRESS

This is durable Area-B source evidence for incorporation into the canonical `## EXPLICIT FILE COVERAGE LEDGER` in `B-frontend-operator-ux.md`. It does not assert global-union completion and contains no Area-A ownership rows.

## EXPLICIT FILE COVERAGE LEDGER INCREMENT

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/components/shell/ContextualSidecar.tsx` | READ | Directly inspected. Conditional Jarvis/Properties sidecar with focus-on-open heading, Escape close, keyboard-switchable two-tab interface, explicit unavailable/no-selection fallbacks, and selection-specific engineering/viewer identity projection. It renders caller-provided Jarvis/Properties content but owns no backend fetch, persistence, mutation, authorization, credential/provider, solver, or CAD-authoring authority. |

## Failure-mode notes

- `ContextualSidecar` projects selection identity but does not establish engineering authority. `geometry-hit` is explicitly described as ephemeral viewer-session data; unresolved/ambiguous BLUECAD binding states explicitly state that no engineering object is editable/selected.
- The component focuses its heading when opened and supports Escape closure, but does not itself restore focus to the opener. Focus restoration therefore remains a parent-shell contract and must not be inferred from this file alone.
- The tablist handles only Left/Right arrows and toggles between exactly two tabs. It does not implement Home/End behavior; any broader keyboard-tab contract would require evidence elsewhere.
- `propertiesContent` can replace the fallback body while `semanticTarget` is still rendered first for BLUECAD part/binding selections; callers must account for that composition rather than assuming full replacement of all Properties content.

## Reconciliation state

Fresh master remains `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Fresh branch enumeration verified `ContextualSidecar.tsx` as a tracked B-owned shell file before direct inspection. PR #660 remains the sole target on `docs/capability-map-B-frontend-ux`.

Canonical `B-frontend-operator-ux.md` still contains a stale `MAPPING_STATUS: COMPLETE` declaration and does not yet defensibly prove literal one-row-per-owned-file reconciliation. Therefore Area B remains `IN_PROGRESS`; `UNACCOUNTED_FILES: 0` is deliberately not asserted.