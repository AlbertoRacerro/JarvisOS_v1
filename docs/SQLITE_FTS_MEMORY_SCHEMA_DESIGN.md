# SQLite/FTS Memory Schema Design

Milestone: 1D-E - SQLite/FTS schema design

## Executive Summary

This document designs the future SQLite/FTS schema concepts for staged memory
and compact retrieval.

Core principle:

```text
SQLite/FTS stores staged memory records and compact retrieval indexes, but MemoryStore remains the write boundary and raw/original evidence remains authoritative
```

This milestone is design-only. It does not create migrations, tables,
SQLAlchemy models, Pydantic models, APIs, repositories, runtime queries, memory
runtime, retrieval runtime, compression runtime, hooks, MCP, workers, viewers,
provider calls, tool execution, or BlueRev modeling.

## Design Goals

- Support the staged memory lifecycle.
- Keep `MemoryStore` as the only future write boundary.
- Preserve source, provenance, scope, and auditability.
- Keep raw/original evidence references authoritative.
- Support compact-first retrieval without full-body over-fetch.
- Keep FTS indexes scoped and non-authoritative.
- Avoid blindly indexing secrets or sensitive content.
- Stay migration-friendly while using SQLite first.

## Non-Goals And Hard Boundaries

This milestone does not add:

- backend code;
- frontend code;
- database migrations;
- SQLAlchemy models;
- Pydantic runtime models;
- routes or APIs;
- repository or storage classes;
- FTS runtime queries;
- memory runtime;
- retrieval runtime;
- compression runtime;
- model or provider calls;
- hooks;
- MCP;
- worker processes;
- viewers;
- BlueRev modeling;
- external reference audits;
- vendored code.

All table/entity names below are conceptual only.

## Relationship To Adjacent Designs

### MemoryStore Facade

The schema sits behind `MemoryStore`. Future durable writes must pass through
the facade before any table receives data. Schema design must not create public
write authority for models, routes, hooks, workers, tools, providers, or UI.

Canonical design:

- `docs/MEMORYSTORE_FACADE_DESIGN.md`

### Staged Memory Intake

The schema supports the staged lifecycle from `docs/STAGED_MEMORY_INTAKE.md`:

```text
raw_input
fast_intake
proposed_memory
enriched_memory
accepted_memory
canonical_state
superseded
```

### Compression Policy

Compression remains optional and later. The schema must preserve raw/original
body references even if compact or compressed snippets are added later.

Canonical design:

- `docs/INTERNAL_COMPRESSION_POLICY_TESTS.md`

### Future Retrieval Contract

Progressive retrieval contract design lives in
`docs/PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`. This schema concept supports
compact candidate retrieval first and full body by ID/source reference second.
It does not add retrieval runtime, database queries, or FTS indexes.

### Future Context Pack Broker

The future Context Pack Broker may consume scoped compact candidates and request
full evidence by ID after policy checks. This milestone does not add Context
Pack Broker runtime.

### Audit And Events

Write, promotion, supersession, sensitivity, compression, and indexing events
must be auditable. Event tables here are conceptual only and do not implement
runtime logging.

## Future Conceptual Tables And Entities

### `memory_sources`

Purpose:

- Track source/input records and provenance.
- Preserve the link between raw input, accepted state, and later memory records.

Conceptual content:

- source ID;
- input ID;
- source type;
- workspace/project/milestone scope;
- timestamp;
- raw/original body reference;
- sensitivity;
- provenance.

### `memory_records`

Purpose:

- Represent staged memory records and lifecycle status.

Conceptual content:

- stable record ID;
- schema version;
- stage/status;
- source ID;
- workspace/project/milestone scope;
- sensitivity;
- current body reference;
- audit metadata.

### `memory_bodies`

Purpose:

- Store or reference raw/original, compact, and future compressed bodies.

Conceptual content:

- body ID;
- record/source ID;
- body kind;
- raw/original reference;
- compact/snippet reference;
- compression status;
- retention flags;
- created timestamp.

### `memory_intake_signals`

Purpose:

- Store normalized fast-intake signals linked to source and record IDs.

Conceptual content:

- signal ID;
- source ID;
- schema version;
- observable flags;
- broad buckets;
- uncertainty;
- confidence;
- deterministic/model provenance.

### `memory_cards`

Purpose:

- Store proposed/enriched/accepted card-shaped memory objects.

Conceptual content:

- card ID;
- record ID;
- card type;
- status;
- linked sources;
- review state;
- structured fields.

### `memory_links`

Purpose:

- Link records, cards, sources, decisions, artifacts, and supersession chains.

Conceptual content:

- link ID;
- from ID;
- to ID;
- link type;
- scope;
- provenance;
- created timestamp.

### `memory_audit_events`

Purpose:

- Record write, validation, transition, promotion, supersession, sensitivity,
  compression, and indexing events.

Conceptual content:

- event ID;
- record/source/card ID;
- event type;
- actor/system source;
- timestamp;
- before/after status where applicable;
- reason;
- policy result.

### `memory_fts`

Purpose:

- Index compact snippets for scoped candidate retrieval.

