"""Pinned surrogate weather evidence for the C1 prediction (spec 215)."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pvlib

from app.core.database import initialize_database
from app.modules.environment import profiles
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "scripts/qualification/215/knmi_2013_deelen_surrogate.csv"
SHA256 = "4e5c40c22639c21b562d4ce017e44bc96646fc8a16dea08c49187ce79264c584"


def test_surrogate_is_pinned_hourly_and_energy_closes() -> None:
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == SHA256
    with DATA.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 62 * 24
    stamps = pd.to_datetime([row["time_end_utc"] for row in rows], utc=True)
    assert stamps[0] == datetime(2013, 7, 1, 1, tzinfo=UTC)
    assert stamps[-1] == datetime(2013, 9, 1, tzinfo=UTC)
    assert (stamps[1:] - stamps[:-1] == pd.Timedelta(hours=1)).all()
    values = {key: [float(row[key]) for row in rows] for key in rows[0] if key != "time_end_utc"}
    assert all(math.isfinite(value) for column in values.values() for value in column)
    assert min(values["ghi_w_m2"]) >= 0
    assert min(values["dni_w_m2"]) >= 0
    assert min(values["dhi_w_m2"]) >= 0
    midpoint = stamps - pd.Timedelta(minutes=30)
    zenith = pvlib.solarposition.get_solarposition(
        midpoint, 52.056, 5.873, altitude=48.20
    )["zenith"].to_numpy()
    assert min(zenith) < 35  # summer noon at this latitude
    for ghi, dni, dhi, par, stamp in zip(
        values["ghi_w_m2"], values["dni_w_m2"], values["dhi_w_m2"],
        values["par_umol_m2_s"], stamps, strict=True,
    ):
        assert math.isclose(par, ghi * 0.45 * 4.57, rel_tol=1e-8, abs_tol=1e-7)
        # Midpoint solar zenith is needed because KNMI stamps are interval ends.
        if stamp.hour in {0, 1, 2, 3}:
            assert dni == 0
            assert dhi == ghi
    for ghi, dni, dhi, angle in zip(values["ghi_w_m2"], values["dni_w_m2"],
                                   values["dhi_w_m2"], zenith, strict=True):
        assert math.isclose(ghi, dhi + dni * max(0.0, math.cos(math.radians(angle))), abs_tol=1e-6)


def test_declared_36_day_forcing_windows() -> None:
    script = ROOT / "scripts/qualification/215/forcing_windows.py"
    result = runpy.run_path(str(script))["select_windows"]()
    assert result["input_sha256"] == SHA256
    assert result["window_hours"] == 36 * 24
    assert result["candidate_windows"] == 27
    assert "observation dates unknown" in result["status"]
    selected = result["selected"]
    assert selected["low"]["first_end_utc"] == "2013-07-26T01:00:00Z"
    assert selected["median"]["first_end_utc"] == "2013-07-14T01:00:00Z"
    assert selected["high"]["first_end_utc"] == "2013-07-06T01:00:00Z"
    assert [selected[name]["par_dose_mol_m2"] for name in ("low", "median", "high")] == [
        1173.4389, 1303.73874, 1431.838125,
    ]


def test_surrogate_imports_through_environment_profile_owner() -> None:
    initialize_database()
    wid = create_workspace(WorkspaceCreate(name="C1 surrogate", slug="c1-surrogate-test")).id
    mapping = json.loads((DATA.parent / "environment_mapping.json").read_text(encoding="utf-8"))
    imported = profiles.confirm_csv(wid, DATA, DATA.name, mapping)
    record = profiles.read_profile(wid, imported["digest"], limit=62 * 24)
    assert record["provenance"]["original_sha256"] == SHA256
    assert record["provenance"]["column_mapping"] == mapping
    assert record["resolution_minutes"] == 60
    assert record["timestamps"][0] == "2013-07-01T01:00:00Z"
    assert record["timestamps"][-1] == "2013-09-01T00:00:00Z"
    assert len(record["timestamps"]) == 62 * 24
    assert record["units"] == {
        "ghi": "W m-2", "dni": "W m-2", "dhi": "W m-2",
        "par": "umol m-2 s-1", "air_temperature": "K",
    }
    assert record["channels"]["air_temperature"][0] == 14.3 + 273.15
    assert record["channels"]["par"] != record["channels"]["ghi"]
