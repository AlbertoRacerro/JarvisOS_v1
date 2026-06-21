# Progressive Retrieval Contract Design

Milestone: 1D-F - Progressive retrieval contract design

## Executive Summary

Progressive retrieval is the future scoped read contract for JarvisOS memory
and source grounding.

Core principle:

```text
retrieval returns scoped candidates and source-grounded evidence; retrieval never creates truth, authority, memory promotion, provider permission, tool permission, route permission, final sensitivity, or BlueRev assumptions
```

Progressive retrieval starts from orientation, moves to scoped compact
candidates, then fetches full evidence only by stable ID or source reference
after policy checks.

Conceptual flow:

```text
micro-context / showcase orientation
-> scoped retrieval request
-> scope + sensitivity gate
-> compact candidate discovery
-> candidate IDs + provenance
-> optional full body request by stable ID/source reference
-> full evidence with provenance
-> later context package assembly / review / reasoning
```

This milestone designs the retrieval contract only. It does not implement
retrieval, RAG runtime, Context Pack Broker runtime, memory runtime, database
queries, FTS indexes, model-controlled memory access, provider access, tool
access, routes, services, storage classes, or runtime files.

## Design Goals

- Define retrieval as a scoped read contract, not a source of authority.
- Preserve the sequence of orientation, compact candidates, and full evidence.
- Require workspace, project, and milestone scope before candidates are
  returned.
- Keep compact snippets, compressed text, showcase files, and micro-context
  non-authoritative.
- Require stable IDs or source references before full evidence is fetched.
- Carry source, provenance, lifecycle status, sensitivity, and stale/conflict
  markers forward.
- Keep `raw_input`, `proposed_memory`, and `superseded` records review-only by
  default.
- Prevent model, provider, tool, route, or Context Pack Broker bypass of policy
  gates.
- Prepare the contract that a future Context Pack Broker may consume without
  implementing that broker now.

## Non-Goals And Hard Boundaries

This milestone does not add:

- backend code;
- frontend code;
- routes or APIs;
- database migrations;
- SQLAlchemy models;
- Pydantic runtime models;
- repository or storage classes;
- FTS runtime queries;
- FTS indexes;
- retrieval runtime;
- RAG runtime;
- memory runtime;
- Context Pack Broker runtime;
- compression runtime;
- local or external model calls;
- provider calls;
- hooks;
- MCP;
- worker processes;
- viewers;
- tool execution;
- BlueRev modeling;
- external reference audits;
- vendored code;
- runtime-approved model status.

All contracts in this document are conceptual only. They are not Pydantic
models, API schemas, database schemas, routes, services, migrations, indexes,
storage classes, runtime files, or implementation plans.

## Relationship To Adjacent Designs

### Staged Memory Intake

Staged intake preserves raw input and cheap signals first, then defers deeper
interpretation.

Retrieval is where later contextual reasoning may ask for scoped candidates and
full evidence. That does not mean snippets are trusted. The retrieval contract
keeps the canonical lifecycle vocabulary:

```text
raw_input
fast_intake
proposed_memory
enriched_memory
accepted_memory
canonical_state
superseded
unknown
```

If future UI or reports need shorter display labels, those labels must be
derived metadata only. They must not become canonical lifecycle states.

### Micro-Context

Micro-context is bounded orientation context. It may help form a retrieval
intent or scope a request, but it is not retrieval, memory, full evidence, or
decision authority.

If micro-context is stale, insufficient, or contradictory, retrieval should
report the gap or request bounded clarification rather than treating
micro-context as truth.

### Showcase Files

Showcase files are synthetic, non-authoritative, regenerable views over
canonical sources. They may orient a model before it requests context, but they
do not satisfy evidence requirements.

Important decisions require canonical docs, `accepted_memory`,
`canonical_state`, or full evidence fetched by stable ID or source reference.

### MemoryStore Facade

`MemoryStore` is the future durable memory write boundary. Progressive
retrieval is a future scoped read contract.

The two boundaries must remain separate:

- `MemoryStore` controls writes, lifecycle transitions, raw/original retention,
  promotion, supersession, and audit.
- Progressive retrieval controls read requests, compact candidates, full-body
  evidence access, scope gates, sensitivity gates, and gap reporting.

Retrieval output must not write memory, promote memory, or patch canonical
state.

### SQLite/FTS Schema

Future SQLite/FTS schema concepts support compact scoped candidate discovery.
FTS snippets are search/display aids only. FTS output is not full evidence and
does not authorize decisions.

