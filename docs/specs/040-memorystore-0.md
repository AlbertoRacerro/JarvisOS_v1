# 040 — MEMORYSTORE-0: AI-proposal write boundary for existing engineering records

Status: ready
Depends on: none

## Goal

After this slice, `decisions`, `assumptions`, and `parameters` rows can carry
provenance for AI-originated proposals (`origin`,
`source_ai_job_id`, `promoted_at`), and a new `backend/app/modules/memory/`
module is the only write path that creates `origin='ai_proposed'` rows and the
only path that promotes or rejects any record's proposal lifecycle. No new
tables, no AI calls, no retrieval, no UI. This is `MEMORYSTORE-0` from
`docs/strategy/JARVISOS_MEMORY_CONTEXT_DESIGN.md`, narrowed to a single
write-boundary slice over three of those tables (requirements are excluded —
see Review resolutions).

## Why

`AGENTS.md` invariant 8 requires that AI/agent outputs remain proposals until
explicit user or deterministic-policy promotion. Today, nothing distinguishes a
human-entered `assumptions`/`parameters`/`decisions` row from an
AI-authored one, and there is no single place that enforces a status lifecycle
before a record counts as accepted. `docs/MEMORYSTORE_FACADE_DESIGN.md` and
`docs/strategy/JARVISOS_MEMORY_CONTEXT_DESIGN.md` already call for a single
future write boundary; this slice is the smallest reality-anchored step toward
it, reusing the existing tables instead of standing up new memory storage.

## Scope

In scope:
- Additive columns on `decisions`, `assumptions`, `parameters` (requirements
  excluded — see Review resolutions):
  `origin TEXT NOT NULL DEFAULT 'user'` (values: `'user'` | `'ai_proposed'` |
  `'calc'`; `'calc'` is valid only for parameter records created by the calc
  batch path — see Design constraints),
  `source_ai_job_id TEXT NULL` (references `ai_jobs.id`, no enforced FK
  constraint — see Design constraints), `promoted_at TEXT NULL`. Added via the
  existing `schema.py` `SCHEMA_MIGRATION_STATEMENTS` additive-ALTER pattern,
  with a new schema migration id/name bump.
- New module `backend/app/modules/memory/` (`models.py`, `service.py`,
  `routes.py`), following the existing module layout convention
  (`modeling`, `engineering`, `runner`).
- The memory service is the only write path that may insert a row with
  `origin='ai_proposed'` and the only path that may transition a record's
  status via promote/reject.
- A fixed status transition matrix enforced by the memory service:
  `proposed -> accepted`, `proposed -> rejected`, `accepted -> superseded`. No
  other transition is permitted. Promotion in this slice is manual only
  (operator-triggered HTTP call); there is no auto-promotion policy.
- Validation: when `origin='ai_proposed'`, `source_ai_job_id` is mandatory; the
  write is rejected otherwise.
- Endpoints:
  - `POST /memory/proposals` — typed payload (`record_kind` +
    kind-specific fields + `workspace_id`) creating a proposed-status record
    with `origin='ai_proposed'`.
  - `POST /memory/{record_kind}/{id}/promote`
  - `POST /memory/{record_kind}/{id}/reject`
  - `GET /memory/proposals?workspace_id=...&status=...` — list pending
    proposals.
- A per-table mapping (see Design constraints) from the facade's
  `proposed/accepted/rejected/superseded` vocabulary onto each table's existing
  `status` (and, for `parameters`, `value_status`) column, defined precisely
  enough to implement and test.

Out of scope (binding non-goals):
- No new storage engine, no new tables, no vector store, no FTS.
- No semantic retrieval and no retrieval-path changes of any kind.
- No auto-promotion policy or automatic status transitions of any kind.
- No chat integration.
- No frontend/UI work.
- No new dependencies.
- No AI model calls; nothing in this slice invokes `run_ai_task` or any
  provider adapter. `source_ai_job_id` only records that some prior AI job
  (created elsewhere) is the origin of the proposal.
