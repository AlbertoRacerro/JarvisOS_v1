# 059 — IP-EGRESS-1: sensitivity, retrieval, and external-boundary enforcement

Status: ready after definition reconciliation; `docs/specs/STATUS.md` is authoritative.

Depends on: 003, 015, 018, 021, 040, 042

## Goal

Add one fail-closed, server-owned policy boundary that determines whether the
**exact outbound packet** for an AI provider or future external tool may leave
JarvisOS.

The boundary must cover the current prompt, manual context, workspace/context-pack
records, sanitized derivatives, target provider/model, explicit user confirmation,
and provenance. It must run immediately before every concrete external provider
attempt, including each fallback, while preserving the independent budget and
credential gate from spec 021.

After 059, real BlueRev project data may be dogfooded only when its sensitivity
and provenance are known and the outbound packet satisfies this contract. A model,
request body, route label, caller-supplied `confirmed` flag, or provider response
cannot authorize egress or lower sensitivity.

## Current runtime facts that bind this definition

1. `run_ai_task` is the shared provider execution spine. It resolves concrete
   bindings and currently calls `adapter.complete(...)` after route/config and
   budget checks.
2. `evaluate_alpha_execution_gate(...)` in `ai/budget.py` governs provider,
   credential, usage, and cost state. It intentionally does not govern IP,
   retrieval, redaction, or confirmation.
3. `AITaskRunRequest` permits a caller to select an explicit external route and
   attach arbitrary `context_blocks`. The current block schema contains only
   `source`, `content`, `type`, and `id`; it carries no authoritative sensitivity
   or provenance binding.
4. `build_workspace_context_bundle` and the context-pack preview select accepted
   project records deterministically but do not filter them by sensitivity.
5. Domain Foundation and MemoryStore records have no persisted sensitivity label.
   Existing rows therefore cannot be assumed public or internal.
6. `AIRequest.privacy_class` and model `allowed_privacy_classes` exist as contract
   fields, but the execution spine currently creates requests without an
   authoritative final privacy class.
7. Auto classification sensitivity is advisory. Deterministic hard overrides and
   JarvisOS policy remain authoritative.
8. The current escalation-confirm endpoint accepts a client-supplied proposal
   object and directly reuses its `outbound_text`, route, and token limit. This is
   not an authorization boundary: 059 must replace it with a server-loaded,
   digest-bound, single-use confirmation ticket.
9. No production external-tool execution path exists today. The shared egress
   operation enum must deny unsupported external-tool operations by default; 059
   must not invent a tool runtime.
10. Conversation history runtime is not yet implemented. Future history/chat must
    enter through the same context-source and egress-packet contracts rather than
    creating a parallel path.

## Canonical sensitivity taxonomy

059 maps the existing privacy vocabulary onto one persisted five-level scale:

| Level | Existing meaning | Examples | Raw external rule |
| --- | --- | --- | --- |
| `S0` | `public` | published literature, public standards excerpts, synthetic smoke data | eligible after ordinary external confirmation and all other gates |
| `S1` | `internal` | non-proprietary working notes, generic code, ordinary internal task text | eligible after ordinary external confirmation and all other gates |
| `S2` | `confidential` | private project planning or partner/internal material that can be safely abstracted | raw denied; an approved `S2` derivative remains internal-only, and only an approved derivative with effective level `S0` or `S1` may be external-eligible |
| `S3` | `sensitive_ip` | proprietary BlueRev geometry, correlations, process parameters, unpublished design decisions | raw denied; only a separately reviewed derivative with effective level `S0` or `S1` may be external-eligible |
| `S4` | `secret` | credentials, private keys, tokens, passwords, secret material | raw denied; a derivative may be eligible only when no secret-bearing content survives and its effective level is `S0` or `S1` |

`unknown` is not a sixth permissive level. It is a fail-closed state for external
use and is treated at least as restrictive as `S3` until a human-reviewed label or
approved derivative resolves it.

### Final-level rules

- JarvisOS computes one final level as the most restrictive applicable signal.
- Deterministic secret/credential detection floors to `S4`.
- Explicit proprietary BlueRev/IP markers floor to `S3`.
- Explicit private/confidential project markers floor to `S2`.
- A local-model hint may raise the floor but can never lower it or authorize
  external use. Low-confidence or failed classification remains `unknown` where
  no deterministic level is available.
