# Spec 075 — PROCESS-KERNEL-1: express 047 as a flowsheet of blocks

**Registry name:** Process kernel — quantities, streams, components, ports, and unit operations  
**Depends on:** 043, 047, 048, 071  
**Implementation precondition:** the bundled-only runner cleanup is merged  
**Status:** draft for independent review  
**Target path:** `docs/specs/075-process-kernel-1.md`

---

## 1. Purpose and method

The current BlueRev process layer consists of reviewed straight-line calculation scripts. The first model, 047, already has a known numerical answer, an immutable nine-variable contract, deterministic `result.json`, and extensive verification cases. It does not have material streams, components, reusable unit operations, or dimensional conversion: its input units are exact strings and its equations are one sequence of float operations.

Do not design a general simulator first.

Take 047 and re-express the same calculation as an explicit graph of blocks connected by typed material and scalar ports. The new path must reproduce the existing script before it is allowed to become a foundation. The abstractions are therefore constrained by a validated case rather than invented in the abstract.

The deliverable is not an Aspen replacement and not a nonlinear solver. It is the smallest reusable process kernel forced into existence by exact reproduction of 047:

- dimensional quantities at boundaries;
- immutable components and material streams;
- declared material and scalar ports;
- four unit-operation blocks;
- deterministic graph validation and straight-line execution;
- one bundled 047 flowsheet implementation whose result is numerically and byte-for-byte reconciled with the current script for canonical fixtures.

The existing `bluerev_geometry_hydraulics_v0.py`, its version label, contract, tests, and digests remain unchanged throughout 075. The new path runs beside it. Retirement or replacement is a later decision.

---

## 2. Runtime facts this definition must preserve

The implementation is grounded in current `master`:

1. 047 accepts exactly nine inputs and performs its canonical conversions in a fixed order:
   - `tube_length` in `m`;
   - inner/outer diameter in `mm`;
   - reservoir volume in `L`;
   - velocity in `m/s`;
   - density in `kg/m3`;
   - viscosity in `Pa*s`;
   - dimensionless minor-loss coefficient and pump efficiency.
2. The current 071 input-contract schema is version 1 and compares unit strings exactly. A compatible alternative unit such as `in` or `cm` is currently invalid.
3. The current `calc_v0` AST profile permits only a small standard-library import set. A reusable Pint-backed kernel cannot be reached by silently importing application modules from an ordinary generic script.
4. The current FLOWSHEET-1 topological ordering is a deterministic private implementation coupled to provenance graph models.
5. 047 represents a physical closed recirculating loop at an imposed velocity, but its calculation is acyclic. 075 must represent this honestly as a computational cut at the asserted operating point, not claim that it has solved the recycle.

Any implementation that ignores one of these facts and creates a parallel hidden mechanism has failed the definition.

---

## 3. Scope

075 includes:

1. a project quantity/unit boundary based on a pinned Pint runtime dependency;
2. additive version-2 model-input-contract support for dimensional conversion, while version 1 remains byte- and behavior-compatible;
3. an immutable component registry sufficient for the 047 stream and the first verified stoichiometric fixture from 048;
4. an immutable `MaterialStream`;
5. typed material and scalar port contracts;
6. a `UnitOperation` contract;
7. four concrete blocks: `Reservoir`, `Pipe`, `Fitting`, `Pump`;
8. an immutable `ProcessFlowsheet`;
9. a deterministic acyclic executor;
10. extraction of one shared pure topological-order utility reused by FLOWSHEET-1 and PROCESS-KERNEL-1;
11. an exact bundled multi-file `calc_v0` profile containing the entry point and process-kernel package;
12. side-by-side execution against the merged 047 script.

No canonical database migration is required. `parameters.value TEXT`, accepted Parameter authority, simulation runs, runner jobs, artifacts, proposals, and 071 forward-DOF semantics remain authoritative.

---

## 4. Quantity and unit boundary

### 4.1 Pint is a boundary validator and converter

Pin Pint in `backend/requirements.txt`.

Pint is used only to:

- parse a submitted unit;
- verify dimensional compatibility;
- verify optional semantic basis;
- convert a finite numeric magnitude into the variable's canonical execution unit;
- render deterministic dimensional errors.

Block equations operate on plain Python floats. No Pint quantity enters a block's arithmetic loop, block result, graph ordering, JSON result, or digest input.

### 4.2 Physical dimension and semantic basis are separate

Domain labels such as `gDW`, `mgN`, `mgP`, `gC`, and `mLCO2` carry two meanings:

