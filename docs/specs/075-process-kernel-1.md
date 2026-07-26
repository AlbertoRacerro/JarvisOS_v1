# Spec 075 — PROCESS-KERNEL-1: exact 047 reproduction through typed process blocks

**Registry name:** PROCESS-KERNEL-1: streams, components, units, and unit operations  
**Depends on:** 043, 047, 048, 071  
**Implementation preconditions:** the bundled-only runner cleanup is merged; 074 remains independently owned by PR #183  
**Definition status:** reviewed draft; registry remains `planned`  
**Target path:** `docs/specs/075-process-kernel-1.md`

---

## 1. Purpose

JarvisOS already has a reviewed deterministic process calculation in spec 047. That model accepts nine caller-owned inputs and emits a canonical `result.json` for geometry, hydraulics, residence/turnover, and pumping. It does not expose reusable process objects such as streams, components, ports, or unit operations.

075 introduces only the smallest process kernel required to express the existing 047 calculation as a graph of explicit blocks while preserving the existing numerical contract.

The implementation must prove this invariant before the kernel may be reused elsewhere:

> For every canonical 047 fixture, the new bundled flowsheet path receives the same authoritative nine values, performs the same arithmetic in the same order, and emits the same canonical outputs and diagnostics as the existing 047 script.

075 is not a general process simulator. It does not solve recycles, infer thermodynamic state, select equipment, estimate missing properties, or replace the existing 047 model.

---

## 2. Binding design decisions

1. Derive abstractions from 047; do not design a broad Aspen-like platform first.
2. Keep existing 047 files, version label, v1 contract, fixtures, and digests authoritative and unchanged.
3. Run the new path side by side as a separate exact bundled implementation profile.
4. Separate physical dimensions from semantic bases.
5. Represent unknown composition, temperature, and pressure honestly.
6. Declare every dependency through material ports, scalar ports, caller parameters, or immutable profile constants.
7. Keep text labels in bounded diagnostics, never dimensional scalar outputs.
8. Preserve the public bundled-only runner boundary merged in PR #186.
9. Describe 047 as an acyclic computational cut at an imposed velocity, not a solved recycle.
10. Require deterministic graph, block, assembly, byte, and digest evidence.

---

## 3. Current runtime facts that must remain true

047 accepts exactly:

- `tube_length` in `m`;
- `tube_inner_diameter` in `mm`;
- `tube_outer_diameter` in `mm`;
- `reservoir_liquid_volume` in `L`;
- `target_liquid_velocity` in `m/s`;
- `liquid_density` in `kg/m3`;
- `dynamic_viscosity` in `Pa*s`;
- `minor_loss_coefficient` as dimensionless;
- `pump_efficiency` as dimensionless.

Further constraints:

- 071 schema v1 compares unit strings exactly;
- 047 performs explicit diameter and reservoir-volume conversions internally;
- 047 uses the immutable model constant `standard_gravity = 9.80665 m/s2`;
- the runner public API is bundled-only after PR #186;
- generic `calc_v0` remains deliberately narrow;
- FLOWSHEET-1 already needs deterministic topological ordering but owns different domain records;
- the physical plant is recirculating while current 047 arithmetic is acyclic at an imposed operating point.

Any implementation that silently changes these facts is outside 075.

---

## 4. Scope

075 includes:

1. a pinned Pint-based physical-unit boundary;
2. an immutable project semantic-unit registry;
3. additive input-contract schema v2;
4. immutable component records;
5. an immutable material stream that can represent unknown composition;
6. typed material and scalar ports;
7. a `UnitOperation` protocol;
8. four concrete blocks: `Reservoir`, `Pipe`, `Fitting`, and `Pump`;
9. an immutable `ProcessFlowsheet`;
10. deterministic validation and acyclic execution;
11. one pure topological-order utility shared with FLOWSHEET-1;
12. one exact multi-file bundled runner profile;
13. one model-specific final assembler reproducing 047;
14. side-by-side identity tests against merged 047.

No canonical database migration is required. Existing Parameters, bindings, simulation runs, runner jobs, artifacts, proposals, and MemoryStore authority remain unchanged.

---

## 5. Quantity, unit, and semantic-basis boundary

### 5.1 Pint usage

Pin Pint in `backend/requirements.txt`.

Pint is used only to:

