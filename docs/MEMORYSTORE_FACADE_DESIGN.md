# MemoryStore Facade Design

Milestone: 1D-C - MemoryStore facade design

## Executive Summary

`MemoryStore` is the future single memory write boundary for JarvisOS.

Core principle:

```text
MemoryStore is the single future memory write boundary; models, hooks, routes, workers, tools, and providers must not write durable memory directly.
```

The facade is inspired by Cavemem's `MemoryStore` pattern, but this milestone
does not copy Cavemem runtime code, storage code, hooks, worker, MCP, viewer,
compression, or embeddings.

`MemoryStore` is a future contract, not an implementation. This milestone does
not create a class, database tables, routes, hooks, generator scripts, runtime
memory writes, retrieval runtime, compression runtime, Context Pack Broker
runtime, provider calls, tool execution, or BlueRev modeling.

## Design Goals

- Define one future facade for all memory-related writes.
- Preserve the staged memory lifecycle without letting callers bypass policy.
- Keep raw/original evidence linked and recoverable.
- Separate proposed memory from accepted and canonical state.
- Make model output advisory only.
- Require deterministic provenance, source links, validation, policy overrides,
  and audit before any durable memory write.
- Keep compact-first retrieval as a future design input, not runtime behavior in
  this milestone.
- Adapt Cavemem's write-boundary lesson without vendoring external code.

## Non-Goals And Hard Boundaries

This milestone does not add:

- backend code;
- frontend code;
- routes or APIs;
- database schema or migrations;
- generator scripts;
- actual `MemoryStore` runtime files or classes;
- local or external model calls;
- MCP;
- hooks;
- worker processes;
- viewers;
- retrieval runtime;
- memory runtime;
- compression runtime;
- Context Pack Broker runtime;
- provider routing;
- tool execution;
- BlueRev modeling;
- vendored external repository code;
- runtime-approved model status.

This document is design-only. Conceptual function names and JSON contracts are
not implemented methods, schemas, routes, migrations, or runtime files.

## Cavemem-Inspired Lessons

JarvisOS should copy the facade/write-boundary pattern, not Cavemem code.

Useful lessons:

- A single facade should own memory writes.
- Hooks/events should feed the facade later, not bypass it.
- Observations, summaries, compact context, and full evidence should remain
  separate.
- Compact-first retrieval should precede full-body retrieval.
- Full evidence must remain retrievable by ID or source reference.
- Raw/original retention is mandatory before compression.
- Background worker/indexing should be lazy and non-authoritative.
- CWD-only scope is insufficient for JarvisOS.

Rejected for this milestone:

- copying Cavemem TypeScript code;
- copying Cavemem hooks/runtime now;
- copying Cavemem storage code;
- copying Cavemem worker, MCP, viewer, compression, or embedding runtime;
- treating compact-first retrieval as current runtime;
- allowing hooks, workers, tools, routes, providers, UI, or models to write
  durable memory directly.

## Relationship To Adjacent Designs

### Staged Memory Intake

`MemoryStore` is the future write boundary for the staged lifecycle documented
in `docs/STAGED_MEMORY_INTAKE.md`.

The lifecycle remains:

```text
raw_input
fast_intake
proposed_memory
enriched_memory
accepted_memory
canonical_state
superseded
```

Fast intake stays cheap. Enrichment, acceptance, and canonical promotion remain
later policy-controlled transitions.

### Micro-Context

Micro-context is bounded orientation context, not memory runtime. Future
micro-context snapshots may read accepted state or source-grounded summaries
after `MemoryStore` and accepted-state boundaries exist. Hooks/events must not
write micro-context or memory directly.

### Showcase Files

Showcase files are synthetic, non-authoritative, regenerable views over
canonical sources. They are not durable memory and do not bypass `MemoryStore`.

### Future Context Pack Broker

The Context Pack Broker remains a future service. It may later request compact
memory candidates or full evidence by ID through controlled read boundaries.
This milestone does not implement Context Pack Broker runtime.

### Future Compression Policy

Compression is later and optional. Compact text must not replace raw/original
evidence. Compression policy needs token-preservation tests and retention rules
before runtime use. The policy test design lives in
`docs/INTERNAL_COMPRESSION_POLICY_TESTS.md`.

### Future SQLite/FTS Schema

