from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.modules.process_kernel.profile_047 import execute_047_process_kernel

LEGACY_047_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "runner"
    / "examples"
    / "bluerev_geometry_hydraulics_v0.py"
)


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _input(*, velocity: float) -> dict[str, dict[str, object]]:
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": {
            "value": 30.0,
            "unit": "mm",
            "source_parameter_id": "tube-inner-diameter",
        },
        "tube_outer_diameter": {"value": 36.0, "unit": "mm"},
        "reservoir_liquid_volume": {"value": 5.0, "unit": "L"},
        "target_liquid_velocity": {"value": velocity, "unit": "m/s"},
        "liquid_density": {"value": 1025.0, "unit": "kg/m3"},
        "dynamic_viscosity": {"value": 0.0011, "unit": "Pa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "1"},
        "pump_efficiency": {"value": 0.35, "unit": "1"},
    }


def _run_legacy(tmp_path: Path, input_set: dict[str, dict[str, object]]) -> tuple[dict[str, object], bytes]:
    (tmp_path / "input.json").write_bytes(_canonical_bytes(input_set))
    completed = subprocess.run(
        [sys.executable, str(LEGACY_047_SCRIPT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    raw = (tmp_path / "result.json").read_bytes()
    return json.loads(raw), raw


@pytest.mark.parametrize(
    ("velocity", "expected_correlation"),
    [
        (0.25, "blasius_smooth_pipe_v0"),
        (0.05, "laminar_64_over_Re"),
    ],
)
def test_process_kernel_matches_canonical_047_bytes_and_float_hex(
    tmp_path: Path,
    velocity: float,
    expected_correlation: str,
) -> None:
    input_set = _input(velocity=velocity)
    legacy, legacy_bytes = _run_legacy(tmp_path, input_set)
    values = {name: float(item["value"]) for name, item in input_set.items()}
    kernel = execute_047_process_kernel(values)
    kernel_bytes = _canonical_bytes(kernel)

    assert kernel["schema_version"] == legacy["schema_version"] == 1
    assert kernel["status"] == legacy["status"] == "succeeded"
    assert kernel["diagnostics"] == legacy["diagnostics"]
    assert kernel["diagnostics"]["friction_correlation"] == expected_correlation
    assert set(kernel["outputs"]) == set(legacy["outputs"])

    for name in legacy["outputs"]:
        legacy_item = legacy["outputs"][name]
        kernel_item = kernel["outputs"][name]
        assert kernel_item["unit"] == legacy_item["unit"]
        assert float(kernel_item["value"]).hex() == float(legacy_item["value"]).hex()

    assert kernel_bytes == legacy_bytes
    assert hashlib.sha256(kernel_bytes).hexdigest() == hashlib.sha256(legacy_bytes).hexdigest()
