# Spec 078 — PBR-MODELING-0: bounded photobioreactor modeling kernel

**Definition status:** planning kernel; registry remains `planned`.

**Depends on:** 043, 047, 048, 049, 071, 075

**Target path:** `docs/specs/078-pbr-modeling-0.md`

---

## 1. Purpose

Define the smallest technically sound boundary for extending JarvisOS from the static BlueRev
screening models in 048 and 049 toward bounded photobioreactor modeling. The candidate capability
covers configurable biological kinetics, light attenuation and light-growth coupling, and CO2/O2
gas-liquid transfer. It does not authorize implementation.

048 imposes productivity and reports biomass, nutrient, gas-equivalent, harvest, energy and
screening-economic quantities. 049 reports dimensionless buoyancy/light-transmittance proxies and
explicitly states that light-growth coupling is not evaluated. Neither model represents dissolved
gases or derives growth from delivered light.

## 2. Current runtime facts that must remain true

Every fact below was re-read against exact baseline
`132856f057c27d2800086912fa1cc926a72056eb` (`master` on 2026-07-29). Exact SHA-pinned file reads
and explicit 404 responses were used. Evidence IDs resolve in
`078-pbr-modeling-source-evidence.md`.

1. 043 CALC-1 owns the bounded bundled `calc_v0` contract, AST policy and deterministic artifacts.
   `RT-42`
2. 047, 048, 049 and 072 are bundled runner examples with sibling v1 contract JSON files. Their
   contracts contain `schema_version`, `evaluation_mode` and typed `variables[]`. `RT-43`
3. 071 owns caller-editable bindings and side-effect-free forward degree-of-freedom inspection.
   `RT-44`
4. 075 exposes `MaterialStream`, `Component`, `COMPONENT_CATALOG`, typed material/scalar ports,
   `UnitOperation`, `BlockResult`, `ProcessFlowsheet`, `Pipe`, `Pump`, `Fitting`, `Reservoir`, the
   047 profile and the semantic-unit registry. `RT-45`
5. `UnitOperation` is a `runtime_checkable Protocol`; blocks conform structurally. `RT-09`
6. Blocks separate `caller_parameters` from `profile_constants`; flowsheet execution requires
   exact and exhaustive name sets. `RT-10`, `RT-46`
7. `ProcessFlowsheet.execute` is one deterministic acyclic forward pass. It has no time state,
   iteration, convergence loop or tear stream. Cycles fail as `topology_cycle`; limits are 64
   blocks and 256 connections. `RT-11`, `RT-12`
8. Scalar connections require exact `unit`, `physical_dimension` and `semantic_basis`; every
   declared inlet must be driven. `RT-13`
9. `process_semantic_units_v1` contains eleven semantic tokens. Conversions across semantic bases
   fail. `RT-01`, `RT-02`
10. Physical dimensions are a closed fifteen-entry whitelist with no substance, photon-flux or
    mass-rate dimension. `RT-03`
11. Stream composition is a catalogue-keyed fraction mapping summing to 1 within `1e-12`; it has
    no absolute concentration or phase split. The catalogue contains water, CO2, O2 and a
    formula-less fixture biomass pseudo-component. `RT-07`, `RT-08`
12. `Pipe` uses `correlation_not_qualified` outside its qualified Reynolds envelope. `RT-14`
13. `BlockResult.diagnostics` is a free-form mapping not validated by the executor. `RT-15`
14. Existing verification has three distinct classes: tolerance tests for algebraic outputs; the
    075 same-machine canonical-047 parity test comparing `float.hex()`, diagnostics, canonical
    JSON bytes and SHA-256; and the 056 exact-digest canary under a pinned platform profile. None
    is an unconditional cross-environment guarantee. `RT-32`, `RT-35`, `RT-37`
15. Runtime requirements include FastAPI, Uvicorn, Pydantic, HTTPX, build123d, PyYAML and Pint,
    but no NumPy, SciPy, SUNDIALS, CasADi or Assimulo. `RT-38`

The supplied draft incorrectly stated that the 075 enforcing test was absent. It exists at
`backend/tests/test_process_kernel_075_identity.py`. That test is a narrow compatibility precedent
for canonical 047 fixtures, not a generic bit-identical tier for future 078 outputs. `RT-34`,
`RT-37`

## 3. Problem boundary

JarvisOS currently cannot derive supported productivity from a geometry/light regime, determine
whether gas transfer meets biological demand, or propagate a design change from light through
growth to harvest. 048 and 049 also expose separate `operating_biomass_concentration` inputs
without enforcing consistency.

## 4. Candidate scope

078 may later define:

1. a bounded typed schema for biological rate laws, including parameter units, meaning, validity
   domain, uncertainty and source;
2. a closed server-bundled rate-law registry with content-hash identity;
3. an incident photosynthetically active radiation quantity;
4. a declared one-dimensional path-averaged irradiance derived from the existing 049 optical
   separation;
5. a light-limited growth relation with respiration;
6. dissolved free CO2 and O2 quantities with one declared Henry-equilibrium convention;
7. externally supplied `kLa` values and explicit validity/source metadata;
8. transfer-sufficiency checks against carbon demand already derivable from 048;
9. carbon and oxygen balance residuals in diagnostics;
10. only the additional semantic units and physical dimensions required by these quantities;
11. new model identities coexisting with 047, 048 and 049.

