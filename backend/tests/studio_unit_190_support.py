"""Shared fixtures for the spec 190 Studio process-unit tests (a nutrient dosing unit with declared generation)."""

from __future__ import annotations

from fastapi.testclient import TestClient

DOSING_CONTRACT = {
    "category": "process_unit", "name": "Nutrient dosing",
    "engineering_question": "How does the dose change the outlet nitrogen?",
    "inlets": [{"name": "culture", "label": "Culture"}, {"name": "dose", "label": "Nutrient dose"}],
    "outlets": [{"name": "outlet", "label": "Dosed culture"}],
    "parameters": [{"name": "dose_split", "label": "Dose split", "unit": "percent",
                    "description": "Share of the dose kept as nitrogen", "min": 0, "max": 100}],
    "culture_generation": ["nitrogen"],
}

PLACEHOLDER = '    raise NotImplementedError("Complete evaluate before testing")'

MIX_BODY = '''    a, b = inlets["culture"], inlets["dose"]
    ma, mb = a["mass_flow_kg_s"], b["mass_flow_kg_s"]
    m = ma + mb
    names = set(a["mass_fractions"]) | set(b["mass_fractions"])
    fractions = {n: (ma * a["mass_fractions"].get(n, 0.0) + mb * b["mass_fractions"].get(n, 0.0)) / m for n in names}
    generated = params["dose_split"] / 100.0 * 1e-6
    culture = {}
    for field in ("biomass", "nitrogen"):
        amount = ma * (a["culture"].get(field) or 0.0) + mb * (b["culture"].get(field) or 0.0)
        culture[field] = (amount + (generated if field == "nitrogen" else 0.0)) / m
    outlet = {"mass_flow_kg_s": m, "temperature_K": (ma * a["temperature_K"] + mb * b["temperature_K"]) / m,
              "pressure_Pa": min(a["pressure_Pa"], b["pressure_Pa"]), "mass_fractions": fractions, "culture": culture}
    return {"outlets": {"outlet": outlet}, "culture_generation": {"nitrogen": generated}}'''


def stream(flow: float = 1.0, *, nitrogen: float = 0.001, biomass: float = 0.0, temperature: float = 300.0) -> dict:
    return {"mass_flow_kg_s": flow, "temperature_K": temperature, "pressure_Pa": 200000.0,
            "mass_fractions": {"Water": 1.0}, "culture": {"biomass": biomass, "nitrogen": nitrogen}}


def unit_case(**extra) -> dict:
    return {"inlets": {"culture": stream(1.0, biomass=0.5), "dose": stream(0.5, nitrogen=0.02, temperature=290.0)},
            "params": {"dose_split": 50.0}, **extra}


def publish_unit(client: TestClient, body: str = MIX_BODY, contract: dict | None = None) -> tuple[str, str]:
    """Create, edit, test and publish a unit; returns (model id, version id)."""
    created = client.post("/workspaces/bluerev/studio/models", json=contract or DOSING_CONTRACT)
    assert created.status_code == 201, created.text
    model = created.json()
    path = f"/workspaces/bluerev/studio/models/{model['id']}"
    assert client.put(path, json={"source": model["source"].replace(PLACEHOLDER, body)}).status_code == 200
    report = client.post(path + "/test", json={"cases": [unit_case()]})
    assert report.status_code == 200 and report.json()["passed"], report.text
    published = client.post(path + "/publish")
    assert published.status_code == 200, published.text
    return model["id"], published.json()["id"]
