# JarvisOS Coordination Bus V2

Status: **retired historical coordination mechanism**

The ordinary Coordination Bus V2 production model is retired by the pipeline V3.2 migration. This file remains only as a tombstone for canonical references and historical issue/comment provenance.

## Current rule

- Fresh canonical repository files, exact Git/PR state, deterministic checks, and exact-head review evidence are the continuation source.
- If another enabled JarvisOS Roadmap Builder A/B/C/D owns a non-stale `[BUSY <UTC>]` lease, the non-owner exits promptly. It does not enter helper mode, perform duplicate analysis, publish Bus workpacks/messages, or mutate shared authority.
- No new ordinary V2 `REQUEST`, `RESULT`, `FINDING`, `INFO`, `WORKPACK`, `CANDIDATE_PATCH`, or `CANCEL` messages are produced for scheduler coordination.
- Existing Bus issue comments and candidate workpacks are historical/advisory provenance only. They never establish queue, status, readiness, implementation, review, merge, persistence, or mutation authority and must not be consumed as current coordination state.
- Active or recent authorized work is recovered from fresh PR/branch state and revalidated against current repository authority rather than reconstructed from Bus packets.

## Historical provenance

Coordination Bus V2 was authorized on 2026-08-30 as a non-authoritative append-only GitHub issue transport so BUSY-blocked builders could prepare proposal-only helper workpacks while another builder held the writer mutex. Its envelope used the `<!-- JARVIS_COORD_V2 -->` marker and supported request/result/finding/workpack/candidate-patch messages with explicit `authority: NONE` and bounded freshness.

That helper-mode transport reduced duplicated rediscovery during the earlier multi-scheduler operating regime, but V3.2 deliberately removes ordinary Bus production and its mutex exception in favor of one active writer plus fresh GitHub/PR continuation state. Historical Bus messages remain available only for provenance; their prior schemas, TTLs, workpack formats, helper algorithm, request-stealing rules, and consumption rules are no longer an active operating contract.

Repository authority continues to live in `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, accepted specs/readiness, applicable delivery profiles, exact Git state, and exact-head deterministic/review evidence. This tombstone cannot override any of them.
