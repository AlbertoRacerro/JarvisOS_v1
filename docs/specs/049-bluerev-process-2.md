# 049 — BLUEREV-PROCESS-2: buoyancy and optical-transmission screening

Status: implementation-ready full specification. `docs/specs/STATUS.md` is authoritative.

Depends on: 043, 047

Related merged operator surface: 071

## Goal

Add one reviewed deterministic `calc_v0` forward model for two bounded BlueRev M0 blocks:

1. hydrostatic displacement and auxiliary-flotation sizing from explicit mass,
   displacement, density, and safety-factor bindings;
2. tube/fouling and culture-transmission proxies from an explicit optical path.

This is a scenario-comparison model. It is not marine certification, stability,
freeboard, wave/mooring, structural, radiative-transfer, photosynthesis, or growth
prediction.

No fixture is a selected Mark-1 value or hidden default. Every project value remains an
editable 071 binding.

## Implementation direction

Use only existing mechanisms:

- one reviewed `calc_v0` repository script;
- one immutable value-free 071 input contract;
- explicit caller binding of accepted 047 outputs where appropriate;
- explicit manual or future CAD/evidence binding for mass and displacement;
- existing runner, hash, timeout, artifact, log, simulation-run, MemoryStore proposal,
  and Domain Foundation boundaries;
- deterministic offline tests with independent arithmetic;
- no workbook runtime, schema, CAD/FEM/CFD execution, optimizer, inverse solver,
  provider/model/Ollama call, background worker, or second scenario store.

## Source baseline and corrections

Reference artifact: `BlueRev_Data_Model_v0_10_N_gaditana_refs_fixed.xlsx`.
Relevant sheets are `10_Model_Input`, `22_Data_Materials`, `30_To_Measure`,
`40_Calculations`, and `70_Formula_Audit`.

The workbook is source evidence, not executable truth. Runtime and CI must not read it.

Workbook relationships reproduced as regression history:

```text
fluid_mass = total_liquid_volume * liquid_density
wet_mass = tube_mass + fluid_mass
neutral_displacement = wet_mass / external_fluid_density

T_after_interval
= clean_tube_transmittance
  * (1 - daily_fouling_loss_fraction) ^ (cleaning_interval / 1 day)

combined_transmission_proxy
= T_after_interval
  * exp(-k_att * biomass_concentration * optical_path_length)
```

049 corrects the workbook boundary:

- hardware and other supported payload mass are explicit;
- the safety factor is explicit and applies to total supported wet mass;
- inherent displacement is explicit and receives credit only when sealed/non-flooded;
- optical path is explicit and never inferred from tube diameter;
- the workbook full-diameter case is a fixture, not a center-light claim;
- the attenuation coefficient uses explicit dry-weight unit `L/gDW/m` rather than the
  workbook's generic `L/g/m` label.

## Hydrostatic boundary

The supported mass scope is exactly:

- caller-supplied tube/material mass;
- contained liquid mass calculated from bound volume and density;
- attached hardware mass;
- other supported payload mass.

No unbound category is inferred. Sensors, nodes, cables, manifolds, floats, cleaning
hardware, mooring, trapped water, biofouling, people, maintenance, and storm allowances
exist only when included in an explicit mass binding.

`inherent_displacement_volume` means external volume that actually excludes surrounding
water in the asserted operating condition. Floodable, vented, or water-filled volume
must not receive credit.

`buoyancy_safety_factor` is a screening multiplier, not a regulatory factor, freeboard
rule, reserve-buoyancy standard, or stability criterion.

## Optical boundary

The optical outputs are dimensionless M0 transmission proxies.

`daily_fouling_loss_fraction` is a dimensionless loss fraction for one nominal day. The
workbook's discrete daily compounding relationship is retained; it is not presented as a
continuous kinetic law.

The culture proxy is Beer-Lambert-like:

