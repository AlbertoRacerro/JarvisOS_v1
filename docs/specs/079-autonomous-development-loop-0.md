# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: proposed full specification; it becomes merged authority only after an explicit human merge. `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Pinned baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Predecessor evidence:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one explicitly authorized JarvisOS repository-development slice to continue safely across agent-session termination.

V0 may reconstruct GitHub-owned authority, claim one repository-wide front, create one exact-base work branch, invoke one bounded implementer before a PR exists, create one PR only after a real delta, terminalize a verified initial no-change result without an empty PR, collect exact-head gates, run one reviewer request per review attempt, perform at most two fix/re-review rounds, settle accepted calls before applying stops, record every failure path canonically, record human PR actions truthfully, and release a reconciled terminal front without erasing history.

V0 may never merge, auto-merge, approve authoritatively, change roadmap priority, infer authority from activity, create a second front, or turn model output into authority.

## 2. Boundary and proposed sequencing amendment

This document specifies canonical state, authorization, claim, lease, branch/PR lifecycle, dispatch, gates, review attempts and rounds, findings, spend, permissions, webhooks, proofs, rollout, kill switches, and compatibility.

It creates no App, service, database, queue, branch, ruleset, workflow, secret, provider, dependency, runtime change, governance amendment, readiness decision, implementation, or merge automation. It does not modify `AGENTS.md` or `STATUS.md` and invokes no model or paid service.

Current `AGENTS.md` remains binding. Live development-agent dispatch is prohibited until section 24's separate governance amendment and dated readiness decision merge.

### 2.1 Documentary ordering presented for human approval

The merged architecture closure requires isolated race, CAS, credential, cost, PR, and recovery proofs before full-spec promotion. The maintainer subsequently instructed drafting to proceed.

Before merge, the prior ordering remains authoritative. Human merge of this PR would approve only that the complete documentary specification may merge while 079 remains `planned`. All mechanisms remain unproven and unavailable; every architecture-closure proof remains mandatory before readiness and implementation; no live App, JarvisOS proof prototype, governance exception, provider call, readiness promotion, or implementation is authorized.

No proof is waived, weakened, relabelled, or treated as complete.

## 3. Hard invariants

1. `STATUS.md` is the sole live roadmap/status authority.
2. At most one product or implementation front is active repository-wide.
3. Branches, PRs, labels, comments, reviews, checks, workflows, timers, and model text are not authorization.
4. V0 starts only from a maintainer command naming exact repository, spec, slice, base SHA, scope, adapters, and budget policy.
5. Every side-effect event rechecks grant currency, claim, exact GitHub facts, stop state, role capacity, provider policy, idempotency, and canonical reservation; mutation also requires a current reconciled lease.
6. Initial implementation binds verified PR absence. Repairs and review bind the one recorded PR.
7. A PR is created only after a strict non-empty in-scope delta. Verified initial no-change may terminalize without a PR.
8. Exactly one active external request exists at a time. Exactly one reviewer request exists per review attempt.
9. Review round and review attempt are distinct. Fix/re-review advances the round; retrying an invalid or inconclusive reviewer advances only the attempt.
10. Expiry, revocation, security, head change, or human PR action during an accepted request blocks follow-on work but does not strand settlement.
11. Every invalid completed response settles usage/reservation and writes a canonical event. Every ambiguity writes a halt. Every pre-call denial writes a zero-call blocked event.
12. Gate failure destinations are selected by disjoint predicates.
13. Gates and reviews are exact-head evidence; head change invalidates them.
14. Reviewer cannot mutate; implementer cannot supply authoritative review.
15. Automated actors cannot merge, auto-merge, force-push, delete protected refs, change settings/secrets, or bypass rulesets.
16. Open PRs are never silently abandoned: PR-bound terminal abandonment requires the PR already closed by the maintainer.
17. Revocation or expiry never clears a security, integrity, or ambiguity halt.
18. Safety dominates liveness.

## 4. Architecture

The selected dispatcher is an installed GitHub App operated by a stateless Python 3.11 FastAPI/ASGI service with a GitHub REST/Git Data client and PostgreSQL 16.

PostgreSQL is non-authoritative and may store delivery IDs/digests, queue jobs, bounded retries, cached projections, provider correlations, notifications, and health. It never owns the sole grant, claim, lease, PR binding, gate/review result, request settlement, reservation, terminal outcome, or release.

One OCI image and multiple identical replicas are permitted. Redis, agent frameworks, vector databases, browser automation, and a second orchestrator are excluded.

The service is outside JarvisOS runtime and shares neither product SQLite, runtime egress state, provider secrets, nor `C:\JarvisOS` data.

Canonical authority lives on protected branch `jarvis-control` in one file:

`.jarvis/development-loop/authority.json`

Comments, checks, workflow runs, database rows, and dashboards are rebuildable projections.

## 5. Canonical encoding and integrity

`authority.json` uses deterministic UTF-8 JSON: sorted keys, compact separators, UTC `Z` timestamps, integer money/counters/durations/sizes, no float/NaN/infinity, and lowercase SHA-256 identifiers.

