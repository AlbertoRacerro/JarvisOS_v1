"""Build the pinned July–August 2013 C1 *surrogate* forcing CSV.

Run from the repository root with the archived KNMI file passed explicitly::

    backend/.venv/bin/python scripts/qualification/215/knmi_surrogate.py \
      /path/to/knmi_2013_hourly_275_260.txt \
      scripts/qualification/215/knmi_2013_deelen_surrogate.csv

The CSV has end-of-hour UTC stamps and can be mapped through the existing
environment CSV importer. It is weather at Deelen, not AlgaePARC measurements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

SOURCE_SHA256 = "e70bb6199912e3e19af9173a1e9a5761ea2b4c3a5f385b1c78028f96a6f452c0"
STATION = 275  # Deelen Airport: 52.056 N, 5.873 E, 48.20 m (KNMI header).
LATITUDE, LONGITUDE, ALTITUDE_M = 52.056, 5.873, 48.20
FIRST_END = datetime(2013, 7, 1, 1, tzinfo=UTC)
LAST_END = datetime(2013, 9, 1, 0, tzinfo=UTC)
# Spec 171's explicit screening convention: 45% of broadband W and 4.57 umol/J of PAR.
PAR_UMOL_PER_BROADBAND_J = 0.45 * 4.57
HEADER = ("time_end_utc", "ghi_w_m2", "dni_w_m2", "dhi_w_m2",
          "par_umol_m2_s", "air_temperature_c")


def read_knmi(path: Path) -> tuple[list[datetime], np.ndarray, np.ndarray]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"KNMI archive SHA-256 mismatch: {digest}")
    selected: dict[datetime, tuple[float, float]] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#") or not line.strip():
                continue
            station, date, hour, q, temperature, *_ = (part.strip() for part in line.split(","))
            if int(station) != STATION:
                continue
            end = datetime.strptime(date, "%Y%m%d").replace(tzinfo=UTC) + timedelta(hours=int(hour))
            if FIRST_END <= end <= LAST_END:
                if end in selected:
                    raise ValueError(f"Duplicate KNMI hour: {end}")
                if q == "" or temperature == "":
                    raise ValueError(f"Missing KNMI Q/T at {end}")
                # Q is J/cm2 accumulated over the preceding hour; T is 0.1 C.
                selected[end] = (float(q) * 10_000 / 3_600, float(temperature) / 10)
    expected = pd.date_range(FIRST_END, LAST_END, freq="h")
    if set(selected) != set(expected.to_pydatetime()):
        raise ValueError("KNMI July–August Deelen hourly coverage is incomplete")
    ends = list(expected.to_pydatetime())
    ghi, air = (np.asarray([selected[t][i] for t in ends], dtype=float) for i in (0, 1))
    if not np.isfinite(ghi).all() or (ghi < 0).any() or not np.isfinite(air).all():
        raise ValueError("Invalid KNMI irradiance or temperature")
    return ends, ghi, air


def decompose(ends: list[datetime], ghi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # KNMI HH labels the *end* of the interval. Use interval midpoint for SPA
    # solar position and Erbs hourly GHI decomposition; retain end stamps in CSV.
    midpoints = pd.DatetimeIndex(ends) - pd.Timedelta(minutes=30)
    sun = pvlib.solarposition.get_solarposition(
        midpoints, LATITUDE, LONGITUDE, altitude=ALTITUDE_M
    )
    split = pvlib.irradiance.erbs(ghi, sun["zenith"].to_numpy(), midpoints)
    dni = np.asarray(split["dni"], dtype=float)
    dhi = np.asarray(split["dhi"], dtype=float)
    if not np.isfinite(dni).all() or not np.isfinite(dhi).all() or (dni < 0).any() or (dhi < 0).any():
        raise ValueError("Erbs returned invalid direct/diffuse irradiance")
    cos_zenith = np.maximum(0, np.cos(np.deg2rad(sun["zenith"].to_numpy())))
    if not np.allclose(ghi, dhi + dni * cos_zenith, atol=1e-6):
        raise ValueError("Erbs decomposition does not close measured GHI")
    return dni, dhi


def build(source: Path, output: Path) -> None:
    ends, ghi, air = read_knmi(source)
    dni, dhi = decompose(ends, ghi)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(HEADER)
        for end, g, direct, diffuse, temperature in zip(ends, ghi, dni, dhi, air, strict=True):
            writer.writerow((end.isoformat().replace("+00:00", "Z"),
                             *(format(value, ".10g") for value in
                               (g, direct, diffuse, g * PAR_UMOL_PER_BROADBAND_J, temperature))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
