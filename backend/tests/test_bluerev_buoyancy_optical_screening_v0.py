import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "app/modules/runner/examples/bluerev_buoyancy_optical_screening_v0.py"
CONTRACT_PATH = ROOT / "app/modules/runner/examples/bluerev_buoyancy_optical_screening_v0.contract.json"
REGISTER_ENDPOINT = "/workspaces/bluerev/bundled-models/bluerev-buoyancy-optical-screening-v0/register"


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


def contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def baseline(*, auxiliary_volume: float | None = None) -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {
        "tube_material_mass": {"value": 7.402220610388268, "unit": "kg"},
        "contained_liquid_volume": {"value": 0.019137166941154067, "unit": "m3"},
        "contained_liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "attached_hardware_mass": {"value": 5.0, "unit": "kg"},
        "other_supported_payload_mass": {"value": 2.0, "unit": "kg"},
        "external_fluid_density": {"value": 1025.0, "unit": "kg/m3"},
        "buoyancy_safety_factor": {"value": 1.3, "unit": "1"},
        "inherent_displacement_volume": {"value": 0.0, "unit": "m3"},
        "clean_tube_transmittance": {"value": 0.92, "unit": "1"},
        "daily_fouling_loss_fraction": {"value": 0.01, "unit": "1"},
        "cleaning_interval": {"value": 7.0, "unit": "d"},
        "culture_attenuation_coefficient": {"value": 1.0, "unit": "L/gDW/m"},
        "operating_biomass_concentration": {"value": 0.8, "unit": "gDW/L"},
        "optical_path_length": {"value": 0.03, "unit": "m"},
    }
    if auxiliary_volume is not None:
        values["available_auxiliary_flotation_volume"] = {
            "value": auxiliary_volume,
            "unit": "m3",
        }
    return values


def register(client: TestClient) -> dict[str, object]:
    response = client.post(REGISTER_ENDPOINT)
    assert response.status_code == 200, response.text
    return response.json()


def preview(client: TestClient, implementation_id: str, bindings: dict[str, object]) -> dict[str, object]:
    response = client.post(
        f"/workspaces/bluerev/model-implementations/{implementation_id}/binding-preview",
        json={"bindings": bindings},
    )
    assert response.status_code == 200, response.text
    return response.json()


def run_scenario(
    client: TestClient,
    implementation_id: str,
    bindings: dict[str, object],
    label: str,
) -> dict[str, object]:
    prepared = preview(client, implementation_id, bindings)
    assert prepared["state"] == "ready", prepared
    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation_id,
            "run_label": label,
            "input_set": prepared["normalized_input_set"],
        },
    )
    assert created.status_code == 201, created.text
    result = client.post(f"/runner-jobs/{created.json()['runner_job']['id']}/run")
    assert result.status_code == 200, result.text
    return result.json()


def output_value(result: dict[str, object], name: str) -> float:
    return float(result["output"]["outputs"][name]["value"])


def test_049_contract_is_value_free_and_optional_float_does_not_consume_dof(client: TestClient) -> None:
    stored_contract = contract()
    variables = stored_contract["variables"]
    assert len(variables) == 15
    assert sum(bool(variable["required"]) for variable in variables) == 14
    optional = next(
        variable for variable in variables if variable["name"] == "available_auxiliary_flotation_volume"
    )
    assert optional["required"] is False

    forbidden = {"value", "default", "recommended_value", "initial_guess"}
    assert all(not forbidden.intersection(variable) for variable in variables)

    encoded = json.dumps(stored_contract, sort_keys=True, separators=(",", ":"), allow_nan=False)
    implementation = register(client)
    assert implementation["input_contract_sha256"] == hashlib.sha256(encoded.encode()).hexdigest()
    assert implementation["version_label"] == "bluerev-buoyancy-optical-screening-v0-bundled"

    empty = preview(client, implementation["id"], {})
    assert empty["state"] == "incomplete"
    assert empty["structural_input_dof"] == 14
    assert empty["bound_input_dof"] == 0
    assert empty["unresolved_input_dof"] == 14

    ready = preview(client, implementation["id"], baseline())
    assert ready["state"] == "ready"
    assert ready["bound_input_dof"] == 14
    assert ready["unresolved_input_dof"] == 0
    optional_preview = next(
        variable for variable in ready["variables"] if variable["name"] == "available_auxiliary_flotation_volume"
    )
    assert optional_preview["binding_state"] == "missing"