Top-level v1:

```json
{
  "schema_version": 1,
  "repository": {
    "repository_id": 0,
    "full_name": "owner/repo",
    "default_branch": "master",
    "control_branch": "jarvis-control"
  },
  "sequence": 0,
  "snapshot": {},
  "snapshot_digest": "sha256:...",
  "events": []
}
```

Every event binds sequence, deterministic event ID, closed type, timestamp, effective actor/role, idempotency key, previous digest, payload/digest, and event digest.

Identical duplicate input is a no-op returning the existing event. Same key with different bytes is an integrity failure. Sequence and Git ancestry, not timestamps, own order.

Both event hash chain and linear `jarvis-control` ancestry must validate. Missing, altered, reordered, duplicated, forked, force-pushed, or non-linear history causes `control_integrity_failure` and zero external side effects. V1 has no compaction and halts before event 4097 or 2,000,000 canonical bytes.

## 6. Closed IDs, roles, states, and snapshot

### 6.1 IDs and roles

Control-App-derived prefixes: `run_`, `grant_`, `claim_`, `lease_`, `pr_`, `gates_`, `review_`, `finding_`, `fix_`, `provider_`, `human_`. Models/providers never choose authoritative IDs.

Closed roles: `maintainer`, `control`, `implementer`, `reviewer`, `gate_collector`, `system_reconciler`. Effective credentials determine role.

### 6.2 States

- `idle`
- `authorized`
- `claimed`
- `implementing`
- `awaiting_pr`
- `awaiting_gates`
- `awaiting_review_dispatch`
- `reviewing`
- `fix_required`
- `awaiting_re_review_dispatch`
- `re_reviewing`
- `awaiting_maintainer`
- `terminal`
- `halted`

### 6.3 Terminal outcomes

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `authorization_expired`
- `abandoned_after_human_decision`

A merge record separates `pr_head_at_merge_boundary` from `merge_result_sha`, records merge method, actor, timestamp, prior state, and evidence status. PR head and result SHA are never assumed equal.

### 6.4 Review round and attempt

The snapshot contains:

- `review_round`: starts at 0; increments only after a genuine review-fix cycle or an evidence-backed no-change disposition that requires re-review; maximum 2.
- `review_attempt`: starts at 0 for each round; increments only after a completed invalid or inconclusive review when the maintainer explicitly authorizes another reviewer call on the same head; bounded by total reviewer-call capacity.
- `review_mode`: `initial` or `re_review`.

A gate repair before the first review does not advance `review_round`. Entering a new review round resets `review_attempt` to 0.

### 6.5 Active request and pending stops

At most one `active_request` exists. It binds request ID, kind, role, round, attempt, head, adapter, idempotency key, reservation, and status. It is created before dispatch and cleared only after exact settlement.

The snapshot may contain an ordered `pending_stops` set with closed kinds:

- `security_signal`
- `human_pr_action`
- `work_head_changed`
- `authorization_revoked`
- `authorization_expired`

Any pending stop sets `follow_on_forbidden=true`. Priority after request settlement is:

1. security/integrity/ambiguity -> `halted`;
2. reconciled human PR action -> `terminal`;
3. valid scoped head change -> `awaiting_pr`, invalid/ambiguous -> `halted`;
4. revocation/expiry -> `awaiting_maintainer`.

An invalid or ambiguous work-head observation during an active request is recorded as a pending `work_head_changed` stop with classification `invalid_or_ambiguous`; it cannot move state until the request and reservation settle or are proven safely cancelled.

Multiple pending stops are preserved; the highest-priority result controls state while all overlays remain recorded.

### 6.6 Other snapshot fields

The snapshot binds run, grant/expiry/revocation, claim/lease, branch/head, optional PR/base/head branch/state, ancestry/diff/scope, gates, review round/attempt/mode/head/verdict/findings/dispositions, integer-micro-USD reservations and usage, call counts, next action, primary stop/overlays, outcome, and last completed run.

A repository-scoped security halt additionally binds `security_prior_state`, `security_prior_snapshot_digest`, verified signal identity, remediation requirements, and whether the prior state was `idle`, an active run state, or unreleased `terminal`.

Before PR creation: `pr_number=null`, `pr_expected_absent=true`.

## 7. Authorization lifecycle

Readiness bootstraps one control issue and allow-listed maintainer numeric IDs. Commands are new, exactly formatted, repository/issue/author validated, and rechecked against current facts. Comments are inputs, not authority.

The grant binds repository, three-digit spec, slice, `master` and exact base SHA, normalized allow/deny paths and file/line limits, distinct adapters, budget policy, max fix rounds 0–2, optional expiry within 30 days, and bounded reason. Scope produces `scope_digest`; work branch derives as `jarvis-work/<run_id>`.

No grant is inferred from a row, branch, PR, label, schedule, chat, previous run, or model.

