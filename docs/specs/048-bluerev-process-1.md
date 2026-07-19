# 048 — BLUEREV-PROCESS-1: biomass, nutrients, gas, harvest, energy, and preliminary economics

Status: planned definition draft. `docs/specs/STATUS.md` is authoritative. This
document does not authorize implementation and must not be promoted to `ready`
until every promotion blocker below is closed with source-bound evidence.

Depends on: 043, 047

Related merged operator surface: 071

## Goal

Port the next BlueRev workbook block into one reviewed, deterministic `calc_v0`
forward model for:

- biological productive-volume semantics;
- biomass inventory and production rate;
- nitrogen, phosphorus, and carbon demand;
- bounded gas-demand and degassing proxies;
- semi-continuous harvest, recovered biomass, concentrate, and filtration sizing;
- pump and declared auxiliary energy;
- preliminary variable operating-cost and margin proxies.

The result must be useful for comparing operator-selected BlueRev scenarios without
pretending that the workbook is a validated biological model, a gas-transfer model,
a complete equipment design, or a techno-economic assessment.

This definition freezes known corrections and the evidence needed to finish the
contract. It deliberately does not invent workbook formulas that are not available
in the repository.

## Maintainer direction

Use the existing mechanisms only:

- one reviewed repository script executed through `calc_v0` after the full formula
  contract is frozen;
- the merged 047 outputs as explicit caller-bound inputs where needed, never by
  reading another run or a workbook at runtime;
- the merged 071 model contract, binding preview, and scenario panel;
- the existing runner registration, hash, timeout, artifact, log, simulation-run,
  and MemoryStore proposal boundaries;
- deterministic offline tests with independent calculations;
- no workbook runtime dependency;
- no new equation engine, optimizer, workflow engine, TEA framework, unit package,
  background worker, provider call, model call, or second scenario store.

No numerical fixture in this document is a selected Mark-1 value or product default.

## Source baseline and current evidence

External reference artifact identified by the prior workbook audit:

- `BlueRev_Data_Model_v0_10_N_gaditana_refs_fixed.xlsx`;
- principal sheets: `10_Model_Input`, `40_Calculations`, `50_Sensitivity`, and
  `70_Formula_Audit`;
- workbook formulas are concentrated in `01_Dashboard`, `40_Calculations`, and
  `50_Sensitivity`;
- the workbook lookup pattern resolves input IDs from `10_Model_Input` through an
  `INDEX(..., MATCH(...))` lookup.

The workbook is not stored in this repository and must not become a runtime or CI
input. Before this definition may become implementation-ready, the relevant ranks
8–18 must be transcribed into this document with exact source locations, original
formulas, corrected formulas, units, validity domains, and verification cases.

### Audited workbook inputs already known

These values are regression fixtures from the workbook audit, not defaults:

| Parameter ID | Fixture value | Workbook unit / meaning |
| --- | ---: | --- |
| `X_set` | 0.8 | `gDW/L`, target broth biomass concentration |
| `P_vol` | 0.15 | `gDW/L/d`, volumetric biomass productivity |
| `mu_max` | 0.4 | `1/d`, maximum specific growth-rate reference |
| `gN_gDW` | 0.06 | `gN/gDW`, biomass nitrogen requirement |
| `gP_gDW` | 0.008 | `gP/gDW`, biomass phosphorus requirement |
| `gC_gDW` | 0.5 | `gC/gDW`, biomass carbon requirement |
| `N_res_target_mg_L` | 2 | `mgN/L`, residual nitrogen target |
| `P_res_target_mg_L` | 0.2 | `mgP/L`, residual phosphorus target |
| `feed_events_per_d` | 1 | `1/d`, nominal daily feed/harvest events |
| `stock_N_mgN_mL` | 20 | `mgN/mL`, nitrogen stock concentration |
| `stock_P_mgP_mL` | 2 | `mgP/mL`, phosphorus stock concentration |
| `stock_C_mgC_mL` | 20 | `mgC/mL`, carbon stock concentration |
| `DO_target_pct` | 150 | `% saturation`, operating reference only |
| `DO_alarm_pct` | 200 | `% saturation`, alarm reference only |
| `CO2_spec_mL_L_min` | 0.8 | `mL gas/L/min`, nominal gas-dose proxy |
| `degasser_gas_velocity_m_s` | 0.04 | `m/s`, degasser superficial-velocity proxy |
| `harvest_recovery` | 0.9 | `1`, recovered-product fraction |
| `X_concentrate_g_L` | 20 | `gDW/L`, concentrate solids concentration |
| `filter_flux_LMH` | 24.7 | `L/m2/h`, filtration flux fixture |
| `electricity_EUR_kWh` | 0.25 | `EUR/kWh`, electricity-price fixture |
| `op_days_y` | 300 | `d/y`, annual operating-days fixture |

