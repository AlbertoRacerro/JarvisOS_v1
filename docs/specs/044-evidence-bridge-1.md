# 044 — EVIDENCE-BRIDGE-1: typed evidence records for simulation/validation outcomes

Status: ready (after 042 is merged)
Depends on: 042 (must be implemented first — hard dependency for the pack
integration). 009 is already implemented (`backend/app/modules/bluecad/
fem_adapter.py`, verified 2026-07-06) — its writer hook can be wired against
the real `ResultSummary` shape, not a guessed contract (see corrected field
mapping in Design constraints). Note: like 008's `mesh_analysis_spec`, 009's
`solve_static_analysis`/`append_tier3_checks` have no call site yet in
`routes.py`/`loop.py` — this is a pre-existing integration gap independent of
this spec (see "## Open questions").

## Goal

After this slice, three kinds of simulation/validation outcomes — CalculiX
static FEM results (009), Gmsh mesh quality gate results (008), and BLUECAD
loop validation verdicts (010) — are written as compact, typed
`evidence_records` rows by deterministic service-layer hooks in their
respective producing paths, and are readable through the 042 context-pack
selection spec under a new record kind `'evidence'`, each serializing to a
pack line of at most 300 characters. Agents can consult headline verdicts and
metrics in tens of tokens instead of re-reading full report/result artifacts.

## Why

`BLUECAD_CORE_DESIGN.md` and the 010/009 seam both establish that review
agents and humans judge summarized outcomes (`ResultSummary`, validation
reports), never raw solver output — but today those summaries live only as
JSON blobs inside artifact files, invisible to context packs. This spec
closes that gap with the smallest possible bridge: one additive table, three
deterministic mapping hooks, and one new selection-spec record kind. It
directly serves the JarvisOS positive execution spine's "Context" and
"Ledger" stages without adding any new analysis, aggregation, or model
involvement (`AGENTS.md` invariant 9: no fabricated results; this spec only
compresses already-computed, already-persisted outcomes).

## Scope

In scope:
- New table `evidence_records` (additive migration, schema version bump —
  see "Design constraints").
- Three deterministic writer hooks, one per producing path (008 mesh
  adapter, 009 FEM adapter, 010 loop validation), each a pure mapping from
  that path's existing typed output to `evidence_records` fields. No model
  involvement; hooks run only from service-layer code in the producing
  path itself, never from sandboxed/runner scripts.
- Extension of the 042 selection spec with a fourth record kind, `'evidence'`,
  selectable by the same typed selection fields 042 defines for its other
  kinds (status filter, explicit ids, text query match against
  `kind`/`verdict`, max-per-kind cap).
- A pack-line serializer for `'evidence'` records, bound to <= 300 chars per
  line (binding contract; example given below).
- Per-kind typed `metrics_json` schemas for `fem_static_v0`, `mesh_quality_v0`,
  `validation_v0` (documented in this spec; small, headline-only fields).

Out of scope (binding non-goals):
- No aggregation dashboards, no cross-record analytics, no new analysis
  types beyond the three named kinds.
- No UI/frontend work.
- No backfill of historical runs/candidates/attempts — only new
  writes from the moment each hook lands.
- No writes from models, agents, or sandboxed/runner scripts — hooks are
  called only from the deterministic service code of 008/009/010's own
  execution paths.
- No changes to `artifacts`, `simulation_runs`, `bluecad_candidates`,
  `bluecad_attempts`, or any other existing table's DDL.
- No new report format: the full report/result JSON stays exactly where it
  already lives (an `artifacts` row); `evidence_records` never duplicates it,
  only points at it.
- No implementation of 042 itself; this spec only adds the `'evidence'` kind
  to 042's selection spec once 042 lands, and does not implement 042's core
  selection/pack-building machinery.

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing — in particular, verify that neither `mesh_adapter.py`'s
`mesh_analysis_spec()` nor `fem_adapter.py`'s `solve_static_analysis()`/
`append_tier3_checks()` has gained a caller since this spec was reviewed
(see "## Open questions" — as of 2026-07-06 neither has one).

- `backend/app/core/schema.py` (additive: `evidence_records` table + index,
  `CURRENT_SCHEMA_MIGRATION_ID`/`CURRENT_SCHEMA_MIGRATION_NAME` bump following
  the existing pattern of `SCHEMA_STATEMENTS` + `SCHEMA_MIGRATION_STATEMENTS`
  + `SCHEMA_INDEX_STATEMENTS`)
