# 005 — BLUECAD CAD adapter MVP (GeometrySpec v0, build123d, Tier 0–1 validation)

Status: implemented (pending review)
Depends on: none (first BLUECAD slice)

## Goal

After this slice, JarvisOS can take a `GeometrySpec v0` JSON (tube runs, bends,
socket joints composed via ports), deterministically build the solid geometry
with build123d, export `model.step` + `model.stl` + `model.glb` +
`manifest.json`, and produce a machine-readable `validation_report` with
Tier 0 (execution) and Tier 1 (geometric) checks. Callable as a Python API and
a CLI. No AI, no mesh, no FEM in this slice.

## Why

This is the deterministic foundation of BLUECAD (see
`docs/strategy/BLUECAD_CORE_DESIGN.md`, §2–§4): every later slice (viewer,
Gmsh, CalculiX, AI generate/repair loop) consumes exactly the artifacts and
report defined here. The AI loop's safety story depends on this layer being a
pure, deterministic function — do not add flexibility that weakens that.

## Scope

In scope:
- `schemas/bluecad_geometry_spec_v0_1.schema.json` — JSON Schema for
  GeometrySpec v0 exactly as specified in `BLUECAD_CORE_DESIGN.md` §2, with
  part kinds `tube_run`, `bend`, `joint` only (others rejected with
  `SPEC_INVALID` for now).
- `schemas/bluecad_validation_report_v0_1.schema.json` — per §4.
- `backend/app/modules/bluecad/` new module:
  - `spec.py` — load/validate/canonicalize spec, compute `spec_id`
    (sha256 of canonical JSON, same canonicalization style already used by
    RouterPolicy input digests).
  - `builders.py` — one builder per part kind using **public build123d API
    only**: `tube_run` = hollow cylinder swept along its axis; `bend` = pipe
    section swept along a circular arc (constant `outer_d`, `wall_t`,
    `bend_radius`, `angle`); `joint` (type `socket`) = short sleeve with inner
    diameter matching mating `outer_d`, length `socket_len`. Every builder
    returns the solid plus its named ports (`port_a`, `port_b`) as frames.
  - `assembly.py` — resolve `connections`: place parts so connected ports are
    coincident with opposed directions; error `PORT_MISMATCH` if diameters or
    wall thicknesses differ beyond 1e-6 relative.
  - `export.py` — write STEP (AP214), STL, GLB, `manifest.json` (fields per
    §3: spec_id, tool versions, per-part volume/bbox, resolved port frames,
    sha256 per artifact).
  - `validate.py` — Tier 0 + Tier 1 checks per §4: artifacts present;
    B-rep validity per solid (build123d/OCP validity check); watertight
    closed shells; volume vs `declared.total_volume_mm3` within `rel_tol`;
    bbox vs declared within `abs_tol`; port conformity for every connection;
    assembly connectedness. Deterministic `hint` strings from templates.
  - `cli.py` — `python -m backend.app.modules.bluecad build <spec.json> --out <dir>`
    → builds, validates, prints report path, exit code 0 iff verdict pass.
- `backend/requirements.txt`: add `build123d==0.11.1` (version verified by
  the A1/A2 spike, `reports/bluecad_spike_a1_a2.md`) — this is the only new
  runtime dependency.

Out of scope (binding non-goals):
- No AI/LLM code, no RouterPolicy integration (spec 010).
- No Gmsh, no CalculiX, no subprocess execution of any kind.
- No frontend changes (spec 006).
- No `manifold`, `float`, `anchor_mount`, `harvest_module` kinds.
- No L2 script execution.
- No modification to the sandboxed runner (integration with it lands with
  spec 010; MVP runs as normal backend code).
- No BlueRev domain formulas anywhere in this module.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `schemas/bluecad_geometry_spec_v0_1.schema.json` (new)
- `schemas/bluecad_validation_report_v0_1.schema.json` (new)
- `backend/app/modules/bluecad/*` (new)
- `backend/requirements.txt`
- `backend/tests/bluecad/*` (new)

## Design constraints

- Units: mm/kg/s/rad, no unit fields (design doc §2).
- Determinism: same spec → identical manifest geometry numbers across runs.
  Geometric assertions in tests; do not assert STEP byte equality.
- **Execution model**: the build runs in a JarvisOS-owned worker subprocess
  (plain `multiprocessing`/`subprocess` child running our module) so that
  `TIMEOUT` is enforced by killing the worker — OCCT kernel calls cannot be
  safely interrupted in-thread. The CLI wraps the same worker path.
