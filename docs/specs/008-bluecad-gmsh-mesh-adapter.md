# 008 — BLUECAD Gmsh mesh adapter (subprocess, physical groups, quality gate)

Status: implemented (pending review)
Depends on: 005, 007

## Goal

After this slice, JarvisOS can take a built candidate's STEP + manifest plus
an `AnalysisSpec` and produce a CalculiX-ready mesh: a generated `.geo`
script drives the registered `gmsh` binary as a subprocess, physical groups
are assigned deterministically from manifest port frames, and a machine-
readable `MeshResult` reports element counts and quality gates.

## Why

The deterministic geometry→analysis link (`BLUECAD_CORE_DESIGN.md` §5). The
bounding-box physical-group mechanism is the decided design; this slice also
closes assumption A3 (its real-gmsh acceptance test is the A3 verification).

## Scope

In scope:
- `schemas/bluecad_analysis_spec_v0_1.schema.json` — the FULL schema per
  `BLUECAD_CORE_DESIGN.md` §5 (analysis_type enum incl. reserved `cfd_*`
  values, material, `bcs`/`loads` addressed by port labels, mesh controls,
  pass_criteria) — 008 consumes only geometry ref + mesh controls + labels;
  the rest is data for 009.
- `backend/app/modules/bluecad/mesh_adapter.py`:
  - `.geo` generation: `Merge "<model.step>";` + one
    `Physical Surface("BC_<label>") = Surface In BoundingBox {…};` (resp.
    `LOAD_<label>`) per referenced port — box computed from the manifest's
    absolute port frame: cube centered on the port origin, half-side =
    `0.75 × outer_d` of that port; + `Physical Volume("BODY") = …` (all
    volumes); + mesh size fields from `mesh.target_size` (+ optional
    per-label refinement).
  - Invocation via `registry.run_tool("gmsh", …)` (007): 3D mesh, output
    `mesh.inp` (CalculiX format) + `mesh.msh` + captured log. GPL boundary:
    strictly CLI/file — **never** `import gmsh` (CI-enforced by 007).
  - Post checks → `MeshResult` JSON (schema
    `bluecad_mesh_result_v0_1.schema.json`): node/element counts total and
    per physical group, gmsh exit status, warnings. Gates: any referenced
    physical group with 0 elements → `MESH_GROUP_EMPTY` (this is the A3
    failure signal); zero volume elements → `MESH_FAIL`; parse failure →
    `PARSE_ERROR`; registry/timeout errors pass through (`TIMEOUT`, etc.).
  - Deterministic retry policy as data (not LLM): on `MESH_FAIL` only,
    retry once with `target_size × 0.5`; record both attempts in MeshResult.

Out of scope (binding non-goals):
- No ccx invocation, no `.inp` solver sections (material/steps are 009 —
  gmsh's `.inp` here is mesh + node sets only).
- No mesh adaptivity beyond the single deterministic retry.
- No quality metrics beyond counts/empty-group/negative-element detection in
  v0 (report gmsh's own quality log lines verbatim in `warnings`).
- No AI anywhere in this path.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `schemas/bluecad_analysis_spec_v0_1.schema.json`,
  `schemas/bluecad_mesh_result_v0_1.schema.json` (new)
- `backend/app/modules/bluecad/mesh_adapter.py` (new)
- `backend/tests/bluecad/test_mesh_adapter.py`, fake-gmsh fixture script
- `configs/bluecad_tools.yaml` untouched (enabling real gmsh is a local,
  uncommitted action — the maintainer fills entrypoint+hash on his machine)

## Design constraints

- All 005 conventions (units mm, structured errors, determinism given same
  inputs+tool version).
- The `.geo` file is written into the run's output dir and kept as an
  artifact (`bluecad_geo` role) — it is the audit trail for group
  assignment.
- Label sanitization: port labels are validated `[A-Za-z0-9_]+` before
  interpolation into `.geo` (no injection).
- Offline tests use a fake `gmsh` executable (python fixture script that
  validates argv, reads the `.geo`, emits a canned `.inp`/`.msh` and log);
  real-gmsh tests behind pytest marker `bluecad_gmsh`, skipped when the
  registry has gmsh disabled.

## Acceptance criteria

1. Given the 005 golden chain fixture + an AnalysisSpec referencing
   `run1.port_a` as BC and `joint1.port_b` as LOAD, the generated `.geo`
   contains exactly two Physical Surface statements with boxes centered on
   those ports' manifest frames (numeric assertion, offline).
2. Fake-gmsh happy path → MeshResult with counts, artifacts registered
   (`mesh.inp`, `mesh.msh`, `.geo`, log), exit ok.
3. Fake-gmsh emitting an empty group → `MESH_GROUP_EMPTY` naming the group.
4. `MESH_FAIL` triggers exactly one halved-size retry, both recorded; second
   failure → final `MESH_FAIL`.
5. Injection attempt (port label `a"; Kill;`) rejected before any file
   write.
6. **A3 verification (real gmsh, `bluecad_gmsh` marker)**: meshing the 005
   golden STEP yields >0 elements in every referenced physical group and a
   loadable `.inp`. Marked test documented as the A3 closure in the summary.
7. AnalysisSpec schema round-trips a full static-analysis example (material,
   bcs, loads, pass_criteria) even though 008 ignores the solver fields.

## Required tests

- Offline pytest with the fake tool via a tmp registry (007 fixtures
  pattern); real-gmsh marker suite as above.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written. A3 row in `BLUECAD_CORE_DESIGN.md` §11 updated by
the maintainer after the marker test passes locally.


## Implementation notes

Status updated after implementing the subprocess-only Gmsh mesh adapter. The adapter generates `.geo` physical groups from manifest port frames with `Surface In BoundingBox`, invokes `gmsh` only via the BLUECAD tool registry, records mesh artifacts, parses CalculiX `.inp` counts, and applies the one-shot deterministic retry on `MESH_FAIL`.

Deviations from spec: none. The real-Gmsh A3 test is present behind the `bluecad_gmsh` marker and skips unless a maintainer supplies an enabled real Gmsh registry entry outside the shipped config.

## Amendment (reconciled 2026-07-10)

Spec 024-A owns one narrowly scoped additive capability for this adapter: an
optional `mesh.element_order` field in the AnalysisSpec schema with integer enum
`[1, 2]`. Absence is equivalent to order `1` and preserves all current behavior;
order `2` requests quadratic tetrahedra from Gmsh and must be verified against
the generated C3D10 mesh artifact. Implementation and real-tool proof belong to
024-A, not to spec 008 itself. See
`docs/specs/024-fem-verification-battery.md`, section `024-A — quadratic
tetrahedron contract`.
