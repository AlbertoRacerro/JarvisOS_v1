# Area B explicit file coverage ledger increment — frontend entrypoint

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: NOT_YET_RECONCILED

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` and PR #660 branch state inspected 2026-09-19. This increment is B-only source evidence for canonical consolidation into `B-frontend-operator-ux.md`; it is not a completion claim.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `frontend/src/main.tsx` | READ | React/Vite browser entrypoint. Directly inspected in full from fresh master: imports `App`, applies stored visual preferences before render, imports the ordered global/operator CSS stack, and mounts `<App />` under `React.StrictMode` into `#root`. It has presentation/bootstrap authority only; no backend/domain persistence or operator mutation authority. The unchecked `document.getElementById("root") as HTMLElement` cast means a missing/misnamed root element is not handled locally and would fail during React root creation. |

### Inspection notes

`main.tsx` establishes CSS cascade order explicitly through import order: tokens/global/foundation/shell first, then fusion/operator/surface-specific layers, responsive rules, and finally `100g-ui-repair.css`. This makes stylesheet order part of the effective operator presentation contract even though this file itself contains no styling logic.

The call to `applyStoredVisualPreferences()` occurs before `ReactDOM.createRoot(...).render(...)`, so stored appearance/accent state is applied at bootstrap rather than waiting for a mounted Settings surface.

### Completion guard

Do not promote this increment to `MAPPING_STATUS: COMPLETE`. A fresh literal set reconciliation across the entire tracked `frontend/` tree and canonical operator files/assets under `docs/design-references/` is still required, and every owned path must appear exactly once in the canonical `## EXPLICIT FILE COVERAGE LEDGER` before `UNACCOUNTED_FILES: 0` is defensible.
