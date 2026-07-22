import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app/modules/runner/examples/bluerev_process_topology_m1_v0.py"
CONTRACT = ROOT / "app/modules/runner/examples/bluerev_process_topology_m1_v0.contract.json"
SCHEMA = ROOT.parent / "schemas/bluerev_process_topology_m1_v0_1.schema.json"


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
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed


def test_contract_and_schema_are_value_free_and_closed():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["evaluation_mode"] == "forward"
    assert len(contract["variables"]) == 26
    assert all("default" not in variable for variable in contract["variables"])
    assert len({variable["name"] for variable in contract["variables"]}) == 26

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["model_label"]["const"] == "bluerev-process-topology-m1-v0.1.0"
    assert schema["additionalProperties"] is False


def test_symmetric_topology_scales_inventory_not_path_pressure(tmp_path):
    completed = run_model(tmp_path, input_set())
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "topology_manifest.json").read_text(encoding="utf-8"))

    outputs = result["outputs"]
    assert outputs["installed_branch_length_total"]["value"] == pytest.approx(
        2 * outputs["branch_length_each"]["value"]
    )
    assert outputs["total_circulation_flow_rate"]["value"] == pytest.approx(
        2 * outputs["branch_flow_rate_each"]["value"]
    )
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(
        outputs["branch_path_pressure_loss"]["value"] + outputs["common_path_pressure_loss"]["value"]
    )
    assert manifest["topology"]["parallel_path_count"] == 2
    assert manifest["topology"]["components"][2]["multiplicity"] == 2
    assert len(manifest["topology_digest"]) == 64


def test_manifest_digest_and_input_identity_are_deterministic(tmp_path):
    payload = input_set()
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "topology_manifest.json").read_text(encoding="utf-8"))

    expected_input = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert manifest["input_sha256"] == hashlib.sha256(expected_input.encode()).hexdigest()
    topology_digest = manifest.pop("topology_digest")
    expected_manifest = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert topology_digest == hashlib.sha256(expected_manifest.encode()).hexdigest()
    assert result["diagnostics"]["topology_digest"] == topology_digest


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"parallel_path_count": (1.5, "1")}, "parallel_path_count"),
        ({"branch_bend_count": (0, "1"), "branch_bend_centerline_radius": (1.0, "mm")}, "branch_bend_centerline_radius"),
        ({"branch_bend_count": (0, "1"), "branch_bend_loss_coefficient_per_bend": (0.1, "1")}, "branch_bend_loss_coefficient_per_bend"),
        ({"branch_bend_centerline_radius": (30.0, "mm")}, "branch_bend_centerline_radius"),
        ({"branch_bend_angle": (181.0, "deg")}, "branch_bend_angle"),
        ({"branch_tube_outer_diameter": (50.0, "mm")}, "branch_tube_outer_diameter"),
    ],
)
def test_invalid_cross_field_topology_fails_closed(tmp_path, overrides, field):
    completed = run_model(tmp_path, input_set(**overrides))
    assert completed.returncode != 0
    assert "bluerev_topology_error:" in completed.stderr
    assert field in completed.stderr
    assert not (tmp_path / "result.json").exists()


def test_one_path_degenerate_case_matches_047_core_semantics(tmp_path):
    payload = input_set(
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
    completed = run_model(tmp_path, payload)
    assert completed.returncode == 0, completed.stderr
    outputs = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))["outputs"]

    diameter = 0.05
    length = 12.0
    velocity = 0.5
    area = 3.141592653589793 * diameter**2 / 4.0
    reynolds = 1000.0 * velocity * diameter / 0.001
    friction = 0.3164 * reynolds**-0.25
    dynamic_pressure = 1000.0 * velocity**2 / 2.0
    expected_major = friction * (length / diameter) * dynamic_pressure
    expected_misc = 0.1 * dynamic_pressure

    assert outputs["branch_liquid_volume_total"]["value"] == pytest.approx(area * length)
    assert outputs["total_circulation_flow_rate"]["value"] == pytest.approx(velocity * area)
    assert outputs["branch_major_pressure_loss"]["value"] == pytest.approx(expected_major)
    assert outputs["total_pressure_loss"]["value"] == pytest.approx(expected_major + expected_misc)