- parse validated physical-unit expressions;
- check physical dimensions;
- convert finite magnitudes to canonical execution units;
- produce deterministic dimensional errors.

Block arithmetic uses plain finite Python floats. Pint quantities do not enter block arithmetic, graph ordering, `BlockResult`, final JSON, or digest inputs.

### 5.2 Immutable semantic-unit registry

Pint does not own JarvisOS semantic bases. Add one immutable bundled registry, versioned as `process_semantic_units_v1`, whose canonical bytes and SHA-256 are included in the bundled model profile.

Each exact semantic token maps to:

```text
SemanticUnitDefinition:
    token
    pint_unit
    scale_to_SI
    physical_dimension
    semantic_basis
```

The initial closed registry is:

| Token | Pint physical unit | Exact SI scale | Physical dimension | Semantic basis |
|---|---|---:|---|---|
| `gDW` | `gram` | `0.001 kg` | mass | `dry_biomass` |
| `kgDW` | `kilogram` | `1 kg` | mass | `dry_biomass` |
| `mgN` | `milligram` | `0.000001 kg` | mass | `nitrogen` |
| `gN` | `gram` | `0.001 kg` | mass | `nitrogen` |
| `mgP` | `milligram` | `0.000001 kg` | mass | `phosphorus` |
| `gP` | `gram` | `0.001 kg` | mass | `phosphorus` |
| `gC` | `gram` | `0.001 kg` | mass | `carbon` |
| `kgC` | `kilogram` | `1 kg` | mass | `carbon` |
| `mLCO2` | `milliliter` | `0.000001 m3` | volume | `carbon_dioxide` |
| `LCO2` | `liter` | `0.001 m3` | volume | `carbon_dioxide` |
| `EUR` | bundled `[currency]` unit | `1 EUR` | currency | `EUR` |

Rules:

1. Exact semantic tokens are resolved through this registry before ordinary Pint parsing.
2. The registry supplies both physical unit and semantic basis; callers do not submit a separate basis field.
3. An ordinary Pint token such as `kg`, `mg`, or `mL` has `semantic_basis = null`.
4. A contract that requires a semantic basis rejects a basis-null ordinary unit even when its physical dimension matches.
5. Conversion is allowed only when source and target semantic bases are identical.
6. Unknown lookalike tokens fail; no prefix or suffix inference creates new semantic units.
7. Registry additions or scale changes require a later reviewed spec and new registry version.

Thus `gDW -> kgDW` is valid, while `mgN -> mgP`, `kg -> kgDW`, and `mL -> mLCO2` are invalid without an explicit later authority.

### 5.3 Input-contract schema v2

Schema v1 remains byte- and behavior-compatible.

Schema v2 adds, per variable:

- canonical execution `unit`;
- canonical `physical_dimension`;
- optional required `semantic_basis`;
- existing description/category/required/domain metadata.

For v2 inputs:

1. validate finite JSON magnitude;
2. resolve an exact semantic token or parse an ordinary Pint unit;
3. require physical-dimension compatibility;
4. require semantic-basis compatibility;
5. convert to canonical execution unit;
6. apply domain after conversion;
7. compare Parameter-backed values in the same canonical unit and basis;
8. emit a canonical normalized input set.

The 075 version of the 047 contract uses the historical 047 units as canonical execution units. For already-canonical fixtures, the original float magnitude is preserved and legacy conversions remain inside the blocks.

Equivalent-unit cases are accepted separately, but byte identity against old 047 is required only for the historical canonical fixtures.

---

## 6. Component registry and 048 compatibility constants

### 6.1 Component contract

```text
Component:
    id
    name
    phase_hint | null
    molecular_formula{element: stoichiometric_count} | null
    scientific_molar_mass_kg_per_mol | null
    elemental_mass_fractions{element: fraction} | null
```

Rules:

- records are immutable and server-bundled;
- molecular species and pseudo-components remain distinct;
- pseudo-components do not invent molecular formulas or molar masses;
- a scientific molar mass, when present, must identify its pinned source/table and precision convention.

Initial catalog:

- water;
- carbon dioxide;
- oxygen;
- one explicitly fixture-owned biomass pseudo-component.

The biomass fixture is test evidence, not an accepted BlueRev value.

### 6.2 Rounded screening constants from 048

Do not claim that 048's exact `44.0 / 12.0` ratio is derived from a modern conventional atomic-weight table.