The following audited fields are intentionally not consumed by 048 unless the final
formula extraction proves they belong here:

- `tube_transmittance`, `fouling_loss_pct_d`, `cleaning_interval_d`, and
  `k_att_L_g_m` belong primarily to 049 light/transmittance work;
- `node_cost_EUR`, `pump_cost_EUR`, and `sensor_cost_EUR` are capital-cost fixtures
  and must not be silently included in variable OPEX;
- blank `OD_DW_factor`, `v_min_susp_m_s`, and `shear_limit_Pa` values remain missing
  measurements, never zeroes.

## Known corrections that are binding

### 1. Productive volume must be explicit

047 distinguishes:

- `tube_liquid_volume`;
- `total_liquid_inventory`.

048 must not silently rename either quantity as productive volume. The final contract
must require an explicit productive-volume basis that is visible in the input and
result diagnostics. Acceptable directions for the final spec are limited to:

1. an explicitly bound upstream 047 volume whose whole inventory is asserted to be
   biologically productive; or
2. an explicit productive-volume value with provenance; or
3. a bound inventory multiplied by an explicit active-volume fraction.

The implementation must reject an absent or contradictory basis. A regression fixture
may choose one basis for testing, but no basis may become a product default.

### 2. Recovery must not corrupt the reactor harvest balance

For a steady or quasi-steady semi-continuous comparison, the amount of broth removed
to maintain the reactor biomass inventory is governed by net biomass production and
broth concentration. Downstream recovery affects recovered product and losses; it
must not silently increase or decrease the reactor broth withdrawal.

The final equations must preserve the distinction between at least:

- gross biomass removed from the reactor;
- recovered biomass product;
- unrecovered biomass loss;
- harvest broth volume;
- concentrate volume.

A formula that divides the reactor harvest volume by `harvest_recovery` is rejected
unless a separately named make-up or compensation policy is explicitly modeled and
mass-balanced.

### 3. Pump-only energy is not total process energy

047 supplies `pump_electric_power`. 048 may calculate pump energy on an explicit
operating-time basis. It must never label pump energy or pump electricity cost as
`total_energy`, `total_electricity`, `total_opex`, or an equivalent complete KPI.

Every energy and cost result must carry a machine-readable completeness boundary:

- included loads;
- excluded loads;
- missing loads;
- time basis;
- whether a total is computable.

Gas handling, filtration/harvest, controls, cleaning, thermal management, and other
loads are excluded unless an explicit input or reviewed submodel represents them.

### 4. Missing economic inputs produce `not_computable`

The workbook audit confirms an electricity-price fixture but does not establish all
prices, consumable costs, product price, operating-time bases, or auxiliary loads
required for a complete economic result.

The `preliminary_economic_evaluation_v0` family must therefore support explicit
`not_computable` outcomes. Missing data must never be replaced by zero and a partial
boundary must never be presented as a full economic value.

## Candidate calculation families to freeze after extraction

The names below define the required semantic separation. Exact equations remain
blocked until the source extraction table is complete.

### A. Volume, biomass, and productivity

Required candidate outputs:

