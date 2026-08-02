# Spec 078 — PBR-MODELING-0 full specification

**Status:** complete documentation contract; registry remains `planned`.

**Depends on:** 043, 047, 048, 049, 071, 075.

**Normative companions:**

- `078-full-specification-source-evidence-2026-08-02.md`;
- `078-full-specification-quantity-contract-2026-08-02.md`.

**Supersedes for implementation decisions:** unresolved items `RT-37`, `U1`, `U2`, `U3`, `U5`, and literature gates `LIT-01` through `LIT-07` in the merged planning kernel and its evidence register.

**Authority boundary:** this pull request is documentation-only. It authorizes no runtime code, migration, dependency, workflow, frontend, provider call, spend, implementation branch, readiness promotion, or implementation pull request.

---

## 1. Purpose

078 defines the smallest bounded step from merged static BlueRev screening models toward photobioreactor calculations that connect:

1. incident photosynthetically active radiation to one declared optical-path average proxy;
2. that scalar light quantity to one source-bound *Nannochloropsis gaditana* growth relation;
3. gross biomass synthesis to gross carbon-fixation demand;
4. externally characterized gas transfer to conservative CO2-supply and O2-stripping sufficiency checks.

The first implementation is a closed set of deterministic algebraic forward models. It is not a dynamic reactor, generic process simulator, equation-oriented language, CFD model, carbonate/pH model, property package, inverse solver, optimizer, or automatic `kLa` estimator.

## 2. Existing authority preserved unchanged

The implementation must preserve every merged contract, file, numerical fixture, canonical JSON byte sequence, and digest owned by 043, 047, 048, 049, 071, and 075.

In particular:

- 048 remains authority for its static biomass, nutrient, harvest, gas-equivalent, energy, and economic screening outputs;
- 049 remains authority for its tube/culture transmission proxies and disclaimers;
- 071 remains authority for editable caller bindings and forward degree-of-freedom inspection;
- 075 remains authority for typed ports, streams, components, semantic units, acyclic execution, and canonical 047 identity;
- `MaterialStream.composition`, `COMPONENT_CATALOG`, `fixture_biomass`, `process_semantic_units_v1`, and every pre-078 profile remain byte-for-byte unchanged.

Every 078 model receives a new identity and coexists with 047, 048, and 049. No existing model is rewritten, reinterpreted, or silently upgraded.

## 3. Closed architecture

### 3.1 Server-bundled profile registry

078 adds a closed server-bundled profile registry. A caller selects a known profile identifier but cannot submit equations, Python, expressions, arbitrary parameter names, or a custom model definition.

Each profile record must contain:

- `profile_id` and `profile_version`;
- exact model identities used by the profile;
- canonical content hash over metadata and constants;
- organism, strain, culture mode, medium/salinity, temperature, acclimation and measurement context;
- every constant with canonical unit, semantic basis, source locator, applicable range, uncertainty when reported, and transformation history;
- explicit status `verification_only` or `operational`.

A profile is `operational` only when all constants needed by the selected models have compatible primary-source or approved-experiment authority and the caller state lies inside their intersected validity envelopes. Missing evidence is never replaced by a default.

### 3.2 Initial model identities

The first bounded implementation consists of four independently removable algebraic models:

1. `pbr_optical_path_average_v0`;
2. `pbr_light_growth_monod_path_average_v0`;
3. `pbr_co2_transfer_sufficiency_v0`;
4. `pbr_o2_stripping_sufficiency_v0`.

They may be assembled in one bundled profile, but each retains its own contracts, diagnostics, validity envelope, and tests.

## 4. Decision closures

### 4.1 `RT-37` — identity and numerical verification

The 075 exact-identity test proves canonical 047 equivalence in the same runtime. It does not grant an exact-digest class to new 078 calculations.

078 uses three verification classes:

- **structural identity:** exact model/profile identifiers, canonical metadata, input/output keys, units, semantic bases, source records, and content hashes;
- **algebraic numerical tolerance:** `pytest.approx(rel=1e-12, abs=1e-15)` unless a named oracle defines a tighter tolerance;
- **pinned-platform digest:** prohibited for ordinary acceptance and permitted only in a future explicitly environment-gated canary.

Cross-platform bit identity for new floating-point outputs must not be claimed.

### 4.2 `U1` — dissolved-gas representation

Dissolved free CO2 and O2 are absolute scalar liquid-phase molar concentrations outside `MaterialStream.composition`.

