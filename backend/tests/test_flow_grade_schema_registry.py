from __future__ import annotations

from app.core.database import (
    count_schema_migrations,
    get_current_schema_migration,
    initialize_database,
    open_sqlite_connection,
)
from app.core.grade_schema import GRADE_SCHEMA_MIGRATION_ID
from app.core.schema import CURRENT_SCHEMA_MIGRATION_ID


def test_grade_schema_is_the_current_registered_migration() -> None:
    first = initialize_database()
    second = initialize_database()

    assert first.ready is True
    assert second.ready is True
    assert CURRENT_SCHEMA_MIGRATION_ID == GRADE_SCHEMA_MIGRATION_ID
    assert get_current_schema_migration().migration_id == GRADE_SCHEMA_MIGRATION_ID
    assert count_schema_migrations() == 14

    with open_sqlite_connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"ai_flow_grade_subjects", "ai_flow_grade_events"} <= tables
