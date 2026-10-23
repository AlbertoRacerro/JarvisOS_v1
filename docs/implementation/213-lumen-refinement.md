# 213 LUMEN-REFINEMENT-1 — implementation evidence

Spec: [213-lumen-refinement.md](../specs/213-lumen-refinement.md), from maintainer
[issue #900](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/900). Frontend presentation only: no backend,
API, persistence, engine/solver, unit, Studio runtime or model-versioning change.

## What changed and why

| # | Item | Change |
| --- | --- | --- |
| 1 | Two button languages | The old default button (flat full-accent fill, 8 px corners, `foundation.css`) was the source of the square, glaring green controls. It is now one Lumen family: every button is a capsule; the default is a quiet **tonal fill** (accent-subtle surface, accent border, accent text), so Design keeps filled buttons; `primary-button` and existing primary roles keep the lit accent fill and are reserved for one main action per view (Create process draft, Create tube/manifold, Promote to Decision, empty-state New model, Jarvis send); secondary/ghost stay outlined. Memory/Literature/Development/Coding inherit the same family where they used defaults. |
| 2 | Switcher moves | The Process / BlueCad / Studio switcher left the three page headers and lives in the rail under **Design**. It has identical screen coordinates on all three surfaces whatever each header or the BlueCad navigator does (browser check: same box `x 37, y 232` everywhere). On narrow widths it becomes a row under the rail capsule. |
| 3 | Active project/version context | Audit below. Clarity fix only: the BlueCad navigator workspace selector now states “BlueCad only · Process and Studio keep the app workspace” (visible caption, `aria-describedby`, tooltip). |
| 4 | Tree → viewport | Selecting a part in the project tree (or in the inspector, or by clicking the mesh) now **highlights that mesh in the viewport** with the accent (per-mesh material clone, original restored on deselection and disposal). Part rows say “Highlight in the viewport and inspect” / “highlighted”, other content rows “Open in the inspector”. |
| 5 | Sidecar default | Jarvis opens by default on Studio as on Process and BlueCad; closing works as before. |
| 6 | Resizable panels | The navigator and the Jarvis sidecar have WAI-ARIA window splitters (pointer drag, Arrow ±16 px, Shift+Arrow ±64 px, Home/End, double-click reset) overlaid on the main area’s inner edge. Bounds: navigator 200–480 px, sidecar 280–640 px; widths persist per browser (`jarvisos:panel-widths:v1`, visual preference only). Hidden at ≤ 760 px where panels stack. |
| 7 | Lumen Light hue | Every yellow-green Lumen Light token (OKLCH hue 95–142°) was moved to the 146–156° pine/fern family with lightness kept and chroma reduced (×0.72), so harmony improves without more saturation. Default Light accent `#357D4D` (was `#8DB943`); e.g. canvas `#eef0e1 → #e8f1e9`, green-700 `#4f8a22 → #3c8a5b`. Lumen Dark is unchanged (approved). |
| 8 | Custom accents | The free HEX picker is gone. Six curated accents, each with its own Light and Dark seed: Microalgae (default), Leaf Chlorophyll, Lagoon, Glacier (blue), Iris (violet), Ember (orange). Light seeds sit near OKLCH L 0.53 / C 0.10 (white text ≥ 4.5:1 on fills), Dark seeds near L 0.77 (black text ≥ 9:1); Dark Microalgae keeps `#8DB943`. A stored pre-213 custom HEX migrates to the perceptually nearest preset (OKLab); invalid storage falls back to Microalgae. Swatches preview the seed of the current appearance. |
| 9 | Numeric steppers | New shared `NumericInput` (`components/ui`) replaces every `type="number"` field outside the legacy AI Draft page (70 call sites across Studio, BlueCad, Process, Dynamic, Environment, Studies, procedures, Memory). Stepping is magnitude-aware in the field’s own unit — ≥ 1 by 1, below 1 by tenths, then hundredths… — snaps to the step grid, never crosses zero toward negatives, and respects declared bounds (inclusive/exclusive minimum, maximum, whole numbers) from the existing field specs, Studio variable min/max and physical sign (e.g. temperature and pressure > 0, mass flow and fractions ≥ 0). Typing stays free and owner validation is unchanged. The field is a `spinbutton` with ArrowUp/ArrowDown and small step buttons. |
| 10 | Solver console | Starting a Run scrolls the spec 210 live console into view (focus stays on the toolbar), and while a solve exists the toolbar shows a “Live solver console” / “Solver console” shortcut that scrolls to and focuses it. |

## Item 3 audit: what the BlueCad selection governs today

- The app has one **active workspace** (App state, persisted in local storage) used by Process, Studio, Memory and the Jarvis sidecar. Studio’s “Open example workspace” switches it.
- The BlueCad navigator **Workspace** selector is **local to BlueCad**: it initialises to the first workspace returned by the API, does not read the app workspace and does not change it. Choosing “BlueRev Model Foundry” in BlueCad therefore governs only the BlueCad candidates and viewport; the Process flowsheet and Studio artifacts keep the app workspace. They can silently differ (e.g. after opening the Studio example workspace).
- BlueCad has **no version concept**: candidates are geometry variants with a lifecycle; Studio models have published versions; Process drafts have revisions. Nothing links them as one project version.
- Before this change the UI did not say any of this. The caption now states the BlueCad-only scope. A shared project/version model is out of scope here and owned by the Design architecture directive ([issue #901](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/901), decision 1).

## Partial and future work

- **Item 4:** highlight is implemented; the camera does not yet frame (zoom to) the selected part. Gap: `setView` fits the whole scene; framing needs a per-mesh bounding box fit in `BluecadGlbViewer` — small, but left out to keep camera behaviour unchanged here.
- **Item 6:** the in-stage Process boundary between flowsheet and its unit inspector (`draft-body--inspector` grid) is not yet draggable; the shell navigator/sidecar splitters cover the main work-area boundaries named in the issue. Same splitter component can be reused there.
- **Item 3:** consolidating BlueCad onto the app workspace (or a project/version selector in the top bar) belongs to issue #901 Phase 1.
- The legacy AI Draft diagnostic page keeps its native number inputs (diagnostic route, outside Design).

## Verification at head `ec033853`

- `npm run build` (full frontend suite including new `tests/213-lumen-refinement.mjs`, `tsc`, `vite build`): pass. Three earlier source-pinning tests were updated to the accepted 213 decisions: `100-visual-identity` (curated per-appearance accents instead of Custom HEX), `100g-final-operator-ui-repair` (rail switcher instead of header peer tabs), `198-lumen-identity` (cooler Light canvas).
- Real Chromium (Playwright, isolated backend on a temporary data root with a BlueCad template candidate, the Studio example workspace and a Process draft). Evidence: `~/jarvis-control/work/evidence/213-browser/` (`HEAD.txt`, `seed.mjs`, `walk.mjs`, `capture.mjs`).
  - Interaction walk `r4/walk-report.json`: 19/19 checks pass, no page/console/HTTP errors — switcher position identical on the three surfaces and Jarvis open on all three; splitters leave the main area's edges and scrollbar free; sidecar drag +120 px, navigator keyboard +48 px, clamp at 480 px, persistence across reload, double-click reset; tree part selection changes the viewport rendering and clears; Wall stepper `3, 2, 1, 0.9 … 0.5` stopping at the 0.5 mm minimum, free typing of `0.`; Run reveals the console and the toolbar shortcut focuses it. The reveal check stubs only the solve endpoints in the browser (presentation; spec 210 semantics untouched). One earlier run logged a transient 404 before HTTP logging was added; it did not recur in five later runs.
  - Spec 198 matrix re-run, all 19 production routes × Dark/Light × 1440/390 px: before (`origin/master` build) `matrix-before/` and after `matrix-after/`: **76 captures each, 0 WCAG AA text-contrast failures, 0 missing focus indicators (434/435 tab stops), 0 wrong themes**; page/console errors 0 before and 1 after — an environmental `429` from the backend's GitHub read on Coding → Repository (Light, 390 px), as also seen in spec 198. The 4 `BLUECAD` hits are quoted relay transcript text on Coding → Runtime, identical before and after.

Exact-head review (coordinator) found and fixed before freeze: the sidecar splitter first overlaid the main area's right edge, over its scrollbar — both splitters now sit on their panel's side of the gap; capsule panel-header actions (Memory → Models “+ New model”) no longer wrap into a tall pill.

## Where to look

- Design → Process / BlueCad / Studio: rail switcher under Design; Jarvis open; splitters on the inner edges of the navigator and Jarvis; tonal vs primary buttons.
- BlueCad: select a part under **Parts** in the tree; the mesh lights up in the viewport; the “BlueCad only” caption under the workspace selector; New geometry → Wall/Outer Ø steppers.
- Process: Run → the console comes into view; “Live solver console” in the toolbar.
- Settings → Appearance: the six accents in Light and Dark.
- Before/after pairs: `matrix-before/<route>-<theme>-<width>.png` vs `matrix-after/…`.
