# Staged Memory Intake

This document defines the JarvisOS design for fast, staged memory intake.

Core rule:

```text
write fast, enrich later, reason deeply only on retrieval
```

Memory ingestion must preserve useful evidence cheaply at write time without
pretending that one-shot semantic classification has produced canonical truth.

## Why This Replaces One-Shot Classification

The 1C classification diagnostics showed that local models can produce valid
JSON under bounded forms, but valid JSON did not imply reliable semantic
agreement. Model-specific profiles improved structural compliance, while
`topic_hints`, `context_need_hint`, and overconfident wrong outputs remained
unstable.

That means memory intake must not depend on a fine-grained one-shot classifier
being correct every time a user says something worth preserving.

The correct foundation is staged:

- preserve raw text and provenance immediately;
- extract observable signals cheaply;
- assign broad uncertain buckets;
- defer expensive context interpretation;
- promote only after validation, enrichment, review, or repeated reliable use.

## Design Principle

Initial memory storage is intentionally cheap and approximate.

At write time, JarvisOS should preserve:

- raw text;
- source or input ID;
- timestamp;
- conversation or project reference when available;
- observable boolean signals;
- broad uncertain buckets;
- uncertainty flags;
- enrichment status.

Heavy contextual interpretation happens later only when the memory is retrieved
for reasoning, used in a decision, conflicts with another memory, becomes
high-value, is sensitive, is promoted from raw/proposed to accepted/canonical,
or has a full project context pack available.

## Staged Lifecycle

```text
raw_input
fast_intake
proposed_memory
enriched_memory
accepted_memory
canonical_state
superseded
```

### `raw_input`

The original text or source payload is preserved with an input ID, timestamp,
and provenance. This is the durable fallback that lets later enrichment
reinterpret weak or stale tags.

### `fast_intake`

JarvisOS records a `FastIntakeSignalForm`. This is a cheap signal envelope, not
a final memory object. It captures observable flags, broad buckets, explicit
mentions, a surface summary, uncertainty, and confidence in extraction.

### `proposed_memory`

A later enrichment pass may transform raw intake into a candidate memory object
such as a `MemoryCard`, `DecisionCard`, `AssumptionCard`, `EvidenceCard`,
`SourceCard`, or `KnowledgeCard`. Proposed memory is still not canonical truth.

### `enriched_memory`

The proposed object is interpreted with more context, source links, conflict
checks, sensitivity review, or stronger model/human review. Enrichment may
split one raw input into multiple cards or merge repeated evidence.

### `accepted_memory`

JarvisOS has enough confidence to use the memory as accepted working knowledge,
subject to source links, status, and audit metadata.

### `canonical_state`

The memory has been promoted into a stable project or system state, such as a
current decision, accepted assumption, validated source, or durable user
preference.

### `superseded`

The memory remains auditable but no longer represents the active state because
it was replaced, contradicted, expired, or corrected.

## Intake Is Not Enrichment

JarvisOS separates four jobs that should not be collapsed into one model call.

| Job | Timing | Purpose | Output authority |
| --- | --- | --- | --- |
| Observable extraction | Write time | Detect visible facts such as numbers, commands, prior-context references, or explicit decisions. | Structural signal only. |
| Broad bucket assignment | Write time | Place the input into coarse uncertain buckets for later retrieval. | Advisory routing signal only. |
| Contextual enrichment | Later, on demand | Interpret meaning using project context, source history, conflicts, and sensitivity policy. | Proposed or enriched memory. |
| Canonical promotion | Later, policy controlled | Decide whether a memory becomes accepted or canonical state. | JarvisOS policy, review, and audit. |

## FastIntakeSignalForm v0

`FastIntakeSignalForm` is not a final memory object. It is a cheap intake
envelope used to decide whether an input is worth preserving and how broadly to
bucket it.

Raw text must be preserved separately and linked by `source.input_id`.

