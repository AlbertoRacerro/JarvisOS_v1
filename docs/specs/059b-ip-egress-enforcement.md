# 059b — IP-EGRESS-1B: policy autopilot and execution enforcement

Status: blocked until the amended 059 definition and ADR are merged; `docs/specs/STATUS.md` is authoritative.

Depends on: 059a

Parent definition: `docs/specs/059-ip-egress-1.md`

## Goal

Implement the normal external-provider path as a server-owned policy autopilot:
minimum context, automatic local sanitization, exact packet construction,
deterministic egress/economic decisions, silent S0/S1 allow, and execution through
the shared spine. Human confirmation occurs only when a configured trigger fires.

This is not permission for a model, frontend, or request payload to authorize a
provider call. Models may propose task kind, transformations, and route family;
JarvisOS policy owns the final route, provider/model, budget, sensitivity, packet,
ticket, and execution decision.

Any model-backed sanitizer, including a sanitizer served by local Ollama, is an AI
call. It must use `run_ai_task` with an explicit local route and write its own
`ai_jobs` row. Only a strictly deterministic non-model transformation may run
without an AI call. Sanitizer output remains advisory/untrusted and gains no
permission authority from model or schema success.

Merged 059a remains authoritative. In particular, only effective S0/S1 content may
enter an external preview or packet. Confirmation cannot override that rule.

## Runtime scope

059b owns only:

- automatic sanitizer orchestration over merged 059a labels and derivatives;
- model-backed sanitizer calls through `run_ai_task`/`ai_jobs`, or explicitly
  deterministic non-model transformations;
- deterministic pre/post scans and provenance/version binding;
- sampled human-audit queue, defaulting to 5% weekly;
- derivative revocation and sanitizer-failure evidence after sampled rejection;
- configured count/size caps for blocks derived from S2/S3/unknown sources;
- canonical `EgressPacket` and immutable `EgressDecision`;
- silent server-owned allow for effectively S0/S1 packets without triggers;
- configured trigger evaluation (`t1`–`t5`);
- expiring digest-bound single-use tickets only for confirmable triggered flows;
- projected daily/monthly/provider economic re-check immediately before calls;
- replacement of client-trusted escalation confirmation;
- independent enforcement for every concrete fallback binding;
- safe egress/sanitizer/ticket ledger metadata;
- mutation-resistant offline integration tests.

It must not create a second AI execution spine, gateway, MemoryStore, sensitivity
store, provider adapter, external-tool runtime, conversation system, vector store,
worker process, streaming transport, DAG orchestrator, or frontend redesign.

## Automatic sanitizer contract

For S2, S3, or `unknown` source material:

1. load current source and 059a authority in one coherent read snapshot;
2. minimize selected context;
3. run either a strictly deterministic non-model transformation or the configured
   model-backed rewrite/abstraction sanitizer through `run_ai_task` on an explicit
   local route, producing a separate `ai_jobs` record;
4. run deterministic secret/IP scans before and after rewriting;
5. recompute the content digest and effective level;
6. store a derivative bound to source digests and sanitizer/model/config version;
7. record `reviewer = policy-sanitizer-vN` for automatic approval;
8. fail closed on stale source, malformed output, scan failure, surviving secret
   evidence, or a final level above S1.

Raw S2/S3/unknown never enters an external packet. Raw S4 and any final or derived
content that remains S4 or secret-bearing are denied with no override.

A derivative originating from an S4-labelled source is not denied solely because
of its source label. Consistent with merged 059a, it may become externally eligible
only when it is current, provenance-bound, effective S0/S1, all deterministic scans
confirm that no secret-bearing content survives, and every other gate passes.

An effective S0/S1 derivative may follow silent autopilot. A result that remains
S2/S3 invokes `t3` and is routed to review/resanitization or local execution; it
cannot be confirmed into an external packet.

## Sampled audit contract

- Default: deterministically sample 5% of auto-approved derivatives each calendar
  week.
- Store sampling-policy version, cohort, and selection evidence.
- Sampled rejection revokes the derivative immediately, logs sanitizer failure,
  and blocks reuse.
- Policy may increase sampling or require full review by workspace, task kind,
  provider family, or recent failure window.
- Reducing the default below 5% is outside implementation authority.

## Context minimization contract

- Never include an entire workspace, vault, conversation archive, or corpus in one
  packet.
- Configuration supplies a fail-closed maximum count and serialized-size budget for
  blocks derived from S2/S3/unknown sources.
- Sensitivity withholding and cap enforcement occur before prompt serialization.
- Explicit IDs, task instructions, and model requests cannot bypass the cap.
- Withheld, sanitizer-failed, policy-capped, and token-budget-dropped reasons remain
  separately auditable.
- Packet accounting must inspect derivative `source_refs`; it must not assume a
  one-to-one mapping between selected raw records and outbound blocks.

## Packet and decision contract

The canonical packet binds:

- exact prompt and exact included context;
- included, withheld, sanitizer-failed, policy-capped, and budget-dropped manifests;
- source and derivative IDs/digests;
- explicit route and concrete provider/model;
- task kind and server-sized token limit;
- final effective level;
- sanitizer, trigger, and policy versions.

Any change creates a new digest.

The immutable decision records allow/deny/pause, deterministic reason, operation,
concrete binding, effective sensitivity, packet digest, source counts, policy
versions, trigger IDs, and ticket state where present.

Every external network adapter attempt requires both:

1. current projected economic/provider/credential approval; and
2. current exact-packet egress approval.

Fallbacks are reconstructed and re-evaluated independently. Local model-backed
sanitizer tasks are separately recorded through the same AI spine but do not receive
external-egress permission and cannot authorize their own output.

