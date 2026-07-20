# 048 — BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, energy, and preliminary economics

Status: implementation-ready full specification. `docs/specs/STATUS.md` is authoritative.

Depends on: 043, 047

Related merged operator surface: 071

## Goal

Add one reviewed, deterministic `calc_v0` forward model that turns an explicit
productive liquid volume and caller-selected biological, nutrient, harvesting, and
economic inputs into an M0 screening result for:

- biomass inventory and imposed productivity;
- nitrogen, phosphorus, and carbon incorporation demand;
- stock-solution dosing;
- bounded CO2/O2 stoichiometric and gas-rate proxies;
- whole-culture bleed and side-stream cell-retention sizing;
- corrected concentrate and filtration sizing;
- pump electricity and pump-electricity-only variable-cost KPIs;
- an optional gross-margin proxy with an explicit `not_computable` state.

The model compares operator-selected scenarios. It is not a calibrated biological
model, gas-transfer model, harvesting-equipment selection, complete energy balance,
full techno-economic assessment, or digital twin.

No numerical fixture in this document is a selected Mark-1 value or product default.
Every project and operating value remains an editable 071 binding.

## Maintainer direction

Use the smallest existing mechanisms:

- one reviewed repository script executed only through `calc_v0`;
- one immutable, value-free 071 input-contract artifact;
- explicit caller binding of upstream 047 outputs where appropriate;
- the existing runner registration, hash, timeout, artifact, log, simulation-run,
  and MemoryStore proposal boundaries;
- the existing Domain Foundation scenario panel without a new frontend surface;
- deterministic offline tests with independent calculations;
- no workbook runtime dependency;
- no equation engine, optimizer, workflow engine, TEA framework, unit package,
  background worker, provider call, model call, or second scenario store.

## Source baseline and authority

External reference artifact:

- `BlueRev_Data_Model_v0_10_N_gaditana_refs_fixed.xlsx`;
- internal workbook headings still say v0.9, which is configuration drift and is
  preserved only as source history;
- relevant sheets: `10_Model_Input`, `23_Data_Media_Nutrients`,
  `24_Data_Harvesting`, `40_Calculations`, `50_Sensitivity`, and
  `70_Formula_Audit`.

The workbook is a requirements and regression artifact, not executable truth. It is
not stored in the repository and must not be read at runtime or in CI. The complete
corrected equations and golden values required by 048 are restated below.

The workbook formula audit already records these prior corrections:

- dilution equivalent is whole-culture bleed divided by liquid volume;
- filtration area is based on side-stream volume, not concentrate volume;
- biomass sensitivity recalculates liquid volume for each diameter case;
- formula references use stable Parameter IDs rather than fixed input-row positions.

The independent architecture audit found one remaining recovery-basis defect:

- `40_Calculations!C43` sizes side-stream volume as biomass production divided by
  culture concentration and capture recovery;
- `40_Calculations!C44` divides concentrate volume by capture recovery again.

048 keeps the first relationship under explicit filtrate-return semantics and removes
the second recovery division. Recovery is applied exactly once.

## Model boundary

### Biological fidelity

The calculation is `M0_static_screening`.

Volumetric productivity is an independent caller input. It is not calculated from
light, temperature, pH, salinity, nutrients, DIC, dissolved oxygen, flow, fouling, or
`maximum_specific_growth_rate`. Those variables may affect the real process but are
not coupled in 048.

`maximum_specific_growth_rate` is used only for a screening ratio. The model must not
present `volumetric_productivity / biomass_concentration` as a calibrated kinetic rate
or washout prediction.

### Productive-volume boundary

047 distinguishes tube liquid volume from total liquid inventory. 048 therefore
requires `productive_liquid_volume` explicitly in `m3`.

A caller may bind the accepted 047 `total_liquid_inventory` output when the whole
inventory is deliberately asserted to be biologically productive, or may supply a
different accepted/manual volume. 048 never chooses this basis automatically.

Required diagnostics:

