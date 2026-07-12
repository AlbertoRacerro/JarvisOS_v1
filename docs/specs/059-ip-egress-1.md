# 059 — IP-EGRESS-1: sensitivity, retrieval, and external-boundary enforcement

Status: ready after maintainer amendment; `docs/specs/STATUS.md` is authoritative.

Depends on: 003, 015, 018, 021, 040, 042

## Binding maintainer amendment — 2026-07-12

This definition supersedes the earlier assumption that every external provider call
requires human confirmation. JarvisOS will normally use external providers through
a server-owned policy autopilot. Human confirmation is exceptional and occurs only
when a configured trigger fires.

The maintainer explicitly accepts the residual risk that an automatically sanitized
S2/S3-derived representation may still retain some project-specific information.
Prototype velocity takes priority over exhaustive IP protection. This accepted risk
changes policy defaults and ceremony, not the execution-spine mechanics.

The amendment does not weaken these invariants:

- every provider call passes through `run_ai_task` and writes an `ai_jobs` row;
- models, frontend code, and request fields may recommend but never authorize a
  provider route, budget, permission, sensitivity downgrade, or state change;
- exact packet construction, policy decisions, provider/model binding, and fallback
  checks are server-owned;
- safe defaults remain paid AI disabled, budget zero, and fake provider;
- `route_class="auto"` remains local-only; policy autopilot resolves an explicit
  external route before execution;
- S4 and secret-bearing content never leaves JarvisOS;
- monthly hard-budget denial cannot be confirmed away.

Spec 059a was merged through PR #90 and is the unchanged substrate for this
amendment. In particular, external eligibility remains strictly effective S0/S1.
059b must build on that rule rather than reopening or bypassing it.

## Goal

Add one fail-closed, server-owned boundary that decides whether the **exact outbound
packet** for an external provider may leave JarvisOS.

The normal path is:

1. select the minimum necessary context;
2. classify current sources using the merged 059a labels, derivatives, floors, and
   stale-state rules;
3. automatically sanitize eligible S2/S3/unknown sources locally;
4. require the resulting outbound representation to be effectively S0 or S1;
5. construct and digest the exact packet;
6. apply egress, projected-economic, credential, provider, and trigger policy;
7. silently allow the packet when no configured confirmation trigger fires;
8. execute through the shared spine and record the decision and call.

The boundary runs immediately before every concrete provider attempt, including
each fallback. A model, route label, request body, caller-supplied confirmation flag,
or provider response cannot authorize egress or lower sensitivity.

## Current runtime facts that bind this definition

1. `run_ai_task` is the shared provider execution spine.
2. `evaluate_alpha_execution_gate(...)` governs provider, credential, usage, and
   cost state but does not own IP sensitivity, sanitization, exact-packet binding,
   or confirmation-ticket integrity.
3. Explicit external routes and manual context currently lack one final exact-packet
   egress decision immediately before adapter invocation.
4. The merged 059a implementation provides digest-bound labels and derivatives,
   deterministic floors, stale handling, sensitivity-aware selection, and
   read-only included/withheld previews.
5. 059a permits only effective S0/S1 records or derivatives in external previews.
   Approved S2 derivatives remain internal-only.
6. Auto sensitivity classification remains advisory. Deterministic policy is
   authoritative.
7. The legacy escalation-confirm path accepts client-supplied outbound text, route,
   and token metadata. 059b must replace this trust with server-loaded packet state.
8. Unsupported external-tool operations deny by default; 059 does not create an
   external-tool runtime.
9. Conversation history is not yet a separate authority or egress path. Future
   history must enter through the same context and packet contracts.

## Canonical sensitivity taxonomy

| Level | Existing meaning | Raw external rule |
| --- | --- | --- |
| `S0` | public | eligible for silent policy allow when all other gates pass and no trigger fires |
| `S1` | internal/non-proprietary | eligible for silent policy allow when all other gates pass and no trigger fires |
| `S2` | confidential/private project material | raw denied; derivative path only; final external representation must be S0/S1 |
| `S3` | proprietary or sensitive IP | raw denied; derivative path only; final external representation must be S0/S1 |
| `S4` | credentials, private keys, tokens, passwords, equivalent secret material | deny always; no confirmation override |

`unknown` is not a permissive sixth level. It is treated at least as restrictive as
S3 for raw egress and enters the local sanitization/review path. It is never sent
raw.

### Final-level rules

