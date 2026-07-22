# 074 — CAD-LINK-1: 072 M1 topology to deterministic multi-part BLUECAD

## Status

Definition complete. Implementation may start only after this definition and the
registry promotion are merged and the `074` row is `ready`.

`docs/specs/STATUS.md` is authoritative.

## Problem

Spec 072 now produces one explicit, bounded, symmetric process topology with:

- one common supply section;
- one split manifold;
- 1–12 identical branch paths;
- one merge manifold;
- one common return section;
- explicit tube dimensions, centreline lengths, bend count/radius/angle, liquid
  inventory, illuminated/dark classification, and topology multiplicity;
- a canonical `bluerev_process_topology_m1_v0_1` manifest.

Spec 073 now provides the missing physically honest `capped_manifold` primitive with
one common port, N fluid-open branch ports, and one closed far end.

Neither result authorizes a spatial CAD layout. The 072 manifest intentionally has no
coordinates, branch routing, bend handedness, manifold clearances, branch-port mapping,
anchor frame, collision decision, or project default. A converter that infers any of
those values would turn a process model into an undocumented design decision.

The existing CAD-LINK-0 service is also too narrow. It maps one fresh bundled-047 run
to one `tube_run`; it does not consume topology artifacts, expand repeated branches,
validate a multi-path assembly, preserve illuminated/dark component mapping, or
reconcile manifold liquid volume.

## Goal

Add one deterministic backend-only CAD-LINK-1 slice that converts:

1. one fresh, successful, exact bundled-072 simulation run and canonical topology
   manifest; and
2. one explicit, closed, operator-reviewed planar layout contract

into one digest-bound, idempotent, multi-part BLUECAD candidate.

The result must:

- use the existing GeometrySpec, `tube_run`, `bend`, and `capped_manifold` builders;
- use the existing assembly engine, candidate/attempt ledger, build/export,
  validation, evidence, optional 038 analysis, flowsheet lineage, and stale
  propagation boundaries;
- preserve source/model/artifact/Parameter/layout provenance;
- reconcile process geometry, multiplicity, tube liquid volume, manifold liquid
  volume, illuminated/dark tube area, tube material volume, ports, and component
  lineage;
- fail closed rather than infer bend handedness, branch-to-merge mapping, manifold
  dimensions, routing, or design defaults;
- create no AI job and perform no provider call.

This is a fixed-template topology-to-CAD transformation, not a generic network or
layout engine.

## Dependencies

Hard dependencies:

- `038` — optional advisory mesh/FEM stage already owned by the BLUECAD loop;
- `050` — inspectable dependency graph and canonical reference resolver;
- `051` — deterministic stale propagation;
- `052` — digest-bound, idempotent, non-AI CAD-link transaction and lineage pattern;
- `071` — scenario binding and forward-run authority;
- `072` — exact bundled process-topology model and canonical topology manifest;
- `073` — fluid-open capped split/merge manifold primitive.

No UI, Hermes, provider, optimizer, or runner-hardening dependency is introduced.

## Authority order

When data disagree, implementation must apply this authority order:

1. current accepted Parameters and current freshness state;
2. the exact executed 072 input payload and exact successful runner job;
3. the canonical validated 072 topology manifest artifact;
4. the explicit CAD layout contract supplied to CAD-LINK-1;
5. derived GeometrySpec and reconciliation evidence.

The layout contract owns spatial choices only. It cannot override process values from
072, change topology multiplicity, change tube diameters/lengths/bend geometry, alter
illumination totals, lower sensitivity, promote records, or mark stale data fresh.

## Source-run gate

Preview and execute accept only one source simulation run satisfying every condition
below.

### Exact identity

The source must be:

- in the requested workspace;
- `succeeded`;
- fresh under existing 050/051 authority;
- backed by exactly one succeeded runner job;
- the exact current bundled 072 implementation identity, including:
  - version label;
  - `calc_v0` implementation kind;
  - bundled script hash;
  - bundled input-contract hash;
  - runner-job script hash;
- accompanied by exactly one runner-owned topology manifest artifact with the expected
  role and media type.