- `productive_volume_basis = "caller_asserted_explicit_volume"`;
- `upstream_volume_not_auto_selected = true`.

### Nutrient boundary

N, P, and C calculations represent biomass-incorporation demand only. They do not
include:

- initial medium charge;
- residual N/P target inventory;
- replacement of nutrients discharged in makeup, purge, or cleaning streams;
- precipitation, volatilization, leakage, biological excretion, or measurement error.

The workbook residual targets remain inactive validation/control targets and are not
048 model inputs. They must not be silently added to daily demand.

### Gas boundary

The model separates:

- carbon incorporated into biomass;
- stoichiometric CO2-equivalent uptake;
- stoichiometric O2-equivalent production;
- an instantaneous CO2 gas-rate benchmark used for pH-control screening.

The gas-rate benchmark is not continuous consumed CO2, mass transfer, kLa, utilization,
off-gas, blower duty, or degasser performance. DO setpoint/alarm and degasser velocity
remain outside the active 048 contract.

### Harvest boundary

V0 supports two explicitly different comparisons:

1. whole-culture bleed with no cell retention;
2. side-stream filtration with filtrate returned to the loop.

For side-stream filtration, `harvest_recovery` is the single-pass biomass capture
fraction. The side stream is sized so captured biomass equals imposed daily biomass
production. Uncaptured biomass is returned with filtrate and is not called a product
loss.

The following identity is mandatory:

```text
side_stream_biomass_feed
= recovered_biomass + returned_uncaptured_biomass
```

A discard-filtrate or purge-loss model is not supported in 048 and requires a later
mass-balance contract.

### Energy and economic boundary

048 represents only electricity used by the bound 047 pump power. Its exact economic
boundary is:

```text
economic_boundary = pump_electricity_only
```

Excluded categories are:

- nutrient and carbon-source purchase;
- CO2/air supply and gas handling;
- filtration/harvesting power and consumables;
- controls and sensors;
- cleaning and fouling management;
- thermal management;
- labor, maintenance, logistics, leases, waste, and water;
- CAPEX, financing, depreciation, tax, and revenue quality adjustments.

`variable_opex_rate` and `specific_variable_cost` are therefore valid only under the
named partial boundary. They must never be labelled total OPEX or total production
cost.

`gross_margin_proxy` is emitted only when `product_price` is supplied. Otherwise the
biological/harvest calculation succeeds, the numeric KPI is absent, and diagnostics
report `not_computable:missing_product_price`. Missing price is never replaced by zero.

## Exact input contract

The value-free 071 contract contains the following variables. Required variables count
toward forward input DOF; `product_price` is optional.

| Name | Unit | Required | Category | Domain / meaning |
| --- | --- | --- | --- | --- |
| `productive_liquid_volume` | `m3` | yes | design | `> 0`; explicit biologically productive liquid volume |
| `operating_biomass_concentration` | `gDW/L` | yes | operating | `> 0` |
| `volumetric_productivity` | `gDW/L/d` | yes | model_parameter | `> 0`; imposed M0 productivity |
| `maximum_specific_growth_rate` | `1/d` | yes | model_parameter | `> 0`; screening reference only |
| `operating_days_per_year` | `d/y` | yes | operating | `> 0` and `<= 366` |
| `feed_events_per_day` | `1/d` | yes | operating | `> 0` |
| `biomass_nitrogen_fraction` | `gN/gDW` | yes | property | `>= 0` and `<= 1` |
| `biomass_phosphorus_fraction` | `gP/gDW` | yes | property | `>= 0` and `<= 1` |
| `biomass_carbon_fraction` | `gC/gDW` | yes | property | `> 0` and `<= 1` |
| `nitrogen_stock_concentration` | `mgN/mL` | yes | operating | `> 0` |
| `phosphorus_stock_concentration` | `mgP/mL` | yes | operating | `> 0` |
| `carbon_stock_concentration` | `mgC/mL` | yes | operating | `> 0` |
| `co2_specific_gas_rate` | `mLCO2/L/min` | yes | operating | `>= 0`; instantaneous benchmark |
| `harvest_recovery` | `1` | yes | equipment | `> 0` and `<= 1`; capture fraction |
| `concentrate_biomass_concentration` | `gDW/L` | yes | equipment | `> 0`; script also requires it to exceed culture concentration |
| `filtration_flux` | `L/m2/h` | yes | equipment | `> 0` |
| `filtration_operating_hours_per_day` | `h/d` | yes | operating | `> 0` and `<= 24` |
| `pump_electric_power` | `W` | yes | equipment | `>= 0`; caller may bind 047 output |
| `circulation_operating_hours_per_day` | `h/d` | yes | operating | `> 0` and `<= 24` |
| `electricity_price` | `EUR/kWh` | yes | model_parameter | `>= 0` |
| `product_price` | `EUR/kgDW` | no | model_parameter | `>= 0`; optional margin proxy |

