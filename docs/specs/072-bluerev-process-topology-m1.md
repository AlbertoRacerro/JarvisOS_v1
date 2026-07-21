# 072 — BLUEREV-PROCESS-3: explicit symmetric hydraulic topology M1

Status: ready for implementation after this definition is merged. `docs/specs/STATUS.md`
is authoritative.

Depends on: 043, 047, 050, 051, 052, 071

## Goal

Replace the single-cylinder hydraulic abstraction used by 047 with the smallest
explicit process-topology model that can represent one closed BlueRev circulation loop
with common sections and bounded symmetric parallel branches.

This slice creates a deterministic forward `calc_v0` model and a canonical topology
manifest. It does **not** create a generic process simulator, arbitrary network solver,
Aspen replacement, spatial CAD layout, optimizer, or automatic recompute engine.

After this slice, an operator can:

1. bind accepted Parameters or temporary scenario values to one reviewed M1 topology;
2. preview forward degrees of freedom through the existing 071 contract;
3. run a bounded symmetric-loop calculation through the existing runner;
4. inspect separate geometry, inventory, flow, Reynolds, pressure-loss, residence-time,
   illuminated-area, and pump-power contributions;
5. distinguish total installed geometry from the one representative hydraulic path;
6. inspect a canonical topology manifest with explicit multiplicity and component roles;
7. replace an accepted upstream Parameter and observe the run and downstream evidence
   become stale through existing 050/051 behavior;
8. use the manifest as the engineering authority for a later fixed-template CAD-LINK-1
   slice without pretending that 047 already defined full-reactor topology.

## Why this is the next engineering seam

### One scalar tube length is no longer sufficient

The 047 M0 model uses one `tube_length` for all of the following:

- liquid volume;
- illuminated external area;
- transit time;
- Darcy major pressure loss.

That is coherent for one equivalent cylinder. It is not coherent for parallel paths.
With two or more branches:

- total liquid inventory and illuminated area scale with the sum of all branch lengths;
- total circulation flow scales with the number of active identical branches;
- pressure loss is evaluated along one common-plus-branch hydraulic path and must not be
  multiplied by the number of parallel branches.

No single replacement value for `tube_length` preserves both relationships. 072 must
therefore expose two different, explicit concepts:

- **installed geometric length**, summed across all repeated branches and common runs;
- **representative hydraulic path length**, containing the common supply, one branch,
  and the common return.

The implementation must never hide this distinction behind an equivalent-length field.

### Symmetry removes the need for a network solver

M1 supports only identical parallel branches connected between one split and one merge
manifold. Every branch has the same geometry, diameter, roughness convention, velocity,
and local-loss coefficients. Their pressure drops are therefore equal by construction.

This permits a deterministic forward calculation:

- compute one branch flow from target branch velocity;
- multiply by branch count for total loop flow;
- compute common-section velocity from total flow;
- compute pressure loss through one representative branch plus common sections.

No nonlinear flow split, pressure-balance iteration, tear stream, recycle convergence,
or equation-oriented solve is required or implied.

### Topology is not spatial layout

The topology manifest defines component order, hydraulic role, multiplicity, lengths,
diameters, volumes, and illumination classification. It does not define 3D coordinates,
frames, anchoring, collision clearance, manifold port placement, or routing around a
floating structure.

A later CAD-LINK-1 may consume this manifest only together with a reviewed fixed layout
template. 072 itself does not generate a multi-part GeometrySpec.

## Model identity and files

The implementation adds one bundled model with stable identity:

```text
model label: bluerev-process-topology-m1-v0.1.0
implementation kind: calc_v0
script: backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.py
input contract: backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.contract.json
topology schema: schemas/bluerev_process_topology_m1_v0_1.schema.json
```

The registration endpoint follows the existing bundled-model pattern and is scoped to
one workspace:

```text
POST /workspaces/{workspace_id}/bundled-models/bluerev-process-topology-m1-v0/register
```

Registration is idempotent and verifies the exact script and contract hashes. It does
not create project Parameters or design defaults.

