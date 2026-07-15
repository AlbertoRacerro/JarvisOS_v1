# 059b policy autopilot implementation

## Status

Implementation is complete on runtime checkpoint
`a360fdcc0584bc0697213961c2455f1e831c3416` in draft PR #119.
The canonical-workflow verification checkpoint is
`eb0a1b50022d686a11f8b863546c6cb34deeb9b3`.

The implementation started from merged definition commit
`bd31dae42c43a2ec052ae614a5a07a0dbdd37d94`.
The PR remains `in_review`; real project-data external egress must remain disabled
until an explicit maintainer ready/merge decision.

## Implemented boundary

1. Strict `configs/ai_egress_policy.json` loading with a canonical config digest,
   bounded prompt/context sizes, confirmation TTL, reservation TTL, sampled-audit
   rate, daily soft-spend threshold, and an explicit operation allowlist.
2. Concrete provider/model execution authority and pricing in the existing provider
   registry. Route-level pricing remains advisory and cannot authorize execution.
3. Additive migration `0010_ip_egress_policy_autopilot` for prompt derivatives,
   immutable packets and decisions, mutable CAS-controlled reservations and tickets,
   immutable attempts, sanitizer audit items, workspace egress policy, and the
   `ai_jobs.usage_source` evidence field.
4. Deterministic S0/S1 packet projection with exact prompt/context, concrete binding,
   fallback index, source manifests, source digests, token upper bounds, cost upper
   bounds, pricing version, policy version, trigger version, and config digest.
5. Prompt and manual-context authority with deterministic secret denial, local-only
   sanitizer execution through the existing `run_ai_task`/`ai_jobs` spine, and
   provenance-bound prompt and canonical derivatives.
6. Mandatory per-binding execution hook for every network-capable binding, including
   independent policy and budget evaluation for each fallback attempt. Sanitizer tasks
   cannot open an external fallback path and adapters do not own hidden retries.
7. Ticket-ID-only confirmation. The client may submit only `ticket_id`; prompt,
   context, route, provider, model, fallback index, and token cap are reloaded from
   persisted server-owned rows. The exact authorized binding is called at most once
   and confirmation does not reopen the fallback chain.
8. Confirmation audit metadata is loaded and validated before ticket consumption. A
   missing or malformed ticket/decision/packet metadata join fails before the
   pending-to-consumed CAS, leaving zero reservation and zero execution job. A binding
   mismatch detected after consumption creates a terminal job and releases the
   reservation before any adapter call.
9. Atomic ticket consumption and projected-budget reservation. Pending-to-consumed,
   active-to-in-flight, and reconciliation transitions use explicit state/version
   checks; pre-network failures release zero provider consumption and post-network
   failures are conservatively reconciled.
10. Mutable authority is revalidated inside the same `BEGIN IMMEDIATE` transaction as
    ticket consumption. Prompt-derivative revocation, canonical-derivative revocation
    or staleness, source deletion or mutation, label replacement or elevation, policy
    drift, registry/binding drift, credential loss, and budget drift revoke or deny the
    ticket before a reservation is created.
11. Sampled sanitizer audit can revoke dependent pending tickets and release unstarted
    reservations without mutating immutable decisions or attempts.
12. Provider usage evidence is ledger-bound. `finalize_queued_ai_job` persists
    `actual`, `estimated`, or `mixed`; runtime and confirmation propagate the adapter's
    declared source; reconciliation accepts `actual` only when caller evidence and the
    persisted job source both say `actual`. Historical or malformed rows fail closed.
13. Stale `in_flight` recovery preserves finalized usage only when its persisted source
    is `actual`. Estimated, mixed, missing, or malformed evidence is reconciled at the
    reserved conservative upper bound.

## Maintainer-review correction

The current-head review found one accounting-authority blocker after the first green
implementation checkpoint:

- tokens and cost were persisted in `ai_jobs`, but their evidence source was not;
- both network runtimes passed `usage_source="actual"` unconditionally;
- a response marked `estimated` could therefore be promoted to actual accounting when
  it happened to carry a populated cost, including after crash recovery.

The correction at `a360fdcc0584bc0697213961c2455f1e831c3416` adds the constrained
`usage_source` column, persists the adapter-declared source, requires persisted actual
evidence for actual reconciliation, and makes stale recovery source-aware. Migration,
direct reconciliation, legacy fixture, and crash-recovery tests cover this boundary.

## Failure modes explicitly covered

- packet JSON, packet digest, policy/config, provider/model, pricing, and fallback-index
  tampering or drift;
- expired, replayed, revoked, missing, concurrently consumed, or metadata-corrupted
  confirmation tickets;
- client-owned replacement prompt, task kind, context, route, provider, model, or
  output cap submitted to the confirmation endpoint;
- missing settings, disabled policy, paid-AI disabled, zero/exhausted budget, provider
  token/cost caps, missing or invalid credentials, and post-ticket gate changes;
