from __future__ import annotations

from app.core.database import initialize_database, open_sqlite_connection
from app.modules.modeling.project_search_owner import search_context_records_literal


def _insert_workspace(connection, workspace_id: str) -> None:
    connection.execute(
        "INSERT INTO workspaces (id, name, slug, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (workspace_id, workspace_id, workspace_id, "2026-09-12T00:00:00Z", "2026-09-12T00:00:00Z"),
    )


def test_owner_ranks_exact_before_contains_before_applying_match_bound() -> None:
    initialize_database()
    workspace_id = "ws-search-rank-before-cap"
    now = "2026-09-12T00:00:00Z"
    with open_sqlite_connection() as connection:
        _insert_workspace(connection, workspace_id)
        connection.executemany(
            "INSERT INTO requirements (id, workspace_id, statement, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (f"a-contains-{index:03d}", workspace_id, f"noise needle tail {index}", "active", now, now)
                for index in range(101)
            ],
        )
        connection.execute(
            "INSERT INTO requirements (id, workspace_id, statement, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("z-exact", workspace_id, "needle", "active", now, now),
        )
        connection.commit()

    selected = search_context_records_literal(
        workspace_id,
        kinds=["requirement"],
        statuses_by_kind={"requirement": ["active"]},
        query="needle",
        max_matches_per_kind=101,
    )

    assert selected["requirement"][0].id == "z-exact"
    assert any(record.id == "z-exact" for record in selected["requirement"])


def test_owner_filters_retired_decisions_before_applying_match_bound() -> None:
    initialize_database()
    workspace_id = "ws-search-decision-lifecycle-before-cap"
    now = "2026-09-12T00:00:00Z"
    with open_sqlite_connection() as connection:
        _insert_workspace(connection, workspace_id)
        connection.executemany(
            "INSERT INTO decisions (id, workspace_id, title, status, basis_lifecycle_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    f"a-retired-{index:03d}",
                    workspace_id,
                    f"noise needle tail {index}",
                    "accepted",
                    "retired",
                    now,
                    now,
                )
                for index in range(101)
            ],
        )
        connection.execute(
            "INSERT INTO decisions (id, workspace_id, title, status, basis_lifecycle_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("z-active-exact", workspace_id, "needle", "accepted", "active", now, now),
        )
        connection.commit()

    selected = search_context_records_literal(
        workspace_id,
        kinds=["decision"],
        statuses_by_kind={"decision": None},
        query="needle",
        max_matches_per_kind=101,
    )

    assert [record.id for record in selected["decision"]] == ["z-active-exact"]
