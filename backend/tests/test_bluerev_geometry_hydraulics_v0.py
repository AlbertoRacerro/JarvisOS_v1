import hashlib
import json
import math
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "runner"
    / "examples"
    / "bluerev_geometry_hydraulics_v0.py"
)

EXPECTED_UNITS = {
    "tube_hydraulic_cross_section_area": "m2",
    "tube_liquid_volume": "m3",
    "total_liquid_inventory": "m3",
    "external_illuminated_area_proxy": "m2",
    "internal_wetted_area_to_tube_volume": "1/m",
    "external_area_to_tube_volume_proxy": "1/m",
    "circulation_flow_rate": "m3/s",
    "tube_nominal_transit_time": "s",
    "total_inventory_turnover_time": "s",
    "reynolds_number": "1",
    "darcy_friction_factor": "1",
    "major_pressure_loss": "Pa",
    "minor_pressure_loss": "Pa",
    "total_pressure_loss": "Pa",
    "equivalent_static_head": "m",
    "hydraulic_power": "W",
    "pump_electric_power": "W",
}


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "JarvisOS"))
    monkeypatch.setenv("DATABASE_URL", "must-not-enter-runner")

    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def _baseline_input() -> dict[str, dict[str, object]]:
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {
            "value": 30.0,
            "unit": "mm",
            "source_parameter_id": "tube-inner-diameter",
        },
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": 0.25, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }


