# 182 — Process workspace layout: the flowsheet takes the central width

State: **accepted and ready**. Written under the maintainer directive of 2026-10-07 ("Lane F — Process workspace UI cleanup"). Reviewed against the Process editor at master `0b755d47`.

- **Hard dependency:** 181 (merged). It changes no science, no solver, no backend and no run semantics.

## Fresh evidence

At master `0b755d47` the Process editor keeps a permanent right column (`frontend/src/stages/ProcessDraftEditor.tsx`, `.draft-inspector`). With nothing selected that column holds only "Select a stream or unit…" and an "Open setup (species and thermodynamics)" button. The Setup drawer is stacked above the canvas, in the same central column. At 1280×800 the idle canvas is 349 px wide.

## Decision

1. **Toolbar.** The toolbar above the flowsheet holds: revision, Biology models…, Setup, Run, run state, readiness, results state, More controls. It is a labelled `role="toolbar"` ("Process actions").
2. **Setup** opens from the toolbar as an overlay drawer inside the canvas frame. When closed it takes zero width. Opening it moves focus into the drawer; Close or Escape returns focus to the toolbar button. It still opens by default on a draft with no compounds.
3. **Inspector.** The inspector column exists only while a unit or stream is selected: 300 px, or 380 px for PBR, PFR and CSTR. It closes with a × button, with Escape (outside form fields), or with a click on empty canvas, and the canvas width comes back. Focus inside a closing inspector returns to the canvas.
4. **Proposals** move to the central column, so pending proposals stay visible without a selection.
5. Preserved:
   - zoom, pan and Fit all;
   - object drag;
   - the results navigator;
   - the 181 run outcome semantics;
   - the Sidecar;
   - the single-column layout below 1100 px.

## Acceptance

- The frontend build gate passes, and it includes a new `tests/182-process-layout.mjs` covering:
  - toolbar order and the Setup toggle;
  - no inspector column without a selection;
  - inspector close by button, Escape and canvas click, with focus return;
  - the Setup overlay;
  - proposals outside the inspector.
- Chromium acceptance against a candidate backend at 1280×800, 1440×1000 and 1920×1080, in each of these states: nothing selected, unit selected, PBR selected, Setup open. It records measured canvas widths and checks for no horizontal overflow and no page errors.

## Non-goals

- Inspector content.
- A resizable splitter.
- The Sidecar layout.
- Mobile layouts below the existing breakpoint.
