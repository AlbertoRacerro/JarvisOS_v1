import sqlite3

from app.core.database import open_sqlite_connection
from app.modules.modeling.dossier_models import (
    ModelDossierArtifactRef,
    ModelDossierDetail,
    ModelDossierIndexItem,
    ModelDossierRunSummary,
    ModelDossierVersionIdentity,
)

MODEL_DOSSIER_MAX_MODELS = 100
MODEL_DOSSIER_MAX_VERSIONS_PER_MODEL = 20
MODEL_DOSSIER_MAX_RUNS = 50
MODEL_DOSSIER_MAX_ARTIFACTS = 100


def _version_identity(row: sqlite3.Row) -> ModelDossierVersionIdentity:
    return ModelDossierVersionIdentity(
        model_spec_id=row["model_spec_id"],
        model_version_id=row["model_version_id"],
        version_label=row["version_label"],
        implementation_kind=row["implementation_kind"],
        status=row["version_status"],
        created_at=row["version_created_at"],
        input_contract_digest=row["input_contract_sha256"],
    )


def list_model_dossier_index(workspace_id: str) -> list[ModelDossierIndexItem]:
    """Return a bounded exact-identity model/version index without persistence side effects."""
    with open_sqlite_connection() as connection:
        workspace = connection.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise ValueError("Workspace not found.")

        spec_rows = connection.execute(
            """
            SELECT id, title, engineering_question, scope
            FROM model_specs
            WHERE workspace_id = ?
            ORDER BY created_at DESC, id ASC
            LIMIT ?
            """,
            (workspace_id, MODEL_DOSSIER_MAX_MODELS),
        ).fetchall()

        items: list[ModelDossierIndexItem] = []
        for spec in spec_rows:
            version_rows = connection.execute(
                """
                SELECT
                    model_spec_id,
                    id AS model_version_id,
                    version_label,
                    implementation_kind,
                    status AS version_status,
                    created_at AS version_created_at,
                    input_contract_sha256
                FROM model_versions
                WHERE workspace_id = ? AND model_spec_id = ?
                ORDER BY created_at DESC, id ASC
                LIMIT ?
                """,
                (workspace_id, spec["id"], MODEL_DOSSIER_MAX_VERSIONS_PER_MODEL),
            ).fetchall()
            items.append(
                ModelDossierIndexItem(
                    model_spec_id=spec["id"],
                    title=spec["title"],
                    engineering_question=spec["engineering_question"],
                    scope=spec["scope"],
                    versions=[_version_identity(row) for row in version_rows],
                )
            )
        return items


def get_model_dossier(workspace_id: str, model_version_id: str) -> ModelDossierDetail | None:
    """Return one workspace-isolated dossier for an exact model-version identity."""
    with open_sqlite_connection() as connection:
        identity_row = connection.execute(
            """
            SELECT
                ms.id AS model_spec_id,
                ms.title,
                ms.engineering_question,
                ms.scope,
                ms.maturity_status,
                ms.assumptions_summary,
                ms.inputs_summary,
                ms.outputs_summary,
                mv.id AS model_version_id,
                mv.version_label,
                mv.implementation_kind,
                mv.status AS version_status,
                mv.created_at AS version_created_at,
                mv.input_contract_sha256
            FROM model_versions AS mv
            JOIN model_specs AS ms
              ON ms.id = mv.model_spec_id
             AND ms.workspace_id = mv.workspace_id
            WHERE mv.id = ? AND mv.workspace_id = ?
            """,
            (model_version_id, workspace_id),
        ).fetchone()
        if identity_row is None:
            return None

        run_rows = connection.execute(
            """
            SELECT
                id AS run_id,
                run_label,
                status,
                created_at,
                started_at,
                completed_at,
                project_knowledge_revision_id
            FROM simulation_runs
            WHERE workspace_id = ? AND model_version_id = ?
            ORDER BY created_at DESC, id ASC
            LIMIT ?
            """,
            (workspace_id, model_version_id, MODEL_DOSSIER_MAX_RUNS),
        ).fetchall()
        runs = [ModelDossierRunSummary(**dict(row)) for row in run_rows]

        artifact_rows = connection.execute(
            """
            SELECT
                ra.artifact_id,
                ra.simulation_run_id AS run_id,
                ra.role,
                a.sha256 AS digest,
                a.source_ref,
                CASE WHEN a.id IS NULL THEN 'unavailable' ELSE 'available' END AS availability
            FROM run_artifacts AS ra
            JOIN simulation_runs AS sr
              ON sr.id = ra.simulation_run_id
             AND sr.workspace_id = ra.workspace_id
            LEFT JOIN artifacts AS a
              ON a.id = ra.artifact_id
             AND a.workspace_id = ra.workspace_id
            WHERE ra.workspace_id = ? AND sr.model_version_id = ?
            ORDER BY ra.created_at DESC, ra.id ASC
            LIMIT ?
            """,
            (workspace_id, model_version_id, MODEL_DOSSIER_MAX_ARTIFACTS),
        ).fetchall()
        artifacts = [ModelDossierArtifactRef(**dict(row)) for row in artifact_rows]

        return ModelDossierDetail(
            identity=_version_identity(identity_row),
            title=identity_row["title"],
            engineering_question=identity_row["engineering_question"],
            scope=identity_row["scope"],
            maturity_status=identity_row["maturity_status"],
            assumptions_summary=identity_row["assumptions_summary"],
            inputs_summary=identity_row["inputs_summary"],
            outputs_summary=identity_row["outputs_summary"],
            runs=runs,
            artifacts=artifacts,
            evidence=[],
        )