- prompt secrets, external-ineligible prompt/context levels, stale labels, stale or
  revoked derivatives, source mutation/deletion, source-label elevation, malformed
  manifests, duplicate context sources, and response binding mismatch;
- adapter absence, exception before network, provider exception after network,
  retryable provider failure without confirmed-ticket fallback, missing usage, and
  pricing drift during reconciliation;
- estimated or mixed usage carrying a populated/list-price-consistent cost;
- caller attempts to claim actual usage when the persisted job source is not actual;
- stale in-flight recovery with missing, estimated, mixed, or malformed usage evidence;
- duplicate reservation start/reconciliation, orphan-reservation prevention, and
  concurrent ticket consumption.

## Verification evidence

Canonical-workflow checkpoint:
`eb0a1b50022d686a11f8b863546c6cb34deeb9b3`.

GitHub Actions CI run `29450032924` completed successfully:

- spec status registry gate;
- manual-review tooling offline gate;
- BLUECAD license-boundary import gate;
- Ruff over the backend;
- full backend Pytest suite, including usage-source migration, estimated-to-actual
  rejection, stale in-flight source-aware recovery, ticket-only confirmation,
  authority-state revalidation, concurrency, fallback, budget, and regression tests;
- BLUECAD bounded property suite and canonical geometry canary.

GitHub Actions BLUECAD Real Tool Proof run `29450032925` completed successfully:

- offline regression suite;
- distro-pinned Gmsh and CalculiX installation;
- external hash-pinned tool-registry build and verification;
- strict full-chain real-tool proof;
- final offline and strict proof gates.

The bounded actuator used to apply the reviewed patch also required Ruff and the full
backend suite before it could create the runtime commit. Temporary patch files and the
one-shot workflow were removed; `.github/workflows/ci.yml` is back to its canonical
blob `9b8c76d334189e6d96f5a085491835e85753c0bb`.

PR review state at this checkpoint:

- PR remains open, draft, mergeable, and not merged;
- no automatic ready transition, auto-merge, provider call, Hermes call, or real
  BlueRev-data egress occurred;
- current-head maintainer review found and corrected the usage-source blocker;
- final residual-risk acceptance and merge readiness remain explicit maintainer
  decisions.

## Hard constraints preserved

- no packet body before effective S0/S1 eligibility;
- no model-backed sanitizer outside local-only `run_ai_task` / `ai_jobs`;
- no hidden adapter retries;
- no fallback after a concrete confirmation ticket is consumed;
- immutable decisions and attempts; mutable reservations and tickets only through
  bounded lifecycle transitions;
- no second gateway, usage ledger, sensitivity authority, worker, vector store,
  conversation engine, or Hermes runtime;
- no secret value stored in packets, ledgers, route metadata, reports, or tests;
- merged 059a behavior remains backward compatible;
- real project-data external dogfood remains disabled until merge.

## Residual risks and limitations

1. **No real external-provider dogfood in this PR.** Network-capable adapters are
   exercised through deterministic stubs in backend tests. Actual provider latency,
   error payloads, rate limits, and usage-report fidelity remain operational evidence
   to collect only after maintainer-approved activation.
2. **Large security-sensitive diff.** PR #119 changes policy, schema, persistence,
   routing, confirmation, and accounting boundaries. Green CI and this review pass do
   not eliminate the need for explicit maintainer acceptance before activation.
3. **Backend compatibility surface only.** This PR exposes the ticket in the task API
   and accepts ticket-ID-only confirmation; it does not add a new frontend design.
   Any operator UI must display only server-owned ticket metadata and must not recreate
   proposal-owned execution fields.
4. **Single-process SQLite authority.** `BEGIN IMMEDIATE` and versioned state changes
   provide one-writer correctness for the current local architecture. A future
   multi-process or distributed worker design requires a separately specified
   transactional/idempotency boundary.
5. **Lazy stale-in-flight recovery.** An orphaned `in_flight` reservation is recovered
   at the next egress gate rather than by a background worker. It cannot permanently
   bypass or free budget, but it may remain visibly in-flight while no subsequent gate
   runs.
6. **Catastrophic persistence failure.** Normal pre-network failures create a terminal
   `ai_jobs` row and release their reservation. A process or storage failure that makes
   both job finalization and reconciliation unavailable is conservatively bounded by
   stale-in-flight recovery and requires operator diagnosis; it must not be converted
   into an execution bypass.
7. **Policy/config deployment discipline.** Changing provider registry or egress policy
   intentionally invalidates pending tickets. Operators must expect re-confirmation
   after such changes; bypassing drift checks is not an acceptable recovery path.

## Final lifecycle state

- Spec registry: `059b = in_review`, implementation PR #119.
- PR: open, draft, not merged.
- Runtime activation: blocked until reviewed and merged.
- Next action: explicit maintainer residual-risk acceptance and readiness decision.
  Do not mark ready or merge automatically.
