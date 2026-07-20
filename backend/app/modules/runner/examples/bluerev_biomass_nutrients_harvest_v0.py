import json
import math

REQUIRED_UNITS = {
    "productive_liquid_volume": "m3",
    "operating_biomass_concentration": "gDW/L",
    "volumetric_productivity": "gDW/L/d",
    "maximum_specific_growth_rate": "1/d",
    "operating_days_per_year": "d/y",
    "feed_events_per_day": "1/d",
    "biomass_nitrogen_fraction": "gN/gDW",
    "biomass_phosphorus_fraction": "gP/gDW",
    "biomass_carbon_fraction": "gC/gDW",
    "nitrogen_stock_concentration": "mgN/mL",
    "phosphorus_stock_concentration": "mgP/mL",
    "carbon_stock_concentration": "mgC/mL",
    "co2_specific_gas_rate": "mLCO2/L/min",
    "harvest_recovery": "1",
    "concentrate_biomass_concentration": "gDW/L",
    "filtration_flux": "L/m2/h",
    "filtration_operating_hours_per_day": "h/d",
    "pump_electric_power": "W",
    "circulation_operating_hours_per_day": "h/d",
    "electricity_price": "EUR/kWh",
}
OPTIONAL_UNITS = {"product_price": "EUR/kgDW"}


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

if "product_price" not in inputs:
    input_evidence["product_price"] = {
        "binding_state": "missing_optional",
        "uncertainty_state": "not_characterized",
    }

positive_fields = (
    "productive_liquid_volume",
    "operating_biomass_concentration",
    "volumetric_productivity",
    "maximum_specific_growth_rate",
    "operating_days_per_year",
    "feed_events_per_day",
    "biomass_carbon_fraction",
    "nitrogen_stock_concentration",
    "phosphorus_stock_concentration",
    "carbon_stock_concentration",
    "harvest_recovery",
    "concentrate_biomass_concentration",
    "filtration_flux",
    "filtration_operating_hours_per_day",
    "circulation_operating_hours_per_day",
)
for name in positive_fields:
    if values[name] <= 0:
        fail("input_domain_invalid", name)

nonnegative_fields = (
    "biomass_nitrogen_fraction",
    "biomass_phosphorus_fraction",
    "co2_specific_gas_rate",
    "pump_electric_power",
    "electricity_price",
)
for name in nonnegative_fields:
    if values[name] < 0:
        fail("input_domain_invalid", name)

fraction_fields = (
    "biomass_nitrogen_fraction",
    "biomass_phosphorus_fraction",
    "biomass_carbon_fraction",
    "harvest_recovery",
)
for name in fraction_fields:
    if values[name] > 1:
        fail("input_domain_invalid", name)

if values["operating_days_per_year"] > 366:
    fail("time_basis_invalid", "operating_days_per_year")
for name in ("filtration_operating_hours_per_day", "circulation_operating_hours_per_day"):
    if values[name] > 24:
        fail("time_basis_invalid", name)
if values["concentrate_biomass_concentration"] <= values["operating_biomass_concentration"]:
    fail("harvest_concentration_invalid", "concentrate_biomass_concentration")
if "product_price" in values and values["product_price"] < 0:
    fail("input_domain_invalid", "product_price")

volume_m3 = values["productive_liquid_volume"]
volume_l = volume_m3 * 1000.0
culture_concentration = values["operating_biomass_concentration"]
productivity = values["volumetric_productivity"]
mu_max = values["maximum_specific_growth_rate"]
operating_days = values["operating_days_per_year"]
feed_events = values["feed_events_per_day"]

biomass_inventory = volume_l * culture_concentration / 1000.0
production_g_d = volume_l * productivity
production_kg_d = production_g_d / 1000.0
annual_biomass = production_kg_d * operating_days
equivalent_dilution = productivity / culture_concentration
equivalent_dilution_to_mu = equivalent_dilution / mu_max

nitrogen_demand = production_g_d * values["biomass_nitrogen_fraction"] * 1000.0
phosphorus_demand = production_g_d * values["biomass_phosphorus_fraction"] * 1000.0
carbon_demand = production_g_d * values["biomass_carbon_fraction"] * 1000.0
sodium_nitrate_dose = nitrogen_demand * 6.07
phosphate_dose = phosphorus_demand * 4.46
bicarbonate_dose = carbon_demand * 6.99
nitrogen_stock = nitrogen_demand / values["nitrogen_stock_concentration"]
phosphorus_stock = phosphorus_demand / values["phosphorus_stock_concentration"]
carbon_stock = carbon_demand / values["carbon_stock_concentration"]