Add one separate immutable compatibility record:

```text
screening_mass_constants_v0:
    carbon_g_per_mol = 12.0
    oxygen_g_per_mol = 16.0
    carbon_dioxide_g_per_mol = 44.0
    carbon_dioxide_to_carbon_ratio = 44.0 / 12.0
    authority = "merged 048 rounded screening constants"
```

These are exact nominal screening constants retained for 048 compatibility. They are not labelled IUPAC atomic weights and do not populate `scientific_molar_mass_kg_per_mol` automatically.

A proof test reconstructs `44.0` from `12.0 + 2 * 16.0` and then reproduces the exact 048 screening ratio. Any later scientific molar-mass model requires its own pinned table and reviewed precision policy.

---

## 7. MaterialStream

### 7.1 Contract

```text
MaterialStream:
    id
    composition{component_id: mass_fraction} | null
    density_kg_m3 | null
    dynamic_viscosity_Pa_s | null
    mass_flow_kg_s | null
    volumetric_flow_m3_s | null
    temperature_K | null
    pressure_Pa | null
```

Rules:

- the record is immutable;
- `composition = null` means unknown, not empty and not pure water;
- when composition is present, fractions are finite, nonnegative, reference bundled components, and sum to one within a fixed tolerance;
- density and viscosity, when present, are positive finite supplied properties;
- either flow may remain unknown;
- if one flow and density are known, the other may be derived;
- if both flows are present, consistency is validated;
- blocks return new streams and never mutate inputs;
- a block requiring composition or a specific component declares that requirement and rejects unknown composition before execution.

Density and viscosity are supplied values. No property package is implied.

### 7.2 Exact 047 external stream

```text
loop_liquid:
    composition = unknown
    density = liquid_density
    dynamic_viscosity = dynamic_viscosity
    temperature = unknown
    pressure = unknown
    mass_flow = unknown
    volumetric_flow = unknown
```

The nine-input 047 contract contains no composition authority, so 075 must not represent this stream as pure water.

The 047 blocks do not require composition. Pipe derives operating flow from target velocity and hydraulic area exactly as the current script does.

---

## 8. Ports, parameters, constants, and block results

### 8.1 Port kinds

A port is either `material` or `scalar`.

A material port declares each required stream field and optional component/phase constraints.

A scalar port declares canonical unit, physical dimension, and optional semantic basis. Scalar values are finite numerics only.

Text labels, warnings, selected correlation names, and regime identifiers belong in bounded diagnostics.

### 8.2 Parameter authority classes

Every block dependency belongs to one declared class:

- `caller_parameter`: one of the nine caller-owned 047 values;
- `profile_constant`: immutable server-owned model constant included in bundled profile bytes/digest;
- `material_input`;
- `scalar_input`.

A block may not read undeclared module globals, environment values, previous runs, another block's internals, or database records.

### 8.3 UnitOperation protocol

```text
class UnitOperation:
    material_inlets
    scalar_inlets
    material_outlets
    scalar_outlets
    caller_parameters
    profile_constants

    solve(
        material_inputs,
        scalar_inputs,
        caller_parameter_values,
        profile_constant_values,
    ) -> BlockResult
```

```text
BlockResult:
    material_outputs
    scalar_outputs
    diagnostics
```

The validator rejects unknown ports, wrong kinds, incompatible dimensions/bases, unsatisfied material requirements, missing drivers, duplicate drivers, undeclared extras, cycles, and graphs above fixed bounds before any block executes.

---

## 9. Exact 047 block decomposition

### 9.1 Graph

Material path:

```text
external loop_liquid -> Reservoir.inlet
Reservoir.outlet      -> Pipe.inlet
Pipe.outlet           -> Fitting.inlet
Fitting.outlet        -> Pump.inlet
```

Scalar connections:

```text
Pipe.dynamic_pressure       -> Fitting.dynamic_pressure
Pipe.major_pressure_loss    -> Pump.major_pressure_loss
Fitting.minor_pressure_loss -> Pump.minor_pressure_loss
```

The dynamic-pressure connection is mandatory. Fitting may not inspect Pipe internals or recompute dynamic pressure through hidden inputs.

The graph is an acyclic computational cut through a physical recirculating system. `target_liquid_velocity` is an imposed operating specification. 075 does not solve a recycle or pump/system intersection.

