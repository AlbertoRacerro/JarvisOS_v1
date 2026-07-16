# 066 — HERMES-PASSTHROUGH-0: evidence-gated model boundary

Status: planned compatibility draft, not implementation-ready. `docs/specs/STATUS.md`
is authoritative. This contract must not become `ready` until one immutable Hermes
identity and captured request/response/retry fixtures prove the exact disabled Phase-A
integration surface.

Depends on: 015, 018, 021, 059b, 061, 062

Durable decision: ADR-060

## Goal

Allow a pinned Hermes runtime to request model work only through JarvisOS while
JarvisOS retains provider credentials, route permission, sensitivity, 059b egress,
061 flow/economic/accounting authority, attempt ledgers, and final control.

066 is not a public OpenAI service, a provider proxy, a conversation database, a
runtime installer, or permission for Hermes to call providers directly.

## Disabled implementation versus production activation

066 may be implemented only as a disabled-by-default, transport-abstract boundary.
Captured local fixtures may instantiate the contract through an explicitly injected
test transport. This is contract evidence, not production isolation evidence.

066 does not select or authorize:

- a production bind address, port, socket family, or network namespace;
- firewall or VM/container policy;
- production runtime credentials or their injection;
- Hermes installation, launch, process supervision, or activation.

Those operations belong exclusively to 068 after merged 066 and 067 interfaces exist.
Importing, migrating, testing, or starting ordinary JarvisOS must not bind a production
listener or make the endpoint reachable.

The activation state defaults to `disabled`. Only a server-owned activation interface
may later inject the approved transport and credential verifier. Ordinary settings,
environment drift, client payloads, model content, forwarded headers, and reverse
proxies cannot activate the boundary or manufacture local trust.

## Why this remains a compatibility draft

Before implementation, fixtures from one selected immutable Hermes build must prove:

- exact custom-provider request and response shapes;
- authentication and correlation fields actually transmitted on every model path;
- behavior after HTTP errors, timeouts, disconnects, and response loss;
- provider/model retry and fallback behavior;
- every auxiliary, compression, delegated, vision, and helper model path;
- structured assistant tool-call/tool-result semantics required by the later tool phase.

Unsupported assumptions require a definition amendment. Do not fork Hermes or weaken
JarvisOS policy to fit an unproven client behavior.

## Phased boundary

### Phase A — text-only passthrough

The first implementable slice supports only non-streaming structured text requests.
Tools and tool messages are unavailable.

Every accepted concrete provider attempt must traverse:

1. `run_ai_task`;
2. the complete 059b packet, policy, trigger, credential, sensitivity, provenance,
   pricing, and reservation boundary;
3. the 061 capability, context, continuation, usage, cost, and monthly-budget boundary;
4. one canonical `ai_jobs` attempt row under the server-owned 061 flow.

Phase A remains disabled after merge. Fixture tests may use in-process or
same-namespace loopback only as test plumbing.

### Phase B — tool-capable passthrough

Tool schemas, assistant tool calls, tool-result messages, and provenance capsules remain
mechanically disabled until 067 is implemented and exact pinned-Hermes fixtures prove
the canonical/effective names, schemas, IDs, and result round trip.

Before 067, Phase-B tests are conditional fixtures only; they are not required runtime
interfaces for Phase A. Real tool use additionally requires 068 activation.

## Immutable Hermes identity

Before promotion, select one release/tag and resolve it to:

- upstream repository identity;
- immutable commit SHA;
- source/package fingerprint;
- Python and dependency-lock identity;
- license and notice identity;
- captured fixture-bundle digest;
- 066 compatibility-matrix version.

A moving branch, unconstrained package range, cached installation, or version string
without matching fingerprints fails closed. Upgrades create a new identity and rerun
the compatibility suite. The later 068 profile binds the accepted identity to its own
effective-config and isolation fingerprint.

## Model-path closure

The compatibility matrix must enumerate every Hermes path capable of invoking a model,
including:

- primary conversation and planner calls;
- provider/model retry and fallback lists;
- compression and summarization;
- delegation and sub-agents;
- vision or multimodal helpers, if present;
- title, approval, auxiliary, and provider-specific helpers;
- any plugin or feature that can initiate a completion request.

V0 contract:

- every model-capable path is mapped to the same logical 066 contract or disabled;
- Hermes receives no provider credentials;
- raw provider URLs and provider model names are absent from the accepted profile;
- Hermes-side automatic model retries are unconditionally `0`;
- Hermes provider/model fallback lists are empty;
- JarvisOS alone owns qualified provider fallback inside the shared spine;
- browser, computer, search, provider, or other bypass plugins remain disabled.

066 proves these expectations against captured fixtures. 068 later inspects the actual
effective runtime configuration and refuses activation on any unaccounted path, retry,
fallback, credential, or second model endpoint.

## Transport-facing request subset

The exact subset is derived from fixtures and uses strict schemas with unknown fields
rejected.

Minimum Phase-A candidate fields:

- one logical JarvisOS model alias, never a provider model name;
- non-empty ordered messages;
- `stream=false` only;
- an optional explicit lower output ceiling supported by 061;
- optional temperature, top-p, or stop only when fixtures and all eligible adapters
  preserve them honestly.

Unavailable:

- provider-specific headers, body fields, URLs, or model identifiers;
- remote files, image/audio/video content, parallel candidates, background, or async
  execution;
- tools, tool choice, tool calls, and tool-result roles in Phase A;
- caller-supplied workspace, sensitivity, route, provider permission, budget authority,
  credentials, activation state, or flow-finalization authority.

Transport/body/message limits are bounded abuse and resource limits, not hidden economic
output targets.

## Correlation, authentication, and flow grant

Every accepted request binds server-verifiably to:

- pinned Hermes profile/client identity;
- one JarvisOS-issued top-level `flow_id`;
- workspace and operator identity;
- logical turn and agent/parent identity;
- one idempotency identity and canonical request digest;
- an allowed logical JarvisOS alias;
- applicable 059b/061 policy and configuration versions.

The wire mechanism is not frozen. Custom headers are acceptable only if fixtures prove
they are present on every ordinary and auxiliary request. Otherwise use another
standards-compatible server-verifiable mechanism. Model-visible prose and the OpenAI
`user` field are never identity authority.

066 defines credential verification semantics but does not generate or inject a
production runtime credential. The later credential is rotatable/revocable, scoped only
to 066, generated outside committed configuration, stored as a verifier or secret
reference, and excluded from logs/errors.

A credential proves client identity only. Every request also requires an active
server-owned flow grant binding:

- flow, workspace, operator, and profile;
- allowed logical aliases;
- expiry, revocation, and flow state;
- server-owned model-call, agent, depth, concurrency, and wall-time limits;
- optional explicit lower flow-spend ceiling;
- 059b/061 policy versions;
- tool-disabled state or an accepted 067 catalog identity.

Absent an explicit lower operator ceiling, the 061 monthly USD hard budget remains the
economic authority.

## Shared-spine execution

For every accepted request:

1. require the server-owned activation interface to permit request handling; production
   activation is unavailable until 068, while fixtures use explicit test-only injection;
2. authenticate the pinned client;
3. resolve the active server-owned flow grant;
4. atomically validate and claim correlation/idempotency plus canonical request digest;
5. parse the exact supported compatibility subset;
6. resolve the logical alias and current capability requirements;
7. map structured content into the provider-neutral JarvisOS contract;
8. call only `run_ai_task`;
9. reconstruct and gate every concrete binding/fallback independently through 059b;
10. apply all 061 capability/context/continuation/usage/cost/budget rules;
11. write one `ai_jobs` row per real provider attempt under the same flow;
12. build the compatibility response only from normalized server-owned results;
13. complete the turn-claim record atomically.