V0 performs no unit conversion. Equivalent unit strings are rejected.

The script accepts exactly all required names and at most the optional
`product_price`. Unknown names, absent required names, unknown keys inside an input
item, booleans, non-finite values, wrong units, and domain violations fail closed.

## Constants and derived quantities

Use SI-compatible arithmetic internally while preserving the exact units above.

```text
V_L = productive_liquid_volume * 1000
```

Frozen workbook screening conversion factors:

```text
NaNO3_per_N = 6.07 mg NaNO3 / mg N
NaH2PO4_H2O_per_P = 4.46 mg salt / mg P
NaHCO3_per_C = 6.99 mg NaHCO3 / mg C
O2_molar_volume_STP = 22.414 L/mol
```

The three salt factors are intentionally the rounded factors stored in the workbook
data sheet. Diagnostics must identify them as rounded screening constants. A later
precision amendment may replace them, but implementation must not silently mix exact
molar-mass ratios with the regression baseline.

## Calculation contract

### 1. Biomass inventory and production

```text
biomass_inventory = V_L * X / 1000
biomass_production_g_d = V_L * P_vol
biomass_production_kg_d = biomass_production_g_d / 1000
annual_biomass_equivalent = biomass_production_kg_d * operating_days_per_year
D_eq = P_vol / X
D_eq_over_mu_max = D_eq / mu_max
```

Outputs:

- `biological_productive_volume`, `m3`;
- `biomass_inventory`, `kgDW`;
- `gross_biomass_production_rate`, `kgDW/d`;
- `annual_biomass_equivalent`, `kgDW/y`;
- `equivalent_dilution_rate`, `1/d`;
- `equivalent_dilution_to_mu_max`, `1`.

`annual_biomass_equivalent` is an annualized equivalent, not a production guarantee.

### 2. Nutrient and carbon incorporation

```text
N_demand = biomass_production_g_d * gN_gDW * 1000
P_demand = biomass_production_g_d * gP_gDW * 1000
C_demand = biomass_production_g_d * gC_gDW * 1000

NaNO3_dose = N_demand * 6.07
NaH2PO4_H2O_dose = P_demand * 4.46
NaHCO3_equivalent_dose = C_demand * 6.99

N_stock_volume = N_demand / stock_N
P_stock_volume = P_demand / stock_P
C_stock_volume = C_demand / stock_C

stock_volume_per_event = stock_volume_per_day / feed_events_per_day
```

Outputs:

- `nitrogen_incorporation_demand`, `mgN/d`;
- `phosphorus_incorporation_demand`, `mgP/d`;
- `carbon_incorporation_demand`, `mgC/d`;
- `sodium_nitrate_equivalent_dose`, `mg/d`;
- `sodium_dihydrogen_phosphate_monohydrate_equivalent_dose`, `mg/d`;
- `sodium_bicarbonate_equivalent_dose`, `mg/d`;
- `nitrogen_stock_volume_rate`, `mL/d`;
- `phosphorus_stock_volume_rate`, `mL/d`;
- `carbon_stock_volume_rate`, `mL/d`;
- corresponding three `*_stock_volume_per_event`, `mL/event`.

