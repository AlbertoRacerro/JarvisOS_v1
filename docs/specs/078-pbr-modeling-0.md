# Spec 078 — PBR-MODELING-0: bounded photobioreactor modeling kernel

**Definition status:** planning kernel; registry remains `planned`.

**Depends on:** 043, 047, 048, 049, 071, 075

**Target path:** `docs/specs/078-pbr-modeling-0.md`

---

## 1. Purpose

Determine the smallest technically sound direction for extending JarvisOS from its existing static
BlueRev biological and optical screening models toward a bounded photobioreactor modeling
capability, covering configurable biological kinetics including *Nannochloropsis*-specific models,
light attenuation and light-growth coupling, CO2 and O2 gas-liquid transfer, and an eventual
integrated validated vertical slice.

078 exists because 048 and 049 answer screening questions and cannot answer design questions. 048
imposes productivity as an input; 049 produces a dimensionless transmittance and declares
`light_growth_coupling_not_evaluated`. Within 048 and 049 nothing relates delivered light to
growth, and nothing represents a dissolved gas.

This document is a planning kernel, not an implementation contract. It fixes the problem, the
boundaries, the candidate architectures and the evidence still required. It deliberately does not
state acceptance criteria for scientific decisions that remain unresolved.

## 2. Current runtime facts that must remain true

Each fact traces to a row in `078-pbr-modeling-source-evidence.md`. Every fact below was
re-read directly against pinned baseline `132856f057c27d2800086912fa1cc926a72056eb` on 2026-07-29. The definition work did not
execute runtime code or make provider calls; source and test files were inspected at that exact
commit. The corrections found by this verification are recorded in the definition pull request.

1. 043 CALC-1 owns the bundled `calc_v0` runner contract, AST policy and deterministic artifacts.
   `RT-42`
2. 047, 048, 049 and 072 are bundled runner examples at
   `backend/app/modules/runner/examples/<name>.py` with a sibling `<name>.contract.json`.
   Contracts are `{schema_version, evaluation_mode, variables[]}`; each variable carries `name`,
   `label`, `unit`, `required`, `category`, `description` and `domain`. `RT-43`
3. 071 owns caller-editable bindings and forward degree-of-freedom inspection. `RT-44`
4. 075 PROCESS-KERNEL-1 provides `MaterialStream`, `Component`, `COMPONENT_CATALOG`,
   `MaterialPort`, `ScalarPort`, `UnitOperation`, `BlockResult`, `ProcessFlowsheet`, the blocks
   `Pipe`, `Pump`, `Fitting` and `Reservoir`, the bundled `profile_047`, and the semantic-unit
   registry. `RT-45`
5. `UnitOperation` is a `runtime_checkable` `Protocol`. A conforming block is added by structural
   conformance without modifying kernel runtime. `RT-09`
6. `UnitOperation` separates `caller_parameters` from `profile_constants`. The flowsheet requires
   its constants mapping to equal exactly the union of all block-declared constant names, and
   requires each block's caller-parameter set to match exactly. `RT-10`, `RT-46`
7. `ProcessFlowsheet.execute` performs one forward pass over a deterministic topological order.
   There is no time variable, no state carried between calls, no iteration, no convergence loop
   and no tear stream. Cycles are rejected as `topology_cycle`. Bounds are
   `MAX_PROCESS_BLOCKS = 64` and `MAX_PROCESS_CONNECTIONS = 256`. `RT-11`, `RT-12`
8. Scalar port connection requires exact equality of `unit`, `physical_dimension` and
   `semantic_basis`, with no conversion at connect time. Every declared inlet must be driven.
   `RT-13`
9. `SEMANTIC_UNIT_REGISTRY_VERSION` is `process_semantic_units_v1` with eleven tokens.
   `semantic_basis` discriminates units sharing a physical dimension, and `normalize_magnitude`
   refuses conversion across bases. `RT-01`, `RT-02`
10. Accepted physical dimensions are a closed fifteen-entry whitelist; anything else raises
    `unit_dimension_unsupported`. The set contains no molar or substance dimension, no photon-flux
    dimension, and no mass-per-time rate dimension. `RT-03`
11. `MaterialStream.composition` holds component *fractions* constrained to sum to 1.0 within
    1e-12 over keys present in `COMPONENT_CATALOG`. There is no representation of an absolute
    concentration and no phase split. `COMPONENT_CATALOG` holds `water`, `carbon_dioxide`,
    `oxygen` and the formula-less pseudo-component `fixture_biomass`. `RT-07`, `RT-08`
12. `Pipe` raises `correlation_not_qualified` outside its qualified Reynolds range. This is the
    house precedent for a validity-envelope gate. `RT-14`
