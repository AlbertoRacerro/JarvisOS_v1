from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from app.core.bootstrap import initialize_storage
from app.core.paths import build_paths
from app.modules.bluecad.export import sha256_file
from app.modules.bluecad.ledger import ScriptedFakeBluecadAdapter, candidate_work_dir
from app.modules.bluecad.loop import create_bluecad_candidate
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadLoopConfig
from app.modules.bluecad.registry import ToolRegistryError, check_registry, resolve_registry_path, resolve_tool
from tests.bluecad.alpha_real_tools_support import analysis_spec, assert_full_chain, offline_bindings

FIXTURES = Path(__file__).parent / "fixtures"
_DIAGNOSTIC_SUFFIXES = {".inp", ".log", ".frd", ".dat", ".sta", ".cvg", ".geo", ".msh"}
_MAX_DIAGNOSTIC_FILE_BYTES = 2 * 1024 * 1024


def _handle_unavailable(*, strict: bool, reason: str) -> None:
    if strict:
        pytest.fail(f"strict BLUECAD real-tool proof unavailable: {reason}")
    pytest.skip(f"BLUECAD real-tool proof unavailable: {reason}")


def _require_toolchain(request: pytest.FixtureRequest) -> tuple[dict[str, Any], dict[str, Any], str]:
    strict = bool(request.config.getoption("--require-bluecad-real-tools"))
    if importlib.util.find_spec("build123d") is None:
        _handle_unavailable(strict=strict, reason="build123d is not installed")
    try:
        registry_path = resolve_registry_path()
        gmsh = resolve_tool("gmsh", registry_path)
        calculix = resolve_tool("calculix", registry_path)
        exit_code, output = check_registry(registry_path)
    except (ToolRegistryError, OSError) as exc:
        _handle_unavailable(strict=strict, reason=str(exc))
    if exit_code != 0:
        _handle_unavailable(strict=strict, reason=output)
    for entry in (gmsh, calculix):
        if str(entry["version_pin"]).lower().startswith("fake"):
            _handle_unavailable(strict=strict, reason=f"{entry['id']} uses a fake version pin")
    return gmsh, calculix, output


def _preserve_text_diagnostics(candidates: list[Any]) -> None:
    configured = os.getenv("JARVISOS_BLUECAD_PROOF_DEBUG_DIR")
    if not configured:
        return
    destination_root = Path(configured)
    destination_root.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        source_root = candidate_work_dir("bluerev", candidate.id, 1) / "simulation"
        destination = destination_root / candidate.id
        for source in source_root.rglob("*"):
            if not source.is_file() or source.suffix.lower() not in _DIAGNOSTIC_SUFFIXES:
                continue
            if source.stat().st_size > _MAX_DIAGNOSTIC_FILE_BYTES:
                continue
            target = destination / source.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _create_candidate(adapter: ScriptedFakeBluecadAdapter, *, quadratic: bool) -> Any:
    payload = BluecadCandidateCreate(
        brief_text="deterministic single tube real-tool alpha proof",
        loop_config=BluecadLoopConfig(
            max_attempts_per_tier=1,
            tier_ladder=["external:cheap"],
            analysis_spec=analysis_spec(element_order=2 if quadratic else None),
        ),
    )
    return create_bluecad_candidate(
        "bluerev",
        payload,
        adapters={"scaleway": adapter},
        bindings=offline_bindings(),
        force_external_allowed=True,
    )


def test_ordinary_mode_skips_unavailable_real_tools() -> None:
    with pytest.raises(pytest.skip.Exception):
        _handle_unavailable(strict=False, reason="missing")


def test_strict_mode_fails_unavailable_real_tools() -> None:
    with pytest.raises(pytest.fail.Exception):
        _handle_unavailable(strict=True, reason="missing")


@pytest.mark.bluecad_kernel
@pytest.mark.bluecad_gmsh
@pytest.mark.bluecad_ccx
def test_strict_real_tool_full_chain_twice(request: pytest.FixtureRequest) -> None:
    gmsh, calculix, registry_output = _require_toolchain(request)
    initialize_storage(seed_default=True)
    fixture_text = (FIXTURES / "minimal_single_tube.json").read_text(encoding="utf-8")
    adapter = ScriptedFakeBluecadAdapter([fixture_text, fixture_text])

    candidates = [_create_candidate(adapter, quadratic=False) for _ in range(2)]
    _preserve_text_diagnostics(candidates)
    assert len(adapter.prompts) == 2
    manifests = [assert_full_chain(candidate) for candidate in candidates]
    assert manifests[0].read_bytes() == manifests[1].read_bytes()
    assert sha256_file(manifests[0]) == sha256_file(manifests[1])

    proof = {
        "schema_version": "bluecad_alpha_real_tool_proof_v0_1",
        "registry_path": str(resolve_registry_path()),
        "registry_check": registry_output,
        "tools": {
            "gmsh": {key: gmsh[key] for key in ("entrypoint", "version_pin", "binary_sha256")},
            "calculix": {key: calculix[key] for key in ("entrypoint", "version_pin", "binary_sha256")},
        },
        "candidate_ids": [candidate.id for candidate in candidates],
        "manifest_sha256": sha256_file(manifests[0]),
        "provider_mode": "caller-injected-offline-scripted-adapter",
    }
    proof_path = Path(
        os.getenv("JARVISOS_BLUECAD_PROOF_JSON", str(build_paths().data_root / "bluecad-alpha-proof.json"))
    )
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@pytest.mark.bluecad_kernel
@pytest.mark.bluecad_gmsh
@pytest.mark.bluecad_ccx
def test_strict_real_tool_quadratic_mesh_and_solve(request: pytest.FixtureRequest) -> None:
    _require_toolchain(request)
    initialize_storage(seed_default=True)
    fixture_text = (FIXTURES / "minimal_single_tube.json").read_text(encoding="utf-8")
    adapter = ScriptedFakeBluecadAdapter([fixture_text])

    candidate = _create_candidate(adapter, quadratic=True)
    _preserve_text_diagnostics([candidate])
    assert len(adapter.prompts) == 1
    assert_full_chain(candidate, expected_volume_element_type="C3D10")
