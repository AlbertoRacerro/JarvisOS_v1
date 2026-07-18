# 061b — TOKEN-FLOW-CONTINUATION-0

Status: blocked pending merged 061a. `docs/specs/STATUS.md` is authoritative.

Depends on: 061a

## Goal

Complete bounded model responses across multiple attempts while preserving one flow identity, exact 059b authority on every external call, protected restart-safe partial output, and honest partial termination when continuation cannot safely proceed.

This slice implements only the continuation, pause/resume, and assembled-output portions extracted from the 061 umbrella. It must reuse the 061a attempt ledger and flow/accounting model rather than creating another execution or accounting system.

## Scope

061b owns:

- exact normalized `length` detection as the only automatic direct-continuation trigger;
- one fresh `ai_jobs` attempt for every continuation;
- parent-attempt and continuation-index lineage within the same flow;
- server-owned continuation guard snapshotted at flow creation;
- protected accumulated-output segments with digest, sensitivity, policy binding, expiry, and restart-safe validation;
- fresh capability, context-capacity, route, policy, and guard evaluation for every local/synthetic continuation;
- a fresh complete 059b evaluation and reservation for every external continuation or fallback;
- `confirmation_required` pause and ticket-bound resume without reusing stale authorization;
- deterministic assembled final-output digest;
- record capture exactly once, after the final assembled output is complete;
- safe bounded flow status needed to inspect running, paused, partial, failed, and complete continuation flows.

## Continuation eligibility

Automatic direct continuation is allowed only when all conditions are true:

1. the latest ordered attempt invoked an adapter;
2. the normalized finish reason is exactly `length`;
3. the response contains a non-empty bounded segment;
4. the flow is still `running`;
5. the snapshotted continuation guard is not exhausted;
6. the protected accumulated-output state validates;
7. the next binding has sufficient trusted context and output capacity;
8. all route, sensitivity, provider, budget, and 059b checks pass for the next attempt.

`stop`, `content_filter`, `tool_call`, `error`, missing finish reason, malformed provider metadata, and unknown reasons must not trigger automatic continuation.

## Protected segments

Protected segment bodies are local runtime state, not attempt-ledger content.

Each stored segment must bind at least:

- flow ID and ordered segment index;
- originating attempt ID;
- canonical body digest and bounded byte/token counts;
- effective sensitivity level;
- policy/configuration binding digest;
- continuation-guard digest;
- creation and expiry timestamps.

Segment bodies must never appear in `ai_jobs`, ordinary events, public status payloads, grading analytics, or accounting digests. Missing, expired, altered, cross-workspace, or policy-mismatched segments fail closed and terminalize honestly as partial when prior output exists.

## Confirmation resume

When a fresh 059b evaluation returns `confirmation_required`:

- the flow transitions to `confirmation_required` only after a canonical non-dispatched attempt is persisted;
- the pending ticket, packet digest, decision, trigger set, provider/model binding, workspace, policy/config digest, and expiry remain authoritative;
- resume must consume the exact current ticket through the existing 059b path;
- restart must not require in-memory state;
- expired, consumed, mutated, or mismatched tickets cannot resume;
- resume creates a new ordered attempt and never mutates the pause attempt into an execution attempt.

## Output assembly and capture

- Segments are concatenated only after every referenced segment passes integrity and authority checks.
- The terminal flow stores a digest of the assembled output, while each attempt keeps only its own output digest.
- A failed or blocked continuation preserves already validated output and uses `partial_terminal`; it must not report `complete`.
- MemoryStore/record parsing runs once against the assembled complete output. Partial outputs do not silently create duplicate proposals.

## Required evidence

The implementation must prove offline that:

1. only exact `length` triggers continuation;
2. every continuation creates a new contiguous attempt in the same flow;
3. guard `0` produces one honest partial attempt with no hidden retry;
4. guard exhaustion terminates partial without exceeding the snapshot;
5. local continuation reruns capability and context-capacity checks before adapter invocation;
6. every external continuation receives a new 059b packet/decision/reservation;
7. confirmation pause survives process restart and resumes only through the exact valid ticket;
8. missing, expired, altered, or cross-workspace segments fail closed;
9. continuation errors preserve validated accumulated output as partial;
10. assembled output and accounting digests are deterministic;
11. record capture occurs exactly once after complete assembly;
12. public status contains only safe aggregate metadata and no segment or prompt bodies.

## Non-goals

- generic workflow engine;
- background workers or scheduled continuation;
- streaming;
- semantic overlap removal or model-written merge logic;
- task-kind output target tables;
- Hermes child-agent orchestration;
- provider additions, routing optimization, grading, or UI redesign;
- changing 059b authority or reservation mathematics.

## Start gate

061b must remain blocked until 061a is merged and its exact core flow/evidence contract is stable. Implementation should be a separate PR with small slices and focused tests before one final full gate.
