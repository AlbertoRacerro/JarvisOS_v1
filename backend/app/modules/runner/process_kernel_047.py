from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.modules.process_kernel.components import (
    component_catalog_sha256,
    screening_mass_constants_sha256,
)
from app.modules.process_kernel.profile_047 import (
    assembler_contract_sha256,
    flowsheet_profile_sha256,
    profile_constants_sha256,
)
from app.modules.process_kernel.units import semantic_registry_sha256
from app.modules.runner.input_contracts import (
    ModelInputContractV2,
    build_binding_preview,
    canonicalize_input_contract,
    normalize_input_set_v2,
    parse_stored_input_contract,
)
from app.modules.runner.models import BindingPreviewResponse
from app.modules.runner.safety import (
    ALLOWED_CALC_V0_PROCESS_KERNEL_IMPORT_ROOTS,
    RunnerSafetyError,
    canonical_json,
    sha256_file,
)

MODEL_LABEL = "bluerev-geometry-hydraulics-process-kernel-v1.0.0"
MODEL_TITLE = "BlueRev geometry and hydraulics process kernel V1"
PROFILE_ID = "bluerev_geometry_hydraulics_process_kernel_v1"
CONTRACT_VERSION = "bluerev_geometry_hydraulics_process_kernel_contract_v2"
AST_POLICY_ID = "calc_v0_process_kernel_v1"
ALLOWED_IMPORT_ROOTS = tuple(sorted(ALLOWED_CALC_V0_PROCESS_KERNEL_IMPORT_ROOTS))
REGISTERED_ENTRYPOINT_FILENAME = "calc_v0.py"
BUNDLE_MANIFEST_FILENAME = "process_kernel_bundle_manifest.json"
PROCESS_PACKAGE_FILENAMES = (
    "__init__.py",
    "blocks.py",
    "canonical.py",
    "components.py",
    "contracts.py",
    "errors.py",
    "flowsheet.py",
    "profile_047.py",
    "streams.py",
    "units.py",
)

ParameterLoader = Callable[[str], dict[str, object] | None]


def backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def bundled_script_path() -> Path:
    return Path(__file__).resolve().parent / "examples" / "bluerev_geometry_hydraulics_process_kernel_v1.py"


def bundled_contract_path() -> Path:
    return (
        Path(__file__).resolve().parent
        / "examples"
        / "bluerev_geometry_hydraulics_process_kernel_v1.contract.json"
    )


def process_package_source_root() -> Path:
    return Path(__file__).resolve().parents[1] / "process_kernel"


def core_topology_source_path() -> Path:
    return Path(__file__).resolve().parents[2] / "core" / "topology.py"


def expected_contract() -> dict[str, Any]:
    raw = json.loads(bundled_contract_path().read_text(encoding="utf-8"))
    _, _, normalized = canonicalize_input_contract(raw)
    return normalized


def expected_contract_sha256() -> str:
    raw = json.loads(bundled_contract_path().read_text(encoding="utf-8"))
    _, digest, _ = canonicalize_input_contract(raw)
    return digest


def bundle_source_entries() -> tuple[tuple[Path, str], ...]:
    source_root = process_package_source_root()
    package_entries = tuple(
        (source_root / filename, f"process_kernel/{filename}")
        for filename in PROCESS_PACKAGE_FILENAMES
    )
    return package_entries + ((core_topology_source_path(), "process_kernel/topology.py"),)


def expected_bundle_manifest() -> dict[str, object]:
    files = [
        {
            "target_path": target_path,
            "source_path": source.relative_to(backend_root()).as_posix(),
            "sha256": sha256_file(source),
        }
        for source, target_path in bundle_source_entries()
    ]
    return {
        "schema_version": 1,
        "profile_id": PROFILE_ID,
        "model_label": MODEL_LABEL,
        "contract_version": CONTRACT_VERSION,
        "ast_policy_id": AST_POLICY_ID,
        "allowed_import_roots": list(ALLOWED_IMPORT_ROOTS),
        "registered_entrypoint": REGISTERED_ENTRYPOINT_FILENAME,
        "contract_sha256": expected_contract_sha256(),
        "semantic_unit_registry_sha256": semantic_registry_sha256(),
        "component_catalog_sha256": component_catalog_sha256(),
        "screening_mass_constants_sha256": screening_mass_constants_sha256(),
        "flowsheet_profile_sha256": flowsheet_profile_sha256(),
        "profile_constants_sha256": profile_constants_sha256(),
        "assembler_contract_sha256": assembler_contract_sha256(),
        "entrypoint_sha256": sha256_file(bundled_script_path()),
        "files": files,
    }


def expected_bundle_manifest_bytes() -> bytes:
    return canonical_json(expected_bundle_manifest()).encode("utf-8")


def install_registered_bundle(target_dir: Path) -> None:
    entrypoint = target_dir / REGISTERED_ENTRYPOINT_FILENAME
    if entrypoint.is_symlink() or not entrypoint.is_file():
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_missing",
            "Registered process-kernel entrypoint is missing.",
        )
    if sha256_file(entrypoint) != sha256_file(bundled_script_path()):
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_hash_mismatch",
            "Registered process-kernel entrypoint hash mismatch.",
        )
    package_dir = target_dir / "process_kernel"
    if package_dir.exists() or package_dir.is_symlink():
        raise RunnerSafetyError("runner_process_kernel_bundle_exists", "Process-kernel bundle already exists.")
    package_dir.mkdir(parents=False, exist_ok=False)
    try:
        for source, target_path in bundle_source_entries():
            target = target_dir / target_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (target_dir / BUNDLE_MANIFEST_FILENAME).write_bytes(expected_bundle_manifest_bytes())
        validate_registered_bundle(target_dir)
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        (target_dir / BUNDLE_MANIFEST_FILENAME).unlink(missing_ok=True)
        raise


