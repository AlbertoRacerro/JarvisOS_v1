import hashlib
import json
import math

MODEL_ID = "bluerev_process_topology_m1_v0"
MODEL_LABEL = "bluerev-process-topology-m1-v0.1.0"
MANIFEST_SCHEMA_VERSION = "0.1"

EXPECTED_UNITS = {
    "parallel_path_count": "1",
    "branch_illuminated_straight_length": "m",
    "branch_dark_straight_length": "m",
    "branch_bend_count": "1",
    "branch_illuminated_bend_count": "1",
    "branch_bend_centerline_radius": "mm",
    "branch_bend_angle": "deg",
    "common_supply_length": "m",
    "common_return_length": "m",
    "branch_tube_inner_diameter": "mm",
    "branch_tube_outer_diameter": "mm",
    "common_tube_inner_diameter": "mm",
    "common_tube_outer_diameter": "mm",
    "split_manifold_liquid_volume": "L",
    "merge_manifold_liquid_volume": "L",
    "reservoir_liquid_volume": "L",
    "target_branch_velocity": "m/s",
    "liquid_density": "kg/m3",
    "dynamic_viscosity": "Pa*s",
    "pump_efficiency": "1",
    "common_supply_minor_loss_coefficient": "1",
    "split_manifold_loss_coefficient": "1",
    "branch_bend_loss_coefficient_per_bend": "1",
    "branch_misc_minor_loss_coefficient": "1",
    "merge_manifold_loss_coefficient": "1",
    "common_return_minor_loss_coefficient": "1",
}


def fail(reason, field_name=None):
    message = "bluerev_topology_error:" + reason
    if field_name is not None:
        message += ":" + field_name
    raise SystemExit(message)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def require_integer(values, name, minimum, maximum):
    value = values[name]
    if not value.is_integer():
        fail("integer_required", name)
    integer = int(value)
    if integer < minimum or integer > maximum:
        fail("input_domain_invalid", name)
    return integer


def friction_factor(reynolds, field_name):
    if reynolds < 2300.0:
        return 64.0 / reynolds, "laminar_64_over_Re"
    if 4000.0 <= reynolds <= 100000.0:
        return 0.3164 * reynolds**-0.25, "blasius_smooth_pipe_v0"
    fail("correlation_not_qualified", field_name)


with open("input.json", encoding="utf-8") as handle:
    inputs = json.load(handle)

if not isinstance(inputs, dict) or set(inputs) != set(EXPECTED_UNITS):
    fail("input_contract_invalid")

values = {}
for name, expected_unit in EXPECTED_UNITS.items():
    item = inputs.get(name)
    if not isinstance(item, dict):
        fail("input_contract_invalid", name)
    allowed_keys = {"value", "unit", "source_parameter_id"}
    if "value" not in item or "unit" not in item or not set(item).issubset(allowed_keys):
        fail("input_contract_invalid", name)
    value = item["value"]
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        fail("input_contract_invalid", name)
    if item["unit"] != expected_unit:
        fail("input_unit_invalid", name)
    values[name] = float(value)

parallel_path_count = require_integer(values, "parallel_path_count", 1, 12)
branch_bend_count = require_integer(values, "branch_bend_count", 0, 64)
branch_illuminated_bend_count = require_integer(
    values, "branch_illuminated_bend_count", 0, branch_bend_count
)

nonnegative_fields = (
    "branch_illuminated_straight_length",
    "branch_dark_straight_length",
    "common_supply_length",
    "common_return_length",
    "split_manifold_liquid_volume",
    "merge_manifold_liquid_volume",
    "reservoir_liquid_volume",
    "common_supply_minor_loss_coefficient",
    "split_manifold_loss_coefficient",
    "branch_bend_loss_coefficient_per_bend",
    "branch_misc_minor_loss_coefficient",
    "merge_manifold_loss_coefficient",
    "common_return_minor_loss_coefficient",
)
for name in nonnegative_fields:
    if values[name] < 0:
        fail("input_domain_invalid", name)

positive_fields = (
    "branch_tube_inner_diameter",
    "common_tube_inner_diameter",
    "target_branch_velocity",
    "liquid_density",
    "dynamic_viscosity",
)
for name in positive_fields:
    if values[name] <= 0:
        fail("input_domain_invalid", name)

if values["branch_tube_outer_diameter"] <= values["branch_tube_inner_diameter"]:
    fail("input_domain_invalid", "branch_tube_outer_diameter")
if values["common_tube_outer_diameter"] <= values["common_tube_inner_diameter"]:
    fail("input_domain_invalid", "common_tube_outer_diameter")