- a physical dimension, such as mass or volume;
- a semantic basis, such as dry biomass, nitrogen, phosphorus, carbon, or carbon dioxide.

Do not create mutually incompatible pseudo-physics dimensions that prevent `gDW ↔ kgDW` conversion. Define the physical units as aliases of real physical units and preserve the semantic basis in the variable/port contract.

Examples:

| Unit | Physical dimension | Basis |
|---|---|---|
| `gDW` | mass | `dry_biomass` |
| `kgDW` | mass | `dry_biomass` |
| `mgN` | mass | `nitrogen` |
| `mgP` | mass | `phosphorus` |
| `gC` | mass | `carbon` |
| `mLCO2` | volume | `carbon_dioxide` |
| `EUR` | currency | `EUR` |

A value with the right physical dimension but a conflicting declared basis fails. `mgN` is not silently accepted for a phosphorus field merely because both are mass.

### 4.3 Contract schema version 2

Extend `ModelInputContract` additively:

- schema version 1 retains exact-unit-string behavior;
- schema version 2 adds, per variable:
  - `unit`: canonical execution unit;
  - `dimension`: canonical dimensional identifier;
  - optional `basis`;
  - the existing category, description, required flag, and canonical-unit domain.

For version 2 bindings:

1. parse and validate the submitted unit;
2. require matching physical dimension;
3. require matching semantic basis where declared;
4. convert the magnitude to the canonical execution unit;
5. apply the domain after conversion;
6. compare Parameter-backed values after both are converted to the same canonical unit;
7. emit the normalized input set in the canonical unit.

The v1 047 contract and all existing 071 tests remain unchanged. The 075 implementation uses a new v2 contract.

### 4.4 Numerical-identity rule for canonical fixtures

The canonical execution units for 075's 047 contract remain the historical units listed in §2, not a newly homogenized all-SI API. This permits the blocks to perform the same explicit conversions in the same order as the current script:

- diameter `/ 1000.0`;
- reservoir volume `/ 1000.0`;
- all subsequent operations in the current order.

For a binding already submitted in its canonical historical unit, the boundary does not multiply by a conversion factor and then round it back. It preserves the finite float magnitude and the block performs the legacy conversion.

Alternative compatible units are accepted and normalized, but bit identity against the old script is required only for the canonical historical fixtures. Equivalent-unit tests compare the converted 075 result against the same physical case supplied in canonical 075 units.

---

## 5. Component registry

### 5.1 Contract

A component is immutable and server-bundled:

```text
Component:
    id
    name
    phase_hint
    molar_mass_kg_per_mol | null
    molecular_formula{element: stoichiometric_count} | null
    elemental_mass_fractions{element: fraction} | null
```

A molecular species uses a formula and a molar mass derived from one immutable atomic-weight table.

A pseudo-component such as biomass uses elemental mass fractions and has no invented molecular formula or molar mass.

The two representations are not conflated.

### 5.2 Initial catalog

075 includes only what is required for a real test seam:

- water;
- carbon dioxide;
- oxygen;
- a biomass pseudo-component with an explicitly fixture-owned elemental composition.

The biomass composition is not promoted as a universal or accepted BlueRev design value. It is test/catalog evidence only until bound by a later reviewed biological model.

### 5.3 Stoichiometric proof

The registry must compute the `CO2/C` mass ratio currently written as `44.0 / 12.0` in 048 from the atomic/component records.

075 does not modify the 048 script. This test proves that the registry can replace one reviewed literal when a later port is authorized.

---

## 6. MaterialStream

### 6.1 Contract

```text
MaterialStream:
    id
    composition{component_id: mass_fraction}
    density_kg_m3
    dynamic_viscosity_Pa_s
    mass_flow_kg_s | null
    volumetric_flow_m3_s | null
    temperature_K | null
    pressure_Pa | null
```

Rules:

- the object is immutable;
- composition is non-empty, finite, nonnegative, and sums to one within a fixed declared tolerance;
- component IDs must exist in the bundled registry;
- density and viscosity are positive finite supplied properties;
- temperature and pressure may be unknown because 047 does not supply or use them;
- mass and volumetric flow may initially be unknown;
- if one flow and density are known, the other may be derived;
- if both flows are supplied, their consistency is validated;
- a block returns a new stream rather than mutating the input.

Density and viscosity are supplied stream properties in 075. They are not called “derived” and no property package is implied.

### 6.2 047 inlet stream

The 047 flowsheet has one external material input:

```text
loop_liquid:
    composition = {water: 1.0}
    density = liquid_density
    viscosity = dynamic_viscosity
    temperature = unknown
    pressure = unknown
    mass_flow = unknown
    volumetric_flow = unknown
```

The Pipe derives the operating flow from target velocity and hydraulic area, exactly as the script does today.

---

## 7. Ports and UnitOperation

### 7.1 Port kinds

A port is one of:

- `material`;
- `scalar`.

A material port declares:

- required stream properties;
- optional phase hint;
- optional allowed/required component constraints.

A scalar port declares:

- canonical unit;
- physical dimension;
- optional semantic basis.

Connection compatibility is checked on these contracts before execution. A material connection is not reduced to one “dimension”.

### 7.2 UnitOperation contract

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

`BlockResult` contains immutable material outputs, scalar outputs, and bounded diagnostics.

A block declares every port and parameter. It cannot discover new ports at runtime. Missing required connections, extra connections, wrong port kinds, incompatible dimensions/bases, and duplicate drivers fail during flowsheet validation before any block executes.

---

## 8. Exact 047 decomposition

### 8.1 Computational graph

The material path is:

```text
external loop_liquid
    -> Reservoir
    -> Pipe
    -> Fitting
    -> Pump
```

There are also scalar connections:

```text
Pipe.major_pressure_loss   -> Pump.major_pressure_loss
Fitting.minor_pressure_loss -> Pump.minor_pressure_loss
```

This is an acyclic computational cut through a physical recirculating loop. `target_liquid_velocity` is the imposed operating-point specification that closes the M0 arithmetic. 075 does not claim to solve the physical recycle or the pump/system intersection.

The physical tear is closed and solved only in a later reviewed spec.

### 8.2 Complete mapping of the nine inputs

| 047 input | 075 authority |
|---|---|
| `tube_length` | Pipe parameter |
| `tube_inner_diameter` | Pipe parameter |
| `tube_outer_diameter` | Pipe parameter |
| `reservoir_liquid_volume` | Reservoir parameter |
| `target_liquid_velocity` | Pipe operating specification |
| `liquid_density` | external stream property |
| `dynamic_viscosity` | external stream property |
| `minor_loss_coefficient` | Fitting parameter |
| `pump_efficiency` | Pump parameter |

No hidden default supplies an omitted input.

### 8.3 Reservoir

Material behavior: pass the inlet stream through unchanged.

Parameter:

- `reservoir_liquid_volume`.

Scalar output:

- `reservoir_liquid_volume_m3`, computed with the same `/ 1000.0` operation used by 047.

### 8.4 Pipe

Material behavior:

- consume density and viscosity from the inlet stream;
- derive hydraulic area;
- derive volumetric flow from target velocity and area;
- derive mass flow from density and volumetric flow;
- emit a new outlet stream carrying those flows.

Parameters:

- tube length;
- inner diameter;
- outer diameter;
- target liquid velocity.

Scalar results, in legacy operation order:

- hydraulic cross-sectional area;
- tube liquid volume;
- external illuminated-area proxy;
- internal wetted-area-to-volume;
- external-area-to-volume proxy;
- circulation flow;
- nominal tube transit time;
- Reynolds number;
- Darcy friction factor;
- friction-correlation label;
- dynamic pressure;
- major pressure loss.

The current laminar and Blasius behavior, transition rejection, upper validity bound, absence of roughness, and Darcy convention remain unchanged.

### 8.5 Fitting

Material behavior: pass the Pipe outlet stream through unchanged.

Parameter:

- minor-loss coefficient.

Scalar output:

- minor pressure loss, using the same dynamic-pressure basis and operation order as 047.

### 8.6 Pump

Material inputs:

- Fitting outlet stream.

Scalar inputs:

- Pipe major pressure loss;
- Fitting minor pressure loss.

Parameter:

- pump efficiency.

Scalar results, in legacy operation order:

- total pressure loss;
- equivalent static head;
- hydraulic power;
- pump electric power.

No pump curve, NPSH, transient pressure, or absolute discharge pressure is inferred.

### 8.7 Model-specific result assembly

The generic executor does not acquire a general equation/expression language.

One bundled 047 result assembler reads the validated block results and computes, in exact legacy order:

- total liquid inventory = tube volume + reservoir volume;
- total inventory turnover time = total inventory / circulation flow;
- the exact output dictionary and exact diagnostic dictionary currently emitted by 047.

This assembler is part of the bundled 075 model, not a generic process-kernel feature.

---