def test_049_registration_is_idempotent_and_uses_repository_script(client: TestClient) -> None:
    first = register(client)
    second = register(client)
    assert second["id"] == first["id"]
    assert first["script_sha256"] == hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
    implementations = client.get("/workspaces/bluerev/model-implementations").json()
    assert [item["id"] for item in implementations] == [first["id"]]


def test_049_golden_case_without_optional_float_is_honest(client: TestClient) -> None:
    implementation = register(client)
    result = run_scenario(client, implementation["id"], baseline(), "golden-no-float")
    assert result["runner_job"]["status"] == "succeeded"
    assert len(result["output"]["outputs"]) == 10

    expected = {
        "contained_liquid_mass": 19.61559611468292,
        "supported_wet_mass": 34.017816725071185,
        "design_supported_mass": 44.22316174259254,
        "neutral_buoyancy_displacement_volume": 0.03318811387811823,
        "design_required_displacement_volume": 0.04314454804155370,
        "additional_auxiliary_flotation_required": 0.04314454804155370,
        "tube_transmittance_after_interval": 0.8575001200744308,
        "optical_depth_proxy": 0.024,
        "culture_only_transmission_proxy": 0.9762857097579093,
        "combined_transmission_proxy": 0.8371651133443581,
    }
    for name, expected_value in expected.items():
        assert output_value(result, name) == pytest.approx(expected_value, rel=1e-12, abs=1e-15)

    assert "buoyancy_volume_margin" not in result["output"]["outputs"]
    diagnostics = result["output"]["diagnostics"]
    assert diagnostics["center_light_not_claimed"] is True
    assert diagnostics["optical_path_not_auto_derived"] is True
    assert diagnostics["buoyancy_availability_check"] == {
        "status": "not_computable",
        "reason": "missing_available_auxiliary_flotation_volume",
    }
    assert diagnostics["input_evidence"]["available_auxiliary_flotation_volume"]["binding_state"] == (
        "missing_optional"
    )
    assert not any("center_light" in name for name in result["output"]["outputs"])


def test_049_optional_float_margin_and_parameter_provenance(client: TestClient) -> None:
    implementation = register(client)
    parameter = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": "Contained liquid volume", "value": "0.019137166941154067", "unit": "m3"},
    )
    assert parameter.status_code == 201

    bindings = baseline(auxiliary_volume=0.05)
    bindings["contained_liquid_volume"]["source_parameter_id"] = parameter.json()["id"]
    result = run_scenario(client, implementation["id"], bindings, "golden-float")
    assert result["runner_job"]["status"] == "succeeded"
    assert len(result["output"]["outputs"]) == 14

    assert output_value(result, "total_available_displacement_volume") == pytest.approx(0.05)
    assert output_value(result, "buoyancy_volume_margin") == pytest.approx(
        0.00685545195844630, rel=1e-12, abs=1e-15
    )
    assert output_value(result, "buoyancy_mass_margin") == pytest.approx(
        7.026838257407458, rel=1e-12, abs=1e-15
    )
    assert output_value(result, "displacement_utilization") == pytest.approx(
        0.862890960831074, rel=1e-12, abs=1e-15
    )
    assert result["output"]["diagnostics"]["buoyancy_availability_check"] == {
        "status": "computable",
        "buoyancy_check": "pass",
    }
    evidence = result["output"]["diagnostics"]["input_evidence"]["contained_liquid_volume"]
    assert evidence["binding_state"] == "parameter"
    assert evidence["source_parameter_id"] == parameter.json()["id"]
    assert evidence["uncertainty_state"] == "not_characterized"