if values["pump_efficiency"] <= 0 or values["pump_efficiency"] > 1:
    fail("input_domain_invalid", "pump_efficiency")

if branch_bend_count == 0:
    for name in (
        "branch_illuminated_bend_count",
        "branch_bend_centerline_radius",
        "branch_bend_angle",
        "branch_bend_loss_coefficient_per_bend",
    ):
        if values[name] != 0:
            fail("zero_bend_value_must_be_zero", name)
else:
    if values["branch_bend_angle"] <= 0 or values["branch_bend_angle"] > 180:
        fail("input_domain_invalid", "branch_bend_angle")
    if values["branch_bend_centerline_radius"] <= values["branch_tube_outer_diameter"] / 2.0:
        fail("bend_radius_intersects_tube", "branch_bend_centerline_radius")

if (
    values["branch_illuminated_straight_length"] == 0
    and values["branch_dark_straight_length"] == 0
    and branch_bend_count == 0
):
    fail("branch_length_empty", "branch_illuminated_straight_length")

# SI normalization.
li = values["branch_illuminated_straight_length"]
ld = values["branch_dark_straight_length"]
rb = values["branch_bend_centerline_radius"] / 1000.0
theta = math.radians(values["branch_bend_angle"])
ls = values["common_supply_length"]
lr = values["common_return_length"]
di_b = values["branch_tube_inner_diameter"] / 1000.0
do_b = values["branch_tube_outer_diameter"] / 1000.0
di_c = values["common_tube_inner_diameter"] / 1000.0
do_c = values["common_tube_outer_diameter"] / 1000.0
v_split = values["split_manifold_liquid_volume"] / 1000.0
v_merge = values["merge_manifold_liquid_volume"] / 1000.0
v_reservoir = values["reservoir_liquid_volume"] / 1000.0
v_b = values["target_branch_velocity"]
rho = values["liquid_density"]
mu = values["dynamic_viscosity"]
eta = values["pump_efficiency"]

area_b = math.pi * di_b**2 / 4.0
area_c = math.pi * di_c**2 / 4.0
bend_length_each = rb * theta if branch_bend_count else 0.0
branch_bend_length = branch_bend_count * bend_length_each
branch_length = li + branch_bend_length + ld
branch_illuminated_length = li + branch_illuminated_bend_count * bend_length_each
branch_dark_length = ld + (branch_bend_count - branch_illuminated_bend_count) * bend_length_each
common_length = ls + lr
installed_branch_length = parallel_path_count * branch_length
installed_tube_length = installed_branch_length + common_length
representative_path_length = ls + branch_length + lr

branch_volume_each = area_b * branch_length
branch_volume_total = parallel_path_count * branch_volume_each
common_supply_volume = area_c * ls
common_return_volume = area_c * lr
manifold_volume = v_split + v_merge
non_tube_volume = manifold_volume + v_reservoir
total_inventory = branch_volume_total + common_supply_volume + common_return_volume + non_tube_volume

branch_illuminated_area = parallel_path_count * math.pi * do_b * branch_illuminated_length
branch_dark_area = parallel_path_count * math.pi * do_b * branch_dark_length
common_dark_area = math.pi * do_c * common_length
tube_external_area = branch_illuminated_area + branch_dark_area + common_dark_area
wall_area_b = math.pi * (do_b**2 - di_b**2) / 4.0
wall_area_c = math.pi * (do_c**2 - di_c**2) / 4.0
tube_material_volume = parallel_path_count * wall_area_b * branch_length + wall_area_c * common_length

branch_flow = v_b * area_b
total_flow = parallel_path_count * branch_flow
v_c = total_flow / area_c
branch_transit_time = branch_length / v_b
representative_path_transit_time = ls / v_c + branch_transit_time + lr / v_c
inventory_turnover_time = total_inventory / total_flow

re_b = rho * v_b * di_b / mu
re_c = rho * v_c * di_c / mu
ff_b, corr_b = friction_factor(re_b, "branch_reynolds_number")
ff_c, corr_c = friction_factor(re_c, "common_reynolds_number")
q_b = rho * v_b**2 / 2.0
q_c = rho * v_c**2 / 2.0