Full evidence must be fetched separately by stable ID or source reference after
policy checks.

### Compression Policy

Compressed text may support display, ranking, compact context, or snippets
later. It remains non-authoritative.

Compression cannot replace raw/original evidence, cannot authorize promotion,
and cannot satisfy evidence requirements when a decision, provider call, tool
call, final sensitivity decision, or BlueRev assumption is affected.

### Future Context Pack Broker

The future Context Pack Broker may assemble retrieved full evidence into
bounded packages. This retrieval contract supplies scoped candidates, evidence
references, and gap/conflict markers.

This milestone does not implement Context Pack Broker runtime.

### Local Model Form Protocols

Local models may propose retrieval intents or `ContextAccessRequest`-style
forms. They may not query storage, authorize full-body retrieval, choose final
sensitivity, promote memory, route providers, execute tools, or decide truth
from snippets.

When evidence is insufficient, local models must use `not_decided`.

## Retrieval Authority Rule

Retrieval is a source-grounding pathway, not an authority pathway.

Retrieval output cannot authorize:

- memory promotion;
- canonical state changes;
- provider calls;
- tool calls;
- route selection;
- final sensitivity decisions;
- safety decisions;
- execution;
- BlueRev assumptions;
- model runtime approval;
- external API use.

Retrieval can return scoped candidates, metadata, source references, full-body
references, and gap/conflict/stale markers. JarvisOS policy and review decide
what those results may affect later.

## Progressive Retrieval Stages

### 1. Orientation From Micro-Context And Showcase Files

The model or caller starts with bounded orientation surfaces when available.
Orientation can identify project, milestone, likely source areas, current
decisions, and known non-approved behavior.

Orientation cannot prove evidence.

### 2. Scoped Retrieval Request

The caller proposes a scoped retrieval request with purpose, requester source,
downstream consumer, project scope, milestone scope, allowed source classes, and
candidate limits.

Models may propose this request. JarvisOS owns validation and policy.

### 3. Scope And Sensitivity Gate

Scope and sensitivity checks run before candidate discovery.

Unknown or ambiguous scope fails closed or asks for bounded clarification.
Sensitive or secret content requires policy gates before any candidate, snippet,
or full body is exposed.

### 4. Compact Candidate Discovery

Retrieval returns compact candidates first. Candidates include IDs, source
references, snippets, scope, lifecycle status, sensitivity, and match rationale.

Candidates are non-authoritative.

### 5. Candidate Ranking And Deduplication

Future ranking may sort, group, and deduplicate candidates by source,
freshness, lifecycle status, scope match, and relevance.

Ranking does not create truth. Ranking does not override scope, sensitivity,
stale, superseded, or review-only gates.

### 6. Full Body Request By Stable ID Or Source Reference

Full evidence is fetched only after a candidate or source reference is selected
and policy checks pass.

Full-body access is not automatic model-controlled browsing.

### 7. Source-Grounded Context Package Handoff Later

A future Context Pack Broker may assemble approved full evidence into bounded
packages for review or reasoning. The package is downstream of retrieval and
must preserve provenance, scope, freshness, and redaction metadata.

### 8. Stale, Gap, And Conflict Reporting

Retrieval should report when evidence is missing, stale, contradictory,
review-only, sensitive-blocked, or insufficient. The expected answer in these
cases is often `not_decided`, bounded clarification, or stop-for-review.

## Scope-First Rule

Scope is applied before candidate discovery.

Required scope dimensions:

- workspace;
- project;
- milestone when applicable.

Rules:

- no CWD-only authority;
- no global recent memory injection;
- no cross-project leakage;
- no broad "last session" context injection;
- no BlueRev context in JarvisOS-only requests unless a canonical source
  explicitly establishes the boundary;
- unknown scope fails closed or asks for bounded clarification;
- review-only source classes require explicit purpose, scope, sensitivity
  checks, and audit.

## Conservative Default Retrieval

Default retrieval is conservative.

Normal source layer:

- canonical docs;
- accepted memory;
- canonical state;
- accepted decisions;
- source cards;
- artifact metadata.

Exceptional review targets:

- `raw_input`;
- `fast_intake`;
- `proposed_memory`;
- `enriched_memory`;
- `superseded`.

Rules:

- canonical docs, `accepted_memory`, and `canonical_state` records are the
  normal source layer;
- `raw_input`, `proposed_memory`, and `superseded` records are exceptional
  review targets;
