# 074 — CAD-LINK-1: 072 M1 topology to deterministic multi-part BLUECAD

Status: ready for implementation after this definition is merged. `docs/specs/STATUS.md`
is authoritative.

Depends on: 038, 050, 051, 052, 071, 072, 073

## Goal

Convert one fresh successful 072 topology run into one deterministic, idempotent,
multi-part BLUECAD candidate **only** when the caller supplies a closed reviewed planar
layout contract.

The represented CAD boundary is deliberately narrower than the complete 072 process
loop. V0 represents:

- one split `capped_manifold`;
- one merge `capped_manifold`;
- one common-supply straight tube when its 072 length is positive;
- one common-return straight tube when its 072 length is positive;
- 1–12 identical planar branch routes made only from existing `tube_run` and `bend`
  primitives;
- exactly two open external common boundaries: supply inlet and return outlet.

V0 does **not** invent CAD for the pump, reservoir, supports, floats, anchors, valves,
joints, reducers, instrumentation, or any other component that 072 does not spatially
specify. Those exclusions are returned explicitly in preview and persisted as link
evidence. The candidate must never be described as a complete closed-loop reactor CAD
model.

After this slice, an operator can:

1. select a fresh successful exact bundled-072 run;
2. provide one explicit planar route/manifold layout with no hidden project defaults;
3. preview the exact GeometrySpec, source snapshot, transformation, boundary omissions,
   fluid/material reconciliation, route closure, and collision evidence with zero
   persistent writes;
4. execute the exact digest-bound preview through the existing deterministic BLUECAD
   build/validation and optional 038 analysis path;
5. inspect lineage from source Parameters and the canonical 072 topology manifest through
   the process-linked CAD candidate and its artifacts/evidence;
6. replace an accepted upstream geometry Parameter and observe the existing 050/051
   dependency chain become stale without automatic rerun, rebuild, or promotion.

## Why a separate reviewed layout contract is mandatory

### 072 topology is intentionally non-spatial

The 072 manifest defines multiplicity, component roles, centreline totals, diameters,
wall thicknesses, bend count/radius/angle, illumination classification, hydraulic bases,
and liquid-volume totals. It explicitly does not define:

- bend handedness or ordered turn sequence;
- allocation of aggregate illuminated/dark straight length among route segments;
- 3D coordinates or frames;
- manifold clearances, branch pitch, exposed stubs, or cap thickness;
- collision clearance or routing around hardware;
- pump/reservoir/support geometry.

CAD-LINK-1 must not infer any of these from plausibility, visual symmetry, a project
report, or a model-generated suggestion.

### 073 is a primitive, not a process/CAD transformation

The 073 `capped_manifold` provides one physically closed header, one common port, N open
branch bores, deterministic ports, and kernel material volume. It does not choose its
clearances or claim that its internal cavity equals the 072 split/merge liquid holdup.
074 must supply those dimensions explicitly and prove the cavity-volume match.

### Existing BLUECAD validation does not prove process equivalence

A schema-valid, watertight assembly may still have:

- the wrong branch count or route length;
- the wrong illuminated/dark allocation;
- the wrong manifold fluid volume;
- branches connected in the wrong order;
- colliding non-connected parts;
- extra CAD volume not present in the process model;
- omitted source lineage.

074 therefore performs deterministic process/CAD reconciliation before execution. JSON
validity and a passing BLUECAD validation report are necessary but not sufficient.

## Exact source authority

The source is mandatory and must satisfy all of the following:

- `simulation_runs.status = succeeded`;
- the run is fresh under existing 051 behavior;
- exactly one associated runner job exists and has `status = succeeded`;
- the model version and runner job match the current bundled 072 identity by all of:
  - `implementation_kind = calc_v0`;
  - version label `bluerev-process-topology-m1-v0.1.0`;
  - exact bundled script SHA-256;
  - exact bundled input-contract SHA-256;
- the run owns exactly one registered artifact with role
  `bluerev_topology_manifest`;
- the artifact is a regular immutable JSON artifact associated with that exact run and
  runner job;
- its raw bytes, artifact SHA-256, result diagnostic
  `topology_manifest_sha256`, schema, model identity, input digest, and executed-input
  payload all agree through the existing trusted 072 validation path;
- the manifest has `topology_kind = symmetric_parallel_closed_loop` and schema version
  `bluerev_process_topology_m1_v0_1`;
