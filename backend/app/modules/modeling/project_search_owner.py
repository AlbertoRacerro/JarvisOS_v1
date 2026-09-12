from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.core.database import open_sqlite_connection
from app.core.repository import rows_to_models
from app.modules.modeling.models import AssumptionRead, DecisionRead, ParameterRead, RequirementRead

_TABLES = {
    "decision": "decisions",
    "assumption": "assumptions",
    "parameter": "parameters",
    "requirement": "requirements",
}
_STATUS_COLUMNS = {
    "decision": "status",
    "assumption": "status",
    "parameter": "value_status",
    "requirement": "status",
}
_MODELS = {
    "decision": DecisionRead,
    "assumption": AssumptionRead,
    "parameter": ParameterRead,
    "requirement": RequirementRead,
}
_TEXT_COLUMNS = {
    "decision": ("title", "decision_text", "rationale", "notes"),
    "assumption": ("statement", "notes"),
    "parameter": ("name", "symbol", "notes"),
    "requirement": ("statement", "rationale", "notes"),
}


def _escape_like_literal(value: str) -> str:
    return value.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_context_records_literal(
    workspace_id: str,
    *,
    kinds: list[str],
    statuses_by_kind: Mapping[str, Sequence[str] | None],
    query: str,
    max_matches_per_kind: int,
) -> dict[str, list[Any]]:
    """Read bounded literal matches from canonical Project Basis owner tables.

    This is a read-only owner adapter for Project Search. It deliberately bounds
    matching rows rather than total owner cardinality, so a large workspace does
    not make unrelated literal searches unavailable.
    """
    pattern = f"%{_escape_like_literal(query)}%"
    results: dict[str, list[Any]] = {}
    with open_sqlite_connection() as connection:
        workspace = connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise ValueError("Workspace not found.")

        for kind in kinds:
            table = _TABLES[kind]
            values: list[object] = [workspace_id]
            clauses = ["workspace_id = ?"]
            if kind == "parameter":
                clauses.append("lifecycle_state = 'active'")

            statuses = statuses_by_kind[kind]
            if statuses is not None:
                if not statuses:
                    results[kind] = []
                    continue
                placeholders = ", ".join("?" for _ in statuses)
                clauses.append(f"{_STATUS_COLUMNS[kind]} IN ({placeholders})")
                values.extend(statuses)

            literal_terms = []
            for column in _TEXT_COLUMNS[kind]:
                literal_terms.append(f"LOWER(COALESCE({column}, '')) LIKE ? ESCAPE '\\'")
                values.append(pattern)
            clauses.append("(" + " OR ".join(literal_terms) + ")")

            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} "
                "ORDER BY updated_at DESC, id ASC LIMIT ?",
                (*values, max_matches_per_kind),
            ).fetchall()
            results[kind] = rows_to_models(rows, _MODELS[kind])
    return results
