# BLUECAD — Core Design: Contracts, AI-CAD Loop, Routing Integration

Status: draft v0.1 (2026-07-03)
Depends on: `BLUECAD_TOOLING_AND_LICENSING.md` (tool choices, license boundaries, hard invariants).
Supersedes: the previously planned `BLUECAD_ADAPTER_CONTRACTS.md` + `BLUECAD_DOMAIN_MODEL_AND_AI_LOOP.md` + `BLUECAD_ROADMAP.md` (compressed into this one doc so implementation can start immediately).

This document fixes the load-bearing design decisions. Implementation slices
(`docs/specs/005+`) reference it; implementers must not re-litigate decisions
here — report conflicts instead.

---

## 0. Architecture overview

```
BlueRev domain package (private formulas)          JarvisOS (generic)
┌─────────────────────────────┐
│ sizing rules, correlations, │
│ domain validators (Tier 2)  │
└──────────────┬──────────────┘
               │ GeometrySpec / AnalysisSpec (neutral JSON, versioned)
               ▼
┌─ CAD adapter ────────────────────────────────┐
│ spec → build123d builder → solids            │  in-process (Apache/LGPL-B)
│ export: STEP (truth) + STL + GLB (viewer)    │  runs inside sandboxed runner
└──────────────┬───────────────────────────────┘
               ▼ artifacts + manifest
┌─ Validation service ─────────────────────────┐
│ Tier 0 execution · Tier 1 geometric ·        │  deterministic, pure function
│ Tier 2 domain (plugin) · Tier 3 analysis     │  of artifacts + spec
└──────────────┬───────────────────────────────┘
               ▼ validation_report (machine-readable)
┌─ Mesh adapter ───────┐   ┌─ FEM adapter ─────┐   ┌─ CFD adapter (future) ─┐
│ Gmsh CLI subprocess  │──▶│ CalculiX ccx      │   │ OpenFOAM case bundle   │
│ STEP → .msh/.inp     │   │ subprocess        │   │ in WSL2/container      │
└──────────────────────┘   └───────┬───────────┘   └────────────────────────┘
                                   ▼ ResultSummary (JSON)
┌─ AI layer (all calls via RouterPolicy) ──────────────────────────────────┐
│ cad.generate → proposal (spec or script)                                 │
│ cad.repair   → bounded retry loop on validation failures                 │
│ review panel → multi-agent critique of report+summary artifacts          │
│ ALL OUTPUT IS ADVISORY. Only validators pass/fail. Only the human        │
│ promotes a passing candidate to a workspace Decision.                    │
└──────────────────────────────────────────────────────────────────────────┘
```

Code layout target: `backend/app/modules/bluecad/` (adapters, validation,
loop orchestration — generic), `schemas/bluecad_*.schema.json` (contracts),
BlueRev domain package separate (see tooling doc, boundary rule 5).

---

## 1. Tool registry schema

One YAML file, `configs/bluecad_tools.yaml`, validated by
`schemas/bluecad_tool_registry_v0_1.schema.json`. Every external tool the
adapters may invoke must be registered; adapters refuse to run unregistered
tools (fail-closed here because the blast radius is arbitrary process
execution — consistent with the determinism/blast-radius principle).

```yaml
registry_version: bluecad_tool_registry_v0_1
tools:
  - id: build123d
    kind: cad_kernel            # cad_kernel | mesher | fem_solver | cfd_solver | viewer
    integration_mode: in_process # in_process | subprocess | container
    version_pin: "0.x.y"        # exact pin, no ranges
    license: { spdx: Apache-2.0, boundary: A }   # boundary per tooling doc A/B/C/D
    entrypoint: null            # python import for in_process
    capabilities: [brep, sweep, boolean, fillet, step_export, stl_export]
    health_check: "python -c \"import build123d\""
  - id: gmsh
    kind: mesher
    integration_mode: subprocess
    version_pin: "4.x.y"
    license: { spdx: GPL-2.0-or-later, boundary: C }
    entrypoint: "C:/tools/gmsh/gmsh.exe"
    binary_sha256: "<hash>"     # required for subprocess/container tools
    capabilities: [step_import, tet_mesh, physical_groups, inp_export]
    health_check: "gmsh --version"
  - id: calculix
    kind: fem_solver
    integration_mode: subprocess
    version_pin: "2.x"
    license: { spdx: GPL-2.0, boundary: C }
    entrypoint: "C:/tools/ccx/ccx.exe"
    binary_sha256: "<hash>"
    provenance_url: "<where the binary came from>"
    capabilities: [static, modal, thermal]
    health_check: "ccx -v"
```

