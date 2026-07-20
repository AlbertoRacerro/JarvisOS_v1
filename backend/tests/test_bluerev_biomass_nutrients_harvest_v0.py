import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.py"
CONTRACT_PATH = ROOT / "app/modules/runner/examples/bluerev_biomass_nutrients_harvest_v0.contract.json"
REGISTER_ENDPOINT = "/workspaces/bluerev/bundled-models/bluerev-biomass-nutrients-harvest-v0/register"


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


def baseline(*, product_price: float | None = None) -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {
        "productive_liquid_volume": {"value": 0.019137166941154067, "unit": "m3"},
        "operating_biomass_concentration": {"value": 0.8, "unit": "gDW/L"},
        "volumetric_productivity": {"value": 0.15, "unit": "gDW/L/d"},
        "maximum_specific_growth_rate": {"value": 0.4, "unit": "1/d"},
        "operating_days_per_year": {"value": 300.0, "unit": "d/y"},
        "feed_events_per_day": {"value": 1.0, "unit": "1/d"},
        "biomass_nitrogen_fraction": {"value": 0.06, "unit": "gN/gDW"},
        "biomass_phosphorus_fraction": {"value": 0.008, "unit": "gP/gDW"},
        "biomass_carbon_fraction": {"value": 0.5, "unit": "gC/gDW"},
        "nitrogen_stock_concentration": {"value": 20.0, "unit": "mgN/mL"},
        "phosphorus_stock_concentration": {"value": 2.0, "unit": "mgP/mL"},
        "carbon_stock_concentration": {"value": 20.0, "unit": "mgC/mL"},
        "co2_specific_gas_rate": {"value": 0.8, "unit": "mLCO2/L/min"},
        "harvest_recovery": {"value": 0.9, "unit": "1"},
        "concentrate_biomass_concentration": {"value": 20.0, "unit": "gDW/L"},
        "filtration_flux": {"value": 24.7, "unit": "L/m2/h"},
        "filtration_operating_hours_per_day": {"value": 24.0, "unit": "h/d"},
        "pump_electric_power": {"value": 0.5024804066626467, "unit": "W"},
        "circulation_operating_hours_per_day": {"value": 24.0, "unit": "h/d"},
        "electricity_price": {"value": 0.25, "unit": "EUR/kWh"},
    }
    if product_price is not None:
        values["product_price"] = {"value": product_price, "unit": "EUR/kgDW"}
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


def test_048_contract_is_value_free_and_optional_price_does_not_consume_dof(client: TestClient) -> None:
    stored_contract = contract()
    variables = stored_contract["variables"]
    assert len(variables) == 21
    assert sum(bool(variable["required"]) for variable in variables) == 20
    product_price = next(variable for variable in variables if variable["name"] == "product_price")
    assert product_price["required"] is False

    forbidden = {"value", "default", "recommended_value", "initial_guess"}
    assert all(not forbidden.intersection(variable) for variable in variables)

    encoded = json.dumps(stored_contract, sort_keys=True, separators=(",", ":"), allow_nan=False)
    implementation = register(client)
    assert implementation["input_contract_sha256"] == hashlib.sha256(encoded.encode()).hexdigest()
    assert implementation["version_label"] == "bluerev-biomass-nutrients-harvest-v0-bundled"

    empty = preview(client, implementation["id"], {})
    assert empty["state"] == "incomplete"
    assert empty["structural_input_dof"] == 20
    assert empty["bound_input_dof"] == 0
    assert empty["unresolved_input_dof"] == 20

    ready = preview(client, implementation["id"], baseline())
    assert ready["state"] == "ready"
    assert ready["bound_input_dof"] == 20
    assert ready["unresolved_input_dof"] == 0
    optional = next(variable for variable in ready["variables"] if variable["name"] == "product_price")
    assert optional["binding_state"] == "missing"


def test_048_registration_is_idempotent_and_uses_repository_script(client: TestClient) -> None:
    first = register(client)
    second = register(client)
    assert second["id"] == first["id"]
    assert first["script_sha256"] == hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
    implementations = client.get("/workspaces/bluerev/model-implementations").json()
    assert [item["id"] for item in implementations] == [first["id"]]


def test_048_corrected_golden_case_and_noncomputable_margin(client: TestClient) -> None:
    implementation = register(client)
    result = run_scenario(client, implementation["id"], baseline(), "workbook-corrected")
    assert result["runner_job"]["status"] == "succeeded"
    assert len(result["output"]["outputs"]) == 38

    expected = {
        "biomass_inventory": 0.015309733552923255,
        "gross_biomass_production_rate": 0.00287057504117311,
        "annual_biomass_equivalent": 0.8611725123519329,
        "equivalent_dilution_rate": 0.1875,
        "equivalent_dilution_to_mu_max": 0.46875,
        "nitrogen_incorporation_demand": 172.2345024703866,
        "phosphorus_incorporation_demand": 22.96460032938488,
        "carbon_incorporation_demand": 1435.287520586555,
        "sodium_nitrate_equivalent_dose": 1045.4634299952465,
        "sodium_dihydrogen_phosphate_monohydrate_equivalent_dose": 102.42211746905656,
        "sodium_bicarbonate_equivalent_dose": 10032.659768900021,
        "co2_uptake_equivalent": 5.262720908817368,
        "oxygen_production_equivalent": 3.8274333882308134,
        "oxygen_volume_stp_equivalent": 2.6808778738689205,
        "whole_culture_bleed_rate": 3.5882188014663874,
        "side_stream_processed_rate": 3.9869097794070965,
        "recovered_biomass_rate": 0.00287057504117311,
        "returned_uncaptured_biomass_rate": 0.00031895278235256766,
        "concentrate_volume_rate": 0.1435287520586555,
        "required_filter_area": 0.006725556308041661,
        "pump_electric_energy_rate": 0.012059529759903521,
        "specific_pump_energy": 4.201085004548492,
        "variable_opex_rate": 0.0030148824399758804,
        "specific_variable_cost": 1.050271251137123,
    }
    for name, expected_value in expected.items():
        assert output_value(result, name) == pytest.approx(expected_value, rel=1e-12, abs=1e-15)

    assert result["output"]["outputs"]["oxygen_volume_stp_equivalent"]["unit"] == "L O2/d"
    assert "gross_margin_proxy" not in result["output"]["outputs"]
    diagnostics = result["output"]["diagnostics"]
    assert diagnostics["harvest_recovery_application_count"] == 1
    assert diagnostics["economic_boundary"] == "pump_electricity_only"
    assert diagnostics["full_tea"] is False
    assert diagnostics["economic_kpi_status"]["gross_margin_proxy"] == {
        "status": "not_computable",
        "reason": "missing_product_price",
    }
    assert diagnostics["input_evidence"]["product_price"]["binding_state"] == "missing_optional"


