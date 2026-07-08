# 038 — SIM-WIRE: wire mesh + FEM into the candidate/attempt loop

Status: ready (implement after 044 merges; drafted 2026-07-07 from expert
kernel, expert review resolutions written same day — see final section)
Depends on: 044 (hard dependency — `evidence_records` table and writer hooks
must exist and be merged before this spec starts; do not build a stand-in).
Also assumes 008 and 009 remain as implemented and verified below, and reads
010's actual loop code, not just its spec.

## Goal

After this slice, a BLUECAD loop invocation that opts in to simulation runs
the Gmsh mesh adapter (008) and the CalculiX static FEM adapter (009) as a
post-validation stage on any attempt whose Tier 0–2 geometry validation
passed. Mesh and solve outcomes — pass, fail, or adapter error — are recorded
as `evidence_records` rows via 044's hooks and never crash or block the rest
of the loop. Simulation stays fully advisory: nothing about candidate status,
`valid`/`parked` outcome, or promotion changes as a result of a sim verdict.

## Why

008 and 009 are implemented, tested, and — as of 2026-07-06 — called by
nothing (`docs/specs/044-evidence-bridge-1.md`'s Open Questions, confirmed
independently below): `mesh_adapter.mesh_analysis_spec()` and
`fem_adapter.solve_static_analysis()`/`append_tier3_checks()` have no caller
anywhere in `routes.py`, `service.py`, or `loop.py`. This is the exact gap
the beta program's Phase A names: "the loop that already builds + validates
geometry must also simulate and record, deterministically"
(`docs/strategy/JARVISOS_BETA_PROGRAM.md`, item 038). 044 gives mesh/FEM
outcomes a typed, token-cheap home in evidence; this spec is the missing
wire between the loop and the adapters that produce those outcomes, so a
validated geometry candidate can also carry a structural verdict without any
new orchestration layer, model call, or auto-promotion path
(`AGENTS.md` invariant 8).

## Scope

In scope:
- A opt-in simulate stage appended to `create_bluecad_candidate`
  (`backend/app/modules/bluecad/loop.py`), run only for an attempt whose
  build/validate step already produced `validation_verdict == "pass"`
  (i.e. the same point the loop currently calls `mark_candidate_valid` for a
  passing attempt).
- Calling `mesh_analysis_spec(...)` (008,
  `backend/app/modules/bluecad/mesh_adapter.py`) then, only if meshing
  produces a usable mesh, `solve_static_analysis(...)` and (when pass
  criteria are present) `append_tier3_checks(...)` (009,
  `backend/app/modules/bluecad/fem_adapter.py`), using the candidate's own
  build outputs (STEP + manifest already registered by `_build_and_register`)
  as the AnalysisSpec's `geometry` block.
- Recording every sim outcome (mesh pass/fail/error, solve pass/error) as an
  `evidence_records` row via 044's `record_mesh_quality_evidence(...)` and
  `record_fem_static_evidence(...)` hooks, passing `candidate_id`,
  `attempt_id`, and a `source_run_id` per kernel decision 4.
- A new opt-in field on the loop request schema (`BluecadCandidateCreate` /
  `BluecadLoopConfig` in `backend/app/modules/bluecad/models.py`) that
  defaults to off — see Design constraints for the exact proposed field and
  the open question on where the AnalysisSpec content (material, bcs, loads,
  pass_criteria) comes from when the flag is set.
- Determinism metadata in the evidence `metrics_json`/detail: mesh target
  size, mesh/solver tool versions (from the 007 registry's `version_pin`,
  already present in `MeshResult`/`ResultSummary`), so the same input
  produces the same recorded mesh settings.
- Unit tests with both adapters mocked/faked (no real gmsh/CalculiX
  binaries), plus one integration test under the real-solver pytest marker(s)
  that runs one tiny end-to-end case: brief → build → validate → mesh →
  solve → evidence rows exist.

