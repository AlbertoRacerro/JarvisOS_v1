# Spec 078 — PBR-MODELING-0 full specification

**Status:** complete documentation contract; registry remains `planned`.

**Depends on:** 043, 047, 048, 049, 071, 075.

**Supersedes for implementation decisions:** unresolved items `RT-37`, `U1`, `U2`, `U3`, `U5`, and literature gates `LIT-01` through `LIT-07` in `078-pbr-modeling-0.md` and its evidence companion.

**Authority boundary:** this pull request is documentation-only. It authorizes no runtime code, migration, dependency, workflow, frontend, provider call, spend, implementation branch, or implementation pull request.

---

## 1. Purpose

078 defines the smallest bounded step from merged static BlueRev screening models toward photobioreactor calculations that connect:

1. incident photosynthetically active radiation to one declared optical-path average;
2. that average to one source-bound light-response law;
3. net biomass production to carbon-dioxide demand;
4. externally characterized gas transfer to CO2 supply and O2 removal sufficiency.

The first implementation is a closed set of deterministic algebraic forward models. It is not a dynamic reactor, generic process simulator, equation-oriented language, CFD model, carbonate/pH model, property package, inverse solver, optimizer, or automatic `kLa` estimator.

## 2. Existing authority preserved unchanged

The implementation must preserve all merged contracts, files, numerical fixtures, canonical JSON bytes, and digests owned by 043, 047, 048, 049, 071, and 075.

In particular:

- 048 remains the authority for its static biomass, nutrient, harvest, gas-equivalent, energy, and economic screening outputs.
- 049 remains the authority for its tube/culture transmission proxies and existing disclaimers.
- 071 remains the authority for editable caller bindings and forward degree-of-freedom inspection.
- 075 remains the authority for typed ports, streams, components, units, acyclic execution, and canonical 047 identity.
- `MaterialStream.composition`, `COMPONENT_CATALOG`, `fixture_biomass`, `process_semantic_units_v1`, and every pre-078 profile remain byte-for-byte unchanged.

Every 078 model has a new identity and coexists with 047, 048, and 049. No existing model is rewritten or silently upgraded.

## 3. Closed architecture

### 3.1 Model registry

078 adds a closed server-bundled registry. A caller selects a known profile identifier but cannot submit equations, Python, expressions, arbitrary parameter names, or a custom model definition.

Each profile record must contain:

- `profile_id` and `profile_version`;
- exact model identities used by the profile;
- content hash over canonical profile metadata and constants;
- organism, strain, culture mode, medium/salinity, temperature, acclimation and measurement context;
- every constant with unit, semantic basis, source locator, applicable range, uncertainty when reported, and transformation history;
- an explicit operational state: `verification_only` or `operational`.

A profile is `operational` only when all constants needed by the selected models have primary-source or approved experimental authority and compatible validity envelopes. Missing evidence is never replaced by a default.

### 3.2 Initial model identities

The first bounded implementation consists of four independently removable algebraic models:

1. `pbr_optical_path_average_v0`;
2. `pbr_light_growth_bernard_remond_v0`;
3. `pbr_co2_transfer_sufficiency_v0`;
4. `pbr_o2_stripping_sufficiency_v0`.

They may be assembled in a bundled profile, but each model retains its own inputs, outputs, diagnostics, validity envelope, and tests.

## 4. Decision closures

### 4.1 `RT-37` — identity and numerical verification

The exact 075 identity test is limited to canonical 047 equivalence in the same runtime. It does not grant an exact-digest class to new 078 calculations.

078 uses three distinct verification classes:

- **structural identity:** exact model/profile identifiers, canonical metadata, input/output keys, units, semantic bases, source records, and content hashes;
- **algebraic numerical tolerance:** `pytest.approx(rel=1e-12, abs=1e-15)` unless an individual oracle defines a tighter bound;
- **pinned-platform digest:** prohibited for normal acceptance and permitted only in a future explicitly environment-gated canary.

Cross-platform bit identity for floating-point outputs must not be claimed.

### 4.2 `U1` — dissolved-gas representation

Dissolved free CO2 and O2 are absolute scalar liquid-phase molar concentrations outside `MaterialStream.composition`.

