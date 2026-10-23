"""Select declared 36-day surrogate windows without claiming C1 campaign dates.

Run from the repository root::

    python3 scripts/qualification/215/forcing_windows.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

INPUT = Path(__file__).with_name("knmi_2013_deelen_surrogate.csv")
DAYS = 36
HOURS = DAYS * 24
EXPECTED_SHA256 = "4e5c40c22639c21b562d4ce017e44bc96646fc8a16dea08c49187ce79264c584"


def select_windows(path: Path = INPUT) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Surrogate forcing digest changed")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 62 * 24:
        raise ValueError("Expected complete July–August hourly surrogate")
    ends = [datetime.fromisoformat(row["time_end_utc"].replace("Z", "+00:00")) for row in rows]
    if any(right - left != timedelta(hours=1) for left, right in zip(ends, ends[1:], strict=False)):
        raise ValueError("Surrogate hours are not contiguous")
    par = [float(row["par_umol_m2_s"]) for row in rows]
    windows = []
    for day in range(62 - DAYS + 1):
        start = day * 24
        stop = start + HOURS
        # Hourly PAR integrated to mol photons per square metre over 36 days.
        dose = sum(par[start:stop]) * 3600 / 1_000_000
        windows.append({"first_end_utc": ends[start].isoformat().replace("+00:00", "Z"),
                        "last_end_utc": ends[stop - 1].isoformat().replace("+00:00", "Z"),
                        "par_dose_mol_m2": round(dose, 6)})
    ordered = sorted(windows, key=lambda item: (item["par_dose_mol_m2"], item["first_end_utc"]))
    return {"status": "surrogate forcing scenarios; C1 observation dates unknown",
            "input_sha256": digest, "window_hours": HOURS, "candidate_windows": len(windows),
            "selected": {"low": ordered[0], "median": ordered[len(ordered) // 2], "high": ordered[-1]}}


if __name__ == "__main__":
    print(json.dumps(select_windows(), indent=2, sort_keys=True))