- `biological_productive_volume`, `m3`;
- `biomass_inventory`, `kgDW`;
- `gross_biomass_production_rate`, `kgDW/d`;
- `specific_productivity_check`, `1/d`, only when its denominator is defined;
- `productive_volume_basis_code`, diagnostic metadata.

The final spec must reconcile `P_vol`, `mu_max`, and `X_set` without implying that a
volumetric-productivity fixture is mechanistically derived from `mu_max` unless the
workbook formula and biological assumptions explicitly do so.

### B. Nutrient and carbon demand

Required semantic families:

- stoichiometric biomass-incorporation demand for N, P, and C;
- residual-inventory or residual-replacement requirement, if and only if the final
  mass-balance boundary defines feed/makeup concentration and replacement volume;
- total declared addition rate;
- stock-solution dosing volume per day and per feed event;
- omitted or uncharacterized losses as diagnostics, never hidden factors.

A residual target alone is not a nutrient-consumption model. The final formula must
state whether incoming makeup contains nutrients, whether the residual inventory is
already established, and whether the calculation is initial charge, replacement,
or daily metabolic demand.

### C. Gas and degassing proxies

At least three different quantities must remain separate:

- stoichiometric carbon demand;
- nominal gas-dose flow derived from `CO2_spec_mL_L_min` and an explicit liquid-volume
  basis;
- any degasser area or capacity proxy derived from a declared gas volumetric flow and
  `degasser_gas_velocity_m_s`.

No gas-transfer efficiency, CO2 utilization, oxygen-production rate, kLa, mass-transfer
coefficient, compressor/blower duty, or degassing performance may be inferred without
an explicit input or reviewed correlation.

`DO_target_pct` and `DO_alarm_pct` are operating references. They are not sufficient
to calculate oxygen mass transfer or degasser duty.

### D. Harvest and filtration

Required candidate outputs:

- `harvest_broth_volume_rate`, `L/d`;
- `gross_harvested_biomass_rate`, `kgDW/d`;
- `recovered_biomass_rate`, `kgDW/d`;
- `unrecovered_biomass_loss_rate`, `kgDW/d`;
- `concentrate_volume_rate`, `L/d`;
- `required_filter_area`, `m2`, only with an explicit filtration-time basis;
- `harvest_events_per_day` and `harvest_volume_per_event` when event semantics are
  included.

`filter_flux_LMH` cannot produce area from a daily volume without an explicit number
of filtration operating hours per day or per event. Using 24 hours or one event as a
silent default is forbidden.

### E. Energy and operating-cost boundary

Required energy separation:

- `pump_electric_energy_rate`, such as `kWh/d`, with explicit circulation hours;
- separately declared gas, harvest, controls, cleaning, thermal, or other loads;
- `known_electric_energy_rate`, the sum of represented loads;
- `total_electric_energy_rate` only when the declared completeness gate is satisfied;
- annualized values only from an explicit operating-days basis.

Required `preliminary_economic_evaluation_v0` family:

- `variable_opex_rate`;
- `specific_variable_cost`;
- `gross_margin_proxy`.

Each member has a parallel machine-readable status:

- `computable`;
- `not_computable` with bounded missing-input and boundary reason codes.

When computable:

- `variable_opex_rate` sums only named included variable-cost categories;
- `specific_variable_cost` divides the compatible-time-basis variable OPEX by
  recovered biomass, not gross production or reactor inventory;
- `gross_margin_proxy` uses recovered biomass, an explicit product-price input, and
  a compatible time basis, then subtracts the same declared variable-OPEX boundary.

The numeric `outputs` object remains compatible with the existing 043 requirement
that outputs are finite numbers with units. A non-computable KPI is omitted from
numeric outputs and represented explicitly in bounded diagnostics; it is never
emitted as zero, NaN, infinity, or a partial number under the full KPI name.

Required diagnostic metadata includes:

