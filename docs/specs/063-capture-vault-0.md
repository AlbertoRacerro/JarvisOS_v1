# 063 — CAPTURE-VAULT-0: local semantic working memory

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 040, 042

## Problem

Canonical SQLite records provide authority and deterministic retrieval, but they
are too structured for zero-ceremony notes and fuzzy recall during active work.
JarvisOS needs a local working layer without turning vectors into a second source
of truth.

## Maintainer direction

Create a stand-alone local working-memory layer with two retrieval lanes in
parallel:

1. a local vector index over a markdown second-brain vault and bounded fragments
   of past conversations;
2. existing canonical SQLite retrieval through FTS and kind/status/id filters,
   reusing context-pack selection.

Embeddings use a configured local Ollama-compatible model, but every embedding
model call must traverse the shared `run_ai_task` execution spine on an explicit
local route and write an `ai_jobs` row. A direct embedding adapter call is
forbidden. If the current provider-neutral spine cannot represent embedding
requests and usage safely, the full spec must extend that spine before any index
runtime is implemented.

The index never leaves the machine. Canonical records are not embedded.

Merged results carry authority tags:

`canonical > note > literature`

On conflict, canonical data wins and the conflict is surfaced rather than
silently blended.

Sensitivity is not enforced while indexing. It is enforced when retrieved
content enters a 059 egress packet.

## Required future contract

A full spec must define:

1. vault root under the JarvisOS data root, never the repository;
2. supported markdown/front-matter shape and stable note/fragment ids;
3. a provider-neutral embedding task through `run_ai_task`, including explicit
   local route, model/version metadata, input/output digests, usage accounting,
   safe `ai_jobs` metadata, chunking, batching, retry, and re-index rules;
4. zero direct Ollama/provider adapter calls from the indexing or retrieval layer;
5. bounded hybrid query, score normalization, deduplication, and authority merge;
6. conflict representation and exact provenance back to note/conversation ids;
7. deletion, rename, stale-index, corruption, and rebuild semantics;
8. no-network defaults and behavior when Ollama/index is unavailable;
9. context-pack integration without bypassing canonical filters or 059;
10. bounded storage, observability, and deterministic test fixtures.

## Authority boundary

The vector index is an expendable cache/working layer. It may propose recall but
cannot promote records, choose providers, authorize egress, or override SQLite.
Explicit mid-conversation capture continues through spec 041.

Embedding success, vector similarity, or schema validity is not semantic or
policy authority. JarvisOS retains validation, routing, budget, persistence,
sensitivity, and audit ownership.

## Non-goals

No vectors over canonical records, cloud embedding service, direct model-adapter
call, automatic canonical promotion, conversation runtime, boundary consolidation
job, background worker, SSE, generic agent memory framework, or second database
authority.

## Promotion evidence

Before this row becomes `ready`:

1. identify the smallest local index technology that can be rebuilt from
   vault/conversation sources;
2. prove that deleting the index loses no canonical state;
3. prove every embedding call uses `run_ai_task` and creates safe `ai_jobs`
   evidence, with a deterministic test that fails if the indexing layer calls a
   provider/Ollama adapter directly;
4. define the required provider-neutral embedding contract if the current AI spine
   does not yet support it.
