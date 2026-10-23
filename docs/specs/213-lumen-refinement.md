# LUMEN-REFINEMENT-1 — one Lumen control family, continuous Design switcher, resizable panels

Accepted outcome and readiness: maintainer [issue #900](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/900)
(visual review of the merged 198/208/209–211 surfaces on a real WSL install,
2026-10-23), scheduled by maintainer directive `L20261023112716-dcd2` alongside
spec 212 and before the Design architecture directive in issue #901. Items the
issue marks *maintainer direction* are product decisions; everything else is the
builder's design choice. Live state is recorded only in STATUS.md.

## Outcome

The app reads as one Lumen visual system, and Design surfaces behave consistently:

1. **One control family.** Every button belongs to one Lumen family of shape,
   radius, hue and luminance. Filled buttons may remain on Design surfaces as the
   primary variant, but they use the Lumen accent family, not the off-palette
   bright green. No surface keeps square, glaring legacy buttons.
2. **Switcher continuity.** The Process / BlueCad / Studio switcher sits in the
   same left position on all three surfaces, so the pointer stays put while
   switching.
3. **Active project/version context — audit and report only.** The evidence note
   states precisely what the BlueCad workspace/version selection governs today
   (Process flowsheet, Studio artifacts) and whether the UI says so. Only
   low-risk label clarifications are allowed; no shared project model (issue #901).
4. **BlueCad tree → viewport.** Tree items show what clicking does. Selecting a
   part node highlights or focuses that geometry if the current viewer supports
   it within a bounded change; otherwise the exact gap is documented as future work.
5. **Sidecar open by default in Studio**, closable as elsewhere.
6. **Resizable panels.** The Sidecar, the BlueCad navigator and the boundary
   between a main work area and its side panel have draggable, keyboard-operable
   splitters with sensible min/max widths, persisted per browser when cheap.
7. **Lumen Light hue.** The Light primary green moves from yellowish toward a
   cooler pine/fern/spirulina family without more saturation, keeping AA contrast.
8. **Curated accents.** The free hex accent picker is replaced by a curated set,
   designed per appearance (Light and Dark): a few greens plus a few other
   families (for example blue, violet, orange), harmonised with Lumen. A stored
   custom hex migrates to the nearest curated option or the default without error.
9. **Magnitude-aware numeric steppers.** The shared numeric control respects the
   parameter's valid range (no negative step for positive-only quantities) and
   steps by magnitude in the selected unit: ≥ 1 by 1, below 1 by tenths, then by
   hundredths, and so on. Typing remains free; validation still reports invalid input.
10. **Solver console discoverability.** When a Process run starts, the spec 210
    live console is visible or explicitly revealed without hunting through
    "More controls".

## Scope

- `frontend/` presentation: tokens, styles, shell/workspace layout, shared
  controls, Settings accent UI, and the presentation of the affected Design
  surfaces. Implementation may land in more than one PR.
- The accent preference keeps its storage key and becomes a curated preset id;
  this visual-only browser preference change is justified by item 8.

## Non-goals and boundaries

- No change to engine/solver semantics, units, Studio runtime boundaries, model
  versioning, backend APIs or persistence. No new cross-surface project/version
  model and no Studio workflow redesign (issue #901 owns those).
- No new runtime dependency or network egress.
- Product text keeps the **BlueCad** spelling.

## Acceptance

- Frontend build, type check and frontend tests pass on the exact head, with
  focused tests for stepper arithmetic/range clamping, curated accent resolution
  and migration, and splitter clamping/persistence.
- Real-Chromium before/after captures for Design → Process, BlueCad and Studio,
  Coding, and Memory/Literature/Development navigation, in Light and Dark, with
  the spec 198 matrix re-run: no page or console errors and no WCAG AA
  text-contrast failures.
- An implementation evidence note: what changed and why, what is partial, what
  is future work (notably items 3 and 4), and where the maintainer should look.