def test_049_buoyancy_metamorphic_relationships(client: TestClient) -> None:
    implementation = register(client)
    base = run_scenario(client, implementation["id"], baseline(auxiliary_volume=0.05), "base")

    heavier_inputs = baseline(auxiliary_volume=0.05)
    heavier_inputs["attached_hardware_mass"]["value"] = 8.0
    heavier = run_scenario(client, implementation["id"], heavier_inputs, "heavier")
    assert output_value(heavier, "supported_wet_mass") - output_value(base, "supported_wet_mass") == pytest.approx(3.0)
    assert output_value(heavier, "design_required_displacement_volume") > output_value(
        base, "design_required_displacement_volume"
    )

    safer_inputs = baseline(auxiliary_volume=0.05)
    safer_inputs["buoyancy_safety_factor"]["value"] = 1.5
    safer = run_scenario(client, implementation["id"], safer_inputs, "safer")
    assert output_value(safer, "neutral_buoyancy_displacement_volume") == pytest.approx(
        output_value(base, "neutral_buoyancy_displacement_volume")
    )
    assert output_value(safer, "design_required_displacement_volume") > output_value(
        base, "design_required_displacement_volume"
    )

    denser_inputs = baseline(auxiliary_volume=0.05)
    denser_inputs["external_fluid_density"]["value"] = 1030.0
    denser = run_scenario(client, implementation["id"], denser_inputs, "denser")
    assert output_value(denser, "design_required_displacement_volume") < output_value(
        base, "design_required_displacement_volume"
    )

    insufficient_inputs = baseline(auxiliary_volume=0.02)
    insufficient = run_scenario(client, implementation["id"], insufficient_inputs, "insufficient")
    assert output_value(insufficient, "buoyancy_volume_margin") < 0
    assert insufficient["output"]["diagnostics"]["buoyancy_availability_check"]["buoyancy_check"] == "fail"


def test_049_optical_metamorphic_relationships(client: TestClient) -> None:
    implementation = register(client)
    base = run_scenario(client, implementation["id"], baseline(), "optical-base")

    clean_inputs = baseline()
    clean_inputs["cleaning_interval"]["value"] = 0.0
    clean = run_scenario(client, implementation["id"], clean_inputs, "clean")
    assert output_value(clean, "tube_transmittance_after_interval") == pytest.approx(0.92)

    zero_fouling_inputs = baseline()
    zero_fouling_inputs["daily_fouling_loss_fraction"]["value"] = 0.0
    zero_fouling_inputs["cleaning_interval"]["value"] = 100.0
    zero_fouling = run_scenario(client, implementation["id"], zero_fouling_inputs, "zero-fouling")
    assert output_value(zero_fouling, "tube_transmittance_after_interval") == pytest.approx(0.92)

    longer_inputs = baseline()
    longer_inputs["cleaning_interval"]["value"] = 14.0
    longer = run_scenario(client, implementation["id"], longer_inputs, "longer")
    assert output_value(longer, "tube_transmittance_after_interval") < output_value(
        base, "tube_transmittance_after_interval"
    )

    zero_attenuation_inputs = baseline()
    zero_attenuation_inputs["culture_attenuation_coefficient"]["value"] = 0.0
    zero_attenuation = run_scenario(client, implementation["id"], zero_attenuation_inputs, "zero-k")
    assert output_value(zero_attenuation, "culture_only_transmission_proxy") == pytest.approx(1.0)

    longer_path_inputs = baseline()
    longer_path_inputs["optical_path_length"]["value"] = 0.06
    longer_path = run_scenario(client, implementation["id"], longer_path_inputs, "longer-path")
    assert output_value(longer_path, "culture_only_transmission_proxy") < output_value(
        base, "culture_only_transmission_proxy"
    )
    assert output_value(longer_path, "combined_transmission_proxy") < output_value(
        base, "combined_transmission_proxy"
    )


def test_049_invalid_domain_is_rejected_before_execution(client: TestClient) -> None:
    implementation = register(client)
    bindings = baseline()
    bindings["daily_fouling_loss_fraction"]["value"] = 1.0
    prepared = preview(client, implementation["id"], bindings)
    assert prepared["state"] == "invalid"
    variable = next(
        item for item in prepared["variables"] if item["name"] == "daily_fouling_loss_fraction"
    )
    assert "binding_domain_violation" in variable["errors"]