- no caller-supplied manifest body, path, artifact ID, digest override, or model label is
  accepted.

A successful label match without the exact script/contract hashes is insufficient.
A copied or cross-workspace manifest is insufficient. Preview fails before layout work
when source authority is not proven.

## Geometry-driving source Parameters

Canonical CAD lineage requires every 072 input that drives represented geometry or
manifold reconciliation to carry a non-empty `source_parameter_id` in the exact executed
input payload:

- `parallel_path_count`;
- `branch_illuminated_straight_length`;
- `branch_dark_straight_length`;
- `branch_bend_count`;
- `branch_illuminated_bend_count`;
- `branch_bend_centerline_radius`;
- `branch_bend_angle`;
- `common_supply_length`;
- `common_return_length`;
- `branch_tube_inner_diameter`;
- `branch_tube_outer_diameter`;
- `common_tube_inner_diameter`;
- `common_tube_outer_diameter`;
- `split_manifold_liquid_volume`;
- `merge_manifold_liquid_volume`.

Each referenced Parameter must:

- belong to the same workspace;
- exist, be `accepted`, and be fresh;
- still contain the exact executed value and unit;
- use one compatible source name/unit role; accidental reuse under incompatible input
  names fails closed.

Temporary/manual 071 values remain valid for scenario exploration but cannot create the
canonical 074 CAD link. Non-geometric hydraulic inputs and `reservoir_liquid_volume` are
recorded in the source manifest snapshot but need not be Parameter-backed for 074 because
they do not drive represented CAD.

## Closed spatial-layout contract

Layout schema version:

```text
bluerev_cad_layout_m1_v0_1
```

The exact request-owned object is:

```json
{
  "schema_version": "bluerev_cad_layout_m1_v0_1",
  "layout_kind": "planar_mirrored_parallel_headers",
  "plane": "xy",
  "boundary_policy": "open_common_supply_and_return",
  "split_manifold": {
    "branch_gap_mm": 0.0,
    "end_gap_mm": 0.0,
    "branch_stub_length_mm": 0.0,
    "cap_thickness_mm": 0.0
  },
  "merge_manifold": {
    "branch_gap_mm": 0.0,
    "end_gap_mm": 0.0,
    "branch_stub_length_mm": 0.0,
    "cap_thickness_mm": 0.0
  },
  "branch_route": {
    "steps": [
      {
        "kind": "straight",
        "length_mm": 0.0,
        "illumination": "illuminated"
      },
      {
        "kind": "bend",
        "turn": "left",
        "illumination": "dark"
      }
    ]
  }
}
```

The example numbers are placeholders only. Every dimensional value in an accepted
layout is finite and strictly positive.

The contract is closed at every object level. No optional field, arbitrary coordinate,
frame, part ID, port name, expression, unit string, material, pressure, process role,
project default, or caller-defined GeometrySpec fragment is accepted.

`layout_kind` authorizes exactly one template:

- the split manifold is the first GeometrySpec part and is anchored by the existing
  default frame at the origin in the XY plane;
- all branch routes leave the ordered split branch ports;
- the merge manifold is placed by the existing assembly engine from the first complete
  branch route and is checked against every remaining branch route;
- split branch `i` connects to merge branch `N + 1 - i`;
- common supply and common return are single straight runs normal to their corresponding
  common ports;
- no part leaves the XY plane;
- the supply and return outer endpoints remain intentionally unconnected boundaries.

The fixed coordinate convention is not a design default. It is a canonical origin and
plane for deterministic hashing. Every design-relevant clearance and route decision is
still explicit in the layout object.

## Layout validation and canonicalization

Use one strict decimal parser over request numbers and exact manifest values. Booleans,
NaN, Infinity, locale commas, embedded units, expressions, strings with trailing text,
and non-finite derived values fail closed.

### Manifold fields

For both split and merge:

- `branch_gap_mm > 0`;
- `end_gap_mm > 0`;
- `branch_stub_length_mm > 0`;
- `cap_thickness_mm > 0`.

`main_outer_d/main_wall_t`, `branch_outer_d/branch_wall_t`, and `branch_count` are never
caller fields. They are derived exactly from the trusted 072 manifest:

