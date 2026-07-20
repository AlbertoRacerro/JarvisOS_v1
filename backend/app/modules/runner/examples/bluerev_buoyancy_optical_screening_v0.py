import json
import math

REQUIRED_UNITS = {
    "tube_material_mass": "kg",
    "contained_liquid_volume": "m3",
    "contained_liquid_density": "kg/m3",
    "attached_hardware_mass": "kg",
    "other_supported_payload_mass": "kg",
    "external_fluid_density": "kg/m3",
    "buoyancy_safety_factor": "1",
    "inherent_displacement_volume": "m3",
    "clean_tube_transmittance": "1",
    "daily_fouling_loss_fraction": "1",
    "cleaning_interval": "d",
    "culture_attenuation_coefficient": "L/gDW/m",
    "operating_biomass_concentration": "gDW/L",
    "optical_path_length": "m",
}
OPTIONAL_UNITS = {"available_auxiliary_flotation_volume": "m3"}


def fail(reason, field_name=None):
    message = "bluerev_calc_error:" + reason
    if field_name is not None:
        message += ":" + field_name
    raise SystemExit(message)


with open("input.json", encoding="utf-8") as handle:
    inputs = json.load(handle)

if not isinstance(inputs, dict):
    fail("input_contract_invalid")
if not set(REQUIRED_UNITS).issubset(inputs):
    fail("input_contract_invalid")
if not set(inputs).issubset(set(REQUIRED_UNITS) | set(OPTIONAL_UNITS)):
    fail("input_contract_invalid")

expected_units = dict(REQUIRED_UNITS)
expected_units.update(OPTIONAL_UNITS)
values = {}
input_evidence = {}
for name, item in inputs.items():
    if not isinstance(item, dict):
        fail("input_contract_invalid", name)
    allowed_keys = {"value", "unit", "source_parameter_id"}
    if "value" not in item or "unit" not in item or not set(item).issubset(allowed_keys):
        fail("input_contract_invalid", name)
    value = item["value"]
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        fail("input_contract_invalid", name)
    if item["unit"] != expected_units[name]:
        fail("input_unit_invalid", name)
    values[name] = float(value)
    evidence = {
        "binding_state": "parameter" if item.get("source_parameter_id") else "manual",
        "uncertainty_state": "not_characterized",
    }
    if item.get("source_parameter_id"):
        evidence["source_parameter_id"] = item["source_parameter_id"]
    input_evidence[name] = evidence

if "available_auxiliary_flotation_volume" not in inputs:
    input_evidence["available_auxiliary_flotation_volume"] = {
        "binding_state": "missing_optional",
        "uncertainty_state": "not_characterized",
    }

nonnegative_fields = (
    "tube_material_mass",
    "contained_liquid_volume",
    "attached_hardware_mass",
    "other_supported_payload_mass",
    "inherent_displacement_volume",
    "daily_fouling_loss_fraction",
    "cleaning_interval",
    "culture_attenuation_coefficient",
    "operating_biomass_concentration",
)
for name in nonnegative_fields:
    if values[name] < 0:
        fail("input_domain_invalid", name)

positive_fields = (
    "contained_liquid_density",
    "external_fluid_density",
    "clean_tube_transmittance",
    "optical_path_length",
)
for name in positive_fields:
    if values[name] <= 0:
        fail("input_domain_invalid", name)

if values["buoyancy_safety_factor"] < 1:
    fail("input_domain_invalid", "buoyancy_safety_factor")
if values["clean_tube_transmittance"] > 1:
    fail("input_domain_invalid", "clean_tube_transmittance")
if values["daily_fouling_loss_fraction"] >= 1:
    fail("input_domain_invalid", "daily_fouling_loss_fraction")
if (
    "available_auxiliary_flotation_volume" in values
    and values["available_auxiliary_flotation_volume"] <= 0
):
    fail("input_domain_invalid", "available_auxiliary_flotation_volume")

contained_liquid_mass = values["contained_liquid_volume"] * values["contained_liquid_density"]
supported_wet_mass = (
    values["tube_material_mass"]
    + contained_liquid_mass
    + values["attached_hardware_mass"]
    + values["other_supported_payload_mass"]
)
design_supported_mass = supported_wet_mass * values["buoyancy_safety_factor"]
neutral_displacement = supported_wet_mass / values["external_fluid_density"]
design_displacement = design_supported_mass / values["external_fluid_density"]
auxiliary_required = max(0.0, design_displacement - values["inherent_displacement_volume"])

tube_transmission = values["clean_tube_transmittance"] * (
    1.0 - values["daily_fouling_loss_fraction"]
) ** values["cleaning_interval"]
optical_depth = (
    values["culture_attenuation_coefficient"]
    * values["operating_biomass_concentration"]
    * values["optical_path_length"]
)
culture_transmission = math.exp(-optical_depth)
combined_transmission = tube_transmission * culture_transmission