If no request is active, expiry from an active non-halted state records `authorization_expired_no_request` and enters `awaiting_maintainer`; revocation records `authorization_revoked_no_request` and enters `awaiting_maintainer`. From `halted`, `authorization_expired_overlay_recorded` or `authorization_revoked_overlay_recorded` preserves `halted` and the original primary stop while adding the authority overlay.

If a request is active, expiry/revocation appends the matching pending stop and leaves the request response state unchanged until section 11.4 settlement.

Recovery binds exact control head, run, target/action/reason, and reconciles control history, ref, PR, workflows, requests, reservations, usage/cost, lease/grant/overlays, security, and integrity. Security/integrity recovery requires remediation evidence.

Release is allowed only from `terminal` after all actions, reservations, ambiguity, stops, and PR/ref facts reconcile. `front_released` returns to `idle` while preserving history. A later run requires a new grant.

## 8. Claim, work ref, and lease

`claim_acquired` requires current grant, eligible registry/dependencies, repository-wide vacancy, no competing owner/PR/run, exact base, current policies, and no stop. One CAS records claim and initial 60-minute lease. Losers or ambiguity produce zero side effects.

The Control App may create only `refs/heads/jarvis-work/<run_id>` at exact grant base while state/claim/lease match. Existing exact ref is idempotently accepted. The App cannot later update, force-update, delete, or commit. Mismatch/ambiguity halts.

Later engineering writes are implementer-only under lease.

Lease duration is 60 minutes; renewal window is final 20 minutes; one mutation request may be active; renewal cannot alter grant, scope, round, adapter, provider, or budget. Expiry never releases and blocks mutation until reconciliation and canonical renewal.

## 9. Exact-head Git CAS

Every authority transition reads exact control ref/parent/tree/blob, validates schema/chains/snapshot, rereads preconditions, computes one event, creates blob/tree/commit with sole exact parent, and updates ref with `force=false`.

Contents API blob update is forbidden as CAS.

Rejection, timeout, disconnect, or ambiguity permits no external side effect. Re-read ref/ancestry/event ID: exact occurrence means committed, absence means lost, unresolved ambiguity halts. Same idempotency key never creates a different event.

## 10. Dispatch contract

Only `implementation_requested`, `gate_repair_authorized`, `review_fix_authorized`, and `review_dispatch_authorized` authorize model calls.

Every dispatch binds current grant/claim/no stop, `active_request=null`, exact repository/ref/base/head, role/adapter/capacity, provider policy, canonical reservation even at marginal zero, idempotency key, and valid lease/scope for mutation.

Initial implementation additionally binds PR absence. Gate repair/review fix/review dispatch bind the one recorded PR and exact PR head. Review dispatch binds exact eligible gates.

Blocked preconditions append `dispatch_blocked`, release provisional reservation, record exact reason, make zero call, and enter `awaiting_maintainer`, except security/integrity/expiry/revocation use their specific events.

### 10.1 Reviewer single-flight

`review_dispatch_authorized` is allowed only from a review-dispatch state and moves to `reviewing` or `re_reviewing` while creating `active_request`.

The request key derives from repository, run, PR, review round, review attempt, exact head, adapter, and schema version.

Identical replay returns the existing request without another reservation/call. A different key for the same round/attempt/head is an integrity failure. A later call requires a new attempt or new round/head.

## 11. Closed transition system

### 11.1 Main transitions