## Exact fixed topology

The only topology supported by V0 is:

```text
pump discharge
  -> common supply run
  -> split manifold
  -> N identical parallel branch templates
       branch illuminated straight run
       branch bend group
       branch dark straight run
  -> merge manifold
  -> common return run
  -> reservoir / pump suction inventory
```

`N` is `parallel_path_count` and is bounded to 1–12.

The branch template is hydraulic and one-dimensional. Its bend group records identical
bend count, radius, angle, and illumination count. It does not claim an ordered 3D bend
route or assign frames.

The model has exactly one active loop, one split, one merge, one pump, and one reservoir.
No bypass, closed branch, valve state, alternate routing, nested split, cross-connection,
or multiple pump is supported.

## Input contract

Every variable is required. The runtime accepts only the exact flat input set below,
with no extra keys and no embedded design defaults.

### Topology and multiplicity

| Name | Unit | Domain | Meaning |
| --- | --- | --- | --- |
| `parallel_path_count` | `1` | integer 1–12 | Number of identical active hydraulic branches. |
| `branch_illuminated_straight_length` | `m` | `>= 0` | Illuminated straight centreline length per branch. |
| `branch_dark_straight_length` | `m` | `>= 0` | Dark straight centreline length per branch. |
| `branch_bend_count` | `1` | integer 0–64 | Identical bends per branch. |
| `branch_illuminated_bend_count` | `1` | integer 0–`branch_bend_count` | Bends whose arc area is counted as illuminated. |
| `branch_bend_centerline_radius` | `mm` | `= 0` when bend count is 0; `> branch_tube_outer_diameter / 2` otherwise | Centreline radius of every represented bend. |
| `branch_bend_angle` | `deg` | `= 0` when bend count is 0; `> 0` and `<= 180` otherwise | Included angle of every represented bend. |
| `common_supply_length` | `m` | `>= 0` | Centreline length carrying total flow before the split. |
| `common_return_length` | `m` | `>= 0` | Centreline length carrying total flow after the merge. |

At least one of illuminated straight length, dark straight length, or bend count must be
positive. If `branch_bend_count = 0`, illuminated bend count, bend radius, and bend angle
must all be exactly zero. They remain explicit required bindings so the input shape is
stable, but no irrelevant positive value may alter the run or manifest digest. When bend
count is non-zero, the centreline radius must exceed half the branch outer diameter to
exclude a geometrically self-intersecting tube sweep. Implementations must not silently
substitute radius or angle defaults.

### Hydraulic diameters

| Name | Unit | Domain | Meaning |
| --- | --- | --- | --- |
| `branch_tube_inner_diameter` | `mm` | `> 0` | Hydraulic diameter of every branch. |
| `branch_tube_outer_diameter` | `mm` | `> inner` | External diameter for material and area accounting. |
| `common_tube_inner_diameter` | `mm` | `> 0` | Hydraulic diameter of supply and return common runs. |
| `common_tube_outer_diameter` | `mm` | `> inner` | External diameter of common runs. |

Wall thickness is derived independently for branch and common tubing as
`(outer - inner) / 2`; it must be positive and representable by GeometrySpec numeric
rules, although this slice does not build CAD.

### Non-tube liquid inventory

| Name | Unit | Domain | Meaning |
| --- | --- | --- | --- |
| `split_manifold_liquid_volume` | `L` | `>= 0` | Explicit liquid holdup in the split manifold. |
| `merge_manifold_liquid_volume` | `L` | `>= 0` | Explicit liquid holdup in the merge manifold. |
| `reservoir_liquid_volume` | `L` | `>= 0` | Reservoir and pump-suction liquid holdup outside tubing/manifolds. |

These volumes affect total inventory and inventory turnover time. They do not acquire
invented centreline lengths, external areas, or residence-path order.

### Operating point and properties

