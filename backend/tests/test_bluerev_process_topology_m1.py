import hashlib
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