- `economic_model_id = "preliminary_economic_evaluation_v0"`;
- `economic_boundary` listing included, excluded, and missing categories;
- `economic_basis` naming the time and product-mass basis;
- per-KPI status and missing-input reason codes;
- `full_tea = false`;
- `capex_included = false` unless a later reviewed amendment says otherwise;
- `workbook_runtime_dependency = false`.

## Provenance and uncertainty blocker

Current 043 `calc_v0` items preserve numeric `value`, exact `unit`, and optional
`source_parameter_id`. That is sufficient for basic provenance but not for an
immutable per-run snapshot of uncertainty metadata.

048 must not claim per-input uncertainty support merely because a source parameter ID
exists. Before promotion to `ready`, the definition must select and test one bounded
mechanism that snapshots, for every decision-relevant input:

- uncertainty kind;
- lower/upper bound or equivalent bounded representation;
- confidence or evidence-quality state where available;
- source record identity;
- explicit `not_characterized` when uncertainty is missing.

Recommended direction: a minimal additive, generic input-metadata snapshot associated
with the immutable simulation-run input, populated by the existing binding service
from current Parameter records. The calculation script should receive only the
numeric values it needs; uncertainty metadata should remain inspectable evidence and
must not silently alter equations. This recommendation requires a separately reviewed
contract amendment if it changes 043/071 storage or API semantics.

Companion numeric pseudo-inputs for every uncertainty field are not recommended: they
inflate the engineering DOF count and confuse model variables with evidence metadata.

## Exact formula-extraction gate

Before this definition can become a full implementation-ready spec, add one row for
every workbook rank 8–18 calculation:

| Rank / output | Source sheet and cell | Original Excel formula | Referenced input IDs | Original unit | Corrected equation | Corrected unit | Validity domain | Verification case | Correction rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

The completed table must establish at least:

1. which 047 volume output, explicit volume, or active fraction defines productive
   volume;
2. biomass inventory and production equations;
3. N/P/C demand, residual, stock-dose, and event-basis equations;
4. carbon-demand versus gas-dose semantics;
5. harvest, recovery, concentrate, and filter-area balances;
6. operating hours and annualization bases;
7. every included energy load and the completeness rule;
8. every economic price/cost input and the exact `not_computable` conditions;
9. independent numerical golden cases and failure cases;
10. every intentional difference from workbook output.

A screenshot, cached value, dashboard label, or apparent numerical agreement is not a
formula contract.

## Required additional inputs to resolve

The final extraction may rename or remove these, but it must explicitly resolve the
underlying information gaps rather than assume values:

- productive-volume basis and, when used, active-volume fraction;
- circulation operating hours per day;
- filtration operating hours per day or per event;
- makeup/feed N and P concentrations when residual replacement is calculated;
- carbon-source identity and carbon-to-delivered-CO2 or carbon-source conversion;
- gas composition, standard-state basis, and utilization fraction when a gas mass
  balance is claimed;
- gas-handling power or specific energy if gas electricity is included;
- filtration/harvest power, specific energy, or consumable cost if included;
- nutrient and carbon-source prices if included in variable OPEX;
- product price and saleable-product basis for gross margin;
- any cleaning, thermal, controls, or other variable loads included in a total;
- uncertainty and provenance snapshot fields for every decision-relevant input.

Missing entries remain missing and drive explicit non-computable statuses.

## Validation and failure semantics

The final implementation must retain the existing 043 envelope and use bounded script
diagnostics without adding runner error codes merely for 048.

Required stable script reasons must include at least:

- `input_contract_invalid`;
- `input_unit_invalid`;
- `input_domain_invalid`;
- `productive_volume_basis_invalid`;
- `mass_balance_invalid`;
- `time_basis_missing`;
- `economic_basis_incompatible`;
- `correlation_not_qualified`.

Invalid physical inputs fail the run. Missing optional economic inputs do not fail an
otherwise valid biological/harvest run; they produce explicit economic
`not_computable` diagnostics.

## Required verification before implementation merge

