# 024 — FEM verification battery

Status: ready (definition reconciled 2026-07-10; live state remains in
`docs/specs/STATUS.md`)
Depends on: 008, 009, 021b

## Goal

Give JarvisOS a credible, repeatable acceptance boundary for the real
Gmsh → CalculiX static-FEM chain. The completed work must prove three separate
claims instead of conflating them:

1. the mesh adapter can request and verify quadratic tetrahedra without changing
   existing first-order behavior;
2. a pressure attached to a named geometric surface reaches the correct faces of
   solid elements and produces the expected resultant reaction;
3. prescribed benchmark results agree with closed-form mechanics solutions at
   stated locations and tolerances.

Passing a solver process, obtaining a non-empty FRD file, or reporting a global
maximum is not sufficient evidence for any of these claims.

## Why this definition replaces the previous draft

The earlier body and its appended review resolutions contradicted one another.
It simultaneously declared adapter changes out of scope, required C3D10, left
Lamé blocked, and later declared it unblocked. A fresh code audit found further
load-bearing blockers:

- `schemas/bluecad_analysis_spec_v0_1.schema.json` has no `mesh.element_order`;
- `mesh_adapter.py` invokes Gmsh without `-order 2`, so current volume elements
  are first order;
- the mesh adapter identifies named surfaces through cubic bounding boxes and
  Gmsh exports boundary elements for those groups;
- `fem_adapter.py` currently emits `*DLOAD` directly against the named load set
  with `P`, but no real test proves that the set is translated to the intended
  face of a C3D4/C3D10 solid;
- the existing FEM tests exercise `force_total`, not real pressure;
- global `max_von_mises` can occur at a fixed-end disturbance or another local
  concentration and therefore cannot validate Lamé or Kirsch at their analytic
  comparison locations;
- the existing per-label `mesh.refinements` path records a comment but does not
  create a Gmsh refinement field, so this battery may not claim local refinement;
- the existing density examples use the N–mm–s-consistent value for tonnes per
  cubic millimetre while schema prose calls the mass unit kilograms.

This reconciled contract supersedes every earlier `pending`, `STOP`, linear-tet,
and appended-resolution clause in this file. There is one binding definition
below.

## Delivery structure

024 is implemented as three ordered PR slices. Do not combine them unless the
maintainer explicitly chooses a larger review boundary after seeing the diff.

- **024-A — quadratic tetrahedron contract**
- **024-B — solid-face pressure contract**
- **024-C — analytic benchmark battery and report**

The registry row remains one spec and may list multiple implementation PRs.
Each slice must be independently green before the next begins.

# 024-A — quadratic tetrahedron contract

## Scope

Add one backward-compatible AnalysisSpec field:

```json
"mesh": {
  "target_size": 5.0,
  "element_order": 2
}
```

Binding semantics:

- `element_order` is optional;
- allowed values are integer `1` and `2`;
- absence is exactly equivalent to `1`;
- order `1` preserves the current Gmsh invocation and C3D4 behavior;
- order `2` adds the narrow Gmsh order request required to produce quadratic
  tetrahedra;
- no other mesh option, adaptive algorithm, optimization pass, or solver setting
  is added.

The adapter must not claim quadratic output from the requested flag alone. It
must inspect the generated CalculiX mesh artifact and fail closed if an order-2
request produces no C3D10 volume elements or mixes unsupported volume types.

Because this slice already changes the AnalysisSpec schema, it also corrects the
schema description only: the coherent mass unit for the existing N–mm–s system
is **tonne**, so steel density is approximately `7.85e-9 tonne/mm^3`. This is a
factual documentation correction, not a validation-rule or runtime conversion
change. Static benchmark results must not depend on density.

## 024-A acceptance criteria

1. The schema accepts `element_order` only as integer `1` or `2`, defaulting to
   current order-1 behavior when omitted.
2. Omitted order and explicit order `1` produce the same command contract and
   equivalent generated mesh behavior.
3. Order `2` causes the registered Gmsh subprocess invocation to request second
   order; no in-process `gmsh` import is introduced.
