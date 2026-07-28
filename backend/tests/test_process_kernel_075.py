from __future__ import annotations

import math
import shutil
from pathlib import Path

import pytest

from app.modules.process_kernel.blocks import Pipe
from app.modules.process_kernel.components import SCREENING_MASS_CONSTANTS_V0
from app.modules.process_kernel.streams import MaterialStream
from app.modules.runner.process_kernel_047 import (
    BUNDLE_MANIFEST_FILENAME,
    PROCESS_PACKAGE_FILENAMES,
    REGISTERED_ENTRYPOINT_FILENAME,
    bundle_source_entries,
    bundled_script_path,
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


def _installed_bundle(tmp_path: Path, name: str) -> Path:
    target_dir = tmp_path / name
    target_dir.mkdir()
    shutil.copy2(bundled_script_path(), target_dir / REGISTERED_ENTRYPOINT_FILENAME)
    install_registered_bundle(target_dir)
    assert len(validate_registered_bundle(target_dir)) == 64
    return target_dir


def _assert_bundle_error(target_dir: Path, code: str) -> None:
    with pytest.raises(RunnerSafetyError) as exc_info:
        validate_registered_bundle(target_dir)
    assert exc_info.value.code == code


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
    assert result_a.material_outputs["outlet"] is not result_b.material_outputs["outlet"]
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
        f"process_kernel/{filename}" for filename in PROCESS_PACKAGE_FILENAMES
    } | {"process_kernel/topology.py"}
    entries = bundle_source_entries()

    assert {target for _, target in entries} == expected_targets
    assert len(entries) == len(expected_targets)
    assert all(source.is_file() for source, _ in entries)


def test_registered_bundle_rejects_modified_file(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "modified")
    target = target_dir / "process_kernel" / "blocks.py"
    target.write_bytes(target.read_bytes() + b"\n# modified\n")
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_hash_mismatch")


def test_registered_bundle_rejects_missing_file(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "missing")
    (target_dir / "process_kernel" / "errors.py").unlink()
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


@pytest.mark.parametrize("filename", ["unexpected.py", "unexpected.txt"])
def test_registered_bundle_rejects_extra_file(tmp_path: Path, filename: str) -> None:
    target_dir = _installed_bundle(tmp_path, filename.replace(".", "-"))
    (target_dir / "process_kernel" / filename).write_text("unexpected", encoding="utf-8")
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


def test_registered_bundle_rejects_extra_directory(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "extra-directory")
    (target_dir / "process_kernel" / "unexpected").mkdir()
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


def test_registered_bundle_rejects_symlink_entry(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "symlink")
    target = target_dir / "outside.py"
    target.write_text("outside", encoding="utf-8")
    (target_dir / "process_kernel" / "unexpected.py").symlink_to(target)
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


def test_registered_bundle_rejects_stale_manifest(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "stale-manifest")
    manifest = target_dir / BUNDLE_MANIFEST_FILENAME
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_hash_mismatch")


@pytest.mark.parametrize("filename", ["json.py", "sitecustomize.py", "unexpected.txt"])
def test_registered_bundle_rejects_top_level_sibling_file(tmp_path: Path, filename: str) -> None:
    target_dir = _installed_bundle(tmp_path, f"top-level-{filename.replace('.', '-')}")
    (target_dir / filename).write_text("raise RuntimeError('must never import')", encoding="utf-8")
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


def test_registered_bundle_rejects_top_level_directory(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "top-level-directory")
    (target_dir / "unexpected").mkdir()
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_files_invalid")


def test_registered_bundle_rejects_modified_registered_entrypoint(tmp_path: Path) -> None:
    target_dir = _installed_bundle(tmp_path, "modified-entrypoint")
    entrypoint = target_dir / REGISTERED_ENTRYPOINT_FILENAME
    entrypoint.write_bytes(entrypoint.read_bytes() + b"\n# modified\n")
    _assert_bundle_error(target_dir, "runner_process_kernel_bundle_hash_mismatch")