```text
main_outer_d_mm = common_outer_diameter_m * 1000
main_wall_t_mm = common_wall_thickness_m * 1000
branch_outer_d_mm = branch_outer_diameter_m * 1000
branch_wall_t_mm = branch_wall_thickness_m * 1000
branch_count = parallel_path_count
```

For `branch_count > 1`, split and merge `branch_gap_mm` must be exactly equal after
canonical decimal normalization so their branch pitch is identical. For one branch the
gaps may differ because no inter-port pitch exists.

### Branch-route steps

`steps` is non-empty and contains at most 129 entries, corresponding to the 072 maximum
of 64 bends plus at most 65 positive straight allocations.

A `straight` step has exactly:

- `kind = straight`;
- finite `length_mm > 0`;
- `illumination = illuminated | dark`.

A `bend` step has exactly:

- `kind = bend`;
- `turn = left | right`;
- `illumination = illuminated | dark`.

Bend radius, absolute angle, outer diameter, and wall thickness are not repeated in the
layout. Every bend uses the exact trusted 072 values:

```text
bend_radius_mm = branch_bend_centerline_radius_m * 1000
bend_angle_rad = radians(branch_bend_angle_deg)
```

The converter realizes `left` and `right` deterministically through the existing bend
port orientation: one traversal uses `port_a -> port_b`, the opposite traversal uses
`port_b -> port_a`. No signed-angle extension or second bend primitive is introduced.

Required aggregate checks:

- bend-step count equals `branch_bend_count`;
- illuminated bend-step count equals `branch_illuminated_bend_count`;
- dark bend-step count equals the manifest dark bend count;
- sum of illuminated straight-step lengths equals the exact executed
  `branch_illuminated_straight_length * 1000`;
- sum of dark straight-step lengths equals the exact executed
  `branch_dark_straight_length * 1000`;
- two adjacent straight steps with the same illumination are rejected as a non-canonical
  redundant decomposition;
- every resulting route length, illuminated length, and dark length equals the manifest
  values within the reconciliation tolerances below.

The layout contract allocates existing totals. It cannot change process geometry.

### Complexity bound

The resolved GeometrySpec must contain no more than 256 parts. This is a V0 execution
bound, not a design recommendation. It includes both manifolds, present common runs, and
all repeated branch-route parts.

A valid 072 run whose explicit layout exceeds the bound is not silently simplified. It
fails with `cad_link_layout_complexity_unsupported` and requires a future measured slice
or a different reviewed decomposition.

## Deterministic GeometrySpec transformation

Transformation version:

```text
bluerev_072_m1_planar_tubing_v0_1
```

Implementation version:

```text
cad_link_072_v0_1
```

The resolved GeometrySpec uses:

```text
spec_version = bluecad_geometry_spec_v0_1
name = bluerev_072_m1_planar_tubing
```

No caller-controlled name, part ID, port, frame, connection, or `declared` block exists.

### Deterministic part IDs and order

Part order is exact:

1. `split_manifold`;
2. `common_supply` when source supply length is positive;
3. branch routes in increasing branch index, with route steps in increasing step index;
4. `merge_manifold`;
5. `common_return` when source return length is positive.

Branch step IDs are:

```text
branch_<i>_step_<j>
```

where both indices are one-based decimal integers without padding.

### Split and merge manifolds

Both are `capped_manifold` parts. Common and branch tube dimensions and branch count come
only from the manifest. Layout-owned gap/end/stub/cap dimensions map exactly to the 073
parameter names.

The two manifolds may have different `end_gap`, `branch_stub_length`, and
`cap_thickness`. Their pitch constraint remains as defined above.

### Common runs

When `common_supply_length_m > 0`, create one `tube_run` with common outer diameter,
common wall thickness, and exact length in millimetres. Connect its outer-facing
`port_b` to `split_manifold.common`, leaving `port_a` as the supply boundary.

When `common_return_length_m > 0`, create one equivalent common `tube_run` connected to
`merge_manifold.common`, leaving its outer `port_a` as the return boundary.

When either source length is exactly zero, omit the zero-length part and use the
corresponding manifold `common` port as that external boundary. GeometrySpec never
contains a zero-length tube.

### Repeated branch routes

Generate one independent copy of the canonical step list for each branch. Straight steps
become `tube_run` parts. Bend steps become existing `bend` parts using source-derived
radius, angle in radians, diameter, and wall thickness.

