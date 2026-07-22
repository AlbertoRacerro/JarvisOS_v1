import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.py"
CONTRACT = ROOT / "backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.contract.json"
SCHEMA = ROOT / "schemas/bluerev_process_topology_m1_v0_1.schema.json"
SERVICE = ROOT / "backend/app/modules/runner/service.py"
DIRECT_TEST = ROOT / "backend/tests/test_bluerev_process_topology_m1.py"
RUNNER_TEST = ROOT / "backend/tests/test_bluerev_process_topology_m1_runner.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    SERVICE,
    "                validate_manifest(output_dir, simulation_run.input_payload, output)\n",
    """                validate_manifest(
                    output_dir,
                    simulation_run.input_payload,
                    output,
                    max_bytes=min(
                        int(job["max_output_json_bytes"]),
                        int(job["max_artifact_bytes"]),
                    ),
                )
""",
)

replace_once(
    SCRIPT,
    'MANIFEST_SCHEMA_VERSION = "0.1"\n',
    'MANIFEST_SCHEMA_VERSION = "bluerev_process_topology_m1_v0_1"\n'
    'CONTRACT_VERSION = "bluerev_process_topology_m1_v0_contract_1"\n',
)
replace_once(
    SCRIPT,
    """    if item["unit"] != expected_unit:
        fail("input_unit_invalid", name)
    values[name] = float(value)
""",
    """    if item["unit"] != expected_unit:
        fail("input_unit_invalid", name)
    source_parameter_id = item.get("source_parameter_id")
    if source_parameter_id is not None and (
        not isinstance(source_parameter_id, str) or not source_parameter_id.strip()
    ):
        fail("input_contract_invalid", name)
    values[name] = float(value)
""",
)

