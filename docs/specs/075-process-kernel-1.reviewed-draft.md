# Spec 075 — PROCESS-KERNEL-1: exact 047 reproduction through typed process blocks

**Registry name:** PROCESS-KERNEL-1: streams, components, units, and unit operations  
**Depends on:** 043, 047, 048, 071  
**Implementation preconditions:** the bundled-only runner cleanup is merged; 074 remains independently owned by PR #183  
**Definition status:** reviewed draft; registry remains `planned`  
**Target path:** `docs/specs/075-process-kernel-1.md`

---

## 1. Purpose

JarvisOS already has a reviewed deterministic process calculation in spec 047. That model accepts nine caller-owned inputs and emits a canonical `result.json` for geometry, hydraulics, residence/turnover, and pumping. It does not yet expose reusable process objects such as streams, components, ports, or unit operations.

075 introduces only the smallest process kernel required to express the existing 047 calculation as a graph of explicit blocks while preserving the existing numerical contract.

The implementation must prove the following invariant before the kernel may be reused elsewhere:

> For every canonical 047 fixture, the new bundled flowsheet path receives the same authoritative nine values, performs the same arithmetic in the same order, and emits the same canonical outputs and diagnostics as the existing 047 script.

075 is not a general process simulator. It does not solve recycles, infer thermodynamic state, select equipment, estimate missing properties, or replace the existing 047 model.

---

## 2. Binding design decisions

1. **Derive abstractions from 047.** Do not design a broad Aspen-like platform first.
2. **Keep 047 authoritative.** The existing script, label, v1 input contract, fixtures, and digests remain unchanged.
3. **Run side by side.** The 075 path is a new exact bundled implementation profile, not an in-place rewrite.
4. **Separate dimensions from semantic bases.** `kg`, `kgDW`, `mgN`, and `mgP` may share physical dimensions while retaining incompatible semantic bases.
5. **Represent unknowns honestly.** Composition, temperature, and pressure are not invented when 047 does not provide them.
6. **Declare every dependency.** No block may read another block, global state, or undeclared value outside its material/scalar inputs and parameters.
7. **Keep labels out of scalar physics.** Textual regime/correlation labels belong in bounded diagnostics, not dimensional scalar ports.
8. **Preserve runner authority.** Only exact server-known bundled files may execute; callers never submit executable source or trust metadata.
9. **Do not imply recycle convergence.** The 047 graph is an acyclic computational cut at an imposed velocity.
10. **Require deterministic evidence.** Graph order, canonical inputs, block results, final assembly, and digests must be reproducible.

---

## 3. Current runtime facts that must remain true

The implementation is constrained by current merged behavior:

- 047 accepts exactly:
  - `tube_length` in `m`;
  - `tube_inner_diameter` in `mm`;
  - `tube_outer_diameter` in `mm`;
  - `reservoir_liquid_volume` in `L`;
  - `target_liquid_velocity` in `m/s`;
  - `liquid_density` in `kg/m3`;
  - `dynamic_viscosity` in `Pa*s`;
  - `minor_loss_coefficient` as dimensionless;
  - `pump_efficiency` as dimensionless.
- 071 schema version 1 compares unit strings exactly.
- 047 performs explicit diameter and reservoir-volume conversions inside the calculation.
- The runner public API is bundled-only after PR #186.
- Generic `calc_v0` remains deliberately narrow and must not gain unrestricted application imports.
- FLOWSHEET-1 already needs deterministic topological ordering, but its domain records are not process blocks.
- The physical plant is recirculating while the current arithmetic is an acyclic forward calculation at an imposed operating point.

A proposed implementation that silently changes any of these facts is outside 075.

---

## 4. Scope

075 includes:

1. a pinned Pint-based quantity-validation boundary;
2. additive input-contract schema version 2;
3. immutable component records;
4. an immutable material-stream record that can represent unknown composition;
5. typed material and scalar ports;
6. a `UnitOperation` protocol;
7. four concrete blocks: `Reservoir`, `Pipe`, `Fitting`, and `Pump`;
8. an immutable `ProcessFlowsheet`;
9. deterministic validation and acyclic execution;
10. extraction of one pure deterministic topological-order utility shared with FLOWSHEET-1;
11. one exact multi-file bundled runner profile for the 075 entry point and kernel package;
12. a model-specific final assembler reproducing 047;
13. side-by-side identity tests against the merged 047 script.