The connection sequence and selected bend entry/exit ports encode each explicit turn.
Every branch uses the same step list and is translated by manifold port placement only.
No per-branch asymmetry, flow split, length adjustment, or auto-routing occurs.

The last endpoint of branch `i` connects to merge branch `N + 1 - i`. All connection
paths must place one and the same merge manifold frame. A conflicting placement is a
layout failure, not a reason to move, stretch, trim, or reorder parts.

## Exact external-boundary semantics

The finished GeometrySpec must have exactly two intentionally unconnected tube ports:

- `common_supply_boundary`;
- `common_return_boundary`.

These are semantic names in preview/reconciliation evidence, not new GeometrySpec port
aliases. They resolve to the outer common-run port when that run exists, otherwise to the
corresponding manifold common port.

Every manifold branch port and every internal route/common port is connected exactly
once. No capped-end port exists. No hidden connection closes the supply/return boundary.

Preview and candidate notes state explicitly:

```text
represented: common tubing, split/merge manifolds, repeated branch tubing
not represented: pump, reservoir vessel, supports, floats, anchors, instrumentation
CAD boundary: open supply inlet and open return outlet
```

## Side-effect-free kernel preflight

Unlike 052, 074 needs bounded kernel evidence before execution because route closure,
manifold fluid volume, and collisions cannot be established from JSON shape alone.

Preview may invoke build123d only in one isolated bounded worker that:

- performs no database write;
- creates no candidate, attempt, event, artifact, evidence, or `ai_jobs` row;
- writes no persistent or data-root file;
- receives only the canonical resolved GeometrySpec and bounded reconciliation inputs;
- terminates within 30 seconds;
- returns only finite bounded JSON evidence;
- is killed and fails closed on timeout, crash, missing native dependency, or malformed
  response.

No fallback geometry, reduced candidate, or skipped collision proof is permitted.

The preflight must:

1. canonicalize and assemble the exact GeometrySpec through existing builders and
   placement logic;
2. prove every declared connection is dimensionally conformant, coincident, and opposed;
3. prove all multi-path placement constraints resolve to one merge-manifold placement;
4. prove every part BREP is valid and manifold/watertight under existing kernel checks;
5. identify exactly the two intended unconnected boundary ports and no other open
   assembly interface;
6. compute split and merge fluid-cavity volumes from the same 073 void construction used
   to subtract the solid;
7. reject positive-volume material interference between non-identical parts after an
   axis-aligned bounding-box broad phase;
8. allow only zero-volume face/edge contact at declared connections;
9. return placed part frames, represented bounds, kernel cavity/material metrics, and
   collision-pair diagnostics.

The absolute positive-interference tolerance is `1e-6 mm3`. A larger intersection fails.
This tolerance is a numerical classification threshold, not a fabrication clearance.
No minimum physical clearance or manufacturability claim is added.

To prevent geometry drift, 074 may make the smallest extraction in
`capped_manifold.py` that exposes the already-constructed outer and void shapes to the
073 builder and the 074 preflight. It must not duplicate the capped-manifold equations in
a second module or change the 073 public GeometrySpec contract.

## Process/CAD reconciliation

All checks are returned individually with source value, CAD value, unit, absolute error,
relative error, tolerance, and pass/fail status. Any required failure blocks execution.

Use:

```text
dimension absolute tolerance = 1e-9 mm
dimension relative tolerance = 1e-12
length/area/volume relative tolerance = 1e-9
length absolute tolerance = 1e-9 mm
area absolute tolerance = 1e-12 m2
volume absolute tolerance = 1e-12 m3
```

A comparison passes when either the absolute or relative criterion passes, matching the
recorded check contract. Tolerances are fixed implementation constants and enter the
preview digest.

### Topology and dimensions

Reconcile at least:

- source and CAD branch count;
- branch/common inner diameter, outer diameter, and wall thickness;
- split/merge branch pitch and ordered branch-port count;
- each common-run centreline length;
- each branch bend count, radius, absolute angle, turn sequence, and illumination label;
- each branch straight allocation;
- branch route total, illuminated, and dark centreline lengths;
- installed branch and installed total tube centreline lengths;
- representative hydraulic path length.

### Tube liquid volume and external area

Using the resolved `tube_run` and `bend` parts, reconcile:

- branch liquid volume each and total;
- common supply and return liquid volumes;
- represented tube liquid volume total;
- illuminated branch external area;
- dark branch external area;
- common external area;
- total tube external area;
- 072 `tube_material_volume_proxy` against the annular material volume of tube and bend
  parts only.

