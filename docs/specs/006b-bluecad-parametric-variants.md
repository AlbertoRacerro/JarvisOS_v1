# 006b — BLUECAD parametric variants (sliders → deterministic rebuild)

Status: ready (after 006 is merged; needs 005b for full-reactor params)
Depends on: 006, 010 (schema fields `origin`/`parent_candidate_id` already exist)

## Goal

After this slice, a user can select a `valid` candidate in the workbench,
adjust numeric parameters (sliders/number inputs generated from its
GeometrySpec), and trigger a deterministic rebuild — **no LLM involved**. The
result is a child candidate (`origin=parametric_variant`) with its own
artifacts and validation report, listed under its parent.

## Why

This is the second half of the alpha-2 GUI gate: AI proposes the topology
once; the human explores the parameter space for free (0 tokens, ~1s per
rebuild). It also exercises the candidate ledger as a design-history tree.

## Scope

In scope:
- Backend: `POST /workspaces/{id}/bluecad/candidates/{cid}/variants`
  - Body: overrides map `{"<part_id>.<param>": <number>, ...}` plus optional
    note.
  - Guard: parent must be `valid`; override keys must address existing
    numeric leaf params of existing parts (no adding/removing parts, no
    connections/`declared` edits — `declared` is recomputed server-side as
    "actual of parent scaled" is NOT attempted: the variant spec simply
    drops the parent's `declared` block and Tier 1 runs intrinsic checks
    only). Violations → structured 422.
  - Flow: deep-copy parent spec → apply overrides → schema-validate → 005
    build + validate in the worker → create child candidate
    (`origin=parametric_variant`, `parent_candidate_id`, `status` `valid`
    or `parked(attempts_exhausted)` is wrong here — a failed variant gets
    status `parked` with a new parked_reason value `variant_failed`), link
    artifacts. Exactly zero rows written to `ai_jobs`.
  - `parked_reason` enum: add `variant_failed` (additive).
- Frontend (workbench detail view):
  - Parameter panel generated from the candidate's spec: one control per
    numeric param, grouped by part_id; slider bounds default to
    [0.5×, 1.5×] of the current value with editable number input.
  - "Rebuild variant" button → POST → child appears in a variants list under
    the parent; clicking a variant loads it in the same viewer/report
    components (reused from 006).
- API client additions.

Out of scope (binding non-goals):
- No LLM calls anywhere in this path (test-asserted).
- No topology edits (parts, connections, kinds) — parameters only.
- No optimization/sweeps/batch variants; one rebuild per click.
- No comparison view between variants (future).
- No changes to the 010 loop.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `backend/app/modules/bluecad/routes.py`, `variants.py` (new), `models.py`
- `backend/app/core/schema.py` only if `parked_reason` is DB-constrained
  (otherwise enum lives in module models)
- `backend/tests/bluecad/test_variants.py` (new)
- `frontend/src/pages/BlueCAD.tsx`, viewer/param components,
  `frontend/src/api/client.ts`

## Design constraints

- Rebuild path reuses the 005 worker entrypoint verbatim — no second build
  code path.
- Variant creation is synchronous (build ≈ sub-second per the spike
  timings).
- The overrides map is stored on the child candidate (in `loop_config_json`
  or a dedicated field — match existing column usage; report the choice).
- Determinism: same parent + same overrides → identical artifact digests.

## Acceptance criteria

1. Happy path: valid parent + `{"run1.length": 7000}` → child candidate
   `valid`, `origin=parametric_variant`, correct parent id, artifacts and
   report linked; parent unchanged.
2. Zero `ai_jobs` rows are written by the whole variant flow (asserted by
   row-count before/after in tests).
3. Guard failures (parent not valid; unknown part_id; non-numeric param;
   attempt to override `connections`) → structured 422, no candidate
   created.
4. A variant that fails validation (e.g. wall thicker than radius) →
   child `parked(variant_failed)` with report attached; endpoint returns it
   (not an error).
5. Determinism criterion above verified in tests.
6. Frontend: param panel renders controls for every numeric param of a
   valid candidate; rebuild adds the variant to the list and loads it in
   the viewer. `npm run build` green.

## Required tests

- Offline pytest: happy path, all guard negatives, failed-variant path,
  determinism, ai_jobs zero-write assertion. Frontend: build only.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
