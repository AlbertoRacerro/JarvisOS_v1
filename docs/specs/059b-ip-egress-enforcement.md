# 059b — IP-EGRESS-1B: policy autopilot and execution enforcement

Status: ready after full-spec reconciliation; `docs/specs/STATUS.md` is authoritative.

Depends on: 059a

Parent definition: `docs/specs/059-ip-egress-1.md`

Durable decisions: ADR-059 and ADR-060

## Goal

Implement the normal external-provider path as a server-owned policy autopilot:
minimum context, automatic local sanitization, exact packet construction,
deterministic egress/economic decisions, silent effective-S0/S1 allow, configured
confirmation triggers, and execution through the existing shared spine.

This is not permission for a model, frontend, request payload, Hermes, or provider
adapter to authorize a call. JarvisOS owns sensitivity, packet construction,
concrete provider/model binding, projected budget, trigger evaluation, ticket state,
and the final execution decision.

Every model-backed sanitizer, including local Ollama, is an AI call. It must use
`run_ai_task` on an explicit local route and write its own `ai_jobs` row. Only a
strictly deterministic non-model transformation may run without an AI call.
Sanitizer output remains untrusted until deterministic policy accepts it.

Merged 059a remains authoritative: only current effective S0/S1 material may enter
an externally eligible packet. Confirmation cannot override this rule.

## Current master facts

The implementation must start from these observed facts rather than from the desired
architecture:

1. `AIGateway.run_task` currently forwards caller prompt and manual context to
   `run_ai_task`.
2. `run_ai_task` canonicalizes and globally size-bounds context, resolves a concrete
   binding and fallback chain, evaluates current provider/budget readiness, then
   calls `adapter.complete(...)`. It has no exact-packet egress hook.
3. The hook must therefore live in the shared spine inside the per-binding loop,
   after the concrete binding is known and immediately before `AIRequest`
   construction and adapter invocation.
4. `confirm_escalation` currently trusts client-owned outbound text, route, and token
   metadata. That path must be replaced, not wrapped with another boolean.
5. The current budget gate checks already-recorded usage and provider caps. It does
   not reserve the pending call, cannot prevent concurrent last-call overshoot, and
   has no daily soft-threshold trigger.
6. Merged 059a provides labels, canonical derivatives, deterministic floors,
   coherent read-snapshot selection, stale/revoked handling, and S0/S1-only external
   previews.
7. `preview_manual_context` accepts only exact server-loaded approved derivative
   blocks. Arbitrary manual blocks are `unknown` and withheld.
8. 059a canonical derivative source refs are limited to decisions, assumptions,
   parameters, requirements, and evidence. Raw user prompts require a separate
   059b-owned prompt envelope and derivative contract.
9. Current schema migration is `0009_sensitivity_context_foundation`. No packet,
   decision, ticket, attempt, prompt-derivative, workspace-policy, reservation, or
   sampled-audit persistence exists.
10. Existing route cost estimation is conservative and route-based. Unknown pricing
    must fail closed rather than silently estimate zero.

## Runtime scope

059b owns only:

- server-owned prompt envelopes and bounded prompt derivatives;
- automatic sanitizer orchestration over prompt material and merged 059a sources;
- model-backed sanitizer calls through `run_ai_task`/`ai_jobs`, or explicitly
  deterministic non-model transformations;
- deterministic pre/post scans and exact provenance/version binding;
- sampled human-audit queue, defaulting to deterministic 5% weekly;
- derivative revocation and sanitizer-failure evidence after sampled rejection;
- configured count/size caps for blocks derived from S2/S3/unknown sources;
- canonical persisted `EgressPacket` and immutable `EgressDecision`;
- silent server-owned allow for eligible packets without triggers;
- configured trigger evaluation (`t1`–`t5`);
- expiring digest-bound single-use tickets for confirmable triggers;
- projected daily/monthly/provider economic reservation immediately before calls;
- replacement of client-trusted escalation confirmation;
- independent enforcement for every concrete fallback binding;
- safe attempt/egress/sanitizer/ticket metadata;
- mutation-resistant offline integration tests.