prefix = SCRIPT.read_text(encoding="utf-8").split("outputs = {", 1)[0]
tail = r'''branch_wall_thickness_mm = (
    values["branch_tube_outer_diameter"] - values["branch_tube_inner_diameter"]
) / 2.0
common_wall_thickness_mm = (
    values["common_tube_outer_diameter"] - values["common_tube_inner_diameter"]
) / 2.0
common_supply_transit_time = ls / v_c
common_return_transit_time = lr / v_c

single_length_representable = (
    parallel_path_count == 1
    and ls == 0.0
    and lr == 0.0
    and v_split == 0.0
    and v_merge == 0.0
    and di_c == di_b
    and do_c == do_b
)
m0_reduction_case = (
    single_length_representable
    and branch_bend_count == 0
    and branch_illuminated_bend_count == 0
    and rb == 0.0
    and values["branch_bend_angle"] == 0.0
    and values["branch_bend_loss_coefficient_per_bend"] == 0.0
    and ld == 0.0
    and values["common_supply_minor_loss_coefficient"] == 0.0
    and values["split_manifold_loss_coefficient"] == 0.0
    and values["merge_manifold_loss_coefficient"] == 0.0
    and values["common_return_minor_loss_coefficient"] == 0.0
)
m0_reduction_status = (
    "exact_047_reduction" if m0_reduction_case else "not_m0_reduction_case"
)
single_length_projection_status = (
    "single_length_representable"
    if single_length_representable
    else "not_single_length_representable"
)

outputs = {
    "parallel_path_count": {"value": parallel_path_count, "unit": "1"},
    "branch_bend_count": {"value": branch_bend_count, "unit": "1"},
    "branch_bend_arc_length_each": {"value": bend_length_each, "unit": "m"},
    "branch_bend_total_length": {"value": branch_bend_length, "unit": "m"},
    "branch_centerline_length": {"value": branch_length, "unit": "m"},
    "branch_illuminated_centerline_length": {
        "value": branch_illuminated_length,
        "unit": "m",
    },
    "branch_dark_centerline_length": {"value": branch_dark_length, "unit": "m"},
    "installed_branch_centerline_length_total": {
        "value": installed_branch_length,
        "unit": "m",
    },
    "installed_tube_centerline_length_total": {
        "value": installed_tube_length,
        "unit": "m",
    },
    "representative_hydraulic_path_length": {
        "value": representative_path_length,
        "unit": "m",
    },
    "branch_wall_thickness": {"value": branch_wall_thickness_mm, "unit": "mm"},
    "common_wall_thickness": {"value": common_wall_thickness_mm, "unit": "mm"},
    "tube_material_volume_proxy": {"value": tube_material_volume, "unit": "m3"},
    "branch_liquid_volume_each": {"value": branch_volume_each, "unit": "m3"},
    "branch_liquid_volume_total": {"value": branch_volume_total, "unit": "m3"},
    "common_supply_liquid_volume": {"value": common_supply_volume, "unit": "m3"},
    "common_return_liquid_volume": {"value": common_return_volume, "unit": "m3"},
    "manifold_liquid_volume_total": {"value": manifold_volume, "unit": "m3"},
    "non_tube_liquid_volume_total": {"value": non_tube_volume, "unit": "m3"},
    "total_liquid_inventory": {"value": total_inventory, "unit": "m3"},
    "illuminated_branch_external_area": {
        "value": branch_illuminated_area,
        "unit": "m2",
    },
    "dark_branch_external_area": {"value": branch_dark_area, "unit": "m2"},
    "common_external_area": {"value": common_dark_area, "unit": "m2"},
    "tube_external_area_total": {"value": tube_external_area, "unit": "m2"},
    "branch_hydraulic_cross_section_area": {"value": area_b, "unit": "m2"},
    "common_hydraulic_cross_section_area": {"value": area_c, "unit": "m2"},
    "branch_flow_rate": {"value": branch_flow, "unit": "m3/s"},
    "total_circulation_flow_rate": {"value": total_flow, "unit": "m3/s"},
    "branch_velocity": {"value": v_b, "unit": "m/s"},
    "common_velocity": {"value": v_c, "unit": "m/s"},
    "common_supply_nominal_transit_time": {
        "value": common_supply_transit_time,
        "unit": "s",
    },
    "branch_nominal_transit_time": {"value": branch_transit_time, "unit": "s"},
    "common_return_nominal_transit_time": {
        "value": common_return_transit_time,
        "unit": "s",
    },
    "representative_path_nominal_transit_time": {
        "value": representative_path_transit_time,
        "unit": "s",
    },
    "total_inventory_turnover_time": {"value": inventory_turnover_time, "unit": "s"},
    "branch_reynolds_number": {"value": re_b, "unit": "1"},
    "common_reynolds_number": {"value": re_c, "unit": "1"},
    "branch_darcy_friction_factor": {"value": ff_b, "unit": "1"},
    "common_darcy_friction_factor": {"value": ff_c, "unit": "1"},
    "branch_major_pressure_loss": {"value": branch_major, "unit": "Pa"},
    "branch_bend_pressure_loss": {"value": bend_loss, "unit": "Pa"},
    "branch_misc_pressure_loss": {"value": branch_misc_loss, "unit": "Pa"},
    "representative_branch_pressure_loss": {"value": branch_path_loss, "unit": "Pa"},
    "common_supply_major_pressure_loss": {"value": supply_major, "unit": "Pa"},
    "common_supply_minor_pressure_loss": {"value": supply_minor, "unit": "Pa"},
    "split_manifold_pressure_loss": {"value": split_loss, "unit": "Pa"},
    "merge_manifold_pressure_loss": {"value": merge_loss, "unit": "Pa"},
    "common_return_major_pressure_loss": {"value": return_major, "unit": "Pa"},
    "common_return_minor_pressure_loss": {"value": return_minor, "unit": "Pa"},
    "common_pressure_loss": {"value": common_path_loss, "unit": "Pa"},
    "total_pressure_loss": {"value": total_pressure_loss, "unit": "Pa"},
    "equivalent_static_head": {"value": equivalent_static_head, "unit": "m"},
    "hydraulic_power": {"value": hydraulic_power, "unit": "W"},
    "pump_electric_power": {"value": pump_electric_power, "unit": "W"},
}

canonical_input = canonical_json(inputs)
input_sha256 = hashlib.sha256(canonical_input.encode("utf-8")).hexdigest()
limitations = [
    "symmetric_parallel_branches_only",
    "non_spatial_topology",
    "no_network_solver",
    "no_recycle_convergence",
    "no_property_package",
    "no_pump_curve_or_npsh",
    "tube_external_area_is_not_complete_reactor_area",
]
manifest = {
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "topology_kind": "symmetric_parallel_closed_loop",
    "model_identity": {
        "model_id": MODEL_ID,
        "version_label": MODEL_LABEL,
        "input_contract_version": CONTRACT_VERSION,
        "result_schema_version": 1,
    },
    "executed_inputs": inputs,
    "input_payload_sha256": input_sha256,
    "symmetry": {
        "parallel_path_count": parallel_path_count,
        "branch_template_id": "branch_template",
        "representative_path_id": "representative_path",
    },
    "ordered_components": [
        "pump",
        "common_supply",
        "split_manifold",
        "parallel_branch_group",
        "merge_manifold",
        "common_return",
        "reservoir",
    ],
    "branch_template": {
        "illuminated_straight": {
            "length_m": li,
            "inner_diameter_m": di_b,
            "outer_diameter_m": do_b,
            "wall_thickness_m": branch_wall_thickness_mm / 1000.0,
            "illumination": "illuminated",
        },
        "bend_group": {
            "bend_count_each": branch_bend_count,
            "illuminated_bend_count_each": branch_illuminated_bend_count,
            "dark_bend_count_each": branch_bend_count - branch_illuminated_bend_count,
            "arc_length_each_m": bend_length_each,
            "total_length_each_m": branch_bend_length,
            "centerline_radius_m": rb,
            "angle_deg": values["branch_bend_angle"],
            "loss_coefficient_each": values[
                "branch_bend_loss_coefficient_per_bend"
            ],
            "dynamic_pressure_basis": "branch",
        },
        "dark_straight": {
            "length_m": ld,
            "inner_diameter_m": di_b,
            "outer_diameter_m": do_b,
            "wall_thickness_m": branch_wall_thickness_mm / 1000.0,
            "illumination": "dark",
        },
    },
    "hydraulic_basis": {
        "branch": {
            "velocity_m_s": v_b,
            "cross_section_area_m2": area_b,
            "reynolds_number": re_b,
            "darcy_friction_factor": ff_b,
            "friction_correlation": corr_b,
            "dynamic_pressure_pa": q_b,
        },
        "common": {
            "velocity_m_s": v_c,
            "cross_section_area_m2": area_c,
            "reynolds_number": re_c,
            "darcy_friction_factor": ff_c,
            "friction_correlation": corr_c,
            "dynamic_pressure_pa": q_c,
        },
        "loss_coefficients": {
            "common_supply": values["common_supply_minor_loss_coefficient"],
            "split_manifold": values["split_manifold_loss_coefficient"],
            "branch_bend_each": values[
                "branch_bend_loss_coefficient_per_bend"
            ],
            "branch_misc": values["branch_misc_minor_loss_coefficient"],
            "merge_manifold": values["merge_manifold_loss_coefficient"],
            "common_return": values["common_return_minor_loss_coefficient"],
        },
    },
    "geometry_totals": {
        "branch_centerline_length_each_m": branch_length,
        "installed_branch_centerline_length_total_m": installed_branch_length,
        "installed_tube_centerline_length_total_m": installed_tube_length,
        "representative_hydraulic_path_length_m": representative_path_length,
        "branch_liquid_volume_total_m3": branch_volume_total,
        "common_supply_liquid_volume_m3": common_supply_volume,
        "common_return_liquid_volume_m3": common_return_volume,
        "manifold_liquid_volume_total_m3": manifold_volume,
        "reservoir_liquid_volume_m3": v_reservoir,
        "total_liquid_inventory_m3": total_inventory,
        "illuminated_branch_external_area_m2": branch_illuminated_area,
        "dark_branch_external_area_m2": branch_dark_area,
        "common_external_area_m2": common_dark_area,
        "tube_external_area_total_m2": tube_external_area,
        "tube_material_volume_proxy_m3": tube_material_volume,
    },
    "limitations": limitations,
}
manifest_text = canonical_json(manifest)
manifest_sha256 = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()

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
        "pressure_path_semantics": (
            "common_supply_plus_one_representative_branch_plus_common_return"
        ),
        "installed_geometry_semantics": (
            "sum_across_all_repeated_branches_and_common_runs"
        ),
        "topology_manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "topology_manifest_sha256": f"sha256:{manifest_sha256}",
        "input_payload_sha256": input_sha256,
        "m0_reduction_status": m0_reduction_status,
        "single_length_projection_status": single_length_projection_status,
        "workbook_runtime_dependency": False,
    },
}

with open("topology_manifest.json", "w", encoding="utf-8") as handle:
    handle.write(manifest_text)
with open("result.json", "w", encoding="utf-8") as handle:
    handle.write(canonical_json(result))
'''
SCRIPT.write_text(prefix + tail, encoding="utf-8")

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
input_properties = {}
for variable in contract["variables"]:
    input_properties[variable["name"]] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["value", "unit"],
        "properties": {
            "value": {"type": "number"},
            "unit": {"const": variable["unit"]},
            "source_parameter_id": {"type": "string", "minLength": 1},
        },
    }