A compatible-looking custom script, copied JSON result, old model version, manually
uploaded manifest, failed/partial run, or multiple runner-job ambiguity is rejected.

### Canonical manifest

The source artifact must:

- be contained inside the workspace data root through existing safe-path rules;
- parse as one JSON object;
- validate against `bluerev_process_topology_m1_v0_1.schema.json`;
- have the exact manifest schema/version identity;
- bind to the source simulation-run ID and runner-job ID;
- bind to the exact executed-input payload and raw result digest recorded by 072;
- match the canonical bytes/digest expected from the validated object;
- contain the exact fixed topology profile:
  common supply → split → N identical branches → merge → common return;
- contain no extra component, alternate path, bypass, valve state, nested split,
  cross-connection, second loop, or second pump.

A valid JSON document is not sufficient evidence. All identity and digest links must
match.

### Parameter-backed CAD-driving inputs

Every source input that drives persistent CAD geometry must carry a
`source_parameter_id` and must still match one accepted, fresh Parameter in the same
workspace by exact value and unit.

Required CAD-driving source inputs are:

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

Operating properties and loss coefficients remain source-run evidence but do not become
CAD dimensions. Manual or temporary scenario values may be used for 072 exploration;
they may not create a persistent CAD-LINK-1 candidate when any CAD-driving source lacks
accepted Parameter authority.

## API

Add two routes beside the existing 047 CAD-link routes:

```text
POST /workspaces/{workspace_id}/bluecad/cad-link/072/preview
POST /workspaces/{workspace_id}/bluecad/cad-link/072/execute
```

Both request models are strict and closed to unknown fields.

Preview request:

```json
{
  "source_simulation_run_id": "...",
  "layout_contract": {},
  "analysis_spec": null
}
```

Execute request adds:

```json
{
  "preview_digest": "sha256:..."
}
```

`analysis_spec` retains the existing 038/BLUECAD-loop validation and authority. It is
included in the preview digest. It cannot change the generated GeometrySpec.

## Explicit layout contract

The exact V0 layout object is:

```json
{
  "layout_version": "bluerev_cad_layout_m1_v0_1",
  "units": "mm",
  "plane": "xy",
  "anchor": {
    "split_common_origin_mm": [0.0, 0.0, 0.0],
    "split_header_direction_xy": [1.0, 0.0]
  },
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
  "bend_traversal": [],
  "illuminated_bend_indices": [],
  "merge_branch_order": []
}
```

No field is optional and no field has a registration, runtime, project, or model
default.

### Closed validation

Validation occurs before kernel execution or persistence.

Required rules:

- `layout_version`, `units`, and `plane` equal the exact constants above;
- all objects are closed to unknown fields;
- all numbers are finite and booleans are rejected;
- the anchor origin contains exactly three finite numbers and its z value is exactly
  zero;
- `split_header_direction_xy` contains exactly two finite numbers, has unit norm within
  the existing deterministic tolerance, and is not the zero vector;
- every manifold dimension is strictly positive;
- `bend_traversal` has exactly `branch_bend_count` entries;
- every traversal entry is exactly `a_to_b` or `b_to_a`;
- `illuminated_bend_indices` contains exactly
  `branch_illuminated_bend_count` unique one-based indices in
  `[1, branch_bend_count]`;
- when bend count is zero, both bend arrays are empty;
- `merge_branch_order` has exactly N entries and is a permutation of one-based branch
  indices `1..N`;
- no process value, tube diameter, source length, bend radius/angle, flow, pressure,
  material, support, collision clearance, or fabrication recommendation may appear in
  the layout contract.

The operator chooses every spatial field. The service validates; it does not repair,
complete, reorder, mirror, optimize, or infer the layout.

### Anchor semantics

The split manifold is the first GeometrySpec part.

- `split_common_origin_mm` is the placed origin of its `common` port;
- `split_header_direction_xy` is the placed local +x header-axis direction;
- the `common` port therefore points opposite the header-axis direction, consistent
  with the 073 primitive;