outputs = {
    "contained_liquid_mass": {"value": contained_liquid_mass, "unit": "kg"},
    "supported_wet_mass": {"value": supported_wet_mass, "unit": "kg"},
    "design_supported_mass": {"value": design_supported_mass, "unit": "kg"},
    "neutral_buoyancy_displacement_volume": {"value": neutral_displacement, "unit": "m3"},
    "design_required_displacement_volume": {"value": design_displacement, "unit": "m3"},
    "additional_auxiliary_flotation_required": {"value": auxiliary_required, "unit": "m3"},
    "tube_transmittance_after_interval": {"value": tube_transmission, "unit": "1"},
    "optical_depth_proxy": {"value": optical_depth, "unit": "1"},
    "culture_only_transmission_proxy": {"value": culture_transmission, "unit": "1"},
    "combined_transmission_proxy": {"value": combined_transmission, "unit": "1"},
}

availability_status = {
    "status": "not_computable",
    "reason": "missing_available_auxiliary_flotation_volume",
}
if "available_auxiliary_flotation_volume" in values:
    total_available = (
        values["inherent_displacement_volume"]
        + values["available_auxiliary_flotation_volume"]
    )
    volume_margin = total_available - design_displacement
    mass_margin = volume_margin * values["external_fluid_density"]
    utilization = design_displacement / total_available
    outputs.update(
        {
            "total_available_displacement_volume": {"value": total_available, "unit": "m3"},
            "buoyancy_volume_margin": {"value": volume_margin, "unit": "m3"},
            "buoyancy_mass_margin": {"value": mass_margin, "unit": "kg"},
            "displacement_utilization": {"value": utilization, "unit": "1"},
        }
    )
    availability_status = {
        "status": "computable",
        "buoyancy_check": "pass" if volume_margin >= 0 else "fail",
    }

for name, item in outputs.items():
    value = item["value"]
    if not math.isfinite(value):
        fail("result_invariant_invalid", name)

if design_supported_mass + 1e-12 < supported_wet_mass:
    fail("result_invariant_invalid", "design_supported_mass")
if design_displacement + 1e-12 < neutral_displacement:
    fail("result_invariant_invalid", "design_required_displacement_volume")
if auxiliary_required < -1e-12:
    fail("result_invariant_invalid", "additional_auxiliary_flotation_required")
if not math.isclose(
    design_supported_mass,
    supported_wet_mass * values["buoyancy_safety_factor"],
    rel_tol=1e-12,
    abs_tol=1e-15,
):
    fail("result_invariant_invalid", "design_supported_mass")
for name, value in (
    ("tube_transmittance_after_interval", tube_transmission),
    ("culture_only_transmission_proxy", culture_transmission),
    ("combined_transmission_proxy", combined_transmission),
):
    if value < -1e-12 or value > 1.0 + 1e-12:
        fail("result_invariant_invalid", name)
if not math.isclose(
    combined_transmission,
    tube_transmission * culture_transmission,
    rel_tol=1e-12,
    abs_tol=1e-15,
):
    fail("result_invariant_invalid", "combined_transmission_proxy")

result = {
    "schema_version": 1,
    "status": "succeeded",
    "outputs": outputs,
    "diagnostics": {
        "model_id": "bluerev_buoyancy_optical_screening_v0",
        "model_fidelity": "M0_static_screening",
        "hydrostatic_model": "archimedes_static_displacement_screening",
        "supported_mass_basis": "caller_asserted_explicit_mass_categories",
        "contained_liquid_mass_calculated_from_volume_and_density": True,
        "hardware_mass_explicit": True,
        "other_payload_mass_explicit": True,
        "inherent_displacement_basis": "caller_asserted_sealed_nonflooded_volume",
        "safety_factor_is_screening_multiplier": True,
        "gravity_cancels_from_displacement_volume": True,
        "buoyancy_availability_check": availability_status,
        "freeboard_not_evaluated": True,
        "stability_not_evaluated": True,
        "center_of_gravity_not_evaluated": True,
        "center_of_buoyancy_not_evaluated": True,
        "wave_loads_not_evaluated": True,
        "mooring_not_evaluated": True,
        "flooding_not_evaluated": True,
        "dynamic_immersion_not_evaluated": True,
        "optical_model": "beer_lambert_like_transmission_proxy",
        "fouling_model": "discrete_daily_compounding_proxy",
        "optical_path_basis": "caller_asserted_explicit_length",
        "optical_path_not_auto_derived": True,
        "center_light_not_claimed": True,
        "spectral_PAR_not_evaluated": True,
        "scattering_not_evaluated": True,
        "radial_light_field_not_evaluated": True,
        "light_growth_coupling_not_evaluated": True,
        "input_evidence": input_evidence,
        "workbook_runtime_dependency": False,
    },
}

with open("result.json", "w", encoding="utf-8") as handle:
    json.dump(result, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
