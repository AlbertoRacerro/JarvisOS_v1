# 066 — HERMES-PASSTHROUGH-0: policy-owned OpenAI-compatible agent-loop boundary

Status: planned; this is a kernel, not an implementation-ready spec.

Depends on: 015, 018, 021, 059b, 061, 062

## Problem

Hermes Agent needs an OpenAI-compatible model endpoint, but JarvisOS cannot let
Hermes hold provider credentials, select an unbounded provider, bypass sensitivity
or economic policy, or create a second AI gateway.

The current `run_ai_task` path is not yet an agent-loop-compatible passthrough. It
accepts a user prompt plus bounded context, assembles a text prompt, and returns a
provider-neutral response. The current contracts do not preserve the complete
OpenAI tool-calling exchange required by Hermes.

A text-only `/chat/completions` wrapper would appear operational while silently
breaking tool calls, tool results, retry semantics, or ledger attribution.

## Maintainer direction

- JarvisOS exposes a loopback-only OpenAI-compatible endpoint implemented through
  the shared `run_ai_task` execution spine.
- Hermes uses only `model.provider: custom` against that endpoint.
- Provider API keys remain only inside JarvisOS.
- Hermes receives only a scoped local client credential; that credential is not a
  provider key and cannot authorize route, egress, budget, sensitivity, or
  promotion.
- Every concrete provider attempt remains subject to the alpha/budget gate, 059b
  exact-packet egress enforcement, and `ai_jobs` accounting.
- Models advertised to Hermes are policy aliases derived from the currently
  permitted JarvisOS route catalog. Discovery never constitutes authorization.
- External execution is hard-blocked until 059b is merged and its exact-packet,
  trigger, replay, fallback, and economic contracts are active.

## Required future contract

A full spec must define at least the following.

### 1. Supported wire surface

- `GET /v1/models`, or the exact standards-compatible equivalent required by the
  pinned Hermes version;
- `POST /v1/chat/completions`;
- explicit behavior for `stream=true`; the first slice may reject streaming
  deterministically if the pinned Hermes profile is proven to operate
  non-streaming;
- bounded request size, message count, tool count, tool-schema size, output-token
  request, and timeout;
- OpenAI-shaped error bodies with stable JarvisOS reason codes in safe metadata.

The accepted subset must be written as a compatibility matrix, not described only
as “OpenAI-compatible”.

### 2. Agent-loop message and tool semantics

The JarvisOS provider-neutral contract must preserve the subset used by the pinned
Hermes version, including:

- `system`, `developer`, `user`, `assistant`, and `tool` message roles where used;
- string content and any explicitly approved content-part forms;
- OpenAI tool definitions and bounded JSON Schemas;
- assistant `tool_calls`, stable call IDs, function names, and JSON arguments;
- tool-result messages bound by `tool_call_id`;
- `finish_reason`, refusal/block state, and usage fields;
- deterministic rejection of unsupported or ambiguous fields.

The implementation must not tunnel the complete unvalidated request through an
opaque metadata dictionary.

### 3. Route aliases and policy ownership

- Expose logical, stable JarvisOS model aliases rather than raw provider
  credentials or unrestricted provider model names.
- Resolve every requested alias again at execution time.
- Re-check provider availability, model capability, sensitivity, exact packet,
  token/cost envelope, and configured confirmation triggers for every concrete
  attempt and fallback.
- A stale, removed, unknown, or currently disallowed alias fails closed.
- Hermes-side `adaptive_local`, provider fallback, or model switching may choose
  only among aliases currently offered by JarvisOS and never grants permission.
- `/v1/models` output is a snapshot for discovery, not a capability token.

### 4. Provenance continuity

Messages originating from Jarvis MCP tools must carry a server-owned provenance
reference that the passthrough can verify without trusting model-visible text.

The preferred first contract is an opaque `context_capsule_id` plus canonical
digest whose authoritative sensitivity, source references, expiry, workspace,
actor/session binding, and policy version are reloaded by JarvisOS. If a signed
capsule is used, the signing key remains inside JarvisOS.

Missing, expired, forged, altered, cross-workspace, or unrecognized provenance is
`unknown` for external eligibility. Hermes, the model, a tool result, or caller
metadata cannot self-declare S0/S1.

### 5. Authentication and network boundary

- Bind only to loopback or an equivalently isolated local transport.
- Use a least-privilege, rotatable, revocable local credential supplied outside
  the committed profile.
- Never log the credential or return it in diagnostics.
- Define startup failure when authentication, loopback binding, or effective
  route policy cannot be proven.
- Host firewall/egress controls are defense-in-depth and must prevent Hermes from
  reaching provider endpoints directly.

### 6. Retry, idempotency, confirmation, and denial

- Define a JarvisOS request/correlation ID and canonical request digest.
- Correlate one Hermes turn with all `ai_jobs` rows produced by provider attempts,
  fallbacks, retries, and bounded continuations.
- Do not claim one ledger row per high-level turn when the execution spine records
  one row per attempt.
- Define which retries are safe, how replay is detected, and how duplicate client
  retries avoid accidental duplicate spend.
- A 059b denial or confirmation trigger must not cause Hermes to rotate to an
  ungoverned provider or retry indefinitely.
- The full spec must prove the pinned Hermes version's behavior for each HTTP
  denial class used by JarvisOS.
- If a standards-only, resumable confirmation flow cannot be made reliable in the
  first slice, the first passthrough profile must exclude confirmation-triggering
  external operations rather than weaken 059b.

### 7. Economic and concurrency enforcement

- 061 owns token sizing, projected reservation, continuation, and reconciliation.
- 062 supplies graded quality evidence; it does not authorize a route.
- JarvisOS enforces per-request, per-session, provider, and monthly limits.
- Hermes iteration or subagent settings are not trusted as the economic boundary.
- Concurrent attempts must not oversubscribe the remaining budget.

### 8. Compatibility and conformance tests

The full spec must include a pinned-Hermes conformance fixture covering:

- ordinary text completion;
- one tool call and one tool-result continuation;
- multiple tool calls if enabled;
- malformed arguments and unknown tools;
- length stop and bounded continuation;
- refusal and policy denial;
- unknown/stale model alias;
- usage propagation;
- timeout and client retry;
- provider fallback with per-attempt gating;
- forged/missing MCP provenance;
- zero network calls on every pre-provider denial;
- `ai_jobs` correlation and safe metadata only.

## Hard lines

- No direct provider key or provider OAuth token in Hermes.
- No endpoint path may call an adapter directly outside `run_ai_task`.
- No model, Hermes field, caller field, route alias, or cached model list may
  authorize execution.
- No raw prompt, tool payload, secret, or canonical record body is added to
  `ai_jobs`.
- No import of Hermes internals into JarvisOS and no JarvisOS patch inside Hermes
  to make the boundary work.
- No external execution before 059b is merged and active.

## Non-goals

No provider addition, UI, generic public OpenAI service, Responses API, browser,
computer use, autonomous cron, unrestricted streaming, direct database access,
canonical-memory write, promotion, or Hermes vendoring.

## Promotion evidence

Before this row may become `ready`, the full spec must:

1. bind the accepted wire subset to a specific Hermes commit/tag and fingerprint;
2. identify exact JarvisOS contract, execution, route, and ledger surfaces;
3. reconcile denial/confirmation behavior with 059b and Hermes fallback behavior;
4. bind projected economics to 061;
5. include deterministic agent-loop parity tests with zero live-provider CI;
6. prove that every model call made by the hardened profile, including auxiliary
   and delegated calls, reaches this boundary.