Canonical quantities:

- `dissolved_co2_concentration`, unit `mol/m3`, semantic basis `dissolved_free_co2_liquid`;
- `dissolved_o2_concentration`, unit `mol/m3`, semantic basis `dissolved_o2_liquid`;
- corresponding equilibrium concentrations with separate semantic bases.

They are not component fractions, do not participate in the stream composition sum, and do not imply carbonate speciation or a phase-equilibrium package.

### 4.3 `U2` — semantic units

078 requires an additive registry version `process_semantic_units_v2`. Version 1 remains immutable and all existing profiles stay bound to it.

The v2 contract adds only the dimensions and reviewed tokens required by the four models:

- photon-flux density: `umol_photons/m2/s`;
- amount concentration: `mol/m3`;
- inverse time: `1/s` and `1/d`;
- dry-biomass concentration: `kgDW/m3` and `gDW/L`;
- dry-biomass volumetric productivity: `kgDW/m3/s` and `gDW/L/d`;
- molar volumetric rate: `mol/m3/s`.

Every token must resolve to a distinct declared semantic basis where physical dimensions alone are ambiguous. V2 is additive, has its own canonical hash, requires no database migration, and must not change the v1 payload or digest.

### 4.4 `U3` — biomass authority

078 does not modify `COMPONENT_CATALOG` or promote `fixture_biomass` into a universal scientific component.

Biomass concentration is a scalar operating quantity. Carbon mass fraction, photosynthetic quotient, respiration rate, and any other composition-dependent property are profile constants bound to organism, strain, conditions, source, and validity envelope.

No universal *Nannochloropsis* composition is asserted. A profile lacking an authoritative carbon fraction cannot compute gas-demand sufficiency and must return `not_computable` rather than substitute a value.

### 4.5 `U5` — light-response relation

The selected mathematical identity is the optimum-shaped Bernard–Rémond light-response form:

```text
mu_gross(I) = mu_max * I
              / (I + (mu_max / alpha) * (I / I_opt - 1)^2)
```

with:

- `I >= 0`;
- `mu_max > 0`;
- `alpha > 0`;
- `I_opt > 0`.

Net specific growth is:

```text
mu_net = mu_gross(I_path_avg) - respiration_rate
```

The formula is selected as a bounded, differentiable identity with an explicit interior optimum and analytic limiting cases. It is not declared universally correct for *Nannochloropsis*.

`mu_max`, `alpha`, `I_opt`, and `respiration_rate` are mandatory server-owned profile constants. They may not be translated from another strain, temperature, salinity, acclimation state, spectral regime, or measured response without an explicit reviewed transformation and uncertainty statement.

## 5. Optical-path model

### 5.1 Inputs

Caller inputs:

- `incident_par`, `umol_photons/m2/s`, `>= 0`;
- `tube_clean_transmittance`, dimensionless, `[0, 1]`;
- `fouling_transmittance_factor`, dimensionless, `[0, 1]`;
- `biomass_concentration`, `kgDW/m3`, `>= 0`;
- `optical_path_length`, `m`, `>= 0`.

Profile constant:

- `biomass_extinction_coefficient`, `m2/kgDW`, `>= 0`, with source and envelope.

The caller must explicitly select the fouling convention. Reuse of 049's end-of-cleaning-interval value must be labelled `end_interval`; a cycle average requires a separate future model and cannot be inferred.

### 5.2 Formula

```text
I_wall = incident_par
         * tube_clean_transmittance
         * fouling_transmittance_factor

tau = biomass_extinction_coefficient
      * biomass_concentration
      * optical_path_length

I_path_avg = I_wall * (-expm1(-tau) / tau)   for tau > 0
I_path_avg = I_wall                           for tau = 0
```

`expm1` is required to avoid cancellation near zero.

### 5.3 Claims and non-claims

The output is a one-dimensional Beer–Lambert-like path-average proxy. It does not claim:

- a radial or angular light field;
- direct/diffuse decomposition;
- scattering;
- spectral resolution;
- self-consistent pigment acclimation;
- a quantified error against radiative transfer.

Those claims remain outside 078.

## 6. Light-growth model

### 6.1 Inputs and outputs