## 9. Flowsheet and deterministic execution

### 9.1 ProcessFlowsheet

An immutable flowsheet contains:

- stable block IDs;
- block instances;
- material connections;
- scalar connections;
- external material/scalar inputs;
- declared result assembler;
- schema/version identity.

The validator proves:

- unique block and port identities;
- every required input connected exactly once;
- no unknown connection;
- material/scalar kind compatibility;
- dimensional and semantic-basis compatibility;
- no cycle;
- bounded graph size;
- deterministic canonical representation.

### 9.2 Shared topological-order utility

Do not import or repurpose the private `_topological_projection` function directly.

Extract its pure deterministic ordering behavior into one generic utility that accepts stable node IDs and directed edges. Preserve the existing heap/lexicographic tie-break behavior and cycle evidence.

Then:

- FLOWSHEET-1 calls the shared utility for provenance dependency projection;
- PROCESS-KERNEL-1 calls the same utility for block and scalar/material dependency edges.

Existing FLOWSHEET-1 tests must remain unchanged and green. There is one algorithm, not two process/provenance implementations coupled through each other's domain models.

### 9.3 Execution

Execution follows the validated deterministic topological order.

There is:

- no iteration;
- no residual vector;
- no convergence tolerance;
- no tear selection;
- no automatic recomputation;
- no background worker;
- no parallel block execution.

Each block executes once.

---

## 10. Runner integration

### 10.1 No new implementation kind

The implementation remains `calc_v0`.

075 adds one exact bundled profile, not a caller-selectable generic capability.

### 10.2 Bundled multi-file profile

The reusable kernel cannot be hidden inside one monolithic script, and the current generic `calc_v0` script import policy cannot silently import arbitrary application modules.

Create one server-known bundled package containing:

- a thin 047 flowsheet entry point;
- the process-kernel package;
- the immutable unit definitions;
- the component catalog;
- the v2 input contract;
- a canonical bundle manifest binding every file and SHA-256.

Bundled registration copies or materializes the exact package as one reviewed implementation artifact. Execution uses the existing runner job/run/artifact lifecycle.

The profile permits only the exact imports required by this package, including Pint. Generic `calc_v0` remains on its current closed standard-library profile.

No caller may upload support modules, choose the bundle profile, extend the import list, or change the manifest.

### 10.3 No new HTTP product surface

Reuse:

- existing bundled registration conventions;
- existing binding/DOF preview;
- existing runner-job creation and execution;
- existing simulation-run and artifact routes;
- existing MemoryStore proposal behavior.

A small idempotent bundled-registration endpoint may be added only if the existing bundled-registration service requires it. There is no process-simulator API, mutable flowsheet table, or second job system.

---

## 11. Numerical identity contract

### AC-075-01 — Canonical numerical identity

For every existing 047 canonical fixture and verification case:

- every output key is identical;
- every unit string is identical;
- every float has the same `float.hex()` representation;
- every diagnostic field and value is identical;
- canonical `result.json` bytes and SHA-256 are identical.

The new implementation may organize operations into blocks, but it must preserve the legacy float operation sequence where sequence affects rounding.

### AC-075-02 — Existing 047 evidence unchanged

All existing 047 and 071 conformance, deterministic-artifact, domain, laminar, and metamorphic tests pass without modification.

### AC-075-03 — Side-by-side authority

Tests execute both:

- the merged `bluerev_geometry_hydraulics_v0.py`;
- the new bundled 075 flowsheet profile.

The comparison is over real runner executions, not direct calls to duplicated helper functions.

### AC-075-04 — Compatible-unit conversion

A dimensionally compatible alternative unit is accepted by the v2 contract and normalized. A physically wrong dimension or wrong semantic basis fails with an error naming:

- field;
- expected dimension;
- expected basis where present;
- received unit/dimension/basis.

Version-1 contracts retain exact-unit rejection.

### AC-075-05 — Reusable independent blocks

Two Pipe instances with different stable IDs and different lengths execute in one flowsheet without shared mutable state, and each produces the correct independent outputs.

### AC-075-06 — Connectivity validation

Before any solve call:

- an unconnected required material port fails;
- an unconnected required scalar port fails;
- a scalar dimensional mismatch fails;
- a material property-contract mismatch fails;
- a material-to-scalar connection fails;
- a cycle fails.

### AC-075-07 — Deterministic order

A graph with multiple valid topological orders always selects the same lexicographic order, and FLOWSHEET-1 retains its current deterministic order.

### AC-075-08 — Component-derived stoichiometry