- all generated parts remain in the XY plane with z = 0;
- no out-of-plane frame, arbitrary 3D rotation, roll, pitch, or elevation is supported
  in V0.

This matches the current BLUECAD assembly engine, which owns translation and rotation
about z only. The service must not claim general 3D placement.

### Bend handedness

072 defines bend count, common radius, common included angle, and illuminated bend
count. It does not define left/right turns.

For bend `j` in the ordered bend group:

- `a_to_b` connects the preceding element to `bend_j.port_a` and the following element
  to `bend_j.port_b`;
- `b_to_a` reverses those endpoint roles and is the explicit opposite-turn choice;
- the bend parameter `angle` remains the positive 072 angle converted from degrees to
  radians;
- negative angles, `2π-angle` substitutions, reflection transforms, or inferred
  handedness are forbidden.

### Illumination mapping

`illuminated_bend_indices` explicitly selects which bends contribute to the illuminated
area. Count equality with the 072 manifest is mandatory.

The array changes metadata/reconciliation mapping, not bend geometry. The converter
must not assume that the first N bends are illuminated.

### Branch mapping

For split branch `i`, `merge_branch_order[i-1]` names the merge-manifold branch port to
which the replicated route connects.

The array must be an explicit permutation. Identity, reverse, or another permutation
may be supplied, but none is inferred. All N replicated paths use the same ordered
route geometry; only their split and merge port identities differ.

The existing assembly consistency checks are authoritative. If one rigid merge
placement cannot satisfy every path, preview fails closed with no writes.

## Deterministic transformation

Use one versioned transformation and implementation identity, for example:

```text
transformation_version: bluerev_072_m1_cad_layout_v0_1
implementation_version: cad_link_072_v0_1
```

The exact names are frozen by implementation tests.

### Derived dimensions

All source units are converted deterministically:

- metres to millimetres by exact decimal multiplication by 1000;
- degrees to radians using the existing numeric convention;
- branch wall thickness = `(branch_outer_d - branch_inner_d) / 2`;
- common wall thickness = `(common_outer_d - common_inner_d) / 2`.

No rounding to commercial sizes occurs.

### Generated parts

The resolved GeometrySpec contains only existing trusted kinds.

Required deterministic identities:

- `split_manifold` — one `capped_manifold`;
- `merge_manifold` — one `capped_manifold`;
- `common_supply` — one `tube_run` only when source supply length is positive;
- `common_return` — one `tube_run` only when source return length is positive;
- for each branch `01..N`:
  - one illuminated straight `tube_run` only when illuminated straight length is
    positive;
  - exactly `branch_bend_count` `bend` parts, ordered `01..M`;
  - one dark straight `tube_run` only when dark straight length is positive.

Part IDs are stable, zero-padded, role-bearing identifiers. Repeated transformations of
the same source/layout produce byte-identical part order, IDs, parameters, connections,
and GeometrySpec digest.

### Manifold parameters

For both split and merge manifolds:

- `branch_count` comes from 072 N;
- `main_outer_d/main_wall_t` come from common tube dimensions;
- `branch_outer_d/branch_wall_t` come from branch tube dimensions;
- `branch_gap`, `end_gap`, `branch_stub_length`, and `cap_thickness` come only from the
  corresponding layout object;
- no split/merge process role is stored in the primitive.

The two manifolds may have different explicit layout dimensions.

### Branch template order

Each branch expands the exact 072 order:

```text
split branch port
  -> illuminated straight, when length > 0
  -> bend_01 ... bend_M using explicit traversal
  -> dark straight, when length > 0
  -> explicitly mapped merge branch port
```

No additional straight spacer, joint, reducer, valve, support, or hidden component is
inserted. Zero-length straight contributions are omitted rather than represented by an
invalid zero-length `tube_run`.

### Common boundaries

A positive common supply length produces a tube connected to the split common port. Its
other port is the declared pump-discharge boundary.

A positive common return length produces a tube connected to the merge common port. Its
other port is the declared reservoir/pump-suction boundary.