| Name | Unit | Domain | Meaning |
| --- | --- | --- | --- |
| `target_branch_velocity` | `m/s` | `> 0` | Mean velocity in each identical branch. |
| `liquid_density` | `kg/m3` | `> 0` | Density used in Reynolds and pressure loss. |
| `dynamic_viscosity` | `Pa*s` | `> 0` | Dynamic viscosity used in Reynolds. |
| `pump_efficiency` | `1` | `> 0`, `<= 1` | Overall electrical efficiency. |

### Explicit local-loss coefficients

| Name | Unit | Domain | Dynamic-pressure basis |
| --- | --- | --- | --- |
| `common_supply_minor_loss_coefficient` | `1` | `>= 0` | Common-section velocity. |
| `split_manifold_loss_coefficient` | `1` | `>= 0` | Common-section inlet velocity. |
| `branch_bend_loss_coefficient_per_bend` | `1` | `= 0` when bend count is 0; `>= 0` otherwise | Branch velocity, multiplied by bend count. |
| `branch_misc_minor_loss_coefficient` | `1` | `>= 0` | Branch velocity. |
| `merge_manifold_loss_coefficient` | `1` | `>= 0` | Common-section outlet velocity. |
| `common_return_minor_loss_coefficient` | `1` | `>= 0` | Common-section velocity. |

All K values are caller-owned preliminary model parameters with normal Parameter
provenance. The model does not infer them from CAD, vendor data, elbow radius, manifold
shape, or part count. When `branch_bend_count = 0`,
`branch_bend_loss_coefficient_per_bend` must also be exactly zero so an inert coefficient
cannot create a second manifest or digest for the same physical topology.

## Integer and cross-field validation

The existing input-contract layer is numeric. The implementation must therefore apply
additional exact runtime checks:

- counts must be finite integers, not rounded floats or booleans;
- `parallel_path_count` is between 1 and 12 inclusive;
- `branch_bend_count` is between 0 and 64 inclusive;
- `branch_illuminated_bend_count` is between 0 and `branch_bend_count` inclusive;
- when bend count is zero, illuminated bend count, radius, angle, and bend-loss
  coefficient are exactly zero;
- when bend count is non-zero, angle is in `(0, 180]` degrees and bend centreline radius
  is greater than half the branch outer diameter;
- branch and common outer diameters exceed their inner diameters;
- at least one branch length contribution is positive;
- every numeric value is finite;
- unit strings match exactly.

Invalid topology fails with a stable `bluerev_topology_error:<reason>:<field>` family and
writes no successful result.

## Deterministic geometry and inventory equations

Use SI units internally. Let:

```text
N = parallel_path_count
Di_b, Do_b = branch inner and outer diameters [m]
Di_c, Do_c = common inner and outer diameters [m]
L_i = illuminated straight length per branch [m]
L_d = dark straight length per branch [m]
N_b = bend count per branch
N_bi = illuminated bend count per branch
R_b = bend centreline radius [m]
theta = bend angle [rad]
L_s = common supply length [m]
L_r = common return length [m]
```

Then:

```text
A_b = pi * Di_b^2 / 4
A_c = pi * Di_c^2 / 4
L_bend_each = R_b * theta                  when N_b > 0, else 0
L_bends = N_b * L_bend_each
L_branch = L_i + L_bends + L_d
L_branch_illuminated = L_i + N_bi * L_bend_each
L_branch_dark = L_d + (N_b - N_bi) * L_bend_each
L_common = L_s + L_r
L_installed_branch_total = N * L_branch
L_installed_tube_total = N * L_branch + L_common
L_representative_hydraulic_path = L_s + L_branch + L_r
```

Liquid volumes:

```text
V_branch_each = A_b * L_branch
V_branch_total = N * V_branch_each
V_common_supply = A_c * L_s
V_common_return = A_c * L_r
V_manifolds = V_split + V_merge
V_non_tube = V_manifolds + V_reservoir
V_total = V_branch_total + V_common_supply + V_common_return + V_non_tube
```

External tube areas:

```text
A_branch_illuminated = N * pi * Do_b * L_branch_illuminated
A_branch_dark = N * pi * Do_b * L_branch_dark
A_common_dark = pi * Do_c * (L_s + L_r)
A_tube_external_total = A_branch_illuminated + A_branch_dark + A_common_dark
```

Manifold, reservoir, pump, joint, support, and float external areas are not evaluated.
The model must not label `A_tube_external_total` as complete reactor surface area.

Solid tube material volume is also reported analytically:

```text
A_wall_b = pi * (Do_b^2 - Di_b^2) / 4
A_wall_c = pi * (Do_c^2 - Di_c^2) / 4
V_tube_material = N * A_wall_b * L_branch + A_wall_c * (L_s + L_r)
```

This is tube material only, not total hardware mass or total CAD solid volume.

## Flow and time equations

```text
v_b = target_branch_velocity
Q_branch = v_b * A_b
Q_total = N * Q_branch
v_common = Q_total / A_c
```

The model reports both branch and common velocities. It must never apply branch velocity
to the common runs or divide total flow by only one branch area.

Nominal geometric transit times:

```text
t_supply = L_s / v_common                 if L_s > 0, else 0
t_branch = L_branch / v_b
t_return = L_r / v_common                 if L_r > 0, else 0
t_representative_path = t_supply + t_branch + t_return
t_inventory_turnover = V_total / Q_total
```

`t_representative_path` excludes residence in manifolds and reservoir because no path
geometry or mixing model is defined for them. `t_inventory_turnover` includes their
explicit holdup and is the appropriate whole-loop turnover proxy.

## Reynolds and friction correlations

For branch and common sections independently:

```text
Re = rho * v * Di / mu
```

Use the same qualified Darcy friction correlations as 047:

```text
Re < 2300:                 f = 64 / Re
4000 <= Re <= 100000:      f = 0.3164 * Re^(-0.25)
otherwise:                 fail correlation_not_qualified
```

The implementation reports separate Reynolds numbers, friction factors, and correlation
identities for branch and common sections. A qualified branch does not make an
unqualified common section acceptable, or vice versa.

No roughness, Colebrook, non-circular hydraulic diameter, two-phase flow, compressibility,
slurry rheology, free-surface flow, or transient regime is supported.

## Pressure-loss equations

Dynamic pressures:

```text
q_b = rho * v_b^2 / 2
q_c = rho * v_common^2 / 2
```

Distributed losses:

```text
dP_branch_major = f_b * (L_branch / Di_b) * q_b
dP_supply_major = f_c * (L_s / Di_c) * q_c
dP_return_major = f_c * (L_r / Di_c) * q_c
```

Explicit local losses:

```text
dP_supply_minor = K_supply * q_c
dP_split = K_split * q_c
dP_bends = N_b * K_bend_each * q_b
dP_branch_misc = K_branch_misc * q_b
dP_merge = K_merge * q_c
dP_return_minor = K_return * q_c
```

Representative branch and whole-loop pressure losses:

```text
dP_branch_representative = dP_branch_major + dP_bends + dP_branch_misc

dP_common = dP_supply_major + dP_supply_minor + dP_split
          + dP_merge + dP_return_major + dP_return_minor

dP_total = dP_common + dP_branch_representative
```

The bend arc length contributes to distributed Darcy loss and liquid volume. The bend K
contributes explicit form loss. No hidden equivalent-length conversion is added, so no
unreported double counting occurs.

Most importantly:

```text
dP_total is not multiplied by N
```

Parallel branches increase total flow and installed inventory; they do not place branch
pressure drops in series.

Power:

```text
hydraulic_power = dP_total * Q_total
pump_electric_power = hydraulic_power / pump_efficiency
equivalent_static_head = dP_total / (rho * g)
```

Pump curve, NPSH, static elevation, wave-induced pressure, manifold maldistribution, and
control margin remain unevaluated and are reported explicitly in diagnostics.

## Closed `calc_v0` topology-manifest artifact profile