- `backend/app/modules/bluecad/evidence.py` (new) — typed writer functions
  (one per kind) + the `EvidenceRecord` read model + the 042 pack-line
  serializer for kind `'evidence'`
- `backend/app/modules/bluecad/mesh_adapter.py` — call the `mesh_quality_v0`
  writer hook at the end of `mesh_analysis_spec` (008, implemented)
- `backend/app/modules/bluecad/fem_adapter.py` (009, implemented) — call the
  `fem_static_v0` writer hook after `solve_static_analysis()` (and, when a
  Tier 3 `report` is produced via `append_tier3_checks()`, after that too) —
  only once a caller for this adapter exists (see Open questions)
- `backend/app/modules/bluecad/loop.py` — call the `validation_v0` writer
  hook at the point `finish_attempt(..., validation_verdict=...)` is invoked
  (010, implemented)
- Whichever module 042 lands in (module unknown at drafting time — 042 has
  no file yet) — add the `'evidence'` kind branch to its selection/pack-line
  dispatch, per its binding kernel description in this spec's context
- `backend/tests/bluecad/test_evidence_records.py` (new)
- `backend/tests/bluecad/test_evidence_pack_lines.py` (new, or folded into
  the 042 pack test suite once that module exists)

## Design constraints

- **New table, not `entities` reuse** (binding, per kernel decision 1):
  `evidence_records` gets real typed columns — `id TEXT PRIMARY KEY`,
  `workspace_id TEXT NOT NULL`, `kind TEXT NOT NULL` (one of
  `'fem_static_v0' | 'mesh_quality_v0' | 'validation_v0'`), `verdict TEXT NOT
  NULL`, `metrics_json TEXT NOT NULL`, `source_run_id TEXT` (nullable FK to
  `simulation_runs.id`), `candidate_id TEXT` (nullable FK to
  `bluecad_candidates.id`), `attempt_id TEXT` (nullable FK to
  `bluecad_attempts.id`), `report_artifact_id TEXT` (FK `artifacts.id`,
  **required** — every evidence record must point at the full report),
  `created_at TEXT NOT NULL`. Follow the exact `schema.py` pattern already in
  the file: add the `CREATE TABLE IF NOT EXISTS evidence_records (...)` block
  to `SCHEMA_STATEMENTS` (for fresh databases), add one additive
  `CREATE INDEX IF NOT EXISTS idx_evidence_records_workspace_kind ON
  evidence_records(workspace_id, kind, created_at)` to `SCHEMA_INDEX_STATEMENTS`,
  and — because `evidence_records` is a wholly new table rather than a
  column added to an existing one — no `ALTER TABLE` entry in
  `SCHEMA_MIGRATION_STATEMENTS` is needed (the `CREATE TABLE IF NOT EXISTS`
  in `SCHEMA_STATEMENTS` already upgrades existing databases in place, exactly
  as `bluecad_candidates`/`bluecad_attempts` were added in 010). Bump
  `CURRENT_SCHEMA_MIGRATION_ID`/`CURRENT_SCHEMA_MIGRATION_NAME` to a new
  migration id/name (e.g. `0005_evidence_records`) and append a matching
  entry to `SCHEMA_MIGRATION_RECORDS`, following the 0004 entry's shape
  exactly.
