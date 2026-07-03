# 005b — BLUECAD remaining part-kind builders (parametric stubs)

Status: ready (after 005 is merged)
Depends on: 005

## Goal

After this slice, GeometrySpec v0 supports all seven part kinds: `manifold`,
`float`, `anchor_mount`, `harvest_module` join `tube_run`/`bend`/`joint` as
parametric stub builders with correct ports. A full-reactor layout (parallel
runs, manifolds at both ends, floats, harvesting stub) builds, validates, and
exports through the 005 pipeline unchanged. This is the geometric half of the
alpha-2 gate.

## Why

The user-confirmed alpha gate is a recognizable full-reactor layout
(`BLUECAD_CORE_DESIGN.md` §9, "Alpha staging"). Stub fidelity is deliberately
low; correctness of ports, volumes, and composition is what matters.

## Scope

In scope:
- Extend `schemas/bluecad_geometry_spec_v0_1.schema.json` **in place**
  (additive enum extension; pre-release, existing fixtures stay valid) with
  the four new part kinds and their params, exactly as frozen in
  `BLUECAD_CORE_DESIGN.md` §2 "Stub definitions":
  - `manifold`: `outer_d_main`, `wall_t`, `length`, `n_out`, `out_d`,
    `out_wall_t`, `spacing` → ports `in_a`, `in_b`, `out_1..out_n`.
  - `float`: `outer_d`, `length`, `n_mounts`, `pad_d` → ports
    `mount_1..mount_n`.
  - `anchor_mount`: `base_w`, `base_l`, `base_t`, `eye_d` → port `mount_a`.
  - `harvest_module`: `outer_d`, `height`, `wall_t`, `port_d` → ports
    `in_a`, `out_a`, `drain_a`.
- Port interface types: ports gain an `interface` field in the manifest —
  `"tube"` (carries `outer_d`, `wall_t`; existing behavior) or `"pad"`
  (carries `pad_d`; used by float mounts and anchor_mount). Connection
  validation: interfaces must match (`tube↔tube` with matching d/wall as in
  005; `pad↔pad` with matching `pad_d`). Mixed connections →
  `PORT_MISMATCH`.
- One builder per new kind in `builders.py`, following the 005 pattern
  (solid + named ports as frames). Generated port names (`out_3`,
  `mount_2`) are deterministic.
- New golden fixture `full_reactor_v0`: 2 parallel tube runs + 4 bends +
  manifolds at both ends (`n_out=2`) + 2 floats + 1 harvest_module in the
  return line + 2 anchor_mounts on float pads. Must build to a single
  connected assembly (plus the floats/anchors subassembly as declared).

Out of scope (binding non-goals):
- No fidelity beyond stubs (no O-ring grooves, no fillets, no drafts).
- No schema version bump, no changes to validation report schema.
- No frontend, no AI-loop changes (the 010 prompt template gains the new
  kinds in a one-line template edit ONLY if 010 is already merged; otherwise
  note it as a follow-up).
- No hydro/buoyancy math (Tier 2 domain validators are BlueRev-side).

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `schemas/bluecad_geometry_spec_v0_1.schema.json`
- `backend/app/modules/bluecad/builders.py`, `assembly.py` (interface-type
  check), `validate.py` (pad-port conformity), `spec.py` (param validation)
- `backend/tests/bluecad/` (new fixtures + tests)

## Design constraints

- All 005 constraints carry over (units, determinism, worker-subprocess
  execution, error taxonomy, clean-room).
- Volume acceptance tolerances: exact-analytic within 0.1% for `float`,
  `anchor_mount`, `harvest_module` (simple solids); within 5% of the
  composed analytic estimate for `manifold` (boolean unions make exact
  analytic messy — the tolerance is a check against gross error, watertight
  and port checks carry the correctness burden).
- `n_out`/`n_mounts` bounds: 1..12, validated at spec load (`SPEC_INVALID`
  outside bounds).

## Acceptance criteria

1. Each new kind builds standalone with all four artifacts and
   `verdict=pass` when `declared` matches within tolerance.
2. Manifold with `n_out=3` exposes exactly ports `in_a`, `in_b`, `out_1`,
   `out_2`, `out_3` in the manifest, with frames on the header at the
   declared `spacing`.
3. `full_reactor_v0` fixture builds, is watertight per solid, passes port
   conformity on every connection, and produces a non-empty GLB.
4. A `tube`-to-`pad` connection fails with `PORT_MISMATCH` at build time.
5. 005 golden fixtures still pass unchanged (regression).
6. Determinism criterion of 005 holds for all new kinds.

## Required tests

- Offline pytest under the existing `bluecad_kernel` marker: per-kind golden
  tests (analytic volumes per the tolerances above), port-name generation,
  interface mismatch negatives, `n_out` bounds negatives, full-reactor
  fixture end-to-end, 005 regression suite green.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