### Source and equation evidence

1. Every rank 8–18 formula is source-located and restated independently of the
   workbook runtime.
2. Every corrected formula has a dimensional derivation and one independent numerical
   calculation.
3. Workbook values are fixtures only and are never product defaults.

### Mass-balance tests

4. Productive volume changes biomass inventory and production linearly and changes no
   unrelated geometry output.
5. Gross harvested biomass closes against production under the declared steady-state
   boundary.
6. Recovered plus unrecovered biomass equals gross harvested biomass.
7. Changing `harvest_recovery` changes recovered/lost product but not reactor broth
   withdrawal under the default balance semantics.
8. Concentrate volume reconciles recovered biomass and concentrate concentration.
9. Filter area scales with harvest volume and inversely with flux and declared
   filtration hours.

### Nutrient and gas tests

10. N/P/C stoichiometric demand scales with biomass production and composition factors.
11. Stock dosing reconciles mass and stock concentration with exact unit conversion.
12. Residual-target additions are excluded or explicitly balanced; no residual target
    is treated as metabolic consumption.
13. Carbon demand, gas-dose proxy, and degasser proxy remain separately named and
    independently testable.

### Energy and economics tests

14. Pump energy reconciles 047 pump power and the explicit operating-time basis.
15. Omitting an auxiliary load prevents a complete-total claim when that load is inside
    the selected economic boundary.
16. Missing product price, recovery, or compatible time basis yields
    `gross_margin_proxy = not_computable`, never zero or a partial numeric output.
17. `specific_variable_cost` uses recovered saleable biomass and the identical time
    basis as variable OPEX.
18. Capital-cost fixtures do not enter variable OPEX.
19. Annualization uses explicit operating days and preserves daily/annual
    reconciliation.

### Provenance and determinism tests

20. Every input preserves exact unit and source identity when supplied.
21. Every input has an immutable uncertainty snapshot or explicit
    `not_characterized` evidence under the selected metadata contract.
22. Same inputs and metadata produce byte-identical canonical result JSON.
23. Failed runs produce no successful result artifact or parameter proposals.
24. Successful numeric outputs create proposed records only; nothing is promoted
    automatically.

## Files likely touched by the future implementation

Verify against current master after this definition is promoted to `ready`:

- one reviewed script under `backend/app/modules/runner/examples/`;
- one value-free 071 input contract artifact;
- focused calculation and runner integration tests;
- the smallest approved uncertainty/provenance snapshot surface if the promotion
  blocker requires it;
- `docs/specs/STATUS.md` for normal implementation lifecycle;
- this document for final source table and implementation notes.

Do not modify the 047 formulas, 071 DOF semantics, MemoryStore promotion authority,
or general runner policy to make 048 easier.

## Non-goals

This slice does not provide:

- dynamic growth, acclimation, inhibition, contamination, or population models;
- validated oxygen or CO2 mass-transfer, kLa, CFD, or gas-equilibrium models;
- filter selection, fouling, cleaning-cycle, or membrane-life prediction;
- complete electrical design, controls design, thermal model, or maintenance model;
- CAPEX, depreciation, financing, tax, labor, logistics, land/sea lease, or full TEA;
- automatic uncertainty propagation, Monte Carlo analysis, sensitivity execution, or
  optimization;
- automatic promotion of inputs, outputs, or design decisions;
- hidden defaults, silent zero substitution, or workbook execution.

## Promotion blockers

048 remains `planned` until all of the following are complete:

1. the exact workbook ranks 8–18 extraction table is filled;
2. productive-volume basis is selected and justified;
3. recovery/harvest balance is independently verified;
4. missing time, energy, price, and consumable inputs are resolved or explicitly
   classified as non-computable;
5. the uncertainty/provenance snapshot contract is accepted through the normal spec
   process;
6. complete input, output, diagnostic, validity, golden-case, and failure contracts
   are frozen;
7. the registry is deliberately promoted to `ready` in a separate maintainer-approved
   change.
