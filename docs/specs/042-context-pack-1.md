# 042 — CONTEXT-PACK-1: deterministic, budgeted, inspectable context packs

Status: implemented (pending review)
Depends on: none (parallel to 040)

## Goal

After this slice, JarvisOS can assemble a **context pack**: an explicit,
deterministic selection over Domain Foundation records (decisions,
assumptions, parameters, requirements) filtered by status/kind/ids/text query,
truncated to a char budget with a documented per-kind priority, and returned
with a stable digest and source manifest — inspectable via a new
`POST /ai/context/packs/preview` endpoint without invoking any AI provider. This
extends `build_workspace_context_bundle` with a typed selection spec; it does
not replace the existing full-dump behavior, which remains the default when no
selection spec is supplied.

## Why

`docs/strategy/JARVISOS_MEMORY_CONTEXT_DESIGN.md` names `SOURCE-SELECTION-0`
("deterministic source chooser for workspace context") and `RETRIEVAL-0`
("structured retrieval over accepted/project records") as the next memory
milestones, explicitly before FTS, before vector search, and before LLM
reranking. `docs/strategy/JARVISOS_CURRENT_ARCHITECTURE.md` names "context
builder doing semantic ranking implicitly" as an architecture smell to avoid.
This slice implements the first two milestones as one deterministic,
testable, auditable step: explicit selection query in, deterministic pack +
manifest + digest out, no ranking, no model call.

## Scope

In scope:
- A new typed selection spec (record kinds, status filter, optional explicit
  ids, optional text query, max items per kind) consumed by an extended
  `build_workspace_context_bundle`.
- Deterministic ordering (`updated_at DESC, id ASC`) and deterministic,
  documented per-kind truncation priority under a char budget.
- SQLite FTS5-backed text query with a mandatory capability probe and a
  behavior-identical `LIKE` fallback when FTS5 is unavailable; FTS/LIKE is used
  **only** when the selection spec's `query` field is non-empty — never as
  implicit ranking of an unqueried selection.
- A new `POST /ai/context/packs/preview` endpoint that assembles a pack and
  returns it plus its manifest, char count, and estimated token count, without
  any AI call.
- Requirements become a selectable/context-eligible record kind for the first
  time (today's `build_workspace_context_bundle` only covers decisions,
  assumptions, parameters).
- Wiring the pack's digest and source manifest through the existing
  `ai_jobs.context_digest` / `ai_jobs.context_sources_json` fields when a
  selection-spec-built pack is used as `context_blocks` for a real AI task, with
  no new `ai_jobs` columns.

Out of scope (binding non-goals):
- No embeddings, no vector store, no vector search of any kind.
- No LLM reranking, summarization, or any AI call inside pack assembly or the
  preview endpoint.
- No caching layer for packs, digests, or FTS results.
- No frontend/UI work.
- No new `ai_jobs` columns.
- No change to `list_decisions` / `list_assumptions` / `list_parameters` /
  `list_requirements` ordering or output shape (they keep `created_at DESC`
  for their existing callers; the new `updated_at DESC, id ASC` ordering is
  specific to the selection-spec code path only — see Design constraints).
- No implicit/automatic ranking: if the selection spec has no `query`, FTS/LIKE
  must not run at all, and block order must come only from the deterministic
  ordering rule.
- No MemoryStore, staged-memory schema, or promotion-state changes (ADR-051's
  future FTS-behind-MemoryStore subsystem is a separate, later piece over
  different tables — see Open questions).
- No changes to `route_class="auto"` context-level/budget logic in
  `backend/app/modules/ai/routing/bridge.py` beyond what is strictly required
  to keep existing behavior byte-identical when no selection spec is passed.

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing.

- `backend/app/modules/ai/context_builder.py` — add the selection-spec type,
  extend `build_workspace_context_bundle` (new optional parameter, default
  `None` preserves current full-dump behavior exactly), add a `_format_requirement`
  helper alongside the existing `_format_decision` / `_format_assumption` /
  `_format_parameter`, add per-kind truncation-priority logic.