- No change to the existing `modeling` module's create endpoints
  (`POST /workspaces/{id}/assumptions`, `/parameters`, `/requirements`,
  `/decisions`); they remain the manual/user path, continue to default
  `origin='user'`, and are not modified in this slice beyond whatever passive
  effect the additive columns have via `SELECT *`/`row_to_model` (see Design
  constraints and Open questions).
- No redesign of the 7-stage `raw_input -> ... -> canonical_state` lifecycle
  from `docs/MEMORYSTORE_FACADE_DESIGN.md` / `docs/STAGED_MEMORY_INTAKE.md`;
  this slice implements only the narrower 4-state
  `proposed/accepted/rejected/superseded` matrix specified here (see Open
  questions for the relationship between the two).

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing.

- `backend/app/core/schema.py` (additive columns on `decisions`, `assumptions`,
  `parameters`, `requirements`; new schema migration id/name constant per the
  existing `CURRENT_SCHEMA_MIGRATION_ID`/`_NAME` pattern; new entries in
  `SCHEMA_MIGRATION_STATEMENTS`)
- `backend/app/modules/memory/__init__.py` (new)
- `backend/app/modules/memory/models.py` (new — `MemoryProposalCreate`,
  per-kind payload variants, `MemoryRecordRead` or per-kind read models,
  promote/reject request/response shapes)
- `backend/app/modules/memory/service.py` (new — proposal creation, transition
  matrix enforcement, promote/reject, list-proposals query)
- `backend/app/modules/memory/routes.py` (new — the four endpoints in Scope)
- `backend/app/main.py` (register the new router, following the existing
  `include_router` pattern used for `modeling_router`/`runner_router`)
- `backend/app/modules/modeling/models.py` (reference only — confirms current
  per-table status vocabularies; not modified unless Design constraints below
  require otherwise)
- `backend/tests/test_domain_foundation.py` and/or a new
  `backend/tests/test_memory_store.py` (new tests; existing file already
  contains the legacy-upgrade pattern this slice's migration test should
  follow)

## Design constraints

- **Reuse, do not replace:** no new tables. `decisions`, `assumptions`,
  `parameters`, `requirements` remain the only storage for these record kinds.
- **Additive-only migration, existing pattern:** follow
  `backend/app/core/schema.py` exactly — add columns via new
  `SCHEMA_MIGRATION_STATEMENTS` entries (`ALTER TABLE ... ADD COLUMN ...`),
  each with a safe default, and bump `CURRENT_SCHEMA_MIGRATION_ID`/
  `CURRENT_SCHEMA_MIGRATION_NAME` (next id after `0004_...` is
  `0005_...`). `initialize_database()` already swallows
  `duplicate column name` errors, so re-running on an already-upgraded DB stays
  idempotent; do not change that swallow behavior.
- **No declared FK for `source_ai_job_id` (decided at expert review,
  2026-07-06):** SQLite cannot add a `FOREIGN KEY` constraint via
  `ALTER TABLE ADD COLUMN`, so `source_ai_job_id` ships as a plain nullable
  TEXT column. Referential integrity is enforced at the service level instead:
  on proposal creation the memory service verifies the referenced `ai_jobs`
  row exists (simple SELECT) and rejects the write otherwise. This is a
  deliberate, documented deviation from the `bluecad_attempts`
  CREATE-TABLE-time FK precedent — do not attempt the declared FK.