Decisions:
- **Exact version pins + binary hashes.** Determinism of the whole pipeline
  starts here. Upgrading a tool is a deliberate registry change, reviewed.
- License fields are informative duplication of the tooling doc so CI can
  assert `boundary in {C, D} → integration_mode != in_process`.

---

## 2. Domain primitive model — `GeometrySpec v0`

Neutral, versioned JSON (`schemas/bluecad_geometry_spec_v0_1.schema.json`).
Units: **millimetres, kilograms, seconds, radians** everywhere. No unit
fields, no ambiguity. All numbers finite; canonical JSON for digesting.

```json
{
  "spec_version": "bluecad_geometry_spec_v0_1",
  "spec_id": "sha256-derived stable id",
  "name": "pilot_loop_v3",
  "parts": [
    { "part_id": "run1", "kind": "tube_run",
      "params": { "outer_d": 110.0, "wall_t": 4.0, "length": 6000.0 },
      "frame": { "origin": [0,0,0], "direction": [1,0,0] } },
    { "part_id": "bend1", "kind": "bend",
      "params": { "outer_d": 110.0, "wall_t": 4.0,
                  "bend_radius": 400.0, "angle": 3.14159265 } },
    { "part_id": "joint1", "kind": "joint",
      "params": { "joint_type": "socket", "outer_d": 110.0, "socket_len": 120.0 } }
  ],
  "connections": [
    { "from": "run1.port_b", "to": "bend1.port_a" },
    { "from": "bend1.port_b", "to": "joint1.port_a" }
  ],
  "declared": {
    "total_volume_mm3": { "value": 1.234e7, "rel_tol": 0.02 },
    "bbox_mm": { "min": [0,0,0], "max": [6500, 900, 200], "abs_tol": 5.0 },
    "min_wall_t": 3.5
  }
}
```

Decisions:
- **Part kinds v0**: `tube_run`, `bend`, `joint`, `manifold`, `float`,
  `anchor_mount`, `harvest_module` — the last four start as parametric
  stubs (simple solids with correct ports) and gain fidelity later.
  The *spec schema* must not change when fidelity improves; only builders do.
- **Stub definitions (frozen 2026-07-03, slice 005b)** — all axisymmetric or
  box-like, all ports are standard circular interfaces:
  - `manifold`: cylindrical header (`outer_d_main`, `wall_t`, `length`) with
    `n_out` equally-spaced perpendicular branch stubs (`out_d`, `out_wall_t`,
    `spacing`); ports `in_a`, `in_b` (header ends), `out_1..out_n`
    (generated names — port count is parametric, schema unchanged).
  - `float`: closed capped cylinder (`outer_d`, `length`); `n_mounts` mount
    ports `mount_1..mount_n` as frames on the top surface (mount interface =
    flat circular pad, `pad_d`).
  - `anchor_mount`: base plate + lug (`base_w`, `base_l`, `base_t`, `eye_d`);
    port `mount_a` (pad interface, mates float/tube clamp).
  - `harvest_module`: closed vertical vessel (`outer_d`, `height`, `wall_t`);
    ports `in_a`, `out_a` (side, tube interface), `drain_a` (bottom).
- **Ports are the composition mechanism.** Every part kind declares named
  ports (`port_a`, `port_b`, …); a port = frame (origin, direction) +
  circular interface (`outer_d`, `wall_t`). `connections` are validated
  geometrically (coincident origins, opposed directions, matching diameters)
  — this is the deterministic "smart joint" check.
- **`declared` block is the LLM's contract with the validator.** Any
  AI-proposed spec must declare expected volume/bbox/wall so Tier 1 can catch
  hallucinated geometry. Human-authored specs may omit it (validator then
  only runs intrinsic checks).
- Two proposal levels share this schema:
  - **L1 (default, alpha)**: AI emits a `GeometrySpec` — pure data, maximally
    validatable. The builder is deterministic JarvisOS code.
  - **L2 (experimental flag)**: AI emits a build123d *script* for one novel
    `part_id` (e.g. harvesting internals), executed in the sandboxed runner;
    the result must still expose declared ports and pass the same validators.
    L2 scripts never touch the filesystem/network (existing runner policy).

---

