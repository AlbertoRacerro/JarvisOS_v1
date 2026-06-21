# Micro-Context Design

Milestone: 1D-B - Micro-context design

## Executive Summary

Micro-context is a small, bounded, local-model-facing orientation snapshot. It
helps a model understand the current workspace, project, milestone, durable
decisions, open clarifications, and safety constraints before it requests source
files or context packs.

Core rule:

```text
micro-context is regenerated from canonical sources and accepted state; models may read it but must not directly write or patch it
```

Micro-context is not canonical memory, runtime retrieval, Context Pack Broker
runtime, provider routing, tool execution, model authority, or BlueRev modeling.
If micro-context contradicts canonical docs or source files, the canonical
source wins.

This milestone designs the shape only. It does not create event tables, hooks,
generator scripts, runtime micro-context snapshots, model calls, MCP, workers,
viewers, memory runtime, retrieval runtime, provider routing, tool execution, or
frontend/backend runtime behavior.

## Design Goals

- Give local models a compact orientation surface before bounded source or
  context requests.
- Keep micro-context scoped by workspace, project, and milestone.
- Regenerate micro-context from canonical sources and accepted state.
- Make freshness and staleness visible.
- Prevent model-written context from becoming durable authority.
- Avoid global recent-context injection and cross-project leakage.
- Preserve the distinction between compact orientation and full evidence.
- Keep future update hooks/events behind controlled boundaries.

## Non-Goals And Boundaries

Micro-context is not:

- source of truth;
- canonical memory;
- accepted memory;
- full context pack;
- runtime retrieval;
- Context Pack Broker runtime;
- memory runtime;
- route or UI behavior;
- provider or tool routing;
- automatic provider calls;
- automatic tool execution;
- automatic memory writing;
- model authority;
- safety approval;
- BlueRev modeling.

Micro-context must never authorize:

- memory promotion;
- retrieval access;
- source-file access;
- provider calls;
- tool calls;
- route selection;
- sensitivity downgrades;
- final safety decisions;
- BlueRev assumptions;
- runtime execution.

## Canonical Sources

Micro-context may summarize only canonical sources and accepted state.

Current canonical documentation inputs include:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- `docs/STAGED_MEMORY_INTAKE.md`
- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`
- `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- `docs/LOCAL_MODEL_SHOWCASE_FILES.md`

Future accepted-state inputs may include accepted memory, accepted decisions,
resolved clarifications, and milestone state only after their owning storage,
promotion, scope, and audit policies exist.

## Micro-Context Content Envelope

V0 micro-context should stay small. It may include:

- workspace ID or `null`;
- project ID;
- milestone ID;
- current focus;
- current accepted local-AI boundary;
- recent accepted ADRs;
- high-value open clarifications;
- current non-approved behaviors;
- safety and secret-handling summary;
- source references used to generate the snapshot;
- freshness/staleness metadata.

V0 micro-context must not include:

- raw secrets;
- raw tool output;
- raw prompt logs;
- unscoped recent chat history;
- full source files;
- full memory bodies;
- tentative BlueRev modeling assumptions as accepted facts;
- model-authored patches to the snapshot.

## Updateable Snapshot Lifecycle

Micro-context should be designed as a future updateable snapshot, not as a
static hand-written memory blob.

The snapshot is regenerated from canonical sources and accepted state. A local
model may read it as orientation only. A local model must not directly write,
patch, promote, or authorize it.

Conceptual `micro_context_v0` snapshot contract:

```json
{
  "schema_version": "micro_context_v0",
  "snapshot_id": "string",
  "generated_at": "timestamp|null",
  "scope": {
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null"
  },
  "source_policy": {
    "non_authoritative": true,
    "canonical_sources_required_for_decisions": true,
    "model_may_not_write": true,
    "generated_from_canonical_sources_only": true
  },
  "freshness": {
    "source_heads": [],
    "stale": false,
    "stale_reason": "none|missing_timestamp|source_changed|manual_review_required|unknown"
  }
}
```

This schema is conceptual only. It does not create a runtime schema, table,
Pydantic model, generator, route, or snapshot file.

Future update events may mark a scoped micro-context snapshot as stale or as a
candidate for regeneration.

Conceptual `micro_context_update_event_v0`:

