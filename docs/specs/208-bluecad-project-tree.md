# BLUECAD-PROJECT-TREE-1 — compact, inspectable BlueCad project tree

Accepted outcome and readiness: binding roadmap directive
`L20261022122708-233d` (P1 "Lumen across all JarvisOS surfaces": "Redesign the
verbose BlueCad navigator as a compact, inspectable CAD project tree"; "Keep API
and persistence compatible unless a change is specifically justified"), after
spec 198 restyled the existing navigator and explicitly left this redesign to a
separate slice. Live state is recorded only in STATUS.md.

## Outcome

The BlueCad workbench navigator becomes a compact CAD-style project tree in the
Lumen identity instead of a stacked form plus a list of tall candidate cards:

- **Tree.** The workspace is the root; its candidates are one-line nodes with a
  status marker, a short title and, when parked, a compact parked indicator
  (the full reason stays available). The selected candidate expands to its
  inspectable contents from data the frontend already loads: geometry parts
  (meshes of the current viewer session), Studio visual references, artifacts
  and a validation summary. Selecting a part node drives the existing geometry
  inspection; other content nodes open the existing inspector.
- **Inspectable.** The tree follows the WAI-ARIA tree pattern: `tree` /
  `treeitem` roles, `aria-expanded`, `aria-selected`, a single tab stop with
  roving focus, and Up/Down/Left/Right/Home/End/Enter/Space keyboard behaviour.
  Lifecycle status is exposed as text, not colour only.
- **Compact controls.** Workspace selection, filter, archived visibility and
  refresh form one compact toolbar. The AI brief composer is collapsed behind a
  single "New from brief" control and opens (with focus) when requested from
  the toolbar, the viewport create panel or "Duplicate brief". The provider and
  budget notice stays attached to the composer.

## Scope

- `frontend/` presentation of the BlueCad navigator region and the styles it
  needs; extraction of the tree into its own component is allowed.
- Existing behaviour is preserved: selection publication, request/mutation
  generation guards, filter and archived semantics, focus restoration after
  selection change and archive, empty/loading/error states, disabled states
  while busy, and the existing create/archive/promote/duplicate flows.

## Non-goals and boundaries

- No backend, API, persistence, route or data-model change; the tree uses only
  data the workbench already loads. No new runtime dependency or network egress.
- No change to the viewport, inspector content, dock, export, print handoff or
  geometry generation.
- No multi-candidate assembly hierarchy, drag-and-drop, renaming or new
  mutations; those require a separate accepted change.
- User-visible text keeps the **BlueCad** spelling.

## Acceptance

- Frontend build, type check and the frontend test suite pass on the exact
  head, including a focused test for the tree structure, roles and keyboard
  model.
- Real-Chromium captures of the BlueCad workbench with candidates (selected
  candidate expanded, parked candidate present) and with an empty workspace,
  Dark and Light, 1440 px and a narrow width: no page or console errors, no
  WCAG AA text-contrast failures, visible focus on the tree and toolbar
  controls, and a keyboard walk of the tree recorded in an implementation
  evidence note.
- Workflow parity: candidate selection, filter, archived toggle, refresh,
  brief creation, template creation, duplicate brief, archive and part
  inspection still work in the browser.