They are not component fractions, do not participate in the stream composition sum, and do not imply carbonate speciation, alkalinity, pH dynamics, phase split, or a thermodynamic property package.

The exact quantities, units, and semantic bases are normative in the quantity-contract companion.

### 4.3 `U2` — semantic units

078 requires an additive `process_semantic_units_v2`. Version 1 remains immutable and all existing profiles stay bound to it.

V2 adds only the reviewed dimensions/tokens required by the four models: photon-flux density, amount concentration, inverse time, dry-biomass concentration and productivity, extinction area per dry mass, carbon mass fraction, carbon molar mass, gas-specific molar rates, and gas-specific stoichiometric ratios.

V2 has its own canonical hash, requires no database migration, and must not change the v1 payload or digest. Exact tokens, dimensions, semantic bases, and boundary conversions are defined in the quantity-contract companion.

### 4.4 `U3` — biomass authority

078 does not modify `COMPONENT_CATALOG` or promote `fixture_biomass` into a universal scientific component.

Biomass concentration is a scalar operating quantity. Carbon mass fraction, light-growth constants, specific biomass-loss rate, photosynthetic quotient, and every composition-dependent property are profile constants bound to organism, strain, conditions, source, and validity envelope.

No universal *Nannochloropsis* composition is asserted. Missing carbon fraction or gas stoichiometry produces `not_computable` rather than a substituted value.

### 4.5 `U5` and `LIT-01` — selected light-growth relation

The V0 operational mathematical identity is the Monod-like light-saturation relation fitted in primary experiments on *Nannochloropsis gaditana* grown in a quasi-isoactinic reactor under multiple photon-flux densities:

```text
mu_gross(I) = mu_max * I / (i_half + I)
```

with:

- `I >= 0`;
- `mu_max > 0`;
- `i_half > 0`.

Gross and net biomass rates are separated:

```text
gross_biomass_productivity = mu_gross(I_path_avg)
                             * biomass_concentration

net_specific_growth_rate = mu_gross(I_path_avg)
                           - specific_biomass_loss_rate

net_biomass_productivity = net_specific_growth_rate
                           * biomass_concentration
```

`mu_max`, `i_half`, and `specific_biomass_loss_rate` are mandatory profile constants with exact source/envelope metadata. The loss term must be labelled `respiration`, `decay`, or `combined_loss` according to its evidence; no respiratory carbon or oxygen stoichiometry is inferred from that scalar.

The selected law does **not** model photoinhibition. An operational profile must reject light above its qualified source/calibration envelope with `pbr_validity_envelope_exceeded`; it may not extrapolate the saturation curve into high-light conditions. Bernard–Rémond, Steele, Platt, Haldane/Andrews, or photoacclimation models require separate source-compatible identities and are not aliases of V0.

This closes `LIT-01` for V0 because the selected family is supported by target-organism experiments and is explicitly restricted to the non-photoinhibitory envelope actually characterized. It does not authorize importing the published fitted values without an independent extraction and provenance record.

## 5. Optical-path model

### 5.1 Inputs and constant

Caller inputs:

- incident PAR;
- clean-tube transmittance;
- fouling transmittance factor;
- biomass concentration;
- optical path length;
- explicit fouling convention.

Profile constant:

- biomass PAR extinction coefficient with source and envelope.

Exact names, units, semantic bases, and domains are defined in the quantity-contract companion.

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

The result is a one-dimensional absorption-only path-average proxy. Primary tubular-PBR evidence shows that geometry, scattering, and wavelength dependence can materially affect light distribution; therefore V0 does not claim:

- radial or angular light fields;
- direct/diffuse decomposition;
- scattering;
- spectral resolution;
- self-consistent pigment acclimation;
- a quantified error against radiative transfer.

This claim restriction closes `LIT-02`. A higher-fidelity optical model requires a new identity.

## 6. Light-growth outputs

The light-growth model emits:

- gross specific growth rate;
- gross biomass productivity;
- net specific growth rate;
- net biomass productivity;
- `growth_status`: `net_growth`, `zero_net_growth`, or `net_biomass_decline`.

A negative net rate is a valid screening outcome, not an exception. Gross quantities remain non-negative and are used for conservative instantaneous gas-demand calculations.

## 7. CO2 transfer sufficiency

### 7.1 Boundary and ownership

Caller/profile-bound inputs are:

