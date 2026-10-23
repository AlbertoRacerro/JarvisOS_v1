"""Spec 214 acceptance 3: rebuild both spec 212 C1 layouts inside the Design shell.

The two tubular layouts become T2 PhotobioreactorT1 units in the Process draft of a
fresh Design project version, then Plant components. Geometry and optics run through
the existing owners from the stored records, and are compared with the spec 212 proxy
run on the same pinned condition. This is the same declared proxy as 212, not a 2013
replication and not a productivity prediction.

Run from backend/ with:
PYTHONPATH=. uv run --no-project --with-requirements requirements.txt \
    python ../scripts/qualification/214/c1_shell_parity.py
(or `.venv/bin/python` with PYTHONPATH=.). Without JARVISOS_DATA_ROOT set, the script
uses a temporary data root and deletes it afterwards.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import runpy
import tempfile
from pathlib import Path
from typing import Any

C1_SCRIPT = Path(__file__).resolve().parents[1] / "212" / "c1_proxy_optics.py"
WALL_T_MM = 2.0  # 50 mm OD - 46 mm ID over two walls; secondary S22 access, as in 212.
OUTPUTS = {"intercepted": ("proxy_intercepted_umol_s_m_per_tube", "umol s^-1 m^-1"),
           "transmitted": ("proxy_transmitted_umol_s_m_per_tube", "umol s^-1 m^-1"),
           "i0_eq": ("proxy_equivalent_par_umol_m2_s", "umol m^-2 s^-1")}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unit_values(case: dict, geometry: dict, condition: dict) -> dict[str, dict]:
    """Typed Process quantities for one 212 layout; tube_count is the loop count, as in 212."""
    return {
        "tube_inner_diameter": {"value": geometry["tube_inner_diameter_m"], "unit": "m"},
        "tube_length": {"value": case["tube_length_m"], "unit": "m"},
        "tube_count": {"value": case["loops"], "unit": "dimensionless"},
        "tubes_across": {"value": case["tubes_across"], "unit": "dimensionless"},
        "layers": {"value": case["layers"], "unit": "dimensionless"},
        "pitch_h": {"value": geometry["pitch_horizontal_m"], "unit": "m"},
        "pitch_v": {"value": geometry["pitch_vertical_m"], "unit": "m"},
        "stagger_offset": {"value": 0.0, "unit": "m"},
        "axis_azimuth": {"value": condition["axis_azimuth_deg"], "unit": "dimensionless"},
        "centre_height_above_sea": {"value": geometry["tube_centre_height_m"], "unit": "m"},
        "n_wall": {"value": condition["n_wall"], "unit": "dimensionless"},
        "n_water": {"value": condition["n_water"], "unit": "dimensionless"},
        "sea_albedo": {"value": condition["ground_albedo"], "unit": "dimensionless"},
    }


def parity() -> dict:
    import numpy as np
    from fastapi.testclient import TestClient
    from pydantic import TypeAdapter

    from app.core.database import initialize_database
    from app.main import app
    from app.modules.process_stack import draft, dynamic_engine, optics_t2
    from app.modules.process_stack.draft_models import DraftOp

    module = runpy.run_path(str(C1_SCRIPT))
    reference = module["exercise"]()
    cases, condition, geometry = module["CASES"], reference["condition"], reference["geometry"]
    sun = (np.array([math.radians(condition["sun_elevation_deg"])]),
           np.array([math.radians(condition["sun_azimuth_deg"])]),
           np.array([condition["dni_par_umol_m2_s"]]), np.array([condition["dhi_par_umol_m2_s"]]))

    initialize_database()
    adapter = TypeAdapter(DraftOp)
    output: dict[str, Any] = {
        "scope": "spec 212 one-condition C1 optical proxy rebuilt in the Design shell; no biomass prediction",
        "reference": {"script": "scripts/qualification/212/c1_proxy_optics.py",
                      "input_digest": reference["input_digest"], "model_version": reference["model_version"]},
        "tolerance": "exact (bitwise float equality) for deterministic source arithmetic and optics",
        "cases": {},
    }
    with TestClient(app) as client:
        project_id = client.post("/workspaces", json={"name": "BlueRev C1", "slug": "bluerev-c1"}).json()["id"]
        versions = f"/workspaces/{project_id}/design-versions"
        created = client.post(versions, json={"label": "C1 shell rebuild", "expected_active_version_id": project_id})
        created.raise_for_status()
        version = created.json()["versions"][1]
        client.post(f"{versions}/activate", json={
            "version_id": version["id"], "expected_active_version_id": project_id}).raise_for_status()
        workspace_id = version["data_workspace_id"]
        plant = draft.create_draft(workspace_id, "C1 tubular layouts")
        ops = []
        for index, (name, case) in enumerate(cases.items()):
            ops += [adapter.validate_python({"op": "add_unit", "id": name, "type": "PhotobioreactorT1",
                                             "tag": f"C1-{name}", "x": 200 * index, "y": 0}),
                    adapter.validate_python({"op": "set_unit_params", "unit": name, "mode": "periodic_steady",
                                             "options": {"optics_model": "t2"},
                                             "values": _unit_values(case, geometry, condition)})]
        revision = draft.patch(workspace_id, plant["draft_id"], plant["revision"], ops)["revision"]
        components = f"{versions}/{version['id']}/components"
        stored = {item["id"]: item for item in draft.projection(workspace_id, plant["draft_id"])["objects"]
                  if item["kind"] == "unit"}

        for name in cases:
            component = client.post(f"{components}/from-unit", json={
                "draft_id": plant["draft_id"], "unit_id": name, "expected_draft_revision": revision,
                "expected_active_version_id": version["id"]})
            component.raise_for_status()
            component_id = component.json()["id"]
            mapping = client.get(f"{components}/{component_id}/geometry/process-mapping").json()
            deepen = client.post(f"{components}/{component_id}/geometry/from-process", json={
                "wall_t_mm": WALL_T_MM, "expected_revision": 1, "expected_active_version_id": version["id"],
                "expected_draft_revision": revision})

            unit = stored[name]
            params = {key: value["si"] for key, value in unit["params"].items()}
            item = {"tag": unit["tag"], "unit": unit, "params": params}
            # Existing Process T2 owner: the dynamic engine's layout mapping (inner diameter as optical diameter).
            process_optics = dynamic_engine.t2_optics_for_unit(item)
            # Spec 212 recorded setup: outer diameter = stored ID + two stated walls; other fields as stored.
            outer = params["tube_inner_diameter"] + 2 * WALL_T_MM / 1000
            recorded_optics = optics_t2.Optics(**{**vars(process_optics), "diameter": outer})
            ref_case = reference["cases"][name]
            runs = {}
            for label, optics in (("recorded_212_setup", recorded_optics), ("process_t2_owner", process_optics)):
                result = optics_t2.array_model(optics).evaluate(*sun)
                values = {key: float(result[key][0]) for key in OUTPUTS}
                runs[label] = {
                    "layout_digest": optics.digest(), "model_version": optics_t2.VERSION,
                    "diameter_m": optics.diameter,
                    "outputs": {OUTPUTS[key][0]: {"value": value, "unit": OUTPUTS[key][1],
                                                  "minus_212": value - ref_case[OUTPUTS[key][0]]}
                                for key, value in values.items()},
                }
            cylinder = math.pi * params["tube_inner_diameter"] ** 2 / 4 * params["tube_count"] * params["tube_length"]
            output["cases"][name] = {
                "component_source": {"draft_revision": revision, "unit": unit["tag"],
                                     "linked": component.json()["source_unit_id"] == name},
                "stored_inputs_digest": _digest({key: unit["params"][key] for key in sorted(unit["params"])}),
                "stored_tube_inner_diameter_m": params["tube_inner_diameter"],
                "stored_tube_length_m": params["tube_length"], "stored_tube_count": params["tube_count"],
                "tube_cylinder_m3": cylinder, "tube_cylinder_minus_212_m3": cylinder - ref_case["tube_cylinder_m3"],
                "geometry": {"mapping": {key: mapping.get(key) for key in
                                         ("supported", "template", "inner_d_mm", "length_mm", "basis")},
                             "deepen_status": deepen.status_code,
                             "deepen_detail": deepen.json().get("detail") if deepen.status_code != 200 else None},
                "reference_layout_digest": ref_case["layout_digest"],
                "layout_digest_matches_212": runs["recorded_212_setup"]["layout_digest"] == ref_case["layout_digest"],
                "runs": runs,
                "productivity_prediction": None,
                "prediction_status": ref_case["prediction_status"],
            }
    output["parity_exact"] = all(
        case["layout_digest_matches_212"] and case["tube_cylinder_minus_212_m3"] == 0
        and all(item["minus_212"] == 0 for item in case["runs"]["recorded_212_setup"]["outputs"].values())
        for case in output["cases"].values())
    return output


if __name__ == "__main__":
    if os.environ.get("JARVISOS_DATA_ROOT"):
        result = parity()
    else:
        with tempfile.TemporaryDirectory(prefix="jarvisos-214-c1-") as root:
            os.environ["JARVISOS_DATA_ROOT"] = root
            result = parity()
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