- FTS snippets are non-authoritative;
- compressed text is non-authoritative;
- full evidence by stable ID/source reference is required for decisions;
- retrieval output never promotes memory;
- retrieval output never accepts BlueRev assumptions.

## Candidate-First Rule

Compact candidates come before full body retrieval.

Candidates:

- are non-authoritative;
- carry stable IDs or source references;
- carry scope and sensitivity;
- carry lifecycle status;
- carry stale/superseded/review markers;
- include short snippets for search/display only.

FTS result is not evidence authority. Compressed text is not evidence
authority. Snippets are not enough for decisions, provider calls, tool calls,
final sensitivity, memory promotion, canonical state, or BlueRev assumptions.

## Full-Body-By-ID Rule

Full evidence must be fetched only by stable ID or source reference.

Rules:

- source and provenance must be carried forward;
- full body access requires policy and sensitivity checks;
- full body access requires explicit purpose;
- full body access is not automatic model-controlled browsing;
- ID allowlists and max counts are required before implementation;
- full bodies must not be exposed to local or external models without scope,
  sensitivity, redaction, and audit checks.

## Default Versus Review-Only Source Classes

`allowed_source_classes` are the conservative default source layer. They are
the normal targets for orientation, source grounding, and decision support.

`review_only_source_classes` may be used only for explicit purposes such as:

- conflict check;
- sensitivity review;
- enrichment;
- audit;
- source-grounding repair.

`raw_input`, `proposed_memory`, and `superseded` retrieval is not normal model
context.
`raw_input`, `proposed_memory`, and `superseded` content must not be exposed to
local or external models without scope, sensitivity, and redaction checks.

`raw_input`, `proposed_memory`, and `superseded` content cannot authorize
conclusions, provider calls, tool calls, memory promotion, canonical state,
final sensitivity, or BlueRev assumptions.

## Retrieval Result Classes

Future retrieval may return these result classes:

- orientation reference;
- compact candidate;
- source metadata;
- memory record metadata;
- full body reference;
- contradiction marker;
- gap marker;
- stale marker.

Each result class must preserve source reference, scope, sensitivity, and
authority metadata.

## Model Role

Models may:

- propose retrieval intents;
- propose context requests;
- explain why evidence appears insufficient;
- request bounded source/context by known IDs or allowed source classes;
- report `not_decided` when evidence is insufficient.

Models may not:

- directly query storage;
- authorize full-body retrieval;
- retrieve arbitrary memory;
- promote memory;
- decide final truth from snippets;
- decide final sensitivity;
- expose `raw_input`, `proposed_memory`, or `superseded` content;
- route providers;
- execute tools;
- accept BlueRev assumptions.

## External Provider And Tool Boundary

External providers cannot query memory or retrieval directly.

Tools cannot query memory or retrieval directly.

`external_provider` and `tool` are not valid direct requester actor types.
They may appear only as downstream consumers that require separate policy,
redaction, budget, sensitivity, and audit gates before any future use.

JarvisOS may later prepare redacted and scoped context for a downstream
provider or tool after separate policy gates. Provider/tool use remains a later
separate policy and execution decision.

## Conceptual Future Contracts

These contracts are documentation-only. They are not Pydantic models, API
schemas, database schemas, routes, services, migrations, indexes, storage
classes, or runtime files.

### `retrieval_request_v0`

```json
{
  "schema_version": "retrieval_request_v0",
  "request_id": "string",
  "requester": {
    "actor_type": "user|jarvisos|local_model|system",
    "model_proposed": false
  },
  "downstream_consumer": {
    "consumer_type": "none|external_provider|tool|context_pack_broker",
    "requires_redaction": true,
    "requires_policy_gate": true
  },
  "task": {
    "purpose": "orientation|memory_enrichment|decision_support|source_grounding|conflict_check|sensitivity_review|context_pack_candidate|audit|unknown",
    "user_visible_task": "string|null"
  },
  "scope": {
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null"
  },
  "source_policy": {
    "allowed_source_classes": [
      "canonical_doc",
      "accepted_memory",
      "canonical_state",
      "decision",
      "source_card",
      "artifact_metadata"
    ],
    "review_only_source_classes": [
      "raw_input",
      "fast_intake",
      "proposed_memory",
      "enriched_memory",
      "superseded"
    ],
    "include_raw_body": false,
    "include_superseded": false,
    "max_candidates": 10
  },
  "allowed_effect": "candidate_discovery_only",
  "requires_policy_check": true
}
```