```text
optical_depth_proxy
= culture_attenuation_coefficient
  * operating_biomass_concentration
  * optical_path_length
```

The caller binds `optical_path_length`. 049 does not derive it from diameter, radius,
orientation, sun angle, or cell trajectory.

Not represented: incident/spectral PAR, reflection, refraction, scattering, curvature,
radial/angular integration, flashing light, solar geometry, weather, pigment state,
photoacclimation, photoprotection, photoinhibition, or light-to-growth coupling.

## Exact input contract

Fourteen required variables and one optional comparison variable:

| Name | Unit | Required | Category | Domain / meaning |
| --- | --- | --- | --- | --- |
| `tube_material_mass` | `kg` | yes | design | `>= 0`; caller-asserted supported tube/material mass |
| `contained_liquid_volume` | `m3` | yes | design | `>= 0`; may bind accepted 047 `total_liquid_inventory` |
| `contained_liquid_density` | `kg/m3` | yes | property | `> 0` |
| `attached_hardware_mass` | `kg` | yes | equipment | `>= 0`; explicitly included hardware |
| `other_supported_payload_mass` | `kg` | yes | design | `>= 0` |
| `external_fluid_density` | `kg/m3` | yes | property | `> 0` |
| `buoyancy_safety_factor` | `1` | yes | design | `>= 1` |
| `inherent_displacement_volume` | `m3` | yes | design | `>= 0`; sealed/non-flooded displacement |
| `clean_tube_transmittance` | `1` | yes | property | `> 0` and `<= 1` |
| `daily_fouling_loss_fraction` | `1` | yes | model_parameter | `>= 0` and `< 1`; loss fraction for one nominal day |
| `cleaning_interval` | `d` | yes | operating | `>= 0` |
| `culture_attenuation_coefficient` | `L/gDW/m` | yes | model_parameter | `>= 0`; to-measure screening coefficient |
| `operating_biomass_concentration` | `gDW/L` | yes | operating | `>= 0` |
| `optical_path_length` | `m` | yes | design | `> 0`; explicit attenuation path |
| `available_auxiliary_flotation_volume` | `m3` | no | equipment | `> 0`; optional candidate volume |

V0 performs no unit conversion. Equivalent unit strings are rejected.

The script accepts exactly all required names and at most the optional name. Unknown
names, missing required names, unknown input-item keys, booleans, non-finite values,
wrong units, and domain violations fail closed.

## Hydrostatic equations and outputs

```text
contained_liquid_mass
= contained_liquid_volume * contained_liquid_density

supported_wet_mass
= tube_material_mass
  + contained_liquid_mass
  + attached_hardware_mass
  + other_supported_payload_mass

design_supported_mass
= supported_wet_mass * buoyancy_safety_factor

neutral_buoyancy_displacement_volume
= supported_wet_mass / external_fluid_density

design_required_displacement_volume
= design_supported_mass / external_fluid_density

additional_auxiliary_flotation_required
= max(0,
      design_required_displacement_volume
      - inherent_displacement_volume)
```

Always-present outputs:

- `contained_liquid_mass`, `kg`;
- `supported_wet_mass`, `kg`;
- `design_supported_mass`, `kg`;
- `neutral_buoyancy_displacement_volume`, `m3`;
- `design_required_displacement_volume`, `m3`;
- `additional_auxiliary_flotation_required`, `m3`.

When `available_auxiliary_flotation_volume` is supplied:

```text
total_available_displacement_volume
= inherent_displacement_volume
  + available_auxiliary_flotation_volume

buoyancy_volume_margin
= total_available_displacement_volume
  - design_required_displacement_volume

buoyancy_mass_margin
= buoyancy_volume_margin * external_fluid_density

displacement_utilization
= design_required_displacement_volume
  / total_available_displacement_volume
```

Additional outputs:

- `total_available_displacement_volume`, `m3`;
- `buoyancy_volume_margin`, `m3`;
- `buoyancy_mass_margin`, `kg`;
- `displacement_utilization`, `1`.