Conceptual content:

- record ID;
- source ID;
- workspace/project/milestone scope;
- compact snippet;
- sensitivity/index eligibility;
- source head or stale marker.

FTS must not index full bodies or secrets.

## Required Fields

Future schema concepts require:

- stable IDs;
- schema version;
- workspace scope;
- project scope;
- milestone scope;
- source/input IDs;
- timestamps;
- stage/status;
- sensitivity;
- provenance;
- raw/original body reference;
- compact/snippet body reference;
- audit metadata.

## Staged Lifecycle Mapping

| Stage | Schema concept | Authority |
| --- | --- | --- |
| `raw_input` | `memory_sources` plus raw/original `memory_bodies` reference | Preserved evidence only. |
| `fast_intake` | `memory_intake_signals` linked to source | Cheap signals, not canonical truth. |
| `proposed_memory` | `memory_records` and `memory_cards` in proposed status | Candidate memory only. |
| `enriched_memory` | Record/card with enrichment links and audit | Interpreted with more context, still not necessarily accepted. |
| `accepted_memory` | Accepted record/card status | Working knowledge subject to source links and audit. |
| `canonical_state` | Linked accepted record/decision state | Stable state only after policy promotion. |
| `superseded` | Supersession link and status | Auditable, not active. |

## FTS Design Concepts

FTS is for compact scoped candidates only.

Rules:

- index compact snippets only;
- apply source scope filters;
- apply project/workspace filters;
- apply milestone filters when relevant;
- avoid full body over-fetch;
- do not index secrets;
- do not blindly index sensitive content;
- carry source/provenance IDs with each result;
- support stale index detection later;
- treat FTS output as candidate retrieval, not evidence authority.

Full evidence requires separate full-body retrieval by stable ID or source
reference after policy checks.

## Raw/Original Retention

Raw evidence cannot be replaced by compressed text.

Rules:

- raw/original body references must survive later compression;
- compact snippets must remain linked to raw/original evidence;
- body references must carry source/provenance;
- deletion and retention are deferred to later policy;
- compression status must not imply evidence authority;
- FTS snippets are not canonical source.

## Scope And Leakage Controls

Required scope:

- workspace;
- project;
- milestone when applicable.

Controls:

- no CWD-only authority;
- no global recent memory injection;
- no cross-project leakage;
- scope filters before candidate retrieval;
- unknown scope fails closed or remains `raw_input` or `proposed_memory`
  pending review.

## Audit Requirements

Future audit concepts must cover:

- write events;
- validation failures;
- promotion events;
- supersession events;
- sensitivity changes;
- compression events later;
- indexing events later;
- stale index detection later.

Audit records must carry source IDs, scope, timestamp, actor/system source, and
policy result.

## Future Migration Considerations

Design should remain migration-friendly:

- schema versioning is required;
- records should tolerate added fields;
- SQLite is first;
- PostgreSQL later remains possible;
- avoid hard-coding SQLite-only assumptions where possible;
- avoid table shapes that make raw/original body retention optional;
- keep FTS indexes rebuildable from source records and compact snippets.

SQLite-specific features may be used later, but conceptual ownership should not
depend on bypassing `MemoryStore`.

## Failure Modes

Model bypasses MemoryStore:

- A model writes directly to tables.
- Mitigation: schema sits behind MemoryStore only.

Full body indexed into FTS:

- Full evidence over-fetches into compact search.
- Mitigation: FTS indexes compact snippets only.

Secret indexed:

- Sensitive text becomes searchable or exposed.
- Mitigation: eligibility and sensitivity gates before indexing.

Cross-project retrieval leakage:

- A query returns another project's memory.
- Mitigation: workspace/project/milestone scope filters.

Stale FTS results:

- Candidate index points to old or superseded state.
- Mitigation: stale markers, rebuild policy, and audit.

Canonical state overwritten without audit:

- Active state changes without trace.
- Mitigation: promotion and supersession events are required.

Raw body lost after compression:

- Compact text replaces evidence.
- Mitigation: raw/original body references are required and authoritative.

## Future Implementation Acceptance Criteria

Future implementation may proceed only when:

- MemoryStore remains the write boundary;
- schema migrations are explicit and reviewed;
- stable IDs and source IDs are required;
- raw/original body references are required;
- scope fields are required for records and FTS;
- FTS indexes compact snippets only;
- secret/sensitive indexing is gated;
- audit events exist for writes and state transitions;
- stale index detection or rebuild policy exists;
- full body retrieval remains by ID/source reference;
- tests cover cross-project leakage and raw body retention;
- no route, UI, model, hook, worker, provider, or tool writes directly to
  storage.

## Milestone Boundary Confirmation

1D-E is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- database migrations;
- SQLAlchemy models;
- Pydantic runtime models;
- routes or APIs;
- repository or storage classes;
- FTS runtime queries;
- memory runtime;
- retrieval runtime;
- compression runtime;
- model or provider calls;
- hooks;
- MCP;
- worker processes;
- viewers;
- BlueRev modeling;
- external reference audits;
- vendored code.
