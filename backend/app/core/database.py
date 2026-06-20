import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from app.core.paths import build_paths
from app.core.schema import (
    SCHEMA_INDEX_STATEMENTS,
    SCHEMA_MIGRATION_RECORDS,
    SCHEMA_MIGRATION_STATEMENTS,
    SCHEMA_STATEMENTS,
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
    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> DatabaseInfo:
    with open_sqlite_connection() as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        for statement in SCHEMA_MIGRATION_STATEMENTS:
            try:
                connection.execute(statement)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
        for statement in SCHEMA_INDEX_STATEMENTS:
            connection.execute(statement)
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
        "simulation_runs",
        "runner_jobs",
        "run_logs",
        "run_artifacts",
        "decisions",
        "ai_settings",
    }
    with open_sqlite_connection() as connection:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    existing_tables = {row["name"] for row in rows}
    return required_tables.issubset(existing_tables)


def get_database_info() -> DatabaseInfo:
    database_path = get_database_path()
    initialized = is_database_initialized()
    schema_current = get_current_schema_migration() if initialized else _empty_schema_migration()
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
        row = connection.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()
    return int(row["count"])


def _record_schema_migrations(connection: sqlite3.Connection) -> None:
    now = utc_now()
    for record in SCHEMA_MIGRATION_RECORDS:
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