Out of scope (binding non-goals):
- No modal or thermal analysis (009 is static-only in this slice; modal/
  thermal are spec 027).
- No UI/frontend changes.
- No flowsheet or recompute logic (specs 050/051).
- No auto-promotion of any kind: a sim `fail`/`error` verdict never blocks
  promotion, and a sim `pass` never auto-promotes. `create_decision` remains
  uncalled from `loop.py` and from this stage.
- No changes to the 008/009 adapter internals beyond what wiring strictly
  requires (e.g. no new adapter parameters unless the AnalysisSpec-sourcing
  open question below forces a minimal one — flag any such change loudly in
  the implementation notes rather than doing it silently).
- No new orchestration layer, job queue, background worker, or async
  execution path. The sim stage runs synchronously, in-process, in the same
  call stack as `create_bluecad_candidate`'s existing build/validate step.
- No `simulation_runs`-parallel table: if a `simulation_runs` row is needed
  as `source_run_id`, use the existing `simulation_runs` table
  (`backend/app/core/schema.py`); creating a second table for the same
  purpose is forbidden.

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing.

- `backend/app/modules/bluecad/loop.py` — add the post-validation sim stage
  inside/after `create_bluecad_candidate`'s pass-verdict branch (around the
  `if verdict == "pass":` block, currently lines 127–129).
- `backend/app/modules/bluecad/models.py` — add the opt-in flag (see Design
  constraints) to `BluecadLoopConfig` and/or `BluecadCandidateCreate`.
- `backend/app/modules/bluecad/mesh_adapter.py`,
  `backend/app/modules/bluecad/fem_adapter.py` — call sites only; no adapter
  logic changes expected (008/009 are otherwise frozen by this spec).
- `backend/app/modules/bluecad/evidence.py` (044) — call only
  `record_mesh_quality_evidence(...)` / `record_fem_static_evidence(...)`;
  do not modify 044's writer functions from this spec.
- `backend/app/modules/bluecad/ledger.py` — likely needs a small addition if
  attempt/candidate rows should reference the sim outcome (e.g. a
  `source_run_id` on the attempt, or a new nullable column) — verify whether
  `bluecad_attempts` needs an additive column or whether evidence rows alone
  (linked by `attempt_id`) are sufficient; do not add a column speculatively.
- `backend/tests/bluecad/test_loop_*.py` (extend) and/or a new
  `backend/tests/bluecad/test_loop_sim_wire.py`.

## Design constraints

- **Opt-in field (kernel decision 2 — verify exact name/shape at
  implementation).** `BluecadCandidateCreate` currently has only
  `brief_text` and `loop_config: BluecadLoopConfig | None`
  (`backend/app/modules/bluecad/models.py:150-152`); `BluecadLoopConfig` has
  `max_attempts_per_tier`, `tier_ladder`, `max_output_tokens`,
  `per_call_timeout_s` (`models.py:143-147`) — no simulate/analysis flag
  exists today. This spec proposes adding `simulate: bool = False` to
  `BluecadLoopConfig` (loop-scoped, consistent with how attempt/tier policy
  already lives there) rather than to `BluecadCandidateCreate` directly,
  since `loop_config` is already the "policy as data" home
  (`docs/specs/010-bluecad-ai-loop-v0.md` Scope). Default is `False` (opt-in,
  per kernel decision 2). Spec 021 (alpha gate, not yet drafted) and the
  workbench UI are the intended callers that set it `True`. **This exact
  field name/location is a proposal, not settled** — confirm against
  whatever `BluecadLoopConfig`/`BluecadCandidateCreate` actually look like at
  implementation time, since 010 or an intervening spec may have changed
  them. **Superseded by Review resolution 1**: the opt-in is the presence of
  a caller-supplied `analysis_spec`, not a separate boolean.