4. Offline fake-tool tests distinguish C3D4 and C3D10 output and reject a fake
   tool that ignores the order-2 request.
5. The existing INP parser and FEM mesh reader accept C3D10 connectivity without
   truncation or filtering.
6. A real hash-pinned Gmsh run under the existing strict-tool workflow produces
   a non-empty mesh whose volume element records are C3D10.
7. A real CalculiX smoke solve consumes that C3D10 mesh and produces parseable
   displacement and stress blocks.
8. Schema prose and fixtures name the density unit `tonne/mm^3`; no hidden density
   conversion is added.
9. Existing order-1 tests and the complete backend suite remain green.

## 024-A non-goals

- No pressure implementation.
- No benchmark geometry.
- No tolerance or analytic comparison.
- No default switch from order 1 to order 2 outside the battery fixtures.
- No change to candidate promotion or normal BLUECAD loop defaults.

# 024-B — solid-face pressure contract

## Problem

A named Gmsh physical surface is represented by boundary elements. CalculiX
solid pressure must be bound to the corresponding face of the adjacent volume
element. A boundary-element ELSET is not accepted as proof that the intended
solid face received the pressure.

## Required behavior

Add a deterministic translation step owned by the FEM adapter:

1. parse the named pressure surface elements from the mesh artifact;
2. map every surface element to exactly one adjacent BODY volume-element face;
3. support the element families used by 024: C3D4 with triangular first-order
   faces and C3D10 with triangular quadratic faces;
4. emit CalculiX pressure loads against explicit volume-element face identifiers
   using the face-number convention verified against the installed solver;
5. reject zero matches, non-manifold matches, ambiguous matches, unsupported
   element families, duplicate face assignments, and pressure groups containing
   elements outside BODY;
6. retain an inspectable mapping artifact or structured mapping summary in the
   solve output directory.

The mapping must use connectivity, not coordinate proximity alone. Corner-node
identity establishes adjacency; midside nodes must also be checked for C3D10.

## Mandatory real pressure proof

Before Lamé is permitted, run a rectangular solid patch test:

- geometry: `10 mm × 10 mm × 10 mm` solid;
- material: linear elastic steel, `E = 200000 MPa`, `nu = 0.3`;
- one face fixed;
- opposite face loaded by uniform pressure `p = 1 MPa`;
- expected resultant magnitude: `p A = 100 N`;
- C3D10 mesh;
- reaction resultant on the fixed face must oppose the applied load and agree
  within `1%`;
- no transverse resultant may exceed `0.5%` of `p A`.

This test proves surface selection, face numbering, pressure sign, deck syntax,
and solver interpretation together. A deck-text assertion alone is insufficient.

## 024-B acceptance criteria

1. Unit tests cover C3D4 and C3D10 face mapping for every local face number.
2. Adversarial meshes fail closed for missing, duplicate, ambiguous, detached,
   mixed-order, or unsupported pressure surfaces.
3. Existing `force_total` behavior is unchanged.
4. The real pressure patch test passes the reaction-balance criteria above with
   hash-verified Gmsh and CalculiX.
5. The generated deck and mapping evidence remain in the bounded proof artifact.
6. No shell section or fake boundary-element pressure is used to stand in for a
   solid-face load.

## 024-B non-goals

- No contact, gravity, centrifugal load, fluid coupling, follower load, or
  nonlinear pressure.
- No generic surface-query language.
- No Lamé tolerance claim before the patch test is green.

# 024-C — analytic benchmark battery

## Common contract

All cases:

- use the real registry-bound Gmsh and CalculiX executables;
- use C3D10 (`mesh.element_order = 2`);
- use the coherent N–mm–s system: geometry in mm, force in N, stress in MPa,
  mass in tonne, and density in `tonne/mm^3`;
- use deterministic checked-in STEP and manifest fixtures generated from an
  inspectable fixture-builder script;
- call `mesh_adapter.mesh_analysis_spec` and
  `fem_adapter.solve_static_analysis` rather than invoking binaries directly;
