from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

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
        return _create_runner_job_idempotent(workspace_id, payload)
    except RunnerSafetyError as exc:
        translated = _translate_policy_error(exc)
        if translated is exc:
            raise
        raise translated from exc


def _create_runner_job_idempotent(
    workspace_id: str,
    payload: RunnerJobCreate,
) -> RunnerJobCreateResponse:
    now = _base.utc_now()
    timeout_seconds = min(payload.timeout_seconds or _base.DEFAULT_TIMEOUT_SECONDS, 60)

    with open_sqlite_connection() as connection:
        _base._require_workspace(connection, workspace_id)
        model_version = _base._load_model_version_with_artifact(
            connection,
            workspace_id,
            payload.model_version_id,
        )
        implementation_kind = model_version["implementation_kind"]
        if implementation_kind == _base.IMPLEMENTATION_KIND:
            input_payload, parameter_payload = _base.validate_batch_growth_input(payload.input_set)
        elif implementation_kind == _base.BLUECAD_L2_IMPLEMENTATION_KIND:
            input_payload, parameter_payload = _base.validate_bluecad_l2_input(payload.input_set)
        elif implementation_kind == _base.CALC_V0_IMPLEMENTATION_KIND:
            input_payload, parameter_payload = _base.validate_calc_v0_input(payload.input_set)
        else:
            raise RunnerSafetyError("runner_implementation_kind_unsupported", "Unsupported implementation kind.")

        script_path = _base.validate_script_path(workspace_id, model_version["script_path"])
        script_sha = _base.sha256_file(script_path)
        if script_sha != model_version["script_sha256"]:
            raise RunnerSafetyError("runner_script_hash_mismatch", "Script hash does not match registered artifact.")
        if implementation_kind == _base.BLUECAD_L2_IMPLEMENTATION_KIND:
            _base.preflight_script_policy(script_path, ast_import_allowlist=True)
        elif implementation_kind == _base.CALC_V0_IMPLEMENTATION_KIND:
            topology_profile = _base.is_exact_bundled_profile(model_version, script_sha)
            if topology_profile:
                _base._validate_topology_source_parameter_bindings(
                    connection,
                    workspace_id,
                    input_payload,
                )
            _base.preflight_script_policy(
                script_path,
                ast_policy=(
                    "calc_v0_topology_m1"
                    if topology_profile
                    else _base.CALC_V0_IMPLEMENTATION_KIND
                ),
            )

        if payload.request_key is not None:
            # Serialize request-key owners so concurrent retries cannot both create
            # a run before the unique workspace/key row becomes visible.
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT
                    rj.id AS runner_job_id,
                    rj.simulation_run_id,
                    rj.timeout_seconds,
                    sr.model_version_id,
                    sr.run_label,
                    sr.input_payload,
                    sr.parameter_payload
                FROM runner_jobs rj
                JOIN simulation_runs sr ON sr.id = rj.simulation_run_id
                WHERE rj.workspace_id = ? AND rj.request_key = ?
                """,
                (workspace_id, payload.request_key),
            ).fetchone()
            if existing is not None:
                same_payload = (
                    existing["model_version_id"] == payload.model_version_id
                    and existing["run_label"] == payload.run_label
                    and existing["input_payload"] == input_payload
                    and existing["parameter_payload"] == parameter_payload
                    and int(existing["timeout_seconds"]) == timeout_seconds
                )
                runner_job_id = str(existing["runner_job_id"])
                simulation_run_id = str(existing["simulation_run_id"])
                connection.rollback()
                if not same_payload:
                    raise RunnerSafetyError(
                        "runner_request_key_conflict",
                        "Runner request key is already bound to a different create payload.",
                    )
                return RunnerJobCreateResponse(
                    runner_job=_base.get_runner_job(runner_job_id),
                    simulation_run=_base.get_simulation_run_detail(workspace_id, simulation_run_id),
                )

        simulation_run_id = str(uuid4())
        runner_job_id = str(uuid4())
        job_run_root = _base.run_root(workspace_id, simulation_run_id)
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload, started_at,
                completed_at, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                simulation_run_id,
                workspace_id,
                payload.model_version_id,
                payload.run_label,
                "queued",
                input_payload,
                parameter_payload,
                None,
                None,
                None,
                now,
                "Created by Python Runner V0.",
            ),
        )
        connection.execute(
            """
            INSERT INTO runner_jobs (
                id, workspace_id, simulation_run_id, runner_type, status,
                script_path, script_sha256, implementation_kind, command_json, environment_json,
                working_dir, input_file, output_dir, timeout_seconds,
                max_stdout_bytes, max_stderr_bytes, max_output_json_bytes,
                max_artifact_bytes, request_key, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                runner_job_id,
                workspace_id,
                simulation_run_id,
                _base.RUNNER_TYPE,
                "queued",
                str(script_path),
                script_sha,
                implementation_kind,
                None,
                None,
                str(job_run_root),
                str(job_run_root / "input.json"),
                str(job_run_root),
                timeout_seconds,
                _base.MAX_STDOUT_BYTES,
                _base.MAX_STDERR_BYTES,
                _base.MAX_OUTPUT_JSON_BYTES,
                _base.MAX_ARTIFACT_BYTES,
                payload.request_key,
                now,
                now,
            ),
        )
        _base._log_event(
            connection,
            event_type="RunnerJobCreated",
            target_type="RunnerJob",
            target_id=runner_job_id,
            workspace_id=workspace_id,
            payload={
                "simulation_run_id": simulation_run_id,
                "model_version_id": payload.model_version_id,
                "status": "queued",
                "script_sha256": script_sha,
            },
        )
        _base._log_event(
            connection,
            event_type="SimulationRunCreated",
            target_type="SimulationRun",
            target_id=simulation_run_id,
            workspace_id=workspace_id,
            payload={"run_label": payload.run_label, "status": "queued"},
        )
        connection.commit()

    return RunnerJobCreateResponse(
        runner_job=_base.get_runner_job(runner_job_id),
        simulation_run=_base.get_simulation_run_detail(workspace_id, simulation_run_id),
    )


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
