import json
from pathlib import Path
from typing import Any

from app.core.database import open_sqlite_connection
from app.modules.runner import service as _legacy
from app.modules.runner.api_models import ModelImplementationCreateRequest
from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.models import (
    BindingPreviewRequest,
    BindingPreviewResponse,
    ModelImplementationCreate,
    ModelImplementationRead,
    RunArtifactRead,
    RunLogRead,
    RunnerJobCreate,
    RunnerJobCreateResponse,
    RunnerJobRunResponse,
    SimulationRunDetail,
)
from app.modules.runner.safety import (
    RunnerSafetyError,
    preflight_script_policy,
    sha256_file,
    validate_script_path,
)
from app.modules.runner.topology_m1 import (
    MODEL_LABEL as BUNDLED_BLUEREV_TOPOLOGY_M1_LABEL,
)
from app.modules.runner.topology_m1 import is_exact_bundled_profile

_RUNNER_DIR = Path(__file__).resolve().parent
_EXAMPLES_DIR = _RUNNER_DIR / "examples"

_BATCH_GROWTH_SCRIPT = _EXAMPLES_DIR / "batch_growth.py"

_BUNDLED_CALC_PROFILES = {
    _legacy.BUNDLED_BLUEREV_PROCESS0_LABEL: (
        _EXAMPLES_DIR / "bluerev_geometry_hydraulics_v0.py",
        _EXAMPLES_DIR / "bluerev_geometry_hydraulics_v0.contract.json",
        "calc_v0",
    ),
    _legacy.BUNDLED_BLUEREV_PROCESS1_LABEL: (
        _EXAMPLES_DIR / "bluerev_biomass_nutrients_harvest_v0.py",
        _EXAMPLES_DIR / "bluerev_biomass_nutrients_harvest_v0.contract.json",
        "calc_v0",
    ),
    _legacy.BUNDLED_BLUEREV_PROCESS2_LABEL: (
        _EXAMPLES_DIR / "bluerev_buoyancy_optical_screening_v0.py",
        _EXAMPLES_DIR / "bluerev_buoyancy_optical_screening_v0.contract.json",
        "calc_v0",
    ),
    BUNDLED_BLUEREV_TOPOLOGY_M1_LABEL: (
        _EXAMPLES_DIR / "bluerev_process_topology_m1_v0.py",
        _EXAMPLES_DIR / "bluerev_process_topology_m1_v0.contract.json",
        "calc_v0_topology_m1",
    ),
}


def create_model_implementation(
    workspace_id: str,
    payload: ModelImplementationCreateRequest,
) -> ModelImplementationRead:
    """Create only the server-owned bundled batch-growth implementation."""

    if payload.implementation_kind == _legacy.BLUECAD_L2_IMPLEMENTATION_KIND:
        raise RunnerSafetyError(
            "runner_implementation_kind_non_instantiable",
            "bluecad_l2_v0 is not instantiable in normal configuration.",
        )
    if payload.implementation_kind != _legacy.IMPLEMENTATION_KIND:
        raise RunnerSafetyError(
            "runner_bundled_registration_required",
            "calc_v0 implementations must use an exact bundled registration endpoint.",
        )
    return _legacy.create_model_implementation(
        workspace_id,
        ModelImplementationCreate(
            model_spec_id=payload.model_spec_id,
            version_label=payload.version_label,
            implementation_kind=payload.implementation_kind,
            notes=payload.notes,
            input_contract=payload.input_contract,
        ),
    )


def create_runner_job(workspace_id: str, payload: RunnerJobCreate) -> RunnerJobCreateResponse:
    _require_exact_bundled_model(workspace_id, payload.model_version_id)
    return _legacy.create_runner_job(workspace_id, payload)


def run_runner_job(runner_job_id: str) -> RunnerJobRunResponse:
    job = _load_job_authority(runner_job_id)
    model_version = _require_exact_bundled_model(job["workspace_id"], job["model_version_id"])

    job_script = validate_script_path(job["workspace_id"], job["job_script_path"])
    model_script = validate_script_path(job["workspace_id"], model_version["script_path"])
    if job_script.resolve() != model_script.resolve():
        raise RunnerSafetyError(
            "runner_implementation_not_bundled",
            "Runner job script does not match its bundled model implementation.",
        )
    actual_sha = sha256_file(job_script)
    if actual_sha != job["job_script_sha256"] or actual_sha != model_version["script_sha256"]:
        raise RunnerSafetyError(
            "runner_implementation_not_bundled",
            "Runner job script no longer matches its bundled implementation identity.",
        )

    ast_policy = _ast_policy_for(model_version)
    try:
        preflight_script_policy(job_script, ast_policy=ast_policy)
    except RunnerSafetyError as exc:
        if exc.code in {"SANDBOX_VIOLATION", "RUNNER_SCRIPT_POLICY_VIOLATION"}:
            raise RunnerSafetyError(
                "RUNNER_SCRIPT_POLICY_VIOLATION",
                exc.message,
            ) from exc
        raise

    return _legacy.run_runner_job(runner_job_id)


