# 041 — DECISION-CAPTURE-0: structured record proposals from AI task responses

Status: implemented (pending review)
Depends on: 040

## Goal

After this slice, an AI task response for an opt-in task kind can carry a single
fenced `jarvis-records` block of structured JSON; the execution spine
deterministically parses it after a successful `run_ai_task` run, validates it
against a new `schemas/jarvis_records_v0.schema.json`, and writes each valid
record as a `'proposed'`-status decision/assumption/parameter row through the
040 `memory` facade, with `origin='ai_proposed'` and `source_ai_job_id` set to
the job that produced it. Task kinds not on the allowlist are byte-identical to
current behavior.

## Why

JarvisOS's memory design (`docs/strategy/JARVISOS_MEMORY_CONTEXT_DESIGN.md`)
calls for staged evidence management where model output becomes a candidate
record, never canonical state, until reviewed. Spec 040 builds the write
boundary and the promotion gate; this slice is the first producer that feeds
it — turning an AI response into `proposed_memory` records instead of leaving
useful structured output stranded in prose. This is deliberately the smallest
possible producer: deterministic parsing of an explicit, model-instructed
block, not an LLM interpreting its own output, and not a new authority (hard
invariant #8: AI outputs are proposals until explicit promotion).

## Scope

In scope:
- A new schema `schemas/jarvis_records_v0.schema.json` (JSON Schema, in the
  style of the existing `schemas/bluecad_*_v0_1.schema.json` files) describing
  a `jarvis_records_v0` envelope: `record_version` (const), a `records` array
  (max 10 items) of kind-tagged objects (`record_kind`: `decision` |
  `assumption` | `parameter`), each with only the fields the corresponding
  040-facade create payload accepts (see Design constraints). `workspace_id` is
  explicitly NOT one of the accepted per-record fields; if the model emits one,
  it is ignored and the task's own workspace context is used instead.
- A stored system-prompt fragment (new small module or constant, e.g.
  `backend/app/modules/ai/record_capture.py`) instructing the model, only for
  allowlisted task kinds, to optionally emit one fenced code block tagged
  ```jarvis-records that contains JSON validating against the schema above,
  and to emit nothing of the kind otherwise.
- A deterministic parser (same module) that:
  - scans the raw response text for a fenced block tagged `jarvis-records`
    (language-tag match, not full markdown parsing);
  - if absent, does nothing (no note, no error — this is the normal case for
    a response with no proposals);
  - if present, `json.loads`s the block content and validates it against the
    schema;
  - on JSON-decode failure or schema-validation failure, does not raise past
    the task boundary: it returns a control note, never blocks or fails the
    task;
  - on success, returns up to 10 validated per-kind record payloads in
    document order; if the parsed `records` array has more than 10 entries,
    keeps the first 10 and notes the rest were dropped.
- Wire-in inside `run_ai_task` (`backend/app/modules/ai/execution.py`), after
  a response is classified `status="success"` and only when `task_kind` is on
  the allowlist: call the parser on `response.text`, then for each accepted
  record call the 040 memory facade's create-proposed path with
  `origin="ai_proposed"`, `source_ai_job_id=<this job's id>`, and
  `workspace_id` taken from the task's own context (the same workspace used to
  build project context for the task, never from the parsed payload).
- A config allowlist of task kinds for which (a) the prompt fragment is
  injected into `assemble_prompt`'s SYSTEM section and (b) the parser runs at
  all. Follow the existing `TASK_KIND_DEFAULT_ROUTE`-style plain Python dict
  pattern in `execution.py` (a YAML-driven provider registry per spec 015 does
  not exist yet on this branch; do not invent a dependency on it). Empty/absent
  allowlist entries mean today's behavior, unchanged.
- Extend `AiTaskOutcome`/`AITaskRunResponse` with response metadata surfacing:
  a `records_parse_error` string (`None` when no block was present or parsing
  succeeded), and `proposed_record_ids` (list of created record ids, `[]` when
  none created). Exact field names may adjust to match 040's facade return
  shape; keep the "no error on parse failure" and "ids of what was actually
  created" semantics.
- Tests (see Required tests).

Out of scope (binding non-goals):
- No LLM-based extraction, re-summarization, or a second model call to produce
  or clean up the block. Parsing is pure deterministic code over the block the
  first model call already produced.
- No auto-promotion. Every record this slice creates is `'proposed'` and
  requires the existing/040 `POST /memory/{kind}/{id}/promote` step.
- No UI. No new frontend surface, no rendering of proposed records, no
  confirmation dialog.
- No retrieval changes: proposed records are not injected into
  `build_workspace_context_bundle` or any other context path by this slice.
- No new chat surface or conversational loop (out of scope relative to
  `BLUECAD_CONVERSATIONAL_DESIGN_LAYER.md`; this slice is plumbing underneath
  any future chat, not the chat itself).