- **Assembly placement algorithm**: the first part in `parts` order is placed
  at its own `frame`; remaining parts are placed by BFS over `connections`
  (each connection fully constrains the next part: mating port origins
  coincident, directions opposed, no extra rotational DOF is used in v0 —
  parts are axisymmetric). A part reachable by two conflicting paths →
  `PORT_MISMATCH`. Unconnected parts keep their own `frame`.
- **Socket joint semantics (v0)**: a sleeve (hollow cylinder) of length
  `socket_len`, inner diameter = mating `outer_d` (clearance 0 in v0), outer
  diameter = `outer_d + 2*wall_t`. `port_a`/`port_b` at the two sleeve ends,
  declared with the mating tube's `outer_d`/`wall_t` so port conformity
  checks pass. Fidelity (clearances, O-ring grooves) comes later via params,
  not schema changes.
- **Canonicalization**: reuse the existing canonical-JSON helper used for
  `router_policy_input` digests (find it in the backend; if it is not
  importable without heavy deps, extract it to a shared util in this slice
  and point RouterPolicy code at it in a follow-up, do not fork the logic).
- **GLB export (verified)**: use build123d's native
  `export_gltf(..., binary=True)` — confirmed working at the pinned version
  by the A1/A2 spike. No trimesh dependency.
- Error taxonomy exactly: `SPEC_INVALID`, `PORT_MISMATCH`, `KERNEL_ERROR`,
  `EXPORT_ERROR`, `TIMEOUT` (design doc §3). Errors are structured (code +
  detail dict), never bare strings.
- Public build123d API only, with one pre-authorized exception (from the
  A1/A2 spike): Tier 1 checks may use `Shape.is_valid` / `Shape.is_manifold`
  (build123d) plus `OCP.BRepCheck.BRepCheck_Analyzer` and
  `OCP.BRep.BRep_Tool.IsClosed_s` for validity/closed-shell — keep all OCP
  low-level usage isolated in one clearly-marked function in `validate.py`.
  Any further OCP usage: note and justify in the PR description.
- Copy no code from build123d/CadQuery examples or source; clean-room rule in
  `BLUECAD_TOOLING_AND_LICENSING.md` applies.
- Schema style, naming, and digest conventions must match existing
  `schemas/*.schema.json` files.

## Acceptance criteria

1. A valid spec with `tube_run + bend + joint` connected in a chain builds
   successfully and produces all four artifacts; `validation_report.verdict
   == "pass"` when `declared` matches actual within tolerance.
2. The same spec run twice produces identical `spec_id`, per-part volumes,
   bboxes, and port frames in both manifests.
3. Tube volume matches the analytic hollow-cylinder value within 0.1% for at
   least three parameter sets; bend volume matches the analytic torus-segment
   value within 0.5%.
4. A spec whose `declared.total_volume_mm3` is 10% off the actual yields
   `verdict == "fail"` with failing check `T1_VOLUME_DECL` and a `hint`
   containing the actual relative error.
5. A connection between ports with different `outer_d` fails at build time
   with structured error `PORT_MISMATCH` (no artifacts emitted, Tier 0
   reflects the failure).
6. A spec with an unknown part kind or non-finite number is rejected as
   `SPEC_INVALID` before any kernel call.
7. Exported STL and GLB are non-empty, watertight-consistent with STEP solids
   (triangle mesh closed), and referenced with correct sha256 in the manifest.
8. CLI exit codes: 0 on pass, 1 on validation fail, 2 on build error.

## Required tests

- Offline pytest suite `backend/tests/bluecad/`, no network, no fake
  providers needed (no AI in this slice). Fixtures: 3+ golden specs (chain,
  U-shape with two bends, minimal single tube) + expected analytic volumes.
- Schema round-trip tests: every fixture validates against the JSON Schema;
  canonicalization is stable (same digest across key order permutations).
- Negative tests for acceptance criteria 4, 5, 6.
- Mark the suite with a pytest marker (e.g. `bluecad_kernel`) so CI can skip
  it where build123d is not installed, but the default local test gate runs it.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Implementation notes

- Implemented in two stages per PR review workflow. Stage 1 added the GeometrySpec and validation-report schemas, spec loading/validation/canonicalization, and golden analytic fixtures.
- Stage 2 added the BLUECAD adapter modules for primitive builders, port-conformity assembly checks, artifact export, Tier 0/Tier 1 validation reports, worker-subprocess build orchestration, and CLI entry point.
- Added the pre-authorized runtime dependency `build123d==0.11.1`; kernel-dependent tests are marked `bluecad_kernel` and skip where build123d is unavailable.
- No BlueRev formulas, AI/LLM calls, frontend changes, Gmsh/CalculiX integrations, sandboxed runner changes, or direct provider calls were added.
