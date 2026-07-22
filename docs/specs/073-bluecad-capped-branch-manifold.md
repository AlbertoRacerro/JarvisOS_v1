# 073 — BLUECAD-PRIMITIVE-1: fluid-open capped branch manifold

## Status

Definition complete. Implementation may start only after this definition and the
registry update are merged and the row is `ready`.

## Problem

Spec 072 now provides an explicit non-spatial process topology with one common
supply, one split, 1–12 identical parallel branches, one merge, and one common
return. A future CAD-LINK-1 must not invent or misrepresent the split and merge
hardware.

The current BLUECAD `manifold` primitive is not an honest split/merge primitive:

- it exposes two through-header main ports (`in_a` and `in_b`), while the 072 split
  and merge each require one common port plus N branch ports;
- its branch tubes are unioned with an annular header, but the current builder does
  not explicitly subtract the branch bores through the header wall;
- using it with one main port left open would create a visibly and hydraulically
  false reactor boundary;
- CAD-LINK-1 therefore cannot proceed by merely renaming, rotating, or partially
  connecting the existing primitive.

## Goal

Add one deterministic typed GeometrySpec part kind, `capped_manifold`, that
represents a fluid-open branch header with exactly:

- one common tube port;
- 1–12 branch tube ports;
- one closed far end;
- explicit finite dimensions and no project defaults;
- branch bores that are geometrically open into the common internal cavity;
- deterministic ports, bounding box, material volume, manifest output, and
  property/conformance tests.

The same geometry may be rotated and used downstream as either a split or merge.
Flow direction and process role are not stored in the primitive.

## Dependencies

Hard dependencies:

- `005` — GeometrySpec and deterministic CAD adapter;
- `005b` — typed part-kind builder and interface-aware port conventions;
- `056` — property-based geometry tests and determinism canary.

Context dependency:

- `072` — establishes why a one-common-port branch manifold is needed, but 073
  does not read process runs or manifests and introduces no process/CAD link.

## Scope

### 1. GeometrySpec extension

Add `capped_manifold` to the closed supported part-kind vocabulary.

The exact parameter object is:

```json
{
  "main_outer_d": 0.0,
  "main_wall_t": 0.0,
  "branch_count": 1,
  "branch_outer_d": 0.0,
  "branch_wall_t": 0.0,
  "branch_gap": 0.0,
  "end_gap": 0.0,
  "branch_stub_length": 0.0,
  "cap_thickness": 0.0
}
```

All dimensional values are millimetres. No field is optional and no field has a
runtime or registration default.

`branch_gap` is the clear distance between adjacent branch outer surfaces.
`end_gap` is the clear axial distance between an end plane of the cylindrical
header cavity and the nearest branch outer surface. Both are explicit positive
caller values; the contract does not choose a design clearance.

`branch_stub_length` is the exposed branch centreline length measured from the
outer tangent surface of the header to the branch port. The total branch sweep
from the header centreline is therefore:

```text
main_outer_d / 2 + branch_stub_length
```

Define:

```text
branch_pitch = branch_outer_d + branch_gap
header_length = branch_outer_d + 2 * end_gap
              + branch_pitch * (branch_count - 1)
```

This removes redundant spacing/length degrees of freedom, prevents tangent branch
or end contacts by construction, and guarantees centered repeatable placement.

### 2. Validation rules

Validation is fail-closed before any CAD-kernel call.

Required rules:

- the parameter object is closed to unknown fields;
- every numeric value is finite and strictly positive;
- `branch_count` is an integer in `[1, 12]`, with booleans rejected;
- `2 * main_wall_t < main_outer_d`;
- `2 * branch_wall_t < branch_outer_d`;
- derived `branch_pitch` and `header_length` are finite and positive;
- no semantic `split`, `merge`, `inlet`, `outlet`, flow-rate, pressure, material,
  process-run, or project-value field is accepted.

Because `branch_gap` and `end_gap` are strictly positive, tangent branch shells and
branch/end contacts are outside the valid domain. They are computational geometry
boundaries, not fabrication or design recommendations. No arbitrary maximum cap
thickness or project clearance is introduced.

### 3. Canonical solid

Use the existing BLUECAD unit convention and deterministic build123d boundary.

The part consists of:

1. a cylindrical header shell from `x = 0` to `x = header_length`;
2. one solid circular cap with diameter exactly `main_outer_d`, extending from
   `x = header_length` to `x = header_length + cap_thickness`;
3. `branch_count` branch shells extending in `+y` from the header centreline to
   `y = main_outer_d / 2 + branch_stub_length`;
4. explicit subtraction of:
   - the common internal header cavity;
   - every branch inner bore through the header wall and into the common cavity.

The resulting solid must have one connected material body and an internally
connected fluid cavity from the common opening to every branch opening.

The cap is external to the declared internal header length. Therefore the nominal
header liquid cavity length remains `header_length`; the cap does not silently
consume process volume.

### 4. Ports

Expose exactly these tube-interface ports:

- `common` at `(0, 0, 0)`, direction `(-1, 0, 0)`, using
  `main_outer_d/main_wall_t`;
- `branch_1` through `branch_N`, ordered by increasing x position, each at:

```text
x_i = end_gap + branch_outer_d / 2 + branch_pitch * (i - 1)
y_i = main_outer_d / 2 + branch_stub_length
z_i = 0
```