No canonical database migration is required by this definition. Existing Parameters, bindings, simulation runs, runner jobs, artifacts, proposals, and MemoryStore authority remain unchanged.

---

## 5. Quantity and unit boundary

### 5.1 Pint usage

Pin Pint in `backend/requirements.txt`.

Pint is used only at validated boundaries to:

- parse submitted unit strings;
- check physical dimensions;
- check optional semantic basis;
- convert a finite magnitude to a canonical execution unit;
- produce deterministic validation errors.

Block arithmetic uses plain finite Python floats. Pint quantities do not enter graph ordering, block arithmetic, `BlockResult`, final JSON, or digest inputs.

### 5.2 Physical dimension and semantic basis

A variable or scalar port may declare:

```text
unit
physical_dimension
semantic_basis | null
```

Examples:

| Unit | Physical dimension | Semantic basis |
|---|---|---|
| `gDW` | mass | `dry_biomass` |
| `kgDW` | mass | `dry_biomass` |
| `mgN` | mass | `nitrogen` |
| `mgP` | mass | `phosphorus` |
| `gC` | mass | `carbon` |
| `mLCO2` | volume | `carbon_dioxide` |
| `EUR` | currency | `EUR` |

Equal physical dimensions do not override basis conflicts. A nitrogen quantity cannot satisfy a phosphorus contract merely because both are mass.

### 5.3 Additive input-contract schema v2

Schema v1 remains byte- and behavior-compatible.

Schema v2 adds, per variable:

- canonical execution `unit`;
- canonical `physical_dimension`;
- optional `semantic_basis`;
- existing description/category/required/domain metadata.

For v2 inputs:

1. validate finite JSON magnitude;
2. parse submitted unit;
3. require dimension compatibility;
4. require semantic-basis compatibility when declared;
5. convert to the canonical execution unit;
6. apply the domain after conversion;
7. compare Parameter-backed values in the same canonical unit;
8. emit a canonical normalized input set.

The 075 version of the 047 contract uses the historical units above as canonical execution units. For already-canonical fixtures, the original float magnitude is preserved and the legacy conversions remain inside the blocks.

Equivalent-unit cases are allowed, but bit identity against the old script is required only for the historical canonical fixtures. Equivalent-unit tests compare physical equivalence after canonical normalization.

---

## 6. Component registry

### 6.1 Component contract

```text
Component:
    id
    name
    phase_hint | null
    molar_mass_kg_per_mol | null
    molecular_formula{element: stoichiometric_count} | null
    elemental_mass_fractions{element: fraction} | null
```

Rules:

- records are immutable and server-bundled;
- molecular species use a formula and a molar mass derived from one immutable atomic-weight table;
- pseudo-components may use elemental mass fractions but must not invent molecular formulas or molar masses;
- the two representations are never conflated.

### 6.2 Initial catalog and proof seam

The initial catalog contains only:

- water;
- carbon dioxide;
- oxygen;
- one explicitly fixture-owned biomass pseudo-component.

The biomass fixture is test evidence, not an accepted BlueRev design value.

A registry test computes the `CO2/C` mass ratio represented as `44.0 / 12.0` in 048 from the immutable atomic/component records. 048 itself remains unchanged.

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
- when composition is present, it is finite, nonnegative, references bundled components, and sums to one within a fixed tolerance;
- density and viscosity, when present, are positive finite supplied properties;
- temperature and pressure may remain unknown;
- either flow may remain unknown;
- when one flow and density are known, the other may be derived;
- when both flows are present, consistency is validated;
- blocks return new streams and never mutate inputs;
- a block that requires composition or a specific component must declare that requirement and reject an unknown composition before execution.

No property package is implied. Density and viscosity are supplied values, not inferred from composition.