These are demanded element and equivalent-stock quantities. They are not proof of
solubility, sterility, bioavailability, precipitation safety, or pH compatibility.

### 3. Carbon, oxygen, and gas-rate proxies

```text
CO2_equivalent_g_d = C_demand * (44 / 12) / 1000
O2_equivalent_g_d = C_demand * (32 / 12) / 1000
O2_volume_STP_L_d = (O2_equivalent_g_d / 32) * 22.414
CO2_gas_rate_benchmark = V_L * co2_specific_gas_rate
```

Outputs:

- `co2_uptake_equivalent`, `gCO2/d`;
- `oxygen_production_equivalent`, `gO2/d`;
- `oxygen_volume_stp_equivalent`, `L O2/d`;
- `co2_gas_rate_benchmark`, `mLCO2/min`.

The O2 relationship is a screening stoichiometric equivalent and not a measured net
photosynthetic oxygen rate.

### 4. Whole-culture bleed comparison

```text
whole_culture_bleed = biomass_production_g_d / X
whole_culture_bleed_per_event = whole_culture_bleed / feed_events_per_day
whole_culture_dilution = whole_culture_bleed / V_L
```

Outputs:

- `whole_culture_bleed_rate`, `L/d`;
- `whole_culture_bleed_per_event`, `L/event`;
- `whole_culture_dilution_equivalent`, `1/d`.

This is the no-cell-retention comparison. It is not the side-stream filtrate-return
liquid loss.

### 5. Side-stream capture with filtrate return

```text
side_stream_processed = biomass_production_g_d / (X * harvest_recovery)
side_stream_processed_per_event = side_stream_processed / feed_events_per_day
side_stream_biomass_feed = side_stream_processed * X / 1000
recovered_biomass = biomass_production_kg_d
returned_uncaptured_biomass = side_stream_biomass_feed - recovered_biomass
concentrate_volume = recovered_biomass * 1000 / X_concentrate
filter_area = side_stream_processed / (filtration_hours_per_day * filtration_flux)
```

Outputs:

- `side_stream_processed_rate`, `L/d`;
- `side_stream_processed_per_event`, `L/event`;
- `side_stream_biomass_feed_rate`, `kgDW/d`;
- `recovered_biomass_rate`, `kgDW/d`;
- `returned_uncaptured_biomass_rate`, `kgDW/d`;
- `concentrate_volume_rate`, `L/d`;
- `required_filter_area`, `m2`.

Required identities, evaluated with deterministic tolerance:

```text
side_stream_biomass_feed
= recovered_biomass + returned_uncaptured_biomass

recovered_biomass = gross_biomass_production_rate
```

`concentrate_volume` must not divide by `harvest_recovery` again.

### 6. Pump electricity

```text
pump_energy_daily = pump_electric_power * circulation_hours_per_day / 1000
pump_energy_annual = pump_energy_daily * operating_days_per_year
specific_pump_energy = pump_energy_daily / recovered_biomass
```

Outputs:

- `pump_electric_energy_rate`, `kWh/d`;
- `annual_pump_electric_energy`, `kWh/y`;
- `specific_pump_energy`, `kWh/kgDW`.

### 7. Preliminary economic evaluation

```text
variable_opex_daily = pump_energy_daily * electricity_price
variable_opex_annual = variable_opex_daily * operating_days_per_year
specific_variable_cost = variable_opex_daily / recovered_biomass
```

Outputs always present under the partial boundary:

- `variable_opex_rate`, `EUR/d`;
- `annual_variable_opex`, `EUR/y`;
- `specific_variable_cost`, `EUR/kgDW`.

When `product_price` is supplied:

```text
gross_margin_proxy = recovered_biomass * product_price - variable_opex_daily
annual_gross_margin_proxy = gross_margin_proxy * operating_days_per_year
```

Additional outputs:

- `gross_margin_proxy`, `EUR/d`;
- `annual_gross_margin_proxy`, `EUR/y`.

