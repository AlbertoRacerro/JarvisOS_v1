# 071 — CONNECTOR-CAL-0: calendar connector

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 059a, 067

## Problem

Daily-life scheduling lives in an external calendar. JarvisOS should be able to
read it (briefings, a "today" view) and, eventually, propose events — without
building a calendar of its own and without letting any orchestrator write to
the outside world ungated.

## Maintainer direction

A read-first MCP connector for exactly one calendar provider (a CalDAV
endpoint or a single Google-class API), exposed as a domain tool under 067.
Ingested entries become labeled content like any other ingested material: they
are never auto-labeled public, default to internal/S1 with the existing
deterministic floors applying, and are subject to the same egress rules as
everything else under 059. Event creation or modification is an outward action
and requires the egress confirmation-trigger path regardless of the
computed sensitivity level — a calendar write is never silent-autopilot
eligible by this kernel's design, independent of whatever level it would
otherwise resolve to. Credentials go through the existing secret-handling
pattern: runtime-only, never written into the repo, browser storage, or logs.

## Required future contract

A full spec must define:

1. a provider abstraction with exactly one concrete first target implemented;
2. polling cadence driven by 070 (SCHED-0), not a push/webhook subscription;
3. read scope bounds (which calendars/date range are ingested, and what is
   explicitly excluded);
4. sensitivity labeling of ingested entries at ingest time, reusing 059a
   labels/floors rather than a parallel labeling scheme;
5. the event-write proposal + confirm flow: how a proposed write is
   represented before confirmation, and what the confirmation record contains;
6. failure/offline behavior (provider unreachable, auth expired, malformed
   response) — read failures must degrade to "no fresher data", never to a
   silent stale-as-fresh read;
7. deterministic fixtures for both read and write paths; no live calendar
   account, network call, or OAuth flow may run in CI.

## Authority boundary

The connector proposes calendar knowledge into JarvisOS; it never silently
mutates external state. Every event write is per-event confirmed through the
egress confirmation-trigger path — there is no batch-approve and no
autopilot path for outward calendar writes in this kernel.

## Non-goals

No custom calendar UI, no email in this row, no push webhooks, no multi-account
sync engine, no OAuth token persistence beyond the existing secrets pattern.

## Promotion evidence

Before this row becomes `ready`:

1. choose the first concrete provider;
2. prove the read path works offline-safe against deterministic fixtures (no
   live calendar dependency in tests);
3. prove a write cannot occur without a corresponding confirmation-trigger
   record — a test asserting the write path is unreachable without one.