def test_048_recovery_is_applied_once_with_filtrate_return(client: TestClient) -> None:
    implementation = register(client)
    base = run_scenario(client, implementation["id"], baseline(), "recovery-90")

    full_recovery_inputs = baseline()
    full_recovery_inputs["harvest_recovery"]["value"] = 1.0
    full = run_scenario(client, implementation["id"], full_recovery_inputs, "recovery-100")

    lower_recovery_inputs = baseline()
    lower_recovery_inputs["harvest_recovery"]["value"] = 0.75
    lower = run_scenario(client, implementation["id"], lower_recovery_inputs, "recovery-75")

    assert output_value(full, "side_stream_processed_rate") == pytest.approx(
        output_value(full, "whole_culture_bleed_rate")
    )
    assert output_value(full, "returned_uncaptured_biomass_rate") == pytest.approx(0.0, abs=1e-15)
    assert output_value(lower, "side_stream_processed_rate") > output_value(base, "side_stream_processed_rate")
    assert output_value(lower, "required_filter_area") > output_value(base, "required_filter_area")

    for name in ("recovered_biomass_rate", "whole_culture_bleed_rate", "concentrate_volume_rate"):
        assert output_value(lower, name) == pytest.approx(output_value(base, name), rel=1e-12)

    side_stream_feed = output_value(lower, "side_stream_biomass_feed_rate")
    recovered = output_value(lower, "recovered_biomass_rate")
    returned = output_value(lower, "returned_uncaptured_biomass_rate")
    assert side_stream_feed == pytest.approx(recovered + returned, rel=1e-12)


def test_048_optional_product_price_and_parameter_provenance(client: TestClient) -> None:
    implementation = register(client)
    parameter = client.post(
        "/workspaces/bluerev/parameters",
        json={"name": "Productive liquid volume", "value": "0.019137166941154067", "unit": "m3"},
    )
    assert parameter.status_code == 201

    bindings = baseline(product_price=12.5)
    bindings["productive_liquid_volume"]["source_parameter_id"] = parameter.json()["id"]
    result = run_scenario(client, implementation["id"], bindings, "priced")
    assert result["runner_job"]["status"] == "succeeded"
    assert len(result["output"]["outputs"]) == 40

    expected_margin = output_value(result, "recovered_biomass_rate") * 12.5 - output_value(
        result, "variable_opex_rate"
    )
    assert output_value(result, "gross_margin_proxy") == pytest.approx(expected_margin, rel=1e-12)
    assert output_value(result, "annual_gross_margin_proxy") == pytest.approx(expected_margin * 300.0, rel=1e-12)
    evidence = result["output"]["diagnostics"]["input_evidence"]["productive_liquid_volume"]
    assert evidence["binding_state"] == "parameter"
    assert evidence["source_parameter_id"] == parameter.json()["id"]
    assert evidence["uncertainty_state"] == "not_characterized"


def test_048_event_frequency_changes_per_event_only(client: TestClient) -> None:
    implementation = register(client)
    daily = run_scenario(client, implementation["id"], baseline(), "one-event")
    twice_inputs = baseline()
    twice_inputs["feed_events_per_day"]["value"] = 2.0
    twice = run_scenario(client, implementation["id"], twice_inputs, "two-events")

    assert output_value(twice, "whole_culture_bleed_rate") == pytest.approx(
        output_value(daily, "whole_culture_bleed_rate")
    )
    assert output_value(twice, "whole_culture_bleed_per_event") == pytest.approx(
        output_value(daily, "whole_culture_bleed_per_event") / 2.0
    )
    assert output_value(twice, "nitrogen_stock_volume_per_event") == pytest.approx(
        output_value(daily, "nitrogen_stock_volume_per_event") / 2.0
    )


def test_048_invalid_concentrate_fails_without_successful_output(client: TestClient) -> None:
    implementation = register(client)
    bindings = baseline()
    bindings["concentrate_biomass_concentration"]["value"] = 0.8
    prepared = preview(client, implementation["id"], bindings)
    assert prepared["state"] == "ready"

    created = client.post(
        "/workspaces/bluerev/runner-jobs",
        json={
            "model_version_id": implementation["id"],
            "run_label": "invalid-concentrate",
            "input_set": prepared["normalized_input_set"],
        },
    )
    assert created.status_code == 201
    result = client.post(f"/runner-jobs/{created.json()['runner_job']['id']}/run")
    assert result.status_code == 200
    assert result.json()["runner_job"]["status"] == "failed"
    assert result.json()["output"] is None
    assert client.get("/workspaces/bluerev/parameters").json() == []