When either source length is exactly zero, that tube is omitted and the corresponding
manifold common port is the boundary. The service reports the exact boundary endpoint in
coverage metadata.

Pump, reservoir, suction hardware, valves, supports, floats, and harvest hardware are
not generated and are not represented as zero-valued parts.

## Side-effect-free preview

Preview executes under a read-only database transaction and creates no:

- candidate;
- attempt;
- CAD-link row;
- artifact;
- evidence record;
- simulation run;
- AI job;
- event;
- directory or file.

Preview must:

1. resolve and validate the source run, runner job, model identity, manifest artifact,
   Parameter snapshots, and freshness;
2. canonicalize and validate the layout contract;
3. construct and canonicalize the resolved GeometrySpec;
4. run the existing in-memory assembly placement/conformance check, including all N
   paths and the single rigid merge placement;
5. calculate reconciliation and coverage evidence;
6. return a canonical digest-bound preview.

Missing CAD kernel/native dependencies fail honestly; they do not downgrade assembly
proof to schema-only success.

## Preview digest

The digest covers at least:

- implementation and transformation versions;
- workspace ID;
- source simulation-run and runner-job IDs/statuses;
- source input/output payload digests;
- source manifest artifact ID, safe stored-path identity, media type, byte digest,
  canonical digest, schema version, and source binding digests;
- exact bundled model/script/contract identity;
- accepted Parameter snapshot and digest;
- layout contract and layout digest;
- analysis-contract digest, when present;
- resolved GeometrySpec and `spec_id`;
- deterministic component map;
- reconciliation and reconciliation digest;
- coverage/exclusion record and digest.

Any source, Parameter, manifest, layout, analysis, implementation, or resolved-CAD change
changes the preview digest.

## Reconciliation

Reconciliation is unit-bearing and split into claims the source can and cannot support.
A single aggregate `passed=true` without individual checks is forbidden.

### Exact topology and component checks

At minimum:

- exactly one split and one merge manifold;
- exactly N generated branch paths;
- exact one-to-one split and merge port usage;
- exact explicit branch permutation;
- every generated branch has the same ordered geometric template;
- no branch, bend, or required positive-length straight is missing or duplicated;
- no unexpected generated component exists;
- all connected ports are coincident, opposed, and dimensionally conformant;
- the resolved assembly has one consistent placement per connected part.

### Tube geometry

Reconcile against the 072 manifest:

- branch/common inner diameter;
- branch/common outer diameter;
- derived wall thickness;
- common supply and return centreline lengths;
- per-branch illuminated and dark straight lengths;
- bend count, centreline radius, included angle, and arc length;
- per-branch total centreline length;
- installed total branch length;
- installed total tube length;
- representative hydraulic path length.

### Tube liquid volume and area

Recompute from the generated CAD parameters and explicit component map:

- branch liquid volume each and total;
- common supply and return liquid volume;
- total tube liquid volume;
- illuminated straight area;
- illuminated bend area selected by explicit indices;
- dark straight area;
- dark bend area;
- common dark external area;
- total tube external area.

Every value is compared to the matching 072 output/manifest value using explicit
relative and absolute tolerances.

### Tube material volume

Reconcile the 072 tube-material-volume proxy against the sum of generated tube and bend
annular material volumes only.

Manifold material is additional CAD hardware and is reported separately. The service
must not compare total candidate material volume directly to a 072 output that excludes
manifold material.

After build, append a validation check comparing:

- expected material volume from all resolved part parameters; and
- final BLUECAD assembly manifest material volume.

### Manifold liquid volume

Compare the source `split_manifold_liquid_volume` and
`merge_manifold_liquid_volume` to the actual fluid-void volumes implied by each
resolved 073 manifold.

The calculation must reuse the same internal 073 geometric construction for header
cavity and branch bores. A second approximate formula or duplicated, drifting manifold
model is forbidden.

The void union must include:

- the common header cavity up to the inner cap face;
- every open branch bore up to its port;
- overlap removal at each branch/header junction.

If either explicit source manifold volume does not reconcile with the reviewed layout
dimensions, preview fails. The service does not solve for branch gap, end gap, stub
length, cap thickness, or any other dimension.