### 7.2 Exact 047 external stream

The 047 compatibility flowsheet receives:

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

This is intentional. The nine-input 047 contract contains no composition authority and therefore 075 may not represent the stream as `{water: 1.0}`.

The four 047 blocks do not require composition. The Pipe derives operating flow from target velocity and hydraulic area exactly as the existing script does.

---

## 8. Ports and block contract

### 8.1 Port kinds

A port is either:

- `material`; or
- `scalar`.

A material port declares required stream fields and optional component/phase constraints.

A scalar port declares a canonical unit, physical dimension, and optional semantic basis. Scalar values are finite numerics only.

Text labels, warnings, selected correlation names, and regime identifiers are not scalar ports. They are bounded diagnostics.

### 8.2 UnitOperation protocol

```text
class UnitOperation:
    material_inlets
    scalar_inlets
    material_outlets
    scalar_outlets
    parameters

    solve(
        material_inputs,
        scalar_inputs,
        parameter_values,
    ) -> BlockResult
```

```text
BlockResult:
    material_outputs
    scalar_outputs
    diagnostics
```

The validator rejects before execution:

- unknown blocks or ports;
- wrong port kind;
- incompatible scalar dimension or basis;
- material requirements that cannot be satisfied;
- missing required drivers;
- duplicate drivers;
- undeclared extra connections;
- cycles;
- graphs above fixed size limits.

A block cannot discover ports dynamically or read values from another block except through declared connections.

---

## 9. Exact 047 block decomposition

### 9.1 Graph

Material path:

```text
external loop_liquid
    -> Reservoir.inlet
Reservoir.outlet
    -> Pipe.inlet
Pipe.outlet
    -> Fitting.inlet
Fitting.outlet
    -> Pump.inlet
```

Scalar connections:

```text
Pipe.dynamic_pressure       -> Fitting.dynamic_pressure
Pipe.major_pressure_loss    -> Pump.major_pressure_loss
Fitting.minor_pressure_loss -> Pump.minor_pressure_loss
```

`Pipe.dynamic_pressure -> Fitting.dynamic_pressure` is mandatory. The Fitting must not read velocity, hydraulic area, Pipe internals, or global execution state indirectly.

The graph is an acyclic computational cut through a physical recirculating system. `target_liquid_velocity` is an imposed operating specification. 075 does not solve the physical tear or pump/system intersection.

### 9.2 Mapping of the nine authoritative inputs

| 047 input | 075 authority |
|---|---|
| `tube_length` | Pipe parameter |
| `tube_inner_diameter` | Pipe parameter |
| `tube_outer_diameter` | Pipe parameter |
| `reservoir_liquid_volume` | Reservoir parameter |
| `target_liquid_velocity` | Pipe operating parameter |
| `liquid_density` | external stream supplied property |
| `dynamic_viscosity` | external stream supplied property |
| `minor_loss_coefficient` | Fitting parameter |
| `pump_efficiency` | Pump parameter |

No default, component record, accepted Parameter, environment variable, or previous run may silently supply one of these values.

### 9.3 Reservoir

Material behavior: pass the stream through unchanged.

Parameter:

- `reservoir_liquid_volume`.

Scalar output:

- `reservoir_liquid_volume_m3`, using the same `/ 1000.0` operation and position in the arithmetic sequence as 047.

### 9.4 Pipe

Material requirements:

- density present;
- dynamic viscosity present;
- composition not required.

Parameters:

- tube length;
- inner diameter;
- outer diameter;
- target liquid velocity.

Material behavior:

- compute hydraulic area;
- compute volumetric flow from imposed velocity and area;
- compute mass flow from density and volumetric flow;
- emit a new stream carrying those flows.

Scalar outputs, in legacy operation order:

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

Diagnostics include:

- hydraulic regime;
- friction-correlation label;
- validity-bound evidence.

The friction-correlation label is diagnostic text. It is not a scalar result and has no fabricated unit or dimension.

The merged 047 laminar/Blasius behavior, transition rejection, upper validity bound, Darcy convention, and absence of roughness remain unchanged.