## 5. Explicit non-goals

No implementation is authorized for kinetics, solvers, expression languages, property packages,
recycle solving, CFD, radiative transfer with scattering/spectral resolution, carbonate chemistry,
pH/alkalinity dynamics, nitrogen quota models, automatic `kLa` estimation, frontend/UI work, CAD,
migrations, dependencies, or changes to runner, egress, sensitivity, provenance, promotion or
MemoryStore authority. 047, 048 and 049 remain byte- and behavior-authoritative.

## 6. Candidate architecture

The default candidate is a small additive set of server-bundled typed blocks and profile records
conforming to the existing 075 protocol. Rate laws are named records, never caller-authored code.
Operating conditions remain 071 bindings; scientific coefficients are immutable profile constants
with source and validity metadata. Dynamic behavior, if later required, must be owned by a full
spec that chooses either an outer bounded integration loop or a separate stateful protocol; the
current `ProcessFlowsheet.execute` contract is not silently changed.

Candidate slices, each requiring a later full specification:

- `S1`: light-response registry plus one-dimensional path-average and respiration;
- `S2`: CO2/O2 equilibrium and linear transfer with externally supplied `kLa`;
- `S3`: bounded time evolution only if a named decision cannot be answered analytically;
- `S4`: one integrated well-mixed PBR vertical slice with carbon/oxygen closure.

No implementation rows for these slices are created by this definition.

## 7. Unresolved decisions

- `U1`: dissolved species as stream concentrations, derived quantities, or scalar ports;
- `U2`: semantic-unit registry extension and versioning for photon/substance/rate dimensions;
- `U3`: whether biomass becomes a real component with elemental fractions;
- `U4`: outer integration loop versus a second stateful protocol;
- `U5`: strain-specific *Nannochloropsis* light-response relation and parameter evidence;
- `U6`: whether any bounded expression AST is ever justified; currently deferred;
- `U7`: transfer-sufficiency result as diagnostic, warning or hard validity rejection;
- `U8`: balance/invariant error-token ownership.

## 8. Failure modes

- unit or semantic-basis confusion;
- double counting physical transfer and biological uptake;
- parameter-name collision across incompatible rate laws;
- extrapolation beyond calibration range;
- unidentifiable or unsourced parameters;
- overstated optical claims;
- mismatch between 049 end-of-cleaning-interval fouling and any growth average;
- semantic-registry or component-catalogue hash drift affecting 047 identity;
- determinism overclaim across environments;
- scope growth into a general process-simulation platform.

## 9. Source and validation requirements

Physics authority is public scientific literature. Vendor documents may establish capabilities,
workflows, expected inputs/outputs and validation practice, but never physical truth. Every future
model must have a named independent oracle: analytic solution, conservation identity, limiting
case, published benchmark or experimental dataset. Professional-software agreement is only a
cross-check.

Candidate analytic oracles include the Beer-Lambert path average, linear-transfer relaxation
`C(t) = C* + (C0 - C*) exp(-kLa t)`, half-time `ln(2)/kLa`, dark-batch respiration and carbon/oxygen
closure. Each future slice must explicitly choose tolerance testing, an exact canonical-parity
fixture with a fixed legacy oracle, or a pinned-platform canary. The 075 canonical-047 proof must
not be generalized.

## 10. Dependencies and non-overlap

078 depends on merged 043, 047, 048, 049, 071 and 075. It does not depend on 072–074 because it
does not own hydraulic topology or CAD linkage. It does not overlap 014 CFD, 013 domain-validator
plugins or 027 modal/thermal analysis. Higher-fidelity geometry-derived `kLa` work belongs to a
later correlation or CFD specification.

## 11. Definition-to-readiness gates

1. Merge this planning-only definition with 078 `planned` and an empty Implementation PR cell.
2. Preserve the pinned-baseline audit and the corrected `RT-37` evidence.
3. Assign every future numerical slice a named oracle and one explicit verification class.
4. Resolve `U1`, `U2`, `U3` and `U5` with recorded evidence.
5. Clear the vendor-manual blocker or explicitly proceed on public literature alone.
6. Replace this kernel with a full per-slice specification.
7. Produce a dated readiness decision naming one implementation branch, one implementation PR,
   owned paths and merge preconditions, then promote in a separate PR.

Promotion beyond `planned` is not authorized by this document.

## 12. Rollback invariant

All future 078 artifacts must be additive and separately removable. Reverting them must restore
unchanged canonical results for every pre-existing model without a migration.

## 13. Definition checks

No runtime tests are added. This definition requires:

- `python scripts/check_spec_status.py --self-test`;
- registry validation for the planned 078 row and merged dependencies;
- exactly the two 078 documents plus `STATUS.md` in the definition PR;
- no runtime, test, dependency, migration, frontend or UI change.

> JarvisOS may claim photobioreactor behavior only for quantities backed by a named check, a stated
> validity domain and traceable parameter evidence. Otherwise the output remains a screening proxy.