### 9.2 Mapping of the nine caller-owned inputs

| 047 input | 075 authority |
|---|---|
| `tube_length` | Pipe caller parameter |
| `tube_inner_diameter` | Pipe caller parameter |
| `tube_outer_diameter` | Pipe caller parameter |
| `reservoir_liquid_volume` | Reservoir caller parameter |
| `target_liquid_velocity` | Pipe caller parameter |
| `liquid_density` | external stream supplied property |
| `dynamic_viscosity` | external stream supplied property |
| `minor_loss_coefficient` | Fitting caller parameter |
| `pump_efficiency` | Pump caller parameter |

No default or previous record silently supplies one of these values.

### 9.3 Reservoir

Material requirement: none beyond a valid stream record.

Behavior: pass stream unchanged.

Caller parameter:

- reservoir liquid volume.

Scalar output:

- reservoir liquid volume in cubic metres, using the same `/ 1000.0` operation and arithmetic position as 047.

### 9.4 Pipe

Material requirements:

- `density_kg_m3` present;
- `dynamic_viscosity_Pa_s` present;
- composition not required.

Caller parameters:

- tube length;
- inner diameter;
- outer diameter;
- target liquid velocity.

Material behavior:

- compute hydraulic area;
- compute volumetric flow from imposed velocity and area;
- compute mass flow from density and volumetric flow;
- emit a new stream carrying density, viscosity, and both flows.

Scalar outputs in legacy order:

- hydraulic cross-sectional area;
- tube liquid volume;
- external illuminated-area proxy;
- internal wetted-area-to-volume;
- external-area-to-volume proxy;
- circulation flow;
- nominal tube transit time;
- Reynolds number;
- Darcy friction factor;
- dynamic pressure;
- major pressure loss.

Diagnostics:

- hydraulic regime;
- friction-correlation label;
- validity-bound evidence.

The friction label is diagnostic text, never a scalar output.

The merged 047 laminar/Blasius behavior, transition rejection, upper validity bound, Darcy convention, and absence of roughness remain unchanged.

### 9.5 Fitting

Material behavior: pass Pipe outlet unchanged.

Required scalar input:

- `dynamic_pressure` from Pipe.

Caller parameter:

- minor-loss coefficient.

Scalar output:

- minor pressure loss from declared dynamic pressure and coefficient in legacy order.

### 9.6 Pump

`Pump.inlet` explicitly requires:

- `density_kg_m3` present and positive;
- `volumetric_flow_m3_s` present and nonnegative.

Required scalar inputs:

- Pipe major pressure loss;
- Fitting minor pressure loss.

Caller parameter:

- pump efficiency.

Immutable profile constant:

```text
standard_gravity:
    value = 9.80665
    unit = m/s2
    physical_dimension = acceleration
    authority = merged 047 model constant
```

`standard_gravity` is not a tenth caller input. Its canonical bytes and digest are included in the exact bundled profile and passed explicitly to `Pump.solve()` through `profile_constant_values`.

Scalar outputs in legacy order:

- total pressure loss;
- equivalent static head using declared density and standard gravity;
- hydraulic power using declared volumetric flow;
- pump electric power.

No pump curve, NPSH, transient pressure, absolute discharge pressure, or efficiency map is inferred.

### 9.7 Model-specific final assembler

The generic executor gains no expression language.

One fixed bundled 047 assembler consumes validated block results and computes in legacy order:

- total liquid inventory;
- total inventory turnover time;
- exact final 047 output dictionary;
- exact final 047 diagnostics dictionary.

The assembler is part of the bundled profile and cannot be caller-supplied.

---

## 10. ProcessFlowsheet and deterministic execution

```text
ProcessFlowsheet:
    schema_version
    model_identity
    semantic_unit_registry_identity
    blocks{stable_block_id: block_definition}
    material_connections[]
    scalar_connections[]
    external_inputs[]
    profile_constants[]
    result_assembler_identity
```

Validation proves stable identities, complete single drivers, material/scalar compatibility, required stream fields, dimension/basis compatibility, acyclicity, bounded size, and deterministic canonical representation.

Extract one pure topological-order utility accepting stable node IDs and directed edges. FLOWSHEET-1 and PROCESS-KERNEL-1 reuse it without sharing domain models. Existing FLOWSHEET-1 tests remain unchanged.

