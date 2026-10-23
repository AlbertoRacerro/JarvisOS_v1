# 208 BLUECAD-PROJECT-TREE-1 — implementation evidence

Contract: [spec 208](../specs/208-bluecad-project-tree.md). Frontend-only; no
backend, API, persistence or dependency change.

## Change

- `BluecadProjectTree.tsx` renders the navigator as a WAI-ARIA tree: the
  workspace is the root and each candidate is a one-line node. A node shows the
  lifecycle status as text, an ellipsised title (the full brief is in the tooltip)
  and a `!` marker for a parked candidate. The parked reason is linked through
  `aria-describedby`. The selected candidate expands to **Parts** (the meshes of
  the current viewer session; activating one drives the existing geometry
  inspection), **Studio references**, **Artifacts** and a **Validation** summary.
  Activating one of these opens the existing inspector. The reference and
  artifact groups start collapsed. The tree has one roving tab stop and supports
  Up/Down/Left/Right/Home/End/Enter/Space.
- `BluecadWorkbench.tsx`: workspace, filter, archived and refresh controls now
  share one compact toolbar. The brief composer sits behind a "New from brief"
  disclosure, which "Duplicate brief" and the viewport's "Write a brief" also
  open (with focus). Focus restoration after a selection change or archive
  still targets the candidate node.
- A latent defect in the navigator's workspace switch is fixed. The switch
  handler nulled `selectedRef` before the workspace effect ran, so that
  effect's `chooseCandidate(null)` returned early. The previous workspace's
  `selectedId` was then paired with the new workspace in aggregate and
  Studio-reference requests, which returned 404s that the request guards
  discarded. The handler now clears the stale list and selection itself.
- `tests/208-bluecad-project-tree.mjs`, wired into `npm run build`, checks the
  tree roles, the keyboard model, the content groups, the collapsed composer,
  focus registration, the tokenised styles and that no API route was added.

## Evidence (exact head `d0528958`)

`VITE_API_BASE_URL=http://127.0.0.1:8208 npm run build` passed the full frontend
suite (including the new 208 check), `tsc` and the Vite build. The browser run
used an isolated copy of the spec 198 fixture data root (artifact paths
rewritten into the copy, removed afterwards), backend port 8208, preview port
5208 and CORS origin `http://127.0.0.1:5208`. Evidence is under
`/home/thera/jarvis-control/work/evidence/208-browser/r4/`
(`capture.mjs`, `empty.mjs`, `run/report.json`, `run/empty-report.json`,
screenshots).

| Check | Result |
| --- | --- |
| Workflow walk, Dark 1440 | "New from brief" opened and focused the composer. Submitting the brief created a parked `budget_blocked` candidate (paid AI is off in the fixture): it was selected, flagged `!` and the composer closed. Selecting the valid template tube expanded Parts (4 meshes), Studio references (0), Artifacts (4) and Validation (`9 pass`). Activating `mesh_0` set `aria-selected` from the viewer's inspection snapshot. The filter narrowed the list to 1 candidate and Refresh restored 2. Duplicate brief opened the composer with the brief text and focused it. Archive returned focus to the remaining candidate node, and the Archived toggle revealed the archived candidate. The viewport's "Create tube" added a valid template candidate. 0 page/console errors. |
| Keyboard walk | Home went to the root. ArrowDown moved through the candidates. ArrowRight expanded Parts and ArrowLeft collapsed it. End went to Validation. ArrowLeft moved to the parent candidate, collapsed it, and ArrowRight re-expanded it. Exactly one `tabindex="0"` stop. Every keyboard-focused item had a visible ring. |
| Matrix: Dark/Light × 1440/390 with candidates | 4 captures, tree visible in all of them (the 390 runs open the navigator): 0 page/console errors, 0 text-contrast failures, 0 focus misses out of 40 checked stops, correct theme, no rendered `BLUECAD`. |
| Empty workspace: Dark/Light × 1440/390 | The root node `Empty 208 · 0` (not expandable), the "No BlueCad candidates exist in this workspace." state and the "No geometry yet" create panel. 0 console errors, and 0 backend 404s across the whole run. |
| Filter with no matches | "No candidates match the current filter…" is visible. |

Focus moved programmatically after a mouse-clicked Archive follows Chromium's
`:focus-visible` heuristic, so the ring appears once the keyboard is used. The
inspector content itself is unchanged.
