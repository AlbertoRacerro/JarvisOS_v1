# Spec 078 — normative quantity and semantic-unit contract

**Authority:** normative companion to `078-full-specification-2026-08-02.md`. It supplies the exact units, semantic bases, and expanded conversions required by that contract. It adds no model, fitted parameter value, runtime authority, dependency, or migration.

The canonical arithmetic basis uses seconds, metres, kilograms of dry biomass, moles, and the declared photon amount. Compatible source/caller units are normalized at the boundary. A physical-dimension match without the listed semantic basis is insufficient.

| Quantity | Owner | Canonical unit | Semantic basis | Domain |
|---|---|---|---|---|
| `incident_par` | caller | `umol_photons/m2/s` | `incident_par_photon_flux_density` | `>= 0` |
| `tube_clean_transmittance` | caller | `1` | `tube_clean_par_transmittance` | `[0,1]` |
| `fouling_transmittance_factor` | caller | `1` | `fouling_par_transmittance_factor` | `[0,1]` |
| `biomass_concentration` | caller | `kgDW/m3` | `dry_biomass_liquid_concentration` | `>= 0` |
| `optical_path_length` | caller | `m` | `optical_path_length` | `>= 0` |
| `biomass_extinction_coefficient` | profile | `m2/kgDW` | `biomass_par_extinction_coefficient` | `>= 0` |
| `wall_par` | output | `umol_photons/m2/s` | `wall_par_photon_flux_density` | `>= 0` |
| `optical_depth` | output | `1` | `beer_lambert_optical_depth_proxy` | `>= 0` |
| `path_average_par` | output or caller | `umol_photons/m2/s` | `path_average_par_proxy` | `>= 0` |
| `mu_max` | profile | `1/s` | `gross_specific_growth_rate_limit` | `> 0` |
| `i_half` | profile | `umol_photons/m2/s` | `light_half_saturation_par` | `> 0` |
| `specific_biomass_loss_rate` | profile | `1/s` | `specific_biomass_loss_rate` | `>= 0` |
| `gross_specific_growth_rate` | output | `1/s` | `gross_specific_biomass_growth_rate` | `>= 0` |
| `net_specific_growth_rate` | output | `1/s` | `net_specific_biomass_growth_rate` | finite, signed |
| `gross_biomass_productivity` | output or compatible caller input | `kgDW/m3/s` | `gross_dry_biomass_synthesis_rate` | `>= 0` |
| `net_biomass_productivity` | output | `kgDW/m3/s` | `net_dry_biomass_accumulation_rate` | finite, signed |
| `dissolved_co2_concentration` | caller | `mol/m3` | `dissolved_free_co2_liquid` | `>= 0` |
| `co2_equilibrium_concentration` | caller/profile boundary | `mol/m3` | `dissolved_free_co2_equilibrium` | `>= 0` |
| `kla_co2` | caller/profile boundary | `1/s` | `volumetric_mass_transfer_coefficient_co2` | `>= 0` |
| `biomass_carbon_mass_fraction` | profile | `kgC/kgDW` | `dry_biomass_carbon_mass_fraction` | `(0,1]` |
| `molar_mass_carbon` | profile | `kgC/molC` | `carbon_molar_mass_authority` | `> 0` |
| `co2_transfer_rate` | output | `mol/m3/s` | `co2_gas_liquid_transfer_into_liquid` | finite, signed |
| `co2_transfer_carbon_equivalent_rate` | output | `molC/m3/s` | `co2_transfer_carbon_equivalent_into_liquid` | finite, signed |
| `gross_carbon_fixation_rate` | output | `molC/m3/s` | `gross_biological_carbon_fixation_demand` | `>= 0` |
| `co2_transfer_margin` | output | `molC/m3/s` | `co2_transfer_carbon_supply_margin` | finite, signed |
| `co2_supply_ratio` | output | `1` | `co2_transfer_to_gross_fixation_ratio` | finite for fixation `> 0`; otherwise `not_computable` |
| `dissolved_o2_concentration` | caller | `mol/m3` | `dissolved_o2_liquid` | `>= 0` |
| `o2_equilibrium_concentration` | caller/profile boundary | `mol/m3` | `dissolved_o2_equilibrium` | `>= 0` |
| `kla_o2` | caller/profile boundary | `1/s` | `volumetric_mass_transfer_coefficient_o2` | `>= 0` |
| `photosynthetic_quotient` | profile | `molO2/molC` | `photosynthetic_oxygen_per_gross_carbon_fixed` | `>= 0` |
| `o2_transfer_rate` | output | `mol/m3/s` | `o2_gas_liquid_transfer_into_liquid` | finite, signed |
| `gross_o2_generation_rate` | output | `molO2/m3/s` | `gross_photosynthetic_oxygen_generation_rate` | `>= 0` |
| `o2_stripping_capacity` | output | `molO2/m3/s` | `oxygen_transfer_out_of_liquid_capacity` | `>= 0` |
| `o2_stripping_margin` | output | `molO2/m3/s` | `oxygen_stripping_capacity_margin` | finite, signed |

The normative growth arithmetic is:

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

The normative CO2 arithmetic is:

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

The normative O2 arithmetic is:

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

No respiratory O2-consumption credit is inferred from `specific_biomass_loss_rate`. Such a credit requires a separate sourced stoichiometric model.

`mol`, `molC`, and `molO2` share an amount dimension but retain distinct semantic bases in contracts, connections, diagnostics, and canonical metadata. External per-day quantities may be accepted only through explicit conversion to the canonical per-second basis.
