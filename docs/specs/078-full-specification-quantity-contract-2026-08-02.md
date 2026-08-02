# Spec 078 — normative quantity and semantic-unit contract

**Authority:** normative companion to `078-full-specification-2026-08-02.md`. It supplies the exact V2 token, Pint unit, scale, physical-dimension identifier, semantic basis, owner, domain, and expanded conversion required by that contract. It adds no model, fitted parameter value, runtime authority, dependency, or migration.

## 1. Resolver invariant

PROCESS-KERNEL-1 resolves one exact token to one `SemanticUnitDefinition` and one semantic basis. V2 preserves that context-free resolver:

- every semantic basis below has one distinct canonical token;
- no canonical token is reused for another semantic basis, even when Pint dimensionality is identical;
- ordinary Pint tokens with `semantic_basis = None` are not valid substitutes for a listed 078 contract token;
- V0 contracts and caller bindings accept only the canonical tokens below;
- source values in other units are converted during the reviewed profile/dataset extraction and stored in canonical units with conversion provenance;
- any future runtime alias must be separately enumerated in V2 with the same semantic basis and a reviewed scale; prefix, suffix, or context inference remains forbidden.

The canonical arithmetic basis uses seconds, metres, kilograms of dry biomass, moles, and the declared photon amount.

## 2. Closed V2 physical-dimension extension

V2 preserves every V1 dimension identifier and adds exactly these mathematical dimensions to the closed `_DIMENSION_REFERENCE_UNITS` vocabulary:

| `physical_dimension` | Pint reference unit |
|---|---|
| `photon_flux_density` | `mole / meter**2 / second` |
| `inverse_time` | `1 / second` |
| `area_per_mass` | `meter**2 / kilogram` |
| `mass_volumetric_rate` | `kilogram / meter**3 / second` |
| `amount_concentration` | `mole / meter**3` |
| `mass_per_amount` | `kilogram / mole` |
| `amount_volumetric_rate` | `mole / meter**3 / second` |

The existing V1 identifiers `dimensionless`, `length`, and `density` are reused where mathematical dimensionality is unchanged. Biological meaning remains exclusively in `semantic_basis`.

## 3. Exact V2 semantic definitions

Each row below is one canonical `SemanticUnitDefinition`. `scale_to_si` is relative to the Pint unit shown.

