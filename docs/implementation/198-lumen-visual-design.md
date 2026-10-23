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
  `/home/thera/jarvis-control/work/evidence/198a-browser/` (`capture.mjs`, `r5/report.json`, `r5/*.png`, captured from the built head recorded in `r5/HEAD.txt`).
  - Page/console errors: 0 (an earlier run saw one transient `429` from the backend's GitHub read on Coding → Repository;
    environmental).
  - Computed text contrast (blended background stack, WCAG AA): 2,978 failures before the `--fusion-*` remap, 564
    after. 0 failures on Studio, Studies, Settings, Runs, Engineering Data, Review and AI Threads.
  - Focus: 433 tab stops audited, 14 without a visible indicator, all the Jarvis sidecar message field.
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
| Legacy top-bar routes (Runs, Review, AI Threads, Engineering Data) keep a full-width accent outline on the focused main region and the older top bar chrome | non-final shell | Slice 2: restyle or retire the redundant chrome. |
| Backend message spells BLUECAD | Workspace actions service | Slice 2 normalizes the Sidecar display copy, including its disclosure; the backend payload remains unchanged. |

## Slice 2 — remaining surfaces and responsive audit (PR #882, draft)

The frontend branch `impl/198-lumen-surfaces` moves Process, Dynamic, Coding,
Development, Sidecar, BlueCad and chart colours to the canonical Lumen roles.
Charts retain their series order and data; the WebGL viewer reads its scene and
grid colours from appearance tokens. A display-only Sidecar conversion spells
BlueCad in backend-owned workspace context; the payload and persisted data are
unchanged. The narrow Roadmap, Brainstorm and Memory layouts now stack their
panels, and the BlueCad navigator uses the available width.

At frontend head `61ce73ab`, `VITE_API_BASE_URL=http://127.0.0.1:8198 npm run
build` passed the full frontend suite, type check and Vite build. CI on PR #882
passed backend, frontend-build, classify and evidence checks at that head.
`git diff --check` passed. The isolated browser used a temporary
`JARVISOS_DATA_ROOT`, `JARVISOS_CORS_ORIGINS=http://127.0.0.1:5198`, backend
port 8198 and frontend preview port 5198. Evidence is under
`/home/thera/jarvis-control/work/evidence/198b-browser/`.

| Browser evidence | Result |
| --- | --- |
| `r2/report.json` on the pre-repair branch | 76 route/theme/width captures; 4 text-contrast failures and 15 Sidecar composer focus flags. |
| `r3/report.json` after focused CSS repair | 6 affected captures; zero contrast, focus or console errors. |
| `r7/report.json` at `61ce73ab` | 19 routes × Dark/Light × 1440/390 = 76 captures, 0 computed text-contrast failures, 0 focus flags across 433 checked tab stops, 0 wrong themes. The 4 console errors are anonymous GitHub API `429` responses on Coding → Repository; the UI shows its explicit read-error state. |
| `r7/bluecad-populated-{dark,light}-1440.png` | A real deterministic template tube was created in the isolated workspace and rendered in the WebGL canvas in both appearances, with no page/console errors on those captures. The light grid was reduced after the earlier populated capture. |
| `r7-first3-debug/report.json` | Focused rerun of Process, Studies and BlueCad in both themes/widths: 12 captures, no rendered `BLUECAD`, contrast or focus failures. |
| `r9/report.json` at `6599d38c` | Instrumented 76-capture rerun located every uppercase hit in Coding → Runtime's quoted Relay transcript: source commands, tool output and earlier commentary, not product-authored copy. The four GitHub `429` console errors remain on Coding → Repository; contrast/focus/theme results remain zero failures. Preserve the transcript verbatim. |

At code head `d687c721`, `r8/report.json` and the paired screenshots opened
the Sidecar workspace-context disclosure over the populated WebGL viewport in
both appearances: one canvas, correct theme, no uppercase product name in
rendered body text and no page/console errors. The frontend build and suite
passed again at this copy-only head. The instrumented full matrix resolved the
spelling flags as quoted evidence. No backend or GitHub behaviour was altered to
suppress the earlier GitHub 429s.

### Final exact-head browser run (`1e46ea90`)

`r11/` holds the final evidence. Its build log is `r11/build.log`, `r11/HEAD.txt` records the head, and
`r11/run2/report.json` plus 76 screenshots hold the matrix results. At code head `1e46ea90`,
`VITE_API_BASE_URL=http://127.0.0.1:8198 npm run build` passed the full frontend suite, the type check and the Vite
build. The audit ran on a fresh copy of the isolated data root, with the same ports and CORS origin as above.

| Run | Result |
| --- | --- |
| `r11/report.json` | 76 captures. 12 console errors, all on BlueCad: the copied fixture's artifact rows still held absolute paths into the original data root, so the backend correctly refused them with `404`. This is a harness error, not a product error. |
| `r11/run2/report.json` | Same matrix after rewriting those 7 `stored_path` rows into the copied root: **76 captures, 0 page/console errors, 0 text-contrast failures, 0 focus flags across 434 tab stops, 0 wrong themes**. The anonymous GitHub API quota had reset, so Coding → Repository loaded without `429`s. |

The 4 remaining `BLUECAD` flags are all on Coding → Runtime. A DOM probe at this head placed every hit in the quoted
Relay transcript (`.coding-relay-timeline` `pre`/`summary`) or in spec names and STATUS summaries in the work list
(`BLUECAD-PRINT-HANDOFF-1`, `BLUECAD-PROJECT-TREE-1`, …). §4 of the contract leaves spec names unchanged, and the
transcript is kept verbatim. All acceptance criteria now have evidence on the exact code head.
