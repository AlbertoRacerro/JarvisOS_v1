# 006 — BLUECAD workbench: 3D viewer + validation report + attempt history

Status: ready (after 005 and 010 are merged)
Depends on: 005, 010

## Goal

After this slice, the frontend has a BLUECAD workbench page: list of
candidates per workspace, and a candidate detail view with an interactive 3D
view of the GLB artifact (orbit/zoom/pan), the validation report rendered as
a check table, and the attempt history (what the AI tried, what failed, what
was repaired). A scoped backend endpoint serves BLUECAD artifact bytes.

## Why

This is the visible face of alpha-1: AI-generated, deterministically
validated geometry a human can inspect. Attempt history makes the loop
auditable at a glance instead of via DB queries.

## Scope

In scope:
- Backend — scoped artifact content endpoint:
  - `GET /workspaces/{id}/bluecad/artifacts/{artifact_id}/content`
  - Serves bytes with correct MIME **only** for artifacts whose role starts
    with `bluecad_` and whose stored path resolves under the data root
    (reuse the existing under-data-root check pattern from the runner
    readback path). Anything else → 404 (not 403 — do not leak existence).
  - Read-only; no listing; no generic artifact download (binding).
- Frontend — new page `frontend/src/pages/BlueCAD.tsx` (registered in the
  existing nav/Layout pattern):
  - Candidate list: status badge, parked reason, created_at, brief excerpt
    (from `GET .../bluecad/candidates`).
  - Detail view: three.js GLB viewer (`three` npm package, MIT — new
    dependency, pinned exact; `GLTFLoader` + `OrbitControls` from
    `three/examples/jsm`), validation report table (check id, tier, status,
    detail, hint), attempt list (attempt_no, route_class, proposal/build/
    validation outcomes, timestamps).
  - Loading/error states consistent with existing pages' style.
- API client additions in `frontend/src/api/client.ts` following its
  existing conventions.

Out of scope (binding non-goals):
- No parameter sliders or rebuilds (006b).
- No candidate creation from this page beyond a minimal "new candidate"
  form posting to the 010 endpoint (brief text + submit); no chat (018).
- No STEP/STL rendering, no measurement tools, no sectioning.
- No websocket/polling infrastructure; manual refresh is acceptable in v0.
- No other pages restyled.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `backend/app/modules/bluecad/routes.py` (content endpoint)
- `backend/tests/bluecad/test_artifact_content.py` (new)
- `frontend/src/pages/BlueCAD.tsx` (new), `frontend/src/components/`
  (viewer component), `frontend/src/api/client.ts`, `frontend/src/App.tsx`
  (route), `frontend/package.json` (`three` + `@types/three`)

## Design constraints

- Frontend calls backend APIs only (AGENTS.md invariant 3) — the GLB is
  fetched through the new endpoint, never from disk paths.
- The viewer component must accept an artifact URL prop and know nothing
  about candidates (reusable by 006b).
- Path traversal safety on the content endpoint is test-covered
  (`..`-containing and outside-data-root stored paths → 404).
- New npm dependencies: `three` (+ types) only, exact-pinned; call them out
  prominently in the summary. No UI framework additions.

## Acceptance criteria

1. Content endpoint returns GLB bytes with `model/gltf-binary` for a
   `bluecad_glb` artifact; returns 404 for: non-bluecad roles, unknown ids,
   artifacts whose stored path is outside the data root.
2. Workbench lists candidates of the active workspace with status and
   parked reason visible.
3. Candidate detail renders the GLB in an orbitable 3D view, the full check
   table, and one row per attempt with its three outcomes.
4. A `parked` candidate shows its parked reason and full attempt trail
   (no GLB required).
5. "New candidate" form posts a brief and the resulting candidate appears
   in the list.
6. `npm run build` passes; backend test gate green.

## Required tests

- Backend: endpoint tests incl. the three 404 classes and MIME correctness,
  offline, fixture artifacts under a tmp data root.
- Frontend: `npm run build` (no frontend test infra exists — do not add a
  test framework in this slice; note it as a gap in the summary).

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