- **Where the AnalysisSpec comes from — unresolved, flag at
  implementation.** 008/009's `mesh_analysis_spec`/`solve_static_analysis`
  both require a full `AnalysisSpec` object
  (`schemas/bluecad_analysis_spec_v0_1.schema.json`): `geometry`
  (`step_path`, `manifest_path` — available from the candidate's own build
  artifacts), but also `material` (E, nu, rho, yield_strength), `bcs`,
  `loads` (both addressed by port labels), `mesh.target_size`, and
  `pass_criteria` — **none of which exist anywhere in the current
  `GeometrySpec`/loop/candidate data model.** `BLUECAD_CORE_DESIGN.md` §7
  states "the AI proposes *AnalysisSpec* changes" as the intended future
  mechanism, but no spec has implemented AnalysisSpec generation (by AI, by
  a template, or by caller-supplied data) yet — this is a distinct, prior
  gap from the mesh/FEM call-site gap 044 already flagged. This spec's scope
  is strictly "wire the adapters into the loop once given an AnalysisSpec";
  it explicitly does NOT invent AnalysisSpec generation. Two non-exclusive
  options for the implementer to evaluate against whatever the loop caller
  looks like at implementation time: (a) the opt-in caller (021/workbench)
  supplies a complete `AnalysisSpec` alongside the `simulate` flag, and this
  spec only threads it through; or (b) a minimal deterministic default
  AnalysisSpec is synthesized from the candidate's manifest ports (fixed
  material constants, default `target_size`, no `pass_criteria`) — but this
  would be new logic beyond "wiring" and must be called out explicitly and
  confirmed with the maintainer rather than assumed. **Resolved — see Review
  resolution 1: option (a), caller-supplied.**
- **Post-validation stage only (kernel decision 1).** The sim stage runs
  only for the attempt that produced `validation_verdict == "pass"` — i.e.
  only on the terminal, `valid`-bound attempt, mirroring where
  `mark_candidate_valid(candidate.id)` is currently called
  (`backend/app/modules/bluecad/loop.py:127-129`). A `fail` verdict on
  geometry validation never reaches the sim stage (matches kernel decision 1:
  "Attempts whose geometry validation passes MAY proceed").
- **Failure semantics (kernel decision 3 / AGENTS.md blast-radius rule).**
  Every call into `mesh_analysis_spec`/`solve_static_analysis` is wrapped so
  that a mesh or solve failure — including adapter-raised exceptions,
  `ToolRegistryError`, or any `verdict in {"fail", "error"}` result — is
  caught and recorded as a typed, non-crashing outcome. The candidate's own
  status/verdict path (`valid` from geometry validation) is unaffected; sim
  failure never re-parks a candidate that already reached `valid`. This
  means the sim stage must run *after* `mark_candidate_valid` (or in a way
  that guarantees an exception inside it cannot prevent that call), and any
  exception raised by the sim stage itself must be caught at the sim-stage
  boundary, not allowed to propagate out of `create_bluecad_candidate`.