13. `BlockResult.diagnostics` is a free-form mapping the executor does not validate. `RT-15`
14. The 047 bundled-model suite uses `pytest.approx(rel=1e-12, abs=1e-15)` for its ordinary
    numerical oracle. Separately, `backend/tests/test_process_kernel_075_identity.py` enforces the
    canonical-047 identity class within the test runtime by comparing every output value with
    `float.hex()`, canonical `result.json` bytes, and SHA-256. Cross-environment exact-digest
    claims remain confined to an explicitly pinned platform profile such as the 056 canary.
    `RT-32`, `RT-35`, `RT-37`
15. `backend/requirements.txt` declares `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`,
    `build123d`, `PyYAML` and `Pint`. There is no NumPy, SciPy, SUNDIALS, CasADi or Assimulo.
    `RT-38`

075 additionally specifies and tests a bit-identical identity class against canonical 047
fixtures. The enforcing test is `backend/tests/test_process_kernel_075_identity.py`; it covers
laminar and turbulent canonical cases and proves exact values, diagnostics, bytes and digest only
for that defined same-runtime comparison. It is a reusable verification precedent, not an
unconditional cross-platform guarantee and not automatic authority for future 078 outputs.

Any implementation that silently changes these facts is outside 078.

## 3. Problem statement

048 computes nutrient, gas-equivalent, harvest and economic quantities from an imposed
`volumetric_productivity`. `maximum_specific_growth_rate` enters only as the denominator of an
emitted, unenforced plausibility ratio. Its CO2 handling consists of two unreconciled paths: a
stoichiometric carbon demand scaled by 44/12, and a separately asserted `co2_specific_gas_rate`
scaled to a per-minute benchmark. It declares `gas_transfer_not_evaluated`. Dissolved oxygen is
absent; oxygen appears only as a stoichiometric evolution equivalent.

049 computes `T_tube = T_clean · (1 − f_daily)^t_clean`, `τ = a · X · L`, `T_culture = exp(−τ)`
and their product. All four optical outputs are dimensionless and three carry a literal `_proxy`
suffix. No incident irradiance appears in the contract or the computation. The model declares
`spectral_PAR_not_evaluated`, `radial_light_field_not_evaluated`, `scattering_not_evaluated`,
`center_light_not_claimed` and `light_growth_coupling_not_evaluated`. Fouling is evaluated at the
end of the cleaning interval, that is at the dirtiest instant, and is not averaged over the cycle.

The two models share the identically named `operating_biomass_concentration` and are never made
consistent with each other.

Consequently JarvisOS cannot answer: what productivity a given geometry and light regime support;
whether a chosen gas supply meets biological demand; or how a design change propagates from light
through growth to harvest.

## 4. Candidate scope

078 candidate scope includes:

1. a bounded typed schema for biological rate laws carrying units, valid domain, biological
   meaning and per-parameter source;
2. a closed server-bundled registry of rate-law profiles with content-hash identity;
3. an incident photosynthetically active radiation quantity;
4. a declared path-averaged irradiance derived from the existing 049 optical separation;
5. a light-limited growth relation with a respiration term;
6. dissolved-oxygen and free-carbon-dioxide state with a Henry equilibrium relation;
7. an externally supplied volumetric mass-transfer coefficient;
8. an explicit transfer-sufficiency comparison against the biological carbon demand already
   derivable from 048 quantities;
9. elemental balance residuals emitted as diagnostics;
10. the semantic units and physical dimensions required by items 3 to 9;
11. new model identities that coexist with 047, 048 and 049 rather than replacing them.

## 5. Explicit non-goals

078 does not add computational fluid dynamics, finite-element analysis, generic process
simulation, economic analysis beyond the existing 048 boundary, equipment costing, CAD changes, a
general thermodynamic or property package, phase equilibrium beyond a single declared Henry
relation, a frontend flowsheet editor, caller-authored Python, an unrestricted mathematical
expression language, a general expression abstract syntax tree, recycle or nonlinear solving in
the kernel executor, a general adaptive stiff solver platform, carbonate speciation, alkalinity or
pH dynamics, nitrogen limitation or internal-quota kinetics, radiative transfer with scattering or
spectral dependence, automatic estimation of the volumetric mass-transfer coefficient, retirement
or rewriting of 047, 048 or 049, or any change to runner, sensitivity, provenance, promotion or
MemoryStore authority.

## 6. Existing authority that must remain unchanged

- 043 bundled `calc_v0` authority;
- 048 static biomass, nutrient and gas-equivalent evidence;
- 049 optical proxy evidence;
- 071 caller-owned editable bindings and degree-of-freedom inspection;
- 075 typed streams, components, units, ports, blocks, deterministic acyclic execution and
  bundled-profile identity;
