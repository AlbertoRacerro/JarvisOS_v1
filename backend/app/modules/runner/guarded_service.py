from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.database import open_sqlite_connection
from app.modules.runner import service as _base
from app.modules.runner.input_contracts import canonicalize_input_contract
from app.modules.runner.models import (
    ModelImplementationCreate,
    ModelImplementationRead,
    RunnerJobCreate,
    RunnerJobCreateResponse,
    RunnerJobRunResponse,
)
from app.modules.runner.process_kernel_047 import (
    is_exact_bundled_profile as is_exact_process_kernel_profile,
)
from app.modules.runner.process_kernel_registration import (
    normalize_process_kernel_input,
)
from app.modules.runner.process_kernel_registration import (
    register_bundled_process_kernel as _register_bundled_process_kernel,
)
from app.modules.runner.public_models import PublicModelImplementationCreate
from app.modules.runner.safety import RunnerSafetyError, sha256_file

RUNNER_SCRIPT_POLICY_VIOLATION = "RUNNER_SCRIPT_POLICY_VIOLATION"
_LEGACY_SANDBOX_VIOLATION = "SANDBOX_VIOLATION"


def create_model_implementation(
    workspace_id: str,
    payload: PublicModelImplementationCreate,
) -> ModelImplementationRead:
    """Register only the fixed bundled batch-growth implementation.

    Reviewed calc models use their dedicated bundled registration routes.
    BLUECAD L2 remains a historical profile but is not instantiable.
    """

    if payload.implementation_kind != _base.IMPLEMENTATION_KIND:
        raise RunnerSafetyError(
            "runner_implementation_kind_unsupported",
            "Normal registration supports only the bundled batch_growth_v0 implementation.",
        )
    return _base.create_model_implementation(
        workspace_id,
        ModelImplementationCreate(
            model_spec_id=payload.model_spec_id,
            version_label=payload.version_label,
            implementation_kind=_base.IMPLEMENTATION_KIND,
            notes=payload.notes,
            input_contract=payload.input_contract,
        ),
    )


def create_runner_job(
    workspace_id: str,
    payload: RunnerJobCreate,
) -> RunnerJobCreateResponse:
    model_version = _load_model_version(workspace_id, payload.model_version_id)
    _require_exact_bundled(model_version)
    stored_sha = str(model_version["script_sha256"])
    if is_exact_process_kernel_profile(model_version, stored_sha):
        normalized = normalize_process_kernel_input(workspace_id, payload.input_set)
        payload = payload.model_copy(update={"input_set": normalized})
    try:
        return _base.create_runner_job(workspace_id, payload)
    except RunnerSafetyError as exc:
        translated = _translate_policy_error(exc)
        if translated is exc:
            raise
        raise translated from exc


def run_runner_job(runner_job_id: str) -> RunnerJobRunResponse:
    model_version = _load_job_model_version(runner_job_id)
    _require_exact_bundled(model_version)
    try:
        response = _base.run_runner_job(runner_job_id)
    except RunnerSafetyError as exc:
        translated = _translate_policy_error(exc)
        if translated is exc:
            raise
        raise translated from exc
    if response.error and response.error.get("code") == _LEGACY_SANDBOX_VIOLATION:
        error = dict(response.error)
        error["code"] = RUNNER_SCRIPT_POLICY_VIOLATION
        return response.model_copy(update={"error": error})
    return response


def _translate_policy_error(exc: RunnerSafetyError) -> RunnerSafetyError:
    if exc.code == _LEGACY_SANDBOX_VIOLATION:
        return RunnerSafetyError(RUNNER_SCRIPT_POLICY_VIOLATION, exc.message)
    return exc


def _require_exact_bundled(model_version: dict[str, Any]) -> None:
    if not _is_exact_bundled(model_version):
        raise RunnerSafetyError(
            RUNNER_SCRIPT_POLICY_VIOLATION,
            "Runner execution is limited to exact server-known bundled implementations.",
        )


def _is_exact_bundled(model_version: dict[str, Any]) -> bool:
    stored_path = model_version.get("script_path")
    stored_sha = model_version.get("script_sha256")
    if not isinstance(stored_path, str) or not isinstance(stored_sha, str):
        return False
    try:
        if sha256_file(Path(stored_path)) != stored_sha:
            return False
    except (OSError, ValueError):
        return False

    kind = model_version.get("implementation_kind")
    if kind == _base.IMPLEMENTATION_KIND:
        return stored_sha == sha256_file(_base._example_script_path())

    if kind != _base.CALC_V0_IMPLEMENTATION_KIND:
        return False

    if is_exact_process_kernel_profile(model_version, stored_sha):
        return True

    if _base.is_exact_bundled_profile(model_version, stored_sha):
        return True

    profiles = (
        (
            _base.BUNDLED_BLUEREV_PROCESS0_LABEL,
            _base._bluerev_process0_script_path(),
            _base._bluerev_process0_contract_path(),
        ),
        (
            _base.BUNDLED_BLUEREV_PROCESS1_LABEL,
            _base._bluerev_process1_script_path(),
            _base._bluerev_process1_contract_path(),
        ),
        (
            _base.BUNDLED_BLUEREV_PROCESS2_LABEL,
            _base._bluerev_process2_script_path(),
            _base._bluerev_process2_contract_path(),
        ),
    )
    for label, script_path, contract_path in profiles:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        _, contract_sha, _ = canonicalize_input_contract(contract)
        if (
            model_version.get("version_label") == label
            and stored_sha == sha256_file(script_path)
            and model_version.get("input_contract_sha256") == contract_sha
        ):
            return True
    return False


def _load_model_version(workspace_id: str, model_version_id: str) -> dict[str, Any]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.workspace_id = ? AND mv.id = ?
            """,
            (workspace_id, model_version_id),
        ).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_model_version_not_found", "Model implementation not found.")
    return dict(row)


def _load_job_model_version(runner_job_id: str) -> dict[str, Any]:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path
            FROM runner_jobs rj
            JOIN simulation_runs sr ON sr.id = rj.simulation_run_id
            JOIN model_versions mv ON mv.id = sr.model_version_id
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE rj.id = ?
            """,
            (runner_job_id,),
        ).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_job_not_found", "Runner job not found.")
    return dict(row)


# Read-only and exact bundled registration paths remain owned by reviewed services.
list_model_implementations = _base.list_model_implementations
preview_model_bindings = _base.preview_model_bindings
register_bundled_bluerev_process0 = _base.register_bundled_bluerev_process0
register_bundled_bluerev_process1 = _base.register_bundled_bluerev_process1
register_bundled_bluerev_process2 = _base.register_bundled_bluerev_process2
register_bundled_bluerev_topology_m1 = _base.register_bundled_bluerev_topology_m1
register_bundled_process_kernel = _register_bundled_process_kernel
get_simulation_run_detail = _base.get_simulation_run_detail
list_run_artifacts = _base.list_run_artifacts
list_run_logs = _base.list_run_logs