```json
{
  "schema_version": "micro_context_update_event_v0",
  "event_type": "adr_added|milestone_advanced|canonical_doc_changed|accepted_memory_promoted|clarification_opened|clarification_resolved",
  "source_ref": "string",
  "scope": {
    "workspace_id": "string|null",
    "project_id": "string|null",
    "milestone_id": "string|null"
  },
  "allowed_effect": "regenerate_snapshot",
  "model_authority": "none"
}
```

This event is documentation only. It must not be implemented in this milestone.

## Scope Rules

Every future micro-context snapshot must have explicit scope:

- workspace scope;
- project scope;
- milestone scope when applicable.

Allowed project IDs for V0 are:

```text
jarvisos | bluerev | coursework | personal | general | unknown
```

Scope rules:

- No global recent-context injection.
- No cross-project leakage.
- No BlueRev assumptions in JarvisOS-only snapshots unless a canonical source
  explicitly references the boundary.
- No coursework, personal, or general context in JarvisOS/BlueRev snapshots
  without explicit scope.
- Unknown scope should trigger a bounded source/context request rather than
  broad injection.

## Freshness And Staleness Rules

Micro-context becomes stale when:

- a canonical doc changes;
- an ADR is added or refined;
- a milestone advances;
- accepted state changes;
- a clarification is opened or resolved;
- the snapshot has no generation timestamp;
- source heads are missing;
- manual review is required;
- the generator cannot prove source consistency.

If canonical sources changed, micro-context becomes stale and must trigger a
bounded source/context request or regeneration.

If micro-context contradicts canonical docs or source files, canonical docs and
source files win. The stale snapshot must not be used as decision authority.

## Canonical-Source Regeneration Rule

Micro-context regeneration must read canonical sources and accepted state, then
emit a bounded snapshot with source references and freshness metadata.

Regeneration must not:

- use model output as direct write authority;
- infer canonical truth from summaries;
- include unscoped recent sessions;
- include raw secrets or raw tool output;
- silently copy tentative assumptions into accepted state;
- fetch full evidence unless referenced by source ID and allowed by scope.

## Model Non-Write Authority Rule

Models may read micro-context as orientation. Models may also propose that a
snapshot is stale or insufficient.

Models must not:

- write micro-context;
- patch micro-context;
- promote micro-context;
- edit accepted state;
- open retrieval directly;
- call tools or providers from micro-context;
- treat micro-context as runtime authority.

Any model-filled form related to micro-context remains advisory until JarvisOS
validates structure, checks scope, applies policy, and decides what happens
next.

## Cavemem-Inspired Lessons

Cavemem is architectural inspiration only. JarvisOS should adapt patterns, not
copy Cavemem code or runtime behavior in this milestone.

Useful lessons:

- Single write/update boundary.
- `MemoryStore`-style single write boundary before durable memory writes.
- Event/hook capture should feed a controlled boundary, not raw memory.
- Observations, summaries, and compact context should remain separate.
- Summaries must remain separate from raw observations.
- Compact-first context should precede full-body retrieval.
- Full evidence should be fetched by source/reference ID only.
- Background enrichment/indexing should be lazy and non-authoritative.
- Hook/event capture must be scoped by workspace, project, and milestone.
- Local-first defaults; no implicit network calls.
- Write path must not depend on background worker success.
- No global recent-context injection.
- No cross-project context leakage.
- No model-written micro-context.
- No runtime authority from micro-context.

Cavemem-style prior-session context is useful, but JarvisOS must avoid global
recent-context injection. Scope must be explicit.

## Cavemem-Inspired Update Path

Future JarvisOS may later use hooks/events to trigger micro-context
regeneration, but hooks must never write micro-context or memory directly.

Future conceptual path:

```text
source events / future hooks
-> EventCaptureBoundary
-> FastIntake or future MemoryStore
-> canonical storage / accepted state
-> MicroContextAssembler
-> bounded micro-context snapshot
-> local model reads snapshot as orientation only
```

Boundary meanings:

- `source events / future hooks`: possible future triggers such as accepted ADRs,
  milestone changes, completed tasks, source changes, or resolved
  clarifications.
- `EventCaptureBoundary`: validates event shape, scope, source reference, and
  allowed effect before anything reaches storage or regeneration.