It must not create a second AI execution spine, provider gateway, MemoryStore,
sensitivity authority, provider adapter, external-tool runtime, conversation system,
vector store, worker process, streaming transport, DAG orchestrator, or frontend
redesign.

## Authority and material classes

The exact outbound packet is composed from three separately governed classes:

1. **Prompt material** — the caller's task instruction, represented by a
   server-owned `PromptEnvelope` containing exact content digest, deterministic
   floor, policy classification source, transformation provenance, and final level.
2. **Canonical project context** — records selected through merged 059a labels and
   canonical derivatives in one coherent SQLite read snapshot.
3. **Manual context** — accepted for external use only when every block exactly
   matches an approved, current, S0/S1 059a derivative through
   `preview_manual_context`; arbitrary inline blocks remain withheld.

Caller fields may identify desired records or task intent. They cannot assert that a
prompt/block is public, select a derivative body, lower sensitivity, authorize a
provider, or bypass a cap.

## Prompt envelope and prompt derivatives

059b adds a bounded prompt-material contract because raw prompts are not canonical
059a source records.

A `PromptEnvelope` binds:

- exact raw prompt digest;
- workspace ID when present;
- task kind;
- deterministic floor and final level;
- classification source and policy version;
- prompt-derivative ID/digest when transformed;
- sanitizer kind/version/config digest and sanitizer `ai_jobs` ID when model-backed.

Rules:

- In `FAST_DEV`, an ordinary prompt with no attached project/manual context and no
  hard marker may retain the parent-definition S1 default.
- Any prompt with a deterministic S2/S3/S4 floor, failed classification, malformed
  state, or unknown authority is not sent raw.
- S2/S3/unknown prompt material may use a deterministic or model-backed local
  sanitizer and must end as current effective S0/S1.
- Raw or surviving S4/secret-bearing prompt material is denied with no override.
- A prompt derivative is a separate immutable row bound to the raw prompt digest;
  it never changes or downgrades the original material.
- Prompt derivatives are reusable only while current, unrevoked, policy-compatible,
  and digest-bound. Sample rejection revokes them.
- Prompt text and prompt-derivative bodies may exist in dedicated local packet or
  derivative tables, but never in `ai_jobs`, events, confirmation responses, or
  normal logs.

## Canonical-source automatic sanitizer

For S2, S3, or `unknown` canonical source material:

1. load current source and 059a authority in one coherent read snapshot;
2. minimize selected context;
3. run a deterministic transformation or a model-backed sanitizer through
   `run_ai_task` on an explicit local route;
4. run deterministic secret/IP scans before and after rewriting;
5. recompute content digest and effective level;
6. persist exact source refs/digests, transformations, sanitizer kind/version/config
   digest, optional sanitizer `ai_jobs` ID, approval source, and policy version;
7. auto-approve only final S0/S1 material under `policy-sanitizer-vN`;
8. fail closed on stale source, malformed output, scan failure, surviving secret,
   missing provenance, policy mismatch, or final level above S1.

The implementation may add nullable structured sanitizer-provenance columns and one
policy-owned approval service entry point around the existing 059a derivative table.
This is a bounded additive 059b extension: existing manual create/approve/revoke,
label, staleness, source-digest, and S4-source semantics must remain unchanged and
all writes must still pass through the sensitivity service rather than direct SQL in
callers.

Raw S2/S3/unknown never enters an external packet. Raw S4 and any material that
remains S4 or secret-bearing are denied. A derivative originating from an S4-labelled
source is not denied solely because of that source label; merged 059a rules still
require current provenance-bound effective S0/S1 content with no surviving secret.

## Sampled audit

- Default selection is deterministic 5% of auto-approved canonical or prompt
  derivatives per ISO calendar week.
- Selection binds derivative ID/digest, cohort, sampling-policy version, and reason.
- Audit items are immutable except for bounded review disposition fields.
- Rejection atomically revokes the derivative, invalidates unconsumed packets and
  tickets that depend on it, records sanitizer failure, and blocks reuse.
- Policy may increase sampling or require 100% review by workspace, provider family,
  task kind, or recent failure window.
- Reducing the default below 5% is outside implementation authority.