```json
{
  "schema_version": "fast_intake_v0",
  "source": {
    "input_id": "string",
    "conversation_id": "string|null",
    "timestamp": "string|null",
    "raw_text_preserved": true
  },
  "observable_flags": {
    "contains_user_preference": false,
    "contains_user_decision": false,
    "contains_assumption": false,
    "contains_design_constraint": false,
    "contains_open_question": false,
    "contains_action_request": false,
    "contains_test_result": false,
    "contains_numbers_or_metrics": false,
    "mentions_previous_context": false,
    "mentions_project_or_artifact": false,
    "mentions_code_or_command": false,
    "mentions_source_or_literature": false
  },
  "broad_storage_buckets": {
    "storage_relevance": "none | low | medium | high",
    "record_bucket": "request | note | decision | assumption | evidence | result | preference | issue | parameter | source | unknown",
    "project_bucket": "jarvisos | bluerev | coursework | personal | general | unknown",
    "domain_bucket": "local_ai | memory | retrieval | modeling | software | bioprocess | reactor_design | coursework | personal | general | unknown",
    "sensitivity_bucket": "public | internal | sensitive | secret | unknown",
    "status_bucket": "raw | proposed | accepted | not_decided | unknown"
  },
  "explicit_mentions": {
    "entities": [],
    "projects": [],
    "artifacts": [],
    "commits_or_versions": [],
    "numbers_or_metrics": []
  },
  "short_description": {
    "surface_summary": "",
    "preserved_user_phrasing": []
  },
  "uncertainty": {
    "needs_enrichment": false,
    "needs_user_confirmation": false,
    "reason": "none | ambiguous | missing_context | sensitive | important_decision | weak_tags | unknown"
  },
  "confidence": {
    "observable": 0.0,
    "bucket_assignment": 0.0
  }
}
```

Rules:

- This form uses broad buckets, not a fine-grained final taxonomy.
- This form may be wrong without corrupting canonical memory.
- This form should be cheap to compute.
- This form should tolerate uncertainty.
- This form must never authorize actions.
- A valid form does not prove semantic truth.

### AI-Facing Flat Smoke Contract

The nested `FastIntakeSignalForm` remains the canonical internal normalized
envelope. Local models should not be required to generate the full nested
envelope directly during smoke diagnostics.

`FastIntakeFlatSignalV0` is an AI-facing smoke/adapter contract. It flattens the
observable booleans, broad buckets, uncertainty fields, and confidence fields
into one JSON object. JarvisOS validates the flat object, then normalizes it
into the canonical nested `FastIntakeSignalForm` by attaching deterministic
source metadata from the case/input.

The flat smoke contract may include only two advisory channels:

- `uncertain_fields`: bounded list of known field names, max 5 items.
- `advisory_note`: bounded string, max 160 characters.

These channels are diagnostic only. They must not be copied into canonical
memory, and they cannot authorize tools, providers, retrieval, memory writes,
actions, routes, final sensitivity, or canonical promotion.

## Hybrid Field Ownership

Fast intake uses hybrid ownership instead of asking a local model to own every
field. The durable rule is:

```text
models may propose intake hints;
JarvisOS validates, owns policy, and decides;
no intake field authorizes runtime action.
```

JarvisOS owns source metadata, schema versioning, raw-text preservation links,
runtime approval, memory-write authorization, retrieval authorization, tool
authorization, provider authorization, route selection, final sensitivity
decisions, and canonical promotion.

Deterministic rules are first owner for obvious signals such as numbers or
metrics, code or command mentions, project/artifact mentions, source/literature
references, obvious secret detection, and obvious status phrases. AI remains
useful only as advisory input for semantically subtle preferences, decisions,
assumptions, constraints, questions, action requests, previous-context
references, and hybrid bucket hints.

The detailed field ownership policy is documented in:

- `docs/HYBRID_INTAKE_FIELD_OWNERSHIP.md`

## Reference Implementation Pattern Audit

1C-Z-T audited Cavemem and Caveman as external implementation references before
the 1D memory/showcase design sequence:

- `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`

The durable lessons are architectural only: a future `MemoryStore` facade should
own the write boundary, retrieval should use compact candidates before full
body-by-ID access, raw/original text must survive compression, and any internal
compression policy needs token-preservation tests. JarvisOS has not vendored
Cavemem/Caveman code and has not added runtime memory, retrieval, compression,
MCP, hooks, worker, viewer, route, UI, or provider behavior from that audit.

## Later Memory Card Types

The following cards are later enrichment targets, not write-time requirements:

- `KnowledgeCard`
- `MemoryCard`
- `DecisionCard`
- `AssumptionCard`
- `EvidenceCard`
- `SourceCard`

Fast intake decides whether and how to preserve the source. It does not need to
know which final card type will eventually win.

## Micro-Context And Full Context Pack

### Always-Loaded Micro-Context

The future always-loaded micro-context is a small, cheap context surface. It may
include:

- active projects;
- current focus;
- recent decisions;
- short taxonomy;
- sensitivity policy summary.

Micro-context exists to make fast intake less blind without forcing full
project interpretation on every input.

### Full Context Pack

A full context pack is heavier and loaded only during enrichment, retrieval,
review, or decision use. It may include source documents, project state,
decision history, related memories, evidence, open questions, and conflict
metadata.

Fast intake should not require a full context pack.

## Enrichment Triggers

JarvisOS should trigger contextual enrichment when:

- memory is retrieved for reasoning;
- memory is used in a decision;
- memory conflicts with another memory;
- memory becomes high-value;
- memory is sensitive or secret;
- memory is promoted from raw/proposed to accepted/canonical;
- a full project context pack is available;
- user confirmation is required;
- repeated related intake suggests a durable pattern.

## Deterministic Validation

JarvisOS validates deterministically:

- schema version;
- required fields;
- enum values;
- booleans;
- field length;
- source/input IDs;
- timestamp shape when present;
- confidence bounds;
- raw-text-preserved flag;
- allowed status transitions;
- obvious secrets such as API keys, passwords, tokens, `.env` content, and
  forbidden paths.

Sensitive and secret handling is overridden deterministically. BlueRev internal
assumptions should not be promoted automatically.

## Model Role

The model may propose:

- observable flags;
- broad buckets;
- explicit mentions;
- surface summaries;
- uncertainty flags;
- enrichment recommendations;
- candidate memory cards during later enrichment.

The model cannot authorize:

- execution;
- memory promotion;
- canonical state changes;
- provider calls;
- retrieval access;
- route selection;
- tool use;
- sensitivity downgrades;
- BlueRev assumption acceptance;
- external API use.

JarvisOS owns validation, persistence, promotion, execution, audit, and policy.

## Examples

### Example 1 - JarvisOS Architecture Decision

Input:

```text
Memory ingestion should be cheap at write time; full contextual interpretation should happen later only when the memory is retrieved or promoted.
```

Expected fast intake:

- `contains_design_constraint = true`
- `contains_user_decision = true` or `contains_user_preference = true`,
  depending on wording and source context
- `storage_relevance = high`
- `record_bucket = decision` or `preference`
- `project_bucket = jarvisos`
- `domain_bucket = memory`
- `status_bucket = proposed`
- `needs_enrichment = true`
- `reason = important_decision`

### Example 2 - BlueRev Tentative Assumption

Input:

```text
For BlueRev, ETFE is a candidate material for the tubes, but it is not decided yet.
```

Expected fast intake:

- `contains_assumption = true`
- `contains_design_constraint = true`
- `storage_relevance = high`
- `record_bucket = assumption`
- `project_bucket = bluerev`
- `domain_bucket = reactor_design`
- `status_bucket = not_decided`
- `sensitivity_bucket = internal` or `sensitive`
- `needs_enrichment = true`

This must not promote ETFE to an accepted BlueRev material decision.

### Example 3 - Low-Value Casual Message

Input:

```text
ok grazie
```

Expected fast intake:

- `storage_relevance = none` or `low`
- `record_bucket = unknown`
- `needs_enrichment = false`

JarvisOS may still preserve raw conversation logs according to retention policy,
but it does not need to create a proposed memory card.

## Boundaries

- `FastIntakeSignalForm` is not canonical truth.
- Model output is advisory.
- A valid form does not prove semantic truth.
- Raw text and source links are preserved so later enrichment can reinterpret
  weak or stale signals.
- Ambiguous memory can be stored as raw/proposed without being accepted.
- BlueRev internal assumptions should not be promoted automatically.
- JarvisOS owns validation, persistence, promotion, execution, audit, and
  policy.
- Do not add routes, frontend UI, memory runtime, retrieval runtime, Context
  Pack Broker runtime, provider integrations, automatic memory writes, or live
  model calls for this design.
