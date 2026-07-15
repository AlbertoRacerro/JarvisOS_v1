# 059b policy autopilot implementation

## Status

Implementation is complete on code checkpoint
`0beb871fa17ec0f391729899e432e2d9a598c141` in draft PR #119.
Subsequent commits on the branch update this evidence report only. The PR remains
`in_review` and must not activate real project-data external egress until maintainer
review and merge.

The implementation started from merged definition commit
`bd31dae42c43a2ec052ae614a5a07a0dbdd37d94`.

## Implemented boundary

1. Strict `configs/ai_egress_policy.json` loading with a canonical config digest,
   bounded prompt/context sizes, confirmation TTL, reservation TTL, sampled-audit
   rate, daily soft-spend threshold, and an explicit operation allowlist.
2. Concrete provider/model execution authority and pricing in the existing provider
   registry. Route-level pricing remains advisory and cannot authorize execution.
3. Additive migration `0010_ip_egress_policy_autopilot` for prompt derivatives,
   immutable packets and decisions, mutable CAS-controlled reservations and tickets,
   immutable attempts, sanitizer audit items, and workspace egress policy.
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
- duplicate reservation start/reconciliation, orphan-reservation prevention, and
  concurrent ticket consumption.

## Verification evidence

Code checkpoint: `0beb871fa17ec0f391729899e432e2d9a598c141`.

GitHub Actions CI run `29395748755` completed successfully:

- spec status registry gate;
- manual-review tooling offline gate;
- BLUECAD license-boundary import gate;
- Ruff over the backend;
- full backend Pytest suite, including ticket-only confirmation, malformed-metadata
  pre-consumption failure, authority-state revalidation, concurrency, migration,
  sanitizer, fallback, budget, and regression tests;
- BLUECAD bounded property suite and canonical geometry canary.

GitHub Actions BLUECAD Real Tool Proof run `29395748770` completed successfully:

- offline regression suite;
- distro-pinned Gmsh and CalculiX installation;
- external hash-pinned tool-registry build and verification;
- strict full-chain real-tool proof;
- final offline and strict proof gates.

Report-only checkpoint `e8302d4ce4b6053358ef34916d8bdb111a36197d`
also completed successfully in CI run `29396150595` and BLUECAD Real Tool Proof run
`29396150561`. The current report-only head must retain the same green gates; GitHub
Actions is the authoritative current-head check state.

PR review state at this checkpoint:

- no unresolved inline review threads;
- no submitted approval or change-request review;
- PR remains draft and mergeable, but maintainer review has not occurred.

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
   routing, confirmation, and accounting boundaries. Green CI does not replace a
   current-head maintainer review of transaction ordering, SQL constraints, authority
   ownership, and response contracts.
3. **Backend compatibility surface only.** This PR exposes the ticket in the task API
   and accepts ticket-ID-only confirmation; it does not add a new frontend design.
   Any operator UI must display only server-owned ticket metadata and must not recreate
   proposal-owned execution fields.
4. **Single-process SQLite authority.** `BEGIN IMMEDIATE` and versioned state changes
   provide one-writer correctness for the current local architecture. A future
   multi-process or distributed worker design would require a separately specified
   transactional/idempotency boundary rather than assuming these semantics transfer.
5. **Catastrophic persistence failure.** Normal pre-network failures create a terminal
   `ai_jobs` row and release their reservation. A process or storage failure that makes
   both job creation and reservation reconciliation unavailable is bounded by the
   reservation TTL and requires operator diagnosis; it must not be converted into an
   execution bypass.
6. **Policy/config deployment discipline.** Changing provider registry or egress policy
   intentionally invalidates pending tickets. Operators must expect re-confirmation
   after such changes; bypassing drift checks is not an acceptable recovery path.

## Final lifecycle state

- Spec registry: `059b = in_review`, implementation PR #119.
- PR: open, draft, not merged.
- Runtime activation: blocked until reviewed and merged.
- Next action: maintainer current-head review of transaction ordering, SQL constraints,
  authority ownership, API compatibility, and residual-risk acceptance. Do not mark
  ready or merge automatically.