- existing runner, sensitivity, provenance, promotion and MemoryStore authority;
- all existing canonical outputs, fixtures and digests.

048 and 049 keep their current runtime paths, identities, outputs and fixtures unchanged. Any
higher-fidelity model takes a new identity and coexists.

## 7. Gaps between 048, 049 and the requested model

`G1` — no absolute light. 049 produces a ratio. Driving a rate law requires an incident PAR
quantity and a declared spatial average. No photon-flux dimension exists in the accepted set.

`G2` — no light-growth coupling in 048 or 049. 049 disclaims it explicitly.

`G3` — productivity is imposed, not derived. 048 takes `volumetric_productivity` as an input and
does not constrain it by `maximum_specific_growth_rate`.

`G4` — no dissolved species. Composition holds fractions summing to one over a four-component
catalogue with no phase split. Biomass at 2 gDW/L or dissolved oxygen at 8 mg/L cannot be
expressed. Whether the fraction basis is mass or mole is not stated in code.

`G5` — no gas transfer. No Henry relation, no volumetric mass-transfer coefficient, no driving
force, no transfer direction. 048's two CO2 paths are never reconciled.

`G6` — no conservation residual. 048 checks only a dry-mass harvest split; 075 checks stream flow
consistency and composition sums.

`G7` — no dynamics. The executor has no time, no state and no iteration, and rejects cycles.

`G8` — no per-parameter provenance in the contract schema. The schema types unit, domain and
category but carries no parameter source and no binding to a model identity, so two incompatible
rate laws could both expose an unqualified `mu_max`.

`G9` — missing dimensions and units. No molar or substance dimension, no photon flux, no
mass-per-time rate dimension. A concentration in mg/L would resolve to the `density` dimension and
collide semantically with fluid density unless given a distinct `semantic_basis`.

## 8. Architecture options

`A1` — separate monolithic PBR calculator: a standalone bundled `calc_v0` model in the runner
examples, in the style of 048, with no kernel involvement.

`A2` — broad general-purpose equation-oriented simulator: a declarative equation system with a
general solver, in the manner of an equation-oriented commercial modeling language.

`A3` — PBR-specific extension over PROCESS-KERNEL-1: new blocks conforming to `UnitOperation`,
new components and semantic units, assembled into a bundled profile alongside `profile_047`.

`A4` — closed library of server-bundled PBR model profiles: a registry of whole named profiles
selected by identifier, mirroring `COMPONENT_CATALOG` and `SEMANTIC_UNITS`.

`A5` — bounded typed rate-law schema with later solver integration: a typed declarative
description of rate laws evaluated by closed bundled code rather than by an expression engine,
with numerical integration deferred to a separate spec.

### Ranking

| Criterion | `A1` | `A2` | `A3` | `A4` | `A5` |
|---|---|---|---|---|---|
| Preservation of current runtime | high | low | high | high | high |
| Scientific validity ceiling | low | high | medium | medium | medium |
| Testability | medium | low | high | high | high |
| Implementation risk | low | very high | medium | low | medium |
| Security | high | very low | high | high | high |
| Provider independence | high | high | high | high | high |
| Local execution cost | low | high | low | low | low |
| Maintenance cost | high | very high | medium | low | medium |
| Extensibility | very low | very high | high | medium | high |
| Rollback isolation | high | very low | medium | high | high |

Provider independence does not discriminate between the options. The discriminating criteria are
security, implementation risk, testability and rollback isolation.

`A2` is rejected. An expression language reachable by callers is functionally equivalent to
caller-authored code, contradicts the 043 AST policy and the 075 closed-vocabulary principle, and
cannot be validated against a bounded set of test oracles. `A1` is rejected as a first choice
because it re-implements stream, unit and port semantics that 075 already owns; it remains the
fallback if kernel extension proves unsafe.

078 proposes the composition `A3` + `A4` + `A5`, under two binding constraints:

1. Declare rate-law coefficients as `profile_constants` and operating conditions as 071 caller
   bindings; the existing split already expresses the required separation.
2. Attach a source to every rate-law parameter and bind it to a model identity, following the
   `Component.scientific_molar_mass_authority` pattern; this is what `G8` requires.

§10 lists the decisions that must close before this direction binds an implementation.

## 9. Likely implementation slices

`S1`–`S4` are a hypothesis, not a delivery commitment. Runtime evidence supersedes this ordering.
Slice names must describe what is computed; a forward evaluation at an imposed biomass
concentration is not a steady-state reactor and must not be named one.

