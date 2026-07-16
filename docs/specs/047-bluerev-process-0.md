# 047 — BLUEREV-PROCESS-0: verified geometry, circulation hydraulics, and pump power

Status: planned full-spec draft. `docs/specs/STATUS.md` is authoritative.

Depends on: 043

## Goal

Port the first BlueRev workbook calculation block into the existing `calc_v0`
runner as one reviewed, deterministic M0 screening calculation for tubular-loop
geometry, circulation hydraulics, pressure loss, and pump electrical power.

The implementation must reproduce the corrected baseline where the workbook is
physically coherent, make intentional corrections explicit, and reject ambiguous
or out-of-domain cases instead of silently returning plausible-looking numbers.

This is not a flowsheet, dynamic model, pump-selection tool, validated reactor
model, or digital twin. It is a unit-bearing and provenance-bearing static
screening baseline.

## Maintainer direction

Use the smallest existing mechanism:

- one reviewed repository script executed through `calc_v0`;
- the existing runner registration, hash, timeout, artifact, and MemoryStore
  proposal boundaries;
- deterministic offline tests;
- no new route, framework, generic equation engine, unit package, database table,
  or frontend surface.

The source workbook is a requirements and regression artifact, not executable
truth and not a runtime dependency.

## Source baseline

External reference artifact:

- `BlueRev_Data_Model_v0_10_N_gaditana_refs_fixed.xlsx`;
- relevant sheets: `10_Model_Input`, `40_Calculations`, `50_Sensitivity`, and
  `70_Formula_Audit`.

The implementation must not read the workbook at runtime or in CI. The formulas,
input contract, corrected definitions, and golden values required by this spec are
fully restated below.

Baseline inputs:

| Input | Value | Required unit | Meaning |
| --- | ---: | --- | --- |
| `tube_length` | 20 | `m` | Illuminated tube centerline length used by the M0 cylinder approximation. |
| `tube_inner_diameter` | 30 | `mm` | Hydraulic diameter and liquid-volume diameter. |
| `tube_outer_diameter` | 36 | `mm` | External geometric/illumination proxy diameter only. |
| `reservoir_liquid_volume` | 5 | `L` | Reservoir plus node/dead liquid inventory. |
| `target_liquid_velocity` | 0.25 | `m/s` | Mean tube velocity. |
| `liquid_density` | 1025 | `kg/m3` | Screening seawater density. |
| `dynamic_viscosity` | 0.0011 | `Pa*s` | Screening apparent dynamic viscosity. |
| `minor_loss_coefficient` | 8 | `1` | Lumped local-loss coefficient, explicitly provisional. |
| `pump_efficiency` | 0.35 | `1` | Wire-to-fluid screening efficiency. |

## Exact input contract

The reviewed script consumes the normal 043 `calc_v0` envelope. The named inputs
above are mandatory and each must contain exactly the caller-authoritative
`value`, exact canonical `unit`, and optional `source_parameter_id` allowed by 043.

V0 performs no unit conversion. Equivalent unit strings such as `cm`, `mPa*s`,
`kg/L`, `%`, or `L/min` are rejected rather than reinterpreted. Unit conversion
belongs to a later quantity/unit slice.

Validation is deterministic and fail-closed:

- all values must be finite real numbers; booleans are not numbers;
- `tube_length > 0`;
- `tube_inner_diameter > 0`;
- `tube_outer_diameter >= tube_inner_diameter`;
- `reservoir_liquid_volume >= 0`;
- `target_liquid_velocity > 0`;
- `liquid_density > 0`;
- `dynamic_viscosity > 0`;
- `minor_loss_coefficient >= 0`;
- `0 < pump_efficiency <= 1`.

Invalid domain, missing input, extra authoritative input, wrong unit, NaN, or
infinity fails before producing parameter proposals. Diagnostics may report
bounded field names and error codes, but never caller data beyond the accepted
numeric value and unit already present in the run artifact.

## Calculation contract

Use SI internally. Decimal formatting is not authoritative; numeric values and
canonical JSON bytes are.