| Quantity | Owner | Canonical token | Pint unit | `scale_to_si` | `physical_dimension` | `semantic_basis` | Domain |
|---|---|---|---|---:|---|---|---|
| `incident_par` | caller | `incident_PAR_umol_m2_s` | `micromole / meter**2 / second` | `1e-6` | `photon_flux_density` | `incident_par_photon_flux_density` | `>= 0` |
| `tube_clean_transmittance` | caller | `tube_clean_PAR_fraction` | `dimensionless` | `1` | `dimensionless` | `tube_clean_par_transmittance` | `[0,1]` |
| `fouling_transmittance_factor` | caller | `fouling_PAR_factor` | `dimensionless` | `1` | `dimensionless` | `fouling_par_transmittance_factor` | `[0,1]` |
| `biomass_concentration` | caller | `biomass_kgDW_m3` | `kilogram / meter**3` | `1` | `density` | `dry_biomass_liquid_concentration` | `>= 0` |
| `optical_path_length` | caller | `optical_path_m` | `meter` | `1` | `length` | `optical_path_length` | `>= 0` |
| `biomass_extinction_coefficient` | profile | `biomass_extinction_m2_kgDW` | `meter**2 / kilogram` | `1` | `area_per_mass` | `biomass_par_extinction_coefficient` | `>= 0` |
| `wall_par` | output | `wall_PAR_umol_m2_s` | `micromole / meter**2 / second` | `1e-6` | `photon_flux_density` | `wall_par_photon_flux_density` | `>= 0` |
| `optical_depth` | output | `optical_depth_proxy` | `dimensionless` | `1` | `dimensionless` | `beer_lambert_optical_depth_proxy` | `>= 0` |
| `path_average_par` | output or caller | `path_average_PAR_umol_m2_s` | `micromole / meter**2 / second` | `1e-6` | `photon_flux_density` | `path_average_par_proxy` | `>= 0` |
| `mu_max` | profile | `gross_growth_limit_s_inv` | `1 / second` | `1` | `inverse_time` | `gross_specific_growth_rate_limit` | `> 0` |
| `i_half` | profile | `light_half_saturation_umol_m2_s` | `micromole / meter**2 / second` | `1e-6` | `photon_flux_density` | `light_half_saturation_par` | `> 0` |
| `specific_biomass_loss_rate` | profile | `biomass_loss_s_inv` | `1 / second` | `1` | `inverse_time` | `specific_biomass_loss_rate` | `>= 0` |
| `gross_specific_growth_rate` | output | `gross_growth_s_inv` | `1 / second` | `1` | `inverse_time` | `gross_specific_biomass_growth_rate` | `>= 0` |
| `net_specific_growth_rate` | output | `net_growth_s_inv` | `1 / second` | `1` | `inverse_time` | `net_specific_biomass_growth_rate` | finite, signed |
| `gross_biomass_productivity` | output or compatible caller input | `gross_biomass_kgDW_m3_s` | `kilogram / meter**3 / second` | `1` | `mass_volumetric_rate` | `gross_dry_biomass_synthesis_rate` | `>= 0` |
| `net_biomass_productivity` | output | `net_biomass_kgDW_m3_s` | `kilogram / meter**3 / second` | `1` | `mass_volumetric_rate` | `net_dry_biomass_accumulation_rate` | finite, signed |
| `dissolved_co2_concentration` | caller | `dissolved_CO2_mol_m3` | `mole / meter**3` | `1` | `amount_concentration` | `dissolved_free_co2_liquid` | `>= 0` |
| `co2_equilibrium_concentration` | caller/profile boundary | `equilibrium_CO2_mol_m3` | `mole / meter**3` | `1` | `amount_concentration` | `dissolved_free_co2_equilibrium` | `>= 0` |
| `kla_co2` | caller/profile boundary | `kla_CO2_s_inv` | `1 / second` | `1` | `inverse_time` | `volumetric_mass_transfer_coefficient_co2` | `>= 0` |
| `biomass_carbon_mass_fraction` | profile | `biomass_carbon_kgC_kgDW` | `dimensionless` | `1` | `dimensionless` | `dry_biomass_carbon_mass_fraction` | `(0,1]` |
| `molar_mass_carbon` | profile | `carbon_molar_mass_kgC_molC` | `kilogram / mole` | `1` | `mass_per_amount` | `carbon_molar_mass_authority` | `> 0` |
| `co2_transfer_rate` | output | `CO2_transfer_mol_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `co2_gas_liquid_transfer_into_liquid` | finite, signed |
| `co2_transfer_carbon_equivalent_rate` | output | `CO2_carbon_equivalent_molC_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `co2_transfer_carbon_equivalent_into_liquid` | finite, signed |
| `gross_carbon_fixation_rate` | output | `gross_carbon_fixation_molC_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `gross_biological_carbon_fixation_demand` | `>= 0` |
| `co2_transfer_margin` | output | `CO2_margin_molC_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `co2_transfer_carbon_supply_margin` | finite, signed |
| `co2_supply_ratio` | output | `CO2_supply_ratio` | `dimensionless` | `1` | `dimensionless` | `co2_transfer_to_gross_fixation_ratio` | finite for fixation `> 0`; otherwise `not_computable` |
| `dissolved_o2_concentration` | caller | `dissolved_O2_mol_m3` | `mole / meter**3` | `1` | `amount_concentration` | `dissolved_o2_liquid` | `>= 0` |
| `o2_equilibrium_concentration` | caller/profile boundary | `equilibrium_O2_mol_m3` | `mole / meter**3` | `1` | `amount_concentration` | `dissolved_o2_equilibrium` | `>= 0` |
| `kla_o2` | caller/profile boundary | `kla_O2_s_inv` | `1 / second` | `1` | `inverse_time` | `volumetric_mass_transfer_coefficient_o2` | `>= 0` |
| `photosynthetic_quotient` | profile | `photosynthetic_quotient_molO2_molC` | `dimensionless` | `1` | `dimensionless` | `photosynthetic_oxygen_per_gross_carbon_fixed` | `> 0` for operational O2 calculation; missing evidence yields `not_computable` |
| `o2_transfer_rate` | output | `O2_transfer_mol_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `o2_gas_liquid_transfer_into_liquid` | finite, signed |
| `gross_o2_generation_rate` | output | `gross_O2_generation_mol_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `gross_photosynthetic_oxygen_generation_rate` | `>= 0` |
| `o2_stripping_capacity` | output | `O2_stripping_capacity_mol_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `oxygen_transfer_out_of_liquid_capacity` | `>= 0` |
| `o2_stripping_margin` | output | `O2_stripping_margin_mol_m3_s` | `mole / meter**3 / second` | `1` | `amount_volumetric_rate` | `oxygen_stripping_capacity_margin` | finite, signed |

## 4. Normative arithmetic

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

CO2, carbon-equivalent, and O2 quantities share mathematical amount dimensionality but retain distinct exact tokens and semantic bases in contracts, connections, diagnostics, and canonical metadata.