- **Status-field mapping (reviewer decision point).** The four tables have
  heterogeneous existing status vocabularies today (verified in
  `backend/app/modules/modeling/models.py` and
  `backend/app/modules/modeling/service.py`):
  - `assumptions.status`: `Pydantic Literal["proposed", "accepted", "rejected",
    "superseded"]`, default `"proposed"`. This already matches the facade
    vocabulary exactly. **Proposal:** the memory service's transition matrix
    maps directly onto `assumptions.status` with no translation. Legacy rows
    with pre-enum values (e.g. `"draft"`) are already normalized to
    `"proposed"` by `list_assumptions`'s defensive `CASE` — the memory service
    must apply the same normalization when reading a record before validating
    a transition, so a legacy `"draft"` row is treated as `"proposed"` for
    transition purposes, not rejected as "unknown state".
  - `parameters.status`: plain `str`, default `"draft"`, distinct from
    `value_status` (`candidate/literature/measured/validated/accepted`
    Literal). Neither column currently uses the facade vocabulary. **Proposal:**
    introduce the facade vocabulary onto `parameters.status` exactly as for
    assumptions (`proposed/accepted/rejected/superseded`), leaving
    `value_status` untouched and orthogonal (it continues to describe
    evidentiary quality, not proposal lifecycle). AI-proposed parameters are
    created with `status='proposed'`; legacy/manual rows with `status='draft'`
    are read as `'proposed'` by the same normalization rule as assumptions.
    Confirmed at expert review (2026-07-06): implement as proposed.
  - `decisions.status`: plain `str`, default `"draft"`. **Proposal:** same
    treatment as `parameters.status` — facade vocabulary applied directly,
    legacy `"draft"` normalized to `"proposed"` on read. Confirmed at expert review (2026-07-06): implement as proposed.
  - `requirements`: excluded from this slice entirely (expert review,
    2026-07-06). The table gets no new columns, no facade coverage, and keeps
    its existing `draft/active/retired` lifecycle and `update_requirement`
    path untouched. Rationale: that shipped lifecycle is not a
    proposal-acceptance lifecycle, and spec 041 deliberately excludes
    requirements from AI capture as well. The facade gains requirements only
    in a future slice with its own design.
  - In every case, `GET /memory/proposals?status=...` filters on the facade
    vocabulary (`proposed|accepted|rejected|superseded`) as computed by the
    per-table mapping above, not on the raw stored column value.
- **Transition matrix is enforced in the service, not the database.** SQLite
  has no CHECK-based state machine here; `backend/app/modules/memory/service.py`
  must look up the current effective facade status (via the per-table mapping
  above) before allowing `promote` (`proposed -> accepted`) or `reject`
  (`proposed -> rejected`), and before allowing any further transition out of
  `accepted` (`accepted -> superseded` only, and this slice does not expose an
  endpoint that triggers `superseded` — it is reserved for a future slice;
  document this as intentionally unreachable via the four endpoints in this
  slice, not silently unimplemented).
- **Origin/provenance invariant:** `POST /memory/proposals` always sets
  `origin='ai_proposed'`; it is not a generic "create with either origin"
  endpoint. If `source_ai_job_id` is missing, blank, or does not exist in
  `ai_jobs` (service-level existence check — see the FK bullet above), the
  service rejects the write (422/400, not a silent default). The existing
  `modeling` module create endpoints continue to insert `origin='user'`
  implicitly (via the column default) and are not required to accept
  `source_ai_job_id` at all in this slice.
- **Calc-origin proposals (service-level only, consumed by spec 043):** the
  memory service additionally exposes an in-process batch function (no HTTP
  endpoint) that creates `'proposed'`-status **parameter** records with
  `origin='calc'` and mandatory `source_ref='runner_job:<runner job id>'`,
  covering all outputs of one runner job in a single transaction
  (all-or-nothing). `'calc'` is invalid for decisions and assumptions in this
  slice. The transition matrix applies to these records identically.
- **`promoted_at`** is set only by the promote transition, using the same
  `utc_now()` helper the rest of the codebase uses
  (`app.modules.events.service.utc_now`). It is never set at proposal-creation
  time and never set for `reject`.