- **Writers are deterministic post-run hooks, not a new orchestration layer**
  (kernel decision 2). Each hook is a pure function:
  `map_<kind>_evidence(...) -> EvidenceRecordCreate` (a typed dataclass/model
  with the columns above minus `id`/`created_at`), plus a thin
  `record_<kind>_evidence(...) -> str` that inserts it and returns the new
  row's id. No hook may call `run_ai_task`, any provider adapter, or any
  code under `backend/app/modules/runner/`. Hooks are called synchronously,
  in-process, at the end of the producing function, by that function's own
  caller path — never as a side effect discovered by scanning artifacts
  later, and never from a sandboxed/runner script (`runner/` scripts must
  never import or call `evidence.py`).
  - **008 (`mesh_quality_v0`, implemented today):** call
    `record_mesh_quality_evidence(workspace_id, result: dict[str, Any],
    *, source_run_id: str | None, report_artifact_id: str) -> str` from the
    caller of `mesh_analysis_spec(...)` (not inside `mesh_adapter.py` itself,
    since that function is pure/adapter-only and does not currently accept a
    `workspace_id` or write DB rows — verify this call-site placement against
    actual caller code before implementing; `mesh_adapter.py` has no current
    caller in the routes/service layer, so this spec's implementer must add
    the call at whichever call site first persists the `MeshResult` as a
    report artifact, and must report a conflict if no such call site exists
    yet). Field mapping (deterministic, from the `MeshResult` dict shape
    documented in 008 and observed in `mesh_adapter.py`'s `_result()`):
    `verdict` = the `MeshResult["verdict"]` string (`"pass" | "fail" |
    "error"`) unchanged; `metrics_json` = `{"elements_total": int, "nodes_total":
    int, "empty_groups": [str, ...], "attempts": int}` taken from the last
    entry of `MeshResult["attempts"]` (`counts.elements_total`,
    `counts.nodes_total`, the list of `MESH_GROUP_EMPTY` detail `"group"`
    values across `MeshResult["errors"]`, and `len(MeshResult["attempts"])`).
  - **009 (`fem_static_v0`, implemented — verified against
    `backend/app/modules/bluecad/fem_adapter.py` at review time, 2026-07-06):**
    call `record_fem_static_evidence(workspace_id, result_summary: dict[str,
    Any], report: dict[str, Any] | None, *, source_run_id: str | None,
    report_artifact_id: str) -> str`. `result_summary` is the raw return of
    `solve_static_analysis(...)`; `report` (optional) is the output of
    `append_tier3_checks(report, result_summary, pass_criteria)` when Tier 3
    checks were run against `pass_criteria` — pass `None` if the caller only
    ran the raw solve with no Tier 3 pass criteria. Real field shapes
    (verified, not guessed):
    - `result_summary["verdict"]` is only `"pass"` or `"error"` at the raw
      solve level (`"fail"` does not occur here — solver failures produce
      `"error"` with an `errors[0]["code"]` of `SOLVE_ERROR`/`SOLVE_DIVERGED`/
      `PARSE_ERROR`/`TIMEOUT`).
    - `result_summary["max_displacement"]` = `{"node_id": int, "value":
      float}`; `result_summary["max_von_mises"]` = `{"element_id": int,
      "node_id": int, "value": float}` — both are dicts with a `"value"` key,
      not flat floats. No `_mm`/`_mpa` suffix exists in the real keys; units
      are implied by BLUECAD's global convention (mm/N/kg/MPa) per the
      adapter's module docstring, not encoded in the field name.
    - `result_summary["solver"]` = `{"tool_id": "calculix", "version": str,
      "returncode": int | None}` — there is no `solver_status` field; use
      `result_summary["errors"][0]["code"]` when `verdict == "error"`, else
      `None`.
    - Tier 3 checks, when present, live on `report["checks"]` (each
      `{"id": "T3_<METRIC>", "tier": 3, "status": "pass"|"fail"|"error",
      "detail": {...}}`), and `report["verdict"]` becomes the combined verdict
      (can be `"fail"` here, unlike the raw `result_summary["verdict"]`).
    - Field mapping: `verdict` = `report["verdict"]` if `report` is supplied,
      else `result_summary["verdict"]`; `metrics_json` =
      `{"max_displacement_value": float (result_summary["max_displacement"]
      ["value"]), "max_von_mises_value": float
      (result_summary["max_von_mises"]["value"]), "solver_error_code": str |
      None, "t3_checks_total": int (len(report["checks"]) if report else 0),
      "t3_checks_failed": int (count of report["checks"] with status !=
      "pass", if report else 0)}`.
  - **010 (`validation_v0`, implemented today):** call
    `record_validation_evidence(workspace_id, candidate_id: str, attempt_id:
    str, report: dict[str, Any], *, report_artifact_id: str) -> str` from
    `loop.py` at the same point it calls
    `finish_attempt(..., validation_verdict=..., report_artifact_id=...)`
    (verified call site: `backend/app/modules/bluecad/loop.py`, the
    build/validate step that consumes `validate.py`'s
    `validate_artifacts`/`write_validation_report` output). Field mapping
    (deterministic, from the report shape in `validate.py`): `verdict` =
    `report["verdict"]` unchanged; `metrics_json` = `{"checks_total":
    len(report["checks"]), "checks_failed": <count of report["checks"] with
    status != "pass">, "tier_max": <max "tier" value across report["checks"],
    or 0 if empty>, "errors_total": len(report["errors"])}`.
- **Reader: extend 042's selection spec, do not create a parallel reader**
  (kernel decision 3). 042's binding kernel (as given, not read from its
  file) is: a typed selection spec over Domain Foundation records (kinds,
  status filter, explicit ids, text query, max per kind) feeding a
  deterministic, char-budgeted context pack with manifest + digest. This
  spec adds `'evidence'` as a fifth allowed value in 042's kind enum (or
  fourth/whatever count 042 lands with — this spec does not know 042's
  final enum and only asserts the new member's name and behavior). Selection
  over `'evidence'` records supports the same fields 042 defines generically
  (status filter maps to `verdict`; explicit ids select by
  `evidence_records.id`; text query matches substring against `kind` or
  `verdict`; max-per-kind caps the count returned for `kind='evidence'`
  specifically, most-recent-`created_at`-first). If 042's actual selection
  spec, once written, uses different field names or a different filter
  algebra than this paragraph assumes, the 042/044 integration point must be
  reconciled at 042 implementation time — flag this explicitly in the
  044 implementer's summary rather than guessing.