- `backend/app/modules/modeling/service.py` — add a selection-query function
  (or functions) over `decisions` / `assumptions` / `parameters` /
  `requirements` supporting kind/status/ids/query/limit and the
  `updated_at DESC, id ASC` ordering; add the FTS5 capability probe and the
  `LIKE` fallback path.
- `backend/app/core/schema.py` — add the FTS5 virtual table(s) (guarded, see
  Design constraints) and any supporting index(es); bump
  `CURRENT_SCHEMA_MIGRATION_ID` / `CURRENT_SCHEMA_MIGRATION_NAME` per existing
  convention if a real schema object is added.
- `backend/app/modules/ai/models.py` — new request/response models for the
  selection spec and the preview endpoint.
- `backend/app/modules/ai/routes.py` — add `POST /ai/context/packs/preview`
  under the existing `/ai` prefix router (expert review, 2026-07-06: no new
  top-level router; the kernel's bare `/context/...` path is corrected to
  `/ai/context/...` throughout this spec).
- `backend/app/main.py` — likely unchanged (the `/ai` router is already
  registered).
- `backend/app/modules/ai/gateway.py` — only if `run_task`'s existing
  `build_workspace_context_bundle` call site needs a compatible optional
  selection-spec passthrough; must not change today's `include_project_context`
  behavior when no selection spec is supplied.
- `backend/tests/test_ai_context_builder.py` — extend with selection-spec
  tests.
- New test file, e.g. `backend/tests/test_context_pack_preview.py`, for the
  preview endpoint.
- New fixture data (small, in-repo test fixtures or programmatic seeding in
  the test file itself — verify existing test conventions before adding a new
  fixture file) for the byte-stability tests.

## Design constraints

- **Extend, do not replace:** `build_workspace_context_bundle(workspace_id, budget_chars=...)`
  keeps its current positional/keyword signature and current default,
  full-dump-by-budget behavior when called with no selection spec. Existing
  callers (`backend/app/modules/ai/gateway.py::run_task`,
  `backend/app/modules/ai/routing/bridge.py`) must not change observable
  behavior. Add the selection spec as a new optional parameter (e.g.
  `selection: ContextSelectionSpec | None = None`), not by breaking the
  existing call sites.
- **Selection spec shape** (typed, e.g. a `dataclass` or Pydantic model,
  matching the existing `dataclass`-based `ContextBundle` style in
  `context_builder.py`):
  - `kinds: list[Literal["decision", "assumption", "parameter", "requirement"]]`
    — which record tables to draw from; empty/omitted means all four.
  - `statuses: dict[kind, list[str]] | list[str] | None` — status filter,
    **default is per-kind, not a single shared vocabulary**, because the four
    tables do not share a status enum today (see Open questions):
    - decision: no enum exists in code (`status: str = "draft"`, free text).
      Decided (expert review, 2026-07-06): default filter is `["accepted"]` —
      spec 040 introduces the facade vocabulary on `decisions.status`, and
      packs default to promoted decisions only. Do not invent a decision
      status enum in this spec (040 owns it); this is a plain string filter.
      Consequence: selection-spec packs exclude unpromoted decisions by
      default (callers can pass explicit statuses); the no-selection-spec
      full dump keeps today's behavior.
    - assumption: `proposed | accepted | rejected | superseded` — default
      filter is `["accepted"]`.
    - parameter: has *two* status-shaped fields, `status` (free text) and
      `value_status` (`candidate | literature | measured | validated |
      accepted`) — the selection spec must filter on `value_status`, and the
      default filter is `["validated", "accepted"]`.
    - requirement: `draft | active | retired` — there is no "accepted" or
      "validated" value in this enum; the closest analog is `active`, so the
      default filter is `["active"]`.
  - `ids: list[str] | None` — optional explicit record ids. Decided (expert
    review, 2026-07-06): explicit ids BYPASS the status filter but must still
    belong to an included kind. Naming a record explicitly is the operator's
    override, matching the memory design's "allowed records: explicit source
    list" contract.
  - `query: str | None` — optional text query; only when non-empty does
    FTS/LIKE search run, scoped to `statement`/`title`/`rationale`/`notes`
    columns across the four tables per the mapping in the FTS section below.
  - `max_items_per_kind: int` — caps rows read per kind before ordering/budget
    truncation; must have a documented default (propose reusing
    `MAX_CONTEXT_BLOCKS` proportionally, or a flat default such as 10; pick
    one and state it in the diff).
