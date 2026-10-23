"""C1 scenario custody and the two unresolved S01 denominator residuals."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/qualification/215/scenario_inputs.py"


def test_declared_scenarios_preserve_source_residuals() -> None:
    spec = importlib.util.spec_from_file_location("c1_scenario_inputs", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.build_inputs()

    assert result["input_sha256"] == "3aa0b29b0b735c22ae555f3571b3a8f7eed0b805a2fd4aac078dd5e1d02dd8d5"
    assert "no biomass prediction" in result["status"]
    assert len(result["scenarios"]) == 24
    identities = {
        (item["layout"], item["tubes_across"], item["layers"],
         item["axis_azimuth_deg"], item["illuminated_volume_basis"])
        for item in result["scenarios"]
    }
    assert len(identities) == 24
    for layout in ("horizontal", "fence"):
        row = result["layouts"][layout]
        assert row["observed_mass_residual_g_day"] == pytest.approx(
            row["observed_volumetric_implied_g_day"] - row["observed_areal_implied_g_day"]
        )
        assert row["tube_minus_reported_illuminated_m3"] == pytest.approx(
            row["tube_cylinder_volume_m3"] - row["reported_illuminated_volume_m3"]
        )
    assert result["layouts"]["horizontal"]["observed_mass_residual_g_day"] == pytest.approx(37.3)
    assert result["layouts"]["fence"]["tube_minus_reported_illuminated_m3"] == pytest.approx(0.1780654)
    assert all(item["cross_section_state"].startswith("assumed") for item in result["scenarios"])
