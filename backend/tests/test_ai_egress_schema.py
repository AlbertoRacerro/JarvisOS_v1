import sqlite3

import pytest

from app.core.database import (
    count_schema_migrations,
    get_current_schema_migration,
    initialize_database,
    open_sqlite_connection,
)
from app.core.egress_schema import EGRESS_SCHEMA_MIGRATION_ID
from app.core.schema import (
    CURRENT_SCHEMA_MIGRATION_ID,
    SCHEMA_STATEMENTS,
)
from app.core.sensitivity_schema import SENSITIVITY_SCHEMA_STATEMENTS
from app.core.token_flow_schema import TOKEN_FLOW_SCHEMA_MIGRATION_ID

EXPECTED_EGRESS_TABLES = {
    "egress_prompt_derivatives",
    "egress_packets",
    "egress_decisions",
    "egress_budget_reservations",
    "egress_confirmation_tickets",
    "egress_attempts",
    "sanitizer_audit_items",
    "workspace_egress_policy",
}
EXPECTED_AI_JOB_USAGE_SOURCE_COLUMN = "usage_source"
EXPECTED_SANITIZER_PROVENANCE_COLUMNS = {
    "sanitizer_kind",
    "sanitizer_version",
    "sanitizer_config_digest",
    "sanitizer_ai_job_id",
    "approval_source",
    "auto_approved",
}


def test_egress_schema_remains_recorded_after_token_flow_migration():
    first = initialize_database()
    second = initialize_database()

    assert first.ready is True
    assert second.ready is True
    assert get_current_schema_migration().migration_id == CURRENT_SCHEMA_MIGRATION_ID
    assert count_schema_migrations() == 18

    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        token_flow_migration = connection.execute(
            "SELECT status FROM schema_migrations WHERE migration_id = ?",
            (TOKEN_FLOW_SCHEMA_MIGRATION_ID,),
        ).fetchone()
        egress_migration = connection.execute(
            """
            SELECT status FROM schema_migrations WHERE migration_id = ?
            """,
            (EGRESS_SCHEMA_MIGRATION_ID,),
        ).fetchone()
    tables = {row["name"] for row in rows}
    assert EXPECTED_EGRESS_TABLES.issubset(tables)
    assert token_flow_migration is not None
    assert token_flow_migration["status"] == "applied"
    assert egress_migration is not None
    assert egress_migration["status"] == "applied"


def test_ai_job_usage_source_column_exists_and_rejects_invalid_values():
    initialize_database()
    initialize_database()

    with open_sqlite_connection() as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(ai_jobs)").fetchall()}
        assert EXPECTED_AI_JOB_USAGE_SOURCE_COLUMN in columns
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO ai_jobs (
                    id, created_at, status, task_kind, route_reason_json, usage_source
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "invalid-usage-source",
                    "2026-07-14T00:00:00+00:00",
                    "completed",
                    "test",
                    "{}",
                    "guess",
                ),
            )


def test_sanitizer_provenance_columns_exist_and_reject_invalid_auto_approval():
    initialize_database()
    initialize_database()

    with open_sqlite_connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(sanitized_derivatives)").fetchall()
        }
        assert EXPECTED_SANITIZER_PROVENANCE_COLUMNS.issubset(columns)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO sanitized_derivatives (
                    id, workspace_id, source_kind, source_id, sanitizer_kind,
                    sanitizer_version, sanitizer_config_digest, sanitized_text,
                    sanitized_sha256, sensitivity_label, approval_source,
                    auto_approved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "invalid-auto-approval",
                    "workspace",
                    "artifact",
                    "artifact-1",
                    "deterministic",
                    "1",
                    "sha256:config",
                    "safe",
                    "sha256:text",
                    "internal",
                    "operator",
                    2,
                    "2026-07-14T00:00:00+00:00",
                ),
            )


def test_sensitivity_schema_is_idempotent_under_current_bootstrap():
    initialize_database()
    initialize_database()

    with open_sqlite_connection() as connection:
        for statement in SENSITIVITY_SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