`S1` — light-limited forward screening at imposed state: incident PAR and a declared
path-averaged irradiance derived from the 049 separation; a light-limited specific growth rate,
with photoinhibition if `U5` selects a photoinhibiting form; a respiration term; a derived
productivity comparable against 048's imposed input. Purely algebraic, no new dependency.

`S2` — gas transfer sufficiency: Henry equilibrium, externally supplied volumetric mass-transfer
coefficient, free dissolved CO2 and O2, transfer rate under a single sign convention, and an
explicit sufficiency comparison against the biological carbon demand derivable from
`biomass_carbon_fraction` and productivity. Algebraic or closed-form.

`S3` — batch dynamic growth: time integration of biomass and dissolved species. The simplest cases
have closed-form solutions and a bounded fixed-step integrator requires no dependency; only robust
adaptive integration would.

`S4` — integrated well-mixed PBR vertical slice: light, growth, gas and harvest coupled, with
conservation closure.

Later: nitrogen limitation with an internal quota, lipid and eicosapentaenoic acid dynamics,
plug-flow or tanks-in-series spatial resolution, cycle-averaged fouling.

No implementation rows are added to STATUS.md for these slices by this definition.

## 10. Unresolved decisions

`U1` — whether dissolved species are represented by extending `MaterialStream` with an absolute
concentration mapping, by deriving concentration from an existing fraction and bulk density, or by
carrying them as scalar port quantities outside the stream. The fraction basis, mass or mole, must
be stated explicitly whichever route is taken.

`U2` — whether the semantic-unit registry is extended with photon-flux, substance and rate
dimensions, and whether `process_semantic_units_v1` is superseded. Any extension changes
`semantic_registry_sha256()`.

`U3` — whether biomass is promoted from `fixture_biomass` to a component carrying elemental mass
fractions, and whether that changes `component_catalog_sha256()` in a way that affects merged 047
identity.

`U4` — whether a dynamic model is hosted by an outer loop over `execute()`, which re-validates the
whole flowsheet on every call, or by a second protocol alongside `UnitOperation`. This belongs to
the slice that first needs it.

`U5` — which light-response relation is selected for *Nannochloropsis*, and on what evidence.
Selection requires strain-specific data stating acclimation history, temperature, salinity,
photon-flux range, the measured quantity and parameter uncertainty. Whether the selected form
exhibits photoinhibition is itself part of this decision.

`U6` — whether a bounded rate-law abstract syntax tree is ever justified, and under what trigger.
The current position is deferred, not adopted.

`U7` — whether the `S2` sufficiency check is a diagnostic, a warning, or a hard validity-envelope
rejection in the manner of `correlation_not_qualified`.

`U8` — whether 078 reuses the 048 error token `mass_balance_invalid`, the 049 token
`result_invariant_invalid`, or defines its own, given that the two merged models already differ.

## 11. Source and validation requirements

Every model entering any slice carries at least one named test oracle: an analytic solution, a
conservation identity, a limiting case, a published benchmark, an experimental dataset, or a
cross-check against professional software. A comparison against professional software alone is
never accepted as proof of physical truth; it corroborates capability and workflow only.

Candidate oracles, to be fixed per slice at full-spec time and constrained to quantities the slice
actually models:

- the closed-form path average of a one-dimensional Beer-Lambert profile;
- for a light-response relation exhibiting an interior optimum, the exact location of that optimum
  with monotone decline on both sides;
- relaxation of a linear transfer equation to equilibrium as `C(t) = C* + (C0 − C*)·exp(−kLa·t)`
  with half-time `ln2 / kLa`;
- a closed dark batch declining only by the respiration integral;
- elemental balance closure in carbon and oxygen. Nitrogen closure is not an oracle for `S1`–`S4`,
  which carry no nitrogen state; it arrives with the deferred quota model.

Verification classes reuse the existing house patterns rather than inventing a third. Algebraic
outputs are compared by `pytest.approx` at the tolerances already used for 047. The exact 075
identity test is reusable only where a later full specification can define an authoritative legacy
path and an exact replacement path performing the same arithmetic in the same order. Numerically
integrated outputs are compared by documented tolerance on a pinned environment; exact digest
equality for such outputs is acceptable only under an environment-gated pinned-platform canary
pattern, never as an unconditional cross-platform claim.

Physics authority is public scientific literature. Vendor documentation may establish only
capabilities, workflows, concepts, expected inputs and outputs, validation practice and useful
abstractions. Source evidence is recorded in `078-pbr-modeling-source-evidence.md`.

## 12. Proposed dependency graph