Manifold solid material is not included in the 072 tube-material proxy and must not be
added to that comparison.

### Split and merge fluid-cavity volume

For each capped manifold, use the exact unioned 073 void shape:

- header inner cylinder from common opening to inner cap face;
- all branch inner bores from header centreline to branch ports;
- overlap counted once by the kernel union.

Convert its kernel volume from mm3 to m3 and require exact tolerance agreement with the
corresponding executed 072 input:

- split cavity ↔ `split_manifold_liquid_volume`;
- merge cavity ↔ `merge_manifold_liquid_volume`.

A zero or otherwise unrepresentable source manifold volume fails honestly with
`cad_link_manifold_volume_unrepresentable`. 074 does not solve for gap/stub dimensions or
silently change process holdup.

### Represented and excluded inventory

Report:

```text
represented_fluid_volume = branch tubes + common tubes + split cavity + merge cavity
expected_represented_fluid_volume = total_liquid_inventory - reservoir_liquid_volume
excluded_fluid_volume = reservoir_liquid_volume
```

The represented and expected represented values must reconcile. Reservoir holdup remains
process-only and is listed as excluded. The candidate must not claim that its open
supply/return endpoints or any invented solid contain the reservoir volume.

### CAD-only metrics

Report, but do not compare to nonexistent 072 process authority:

- split and merge manifold material volume;
- complete CAD assembly material volume;
- assembly bounding box;
- manifold external surface area when readily available;
- collision/interference evidence.

These values are CAD evidence, not new process outputs or accepted Parameters.

## API surface

Add two endpoints following the existing 052 pattern:

```text
POST /workspaces/{workspace_id}/bluecad/cad-link/072/preview
POST /workspaces/{workspace_id}/bluecad/cad-link/072/execute
```

### Preview request

```json
{
  "source_simulation_run_id": "<required-run-id>",
  "layout_spec": {},
  "analysis_spec": null
}
```

`layout_spec` is required and must match the closed contract above. `analysis_spec` is
optional and reuses the existing 038 contract without geometry authority. No other field
is accepted.

### Preview response

Preview returns at least:

- workspace, source simulation-run, and source runner-job IDs;
- exact source model identity and hashes;
- source topology-manifest artifact ID, role, byte size, raw SHA-256, schema version,
  result diagnostic digest, and input digest;
- canonical source geometry-Parameter snapshot with executed/current values, units,
  status, origin, source refs, and freshness;
- canonical layout spec and layout digest;
- transformation and implementation versions;
- exact resolved GeometrySpec and `spec_id`;
- resolved part/connection counts;
- semantic external-boundary mapping;
- represented/excluded component inventory;
- kernel preflight evidence;
- full reconciliation checks and digest;
- canonical analysis-contract digest when supplied;
- one `preview_digest` over every execution-relevant field and fixed tolerance/version.

Preview has zero persistent database/filesystem/artifact/event/candidate/attempt/evidence/
freshness/link/AI writes.

## Execute and TOCTOU boundary

Execute receives the same source run, layout spec, optional analysis spec, and exact
`preview_digest`.

Before any database write or candidate-directory creation, execute must reload and
revalidate:

- workspace, source run, run freshness, and exact runner job;
- bundled 072 script/contract/model identity;
- exact topology-manifest artifact identity, bytes, schema, digests, and run association;
- source executed inputs and every geometry-Parameter snapshot;
- layout schema and canonical digest;
- transformation/implementation/tolerance versions;
- resolved GeometrySpec, boundary mapping, preflight evidence, and reconciliation;
- analysis contract and digest.

Any mismatch returns `409 cad_link_preview_stale` with zero writes and zero directory
creation. Kernel preflight is rerun from current source/layout state; stored preview
output is not trusted as execution authority.

## Idempotency and concurrency

The canonical `preview_digest` is the execution identity.

Reuse the existing `bluecad_cad_links` lifecycle and uniqueness boundary. No second link
table or alternate candidate store is added.

- the first execute owns candidate creation for `(workspace_id, preview_digest)`;
- a repeated or concurrent execute returns the existing linked candidate with
  `replayed=true` after verifying stored digests;
- source manifest artifact identity/digest and canonical layout snapshot are included in
  the existing source snapshot/reconciliation payloads;