def _require_exact_bundled_model(workspace_id: str, model_version_id: str) -> dict[str, Any]:
    row = _load_model_version(workspace_id, model_version_id)
    kind = str(row["implementation_kind"])
    if kind == _legacy.BLUECAD_L2_IMPLEMENTATION_KIND:
        raise RunnerSafetyError(
            "runner_implementation_kind_non_instantiable",
            "bluecad_l2_v0 is not instantiable in normal configuration.",
        )
    if not _is_exact_bundled(row):
        raise RunnerSafetyError(
            "runner_implementation_not_bundled",
            "Only exact server-known bundled implementations are executable.",
        )
    return row


def _is_exact_bundled(row: dict[str, Any]) -> bool:
    if row.get("status") != "ready" or row.get("artifact_status") != "registered":
        return False

    workspace_id = str(row["workspace_id"])
    try:
        script_path = validate_script_path(workspace_id, str(row["script_path"]))
    except RunnerSafetyError:
        return False
    actual_sha = sha256_file(script_path)
    if actual_sha != row.get("script_sha256"):
        return False

    kind = str(row["implementation_kind"])
    if kind == _legacy.IMPLEMENTATION_KIND:
        return actual_sha == sha256_file(_BATCH_GROWTH_SCRIPT)
    if kind != _legacy.CALC_V0_IMPLEMENTATION_KIND:
        return False

    label = str(row["version_label"])
    profile = _BUNDLED_CALC_PROFILES.get(label)
    if profile is None:
        return False
    expected_script, expected_contract, _ = profile
    if actual_sha != sha256_file(expected_script):
        return False
    if row.get("input_contract_sha256") != _contract_sha256(expected_contract):
        return False
    if label == BUNDLED_BLUEREV_TOPOLOGY_M1_LABEL:
        return is_exact_bundled_profile(row, actual_sha)
    return True


def _ast_policy_for(row: dict[str, Any]) -> str | None:
    kind = str(row["implementation_kind"])
    if kind != _legacy.CALC_V0_IMPLEMENTATION_KIND:
        return None
    profile = _BUNDLED_CALC_PROFILES.get(str(row["version_label"]))
    return profile[2] if profile is not None else "calc_v0"


def _contract_sha256(path: Path) -> str:
    contract = json.loads(path.read_text(encoding="utf-8"))
    _, digest, _ = canonicalize_input_contract(contract)
    return digest


def _load_model_version(workspace_id: str, model_version_id: str) -> dict[str, Any]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path,
                   a.status AS artifact_status
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.id = ? AND mv.workspace_id = ?
            """,
            (model_version_id, workspace_id),
        ).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_model_version_not_found", "Model implementation not found.")
    return dict(row)


def _load_job_authority(runner_job_id: str) -> dict[str, str]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT rj.workspace_id, rj.script_path AS job_script_path,
                   rj.script_sha256 AS job_script_sha256, sr.model_version_id
            FROM runner_jobs rj
            JOIN simulation_runs sr ON sr.id = rj.simulation_run_id
            WHERE rj.id = ?
            """,
            (runner_job_id,),
        ).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_job_not_found", "Runner job not found.")
    if row["model_version_id"] is None:
        raise RunnerSafetyError(
            "runner_model_version_not_found",
            "Runner job has no model implementation.",
        )
    return {
        "workspace_id": str(row["workspace_id"]),
        "job_script_path": str(row["job_script_path"]),
        "job_script_sha256": str(row["job_script_sha256"]),
        "model_version_id": str(row["model_version_id"]),
    }


# Read-only and exact bundled-registration paths retain their established behavior.
list_model_implementations = _legacy.list_model_implementations
preview_model_bindings = _legacy.preview_model_bindings
register_bundled_bluerev_process0 = _legacy.register_bundled_bluerev_process0
register_bundled_bluerev_process1 = _legacy.register_bundled_bluerev_process1
register_bundled_bluerev_process2 = _legacy.register_bundled_bluerev_process2
register_bundled_bluerev_topology_m1 = _legacy.register_bundled_bluerev_topology_m1
get_simulation_run_detail = _legacy.get_simulation_run_detail
list_run_artifacts = _legacy.list_run_artifacts
list_run_logs = _legacy.list_run_logs

__all__ = [
    "BindingPreviewRequest",
    "BindingPreviewResponse",
    "ModelImplementationRead",
    "RunArtifactRead",
    "RunLogRead",
    "RunnerJobCreate",
    "RunnerJobCreateResponse",
    "RunnerJobRunResponse",
    "SimulationRunDetail",
    "create_model_implementation",
    "create_runner_job",
    "get_simulation_run_detail",
    "list_model_implementations",
    "list_run_artifacts",
    "list_run_logs",
    "preview_model_bindings",
    "register_bundled_bluerev_process0",
    "register_bundled_bluerev_process1",
    "register_bundled_bluerev_process2",
    "register_bundled_bluerev_topology_m1",
    "run_runner_job",
]
