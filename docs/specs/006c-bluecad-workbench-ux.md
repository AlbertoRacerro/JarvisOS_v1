# 006c — BLUECAD workbench UX pass (archive, malformed detail, promote, retry)

Status: implemented (pending review)
Depends on: 006

## Goal

After this slice, the BLUECAD workbench is usable day-to-day: the user can
archive unwanted candidates and hide them, see *why* a proposal was malformed,
promote a valid candidate to a workspace Decision, and retry a brief in one
click. All five additions use backend endpoints that already exist — this is a
frontend + API-client slice only.

## Why

The first live runs produced a pile of parked candidates and gave no visible
reason for malformed proposals (the reason had to be dug out of the DB). These
are the small controls that turn the workbench from a demo into a tool. Model
selection (needs spec 015) and parametric sliders (006b) are deliberately out
of scope.

## Scope

In scope (frontend `frontend/src/pages/BlueCAD.tsx`, `frontend/src/api/client.ts`,
styles; NO backend changes — every endpoint below already exists):

- **U1 — Archive + hide.** Add an "Archive" button on each candidate (and/or in
  the detail header) calling the existing
  `POST /workspaces/{id}/bluecad/candidates/{cid}/archive`. After archiving,
  refresh the list. By default, hide candidates with `status === "archived"`;
  add a "Show archived" checkbox toggle to reveal them.
- **U2 — Malformed / error detail.** In the attempt-history table, when an
  attempt has `error_detail_json` (a JSON string), make the row expandable (or
  add a "detail" cell/disclosure) that parses and shows it readably — e.g. the
  `parse_error` for a malformed proposal, or the error_type. This is the
  primary debugging affordance; do not hide it behind more than one click.
- **U3 — Promote valid candidate.** When `status === "valid"`, show a
  "Promote to Decision" button calling the existing
  `POST .../candidates/{cid}/promote`. On success, show the returned
  `promoted_decision_id` (and disable the button / show "Promoted"). Never show
  promote for non-valid candidates (the backend rejects them with 409).
- **U4 — Retry brief.** On any candidate, a "Retry / duplicate brief" action
  that copies its `brief_text` into the new-candidate textarea (and scrolls to
  it) so the user can resubmit or tweak. Pure client-side convenience.
- **U5 — Readable validation detail.** The report table's Detail cell currently
  shows stringified JSON (from the 006 crash fix). Render it readably: for the
  common shape `{actual, declared, rel_err/rel_tol}` show a compact
  human line (e.g. `actual 1.30e7 vs declared 1.24e7 (rel err 5.4%)`); fall
  back to compact JSON for other shapes. Keep it defensive — never render a
  raw object as a React child.

Out of scope (binding non-goals):
- No backend changes, no new endpoints, no schema changes.
- No model/provider selector (needs spec 015).
- No parametric sliders / rebuild (006b).
- No raw-model-output display (backend does not persist it yet).
- No restyle of other pages; no new UI framework or component library.
- No websockets/polling; manual refresh stays.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `frontend/src/pages/BlueCAD.tsx`
- `frontend/src/api/client.ts` (add `archiveBluecadCandidate`,
  `promoteBluecadCandidate` following existing client conventions)
- `frontend/src/styles/global.css` (only for the new controls/disclosure)

## Design constraints

- Frontend calls backend APIs only (AGENTS.md invariant 3).
- **Never render an object/array directly as a React child** — the 006
  white-page crash was exactly this; keep the `formatCell`-style guard and
  reuse it for U2/U5.
- Reuse existing button/table/panel classes and the existing loading/error
  patterns; match the current visual style (this is not a redesign).
- Optimistic-free: after archive/promote, re-fetch candidates rather than
  mutating local state by hand, to stay consistent with the backend.
- Endpoints are exactly:
  `POST .../bluecad/candidates/{cid}/archive`,
  `POST .../bluecad/candidates/{cid}/promote` (both already implemented and
  returning `BluecadCandidateRead`).

## Acceptance criteria

1. Archiving a candidate calls the archive endpoint and the candidate
   disappears from the default list; toggling "Show archived" reveals it with
   an archived status pill.
2. An attempt with `error_detail_json` shows its parsed content (e.g. the
   malformed parse_error) in the UI within one interaction; attempts without it
   render normally.
3. A `valid` candidate shows a working "Promote to Decision" button that calls
   promote and then displays the `promoted_decision_id`; the button is absent
   for non-valid candidates.
4. "Retry / duplicate brief" places the candidate's brief into the new-candidate
   textarea.
5. The validation Detail cell shows a readable line for actual-vs-declared
   checks and never crashes the page on any check shape.
6. `npm run build` (tsc + vite) passes. PR includes screenshots of: the list
   with an archived toggle, an expanded malformed attempt detail, and a valid
   candidate with the Promote button.

## Required tests

- Frontend: `npm run build` must pass (no frontend test framework exists — do
  not add one). Manual/visual verification via the required screenshots.
- No backend tests (no backend change). The existing backend
  `test_006_conformance.py` and endpoint tests must remain green and
  unmodified.

## Definition of done

`npm run build` green, backend test gate still green, acceptance criteria met
with screenshots in the PR, spec status updated, summary written.


## Implementation notes

- Added frontend-only archive, show-archived, promote, retry/duplicate-brief, malformed attempt detail, and readable validation detail behavior.
- Deviations from spec: none in implementation scope. Screenshot capture could not be completed in this container because frontend dependencies were not installable from npm (403 fetching `@types/three`), so the build also could not complete here.