- Caller-supplied labels may raise sensitivity but cannot lower a server-owned
  record label or make an unlabeled manual block external-eligible.
- In `STRICT_IP`, an otherwise unclassified raw prompt is `unknown`, not `S1`.
- In `FAST_DEV`, a bounded prompt with no project/manual context and no hard
  marker may retain the existing pragmatic `S1` default. This exception never
  labels project records and never applies to attached/manual context.
- `DISABLED` continues to deny AI execution.

## Policy-owned labels

Add an additive sidecar label store rather than duplicating a sensitivity column
across every record table.

A label binds:

- normalized subject reference `<kind>:<id>`;
- workspace id;
- `S0`–`S4` level;
- canonical digest of the labelled content;
- classification source (`human`, `deterministic_floor`, `import`, or
  `sanitized_derivative`);
- policy version;
- reviewer/actor and timestamps;
- optional prior label id for audit.

Binding to the content digest is mandatory. If the source record changes, the old
label becomes stale and that source is `unknown` for external use until relabelled.
Missing labels on legacy rows are `unknown`; the migration must not mass-label old
records as public/internal.

A human may classify an unlabeled/unknown record. Once a source is labelled `S2`,
`S3`, or `S4`, that source record may not be downgraded in place. A lower-level
representation must be a new sanitized derivative preserving the original source
reference and digest.

## Sanitized derivatives

059 does not claim automatic semantic redaction. The first implementation accepts
operator-reviewed sanitized text and validates deterministic structural rules.
No model-generated derivative is trusted or promoted automatically.

Each derivative stores:

- immutable derivative id and workspace id;
- source references and source content digests;
- sanitized content and its digest;
- declared effective `S0`–`S2` level;
- deterministic sanitizer/policy version;
- transformations/redactions summary;
- reviewer/actor and review timestamp;
- status (`draft`, `approved`, `revoked`, `stale`);
- stale/revoked reason where applicable.

Rules:

1. Source records are never overwritten or relabelled downward.
2. Every source digest must still match when the derivative is used.
3. Structural-secret scanning runs on the derivative and fails closed.
4. A derivative of an `S4` source can be approved only as `S0` or `S1`.
5. An approved derivative may still be raised by deterministic floors.
6. Any source change, policy-version mismatch, revocation, or missing source makes
   the derivative unusable for egress.
7. Approval is a human authority event; schema validity or model output is not
   evidence that redaction is complete.
8. Only effective `S0` and `S1` derivatives are external-eligible. An approved
   effective `S2` derivative is a reviewable internal artifact and must be withheld
   from automatic and manual external previews.

## Context selection and preview contract

Sensitivity enforcement occurs **before content is serialized into an outbound
prompt**.

The context builder must produce two manifests:

- included sources: source ref, content digest, effective level, label/derivative
  id, and inclusion reason;
- withheld sources: source ref, effective level or `unknown`, and deterministic
  exclusion reason, without returning withheld content.

For local-only execution, current legacy blocks remain usable, but their missing
policy metadata is explicit. For external eligibility:

- a workspace record requires a current digest-bound label or an approved
  derivative;
- only effective `S0` or `S1` raw records and derivatives may be included;
- an approved `S2` derivative is withheld even when its source digests and review
  state are current;
- a caller-supplied manual block is `unknown` and external-ineligible unless it
  references a server-owned approved derivative with an exact digest match;
- explicit record ids bypass status filters as in spec 042, but never bypass
  sensitivity filtering;
- budget truncation happens after sensitivity withholding so dropped and withheld
  counts/reasons remain distinct;
- the preview endpoint is read-only, invokes no model/provider, writes no AI job,
  and never exposes withheld content;
- context digests and source manifests cover only the exact included packet.

## Exact outbound packet

Before any network attempt, JarvisOS constructs one canonical `EgressPacket` from:

- current user prompt or approved prompt derivative;
- included context blocks;
- included/withheld source manifests;
- target route, concrete provider id, and model id;
- task kind and token limit;
- policy version and sensitivity decision ids;
- derivative ids where used.

The packet has a canonical SHA-256 digest. Confirmation and execution bind to this
exact digest. Any change to prompt, context, provider/model, route, token cap,
source digest, derivative, or policy version invalidates the confirmation.