- preserve mesh, deck, FRD, DAT, logs, tool versions, registry hashes, and
  comparison data in the report artifact;
- compare the analytic quantity at the analytic location, not merely against a
  global maximum;
- fail closed when the expected sampling region is absent or under-resolved;
- verify that the fixed-face reaction resultant agrees with the applied force or
  pressure resultant within `1%`, with unintended transverse components below
  `0.5%` of the intended resultant.

Material for all three cases unless a fixture states otherwise:

- `E = 200000 MPa`;
- `nu = 0.3`;
- `rho = 7.85e-9 tonne/mm^3`;
- `yield_strength = 250 MPa`.

Density is schema-required but not load-bearing in these static cases. The loads
remain safely in the linear-elastic range.

## Battery-side result sampling

Add a verification-owned parser that reads:

- node coordinates and connectivity from the generated CalculiX mesh INP;
- nodal displacement/stress blocks from the retained FRD;
- named surface membership from the mesh groups.

It may share pure numeric helpers with the existing FEM parser, but it must not
change ResultSummary semantics or silently substitute a global maximum.

For a Cartesian stress tensor ordered as `SXX, SYY, SZZ, SXY, SYZ, SZX`, the
cylindrical hoop component about the z axis is computed explicitly from the
node angle. Parser tests must bind component names/order from the FRD headers;
position-only assumptions are forbidden.

Sampling outputs include selected node IDs, coordinates, raw tensors,
transformed values, aggregation method, and location residuals.

## Case A — slender cantilever tip displacement

Prescribed reference fixture:

- rectangular beam: `L = 200 mm`, `b = 10 mm`, `h = 10 mm`;
- fully fixed root face;
- total transverse end-face force `F = 100 N`;
- second moment `I = b h^3 / 12`;
- analytic Euler–Bernoulli displacement:
  `delta = F L^3 / (3 E I) = 1.6 mm`;
- prescribed fine global target size no larger than `h / 3`;
- compare the maximum displacement magnitude only after proving that its node is
  on the loaded tip face;
- relative-error tolerance: `2%`.

The report also records a coarser run at twice the fine target size. The fine
result must pass the absolute tolerance and must not be less accurate than the
coarse result. This is a two-level refinement sanity check, not a formal order
of convergence claim.

## Case B — thick-walled open-end cylinder under internal pressure

Prescribed reference fixture:

- inner radius `a = 20 mm`;
- outer radius `b = 40 mm`;
- length `L = 160 mm`;
- one end fixed to remove rigid motion; its Saint-Venant disturbance is excluded
  from the comparison region;
- bore surface loaded with `p = 10 MPa`;
- outer surface and remote end traction-free;
- no pressure end-cap load, therefore the mid-length analytic state is open-end;
- global target size no larger than `(b - a) / 4`;
- analytic bore stresses:
  - `sigma_theta(a) = p (b^2 + a^2) / (b^2 - a^2) = 16.6666667 MPa`;
  - `sigma_r(a) = -p = -10 MPa`;
  - `sigma_z(a) approximately 0` away from the fixed end.

The current mesh adapter uses cubic port-selection boxes. One cube large enough
to contain the full long bore would also contain the outer cylinder and end
faces. Therefore the fixture must partition the bore into deterministic axial
surface bands, each short enough for its selection cube to exclude the outer and
end surfaces. Each band has a distinct manifest label and an identical pressure
load. The union of mapped bands must cover the bore exactly once: no gaps,
duplicates, outer-surface elements, or end-face elements. This is fixture design,
not a new generic surface-selection API.

Sampling contract:

- use bore-surface nodes in the axial layer nearest `z = L / 2`;
- require at least eight distinct angular samples;
- require mean sampled radius within `1%` of `a` and mean z within one global mesh
  spacing of `L / 2`;
- compare the arithmetic mean transformed hoop stress with the analytic value;
- relative-error tolerance: `5%`;
- radial-stress sign and magnitude are mandatory sanity evidence; a wrong sign or
  error above `10%` fails even if hoop stress happens to pass;
