"""Spec 215 band plan, scenario mapping and pinned band-summary regression."""

from __future__ import annotations

import json
import math
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "scripts/qualification/215"
BAND = runpy.run_path(str(ROOT / "band.py"))
CENTRAL = runpy.run_path(str(ROOT / "central_run.py"))
PINNED = ROOT / "band_results.json"
CENTRAL_SUMMARY = "16cd2450156b2876e67e8e9fd4965b03a42dfecd3a5e4178e9f864881523819f"


def test_plan_is_seeded_and_inside_declared_ranges() -> None:
    plan = BAND["build_plan"]()
    assert plan == BAND["build_plan"]()
    assert [row["kind"] for row in plan].count("central") == 1
    assert [row["kind"] for row in plan].count("monte_carlo") == BAND["MONTE_CARLO_SAMPLES"]
    assert {row["factor"] for row in plan if row["kind"] == "oat"} == set(BAND["FACTORS"])
    for row in plan:
        for name, value in row["draw"].items():
            law = BAND["FACTORS"][name]["law"]
            if law[0] == "choice":
                assert value in law[1]
            else:
                assert law[1] * (1 - 1e-12) <= value <= law[2] * (1 + 1e-12)
            assert 20.0 <= row["draw"].get("culture_temperature_c", 25.0) <= 30.0


def test_volume_basis_maps_reported_illuminated_volume_into_tube_geometry() -> None:
    settings = {**CENTRAL["CENTRAL"], "illuminated_volume_basis": "reported_illuminated_share"}
    window = {"start_utc": "2013-07-01T00:00:00Z", "end_utc": "2013-07-02T00:00:00Z"}
    for name, row in CENTRAL["LAYOUTS"].items():
        case = CENTRAL["_case"](window, name, settings)
        assert case["illuminated_volume_m3"] == pytest.approx(row["working_volume_m3"] * row["illuminated_share"])
        geometric = case["tube_count"] * math.pi * 0.046**2 / 4 * case["tube_length_m"]
        assert geometric == pytest.approx(case["illuminated_volume_m3"])
        assert case["dark_volume_m3"] + case["illuminated_volume_m3"] == pytest.approx(row["working_volume_m3"])
    with pytest.raises(ValueError, match="basis"):
        CENTRAL["_case"](window, "fence", {**settings, "illuminated_volume_basis": "guess"})


def test_alternative_modules_fit_the_physical_loop_count() -> None:
    for name, row in BAND["LAYOUTS"].items():
        for across, layers in row["cross_sections"]:
            assert across * layers <= row["loops"], name


def test_pinned_band_summary_regression() -> None:
    payload = json.loads(PINNED.read_text(encoding="utf-8"))
    assert payload["days"] is None
    plan = BAND["build_plan"]()
    assert [row["id"] for row in payload["results"]] == [row["id"] for row in plan]
    assert [row["draw"] for row in payload["results"]] == json.loads(json.dumps([row["draw"] for row in plan]))
    central = next(row for row in payload["results"] if row["kind"] == "central")
    assert central["summary_sha256"] == CENTRAL_SUMMARY
    summary = BAND["summarize"](payload["results"])
    assert summary["band_sha256"] == payload["summary"]["band_sha256"]
    assert "assumed / not qualified" in summary["status"] and "surrogate" in summary["status"]
    for layout in summary["layouts"].values():
        for metric in layout.values():
            assert metric["p05"] <= metric["median"] <= metric["p95"]
    for row in payload["results"]:
        for layout in row["layouts"].values():
            assert layout["biomass_residual_rel"] < 1e-9
            assert layout["min_pbr_nitrogen_kg_m3"] > 10 * 0.0013554
