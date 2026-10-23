"""C1 culture-temperature scenarios must not substitute station air for culture."""

from __future__ import annotations

import runpy
from datetime import datetime, timedelta
from pathlib import Path

from app.modules.process_stack.dynamic_models import Scenario

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/qualification/215/run_matrix.py"


def test_run_matrix_pins_36_day_windows_and_unit_mean_temperature() -> None:
    matrix = runpy.run_path(str(SCRIPT))["build_matrix"]()
    assert matrix["forcing_sha256"] == "4e5c40c22639c21b562d4ce017e44bc96646fc8a16dea08c49187ce79264c584"
    assert len(matrix["cases"]) == 9
    assert {case["forcing_window"] for case in matrix["cases"]} == {"low", "median", "high"}
    assert {case["pbr_temperature_mean_k"] for case in matrix["cases"]} == {293.15, 298.15, 303.15}
    assert {case["pbr_temperature_amplitude_k"] for case in matrix["cases"]} == {0.0}
    assert "never culture temperature" in matrix["air_temperature_role"]
    for case in matrix["cases"]:
        start = datetime.fromisoformat(case["start_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(case["end_utc"].replace("Z", "+00:00"))
        assert end - start == timedelta(days=36)
        assert case["temperature_source"] == "unit_mean"
        assert "assumed constant" in case["culture_temperature_state"]
        # The declared source is accepted by the existing dynamic scenario owner.
        scenario = Scenario.model_validate({
            "id": case["id"], "units": ["c1_pbr"],
            "profiles": [{"profile_id": "pinned", "digest": "pinned"}],
            "start_utc": case["start_utc"], "end_utc": case["end_utc"],
            "output_cadence_s": 3600, "temperature_source": case["temperature_source"],
        })
        assert scenario.temperature_source == "unit_mean"