No background worker is introduced. Queue creation occurs synchronously when the
derivative is approved; review remains an explicit operator action.

## Context minimization

- Never include an entire workspace, vault, conversation archive, or corpus.
- Every outbound block carries server-owned source/derivative identity and digest.
- A versioned policy document supplies fail-closed maximum count and serialized-size
  limits for blocks derived from S2/S3/unknown sources.
- Sensitivity withholding and policy caps happen before prompt serialization.
- Token-budget truncation occurs afterward.
- Included, withheld, sanitizer-failed, policy-capped, and token-budget-dropped
  manifests remain distinct and auditable.
- Packet accounting follows derivative `source_refs`; it must not assume one raw
  record per outbound block.
- Explicit IDs, route aliases, task requests, Hermes tool arguments, and model output
  cannot bypass these limits.

## Versioned policy configuration

Trigger, cap, timeout, sampling, and confirmation defaults are loaded from the
strictly validated repository configuration document
`configs/ai_egress_policy.json`, with a canonical digest and explicit schema version.
They are not scattered constants.

The document contains at least:

- policy and trigger versions;
- prompt and context count/size caps;
- 5% weekly sample rate;
- confirmation-ticket TTL;
- daily spend soft threshold;
- reservation expiry;
- confirmable trigger set;
- supported operation set.

Missing, malformed, unsupported, or digest-mismatched configuration fails closed.
A separate `workspace_egress_policy` row may set only bounded overrides such as
`ask_me`; it cannot loosen global hard limits or sensitivity rules.

## Persistence and additive migration

The implementation uses additive migration `0010` and dedicated tables with foreign
keys/indexes. Exact names may be adjusted only if the same contracts remain clear.

Required persistence:

- `egress_prompt_derivatives` — raw prompt digest, derivative content/digest, final
  level, transformations, sanitizer provenance, status and timestamps;
- `egress_packets` — exact packet JSON/body in dedicated local storage, packet
  digest, prompt/context manifests, concrete binding, token limit, final level and
  policy/config digests;
- `egress_decisions` — immutable allow/deny/pause result, reason, packet/binding,
  trigger set, projected token/cost reservation and policy versions;
- `egress_confirmation_tickets` — packet/decision binding, safe target metadata,
  expiry, state and atomic consumption timestamps;
- `egress_attempts` — immutable link from decision/packet to the corresponding
  `ai_jobs` attempt, concrete binding, fallback index, network-attempt flag and
  estimate/actual reconciliation state;
- `sanitizer_audit_items` — deterministic sample cohort and review/revocation
  evidence;
- `workspace_egress_policy` — bounded workspace flags such as `ask_me`.

`egress_decisions` and `egress_attempts` are safe metadata ledgers, not replacements
for `ai_jobs`. Provider attempts still write exactly one `ai_jobs` row each.

Packet and derivative bodies are never duplicated into event payloads or AI ledger
metadata. Tables containing exact bodies are local-only and are not exposed by list
or status APIs.

## Canonical packet

For every concrete network binding, JarvisOS constructs one `EgressPacket` binding:

- exact approved prompt or prompt derivative;
- exact included context blocks;
- included, withheld, sanitizer-failed, policy-capped, and budget-dropped manifests;
- source/derivative IDs and current digests;
- explicit route class and concrete provider/model;
- task kind and server-owned maximum output tokens;
- prompt, maximum-context, and final effective levels;
- sanitizer, trigger, policy, and config versions/digests;
- fallback attempt index and prior retryable-error code where applicable.

Any content, source state, route, binding, token limit, trigger state, policy version,
or config change creates a different digest. A decision or ticket for one digest
cannot authorize another.

## Immutable decision and reason taxonomy

The policy service creates one immutable decision per concrete attempt:

- result: `allow`, `deny`, or `pause`;
- stable deterministic reason code;
- operation: only `external_provider_call` in this spec;
- route/provider/model and fallback index;
- packet digest and final levels;
- source/manifests counts;
- trigger IDs and confirmation requirement;
- projected input/output tokens and cost upper bound;
- active reservation amount and expiry;
- policy/config/sanitizer versions;
- ticket ID when applicable.

