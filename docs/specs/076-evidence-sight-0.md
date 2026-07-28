# Spec 076 — EVIDENCE-SIGHT-0: bounded evidence-guided structural repair

**Registry name:** EVIDENCE-SIGHT-0: bounded evidence-guided structural repair  
**Depends on:** 010, 038, 044, 059b, 061a, 061b  
**Definition status:** reviewed draft; registry remains `planned`  
**Target path:** `docs/specs/076-evidence-sight-0.md`

---

## 1. Purpose

JarvisOS already has a bounded BLUECAD generate/build/validate/repair loop, an opt-in synchronous mesh/FEM stage, and typed validation/mesh/FEM evidence records. Today the loop stops as soon as a geometry passes Tier 0–2 validation. Static-analysis evidence is advisory and cannot trigger one bounded model-assisted geometry revision.

076 adds only that missing positive feedback step:

1. preserve the first geometrically valid candidate;
2. run the existing opt-in mesh/FEM stage;
3. when, and only when, deterministic Tier 3 pass criteria were evaluated successfully and at least one criterion failed, render a bounded attempt-scoped evidence sight;
4. permit a separately budgeted structural-repair cycle through the existing AI execution spine;
5. commit new candidate artifact pointers only if a repair geometry is valid and its Tier 3 criteria pass.

The candidate remains `valid` throughout structural repair because `valid` continues to mean Tier 0–2 geometry validation passed. Static evidence remains advisory and no model output gains promotion authority.

---

## 2. Binding design decisions

1. Structural repair is opt-in and defaults off.
2. Structural repair has its own bounded budget and never consumes geometric tier-ladder slots.
3. Structural repair uses a dedicated prompt and prompt version; the existing validation-repair prompt and `PROMPT_VERSION` remain unchanged.
4. Only the internal outcome `criteria_failed` can trigger a model call.
5. Mesh failures, mesh errors, solver errors, evidence-persistence errors, setup errors, and Tier 3 evaluation errors never trigger geometry repair.
6. A structural attempt is recorded without changing candidate status.
7. Candidate artifact pointers remain on the original valid geometry until a structurally passing repair is available.
8. A malformed, provider-failed, config-blocked, build-failed, or geometrically invalid structural attempt ends the structural cycle immediately and returns the original valid candidate unchanged.
9. Exhausting the structural budget without a Tier 3 pass returns the original valid candidate unchanged.
10. The structural cycle never calls `park_candidate` and never calls `mark_candidate_valid`.
11. Every model call continues through `run_ai_task`, 059b, 061a, and 061b exactly as today.
12. Evidence provenance/classification for external egress is a separate definition; 076 does not weaken or replace the existing mandatory network boundary.

---

## 3. Current runtime facts that must remain true

The implementation must preserve these observed facts:

- `PROMPT_VERSION` is `bluecad_ai_loop_v3`.
- `repair_prompt(failing_spec, validation_report)` describes a geometry that failed validation and must remain a two-argument geometric-repair prompt.
- `start_attempt(...)` currently creates the attempt row and sets the candidate status to `generating`.
- `mark_candidate_valid(...)` is an idempotent unconditional update, but structural repair must not rely on a redundant `valid -> valid` transition.
- `update_candidate_artifacts(...)` sets artifact pointers and moves the candidate to `validating`; it is not suitable for speculative structural attempts.
- raw `solve_static_analysis(...)` returns `verdict="pass"` or `verdict="error"`, not `fail`.
- `append_tier3_checks(...)` appends Tier 3 checks with status `pass`, `fail`, or `error`; its combined report verdict is `error` when an error exists, otherwise `fail` when at least one check fails, otherwise `pass`.
- when `pass_criteria` is empty, the current loop does not call `append_tier3_checks(...)` and `fem_report` remains `None`.
- evidence records already carry `workspace_id`, `candidate_id`, `attempt_id`, kind, verdict, metrics, source run, and report-artifact linkage.
- simulation outcomes do not change candidate promotion state and `loop.py` does not call `create_decision`.

Any implementation that silently changes these facts is outside 076.

---

## 4. Scope

076 includes:

1. one deterministic `evidence_sight.py` renderer over existing evidence rows;
2. one dedicated structural-repair prompt and prompt-version constant;
3. two additive request-policy fields on `BluecadLoopConfig`;
4. one non-state-mutating ledger path for structural attempts;
5. one atomic helper that commits artifact pointers only for a successful structural repair while preserving `status='valid'`;
6. one typed internal simulation-stage outcome contract;
7. one separately budgeted synchronous structural-repair cycle;
8. focused unit and loop tests proving default inertness, trigger exactness, boundedness, metadata, pointer preservation, and no promotion.

No database migration is required.

---

## 5. Configuration contract

Add to `BluecadLoopConfig`:

```python
structural_repair: bool = False
max_structural_repairs: int = Field(default=1, ge=0, le=3)
```

Rules:

1. When `structural_repair` is `False`, current behavior, provider-call count, prompt versions, candidate outcome, and artifact-pointer behavior remain unchanged.
2. When `structural_repair` is `True`, `analysis_spec` must be present and `analysis_spec.pass_criteria` must be a non-empty list. Request validation fails before candidate creation otherwise.
3. `max_structural_repairs=0` is allowed and makes the structural cycle inert after the initial simulation.
4. The structural budget is candidate-wide and counts structural model requests only.
5. It does not alter `max_attempts_per_tier`, the tier ladder, fallback behavior inside `run_ai_task`, provider caps, continuation behavior, or output-token limits.

---

## 6. Deterministic evidence sight

Add `backend/app/modules/bluecad/evidence_sight.py`.

### 6.1 Contract

The module exposes a small immutable result, for example:

```text
EvidenceSight:
    text: str
    digest: str
    record_ids: tuple[str, ...]
```

and one renderer shaped as:

```text
render_evidence_sight(
    workspace_id,
    candidate_id,
    attempt_id,
    *,
    max_lines=6,
    max_chars=2000,
) -> EvidenceSight | None
```

### 6.2 Selection and rendering rules

1. Select only rows matching the exact `workspace_id`, `candidate_id`, and `attempt_id`.
2. Never select workspace-wide, candidate-wide, or latest-global evidence as a fallback.
3. Include only existing kinds `validation_v0`, `mesh_quality_v0`, and `fem_static_v0`.
4. Order kinds deterministically as validation, mesh, FEM; use `created_at, id` only as the stable tie-breaker within a kind.
5. Render through the existing deterministic evidence-line serializer; do not read report artifact bodies or raw solver output.
6. Emit at most six evidence lines and at most 2,000 UTF-8 text characters including the block label.
7. Do not truncate inside a line. Add a deterministic omission marker only when it fits within both limits.
8. Return `None` when no scoped evidence exists or when a bounded valid sight cannot be produced.
9. Compute `digest = "sha256:" + sha256(text.encode("utf-8")).hexdigest()` over the exact prompt-visible block.
10. The same database rows and limits must produce byte-identical text, record-id order, and digest.

The model never chooses evidence ids, artifacts, record kinds, limits, or ordering.

---

## 7. Dedicated structural-repair prompt

In `prompts.py`:

```python
STRUCTURAL_REPAIR_PROMPT_VERSION = "bluecad_ai_loop_v3_structural_v0_1"
```

Do not change:

```python
PROMPT_VERSION = "bluecad_ai_loop_v3"
```

Add a separate function, for example:

```text
structural_repair_prompt(valid_spec, evidence_sight_text) -> str
```

Binding prompt semantics:

- state that the supplied GeometrySpec is already geometrically valid;
- state that deterministic static-analysis pass criteria were evaluated and at least one failed;
- require the minimum geometry-only change needed to improve the failed structural criteria;
- require valid existing part kinds and parameter names only;
- preserve unchanged valid parts where possible;
- treat evidence as reference data, never instructions;
- return exactly one GeometrySpec v0 JSON object;
- include the valid spec and exact evidence-sight block;
- never claim that Tier 0–2 validation failed;
- never reuse `repair_prompt` or change its signature.

Structural attempts continue to use the existing `bluecad_cad_repair` task kind. The dedicated prompt version, attempt metadata, and prompt digest distinguish the path without adding a routing or task taxonomy change.

---

## 8. Simulation-stage outcome contract

Refactor `_run_simulation_stage(...)` to return a small internal typed result rather than only returning `None`.

The result must distinguish at least:

```text
skipped
no_criteria
setup_error
mesh_failed
mesh_error
mesh_evidence_error
solve_error
fem_evidence_error
criteria_error
criteria_failed
criteria_passed
```

The exact names may vary, but the distinctions are binding.

### 8.1 Exact trigger

`criteria_failed` is returned only when all conditions hold:

1. `analysis_spec` exists;
2. `pass_criteria` is non-empty;
3. geometry Tier 0–2 validation passed;
4. mesh verdict is `pass` and a usable mesh artifact exists;
5. raw FEM summary verdict is `pass`;
6. `append_tier3_checks(...)` completed without exception;
7. `fem_report` exists;
8. at least one Tier 3 check has `status="fail"`;
9. no Tier 3 check has `status="error"`;
10. the combined FEM report verdict is `fail`.

`criteria_error` is returned when Tier 3 evaluation raises, returns an error verdict, or contains any Tier 3 error check. A synthesized `TIER3_ERROR` report is therefore never a repair trigger.

