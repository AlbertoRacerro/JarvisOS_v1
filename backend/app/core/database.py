import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from app.core.egress_schema import (
    EGRESS_SCHEMA_INDEX_STATEMENTS,
    EGRESS_SCHEMA_MIGRATION_RECORD,
    EGRESS_SCHEMA_MIGRATION_STATEMENTS,
    EGRESS_SCHEMA_STATEMENTS,
)
from app.core.paths import build_paths
from app.core.schema import (
    CONTEXT_RECORDS_FTS_BACKFILL_STATEMENT,
    SCHEMA_FTS_STATEMENTS,
    SCHEMA_INDEX_STATEMENTS,
    SCHEMA_MIGRATION_RECORDS,
    SCHEMA_MIGRATION_STATEMENTS,
    SCHEMA_STATEMENTS,
)
from app.core.sensitivity_schema import (
    SENSITIVITY_SCHEMA_INDEX_STATEMENTS,
    SENSITIVITY_SCHEMA_STATEMENTS,
)
from app.core.token_flow_schema import (
    TOKEN_FLOW_SCHEMA_INDEX_STATEMENTS,
    TOKEN_FLOW_SCHEMA_MIGRATION_RECORD,
    TOKEN_FLOW_SCHEMA_MIGRATION_STATEMENTS,
    TOKEN_FLOW_SCHEMA_STATEMENTS,
)
from app.modules.events.service import utc_now


@dataclass(frozen=True)
class SchemaMigrationInfo:
    migration_id: str | None
    name: str | None
    applied_at: str | None
    checksum: str | None
    status: str | None


@dataclass(frozen=True)
class DatabaseInfo:
    engine: str
    database_file: str
    configured: bool
    ready: bool
    initialized: bool
    bootstrap_required: bool
    bootstrap_action: str | None
    schema_current: SchemaMigrationInfo
    applied_migration_count: int


def get_database_path() -> Path:
    return build_paths().database_file


@contextmanager
def open_sqlite_connection() -> Iterator[sqlite3.Connection]:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    # Wait instead of failing immediately when another writer holds the lock,
    # and use WAL so readers and a writer do not block each other. Both reduce
    # spurious "database is locked" errors under concurrent requests.
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> DatabaseInfo:
    with open_sqlite_connection() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in SENSITIVITY_SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in EGRESS_SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in TOKEN_FLOW_SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in [
            *SCHEMA_MIGRATION_STATEMENTS,
            *EGRESS_SCHEMA_MIGRATION_STATEMENTS,
            *TOKEN_FLOW_SCHEMA_MIGRATION_STATEMENTS,
        ]:
            try:
                connection.execute(statement)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        for statement in SCHEMA_INDEX_STATEMENTS:
            connection.execute(statement)
        for statement in SENSITIVITY_SCHEMA_INDEX_STATEMENTS:
            connection.execute(statement)
        for statement in EGRESS_SCHEMA_INDEX_STATEMENTS:
            connection.execute(statement)
        for statement in TOKEN_FLOW_SCHEMA_INDEX_STATEMENTS:
            connection.execute(statement)
        if _sqlite_fts5_available(connection):
            for statement in SCHEMA_FTS_STATEMENTS:
                connection.execute(statement)
            connection.execute("DELETE FROM context_records_fts")
            connection.execute(CONTEXT_RECORDS_FTS_BACKFILL_STATEMENT)
        _record_schema_migrations(connection)
        connection.commit()
    return get_database_info()


def is_database_initialized() -> bool:
    database_path = get_database_path()
    if not database_path.exists():
        return False

    required_tables = {
        "schema_migrations",
        "workspaces",
        "events",
        "model_specs",
        "assumptions",
        "parameters",
        "requirements",
        "simulation_runs",
        "freshness_invalidations",
        "freshness_marks",
        "runner_jobs",
        "run_logs",
        "run_artifacts",
        "decisions",
        "ai_jobs",
        "ai_settings",
        "ai_flows",
        "ai_flow_segments",
        "sensitivity_labels",
        "sanitized_derivatives",
        "egress_prompt_derivatives",
        "egress_packets",
        "egress_decisions",
        "egress_budget_reservations",
        "egress_confirmation_tickets",
        "egress_attempts",
        "sanitizer_audit_items",
        "workspace_egress_policy",
    }
    with open_sqlite_connection() as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    existing_tables = {row["name"] for row in rows}
    return required_tables.issubset(existing_tables)


def get_database_info() -> DatabaseInfo:
    database_path = get_database_path()
    initialized = is_database_initialized()
    schema_current = (
        get_current_schema_migration() if initialized else _empty_schema_migration()
    )
    applied_migration_count = count_schema_migrations() if initialized else 0
    return DatabaseInfo(
        engine="sqlite",
        database_file=str(database_path),
        configured=True,
        ready=database_path.parent.exists() and initialized,
        initialized=initialized,
        bootstrap_required=not initialized,
        bootstrap_action=None if initialized else "POST /system/initialize",
        schema_current=schema_current,
        applied_migration_count=applied_migration_count,
    )


def get_current_schema_migration() -> SchemaMigrationInfo:
    database_path = get_database_path()
    if not database_path.exists():
        return _empty_schema_migration()
    with open_sqlite_connection() as connection:
        has_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if has_table is None:
            return _empty_schema_migration()
        row = connection.execute(
            """
            SELECT migration_id, name, applied_at, checksum, status
            FROM schema_migrations
            ORDER BY migration_id DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return _empty_schema_migration()
    return SchemaMigrationInfo(**dict(row))


def count_schema_migrations() -> int:
    database_path = get_database_path()
    if not database_path.exists():
        return 0
    with open_sqlite_connection() as connection:
        has_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if has_table is None:
            return 0
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM schema_migrations"
        ).fetchone()
    return int(row["count"])


def _record_schema_migrations(connection: sqlite3.Connection) -> None:
    now = utc_now()
    records = [
        *SCHEMA_MIGRATION_RECORDS,
        EGRESS_SCHEMA_MIGRATION_RECORD,
        TOKEN_FLOW_SCHEMA_MIGRATION_RECORD,
    ]
    for record in records:
        connection.execute(
            """
            INSERT INTO schema_migrations (migration_id, name, applied_at, checksum, status)
            VALUES (?, ?, ?, ?, 'applied')
            ON CONFLICT(migration_id) DO UPDATE SET
                name = excluded.name,
                checksum = excluded.checksum,
                status = 'applied'
            """,
            (record["migration_id"], record["name"], now, record["checksum"]),
        )


def _empty_schema_migration() -> SchemaMigrationInfo:
    return SchemaMigrationInfo(
        migration_id=None,
        name=None,
        applied_at=None,
        checksum=None,
        status=None,
    )


def _sqlite_fts5_available(connection: sqlite3.Connection) -> bool:
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS temp.jarvisos_fts5_probe USING fts5(x)"
        )
        connection.execute("DROP TABLE IF EXISTS temp.jarvisos_fts5_probe")
    except sqlite3.OperationalError:
        return False
    return True
