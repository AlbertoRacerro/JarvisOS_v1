from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.modules.process_kernel.profile_047 import execute_047_process_kernel
from app.modules.runner.process_kernel_047 import normalize_input_set

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


def _input(*, velocity: float, include_parameter_reference: bool = True) -> dict[str, dict[str, object]]:
    inner: dict[str, object] = {"value": 30.0, "unit": "mm"}
    if include_parameter_reference:
        inner["source_parameter_id"] = "tube-inner-diameter"
    return {
        "tube_length": {"value": 20.0, "unit": "m"},
        "tube_inner_diameter": inner,
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


def _execute_normalized(input_set: dict[str, dict[str, object]]) -> dict[str, object]:
    normalized = normalize_input_set(input_set)
    values = {name: float(item["value"]) for name, item in normalized.items()}
    return execute_047_process_kernel(values)


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


def test_equivalent_units_match_the_same_075_physical_case() -> None:
    canonical = _input(velocity=0.25, include_parameter_reference=False)
    equivalent = {
        "tube_length": {"value": 2000.0, "unit": "cm"},
        "tube_inner_diameter": {"value": 0.03, "unit": "m"},
        "tube_outer_diameter": {"value": 3.6, "unit": "cm"},
        "reservoir_liquid_volume": {"value": 0.005, "unit": "m3"},
        "target_liquid_velocity": {"value": 25.0, "unit": "cm/s"},
        "liquid_density": {"value": 1.025, "unit": "g/cm3"},
        "dynamic_viscosity": {"value": 1.1, "unit": "mPa*s"},
        "minor_loss_coefficient": {"value": 8.0, "unit": "dimensionless"},
        "pump_efficiency": {"value": 35.0, "unit": "percent"},
    }

    canonical_normalized = normalize_input_set(canonical)
    equivalent_normalized = normalize_input_set(equivalent)
    assert set(canonical_normalized) == set(equivalent_normalized)
    for name in canonical_normalized:
        assert equivalent_normalized[name]["unit"] == canonical_normalized[name]["unit"]
        assert float(equivalent_normalized[name]["value"]) == pytest.approx(
            float(canonical_normalized[name]["value"]),
            rel=1e-15,
            abs=1e-15,
        )

    canonical_result = _execute_normalized(canonical)
    equivalent_result = _execute_normalized(equivalent)
    assert canonical_result["diagnostics"] == equivalent_result["diagnostics"]
    for name, canonical_item in canonical_result["outputs"].items():
        equivalent_item = equivalent_result["outputs"][name]
        assert equivalent_item["unit"] == canonical_item["unit"]
        assert float(equivalent_item["value"]) == pytest.approx(
            float(canonical_item["value"]),
            rel=1e-14,
            abs=1e-15,
        )