| State | Event | Predicate | Next | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid command | `authorized` | none |
| `authorized` | `claim_acquired` | section 8/CAS | `claimed` | create/reconcile work ref |
| `claimed` | `work_branch_recorded` | exact ref/base; PR absent | `claimed` | none |
| `claimed` | `work_branch_ambiguous` | ref mismatch/unresolved create | `halted` | none |
| active, no request | `lease_renewed` | current lease/grant/reconciliation/window | same | none |
| active non-terminal, no request, not `halted` | `authorization_expired_no_request` | expiry reached; no higher-priority stop | `awaiting_maintainer` | none |
| active non-terminal, no request, not `halted` | `authorization_revoked_no_request` | valid maintainer revocation; no higher-priority stop | `awaiting_maintainer` | none |
| `halted`, no request | `authorization_expired_overlay_recorded` | expiry reached | `halted` | none |
| `halted`, no request | `authorization_revoked_overlay_recorded` | valid maintainer revocation | `halted` | none |
| dispatch-eligible | `dispatch_blocked` | closed pre-call failure | `awaiting_maintainer` | none |
| `claimed` | `implementation_requested` | initial no-PR dispatch authority | `implementing` | one implementer call |
| `implementing` | `initial_work_head_recorded` | strict descendant, non-empty scope-valid delta | `awaiting_pr` | none |
| `implementing` | `initial_no_change_completed` | deterministic already-satisfied proof | `terminal` | none |
| `implementing` | `initial_no_change_needs_human` | deterministic human-boundary proof | `awaiting_maintainer` | none |
| `implementing` | `initial_no_change_invalid` | valid no-change claim contradicted/unsupported | `halted` | none |
| `implementing` | `implementation_invalid` | completed invalid envelope/head/scope/usage | `halted` | none |
| `implementing` | `repair_work_head_recorded` | repair strict descendant/delta; PR exists | `awaiting_pr` | none |
| `implementing` | `repair_no_change_recorded` | valid repair no-change; PR exists | `awaiting_pr` | none |
| response state | `provider_ambiguous` | unresolved acceptance/result/charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | exact delta/rebind/grant | `awaiting_pr` | create/reconcile PR |
| `awaiting_pr` | `pr_recorded` | one exact open PR/head | `awaiting_gates` | observe/request gates |
| `awaiting_pr` | `pr_needs_human` | deterministic PR conflict | `awaiting_maintainer` | none |
| `awaiting_pr` | `pr_ambiguous` | unresolved PR API/identity/state | `halted` | none |
| `awaiting_gates` | `initial_gates_passed` | exact green gates and `review_mode=initial` | `awaiting_review_dispatch` | none |
| `awaiting_gates` | `re_review_gates_passed` | exact green gates and `review_mode=re_review` | `awaiting_re_review_dispatch` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope source defect | `fix_required` | none |
| `awaiting_gates` | `gate_evidence_needs_human` | missing/stale/cancelled/action-required/required-skipped/policy mismatch | `awaiting_maintainer` | none |
| `awaiting_gates` | `gate_infrastructure_retry_authorized` | first classified infrastructure failure; safe rerun authority exists | `awaiting_gates` | one zero-model rerun |
| `awaiting_gates` | `gate_flaky_or_ambiguous` | second infra failure, inconsistent results, or unclassifiable ambiguity | `halted` | none |
| `awaiting_review_dispatch` | `review_dispatch_authorized` | section 10, unique round/attempt/head | `reviewing` | one reviewer call |
| `awaiting_re_review_dispatch` | `review_dispatch_authorized` | section 10, unique round/attempt/head | `re_reviewing` | one reviewer call |
| `reviewing` or `re_reviewing` | `review_clean` | valid exact-head response; usage settled | `awaiting_maintainer` | presentation only |
| `reviewing` or `re_reviewing` | `review_findings_recorded` | valid findings; usage settled | `fix_required` | triage only |
| `reviewing` or `re_reviewing` | `review_inconclusive` | valid inconclusive; usage settled | `awaiting_maintainer` | none |
| `reviewing` or `re_reviewing` | `review_invalid` | completed invalid response; usage settled | `awaiting_maintainer` | none |
| `fix_required` | `findings_disposed_no_change` | evidence-backed false/superseded; round+1 <=2 | `awaiting_re_review_dispatch` | none |
| `fix_required` | `gate_repair_authorized` or `review_fix_authorized` | section 10 mutation authority and round remains | `implementing` | one repair/fix call |
| `fix_required` | `finding_requires_human` | scope/security/dependency/round boundary | `awaiting_maintainer` | none |
| `awaiting_re_review_dispatch` | `maximum_rounds_reached` | round/call cap exhausted | `awaiting_maintainer` | none |
| PR-bound active, no request | `work_head_changed` | valid scoped descendant | `awaiting_pr` | none |
| PR-bound active, no request | `work_head_ambiguous` | non-descendant/force/scope/concurrency ambiguity | `halted` | none |
| response state with request | `work_head_change_pending` | valid scoped descendant observed | same | settlement only |
| response state with request | `work_head_stop_pending` | non-descendant/force/scope/concurrency ambiguity | same | safe cancellation/settlement only |
| response state with request | `human_pr_action_pending` | reconciled maintainer merge/close observed | same | settlement only |
| response state with request | `authorization_revoked_pending` | valid maintainer revocation | same | settlement only |
| response state with request | `authorization_expired_pending` | expiry reached | same | settlement only |
| PR-bound active, no request | `human_merge_observed` | reconciled human action | `terminal` | none |
| PR-bound active, no request | `human_close_observed` | reconciled human action | `terminal` | none |
| `awaiting_maintainer` | `human_decision_recorded` | section 11.6 | closed target state or `terminal` | none |
| `idle`, active non-terminal, or unreleased `terminal`; no request | `security_halt` | authenticated/verified security signal; preserve prior state/snapshot | `halted` | none |
| `halted`, no request | `security_halt_overlay_recorded` | additional authenticated/verified signal | `halted` | none |
| response state with request | `security_stop_pending` | authenticated/verified security signal | same | safe cancellation/settlement only |
| `halted` | `human_recovery_recorded` | reconciliation/remediation; restore only preserved safe state | preserved safe state or `terminal` | recovery only |
| `terminal` | `front_released` | complete reconciliation; no open PR | `idle` | none |

A PR-bound state contains a recorded PR, including `awaiting_pr` during rebinding, `awaiting_gates`, both review-dispatch/reviewing states, `fix_required`, and PR-bound `awaiting_maintainer`.

### 11.2 Response classification

Mandatory mutually exclusive order:

1. unresolved acceptance/completion/result/charge -> `provider_ambiguous`;
2. completed invalid envelope/schema/bound head/usage/scope/ancestry -> role-specific invalid event;
3. valid initial strict delta -> `initial_work_head_recorded`;
4. valid initial no-change envelope, exact base, zero diff, settled usage -> deterministic verifier selects exactly one initial no-change event;
5. valid repair result -> delta or repair no-change event.

Malformed, wrong-head, usage-invalid, scope-invalid, or ambiguous evidence can never be `initial_no_change_invalid`.

### 11.3 Initial no-change verifier

After a valid no-change envelope is established:

- `initial_no_change_completed`: acceptance conditions already satisfied at the pinned base;
- `initial_no_change_needs_human`: progress requires a specific governance/scope/dependency/permission/secret/destructive decision outside the grant;
- `initial_no_change_invalid`: the no-change claim is contradicted or unsupported by deterministic facts, with no other invalid/ambiguity/security class.

The first terminalizes as `completed_without_pr`; the second enters no-PR `awaiting_maintainer`; the third halts. Provider assertion alone is insufficient. Repair no-change retains the PR and requires gates/re-review.

### 11.4 Pending-stop settlement

If a request is active, security, human PR action, valid or invalid observed head change, revocation, or expiry appends its pending-stop event, remains in the response state, and forbids follow-on work.

Settlement transitions:

- exact valid completion with security pending -> `request_settled_after_security_stop` -> `halted`;
- proven safe cancellation with security pending -> `request_cancelled_after_security_stop` -> `halted`;
- exact valid completion with human PR action pending -> settle usage/head/response, then record factual human outcome -> `terminal`;
- exact valid completion with valid scoped head-change pending -> settle and return `awaiting_pr`;
- exact valid completion with invalid/ambiguous head-change pending -> `request_settled_after_head_ambiguity` -> `halted`;
- proven safe cancellation with invalid/ambiguous head-change pending -> `request_cancelled_after_head_ambiguity` -> `halted`;
- exact valid completion with revocation/expiry pending -> `request_settled_after_authority_stop` -> `awaiting_maintainer`;
- proven safe cancellation with revocation/expiry -> `request_cancelled_after_authority_stop` -> `awaiting_maintainer`;
- completed invalid output -> role-specific invalid-after-stop event; implementer/security invalidity halts, reviewer invalidity without security enters `awaiting_maintainer`;
- unresolved result/charge -> `provider_ambiguous` -> `halted`.

Every settlement clears `active_request`, finalizes/releases reservation, records safe digests and actual usage, and preserves all pending-stop overlays. Outputs settled under a stop are forensic evidence only and cannot authorize continuation.

### 11.5 Completed invalid responses

Before an invalid event, finalize actual usage, release unused reservation, store safe request/response digests and exact invalid class, clear `active_request`, prove no retry/second charge is authorized, and invalidate output-derived authority.

Implementation invalidity halts; reviewer invalidity enters `awaiting_maintainer` unless a security/integrity signal requires halt.

### 11.6 Human decision, review retry, and PR closure

`human_decision_recorded` binds an allow-listed maintainer, exact control head and repository/ref/PR facts, no active request or reservation ambiguity, current overlays, closed action, target, and reason.

Closed actions:

- `resume_pre_pr` -> `claimed` only with no PR/delta, current grant/policies, no stop overlay, and renewed lease;
- `resume_pr_reconciliation` -> `awaiting_pr` only after the exact deterministic PR conflict is resolved;
- `resume_gates` -> `awaiting_gates` only with exact PR/head and valid target evidence;
- `resume_review_pre_dispatch` -> corresponding review-dispatch state only when the stop occurred before any reviewer request for the current round/attempt was authorized;
- `retry_review_next_attempt` -> corresponding review-dispatch state only after a completed `review_invalid` or `review_inconclusive`, exact head/gates unchanged, reviewer-call capacity remains, and `review_attempt` increments by one;
- `request_pr_close` -> remain `awaiting_maintainer`; creates only a human-decision request, never closes the PR automatically;
- `abandon` or `supersede` -> `terminal` only when no PR exists or the recorded PR is already closed and reconciled;
- `terminalize_expired_or_revoked` -> matching terminal outcome after all accepted requests settle.

An open PR makes `abandon` and `supersede` ineligible. The maintainer must close it externally; `human_close_observed` then terminalizes. Release also requires no open PR.

`retry_review_next_attempt` never reuses the completed request key. It increments `review_attempt`, while `review_round` and head remain unchanged. A new fix/re-review round increments `review_round` and resets attempt to zero.

For a repository-scoped security halt, `human_recovery_recorded` may restore only the exact preserved prior state after remediation evidence and complete reconciliation. Recovery to `idle` cannot synthesize a grant or claim; recovery to unreleased `terminal` cannot release it; recovery to an active run state remains subject to grant, lease, PR, head, reservation, provider, and stop checks.

Resume is forbidden for expired/revoked grants, unresolved security/integrity/provider ambiguity, stale heads, active requests, or scope expansion.

### 11.7 Gate classification