- **Deterministic ordering:** the selection query orders every kind's rows by
  `updated_at DESC, id ASC` (tiebreak). This is a **new** ordering specific to
  the selection-spec code path; it must not be applied to
  `list_decisions`/`list_assumptions`/`list_parameters`/`list_requirements`,
  which keep `ORDER BY created_at DESC` for their existing callers (modeling
  CRUD routes). Do not refactor those functions to share the new query path
  unless doing so is proven behavior-preserving with a regression test.
- **Budget in chars, with documented per-kind truncation priority:** decisions
  and requirements survive longest under budget pressure; assumptions and
  parameters are dropped first when the budget is exceeded. State the exact
  drop order in the diff (e.g. drop order when over budget: parameters →
  assumptions → requirements → decisions, or equivalent — pick one order,
  document it in code comments and in this file's acceptance criteria, and
  keep it consistent with "decisions and requirements survive longest").
  Truncation drops whole blocks (matching the existing `build_workspace_context_bundle`
  behavior of dropping blocks wholesale under budget, not truncating block text
  mid-string), unless a documented finer-grained truncation is judged
  necessary — if so, justify the change from whole-block dropping explicitly.
- **Pack digest and manifest reuse existing primitives:** the pack's
  `context_digest` is `canonical_digest(included_blocks)` (already defined in
  `context_builder.py`); its manifest is `context_sources_manifest(included_blocks)`
  (already defined). Do not invent parallel digest/manifest logic. When a
  selection-spec pack is used as `context_blocks` for a real `run_ai_task`
  call, these values flow through the existing `ai_jobs.context_digest` /
  `ai_jobs.context_sources_json` columns exactly as today's workspace-context
  packs already do — no new columns.
- **FTS5 vs. rebuild-on-write vs. triggers — pick one, justify it:** the
  binding decision offers two options for keeping the FTS index current
  (trigger-maintained virtual table, or rebuild-on-write via the service
  layer). No FTS table exists in this codebase today (verified: no
  `CREATE VIRTUAL TABLE` anywhwere in `backend/app/core/schema.py`), so there
  is no precedent to match. Justify the choice against the existing service
  patterns in `backend/app/modules/modeling/service.py` — that layer writes
  through simple `INSERT`/`UPDATE` statements per record kind, with no shared
  write path today. A trigger-maintained FTS5 table needs no service-layer
  changes to existing create/update functions and cannot drift from the base
  tables; a rebuild-on-write approach requires touching every existing
  create/update function for all four kinds and risks silent staleness if one
  write path is missed. Decided (expert review, 2026-07-06): use the trigger-maintained FTS5 table —
  no changes to existing write paths, no drift risk. Do not implement
  rebuild-on-write.
- **FTS5 capability probe is mandatory, and the fallback must be behaviorally
  identical:** at startup or first use, probe FTS5 availability (e.g. attempt
  `CREATE VIRTUAL TABLE IF NOT EXISTS <probe> USING fts5(x)` in a way that can
  be checked/rolled back, or use `PRAGMA compile_options` /
  `sqlite3.Connection` module detection — verify the most robust approach
  against the Python/SQLite versions this repo actually runs, per `AGENTS.md`'s
  cross-platform table). If FTS5 is unavailable, the selection query with a
  non-empty `query` field must fall back to `LIKE '%term%'` (case-insensitive,
  matching current SQLite default collation behavior) over the same four
  columns, and must return the **same result set** as FTS5 would on the same
  fixture data for the required tests (slower is acceptable; different matches
  are not). Do not silently drop the `query` filter when FTS5 is unavailable.