- report axial stress but do not use it as the primary pass metric.

A fixed-end global stress maximum is irrelevant and must not be used.

## Case C — finite-width plate with central circular hole

Prescribed reference fixture:

- plate length `200 mm`, width `W = 100 mm`, thickness `t = 5 mm`;
- centered circular hole diameter `d = 20 mm`, so `x = d / W = 0.2`;
- one remote end fixed;
- opposite remote end loaded by total axial force `F = 5000 N`;
- hole centered midway between loaded and fixed ends;
- net-section nominal stress
  `sigma_nom = F / ((W - d) t) = 12.5 MPa`;
- finite-width net-section correction:
  `Kt(x) = 3 - 3.14 x + 3.667 x^2 - 1.527 x^3`;
- at `x = 0.2`, `Kt = 2.506464` and
  `sigma_peak = 31.3308 MPa`;
- global target size no larger than `d / 12`; the current adapter does not yet
  provide a real local-refinement field;
- relative-error tolerance: `7%`.

The net-section convention is physically load-bearing: as `d/W` approaches one,
the polynomial remains finite, so combining it with gross-section nominal stress
would produce a non-diverging peak stress and is invalid. The implementation
report must still cite the exact Peterson/Pilkey source edition used for the
polynomial and confirm the net-section convention. If that source check
contradicts the equation or convention above, STOP and amend the definition
rather than silently changing the denominator.

Sampling contract:

- sample hole-boundary nodes near the transverse diameter where the tensile
  tangential stress peaks;
- use symmetric points on both sides and the mid-thickness layer;
- transform the stress tensor into the local tangential direction;
- compare the symmetric mean with `sigma_peak`;
- reject a result selected from the fixed or loaded end.

Global `max_von_mises` is recorded only as diagnostic evidence.

## Geometry fixtures

Fixtures live under a dedicated bounded directory such as
`backend/tests/bluecad/fixtures/fem_verification/` and include:

- STEP geometry;
- manifest JSON;
- a source generator script;
- a fixture manifest binding generator version, dimensions, and SHA-256 values.

The battery consumes checked-in fixtures. Regeneration is an explicit maintainer
operation and a fixture digest change requires review. No machine-specific path
is checked in.

## Comparison and report module

Add pure, offline-testable functions for:

- beam displacement;
- Lamé stresses;
- finite-width plate correction;
- relative error and tolerance evaluation;
- INP coordinate/connectivity/group parsing;
- FRD component-aware stress parsing;
- Cartesian-to-cylindrical/tangential stress transformation;
- location filtering and deterministic aggregation;
- Markdown and JSON report rendering.

The generated report contains at minimum:

- timestamp and git SHA;
- OS/Python versions;
- Gmsh and CalculiX version pins and binary hashes;
- fixture digests;
- mesh element order and counts;
- per-case coarse/fine target sizes where applicable;
- analytic formula, inputs, expected value, sampled value, relative error,
  tolerance, and verdict;
- applied and reaction resultants;
- sampling node IDs and location residuals;
- artifact paths relative to the uploaded proof root;
- explicit limitations: linear elasticity, static analysis, ideal geometry,
  and benchmark acceptance rather than certification.

Write `reports/bluecad_fem_verification_battery.md` and a machine-readable JSON
next to it during the run. CI uploads them as artifacts; CI does not commit
runtime-generated reports back to the repository.

## Workflow contract

Extend the existing real-tool proof infrastructure rather than creating an
unrelated provider or execution path.

- Offline formula/parser/report tests run in normal CI.
- Each implementation slice adds its focused real-tool test to the existing
  hash-pinned BLUECAD proof workflow or a narrowly separated job in that same
  workflow.
- The complete analytic battery runs on 024-C changes and via
  `workflow_dispatch`.
- Normal tests remain offline when no registry is enabled.
- No paid model, provider, or network API is involved beyond package installation
  already owned by the tool-proof workflow.

## Required tests

### 024-A