Gate outcomes are disjoint:

- reproducible in-scope source/test defect -> `gate_defect_reproduced`;
- missing, stale, cancelled, action-required, required-but-skipped, or policy-definition mismatch -> `gate_evidence_needs_human`;
- first independently classified infrastructure failure -> `gate_infrastructure_retry_authorized` only if the readiness-approved gate policy and credential permit one zero-model rerun;
- second infrastructure failure, inconsistent rerun conclusions, suspected flake, or unclassifiable evidence -> `gate_flaky_or_ambiguous`.

If safe rerun authority is not configured, the first infrastructure failure uses `gate_evidence_needs_human`, not an invented rerun.

### 11.8 Human PR outcomes and merge SHA semantics

The maintainer may merge or close a recorded PR from any PR-bound state. If a request is active, record the pending human action and settle it first; unresolved settlement halts and recovery later records the already-observed PR outcome.

Merge records PR head at merge boundary, separate merge-result SHA, method, actor, timestamp, prior state, and head-bound evidence.

`current_clean` requires the PR head at the merge boundary to equal the exact current gated/clean-reviewed head with no later invalidation. Merge-result SHA may differ under merge, squash, or rebase. Otherwise evidence is `stale_or_incomplete`; outcome remains factually `merged_by_maintainer` without a system-ready claim.

Close/supersede records facts and creates no replacement PR.

### 11.9 PR lifecycle and head changes

PR creation is eligible only after strict non-empty initial delta and is forbidden after initial no-change outcomes.

`pr_creation_authorized` binds repo/run/branch/head/base/scope/version.

- no PR -> create one non-draft PR;
- one exact open PR -> reuse;
- deterministic duplicate/mismatch/closed conflict -> `pr_needs_human`;
- unresolved API/identity/fork/state -> `pr_ambiguous`;
- timeout -> search before retry; never create a second PR.

`pr_recorded` binds PR ID/repository/base/head branch/current head/operation/state. Gates/review are forbidden before it. Every repair result rebinds the same PR.

Any PR-head change invalidates gates/review/presentation. With no active request, a valid scoped descendant returns to `awaiting_pr`; invalid/ambiguous movement halts. With an active request, a valid change records `work_head_change_pending`; an invalid or ambiguous change records `work_head_stop_pending`; both preserve the response state until section 11.4 settlement.

## 12. Branch and scope

One work branch; App creates once; implementer writes later; no automated force/delete; base `master`; forks unsupported.

Before/after mutation verify normalized paths, deny precedence, file/line limits, linear ancestry, submodules, LFS, symlink escapes, binaries, secret risks, and scope digest.

Denied absent separate authority: `AGENTS.md`, workflows/CODEOWNERS, settings/rulesets, secrets/keys/tokens/environment files, protected conformance tests, vendored dependencies/lockfiles, and canonical authority file.

## 13. Deterministic gates

Readiness freezes exact checks, action pins, and path conditions: registry, manual-review offline boundary, BLUECAD license boundary, Ruff, full Pytest, canary, frontend build when needed, strict real-tool proof when relevant, and 079 service unit/integration/conformance/reconstruction tests.

Eligible evidence is exact repository/head/policy success and not stale, required-but-skipped, cancelled, action-required, or superseded. Gate failure handling follows section 11.7. Tests/workflows may not be weakened.

## 14. Reviewer and findings

Reviewer credentials are read-only, effectively distinct from implementer, and have no write, dispatch, merge, settings, secret, ref-delete, or ruleset authority.

Review request binds repository, spec, slice, scope/non-goals, base/head, diff, PR, gates, round, attempt, prior findings/fixes, content digest, provider policy, reservation, and idempotency.

Response contains exact head, verdict `clean|findings|inconclusive`, bounded summary, and findings with severity/category/path/line/claim/reproduction/resolution. Reviewer cannot provide authoritative IDs. Control App validates/normalizes and derives each `finding_<32 hex>` from round, attempt, head, normalized finding digest, and occurrence index. Model `finding_id` is invalid.

Maximum 50 findings and 2,000 characters per text field. Malformed, oversized, wrong-head, unknown-field, or non-JSON output uses `review_invalid` after usage settlement. Inconclusive uses `review_inconclusive`. P0/P1 block; P2 only when independently reproduced as a binding violation; P3 advisory.

## 15. Findings and bounded rounds

Closed dispositions: `reproduced`, `accepted_without_reproduction`, `false_positive`, `superseded`, `needs_human`, all evidence-bound.

Review round starts 0; maximum fix/re-review round 2. Reviewer calls maximum 3 total; implementer calls maximum 3 total; one fix per negative round.

A code-changing review fix or an evidence-backed no-change disposition increments review round and resets review attempt to 0. Gate repair before initial review does not increment review round. Every code change returns through PR/gates/review. Negative result after round 2 stops. Scope/destructive/governance/secret/dependency expansion stops.

## 16. Adapters and execution-spine block

