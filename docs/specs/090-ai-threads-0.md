# Spec 090 — AI-THREADS-0

**Definition status:** complete definition; registry remains `planned` until a separate readiness decision.

**Depends on:** 040 MEMORYSTORE-0, 041 DECISION-CAPTURE-0, 042 CONTEXT-PACK-1, 059b IP-EGRESS-1B, 061a TOKEN-FLOW-CORE-0, 061b TOKEN-FLOW-CONTINUATION-0, 083 APP-SHELL-1.

**Implementation PR:** none until readiness promotes 090 to `ready`.

---

## 1. Purpose

090 adds one local, workspace-scoped episodic thread record for Jarvis interactions and binds each submitted interaction to the already-authoritative AI execution/proposal/token-flow evidence. It exists so later 091 JARVIS-SIDECAR-1 can render a real conversation history without inventing a second execution engine, second memory authority, or opaque chat transcript.

A thread is navigation and provenance state. It is **not** engineering truth, a provider ledger, a MemoryStore replacement, an agent memory system, or an authorization surface.

The minimum useful result is:

- create/list/read bounded local threads inside one workspace;
- append user/assistant interaction records only through the canonical AI-task execution boundary;
- preserve stable links from each interaction to canonical attempt/flow/proposal evidence when such evidence exists;
- keep external egress packet-scoped and forbid raw complete-thread egress.

## 2. Product authority

This definition consumes existing authority rather than duplicating it:

- 040 remains the only proposal/promotion boundary for engineering records;
- 041 remains the deterministic response-to-proposal capture boundary;
- 042 remains the deterministic bounded context-selection authority;
- 059b remains the external egress/sensitivity/budget/confirmation authority;
- 061a/061b remain token-flow, provider usage, continuation, assembled-output and completion authority;
- 083 remains application-shell/navigation state authority;
- 091 later owns the contextual Jarvis sidecar presentation and advisory-role UX.

090 therefore records *what interaction happened and which canonical evidence it produced*. It must not reinterpret that evidence.

## 3. Scope

090 may add only the minimum contracts and runtime needed to:

1. persist a thread identity scoped to exactly one workspace;
2. list threads deterministically with bounded metadata;
3. read one thread as a bounded ordered sequence of interaction records;
4. create a new thread locally without provider execution;
5. submit one user turn through the existing canonical AI-task path rather than a new provider adapter;
6. persist the user turn, terminal assistant result and canonical provenance references atomically enough to avoid misleading partial history;
7. expose proposal references created by existing 041 capture without promoting them;
8. expose canonical flow/attempt/provider/cost/latency references only by link/summary fields already owned elsewhere;
9. handle continuation/restart outcomes without pretending one provider call equals one interaction;
10. preserve safe failure states for rejected egress, confirmation-required execution, provider failure, parse/capture failure and interrupted continuation.

Readiness must inventory current runtime identifiers and choose the smallest storage/API seam that can preserve these properties.

## 4. Non-goals

090 does **not** authorize:

- a new model/provider gateway, route policy, fallback policy or provider credential path;
- a second token/cost/latency ledger;
- a second context builder, RAG store or semantic-memory system;
- autonomous agents, Hermes integration, persona orchestration, fake multi-agent presence or background execution;
- 091 sidecar visual redesign, role-profile UX or global visual identity;
- 062 grade controls or grade-derived routing;
- automatic proposal promotion/rejection;
- automatic BLUECAD candidate creation outside existing explicit boundaries;
- full-thread provider upload, transcript replay to providers, or hidden conversation-memory injection;
- browser-storage/localStorage transcript authority;
- arbitrary markdown/HTML execution;
- streaming-token persistence as thousands of records;
- editing historical user/assistant turns in place;
- deleting canonical provider/flow/proposal evidence when a thread is deleted or archived;
- infrastructure, dependency or state-framework expansion unless readiness proves it necessary.

## 5. Thread data contract

### 5.1 Thread identity

Every thread must have a stable server-owned ID, one workspace ID, creation time, last-activity time, and bounded local title/label metadata.

A thread cannot move between workspaces. Workspace mismatch must fail closed.

Thread ordering must be deterministic, recommended `last_activity_at DESC, id ASC` with exact readiness-frozen tie handling.

### 5.2 Interaction record

Each interaction record must distinguish at least:

- user input text;
- terminal assistant output text when available;
- lifecycle outcome/status;
- created/completed timestamps;
- canonical AI-task/flow/attempt identifiers that current runtime actually exposes;
- proposal IDs produced by existing 041 capture, if any;
- whether external execution was not attempted, local-only, externally dispatched, confirmation-required, rejected, failed or completed, using canonical state rather than inferred labels.

The interaction must not copy cost, latency, provider usage, fallback decisions or proposal bodies into a second authoritative store when stable references suffice. Small immutable display snapshots may be allowed only when readiness proves they are required for historical readability and labels them as snapshots.

### 5.3 Ordering and immutability