Constants:

```text
pi = math.pi
g = 9.80665 m/s2
```

Derived inputs:

```text
D_i = tube_inner_diameter / 1000
D_o = tube_outer_diameter / 1000
V_res = reservoir_liquid_volume / 1000
```

### 1. Hydraulic cross-section

```text
A_i = pi * D_i^2 / 4
```

Output:

- `tube_hydraulic_cross_section_area`, unit `m2`.

`D_o` must have no effect on this output.

### 2. Liquid inventory

```text
V_tube = A_i * tube_length
V_total = V_tube + V_res
```

Outputs:

- `tube_liquid_volume`, unit `m3`;
- `total_liquid_inventory`, unit `m3`.

`V_total` is inventory, not productive volume, residence volume, or validated
hold-up. Biological productive-volume semantics belong to 048.

### 3. Geometric surface proxies

```text
A_external = pi * D_o * tube_length
A_internal = pi * D_i * tube_length
A_internal_over_V_tube = A_internal / V_tube
A_external_over_V_tube = A_external / V_tube
```

Outputs:

- `external_illuminated_area_proxy`, unit `m2`;
- `internal_wetted_area_to_tube_volume`, unit `1/m`;
- `external_area_to_tube_volume_proxy`, unit `1/m`.

The workbook's unlabeled `4 / D_i` surface-to-volume value is preserved only as
`internal_wetted_area_to_tube_volume`. It must not be presented as the external
illuminated-area ratio. `external_illuminated_area_proxy` remains a geometric
proxy; it does not account for shading, immersion, orientation, fouling, spectral
transmission, or active illuminated fraction.

### 4. Circulation flow

```text
Q = target_liquid_velocity * A_i
```

Output:

- `circulation_flow_rate`, unit `m3/s`.

This is recirculating loop flow, not feed, bleed, harvest, or net throughflow.

### 5. Time definitions

```text
t_tube = tube_length / target_liquid_velocity
t_inventory_turnover = V_total / Q
```

Outputs:

- `tube_nominal_transit_time`, unit `s`;
- `total_inventory_turnover_time`, unit `s`.

The implementation must not expose either value under the unqualified name
`residence_time`. In a recirculating loop, residence-time distribution, mean age,
feed/bleed residence time, and repeated cell exposure are different concepts.
No RTD or plug-flow claim is authorized by these two algebraic times.

### 6. Reynolds number and friction factor

```text
Re = liquid_density * target_liquid_velocity * D_i / dynamic_viscosity
```

Output:

- `reynolds_number`, unit `1`.

Use the Darcy friction factor:

```text
if Re < 2300:
    f_D = 64 / Re
elif Re >= 4000 and Re <= 100000:
    f_D = 0.3164 * Re^(-0.25)
else:
    reject as correlation_not_qualified
```

Output:

- `darcy_friction_factor`, unit `1`.

The transition interval `2300 <= Re < 4000` is rejected. Reynolds numbers above
the qualified V0 Blasius range are rejected. The script must not interpolate,
change correlation, or silently call a Fanning factor a Darcy factor.

### 7. Pressure loss and pump power

```text
q_dynamic = liquid_density * target_liquid_velocity^2 / 2
DeltaP_major = f_D * (tube_length / D_i) * q_dynamic
DeltaP_minor = minor_loss_coefficient * q_dynamic
DeltaP_total = DeltaP_major + DeltaP_minor
head = DeltaP_total / (liquid_density * g)
P_hydraulic = DeltaP_total * Q
P_electric = P_hydraulic / pump_efficiency
```

Outputs:

- `major_pressure_loss`, unit `Pa`;
- `minor_pressure_loss`, unit `Pa`;
- `total_pressure_loss`, unit `Pa`;
- `equivalent_static_head`, unit `m`;
- `hydraulic_power`, unit `W`;
- `pump_electric_power`, unit `W`.

`equivalent_static_head` is only a pressure-loss representation. It is not a pump
selection, available NPSH, shutoff head, transient pressure, or proof that the pump
can operate at the point. The result must carry diagnostics stating:

- `pump_curve_not_applied`;
- `npsh_not_evaluated`;
- `transient_pressure_not_evaluated`;
- `minor_loss_coefficient_provisional`.

## Output and diagnostic contract

The script writes one canonical `result.json` through the existing 043 contract.
Every numeric output above has a finite `value` and exact non-empty `unit`.

Required bounded diagnostics:

- `model_id = "bluerev_geometry_hydraulics_v0"`;
- `model_fidelity = "M0_static_screening"`;
- `friction_factor_convention = "Darcy"`;
- `friction_correlation` equal to `laminar_64_over_Re` or
  `blasius_smooth_pipe_v0`;
- `circulation_semantics = "closed_loop_recirculation"`;
- `time_semantics` listing the two qualified time outputs;
- `external_area_is_proxy = true`;
- the four pump-limit flags above;
- `workbook_runtime_dependency = false`.

Diagnostics are advisory metadata. Numeric outputs remain the only parameter
proposals created by the 043 MemoryStore facade.

## Corrected baseline golden case

For the baseline inputs in this spec, tests use tight deterministic tolerances and
expect approximately:

| Output | Expected value | Unit |
| --- | ---: | --- |
| `tube_hydraulic_cross_section_area` | 0.0007068583470577034 | `m2` |
| `tube_liquid_volume` | 0.014137166941154067 | `m3` |
| `total_liquid_inventory` | 0.019137166941154067 | `m3` |
| `external_illuminated_area_proxy` | 2.2619467105846507 | `m2` |
| `internal_wetted_area_to_tube_volume` | 133.33333333333334 | `1/m` |
| `external_area_to_tube_volume_proxy` | 160.0 | `1/m` |
| `circulation_flow_rate` | 0.00017671458676442585 | `m3/s` |
| `tube_nominal_transit_time` | 80.0 | `s` |
| `total_inventory_turnover_time` | 108.29421210522584 | `s` |
| `reynolds_number` | 6988.636363636363 | `1` |
| `darcy_friction_factor` | 0.03460496098364788 | `1` |
| `major_pressure_loss` | 738.9601043383144 | `Pa` |
| `minor_pressure_loss` | 256.25 | `Pa` |
| `total_pressure_loss` | 995.2101043383144 | `Pa` |
| `equivalent_static_head` | 0.09900798816714486 | `m` |
| `hydraulic_power` | 0.17586814233192632 | `W` |
| `pump_electric_power` | 0.5024804066626467 | `W` |

The head value intentionally uses exact standard gravity and therefore differs
slightly from a workbook value calculated with a rounded gravity constant.

## Files likely touched

Verify against current code before implementation. Stop and report conflicts.

Expected minimal scope:

- `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.py`
  (new reviewed `calc_v0` script);
- `backend/tests/runner/test_bluerev_geometry_hydraulics_v0.py` (new);
- `docs/specs/STATUS.md` only for the normal implementation lifecycle transition;
- this spec only if implementation notes reveal a real contract correction.

Existing 043 runner/service/safety code should not change. A required runtime
change is a blocker requiring explicit maintainer review, not an invitation to
expand 047.

## Required test battery

### Contract and runner integration

1. Register the exact reviewed script bytes through existing
   `create_model_implementation(..., implementation_kind="calc_v0",
   script_text=...)`.
2. Prove the stored artifact SHA-256 matches the reviewed repository file.
3. Run through the real existing `create_runner_job` and `run_runner_job`
   service path using an isolated test data root.
4. Prove one `result.json` artifact is registered and every declared output
   creates one proposed parameter through the existing all-or-nothing 043
   MemoryStore facade.
5. Prove no accepted/canonical parameter is created automatically.
6. Prove identical script bytes and canonical input bytes produce
   byte-identical `result.json` digests.

### Golden and independent calculations

7. Reproduce the complete baseline table above.
8. Independently calculate each golden value in the test without importing or
   calling implementation helpers from the reviewed script.