Adapter requests bind repository/install, branch/head, conditional PR, spec/slice, scope/non-goals, task/findings, provider/budget/reservation/idempotency. Responses bind request/status, resulting head/no-change, safe digests/summary, usage/cost/idempotency/error.

Initial implementation permits `pr_number=null` only under section 10. Repair/review require the recorded PR.

Adapters cannot change authority; implementer writes work branch only; neither actor merges/approves/force-deletes/settings/secrets/control. Accepted ambiguity halts without retry absent exact reconciliation.

Current `AGENTS.md` requires all AI calls through product `run_ai_task` and `ai_jobs`; the selected service does not share product SQLite/egress. Live 079 calls are blocked.

The proposed v0 governance route is a narrow repository-development exception allowing approved 079 adapters outside the product spine only with committed grant, claim, exact branch/head, conditional PR, scope, identity, provider, reservation, idempotency, and durable usage/cost evidence. It requires a separate `AGENTS.md` PR and readiness; otherwise amend this spec to use an authenticated product execution-spine boundary.

## 17. Spend

Separate development budget uses integer micro-USD and defaults zero. Hard maxima: 5,000,000/request; 20,000,000/run; 25,000,000/UTC day; 100,000,000/month. `cost_unknown` stops.

Every model call reserves amount, quota, and call count before dispatch. Missing reservation, stale price, exceeded cap/capacity, unknown cost/quota, or fallback means `dispatch_blocked` and zero call. Final usage finalizes/releases. No fallback. Marginal zero requires current plan/entitlement/quota/timestamp. Hosting/Actions tracked separately.

## 18. Content and secrets

External material is limited to exact spec/scope/diff/findings/PR when present/gates. Exclude secrets, credentials, environment values, keys, tokens, headers, unrelated records. All repository/model text is untrusted and cannot change authority. Deterministic policy constructs requests. No raw provider body enters authority; safe digests/summaries/IDs/usage/cost only. S4/secret content denied absent later egress spec.

## 19. Permissions and rulesets

Candidate App: metadata read; contents read/write; PR read/write; checks/status/Actions read; issues read/write. Actions write only if readiness proves exact need. No administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, or ruleset bypass.

Capability wrapper allow-lists repository/endpoint/method/ref/path/state/schema and audits denials. Separate Control/implementer/reviewer/maintainer credentials.

Rulesets: master requires PR/checks and human merge, no force/delete/bypass; control allows App/human recovery only, linear, no force/delete; work branch allows App create-only then implementer/maintainer write, reviewer read-only, no automated force/delete, base master. Abuse tests cover all prohibited actions.

## 20. Webhook, queue, and service

Events: new issue comments, pushes on master/control/work, PR/review/review-comment/workflow-run, installation suspension/deletion. Edited authorization comments ignored.

Webhook verifies raw-body signature constant-time before JSON. Missing/invalid requests receive auth failure, rate limiting, redacted logging, and create no trusted delivery, queue item, canonical event, security signal, or halt.

Authenticated processing validates installation/repository/event, stores delivery digest, acknowledges within 10 seconds, queues reconciliation, and performs no request-thread side effect.

Verified security signals include signed delivery-ID digest mismatch, identity contradiction, history tamper, credential misuse/unauthorized API success, scope/secret escape, or independently confirmed compromise. Security transitions follow section 11.1 and 11.4 from every unreleased repository state, including `idle` and unreleased `terminal`.

Endpoints are health, readiness, and webhook only. Queue is operational; duplicate jobs converge; reads retry bounded; side-effect retry requires committed authority/proven idempotency; webhook order untrusted.

Retention: delivery 30 days, queue/projections 90 days, logs 30 days; no raw model/secrets/headers. Canonical RPO zero, DB RPO 24h, RTO target 4h; GitHub uncertainty stops.

## 21. Presentation

One non-authoritative check, sticky PR comment, control-issue status, and weekly digest. Idempotent after canonical changes. Between weekly reviews notify only human decision, verified security signal, or budget overrun/disabled authority. Digest Europe/Rome Monday 08:00, at most weekly, omitted without change, never grants authority.

## 22. Security and supply chain

Use short-lived tokens, managed secrets, rotation, immutable pins/digests, SBOM, dependency/container scans, outbound allow-listing, repository/SHA validation, and no untrusted fork with write/secrets. Webhook processing never executes PR code. Invalid unsigned traffic does not halt; verified security evidence does from any unreleased state, with active-request settlement when required and exact prior-state preservation for recovery.

## 23. Verification

### 23.1 Offline tests

Prove canonical encoding/chains/reconstruction/idempotency/schema; every transition edge; grant/expiry/revocation with and without active requests; explicit no-request authority-stop events and halted overlays; pending-stop priority/settlement including valid and ambiguous head changes; repository-scoped security halt/recovery from idle, active, and unreleased terminal states; recovery/release; claim/lease/ref; initial PR absence/delta/no-change classifications; completed invalid settlement; no-PR human decisions; PR closure before abandonment; gate predicates and one infrastructure rerun; review round versus attempt; concurrent reviewer single-flight; review retry next-attempt; every reservation/capacity/lease check; exact-head invalidation; provider ambiguity; deterministic finding IDs; human outcomes/merge SHA semantics; release; invalid webhook; inactivity.