- **Evidence (kernel decision 4).** Both success and failure sim outcomes
  call 044's hooks: `record_mesh_quality_evidence(workspace_id, result:
  dict, *, source_run_id, report_artifact_id)` and
  `record_fem_static_evidence(workspace_id, result_summary: dict, report:
  dict | None, *, source_run_id, report_artifact_id)` — **exact signatures
  must be re-verified against `backend/app/modules/bluecad/evidence.py` once
  044 lands** (see Open questions; this spec was drafted against 044's
  design document, not merged code). This spec's job is to supply
  `candidate_id`/`attempt_id`/`source_run_id`; 044 owns `evidence_records`
  storage and the `report_artifact_id` contract (mesh/FEM report JSON must
  first be registered as an `artifacts` row via the existing
  `register_artifact(...)` helper in `ledger.py`, same pattern
  `_build_and_register` already uses for the validation report). Per SC-1
  (`docs/strategy/JARVISOS_BETA_PROGRAM.md`), evidence writes are expected to
  also carry the normalized `"<kind>:<id>"` provenance ref (e.g.
  `candidate:<id>`, `attempt:<id>`, `sim_run:<id>`) alongside the typed FK
  columns — verify whether 044, once merged, already produces this
  normalized ref internally (per the SC-1 "Action (2026-07-07)" amendment)
  or whether this spec's call sites must pass it explicitly.
- **Determinism (kernel decision 5).** Mesh `target_size`, the mesh/solver
  tool `version_pin` values (already present in `MeshResult["attempts"]`'s
  implicit tool call and `ResultSummary["solver"]["version"]` — see
  `fem_adapter.py:71`), and any AnalysisSpec content used are recorded in the
  evidence metrics (044 field mapping already reads
  `result_summary["solver"]`; this spec adds no new nondeterministic
  meshing — the existing 008 deterministic halved-size retry is the only
  variability, and it is already recorded per-attempt in `MeshResult`).
- **No new orchestration (kernel decision 6).** 010's loop is fully
  synchronous, in-process Python function calls — no `ai_jobs`/
  `run_ai_task` involvement for the 008/009 calls (verified: `mesh_adapter.py`
  and `fem_adapter.py` both call the subprocess tool registry
  (`registry.run_tool`/`resolve_tool`) directly, with no AI/provider
  involvement at all). The sim stage must follow the exact same pattern as
  the existing build/validate step in `_build_and_register` — a plain
  function call inside `create_bluecad_candidate`, writing artifacts via
  `register_artifact`, no new queue, table-poller, or background thread.
- **Hard dependency (kernel decision 7).** This spec cannot be implemented
  until `docs/specs/044-evidence-bridge-1.md` is merged: `evidence.py` does
  not exist in the tree as of this drafting (verified:
  `backend/app/modules/bluecad/evidence.py` is absent). Do not write a
  temporary stand-in evidence writer "until 044 lands" — that is explicitly
  forbidden. 044's function signatures, field mappings, and whether it
  already includes the SC-1 normalized ref must be re-verified against the
  actual merged `evidence.py` at implementation time, not assumed from
  044's spec text.
- **Reuse existing tests/fixtures.** 008/009 already have offline fake-tool
  fixtures (`backend/tests/bluecad/test_mesh_adapter.py`,
  `backend/tests/bluecad/test_fem_adapter.py`) and real-tool marker suites
  (`bluecad_gmsh`, `bluecad_ccx` — both registered in `backend/pytest.ini`).
  This spec's tests should reuse those fixture patterns rather than
  inventing new fake-gmsh/fake-ccx harnesses.

## Acceptance criteria

1. `BluecadLoopConfig` (or wherever the implementer places it, if the
   proposed location is wrong — see Design constraints) gains an opt-in
   simulate flag, default `False`; a candidate created without it set (or
   with it explicitly `False`) never calls `mesh_analysis_spec` or
   `solve_static_analysis` — grep/behavior-level check.
2. A candidate created with the flag set `True`, whose attempt reaches
   `validation_verdict == "pass"`, triggers exactly one mesh call and
   (mesh success) one solve call for that attempt; no sim call occurs for
   attempts that fail geometry validation.
3. A fake/mocked mesh adapter returning `verdict: "fail"` (e.g.
   `MESH_GROUP_EMPTY`) results in one `evidence_records` row via
   `record_mesh_quality_evidence`, no unhandled exception, no change to the
   candidate's `valid` status, and no solve call attempted.
4. A fake/mocked FEM adapter returning `verdict: "error"` (e.g.
   `SOLVE_ERROR`) results in one `evidence_records` row via
   `record_fem_static_evidence`, no unhandled exception, and no change to
   the candidate's `valid` status.
5. A fake/mocked mesh + solve success path produces two `evidence_records`
   rows (`mesh_quality_v0` and `fem_static_v0`), each with `candidate_id`
   and `attempt_id` populated and a `report_artifact_id` pointing at a real,
   registered `artifacts` row.
6. No sim-stage code path calls `create_decision`, sets
   `promoted_decision_id`, or otherwise promotes a candidate — grep-level
   check, consistent with 010's existing acceptance criterion 6.
7. No sim-stage code path uses `run_ai_task`, `ai_jobs`, or any
   provider/adapter mechanism — grep-level check (mirrors 044's acceptance
   criterion 9 for its own hooks).
8. Determinism: given the same fake mesh/solve responses, running the loop
   twice produces identical evidence `metrics_json` content (excluding ids
   and timestamps) — same pattern as 010's existing determinism acceptance
   criterion 7.
9. At least one integration test under the repo's real-solver pytest
   marker(s) (`bluecad_gmsh` and/or `bluecad_ccx`, as registered in
   `backend/pytest.ini`) runs one tiny end-to-end case — brief → build →
   validate → mesh → solve → evidence rows exist — skipped when the
   corresponding real tool is not registry-enabled, matching 008/009's
   existing marker-skip pattern.
10. Existing 010 loop tests (`backend/tests/bluecad/test_loop_*.py`) and
    008/009 adapter tests pass unmodified.

## Required tests

- Unit tests with both adapters mocked/faked (CI-safe, no gmsh/CalculiX
  binaries needed):
  - simulate flag off → adapters never called;
  - simulate flag on, mesh fail → one evidence row, no solve call, no
    exception, candidate stays `valid`;
  - simulate flag on, mesh pass + solve error → two evidence rows (mesh
    pass, fem error), no exception, candidate stays `valid`;
  - simulate flag on, mesh pass + solve pass (+ Tier 3 checks, both a
    passing and a failing criterion) → two evidence rows, `candidate_id`/
    `attempt_id` populated, `report_artifact_id`s resolve to real artifact
    rows;
  - determinism: two runs with identical fake adapter responses produce
    byte-identical (ids/timestamps excluded) evidence `metrics_json`.
- One integration test under the existing real-solver pytest marker(s)
  (`bluecad_gmsh`/`bluecad_ccx`) exercising the full brief → build →
  validate → mesh → solve → evidence chain on a tiny fixture geometry,
  skipped when the real tool is not registry-enabled.
- Regression: existing `test_loop_*.py`, `test_mesh_adapter.py`,
  `test_fem_adapter.py` pass unmodified.
- All non-marker tests offline, no network, no live provider, no running
  Ollama, per `AGENTS.md`.

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Open questions / verify at implementation

- **044 must be re-verified, not assumed.** This spec was drafted while 044
  is still `Status: ready` (not merged) and `backend/app/modules/bluecad/
  evidence.py` does not exist. `record_mesh_quality_evidence` and
  `record_fem_static_evidence`'s exact signatures, return types, and
  whether they already emit the SC-1 normalized `"<kind>:<id>"` provenance
  ref must be re-checked against the actual merged file before writing any
  call site. If 044 lands with different signatures than
  `docs/specs/044-evidence-bridge-1.md` documents (e.g. because 042's real
  shape forced a change), this spec's Design constraints section is wrong
  and must be corrected against the real code, not patched around.
- **AnalysisSpec authorship is an unresolved prior gap.** As detailed in
  Design constraints, no existing spec or code produces the `material`/
  `bcs`/`loads`/`pass_criteria`/`mesh.target_size` fields an AnalysisSpec
  needs. This spec assumes the opt-in caller (021/workbench) supplies this
  data, but neither 021 nor a workbench AnalysisSpec-authoring UI exists yet
  (021 is only an index entry in `JARVISOS_BETA_PROGRAM.md`, not a drafted
  spec, and depends on 038 — i.e. 038 is upstream of 021, so 021 cannot be
  the thing that supplies 038's missing input at 038's own implementation
  time). The implementer must stop and report this sequencing gap rather
  than fabricating a default AnalysisSpec, unless the maintainer has by
  then authorized a specific minimal-default approach.
- **Whether `bluecad_attempts`/`bluecad_candidates` need an additive
  column.** 010's schema has no field pointing an attempt at a sim outcome
  today. If evidence rows are sufficient (queryable by `attempt_id` alone,
  per 044's schema), no schema change is needed here; if the workbench (006)
  or a later spec needs a fast "did this attempt simulate, and with what
  verdict" read without joining `evidence_records`, an additive column may
  be justified — but that is a UI-driven decision this spec should not make
  unilaterally. Flag the choice made in the implementation notes.
- **`source_run_id` sourcing.** Kernel decision 4 says 038 "passes ids; 044
  owns storage," and mentions honoring 044's `source_run_id` field. The
  existing `simulation_runs` table (`backend/app/core/schema.py`) is a
  candidate for this id, but nothing in 010's loop currently creates a
  `simulation_runs` row for a BLUECAD attempt (`simulation_runs` today is
  written by `backend/app/modules/modeling/service.py` and
  `backend/app/modules/runner/service.py`, both unrelated call paths). The
  implementer must decide, and report, whether the sim stage (a) creates a
  `simulation_runs` row per mesh/solve call to use as `source_run_id`, or
  (b) leaves `source_run_id` null and relies on `candidate_id`/`attempt_id`
  alone (044's schema marks `source_run_id` nullable) — do not invent a new
  table for this purpose (binding non-goal).
- **Real-solver marker choice for the integration test.** Both `bluecad_gmsh`
  and `bluecad_ccx` markers exist (`backend/pytest.ini`); the end-to-end
  case in acceptance criterion 9 needs both tools enabled to reach a solve
  outcome. Confirm at implementation time whether the test should be marked
  with both (`@pytest.mark.bluecad_gmsh` and `@pytest.mark.bluecad_ccx`) or
  a new combined marker is warranted — prefer reusing both existing markers
  over adding a third unless test collection requires otherwise.

## Review resolutions (2026-07-07, expert review)

1. **AnalysisSpec authorship: caller-supplied (option (a)), settled.** The
   opt-in mechanism is not a `simulate: bool` — it is an optional
   `analysis_spec` object on `BluecadLoopConfig` (validated against
   `schemas/bluecad_analysis_spec_v0_1.schema.json`, minus the `geometry`
   block). Presence = opt-in; absence = no sim stage; the invalid state
   "simulate requested without analysis data" cannot exist. The loop fills
   the `geometry` block (`step_path`, `manifest_path`) from the attempt's
   own registered build artifacts. BC/load port labels that do not resolve
   against the built geometry's manifest are a recorded sim failure with a
   typed reason, not a crash — consistent with kernel decision 3. Callers:
   021's gate script and this spec's own tests supply fixture AnalysisSpecs;
   the workbench UI later; AI-proposed AnalysisSpec (`BLUECAD_CORE_DESIGN.md`
   §7) remains a separate future spec. Acceptance criteria 1–2 read "flag
   set" as "`analysis_spec` present". This resolves the sequencing gap in
   Open questions: 021 supplies the AnalysisSpec at *invocation* time, so
   nothing upstream of 038 is needed at 038's implementation time.
2. **`source_run_id`: create a `simulation_runs` row per sim invocation.**
   Reuse the existing `simulation_runs` table, mirroring the existing insert
   pattern (`backend/app/modules/runner/service.py` /
   `modeling/service.py` — verify at implementation); the row's id is the
   `source_run_id` passed to 044's hooks, so SC-1's `sim_run:<id>` node
   exists in the provenance graph. No new table.
3. **No additive column on `bluecad_attempts`/`bluecad_candidates` in this
   slice.** Evidence rows queried by `attempt_id` are sufficient; a
   fast-read sim-status column is a UI-driven decision deferred to the spec
   that needs it (006/020/055).
4. **The integration test carries both existing markers** (`bluecad_gmsh` +
   `bluecad_ccx`); no third combined marker.
