# 010 — BLUECAD AI loop v0 (L1 generate → build → validate → repair)

Status: ready (blocked until 005 is merged — see Depends on)
Depends on: 005 (CAD adapter MVP). Reads: `docs/strategy/BLUECAD_CORE_DESIGN.md`
(§7 loop, §8 routing — binding), `docs/strategy/BLUECAD_SEAM_MAP.md` (facts),
`docs/strategy/JARVISOS_PLATFORM_GAPS_PLAN.md` (ledger triage).

## Goal

After this slice, a user can submit a design brief for a workspace and JarvisOS
runs the bounded L1 loop: an external LLM proposes a `GeometrySpec v0` JSON →
the 005 adapter builds it → deterministic validation → on failure, bounded
repair calls with the validation report → outcome is a `valid` candidate
(promotable to a Decision by the user) or a `parked` candidate with the full
attempt trail. Every LLM call, artifact, and verdict is persisted and
inspectable.

## Why

This is the alpha's core promise: AI generates CAD, deterministic validators
decide, humans promote. It also establishes the candidate/attempt ledger
pattern that later slices (011 panel, 012 L2, FEM loops) reuse.

## Scope

In scope:
- New tables (module-owned; **no changes to `ai_jobs`, `artifacts`,
  `run_artifacts`, or any existing table**):
  - `bluecad_candidates`: `id`, `workspace_id`, `brief_text`, `brief_digest`,
    `status` (`generating` | `validating` | `valid` | `parked` | `archived`),
    `parked_reason` (nullable enum: `attempts_exhausted` | `budget_blocked` |
    `policy_blocked` | `malformed_repeated` | `user_cancelled`),
    `spec_artifact_id` (nullable — latest spec), `glb_artifact_id` (nullable),
    `report_artifact_id` (nullable), `promoted_decision_id` (nullable),
    `origin` (`ai` | `parametric_variant` — this slice always writes `ai`;
    the variant value is reserved for slice 006b's deterministic rebuilds),
    `parent_candidate_id` (nullable, for variants),
    `loop_config_json`, `created_at`, `updated_at`, `notes`.
  - `bluecad_attempts`: `id`, `candidate_id`, `attempt_no`, `route_class`,
    `proposal_ai_job_id` (nullable), `proposal_outcome`
    (`ok` | `malformed` | `provider_error` | `blocked`),
    `build_outcome` (nullable: `ok` | 005 error code),
    `validation_verdict` (nullable: `pass` | `fail`),
    `spec_artifact_id`, `report_artifact_id`, `manifest_artifact_id`
    (all nullable), `started_at`, `finished_at`, `error_detail_json`.
  - Attempt phases are recorded as outcome *fields*, not a state machine —
    an attempt row is append-once, updated in place during its own run only.
- Loop orchestrator `backend/app/modules/bluecad/loop.py`:
  - Policy as data (`loop_config_json`, defaults in module config):
    `max_attempts_per_tier = 3`,
    `tier_ladder = ["external:cheap", "external:reasoning"]`,
    `max_output_tokens`, per-call timeout.
  - Provider calls via the existing explicit path
    (`run_ai_task(..., route_class=tier, task_kind="bluecad_cad_generate" | "bluecad_cad_repair")`).
    The RouterPolicy `auto` route is NOT used (seam map: non-executing).
  - `external_blocked_reason` from settings/budget → candidate
    `parked(budget_blocked)` immediately. Never retried, never counted as a
    provider error.
  - LLM output contract: the response must contain exactly one JSON object
    (optionally fenced) parseable as GeometrySpec v0. Strict parse → schema
    validation. Non-parseable/invalid → `proposal_outcome = malformed`
    (counts as an attempt); 3 consecutive malformed on the same tier →
    escalate; malformed persisting after ladder end → `parked(malformed_repeated)`.
  - On `proposal_outcome = ok`: write spec artifact, run 005 build + validate
    (worker subprocess). `verdict = pass` → candidate `valid`, artifacts
    linked. `fail` → next attempt with repair prompt.
  - Repair prompt input = failing GeometrySpec + `validation_report` JSON
    (checks, details, hints) only. No conversation history accumulation.
  - Prompt templates live in `backend/app/modules/bluecad/prompts.py`,
    versioned (`prompt_version` string recorded per attempt in
    `error_detail_json` or a dedicated column). System template contains: the
    GeometrySpec v0 field reference (concise), allowed part kinds, port
    composition rules, the `declared` block requirement, JSON-only output
    instruction. **No BlueRev formulas or proprietary parameters in
    templates** (layering rule).
- API (workspace-scoped, style-matched to existing routes):
  - `POST /workspaces/{id}/bluecad/candidates` — body: brief text + optional
    loop config overrides. Runs the loop synchronously to terminal status
    (bounded: ≤ 6 provider calls); returns the candidate with attempts.
  - `GET .../bluecad/candidates`, `GET .../bluecad/candidates/{cid}` (with
    attempts and artifact refs).
  - `POST .../bluecad/candidates/{cid}/promote` — only from `valid`; creates
    a modeling Decision (existing `create_decision`) referencing the
    candidate id and artifacts in its rationale/notes; stores
    `promoted_decision_id`. Loop code contains no auto-promotion path.
  - `POST .../bluecad/candidates/{cid}/archive`.

Out of scope (binding non-goals):
- No L2 scripts (spec 012; runner extension 016 is a prerequisite).
- No review panel / multi-agent critique (spec 011).
- No mesh/FEM in the loop (009 lands Tier 3 separately).
- No frontend work (006 viewer consumes the GLB artifact refs as-is).
- No RouterPolicy schema changes, no `ai_jobs` changes, no new providers.
- No background job queue: v0 is synchronous and bounded; if the 20s provider
  timeout proves too tight for spec JSON, raise the per-call timeout via
  config — do not build async infrastructure in this slice.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `backend/app/core/schema.py` (additive: two new tables)
- `backend/app/modules/bluecad/loop.py`, `prompts.py`, `ledger.py`,
  `routes.py`, `models.py` (new)
- `backend/app/main.py` (router registration, matching existing pattern)
- `backend/tests/bluecad/test_loop_*.py` (new)

## Design constraints

- Artifacts are written through the existing `artifacts` table machinery
  (sha256, workspace-scoped paths under the data root), role-tagged
  (`bluecad_spec`, `bluecad_manifest`, `bluecad_report`, `bluecad_glb`, …).
- Every provider call in the loop must be traceable: attempt row →
  `proposal_ai_job_id` → `ai_jobs` row (which already records digests,
  tokens, latency).
- Loop determinism: given the same sequence of provider responses, the loop
  produces the same statuses, artifacts, and ledger rows (assert in tests via
  fake adapters).
- Spend safety is fail-closed: any state not explicitly handled → park, never
  loop. Total provider calls per candidate ≤
  `len(tier_ladder) × max_attempts_per_tier` enforced structurally.
- Prompt templates and loop policy are the only places tuned later — keep
  them isolated from orchestration logic.
- Sensitivity: candidate briefs follow the existing workspace egress policy;
  this slice adds no new redaction machinery (S3 material simply must not be
  put in briefs routed externally — user-level policy for now).

## Acceptance criteria

1. Happy path: fake provider returns a valid spec on attempt 1 → candidate
   `valid`, one attempt row (`proposal_outcome=ok`, `build_outcome=ok`,
   `validation_verdict=pass`), spec/manifest/report/GLB artifacts linked, and
   a linked `ai_jobs` id present.
2. Repair path: fake provider returns a spec violating `declared` volume,
   then a corrected one → candidate `valid` with two attempts; the second
   call's prompt (captured by the fake adapter) contains the `T1_VOLUME_DECL`
   check detail from attempt 1's report.
3. Exhaustion path: always-failing specs → exactly 3 attempts on
   `external:cheap`, then exactly 3 on `external:reasoning`, then
   `parked(attempts_exhausted)`. Total provider calls = 6, verified.
4. Malformed path: non-JSON responses → attempts recorded with
   `proposal_outcome=malformed`, no build executed, eventual
   `parked(malformed_repeated)`.
5. Budget-blocked path: `external_blocked_reason` set → candidate
   `parked(budget_blocked)` with zero further provider calls; the reason is
   stored verbatim.
6. Promotion: `promote` on a `valid` candidate creates a Decision via the
   existing modeling service and stores its id; `promote` on any non-`valid`
   status is rejected with a structured error. Grep-level check: no code path
   calls `create_decision` from `loop.py`.
7. Determinism: running the loop twice against the same scripted fake adapter
   yields identical statuses, attempt sequences, and artifact digests
   (timestamps excluded).
8. No modification to existing tables' DDL; migration is purely additive.

## Required tests

- Offline pytest, no network: fake `AIProviderAdapter` implementations
  injected via `run_ai_task(adapters=..., bindings=...)` returning scripted
  response sequences (valid spec / invalid-then-fixed / always-invalid /
  malformed / provider_error), plus a settings fixture forcing
  `external_blocked_reason`.
- Ledger unit tests: status transitions, parked reasons, structural call cap.
- API tests for the four endpoints including promote-guard failure cases.
- Reuse 005 golden specs as the fake provider's payloads (no new geometry
  fixtures needed).

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.