### 23.2 Disposable proofs before readiness

All architecture proofs remain mandatory, including CAS races/timeouts/replay/reconstruction/tamper; lease/ref; initial PR/no-change; classification disjointness; no-PR decisions; PR closure and idempotency; gate predicates/rerun; reviewer single-flight and retry attempts; pending authority/security/head/human stops with request settlement; ambiguous head-change cancellation and settlement before halt; credential abuse; security halt/recovery from idle and terminal; head/human/merge semantics; invalid output settlement; provider ambiguity/finding IDs/release; fork/prompt injection; cost/duplicate charge; outage/kill switches; invalid unsigned no halt; inactivity/no duplicate calls.

### 23.3 Repository/conformance

Implementation passes repository Pytest/Ruff/status/canaries and deterministic service tests; no live/paid/production CI. Readiness freezes maintainer-owned vectors for every authority property. Implementation agents cannot weaken them.

## 24. Governance, rollout, readiness, and kill switches

### 24.1 Required `AGENTS.md` amendment

A separate PR must amend manual/explicit-only development dispatch and the hard `run_ai_task`/`ai_jobs` invariant with the narrow 079 exception described in section 16. It continues to forbid automatic selection, merge, priority, bypass, force/delete, settings/secrets, destructive actions, scope expansion, fallback, or work after any stop. Until governance/readiness merge, no live calls.

### 24.2 Rollout

1. Human merge of this PR accepts the documentary full spec and section 2.1 ordering amendment; 079 remains `planned` and mechanisms unavailable.
2. Merge dormant governance amendment.
3. Build disposable/separate proof prototype with fake actors and zero paid calls.
4. Execute every architecture proof before readiness.
5. Optional explicitly approved read-only JarvisOS shadow: no claim/ref/PR/workflow/provider writes.
6. Dated readiness records host/App/actors/rulesets/adapters/prices/caps/proofs/vectors/owners/rollback and only then `ready`.
7. One bounded implementation PR after readiness.
8. Separate operational grant for one low-risk docs-only activation with human merge.
9. Broader use separately approved after first-run evidence.

No implementation skeleton enters JarvisOS while planned.

### 24.3 Kill switches and readiness evidence

Canonical halt, App suspension, key/secret/provider revocation, service/queue stop, caps zero, dispatch-workflow disable, and human recovery. Rollback never force-pushes or erases.

Readiness proves merged dependencies/architecture/full spec/governance; every proof; exact permissions/rulesets/wrapper/IDs; execution exception; all closed transition and pending-stop behavior; reviewer single-flight/attempts; gate predicates; PR closure; abuse denials; host/database/secrets/adapters/pricing/caps/gates/vectors/owners/first slice; no unresolved P0/P1. Only readiness sets `ready`.

## 25. Compatibility

No product SQLite migration. Product execution/budget/Hermes/MemoryStore/BLUECAD/events do not become authority. Hosted DB rebuildable. Bootstrap new protected control branch explicitly; no chat/old PR/ref imported. Existing work needs exact grant/reconciliation and normally fresh branch. Review remains manual until governance/readiness. Authority versions require additive migration proof. Force-push is never migration.

## 26. Likely implementation scope

After readiness: `services/devloop/`, pinned service manifest/container, fake fixtures, secret-free deployment docs, normal `STATUS.md` transition, CI only for offline tests. Not in implementation: `AGENTS.md` amendment, live App/settings/rulesets/secrets, credentials/account data, product runtime, Hermes/MCP/MemoryStore/BLUECAD/process kernel/078. Dependencies pinned/justified/scanned/service-limited; no agent framework.

## 27. Non-goals

No automatic next-spec selection; simultaneous fronts/branches/actors/PRs; autonomous merge/approval/release/deploy/priority/governance/settings; force/delete/history rewrite/protected-test mutation; arbitrary shell; provider fallback/bidding/swarm; unbounded loops; untrusted fork execution; replacement of runtime 059b/Hermes/Actions; raw model/secret canonical storage; outage liveness guarantee; or 078/other frozen work.

## 28. Definition result

Ready for maintainer merge decision when the diff remains one planning document, 079 remains `planned`, section 2.1 remains proposed until merge, transitions and predicates are closed, review requests are single-flight by attempt, review retry advances attempt, PR-bound abandonment requires closure, gate outcomes are deterministic, security signals have repository-wide no-request and active-request transitions, pending calls settle before every state departure including ambiguous head changes, every proof remains a readiness blocker, execution-spine conflict remains blocked, no mechanism is claimed operational, no runtime/workflow/App/provider/secret/ruleset/dependency/setting changes, exact-head gates pass, no current P0/P1 remains, and the PR stops for human merge.

Merge does not authorize governance, proofs against live JarvisOS, readiness, implementation, provider calls, or automated merge.