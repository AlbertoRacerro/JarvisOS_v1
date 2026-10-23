"""Declare C1 surrogate forcing and culture-temperature cases before running biomass.

Run from the repository root::

    python3 scripts/qualification/215/run_matrix.py

The KNMI air channel is weather evidence only. Dynamic T1 must use its
``unit_mean`` temperature source with the specified PBR unit parameters.
"""

from __future__ import annotations

import json
import runpy
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPERATURE_C = (20.0, 25.0, 30.0)


def build_matrix() -> dict:
    forcing = runpy.run_path(str(HERE / "forcing_windows.py"))["select_windows"]()
    cases = []
    for window_name, window in forcing["selected"].items():
        first_end = datetime.fromisoformat(window["first_end_utc"].replace("Z", "+00:00"))
        last_end = datetime.fromisoformat(window["last_end_utc"].replace("Z", "+00:00"))
        start = first_end - timedelta(hours=1)
        if last_end - start != timedelta(days=36):
            raise ValueError("Selected forcing window is not 36 days")
        for temperature_c in TEMPERATURE_C:
            cases.append({
                "id": f"{window_name}_t{int(temperature_c)}",
                "forcing_window": window_name,
                "start_utc": start.isoformat().replace("+00:00", "Z"),
                "end_utc": last_end.isoformat().replace("+00:00", "Z"),
                "par_dose_mol_m2": window["par_dose_mol_m2"],
                "temperature_source": "unit_mean",
                "pbr_temperature_mean_k": temperature_c + 273.15,
                "pbr_temperature_amplitude_k": 0.0,
                "culture_temperature_state": "assumed constant; S01 reports only maintained 20-30 C",
            })
    return {
        "status": "declared surrogate input scenarios; no biomass prediction",
        "forcing_sha256": forcing["input_sha256"],
        "culture_temperature_source": "S01 reported maintained 20-30 C; 20/25/30 C constants are scenarios, not measurements",
        "air_temperature_role": "surrogate station weather only; never culture temperature",
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(build_matrix(), indent=2, sort_keys=True, allow_nan=False))
