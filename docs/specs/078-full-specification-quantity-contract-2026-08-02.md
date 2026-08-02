# Spec 078 — normative quantity and semantic-unit contract

**Authority:** normative companion to `078-full-specification-2026-08-02.md`. It supplies the exact unit token, Pint unit, physical-dimension identifier, semantic basis, owner, domain, and expanded conversion required by that contract. It adds no model, fitted parameter value, runtime authority, dependency, or migration.

The canonical arithmetic basis uses seconds, metres, kilograms of dry biomass, moles, and the declared photon amount. Compatible source/caller units are normalized at the boundary. A physical-dimension match without the listed semantic basis is insufficient.

## 1. Closed V2 physical-dimension extension

`process_semantic_units_v2` preserves every V1 dimension identifier and adds exactly these mathematical dimensions to the closed `_DIMENSION_REFERENCE_UNITS` vocabulary:

| `physical_dimension` | Pint reference unit |
|---|---|
| `photon_flux_density` | `mole / meter**2 / second` |
| `inverse_time` | `1 / second` |
| `area_per_mass` | `meter**2 / kilogram` |
| `area_per_amount` | `meter**2 / mole` |
| `mass_volumetric_rate` | `kilogram / meter**3 / second` |
| `amount_concentration` | `mole / meter**3` |
| `mass_per_amount` | `kilogram / mole` |
| `amount_volumetric_rate` | `mole / meter**3 / second` |

The existing V1 identifiers `dimensionless`, `length`, and `density` are reused where the mathematical dimensionality is unchanged. Biological meaning remains in `semantic_basis`; it is not encoded by inventing duplicate physical dimensions.

## 2. Normative quantity table

| Quantity | Owner | Canonical token / Pint unit | `physical_dimension` | `semantic_basis` | Domain |
|---|---|---|---|---|---|
| `incident_par` | caller | `umol_photons/m2/s` → `micromole / meter**2 / second` | `photon_flux_density` | `incident_par_photon_flux_density` | `>= 0` |
| `tube_clean_transmittance` | caller | `1` → `dimensionless` | `dimensionless` | `tube_clean_par_transmittance` | `[0,1]` |
| `fouling_transmittance_factor` | caller | `1` → `dimensionless` | `dimensionless` | `fouling_par_transmittance_factor` | `[0,1]` |
| `biomass_concentration` | caller | `kgDW/m3` → `kilogram / meter**3` | `density` | `dry_biomass_liquid_concentration` | `>= 0` |
| `optical_path_length` | caller | `m` → `meter` | `length` | `optical_path_length` | `>= 0` |
| `biomass_extinction_coefficient` | profile | `m2/kgDW` → `meter**2 / kilogram` | `area_per_mass` | `biomass_par_extinction_coefficient` | `>= 0` |
| `wall_par` | output | `umol_photons/m2/s` → `micromole / meter**2 / second` | `photon_flux_density` | `wall_par_photon_flux_density` | `>= 0` |
| `optical_depth` | output | `1` → `dimensionless` | `dimensionless` | `beer_lambert_optical_depth_proxy` | `>= 0` |
| `path_average_par` | output or caller | `umol_photons/m2/s` → `micromole / meter**2 / second` | `photon_flux_density` | `path_average_par_proxy` | `>= 0` |
| `mu_max` | profile | `1/s` → `1 / second` | `inverse_time` | `gross_specific_growth_rate_limit` | `> 0` |
| `i_half` | profile | `umol_photons/m2/s` → `micromole / meter**2 / second` | `photon_flux_density` | `light_half_saturation_par` | `> 0` |
| `specific_biomass_loss_rate` | profile | `1/s` → `1 / second` | `inverse_time` | `specific_biomass_loss_rate` | `>= 0` |
| `gross_specific_growth_rate` | output | `1/s` → `1 / second` | `inverse_time` | `gross_specific_biomass_growth_rate` | `>= 0` |
| `net_specific_growth_rate` | output | `1/s` → `1 / second` | `inverse_time` | `net_specific_biomass_growth_rate` | finite, signed |
| `gross_biomass_productivity` | output or compatible caller input | `kgDW/m3/s` → `kilogram / meter**3 / second` | `mass_volumetric_rate` | `gross_dry_biomass_synthesis_rate` | `>= 0` |
| `net_biomass_productivity` | output | `kgDW/m3/s` → `kilogram / meter**3 / second` | `mass_volumetric_rate` | `net_dry_biomass_accumulation_rate` | finite, signed |
| `dissolved_co2_concentration` | caller | `molCO2/m3` → `mole / meter**3` | `amount_concentration` | `dissolved_free_co2_liquid` | `>= 0` |
| `co2_equilibrium_concentration` | caller/profile boundary | `molCO2/m3` → `mole / meter**3` | `amount_concentration` | `dissolved_free_co2_equilibrium` | `>= 0` |
| `kla_co2` | caller/profile boundary | `1/s` → `1 / second` | `inverse_time` | `volumetric_mass_transfer_coefficient_co2` | `>= 0` |
| `biomass_carbon_mass_fraction` | profile | `kgC/kgDW` → `dimensionless` | `dimensionless` | `dry_biomass_carbon_mass_fraction` | `(0,1]` |
| `molar_mass_carbon` | profile | `kgC/molC` → `kilogram / mole` | `mass_per_amount` | `carbon_molar_mass_authority` | `> 0` |
| `co2_transfer_rate` | output | `molCO2/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `co2_gas_liquid_transfer_into_liquid` | finite, signed |
| `co2_transfer_carbon_equivalent_rate` | output | `molC/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `co2_transfer_carbon_equivalent_into_liquid` | finite, signed |
| `gross_carbon_fixation_rate` | output | `molC/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `gross_biological_carbon_fixation_demand` | `>= 0` |
| `co2_transfer_margin` | output | `molC/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `co2_transfer_carbon_supply_margin` | finite, signed |
| `co2_supply_ratio` | output | `1` → `dimensionless` | `dimensionless` | `co2_transfer_to_gross_fixation_ratio` | finite for fixation `> 0`; otherwise `not_computable` |
| `dissolved_o2_concentration` | caller | `molO2/m3` → `mole / meter**3` | `amount_concentration` | `dissolved_o2_liquid` | `>= 0` |
| `o2_equilibrium_concentration` | caller/profile boundary | `molO2/m3` → `mole / meter**3` | `amount_concentration` | `dissolved_o2_equilibrium` | `>= 0` |
| `kla_o2` | caller/profile boundary | `1/s` → `1 / second` | `inverse_time` | `volumetric_mass_transfer_coefficient_o2` | `>= 0` |
| `photosynthetic_quotient` | profile | `molO2/molC` → `dimensionless` | `dimensionless` | `photosynthetic_oxygen_per_gross_carbon_fixed` | `> 0` for an operational O2 calculation; missing evidence yields `not_computable` |
| `o2_transfer_rate` | output | `molO2/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `o2_gas_liquid_transfer_into_liquid` | finite, signed |
| `gross_o2_generation_rate` | output | `molO2/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `gross_photosynthetic_oxygen_generation_rate` | `>= 0` |
| `o2_stripping_capacity` | output | `molO2/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `oxygen_transfer_out_of_liquid_capacity` | `>= 0` |
| `o2_stripping_margin` | output | `molO2/m3/s` → `mole / meter**3 / second` | `amount_volumetric_rate` | `oxygen_stripping_capacity_margin` | finite, signed |

Every compact biological token in the table is a closed V2 semantic definition or reviewed alias; none is delegated to arbitrary Pint parsing. At minimum this includes `umol_photons/m2/s`, `kgDW/m3`, `m2/kgDW`, `1/s`, `kgDW/m3/s`, `molCO2/m3`, `molC/m3/s`, `molO2/m3`, `kgC/kgDW`, `kgC/molC`, and `molO2/molC`.

## 3. Normative arithmetic

Growth:

```text
gross_specific_growth_rate = mu_max * path_average_par
                             / (i_half + path_average_par)

