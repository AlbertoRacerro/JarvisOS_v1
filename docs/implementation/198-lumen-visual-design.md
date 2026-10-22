# 198 STUDIO-VISUAL-DESIGN-1 — implementation evidence

Spec: [198-studio-visual-design.md](../specs/198-studio-visual-design.md). The spec allows several PRs under this
identity; the STATUS row stays `in_review` until the final one merges.

## Slice 1 — tokens, appearance, shell, BlueCad spelling

What changed (presentation and scoped copy only; no backend, API, persistence, routing or scientific change):

- **Canonical tokens** (`frontend/src/styles/tokens.css`): Lumen Light (Herbarium-inspired daylight on Lumen
  geometry) and Lumen Dark (approved canopy) for surfaces, ink, rules, selection, status, chart, flowsheet and
  technical-viewport roles, plus `--lumen-*` depth tokens (field light, glass islands, rail, emblem, shadows).
  Selected by the existing appearance preference (`system`/`light`/`dark`); no `?direction=` switcher, round-1
  directions or exploration storage key ship.
- **Accent** (`frontend/src/theme.ts`): the Microalgae preset seed is the Lumen chlorophyll `#8DB943`; presets,
  custom HEX and storage keys are unchanged. Accent text now shades the seed toward AA contrast against the deepest
  Lumen light tint (`#E2EEC8`) / raised dark surface (`#142318`) instead of jumping to black/white. The lit accent
  fill is a gradient derived from the seed (plain-seed fallback without `color-mix`).
- **Composition** (`frontend/src/styles/lumen.css`, imported last, no `!important`): lit botanical field, detached
  glass rail carrying the emblem and Bricolage wordmark, glass navigator/sidecar islands, Studio islands, viewport
  frame, rounded fields, Lumen primary-action fill.
- **Reduced overrides at their owners**: peer tabs (Design, Settings, Memory/Development/Coding) become one segmented
  capsule with a soft-accent active segment (100g: never the primary-action fill); the `--fusion-*` palette now
  resolves through the canonical tokens, so Memory/Development/Coding follow the appearance; Studio header no longer
  stretches into an empty band; the 9 px Process/BlueCad header subtitles use the 12 px caption token.
- **BlueCad spelling**: rendered product strings, route title and labels say BlueCad; eyebrows keep authored case so
  CSS no longer re-uppercases it. Identifiers (`BLUECAD_SEMANTIC_KEY`), API paths and comments are unchanged.
- **Assets**: Lumen emblems in `frontend/public/brand/`; Bricolage Grotesque (SIL OFL 1.1, licence text and
  provenance in `frontend/public/fonts/`) served locally. No new dependency or network egress.

### Verification at the slice-1 head

- `npm run build` (full frontend suite incl. new `tests/198-lumen-identity.mjs`, `tsc`, `vite build`): pass.
- `scripts/check_bluecad_workbench.py`: pass (empty-state marker updated to BlueCad). `check_app_shell.py`,
  `check_model_inspection.py` and `check_ui_foundation.py` fail identically on `origin/master` (stale pre-existing
  contracts; unchanged by this slice).
- Real Chromium (Playwright 1.55, isolated backend with a temp data root and one workspace): all 19 production routes
  × Dark/Light × 1440 px/390 px = 76 captures, every capture resolved the requested `data-theme`. Evidence:
  `/home/thera/jarvis-control/work/evidence/198a-browser/` (`capture.mjs`, `r4/report.json`, `r4/*.png`).
  - Page/console errors: 0, apart from one `429` from the backend's GitHub read on Coding → Repository (rate limit,
    environmental).
  - Computed text contrast (blended background stack, WCAG AA): 2,978 failures before the `--fusion-*` remap, 564
    after. 0 failures on Studio, Studies, Settings, Runs, Engineering Data, Review and AI Threads.
  - Focus: 432 tab stops audited, 14 without a visible indicator, all the Jarvis sidecar message field.
  - Rendered `BLUECAD`: only the backend-originated sidecar message “No valid BLUECAD candidate is available…”
    (`backend/app/modules/workspace_actions/service.py`) and relay transcript text quoted by Coding → Runtime.

### Audit findings carried to slice 2 (surfaces)

| Finding | Where | Disposition |
| --- | --- | --- |
| ~800 literal colours remain in surface sheets (`global.css`, `ProcessDraftEditor.css`, `final-fusion.css`, `JarvisSidecar.css`, `ProcessStage.css`, roadmap, PBR/run-result panels, Coding workbench) | Process, Coding, Development, sidecar | Slice 2: move onto tokens. These cause the remaining 564 contrast failures (largest: Coding Runtime ids/kinds, Roadmap calendar, sidecar hint/welcome). |
| Sidecar message field focus uses the light focus separator only | Jarvis sidecar | Slice 2: visible focus ring on the composer. |
| Chart series colours hard-coded for light (`ProfileChart`, `SyncCharts`, `PbrDynamicRuns`) | Dynamic/PBR charts | Slice 2: series tokens per appearance, keeping series identity. |
| BlueCad WebGL scene background/grid fixed light | BlueCad viewport | Slice 2: viewport background token, geometry rendering unchanged. |
| Sub-12 px labels (`8px`/`9px`/`10px`) in final-fusion, Coding and sidecar sheets | several | Slice 2 audit fixes (density/hierarchy). |
| Backend message spells BLUECAD | Workspace actions service | Outside 198 (no backend change); record for a backend copy follow-up. |