## 3. CAD adapter contract

```
build(spec: GeometrySpec, out_dir) -> BuildResult
```

- **Execution model**: the L1 builder is trusted JarvisOS code and runs in a
  **JarvisOS-owned worker subprocess** (plain Python child process, our code —
  no license implication). Rationale: OCCT kernel operations are not safely
  interruptible in-thread, so timeout enforcement = kill the worker; this
  also isolates kernel crashes from the backend. L2 (AI-generated) scripts
  additionally require the sandboxed-runner policy. **Seam-verified
  2026-07-03** (`BLUECAD_SEAM_MAP.md`): the current runner cannot host L2
  scripts — registration accepts only `batch_growth_v0` with a bundled
  script, and input validation is batch-growth-specific. Its sandbox is a
  text-marker denylist + stripped env + path/hash constraints, **not** an
  OS-level network block. L2 therefore needs a scoped runner-extension spec
  (new `implementation_kind`, GeometrySpec input validation) as a
  prerequisite of spec 012; the denylist-based policy is acceptable for L2's
  local blast radius but must be described honestly, not as "network
  blocked".
- **Outputs (all four, always):**
  1. `model.step` — STEP AP214, source of truth;
  2. `model.stl` — mesh for Gmsh input and quick checks;
  3. `model.glb` — for the frontend three.js viewer (primary path: build123d
     glTF export; verified fallback: STL→GLB conversion via `trimesh`, MIT);
  4. `manifest.json` — spec_id, tool versions from registry, per-part solids
     produced, port table (resolved absolute frames), timing, sha256 of each
     artifact.
- **Determinism:** same spec + same registry pins → byte-identical manifest
  geometry fields (volumes, bboxes, port frames). STEP bytes may differ
  (timestamps); geometric assertions in tests, not byte equality.
- **Error taxonomy (machine-readable, feeds the repair loop):**
  `SPEC_INVALID` (schema/params), `PORT_MISMATCH` (connection check failed),
  `KERNEL_ERROR` (boolean/sweep failure), `EXPORT_ERROR`, `TIMEOUT`,
  `SANDBOX_VIOLATION` (L2 only, non-retryable).

## 4. Geometry validation contract

`validate(artifacts, spec) -> validation_report` — deterministic, no LLM, no
network, pure function of inputs.
`schemas/bluecad_validation_report_v0_1.schema.json`:

```json
{
  "report_version": "bluecad_validation_report_v0_1",
  "spec_id": "...", "manifest_sha256": "...",
  "verdict": "pass",              
  "checks": [
    { "id": "T1_BREP_VALID",    "tier": 1, "status": "pass", "detail": {} },
    { "id": "T1_WATERTIGHT",    "tier": 1, "status": "pass", "detail": {} },
    { "id": "T1_VOLUME_DECL",   "tier": 1, "status": "fail",
      "detail": { "declared": 1.234e7, "actual": 1.301e7, "rel_err": 0.054 },
      "hint": "actual volume 5.4% above declared; check wall_t or length" }
  ]
}
```

- **Tier 0 — execution**: build completed, all four artifacts present,
  manifest consistent.
- **Tier 1 — geometric** (generic, ships in alpha): OCCT B-rep validity per
  solid; watertight/closed shells; no self-intersection; volume & bbox vs
  `declared` within tolerance; min wall thickness where declared; port
  conformity for every `connection`; single connected assembly (no floating
  parts) unless spec says otherwise.
- **Tier 2 — domain** (plugin interface, implementations BlueRev-private):
  `DomainValidator.check(manifest, spec) -> [CheckResult]`. Examples: bend
  radius ≥ k·D, buoyancy margin, drainage slope. JarvisOS defines the
  interface and runs whatever plugins are installed; zero BlueRev formulas in
  this repo.
- **Tier 3 — analysis**: pass criteria evaluated on FEM/CFD `ResultSummary`
  (§5), expressed as data in the AnalysisSpec (e.g.
  `max_von_mises <= yield/1.5`), never hardcoded.
- `verdict = pass` iff every non-skipped check passes. `hint` strings are
  generated deterministically (templates) — they exist to make the AI repair
  loop cheap, not to be authoritative.

## 5. Mesh / FEM adapter contract