- JarvisOS computes the most restrictive applicable level.
- Deterministic credential/secret evidence floors to S4.
- Explicit proprietary/IP evidence floors to S3.
- Explicit private/confidential evidence floors to S2.
- Model hints and caller labels may raise but never lower the final level.
- Missing, stale, malformed, or policy-version-mismatched authority becomes
  `unknown` for external use.
- A source once classified S2/S3/S4 cannot be downgraded in place; a lower-level
  representation is a separate derivative with immutable provenance.
- `STRICT_IP` retains fail-closed unknown handling.
- `FAST_DEV` may retain the existing bounded S1 default only for ordinary prompt
  text with no attached project/manual context and no hard marker.
- `DISABLED` continues to deny AI execution.

## 059a substrate: labels and derivatives

059a is merged and remains authoritative for:

- normalized `<kind>:<id>` subject references;
- labels bound to workspace, source content digest, level, policy version,
  classification source, actor/reviewer, timestamp, and prior-label chain;
- deterministic floors and causal latest-label resolution;
- immutable derivative identity, source references/digests, content digest,
  effective level, transformations, reviewer, policy version, and lifecycle state;
- stale/revoked/source-missing/policy-mismatch behavior;
- coherent SQLite read snapshots for selection and eligibility;
- read-only preview and ordinary derivative reads;
- explicit revalidation for persisted stale transitions;
- effective S0/S1-only external preview eligibility.

The derivative `reviewer` field is an actor/provenance field. A value such as
`policy-sanitizer-vN` is valid for an automatically approved derivative and binds
the exact sanitizer policy/version; it need not identify a human.

## Automatic sanitization

S2, S3, and `unknown` sources may become external-eligible only through a
provenance-preserving local pipeline:

1. load current source content and 059a authority in one coherent read snapshot;
2. apply deterministic floors and context minimization;
3. locally rewrite, abstract, redact, or summarize;
4. run deterministic secret and IP scans before and after rewriting;
5. recompute content digest and effective level;
6. persist source digests, sanitizer/model/config version, transformations,
   `reviewer = policy-sanitizer-vN`, approval state, and policy version;
7. fail closed on malformed output, stale source, missing provenance, scan failure,
   S4 evidence, or any final level above S1.

Raw S2/S3/unknown never enters an external packet. S4 does not use this external
eligibility path.

An effectively S0/S1 derivative may be auto-approved and may follow silent
policy autopilot. A result that remains S2/S3 is **not** externally eligible and
cannot be made eligible by confirmation. It invokes trigger `t3`, which pauses for
review, requires another sanitization pass, or remains local. This preserves the
merged 059a contract while implementing the maintainer's sampled-review posture.

Deterministic scans are guardrails, not proof of semantic IP removal.

## Sampled human audit

Human review is sampled rather than required for every automatically approved
derivative:

- default sample: 5% of auto-approved derivatives per calendar week;
- selection, sample cohort, and policy version are deterministic and auditable;
- sampled rejection revokes the derivative, logs a sanitizer failure, and blocks
  reuse;
- policy may increase sampling or require full review by workspace, provider family,
  task kind, recent failure window, or explicit `ask_me` preference;
- reducing the default below 5% requires a separate maintainer decision.

## Context minimization

- Never place an entire workspace, conversation archive, vault, or corpus in one
  packet.
- Every block carries server-owned source/derivative identity and digest.
- Configuration defines fail-closed per-packet count and serialized-size caps for
  blocks derived from S2/S3/unknown sources.
- Explicit IDs, model requests, and task requests never bypass these caps.
- Sensitivity withholding and policy caps occur before serialization.
- Token-budget truncation occurs afterward, with withheld, sanitizer-failed,
  policy-capped, and budget-dropped reasons kept distinct.
- Packet manifests partition outbound blocks and preserve derivative `source_refs`;
  they are not assumed to map one-to-one to selected raw rows.

Provider-family diversification is a separate planned follow-up. It may route
families of derived content across provider accounts, but it may not weaken packet,
budget, sensitivity, or audit gates.

## Exact outbound packet

Before any network attempt, JarvisOS constructs one canonical `EgressPacket`
containing at least:

- exact user prompt or approved prompt derivative;
- exact included context blocks;
- included, withheld, sanitizer-failed, policy-capped, and budget-dropped manifests;
- source/derivative IDs and current digests;
- explicit route and concrete provider/model binding;
- task kind and server-sized token limit;
- sensitivity, sanitizer, trigger, and policy versions;
- final effective level.