Diagnostics report `buoyancy_check = "pass"` for nonnegative volume margin and
`"fail"` otherwise.

When optional volume is absent, the four numeric comparison outputs are absent and:

```json
{
  "buoyancy_availability_check": {
    "status": "not_computable",
    "reason": "missing_available_auxiliary_flotation_volume"
  }
}
```

Missing optional volume is never replaced by zero.

## Optical equations and outputs

```text
tube_transmittance_after_interval
= clean_tube_transmittance
  * (1 - daily_fouling_loss_fraction) ^ (cleaning_interval / 1 day)

optical_depth_proxy
= culture_attenuation_coefficient
  * operating_biomass_concentration
  * optical_path_length

culture_only_transmission_proxy
= exp(-optical_depth_proxy)

combined_transmission_proxy
= tube_transmittance_after_interval
  * culture_only_transmission_proxy
```

Outputs:

- `tube_transmittance_after_interval`, `1`;
- `optical_depth_proxy`, `1`;
- `culture_only_transmission_proxy`, `1`;
- `combined_transmission_proxy`, `1`.

Transmission outputs must remain in `[0, 1]` within deterministic tolerance. No output
may be labelled center light, absorbed PAR, photosynthetic efficiency, or productivity.

## Required diagnostics

- `model_id = "bluerev_buoyancy_optical_screening_v0"`;
- `model_fidelity = "M0_static_screening"`;
- `hydrostatic_model = "archimedes_static_displacement_screening"`;
- `supported_mass_basis = "caller_asserted_explicit_mass_categories"`;
- `contained_liquid_mass_calculated_from_volume_and_density = true`;
- `hardware_mass_explicit = true`;
- `other_payload_mass_explicit = true`;
- `inherent_displacement_basis = "caller_asserted_sealed_nonflooded_volume"`;
- `safety_factor_is_screening_multiplier = true`;
- `gravity_cancels_from_displacement_volume = true`;
- `freeboard_not_evaluated = true`;
- `stability_not_evaluated = true`;
- `center_of_gravity_not_evaluated = true`;
- `center_of_buoyancy_not_evaluated = true`;
- `wave_loads_not_evaluated = true`;
- `mooring_not_evaluated = true`;
- `flooding_not_evaluated = true`;
- `dynamic_immersion_not_evaluated = true`;
- `optical_model = "beer_lambert_like_transmission_proxy"`;
- `fouling_model = "discrete_daily_compounding_proxy"`;
- `optical_path_basis = "caller_asserted_explicit_length"`;
- `optical_path_not_auto_derived = true`;
- `center_light_not_claimed = true`;
- `spectral_PAR_not_evaluated = true`;
- `scattering_not_evaluated = true`;
- `radial_light_field_not_evaluated = true`;
- `light_growth_coupling_not_evaluated = true`;
- `workbook_runtime_dependency = false`.

For every contract variable, diagnostics also contain:

- `binding_state = "parameter"`, `"manual"`, or `"missing_optional"`;
- `source_parameter_id` only for verified parameter bindings;
- `uncertainty_state = "not_characterized"`.

049 does not fabricate uncertainty intervals or alter equations from uncertainty metadata.

## Failure and invariants

Script failures use:

```text
bluerev_calc_error:<reason>[:<field>]
```

Minimum reasons:

- `input_contract_invalid`;
- `input_unit_invalid`;
- `input_domain_invalid`;
- `result_invariant_invalid`.

A failed run emits no successful outputs and creates no calc-derived proposals.

Required invariants:

- design mass is not below wet mass;
- design displacement is not below neutral displacement;
- auxiliary flotation required is nonnegative;
- mass and displacement identities close within deterministic tolerance;
- optical outputs are finite and in `[0, 1]`;
- combined transmission equals tube transmission times culture transmission;
- optional margin identities close when auxiliary volume is supplied.

## Golden verification fixture