def _create_implementation(client: TestClient) -> dict[str, object]:
    spec_response = client.post(
        "/workspaces/bluerev/model-specs",
        json={
            "title": "BlueRev geometry and hydraulics V0",
            "engineering_question": "Screen tubular-loop geometry, circulation losses, and pump power.",
        },
    )
    assert spec_response.status_code == 201, spec_response.text

    response = client.post(
        "/workspaces/bluerev/model-implementations",
        json={
            "model_spec_id": spec_response.json()["id"],
            "version_label": "bluerev-geometry-hydraulics-v0",
            "implementation_kind": "calc_v0",
            "script_text": SCRIPT_PATH.read_text(encoding="utf-8"),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_job(
    client: TestClient,
    implementation: dict[str, object],
    input_set: dict[str, dict[str, object]],
) -> dict[str, object]:
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "run_label": "bluerev-process-0-test",
            "input_set": input_set,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _run(
    client: TestClient,
    implementation: dict[str, object],
    input_set: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    job = _create_job(client, implementation, input_set or _baseline_input())
    response = client.post(f"/runner-jobs/{job['runner_job']['id']}/run")
    assert response.status_code == 200, response.text
    return response.json()


def _outputs(body: dict[str, object]) -> dict[str, dict[str, object]]:
    output = body["output"]
    assert isinstance(output, dict)
    outputs = output["outputs"]
    assert isinstance(outputs, dict)
    return outputs


def _value(outputs: dict[str, dict[str, object]], name: str) -> float:
    return float(outputs[name]["value"])


def _expected_baseline() -> dict[str, float]:
    tube_length = 20.0
    diameter_inner = 30.0 / 1000.0
    diameter_outer = 36.0 / 1000.0
    reservoir_volume = 5.0 / 1000.0
    velocity = 0.25
    density = 1025.0
    viscosity = 0.0011
    minor_loss_coefficient = 8.0
    pump_efficiency = 0.35
    gravity = 9.80665

    hydraulic_area = math.pi * diameter_inner**2 / 4.0
    tube_volume = hydraulic_area * tube_length
    total_inventory = tube_volume + reservoir_volume
    external_area = math.pi * diameter_outer * tube_length
    internal_area = math.pi * diameter_inner * tube_length
    circulation_flow = velocity * hydraulic_area
    reynolds_number = density * velocity * diameter_inner / viscosity
    friction_factor = 0.3164 * reynolds_number**-0.25
    dynamic_pressure = density * velocity**2 / 2.0
    major_loss = friction_factor * (tube_length / diameter_inner) * dynamic_pressure
    minor_loss = minor_loss_coefficient * dynamic_pressure
    total_loss = major_loss + minor_loss
    hydraulic_power = total_loss * circulation_flow

    return {
        "tube_hydraulic_cross_section_area": hydraulic_area,
        "tube_liquid_volume": tube_volume,
        "total_liquid_inventory": total_inventory,
        "external_illuminated_area_proxy": external_area,
        "internal_wetted_area_to_tube_volume": internal_area / tube_volume,
        "external_area_to_tube_volume_proxy": external_area / tube_volume,
        "circulation_flow_rate": circulation_flow,
        "tube_nominal_transit_time": tube_length / velocity,
        "total_inventory_turnover_time": total_inventory / circulation_flow,
        "reynolds_number": reynolds_number,
        "darcy_friction_factor": friction_factor,
        "major_pressure_loss": major_loss,
        "minor_pressure_loss": minor_loss,
        "total_pressure_loss": total_loss,
        "equivalent_static_head": total_loss / (density * gravity),
        "hydraulic_power": hydraulic_power,
        "pump_electric_power": hydraulic_power / pump_efficiency,
    }


def _changed_input(name: str, value: float) -> dict[str, dict[str, object]]:
    inputs = _baseline_input()
    inputs[name] = {**inputs[name], "value": value}
    return inputs


def test_reviewed_script_registers_with_exact_repository_digest(client: TestClient) -> None:
    implementation = _create_implementation(client)

    expected_digest = hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
    assert implementation["script_sha256"] == expected_digest
    assert Path(str(implementation["script_path"])).read_bytes() == SCRIPT_PATH.read_bytes()


def test_baseline_runs_through_real_calc_v0_and_creates_only_proposals(
    client: TestClient,
) -> None:
    implementation = _create_implementation(client)
    body = _run(client, implementation)

    assert body["runner_job"]["status"] == "succeeded"
    assert body["simulation_run"]["status"] == "succeeded"
    assert body["error"] is None
    assert "must-not-enter-runner" not in json.dumps(body)

    outputs = _outputs(body)
    expected = _expected_baseline()
    assert set(outputs) == set(EXPECTED_UNITS) == set(expected)
    for name, expected_value in expected.items():
        assert outputs[name]["unit"] == EXPECTED_UNITS[name]
        assert _value(outputs, name) == pytest.approx(expected_value, rel=1e-12, abs=1e-15)

    assert body["output"]["diagnostics"] == {
        "model_id": "bluerev_geometry_hydraulics_v0",
        "model_fidelity": "M0_static_screening",
        "friction_factor_convention": "Darcy",
        "friction_correlation": "blasius_smooth_pipe_v0",
        "circulation_semantics": "closed_loop_recirculation",
        "time_semantics": [
            "tube_nominal_transit_time",
            "total_inventory_turnover_time",
        ],
        "external_area_is_proxy": True,
        "pump_curve_not_applied": True,
        "npsh_not_evaluated": True,
        "transient_pressure_not_evaluated": True,
        "minor_loss_coefficient_provisional": True,
        "workbook_runtime_dependency": False,
    }

    artifacts = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts.status_code == 200
    assert [(item["role"], item["filename"]) for item in artifacts.json()] == [
        ("calc_result_json", "result.json")
    ]

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT name, status, origin, source_ref FROM parameters ORDER BY name"
        ).fetchall()
    assert len(rows) == len(EXPECTED_UNITS)
    assert {row["name"] for row in rows} == set(EXPECTED_UNITS)
    assert all(row["status"] == "proposed" for row in rows)
    assert all(row["origin"] == "calc" for row in rows)
    assert all(
        row["source_ref"] == f"runner_job:{body['runner_job']['id']}"
        for row in rows
    )


def test_result_json_is_byte_deterministic_for_identical_inputs(client: TestClient) -> None:
    implementation = _create_implementation(client)
    digests: list[str] = []
    for _ in range(2):
        body = _run(client, implementation)
        result_path = Path(str(body["runner_job"]["output_dir"])) / "result.json"
        digests.append(hashlib.sha256(result_path.read_bytes()).hexdigest())
    assert digests[0] == digests[1]


def test_pressure_and_power_reconcile_independently(client: TestClient) -> None:
    body = _run(client, _create_implementation(client))
    outputs = _outputs(body)

    major = _value(outputs, "major_pressure_loss")
    minor = _value(outputs, "minor_pressure_loss")
    total = _value(outputs, "total_pressure_loss")
    flow = _value(outputs, "circulation_flow_rate")
    hydraulic = _value(outputs, "hydraulic_power")
    electric = _value(outputs, "pump_electric_power")

    assert total == pytest.approx(major + minor, rel=1e-15)
    assert hydraulic == pytest.approx(total * flow, rel=1e-15)
    assert electric == pytest.approx(hydraulic / 0.35, rel=1e-15)


def test_outer_diameter_changes_only_external_geometry_outputs(client: TestClient) -> None:
    implementation = _create_implementation(client)
    baseline = _outputs(_run(client, implementation))
    changed = _outputs(
        _run(client, implementation, _changed_input("tube_outer_diameter", 42.0))
    )

    changed_names = {
        name
        for name in EXPECTED_UNITS
        if _value(changed, name) != pytest.approx(_value(baseline, name), rel=1e-14)
    }
    assert changed_names == {
        "external_illuminated_area_proxy",
        "external_area_to_tube_volume_proxy",
    }


def test_inner_diameter_does_not_change_external_illuminated_area(client: TestClient) -> None:
    implementation = _create_implementation(client)
    baseline = _outputs(_run(client, implementation))
    changed = _outputs(
        _run(client, implementation, _changed_input("tube_inner_diameter", 32.0))
    )

    assert _value(changed, "external_illuminated_area_proxy") == pytest.approx(
        _value(baseline, "external_illuminated_area_proxy"), rel=1e-15
    )
    for name in (
        "tube_hydraulic_cross_section_area",
        "tube_liquid_volume",
        "circulation_flow_rate",
        "reynolds_number",
        "total_pressure_loss",
        "pump_electric_power",
    ):
        assert _value(changed, name) != pytest.approx(_value(baseline, name), rel=1e-12)


def test_reservoir_volume_changes_only_inventory_and_turnover(client: TestClient) -> None:
    implementation = _create_implementation(client)
    baseline = _outputs(_run(client, implementation))
    changed = _outputs(
        _run(client, implementation, _changed_input("reservoir_liquid_volume", 8.0))
    )

    changed_names = {
        name
        for name in EXPECTED_UNITS
        if _value(changed, name) != pytest.approx(_value(baseline, name), rel=1e-14)
    }
    assert changed_names == {
        "total_liquid_inventory",
        "total_inventory_turnover_time",
    }


def test_length_minor_losses_and_efficiency_have_bounded_dependencies(
    client: TestClient,
) -> None:
    implementation = _create_implementation(client)
    baseline = _outputs(_run(client, implementation))

    doubled = _outputs(_run(client, implementation, _changed_input("tube_length", 40.0)))
    for name in (
        "tube_liquid_volume",
        "external_illuminated_area_proxy",
        "tube_nominal_transit_time",
        "major_pressure_loss",
    ):
        assert _value(doubled, name) == pytest.approx(
            2.0 * _value(baseline, name), rel=1e-12
        )
    for name in (
        "tube_hydraulic_cross_section_area",
        "circulation_flow_rate",
        "reynolds_number",
        "minor_pressure_loss",
    ):
        assert _value(doubled, name) == pytest.approx(_value(baseline, name), rel=1e-15)

    higher_minor = _outputs(
        _run(client, implementation, _changed_input("minor_loss_coefficient", 10.0))
    )
    changed_minor = {
        name
        for name in EXPECTED_UNITS
        if _value(higher_minor, name)
        != pytest.approx(_value(baseline, name), rel=1e-14)
    }
    assert changed_minor == {
        "minor_pressure_loss",
        "total_pressure_loss",
        "equivalent_static_head",
        "hydraulic_power",
        "pump_electric_power",
    }

    efficient = _outputs(
        _run(client, implementation, _changed_input("pump_efficiency", 0.70))
    )
    changed_efficiency = {
        name
        for name in EXPECTED_UNITS
        if _value(efficient, name)
        != pytest.approx(_value(baseline, name), rel=1e-14)
    }
    assert changed_efficiency == {"pump_electric_power"}
    assert _value(efficient, "pump_electric_power") == pytest.approx(
        0.5 * _value(baseline, "pump_electric_power"), rel=1e-15
    )


@pytest.mark.parametrize(
    ("input_set", "expected_reason"),
    [
        (
            {
                key: value
                for key, value in _baseline_input().items()
                if key != "tube_length"
            },
            "bluerev_calc_error:input_contract_invalid",
        ),
        (
            {
                **_baseline_input(),
                "unexpected": {"value": 1.0, "unit": "1"},
            },
            "bluerev_calc_error:input_contract_invalid",
        ),
        (
            {
                **_baseline_input(),
                "tube_length": {"value": 20.0, "unit": "cm"},
            },
            "bluerev_calc_error:input_unit_invalid:tube_length",
        ),
        (
            _changed_input("tube_length", 0.0),
            "bluerev_calc_error:input_domain_invalid:tube_length",
        ),
        (
            _changed_input("tube_outer_diameter", 25.0),
            "bluerev_calc_error:input_domain_invalid:tube_outer_diameter",
        ),
        (
            _changed_input("reservoir_liquid_volume", -1.0),
            "bluerev_calc_error:input_domain_invalid:reservoir_liquid_volume",
        ),
        (
            _changed_input("minor_loss_coefficient", -1.0),
            "bluerev_calc_error:input_domain_invalid:minor_loss_coefficient",
        ),
        (
            _changed_input("pump_efficiency", 1.1),
            "bluerev_calc_error:input_domain_invalid:pump_efficiency",
        ),
        (
            _changed_input("target_liquid_velocity", 0.10),
            "bluerev_calc_error:correlation_not_qualified",
        ),
        (
            _changed_input("target_liquid_velocity", 4.0),
            "bluerev_calc_error:correlation_not_qualified",
        ),
    ],
)
def test_domain_and_correlation_failures_use_bounded_runner_evidence(
    client: TestClient,
    input_set: dict[str, dict[str, object]],
    expected_reason: str,
) -> None:
    implementation = _create_implementation(client)
    job = _create_job(client, implementation, input_set)
    response = client.post(f"/runner-jobs/{job['runner_job']['id']}/run")

    assert response.status_code == 200
    body = response.json()
    assert body["runner_job"]["status"] == "failed"
    assert body["simulation_run"]["status"] == "failed"
    assert body["error"]["code"] == "runner_process_failed"
    assert body["output"] is None

    logs_response = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/logs"
    )
    assert logs_response.status_code == 200
    stderr = "".join(
        item["content"] for item in logs_response.json() if item["stream"] == "stderr"
    ).strip()
    assert stderr == expected_reason

    artifacts_response = client.get(
        f"/workspaces/bluerev/simulation-runs/{body['simulation_run']['id']}/artifacts"
    )
    assert artifacts_response.status_code == 200
    assert artifacts_response.json() == []

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM parameters"
        ).fetchone()["count"] == 0


@pytest.mark.parametrize(
    "input_set",
    [
        {"tube_length": {"value": True, "unit": "m"}},
        {"tube_length": {"value": "nan", "unit": "m"}},
        {"tube_length": {"value": "inf", "unit": "m"}},
        {"tube_length": {"value": 20.0, "unit": ""}},
    ],
)
def test_generic_calc_envelope_rejects_invalid_values_before_queueing(
    client: TestClient,
    input_set: dict[str, dict[str, object]],
) -> None:
    implementation = _create_implementation(client)
    response = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={"model_version_id": implementation["id"], "input_set": input_set},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "runner_input_invalid"

    from app.core.database import open_sqlite_connection

    with open_sqlite_connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) AS count FROM runner_jobs"
        ).fetchone()["count"] == 0


def test_reviewed_script_passes_existing_calc_v0_policy_without_runtime_changes() -> None:
    from app.modules.runner.safety import preflight_script_policy

    preflight_script_policy(SCRIPT_PATH, ast_policy="calc_v0")