9. Assert the pressure-loss decomposition sums exactly within floating-point
   tolerance.
10. Assert hydraulic and electric power reconcile with pressure loss, flow, and
    efficiency.

### Metamorphic dependency tests

11. Change only `tube_outer_diameter`: external-area outputs change; hydraulic
    area, liquid inventory, flow, times, Reynolds, pressure loss, and power do
    not change.
12. Change only `tube_inner_diameter`: external illuminated area remains fixed;
    hydraulic area, tube volume, flow, Reynolds, losses, and power respond.
13. Change only `reservoir_liquid_volume`: only total inventory and total
    inventory turnover change.
14. Double `tube_length`: tube volume, both geometric areas, tube transit time,
    and major pressure loss double; flow, Reynolds, minor loss, and tube area do
    not.
15. Change only `minor_loss_coefficient`: only minor/total loss, head, and powers
    change.
16. Change only `pump_efficiency`: all hydraulic quantities remain fixed and
    only electric power changes inversely.

### Failure-mode tests

17. Reject missing, extra, wrongly-unitized, boolean, NaN, and infinite inputs.
18. Reject zero/negative length, inner diameter, velocity, density, viscosity,
    or efficiency.
19. Reject outer diameter below inner diameter, negative reservoir volume,
    negative minor-loss coefficient, and efficiency above one.
20. Construct a transitional-Reynolds input and prove deterministic rejection
    with `correlation_not_qualified` and zero parameter proposals.
21. Construct an above-range turbulent Reynolds input and prove the same bounded
    failure rather than extrapolation.
22. Prove the script cannot import non-043-allowed modules, access network,
    filesystem, environment, database, or ambient secrets; existing 043 policy
    remains authoritative.

## Acceptance criteria

1. The reviewed script runs unchanged through the merged 043 `calc_v0` path.
2. The complete corrected baseline is reproduced within declared test
   tolerances, with the intentional standard-gravity head difference documented.
3. Hydraulic area/liquid volume depend on `D_i`; external illuminated area
   depends on `D_o`; tests prove no cross-wiring.
4. The unqualified workbook label `residence time` is replaced by the two exact
   circulation-time definitions and no RTD claim is emitted.
5. Darcy/Fanning convention cannot be confused, transitional or extrapolated
   correlation use is rejected, and pressure-loss components reconcile.
6. Pump electric power is explicitly a screening estimate; curve, NPSH,
   transient, and provisional-local-loss limitations are machine-visible.
7. All outputs are finite, unit-bearing, deterministic proposed parameters with
   traceable runner/script/input provenance and no automatic promotion.
8. No workbook read, live provider, Ollama, network, external solver, or new
   dependency is needed in tests or runtime.
9. Full backend pytest and Ruff gates pass; existing 043 and runner behavior is
   unchanged.

## Non-goals

- No biology, growth, nutrients, gas exchange, harvesting, light attenuation,
  fouling, buoyancy, structural, CAPEX, OPEX, or specific-energy outputs; those
  remain in 048/049 or later work.
- No feed/bleed residence time, RTD, axial dispersion, tanks-in-series, CFD,
  dynamic state, recycle solver, or flowsheet graph.
- No pump catalogue, pump curve, duty-point search, NPSH, cavitation, startup,
  water hammer, wave/transient loading, or control logic.
- No unit parsing or conversion engine.
- No uncertainty propagation or parameter estimation.
- No new database schema, endpoint, frontend, background worker, or model
  orchestration system.
- No claim that the workbook, baseline, PMMA geometry, viscosity, local-loss
  coefficient, or pump efficiency is experimentally validated.
- No automatic promotion of model outputs or BlueRev design decisions.

## Promotion gate

047 may become `ready` only after review confirms:

- the current 043 runtime still supports the exact integration path stated here;
- the reviewed script can remain a pure `calc_v0` artifact with no runner change;
- the golden values and intentional corrections are accepted by the maintainer;
- no active PR overlaps the runner example/test files;
- the source workbook remains available as external evidence but is not needed
  for deterministic implementation or CI.