The current generic `calc_v0` sandbox permits direct literal access only to
`input.json` and `result.json`, and the generic runner registers only `result.json`.
072 must not weaken that default contract or accept arbitrary caller-declared artifact
paths.

Implementation adds one closed internal artifact profile:

```text
profile: bluerev_topology_manifest_v0_1
```

The profile is selected only when all four stored model-identity values match the
reviewed bundled 072 constants:

```text
implementation_kind = calc_v0
version_label = bluerev-process-topology-m1-v0.1.0
script_sha256 = exact bundled 072 script hash
input_contract_sha256 = exact bundled 072 contract hash
```

The profile is derived by trusted runner code after loading the registered model version.
It is not a request field, contract field, script declaration, environment variable, or
caller-selectable model option. A matching label with a different script or contract
hash remains ordinary `calc_v0` and cannot obtain the additional file permission.

For this exact profile only, the AST/file policy extends the generic allowlist by:

- permitting the `hashlib` import root;
- permitting one additional direct literal call:
  `open("topology_manifest.json", "w")`;
- retaining the existing ban on dynamic paths, aliases to `open`, `pathlib` file access,
  binary/append/update/exclusive modes, subdirectories, and every other filename.

`input.json` remains read-only. `result.json` and `topology_manifest.json` remain
write-only text-truncate outputs. Generic `calc_v0` continues to allow only
`input.json` and `result.json`.

The bundled script writes `topology_manifest.json` as exact UTF-8 canonical JSON bytes:

```text
json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
```

with no trailing newline and no self-referential digest field. The script computes
`sha256:<lowercase-hex>` over those exact bytes and places the value under the versioned
`result.json` diagnostics field `topology_manifest_sha256`.

After process exit and before any run or runner job is marked succeeded, trusted runner
code for this profile must:

1. apply the ordinary `calc_v0` numerical output validation;
2. require that `result.json` does not declare caller-controlled artifacts;
3. require exactly one `topology_manifest.json` regular file at the run root, within the
   existing JSON and artifact byte limits;
4. parse it as a finite JSON object and require its on-disk bytes to equal the canonical
   serialization above;
5. validate it against `bluerev_process_topology_m1_v0_1.schema.json`;
6. verify its model, contract, topology, and executed-input identities against the exact
   registered model version and canonical simulation-run input payload, including every
   optional `source_parameter_id`;
7. recompute the raw-file SHA-256 and require exact equality with
   `result.json.diagnostics.topology_manifest_sha256`;
8. register exactly two runner-owned artifacts through the existing artifact and
   `run_artifacts` stores:
   - `result.json` with role `calc_result_json`;
   - `topology_manifest.json` with role `bluerev_topology_manifest`.

The runner constructs this two-item artifact list itself. The script cannot add, remove,
rename, re-role, or re-type artifacts. Missing, extra, non-canonical, schema-invalid,
identity-mismatched, digest-mismatched, oversized, or non-regular manifest output fails
the run before success and before Parameter proposals are created.

No new mutable topology table, general artifact declaration language, wildcard path,
directory traversal, or broader `calc_v0` permission is introduced.

## Canonical topology manifest

Each successful run writes a deterministic `topology_manifest.json` artifact and reports
its SHA-256 in `result.json`.

Schema version:

```text
bluerev_process_topology_m1_v0_1
```

The manifest contains only finite canonical JSON and at least:

```json
{
  "schema_version": "bluerev_process_topology_m1_v0_1",
  "topology_kind": "symmetric_parallel_closed_loop",
  "symmetry": {
    "parallel_path_count": "<integer>",
    "branch_template_id": "branch_template",
    "representative_path_id": "representative_path"
  },
  "ordered_components": [
    "pump",
    "common_supply",
    "split_manifold",
    "parallel_branch_group",
    "merge_manifold",
    "common_return",
    "reservoir"
  ],
  "branch_template": {
    "illuminated_straight": {},
    "bend_group": {},
    "dark_straight": {}
  },
  "hydraulic_basis": {},
  "geometry_totals": {},
  "limitations": []
}
```