078 depends on 043, 047, 048, 049, 071 and 075. Current status of every dependency is owned by
`docs/specs/STATUS.md` and is not restated here.

078 does not depend on 072, 073 or 074, which concern hydraulic topology and CAD linkage. 078 does
not overlap 014, which owns computational fluid dynamics; 013, which owns the domain-validator
plugin boundary; or 027, which owns modal and thermal analysis. Any future estimation of a
volumetric mass-transfer coefficient from geometry belongs to correlation work or, at higher
fidelity, to 014.

Within 078 the slices depend in order `S1` → `S2` → `S3` → `S4`, with `S3` additionally gated on
`U4` and on any dependency decision required for integration.

## 13. Preliminary failure modes

`F1` — silent unit or basis confusion. Mitigated by `semantic_basis`, which must be assigned
distinctly for every new quantity; a concentration must not resolve to the `density` dimension
without a distinguishing basis.

`F2` — double counting between biological uptake and physical transfer. Biological and physical
terms must be separate additive contributions under one sign convention, with the system boundary
stated and an elemental residual emitted.

`F3` — parameter-name collision between incompatible rate laws. Parameters must be qualified by
model identity and carry a source; an unqualified shared name is rejected.

`F4` — extrapolation outside the calibration domain. Mitigated by a validity envelope in the
manner of `correlation_not_qualified`.

`F5` — parameters adopted without reported identifiability. A rate-law parameter whose source did
not report an identifiable estimate must be labelled, never silently defaulted.

`F6` — overstated optical claims. Any claim requiring scattering, spectral dependence, radial
resolution or full radiative transfer is out of scope and remains blocked. The path-averaged
irradiance is a one-dimensional optical-path average and must be labelled as such.

`F7` — fouling convention mismatch. 049 evaluates transmission at the end of the cleaning
interval. Coupling it to a growth model without adopting that convention explicitly or introducing
cycle averaging would misstate delivered light.

`F8` — kernel identity drift. Extending the semantic-unit registry or the component catalogue
changes their content hashes. Any such change must be shown not to disturb merged 047 canonical
identity.

`F9` — determinism overclaim. Integrated outputs must not be presented as bit-identical across
environments.

`F10` — scope creep into a general platform. Mitigated by the closed registry, the absence of an
expression language, and §5.

## 14. Definition-to-readiness gates

1. Merge this kernel as a definition pull request while the registry row stays `planned` and the
   Implementation PR cell stays empty. The pull request body records the pinned baseline commit
   SHA against which §2 was verified.
2. Re-verify every §2 fact at that pinned SHA and correct any row that has moved.
3. Preserve the resolved `RT-37` finding: the 075 exact-identity test is a precedent limited to
   canonical 047 equivalence and does not by itself authorize an exact tier for a new 078 model.
4. Resolve `U1`, `U2`, `U3` and `U5` with recorded evidence.
5. Fix at least one named test oracle for every model in `S1`.
6. Clear the vendor-corpus blocker recorded in `078-pbr-modeling-source-evidence.md` §2, or record
   that 078 proceeds on literature alone. This is not a blocker on physics, which vendor
   documentation may never establish.
7. Supersede this kernel with a full specification carrying per-slice acceptance criteria.
8. Produce a dated readiness decision `078-readiness-YYYY-MM-DD.md` naming the implementation
   branch, the single implementation pull request, the owned paths and the merge preconditions,
   and promote the row in a separate pull request.

Promotion beyond `planned` is not authorized by this document.

## 15. Rollback principle

Every 078 artifact is additive and separately removable. New blocks, components, semantic units
and profiles carry new identities and do not modify 047, 048, 049 or their fixtures. Reverting the
078 implementation must restore byte-identical canonical results for every pre-existing model
without a migration. If a proposed change cannot satisfy this, it is out of scope for 078 and
belongs to a spec that owns the affected authority.

## 16. Required tests

No tests are added by this definition. The following are required before promotion and are named
here so the full specification inherits them:

- `python scripts/check_spec_status.py --self-test` passes, and the pull-request validation run
  accepts the 078 row;
- every §2 fact is re-verified at the pinned baseline SHA;
- merged 047, 048 and 049 canonical fixtures and digests are unchanged by any 078 artifact;
- `semantic_registry_sha256()` and `component_catalog_sha256()` are unchanged, or their change is
  shown not to disturb merged 047 identity;
- each `S1` model has at least one named oracle from §11 implemented as a test.

## 17. Final invariant

> JarvisOS may claim photobioreactor behavior only for quantities it can verify against an
> independent oracle. A model that produces a number without a named check, a stated validity
> domain, and a traceable parameter source is a screening proxy and must be labelled as one.