## Trigger table

The trigger set is configuration, not scattered constants.

| ID | Trigger | Behavior |
| --- | --- | --- |
| `t1` | first use of provider/model pair | exact-packet confirmation |
| `t2` | projected call crosses daily soft-spend threshold | exact-packet confirmation; monthly hard stop remains final |
| `t3` | sanitizer failure or deterministic S2/S3/S4 floor on output | pause and create review/resanitization work; no external ticket until output is S0/S1 |
| `t4` | unsupported/unknown egress operation | deny; confirmation cannot invent support |
| `t5` | workspace `ask_me` flag | exact-packet confirmation for an otherwise eligible S0/S1 packet |

Malformed or missing trigger configuration fails closed. Surviving S4/secret
content, final effective level above S1, hard-budget exhaustion, missing
credentials, stale provenance, and unsupported mechanics are non-confirmable denials
or pauses.

## Ticket lifecycle

Silent S0/S1 calls create no confirmation ticket.

An otherwise eligible packet triggering `t1`, `t2`, or `t5` uses one server-loaded
ticket binding packet digest, fixed target set, trigger IDs, source/derivative
digests, policy versions, and expiry. The spine reloads authoritative state and
atomically consumes `allow_once` immediately before the adapter. Provider error
still consumes it. Replay, mutation, expiry, revocation, target mismatch,
staleness, or policy drift yields zero adapter calls.

Legacy confirmation payload text, route, provider, model, token, digest, and boolean
fields are ignored or rejected; only server-owned identifiers are accepted.

## Projected economic contract

The existing spec-021 gate remains authoritative for paid-AI/provider/credential
policy, but 059b must close the known pre-call projection gap:

- reserve or conservatively estimate the pending call before approval;
- clamp server-owned token sizing to task, model, provider, and remaining-budget
  limits;
- evaluate daily soft threshold triggers before the call;
- enforce monthly hard budget as a non-confirmable denial;
- repeat the check for every concrete fallback;
- distinguish actual provider usage from conservative estimates and failed-before-
  network attempts in ledger aggregation.

059b must not create a second economic ledger or bypass spec 021.

## Ledger contract

Record safe metadata only:

- egress decision/ticket IDs;
- packet and derivative digests;
- effective level and source/manifests counts;
- sanitizer task `ai_jobs` ID when a model-backed sanitizer is used;
- sanitizer, sampling, trigger, and policy versions;
- deterministic result/reason codes;
- concrete target and fallback-attempt index;
- bounded usage/cost fields and estimate/actual status.

Do not store prompt bodies, source bodies, derivative bodies, credentials, or
authorization headers in `ai_jobs` or events.

## Required tests

- S0/S1 no-trigger packet silently allows and writes decision/execution rows.
- Silent allow creates no ticket or human-confirmation requirement.
- Each trigger is configuration-driven and independently tested.
- Missing/malformed policy config fails closed.
- Raw S2/S3/unknown/S4 and final secret-bearing content make zero external adapter
  calls.
- An S4-source derivative that is current, effective S0/S1, and secret-free follows
  the same eligibility rules as other S0/S1 derivatives.
- A final effective S2/S3 derivative makes zero adapter calls even when a user
  attempts confirmation.
- A model-backed sanitizer uses `run_ai_task`, an explicit local route, and its own
  `ai_jobs` row; removing that spine call makes a test fail.
- A deterministic non-model sanitizer makes no AI call and is identified as such in
  provenance.
- Automatic derivative preserves exact source digests and sanitizer provenance.
- Weekly 5% sample is deterministic and auditable.
- Sample rejection revokes and blocks derivative reuse.
- S2/S3/unknown-derived count/size caps apply before serialization.
- Client mutation of prompt, route, target, token, digest, or confirmation fails.
- Projected call cost/token usage cannot cross a hard limit through the last call.
- Monthly hard budget and surviving S4/secret content cannot be overridden.
- Failed-before-network attempts do not masquerade as actual provider consumption.
- Expired, stale, revoked, mismatched, and consumed tickets make zero calls.
- Fallbacks receive independent packet, trigger, credential, and economic checks.
- Removing the external-egress hook from the shared spine makes a test fail.
- Existing provider, Auto, context, MemoryStore, BLUECAD, Ruff, and full backend
  suites remain green.

## Stop conditions

Stop and amend rather than weaken if:

- exact content cannot be digest-bound;
- selection and eligibility cannot share one coherent authority snapshot;
- raw S2/S3/unknown/S4, surviving secret-bearing content, or final effective S2/S3
  must enter an external packet;
- a model-backed sanitizer can bypass `run_ai_task` or `ai_jobs`;
- sanitizer provenance cannot be preserved;
- silent allow can occur above S1;
- trigger/cap/sampling policy must be scattered code constants;
- policy must trust client fields;
- a fallback can reuse an unbound decision;
- hard-budget or surviving-secret denial must become confirmable;
- any adapter can bypass the shared spine;
- implementation requires a second gateway, AI execution spine, MemoryStore,
  sensitivity store, vector store, worker, streaming layer, DAG orchestrator, or
  frontend redesign.

## Merge gate

An implementation PR must declare `**Spec gate:** implementation 059b`.

059b may move to `ready` only after:

- this amended definition is merged;
- ADR-059 is merged and explicitly reconciles the still-accepted ADR-057;
- the full implementation spec is reconciled against current `master`;
- 059a remains `merged`.

Implementation requires executing green CI, focused tests, full backend Pytest,
Ruff, applicable BLUECAD proof, completed review, resolved/dispositioned findings,
and human merge authority.

Real BlueRev external dogfood remains blocked until 059b is merged and active.
