# WP6 — personal-layer planning kernels

## Scope

Registry rows and planning kernels only. No runtime, schema, UI, provider,
worker, MCP server, or connector implementation.

## Maintainer decision source

2026-07-12 direction: the personal layer (scheduling, calendar, documents,
eventually measurement) is built as connectors and configuration over the
existing spine, not as new JarvisOS subsystems: "if a feature needs no
authority, audit, or canonical records, it is Hermes configuration or an MCP
connector, not JarvisOS code." Everything that does need authority, audit, or
a canonical record stays JarvisOS-owned and goes through `run_ai_task`/
`ai_jobs` and the existing gates like any other AI call.

## Added kernels

- 070 `SCHED-0` — deterministic SQLite-backed schedule owned by the policy
  kernel, with a single idempotent OS-triggered tick; launches pinned Hermes
  jobs and internal deterministic checks with per-job budget and full ledger
  evidence; no resident worker.
- 071 `CONNECTOR-CAL-0` — read-first MCP calendar connector; ingested entries
  are labeled content under 059a, never auto-public; event writes are outward
  actions that always require the egress confirmation-trigger path.
- 072 `INGEST-0` — bounded local document ingestion (registration, digest
  dedup, local text extraction) feeding the 063 vault and 064 literature
  corpus; corpus "public" tagging is an explicit human act, default is
  unknown/fail-closed.
- 073 `MEASUREMENT-0` — trigger-gated as-measured record family and
  as-designed-vs-as-measured diff, reusing 050/051 flowsheet stale
  propagation; measurements are evidence, never automatic truth, and never
  actuate hardware. Drafting of the full spec does not start until a physical
  prototype produces real measurements.

All four rows remain `planned`. They are not implementation contracts and
must still pass the normal backlog row -> kernel -> full spec -> ready ->
implementation ladder before any coding agent acts on them.

## Non-goals across this work package

- No multi-user support anywhere in the personal layer.
- No cloud sync of calendar, documents, or measurements.
- No custom email or calendar client; 071 reads and proposes, it does not
  reimplement a calendar.
- No note-taking app beyond the existing 063 vault.
- Phone/messaging reach stays the existing Hermes messaging bridge under
  existing gates — this work package does not add a second messaging surface.

## Registry sequencing note

Numbering 070-073 assumes open PR #99 lands rows 066-069 (`HERMES-PASSTHROUGH-0`,
`JARVIS-MCP-0`, `HERMES-CONFIG-0`, `MEMORY-CONSOLIDATE-0`) first. This PR does
not add or modify 066-069. If #99's numbering shifts before merge, this PR must
be rebased and its dependency references (066, 067, 068, 069) corrected before
merge, not silently left pointing at whatever numbers happened to land.

## Gate

These four rows are planning rows only. Each must independently clear the
kernel -> full-spec -> ready promotion evidence listed in its own file before
any implementation branch may start; none of them authorizes runtime work by
virtue of existing in the registry.
