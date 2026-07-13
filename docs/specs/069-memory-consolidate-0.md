# 069 — MEMORY-CONSOLIDATE-0: first Hermes dogfood through proposal-only memory

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 040, 042, 061, 062, 066, 067, 068

## Problem

Hermes needs a real bounded job that exercises conversation, delegation, model
routing, retrieval, and MCP proposals without granting authority over canonical
engineering truth.

Internal Hermes memory and skills are episodic and disposable. Letting them
silently overwrite, merge, delete, or promote canonical records would create a
second memory system and make provenance unverifiable.

## Maintainer direction

`MEMORY-CONSOLIDATE-0` is the first Hermes dogfood job.

It reads a bounded, workspace-scoped set of accepted JarvisOS records and evidence,
optionally considers explicitly supplied episodic Hermes notes, and proposes
consolidated records through MemoryStore.

It never promotes, overwrites, deletes, relabels, or silently deduplicates canonical
records.

## Required future contract

### 1. Bounded input packet

The job input must bind:

- workspace;
- explicit consolidation purpose and record kinds;
- accepted canonical source IDs and digests;
- relevant evidence IDs and digests;
- optional episodic-note digest and source label;
- sensitivity/provenance capsule IDs;
- maximum sources, characters/tokens, proposals, model calls, tool calls,
  iterations, wall time, and cost;
- policy, prompt, persona, Hermes, and schema versions.

Retrieval snippets alone cannot authorize a consolidation claim. Full canonical
sources must be loaded through bounded JarvisOS services before proposal creation.

### 2. Authority order

The job must preserve:

1. accepted canonical JarvisOS records and evidence;
2. reviewed note/source material;
3. episodic Hermes notes.

Lower-authority material may suggest a question or proposal but cannot supersede a
higher-authority source.

Conflicts are surfaced explicitly as unresolved proposals or review items.

### 3. Output

The only durable engineering output is one or more MemoryStore proposals containing:

- normalized kind and content;
- source record/evidence references and digests;
- transformations performed;
- unresolved contradictions;
- uncertainty and confidence;
- model/job/tool provenance;
- duplicate/overlap candidates;
- sensitivity label proposal without authority to lower the source floor.

The job may also emit a disposable operator summary and metrics. Neither is
canonical truth.

### 4. Duplicate and conflict handling

- Use deterministic candidate retrieval before model synthesis.
- Never merge solely because text is similar.
- Preserve distinct records when scope, units, conditions, time basis, source, or
  authority differs.
- Do not delete or mutate an accepted record.
- A model may recommend `duplicate`, `supersedes`, `refines`, or `conflicts_with`,
  but JarvisOS validation and human promotion decide the durable relation.
- Unit, identifier, source-digest, and workspace mismatches fail closed.

### 5. Routing and egress

- The first dogfood route is local/offline by default.
- External routing is eligible only through spec 066 after 059b and only for an
  exact current packet whose effective content is externally eligible.
- Hermes cannot select a provider outside passthrough-offered aliases.
- Every model attempt writes correlated `ai_jobs` evidence.
- 061 bounds tokens/cost and continuation.
- 062 grades usefulness; grading does not promote the result.

### 6. Evaluation

The full spec must define a deterministic fixture set and operator review rubric
covering:

- source coverage;
- unsupported-claim rate;
- provenance completeness;
- contradiction preservation;
- unit/condition fidelity;
- duplicate precision and recall;
- proposal usefulness;
- token/cost per accepted useful proposal;
- abstention quality;
- regressions across Hermes/model/prompt versions.

A syntactically valid proposal or passing model self-review is not semantic proof.

## Required tests

- no source IDs or empty scope;
- cross-workspace source;
- stale source digest;
- source status not accepted;
- conflicting records;
- same text with different units/conditions;
- episodic note contradicting canonical evidence;
- forged/missing provenance capsule;
- proposal count and token/tool/model-call caps;
- timeout/cancellation and retry;
- local-only routing;
- external denial with zero provider attempts;
- no accepted-record mutation, deletion, sensitivity downgrade, or promotion;
- deterministic source/proposal/audit linkage;
- grading and cost metrics bound to the exact run.

## Hard lines

- Hermes memory and skills remain disposable.
- Canonical engineering truth enters SQLite only through existing MemoryStore
  proposal and promotion paths.
- No automatic promotion or overwrite.
- No model-owned duplicate merge, sensitivity downgrade, route, budget, or
  authority decision.
- No unbounded whole-database consolidation.

## Non-goals

No general memory rewrite, vector-store authority, autonomous cleanup, accepted
record deletion, background cron, unrestricted external model use, schema migration
framework, or replacement of proposal-review UI.

## Promotion evidence

Before this row may become `ready`, the full spec must:

1. freeze the input/output schemas and all bounds;
2. identify exact Context Pack, Evidence, MemoryStore, passthrough, and MCP
   service calls;
3. provide deterministic conflict/duplicate fixtures;
4. define GRADE-0 acceptance and cost-per-useful-proposal metrics;
5. prove proposal-only behavior and zero canonical mutation;
6. bind the run to pinned Hermes/config/prompt/model identities.