- no duplicate candidate, attempt, artifact, evidence, simulation, link, or AI row is
  created;
- inconsistent stored state fails with `cad_link_persistence_inconsistent`.

No database migration is expected. If current runtime inspection proves one additive
column is strictly required for integrity rather than convenience, implementation must
stop and report the conflict instead of silently expanding persistence scope.

## Candidate, attempt, artifacts, and optional analysis

Reuse the 052 process-linked semantics:

- `origin = process_linked`;
- `parent_candidate_id = NULL`;
- no `proposal_ai_job_id`;
- `loop_config_json = {}` as not-applicable legacy storage;
- deterministic brief identifying the 072 planar tubing/manifold representation and
  source run without embedding source values;
- `route_class = deterministic:cad_link:072`;
- `proposal_outcome = not_applicable`;
- honest producer notes that never claim AI generation.

A first successful execute creates exactly one candidate and one deterministic attempt,
then reuses:

- GeometrySpec canonicalization;
- `build_geometry_spec` construction/export;
- artifact hashing and registration;
- validation evidence mapping;
- optional 038 Gmsh/CalculiX analysis through the existing advisory path.

A build/validation failure after candidate creation leaves an inspectable
`parked(cad_link_failed)` candidate with link provenance and available reports. Source,
layout, preflight, or reconciliation failure creates no candidate.

No result, candidate, analysis, decision, Parameter, or record is promoted automatically.

## Flowsheet and stale propagation

Extend the existing 050 graph builder only where needed:

- source 072 `simulation_run:<id>` → child `bluecad_candidate:<id>` as
  `m1_topology_geometry_link`, edge class `dependency`;
- preserve existing source run → topology-manifest artifact lineage;
- process-linked candidate → deterministic attempt as `process_link_build`;
- candidate → current registered candidate artifacts as `process_link_artifact`;
- preserve existing attempt/artifact/simulation/evidence paths.

Do not add a topology node kind, layout node kind, second graph engine, or mutable layout
record. The immutable canonical layout snapshot remains link evidence.

Replacing any accepted geometry-driving source Parameter must allow 051 to mark stale
through:

```text
parameter -> source 072 simulation_run -> process-linked candidate
          -> deterministic attempt/artifact/optional analysis run/evidence
```

A new layout request produces a new digest/link. It does not mutate or overwrite
historical candidates and is not treated as a Parameter change.

## Authority and safety invariants

1. Process geometry and multiplicity come only from the exact fresh 072 run/manifest.
2. Layout-only clearances and turn/allocation decisions come only from the explicit closed
   layout request.
3. No model, heuristic, optimizer, report text, or project default fills a missing value.
4. Preview is persistently side-effect free and kernel work is isolated and bounded.
5. Execute is bound to one exact preview digest and rechecks all authority before writes.
6. Route closure and collision failures block execution; parts are never stretched,
   trimmed, moved, deleted, or reordered to make the layout fit.
7. Manifold process holdup must match the exact 073 fluid cavity; no inverse solve occurs.
8. Pump/reservoir/support CAD is explicitly excluded and never represented by proxy
   geometry.
9. The two open common boundaries are explicit and never described as a closed CAD loop.
10. Zero provider calls and zero `ai_jobs` rows are produced.
11. Existing BLUECAD validation/build/export and optional FEM remain deterministic or
    advisory; none owns process truth or promotion.
12. No failed, timed-out, stale, collision-invalid, or unreconciled layout is represented
    as successful.
13. Historical candidates/artifacts remain immutable inspectable evidence.

## Error contract

Reuse applicable 052 codes and add bounded 072/layout-specific codes including at least:

- `cad_link_run_not_found`;
- `cad_link_run_not_succeeded`;
- `cad_link_run_stale`;
- `cad_link_runner_job_invalid`;
- `cad_link_model_identity_mismatch`;
- `cad_link_topology_manifest_missing`;
- `cad_link_topology_manifest_invalid`;
- `cad_link_topology_manifest_digest_mismatch`;
- `cad_link_topology_manifest_identity_mismatch`;
- `cad_link_parameter_binding_missing`;
- `cad_link_parameter_not_found`;
- `cad_link_parameter_not_accepted`;
- `cad_link_parameter_stale`;
- `cad_link_parameter_snapshot_mismatch`;
- `cad_link_layout_schema_invalid`;
- `cad_link_layout_mismatch`;
- `cad_link_layout_complexity_unsupported`;
- `cad_link_layout_not_closable`;
- `cad_link_layout_collision`;
- `cad_link_kernel_unavailable`;
- `cad_link_kernel_timeout`;
- `cad_link_manifold_volume_unrepresentable`;
- `cad_link_geometry_invalid`;
- `cad_link_reconciliation_failed`;
- `cad_link_preview_stale`;
- `cad_link_persistence_inconsistent`;
- `cad_link_persistence_failed`.