gross_biomass_productivity = gross_specific_growth_rate
                             * biomass_concentration

net_specific_growth_rate = gross_specific_growth_rate
                           - specific_biomass_loss_rate

net_biomass_productivity = net_specific_growth_rate
                           * biomass_concentration
```

CO2:

```text
co2_transfer_rate = kla_co2
                    * (co2_equilibrium_concentration
                       - dissolved_co2_concentration)

co2_transfer_carbon_equivalent_rate = co2_transfer_rate
                                      * (1 molC / 1 molCO2)

gross_carbon_fixation_rate = gross_biomass_productivity
                             * biomass_carbon_mass_fraction
                             / molar_mass_carbon

co2_transfer_margin = co2_transfer_carbon_equivalent_rate
                      - gross_carbon_fixation_rate
```

The 1:1 carbon-equivalent mapping is explicit because one mole of CO2 contains one mole of carbon. It is a closed stoichiometric mapping, not a general semantic-basis conversion. `co2_supply_ratio` uses carbon-equivalent transfer divided by gross carbon fixation.

O2:

```text
o2_transfer_rate = kla_o2
                   * (o2_equilibrium_concentration
                      - dissolved_o2_concentration)

gross_o2_generation_rate = photosynthetic_quotient
                           * gross_carbon_fixation_rate

o2_stripping_capacity = max(0, -o2_transfer_rate)

o2_stripping_margin = o2_stripping_capacity
                      - gross_o2_generation_rate
```

No operational O2 result is produced when `photosynthetic_quotient` is missing, zero, negative, non-finite, or outside its source envelope. The result is `not_computable`; zero is never treated as “no oxygen generated.” No respiratory O2-consumption credit is inferred from `specific_biomass_loss_rate`; such a credit requires a separate sourced stoichiometric model.

`molCO2`, `molC`, and `molO2` share an amount dimensionality but retain distinct semantic bases in contracts, connections, diagnostics, and canonical metadata. External per-day quantities may be accepted only through explicit conversion to the canonical per-second basis.