### 9.5 Fitting

Material behavior: pass the Pipe outlet stream through unchanged.

Required scalar input:

- `dynamic_pressure` from `Pipe.dynamic_pressure`.

Parameter:

- minor-loss coefficient.

Scalar output:

- minor pressure loss, computed from the declared dynamic-pressure input and coefficient in the same operation order as 047.

The Fitting may not recompute dynamic pressure from hidden Pipe values and may not inspect another block result directly.

### 9.6 Pump

Material input:

- Fitting outlet stream.

Required scalar inputs:

- Pipe major pressure loss;
- Fitting minor pressure loss.

Parameter:

- pump efficiency.

Scalar outputs, in legacy operation order:

- total pressure loss;
- equivalent static head;
- hydraulic power;
- pump electric power.

No pump curve, NPSH, transient pressure, absolute discharge pressure, or efficiency map is inferred.

### 9.7 Model-specific final assembler

The generic executor does not gain a general expression language.

One exact bundled 047 assembler consumes validated block results and computes in legacy order:

- total liquid inventory = tube liquid volume + reservoir liquid volume;
- total inventory turnover time = total liquid inventory / circulation flow;
- the exact final 047 output dictionary;
- the exact final 047 diagnostics dictionary.

The assembler is part of the bundled 075 model profile and cannot be supplied or selected by the caller.

---

## 10. ProcessFlowsheet and deterministic execution

### 10.1 Immutable flowsheet

```text
ProcessFlowsheet:
    schema_version
    model_identity
    blocks{stable_block_id: block_definition}
    material_connections[]
    scalar_connections[]
    external_inputs[]
    result_assembler_identity
```

Canonicalization requires stable ordering, finite bounded data, explicit identities, and no defaults hidden in serialization.

### 10.2 Shared topological-order utility

Extract one pure utility that accepts stable node IDs and directed edges and returns deterministic topological order with the existing lexicographic tie-break behavior.

- FLOWSHEET-1 uses it for provenance dependencies.
- PROCESS-KERNEL-1 uses it for material/scalar block dependencies.

Do not import FLOWSHEET-1 domain records into the process kernel and do not duplicate the algorithm.

Existing FLOWSHEET-1 tests remain unchanged and green.

### 10.3 Execution

Execution:

1. validates the complete graph;
2. freezes canonical external values and parameters;
3. derives deterministic order;
4. executes each block exactly once;
5. records bounded per-block evidence;
6. invokes the fixed model assembler;
7. canonicalizes final output;
8. emits deterministic digests.

There is no iteration, convergence loop, optimizer, event simulation, parallel scheduling, implicit recycle, or automatic recomputation.

---

## 11. Exact bundled runner profile

075 must not widen ordinary caller-selected `calc_v0` imports.

Create one server-known bundled profile whose identity includes:

- entry-point path and SHA-256;
- every process-kernel package file path and SHA-256;
- v2 input-contract canonical bytes and digest;
- flowsheet canonical bytes and digest;
- final assembler identity and digest;
- allowed package/import roots;
- profile schema/version.

Registration is through a dedicated bundled endpoint or equivalent server-owned path. The caller can select inputs and a registered model version but cannot provide:

- Python source or source bytes;
- file paths;
- import roots;
- environment variables;
- working directory;
- package manifest;
- hash-as-authority;
- trust flags;
- assembler identity;
- policy profile.

At job creation and immediately before execution, the runner verifies the complete exact bundled profile. Any missing, replaced, extra, or hash-mismatched file fails closed with `RUNNER_SCRIPT_POLICY_VIOLATION` before subprocess launch.

The implementation must preserve the public bundled-only boundary established by PR #186.

---

## 12. Numerical and canonical identity

### 12.1 Canonical fixtures

For every canonical merged 047 fixture, require equality of:

- normalized canonical inputs;
- every final output key;
- every unit string;
- every numeric value by `float.hex()`;
- diagnostic keys and values;
- status and schema fields;
- canonical `result.json` bytes;
- result digest;
- runner-owned artifact metadata relevant to content identity.