When `product_price` is absent, these two numeric outputs are absent and diagnostics
contain:

```json
{
  "gross_margin_proxy": {
    "status": "not_computable",
    "reason": "missing_product_price"
  }
}
```

## Successful result and diagnostics

Every numeric output is finite and has the exact non-empty unit declared above.

Required diagnostics include:

- `model_id = "bluerev_biomass_nutrients_harvest_v0"`;
- `model_fidelity = "M0_static_screening"`;
- `species_basis = "Nannochloropsis_gaditana_screening"`;
- `productivity_is_imposed_input = true`;
- `productive_volume_basis = "caller_asserted_explicit_volume"`;
- `nutrient_boundary = "biomass_incorporation_only"`;
- `residual_nutrient_targets_not_modeled = true`;
- `gas_rate_semantics = "instantaneous_pH_control_benchmark"`;
- `gas_transfer_not_evaluated = true`;
- `harvest_mode = "side_stream_capture_with_filtrate_return"`;
- `harvest_recovery_application_count = 1`;
- `filtrate_discard_not_modeled = true`;
- `economic_model_id = "preliminary_economic_evaluation_v0"`;
- `economic_boundary = "pump_electricity_only"`;
- `economic_basis = "daily_recovered_dry_biomass"`;
- `included_variable_cost_categories = ["pump_electricity"]`;
- bounded excluded and missing cost-category lists;
- per-KPI status for the three economic KPI families;
- `full_tea = false`;
- `capex_included = false`;
- `workbook_runtime_dependency = false`;
- rounded salt-conversion-factor metadata.

### Per-input provenance and uncertainty evidence

For every contract variable, diagnostics contain one bounded entry with:

- `binding_state = "parameter"`, `"manual"`, or `"missing_optional"`;
- `source_parameter_id` only when the caller supplied a verified parameter binding;
- `uncertainty_state = "not_characterized"`.

048 does not fabricate uncertainty intervals and does not change numerical equations
based on uncertainty metadata. The immutable simulation-run input payload and result
diagnostics preserve the evidence available in V0. A later generic uncertainty
snapshot may extend this boundary without changing 048 equations.

## Validation and failure semantics

The existing 043 envelope remains authoritative. Script-specific failures use one
bounded stderr message:

```text
bluerev_calc_error:<stable_reason>[:<field_name>]
```

Required stable reasons:

- `input_contract_invalid`;
- `input_unit_invalid`;
- `input_domain_invalid`;
- `productive_volume_basis_invalid`;
- `harvest_concentration_invalid`;
- `mass_balance_invalid`;
- `time_basis_invalid`.

Failures exit non-zero, produce no successful result artifact, and create zero
parameter proposals. These are script diagnostics, not new runner error codes.

Missing optional `product_price` is not a run failure.

## Corrected workbook regression fixture

The fixture below is evidence only:

| Input | Value | Unit |
| --- | ---: | --- |
| `productive_liquid_volume` | 0.019137166941154067 | `m3` |
| `operating_biomass_concentration` | 0.8 | `gDW/L` |
| `volumetric_productivity` | 0.15 | `gDW/L/d` |
| `maximum_specific_growth_rate` | 0.4 | `1/d` |
| `operating_days_per_year` | 300 | `d/y` |
| `feed_events_per_day` | 1 | `1/d` |
| `biomass_nitrogen_fraction` | 0.06 | `gN/gDW` |
| `biomass_phosphorus_fraction` | 0.008 | `gP/gDW` |
| `biomass_carbon_fraction` | 0.5 | `gC/gDW` |
| `nitrogen_stock_concentration` | 20 | `mgN/mL` |
| `phosphorus_stock_concentration` | 2 | `mgP/mL` |
| `carbon_stock_concentration` | 20 | `mgC/mL` |
| `co2_specific_gas_rate` | 0.8 | `mLCO2/L/min` |
| `harvest_recovery` | 0.9 | `1` |
| `concentrate_biomass_concentration` | 20 | `gDW/L` |
| `filtration_flux` | 24.7 | `L/m2/h` |
| `filtration_operating_hours_per_day` | 24 | `h/d` |
| `pump_electric_power` | 0.5024804066626467 | `W` |
| `circulation_operating_hours_per_day` | 24 | `h/d` |
| `electricity_price` | 0.25 | `EUR/kWh` |
| `product_price` | omitted | `EUR/kgDW` |