No compatibility helper may instantiate or call a provider adapter directly. Adapter
network retry is forbidden. No helper may hide a second HTTP request.

## Idempotency and response loss

Use a local turn-claim record, separate from canonical usage accounting, binding:

- profile, flow, logical turn, and agent;
- idempotency identity and canonical request digest;
- state and safe terminal reason;
- linked attempt IDs;
- request/response digests.

V0 stores no response body for replay.

Required behavior:

- the first valid request claims the logical turn before provider execution;
- the same idempotency identity with a changed digest conflicts with zero new calls;
- a duplicate while in progress returns a non-retryable consumed/in-progress result;
- a duplicate after completion or terminal failure returns
  `hermes_turn_already_consumed` with safe IDs and terminal class/digest, but no output
  body or reconstructed response;
- a new idempotency identity cannot reuse an already claimed logical turn;
- response loss cannot cause a second provider execution;
- claim records contain no message/output body and never become a usage ledger.

Hermes retries remain disabled after every error, timeout, disconnect, response loss,
and confirmation-required result. Exact response replay or transport resume requires a
later specification and cannot be enabled by V0 configuration.

## Error and confirmation behavior

Return one strict compatibility error envelope plus bounded JarvisOS reason metadata.
Never expose prompt/context/packet bodies, credentials, secrets, or free-form stack
traces.

Malformed, unauthenticated, stale-grant, policy-denied, budget-stopped,
duplicate/consumed, and confirmation-required results are non-retryable by Hermes.

OpenAI chat completions has no standard digest-bound human-confirmation resume flow.
Therefore when 059b requires confirmation:

- persist the 059b ticket and exact 061 flow/segment state;
- consume and lock the logical Hermes turn;
- return a non-retryable confirmation-required result with safe IDs;
- make no provider call for the blocked attempt;
- never let Hermes, a model, or a tool consume the ticket;
- never resume the consumed Hermes turn;
- keep the top-level 061 flow in nonterminal `confirmation_required`;
- allow only the direct JarvisOS operator surface to consume the ticket and resume the
  same server-owned 061 flow.

The direct UI resume may complete or terminally stop the 061 flow, but it is not a
Hermes transport replay. A future standards-compatible Hermes resume requires a later
specification.

## Flow state and grading authority

All Hermes turns and agents for one operator task share one JarvisOS-issued 061 flow.
Hermes cannot create authoritative flow state, declare terminality, or grade itself.

The JarvisOS 061 flow service is the only terminality authority:

- runtime exit, process failure, or a returned compatibility envelope does not by itself
  terminalize a flow;
- `confirmation_required` remains nonterminal even after the Hermes process exits;
- the 068 launcher/controller may report runtime lifecycle events but cannot override
  the 061 state machine;
- finalization occurs only when the 061 flow is in a terminal state and every linked
  059b reservation/attempt is reconciled;
- only the resulting immutable finalized 061 outcome snapshot is gradeable by 062.

## Persistence and migration discipline

Do not freeze a numeric migration ID in this compatibility draft. The implementation-
time next additive migration may include:

- disabled activation state and compatibility version;
- strict request/response models;
- scoped local-client verifiers;
- flow grants;
- turn-claim records.

Operational transport records do not replace Hermes session memory, JarvisOS domain
records, 061 flow state, or `ai_jobs`, and do not become a second usage ledger.

## Required evidence and tests

### Pinned identity and path closure

- immutable identity, fingerprint, lock, license, and fixture-bundle checks;
- every model-capable path appears in the compatibility matrix;
- primary, auxiliary, compression, delegation, vision, and fallback requests use the
  same contract or are disabled;
- Hermes retries and fallback lists remain disabled;
- no provider credential or direct provider endpoint appears in fixtures.

### Disabled transport contract

- fresh and upgraded states leave 066 disabled;
- ordinary JarvisOS startup binds no production listener;
- only the explicit activation interface can permit request handling;
- ordinary settings, environment overrides, requests, and model content cannot activate
  or select a bind address;
