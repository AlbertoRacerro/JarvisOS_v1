from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.core.database import open_sqlite_connection
from app.modules.modeling.models import ModelSpecCreate
from app.modules.modeling.service import create_model_spec
from app.modules.runner import service as _base
from app.modules.runner.linked_parameters import load_usable_linked_parameter
from app.modules.runner.models import ModelImplementationCreate, ModelImplementationRead
from app.modules.runner.process_kernel_047 import (
    MODEL_LABEL,
    MODEL_TITLE,
    bundled_script_path,
    expected_contract,
    expected_contract_sha256,
    install_registered_bundle,
    is_exact_bundled_profile,
)
from app.modules.runner.safety import RunnerSafetyError, sha256_file

_ARTIFACT_NOTES = "Server-owned PROCESS-KERNEL-1 exact 047 entrypoint."
_CHANGELOG = "Initial server-owned PROCESS-KERNEL-1 exact 047 implementation."
_MODEL_NOTES = "Server-owned PROCESS-KERNEL-1 exact 047 profile."


def register_bundled_process_kernel(workspace_id: str) -> ModelImplementationRead:
    script_path = bundled_script_path()
    script_sha = sha256_file(script_path)
    contract = expected_contract()
    contract_sha = expected_contract_sha256()

    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)
        existing = connection.execute(
            """
            SELECT mv.*, a.sha256 AS script_sha256, a.stored_path AS script_path
            FROM model_versions mv
            JOIN artifacts a ON a.id = mv.implementation_artifact_id
            WHERE mv.workspace_id = ?
              AND mv.version_label = ?
              AND mv.input_contract_sha256 = ?
              AND a.sha256 = ?
            ORDER BY mv.created_at ASC
            LIMIT 1
            """,
            (workspace_id, MODEL_LABEL, contract_sha, script_sha),
        ).fetchone()
        model_spec = connection.execute(
            """
            SELECT id FROM model_specs
            WHERE workspace_id = ? AND title = ?
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (workspace_id, MODEL_TITLE),
        ).fetchone()

    if existing is not None:
        row = dict(existing)
        if not is_exact_bundled_profile(row, script_sha):
            raise RunnerSafetyError(
                "RUNNER_SCRIPT_POLICY_VIOLATION",
                "Existing process-kernel registration does not match the server-owned profile.",
            )
        return _base.get_model_implementation(workspace_id, str(row["id"]))

    if model_spec is None:
        created_spec = create_model_spec(
            workspace_id,
            ModelSpecCreate(
                title=MODEL_TITLE,
                engineering_question=(
                    "Reproduce the reviewed 047 tubular-loop geometry and hydraulics model "
                    "through explicit typed process blocks."
                ),
                scope=(
                    "PROCESS-KERNEL-1 exact 047 forward profile; all nine values remain "
                    "caller supplied and no recycle, property package, or optimizer is implied."
                ),
            ),
        )
        model_spec_id = created_spec.id
    else:
        model_spec_id = str(model_spec["id"])

    implementation = _base.create_model_implementation(
        workspace_id,
        ModelImplementationCreate(
            model_spec_id=model_spec_id,
            version_label=MODEL_LABEL,
            implementation_kind=_base.CALC_V0_IMPLEMENTATION_KIND,
            notes=_MODEL_NOTES,
            script_text=script_path.read_text(encoding="utf-8"),
            input_contract=contract,
        ),
    )
    target_dir = Path(implementation.script_path).parent
    try:
        target_entrypoint = Path(implementation.script_path)
        target_entrypoint.write_bytes(script_path.read_bytes())
        _mark_server_owned_registration(implementation.id, script_sha)
        install_registered_bundle(target_dir)
        row = _load_model_version(workspace_id, implementation.id)
        if not is_exact_bundled_profile(row, script_sha):
            raise RunnerSafetyError(
                "RUNNER_SCRIPT_POLICY_VIOLATION",
                "Installed process-kernel registration failed exact profile verification.",
            )
    except Exception:
        _rollback_registration(implementation.id, target_dir)
        raise
    return _base.get_model_implementation(workspace_id, implementation.id)


def normalize_process_kernel_input(
    workspace_id: str,
    input_set: dict[str, Any],
) -> dict[str, dict[str, object]]:
    from app.modules.runner.process_kernel_047 import normalize_input_set

    with open_sqlite_connection() as connection:
        _require_workspace(connection, workspace_id)

        def load_parameter(parameter_id: str) -> dict[str, object] | None:
            return load_usable_linked_parameter(connection, workspace_id, parameter_id)

        return normalize_input_set(input_set, load_parameter=load_parameter)


def _mark_server_owned_registration(model_version_id: str, script_sha: str) -> None:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT implementation_artifact_id FROM model_versions WHERE id = ?",
            (model_version_id,),
        ).fetchone()
        if row is None:
            raise RunnerSafetyError("runner_model_version_not_found", "Model implementation not found.")
        connection.execute(
            "UPDATE artifacts SET sha256 = ?, notes = ? WHERE id = ?",
            (script_sha, _ARTIFACT_NOTES, row["implementation_artifact_id"]),
        )
        connection.execute(
            "UPDATE model_versions SET changelog = ?, notes = ? WHERE id = ?",
            (_CHANGELOG, _MODEL_NOTES, model_version_id),
        )
        connection.commit()


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


def _rollback_registration(model_version_id: str, target_dir: Path) -> None:
    with open_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT implementation_artifact_id FROM model_versions WHERE id = ?",
            (model_version_id,),
        ).fetchone()
        if row is not None:
            connection.execute("DELETE FROM model_versions WHERE id = ?", (model_version_id,))
            connection.execute("DELETE FROM artifacts WHERE id = ?", (row["implementation_artifact_id"],))
            connection.commit()
    shutil.rmtree(target_dir, ignore_errors=True)


def _require_workspace(connection: Any, workspace_id: str) -> None:
    row = connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    if row is None:
        raise RunnerSafetyError("runner_workspace_not_found", "Workspace not found.")
