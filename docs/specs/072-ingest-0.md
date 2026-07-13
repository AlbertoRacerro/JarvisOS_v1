# 072 — INGEST-0: document ingestion

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 040, 059a, 063

## Problem

Documents (papers, standards, notes, partner material) have no controlled way
into JarvisOS. The public-literature corpus targeted by 064 and the 063
vault working layer both need a feeding pipeline, and unlabeled ingested
content must never silently become external-eligible.

## Maintainer direction

A bounded local pipeline: file registration under the data root using the
existing artifact pattern (content digest, provenance fields), local text
extraction limited to a small bounded set of formats first (pdf, plain text,
markdown — no cloud parsing service of any kind), and corpus tagging
(public-literature vs internal vs sensitive) where marking something
"public" is an explicit human act. The default tag is unknown, and unknown
content is treated fail-closed — never external-eligible. Deterministic
sensitivity floors (059a) run at ingest time and may only raise the effective
level, never lower it. Extracted text feeds the 063 vault/index and the 064
literature corpus; this kernel owns none of the embedding or retrieval logic
itself.

## Required future contract

A full spec must define:

1. registration API and dedup-by-digest semantics (re-ingesting the same
   bytes must not create a duplicate record);
2. extraction bounds: supported formats, size limits, time limits, and the
   failure state for anything outside those bounds (reject, not best-effort
   partial extraction presented as complete);
3. the corpus-tag vocabulary and precisely who/what may set the "public" tag
   (a human action, not a model output, not a default);
4. label-proposal records via MemoryStore for any tag/sensitivity assignment
   that is not purely deterministic;
5. re-ingest/versioning semantics when the same logical document is submitted
   again with different bytes;
6. storage bounds (how much extracted text/how many documents before the
   pipeline refuses further ingestion or requires cleanup);
7. deterministic fixtures for extraction and tagging; no network fetch of
   documents and no live parsing-service dependency in tests.

## Authority boundary

Ingestion proposes labels and corpus membership; it never grants external
eligibility on its own. External eligibility remains owned exclusively by the
059 labels/derivatives machinery — a document passing through this pipeline
is not thereby cleared for an outbound packet.

## Non-goals

No OCR claim in v0, no crawlers or web ingestion, no cloud parsing services,
no automatic public labeling, no embedding logic here (owned by 063/064).

## Promotion evidence

Before this row becomes `ready`:

1. pick the smallest extraction toolchain that covers pdf/text/markdown
   locally;
2. prove ingested-but-untagged content is withheld from any external preview
   (a test asserting an unknown-tag document cannot appear in an outbound
   packet);
3. prove digest-based dedup: re-ingesting identical bytes does not create a
   second record.