The old and new jobs may have different run IDs, timestamps, paths, and model-version IDs. Those operational identities are excluded from result-content equality.

### 12.2 Intermediate reconciliation

Tests map each merged 047 intermediate equation to a named block scalar or diagnostic. A final-output match alone is insufficient if intermediate responsibility was moved, duplicated, or hidden.

### 12.3 Equivalent-unit cases

For compatible noncanonical units:

- normalize through v2;
- execute the same physical case;
- compare against the 075 canonical-unit equivalent;
- do not require identity with an old 047 request that would have rejected the alternate unit string.

---

## 13. Error taxonomy

Use deterministic structured errors, including:

- `process_quantity_invalid`;
- `process_unit_incompatible`;
- `process_semantic_basis_incompatible`;
- `process_component_unknown`;
- `process_composition_invalid`;
- `process_stream_property_missing`;
- `process_port_unknown`;
- `process_port_kind_mismatch`;
- `process_port_contract_mismatch`;
- `process_input_unconnected`;
- `process_input_multiply_driven`;
- `process_cycle_detected`;
- `process_graph_too_large`;
- `process_block_result_invalid`;
- `process_result_identity_mismatch`;
- existing runner policy errors for bundled-profile denial.

Errors must identify the block/port/variable path without leaking absolute host paths or secrets.

---

## 14. Required tests

### 14.1 Units and bases

- v1 exact-unit behavior unchanged;
- v2 compatible conversion accepted;
- dimension mismatch rejected;
- semantic-basis mismatch rejected;
- domains applied after conversion;
- canonical historical magnitude preserved without unnecessary round-trip conversion;
- non-finite magnitudes rejected.

### 14.2 Components and streams

- molecular and pseudo-component representations remain distinct;
- `CO2/C` registry proof matches the reviewed fixture;
- known composition validates and canonicalizes;
- invalid fractions and unknown components fail;
- unknown composition is represented as `null` and is not converted to pure water;
- a block requiring composition rejects unknown composition;
- 047 blocks accept unknown composition because they declare no component dependency;
- flow consistency and immutable copy behavior are verified.

### 14.3 Graph and ports

- valid 047 graph order is deterministic;
- required material/scalar inputs are connected once;
- `Pipe.dynamic_pressure -> Fitting.dynamic_pressure` is present and required;
- removing that connection fails before any block executes;
- Fitting has no access to Pipe internals outside declared inputs;
- wrong kind/dimension/basis fails;
- duplicate driver fails;
- unknown port fails;
- cycles and graph-size excess fail;
- FLOWSHEET-1 ordering tests remain unchanged and green.

### 14.4 Block behavior

- Reservoir reproduces the legacy volume conversion;
- Pipe reproduces every mapped intermediate;
- friction-correlation label appears only in diagnostics;
- no string appears in scalar outputs;
- Fitting uses the connected dynamic pressure and does not recompute it;
- Pump reproduces loss/head/power equations;
- blocks do not mutate streams or global state.

### 14.5 Runner boundary

- exact bundled multi-file profile registers and runs;
- caller source/path/import/environment/trust fields are rejected;
- a changed entry point fails before launch;
- a changed package file fails before launch;
- an extra unmanifested package file fails if the profile contract requires a closed file set;
- contract/flowsheet/assembler digest mismatch fails;
- denial proves zero subprocess invocation;
- PR #186 boundary tests remain green.

### 14.6 Identity

- side-by-side old/new canonical fixtures match output keys, units, `float.hex()`, diagnostics, bytes, and digest;
- intermediate responsibility mapping is complete;
- equivalent-unit cases are physically equal after canonicalization;
- repeated runs are deterministic in the canonical CI environment;
- no accepted engineering value or MemoryStore record is silently created or promoted.

---

## 15. Acceptance criteria