Storage schema design is separate. `MemoryStore` describes the facade boundary
and lifecycle authority before tables, indexes, FTS, migrations, or storage
repositories exist. Future SQLite/FTS schema concepts are documented in
`docs/SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`.

### Future Retrieval Contract

Retrieval remains deferred. The design direction is compact candidates first,
then full body by stable ID or source reference only. This milestone does not
create retrieval APIs or runtime retrieval.

### Future Hooks/Events

Hooks/events are future triggers only. They must feed controlled boundaries and
must never write memory directly. Hook/event implementation must wait for
MemoryStore facade, storage schema, policy, scope, retention, and tests.

## Single Write Boundary Rule

All future durable memory writes must pass through `MemoryStore`.

The following must not write durable memory directly:

- models;
- hooks;
- routes;
- workers;
- tools;
- providers;
- UI;
- Context Pack Broker;
- micro-context assembler;
- showcase generators;
- imports;
- admin utilities.

If a future component has memory-relevant data, it submits a scoped source,
event, or proposal to `MemoryStore`. The facade validates, applies deterministic
policy, records provenance, preserves raw/original references, writes staged
records, and emits audit events.

## Memory Lifecycle Ownership

`MemoryStore` owns future state-transition authority for:

- `raw_input`;
- `fast_intake`;
- `proposed_memory`;
- `enriched_memory`;
- `accepted_memory`;
- `canonical_state`;
- `superseded`.

Ownership means the facade enforces structural validity, allowed transitions,
source links, provenance, policy overrides, review requirements, and audit. It
does not mean model output becomes semantically trusted.

## Future Input Classes

The following input classes may reach `MemoryStore` in the future:

- raw user input;
- Codex/task completion reports;
- explicit user memory requests;
- deterministic intake signals;
- model-proposed memory cards;
- canonical doc/ADR changes;
- future hook/event records.

Each input must carry scope, provenance, source reference, and allowed effect.
Unscoped inputs should fail closed or remain raw/proposed until scope is
resolved.

## Conceptual Facade Responsibilities

These names are conceptual future responsibilities only, not implemented
methods:

- `record_raw_input`
- `record_fast_intake`
- `propose_memory_card`
- `record_enrichment`
- `accept_memory`
- `promote_canonical`
- `supersede_memory`
- `get_compact_candidates`
- `get_full_body_by_id`

Write responsibilities and read responsibilities should remain distinct. Read
concepts do not authorize retrieval runtime in this milestone.

## Required Validation Layers

Future `MemoryStore` writes must validate:

- schema version;
- source/input ID;
- provenance;
- timestamp;
- allowed state transition;
- raw/original retention reference;
- sensitivity hard overrides;
- secret/path checks;
- field length and enum checks;
- audit event requirement;
- model authority restrictions.

Validation remains structural and policy-focused. It does not prove semantic
truth, memory completeness, strategic correctness, or subtle sensitivity
correctness.

## Model Authority Boundary

Models may propose.

Models may not:

- authorize memory writes;
- promote memory;
- decide final sensitivity;
- retrieve arbitrary memory;
- patch canonical state;
- accept BlueRev assumptions from output alone;
- bypass `MemoryStore`;
- write directly to durable storage.

BlueRev assumptions must not be accepted from model output alone. Acceptance
requires source-grounded review, explicit policy, and future promotion
authority.

## Future Write Transaction Concept

Conceptual flow:

```text
source event / raw input / model proposal
-> MemoryStore facade
-> structural validation
-> deterministic policy overrides
-> raw/original retention reference
-> staged memory record
-> audit event
-> later enrichment / retrieval / promotion
```

Conceptual future write transaction skeleton:

```json
{
  "schema_version": "memory_store_write_request_v0",
  "source": {
    "input_id": "string",
    "source_type": "user_input|codex_report|canonical_doc|hook_event|model_proposal|manual_import",
    "workspace_id": "string|null",
    "project_id": "jarvisos|bluerev|coursework|personal|general|unknown",
    "milestone_id": "string|null",
    "timestamp": "timestamp|null",
    "raw_payload_ref": "string|null"
  },
  "requested_operation": "record_raw_input|record_fast_intake|propose_memory_card|record_enrichment|accept_memory|promote_canonical|supersede_memory",
  "payload_kind": "raw_text|fast_intake_signal|memory_card|decision_card|assumption_card|evidence_card|source_card|event_record",
  "model_proposed": false,
  "requires_review": true,
  "allowed_effect": "staged_record_only"
}
```

