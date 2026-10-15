# 028 — Additive migration discipline

State: **accepted and ready**. Written under the 2026-10-15 maintainer queue directive ("continue until all the queue is done") and the [queue disposition record](../implementation/queue-disposition-2026-10-15.md). Reviewed against master `af053d31`.

- **Hard dependencies:** none.
- **This is a documentation-and-test slice.** It writes down the migration policy the code already follows and adds tests that hold it. It changes no table, column, index or runtime path, and it is not a migration-framework rewrite.

## Fresh evidence (master `af053d31`)

- **One initializer.** `initialize_database()` (`backend/app/core/database.py:156`) runs every owner's `CREATE TABLE IF NOT EXISTS` statements. Then it runs the additive migration lists (`SCHEMA_MIGRATION_STATEMENTS`, `EGRESS_`, `TOKEN_FLOW_`, `RUNNER_CREATE_REQUEST_`, `PROJECT_KNOWLEDGE_`, `RELAY_GATEWAY_`) and tolerates only `duplicate column name` (`:186-197`). Next come the guarded backfill `_ensure_parameter_lifecycle_schema` (`:402`), the index statements and the FTS rebuild. Last, `_record_schema_migrations` (`:370`) inserts each record once.
- **Records.** Each owner declares a `*_MIGRATION_RECORD` with `migration_id`, `name` and `checksum` (`schema.py:28-78`, `literature_schema.py:2`, `database.py:95` and others). The rows land in `schema_migrations` (`schema.py:86`).
- **Upgrade coverage today.** `backend/tests/test_sqlite_legacy_upgrade.py` covers idempotence and one legacy column (`ai_settings.policy_mode`). Its docstring names the global fresh-versus-upgraded diff as out of scope for that test. No document states the policy.
- **SQLite 3.45** is in use, so tests may build a legacy shape with `ALTER TABLE … DROP COLUMN`.

## Decision

1. **Policy document.** `docs/MIGRATIONS.md` states the rules the code already follows:
   - Schema changes are additive: `CREATE … IF NOT EXISTS`, and `ALTER TABLE … ADD COLUMN` with a default or nullable type.
   - An added column appears both in its owner's `CREATE TABLE` (fresh shape) and in a migration list (upgrade shape).
   - Data backfills are idempotent and guarded by a shape check.
   - Every change carries a `*_MIGRATION_RECORD` with a unique `migration_id`.
   - Renames, drops and type changes need their own accepted spec with a backup and restore path.
   - The document says where to add each piece and which test enforces it.
2. **Fresh equals upgraded.** A test builds a fresh database. It makes a legacy copy by dropping every column added by a migration statement (indexes on those columns are dropped first), re-runs `initialize_database()` on it, and asserts both databases have the same tables, columns (name, type, not-null, default) and indexes. A column present in a migration but missing from its owner's `CREATE` fails the test, and so does the reverse case of a migration that cannot be re-applied.
3. **Additive-only lint.** A test parses every migration statement list. It asserts each statement is `ALTER TABLE <t> ADD COLUMN …` or `CREATE … IF NOT EXISTS`, that none contains `DROP`, `RENAME` or a column type change, and that every `migration_id` across all records is unique.
4. **Idempotence of the whole initializer.** Two consecutive runs leave identical `sqlite_master` and `schema_migrations` row counts.
5. **Known debt is recorded, not fixed.** Columns present in a `CREATE` but in no migration (for example `scaleway_token_cap`) are listed in the document as legacy, and an explicit allowlist keeps the test honest. They are not removed.

## Non-goals

- No migration framework, Alembic or version runner.
- No schema change, column removal or data rewrite.
- No change to runtime startup order.

## Acceptance

- `docs/MIGRATIONS.md` exists and matches the code paths cited above.
- `backend/tests/test_migration_discipline.py` holds criteria 2–4 and passes on master. Deleting an added column from its owner's `CREATE`, or adding a `DROP` statement to a migration list, makes it fail. Both negative cases are demonstrated in the PR evidence.
- The full backend suite in a clean environment, Ruff, the typecheck ratchet and contract checks pass at the exact head.
