# 049 — BLUEREV-PROCESS-2: buoyancy and optical-transmission screening

Status: implementation-ready full specification. `docs/specs/STATUS.md` is authoritative.

Depends on: 043, 047

Related merged operator surface: 071

## Goal

Add one reviewed deterministic `calc_v0` forward model for two deliberately bounded
BlueRev M0 screening blocks:

1. hydrostatic displacement and auxiliary-flotation sizing from explicit mass,
   displacement, external-fluid-density, and safety-factor bindings;
2. tube/fouling and culture-transmission proxies from an explicit optical path.

The model exists to compare caller-selected scenarios. It is not a marine-stability
analysis, freeboard calculation, mooring analysis, wave-load model, flooding analysis,
structural certification, radiative-transfer model, photosynthesis model, or productivity
prediction.

No numerical fixture in this document is a selected Mark-1 value or product default.
Every project value remains an editable 071 binding.

## Maintainer direction

Use the smallest existing mechanisms:

- one reviewed repository script executed only through `calc_v0`;
- one immutable, value-free 071 input contract;
- explicit caller binding of accepted 047 outputs where appropriate;
- explicit manual or future CAD/evidence binding for masses and inherent displacement;
- the existing runner registration, hashing, timeout, artifact, log, simulation-run,
  proposal, and Domain Foundation boundaries;
- deterministic offline tests with independent arithmetic;
- no workbook runtime dependency;
- no CAD execution, FEM, CFD, optimizer, inverse solver, marine solver, spectral model,
  provider call, model call, background worker, or second scenario store.

## Source baseline and authority

External reference artifact:

- `BlueRev_Data_Model_v0_10_N_gaditana_refs_fixed.xlsx`;
- relevant sheets: `10_Model_Input`, `22_Data_Materials`, `30_To_Measure`,
  `40_Calculations`, and `70_Formula_Audit`;
- the workbook is a requirements and regression artifact, not executable truth;
- it is not stored in the repository and must not be read at runtime or in CI.

Workbook baseline relationships:

```text
fluid_mass = total_liquid_volume * liquid_density
wet_mass = tube_mass + fluid_mass
neutral_displacement = wet_mass / external_fluid_density

T_after_interval
= clean_tube_transmittance
  * (1 - fouling_loss_fraction_per_day) ^ cleaning_interval_days

combined_transmission_proxy
= T_after_interval
  * exp(-k_att * biomass_concentration * optical_path_length)
```

The workbook's `Floating` block includes only tube and liquid mass and applies no
explicit design safety factor. It also calls the light result a culture-center proxy while
using the full tube diameter as the attenuation path. 049 corrects those semantics:

- attached hardware and other supported payload mass are explicit inputs;
- the hydrostatic safety factor is explicit and applies to total supported wet mass;
- inherent sealed/non-flooded displacement is explicit rather than assumed;
- optical path length is an independent caller binding;
- no tube diameter is silently converted into a center path;
- the output is named a transmission proxy, not center irradiance.

## Model boundary

### Hydrostatic buoyancy boundary

049 calculates static vertical force equivalence through displaced external-fluid mass.
Gravity cancels from the volume relationships and is not a user input.

The supported mass scope is exactly:

- caller-supplied tube/material mass;
- contained process-liquid mass calculated from bound volume and density;
- attached hardware mass;
- other supported payload mass.

The calculation does not include a mass category unless the caller binds it through one
of those inputs. The script must not infer sensor, node, cable, manifold, float, cleaning,
mooring, biofouling, trapped-water, ice, personnel, maintenance, or storm loads.

`inherent_displacement_volume` represents only external volume that is actually sealed
or otherwise excludes water in the asserted operating condition. Floodable, vented, or
fully water-filled volume must not receive displacement credit.

`buoyancy_safety_factor` is a mass/displacement sizing multiplier. It is not a
certification factor, freeboard criterion, reserve-buoyancy rule, stability factor, wave
allowance, or regulatory approval.

### Optical boundary

The optical calculation is an M0 dimensionless screening proxy.

The tube/fouling relationship uses the workbook's discrete daily compounding form.
`fouling_loss_fraction_per_day` is therefore a fractional daily screening loss, not a
continuous kinetic constant.

The culture relationship is Beer-Lambert-like:

```text
optical_depth_proxy
= culture_attenuation_coefficient
  * operating_biomass_concentration
  * optical_path_length
```

The caller must bind `optical_path_length` directly. 049 does not derive it from tube
inner diameter, radius, orientation, sun angle, or cell trajectory.