Reason codes are enums/constants covered by tests. Human-readable prose is not used
for program flow.

## Shared-spine enforcement

Inside `run_ai_task`, for each `ProviderBinding` where `requires_network` is true:

1. resolve the exact adapter and server-owned output-token ceiling;
2. build/reload prompt and context authority;
3. construct the packet for that concrete provider/model and fallback index;
4. open one policy transaction that revalidates source/derivative state, credentials,
   current usage, active reservations, policy/config digests and triggers;
5. write the packet and immutable decision;
6. if denied/paused, write a pre-provider `ai_jobs` row and make zero adapter calls;
7. if confirmation is required, return safe ticket metadata and make zero adapter
   calls;
8. for silent allow, reserve projected cost and continue;
9. for confirmed allow-once, atomically consume the ticket and reserve projected cost
   immediately before adapter invocation;
10. construct `AIRequest` only from the persisted/reloaded packet, never from mutable
    caller fields;
11. invoke the adapter once and write `ai_jobs` plus `egress_attempts` linkage;
12. reconcile reservation versus reported usage/actual estimate.

Local routes, including sanitizer routes, do not require external-egress permission,
but still traverse `run_ai_task` and `ai_jobs`.

Removing or bypassing the external-egress hook must make an integration test fail.
No adapter or alternate endpoint may perform a network call outside this spine.

## Projected economic reservation

059b closes the pre-call overshoot gap without replacing spec 021 or pre-implementing
061 optimization.

- Resolve conservative pricing for the exact concrete provider/model from the
  existing provider registry; route-level estimators remain advisory only.
- Include exact serialized packet input plus the server-owned output-token ceiling.
- Unknown price or inability to compute a conservative upper bound fails closed.
- In the same transaction as the decision, compare actual `ai_jobs` usage plus
  unexpired active reservations against global monthly, provider monthly, provider
  token, and daily soft limits.
- Monthly/global/provider hard limits are non-confirmable denials.
- Crossing the daily soft threshold triggers `t2` for an otherwise eligible packet.
- A reservation is bound to decision, packet, provider/model and expiry.
- Provider failure still consumes a confirmation ticket, but the reservation is
  reconciled to reported/estimated actual attempt cost rather than left active.
- Failed-before-network attempts record zero actual provider consumption and release
  or expire the reservation deterministically.
- Fallbacks repeat the full calculation independently.

059b owns only safe upper-bound clamping and reservation. Task-kind optimization,
continuations, and empirical token sizing remain 061.

## Trigger table

The trigger set is configuration data.

| ID | Trigger | Behavior |
| --- | --- | --- |
| `t1` | no prior recorded network attempt for the provider/model under the current trigger-policy version | exact-packet confirmation |
| `t2` | projected call crosses the configured daily soft-spend threshold | exact-packet confirmation; hard limits remain final |
| `t3` | sanitizer failure or final deterministic level above S1 | pause and create review/resanitization work; no external ticket |
| `t4` | unsupported/unknown egress operation | deny; confirmation cannot invent support |
| `t5` | workspace `ask_me` flag | exact-packet confirmation for an otherwise eligible packet |

`t1` is satisfied after a recorded network attempt, regardless of provider success,
so a consumed ticket followed by provider failure does not create an endless first-use
loop. Policy-version changes may intentionally re-arm it.

Malformed or missing trigger configuration fails closed. Surviving secret content,
final level above S1, hard-budget exhaustion, missing credentials, stale provenance,
and unsupported mechanics are non-confirmable denials or pauses.

## Ticket lifecycle and API

Silent effective-S0/S1 calls create no ticket.

An otherwise eligible packet triggering `t1`, `t2`, or `t5` receives a server-created
single-use ticket binding packet/decision digest, fixed target, trigger IDs,
source/derivative digests, policy/config versions and expiry.

The client receives only:

- ticket ID;
- packet digest;
- provider/model and task kind;
- trigger IDs and safe reason labels;
- bounded projected token/cost metadata;
- expiry.

Confirmation submits only the ticket ID. The server reloads all state. Legacy
proposal text, route, provider, model, token, digest, outbound body and confirmation
booleans are rejected or ignored and never copied into the packet.