`AC-075-01` — Existing 047 files, version label, v1 contract, fixtures, and digests remain unchanged.  
`AC-075-02` — Pint is pinned and used only at validation/conversion boundaries.  
`AC-075-03` — Input-contract v2 is additive and v1 behavior remains exact.  
`AC-075-04` — Physical dimensions and semantic bases are independently enforced.  
`AC-075-05` — Component records distinguish molecular species from pseudo-components.  
`AC-075-06` — `MaterialStream` is immutable and can represent unknown composition honestly.  
`AC-075-07` — The 047 compatibility stream does not invent pure-water composition.  
`AC-075-08` — Every block dependency is declared through ports or parameters.  
`AC-075-09` — `Pipe.dynamic_pressure` is explicitly connected to the Fitting.  
`AC-075-10` — Friction correlation and regime labels are diagnostics, never scalar physics.  
`AC-075-11` — The graph is validated and executed once in deterministic topological order.  
`AC-075-12` — FLOWSHEET-1 and PROCESS-KERNEL-1 share one pure ordering utility without sharing domain models.  
`AC-075-13` — The 047 graph is described as an imposed-operating-point computational cut, not a solved recycle.  
`AC-075-14` — The generic executor gains no equation language, optimizer, or solver.  
`AC-075-15` — The final assembler is fixed, bundled, and model-specific.  
`AC-075-16` — The runner verifies an exact multi-file bundled profile at creation and execution.  
`AC-075-17` — Caller-supplied executable authority remains impossible through public runner routes.  
`AC-075-18` — Canonical fixtures match 047 by outputs, units, `float.hex()`, diagnostics, bytes, and digest.  
`AC-075-19` — Equivalent-unit cases are validated separately without altering old 047 request semantics.  
`AC-075-20` — No database migration, automatic promotion, accepted-value mutation, or frontend work is introduced.  
`AC-075-21` — All canonical backend, runner-boundary, FLOWSHEET-1, and BLUECAD proof workflows remain green.  
`AC-075-22` — An independent reviewer adds or approves at least one negative graph/identity test not authored with the implementation.

---

## 16. Implementation sequence

### Definition PR

This PR:

- adds this spec;
- records 075 as `planned`;
- records 045 as cancelled under the current loopback single-user threat model;
- records trigger-gated future isolation work;
- preserves 074 as `in_review` under PR #183;
- does not authorize implementation.

### Promotion PR

A separate maintainer-reviewed change may move 075 from `planned` to `ready` only after:

- this definition is merged;
- #186 remains merged and green;
- #183/074 state is reconciled in the registry;
- review threads are resolved;
- no open PR overlaps the runner, input-contract, FLOWSHEET ordering, or process-kernel target files;
- implementation slices and ownership are explicitly assigned.

### Implementation PR

The implementation PR then moves 075 through `in_progress` and `in_review`, contains runtime/tests only within the approved definition, and must not silently widen scope.

No automatic merge is permitted.

---

## 17. Non-goals

075 does not add:

- steady-state recycle solving;
- nonlinear equation solving;
- dynamic simulation;
- thermodynamic or electrolyte property packages;
- phase equilibrium or flash calculations;
- reaction networks or kinetic integration;
- general-purpose expression languages;
- general network hydraulics;
- pump/system curve intersection;
- equipment sizing or costing beyond existing 047 outputs;
- automatic design defaults;
- accepted Parameter creation or promotion;
- frontend flowsheet editing;
- hostile-code sandboxing;
- caller-authored Python;
- Hermes/MCP execution authority;
- replacement or retirement of 047.

Each requires later evidence and a separate reviewed specification.

---

## 18. Rollback

If the 075 implementation cannot preserve exact canonical identity or the bundled runner boundary:

- disable or remove only the new 075 bundled registration profile;
- preserve existing 047 registrations, jobs, runs, artifacts, and Parameters;
- preserve any failed 075 evidence as historical data;
- do not relax identity checks or restore caller-supplied source to make tests pass;
- return 075 to `planned` or `blocked` with the observed mismatch documented.

---

## 19. Final invariant

> JarvisOS may generalize process abstractions only after the abstractions reproduce an already reviewed calculation without inventing composition, state, dependencies, authority, or numerical behavior.
