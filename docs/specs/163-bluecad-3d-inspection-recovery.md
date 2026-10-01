# 163 — BLUECAD 3D inspection recovery

State: **ready**. Combined definition/contract/readiness under the maintainer directive of 2026-10-01. Dependencies 006, 023 and 161 are merged or come before this; it depends on 161's shell navigator reopen affordance. It owns `ModelStage`, `components/bluecad/*`, BLUECAD artifact registration and serving, and the dead `pages/BlueCAD.tsx`.

## Fresh evidence (master `fc34a316`)

The three.js/OrbitControls GLB viewer is still connected (`/design/bluecad` → `ModelStage` → `BluecadWorkbench` → `BluecadGlbViewer`), and it auto-selects the first candidate. It is invisible because of the following:

1. **No geometry exists.** Every workspace on the operator data root has zero candidates. Candidate creation accepts only external paid tiers (`_validate_loop_config`). With paid AI off, every brief parks as `budget_blocked`. No deterministic, provider-free way to make geometry is exposed. The bundled-047 CAD link needs a prior verified model run.
2. **The empty state looks like a broken viewer.** A 34 rem graph-paper background, orbit help text and nine permanently disabled "future authoring" buttons make it look like a viewport.
3. **Discoverability.** On final routes the navigator, which holds the candidate list and brief, cannot be reopened once closed.

`model.step` and `model.stl` are written but not registered or served. `pages/BlueCAD.tsx` is unreachable dead code.

## Accepted capability

1. A provider-free deterministic path creates a BLUECAD candidate from explicit operator parameters, using a template over the existing GeometrySpec part builders such as tube or manifold. It goes through the same spec canonicalization, build, validation, evidence and GLB export path as the loop. It needs no AI call and no provider.
2. When a candidate has a GLB, the 3D viewer is the dominant surface:
   - orbit, pan and zoom;
   - a reset or fit view;
   - a small set of standard view angles behind compact secondary controls.
3. The empty state says plainly that no geometry exists yet. It offers the two real creation routes: a deterministic template, and an AI brief with the truthful provider and budget state. It opens the navigator or creation form directly.
   - The disabled future-authoring toolbar and the fake viewport grid are removed.
4. Registered, served STL (mm) and STEP downloads sit behind a secondary Export menu for an inspected candidate. This is the minimal print handoff.
5. The dead `pages/BlueCAD.tsx` is deleted.
6. A decision-quality Bambu Lab / Bambu Studio research record is kept in `docs/implementation/163-bambu-integration-research-2026-10-01.md`. Its recommendation: file handoff only (BLUECAD owns design; Bambu Studio owns slicing, presets and printer). It is reflected in the idea-intake register. The bounded follow-up is registered as `planned` 165.

## Boundaries / non-goals

- No change to the AI loop's external-tier policy, provider defaults or budget.
- No new geometry kernel or part kind.
- No canonical promotion without the existing promotion action.
- No 3MF export, slicer invocation, printer networking, access codes, cloud APIs or embedding. Those are 165, or rejected.

## Required evidence

- **Backend tests:** deterministic template creation produces a valid candidate with a GLB, STL and STEP, with zero `ai_jobs` rows. Invalid parameters are refused. The artifact serving boundary is unchanged.
- **Real build123d geometry on the canonical host:**
  - a template tube candidate is created through the real API;
  - its GLB loads in real Chromium;
  - orbit, zoom and view-angle interaction is screenshotted at 1280 and 1440 px;
  - STL and STEP downloads succeed;
  - no horizontal overflow;
  - the empty state is screenshotted.
- Exact-head CI green.
