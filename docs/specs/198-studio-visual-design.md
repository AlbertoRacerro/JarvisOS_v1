# STUDIO-VISUAL-DESIGN-1 — Lumen across JarvisOS

Accepted outcome and readiness: maintainer roadmap issue
[#834](https://github.com/AlbertoRacerro/JarvisOS_v1/issues/834), the
2026-10-20 maintainer selection of **Lumen** as the base direction (ledger
`L20261020050642-a34f`: Herbarium is a palette/daylight reference only;
Stoa, Grove, Temenos and Rhizome are closed), and the binding roadmap directive
`L20261022122708-233d` (P1 "Lumen across all JarvisOS surfaces", "do not
reconsider it"). Live state is recorded only in STATUS.md.

## Outcome

Lumen becomes the single production visual identity of the existing JarvisOS
frontend, in both appearances, on every existing surface:

- **Dark** is the approved Lumen direction (exploration `lumen2-dark`).
- **Light** keeps Lumen geometry, depth and emblem with Herbarium-inspired
  colours (exploration `lumen2-light`, v2.1: rich green near the title, airy
  ivory far field).
- The existing appearance preference (`system` / `light` / `dark`) selects
  between them; the user-configurable accent remains and keeps its contrast
  guarantees. The `?direction=` exploration switcher, the round-1 directions and
  their storage key are not shipped.

The starting material is the remote exploration branch
`explore/198b-lumen-v2` at `d995f940f00fa9a2e5b87fa8de29081d2de0a5d6`
(token sheets, emblem SVGs, OFL fonts with licence texts). It is reference
material, not a patch to merge verbatim: tokens move into the canonical token
and theme owners, and the layered override sheets are reduced rather than
extended where Lumen replaces them.

## Scope

1. **Tokens and appearance.** Lumen dark/light semantic tokens (surfaces,
   ink, muted text, rules, focus, selection, status, chart and 3D-viewport
   backgrounds) in the canonical token owner, wired to the existing appearance
   and accent preferences. Bundled fonts only if licensed for redistribution,
   with their licence text, served locally (no font CDN or other new egress).
2. **Every existing surface.** Shell, navigation, Studio home/results, Process
   (including Dynamic), BlueCad workbench and viewport, Coding/Runtime,
   Analytics, Settings, review and run views, dialogs, empty/error/loading
   states. No surface may remain on the previous identity or mix both.
3. **Visual UX audit and fixes.** A real browser audit of every surface in
   both appearances at wide and narrow widths, using the repository-owned
   visual-design skill plus standard heuristics (hierarchy, density, alignment,
   whitespace, contrast, focus visibility). Fix excessive whitespace,
   overcrowding, weak hierarchy and verbose navigation found by the audit,
   within presentation and copy.
4. **BlueCad spelling.** User-visible product text spells **BlueCad**, never
   `BLUECAD`. Identifiers, API paths, persisted values, file formats and spec
   names are unchanged.

## Non-goals and boundaries

- The compact, inspectable BlueCad project-tree navigator is a separate slice
  (see STATUS); this slice only restyles the existing navigator.
- No backend, API, persistence, routing, provider, permission, execution,
  numeric-format, unit or scientific-contract change. Workflows, controls,
  labels with engineering meaning, provenance and qualification text are
  preserved. Copy changes are limited to the BlueCad spelling and audit-driven
  removal of redundant chrome; errors, empty states, units, runtime availability
  and permission boundaries stay.
- No new runtime dependency besides font files; no new network egress.
- Frozen backend conformance tests are not modified. Non-frozen visual tests may
  change only where this contract intentionally changes colours, spelling or
  markup.

## Acceptance

- Frontend build, type check and the frontend test suite pass on the exact head.
- Computed-contrast audit of visible text in both appearances: no WCAG AA text
  failures; focus indicators visible on every interactive control audited.
- Real-Chromium captures of every surface listed in scope, both appearances,
  1440 px and a narrow width, with no page or console errors, recorded in an
  implementation evidence note together with the audit findings and their
  dispositions.
- No `BLUECAD` remains in rendered product text (checked mechanically over the
  rendered captures or the source strings that render).
- Workflow parity: the existing route smoke and focused UI tests still pass;
  the diff contains no behavioural change outside presentation and the scoped
  copy.

The work may land in more than one PR under this identity when that reduces
review risk (for example tokens/shell first, then remaining surfaces); each PR
carries its own exact-head evidence and the row stays `in_review` until the
final one merges.