- schema accept/reject/default tests;
- omitted-vs-order-1 compatibility;
- fake Gmsh order propagation and ignored-order rejection;
- C3D10 INP parser and FEM pass-through;
- real C3D10 mesh+solve proof;
- density-unit description regression.

### 024-B

- all C3D4/C3D10 local-face mappings;
- ambiguous/non-manifold/detached/mixed/unsupported rejection;
- pressure deck generation;
- force_total regression;
- real solid patch pressure reaction balance.

### 024-C

- closed-form reference-number tests;
- net-vs-gross nominal-stress regression for the finite-width polynomial;
- FRD component-name/order tests, including reordered headers;
- INP group/coordinate parsing;
- cylindrical/tangential transformations;
- location-selection rejection tests;
- segmented-bore coverage/duplication rejection;
- report determinism with normalized environment inputs;
- one real test per benchmark plus the cantilever refinement sanity run;
- corrupt/missing FRD, missing group, insufficient angular samples, and wrong
  element-order failure cases.

## Global acceptance criteria

024 is complete only when all three implementation slices are merged and:

1. real Gmsh produces verified C3D10 on request while order-1 behavior remains
   backward compatible;
2. real CalculiX pressure on a named solid face passes the patch-test reaction
   balance;
3. cantilever, Lamé, and finite-width-hole cases pass `2%`, `5%`, and `7%`
   location-specific tolerances respectively;
4. applied and reaction resultants pass their balance checks;
5. the battery report and raw bounded artifacts are uploaded from the same run;
6. the complete backend suite and Ruff pass;
7. no conformance test is weakened, skipped by default when strict mode is
   requested, or replaced by fake output;
8. no UI, AI routing, provider behavior, promotion policy, or production default
   is changed.

## Binding stop conditions

Stop and amend the spec rather than guessing when:

- real Gmsh does not emit C3D10 for the chosen STEP/export path;
- CalculiX or the current parser cannot consume the generated C3D10 mesh;
- surface-to-solid-face mapping cannot be made unique from the exported mesh;
- cubic bounding-box groups cannot isolate every segmented bore band without
  selecting outer or end surfaces;
- the pressure patch test fails sign or resultant checks;
- the retained artifacts do not expose coordinates/components needed for
  location-specific sampling;
- the cited finite-width correction uses a different nominal-stress convention;
- a prescribed tolerance requires silent solver tuning, manual mesh editing,
  fictitious local refinement, or a load/BC substitution outside the documented
  adapter contract.

## Non-goals

- No modal, thermal, buckling, fatigue, plasticity, contact, CFD, or certification
  claim.
- No generic FEM framework or broad solver matrix.
- No automatic tolerance loosening.
- No manual mesh edits after Gmsh generation.
- No generic local-refinement implementation in this spec.
- No benchmark result used as authority to promote a BLUECAD candidate.
- No beam-frequency case until spec 027 implements and verifies modal analysis.

## Files likely touched

Verify against the current tree before each slice.

024-A likely touches:

- `schemas/bluecad_analysis_spec_v0_1.schema.json`;
- `backend/app/modules/bluecad/mesh_adapter.py`;
- mesh/fake-tool tests;
- the existing real-tool proof workflow and runbook;
- this spec and spec 008 implementation notes only for factual pointers.

024-B likely touches:

- `backend/app/modules/bluecad/fem_adapter.py`;
- focused FEM pressure-mapping tests and real patch fixture;
- the existing real-tool proof workflow/runbook.

024-C likely touches:

- a new bounded verification module under `backend/app/modules/bluecad/`;
- focused offline and real battery tests;
- benchmark fixtures plus their generator/manifest;
- a battery runner/report renderer;
- the existing real-tool proof workflow/runbook.

## Definition of done

- Three reviewable implementation PRs or an explicitly maintainer-approved
  equivalent split.
- Registry records every implementation PR and becomes `merged` only after the
  final slice.
- Every slice has green normal CI and green applicable real-tool proof.
- Final report is inspectable and contains enough raw evidence to reproduce the
  comparison.
- No generated runtime report, machine path, binary, secret, or tool registry is
  committed.
