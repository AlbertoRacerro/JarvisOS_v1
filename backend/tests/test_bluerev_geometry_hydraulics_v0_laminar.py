import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "runner"
    / "examples"
    / "bluerev_geometry_hydraulics_v0.py"
)


def test_qualified_laminar_case_uses_darcy_64_over_re(tmp_path: Path) -> None:
    inputs = {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {"value": 30.0, "unit": "mm"},
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": 0.05, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }
    (tmp_path / "input.json").write_text(
        json.dumps(inputs, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    reynolds = output["outputs"]["reynolds_number"]["value"]
    friction = output["outputs"]["darcy_friction_factor"]["value"]
    assert reynolds < 2300.0
    assert friction == pytest.approx(64.0 / reynolds, rel=1e-15)
    assert output["diagnostics"]["friction_factor_convention"] == "Darcy"
    assert output["diagnostics"]["friction_correlation"] == "laminar_64_over_Re"