The calculation does not represent:

- incident PAR or spectral irradiance;
- refraction, reflection, scattering, polarization, or wall curvature;
- radial or angular integration;
- flashing-light exposure history;
- solar geometry, shading, waves, immersion, or weather;
- pigment state, photoacclimation, photoprotection, or photoinhibition;
- coupling from light to growth or productivity.

## Exact input contract

The value-free 071 contract contains fourteen required variables and one optional
comparison variable.

| Name | Unit | Required | Category | Domain / meaning |
| --- | --- | --- | --- | --- |
| `tube_material_mass` | `kg` | yes | design | `>= 0`; caller-asserted material/assembly mass allocated to the supported tube system |
| `contained_liquid_volume` | `m3` | yes | design | `>= 0`; caller may bind accepted 047 `total_liquid_inventory` |
| `contained_liquid_density` | `kg/m3` | yes | property | `> 0` |
| `attached_hardware_mass` | `kg` | yes | equipment | `>= 0`; nodes, sensors, fittings, pump allocation, or other explicitly included hardware |
| `other_supported_payload_mass` | `kg` | yes | design | `>= 0`; bounded additional supported mass |
| `external_fluid_density` | `kg/m3` | yes | property | `> 0`; surrounding water density |
| `buoyancy_safety_factor` | `1` | yes | design | `>= 1`; explicit screening multiplier |
| `inherent_displacement_volume` | `m3` | yes | design | `>= 0`; caller-asserted sealed/non-flooded displacement already provided by the assembly |
| `clean_tube_transmittance` | `1` | yes | property | `> 0` and `<= 1` |
| `fouling_loss_fraction_per_day` | `1/d` | yes | model_parameter | `>= 0` and `< 1`; discrete fractional daily loss |
| `cleaning_interval` | `d` | yes | operating | `>= 0` |
| `culture_attenuation_coefficient` | `L/g/m` | yes | model_parameter | `>= 0`; to-measure screening coefficient |
| `operating_biomass_concentration` | `gDW/L` | yes | operating | `>= 0` |
| `optical_path_length` | `m` | yes | design | `> 0`; explicit attenuation path, never auto-derived |
| `available_auxiliary_flotation_volume` | `m3` | no | equipment | `> 0`; optional candidate volume for margin checking |

V0 performs no unit conversion. Equivalent unit strings are rejected.

The script accepts exactly all required names and at most the optional auxiliary-volume
name. Unknown names, absent required names, unknown keys inside an input item,
booleans, non-finite values, wrong units, and domain violations fail closed.

## Hydrostatic calculation contract

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
= max(
    0,
    design_required_displacement_volume - inherent_displacement_volume
  )
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
= inherent_displacement_volume + available_auxiliary_flotation_volume

buoyancy_volume_margin
= total_available_displacement_volume
  - design_required_displacement_volume

buoyancy_mass_margin
= buoyancy_volume_margin * external_fluid_density

displacement_utilization
= design_required_displacement_volume
  / total_available_displacement_volume
```

Additional numeric outputs:

- `total_available_displacement_volume`, `m3`;
- `buoyancy_volume_margin`, `m3`;
- `buoyancy_mass_margin`, `kg`;
- `displacement_utilization`, `1`.

Diagnostics report `buoyancy_check = "pass"` when the volume margin is nonnegative and
`"fail"` otherwise.

When the optional volume is absent, these four numeric outputs are absent and
diagnostics contain:

```json
{
  "buoyancy_availability_check": {
    "status": "not_computable",
    "reason": "missing_available_auxiliary_flotation_volume"
  }
}
```

Missing optional volume must not be replaced by zero.

## Optical calculation contract

```text
tube_transmittance_after_interval
= clean_tube_transmittance
  * (1 - fouling_loss_fraction_per_day) ^ cleaning_interval

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

The implementation must preserve all transmission outputs within `[0, 1]` subject to
floating-point tolerance. It must not label any output center light, absorbed PAR,
photosynthetic efficiency, or productivity.

## Successful result diagnostics

Required diagnostics include:

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

### Per-input provenance and uncertainty evidence

For every contract variable, diagnostics contain one bounded entry with:

- `binding_state = "parameter"`, `"manual"`, or `"missing_optional"`;
- `source_parameter_id` only when supplied by a verified parameter binding;
- `uncertainty_state = "not_characterized"`.

049 does not fabricate uncertainty intervals or modify equations based on uncertainty
metadata.

## Validation and failure semantics

Script-specific failures use one bounded stderr message:

```text
bluerev_calc_error:<reason>[:<field>]
```