Expected response classes:

- `404` for absent workspace-scoped source resources;
- `409` for stale/changed run, artifact, Parameter, preview, or inconsistent replay;
- `422` for ineligible source identity, invalid layout/domain, non-closing route,
  collision, unrepresentable manifold volume, or reconciliation failure;
- `503` for missing required kernel/native dependency;
- `504` for bounded kernel preflight timeout;
- `500` for unexpected infrastructure failure with no internal paths, SQL, source values,
  secrets, or unbounded exception text.

## Files likely touched

Verify against current code before implementation and stop on conflict.

Expected bounded set:

- `schemas/bluerev_cad_layout_m1_v0_1.schema.json` (new);
- `backend/app/modules/bluecad/cad_link.py` for shared 052 lifecycle reuse, or one small
  sibling `cad_link_topology_m1.py` if keeping source-specific transformation logic
  separate is materially clearer;
- `backend/app/modules/bluecad/capped_manifold.py` only for the smallest shared outer/void
  shape extraction;
- `backend/app/modules/bluecad/models.py` and `routes.py` for the closed API types/routes;
- `backend/app/modules/flowsheet/service.py` only for the new dependency-edge label;
- focused 074 tests and existing 052/072/073 regression tests;
- `docs/specs/STATUS.md`.

No frontend, provider, AI-routing, runner-script, 072 manifest-schema, GeometrySpec-schema,
or migration file is expected.

## Acceptance criteria

1. Preview accepts only one fresh successful exact bundled-072 run with one exact trusted
   topology-manifest artifact and accepted fresh geometry-driving Parameters.
2. Wrong model/hash, malformed/copied/mismatched manifest, temporary geometry binding,
   stale run/Parameter, or changed source snapshot fails with zero writes.
3. The layout contract is closed, finite, unit-unambiguous, default-free, and explicitly
   supplies every manifold clearance and branch turn/straight-allocation decision.
4. The resolved GeometrySpec contains exactly two capped manifolds, N identical route
   copies, only the positive-length common runs, deterministic IDs/order/connections, and
   no caller-owned spec fragment.
5. Every 072 aggregate straight/bend/illumination quantity reconciles with the explicit
   branch route; no length or bend is invented, dropped, or redistributed silently.
6. All N branches close on one mirrored merge placement and expose no unconnected internal
   ports.
7. Exactly two external common boundaries remain and pump/reservoir/support exclusions are
   explicit in preview, candidate notes, and link evidence.
8. Split and merge kernel fluid-cavity volumes match the two 072 manifold-volume inputs;
   unrepresentable values block execution.
9. Tube lengths, liquid volumes, external areas, and tube material volume reconcile with
   072 within fixed recorded tolerances.
10. Represented fluid volume equals total 072 inventory minus explicit reservoir volume;
    reservoir volume is never placed into proxy CAD.
11. Side-effect-free bounded preflight proves BREP validity, connection conformity,
    route closure, exact boundaries, and no positive-volume non-connected collision.
12. Preview returns one digest over source run/model/manifest/Parameters, layout,
    transformation, spec, preflight, reconciliation, analysis contract, and tolerances.
13. Execute rechecks the exact preview before writes; TOCTOU changes fail with zero writes.
14. First execute creates one process-linked non-AI candidate/attempt/link and honest
    artifacts; repeated/concurrent execute is idempotent.
15. Optional mesh/FEM reuses 038 and cannot rewrite process inputs/outputs or promote a
    result.
16. Replacing one source geometry Parameter stales the dependency-reachable linked CAD and
    downstream evidence through existing 050/051 behavior.
17. Existing 052 M0 CAD link, 072 manifest validation, 073 primitive, AI loop, mesh/FEM,
    and real-tool proof do not regress.