- fixture transports exercise the complete contract without claiming isolation;
- missing or cross-flow authentication/correlation fails before provider execution;
- merging 066 cannot install, launch, bind production transport, inject runtime
  credentials, or activate Hermes.

### Shared spine and economics

- every concrete external attempt traverses `run_ai_task`, 059b, 061, and `ai_jobs`;
- each fallback is independently reconstructed, priced, reserved, and gated;
- raw provider model, route, URL, permission, and budget-authority fields fail;
- monthly USD budget and reservations cannot be oversubscribed;
- attempts share the correct flow and aggregate exactly once;
- no direct adapter call or hidden second request exists.

### Idempotency, confirmation, and flow state

- exact duplicate/replay cases create at most one provider execution;
- changed digests and reused logical turns conflict before network;
- consumed turns return no replay body;
- confirmation consumes the Hermes turn but leaves the 061 flow nonterminal;
- only the direct operator surface can consume the ticket and resume the same 061 flow;
- runtime exit cannot terminalize `confirmation_required`;
- the launcher/controller cannot override the 061 state machine;
- only terminal reconciled flows produce a finalized 062-gradeable snapshot.

### Phase separation

- Phase A rejects tools and tool messages with zero provider calls;
- 067-dependent catalog/capsule tests remain conditional before 067;
- real tools require Phase B, merged 067, and 068 activation.

### Privacy and regression

- messages, credentials, tickets, and 062 notes stay out of safe logs/ledgers;
- turn-claim records contain no request or response body;
- existing direct AI, 059b, 061, 062, MemoryStore, and BLUECAD tests remain green;
- CI uses fake adapters/captured fixtures and no live provider.

Run full backend tests, Ruff, status-registry self-test, applicable frontend regressions,
and BLUECAD real-tool proof.

## 068 activation obligations

Before activating the merged disabled boundary, 068 must prove:

- the selected Windows-first private endpoint is reachable only by the approved runtime;
- unrelated host, guest, and LAN processes cannot connect;
- actual authentication and correlation appear on every installed ordinary/auxiliary
  request;
- effective configuration closes every direct-provider, retry, fallback, plugin, and
  second-model path;
- runtime credentials are injected without entering committed configuration;
- kill switch and revocation return the interface to disabled without erasing canonical
  flow, attempt, or accounting evidence.

These are activation requirements, not prerequisites for compiling and reviewing the
disabled 066 implementation.

## Non-goals

No production transport binding, Hermes installation/launch/activation, runtime secret
injection, response-body replay, public `/v1`, streaming, multimodal support, provider
addition/OAuth, browser/search/computer use, terminal/filesystem access, cron/proactive
work, conversation database, model self-grading, automatic routing promotion,
canonical-memory mutation, or Hermes fork/vendor patch.

## Promotion gates

Before `STATUS.md` may move 066 to `ready`:

1. 059b, 061, and 062 implementations are merged and stable.
2. One immutable Hermes identity and complete captured Phase-A fixture bundle are
   accepted.
3. All primary, auxiliary, delegated, and fallback model paths are represented by the
   compatibility matrix and use the same contract or remain disabled.
4. Correlation, idempotency, response loss, and duplicate-turn rejection are proven in
   captured local fixtures.
5. Confirmation leaves the 061 flow resumable through the direct operator surface and
   cannot be confused with Hermes turn replay.
6. The implementation defaults disabled, uses only an injectable transport abstraction,
   and cannot bind or activate production transport by itself.
7. Phase-A resource limits and exact compatibility matrix are accepted.
8. 067-dependent behavior remains conditional and real tools remain disabled.
9. Migration ID is assigned from implementation-time `master`.
10. Exact-head CI and independent review have no unresolved blockers.

Even after implementation merge, 068 remains mandatory before any production binding,
Hermes installation/launch, runtime credential injection, or activation.