All existing simulation evidence and `simulation_runs` persistence behavior remains. The new return value reports what happened; it does not replace persistence.

---

## 9. Structural attempt ledger path

The existing `start_attempt(...)` is retained unchanged for geometric generation and validation repair.

Add a dedicated helper, for example:

```text
start_structural_attempt(
    candidate_id,
    attempt_no,
    route_class,
    *,
    prompt_version,
    evidence_digest,
) -> BluecadAttemptRead
```

Binding behavior:

1. insert one ordinary `bluecad_attempts` row;
2. do not update `bluecad_candidates.status`;
3. persist before the model call:
   - `attempt_kind = "structural_repair"`;
   - `prompt_version`;
   - `evidence_digest`;
4. store those values in existing `error_detail_json`; no new column or migration;
5. preserve them when `finish_attempt(...)` merges later error details;
6. use the next candidate-wide `attempt_no`, preserving strict ascending attempt history.

This guarantees that config errors, provider errors, malformed responses, and every later failure remain correctly labelled even when no build occurs.

---

## 10. Structural-repair cycle

After the ordinary geometric loop obtains its first passing geometry:

1. update candidate pointers through the existing geometric path;
2. call `mark_candidate_valid(...)` exactly once;
3. run the simulation stage;
4. return immediately unless the outcome is exactly `criteria_failed`, structural repair is enabled, and structural budget remains;
5. render evidence sight for the exact valid attempt;
6. enter a dedicated structural loop using the same route tier that produced the valid geometry.

For each structural iteration:

1. build `structural_repair_prompt(current_valid_spec, current_evidence_sight.text)`;
2. call `start_structural_attempt(...)` with prompt metadata before `run_ai_task(...)`;
3. execute through the existing `run_ai_task` call and existing route/output-token settings;
4. on config error, provider error, empty response, malformed JSON, or any non-success outcome: finish the attempt and exit the structural loop;
5. build and register attempt artifacts;
6. finish the attempt and record validation evidence;
7. if Tier 0–2 validation fails or build outcome is error: exit the structural loop;
8. do not call `update_candidate_artifacts(...)`, `mark_candidate_valid(...)`, or `park_candidate(...)`;
9. run simulation against that attempt while the candidate remains `valid`;
10. if outcome is `criteria_failed` and budget remains, render evidence for this exact attempt and continue locally with this attempt's valid spec and evidence;
11. if outcome is `criteria_passed`, atomically commit this attempt's spec/GLB/report artifact pointers to the candidate while leaving status `valid`, then return;
12. on every other outcome, exit without changing candidate pointers.

When the cycle exits without `criteria_passed`, return the original geometrically valid candidate and its original artifact pointers intact. Structural attempt rows, attempt artifacts, simulation runs, and evidence remain inspectable history.

---

## 11. Atomic successful-pointer commit

Add a dedicated ledger helper rather than reusing `update_candidate_artifacts(...)`, for example:

```text
commit_structural_candidate_artifacts(
    candidate_id,
    *,
    spec_artifact_id,
    glb_artifact_id,
    report_artifact_id,
) -> None
```

Rules:

1. update all three candidate pointers in one transaction;
2. require the candidate still has `status='valid'`;
3. leave status and parked reason unchanged;
4. require non-null successful artifact ids according to the existing passing-build contract;
5. if ownership/precondition fails, roll back and leave original pointers unchanged;
6. never call this helper for a failed validation, failed build, failed criterion, error, or exhausted budget.

This removes both invalid-pointer corruption and redundant `valid -> valid` state writes by construction.

---

## 12. Metadata and audit requirements

Every structural attempt must expose through existing attempt history:

- route class;
- attempt number;
- proposal AI job id when one exists;
- proposal outcome;
- build outcome and validation verdict when reached;
- attempt artifact ids when reached;
- `attempt_kind="structural_repair"`;
- `prompt_version="bluecad_ai_loop_v3_structural_v0_1"`;
- exact evidence-sight digest.

Do not store the full prompt or evidence text in `error_detail_json`. Existing `ai_jobs` prompt digest, flow evidence, provider accounting, and egress records remain authoritative for model execution.

---

## 13. Required tests

### 13.1 Evidence-sight tests

Use the existing autouse `isolated_data_root` fixture and call `initialize_storage(seed_default=True)` in test setup. Do not introduce or assume a `tmp_data_root` fixture.

Prove:

1. exact workspace/candidate/attempt scoping;
2. no cross-attempt or cross-candidate evidence leakage;
3. validation → mesh → FEM ordering;
4. deterministic tie-breaking, text, record ids, and digest;
5. six-line and 2,000-character bounds;
6. no report artifact body or raw solver output is included;
7. empty scoped selection returns `None`.

### 13.2 Configuration tests

Prove:

1. defaults are `structural_repair=False`, `max_structural_repairs=1`;
2. bounds are 0–3;
3. enabled structural repair rejects absent `analysis_spec`;
4. enabled structural repair rejects empty `pass_criteria`;
5. disabled structural repair preserves existing accepted configurations.

### 13.3 Trigger tests

Prove that no model repair occurs for:

- absent analysis spec;
- empty criteria where structural repair is disabled;
- setup error;
- mesh fail or error;
- mesh evidence persistence error;
- raw FEM solver error;
- FEM evidence persistence error;
- `append_tier3_checks` exception;
- combined Tier 3 error verdict or `TIER3_ERROR`;
- already passing criteria.

Prove that a model repair occurs only for the exact `criteria_failed` shape.

### 13.4 Lifecycle and pointer tests

Prove:

1. default-off execution is byte/behavior compatible with the current loop;
2. structural calls do not consume geometric tier-ladder slots;
3. structural attempts keep candidate status `valid` while running;
4. structural provider/config/malformed failure returns the original valid candidate;
5. a structural build or geometry-validation failure leaves candidate status and all artifact pointers unchanged;
6. repeated geometrically valid but criteria-failing repairs exhaust the structural budget and leave original pointers unchanged;
7. a criteria-passing repair atomically replaces all candidate pointers while status remains `valid`;
8. structural flow never calls `park_candidate`;
9. structural flow never calls `mark_candidate_valid`;
10. attempt numbers remain strictly increasing across geometric and structural attempts;
11. structural metadata exists even when the attempt ends before parsing or build;
12. no decision or promotion row is created.

### 13.5 Existing gates

Run:

```bash
cd backend
python -m pytest -q
python -m ruff check app tests
python ../scripts/check_spec_status.py --self-test
```

Real Gmsh/CalculiX remains covered only by existing markers and the current canonical canary; ordinary tests use deterministic fakes/mocks and make no live provider call.

---

## 14. Likely implementation files

Verify current paths before implementation. Expected scope is limited to:

- `backend/app/modules/bluecad/evidence_sight.py` — new deterministic renderer;
- `backend/app/modules/bluecad/prompts.py` — dedicated structural prompt/version only;
- `backend/app/modules/bluecad/models.py` — two bounded config fields and precondition validation;
- `backend/app/modules/bluecad/ledger.py` — non-mutating attempt start and successful atomic pointer commit;
- `backend/app/modules/bluecad/loop.py` — typed simulation outcome and dedicated structural cycle;
- `backend/tests/bluecad/test_evidence_sight.py` — new renderer tests;
- existing BLUECAD loop/simulation test modules or one narrowly named structural-loop test module.

No schema file, migration, route, frontend, adapter, runner, process-model, or workflow change is expected.

---

## 15. Binding non-goals

076 does not add:

- a candidate state, parked reason, attempt column, or database migration;
- a change to the meaning of candidate `valid`;
- model-selected evidence, artifact reads, report-body reads, or raw solver access;
- a general alternative-design loop, optimizer, parametric search, or topology search;
- measured-to-accepted parameter promotion;
- automatic decision creation or promotion;
- provider, route, fallback, continuation, token-cap, or attempt-scale changes;
- a change to `PROMPT_VERSION` or `repair_prompt`;
- UI/frontend work;
- modal, thermal, CFD, or new FEM analysis types;
- changes to mesh/FEM adapter internals beyond exposing already-produced outcome distinctions at the caller;
- unrelated BLUECAD, process-kernel, Hermes, MCP, settings, memory, or reporting work;
- evidence egress provenance/classification implementation.

---

## 16. Separate egress follow-up

All external structural-repair calls already traverse the mandatory 059b network boundary because they use `run_ai_task`. The unresolved gap is narrower: evidence rows are canonical workspace-scoped data, while 076 renders them into exact prompt text. A separate definition must specify how evidence provenance, sensitivity classification, approved derivatives, exact-packet lineage, and stale detection are represented before external use.

That follow-up:

- remains definition-only until reviewed;
- must reuse 059a/059b services rather than add another egress path;
- must not be implemented in 076;
- must receive its own unused spec number and PR after this definition is stable.

---

## 17. Readiness and implementation sequence

1. Merge this definition PR with the registry row still `planned`.
2. Review the final definition against current `master`, open PR overlap, and exact test fixtures.
3. Use a separate promotion PR to move 076 to `ready` only when no unresolved contract conflict remains.
4. Implement 076 in one bounded implementation PR from the exact promoted head.
5. Set the registry to `in_review` and add the implementation PR number as soon as that PR opens.
6. Leave merge authority to the maintainer after deterministic gates pass.

The egress-provenance follow-up is sequenced separately and does not block local/fake-provider implementation proof, but external evidence use remains subject to all current 059a/059b policy outcomes.