- dissolved free-CO2 concentration;
- CO2 equilibrium concentration;
- `kla_co2`;
- gross biomass productivity from the selected 078 growth model or an explicitly sourced compatible input.

Profile constants are:

- dry-biomass carbon mass fraction;
- carbon molar-mass authority.

Equilibrium concentration must carry temperature, salinity, gas composition, pressure/fugacity convention, source, and calculation provenance. 078 does not calculate it from pH, alkalinity, total inorganic carbon, or a general Henry/property package. This external-equilibrium boundary closes `LIT-03`.

`kla_co2` is supplied from compatible characterization evidence; no automatic correlation is authorized. This closes the CO2 part of `LIT-04`.

### 7.2 Sign convention and formula

Positive gas transfer is into the liquid:

```text
r_co2_transfer = kla_co2
                 * (co2_equilibrium_concentration
                    - dissolved_co2_concentration)

r_co2_transfer_C_equivalent = r_co2_transfer
                              * (1 molC / 1 molCO2)

r_gross_C_fixation = gross_biomass_productivity
                     * biomass_carbon_mass_fraction
                     / molar_mass_carbon

co2_margin = r_co2_transfer_C_equivalent
             - r_gross_C_fixation
```

When gross fixation is positive:

```text
co2_supply_ratio = r_co2_transfer_C_equivalent
                   / r_gross_C_fixation
```

Otherwise the ratio is `not_computable`, while signed rates and margin remain available.

The check compares transfer against **gross instantaneous carbon fixation**, not net biomass accumulation. It is conservative for external makeup because respiratory CO2 recycling is outside V0. `co2_status` is `sufficient` when the margin is non-negative and `insufficient` otherwise. Insufficiency is an engineering result, not an execution failure.

## 8. O2 stripping sufficiency

Caller/profile-bound inputs are:

- dissolved O2 concentration;
- O2 equilibrium concentration;
- `kla_o2`;
- gross carbon-fixation rate from §7.

Profile constant:

- photosynthetic quotient, mol O2 generated per mol C gross-fixed, with source and envelope.

The same positive-into-liquid convention applies:

```text
r_o2_transfer = kla_o2
                * (o2_equilibrium_concentration
                   - dissolved_o2_concentration)

r_gross_o2_generation = photosynthetic_quotient
                        * r_gross_C_fixation

o2_stripping_capacity = max(0, -r_o2_transfer)

o2_stripping_margin = o2_stripping_capacity
                      - r_gross_o2_generation
```

The result is `sufficient`, `insufficient`, or `not_computable`.

This corrects the failure mode of basing O2 generation on net biomass accumulation. Respiratory O2 consumption is not inferred; using gross O2 generation therefore yields a conservative stripping check. A future net-O2 model requires sourced respiratory oxygen stoichiometry and a new identity.

`kla_co2` and `kla_o2` are distinct quantities. A shared value is forbidden unless a source-compatible transformation explicitly justifies it. This closes the O2 part of `LIT-04`.

The model does not claim a complete elemental oxygen balance: water, nutrients, photorespiration products, detailed biomass composition, and respiratory gas stoichiometry are outside its boundary.

## 9. Biomass composition and loss evidence

`LIT-05` is closed by profile ownership: carbon fraction and photosynthetic quotient are mandatory source-bound constants, not universal component properties.

`LIT-06` is closed by requiring a source-bound specific loss term and by withholding unsupported respiratory gas stoichiometry. If compatible evidence cannot distinguish respiration from death/decay, the profile must use `combined_loss` and the gas checks remain gross/conservative.

## 10. Validity envelopes and provenance

Every operational profile fails closed before arithmetic if any required operating value lies outside the intersection of source envelopes.

At minimum, the profile records and validates when applicable:

- organism and strain;
- batch, continuous, or turbidostat context;
- temperature range;
- salinity or medium;
- pH range reported by the source, without modelling pH;
- incident-light range, spectrum, and averaging basis;
- biomass-concentration range;
- acclimation regime;
- gas composition and pressure basis;
- reactor type and scale for `kLa`;
- measurement method;
- parameter uncertainty or `not_reported`.

Interpolation is allowed only when explicitly defined by the profile. Extrapolation raises `pbr_validity_envelope_exceeded`.

## 11. Diagnostics and failure semantics

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