`AnalysisSpec` (`schemas/bluecad_analysis_spec_v0_1.schema.json`): input
geometry ref (manifest), `analysis_type` (`static` | `modal` | `thermal` |
future `cfd_external_flow` | `cfd_internal_flow`), material (E, nu, rho,
yield), named boundary conditions and loads **addressed by port/face labels
from the manifest**, mesh controls (target element size, refinement zones),
pass criteria (Tier 3, as data).

Pipeline decisions:
- **Gmsh subprocess**: input STEP; physical groups named
  `BC_<label>` / `LOAD_<label>` derived from manifest port/face labels — this
  is the deterministic link between geometry and analysis. **Mechanism
  (decided)**: the adapter generates a `.geo` script that selects faces via
  Gmsh's `Surface In BoundingBox {…}` using the absolute port frames from the
  manifest (small box around each port plane), rather than relying on STEP
  import tags, which are not contractually stable. Output `.inp`
  (CalculiX format). Mesh quality gate: report min/max element quality,
  fail if below thresholds (data in AnalysisSpec).
- **CalculiX subprocess**: generated `.inp` = template + spec data only (no
  free-form LLM text into solver decks — the AI proposes *AnalysisSpec*
  changes, never raw `.inp`). Parse `.frd`/`.dat` for a fixed quantity set:
  max displacement (node, value), max von Mises (element, value), reaction
  forces, first N natural frequencies (modal).
- **`ResultSummary` JSON**: those quantities + solver exit status + artifact
  refs (frd, log). This is what Tier 3 evaluates and what review agents read.
  Agents never parse raw solver output.
- Error taxonomy: `MESH_FAIL`, `MESH_QUALITY_FAIL`, `SOLVE_DIVERGED`,
  `SOLVE_ERROR`, `PARSE_ERROR`, `TIMEOUT` — machine-readable, retryable
  flags included (e.g. `MESH_QUALITY_FAIL` → retry with finer size is a
  deterministic policy, not an LLM call).

## 6. CFD boundary (designed now, implemented later)

- Same shape as FEM: `AnalysisSpec(analysis_type=cfd_*)` in →
  `ResultSummary` out. No new top-level concepts.
- **Case-bundle contract**: the CFD adapter materializes a frozen OpenFOAM
  case directory (`0/`, `constant/`, `system/`) from templates + spec data;
  geometry enters as STL from the CAD adapter; meshing via snappyHexMesh (or
  Gmsh→polyMesh); execution in WSL2/container (boundary D); results
  extracted only via postProcess function objects into `ResultSummary`
  (forces/coefficients, patch-averaged fields) + VTK artifacts for viewing.
- v0 target analyses (when implemented): external steady flow around
  float/tube cluster → drag/lift coefficients; internal single-phase flow in
  a tube run → pressure drop vs the domain correlation (mutual sanity check).
  Multiphase/waves are explicitly out of the boundary until a dedicated
  design pass.
- Templates are JarvisOS-generic; **anything encoding BlueRev operating
  conditions arrives via AnalysisSpec data**.

## 7. AI-CAD loop

```
context (workspace, ports catalog, prior reports)
   │
   ▼
cad.generate  ──▶ candidate = GeometrySpec (L1) [or L2 script]
   │                    │
   │                    ▼
   │              build → validate  ──pass──▶ candidate marked VALID
   │                    │                        │
   │                  fail                       ▼ (optional) mesh+solve → Tier 3
   │                    ▼                        │
   └── cad.repair ◀── validation_report      review panel (multi-agent)
        (bounded: max 3 attempts,                │ structured critique +
         then escalate tier once,                ▼ proposed spec deltas
         then park for human)             new cycle OR human Decision (promote)
```

Decisions:
- **The repair loop input is the `validation_report` + failing spec, nothing
  else.** Reports are designed to be sufficient (hints, actual-vs-declared).
- **Bounded retries as data**: `max_attempts_per_tier = 3`,
  `escalation_ladder = [workhorse, frontier]`, then `parked` status with the
  full attempt trail stored as workspace artifacts. No unbounded loops, no
  silent spend — this is a blast-radius boundary (spend), so fail-closed.
- **Attempt ledger storage (decided, seam-verified)**: new module-owned
  tables `bluecad_candidates` and `bluecad_attempts`; each attempt references
  the `ai_jobs.id` of its LLM call(s) and the `artifacts.id` of its outputs.
  Existing `ai_jobs` (per-call ledger) and `artifacts` schemas are reused
  untouched — no columns added to core tables. A provider call blocked by
  budget/settings (`external_blocked_reason`) parks the candidate with that
  reason recorded; it is never treated as a retryable failure.