### Coverage and exclusions

Return explicit coverage for:

- generated tube/manifold geometry;
- represented liquid volumes and areas;
- pump-discharge and suction boundary endpoints;
- source reservoir liquid volume retained as process evidence but not represented in
  CAD;
- pump, reservoir shell, valves, supports, joints, floats, harvest hardware, material,
  fabrication, collision, and structural decisions not represented.

Excluded source values are marked `not_represented`, never zero, passed, or silently
ignored.

## Execute and idempotency

Execution follows the existing 052 transaction pattern.

Required behavior:

1. reconstruct preview from current state before writes;
2. reject a stale/mismatched preview digest;
3. use `BEGIN IMMEDIATE` for the initial candidate/attempt/link transaction;
4. recheck the preview inside the write transaction;
5. enforce uniqueness by `(workspace_id, preview_digest)`;
6. replay the existing coherent candidate/link on duplicate execution or race;
7. create one `process_linked` candidate and one attempt with route class
   `deterministic:cad_link:072`;
8. store source/layout/component/reconciliation/coverage evidence in the existing
   immutable CAD-link record fields and digests;
9. build through existing BLUECAD services;
10. register artifacts with honest CAD-LINK-1 producer notes;
11. record validation evidence;
12. optionally run the existing 038 analysis stage only after deterministic validation
    passes;
13. mark valid or park failure through existing candidate lifecycle;
14. clean unregistered files best-effort on pre-registration failure;
15. create no AI job and perform no provider call.

The existing `bluecad_cad_links` table is reused if its current immutable JSON/digest
fields can carry the complete source snapshot, layout, component map, reconciliation,
and coverage evidence without ambiguity. A migration is permitted only if concrete
runtime evidence shows a required immutable identity cannot be represented. No
speculative table or broad schema redesign is authorized.

## Lineage and stale propagation

Expose existing 050/051 edges from:

- source simulation run;
- source runner job;
- every accepted CAD-driving Parameter;
- source manifest artifact;
- CAD-link record;
- child candidate and attempt;
- generated artifacts;
- validation/mesh/FEM evidence and downstream simulation runs.

Replacing or changing any accepted source Parameter, invalidating the 072 run, changing
artifact identity, or superseding source evidence marks downstream CAD-LINK-1 products
stale through existing authority.

A changed layout contract produces a different preview and a distinct candidate. It
does not mutate or overwrite the previous link.

No automatic recomputation or automatic promotion occurs.

## Stable failure families

Use bounded, stable codes. At minimum distinguish:

- workspace/source run not found;
- source run not succeeded or stale;
- runner-job cardinality/status mismatch;
- exact bundled model/script/contract identity mismatch;
- topology artifact missing, duplicated, unsafe, malformed, schema-invalid, or digest-
  mismatched;
- source manifest/run/result identity mismatch;
- required Parameter binding missing, unaccepted, stale, changed, unit-mismatched, or
  duplicated across incompatible fields;
- layout unknown field, invalid number/vector, invalid manifold dimension, wrong bend
  array length, invalid illumination indices, invalid branch permutation, or unsupported
  plane/version;
- GeometrySpec transform failure;
- assembly placement/port mismatch or inconsistent multi-path closure;
- process/CAD reconciliation failure;
- manifold liquid-volume mismatch;
- preview stale;
- persistence race/incoherence;
- deterministic build/validation failure.

Errors expose no raw path, SQL, secret, stack trace, or unbounded source payload.

## Acceptance criteria

Implementation is acceptable only when all of the following hold:

1. Only one fresh exact bundled-072 run and canonical manifest can enter the transform.
2. Every persistent CAD-driving source value is backed by a current accepted Parameter.
3. The layout contract is closed, explicit, versioned, digest-bound, planar, and has no
   default or inferred value.
4. Bend traversal, illuminated bend identities, and split-to-merge branch mapping are
   operator supplied and never inferred.