Rules:

- `allowed_source_classes` are the conservative default source layer.
- `review_only_source_classes` may be used only for explicit purposes such as
  conflict check, sensitivity review, enrichment, audit, or source-grounding
  repair.
- `raw_input`, `proposed_memory`, and `superseded` retrieval is not normal model
  context.
- `raw_input`, `proposed_memory`, and `superseded` content must not be exposed
  to local or external models without scope, sensitivity, and redaction checks.
- `raw_input`, `proposed_memory`, and `superseded` content cannot authorize
  conclusions, provider calls, tool calls, memory promotion, canonical state, or
  BlueRev assumptions.
- `external_provider` and `tool` are not valid direct requester actor types.
- Downstream provider/tool consumers require separate redaction, policy,
  budget, sensitivity, and audit gates before any future use.

### `retrieval_candidate_v0`

```json
{
  "schema_version": "retrieval_candidate_v0",
  "candidate_id": "string",
  "source_ref": "string",
  "record_id": "string|null",
  "body_ref": "string|null",
  "source_class": "canonical_doc|accepted_memory|canonical_state|decision|source_card|artifact_metadata|raw_input|fast_intake|proposed_memory|enriched_memory|superseded",
  "scope": {
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null"
  },
  "lifecycle_status": "raw_input|fast_intake|proposed_memory|enriched_memory|accepted_memory|canonical_state|superseded|unknown",
  "sensitivity": "public|internal|sensitive|secret|unknown",
  "snippet": "string",
  "snippet_authority": "non_authoritative",
  "requires_full_body": true,
  "requires_review_gate": false,
  "stale": false,
  "why_matched": "string"
}
```

Rules:

- `snippet_authority` must remain `non_authoritative`.
- `requires_full_body = true` whenever the candidate may affect a decision,
  memory promotion, provider use, tool use, final sensitivity, or BlueRev
  assumption.
- Candidates from review-only classes must set
  `requires_review_gate = true`.

### `full_body_request_v0`

```json
{
  "schema_version": "full_body_request_v0",
  "request_id": "string",
  "candidate_id": "string",
  "source_ref": "string",
  "record_id": "string|null",
  "body_ref": "string",
  "purpose": "decision_support|source_grounding|conflict_check|sensitivity_review|context_pack_candidate|audit",
  "scope_confirmed": true,
  "policy_check_required": true,
  "allowed_effect": "evidence_fetch_only"
}
```

Rules:

- full-body requests require a stable candidate ID, source reference, and body
  reference;
- full-body requests require confirmed scope;
- full-body requests remain evidence fetches only;
- a successful full-body request does not authorize promotion, provider calls,
  tool calls, final sensitivity, or BlueRev assumptions.

### `retrieval_gap_report_v0`

```json
{
  "schema_version": "retrieval_gap_report_v0",
  "request_id": "string",
  "gap_type": "missing_source|insufficient_scope|stale_candidate|contradiction|sensitive_block|full_body_required|review_only_gate_required|not_decided",
  "affected_refs": [],
  "model_authority": "none",
  "recommended_next": "request_bounded_context|ask_clarification|full_body_by_id|stop_for_review|not_decided"
}
```

Rules:

- gap reports do not authorize retrieval by themselves;
- `not_decided` is the correct result when evidence is insufficient;
- `stop_for_review` is required when scope, sensitivity, contradiction, or
  review-only class gates block safe use.

## Required Future Validation Layers

Future implementation must validate:

- schema version;
- requester/actor source;
- task purpose;
- workspace scope;
- project scope;
- milestone scope;
- sensitivity and secret gates;
- allowed source classes;
- review-only source-class gates;
- max candidate count;
- full body ID allowlist;
- stale and superseded status handling;
- audit event requirement;
- model authority restrictions;
- downstream provider/tool consumer gates;
- no direct provider/tool requester;
- no global recent-context injection.

Validation is structural and policy-focused. It does not prove semantic truth,
summary quality, source interpretation, memory completeness, final sensitivity,
or BlueRev technical correctness.

## Relationship To Context Pack Broker

The Context Pack Broker may later assemble retrieved full evidence into bounded
packages.

Retrieval contract responsibilities:

- accept scoped requests;
- return compact candidates;
- return source and body references;
- report gaps, stale state, and contradictions;
- enforce full-body-by-ID policy before evidence fetch.

Context Pack Broker responsibilities later:

- choose package shape;
- assemble bounded source-grounded context;
- preserve provenance;
- apply redaction and freshness metadata;
- pass context to approved local or external reasoning paths only after their
  own gates.

Context Pack Broker runtime is not implemented here.

## Relationship To External APIs

Retrieval output does not authorize external provider use.

External prompt packaging and redaction come later. Provider calls require
separate policy, budget, sensitivity, redaction, credential, routing, and audit
gates.

Retrieval may later provide source-grounded evidence references to a packaging
step. It must not send memory, snippets, full bodies, or source files to
external providers directly.

## Failure Modes

Snippet treated as truth:

- Compact text is used as decision authority.
- Required response: require full body by ID/source reference and source
  provenance before decision use.

FTS used as full evidence:

- Search result snippet is treated as original evidence.
- Required response: mark FTS output as non-authoritative and require full
  evidence fetch.

Full body retrieved without ID or policy:

- A model or caller browses memory directly.
- Required response: fail closed; full body requires stable ID/source
  reference, scope, sensitivity, and policy checks.

Global recent context injected:

- Recent sessions enter context regardless of project scope.
- Required response: block global injection and require scoped retrieval.

Cross-project leakage:

- JarvisOS request receives BlueRev, coursework, personal, or unrelated project
  content.
- Required response: scope filters before candidates and audit on failures.

Secret or sensitive content indexed or returned:

- Secret, `.env`, raw tool output, or sensitive payload appears in snippets or
  full bodies.
- Required response: gate indexing and full-body access; fail closed when
  sensitivity is unknown.

Stale or superseded memory treated as active:

- Old record is used as current truth.
- Required response: return stale/superseded marker and require review.

`raw_input`, `proposed_memory`, or `superseded` records returned as ordinary
model context:

- Review-only records become normal local-model input.
- Required response: require explicit purpose, review gate, sensitivity check,
  redaction, and audit.

Model retrieves arbitrary memory:

- Model chooses database/filesystem reads directly.
- Required response: block direct storage access; models may propose forms only.

Retrieval output promotes BlueRev assumptions:

- Candidate text becomes accepted BlueRev material, geometry, process, or
  parameter assumption.
- Required response: require source-grounded review, full evidence, and later
  promotion policy; otherwise `not_decided`.

External provider or tool queries retrieval directly:

- Provider/tool becomes requester.
- Required response: reject; provider/tool can only be downstream consumer
  after separate policy gates.

Retrieval bypasses MemoryStore/storage boundaries:

- Read path exposes private storage internals or unscoped records.
- Required response: retrieval must use controlled read boundaries and policy
  checks; writes remain behind MemoryStore.

Context pack becomes unbounded:

- Retrieval expands into broad repo/memory dumping.
- Required response: candidate limits, source ID allowlists, package budgets,
  and gap reports.

## Future Implementation Acceptance Criteria

Future implementation may proceed only when:

- retrieval requests require schema version, actor, purpose, scope, and source
  policy;
- scope filters run before candidate discovery;
- sensitivity and secret gates run before snippets or full bodies are returned;
- default source classes are conservative;
- `raw_input`, `proposed_memory`, and `superseded` classes require explicit
  review purpose and audit;
- compact candidates include source references and lifecycle status;
- snippets and compressed text are marked non-authoritative;
- full bodies require stable ID/source reference and policy checks;
- stale, superseded, gap, and contradiction markers are returned;
- models can propose retrieval intents but cannot query storage;
- providers and tools cannot query retrieval directly;
- downstream provider/tool use requires separate policy, budget, sensitivity,
  redaction, and audit gates;
- retrieval output cannot promote memory or canonical state;
- retrieval output cannot authorize final sensitivity or BlueRev assumptions;
- tests cover cross-project leakage, unknown scope, sensitive blocks,
  review-only gates, stale/superseded handling, full-body-by-ID access, and
  snippet non-authority.

## Milestone Boundary Confirmation

1D-F is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- routes or APIs;
- database migrations;
- SQLAlchemy models;
- Pydantic runtime models;
- repository or storage classes;
- FTS runtime queries;
- FTS indexes;
- retrieval runtime;
- RAG runtime;
- memory runtime;
- Context Pack Broker runtime;
- compression runtime;
- local or external model calls;
- provider calls;
- hooks;
- MCP;
- worker processes;
- viewers;
- tool execution;
- BlueRev modeling;
- external reference audits;
- vendored code;
- runtime-approved model status.

This milestone does not start `1D-G - Holdout intake generalization set`.