- **Review panel**: N agents (cheap tier) each receive the same artifact set
  — validation_report, ResultSummary, manifest, GLB snapshot render (later) —
  and return a structured critique
  (`schemas/bluecad_review_critique_v0_1.schema.json`: findings[], each with
  severity, affected part_ids, proposed_delta as a JSON-patch against the
  GeometrySpec). One frontier-tier synthesizer merges critiques into at most
  one proposed next candidate. Panel output is **advisory**: it becomes a new
  `cad.generate/repair` input, never a direct write.
- **Promotion is human-gated**: a VALID candidate (+ its reports) is promoted
  to a workspace Decision by the user. Autopilot may run the loop; it may
  never promote.
- L2 scripts get one extra non-negotiable rule: `SANDBOX_VIOLATION` is
  non-retryable and parks the proposal immediately.

## 8. Routing integration

All LLM calls in §7 go through RouterPolicy as ordinary provider calls
(decision contract v3.1.1 unchanged — BLUECAD adds task types, not schema).

| Task type | Default tier | Escalation | Notes |
| --- | --- | --- | --- |
| `bluecad.cad.generate` | workhorse (DeepSeek/GLM/Kimi class) | on 3 failed repairs → frontier, once | high volume, cheap |
| `bluecad.cad.repair` | same tier as the failed attempt | ladder above | input = report + spec only |
| `bluecad.review.panelist` | workhorse ×N (N=2–3) | none | parallel critiques |
| `bluecad.review.synthesis` | frontier (Claude class) | none | one call per cycle |
| `bluecad.fem.interpret` | frontier | none | turns ResultSummary into human-readable engineering commentary; advisory |
| `bluecad.spec.explain` | local/workhorse | none | cheap UX explanations |

- **Alpha reality check (seam-verified 2026-07-03, see `BLUECAD_SEAM_MAP.md`)**:
  the RouterPolicy `auto` path is non-executing by design (external candidates
  become `ask_user_confirm`/`propose_only` control records; confirmation
  replay is not implemented). The only executing path today is the explicit
  `external:cheap` / `external:reasoning` route via
  `AIGateway.run_task → run_ai_task → ScalewayProviderAdapter`. Therefore in
  the alpha: the tier names above map to `workhorse = external:cheap`,
  `frontier-for-now = external:reasoning` (both Scaleway bindings); a true
  frontier (Claude-class) adapter is future work, not an alpha prerequisite.
  The BLUECAD loop calls the explicit route path with its own task kinds and
  inherits the existing budget/settings gates (`evaluate_ai_status`,
  `external_blocked_reason`) for free. Known constraint to size in spec 010:
  the provider HTTP timeout is currently 20s and `AIUsage` carries token
  counts but no provider cost estimate on the Scaleway success path — attempt
  costs are token-derived.
- Sensitivity: BLUECAD payloads are workspace-scoped engineering data; they
  follow the existing sensitivity taxonomy / egress policy — no new
  mechanism. (Concept-level BlueRev sensitivity is a *user* choice of which
  workspaces route externally, not a BLUECAD-layer control.)
- Budget: the attempt ledger (per-candidate attempts, tokens, cost) reuses
  the grading/ledger spine — each loop cycle is one graded execution record.

## 9. Roadmap — implementation slices (specs)

| Spec | Slice | Depends | Fable needed? |
| --- | --- | --- | --- |
| **005** | CAD adapter MVP: GeometrySpec v0 (tube_run, bend, joint), deterministic builder, STEP/STL/GLB export, Tier 0–1 validation, golden tests | — | spec written by Fable; implementation Codex |
| 005b | Remaining part-kind builders as parametric stubs (manifold, float, anchor_mount, harvest_module — definitions frozen in §2); enables full-reactor layouts | 005 | no (mechanical, follows 005 pattern + §2 definitions) |
| 006 | Frontend 3D viewer: GLB panel + validation report view + attempt history | 005 (010 for history) | no (boilerplate) |
| 006b | Parametric variants: sliders on a valid candidate's params → deterministic rebuild (no LLM), variant recorded as child candidate | 006, 010 | no (deterministic path reuse) |
| 007 | Tool registry + health checks + CI license-boundary assert | — | no |
| 008 | Gmsh mesh adapter (subprocess, physical groups, quality gate) | 005, 007 | no |
| 009 | CalculiX FEM adapter + ResultSummary + Tier 3 | 008 | review only |
| 010 | AI loop v0: `cad.generate` + repair loop + attempt ledger (L1 only) | 005, router | review only |
| 011 | Review panel + synthesis + critique schema | 010 | review only |
| 012 | L2 script proposals behind flag | 010 | review only |
| 013 | Domain validator plugin interface (Tier 2) + one dummy plugin | 005 | no |
| 014 | CFD case-bundle adapter v0 (external flow) | 008 | design done here; no |
| 018 | Chat entry point: minimal chat command that creates a BLUECAD candidate via the 010 API and links to the workbench | 010 | no |