- **No AI calls:** `backend/app/modules/memory/service.py` must not import
  from `app.modules.ai.execution` or call any provider adapter. It only
  records that a caller-supplied `source_ai_job_id` (assumed to already exist
  in `ai_jobs`) is the origin of the write; it does not create or validate the
  `ai_jobs` row's own content beyond existence (see Open questions on whether
  existence should be checked).
- **Follow existing module conventions:** service functions open their own
  `sqlite3.Connection` via `open_sqlite_connection()`, use
  `row_to_model`/`optional_row_to_model`/`rows_to_models` from
  `app.core.repository`, log an event via `log_event` for every create and
  every transition (mirroring `_log_creation` in
  `backend/app/modules/modeling/service.py`), and raise `ValueError` for
  domain errors the way `modeling/service.py` does (translated to HTTP 404 by
  a `_domain_error`-style helper in `routes.py`).
- **Workspace scoping:** every proposal and every list call is scoped to an
  existing `workspace_id`, validated with the same
  `_require_workspace`/`ValueError` pattern used throughout `modeling/service.py`.
- **No secrets, no new dependency, no schema engine change, no Alembic** (per
  `AGENTS.md`).

## Acceptance criteria

1. `backend/app/core/schema.py` adds `origin`, `source_ai_job_id`,
   `promoted_at` to `decisions`, `assumptions`, `parameters`
   via additive `ALTER TABLE` statements with safe defaults, and bumps the
   current schema migration id/name. Running `initialize_database()` twice is
   still idempotent (existing duplicate-column swallow behavior unchanged).
2. A pre-existing SQLite DB built from the pre-040 schema (all three affected tables
   without the new columns, with at least one existing row per table)
   upgrades in place via `initialize_database()`: the three columns appear,
   existing rows read back with `origin='user'`, `source_ai_job_id=NULL`,
   `promoted_at=NULL`, and no existing row's other column values change.
3. `backend/app/modules/memory/` exists with `models.py`, `service.py`,
   `routes.py`, matching the module layout of `backend/app/modules/modeling/`.
4. `POST /memory/proposals` with `origin` implicitly `'ai_proposed'` and a
   valid `source_ai_job_id` creates a row in the target table
   (`decisions`/`assumptions`/`parameters`, selected by
   `record_kind`) with `origin='ai_proposed'`, the supplied
   `source_ai_job_id`, `promoted_at=NULL`, and the table-appropriate
   "proposed" status per the mapping in Design constraints.
5. `POST /memory/proposals` for an `ai_proposed` record without
   `source_ai_job_id` (missing or empty), or whose `source_ai_job_id` does not
   exist in `ai_jobs`, is rejected and writes no row.
6. `POST /memory/{record_kind}/{id}/promote` on a record whose effective
   facade status is `proposed` transitions it to `accepted` and sets
   `promoted_at` to a non-null timestamp; the same call on a record already
   `accepted`, `rejected`, or on a nonexistent id is rejected without changing
   `promoted_at` or status.
7. `POST /memory/{record_kind}/{id}/reject` on a record whose effective facade
   status is `proposed` transitions it to `rejected`; the same call on any
   other effective status, or a nonexistent id, is rejected without changing
   the record.
8. No endpoint in this slice can drive any record to `superseded`; this is
   verified by a test asserting the transition is unreachable via the public
   API surface added here.
9. `GET /memory/proposals?workspace_id=...&status=proposed` lists only records
   in that workspace whose effective facade status is `proposed`, across all
   three record kinds, using the per-table mapping from Design constraints
   (including legacy-row normalization for pre-existing `assumptions`/
   `parameters`/`decisions` rows with out-of-vocabulary stored status values).
10. The existing `modeling` module create endpoints
    (`POST /workspaces/{id}/assumptions|parameters|requirements|decisions`) are
    unmodified in behavior: their responses, statuses, and defaults are
    unchanged, and rows they create still read back with `origin='user'` via
    the new column's default.
11. No file under `backend/app/modules/ai/`, `backend/app/modules/local_ai/`,
    or any provider adapter is imported by `backend/app/modules/memory/`.