- **FTS/LIKE columns:** `statement` (assumptions, requirements), `title` and
  `decision_text` (decisions — the decision table has no `statement` column;
  its analogous free-text fields are `title` and `decision_text`, plus
  `rationale`), `name` (parameters — parameters have no `statement` column
  either; the closest text fields are `name`, `symbol`, and `notes`), and
  `rationale`/`notes` where present on a given table. Confirm the exact column
  list per table against `backend/app/core/schema.py` before implementing;
  the binding decision's "statement/title/rationale/notes" list is a
  simplification that does not literally exist as four identical columns on
  all four tables (see Open questions).
- **FTS is opt-in per selection spec, never implicit:** if `query` is empty or
  omitted, no FTS/LIKE execution happens at all, and kind/status/ids filtering
  plus deterministic ordering fully determines block order. This is required
  to avoid the "context builder doing semantic ranking implicitly" smell.
- **New schema objects follow existing conventions:** additive only; if a real
  `CREATE VIRTUAL TABLE`/trigger set is added to `SCHEMA_STATEMENTS` (guarded
  by the capability probe — note this means it likely cannot live unconditionally
  in the same list as other `CREATE TABLE IF NOT EXISTS` statements executed
  unconditionally in `initialize_database()`; determine the right guarding
  mechanism and document it), bump `CURRENT_SCHEMA_MIGRATION_ID`/`_NAME` per
  the pattern in `backend/app/core/schema.py`. No Alembic.
- **Preview endpoint calls no AI provider and writes no `ai_jobs` row.** It is
  a read-only inspection surface: build the pack via the extended
  `build_workspace_context_bundle`, return blocks/manifest/char
  count/estimated token count. Estimated tokens must use a clearly-labeled,
  simple deterministic heuristic (e.g. `chars // 4`), not a tokenizer
  dependency (no new dependency allowed).
- **Zero new dependencies.** FTS5 is a compile-time SQLite feature, not a
  Python package; the capability probe and `LIKE` fallback exist precisely so
  this holds even where FTS5 is not compiled in.
- **Sensitivity/redaction unaffected:** this slice only touches Domain
  Foundation record selection for context assembly; it must not weaken or
  bypass any existing sensitivity, budget, or confirm-to-escalate gate. The
  preview endpoint never calls `run_ai_task` and therefore cannot leak pack
  content to an external provider by itself — but it does expose Domain
  Foundation record content over the local API surface, which is already true
  of the existing `GET` endpoints in `backend/app/modules/modeling/routes.py`.

## Acceptance criteria

1. `build_workspace_context_bundle` accepts a new optional selection-spec
   parameter; called exactly as today (no selection spec), it produces
   byte-identical output to the pre-change behavior on the same fixture data
   (same blocks, same digest, same manifest, same included/dropped counts).
2. With a selection spec restricting `kinds` to a subset (e.g. only
   `["decision", "requirement"]`), the returned pack contains only blocks of
   those kinds.
3. With a selection spec's default status filter (per the per-kind defaults
   documented in Design constraints), records outside the default status set
   are excluded; records inside it are included, ordered `updated_at DESC, id
   ASC`.
4. With a selection spec's explicit `ids`, exactly those ids (intersected with
   the kind/status filter per the documented resolution) appear in the pack.
5. With a selection spec's `query` set and FTS5 available, the pack includes a
   record whose indexed text contains the query term and excludes records
   that do not match, while still respecting the status filter.
6. With FTS5 forced unavailable (via the capability probe returning false,
   exercised directly in a test, not by requiring a special SQLite build), the
   same query against the same fixture returns the same included-record set
   via `LIKE` as the FTS5 path returns when available.
7. Under a char budget too small to fit all selected records, the documented
   per-kind truncation priority is respected: decisions and requirements are
   retained over assumptions and parameters when the budget forces a choice,
   consistent with the stated drop order.
8. Given fixed fixture records and a fixed selection spec, two separate calls
   to the pack-assembly function in the same process (and across a fresh
   process invocation, i.e. not relying on in-memory cache) produce
   byte-identical serialized blocks and an identical `context_digest`.