supply_major = ff_c * (ls / di_c) * q_c
branch_major = ff_b * (branch_length / di_b) * q_b
return_major = ff_c * (lr / di_c) * q_c
supply_minor = values["common_supply_minor_loss_coefficient"] * q_c
split_loss = values["split_manifold_loss_coefficient"] * q_c
bend_loss = branch_bend_count * values["branch_bend_loss_coefficient_per_bend"] * q_b
branch_misc_loss = values["branch_misc_minor_loss_coefficient"] * q_b
merge_loss = values["merge_manifold_loss_coefficient"] * q_c
return_minor = values["common_return_minor_loss_coefficient"] * q_c
branch_path_loss = branch_major + bend_loss + branch_misc_loss
common_path_loss = supply_major + supply_minor + split_loss + merge_loss + return_major + return_minor
total_pressure_loss = branch_path_loss + common_path_loss

gravity = 9.80665
equivalent_static_head = total_pressure_loss / (rho * gravity)
hydraulic_power = total_pressure_loss * total_flow
pump_electric_power = hydraulic_power / eta

outputs = {
    "branch_hydraulic_cross_section_area": {"value": area_b, "unit": "m2"},
    "common_hydraulic_cross_section_area": {"value": area_c, "unit": "m2"},
    "branch_bend_length_each": {"value": bend_length_each, "unit": "m"},
    "branch_bend_length_total_each_path": {"value": branch_bend_length, "unit": "m"},
    "branch_length_each": {"value": branch_length, "unit": "m"},
    "branch_illuminated_length_each": {"value": branch_illuminated_length, "unit": "m"},
    "branch_dark_length_each": {"value": branch_dark_length, "unit": "m"},
    "installed_branch_length_total": {"value": installed_branch_length, "unit": "m"},
    "installed_tube_length_total": {"value": installed_tube_length, "unit": "m"},
    "representative_hydraulic_path_length": {"value": representative_path_length, "unit": "m"},
    "branch_liquid_volume_each": {"value": branch_volume_each, "unit": "m3"},
    "branch_liquid_volume_total": {"value": branch_volume_total, "unit": "m3"},
    "common_supply_liquid_volume": {"value": common_supply_volume, "unit": "m3"},
    "common_return_liquid_volume": {"value": common_return_volume, "unit": "m3"},
    "manifold_liquid_volume_total": {"value": manifold_volume, "unit": "m3"},
    "non_tube_liquid_volume_total": {"value": non_tube_volume, "unit": "m3"},
    "total_liquid_inventory": {"value": total_inventory, "unit": "m3"},
    "branch_illuminated_external_area_total": {"value": branch_illuminated_area, "unit": "m2"},
    "branch_dark_external_area_total": {"value": branch_dark_area, "unit": "m2"},
    "common_dark_external_area_total": {"value": common_dark_area, "unit": "m2"},
    "tube_external_area_total": {"value": tube_external_area, "unit": "m2"},
    "tube_material_volume": {"value": tube_material_volume, "unit": "m3"},
    "branch_flow_rate_each": {"value": branch_flow, "unit": "m3/s"},
    "total_circulation_flow_rate": {"value": total_flow, "unit": "m3/s"},
    "common_velocity": {"value": v_c, "unit": "m/s"},
    "branch_nominal_transit_time": {"value": branch_transit_time, "unit": "s"},
    "representative_tube_path_transit_time": {"value": representative_path_transit_time, "unit": "s"},
    "total_inventory_turnover_time": {"value": inventory_turnover_time, "unit": "s"},
    "branch_reynolds_number": {"value": re_b, "unit": "1"},
    "common_reynolds_number": {"value": re_c, "unit": "1"},
    "branch_darcy_friction_factor": {"value": ff_b, "unit": "1"},
    "common_darcy_friction_factor": {"value": ff_c, "unit": "1"},
    "common_supply_major_pressure_loss": {"value": supply_major, "unit": "Pa"},
    "common_supply_minor_pressure_loss": {"value": supply_minor, "unit": "Pa"},
    "split_manifold_pressure_loss": {"value": split_loss, "unit": "Pa"},
    "branch_major_pressure_loss": {"value": branch_major, "unit": "Pa"},
    "branch_bend_pressure_loss": {"value": bend_loss, "unit": "Pa"},
    "branch_misc_minor_pressure_loss": {"value": branch_misc_loss, "unit": "Pa"},
    "merge_manifold_pressure_loss": {"value": merge_loss, "unit": "Pa"},
    "common_return_major_pressure_loss": {"value": return_major, "unit": "Pa"},
    "common_return_minor_pressure_loss": {"value": return_minor, "unit": "Pa"},
    "branch_path_pressure_loss": {"value": branch_path_loss, "unit": "Pa"},
    "common_path_pressure_loss": {"value": common_path_loss, "unit": "Pa"},
    "total_pressure_loss": {"value": total_pressure_loss, "unit": "Pa"},
    "equivalent_static_head": {"value": equivalent_static_head, "unit": "m"},
    "hydraulic_power": {"value": hydraulic_power, "unit": "W"},
    "pump_electric_power": {"value": pump_electric_power, "unit": "W"},
}