18. Full backend CI, Ruff, the BLUECAD geometry canary, and the real-tool proof pass on the
    exact implementation head.

## Required tests

Offline tests must cover at least:

### Source authority

- succeeded/fresh exact 072 run and exact one-manifest artifact;
- absent, queued, running, failed, timed-out, or stale run;
- zero, duplicate, cross-workspace, wrong-role, non-regular, malformed, non-canonical,
  schema-invalid, identity-mismatched, input-mismatched, or digest-mismatched manifest;
- wrong model label, implementation kind, script hash, contract hash, or runner-job hash;
- missing, temporary, stale, non-accepted, cross-workspace, changed, or incompatible reused
  geometry Parameters.

### Layout contract

- schema closure and canonical digest;
- non-finite/boolean/string numeric rejection;
- positive manifold dimensions;
- branch-pitch equality for multi-branch layouts;
- exact bend count, handedness enumeration, and illumination count;
- exact illuminated/dark straight allocation;
- redundant adjacent same-illumination straight rejection;
- 129-step and 256-resolved-part bounds;
- unknown field, coordinate, frame, part, port, unit, formula, and default rejection.

### Transformation and assembly

- exact deterministic part IDs/order/connections;
- zero common-length omission and boundary remapping;
- N = 1, 2, and 12 route fixtures;
- zero-bend straight route;
- multi-bend left/right route;
- mirrored branch mapping `i -> N + 1 - i`;
- conflicting endpoint displacement/orientation rejection;
- all internal ports connected once and exactly two external boundaries;
- no mutation of source manifest or caller layout.

### Kernel and reconciliation

- split/merge fluid-cavity volume pass/fail against source holdup;
- branch/common tube length, volume, area, and material reconciliation;
- represented inventory equals total minus reservoir;
- valid BREP/manifold results;
- non-connected collision, self-intersection, manifold collision, and common-run collision
  rejection;
- bounded worker timeout, crash, malformed response, and missing build123d/native dependency;
- no persistent preview writes or directory creation.

### Execution, evidence, and regression

- preview/execute TOCTOU rejection for run, artifact, Parameter, layout, analysis, and fixed
  version changes;
- successful candidate/attempt/link/artifact/evidence creation with zero `ai_jobs`;
- idempotent replay and concurrent execute race;
- coherent persistence/build/validation failure behavior;
- same-environment identical preview/spec/manifest/artifact digests;
- 050/051 source-to-linked-candidate stale paths;
- unchanged 052, 072, 073, AI-loop, Gmsh, CalculiX, and canonical digest canaries.

No test may require network access, provider credentials, a live model, frontend runtime,
or a project-specific design value.

## Explicit non-goals

074 does not add:

- an automatic route planner, packing algorithm, collision-avoidance search, optimizer,
  inverse solver, or length-fitting algorithm;
- arbitrary 3D coordinates, out-of-plane bends, asymmetric branches, different per-branch
  lengths, nested splits, cross-connections, bypasses, or valve states;
- pump, reservoir, float, support, anchor, instrumentation, valve, reducer, flange, weld,
  gasket, or joint geometry;
- a complete closed-loop CAD claim;
- derivation of manifold dimensions from process holdup;
- implicit fabrication clearance, material, wall recommendation, code compliance,
  manufacturability, structural, buoyancy, optical, hydraulic, or CFD validation;
- changes to 072 equations, topology manifest, runner permissions, or model outputs;
- a second GeometrySpec, CAD builder, assembly engine, artifact store, link table,
  flowsheet engine, or evidence path;
- provider/LLM calls, automatic candidate creation, automatic repair, recompute,
  promotion, decision, or record write;
- frontend or workspace-home work.

## Implementation slices

Implementation remains one spec but should be reviewed in this order:

1. closed layout schema/canonicalizer and exact 072 source/manifest/Parameter authority;
2. pure deterministic manifest + layout → GeometrySpec transformation and fixtures;
3. bounded kernel preflight, shared 073 void extraction, collision and route-closure proof;
4. process/CAD reconciliation and preview digest;
5. execute/idempotency through the existing 052 link lifecycle and shared BLUECAD build;
6. 050/051 lineage/staleness and optional 038 regression;
7. adversarial failure matrix, exact-head CI, geometry canary, and real-tool proof.

Do not start UI, pump/reservoir primitives, a generic routing solver, or a broad CAD-link
framework inside this spec.