Raw `S2`, raw `S3`, raw `S4`, effective `S2` derivatives, and `unknown` content must
never be placed in an externally eligible packet. Logging uses digests and safe
metadata only.

## Egress decision

Add an immutable `EgressDecision` containing at least:

- `allowed`;
- deterministic reason code;
- operation (`external_provider_call`; unsupported operations deny);
- route class, provider id, and model id;
- prompt level, maximum context level, and final effective level;
- packet digest;
- included, withheld, and derivative source counts;
- policy version;
- confirmation requirement and confirmation/ticket id when present.

The decision is server-owned. Request models must continue rejecting
self-authorization fields.

For every concrete network binding, `run_ai_task` must require both:

1. the existing alpha/budget decision from spec 021; and
2. an allowed 059 egress decision for the exact packet and concrete provider/model.

Both checks run again for each fallback. Approval for provider A does not authorize
provider B unless the ticket explicitly binds the fallback target and exact packet;
the preferred implementation issues one ticket whose allowed target set is fixed
at proposal time and checks each attempted binding against it.

A non-network fixture binding remains offline, but local execution still receives
the final sensitivity metadata and must never treat `S4` as ordinary model input.

## Confirmation and replay prevention

Replace client-trusted proposal execution with a server-owned ticket lifecycle:

1. Proposal creation stores an exact externally eligible packet, packet digest,
   allowed route/provider targets, effective level, policy version, proposal AI job
   id, and expiry.
2. The client receives only safe proposal metadata plus ticket id and digest.
3. Confirmation identifies the ticket; the server reloads it and validates status,
   expiry, packet digest, current source/derivative digests, policy version, target,
   and current budget/credential state.
4. Confirmation creates or marks one `allow_once` authorization.
5. The execution spine atomically consumes it before the adapter call. A failed
   provider call still consumes the ticket; retry/fallback is allowed only within
   the ticket's pre-bound target set during that execution.
6. Replay, altered route, altered payload, expired ticket, revoked derivative, or
   already-consumed ticket fails closed with zero adapter calls.
7. Raw proposal payload is retained locally only for a bounded TTL and only when
   its effective level is `S0`–`S2`. After consumption/expiry, payload content is
   cleared while digest/audit metadata remains. SQLite deletion is not represented
   as forensic secure erase.

The legacy confirm request may be accepted temporarily for compatibility only if
all client-supplied route/text/token fields are ignored and execution is rebuilt
from a valid server ticket. Otherwise the legacy shape must be rejected.

## Ledger and provenance

No prompt, source content, secret, or sanitized body is added to `ai_jobs`.
The ledger records safe metadata:

- egress decision id and policy version;
- packet digest;
- effective level;
- included/withheld/derivative counts;
- ticket id and consumption state;
- deterministic deny reason;
- concrete provider/model and fallback attempt index.

Sanitized derivatives and policy labels retain their own provenance records.
A denied request writes a normal pre-provider ledger row and makes zero network
adapter calls.

## Delivery split

059 is intentionally split into two implementation PRs after this definition PR.

### 059-A — sensitivity and context foundation

- additive schema migration for policy labels and sanitized derivatives;
- services/models for digest-bound labels and approved derivatives;
- deterministic sensitivity floors and stale-label handling;
- sensitivity-aware context selection and preview manifests;
- tests for legacy unknown defaults, digest staleness, withholding, derivative
  provenance, and zero provider calls.

059-A must not alter `adapter.complete(...)`, confirmation semantics, or provider
execution.

### 059-B — packet, ticket, and execution enforcement

- canonical `EgressPacket` and immutable `EgressDecision`;
- server-owned expiring single-use egress tickets;
- ID/digest-bound escalation confirmation;
- execution-spine and per-fallback enforcement immediately before adapters;
- safe ledger metadata and replay prevention;
- mutation-resistant integration tests proving zero adapter calls on every denial.

059-B depends on merged 059-A.

## Files expected to change

Verify paths against `master`; do not create parallel gateways or stores.

Likely 059-A surface:

- `backend/app/core/schema.py`;
- a bounded policy module under `backend/app/modules/ai/`;
- `backend/app/modules/ai/context_builder.py`;
- `backend/app/modules/ai/models.py` and `routes.py` only for label/derivative and
  preview contracts;