Immediately before the adapter call, one transaction checks pending state, expiry,
revocation, target, packet/source/policy/config digests, credentials and projected
budget, then changes the ticket to `consumed`. Provider error still consumes it.
Replay, mutation, stale data, policy drift or mismatch makes zero network calls.

The existing endpoint may be retained as a compatibility route, but its request
model becomes ticket-ID-only. A minimal frontend/API-client adjustment is permitted
solely to carry the server-issued ticket ID; no frontend redesign belongs here.

## Sampled rejection and invalidation

When a sampled derivative is rejected:

- mark the audit item rejected;
- revoke the canonical or prompt derivative through its owning service;
- invalidate all pending packets/tickets referencing its digest;
- record deterministic failure metadata and sanitizer version;
- make reuse impossible;
- do not delete or rewrite prior immutable decisions/attempts.

No automatic canonical-record promotion or sensitivity downgrade occurs.

## Safe ledger contract

Allowed metadata in `ai_jobs`, events, decisions and attempts includes:

- egress packet/decision/ticket IDs and digests;
- prompt and derivative digests, never bodies;
- effective levels and source/manifests counts;
- sanitizer `ai_jobs` ID and sanitizer/config/policy versions;
- deterministic result/reason codes;
- concrete provider/model and fallback index;
- projected/reserved/reconciled token and cost fields;
- network-attempt and estimate/actual status.

Forbidden metadata includes prompt bodies, context bodies, derivative bodies,
credentials, authorization headers, provider secrets and full packet JSON.

## Implementation surface

Expected bounded files, verified again against implementation-time `master`:

- additive migration in `backend/app/core/schema.py` plus one bounded 059b schema
  module;
- one egress policy/service module and typed models under
  `backend/app/modules/ai/`;
- `backend/app/modules/ai/execution.py` for the mandatory per-binding hook;
- `backend/app/modules/ai/budget.py` and existing cost helpers for projected
  reservation;
- bounded additive provenance/service changes in 059a sensitivity files;
- `backend/app/modules/ai/escalations.py`, request/response models and routes for
  ticket-ID confirmation;
- `backend/app/modules/ai/gateway.py` only to route external requests through the
  server-owned policy service;
- minimal frontend client/confirmation wiring only if required by the existing UI;
- focused schema/service/spine/API/adversarial tests and one implementation report;
- `docs/specs/STATUS.md` lifecycle updates.

Provider adapter implementations, Hermes runtime, BLUECAD product code, MemoryStore,
worker infrastructure, vector retrieval and unrelated UI remain unchanged.

## Required tests

### Schema and immutability

- additive migration works on fresh and existing databases;
- packet/decision/attempt rows are immutable through public services;
- ticket state transitions are compare-and-swap and single-use;
- exact bodies never appear in `ai_jobs`, events or safe API responses;
- old 059a rows with null additive provenance remain readable and behaviorally
  unchanged.

### Prompt and context authority

- ordinary context-free FAST_DEV prompt without hard markers may be S1;
- prompt hard markers prevent raw external serialization;
- prompt sanitizer must end S0/S1 and preserve raw/derivative digests;
- arbitrary manual blocks are withheld and make zero network calls;
- exact approved 059a derivative blocks are accepted only while current and digest
  matching;
- raw S2/S3/unknown/S4 and surviving secret-bearing material make zero calls;
- current secret-free effective S0/S1 derivative from an S4 source retains 059a
  eligibility semantics;
- final S2/S3 cannot be confirmed into a packet.

### Sanitizer and audit

- model-backed sanitizer uses explicit local `run_ai_task` and its own `ai_jobs` row;
- deterministic sanitizer makes no AI call and records its provenance;
- policy auto-approval records structured sanitizer provenance;
- weekly 5% sample is deterministic and auditable;
- rejection revokes and invalidates dependent pending packets/tickets;
- removing the sanitizer spine call or provenance check makes tests fail.

### Packet, policy and mutation resistance