9. `POST /ai/context/packs/preview` returns the assembled pack's blocks,
   `context_sources_manifest`, a char count, and an estimated token count, and
   makes no AI provider call and writes no `ai_jobs` row (verified by an
   ai_jobs count assertion before/after the call).
10. The preview endpoint's returned manifest is consistent with the returned
    pack content: every block's `source`/`type`/`id` appears in the manifest
    and vice versa, with no extra or missing entries.
11. Existing `include_project_context=True` behavior through
    `POST /ai/tasks/run` (no selection spec supplied) is unchanged: same
    blocks, same `context_digest`, same `context_sources_count` as before this
    change, on the same fixture workspace.
12. No new entry appears in `backend/requirements.txt` /
    `backend/requirements-dev.txt` as a result of this slice.

## Required tests

- **Byte-stability test:** fixed fixture workspace (decisions, assumptions,
  parameters, requirements seeded with known ids/timestamps) → assert the
  selection-spec pack's serialized blocks and `context_digest` are identical
  across two separate calls (and ideally across two separate test-process
  invocations via a golden constant, if practical) — no run-to-run drift.
- **Budget truncation test:** same fixture, a budget small enough to force
  drops → assert the documented per-kind priority order is followed (decisions
  and requirements present, assumptions/parameters dropped first, or whatever
  exact order is documented in Design constraints).
- **FTS query test:** fixture with a known distinctive term in one record's
  indexed text → selection spec with that `query` finds exactly that record
  (plus any other genuine matches), and the status filter still excludes
  non-matching-status records that would otherwise match textually.
- **LIKE fallback test:** with the FTS5 capability probe monkeypatched/forced
  to report unavailable, the same query against the same fixture returns the
  same included-record id set as the FTS5 path.
- **Preview endpoint test:** call `POST /ai/context/packs/preview` with a
  selection spec against the fixture workspace; assert the response's
  manifest matches its blocks exactly, char count and estimated token count
  are present and consistent with the returned blocks, and no `ai_jobs` row is
  written (count `ai_jobs` before and after).
- **Regression test:** existing `include_project_context` flow through
  `POST /ai/tasks/run` with no selection spec produces the same
  `context_digest`/`context_sources_count`/blocks as before this change on a
  fixed fixture workspace.
- All tests offline, using the existing `JARVISOS_DATA_ROOT`/`tmp_path`
  isolation pattern from `backend/tests/conftest.py`; no live provider, no
  network, no Ollama.

## Open questions

- **Status vocabulary mismatch across the four record kinds.** The binding
  decision specifies "status filter (default: accepted/validated-class
  statuses only)" as if one shared vocabulary existed. It does not:
  `assumptions.status` has `accepted`; `parameters.value_status` has
  `validated`/`accepted` (and a *separate*, differently-named `parameters.status`
  free-text field); `requirements.status` has neither `accepted` nor
  `validated` — its terminal/mature value is `active`; `decisions.status` has
  no enum at all in code today (`str = "draft"`, per
  `backend/app/modules/modeling/models.py` and spec
  `docs/specs/001-parameter-schema-freeze.md`, which froze parameter/assumption/
  requirement statuses but left decision status as free text). This spec
  proposes per-kind defaults (see Design constraints) but the maintainer should
  confirm those defaults, especially for decisions, before implementation.
- **FTS text columns are not uniform across tables.** The binding decision
  says "statement/title/rationale/notes of the four record tables." Verified
  against `backend/app/core/schema.py`: only `assumptions` and `requirements`
  have a `statement` column; `decisions` has `title` + `decision_text` (no
  `statement`); `parameters` has `name` + `symbol` (no `statement`, no
  `title`). `rationale` exists on `decisions` and `requirements` only, not on
  `assumptions` or `parameters`. `notes` exists on all four. The spec above
  proposes a per-table column mapping; please confirm before implementation
  since this changes what "the same query" can mean per table.