co2_equivalent = carbon_demand * (44.0 / 12.0) / 1000.0
oxygen_equivalent = carbon_demand * (32.0 / 12.0) / 1000.0
oxygen_volume_stp = (oxygen_equivalent / 32.0) * 22.414
co2_gas_rate = volume_l * values["co2_specific_gas_rate"]

whole_culture_bleed = production_g_d / culture_concentration
whole_culture_dilution = whole_culture_bleed / volume_l
recovery = values["harvest_recovery"]
side_stream = production_g_d / (culture_concentration * recovery)
side_stream_biomass = side_stream * culture_concentration / 1000.0
recovered_biomass = production_kg_d
returned_biomass = side_stream_biomass - recovered_biomass
concentrate_volume = recovered_biomass * 1000.0 / values["concentrate_biomass_concentration"]
filter_area = side_stream / (
    values["filtration_operating_hours_per_day"] * values["filtration_flux"]
)

if not math.isclose(
    side_stream_biomass,
    recovered_biomass + returned_biomass,
    rel_tol=1e-12,
    abs_tol=1e-15,
):
    fail("mass_balance_invalid")
if not math.isclose(recovered_biomass, production_kg_d, rel_tol=1e-12, abs_tol=1e-15):
    fail("mass_balance_invalid")

pump_energy_daily = values["pump_electric_power"] * values["circulation_operating_hours_per_day"] / 1000.0
pump_energy_annual = pump_energy_daily * operating_days
specific_pump_energy = pump_energy_daily / recovered_biomass
variable_opex_daily = pump_energy_daily * values["electricity_price"]
variable_opex_annual = variable_opex_daily * operating_days
specific_variable_cost = variable_opex_daily / recovered_biomass

outputs = {
    "biological_productive_volume": {"value": volume_m3, "unit": "m3"},
    "biomass_inventory": {"value": biomass_inventory, "unit": "kgDW"},
    "gross_biomass_production_rate": {"value": production_kg_d, "unit": "kgDW/d"},
    "annual_biomass_equivalent": {"value": annual_biomass, "unit": "kgDW/y"},
    "equivalent_dilution_rate": {"value": equivalent_dilution, "unit": "1/d"},
    "equivalent_dilution_to_mu_max": {"value": equivalent_dilution_to_mu, "unit": "1"},
    "nitrogen_incorporation_demand": {"value": nitrogen_demand, "unit": "mgN/d"},
    "phosphorus_incorporation_demand": {"value": phosphorus_demand, "unit": "mgP/d"},
    "carbon_incorporation_demand": {"value": carbon_demand, "unit": "mgC/d"},
    "sodium_nitrate_equivalent_dose": {"value": sodium_nitrate_dose, "unit": "mg/d"},
    "sodium_dihydrogen_phosphate_monohydrate_equivalent_dose": {
        "value": phosphate_dose,
        "unit": "mg/d",
    },
    "sodium_bicarbonate_equivalent_dose": {"value": bicarbonate_dose, "unit": "mg/d"},
    "nitrogen_stock_volume_rate": {"value": nitrogen_stock, "unit": "mL/d"},
    "phosphorus_stock_volume_rate": {"value": phosphorus_stock, "unit": "mL/d"},
    "carbon_stock_volume_rate": {"value": carbon_stock, "unit": "mL/d"},
    "nitrogen_stock_volume_per_event": {"value": nitrogen_stock / feed_events, "unit": "mL/event"},
    "phosphorus_stock_volume_per_event": {"value": phosphorus_stock / feed_events, "unit": "mL/event"},
    "carbon_stock_volume_per_event": {"value": carbon_stock / feed_events, "unit": "mL/event"},
    "co2_uptake_equivalent": {"value": co2_equivalent, "unit": "gCO2/d"},
    "oxygen_production_equivalent": {"value": oxygen_equivalent, "unit": "gO2/d"},
    "oxygen_volume_stp_equivalent": {"value": oxygen_volume_stp, "unit": "L/d"},
    "co2_gas_rate_benchmark": {"value": co2_gas_rate, "unit": "mLCO2/min"},
    "whole_culture_bleed_rate": {"value": whole_culture_bleed, "unit": "L/d"},
    "whole_culture_bleed_per_event": {"value": whole_culture_bleed / feed_events, "unit": "L/event"},
    "whole_culture_dilution_equivalent": {"value": whole_culture_dilution, "unit": "1/d"},
    "side_stream_processed_rate": {"value": side_stream, "unit": "L/d"},
    "side_stream_processed_per_event": {"value": side_stream / feed_events, "unit": "L/event"},
    "side_stream_biomass_feed_rate": {"value": side_stream_biomass, "unit": "kgDW/d"},
    "recovered_biomass_rate": {"value": recovered_biomass, "unit": "kgDW/d"},
    "returned_uncaptured_biomass_rate": {"value": returned_biomass, "unit": "kgDW/d"},
    "concentrate_volume_rate": {"value": concentrate_volume, "unit": "L/d"},
    "required_filter_area": {"value": filter_area, "unit": "m2"},
    "pump_electric_energy_rate": {"value": pump_energy_daily, "unit": "kWh/d"},
    "annual_pump_electric_energy": {"value": pump_energy_annual, "unit": "kWh/y"},
    "specific_pump_energy": {"value": specific_pump_energy, "unit": "kWh/kgDW"},
    "variable_opex_rate": {"value": variable_opex_daily, "unit": "EUR/d"},
    "annual_variable_opex": {"value": variable_opex_annual, "unit": "EUR/y"},
    "specific_variable_cost": {"value": specific_variable_cost, "unit": "EUR/kgDW"},
}