Regression evidence only, never product defaults.

```text
tube_material_mass = 7.402220610388268 kg
contained_liquid_volume = 0.019137166941154067 m3
contained_liquid_density = 1025 kg/m3
attached_hardware_mass = 5 kg
other_supported_payload_mass = 2 kg
external_fluid_density = 1025 kg/m3
buoyancy_safety_factor = 1.3
inherent_displacement_volume = 0 m3
clean_tube_transmittance = 0.92 1
daily_fouling_loss_fraction = 0.01 1
cleaning_interval = 7 d
culture_attenuation_coefficient = 1 L/gDW/m
operating_biomass_concentration = 0.8 gDW/L
optical_path_length = 0.03 m
available_auxiliary_flotation_volume = 0.05 m3
```

Expected:

```text
contained_liquid_mass = 19.61559611468292 kg
supported_wet_mass = 34.017816725071185 kg
design_supported_mass = 44.22316174259254 kg
neutral_buoyancy_displacement_volume = 0.03318811387811823 m3
design_required_displacement_volume = 0.04314454804155370 m3
additional_auxiliary_flotation_required = 0.04314454804155370 m3
total_available_displacement_volume = 0.05 m3
buoyancy_volume_margin = 0.00685545195844630 m3
buoyancy_mass_margin = 7.026838257407458 kg
displacement_utilization = 0.862890960831074

tube_transmittance_after_interval = 0.8575001200744308
optical_depth_proxy = 0.024
culture_only_transmission_proxy = 0.9762857097579093
combined_transmission_proxy = 0.8371651133443581
```

Liquid mass and optical outputs reproduce workbook arithmetic. Hardware, payload,
safety factor, inherent displacement, and available flotation are explicit fixture inputs
for the corrected contract.

## Required tests

### Contract and authority

- fourteen required inputs and one optional input;
- no `value`, `default`, `recommended_value`, or `initial_guess` keys;
- empty preview reports fourteen unresolved DOF;
- optional volume does not count toward required DOF;
- manual and parameter authority are preserved;
- preview is side-effect-free;
- invalid names, keys, values, units, and domains fail closed.

### Independent and metamorphic verification

- reproduce all golden outputs independently;
- hardware/payload mass increases required displacement linearly;
- safety factor changes design but not neutral displacement;
- higher external density lowers required displacement;
- inherent displacement reduces only auxiliary flotation required;
- supplied auxiliary volume produces correct positive/negative margins and pass/fail;
- zero interval returns clean tube transmission;
- zero fouling preserves clean tube transmission;
- positive fouling plus longer interval cannot increase transmission;
- zero attenuation or zero biomass gives culture transmission one;
- increasing explicit optical path cannot increase transmission;
- changing geometry elsewhere has no effect unless explicit path/mass/volume bindings change;
- no `center_light` output exists.

### Runner and registration

- bundled registration is explicit, idempotent, and value-free;
- distinct valid scenarios create distinct immutable runs;
- successful outputs become proposed parameters only through existing MemoryStore authority;
- no workbook, network, provider, model, Ollama, CAD, FEM, CFD, or background execution.

## Implementation shape

One bounded implementation PR may contain only:

- one `calc_v0` script;
- one value-free contract JSON;
- focused backend tests;
- one idempotent bundled registration service/route extension;
- the smallest Domain Foundation registration update;
- the canonical 049 lifecycle update required by CI.

No new schema or frontend page is authorized.

## Non-goals

No selected material, float, safety factor, cleaning interval, attenuation coefficient, or
optical path; no automatic CAD-derived mass/displacement or automatic upstream binding;
no freeboard/stability/trim/CG/CB, waves/current/wind/slamming/fatigue/mooring/anchors,
structural analysis, flooding/damage-state buoyancy, spectral/radiative-transfer,
photosynthesis/growth/heat/weather model, optimizer, inverse solver, parameter estimation,
or autonomous design choice.
