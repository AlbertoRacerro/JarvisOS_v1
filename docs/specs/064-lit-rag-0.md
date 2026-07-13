# 064 — LIT-RAG-0: local public-literature retrieval lane

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 042, 063

## Problem

Public papers, standards notes, benchmark material, and engineering references
need semantic retrieval, but literature must not be confused with canonical
project facts or silently promoted into engineering authority.

## Maintainer direction

Add a corpus-tagged public-literature lane to the local vector working layer from
063. Retrieval runs locally and merges with canonical and vault results using the
authority order:

`canonical > note > literature`

Literature results remain claims/evidence candidates with source provenance.
They cannot override an accepted parameter, decision, or evidence record.
Conflicts with canonical records are surfaced.

Sensitivity remains an egress-time concern under 059. Public corpus tagging does
not authorize an outbound packet or a provider call.

## Required future contract

A full spec must define:

1. admitted corpus/source types and stable document/chunk ids;
2. provenance fields: title, authors, publication/source, date, locator, license
   or access status, corpus tag, ingest timestamp, and content digest;
3. local parsing/chunking/embedding versioning and rebuild behavior;
4. duplicate/version handling and retraction/correction markers;
5. bounded semantic query and merge with 063 + canonical context packs;
6. authority/conflict labels exposed to callers;
7. quotation/citation limits and source-locator preservation;
8. failure behavior for malformed documents, missing text, or unavailable local
   embedding runtime;
9. offline deterministic fixtures and no live-network CI.

## Authority boundary

Literature retrieval is advisory evidence. Any durable engineering assumption,
parameter, decision, or evidence record is still created as a proposal through
MemoryStore and requires explicit user or deterministic-policy promotion.

## Non-goals

No web crawler, cloud vector database, cloud embedding service, autonomous paper
acquisition, copyright bypass, automatic canonical promotion, provider routing,
conversation runtime, or second source of truth.

## Planning gap: boundary consolidation

The 2026-07-12 maintainer direction also requires a separate
`MEMORY-CONSOLIDATE-0` boundary job: idempotent per conversation, provenance to
transcript/note ids, supersede rather than duplicate, contradiction surfacing,
proposal writes through MemoryStore, sampled policy promotion for routine cards,
and working-set compaction.

WP2 explicitly requested kernels only for TOKEN-FLOW-0, GRADE-0,
CAPTURE-VAULT-0, and LIT-RAG-0. This kernel therefore does **not** silently absorb
consolidation. A later maintainer decision must assign its registry id and exact
dependency on Conversation v0 (030).

## Promotion evidence

Before this row becomes `ready`, select the first bounded corpus and prove that
retrieval retains source locators, exposes authority/conflicts, and can rebuild
its index without changing canonical project state.