canonical_input = canonical_json(inputs)
input_sha256 = hashlib.sha256(canonical_input.encode("utf-8")).hexdigest()
manifest_core = {
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "model_id": MODEL_ID,
    "model_label": MODEL_LABEL,
    "input_sha256": input_sha256,
    "topology": {
        "loop_count": 1,
        "parallel_path_count": parallel_path_count,
        "branch_template_order": [
            "branch_illuminated_straight_run",
            "branch_bend_group",
            "branch_dark_straight_run",
        ],
        "representative_path_order": [
            "common_supply_run",
            "split_manifold",
            "branch_template",
            "merge_manifold",
            "common_return_run",
        ],
        "components": [
            {"id": "common_supply_run", "kind": "tube_run", "multiplicity": 1, "hydraulic_role": "common_supply", "length_m": ls, "inner_diameter_m": di_c, "outer_diameter_m": do_c, "illumination": "dark"},
            {"id": "split_manifold", "kind": "manifold", "multiplicity": 1, "hydraulic_role": "split", "liquid_volume_m3": v_split},
            {"id": "branch_illuminated_straight_run", "kind": "tube_run", "multiplicity": parallel_path_count, "hydraulic_role": "parallel_branch", "length_each_m": li, "inner_diameter_m": di_b, "outer_diameter_m": do_b, "illumination": "illuminated"},
            {"id": "branch_bend_group", "kind": "bend_group", "multiplicity": parallel_path_count, "bend_count_each": branch_bend_count, "illuminated_bend_count_each": branch_illuminated_bend_count, "bend_length_each_m": bend_length_each, "centerline_radius_m": rb, "angle_deg": values["branch_bend_angle"]},
            {"id": "branch_dark_straight_run", "kind": "tube_run", "multiplicity": parallel_path_count, "hydraulic_role": "parallel_branch", "length_each_m": ld, "inner_diameter_m": di_b, "outer_diameter_m": do_b, "illumination": "dark"},
            {"id": "merge_manifold", "kind": "manifold", "multiplicity": 1, "hydraulic_role": "merge", "liquid_volume_m3": v_merge},
            {"id": "common_return_run", "kind": "tube_run", "multiplicity": 1, "hydraulic_role": "common_return", "length_m": lr, "inner_diameter_m": di_c, "outer_diameter_m": do_c, "illumination": "dark"},
            {"id": "reservoir_pump_suction_inventory", "kind": "inventory", "multiplicity": 1, "hydraulic_role": "reservoir", "liquid_volume_m3": v_reservoir},
        ],
    },
    "summary": {
        "installed_tube_length_total_m": installed_tube_length,
        "representative_hydraulic_path_length_m": representative_path_length,
        "total_liquid_inventory_m3": total_inventory,
        "total_circulation_flow_rate_m3_s": total_flow,
        "total_pressure_loss_pa": total_pressure_loss,
    },
    "limitations": [
        "symmetric_parallel_branches_only",
        "non_spatial_topology",
        "no_network_solver",
        "no_recycle_convergence",
        "no_property_package",
        "no_pump_curve_or_npsh",
        "tube_external_area_is_not_complete_reactor_area",
    ],
}
manifest_digest = hashlib.sha256(canonical_json(manifest_core).encode("utf-8")).hexdigest()
manifest = dict(manifest_core)
manifest["topology_digest"] = manifest_digest

result = {
    "schema_version": 1,
    "status": "succeeded",
    "outputs": outputs,
    "diagnostics": {
        "model_id": MODEL_ID,
        "model_label": MODEL_LABEL,
        "model_fidelity": "M1_static_symmetric_topology",
        "branch_friction_correlation": corr_b,
        "common_friction_correlation": corr_c,
        "friction_factor_convention": "Darcy",
        "pressure_path_semantics": "common_supply_plus_one_representative_branch_plus_common_return",
        "installed_geometry_semantics": "sum_across_all_repeated_branches_and_common_runs",
        "topology_manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "topology_digest": manifest_digest,
        "input_sha256": input_sha256,
        "workbook_runtime_dependency": False,
    },
}

with open("topology_manifest.json", "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
with open("result.json", "w", encoding="utf-8") as handle:
    json.dump(result, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