5. The transform generates deterministic existing GeometrySpec kinds only.
6. Positive source lengths and all bends are represented exactly; zero source straight
   lengths are omitted honestly.
7. In-memory assembly proves one consistent merge placement across all N paths before
   writes.
8. Process/CAD topology, dimensions, lengths, liquid volumes, areas, tube material
   volume, manifold void volume, ports, and component lineage reconcile within explicit
   tolerances.
9. Reservoir/pump and all other exclusions are reported as not represented.
10. Preview performs zero writes and creates no filesystem path.
11. Execute is digest-bound, transactional, race-safe, and idempotent.
12. Repeated identical preview/execute returns the same link and candidate without
    duplicate attempts, artifacts, evidence, events, runs, or AI jobs.
13. Existing CAD-LINK-0 behavior, schema, routes, tests, and lineage do not regress.
14. Existing 072 manifest bytes/digests and 073 primitive/determinism canaries remain
    unchanged.
15. No provider call, AI job, automatic repair, optimizer, recompute, promotion, or UI
    action is added.
16. Exact-head CI and BLUECAD Real Tool Proof pass.

## Required tests

At minimum:

- strict request/layout contract tests for every field and cross-field rule;
- exact source model/script/contract/job/manifest identity tests;
- malformed, unsafe-path, duplicate, wrong-role, wrong-media-type, stale, and
  digest-mismatched topology artifact tests;
- missing/manual/unaccepted/stale/changed Parameter-binding tests for every CAD-driving
  source family;
- side-effect-free preview table-count and filesystem snapshots;
- deterministic transform fixtures for N = 1, 2, and 12;
- zero common/straight length omission cases;
- zero-bend case with empty arrays;
- forward/reverse bend traversal cases;
- explicit illuminated-bend index cases;
- identity, reverse, and nontrivial branch permutations that either assemble or fail
  honestly;
- inconsistent multi-path closure failure before writes;
- exact part IDs/order/parameters/connections/spec digest tests;
- port conformity and single rigid merge-placement tests;
- tube length, liquid-volume, illuminated/dark area, and material-volume
  reconciliation tests;
- exact manifold fluid-void volume tests sharing 073 geometry internals;
- source manifold-volume mismatch failure;
- preview digest sensitivity to every authoritative source/layout/analysis input;
- TOCTOU recheck before writes;
- duplicate/racing execute idempotency;
- build/validation/artifact failure cleanup and parking tests;
- 050/051 lineage and stale-propagation tests;
- zero AI/provider-call assertions;
- CAD-LINK-0 regression tests;
- geometry/property/determinism canary and Gmsh/CalculiX real-tool regression.

## Non-goals

This spec does not add:

- a generic topology, piping, network, routing, or scene-graph engine;
- a layout solver, optimizer, branch packer, collision search, support placer, or inverse
  design loop;
- inferred bend handedness, inferred branch mapping, inferred manifold clearances, or
  project defaults;
- out-of-plane routing, arbitrary 3D rotations, elevation changes, roll/pitch, or
  non-planar branches;
- branch-specific geometry, unequal branch flows, valves, bypasses, inactive paths,
  nested manifolds, multiple loops, multiple pumps, or recycle convergence;
- new GeometrySpec part kinds;
- reducers, standalone caps, tees, generic reservoirs, pumps, valves, flanges, welds,
  gaskets, supports, floats, harvest modules, or fabrication details;
- commercial size selection, material selection, pressure-code compliance,
  manufacturability, tolerancing, or cost estimation;
- CFD, internal-fluid meshing, hydraulic recalculation from CAD, or replacing 072
  equations;
- storing process role or flow direction inside `capped_manifold`;
- automatic Parameter creation, record promotion, stale clearing, recomputation, or
  candidate promotion;
- frontend or operator-UI work;
- AI/provider execution.

## Downstream boundary

After 074 is merged and dogfooded, later work may add a reviewed project view,
additional fixed layout templates, or explicit support/fabrication components through
separate numbered specs. Such work must consume 074 lineage and evidence; it may not
reinterpret this fixed planar contract as a general CAD or digital-twin authority.