- No streaming.
- No modification of provider adapters (`backend/app/modules/ai/providers/*`).
  Adapters return `AIResponse.text` exactly as today; all new logic lives in
  the spine, downstream of `adapter.complete()`.
- No new columns on `ai_jobs`. Linkage is one-directional via
  `source_ai_job_id` on the 040 tables; `ai_jobs` itself is unchanged.
- No `requirements` record kind in this slice (the binding kernel lists
  decision/assumption/parameter only; extending to requirements is a candidate
  follow-up, not this slice).
- No change to routes/`AIGateway`/frontend beyond passing through the new
  response metadata fields already added to `AITaskRunResponse`.

## Files likely touched

Verify against actual code before starting; report conflicts instead of
guessing (in particular: confirm spec 040's facade module path and function
signature once it exists on this branch — it may not yet).

- `schemas/jarvis_records_v0.schema.json` (new)
- `backend/app/modules/ai/record_capture.py` (new: prompt fragment constant +
  block scanner + JSON/schema validation + bounded extraction)
- `backend/app/modules/ai/execution.py` (`run_ai_task`: allowlist check,
  prompt-fragment injection point, post-success parse-and-write call;
  `AiTaskOutcome` new fields)
- `backend/app/modules/ai/context_builder.py` — NOT modified (expert review,
  2026-07-06): fragment injection happens in `execution.py` before calling
  `assemble_prompt` (option (b) of the Open questions), preserving the
  existing empty-blocks short-circuit contract and all current
  `assemble_prompt` callers
- `backend/app/modules/ai/models.py` (`AITaskRunResponse`: add
  `records_parse_error`, `proposed_record_ids`)
- `backend/app/modules/ai/gateway.py` (`run_task`: pass through new outcome
  fields to the response)
- `backend/app/modules/memory/` (040 facade — call only, do not redefine; if
  it does not exist yet on this branch, stop and report per
  `docs/specs/README.md` workflow rather than drafting a parallel write path)
- `backend/tests/test_ai_execution_spine.py` (extend)
- `backend/tests/test_record_capture.py` (new, parser/schema unit tests)

## Design constraints

- **Extraction is deterministic parsing, not an LLM post-pass.** The model is
  instructed (via the stored prompt fragment) to emit at most one fenced block
  tagged `jarvis-records`; JarvisOS never asks a second model call to find,
  summarize, or repair that block. If the block is malformed, it is dropped,
  not fixed.
- **Parse/schema failure never fails the task.** Whatever the block scanner or
  schema validator encounters — no block, unparsable JSON, schema violation,
  more than 10 records — `run_ai_task` still returns its normal `status`
  (`"success"`) and `response.text` unchanged. The only externally visible
  difference is `records_parse_error` being set and `proposed_record_ids`
  being empty.
- **`workspace_id` always comes from the task, never from the model.** Even if
  the parsed JSON includes a `workspace_id`-shaped field on a record, it must
  be ignored; the schema should not even define such a field on the per-record
  objects (only on nothing — the envelope has no workspace field either). The
  facade call uses the workspace resolved for this task (the same workspace
  used for `include_project_context`/workspace-scoped calls elsewhere in the
  gateway).
- **Wire-in point is the execution spine only.** `AIGateway.run_task`,
  routes, and provider adapters must not call the 040 facade directly; only
  `run_ai_task` (or a helper it calls) does, after a successful run. This
  mirrors hard invariant #2 (all AI calls go through the spine) — record
  writes are a side effect of the spine's own post-success step, not a
  parallel path.
- **Opt-in by task kind, not global.** The allowlist gates both prompt-fragment
  injection and parsing together — a task kind never gets one without the
  other. Task kinds absent from the allowlist must be byte-identical to
  current behavior: same prompt text (no fragment appended), no parser
  invocation, no new fields populated beyond their now-present default
  (`records_parse_error=None`, `proposed_record_ids=[]`).
- **Bounded.** Maximum 10 records accepted per response, enforced by the
  schema (`maxItems: 10` on `records`) and defensively again in the parser.
  Anything beyond the 10th parsed record is dropped with a note folded into
  `records_parse_error` (e.g. `"records_truncated: N dropped"`), not an
  exception and not a full-response rejection — the first 10 are still
  written.
- **Provenance is mandatory and matches 040's kernel exactly.** Every record
  created by this path sets `origin="ai_proposed"` and a non-null
  `source_ai_job_id` equal to the `ai_jobs.id` written by this same
  `run_ai_task` call (the ledger id already computed via `_write_ai_job`).
  Records created this way start life with whatever 040 defines as the
  proposed-status default; this slice does not invent its own status field.