12. Full backend test suite passes; `ruff check app tests` is clean on touched
    files.

## Required tests

- **Migration additive/idempotent test** (in the style of
  `test_legacy_engineering_records_upgrade_without_data_loss` in
  `backend/tests/test_domain_foundation.py`): build pre-040 `decisions`,
  `assumptions`, `parameters` tables with explicit SQL (not
  derived from `SCHEMA_STATEMENTS`), insert one sentinel row per table, run
  `initialize_database()`, assert the three new columns exist, assert the
  sentinel rows are unchanged except for the new columns defaulting to
  `origin='user'`/`NULL`/`NULL`, and assert a second `initialize_database()`
  call is still a no-op.
- **Transition matrix tests:** `proposed -> accepted` succeeds and sets
  `promoted_at`; `proposed -> rejected` succeeds; `accepted -> proposed`,
  `accepted -> rejected`, `rejected -> accepted`, `rejected -> proposed`, and
  promote/reject on an already-`superseded` or nonexistent record are all
  rejected and leave the record unchanged. Run this matrix for at least
  `assumptions` and one other record kind that uses the fallback mapping
  (`parameters` or `decisions`). Requirements are out of scope for the facade.
- **Mandatory-provenance test:** `POST /memory/proposals` with
  `origin` forced to `ai_proposed` and `source_ai_job_id` omitted, blank, or
  set to an id absent from `ai_jobs` is rejected (422/400) and no row is
  written to the target table.
- **Promoted-at test:** after a successful promote, `promoted_at` is a
  non-null timestamp string and the record was not already carrying one.
- **Legacy-status normalization test:** an `assumptions`/`parameters`/
  `decisions` row with a pre-enum stored status value (e.g. `"draft"`) is
  listed under `GET /memory/proposals?status=proposed` and can be promoted,
  proving the read-side normalization from Design constraints is applied
  consistently by the memory service (not just by `modeling/service.py`'s own
  list functions).
- **Manual-path non-regression test:** existing
  `POST /workspaces/{id}/assumptions` (etc.) still returns 201 with unchanged
  fields, and the created row's `origin` reads back as `'user'`.
- **No-AI-call test:** a static/import check (or a test that patches/asserts
  no `run_ai_task`/provider adapter is invoked) confirms creating and
  promoting a proposal never triggers an AI call.
- Full suite: `python -m pytest -q` and `python -m ruff check app tests` stay
  green.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Open questions

These are conflicts or ambiguities found between this prompt and the actual
code, or judgment calls the drafting instructions explicitly deferred to a
reviewer. None of them block drafting this spec, but they should be resolved
(or explicitly accepted as written) before implementation starts.

1. **`assumptions.status` already implements the requested vocabulary,
   in code, at the Pydantic layer — but with no service-level transition
   matrix and no `update_assumption` function.** The task prompt frames the
   4-state matrix as new work; in reality, `AssumptionCreate.status` is
   already `Literal["proposed", "accepted", "rejected", "superseded"]"` with a
   defensive legacy-normalizing `CASE` in `list_assumptions`. This is not a
   conflict with the binding decisions (the matrix still needs to be *enforced*
   somewhere, and today it plainly is not — any caller can `POST` an
   assumption with `status="superseded"` directly, and there is no promote/
   reject transition at all), but it does mean assumptions needed the least
   new "vocabulary" work and the most new "enforcement" work. Flagged so the
   reviewer knows the starting point differs by table.
2. **`requirements.status` cannot cleanly host the facade vocabulary**
   because it already has a real, shipped, unrelated lifecycle
   (`draft/active/retired`) via `update_requirement`. The Design constraints
   section proposes deriving proposed/accepted from `origin`/`promoted_at`
   instead of reusing `status`, and flags "rejected" for requirements as
   unresolved (reuse `retired`, or accept reject-without-status-change). This
   is the single largest open modeling decision in this spec and must be
   settled by the reviewer before implementation, not decided by the
   implementing agent.