with direction `(0, 1, 0)` and
`branch_outer_d/branch_wall_t`.

No second common port, cap port, hidden port alias, role-specific port, or dynamic
port name is allowed.

### 5. Deterministic analytic metadata

The builder must return deterministic:

- part kind and ID;
- exact port frames;
- axis-aligned bounding box;
- material volume in mm³;
- build manifest entry;
- kernel shape.

The bounding box must include the external cap thickness and the complete exposed
branch stubs.

Material volume must be taken from the final boolean-result solid, not from a
naive sum that double-counts header/branch intersections. Tests must compare the
reported value to the final kernel solid volume within the existing BLUECAD
numeric tolerance.

### 6. Fluid-opening verification

Add deterministic geometric conformance probes in tests. At minimum:

- a common-bore probe from the common port to the inner cap face intersects no
  material;
- each branch-bore probe from its port into the header cavity intersects no
  material;
- a small probe volume spanning each branch/header junction belongs to one
  continuous void rather than being blocked by the header wall;
- a probe beyond the capped end intersects cap material;
- no opening exists at the capped end.

The implementation may use bounded build123d boolean/intersection checks in tests.
It must not introduce a general fluid-domain mesher or CFD claim.

### 7. Assembly compatibility

The new part must use the existing `PortFrame`, connection placement, port
conformity, export, validation-report, mesh, and FEM boundaries without a second
assembly engine.

Required assembly fixtures:

- common tube → capped manifold;
- capped manifold branch → tube run;
- two capped manifolds connected by 1, 2, and 12 identical straight branch paths;
- the second manifold is rotated through the existing frame/assembly mechanism;
- for the mirrored second manifold, branch `i` on the first manifold connects to
  branch `N + 1 - i` on the second manifold so all x positions remain consistent;
- all connected tube ports must remain coincident, opposed, and dimensionally
  conformant.

This spec does not require a closed-loop reactor layout or a 072 converter.

### 8. Schema and fixtures

Update the canonical GeometrySpec JSON schema and Python validation together.

Add bounded fixtures for:

- one branch;
- two branches;
- twelve branches;
- small positive branch/end gaps;
- zero or negative branch/end gaps;
- mismatched wall/diameter domains;
- non-integer branch count;
- unknown parameters;
- deterministic repeated build.

Existing GeometrySpec fixtures and digests must remain unchanged unless the schema
version itself changes. This slice should preserve `bluecad_geometry_spec_v0_1`
and add the part kind additively; do not create a broad v1 schema migration merely
for one reviewed typed builder.

## API and persistence

No new API route, table, migration, candidate origin, artifact role, event type, or
persistence record is required.

The new primitive becomes available through existing GeometrySpec ingestion,
build, candidate, mesh, FEM, artifact, and evidence paths.

## Acceptance criteria

Implementation is acceptable only when all of the following hold:

1. `capped_manifold` is accepted by the closed GeometrySpec contract and all
   invalid domains fail before a kernel call.
2. The part exposes exactly one common port and exactly N ordered branch ports.
3. The capped end is physically closed and has no port.
4. Every branch bore is physically open through the header wall into the common
   cavity.
5. Reported volume matches the final boolean-result solid volume within the
   existing deterministic tolerance.
6. BREP validity and watertight/manifold checks pass for branch counts 1, 2, and 12.
7. Existing part kinds, fixtures, canonical IDs, assembly behavior, mesh adapter,
   FEM adapter, and real-tool proof do not regress.
8. Same-environment repeated builds produce identical canonical GeometrySpec,
   manifest, ports, analytic metadata, and artifact digests.
9. No provider call, AI job, process run, Parameter, CAD candidate, promotion,
   automatic repair, or UI action occurs merely by validating or building the
   primitive.
10. CI and the BLUECAD real-tool proof pass on the exact implementation head.

## Required tests

At minimum:

- unit tests for parameter closure and every domain rule;
- property tests over valid branch counts and dimensions;
- exact port order/frame tests;
- boolean fluid-opening probes;
- final-solid volume reconciliation;
- mirrored multi-path assembly fixtures for 1, 2, and 12 branches;
- canonicalization and repeated-build determinism;
- regression tests proving existing `manifold` behavior and existing fixtures are
  unchanged;
- Gmsh/CalculiX real-tool regression through the existing proof workflow.

## Non-goals

This spec does not add:

- CAD-LINK-1 or any 072 run/manifest consumer;
- a reactor layout, branch routing algorithm, bend handedness, optimizer, packing,
  collision-avoidance search, or inverse design;
- a general piping/component library;
- reducers, valves, pumps, reservoirs, tees, caps as standalone generic parts, or
  arbitrary port definitions;
- process flow direction, split fractions, pressure, flow, or hydraulic equations;
- material selection, fabrication thickness recommendations, code compliance,
  flange standards, welds, gaskets, fasteners, tolerances, or manufacturability
  claims;
- CFD, fluid-domain export, automatic meshing of the internal cavity, or pressure-
  drop validation;
- automatic candidate creation, promotion, recomputation, or UI.

## Downstream contract

After 073 is merged and proven, a separately numbered CAD-LINK-1 definition may
consume a fresh 072 topology manifest and create a deterministic multi-part BLUECAD
candidate. That future slice must still solve explicit planar layout, bend sequence,
illumination mapping, process/CAD reconciliation, idempotency, and stale lineage; it
must not infer those semantics merely because this primitive exists.