Numeric values are JSON numbers, not strings, in the runtime artifact. The angle brackets
above are explanatory only.

The manifest records:

- every exact executed input value, unit, and optional `source_parameter_id`;
- derived branch/common diameters and wall thicknesses;
- branch multiplicity;
- straight and bend centreline contributions;
- illuminated and dark length classification;
- explicit manifold/reservoir volumes;
- representative-path and installed-total length distinction;
- K coefficient identities and dynamic-pressure bases;
- result and contract version identifiers;
- no self-referential digest field: the exact canonical file digest is recorded by
  `result.json` and the registered artifact metadata.

It does not contain 3D frames, generated CAD IDs, spatial coordinates, or inferred part
placement.

## Required result outputs

Every output has an explicit unit. The implementation returns at least the following
families.

### Topology and geometry

- `parallel_path_count` [`1`]
- `branch_bend_count` [`1`]
- `branch_bend_arc_length_each` [`m`]
- `branch_bend_total_length` [`m`]
- `branch_centerline_length` [`m`]
- `branch_illuminated_centerline_length` [`m`]
- `branch_dark_centerline_length` [`m`]
- `installed_branch_centerline_length_total` [`m`]
- `installed_tube_centerline_length_total` [`m`]
- `representative_hydraulic_path_length` [`m`]
- `branch_wall_thickness` [`mm`]
- `common_wall_thickness` [`mm`]
- `tube_material_volume_proxy` [`m3`]

### Inventory and area

- `branch_liquid_volume_each` [`m3`]
- `branch_liquid_volume_total` [`m3`]
- `common_supply_liquid_volume` [`m3`]
- `common_return_liquid_volume` [`m3`]
- `manifold_liquid_volume_total` [`m3`]
- `non_tube_liquid_volume_total` [`m3`]
- `total_liquid_inventory` [`m3`]
- `illuminated_branch_external_area` [`m2`]
- `dark_branch_external_area` [`m2`]
- `common_external_area` [`m2`]
- `tube_external_area_total` [`m2`]

### Flow and time

- `branch_hydraulic_cross_section_area` [`m2`]
- `common_hydraulic_cross_section_area` [`m2`]
- `branch_flow_rate` [`m3/s`]
- `total_circulation_flow_rate` [`m3/s`]
- `branch_velocity` [`m/s`]
- `common_velocity` [`m/s`]
- `common_supply_nominal_transit_time` [`s`]
- `branch_nominal_transit_time` [`s`]
- `common_return_nominal_transit_time` [`s`]
- `representative_path_nominal_transit_time` [`s`]
- `total_inventory_turnover_time` [`s`]

### Hydraulic evidence

- `branch_reynolds_number` [`1`]
- `common_reynolds_number` [`1`]
- `branch_darcy_friction_factor` [`1`]
- `common_darcy_friction_factor` [`1`]
- `branch_major_pressure_loss` [`Pa`]
- `branch_bend_pressure_loss` [`Pa`]
- `branch_misc_pressure_loss` [`Pa`]
- `representative_branch_pressure_loss` [`Pa`]
- `common_supply_major_pressure_loss` [`Pa`]
- `common_supply_minor_pressure_loss` [`Pa`]
- `split_manifold_pressure_loss` [`Pa`]
- `merge_manifold_pressure_loss` [`Pa`]
- `common_return_major_pressure_loss` [`Pa`]
- `common_return_minor_pressure_loss` [`Pa`]
- `common_pressure_loss` [`Pa`]
- `total_pressure_loss` [`Pa`]
- `equivalent_static_head` [`m`]
- `hydraulic_power` [`W`]
- `pump_electric_power` [`W`]

### Manifest and compatibility

- `topology_manifest_sha256` [`sha256` textual diagnostic field, not a numerical KPI]
- `m0_reduction_status` diagnostic enum
- `single_length_projection_status` diagnostic enum

The runner result schema may place textual digest/status fields under diagnostics rather
than the numerical `outputs` object, provided their location is versioned and tested.