Execution validates the graph, freezes canonical inputs/constants, executes each block once in deterministic order, records bounded evidence, invokes the fixed assembler, canonicalizes output, and emits deterministic digests.

There is no iteration, convergence loop, optimizer, event simulation, parallel scheduling, implicit recycle, or automatic recomputation.

---

## 11. Exact bundled runner profile

Do not widen generic caller-selected `calc_v0` imports.

The server-known bundled profile identity includes:

- entry-point path and SHA-256;
- every process-kernel package file path and SHA-256;
- v2 input-contract canonical bytes and digest;
- semantic-unit registry canonical bytes and digest;
- compatibility screening constants canonical bytes and digest;
- flowsheet canonical bytes and digest;
- profile constants, including standard gravity, and digest;
- final assembler identity and digest;
- allowed package/import roots;
- profile schema/version.

Callers may select inputs and an already registered model version. They cannot provide source, file paths, import roots, environment, working directory, package manifest, hash-as-authority, trust flags, assembler identity, semantic-unit definitions, constants, or policy profile.

At job creation and immediately before execution, verify the complete profile. Missing, extra, replaced, or hash-mismatched files/records fail closed with `RUNNER_SCRIPT_POLICY_VIOLATION` before subprocess launch.

---

## 12. Numerical and canonical identity

For every canonical merged 047 fixture, require equality of:

- normalized canonical inputs;
- every final output key and unit;
- every numeric value by `float.hex()`;
- diagnostic keys and values;
- status and schema fields;
- canonical `result.json` bytes;
- result digest;
- content-relevant artifact metadata.

Operational run IDs, timestamps, paths, and model-version IDs are excluded.

Tests also map every 047 intermediate equation to a named block scalar or diagnostic. Final-output equality alone is insufficient if responsibility is hidden or duplicated.

Equivalent-unit cases compare the normalized 075 physical case against the same 075 case in canonical units; old 047 request semantics remain unchanged.

---

## 13. Required tests

### Units and bases

- v1 exact-unit behavior unchanged;
- semantic registry canonical bytes/digest deterministic;
- exact scales for every initial semantic token;
- valid same-basis conversions accepted;
- ordinary basis-null unit rejected for basis-required contract;
- cross-basis and lookalike tokens rejected;
- dimension mismatch rejected;
- domain applied after conversion;
- non-finite values rejected.

### Components and compatibility constants

- molecular and pseudo-component representations remain distinct;
- rounded constants are exactly C=12.0, O=16.0, CO2=44.0;
- exact `44.0 / 12.0` compatibility ratio reproduced;
- constants are labelled as 048 screening compatibility, not scientific atomic weights;
- scientific molar mass cannot be populated from compatibility constants implicitly.

### Streams

- known composition validates;
- invalid fractions and unknown components fail;
- unknown composition remains `null`, not pure water;
- a composition-requiring block rejects unknown composition;
- 047 blocks accept unknown composition;
- flow consistency and immutability verified.

### Graph and ports

- valid graph order deterministic;
- dynamic-pressure connection required;
- removing it fails before execution;
- Fitting cannot inspect Pipe internals;
- Pump inlet rejects missing density;
- Pump inlet rejects missing volumetric flow;
- wrong kind/dimension/basis, duplicate driver, unknown port, cycle, and size excess fail;
- FLOWSHEET-1 ordering tests remain green.

### Blocks and constants

- Reservoir preserves legacy conversion;
- Pipe reproduces every mapped intermediate;
- friction label appears only in diagnostics;
- Fitting uses connected dynamic pressure;
- Pump receives explicit density, flow, losses, efficiency, and standard gravity;
- changing standard gravity changes bundled profile identity and canonical result;
- caller cannot override standard gravity;
- blocks do not mutate streams or global state.

### Runner boundary

- exact multi-file profile registers and runs;
- caller source/path/import/environment/trust/registry/constant fields rejected;
- changed entry point, package file, contract, semantic registry, constants, flowsheet, or assembler fails before launch;
- denial proves zero subprocess invocation;
- PR #186 boundary tests remain green.

### Identity

- side-by-side canonical fixtures match outputs, units, `float.hex()`, diagnostics, bytes, and digest;
- intermediate mapping complete;
- equivalent-unit cases physically equal after normalization;
- repeated canonical runs deterministic;
- no accepted engineering value or MemoryStore record silently created or promoted.