Interaction order must be server-deterministic. Historical completed turns are append-only except for narrowly defined lifecycle completion of the same pending interaction.

Client timestamps, array position, optimistic DOM order and provider message indexes are not authority.

## 6. Submission and atomicity contract

A user submit creates one interaction identity before or as canonical execution begins. The implementation must prevent duplicate submission from double-click/retry ambiguity using a readiness-frozen request/idempotency rule.

The system must never display a terminal assistant answer as durably recorded unless the thread record and its canonical provenance reference have reached a coherent state.

Required failure handling includes:

- user record stored but execution never starts;
- policy rejects external egress;
- confirmation is required;
- provider dispatch fails;
- continuation is interrupted and resumable under 061b;
- final answer exists but proposal capture fails;
- thread write fails after canonical execution completed;
- client disconnects during execution;
- stale client retries a submit.

Readiness must choose a minimum recovery rule. Prefer durable interaction state plus canonical flow reference over distributed rollback that could erase real execution evidence.

## 7. Canonical execution boundary

090 must call the same server-owned AI-task spine already governed by 059b and 061a/061b. It must not call provider adapters directly from frontend or a new chat endpoint that bypasses policy/budget/accounting.

One interaction may map to multiple provider attempts/continuations. UI/read models must therefore refer to canonical flow/attempt identity rather than assuming one message equals one HTTP/model call.

No cost or latency value may be recomputed from transcript length or frontend timers.

## 8. Context and egress boundary

### 8.1 Local history is not automatically external context

Persisting a thread locally does not authorize sending that thread externally.

Every external call must continue to receive only the exact bounded packet authorized by existing 042/059b logic. 090 may provide selected current-turn text and explicit thread references as inputs to that existing context-selection path only if readiness proves the current contract supports them safely.

### 8.2 Raw complete-thread egress forbidden

The implementation must not concatenate or serialize the complete thread and send it to an external provider by default, fallback, retry, continuation or convenience helper.

If future product work requires transcript-derived external context, it needs a separate bounded authority decision with sensitivity, truncation, provenance and egress semantics. 090 does not grant it.

### 8.3 Secrets and sensitive text

Thread reads/writes must preserve existing sensitivity and sanitization boundaries. Secrets, credentials and filesystem paths that existing APIs intentionally hide must not become visible merely because an assistant output or diagnostic references them.

## 9. Proposal and engineering authority

Assistant text is advisory text. It does not become an accepted engineering record because it appears in a thread.

Existing 041 capture may create MemoryStore proposals from an approved terminal AI-task response. 090 may expose links/counts/status summaries for those proposals, but:

- promotion/rejection remains explicit and owned by existing MemoryStore/054 behavior;
- thread deletion/archive cannot delete promoted engineering truth;
- proposal status must be re-read from canonical authority when current state matters;
- a missing proposal does not mean the assistant answer is accepted truth.

## 10. Frontend boundary

090 should provide only the minimum frontend surface required to prove thread persistence/provenance before 091.

Expected minimum is a bounded thread-history development/product seam reachable inside the existing shell or legacy continuity path, not the final Jarvis sidecar. Readiness may choose one of:

- a minimal non-primary thread inspection route/panel; or
- typed data/state helpers consumed by an existing safe placeholder surface.

It must not redesign global navigation or introduce the final 091 interaction chrome early.

The implementation must preserve App-owned workspace authority. No thread-local duplicate workspace store.

## 11. Async and stale-state contract

All workspace/thread reads must use generation + identity guards sufficient for:

- workspace A → B with late A response;
- A → B → A with late first-A response;
- thread X → Y with late X response;
- X → Y → X with late first-X response;
- submit on X followed by navigation to Y before completion;
- thread disappearance/archive while selected;
- retry after a failed/current interaction.

Stale responses must not repaint old thread text, proposal references, execution status or errors under a new workspace/thread.

## 12. Bounded rendering and hostile text

Thread text is untrusted inert text.

Readiness must freeze limits for:

- user input length;
- assistant output display length;
- thread page size / maximum initially loaded turns;
- title length;
- provenance reference count;
- diagnostic/error text.

No `dangerouslySetInnerHTML`, executable markdown, dynamic code, provider-supplied links or arbitrary file links are authorized. If markdown rendering already exists, readiness must prove its sanitizer and link policy before reuse; otherwise plain/pre-wrapped text is sufficient.

## 13. Accessibility and 200% zoom

Any 090-visible UI must inherit 070/083 and require:

- keyboard-operable thread selection and submit controls;
- visible labels for thread, status and provenance links;
- deterministic focus after thread creation/submission/error recovery;
- no color-only lifecycle distinctions;
- long IDs/text wrapping or local bounded scrolling;
- no document-level horizontal overflow at effective 200% zoom;
- preserved shell navigator/sidecar/dock behavior and legacy route reachability.

090 does not own final Jarvis sidecar keyboard choreography; 091 will.

## 14. Failure states