Expected values include:

| Output | Expected value | Unit |
| --- | ---: | --- |
| `biomass_inventory` | 0.015309733552923255 | `kgDW` |
| `gross_biomass_production_rate` | 0.00287057504117311 | `kgDW/d` |
| `annual_biomass_equivalent` | 0.8611725123519329 | `kgDW/y` |
| `equivalent_dilution_rate` | 0.1875 | `1/d` |
| `equivalent_dilution_to_mu_max` | 0.46875 | `1` |
| `nitrogen_incorporation_demand` | 172.2345024703866 | `mgN/d` |
| `phosphorus_incorporation_demand` | 22.96460032938488 | `mgP/d` |
| `carbon_incorporation_demand` | 1435.287520586555 | `mgC/d` |
| `sodium_nitrate_equivalent_dose` | 1045.4634299952465 | `mg/d` |
| `sodium_dihydrogen_phosphate_monohydrate_equivalent_dose` | 102.42211746905656 | `mg/d` |
| `sodium_bicarbonate_equivalent_dose` | 10032.659768900021 | `mg/d` |
| `nitrogen_stock_volume_rate` | 8.61172512351933 | `mL/d` |
| `phosphorus_stock_volume_rate` | 11.48230016469244 | `mL/d` |
| `carbon_stock_volume_rate` | 71.76437602932775 | `mL/d` |
| `co2_uptake_equivalent` | 5.262720908817368 | `gCO2/d` |
| `oxygen_production_equivalent` | 3.8274333882308134 | `gO2/d` |
| `oxygen_volume_stp_equivalent` | 2.6808778738689205 | `L O2/d` |
| `co2_gas_rate_benchmark` | 15.309733552923255 | `mLCO2/min` |
| `whole_culture_bleed_rate` | 3.5882188014663874 | `L/d` |
| `side_stream_processed_rate` | 3.9869097794070965 | `L/d` |
| `side_stream_biomass_feed_rate` | 0.0031895278235256775 | `kgDW/d` |
| `recovered_biomass_rate` | 0.00287057504117311 | `kgDW/d` |
| `returned_uncaptured_biomass_rate` | 0.00031895278235256766 | `kgDW/d` |
| `concentrate_volume_rate` | 0.1435287520586555 | `L/d` |
| `required_filter_area` | 0.006725556308041661 | `m2` |
| `pump_electric_energy_rate` | 0.012059529759903521 | `kWh/d` |
| `annual_pump_electric_energy` | 3.6178589279710565 | `kWh/y` |
| `specific_pump_energy` | 4.201085004548492 | `kWh/kgDW` |
| `variable_opex_rate` | 0.0030148824399758804 | `EUR/d` |
| `annual_variable_opex` | 0.9044647319927641 | `EUR/y` |
| `specific_variable_cost` | 1.050271251137123 | `EUR/kgDW` |

The workbook concentrate result near `0.159476 L/d` is intentionally superseded by
`0.143529 L/d` because recovery is not applied twice. The fixture has no product price,
so no numeric margin output is expected.

## Required verification

### Contract and registration

1. The value-free input contract is canonical and digest-stable.
2. It contains exactly 20 required variables and one optional variable.
3. It embeds no value, default, recommendation, or fixture.
4. The bundled registration path creates or reuses the reviewed implementation
   idempotently and the 071 panel can select it.
5. Empty bindings report `20/0/20`; all required valid bindings report `20/20/0`.
6. Missing optional product price does not prevent preview state `ready`.

### Formula and dimensional tests