number = {"type": "number"}
nonnegative = {"type": "number", "minimum": 0}
positive = {"type": "number", "exclusiveMinimum": 0}
flow_basis = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "velocity_m_s",
        "cross_section_area_m2",
        "reynolds_number",
        "darcy_friction_factor",
        "friction_correlation",
        "dynamic_pressure_pa",
    ],
    "properties": {
        "velocity_m_s": positive,
        "cross_section_area_m2": positive,
        "reynolds_number": positive,
        "darcy_friction_factor": positive,
        "friction_correlation": {
            "enum": ["laminar_64_over_Re", "blasius_smooth_pipe_v0"]
        },
        "dynamic_pressure_pa": positive,
    },
}
manifest_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://jarvisos.local/schemas/bluerev_process_topology_m1_v0_1.schema.json",
    "title": "BlueRev process topology M1 manifest",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "topology_kind",
        "model_identity",
        "executed_inputs",
        "input_payload_sha256",
        "symmetry",
        "ordered_components",
        "branch_template",
        "hydraulic_basis",
        "geometry_totals",
        "limitations",
    ],
    "properties": {
        "schema_version": {"const": "bluerev_process_topology_m1_v0_1"},
        "topology_kind": {"const": "symmetric_parallel_closed_loop"},
        "model_identity": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "model_id",
                "version_label",
                "input_contract_version",
                "result_schema_version",
            ],
            "properties": {
                "model_id": {"const": "bluerev_process_topology_m1_v0"},
                "version_label": {"const": "bluerev-process-topology-m1-v0.1.0"},
                "input_contract_version": {
                    "const": "bluerev_process_topology_m1_v0_contract_1"
                },
                "result_schema_version": {"const": 1},
            },
        },
        "executed_inputs": {
            "type": "object",
            "additionalProperties": False,
            "required": [variable["name"] for variable in contract["variables"]],
            "properties": input_properties,
        },
        "input_payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "symmetry": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "parallel_path_count",
                "branch_template_id",
                "representative_path_id",
            ],
            "properties": {
                "parallel_path_count": {"type": "integer", "minimum": 1, "maximum": 12},
                "branch_template_id": {"const": "branch_template"},
                "representative_path_id": {"const": "representative_path"},
            },
        },
        "ordered_components": {
            "const": [
                "pump",
                "common_supply",
                "split_manifold",
                "parallel_branch_group",
                "merge_manifold",
                "common_return",
                "reservoir",
            ]
        },
        "branch_template": {
            "type": "object",
            "additionalProperties": False,
            "required": ["illuminated_straight", "bend_group", "dark_straight"],
            "properties": {
                "illuminated_straight": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "length_m",
                        "inner_diameter_m",
                        "outer_diameter_m",
                        "wall_thickness_m",
                        "illumination",
                    ],
                    "properties": {
                        "length_m": nonnegative,
                        "inner_diameter_m": positive,
                        "outer_diameter_m": positive,
                        "wall_thickness_m": positive,
                        "illumination": {"const": "illuminated"},
                    },
                },
                "bend_group": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "bend_count_each",
                        "illuminated_bend_count_each",
                        "dark_bend_count_each",
                        "arc_length_each_m",
                        "total_length_each_m",
                        "centerline_radius_m",
                        "angle_deg",
                        "loss_coefficient_each",
                        "dynamic_pressure_basis",
                    ],
                    "properties": {
                        "bend_count_each": {"type": "integer", "minimum": 0, "maximum": 64},
                        "illuminated_bend_count_each": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 64,
                        },
                        "dark_bend_count_each": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 64,
                        },
                        "arc_length_each_m": nonnegative,
                        "total_length_each_m": nonnegative,
                        "centerline_radius_m": nonnegative,
                        "angle_deg": {"type": "number", "minimum": 0, "maximum": 180},
                        "loss_coefficient_each": nonnegative,
                        "dynamic_pressure_basis": {"const": "branch"},
                    },
                },
                "dark_straight": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "length_m",
                        "inner_diameter_m",
                        "outer_diameter_m",
                        "wall_thickness_m",
                        "illumination",
                    ],
                    "properties": {
                        "length_m": nonnegative,
                        "inner_diameter_m": positive,
                        "outer_diameter_m": positive,
                        "wall_thickness_m": positive,
                        "illumination": {"const": "dark"},
                    },
                },
            },
        },
        "hydraulic_basis": {
            "type": "object",
            "additionalProperties": False,
            "required": ["branch", "common", "loss_coefficients"],
            "properties": {
                "branch": flow_basis,
                "common": flow_basis,
                "loss_coefficients": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "common_supply",
                        "split_manifold",
                        "branch_bend_each",
                        "branch_misc",
                        "merge_manifold",
                        "common_return",
                    ],
                    "properties": {
                        "common_supply": nonnegative,
                        "split_manifold": nonnegative,
                        "branch_bend_each": nonnegative,
                        "branch_misc": nonnegative,
                        "merge_manifold": nonnegative,
                        "common_return": nonnegative,
                    },
                },
            },
        },
        "geometry_totals": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "branch_centerline_length_each_m",
                "installed_branch_centerline_length_total_m",
                "installed_tube_centerline_length_total_m",
                "representative_hydraulic_path_length_m",
                "branch_liquid_volume_total_m3",
                "common_supply_liquid_volume_m3",
                "common_return_liquid_volume_m3",
                "manifold_liquid_volume_total_m3",
                "reservoir_liquid_volume_m3",
                "total_liquid_inventory_m3",
                "illuminated_branch_external_area_m2",
                "dark_branch_external_area_m2",
                "common_external_area_m2",
                "tube_external_area_total_m2",
                "tube_material_volume_proxy_m3",
            ],
            "properties": {
                "branch_centerline_length_each_m": positive,
                "installed_branch_centerline_length_total_m": positive,
                "installed_tube_centerline_length_total_m": positive,
                "representative_hydraulic_path_length_m": positive,
                "branch_liquid_volume_total_m3": positive,
                "common_supply_liquid_volume_m3": nonnegative,
                "common_return_liquid_volume_m3": nonnegative,
                "manifold_liquid_volume_total_m3": nonnegative,
                "reservoir_liquid_volume_m3": nonnegative,
                "total_liquid_inventory_m3": positive,
                "illuminated_branch_external_area_m2": nonnegative,
                "dark_branch_external_area_m2": nonnegative,
                "common_external_area_m2": nonnegative,
                "tube_external_area_total_m2": positive,
                "tube_material_volume_proxy_m3": positive,
            },
        },
        "limitations": {
            "const": [
                "symmetric_parallel_branches_only",
                "non_spatial_topology",
                "no_network_solver",
                "no_recycle_convergence",
                "no_property_package",
                "no_pump_curve_or_npsh",
                "tube_external_area_is_not_complete_reactor_area",
            ]
        },
    },
}
SCHEMA.write_text(json.dumps(manifest_schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")

DIRECT_TEST.write_text(r'''import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app/modules/runner/examples/bluerev_process_topology_m1_v0.py"
CONTRACT = ROOT / "app/modules/runner/examples/bluerev_process_topology_m1_v0.contract.json"
SCHEMA = ROOT.parent / "schemas/bluerev_process_topology_m1_v0_1.schema.json"

REQUIRED_OUTPUTS = {
    "parallel_path_count",
    "branch_bend_count",
    "branch_bend_arc_length_each",
    "branch_bend_total_length",
    "branch_centerline_length",
    "branch_illuminated_centerline_length",
    "branch_dark_centerline_length",
    "installed_branch_centerline_length_total",
    "installed_tube_centerline_length_total",
    "representative_hydraulic_path_length",
    "branch_wall_thickness",
    "common_wall_thickness",
    "tube_material_volume_proxy",
    "branch_liquid_volume_each",
    "branch_liquid_volume_total",
    "common_supply_liquid_volume",
    "common_return_liquid_volume",
    "manifold_liquid_volume_total",
    "non_tube_liquid_volume_total",
    "total_liquid_inventory",
    "illuminated_branch_external_area",
    "dark_branch_external_area",
    "common_external_area",
    "tube_external_area_total",
    "branch_hydraulic_cross_section_area",
    "common_hydraulic_cross_section_area",
    "branch_flow_rate",
    "total_circulation_flow_rate",
    "branch_velocity",
    "common_velocity",
    "common_supply_nominal_transit_time",
    "branch_nominal_transit_time",
    "common_return_nominal_transit_time",
    "representative_path_nominal_transit_time",
    "total_inventory_turnover_time",
    "branch_reynolds_number",
    "common_reynolds_number",
    "branch_darcy_friction_factor",
    "common_darcy_friction_factor",
    "branch_major_pressure_loss",
    "branch_bend_pressure_loss",
    "branch_misc_pressure_loss",
    "representative_branch_pressure_loss",
    "common_supply_major_pressure_loss",
    "common_supply_minor_pressure_loss",
    "split_manifold_pressure_loss",
    "merge_manifold_pressure_loss",
    "common_return_major_pressure_loss",
    "common_return_minor_pressure_loss",
    "common_pressure_loss",
    "total_pressure_loss",
    "equivalent_static_head",
    "hydraulic_power",
    "pump_electric_power",
}


def input_set(**overrides):
    values = {
        "parallel_path_count": (2, "1"),
        "branch_illuminated_straight_length": (10.0, "m"),
        "branch_dark_straight_length": (2.0, "m"),
        "branch_bend_count": (2, "1"),
        "branch_illuminated_bend_count": (1, "1"),
        "branch_bend_centerline_radius": (100.0, "mm"),
        "branch_bend_angle": (90.0, "deg"),
        "common_supply_length": (1.0, "m"),
        "common_return_length": (1.5, "m"),
        "branch_tube_inner_diameter": (50.0, "mm"),
        "branch_tube_outer_diameter": (60.0, "mm"),
        "common_tube_inner_diameter": (80.0, "mm"),
        "common_tube_outer_diameter": (90.0, "mm"),
        "split_manifold_liquid_volume": (5.0, "L"),
        "merge_manifold_liquid_volume": (5.0, "L"),
        "reservoir_liquid_volume": (100.0, "L"),
        "target_branch_velocity": (0.5, "m/s"),
        "liquid_density": (1000.0, "kg/m3"),
        "dynamic_viscosity": (0.001, "Pa*s"),
        "pump_efficiency": (0.7, "1"),
        "common_supply_minor_loss_coefficient": (0.2, "1"),
        "split_manifold_loss_coefficient": (0.5, "1"),
        "branch_bend_loss_coefficient_per_bend": (0.3, "1"),
        "branch_misc_minor_loss_coefficient": (0.1, "1"),
        "merge_manifold_loss_coefficient": (0.5, "1"),
        "common_return_minor_loss_coefficient": (0.2, "1"),
    }
    values.update(overrides)
    return {name: {"value": value, "unit": unit} for name, (value, unit) in values.items()}


def run_model(tmp_path, payload):
    (tmp_path / "input.json").write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )


def reduction_input():
    return input_set(
        parallel_path_count=(1, "1"),
        branch_illuminated_straight_length=(12.0, "m"),
        branch_dark_straight_length=(0.0, "m"),
        branch_bend_count=(0, "1"),
        branch_illuminated_bend_count=(0, "1"),
        branch_bend_centerline_radius=(0.0, "mm"),
        branch_bend_angle=(0.0, "deg"),
        common_supply_length=(0.0, "m"),
        common_return_length=(0.0, "m"),
        common_tube_inner_diameter=(50.0, "mm"),
        common_tube_outer_diameter=(60.0, "mm"),
        split_manifold_liquid_volume=(0.0, "L"),
        merge_manifold_liquid_volume=(0.0, "L"),
        branch_bend_loss_coefficient_per_bend=(0.0, "1"),
        common_supply_minor_loss_coefficient=(0.0, "1"),
        split_manifold_loss_coefficient=(0.0, "1"),
        merge_manifold_loss_coefficient=(0.0, "1"),
        common_return_minor_loss_coefficient=(0.0, "1"),
    )


def test_contract_and_schema_are_value_free_and_closed():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["evaluation_mode"] == "forward"
    assert len(contract["variables"]) == 26
    assert all("default" not in variable for variable in contract["variables"])
    names = [variable["name"] for variable in contract["variables"]]
    assert len(set(names)) == 26

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["schema_version"]["const"] == "bluerev_process_topology_m1_v0_1"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["executed_inputs"]["required"] == names


def test_symmetric_topology_uses_required_output_contract(tmp_path):
    completed = run_model(tmp_path, input_set())
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    outputs = result["outputs"]
    assert set(outputs) == REQUIRED_OUTPUTS
    assert outputs["installed_branch_centerline_length_total"]["value"] == pytest.approx(
        2 * outputs["branch_centerline_length"]["value"]
    )
    assert outputs["total_circulation_flow_rate"]["value"] == pytest.approx(
        2 * outputs["branch_flow_rate"]["value"]
    )
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(
        outputs["representative_branch_pressure_loss"]["value"]
        + outputs["common_pressure_loss"]["value"]
    )
    assert result["diagnostics"]["single_length_projection_status"] == (
        "not_single_length_representable"
    )
    assert result["diagnostics"]["m0_reduction_status"] == "not_m0_reduction_case"


def test_manifest_is_canonical_complete_and_raw_hash_bound(tmp_path):
    payload = input_set()
    payload["liquid_density"]["source_parameter_id"] = "parameter-density"
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0, completed.stderr
    raw = (tmp_path / "topology_manifest.json").read_bytes()
    manifest = json.loads(raw)
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))

    assert raw == json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert not raw.endswith(b"\n")
    assert "topology_digest" not in manifest
    assert manifest["executed_inputs"] == payload
    expected_input = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert manifest["input_payload_sha256"] == hashlib.sha256(expected_input.encode()).hexdigest()
    expected_raw_sha = hashlib.sha256(raw).hexdigest()
    assert result["diagnostics"]["topology_manifest_sha256"] == f"sha256:{expected_raw_sha}"
    assert manifest["symmetry"]["parallel_path_count"] == 2
    assert manifest["ordered_components"][3] == "parallel_branch_group"


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"parallel_path_count": (1.5, "1")}, "parallel_path_count"),
        ({"branch_illuminated_bend_count": (3, "1")}, "branch_illuminated_bend_count"),
        ({"branch_bend_count": (0, "1"), "branch_bend_centerline_radius": (1.0, "mm")}, "branch_bend_centerline_radius"),
        ({"branch_bend_count": (0, "1"), "branch_bend_loss_coefficient_per_bend": (0.1, "1")}, "branch_bend_loss_coefficient_per_bend"),
        ({"branch_bend_centerline_radius": (30.0, "mm")}, "branch_bend_centerline_radius"),
        ({"branch_bend_angle": (181.0, "deg")}, "branch_bend_angle"),
        ({"branch_tube_outer_diameter": (50.0, "mm")}, "branch_tube_outer_diameter"),
        ({"common_tube_outer_diameter": (80.0, "mm")}, "common_tube_outer_diameter"),
        ({"branch_illuminated_straight_length": (0.0, "m"), "branch_dark_straight_length": (0.0, "m"), "branch_bend_count": (0, "1"), "branch_illuminated_bend_count": (0, "1"), "branch_bend_centerline_radius": (0.0, "mm"), "branch_bend_angle": (0.0, "deg"), "branch_bend_loss_coefficient_per_bend": (0.0, "1")}, "branch_illuminated_straight_length"),
    ],
)
def test_invalid_cross_field_topology_fails_closed(tmp_path, overrides, field):
    completed = run_model(tmp_path, input_set(**overrides))
    assert completed.returncode != 0
    assert "bluerev_topology_error:" in completed.stderr
    assert field in completed.stderr
    assert not (tmp_path / "result.json").exists()


def test_invalid_source_parameter_id_fails_closed(tmp_path):
    payload = input_set()
    payload["liquid_density"]["source_parameter_id"] = 5
    completed = run_model(tmp_path, payload)
    assert completed.returncode != 0
    assert "liquid_density" in completed.stderr


def test_one_path_degenerate_case_matches_047_equations(tmp_path):
    payload = reduction_input()
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    outputs = result["outputs"]

    diameter = 0.05
    outer = 0.06
    length = 12.0
    velocity = 0.5
    density = 1000.0
    viscosity = 0.001
    area = math.pi * diameter**2 / 4.0
    tube_volume = area * length
    external_area = math.pi * outer * length
    flow = velocity * area
    total_inventory = tube_volume + 0.1
    reynolds = density * velocity * diameter / viscosity
    friction = 0.3164 * reynolds**-0.25
    dynamic_pressure = density * velocity**2 / 2.0
    major = friction * (length / diameter) * dynamic_pressure
    minor = 0.1 * dynamic_pressure
    total_loss = major + minor
    hydraulic_power = total_loss * flow

    assert outputs["branch_liquid_volume_total"]["value"] == pytest.approx(tube_volume)
    assert outputs["total_liquid_inventory"]["value"] == pytest.approx(total_inventory)
    assert outputs["illuminated_branch_external_area"]["value"] == pytest.approx(external_area)
    assert outputs["total_circulation_flow_rate"]["value"] == pytest.approx(flow)
    assert outputs["branch_nominal_transit_time"]["value"] == pytest.approx(length / velocity)
    assert outputs["total_inventory_turnover_time"]["value"] == pytest.approx(total_inventory / flow)
    assert outputs["branch_reynolds_number"]["value"] == pytest.approx(reynolds)
    assert outputs["branch_darcy_friction_factor"]["value"] == pytest.approx(friction)
    assert outputs["branch_major_pressure_loss"]["value"] == pytest.approx(major)
    assert outputs["branch_misc_pressure_loss"]["value"] == pytest.approx(minor)
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(total_loss)
    assert outputs["hydraulic_power"]["value"] == pytest.approx(hydraulic_power)
    assert outputs["pump_electric_power"]["value"] == pytest.approx(hydraulic_power / 0.7)
    assert result["diagnostics"]["m0_reduction_status"] == "exact_047_reduction"
    assert result["diagnostics"]["single_length_projection_status"] == (
        "single_length_representable"
    )
    assert outputs["common_supply_nominal_transit_time"]["value"] == 0.0
    assert outputs["common_return_nominal_transit_time"]["value"] == 0.0


@pytest.mark.parametrize(
    ("overrides", "qualified"),
    [
        ({"target_branch_velocity": (0.02, "m/s"), "parallel_path_count": (1, "1"), "common_tube_inner_diameter": (50.0, "mm"), "common_tube_outer_diameter": (60.0, "mm")}, True),
        ({}, True),
        ({"target_branch_velocity": (0.06, "m/s")}, False),
        ({"common_tube_inner_diameter": (833.3333333333, "mm"), "common_tube_outer_diameter": (850.0, "mm")}, False),
    ],
)
def test_branch_and_common_correlation_qualification(tmp_path, overrides, qualified):
    completed = run_model(tmp_path, input_set(**overrides))
    assert (completed.returncode == 0) is qualified
    if not qualified:
        assert "correlation_not_qualified" in completed.stderr
''', encoding="utf-8")

RUNNER_TEST.write_text(r'''import hashlib
import json
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.safety import RunnerSafetyError, preflight_script_policy, sha256_file
from app.modules.runner.topology_m1 import (
    MODEL_LABEL,
    bundled_contract_path,
    bundled_script_path,
    is_exact_bundled_profile,
    validate_manifest,
)


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _valid_input() -> dict[str, object]:
    fixture = Path(__file__).parent / "fixtures" / "bluerev_process_topology_m1_valid.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def _register_and_create_job(client: TestClient):
    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    registered = client.post(endpoint)
    assert registered.status_code == 200, registered.text
    implementation = registered.json()
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    return implementation, created.json()["runner_job"]


def test_topology_m1_registration_preview_run_and_artifacts(client: TestClient) -> None:
    endpoint = "/workspaces/bluerev/bundled-models/bluerev-process-topology-m1-v0/register"
    first = client.post(endpoint)
    second = client.post(endpoint)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    implementation = first.json()
    assert second.json()["id"] == implementation["id"]
    assert implementation["version_label"] == MODEL_LABEL
    assert implementation["script_sha256"] == sha256_file(bundled_script_path())

    preview = client.post(
        f"/workspaces/bluerev/model-implementations/{implementation['id']}/binding-preview",
        json={"bindings": _valid_input()},
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["state"] == "ready"
    assert preview_body["structural_input_dof"] == 26
    assert preview_body["bound_input_dof"] == 26
    assert preview_body["unresolved_input_dof"] == 0

    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": _valid_input()},
    )
    assert created.status_code == 201, created.text
    runner_job = created.json()["runner_job"]
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200, executed.text
    body = executed.json()
    assert body["runner_job"]["status"] == "succeeded"
    assert body["error"] is None
    diagnostics = body["output"]["diagnostics"]
    assert diagnostics["model_id"] == "bluerev_process_topology_m1_v0"

    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200, artifacts.text
    rows = artifacts.json()
    assert [(row["role"], row["filename"]) for row in rows] == [
        ("calc_result_json", "result.json"),
        ("bluerev_topology_manifest", "topology_manifest.json"),
    ]
    assert all(row["under_data_root"] for row in rows)
    assert all(row["sha256"] and len(row["sha256"]) == 64 for row in rows)
    manifest_row = next(row for row in rows if row["role"] == "bluerev_topology_manifest")
    assert diagnostics["topology_manifest_sha256"] == f"sha256:{manifest_row['sha256']}"

    repeated = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert repeated.status_code == 409


def test_exact_profile_requires_kind_label_script_and_contract_hash() -> None:
    contract = json.loads(bundled_contract_path().read_text(encoding="utf-8"))
    _, contract_sha, _ = canonicalize_input_contract(contract)
    script_sha = sha256_file(bundled_script_path())
    exact = {
        "implementation_kind": "calc_v0",
        "version_label": MODEL_LABEL,
        "script_sha256": script_sha,
        "input_contract_sha256": contract_sha,
    }
    assert is_exact_bundled_profile(exact, script_sha) is True
    for key, value in (
        ("implementation_kind", "bluecad_l2_v0"),
        ("version_label", "wrong"),
        ("script_sha256", "0" * 64),
        ("input_contract_sha256", "0" * 64),
    ):
        changed = dict(exact)
        changed[key] = value
        assert is_exact_bundled_profile(changed, script_sha) is False


@pytest.mark.parametrize(
    "source",
    [
        "import hashlib\n",
        "with open('topology_manifest.json', 'w', encoding='utf-8') as handle:\n    handle.write('{}')\n",
    ],
)
def test_generic_calc_cannot_activate_topology_surface(tmp_path: Path, source: str) -> None:
    script = tmp_path / "calc_v0.py"
    script.write_text(source, encoding="utf-8")
    with pytest.raises(RunnerSafetyError) as exc_info:
        preflight_script_policy(script, ast_policy="calc_v0")
    assert exc_info.value.code == "SANDBOX_VIOLATION"


def test_exact_profile_allows_only_fixed_manifest_write(tmp_path: Path) -> None:
    valid = tmp_path / "valid.py"
    valid.write_text(
        "import hashlib\n"
        "with open('input.json', encoding='utf-8') as source:\n    source.read()\n"
        "with open('topology_manifest.json', 'w', encoding='utf-8') as target:\n    target.write('{}')\n"
        "with open('result.json', 'w', encoding='utf-8') as target:\n    target.write('{}')\n",
        encoding="utf-8",
    )
    preflight_script_policy(valid, ast_policy="calc_v0_topology_m1")

    for source in (
        "with open('other.json', 'w') as handle:\n    handle.write('{}')\n",
        "with open('topology_manifest.json', 'a') as handle:\n    handle.write('{}')\n",
    ):
        invalid = tmp_path / f"invalid-{hashlib.sha256(source.encode()).hexdigest()}.py"
        invalid.write_text(source, encoding="utf-8")
        with pytest.raises(RunnerSafetyError):
            preflight_script_policy(invalid, ast_policy="calc_v0_topology_m1")


def _direct_model_run(tmp_path: Path):
    payload = _valid_input()
    (tmp_path / "input.json").write_text(json.dumps(payload), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(bundled_script_path())],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    return payload, result


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("missing", "runner_topology_manifest_missing"),
        ("malformed", "runner_topology_manifest_invalid"),
        ("noncanonical", "runner_topology_manifest_noncanonical"),
        ("schema", "runner_topology_manifest_schema_invalid"),
        ("input", "runner_topology_manifest_input_mismatch"),
        ("digest", "runner_topology_manifest_digest_mismatch"),
    ],
)
def test_manifest_failure_matrix(tmp_path: Path, mutation: str, code: str) -> None:
    payload, result = _direct_model_run(tmp_path)
    path = tmp_path / "topology_manifest.json"
    if mutation == "missing":
        path.unlink()
    elif mutation == "malformed":
        path.write_text("{", encoding="utf-8")
    else:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "schema":
            manifest["topology_kind"] = "wrong"
        elif mutation == "input":
            manifest["executed_inputs"]["liquid_density"]["value"] = 999.0
        raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if mutation == "noncanonical":
            raw = json.dumps(manifest, indent=2, sort_keys=True)
        path.write_text(raw, encoding="utf-8")
        if mutation in {"schema", "input"}:
            result["diagnostics"]["topology_manifest_sha256"] = (
                f"sha256:{hashlib.sha256(raw.encode()).hexdigest()}"
            )
        if mutation == "digest":
            result["diagnostics"]["topology_manifest_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_manifest(
            tmp_path,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
            result,
            max_bytes=1024 * 1024,
        )
    assert exc_info.value.code == code


def test_invalid_manifest_fails_run_before_artifact_registration(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.runner import service

    original_execute = service.execute_python_script

    def corrupt_manifest(**kwargs):
        execution = original_execute(**kwargs)
        (Path(kwargs["output_dir"]) / "topology_manifest.json").write_text(
            "{",
            encoding="utf-8",
        )
        return execution

    monkeypatch.setattr(service, "execute_python_script", corrupt_manifest)
    _, runner_job = _register_and_create_job(client)
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200
    body = executed.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["error"]["code"] == "runner_topology_manifest_invalid"
    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200
    assert artifacts.json() == []


def test_caller_artifact_declaration_is_rejected_before_registration(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.modules.runner import service

    original_execute = service.execute_python_script

    def declare_artifact(**kwargs):
        execution = original_execute(**kwargs)
        result_path = Path(kwargs["output_dir"]) / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["artifacts"] = []
        result_path.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return execution

    monkeypatch.setattr(service, "execute_python_script", declare_artifact)
    _, runner_job = _register_and_create_job(client)
    executed = client.post(f"/runner-jobs/{runner_job['id']}/run")
    assert executed.status_code == 200
    body = executed.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["error"]["code"] == "runner_topology_artifact_declaration_forbidden"
''', encoding="utf-8")