---

## 14. Acceptance criteria

`AC-075-01` — Existing 047 files, label, v1 contract, fixtures, and digests remain unchanged.  
`AC-075-02` — Pint is pinned and used only at physical-unit boundaries.  
`AC-075-03` — A closed immutable semantic-unit registry defines exact scales and bases.  
`AC-075-04` — Input-contract v2 is additive and v1 behavior remains exact.  
`AC-075-05` — Physical dimensions and semantic bases are independently enforced.  
`AC-075-06` — Rounded 048 compatibility constants are explicit and not mislabelled scientific atomic weights.  
`AC-075-07` — MaterialStream is immutable and can represent unknown composition honestly.  
`AC-075-08` — The 047 stream does not invent pure-water composition.  
`AC-075-09` — Every dependency is a declared port, caller parameter, or profile constant.  
`AC-075-10` — Pipe dynamic pressure is explicitly connected to Fitting.  
`AC-075-11` — Friction/regime labels are diagnostics, never scalar physics.  
`AC-075-12` — Pump inlet explicitly requires density and volumetric flow.  
`AC-075-13` — Standard gravity is an immutable bundled Pump/profile constant, not a caller input or hidden global.  
`AC-075-14` — The graph executes once in deterministic topological order.  
`AC-075-15` — FLOWSHEET-1 and PROCESS-KERNEL-1 share one pure ordering utility without sharing domain models.  
`AC-075-16` — The graph is an imposed-operating-point computational cut, not a solved recycle.  
`AC-075-17` — The generic executor gains no equation language, optimizer, or solver.  
`AC-075-18` — The final assembler is fixed, bundled, and model-specific.  
`AC-075-19` — Runner verifies the complete multi-file/profile-record identity at creation and execution.  
`AC-075-20` — Caller-supplied executable, registry, constant, or trust authority remains impossible.  
`AC-075-21` — Canonical fixtures match 047 by outputs, units, `float.hex()`, diagnostics, bytes, and digest.  
`AC-075-22` — Equivalent-unit cases are separate and do not change old 047 semantics.  
`AC-075-23` — No database migration, automatic promotion, accepted-value mutation, or frontend work is introduced.  
`AC-075-24` — Canonical backend, runner-boundary, FLOWSHEET-1, and BLUECAD proof workflows remain green.  
`AC-075-25` — An independent reviewer adds or approves at least one negative graph/identity test not authored with the implementation.

---

## 15. Delivery sequence

### Definition PR

This PR:

- adds this definition;
- records 075 as `planned`;
- records 045 as cancelled under the current loopback single-user threat model;
- records trigger-gated future isolation work;
- preserves 074 as `in_review` under PR #183;
- does not authorize implementation.

### Promotion PR

A separate maintainer-reviewed PR may move 075 from `planned` to `ready` only after:

- this definition is merged;
- PR #186 remains merged and green;
- #183/074 state is reconciled;
- all review threads are resolved;
- no open PR overlaps runner, input-contract, ordering, or process-kernel target files;
- implementation slices and ownership are explicit.

### Implementation PR

Implementation then moves through `in_progress` and `in_review`, stays within this definition, and does not widen scope silently.

No automatic merge is permitted.

---

## 16. Non-goals

075 does not add recycle solving, nonlinear solving, dynamic simulation, thermodynamic/property packages, phase equilibrium, reaction kinetics, general expression languages, general network hydraulics, pump/system curve intersection, equipment sizing beyond 047, automatic defaults, accepted Parameter promotion, frontend flowsheet editing, hostile-code sandboxing, caller-authored Python, Hermes/MCP execution authority, or retirement of 047.

---

## 17. Rollback

If implementation cannot preserve canonical identity or bundled runner authority:

- disable/remove only the new 075 bundled profile;
- preserve existing 047 registrations, runs, artifacts, and Parameters;
- retain failed 075 evidence historically;
- do not relax identity checks or restore caller source;
- return 075 to `planned` or `blocked` with the mismatch documented.

---

## 18. Final invariant

> JarvisOS may generalize process abstractions only after they reproduce an already reviewed calculation without inventing composition, semantic units, scientific constants, stream requirements, dependencies, execution authority, or numerical behavior.