The read model must distinguish at least:

- no workspace;
- workspace with no threads;
- thread list failure;
- thread disappeared/not found;
- thread read failure;
- pending interaction;
- execution rejected by policy;
- confirmation required;
- local/no-external execution;
- provider/execution failure;
- continuation/resume state already represented by canonical flow;
- completed answer with zero proposals;
- completed answer with proposal references;
- proposal-capture failure if current runtime exposes it distinctly;
- stale response ignored.

Unknown canonical statuses must render as bounded raw status text or explicit unknown state, never be coerced to success.

## 15. Security/privacy/cost failure modes

Beta-blocking failures include:

- raw complete-thread external egress;
- provider call bypassing 059b/061 authority;
- secret/credential exposure in thread APIs or frontend state;
- duplicate submit causing unbounded duplicate paid execution;
- cost/latency/provider claims invented from frontend timing or transcript length;
- cross-workspace thread read/write;
- assistant text presented as accepted engineering truth;
- stale thread content shown under another workspace/thread;
- silent loss of completed canonical execution because thread persistence failed;
- persisted raw provider request packets when canonical audit/evidence already owns them.

## 16. Likely implementation boundary to verify at readiness

Readiness must derive the exact allow-list from current master. Expected bounded areas are:

```text
backend thread persistence/read-model module or existing repository module
backend API schemas/routes only for thread CRUD/submit if no suitable route exists
existing canonical AI-task execution service only through a narrow call seam
frontend typed thread API/state helpers
one minimum inspection surface required before 091
frontend local styles only if a visible surface is required
focused backend/frontend tests
scripts/check_ai_threads.py
docs/specs/STATUS.md during implementation lifecycle
```

By default exclude provider adapters, 059b/061 accounting logic, MemoryStore schema/authority, package manifests, global theme/token files, workflows and 091 sidecar components.

## 17. Readiness questions

Before promoting 090 to `ready`, readiness must answer from exact current master:

1. What exact canonical function/route starts an AI task under 059b + 061 authority?
2. Which stable flow/attempt/result identifiers can be referenced from a thread interaction?
3. How does 041 expose captured proposal IDs/results today?
4. What current continuation states from 061b must the thread read model preserve?
5. What storage/migration discipline is already used for additive local SQLite records?
6. Can one additive thread schema remain independently removable without touching canonical engineering truth?
7. What exact idempotency rule prevents duplicate paid submissions?
8. What happens if canonical execution succeeds but the thread completion write fails?
9. Which fields are authoritative references versus optional immutable display snapshots?
10. What current sensitivity/sanitization fields must be preserved and what raw data is forbidden from thread APIs?
11. What minimal visible UI is required to test 090 without implementing 091 early?
12. What exact request-generation/identity guards are required in that surface?
13. Which existing 040/041/042/059b/061/083 tests/checkers must remain green?
14. What rollback removes 090 without deleting canonical proposal/flow/evidence records?

If these questions cannot be answered without redefining provider, context, accounting or proposal authority, readiness must stop rather than widening 090 silently.

## 18. Acceptance criteria

090 is complete only when exact-head evidence proves all of the following:

1. Threads are persisted locally and scoped to exactly one workspace.
2. Thread list/read ordering is deterministic and bounded.
3. A submitted turn uses the existing canonical AI-task execution spine; no direct/new provider path exists.
4. Duplicate submission is bounded by a deterministic idempotency/concurrency rule.
5. Interaction records preserve real canonical flow/attempt provenance and do not duplicate provider/cost/latency authority.
6. Existing 041 proposal capture remains authoritative and thread UI/read models expose proposals only as references/advisory workflow evidence.
7. Raw complete-thread external egress is absent and a deterministic checker/test rejects any newly introduced bypass pattern within 090 scope.
8. Cross-workspace thread access fails closed.
9. Pending/rejected/confirmation-required/failed/completed outcomes are distinguishable without invented success.
10. Stale workspace/thread responses cannot repaint another context.
11. Untrusted text is inert and bounded.
12. Any visible 090 surface remains keyboard-operable, 200%-zoom contained and structurally compatible with 083.
13. Existing 040/041/042/059b/061/083 deterministic gates remain green.
14. No 062 grade surface, 091 final sidecar UX, Hermes behavior, global visual identity, provider credential or package expansion is introduced.
15. The slice can be rolled back independently while canonical AI-flow/proposal/evidence records remain valid.

## 19. Exact-head delivery and rollback

Every implementation-head mutation invalidates earlier execution/browser/review evidence. Merge requires one unchanged exact remote head with the readiness-frozen checker/test/build/browser matrix green and no material P0/P1/beta-blocking P2.

Rollback must remove 090-owned thread routes/storage/UI without deleting or mutating existing canonical AI flow, provider usage, MemoryStore proposal, engineering record, BLUECAD or evidence authority. Historical dangling provenance references must be handled by explicit nullable/not-available presentation rather than guessed reconstruction.
