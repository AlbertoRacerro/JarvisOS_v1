# 061 — TOKEN-FLOW-0: complete paid responses within bounded economics

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 021, 059b

## Problem

Per-response hard caps can cut a paid answer mid-generation while the current
runtime also fails to enforce projected cost/token limits before a call. JarvisOS
needs bounded completion semantics without pretending that an arbitrary model
response length can be known exactly.

## Maintainer direction

- Size `max_tokens` before each call from a deterministic task-kind policy.
- Do not use product-level hard caps whose purpose is to truncate an otherwise
  useful paid answer mid-generation.
- When the provider stop reason is length, allow bounded automatic continuation;
  default maximum: two continuations.
- The monthly budget remains the hard economic stop.
- The daily soft threshold is a 059b confirmation trigger, not a second silent
  hard cap.
- Surface today/month token and spend counters by provider through existing
  `/ai/status` data where possible; do not build a second usage store.

## Required future contract

A full spec must define:

1. deterministic task-kind sizing inputs and safe defaults;
2. server-owned clamping to model/provider capability and the remaining economic
   envelope;
3. projected token/cost reservation immediately before each concrete call;
4. continuation prompt/digest linkage and stop-reason validation;
5. maximum continuation count and loop termination;
6. usage reconciliation between estimates, provider-reported usage, failures,
   and partial responses;
7. fallback behavior without double-counting or bypassing budget;
8. status/API fields consumed by specs 029 and 058;
9. offline tests proving no unbounded continuation and no cap overshoot.

## Failure modes to resolve

- one call can currently exceed the remaining monthly/provider cap;
- caller `max_tokens` can exceed the registry model cap;
- failed/no-call adapter responses can be counted as full output usage;
- fallback and continuation could accidentally multiply the economic envelope;
- a continuation could lose packet, sensitivity, or provider provenance.

## Non-goals

No streaming/SSE, worker process, DAG orchestrator, provider addition, frontend
implementation, live-provider CI, or unlimited response loop.

## Promotion evidence

Before this row may become `ready`, the full spec must bind to current 059b
packet/ticket semantics, identify the exact `ai_jobs`/usage fields to extend, and
include deterministic projected-budget and continuation tests.