- **No new authority.** Created rows are `'proposed'`; nothing in this slice
  promotes them, surfaces them in context, or treats them as accepted fact.
  This satisfies hard invariant #8.
- **Reuse the 040 facade's validation, don't shadow it.** If the 040 facade
  already re-validates required fields (e.g. `unit` on parameters,
  `decision_text` on decisions) at its own boundary, this slice's schema
  should not silently diverge from those requirements — a record that passes
  `jarvis_records_v0.schema.json` but fails the facade's own validation is a
  facade-level rejection for that one record (dropped, logged in the parse
  outcome), not a schema bug to route around.
- **No secrets, no prompt/output content in `ai_jobs`.** The existing ledger
  contract (`ai_jobs` stores digests/metadata only) is unchanged; this slice
  must not add record text, JSON payloads, or the raw block into any `ai_jobs`
  column. Record content lives only in the 040 tables it was written to.

## Acceptance criteria

1. `schemas/jarvis_records_v0.schema.json` exists, is valid JSON Schema
   (2020-12 dialect, matching the existing `schemas/*.schema.json` style),
   rejects unknown top-level and per-record fields (`additionalProperties:
   false`), defines `record_kind` as one of `decision`/`assumption`/
   `parameter`, and caps `records` at 10 items.
2. For an allowlisted task kind, a fake-provider response whose text contains
   a fenced ` ```jarvis-records ` block with a valid single-decision payload
   results in: `run_ai_task` status `"success"`; exactly one row created in
   the decisions table (via the 040 facade) with `origin="ai_proposed"`,
   `source_ai_job_id` equal to this call's `ai_jobs.id`, and proposed status;
   `AITaskRunResponse.proposed_record_ids` containing that row's id;
   `records_parse_error` is `None`.
3. For an allowlisted task kind, a response whose `jarvis-records` block
   contains malformed JSON (or JSON that fails schema validation) results in:
   `run_ai_task` status unchanged at `"success"`; zero records created;
   `records_parse_error` non-null and descriptive; `response.text` returned to
   the caller unmodified (the malformed block is not stripped or altered).
4. For a task kind absent from the allowlist, given the same fake-provider
   response text (including a `jarvis-records` block) as case 2: no prompt
   fragment is present in the assembled prompt sent to the adapter, the
   parser is never invoked, `proposed_record_ids` is `[]`, and
   `records_parse_error` is `None` — behavior and response shape otherwise
   match pre-slice `run_ai_task` output for that same input exactly (same
   `response.text`, same ledger fields).
5. A `jarvis-records` block whose `records` array has more than 10 entries
   causes exactly the first 10 (by document order) to be created and the
   remaining entries to be dropped, with a note reflecting the drop count
   surfaced via `records_parse_error` (or an equivalent non-blocking metadata
   field, per Design constraints), while `run_ai_task` status remains
   `"success"`.
6. A `jarvis-records` block whose payload supplies a `workspace_id`-shaped
   value on the envelope or a record results in that value being ignored:
   the created record's `workspace_id` equals the task's own resolved
   workspace, never the model-supplied value. A test proves this by
   supplying a workspace id in the block that differs from the task's actual
   workspace and asserting the created row belongs to the task's workspace.
7. No `ai_jobs` row (for this or any other call in the test suite) contains
   record JSON, the raw `jarvis-records` block text, or any parsed record
   field in any column.
8. Provider adapter files under `backend/app/modules/ai/providers/` are
   unmodified by this slice (grep-checkable from the diff).
9. Full backend test gate green (`pytest`, `ruff`) per `AGENTS.md`.

## Required tests

- Schema tests: a minimal valid single-record payload for each of
  `decision`/`assumption`/`parameter` validates; a payload with an unknown
  top-level key, an unknown per-record key, an invalid `record_kind`, or 11
  records fails validation.
- Parser unit tests (offline, no provider): response text with no
  `jarvis-records` block → no-op (no error, no records); response text with a
  valid block → parsed records list; response text with malformed JSON in the
  block → parse error result, no exception raised past the parser boundary;
  response text with a block that parses as JSON but fails schema validation
  → parse error result, no exception.
- Execution-spine integration tests (fake provider, allowlisted task kind):
  - valid block → `run_ai_task` returns `status="success"`,
    `proposed_record_ids` non-empty, records exist in the target table with
    `origin="ai_proposed"` and `source_ai_job_id` set to the returned
    `ledger_id`.
  - malformed block → `status="success"`, zero records written,
    `records_parse_error` set.
  - non-allowlisted task kind with the same response text → no injection (
    assert the assembled prompt sent to the adapter has no fragment), no
    parsing attempted (assert zero records regardless of block validity), and
    output byte-identical to a pre-slice baseline call with the same inputs.
  - 11-record block → exactly 10 created, drop noted.
  - block supplying a foreign `workspace_id` → created record's
    `workspace_id` is the task's actual workspace, not the supplied one.
- Ledger-content test: after running the above cases, assert no `ai_jobs` row
  contains record content (search serialized ledger fields for record marker
  strings/JSON keys and assert absence).
- Regression test: an allowlisted-eligible call with `task_kind` not on the
  allowlist and a response with no block behaves identically (status, ledger
  fields, response fields) to the same call made before this slice's change
  (compare against current `test_ai_execution_spine.py` fixtures/baselines).

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status
updated, summary written.

## Open questions

- **Spec 040 facade shape is unread.** This spec was drafted while 040
  (MEMORYSTORE-0) is being drafted in parallel; its module path, the exact
  function signature for a "create proposed record" call, and its returned
  proposed-status field name are unknown here and must be verified once 040
  exists on this branch. If 040 lands with a materially different shape (for
  example, a single generic `create_proposed(kind, payload, origin,
  source_ai_job_id)` versus four kind-specific functions), the "Files likely
  touched" and Design constraints referencing "the 040 facade" should be
  read as referring to whatever that module turns out to be, not a specific
  function name.
- **`requirements` is a record kind in the existing schema (spec 001) but is
  excluded from the binding kernel's record_kind list** (only
  decision/assumption/parameter are named). This spec follows the kernel as
  given and excludes `requirements`; flagging in case the omission was
  unintentional rather than deliberate scoping.
- **Provider gateway (spec 015) has not landed on this branch** (no
  `configs/ai_providers.yaml` present, `execution.py` still uses the
  hardcoded `_default_bindings()` table read during this review). This spec's
  allowlist is therefore specified as a plain Python constant alongside
  `TASK_KIND_DEFAULT_ROUTE`, not as YAML-driven config. If 015 lands first,
  the allowlist should move into that registry instead — flagging so the
  implementer picks whichever exists at branch time rather than guessing.
- **Prompt-fragment injection seam in `assemble_prompt` is call-site-only
  today.** `assemble_prompt(blocks, user_prompt)` currently has no parameter
  for task-kind-conditional system-text injection, and it also short-circuits
  to returning the bare `user_prompt` when `blocks` is empty (preserving
  pre-POS-2 behavior). Injecting the `jarvis-records` fragment for an
  allowlisted task kind with zero context blocks means either (a) adding a
  parameter to `assemble_prompt` and updating its empty-blocks short-circuit,
  or (b) building the fragment injection in `execution.py` before calling
  `assemble_prompt`, leaving `context_builder.py` untouched. Recommend (b) to
  avoid touching the existing empty-blocks-returns-bare-prompt contract that
  other callers/tests may depend on, but this is a genuine open
  implementation choice, not a stale-doc conflict — flagging for the
  implementer to confirm against current tests for `assemble_prompt`.
- **No existing precedent for "system fragment stored where."** The spec
  says "a stored system-prompt fragment instructing the block format." There
  is no existing convention in this repo for storing prompt fragments
  (no `prompts/` directory, no template module) — this spec places it as a
  Python string constant in the new `record_capture.py` module, matching how
  `SYSTEM_INSTRUCTIONS` lives as a constant in `context_builder.py`. Flagging
  in case a different convention is preferred.

## Review resolutions (2026-07-06 — expert review, binding)

1. (040 facade shape) 040 is now drafted: module `backend/app/modules/memory/`
   with per-kind create-proposed payloads through `service.py`, provenance
   columns `origin`/`source_ai_job_id`/`promoted_at`, and a service-level
   existence check on `source_ai_job_id`. Verify the exact function names at
   implementation time as planned; requirements are excluded from the facade
   (see next point).
2. (requirements omission) Intentional, not accidental: requirements keep
   their shipped `draft/active/retired` lifecycle and are excluded from both
   040's facade and this slice's capture. They join in a future slice.
3. (allowlist location) Confirmed: plain Python dict beside
   `TASK_KIND_DEFAULT_ROUTE`. When spec 015's registry lands, moving it there
   is a follow-up, not a blocker.
4. (injection seam) Option (b) is binding: inject in `execution.py` before
   `assemble_prompt`; `context_builder.py` is not modified.
5. (fragment storage) Constant in `record_capture.py` confirmed. Note there is
   in fact a precedent for prompt text as module constants:
   `backend/app/modules/bluecad/prompts.py` — consistent with this choice.

## Implementation notes

- Implemented deterministic `jarvis-records` parsing in the AI execution spine for the `decision_support` task kind allowlist.
- Record proposals are written through the MemoryStore facade only after successful provider responses; malformed blocks remain non-blocking metadata.
- No provider adapters, `ai_jobs` columns, retrieval/context-pack behavior, or frontend surfaces were changed.