- Domain Foundation/MemoryStore read helpers only as needed for normalized
  `<kind>:<id>` resolution;
- focused tests and one implementation report.

Likely 059-B surface:

- the same bounded policy module;
- `backend/app/modules/ai/execution.py`;
- `backend/app/modules/ai/escalations.py`;
- `backend/app/modules/ai/models.py` and `routes.py`;
- `backend/app/modules/ai/routing/bridge.py` only for proposal metadata, never as
  the authoritative final gate;
- focused tests and one implementation report.

Provider adapters, BLUECAD product callers, frontend, corpus PRs, and unrelated
runner/solver code should remain unchanged unless a concrete integration test
proves a shared-spine defect.

## Required tests

### 059-A

- legacy unlabeled records are `unknown` for external selection;
- human initial classification is audited and digest-bound;
- source mutation makes a label/derivative stale;
- an `S2`/`S3`/`S4` source cannot be downgraded in place;
- approved derivative preserves source refs/digests and passes secret scanning;
- `S4` derivative cannot be approved above `S1`;
- explicit ids do not bypass sensitivity withholding;
- manual blocks cannot self-declare an external-safe level;
- preview returns included and withheld manifests but no withheld content;
- local preview/build behavior remains deterministic and makes zero provider calls.

### 059-B

- direct explicit external route without a ticket makes zero adapter calls;
- unsupported egress operation, missing policy context, unknown level, raw `S2`,
  raw `S3`, and raw `S4` fail closed;
- approved derivative packet can be proposed but not executed before confirmation;
- client mutation of text, route, target, tokens, or digest is ignored/rejected;
- expired, revoked, stale, mismatched, and consumed tickets make zero adapter calls;
- one confirmation is consumed exactly once, including after provider error;
- fallback providers are independently checked against the ticket target set and
  current alpha/budget state;
- removal of the egress-gate call from the execution spine makes an integration
  test fail;
- local non-network fixtures remain testable and `S4` is not sent to a local model;
- ledger rows contain only safe metadata and deterministic reason codes;
- all existing provider, Auto, context-pack, MemoryStore, BLUECAD, and full backend
  tests remain green.

## Stop conditions

Stop and amend this definition rather than weakening the boundary if:

- labels cannot be bound to a stable digest of the content actually retrieved;
- sensitivity filtering can occur only after withheld content has already entered
  the outbound prompt;
- any network adapter can be called outside the shared execution spine;
- fallback execution can reuse approval for an unbound provider/model;
- confirmation requires trusting client-supplied outbound text or route data;
- a ticket cannot be consumed atomically enough to prevent ordinary replay;
- raw `S2`/`S3`/`S4`/`unknown` content must be persisted in an egress proposal to make
  the flow work;
- the implementation requires automatic semantic redaction or claims that a
  deterministic secret scan proves IP removal;
- legacy records must be silently labelled public/internal;
- a model hint becomes final sensitivity or permission authority;
- implementation requires a second provider gateway, second MemoryStore, external
  tool runtime, conversation system, vector database, frontend, or provider SDK.

## Non-goals

- No automatic semantic redaction or model-approved downgrade.
- No vector retrieval, embeddings, LLM reranking, or conversation history runtime.
- No external-tool execution runtime.
- No provider/model addition and no live provider calls in tests.
- No frontend settings or proposal-review UI.
- No encryption-at-rest claim or forensic secure-delete claim.
- No automatic relabelling of the existing database.
- No change to local CAD, mesh, FEM, runner, promotion, or engineering authority.

## Acceptance criteria

1. The definition PR is docs/registry/report only and receives Codex review before
   maintainer merge.
2. 059-A and 059-B are separate implementation PRs.
3. Each implementation PR has green focused tests, full backend Pytest, Ruff, and
   any applicable existing BLUECAD proof.
4. Each implementation PR receives a completed Codex review whose findings are
   read and resolved or explicitly dispositioned before merge.
5. No implementation PR is self-merged; human merge authority remains final.
6. After 059-B, deleting or bypassing the egress check permits no green test suite.
7. Real BlueRev IP/cloud dogfood remains blocked until both slices are merged.