- **Pack line format, <= 300 chars, binding** (kernel decision 3). One
  evidence record serializes to exactly one pack line of this form:

  ```
  evidence:<kind> id=<id[:8]> verdict=<verdict> <k1>=<v1> <k2>=<v2> ... src=<report_artifact_id[:8]>
  ```

  Concrete example (a `fem_static_v0` record, corrected to match the real
  `metrics_json` keys above):

  ```
  evidence:fem_static_v0 id=a1b2c3d4 verdict=pass max_displacement_value=2.410 max_von_mises_value=118.300000 t3_checks_total=4 t3_checks_failed=0 src=9f8e7d6c
  ```

  (86 chars as written above — comfortably under the 300-char bound even
  with a worst-case `metrics_json` for any of the three kinds; the
  serializer must **truncate the least significant metric fields with a
  trailing `...` marker**, never truncate `id`/`verdict`/`src`, if a future
  kind's metrics would overflow 300 chars — write this fallback path even
  though no current kind needs it, and cover it with a test using a
  synthetic oversized `metrics_json`). Field order inside `metrics_json` is
  fixed per kind (the order given in each kind's typed schema above) so the
  line is a pure, deterministic function of the record's stored fields —
  no reordering, no locale-dependent number formatting (fixed
  `.` decimal separator, `repr`-stable floats truncated to a fixed number of
  decimals per field, documented per kind).
- **Full report stays in `artifacts`** (kernel decision 4).
  `evidence_records.metrics_json` never contains the full check list, full
  attempt history, or raw solver text — only the headline scalars documented
  above, `verdict`, and the three nullable source pointers plus the
  mandatory `report_artifact_id`. Anything needed beyond those headline
  fields requires reading the artifact.
- Follow existing repo conventions: `sqlite3`/`open_sqlite_connection()`
  pattern from `backend/app/modules/bluecad/ledger.py`, `row_to_model`/
  `rows_to_models` from `app.core.repository`, `utc_now()` from
  `app.modules.events.service`, `uuid4()` string ids — do not introduce an
  ORM.
- No new dependency.

## Acceptance criteria

1. `evidence_records` table exists after running `initialize_database()` on
   a fresh database, with exactly the columns listed in "Design
   constraints", and also exists (via the additive `CREATE TABLE IF NOT
   EXISTS`) when run against a database created before this migration —
   i.e. the migration is additive and idempotent (test-asserted by calling
   `initialize_database()` twice and on both a fresh and a pre-existing
   `schema_migrations` state).
2. `CURRENT_SCHEMA_MIGRATION_ID` and `CURRENT_SCHEMA_MIGRATION_NAME` are
   bumped to a new migration id/name distinct from `0004_...`, and
   `SCHEMA_MIGRATION_RECORDS` contains a matching entry (diff-checkable).
3. Given a fake/fixture `MeshResult` dict matching 008's actual
   `mesh_adapter._result()` shape (pass case with known `counts` and a
   fail case with a `MESH_GROUP_EMPTY` error), `record_mesh_quality_evidence`
   inserts exactly one row with `kind='mesh_quality_v0'`, the documented
   `verdict`, and `metrics_json` containing the exact `elements_total`,
   `nodes_total`, `empty_groups`, and `attempts` values derivable from the
   fixture (test-asserted field-by-field, not just "no exception").
4. Given a fixture built from `solve_static_analysis`'s real return shape
   (`max_displacement`/`max_von_mises` as `{"value": float, ...}` dicts,
   `solver`, `verdict`, `errors`) — pass and error cases — plus, for the pass
   case, a fixture `report` dict from `append_tier3_checks` (with a mix of
   passing and failing `T3_*` checks), `record_fem_static_evidence` inserts
   one row with `kind='fem_static_v0'` and the documented typed
   `metrics_json` fields, correctly reading nested `["value"]` keys rather
   than flat floats.
5. Given a fake validation report dict matching `validate.py`'s actual
   `validate_artifacts()` return shape (pass case and fail case with at
   least one non-passing check), `record_validation_evidence` inserts one
   row with `kind='validation_v0'` and `metrics_json` fields
   (`checks_total`, `checks_failed`, `tier_max`, `errors_total`) matching
   hand-computed expected values from the fixture.
6. Every produced pack line for a `kind='evidence'` selection is <= 300
   characters (test-asserted with `len(line) <= 300` for at least one
   fixture per evidence kind, plus the synthetic-oversized-metrics
   truncation-fallback case).
7. Pack-line serialization is digest-stable: serializing the same
   `EvidenceRecord` twice (or across two Python process runs simulated by
   re-instantiating the serializer) yields byte-identical line text and
   therefore an identical contribution to the pack digest — test-asserted
   by calling the serializer twice and comparing strings, and by hashing a
   two-line pack containing one evidence line twice and comparing digests.
8. A pack selection including `kind='evidence'` alongside at least one other
   kind respects both the per-line 300-char bound and 042's overall char
   budget. 042 is a hard, implemented-first dependency of this spec (expert
   review, 2026-07-06): do NOT build a stand-in pack assembler, in tests or
   otherwise.
9. No evidence-record writer function calls `run_ai_task`, any provider
   adapter class, or anything under `backend/app/modules/runner/`
   (grep-level check, test-asserted or explicitly noted as a manual grep in
   the summary).
10. `backend/app/modules/bluecad/mesh_adapter.py`'s and
    `backend/app/modules/bluecad/loop.py`'s pre-existing behavior
    (arguments, return values, DB rows they already write) is unchanged
    except for the added evidence-hook call — existing 008/010 tests pass
    unmodified.

## Required tests

- `test_evidence_records.py`:
  - Fresh-DB migration creates `evidence_records` with the documented
    columns; running `initialize_database()` twice is idempotent.
  - `record_mesh_quality_evidence` against a fixture `MeshResult` (pass and
    `MESH_GROUP_EMPTY` fail cases) produces the correct typed
    `metrics_json`.
  - `record_fem_static_evidence` against a fixture `ResultSummary`-shaped
    dict (clearly marked as a stand-in for unimplemented 009) produces the
    correct typed `metrics_json`.
  - `record_validation_evidence` against a fixture validation-report dict
    (pass and fail cases) produces the correct typed `metrics_json`.
  - All three writers reject an unknown `kind` value / malformed input with
    a structured error rather than silently inserting a row (fail-closed,
    per `AGENTS.md` invariant 9 — no fabricated verdicts).
- `test_evidence_pack_lines.py` (or folded into the 042 pack test suite once
  it exists):
  - One evidence line per kind is <= 300 chars.
  - Synthetic oversized `metrics_json` triggers the truncation fallback and
    still stays <= 300 chars.
  - Serializing twice yields byte-identical output (digest stability).
  - A multi-line pack containing at least one evidence line and one other
    kind respects a fixed overall budget (via the real 042 pack assembler —
    no stand-in).
- 008 regression: existing `backend/tests/bluecad/test_mesh_adapter.py`
  passes unchanged; add one test showing the mesh-quality evidence hook is
  invoked at the actual call site added by this spec, without altering
  `MeshResult`'s returned shape.
- 010 regression: existing `backend/tests/bluecad/test_loop_*.py` passes
  unchanged; add one test showing the validation evidence hook is invoked
  when `loop.py` finishes an attempt, without altering
  `bluecad_attempts`/`bluecad_candidates` rows.
- All tests offline, no network, no live provider, no running Ollama — fake
  fixtures only, per `AGENTS.md`.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Open questions

- **009 status corrected (2026-07-06, expert review).** The spec-drafting
  agent worked from a stale local branch that predated PR #35 (`Add BLUECAD
  CalculiX FEM adapter`), already merged to `master`. `009 is implemented`:
  `backend/app/modules/bluecad/fem_adapter.py` exists with
  `solve_static_analysis()` and `append_tier3_checks()`. The `fem_static_v0`
  field mapping in Design constraints has been corrected against the real
  code (verified field names, nested `{"value": ...}` shape, no `_mm`/`_mpa`
  suffixes, no `solver_status` field). No further reconciliation with a
  future 009 implementer is needed — the mapping above is final, not a
  contract.
- **008 and 009 share the same integration gap: no call site.** Verified
  2026-07-06: neither `mesh_adapter.mesh_analysis_spec()` nor
  `fem_adapter.solve_static_analysis()`/`append_tier3_checks()` is called
  anywhere in `routes.py`, `service.py`, or `loop.py`. Both exist as tested,
  standalone adapter functions with no wiring into the BLUECAD
  candidate/attempt loop yet — simulation (mesh + FEM) is not yet part of
  the live loop; only build + Tier 0-2 geometric validation runs today. This
  spec's writer hooks (`record_mesh_quality_evidence`,
  `record_fem_static_evidence`) are therefore genuinely uncallable from
  production code until a caller exists for each adapter. The 044
  implementer must report this as a blocking conflict per `AGENTS.md`'s
  "stop and report" rule rather than inventing a call site for either
  adapter — this spec's own tests exercise the writer functions directly
  against fixtures, which remains valid regardless of the wiring gap.
- **042 has no file yet.** This spec was explicitly instructed not to depend
  on reading it and to treat its binding kernel (typed selection spec: kinds,
  status filter, explicit ids, text query, max per kind, feeding a
  deterministic char-budgeted pack with manifest + digest) as given. The
  exact selection-field names, the pack assembler's module location, its
  manifest/digest format, and its overall char-budget mechanism are
  therefore unknown to this spec. Acceptance criterion 8 provides a
  fallback (a local stand-in assembler) so this spec's tests do not block
  on 042 landing first; the real integration (adding `'evidence'` to 042's
  actual kind-dispatch code) must happen either as part of 044's
  implementation if 042 has landed by then, or as a small follow-up once it
  does, whichever comes first — flag this explicitly rather than guessing
  042's internals.
- **`docs/specs/README.md`'s index table**: reconciled directly on `master`
  2026-07-06 (009, 015, 018 statuses corrected; rows added for 040-044) as
  part of landing this spec batch — no longer an open item.
- **Retry/multi-attempt mesh results**: 008's `MeshResult` can contain up to
  two `attempts` entries (the deterministic halved-size retry). This spec's
  `mesh_quality_v0` mapping reads counts from the **last** attempt only
  (the one that determined the final verdict). This seems like the correct
  headline choice but was not explicitly specified in 008 or the kernel
  description, so it is called out here rather than assumed silently.

## Review resolutions (2026-07-06 — expert review, binding)

1. (009 status) Corrected: 009 is implemented (PR #35, already on `master`
   before this spec batch was drafted — the drafting agent worked from a
   stale local branch). The `fem_static_v0` field mapping is rewritten above
   against the real, verified `fem_adapter.py` code — it is final, not a
   contract for a future implementer to reconcile.
2. (042 dependency) Hardened: 042 must be implemented before 044 starts. The
   stand-in pack assembler variant is removed from acceptance criterion 8 and
   the tests — integrate against the real assembler only.
3. (mesh AND fem call-site gap) Confirmed binding, extended to both adapters:
   if no route/service call site persists `MeshResult` or FEM
   `ResultSummary`/`report` as artifacts when 044 is implemented, stop and
   report for whichever adapter(s) lack one — do not invent a call site.
4. (README index staleness) Fixed directly on `master` as part of this batch.
5. (last-attempt mesh metrics) Approved: headline metrics come from the last
   attempt only, the one that determined the final verdict.