## M0 reduction and compatibility proof

A dedicated fixture must reduce M1 exactly to the 047 M0 equations when:

- `parallel_path_count = 1`;
- common supply and return lengths are zero;
- split and merge manifold volumes are zero;
- bend count, illuminated bend count, bend radius, bend angle, and bend-loss
  coefficient are zero;
- dark branch length is zero;
- branch illuminated length equals 047 `tube_length`;
- branch diameters equal 047 tube diameters;
- branch velocity, density, viscosity, reservoir volume, and pump efficiency equal 047;
- the sum of represented M1 branch/common K values equals the 047 aggregate K;
- unused common-diameter bindings equal branch diameters.

Within the same deterministic tolerances as 047, the fixture must match:

- tube liquid volume;
- total liquid inventory;
- external illuminated area proxy;
- circulation flow;
- nominal tube transit time;
- inventory turnover time;
- Reynolds number;
- Darcy friction factor;
- major, minor, and total pressure loss;
- equivalent head;
- hydraulic and electric pump power.

For `parallel_path_count > 1`, differing common and branch diameters, non-zero common
length, or explicit manifold holdup, diagnostics must report:

```text
single_length_projection_status = not_single_length_representable
```

The model must not emit a fabricated 047-equivalent tube length.

## Provenance, persistence, and flowsheet behavior

072 reuses existing model-version, runner-job, simulation-run, artifact, Parameter,
run-artifact, and evidence stores. No topology-specific mutable database table is added
in V0.

The topology manifest is immutable run evidence. Runtime authority remains with:

- exact model script and contract hashes;
- executed run input payload;
- source Parameter bindings where supplied;
- registered artifacts and their hashes;
- simulation-run status and output payload.

Existing 050 graph construction must expose Parameter-to-run and run-to-artifact
lineage using existing node kinds and edge semantics. If one new artifact role is needed,
it must use the existing artifact node kind; no second graph engine or topology node
store is introduced.

Replacing an accepted bound Parameter must permit 051 to mark the M1 run and its
manifest/output artifacts stale. No automatic rerun, CAD rebuild, or promotion occurs.

## Authority and safety invariants

1. Every engineering input is caller-bound; no hidden BlueRev design default is
   embedded in the contract, registration endpoint, or UI.
2. The model is deterministic, local, and performs zero AI/provider calls.
3. Counts are validated as integers rather than silently rounded.
4. Pressure drop through parallel branches is represented by one branch, never summed
   as if branches were in series.
5. Total flow and installed branch inventory scale with branch count.
6. Common-section velocity is derived from total flow and common area.
7. Installed geometry and representative hydraulic path are separate outputs.
8. No single equivalent tube length is invented for non-degenerate M1 cases.
9. K coefficients remain explicit preliminary inputs with provenance.
10. The topology manifest is engineering evidence, not a mutable second source of truth.
11. No CAD, FEM, CFD, optimization, decision, or record is promoted automatically.
12. No failed or unqualified run is represented as successful.
13. No topology result claims spatial feasibility, manufacturability, structural safety,
    mixing quality, or complete reactor surface area.

## Explicit non-goals

- arbitrary directed process graphs;
- broadening generic `calc_v0` file or artifact permissions;
- asymmetric branch dimensions or velocities;
- automatic flow distribution or pressure balancing;
- valves, branch states, bypasses, nested manifolds, or cross-connections;
- recycle/tear convergence;
- mass or energy equation assembly;
- thermodynamic property packages;
- reactions, phase equilibrium, heat exchange, or dynamic simulation;
- pump curves, NPSH, cavitation, surge, transient pressure, or wave loading;
- roughness/Colebrook or non-Newtonian correlations;
- 3D CAD placement, frames, collisions, supports, floats, anchors, or manifold geometry;
- CAD-LINK-1 implementation;
- CFD, FEM, modal, thermal, or fluid-structure coupling;
- target solving, optimization, automatic recomputation, or automatic promotion;
- frontend or workspace-home changes;
- claiming Aspen HYSYS equivalence.