Caller inputs:

- `path_average_par` from the optical model or a caller-supplied measured value;
- `biomass_concentration`.

Profile constants:

- `mu_max`;
- `alpha`;
- `I_opt`;
- `respiration_rate`;
- the complete calibration envelope.

Outputs:

- `gross_specific_growth_rate`;
- `net_specific_growth_rate`;
- `derived_biomass_productivity = mu_net * biomass_concentration`;
- `growth_status`: `net_growth`, `zero_net_growth`, or `net_biomass_decline`.

A negative net rate is a valid physical screening outcome, not an exception.

## 7. CO2 transfer sufficiency

### 7.1 Required quantities

Caller inputs:

- `dissolved_co2_concentration`;
- `co2_equilibrium_concentration`;
- `kla_co2`;
- net biomass productivity, either produced by the selected 078 growth model or supplied with explicit provenance.

Profile constants:

- `biomass_carbon_mass_fraction`;
- carbon molar mass authority.

Equilibrium concentration is caller/profile supplied with temperature, salinity, gas composition, pressure/fugacity convention, source, and calculation provenance. 078 does not calculate it from pH, alkalinity, total inorganic carbon, or a generic Henry-law package.

### 7.2 Sign convention and formula

Positive transfer is into the liquid:

```text
r_co2_transfer = kla_co2
                 * (co2_equilibrium_concentration
                    - dissolved_co2_concentration)

r_co2_demand = max(derived_biomass_productivity, 0)
               * biomass_carbon_mass_fraction
               / molar_mass_carbon

co2_margin = r_co2_transfer - r_co2_demand
```

When `r_co2_demand > 0`:

```text
co2_supply_ratio = r_co2_transfer / r_co2_demand
```

Otherwise the ratio is `not_computable`, while the signed rates and margin remain available.

`co2_status` is `sufficient` when the margin is non-negative and `insufficient` otherwise. Insufficiency is a diagnostic engineering result, not a hard execution failure.

## 8. O2 stripping sufficiency

Caller inputs:

- `dissolved_o2_concentration`;
- `o2_equilibrium_concentration`;
- `kla_o2`;
- carbon-demand rate from §7.

Profile constant:

- `photosynthetic_quotient`, mol O2 generated per mol C fixed, with source and envelope.

The same positive-into-liquid convention applies:

```text
r_o2_transfer = kla_o2
                * (o2_equilibrium_concentration
                   - dissolved_o2_concentration)

r_o2_generation = photosynthetic_quotient * r_co2_demand

o2_stripping_capacity = max(0, -r_o2_transfer)

o2_stripping_margin = o2_stripping_capacity - r_o2_generation
```

The result is `sufficient`, `insufficient`, or `not_computable`.

`kla_co2` and `kla_o2` are distinct quantities. A shared value is forbidden unless a source and reviewed transformation explicitly justify it.

This model does not claim a complete elemental oxygen balance: water, nutrients, photorespiration products, and detailed biomass composition are outside its system boundary.

## 9. Validity envelopes and provenance

Every operational profile must fail closed before arithmetic if any required operating value lies outside the intersection of the source envelopes for the selected constants.

At minimum, the profile records and validates when applicable:

- organism and strain;
- batch/continuous/turbidostat context;
- temperature range;
- salinity or medium;
- pH range when reported by the source, without modelling pH;
- incident-light range and spectral basis;
- biomass-concentration range;
- acclimation regime;
- gas composition and pressure basis;
- reactor type and scale for `kLa`;
- measurement method;
- parameter uncertainty or `not_reported`.

Interpolation within a source envelope may be allowed only when the profile defines it. Extrapolation raises `pbr_validity_envelope_exceeded`.

## 10. Diagnostics and failure semantics

Hard failures:

- `pbr_profile_unknown`;
- `pbr_profile_not_operational`;
- `pbr_input_invalid`;
- `pbr_unit_or_basis_mismatch`;
- `pbr_validity_envelope_exceeded`;
- `pbr_result_invariant_invalid`.

Non-failing result states:

- `sufficient`;
- `insufficient`;
- `not_computable` with a machine-readable reason;
- `net_biomass_decline`.