The packet has a canonical SHA-256 digest. Any change to content, source state,
derivative, route, provider/model, token sizing, policy version, or trigger state
creates a new digest and invalidates any prior decision or ticket.

Raw S2/S3/S4, unknown content, effective S2/S3 derivatives, and secret-bearing
content must never be serialized into an externally eligible packet. Logs contain
digests and safe metadata only.

## Egress decision

Add an immutable, server-owned `EgressDecision` containing at least:

- result (`allow`, `deny`, or `pause`);
- deterministic reason code;
- operation (`external_provider_call`; unsupported operations deny);
- explicit route, concrete provider ID, and model ID;
- prompt level, maximum context level, and final effective level;
- packet digest;
- included, withheld, derivative, sanitizer-failed, and policy-capped counts;
- policy/sanitizer/trigger versions;
- confirmation requirement, trigger IDs, and ticket ID where present.

For every concrete network binding, including every fallback, `run_ai_task` must
require both:

1. a current projected economic/provider/credential approval; and
2. an allowed exact-packet egress decision for that concrete provider/model.

Approval for one binding does not authorize another. Fallbacks are independently
reconstructed and re-evaluated.

## Policy autopilot

A packet whose included blocks are all effectively S0/S1 receives a silent
server-owned `allow` when all other gates pass and no confirmation trigger fires.
Silent allows still write decision and execution ledger rows; they create no
confirmation ticket.

The trigger list is configuration data, not scattered code constants:

| ID | Trigger | Required behavior |
| --- | --- | --- |
| `t1` | first use of a provider/model pair | exact-packet confirmation |
| `t2` | projected call crosses the daily spend soft threshold | exact-packet confirmation; monthly hard budget remains final |
| `t3` | sanitization pipeline failure or deterministic S2/S3/S4 floor on sanitized output | pause and create review/resanitization work; no externally eligible packet exists until the final output is S0/S1 |
| `t4` | unsupported or unknown egress operation | deny; confirmation cannot invent a runtime |
| `t5` | explicit per-workspace `ask_me` flag | exact-packet confirmation for an otherwise eligible S0/S1 packet |

Unknown, missing, or malformed trigger configuration fails closed. S4, monthly
hard-budget exhaustion, missing credentials, stale provenance, final level above
S1, and unsupported mechanics are non-confirmable denials or pauses.

## Confirmation and replay prevention

A single-use confirmation ticket exists only when an otherwise eligible packet
triggers `t1`, `t2`, or `t5` (or another future explicitly configured confirmable
trigger approved by a later spec).

The lifecycle is:

1. proposal creation stores the exact eligible packet, packet digest, fixed target
   set, trigger IDs, source/derivative digests, policy versions, proposal AI job ID,
   and expiry;
2. the client receives only safe metadata, ticket ID, and packet digest;
3. confirmation identifies the ticket; the server reloads all authoritative state;
4. current source/derivative digests, policy, target, credential, and projected
   budget state are revalidated;
5. one `allow_once` authorization is atomically consumed immediately before the
   adapter call;
6. provider failure still consumes it;
7. replay, mutation, expiry, revocation, staleness, target mismatch, or policy drift
   yields zero adapter calls.

The legacy confirmation request may remain temporarily only as an identifier
carrier. Client-supplied text, route, provider, model, token, digest, and boolean
confirmation fields are ignored or rejected.

## Ledger and provenance

No prompt, source body, derivative body, credential, or authorization header is
added to `ai_jobs` or events.

Safe metadata includes:

- egress decision and ticket IDs;
- packet and derivative digests;
- effective level;
- source/manifests counts;
- sanitizer, policy, sampling, and trigger versions;
- deterministic allow/deny/pause reason;
- concrete provider/model and fallback-attempt index;
- bounded usage/cost fields.

A denied or paused request writes a normal pre-provider ledger row and makes zero
network adapter calls.

## Delivery split

### 059a — sensitivity and context foundation

Merged through PR #90. It owns labels, derivatives, deterministic floors,
staleness, coherent context selection, read-only preview, and S0/S1-only external
eligibility. This amendment does not modify that implementation.

### 059b — policy autopilot and execution enforcement

After this definition amendment is merged and its ADR is reconciled, 059b owns:

- automatic sanitizer orchestration;
- sampled human-audit queue and revocation behavior;
- S2/S3/unknown-derived packet caps;
- canonical packet and immutable decision;
- silent S0/S1 allow;
- configured trigger evaluation;
- single-use tickets for confirmable triggers;
- projected economic re-checks;
- removal of client-trusted escalation data;
- per-fallback spine enforcement;
- safe ledger evidence and mutation-resistant tests.

059b follows the normal backlog row → kernel/full-spec → implementation ladder.

## Files expected to change

Verify paths against current `master`; do not create parallel gateways or stores.
Likely 059b surface:

- one bounded egress-policy module under `backend/app/modules/ai/`;
- the existing 059a sensitivity/derivative services only through public contracts;
- `backend/app/modules/ai/execution.py`;
- `backend/app/modules/ai/escalations.py`;
- `backend/app/modules/ai/budget.py` for projected-call checks;
- AI request/response models and routes for safe decision/ticket contracts;
- `backend/app/modules/ai/routing/bridge.py` only for advisory proposal metadata;
- focused tests and one implementation report.

Provider adapters, BLUECAD product callers, frontend, conversation runtime, vector
stores, worker infrastructure, and unrelated runner/solver code remain unchanged
unless a concrete shared-spine defect requires a bounded correction.

## Required 059b tests

- S0/S1 no-trigger packet silently allows and creates no ticket;
- each trigger is configuration-driven and independently tested;
- missing/malformed policy or trigger configuration fails closed;
- raw S2/S3/unknown/S4 makes zero adapter calls;
- final effective S2/S3 derivative makes zero adapter calls even after human
  confirmation input;
- automatic derivative preserves source digest and sanitizer provenance;
- default weekly 5% sampling is deterministic and auditable;
- sampled rejection revokes and blocks derivative reuse;
- S2/S3/unknown-derived count and size caps apply before serialization;
- client mutation of text, route, target, token, digest, or confirmation fails;
- projected daily/monthly/provider limits are checked before every attempt;
- monthly hard budget and S4 cannot be overridden;
- expired, stale, revoked, mismatched, and consumed tickets make zero calls;
- one confirmation is consumed exactly once, including after provider error;
- fallbacks receive independent packet, trigger, credential, and economic checks;
- removing the egress hook from the shared spine makes an integration test fail;
- ledger rows contain only safe metadata and deterministic reason codes;
- existing provider, Auto, context, MemoryStore, BLUECAD, Ruff, and full backend
  suites remain green.

## Stop conditions

Stop and amend rather than weaken this definition if:

- exact content cannot be digest-bound;
- selection and eligibility cannot share a coherent authority snapshot;
- raw S2/S3/S4/unknown or final effective S2/S3 derivatives must enter an external
  packet;
- sanitizer provenance cannot be preserved;
- silent allow can occur above S1;
- trigger, cap, or sampling policy must be scattered code constants;
- a fallback can reuse an unbound decision;
- client-supplied outbound text, route, provider, token, or confirmation must be
  trusted;
- a provider can bypass the shared execution spine;
- S4 or monthly hard-budget denial must become confirmable;
- the design requires a second gateway, MemoryStore, sensitivity store, vector
  database, worker, streaming layer, DAG orchestrator, external-tool runtime, or
  frontend redesign.

## Non-goals

- No modification or reopening of merged 059a runtime.
- No claim that deterministic scans prove semantic IP removal.
- No S4 or final-S2/S3 confirmation override.
- No provider/model addition or live-provider test.
- No vector retrieval, conversation runtime, worker process, SSE streaming, or DAG
  orchestration.
- No external-tool execution runtime.
- No automatic canonical record promotion.
- No encryption-at-rest or forensic secure-delete claim.
- No local CAD, mesh, FEM, runner, or engineering-authority change.

## Acceptance criteria

1. This amendment PR changes docs, registry, and report only.
2. The maintainer's residual-risk acceptance and sampled-audit rationale are
   explicit.
3. Merged 059a remains unchanged and authoritative.
4. Silent autopilot is restricted to exact effective S0/S1 packets.
5. Confirmation cannot authorize S4, monthly hard-budget denial, unsupported
   mechanics, stale authority, or a final level above S1.
6. 059b follows the normal registry ladder before runtime work.
7. 059b implementation requires executing green CI, focused tests, full backend
   Pytest, Ruff, applicable BLUECAD proof, completed review, and human merge
   authority.
8. Real BlueRev external dogfood remains blocked until 059b is merged and active.
