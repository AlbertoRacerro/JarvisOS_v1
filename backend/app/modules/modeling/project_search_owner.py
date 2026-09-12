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
    return value.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _register_casefold(connection) -> None:
    connection.create_function(
        "JARVIS_CASEFOLD",
        1,
        lambda value: "" if value is None else str(value).casefold(),
        deterministic=True,
    )


def search_context_records_literal(
    workspace_id: str,
    *,
    kinds: list[str],
    statuses_by_kind: Mapping[str, Sequence[str] | None],
    query: str,
    max_matches_per_kind: int,
) -> dict[str, list[Any]]:
    """Read bounded literal matches from canonical Project Basis owner tables.

    Eligibility and literal match tier are applied before the per-kind bound so
    retired/newer contains rows cannot hide an eligible exact or prefix match.
    """
    normalized_query = query.casefold()
    escaped_query = _escape_like_literal(query)
    contains_pattern = f"%{escaped_query}%"
    prefix_pattern = f"{escaped_query}%"
    results: dict[str, list[Any]] = {}
    with open_sqlite_connection() as connection:
        _register_casefold(connection)
        workspace = connection.execute("SELECT 1 FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
        if workspace is None:
            raise ValueError("Workspace not found.")

        for kind in kinds:
            table = _TABLES[kind]
            values: list[object] = [workspace_id]
            clauses = ["workspace_id = ?"]
            if kind == "parameter":
                clauses.append("lifecycle_state = 'active'")
            elif kind == "decision":
                clauses.append("basis_lifecycle_state = 'active'")

            statuses = statuses_by_kind[kind]
            if statuses is not None:
                if not statuses:
                    results[kind] = []
                    continue
                placeholders = ", ".join("?" for _ in statuses)
                clauses.append(f"{_STATUS_COLUMNS[kind]} IN ({placeholders})")
                values.extend(statuses)

            text_columns = _TEXT_COLUMNS[kind]
            literal_terms = []
            for column in text_columns:
                literal_terms.append(f"JARVIS_CASEFOLD(COALESCE({column}, '')) LIKE ? ESCAPE '\\'")
                values.append(contains_pattern)
            clauses.append("(" + " OR ".join(literal_terms) + ")")

            exact_terms = [f"JARVIS_CASEFOLD(COALESCE({column}, '')) = ?" for column in text_columns]
            prefix_terms = [
                f"JARVIS_CASEFOLD(COALESCE({column}, '')) LIKE ? ESCAPE '\\'" for column in text_columns
            ]
            order_values: list[object] = [normalized_query] * len(text_columns)
            order_values.extend([prefix_pattern] * len(text_columns))
            match_tier_order = (
                "CASE "
                f"WHEN ({' OR '.join(exact_terms)}) THEN 0 "
                f"WHEN ({' OR '.join(prefix_terms)}) THEN 1 "
                "ELSE 2 END"
            )

            rows = connection.execute(
                f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} "
                f"ORDER BY {match_tier_order}, id ASC LIMIT ?",
                (*values, *order_values, max_matches_per_kind),
            ).fetchall()
            results[kind] = rows_to_models(rows, _MODELS[kind])
    return results