Diagnostics must include model/profile identities and hashes, source IDs, active envelopes, fouling convention, sign convention, every withheld claim, and residuals or margins used for classification.

NaN and infinity are prohibited. All outputs must carry explicit units and semantic bases.

## 11. Acceptance tests

### 11.1 Preservation gates

- Existing 047, 048, 049, 071, and 075 tests remain unchanged and green.
- Existing canonical fixture values, `float.hex()` values, JSON bytes, script/profile hashes, and result digests remain unchanged.
- `process_semantic_units_v1` and the component-catalog payload/digest remain unchanged.

### 11.2 Optical oracles

- `tau = 0` gives `I_path_avg = I_wall` exactly through the defined branch.
- For positive finite inputs, `0 <= I_path_avg <= I_wall`.
- `I_path_avg` decreases monotonically with extinction coefficient, biomass concentration, and path length.
- Near zero, the implementation agrees with the analytic series within the numerical tolerance class.

### 11.3 Growth oracles

- `mu_gross(0) = 0`.
- The initial slope is `alpha` within tolerance.
- `mu_gross(I_opt) = mu_max`.
- The response increases below `I_opt` and decreases above it for positive parameters.
- `mu_gross(I) -> 0` as `I -> infinity`.
- Net productivity equals `mu_net * biomass_concentration` and preserves negative outcomes.

### 11.4 Gas-transfer oracles

For each gas:

- transfer is zero at equilibrium;
- the sign changes correctly across equilibrium;
- magnitude is linear in `kLa` and the concentration driving force;
- zero `kLa` yields zero transfer;
- sufficiency classifications equal the sign of the defined margin;
- separate CO2 and O2 coefficients cannot be silently interchanged.

The closed linear relaxation equation

```text
C(t) = C_star + (C0 - C_star) * exp(-kla * t)
```

may be used as an analytic verification fixture, but time integration is not part of the v0 runtime models.

### 11.5 Profile and evidence gates

- every operational constant resolves to a recorded primary source or approved experimental record;
- every source locator and DOI is syntactically and semantically checked;
- no profile becomes operational with `not_reported` for a load-bearing validity dimension unless the specification explicitly permits the omission;
- the pilot-scale dataset in `LIT-07` is not called a validation until a versioned extraction maps measured quantities to model outputs and records excluded physics.

## 12. Implementation slices

Implementation remains unauthorized until a separate dated readiness decision promotes 078 to `ready` and names one implementation PR.

Candidate independently reviewable slices are:

- **078-A — contracts, v2 units, profile registry, optical and light-growth algebraic models**;
- **078-B — CO2 transfer sufficiency**;
- **078-C — O2 stripping sufficiency**;
- **078-D — source-bound operational profile and external benchmark extraction**.

A readiness decision may combine only slices whose shared change is strictly smaller and safer than separate delivery. No slice may add dynamics, a general solver, expression execution, carbonate chemistry, automatic `kLa`, CFD, or a UI.

## 13. Migration and rollback

No database migration is required. New code, profiles, units, and tests are additive and separately removable.

Reverting every 078 implementation artifact must restore the pre-078 tree and preserve byte-identical results for all pre-existing model fixtures. A proposal unable to satisfy this rollback property is outside 078.

## 14. Literature closure and withheld claims

Scientific evidence and exact bibliographic records are maintained in `078-pbr-modeling-source-evidence.md`.

The literature supports the selected model families and the decision to require condition-specific parameters. It does not support universal *Nannochloropsis* constants, a universal biomass composition, a shared gas-transfer coefficient, a resolved cylindrical light field, or automatic validation of an integrated reactor.

`LIT-01` through `LIT-06` are closed for specification by selecting bounded identities and converting unsupported universal values into mandatory sourced profile constants. `LIT-07` is closed for specification by identifying a candidate independent pilot-scale dataset while explicitly deferring any validation claim until a versioned compatible extraction exists.

## 15. Final invariant

> JarvisOS may emit a photobioreactor quantity only when its formula, unit and semantic basis, input ownership, parameter source, validity envelope, diagnostics, and independent oracle are explicit. Otherwise the quantity is `not_computable` or an honestly labelled proxy; it is never silently estimated.
