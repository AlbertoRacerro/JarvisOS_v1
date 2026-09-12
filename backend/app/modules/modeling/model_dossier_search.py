from __future__ import annotations

from app.core.database import open_sqlite_connection
from app.modules.modeling.dossier_models import ModelDossierIndexItem, ModelDossierVersionIdentity

_MODEL_SEARCH_MATCH_LIMIT = 101


def _escape_like_literal(value: str) -> str:
    return value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_model_dossier_index(workspace_id: str, query: str) -> list[ModelDossierIndexItem]:
    """Return bounded literal model/version matches from canonical dossier tables."""
    pattern = f"%{_escape_like_literal(query)}%"
    with open_sqlite_connection() as connection:
        workspace = connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise ValueError("Workspace not found.")
        rows = connection.execute(
            """
            SELECT
                ms.id AS model_spec_id,
                ms.title,
                ms.engineering_question,
                ms.scope,
                ms.created_at AS model_created_at,
                mv.id AS model_version_id,
                mv.version_label,
                mv.implementation_kind,
                mv.status AS version_status,
                mv.created_at AS version_created_at,
                mv.input_contract_sha256
            FROM model_specs AS ms
            LEFT JOIN model_versions AS mv
              ON mv.model_spec_id = ms.id
             AND mv.workspace_id = ms.workspace_id
            WHERE ms.workspace_id = ?
              AND (
                LOWER(COALESCE(ms.title, '')) LIKE ? ESCAPE '\\'
                OR LOWER(COALESCE(ms.engineering_question, '')) LIKE ? ESCAPE '\\'
                OR LOWER(COALESCE(ms.scope, '')) LIKE ? ESCAPE '\\'
                OR LOWER(COALESCE(mv.version_label, '')) LIKE ? ESCAPE '\\'
                OR LOWER(COALESCE(mv.implementation_kind, '')) LIKE ? ESCAPE '\\'
              )
            ORDER BY ms.created_at DESC, ms.id ASC, mv.created_at DESC, mv.id ASC
            LIMIT ?
            """,
            (workspace_id, pattern, pattern, pattern, pattern, pattern, _MODEL_SEARCH_MATCH_LIMIT),
        ).fetchall()

    grouped: dict[str, ModelDossierIndexItem] = {}
    for row in rows:
        model_spec_id = str(row["model_spec_id"])
        item = grouped.get(model_spec_id)
        if item is None:
            item = ModelDossierIndexItem(
                model_spec_id=model_spec_id,
                title=str(row["title"]),
                engineering_question=str(row["engineering_question"]),
                scope=row["scope"],
                versions=[],
            )
            grouped[model_spec_id] = item
        if row["model_version_id"] is not None:
            item.versions.append(
                ModelDossierVersionIdentity(
                    model_spec_id=model_spec_id,
                    model_version_id=str(row["model_version_id"]),
                    version_label=row["version_label"],
                    implementation_kind=row["implementation_kind"],
                    status=row["version_status"],
                    created_at=row["version_created_at"],
                    input_contract_digest=row["input_contract_sha256"],
                )
            )
    return list(grouped.values())