Diagnostics include model/profile identities and hashes, source IDs, active envelopes, light-averaging and fouling conventions, gas sign convention, gross-versus-net basis, conservative-bound labels, withheld claims, and every margin used for classification.

NaN and infinity are prohibited. All quantities carry the exact units and semantic bases in the normative quantity contract.

## 12. Acceptance tests

### 12.1 Preservation gates

- Existing 047, 048, 049, 071, and 075 tests remain unchanged and green.
- Existing canonical values, `float.hex()` values, JSON bytes, hashes, and result digests remain unchanged.
- `process_semantic_units_v1` and the component-catalog payload/digest remain unchanged.

### 12.2 Optical oracles

- `tau = 0` gives `I_path_avg = I_wall` through the explicit branch.
- For finite valid inputs, `0 <= I_path_avg <= I_wall`.
- `I_path_avg` decreases monotonically with extinction coefficient, biomass concentration, and path length.
- Near zero, the implementation agrees with the analytic series within tolerance.

### 12.3 Growth oracles

- `mu_gross(0) = 0`.
- Initial slope is `mu_max / i_half` within tolerance.
- `mu_gross(i_half) = mu_max / 2`.
- The response is monotone increasing inside the qualified envelope.
- `mu_gross(I)` approaches `mu_max` from below.
- Inputs above the qualified non-photoinhibitory envelope fail closed rather than extrapolate.
- Gross and net productivity equal their defined specific rates times biomass concentration.
- Negative net outcomes are preserved.

### 12.4 Gas-transfer oracles

For each gas:

- transfer is zero at equilibrium;
- sign changes correctly across equilibrium;
- magnitude is linear in `kLa` and driving force;
- zero `kLa` yields zero transfer;
- classifications equal the sign of the defined margin;
- CO2 and O2 coefficients cannot be interchanged.

Additional gates:

- one mol CO2 maps explicitly to one mol carbon-equivalent before comparison;
- CO2 demand and O2 generation use gross carbon fixation;
- increasing the loss rate cannot reduce the gross gas burden at fixed gross growth;
- no respiratory O2-consumption credit is applied without a separate sourced identity.

The analytic relaxation equation

```text
C(t) = C_star + (C0 - C_star) * exp(-kla * t)
```

may be used as a verification fixture, but time integration is not part of V0 runtime.

### 12.5 Profile and evidence gates

- every operational constant resolves to a primary source or approved experimental record;
- source locator and DOI metadata are checked;
- no profile is operational with a missing load-bearing validity dimension unless explicitly permitted;
- published fitted values are imported only through a reviewed extraction with units, uncertainty, and transformation provenance;
- the `LIT-07` pilot dataset is not called validation until a versioned extraction maps measured quantities to model outputs and proves parameter independence.

## 13. `LIT-07` benchmark closure

A primary pilot-scale tubular-PBR dataset for *Nannochloropsis granulata* is identified as the candidate independent benchmark.

`LIT-07` is closed for specification by naming this dataset and the acceptance conditions. No validation claim exists until implementation slice 078-D provides:

- immutable source locator and extraction hash;
- included/excluded experiments and time windows;
- unit conversions;
- measured-to-model quantity mapping;
- parameter-independence audit;
- excluded-physics statement;
- predeclared comparison metrics and thresholds.

## 14. Implementation slices

Implementation remains unauthorized until a separate dated readiness decision promotes 078 to `ready` and names one implementation PR.

Candidate independently reviewable slices are:

- **078-A — contracts, V2 units, profile registry, optical proxy, and Monod path-average growth**;
- **078-B — conservative gross CO2-transfer sufficiency**;
- **078-C — conservative gross O2-stripping sufficiency**;
- **078-D — source-bound operational profile and external benchmark extraction**.

No slice may add dynamics, a general solver, expression execution, carbonate chemistry, automatic `kLa`, CFD, or UI.

## 15. Migration and rollback

No database migration is required. New code, profiles, units, and tests are additive and separately removable.

Reverting every 078 implementation artifact must restore the pre-078 tree and preserve byte-identical results for every pre-existing model fixture. A proposal unable to satisfy this rollback property is outside 078.

## 16. Final invariant

> JarvisOS may emit a photobioreactor quantity only when its formula, unit and semantic basis, gross/net basis, input ownership, parameter source, validity envelope, diagnostics, and independent oracle are explicit. Otherwise the quantity is `not_computable` or an honestly labelled proxy; it is never silently estimated.