The component/atomic registry derives the exact `CO2/C` mass ratio represented by `44.0 / 12.0` in 048 without changing the 048 production script.

### AC-075-09 — Honest operating-point semantics

Internal execution evidence records that 075 is an acyclic computational cut at an imposed target velocity. It does not claim recycle convergence, pump/system intersection, or a solved closed-loop operating point.

This evidence is additional implementation metadata; it must not alter the canonical 047 result bytes required by AC-075-01.

### AC-075-10 — No second authority surface

No new mutable flowsheet database, solver ledger, result store, parameter store, artifact system, or promotion path is introduced.

---

## 12. Required tests

In addition to the unchanged existing suites:

1. real runner: 075 flowsheet versus 047 script for every current canonical fixture, key/unit/`float.hex()`/diagnostics/result-bytes comparison;
2. v1 contract still rejects a compatible but non-exact unit;
3. v2 contract accepts compatible units and normalizes them;
4. v2 dimensional and semantic-basis failures;
5. Parameter-backed v2 comparison after conversion;
6. two independent Pipe instances;
7. missing material port;
8. missing scalar port;
9. material/scalar kind mismatch;
10. scalar dimension mismatch;
11. material property-contract mismatch;
12. deterministic multi-order graph;
13. cycle detection and evidence;
14. existing FLOWSHEET-1 ordering regression;
15. component-derived `CO2/C` mass ratio;
16. exact bundle-manifest and source digest;
17. generic `calc_v0` cannot select or imitate the bundled process-kernel profile;
18. zero AI/provider calls and unchanged MemoryStore proposal semantics.

All tests live under `backend/tests/`, are collected and linted by canonical CI, and make no network call.

---

## 13. Explicit non-goals

075 does not add:

- recycle tearing or convergence;
- nonlinear, linear, or network solving;
- unequal parallel branches;
- a pump curve or system-curve intersection;
- roughness or a new friction correlation;
- a property package;
- phase equilibrium;
- energy balances;
- reactions;
- a generic expression engine;
- equation-count DOF analysis;
- optimization, sensitivity, or case studies;
- mutable persisted flowsheets;
- automatic recomputation;
- frontend work;
- changes to 047, 048, 049, or 072 production scripts;
- a new runner implementation kind;
- a claim that the physical loop has been solved.

---

## 14. What this unlocks

A later solver spec may replace the imposed operating-point cut with an explicit tear, close the recirculation, and solve the pump/system operating point. It must first reduce to 047/075 exactly before adding unequal branches or broader network behavior.

A later photobioreactor block may consume geometry, optical-path, transmittance, and constitutive-model bindings through these same typed ports.

Immediately after 075, a thin canvas can edit a real object—blocks, ports, connections, and externally bound values—without waiting for a nonlinear solver. That UI is a separate reviewed slice and cannot mutate accepted engineering state silently.

---

## 15. Definition and implementation lifecycle

### Definition PR

The definition PR:

- adds this document;
- adds 075 to `STATUS.md` as `planned`;
- may reprioritize drafting order according to maintainer direction;
- changes no runtime or dependency.

### Promotion

After exact-head review resolves the contracts above, a separate narrow registry PR may move 075 from `planned` to `ready`.

### Implementation

The implementation may be delivered in three reviewable checkpoints inside one implementation PR or a stacked chain:

1. quantity/contract/component/stream/port kernel;
2. graph/block execution and exact runner bundle;
3. full side-by-side identity and integration gates.

075 remains incomplete until all acceptance criteria merge. Existing 047 stays authoritative throughout.

---

## 16. Stop conditions

Stop and report rather than guess if:

- a canonical 047 output cannot be reproduced bit-for-bit and the exact operation-order difference cannot be identified;
- an existing 047 or 071 test would need to be weakened or rewritten;
- version-2 unit conversion cannot coexist with exact version-1 behavior;
- a MaterialStream would require invented temperature, pressure, composition, or property-package output;
- a block needs an undeclared hidden input;
- Pump power cannot be derived through declared stream/scalar connections;
- the process-kernel package cannot execute through a bounded exact bundled `calc_v0` profile without opening generic imports;
- the shared topological-order extraction changes FLOWSHEET-1 behavior;
- component stoichiometry requires an invented biomass molar mass;
- implementing 075 would require a recycle solver, expression engine, mutable flowsheet persistence, or new runner kind.

No stop condition may be resolved by embedding a product value, silently changing a unit, copying the old script wholesale into a “block”, or relaxing numerical identity.
