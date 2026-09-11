from __future__ import annotations

from app.core.database import open_sqlite_connection
from app.modules.modeling.dossier_models import ModelDossierIndexItem
from app.modules.modeling.model_dossier import (
    MODEL_DOSSIER_MAX_MODELS,
    MODEL_DOSSIER_MAX_VERSIONS_PER_MODEL,
    list_model_dossier_index,
)


class ModelDossierSearchCapacityError(RuntimeError):
    pass


def _contains_literal(needle: str, value: str | None) -> bool:
    return isinstance(value, str) and needle in value.casefold()


def search_model_dossier_index(workspace_id: str, query: str) -> list[ModelDossierIndexItem]:
    """Return bounded literal model/version candidates without creating a second index.

    The existing dossier index intentionally caps models and versions. Search must
    never silently present that capped prefix as a complete project-wide result,
    so datasets beyond those owner bounds fail closed until a separately accepted
    search/index strategy exists.
    """
    with open_sqlite_connection() as connection:
        workspace = connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise ValueError("Workspace not found.")
        model_count = int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM model_specs WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()["count"]
        )
        if model_count > MODEL_DOSSIER_MAX_MODELS:
            raise ModelDossierSearchCapacityError("Model dossier search exceeds the bounded model scan capacity.")
        overflowing_version = connection.execute(
            """
            SELECT model_spec_id
            FROM model_versions
            WHERE workspace_id = ?
            GROUP BY model_spec_id
            HAVING COUNT(*) > ?
            LIMIT 1
            """,
            (workspace_id, MODEL_DOSSIER_MAX_VERSIONS_PER_MODEL),
        ).fetchone()
        if overflowing_version is not None:
            raise ModelDossierSearchCapacityError("Model dossier search exceeds the bounded version scan capacity.")

    needle = query.casefold()
    matches: list[ModelDossierIndexItem] = []
    for item in list_model_dossier_index(workspace_id):
        matching_versions = [
            version
            for version in item.versions
            if any(
                _contains_literal(needle, value)
                for value in (
                    item.title,
                    item.engineering_question,
                    item.scope,
                    version.version_label,
                    version.implementation_kind,
                )
            )
        ]
        if matching_versions:
            matches.append(item.model_copy(update={"versions": matching_versions}))
    return matches