- **ADR-051 relationship.** `docs/DECISIONS.md` ADR-051 ("Staged memory schema
  uses SQLite/FTS behind MemoryStore") describes a *future* FTS layer behind a
  not-yet-built MemoryStore facade, over staged/raw memory records — a
  different subsystem than the four already-canonical Domain Foundation tables
  this spec indexes. This spec's FTS5 usage is over already-accepted
  structured records (decisions/assumptions/parameters/requirements owned by
  `modeling/service.py`), not staged/raw memory, so it should not conflict
  with ADR-051's future scope — but the maintainer should confirm this reading
  is correct, since both use the term "FTS" and a future reader could conflate
  the two.
- **Endpoint prefix/router placement.** All existing AI-module HTTP endpoints
  are nested under `APIRouter(prefix="/ai", ...)` in
  `backend/app/modules/ai/routes.py`. The binding decision specifies
  `POST /context/packs/preview` verbatim (no `/ai` prefix), which means either
  a new top-level router or a deliberate deviation from the existing
  prefix-per-module convention. Confirm this is intentional before
  implementation; if not, the endpoint may need to become
  `/ai/context/packs/preview` instead, which would be a spec correction, not
  an implementer's call to make silently.
- **`docs/specs/README.md` index and spec 040.** Per instruction, this file
  was authored in isolation and does not update `docs/specs/README.md`'s
  index table (which also does not yet list spec 017, so omission is
  consistent with recent practice, not a regression). Spec 040 does not exist
  in the repo as of this writing (`ls docs/specs/` shows no `040-*` file), so
  "parallel to 040" is taken as directional intent (a sibling context/memory
  slice expected to land separately) rather than a verified dependency; please
  confirm what 040 is and that no ordering conflict exists once it is drafted.
- **Selection spec transport for `POST /ai/tasks/run`.** This spec's scope
  section allows (but does not mandate) threading a selection spec through
  `AIGateway.run_task`/`AITaskRunRequest` so a real AI task can use a
  selection-spec-built pack instead of the full-dump. Given the binding
  decision's emphasis on the preview endpoint as "the" inspection surface, and
  to keep this slice small, the maintainer should confirm whether wiring the
  selection spec into `AITaskRunRequest` is in-scope for 042 or deferred to a
  later slice — the acceptance criteria above only require the preview
  endpoint to exercise selection specs, plus a regression test proving
  unmodified `include_project_context` behavior.

## Review resolutions (2026-07-06 — expert review, binding)

1. (status vocabulary) Per-kind defaults confirmed as proposed in Design
   constraints, including decisions = `["accepted"]` (see the updated decision
   sub-bullet).
2. (FTS columns) The per-table column mapping proposed in Design constraints
   is approved; the kernel's uniform "statement/title/rationale/notes" wording
   is superseded by it.
3. (ADR-051) Reading confirmed: different subsystem/data scope; no conflict.
4. (endpoint prefix) Resolved: `/ai/context/packs/preview` under the existing
   `/ai` router. Body updated throughout.
5. (README index / spec 040) The stale `docs/specs/README.md` index is a
   separate maintenance task. Spec 040 now exists as a reviewed draft; there
   is no hard ordering conflict — only the decisions default filter leans on
   040's vocabulary, and it is a plain string filter either way. 042 and 040
   can be implemented in parallel.
6. (selection-spec transport) DEFERRED, binding: 042 ships the preview
   endpoint and builder extension only. Native wiring of a selection spec
   into `AITaskRunRequest` is a later slice; in the meantime a caller can
   already pass a previewed pack's blocks as manual `context_blocks`, so the
   capability exists compositionally.

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
## Implementation notes

- Implemented context-pack selection as a `ContextSelectionSpec` extension to `build_workspace_context_bundle`; calls without a selection spec retain the historical full-dump path unchanged.
- Added trigger-maintained SQLite FTS5 indexing for Domain Foundation records when FTS5 is available, with service-level LIKE fallback when the mandatory capability probe reports unavailable.
- Added `POST /ai/context/packs/preview` under the existing `/ai` router. It assembles packs only and does not call providers or write `ai_jobs`.
- Documented and implemented whole-block budget drop priority for selection-spec packs: parameters → assumptions → requirements → decisions.
- Did not wire selection specs into `POST /ai/tasks/run`, per the binding review resolution deferring native transport to a later slice.