- `FastIntake or future MemoryStore`: controlled write boundary for raw/proposed
  intake or accepted durable memory after the MemoryStore design exists. The
  facade design lives in `docs/MEMORYSTORE_FACADE_DESIGN.md`.
- `canonical storage / accepted state`: durable source of truth, not model
  output.
- `MicroContextAssembler`: future component that reads only allowed canonical
  sources and accepted state to build a bounded snapshot.
- `bounded micro-context snapshot`: non-authoritative local-model orientation.
- `local model reads snapshot as orientation only`: read-only model input, never
  runtime authority.

Conceptual event schema:

```json
{
  "schema_version": "context_event_v0",
  "event_id": "string",
  "event_type": "session_started|user_prompt_received|assistant_response_finalized|codex_task_completed|git_commit_detected|canonical_doc_changed|adr_added|milestone_advanced|test_report_added|artifact_created|clarification_opened|clarification_resolved",
  "created_at": "timestamp|null",
  "source_ref": "string",
  "scope": {
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null"
  },
  "allowed_effect": "candidate_micro_context_regeneration",
  "model_authority": "none",
  "raw_payload_preserved": true,
  "sensitivity_hint": "public|internal|sensitive|secret|unknown"
}
```

This schema is conceptual only.

Do not create:

- event tables;
- hooks;
- generator scripts;
- runtime micro-context snapshots;
- Claude Code integration;
- Codex integration;
- Git hooks;
- MCP integration;
- worker integration;
- viewer integration;
- provider routing;
- memory runtime;
- retrieval runtime.

Future hook implementation must wait until MemoryStore facade, storage schema,
policy, scope, retention, and tests exist.

### Why JarvisOS must not copy Cavemem hooks directly yet

- Automatic capture can store secrets or irrelevant tool output.
- Global recent-session context can leak across projects.
- Unscoped summaries can mislead local models.
- Hooks can create hidden behavior.
- Worker/indexing failure must not break the write path.
- Model output must not become write authority.

## Failure Modes

Stale micro-context:

- A snapshot can lag behind canonical docs, ADRs, source files, or accepted
  state.
- Mitigation: source heads, timestamps, stale flags, and bounded source/context
  requests.

Over-trusted micro-context:

- A model may treat orientation as canonical truth.
- Mitigation: explicit `non_authoritative` policy and canonical-source
  requirement for decisions.

Under-scoped context:

- A model may rely on a generic snapshot for a project-specific task.
- Mitigation: require workspace/project/milestone scope and request more
  context when scope is missing.

Over-broad context:

- Global recent context may leak across projects or include irrelevant personal
  material.
- Mitigation: no global recent-context injection and explicit source scope.

Model-written context:

- A model may propose a useful summary but accidentally change authority state.
- Mitigation: model output is advisory only; JarvisOS owns validation,
  persistence, promotion, execution, audit, and policy.

Background update coupling:

- A worker or indexer failure could block the write path.
- Mitigation: background enrichment/indexing remains lazy and
  non-authoritative; write path must not depend on worker success.

## Acceptance Criteria For Future Implementation

Future implementation may proceed only when:

- MicroContextAssembler has a design and tests.
- MemoryStore facade has a design and tests before durable memory writes.
- Storage schema, scope policy, retention policy, and source-reference rules
  exist.
- Hook/event capture has explicit opt-in policy and secret handling.
- Event capture feeds a controlled boundary, not raw memory.
- Snapshot regeneration uses canonical sources and accepted state only.
- Snapshot freshness is auditable.
- No global recent-context injection exists.
- Full evidence is fetched by source/reference ID only.
- Model output cannot write or patch micro-context.
- Runtime authority remains outside micro-context.

## Milestone Boundary Confirmation

1D-B is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- routes or APIs;
- database schema or migrations;
- event tables;
- hooks;
- generator scripts;
- runtime micro-context snapshots;
- Claude Code integration;
- Codex integration;
- Git hooks;
- MCP;
- worker processes;
- viewers;
- provider routing;
- memory runtime;
- retrieval runtime;
- Context Pack Broker runtime;
- tool execution;
- local or external model calls;
- BlueRev modeling;
- vendored Cavemem or Caveman code.