3. **`source_ai_job_id` foreign key feasibility.** `schema.py` shows one
   existing precedent for an FK to `ai_jobs.id`
   (`bluecad_attempts.proposal_ai_job_id`), but that column was defined in a
   `CREATE TABLE`, not added later via `ALTER TABLE ADD COLUMN`. SQLite does
   not support adding a `FOREIGN KEY` constraint through
   `ALTER TABLE ... ADD COLUMN`, and `foreign_keys = ON` is set on every
   connection (`backend/app/core/database.py`). This spec directs the
   implementer to attempt the FK and stop-and-report if SQLite rejects it,
   rather than deciding now whether `source_ai_job_id` ships with or without
   an enforced FK. The reviewer should decide up front whether an unenforced
   (application-level-only) reference is acceptable, since it changes
   Acceptance Criterion 1's exact wording.
4. **`ai_jobs` existence is not validated by this spec.** The task prompt does
   not ask for `source_ai_job_id` to be checked against a real `ai_jobs` row
   before accepting a proposal (only that it be present/non-null). Given
   invariant 8 ("AI outputs are proposals") and the fact this slice explicitly
   makes no AI calls, should `POST /memory/proposals` verify the referenced
   `ai_jobs` row actually exists (defense against a caller fabricating an
   arbitrary id), or is presence-only validation sufficient for this slice? Left
   as a reviewer call; Acceptance Criterion 4/5 as written only requires
   presence, not existence-checking.
5. **Relationship between this slice's 4-state matrix and the 7-stage
   lifecycle in `docs/MEMORYSTORE_FACADE_DESIGN.md` /
   `docs/strategy/JARVISOS_MEMORY_CONTEXT_DESIGN.md`
   (`raw_input -> fast_intake -> proposed_memory -> enriched_memory ->
   accepted_memory -> canonical_state -> superseded`).** The task prompt's
   binding kernel decisions specify the narrower matrix directly, so this spec
   implements that matrix as given rather than the 7-stage design. This is not
   treated as a code-vs-prompt conflict (both documents are docs-level
   strategy, not implemented code), but it is worth the reviewer's explicit
   sign-off that `MEMORYSTORE-0` is intentionally scoped down to "provenance +
   promotion boundary over four existing tables" rather than the fuller staged
   design, and that a future slice remains free to layer the richer lifecycle
   on top without contradicting this one.
6. **No conflict found** between the prompt's binding decisions and
   `backend/app/modules/modeling/service.py`/`routes.py` as they exist today:
   the existing create endpoints and functions are exactly as described (no
   update path for assumptions/parameters/decisions; only `requirements` has
   `update_requirement`), so "existing modeling create endpoints are NOT
   modified" is achievable without any hidden coupling.

## Review resolutions (2026-07-06 — expert review, binding)

1. (OQ1) Acknowledged: assumptions need enforcement, not new vocabulary. No
   change.
2. (OQ2) Resolved by exclusion: requirements are out of this slice entirely
   (no columns, no facade coverage). Body updated accordingly.
3. (OQ3) Resolved: no declared FK; plain column + service-level existence
   check. Body updated.
4. (OQ4) Resolved: yes — the referenced `ai_jobs` row's existence IS checked
   at proposal time (fail-closed).
5. (OQ5) Confirmed: MEMORYSTORE-0 is deliberately the narrow
   provenance+promotion boundary; the 7-stage lifecycle in
   `docs/MEMORYSTORE_FACADE_DESIGN.md` remains a future superset that can
   layer on top without contradiction.
6. (OQ6) Noted; no action.

Additional binding decision: the facade exposes a calc-origin in-process batch
path for spec 043 (see Design constraints) — `origin='calc'`,
`source_ref='runner_job:<id>'`, parameters only, single transaction.