- S0/S1 no-trigger packet silently allows and creates no ticket;
- packet digest changes for prompt/context/binding/token/policy/config changes;
- each trigger is configuration-driven and independently tested;
- malformed/missing config fails closed;
- client mutation of prompt, context, route, provider, model, token, digest, trigger or
  confirmation data cannot affect a persisted packet;
- unsupported operation denies with zero calls;
- removing the external-egress hook makes an integration test fail.

### Tickets and concurrency

- pending ticket allows exactly one atomic consume;
- provider error still consumes the ticket;
- replay, expiry, revocation, target mismatch and policy drift make zero calls;
- concurrent confirmation attempts produce at most one adapter invocation;
- legacy proposal-body confirmation cannot execute.

### Economic and fallback

- projected pending call cannot cross a hard monthly/provider/token limit;
- concurrent reservations cannot oversubscribe the final budget window;
- daily soft threshold triggers confirmation;
- unknown pricing fails closed;
- failed-before-network does not masquerade as provider consumption;
- actual/estimated reconciliation is deterministic;
- every fallback receives a new packet, decision, trigger, credential and economic
  evaluation;
- a decision for one provider/model cannot authorize another.

### Regression

- local routes and Auto local-only behavior remain unchanged;
- existing provider, context, 059a, MemoryStore, BLUECAD and API suites remain green;
- Ruff, full backend Pytest and applicable BLUECAD proof remain green.

## Stop conditions

Stop and amend rather than weaken if:

- exact prompt/context cannot be digest-bound;
- source selection and eligibility cannot share coherent authority;
- arbitrary manual context must be trusted externally;
- raw S2/S3/S4/unknown, surviving secret content or final S2/S3 must enter a packet;
- a model sanitizer can bypass `run_ai_task`/`ai_jobs`;
- automatic sanitizer provenance cannot be represented without falsifying the 059a
  reviewer/actor record;
- silent allow can occur above S1;
- policy configuration must be scattered constants;
- projected reservations cannot be atomic under SQLite concurrency;
- ticket consumption cannot occur immediately before the network attempt;
- a fallback can reuse an unbound decision;
- hard-budget or secret denial must become confirmable;
- any adapter or endpoint can bypass the shared spine;
- implementation requires a second gateway, AI spine, sensitivity system,
  MemoryStore, vector store, worker, streaming layer, DAG orchestrator, external-tool
  runtime, broad UI redesign or Hermes activation.

## Non-goals

- No change to accepted ADR-059 or ADR-060.
- No weakening or semantic rewrite of merged 059a labels, derivative eligibility,
  staleness, S4-source handling or manual review.
- No real project-data external dogfood before implementation merge.
- No claim that deterministic scans prove semantic IP removal.
- No provider/model addition or live-provider test.
- No 061 token continuation/optimization behavior.
- No provider-family diversification from 065.
- No vector retrieval, conversation runtime, worker, SSE or DAG orchestration.
- No external-tool execution.
- No automatic canonical record promotion.
- No encryption-at-rest or secure-delete claim.
- No CAD, mesh, FEM, runner or engineering-authority change.

## Definition acceptance criteria

1. Current master gaps are mapped to exact existing functions and schemas.
2. Prompt/manual context cannot bypass merged 059a authority.
3. The per-binding shared-spine hook location is explicit.
4. Exact packet, decision, ticket, attempt, prompt-derivative and audit persistence is
   defined without creating a second AI or sensitivity authority.
5. Projected economic reservation is atomic and remains subordinate to spec 021.
6. Automatic sanitizer provenance is honest and existing 059a behavior remains
   backward compatible.
7. Confirmation becomes ticket-ID-only and mutation resistant.
8. Fallback and concurrency semantics are mechanically testable.
9. The registry may promote 059b to `ready`; this authorizes implementation work only.
10. External autopilot, Hermes external passthrough and real BlueRev external dogfood
    remain inactive until the implementation PR is reviewed and merged.

## Implementation merge gate

An implementation PR must declare:

`**Spec gate:** implementation 059b`

Before merge it must set the registry row to `in_review` with its PR number, pass
focused and full backend tests, Ruff, schema migration tests, applicable BLUECAD
proof, current-head review, resolved/dispositioned findings, and explicit human merge
authority.