Minimum reasons:

- `input_contract_invalid`;
- `input_unit_invalid`;
- `input_domain_invalid`;
- `result_invariant_invalid`.

A failed run emits no successful `outputs` object and creates no calc-derived parameter
proposals.

Required invariants:

- `design_supported_mass >= supported_wet_mass`;
- `design_required_displacement_volume >= neutral_buoyancy_displacement_volume`;
- `additional_auxiliary_flotation_required >= 0`;
- mass and displacement identities close within deterministic tolerance;
- all optical outputs are finite and within `[0, 1]`;
- `combined_transmission_proxy` equals the product of tube and culture proxies;
- optional margin identities close when auxiliary volume is supplied.

## Golden verification fixture

The following values are regression evidence only. They are not product defaults.

Inputs:

```text
tube_material_mass = 7.402220610388268 kg
contained_liquid_volume = 0.019137166941154067 m3
contained_liquid_density = 1025 kg/m3
attached_hardware_mass = 5 kg
other_supported_payload_mass = 2 kg
external_fluid_density = 1025 kg/m3
buoyancy_safety_factor = 1.3
inherent_displacement_volume = 0 m3
clean_tube_transmittance = 0.92
fouling_loss_fraction_per_day = 0.01 1/d
cleaning_interval = 7 d
culture_attenuation_coefficient = 1 L/g/m
operating_biomass_concentration = 0.8 gDW/L
optical_path_length = 0.03 m
available_auxiliary_flotation_volume = 0.05 m3
```

Expected values:

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

The liquid mass and optical values reproduce the workbook arithmetic. Hardware mass,
payload mass, safety factor, inherent displacement, and available flotation are added
only as explicit test-fixture inputs to verify the corrected 049 contract.

## Required tests

### Contract and authority

- the contract contains fourteen required variables and one optional variable;
- it contains no `value`, `default`, `recommended_value`, or `initial_guess` key;
- empty preview reports fourteen unresolved forward input DOF;
- optional auxiliary volume does not count toward structural required DOF;
- manual and parameter bindings preserve source authority;
- preview has no side effects;
- unknown names, wrong units, booleans, non-finite values, and domain violations fail.

### Independent equation verification

- independently reproduce every golden output;
- adding hardware or payload mass increases required displacement linearly;
- increasing safety factor increases design displacement but not neutral displacement;
- increasing external-fluid density decreases required displacement;
- increasing inherent displacement decreases only auxiliary flotation required;
- auxiliary volume below design requirement reports a negative margin and fail;
- auxiliary volume above design requirement reports a positive margin and pass.

### Optical metamorphic verification

- zero cleaning interval returns clean tube transmittance;
- zero fouling loss preserves clean tube transmittance for any interval;
- increasing cleaning interval cannot increase tube transmission when fouling loss is positive;
- zero attenuation coefficient or zero biomass concentration gives a culture-only proxy of one;
- increasing explicit optical path cannot increase culture or combined transmission;
- changing tube geometry elsewhere has no effect unless the caller changes the explicit path;
- the implementation never emits a `center_light` output.

### Runner and registration

- explicit bundled registration is idempotent and value-free;
- two valid scenarios create distinct immutable simulation runs;
- successful outputs become proposed parameters only through the existing MemoryStore facade;
- no workbook, network, provider, model, Ollama, CAD, FEM, CFD, or background execution occurs.

## Implementation shape

Implementation is one bounded follow-up PR containing only:

- one `calc_v0` script;
- one value-free contract JSON;
- focused backend tests;
- one idempotent bundled registration service/route extension;
- the smallest Domain Foundation registration update needed to expose the reviewed model;
- the canonical `048/049` lifecycle row update required by CI.

No new schema or frontend page is authorized.

## Non-goals

049 does not authorize:

- selected material, float, safety-factor, cleaning, or optical-path values;
- automatic CAD-derived mass or displacement;
- automatic binding from 047, 048, BLUECAD, or MemoryStore;
- hydrostatic stability, freeboard, trim, roll, pitch, center-of-gravity, or center-of-buoyancy calculations;
- wind, current, waves, slamming, fatigue, storms, mooring, anchors, or marine certification;
- structural stress or buckling analysis;
- flooding, leaks, damaged-state buoyancy, trapped water, or biofouling mass prediction;
- spectral/radiative-transfer, photosynthesis, growth, heat, or weather models;
- CFD, FEM, optimizer, inverse solver, parameter estimation, or autonomous design choice;
- silent promotion of any scenario value or result.