This is a conceptual contract only. It does not create code, schemas, routes,
database tables, migrations, or runtime files.

Future write transaction steps:

- receive source, event, or proposal;
- validate structure;
- attach deterministic provenance;
- apply hard policy overrides;
- preserve raw/original payload reference;
- store proposed or staged record;
- record audit event;
- return stable ID and status.

## Future Read Boundary Concept

Future memory reads should use progressive disclosure:

- compact candidates first;
- full body by ID only;
- source and provenance carried forward;
- scope filters applied before candidates are returned;
- retrieval runtime deferred.

Compact candidates may include IDs, source references, timestamps, scope,
status, short snippets, and sensitivity metadata. Full body retrieval must
require stable ID/source reference and policy checks. No component should inject
global recent memory into model context.

## Retention And Raw/Original Preservation Policy

Raw input must survive.

Rules:

- raw/original payload references are mandatory before staged records become
  durable;
- compression is optional and later;
- compact text cannot replace original evidence;
- deletion and retention require later policy;
- compressed text must remain linked to raw/original evidence;
- source IDs and provenance must survive enrichment and promotion.

Compression must not be used to erase, mutate, or replace technical evidence.

## Scope Rules

All memory writes and reads must be scoped by:

- workspace;
- project;
- milestone when applicable.

Scope rules:

- no global recent memory injection;
- no cross-project leakage;
- no CWD-only authority;
- no BlueRev assumption acceptance from unscoped or model-only inputs;
- unknown scope fails closed or remains raw/proposed pending review.

## Failure Modes

Bypassing `MemoryStore`:

- Routes, workers, hooks, UI, providers, tools, or models write directly to
  storage.
- Mitigation: single facade boundary and tests that reject bypasses.

Model-written memory:

- A model proposal is treated as accepted memory.
- Mitigation: model output remains proposed until validation, review, and policy
  allow promotion.

Hook writes directly to DB:

- Future capture hooks skip validation and write raw memory.
- Mitigation: hooks/events feed `MemoryStore` only.

Tool output captured without allowlist/redaction:

- Tool output stores secrets, private files, or irrelevant logs.
- Mitigation: explicit allowlists, truncation, redaction, scope, and review.

Accepted/canonical promotion too early:

- Proposed memory becomes accepted state before evidence supports it.
- Mitigation: allowed transitions, review gates, source links, and audit.

Raw evidence lost after compression:

- Compact text replaces original evidence.
- Mitigation: raw/original retention reference is required before compression.

Sensitive data leaked to provider/retrieval:

- Memory content enters external providers or broad retrieval without policy.
- Mitigation: sensitivity hard overrides, local-first defaults, and scope
  filters.

Stale or contradictory memory:

- Older records conflict with newer canonical state.
- Mitigation: supersession, source links, contradiction checks, and status
  transitions.

## Future Implementation Acceptance Criteria

Future implementation may proceed only when:

- all memory writes pass through a `MemoryStore` facade;
- direct durable writes by models, hooks, routes, workers, tools, providers, UI,
  imports, and admin utilities are blocked;
- staged lifecycle transitions are explicit and tested;
- raw/original payload references are required;
- deterministic provenance and scope are attached;
- sensitivity hard overrides and secret/path checks exist;
- audit events are recorded for writes and transitions;
- compact candidates and full-body-by-ID read concepts are separated;
- no global recent memory injection exists;
- cross-project leakage is prevented;
- compression cannot replace raw/original evidence;
- model output cannot promote memory or canonical state;
- BlueRev assumptions cannot be accepted from model output alone;
- external provider use remains explicitly gated and out of the memory write
  path.

## Milestone Boundary Confirmation

1D-C is a docs-only design milestone.

It does not add:

- backend code;
- frontend code;
- routes or APIs;
- database schema or migrations;
- generator scripts;
- actual `MemoryStore` runtime files or classes;
- local or external model calls;
- MCP;
- hooks;
- worker processes;
- viewers;
- retrieval runtime;
- memory runtime;
- compression runtime;
- Context Pack Broker runtime;
- provider routing;
- tool execution;
- BlueRev modeling;
- vendored external repository code;
- runtime-approved model status.

Cavemem remains an architectural reference only.