7. An independent calculation reproduces the corrected golden case.
8. Every output has the exact declared unit and finite numeric value.
9. Same normalized inputs produce byte-identical result JSON.
10. Productive volume scales inventory, production, nutrient demand, harvest, energy
    intensity denominator, and gas-rate benchmark as specified.
11. `maximum_specific_growth_rate` changes only the screening ratio.
12. Salt and stock-volume calculations reconcile mass and concentration.

### Harvest balance tests

13. Recovery = 1 makes side-stream processed equal whole-culture bleed and returned
    uncaptured biomass equal zero.
14. Lower recovery increases side-stream and filter area but does not change recovered
    biomass, whole-culture bleed comparison, or concentrate volume.
15. Side-stream feed equals recovered plus returned biomass at recovery < 1.
16. Concentrate volume equals recovered biomass divided by concentrate concentration
    and never divides by recovery twice.
17. Concentrate concentration at or below culture concentration fails deterministically.
18. Filter area scales inversely with filtration flux and filtration hours.
19. Event outputs scale inversely with event frequency without changing daily totals.

### Gas and inactive-input tests

20. Carbon demand, CO2 equivalent, O2 equivalent, and gas-rate benchmark remain
    separately named and independently scalable.
21. No kLa, gas utilization, degasser area, DO control, or blower-power output exists.
22. Residual N/P targets, pH, temperature, salinity, light/fouling, and validation-only
    workbook inputs are absent from the active contract.

### Energy and economics tests

23. Pump energy reconciles bound 047 pump power and circulation hours.
24. Specific pump energy and specific variable cost use recovered dry biomass on the
    same daily basis.
25. Product price absent yields explicit margin `not_computable` diagnostics and no
    numeric zero/partial margin output.
26. Product price present yields daily and annual gross-margin proxies with exact
    time-basis reconciliation.
27. Capital-cost workbook fixtures never enter variable OPEX.
28. Diagnostics expose included, excluded, and missing economic categories and never
    claim full TEA or total economic cost.

### Authority and failure tests

29. Manual bindings carry no fabricated source parameter ID.
30. Parameter-backed bindings preserve their verified source IDs.
31. Every input has explicit `uncertainty_state = "not_characterized"` in V0.
32. Two binding sets create distinct immutable simulation runs.
33. Successful outputs create proposed records only; nothing is promoted automatically.
34. Wrong units, non-finite values, absent required inputs, invalid domains, impossible
    concentration order, and unknown fields fail with bounded reasons.
35. Failed runs produce no successful result artifact or parameter proposals.
36. Tests run offline and make no provider, network, Ollama, workbook, or external-tool
    call.

## Files expected in implementation

Verify against current master before starting:

- `backend/app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.py`;
- one adjacent value-free contract JSON;
- focused script and real-runner integration tests;
- the smallest extension of the existing bundled-model registration service needed to
  register this second reviewed BlueRev model;
- `docs/specs/STATUS.md` for normal implementation lifecycle;
- this file only for implementation notes if concrete compatibility findings require it.

No frontend change is expected: 071 renders contracts generically.

Do not modify 047 equations, 071 DOF semantics, MemoryStore promotion authority, or
general runner policy merely to implement 048.

## Non-goals

048 does not provide:

- dynamic growth, acclimation, limitation, inhibition, contamination, or population
  models;
- residual-nutrient control or a complete liquid/material balance;
- carbonate equilibrium, alkalinity, pH, DIC, kLa, gas utilization, or DO dynamics;
- validated oxygen production or degassing performance;
- filter selection, fouling, cleaning-cycle, membrane-life, or discard-filtrate models;
- gas, harvesting, cleaning, control, thermal, labor, maintenance, or logistics cost;
- CAPEX, depreciation, financing, tax, LCA, or full TEA;
- automatic uncertainty propagation, Monte Carlo, sensitivity execution, optimization,
  inverse solving, or target selection;
- automatic promotion or automatic design selection;
- hidden defaults, silent zero substitution, or workbook execution.