**Alpha staging (user-confirmed 2026-07-03):**
- **Alpha-1** (pipeline proof) = 005 + 006 + 010: brief → AI-generated
  tube/bend/joint geometry, validated, visible in the workbench viewer.
- **Alpha-2** (user's alpha gate) = alpha-1 + 005b + 006b + 018: a
  recognizable full-reactor layout (parallel runs, manifolds, floats,
  harvesting stub), parametric sliders with deterministic rebuild, and a
  minimal chat entry point. Interaction model: workbench as the primary
  surface, chat as a thin on-ramp.

Everything after 011 (and all of alpha-2) is safely post-Fable: contracts and
stub definitions are fixed here, slices are mechanical, Opus 4.8 reviews.

## 10. Hard invariants (recap, binding for all slices)

1. License boundaries per `BLUECAD_TOOLING_AND_LICENSING.md` (no GPL
   in-process; no copyleft vendoring; OCCT via unmodified wheels).
2. LLM output is advisory; only deterministic validators produce verdicts;
   only humans promote Decisions.
3. Adapters/validators are deterministic pure functions of (spec, artifacts,
   registry pins).
4. All external tool invocations go through the registry (pin + hash).
5. AI never writes raw solver decks or raw geometry files — only
   GeometrySpec/AnalysisSpec (L1) or sandboxed scripts (L2, flagged).
6. Bounded retries and spend on every AI loop; parked, never silent-failed.
7. No BlueRev formulas in JarvisOS code (layering rule; data flows freely).

## 11. Technical assumption ledger

Unverified assumptions, each with a deadline (the slice that depends on it).
Verifying these is part of the *preceding* slice's definition of done or a
5-minute spike before starting. An assumption past its deadline blocks the
slice.

| # | Assumption | Verify how | Deadline |
| --- | --- | --- | --- |
| A1 | ✅ **VERIFIED 2026-07-03** (spike, `reports/bluecad_spike_a1_a2.md`): native GLB export works — `build123d.export_gltf(binary=True)` on build123d 0.11.1 / cadquery-ocp-novtk 7.9.3.1.1 / Python 3.13. trimesh fallback not needed | — | closed |
| A2 | ✅ **VERIFIED 2026-07-03** (same spike): Tier 1 checks available — `Shape.is_valid`, `Shape.is_manifold`, `OCP.BRepCheck.BRepCheck_Analyzer`, closed-shell via `OCP.BRep.BRep_Tool.IsClosed_s`. Volumes match analytic values to machine precision | — | closed |
| A3 | `Surface In BoundingBox` face selection is robust for our port geometry | spike during 008 spec review with a 005 golden STEP | before 008 |
| A4 | A trusted CalculiX Windows binary exists (or WSL2 build) with recordable provenance | manual: locate, hash, register | before 009 |
| A5 | ✅ **VERIFIED 2026-07-03** (`BLUECAD_SEAM_MAP.md`): multi-step loop infra **does not exist** — spec 010 builds it. Executing provider path = explicit `external:*` routes only (auto path is non-executing control); single provider adapter (Scaleway); `ai_jobs` is a reusable per-call ledger; attempt tables are new module-owned schema (§7) | — | closed; findings folded into §7/§8 |
| A6 | ✅ **VERIFIED 2026-07-03** (`BLUECAD_SEAM_MAP.md`): runner **cannot** host L2 today (only `batch_growth_v0`, batch-growth input validation, denylist-based policy, no OS network block). Scoped runner-extension spec required as prerequisite of 012 | — | closed; new prerequisite spec added before 012 |
| A7 | Remaining license rows marked "high-confidence" in the tooling doc (incl. `cadquery-ocp-novtk` wheel license) | fetch each LICENSE at version-pin time | slice 007 |
