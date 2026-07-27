from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.modules.process_kernel.blocks import Pipe
from app.modules.process_kernel.components import SCREENING_MASS_CONSTANTS_V0
from app.modules.process_kernel.streams import MaterialStream
from app.modules.runner.process_kernel_047 import (
    PROCESS_PACKAGE_FILENAMES,
    bundle_source_entries,
    install_registered_bundle,
    validate_registered_bundle,
)
from app.modules.runner.safety import RunnerSafetyError


def _pipe_parameters(*, length: float, inner_mm: float, outer_mm: float, velocity: float) -> dict[str, float]:
    return {
        "tube_length": length,
        "tube_inner_diameter": inner_mm,
        "tube_outer_diameter": outer_mm,
        "target_liquid_velocity": velocity,
    }


def test_two_pipe_instances_are_independent_and_parameterized() -> None:
    stream = MaterialStream(
        id="loop_liquid",
        density_kg_m3=1000.0,
        dynamic_viscosity_Pa_s=0.001,
    )
    pipe_a = Pipe(block_id="pipe_a")
    pipe_b = Pipe(block_id="pipe_b")

    result_a = pipe_a.solve(
        {"inlet": stream},
        {},
        _pipe_parameters(length=20.0, inner_mm=50.0, outer_mm=60.0, velocity=1.0),
        {},
    )
    result_b = pipe_b.solve(
        {"inlet": stream},
        {},
        _pipe_parameters(length=40.0, inner_mm=80.0, outer_mm=90.0, velocity=0.75),
        {},
    )

    assert pipe_a.block_id == "pipe_a"
    assert pipe_b.block_id == "pipe_b"
    assert result_a.scalar_outputs["tube_volume"] != result_b.scalar_outputs["tube_volume"]
    assert result_a.scalar_outputs["circulation_flow"] != result_b.scalar_outputs["circulation_flow"]
    assert result_a.material_outputs["outlet"] is not stream
    assert result_b.material_outputs["outlet"] is not stream
    assert stream.volumetric_flow_m3_s is None
    assert result_a.material_outputs["outlet"].volumetric_flow_m3_s == pytest.approx(
        math.pi * 0.05**2 / 4.0
    )
    assert result_b.material_outputs["outlet"].volumetric_flow_m3_s == pytest.approx(
        0.75 * math.pi * 0.08**2 / 4.0
    )


def test_048_screening_ratio_is_derived_from_explicit_compatibility_constants() -> None:
    constants = SCREENING_MASS_CONSTANTS_V0
    reconstructed_co2 = constants.carbon_g_per_mol + 2.0 * constants.oxygen_g_per_mol

    assert constants.carbon_g_per_mol == 12.0
    assert constants.oxygen_g_per_mol == 16.0
    assert constants.carbon_dioxide_g_per_mol == 44.0
    assert reconstructed_co2 == constants.carbon_dioxide_g_per_mol
    assert constants.carbon_dioxide_to_carbon_ratio == reconstructed_co2 / constants.carbon_g_per_mol
    assert constants.authority == "merged 048 rounded screening constants"


def test_process_kernel_bundle_uses_a_closed_explicit_file_set() -> None:
    expected_targets = {
        *(f"process_kernel/{filename}" for filename in PROCESS_PACKAGE_FILENAMES),
        "process_kernel/topology.py",
    }
    entries = bundle_source_entries()

    assert {target for _, target in entries} == expected_targets
    assert len(entries) == len(expected_targets)
    assert all(source.is_file() for source, _ in entries)


def test_registered_bundle_rejects_missing_modified_and_extra_entries(tmp_path: Path) -> None:
    target_dir = tmp_path / "registered"
    target_dir.mkdir()
    install_registered_bundle(target_dir)
    digest = validate_registered_bundle(target_dir)
    assert len(digest) == 64

    modified = target_dir / "process_kernel" / "blocks.py"
    original = modified.read_bytes()
    modified.write_bytes(original + b"\n# modified\n")
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_registered_bundle(target_dir)
    assert exc_info.value.code == "runner_process_kernel_bundle_hash_mismatch"
    modified.write_bytes(original)

    missing = target_dir / "process_kernel" / "errors.py"
    missing_bytes = missing.read_bytes()
    missing.unlink()
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_registered_bundle(target_dir)
    assert exc_info.value.code == "runner_process_kernel_bundle_files_invalid"
    missing.write_bytes(missing_bytes)

    extra_file = target_dir / "process_kernel" / "unexpected.txt"
    extra_file.write_text("unexpected", encoding="utf-8")
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_registered_bundle(target_dir)
    assert exc_info.value.code == "runner_process_kernel_bundle_files_invalid"
    extra_file.unlink()

    extra_directory = target_dir / "process_kernel" / "unexpected"
    extra_directory.mkdir()
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_registered_bundle(target_dir)
    assert exc_info.value.code == "runner_process_kernel_bundle_files_invalid"