economic_kpi_status = {
    "variable_opex_rate": {"status": "computable"},
    "specific_variable_cost": {"status": "computable"},
}
if "product_price" in values:
    gross_margin = recovered_biomass * values["product_price"] - variable_opex_daily
    outputs["gross_margin_proxy"] = {"value": gross_margin, "unit": "EUR/d"}
    outputs["annual_gross_margin_proxy"] = {"value": gross_margin * operating_days, "unit": "EUR/y"}
    economic_kpi_status["gross_margin_proxy"] = {"status": "computable"}
else:
    economic_kpi_status["gross_margin_proxy"] = {
        "status": "not_computable",
        "reason": "missing_product_price",
    }

result = {
    "schema_version": 1,
    "status": "succeeded",
    "outputs": outputs,
    "diagnostics": {
        "model_id": "bluerev_biomass_nutrients_harvest_v0",
        "model_fidelity": "M0_static_screening",
        "species_basis": "Nannochloropsis_gaditana_screening",
        "productivity_is_imposed_input": True,
        "productive_volume_basis": "caller_asserted_explicit_volume",
        "upstream_volume_not_auto_selected": True,
        "nutrient_boundary": "biomass_incorporation_only",
        "residual_nutrient_targets_not_modeled": True,
        "gas_rate_semantics": "instantaneous_pH_control_benchmark",
        "gas_transfer_not_evaluated": True,
        "oxygen_volume_reference": "STP_22.414_L_per_mol",
        "harvest_mode": "side_stream_capture_with_filtrate_return",
        "harvest_recovery_application_count": 1,
        "filtrate_discard_not_modeled": True,
        "economic_model_id": "preliminary_economic_evaluation_v0",
        "economic_boundary": "pump_electricity_only",
        "economic_basis": "daily_recovered_dry_biomass",
        "included_variable_cost_categories": ["pump_electricity"],
        "excluded_variable_cost_categories": [
            "nutrients",
            "carbon_source",
            "gas_handling",
            "harvesting",
            "controls",
            "cleaning",
            "thermal_management",
            "labor",
            "maintenance",
            "logistics",
        ],
        "economic_kpi_status": economic_kpi_status,
        "full_tea": False,
        "capex_included": False,
        "salt_conversion_factors": {
            "basis": "rounded_workbook_screening_constants",
            "sodium_nitrate_per_nitrogen": 6.07,
            "phosphate_monohydrate_per_phosphorus": 4.46,
            "sodium_bicarbonate_per_carbon": 6.99,
        },
        "input_evidence": input_evidence,
        "workbook_runtime_dependency": False,
    },
}

with open("result.json", "w", encoding="utf-8") as handle:
    json.dump(result, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
