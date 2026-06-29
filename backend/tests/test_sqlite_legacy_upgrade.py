"""Stage 3-min — Characterize SQLite policy-mode legacy upgrade behavior.

Test-only. Protects local SQLite DBs that predate the `policy_mode` column in
`ai_settings`. Characterizes the CURRENT upgrade path (re-running
`initialize_database()`); it does NOT change schema, migrations, or runtime.

Scope is intentionally narrow:
  - Test 1: initialize_database() is idempotent on a fresh DB.
  - Test 2: a legacy ai_settings without policy_mode is upgraded in place.

Out of scope (later slices): global fresh-vs-upgraded schema diff, index diff,
dead-column detection (e.g. scaleway_token_cap / scaleway_tokens_month_to_date
exist in the CREATE but in no migration), binary .db fixtures.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

# Legacy ai_settings = the current CREATE TABLE ai_settings, verbatim, MINUS the
# policy_mode column. Built with explicit SQL on purpose: it must NOT be derived
# from SCHEMA_STATEMENTS, so the test genuinely exercises the 0003 migration that
# adds policy_mode. A non-default sentinel value is inserted to prove the
# pre-existing row survives the upgrade.
LEGACY_AI_SETTINGS_SQL = """
CREATE TABLE ai_settings (
    id TEXT PRIMARY KEY,
    monthly_api_budget_usd REAL NOT NULL DEFAULT 0,
    api_spend_month_to_date_usd REAL NOT NULL DEFAULT 0,
    paid_ai_enabled INTEGER NOT NULL DEFAULT 0,
    default_ai_provider TEXT NOT NULL DEFAULT 'fake',
    default_ai_model TEXT NOT NULL DEFAULT 'fake-modeling-draft-v1',
    provider_mode TEXT NOT NULL DEFAULT 'fake',
    use_fake_provider_when_budget_zero INTEGER NOT NULL DEFAULT 1,
    scaleway_enabled INTEGER NOT NULL DEFAULT 0,
    scaleway_token_cap INTEGER NOT NULL DEFAULT 0,
    scaleway_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
    scaleway_smoke_test_enabled INTEGER NOT NULL DEFAULT 0,
    scaleway_live_smoke_test_enabled INTEGER NOT NULL DEFAULT 0,
    scaleway_monthly_token_cap INTEGER NOT NULL DEFAULT 500000,
    scaleway_hard_stop_token_cap INTEGER NOT NULL DEFAULT 800000,
    scaleway_free_tier_reference_tokens INTEGER NOT NULL DEFAULT 1000000,
    scaleway_input_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
    scaleway_output_tokens_month_to_date INTEGER NOT NULL DEFAULT 0,
    smoke_test_mode_enabled INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
)
"""


def _isolate_data_root(monkeypatch, tmp_path: Path) -> None:
    """Point the DB path at an isolated tmp root and clear the settings cache.

    Consistent with the existing DB-test pattern; explicit even though the
    autouse Stage 0 fixture also isolates the root.
    """
    monkeypatch.setenv("JARVISOS_DATA_ROOT", str(tmp_path / "jarvisos-legacy"))
    from app.core.config import get_settings

    get_settings.cache_clear()


def _non_internal_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def test_initialize_database_is_idempotent_on_fresh_db(monkeypatch, tmp_path) -> None:
    """Running initialize_database() twice on a fresh DB is a no-op for the
    table set. This anchors the whole upgrade model: the CREATE statements are
    IF NOT EXISTS and the ALTER migrations swallow duplicate-column errors."""
    _isolate_data_root(monkeypatch, tmp_path)
    from app.core.database import initialize_database, open_sqlite_connection

    initialize_database()
    with open_sqlite_connection() as connection:
        tables_after_first = _non_internal_tables(connection)

    initialize_database()
    with open_sqlite_connection() as connection:
        tables_after_second = _non_internal_tables(connection)

    assert tables_after_first == tables_after_second
    assert "ai_settings" in tables_after_first
    # Core app tables read from SCHEMA_STATEMENTS, not guessed.
    assert {"workspaces", "events", "model_specs"}.issubset(tables_after_first)


def test_legacy_ai_settings_without_policy_mode_is_upgraded(monkeypatch, tmp_path) -> None:
    """A legacy ai_settings (no policy_mode) with a pre-existing row is upgraded
    by initialize_database(): policy_mode is added, the old row survives, and the
    new column is populated with the migration default ('FAST_DEV')."""
    _isolate_data_root(monkeypatch, tmp_path)
    from app.core.database import initialize_database, open_sqlite_connection

    # Build the legacy DB with explicit SQL (NOT the current schema).
    with open_sqlite_connection() as connection:
        connection.execute(LEGACY_AI_SETTINGS_SQL)
        connection.execute(
            "INSERT INTO ai_settings (id, monthly_api_budget_usd, updated_at) VALUES (?, ?, ?)",
            ("legacy-singleton", 42.0, "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()
        assert "policy_mode" not in _column_names(connection, "ai_settings")

    # Run the real upgrade path.
    initialize_database()

    with open_sqlite_connection() as connection:
        columns = _column_names(connection, "ai_settings")
        rows = connection.execute(
            "SELECT id, monthly_api_budget_usd, policy_mode FROM ai_settings WHERE id = ?",
            ("legacy-singleton",),
        ).fetchall()

    assert "policy_mode" in columns
    assert len(rows) == 1
    row = rows[0]
    # The pre-existing row survived with its sentinel data intact.
    assert row["monthly_api_budget_usd"] == 42.0
    # CURRENT BEHAVIOR: the migration default populates the legacy row.
    assert row["policy_mode"] == "FAST_DEV"

    # A second initialize_database() after upgrade is still a no-op.
    initialize_database()
    with open_sqlite_connection() as connection:
        assert "policy_mode" in _column_names(connection, "ai_settings")
        count = connection.execute("SELECT COUNT(*) AS c FROM ai_settings").fetchone()["c"]
    assert count == 1


# ---------------------------------------------------------------------------
# Stage 3-full — fresh-vs-legacy drift for the two columns that live in the
# current CREATE TABLE ai_settings but in NO migration statement.
# ---------------------------------------------------------------------------

# Legacy ai_settings that predates BOTH the policy_mode migration AND the two
# "dead" columns scaleway_token_cap / scaleway_tokens_month_to_date. Because
# those two columns are in the current CREATE but in no ALTER migration, a DB
# created before they were added to CREATE can never receive them via upgrade.
LEGACY_AI_SETTINGS_PRE_SCALEWAY_SQL = """
CREATE TABLE ai_settings (
    id TEXT PRIMARY KEY,
    monthly_api_budget_usd REAL NOT NULL DEFAULT 0,
    api_spend_month_to_date_usd REAL NOT NULL DEFAULT 0,
    paid_ai_enabled INTEGER NOT NULL DEFAULT 0,
    default_ai_provider TEXT NOT NULL DEFAULT 'fake',
    default_ai_model TEXT NOT NULL DEFAULT 'fake-modeling-draft-v1',
    provider_mode TEXT NOT NULL DEFAULT 'fake',
    use_fake_provider_when_budget_zero INTEGER NOT NULL DEFAULT 1,
    scaleway_enabled INTEGER NOT NULL DEFAULT 0,
    smoke_test_mode_enabled INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
)
"""

DRIFT_COLUMNS = ("scaleway_token_cap", "scaleway_tokens_month_to_date")


def _build_legacy_pre_scaleway_db(connection: sqlite3.Connection) -> None:
    connection.execute(LEGACY_AI_SETTINGS_PRE_SCALEWAY_SQL)
    connection.execute(
        "INSERT INTO ai_settings (id, monthly_api_budget_usd, updated_at) VALUES (?, ?, ?)",
        ("legacy-singleton", 7.0, "2026-01-01T00:00:00+00:00"),
    )
    connection.commit()


def test_fresh_db_ai_settings_has_scaleway_drift_columns(monkeypatch, tmp_path) -> None:
    """A fresh DB built by the current CREATE has both columns — they ARE part of
    the intended current schema."""
    _isolate_data_root(monkeypatch, tmp_path)
    from app.core.database import initialize_database, open_sqlite_connection

    initialize_database()
    with open_sqlite_connection() as connection:
        columns = _column_names(connection, "ai_settings")

    for column in DRIFT_COLUMNS:
        assert column in columns


def test_legacy_upgrade_still_lacks_scaleway_drift_columns(monkeypatch, tmp_path) -> None:
    """CURRENT BEHAVIOR (drift, not desired): a legacy ai_settings that predates
    these columns is upgraded by initialize_database() — policy_mode and the
    migration-listed scaleway columns appear — but scaleway_token_cap and
    scaleway_tokens_month_to_date are in NO migration, so they stay missing.
    A future migration-repair slice is expected to change this characterization."""
    _isolate_data_root(monkeypatch, tmp_path)
    from app.core.database import initialize_database, open_sqlite_connection

    with open_sqlite_connection() as connection:
        _build_legacy_pre_scaleway_db(connection)
        before = _column_names(connection, "ai_settings")
    assert "policy_mode" not in before
    for column in DRIFT_COLUMNS:
        assert column not in before

    initialize_database()

    with open_sqlite_connection() as connection:
        after = _column_names(connection, "ai_settings")
        rows = connection.execute(
            "SELECT id, monthly_api_budget_usd FROM ai_settings WHERE id = ?",
            ("legacy-singleton",),
        ).fetchall()

    # The migration path DID add policy_mode and the migration-listed scaleway columns...
    assert "policy_mode" in after
    assert "scaleway_input_tokens_month_to_date" in after
    # ...but the two columns that no migration adds stay missing.
    for column in DRIFT_COLUMNS:
        assert column not in after
    # The pre-existing row survived.
    assert len(rows) == 1
    assert rows[0]["monthly_api_budget_usd"] == 7.0

    # Second init does not retroactively add them either.
    initialize_database()
    with open_sqlite_connection() as connection:
        assert _column_names(connection, "ai_settings").isdisjoint(DRIFT_COLUMNS)


def test_legacy_upgrade_breaks_ensure_ai_settings_current_behavior(monkeypatch, tmp_path) -> None:
    """CURRENT BEHAVIOR / latent breakage: the drift is NOT benign. ensure_ai_settings()
    runs an INSERT naming scaleway_token_cap / scaleway_tokens_month_to_date. SQLite
    resolves column names at compile time, so on a legacy DB upgraded only through
    initialize_database() (which never adds those columns) that INSERT fails even
    with OR IGNORE — bootstrap of a legacy DB cannot complete. This locks the real
    severity ahead of a repair slice; it does NOT fix it."""
    _isolate_data_root(monkeypatch, tmp_path)
    from app.core.database import initialize_database, open_sqlite_connection
    from app.modules.ai.settings import ensure_ai_settings

    with open_sqlite_connection() as connection:
        _build_legacy_pre_scaleway_db(connection)
    initialize_database()

    with pytest.raises(sqlite3.OperationalError) as excinfo:
        ensure_ai_settings()
    message = str(excinfo.value).lower()
    assert "scaleway_token_cap" in message or "no column" in message