def validate_registered_bundle(target_dir: Path) -> str:
    if target_dir.is_symlink() or not target_dir.is_dir():
        raise RunnerSafetyError("runner_process_kernel_bundle_missing", "Process-kernel model directory is missing.")
    expected_top_level = {
        REGISTERED_ENTRYPOINT_FILENAME,
        BUNDLE_MANIFEST_FILENAME,
        "process_kernel",
    }
    actual_top_level = {path.name for path in target_dir.iterdir()}
    if actual_top_level != expected_top_level:
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_files_invalid",
            "Process-kernel model directory file set is invalid.",
        )

    entrypoint = target_dir / REGISTERED_ENTRYPOINT_FILENAME
    manifest_path = target_dir / BUNDLE_MANIFEST_FILENAME
    package_dir = target_dir / "process_kernel"
    if entrypoint.is_symlink() or not entrypoint.is_file():
        raise RunnerSafetyError("runner_process_kernel_bundle_missing", "Process-kernel entrypoint is missing.")
    if sha256_file(entrypoint) != sha256_file(bundled_script_path()):
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_hash_mismatch",
            "Process-kernel entrypoint hash mismatch.",
        )
    if package_dir.is_symlink() or not package_dir.is_dir():
        raise RunnerSafetyError("runner_process_kernel_bundle_missing", "Process-kernel package is missing.")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise RunnerSafetyError("runner_process_kernel_bundle_missing", "Process-kernel bundle manifest is missing.")
    raw = manifest_path.read_bytes()
    expected = expected_bundle_manifest_bytes()
    if raw != expected:
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_hash_mismatch",
            "Process-kernel bundle manifest is stale or modified.",
        )
    manifest = expected_bundle_manifest()
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list):
        raise RunnerSafetyError("runner_process_kernel_bundle_files_invalid", "Process-kernel manifest is invalid.")
    expected_targets = {str(item["target_path"]) for item in manifest_files}
    actual_targets: set[str] = set()
    for path in package_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            raise RunnerSafetyError(
                "runner_process_kernel_bundle_files_invalid",
                "Process-kernel package contains an unsupported entry.",
            )
        actual_targets.add(path.relative_to(target_dir).as_posix())
    if actual_targets != expected_targets:
        raise RunnerSafetyError(
            "runner_process_kernel_bundle_files_invalid",
            "Process-kernel package file set is invalid.",
        )
    for item in manifest_files:
        target = target_dir / str(item["target_path"])
        if target.is_symlink() or not target.is_file() or sha256_file(target) != item["sha256"]:
            raise RunnerSafetyError(
                "runner_process_kernel_bundle_hash_mismatch",
                "Process-kernel package hash mismatch.",
            )
    return hashlib.sha256(raw).hexdigest()


def is_exact_bundled_profile(model_version: Any, script_sha256: str) -> bool:
    try:
        script_path = Path(str(model_version["script_path"]))
        expected_manifest_sha = hashlib.sha256(expected_bundle_manifest_bytes()).hexdigest()
        return (
            script_path.name == REGISTERED_ENTRYPOINT_FILENAME
            and model_version["implementation_kind"] == "calc_v0"
            and model_version["version_label"] == MODEL_LABEL
            and script_sha256 == sha256_file(bundled_script_path())
            and model_version["script_sha256"] == script_sha256
            and model_version["input_contract_sha256"] == expected_contract_sha256()
            and validate_registered_bundle(script_path.parent) == expected_manifest_sha
        )
    except (KeyError, OSError, RunnerSafetyError, TypeError, ValueError):
        return False


def normalize_input_set(
    input_set: dict[str, Any],
    *,
    load_parameter: ParameterLoader | None = None,
) -> dict[str, dict[str, object]]:
    contract_payload, contract_sha, _ = canonicalize_input_contract(expected_contract())
    contract, parsed_sha = parse_stored_input_contract(contract_payload, contract_sha)
    if parsed_sha != contract_sha or not isinstance(contract, ModelInputContractV2):
        raise RunnerSafetyError("runner_input_contract_invalid", "Bundled process-kernel contract is not schema v2.")
    normalized = normalize_input_set_v2(contract, input_set, load_parameter=load_parameter)
    inner = normalized["tube_inner_diameter"]["value"]
    outer = normalized["tube_outer_diameter"]["value"]
    if not isinstance(inner, float) or not isinstance(outer, float) or outer < inner:
        raise RunnerSafetyError("runner_input_invalid", "Tube outer diameter must not be smaller than inner diameter.")
    return normalized


def build_binding_preview_v2(
    *,
    model_version_id: str,
    contract_payload: str | None,
    contract_sha256: str | None,
    bindings: dict[str, Any],
    load_parameter: ParameterLoader,
) -> BindingPreviewResponse:
    return build_binding_preview(
        model_version_id=model_version_id,
        contract_payload=contract_payload,
        contract_sha256=contract_sha256,
        bindings=bindings,
        load_parameter=load_parameter,
    )