## Acceptance tests

### Contract and registration

- contract canonicalization and hash stability;
- registration idempotency and exact script/contract identity;
- the closed topology-manifest profile is selected only by the exact bundled label,
  script hash, contract hash, and `calc_v0` implementation kind;
- spoofed labels or mismatched hashes retain generic `calc_v0` restrictions;
- generic `calc_v0` cannot open or register `topology_manifest.json`;
- the exact 072 profile permits only the fixed manifest filename and write-only mode;
- all variables required, exact-name, exact-unit, no extra keys;
- zero seeded Parameters or defaults;
- existing 071 preview reports the correct structural/bound/unresolved DOF counts.

### Numeric and domain behavior

- integer count acceptance/rejection without rounding;
- invalid illuminated bend count rejection;
- exact zero radius/angle/illuminated-count/bend-loss-K enforcement for zero-bend
  branches;
- non-zero bend angle and centreline-radius geometry-bound rejection;
- positive wall-thickness checks for branch and common tubing;
- finite-number and exact-unit rejection;
- zero-length branch rejection;
- laminar branch/common qualified cases;
- turbulent branch/common qualified cases;
- transitional or out-of-range correlation rejection independently for either section.

### Geometry, inventory, and area

- bend arc-length conversion from degrees to radians;
- illuminated/dark bend classification;
- branch multiplicity scaling of installed length, volume, and area;
- common-section contributions counted once;
- manifold/reservoir volume included in inventory but not invented as tube area;
- solid tube material proxy matches analytic annular-wall equations.

### Flow and hydraulics

- total flow equals branch flow times path count;
- common velocity equals total flow divided by common area;
- representative branch pressure loss is not multiplied by path count;
- common and branch dynamic-pressure bases are kept separate;
- every pressure-loss subtotal sums exactly to total pressure loss;
- pump power uses total flow and representative-loop pressure loss;
- no hidden equivalent-length contribution appears.

### Time semantics

- geometric representative-path transit excludes non-geometric holdup;
- inventory turnover includes all explicit liquid volume;
- zero common lengths produce zero common geometric transit without division errors.

### Determinism and evidence

- identical input produces byte-identical canonical topology manifest and digest in the
  same pinned environment;
- no wall-clock value, UUID, filesystem root, or absolute runner path enters the
  manifest digest;
- exact canonical manifest bytes and raw SHA-256 agree with the result diagnostic and
  registered artifact hash;
- the registered run has exactly the runner-owned result and topology-manifest artifacts;
- zero `ai_jobs` rows and no AI provenance note;
- graph/staleness paths remain explainable through existing 050/051 nodes.

### M0 compatibility

- the exact one-path degenerate fixture reproduces the 047 equations and outputs within
  existing deterministic tolerances;
- a multi-path fixture reports `not_single_length_representable` and never fabricates a
  047-equivalent length.

### Failure modes

- missing, extra, non-regular, oversized, non-canonical, malformed, schema-invalid,
  input-identity-mismatched, or digest-mismatched manifest output fails the run honestly;
- caller-controlled artifact declarations are rejected for the closed profile;
- artifact registration failure cannot leave a succeeded run with a missing manifest;
- script or contract hash tampering fails closed and cannot activate the profile;
- repeated registration or repeated runner execution follows existing idempotency and
  immutable-history behavior;
- no test requires network access, provider credentials, or frontend runtime.

## Implementation slices

Implementation remains one spec but should be reviewed in this order:

1. bundled contract, script, topology schema, and pure numeric fixtures;
2. exact model-identity registration and the closed, model-scoped `calc_v0` manifest
   file-policy profile;
3. fixed two-artifact validation/registration and output digest binding;
4. 050/051 lineage and stale-propagation verification;
5. M0 reduction proof and adversarial failure matrix;
6. exact-head CI and existing real-tool regression proof to ensure CAD/FEM boundaries
   remain unchanged.

Do not start CAD-LINK-1, UI work, or a generic network solver inside this spec.
