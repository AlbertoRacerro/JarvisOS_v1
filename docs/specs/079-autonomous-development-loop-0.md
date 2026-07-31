# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: proposed full specification; it becomes the merged full-spec authority only after an explicit human merge. `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Pinned full-spec baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Evidence and predecessor documents:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one already and explicitly authorized JarvisOS repository-development slice to continue safely across agent-session termination without repeated conversational `continue` prompts.

The v0 control plane may:

- reconstruct durable authority from GitHub;
- claim exactly one repository-wide development front;
- create one derived work branch at one exact authorized base;
- invoke one bounded implementer on that branch before a PR exists;
- after a real branch delta exists, create or reconcile exactly one pull request idempotently;
- terminalize a verified initial no-change result without inventing an empty PR;
- record every invalid, blocked, ambiguous, or human-required path canonically rather than leaving a state suspended;
- bind deterministic gates and review to an exact PR head;
- perform at most two bounded fix/re-review rounds;
- recover from duplicate delivery, process restart, stale local state, and ambiguous API responses;
- truthfully record human merge or close actions even when they occur before system-prepared readiness;
- release a fully reconciled terminal front back to canonical `idle` without erasing history.

The control plane may never merge, enable auto-merge, approve authoritatively, change roadmap priority, infer authorization from repository activity, create a second active front, or turn model output into authority.

## 2. Full-spec and sequencing boundary

This document freezes the proposed v0 contract for canonical state and event integrity; authorization, expiry, revocation, recovery, terminalization, and release; repository-wide claim and lease; initial implementation before PR creation; verified no-change terminalization; exact branch/PR lifecycle; gates and review; adapters; blocked/invalid/ambiguous failure paths; provider, spend, content, secret, and permission boundaries; webhook, queue, notification, retention, proofs, rollout, kill switches, and compatibility.

This PR does not install or configure an App, service, database, queue, branch, ruleset, workflow, secret, provider route, or dependency; modify `AGENTS.md` or `STATUS.md`; invoke a model or paid service; or authorize readiness, implementation, repository settings, merge, or auto-merge.

Current `AGENTS.md` remains binding. Live development-agent dispatch is impossible until the separate governance amendment in section 24 reconciles both the execution-spine invariant and the manual/explicit-only review rules.

### 2.1 Proposed documentary sequencing amendment

The merged architecture/evidence closure labelled the disposable-repository concurrency, CAS, credential, cost, PR, and recovery proofs mandatory before full-spec promotion.

The maintainer subsequently instructed the full-spec drafting step to proceed. This PR therefore presents a narrow sequencing amendment for explicit human approval:

- before this PR is merged, the prior architecture-closure ordering remains authoritative;
- merging this PR accepts only that the complete documentary full specification may be merged while 079 remains `planned`;
- every mechanism remains unproven, unavailable, and fail-closed;
- every mandatory architecture-closure proof remains a hard blocker before dated readiness and implementation;
- no governance exception, live App, JarvisOS proof prototype, provider call, readiness promotion, or implementation is authorized by this ordering change.

The amendment changes only the order of documentary consolidation versus isolated proof execution. It does not waive, weaken, relabel, or claim completion of any proof.

## 3. Binding invariants

1. `docs/specs/STATUS.md` is the sole live roadmap and status authority.
2. At most one product or implementation front is active repository-wide.
3. A branch, PR, label, review, check, workflow, timer, comment, or model message is not authorization.
4. V0 starts only from a maintainer-authored command naming exact spec, slice, base SHA, scope, adapters, and budget policy.
5. Every side-effect event rechecks grant currency, claim ownership, exact GitHub facts, stop state, role capacity, provider policy, and canonical reservation; mutation additionally requires a valid reconciled lease.
6. Initial implementer dispatch binds verified PR absence; all repair and review dispatches bind the one recorded PR.
7. A PR is created only after a strict non-empty in-scope branch delta. A verified initial no-change result terminalizes without a PR.
8. Every completed invalid response finalizes usage and writes a canonical failure event. Every ambiguous response writes a canonical halt event. Every deterministic pre-dispatch denial writes a canonical blocked event with zero external call.
9. Deterministic gates and advisory review inform readiness; maintainer alone owns merge.
10. Reviewer credentials cannot mutate code; implementer credentials cannot provide authoritative review.
11. Automated actors cannot merge, auto-merge, force-push, delete protected refs, change settings/secrets, or bypass rulesets.
12. Repository-development provider authority is separate from runtime policy 059b.
13. Planned, blocked, cancelled, dependency-incomplete, expired, or revoked work never starts or continues automatically.
14. Lease expiry, grant expiry, inactivity, process death, or a timer never releases ownership.
15. Any work-head change invalidates all prior head-bound gates, review, and presentation evidence.
16. Human PR actions are recorded factually from every PR-bound active state; observation never retroactively manufactures a clean verdict.
17. Revocation or expiry never clears an existing security, integrity, or ambiguity halt.
18. Safety dominates liveness; indefinite inactivity is valid.

## 4. Selected architecture

### 4.1 Control service

The primary dispatcher is an installed GitHub App operated by a small stateless Python 3.11 FastAPI/ASGI service with a GitHub REST/Git Data client and PostgreSQL 16 for non-authoritative queueing, delivery deduplication, retries, and projections.

One OCI image and multiple identical replicas are permitted. Redis, agent frameworks, vector databases, browser automation, and a second orchestration engine are excluded.

The service is outside JarvisOS product runtime and does not share JarvisOS SQLite, runtime egress state, runtime provider secrets, or `C:\JarvisOS` data.

### 4.2 Canonical state

Canonical authority lives on protected branch `jarvis-control` in exactly one file:

`.jarvis/development-loop/authority.json`

Comments, checks, workflow runs, PostgreSQL rows, dashboards, and digests are rebuildable non-authoritative projections.

### 4.3 PostgreSQL

PostgreSQL may store delivery IDs/digests, queued reconciliation jobs, bounded retries, cached projections, provider correlation, notification deduplication, and service health/audit summaries.

It never owns the sole grant, claim, lease, PR binding, gate/review verdict, finding disposition, reservation, terminal outcome, or release. Total database loss may delay work but cannot alter authority.

## 5. Canonical encoding and integrity

`authority.json` uses deterministic UTF-8 JSON: sorted keys, compact separators, UTC `Z` timestamps, integer money/counters/durations/sizes, no float/NaN/infinity, and lowercase SHA-256 identifiers.

Top-level v1 envelope:

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

Every event binds monotonically increasing sequence, deterministic event ID, closed event type, timestamp, effective actor/role, idempotency key, previous digest, payload/digest, and event digest.

Identical duplicate input is a no-op returning the existing event. Same idempotency key with different bytes is an integrity failure. Sequence and Git ancestry, not timestamps, own order.

Both the in-file hash chain and linear `jarvis-control` Git ancestry must validate. Missing, reordered, altered, duplicated, forked, force-pushed, or non-linear history causes `control_integrity_failure` and zero external side effects. V1 has no compaction; halt before event 4097 or 2,000,000 canonical bytes.

## 6. Closed identifiers, roles, states, outcomes, and failure classes

### 6.1 IDs and roles

Deterministic ID prefixes: `run_`, `grant_`, `claim_`, `lease_`, `pr_`, `gates_`, `review_`, `finding_`, `fix_`, `provider_`, `human_`. Control App derives authoritative IDs; models/providers do not choose them.

Closed roles: `maintainer`, `control`, `implementer`, `reviewer`, `gate_collector`, `system_reconciler`. Effective credentials determine role.

### 6.2 States

- `idle`
- `authorized`
- `claimed`
- `implementing`
- `awaiting_pr`
- `awaiting_gates`
- `awaiting_review`
- `fix_required`
- `awaiting_re_review`
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

`completed_without_pr` is allowed only for the first implementer request after section 11.3 verification. It never bypasses a required repair, review, or PR.

A human-merge event separately records `prepared_state_at_human_action`, `pr_head_at_merge_boundary`, `merge_result_sha`, `merge_method`, actor, timestamp, and `evidence_status` (`current_clean`, `stale_or_incomplete`, or `not_applicable`). PR head and merge-result SHA are never assumed equal.

### 6.4 Closed deterministic failure classes

Pre-dispatch blocked classes:

- `provider_disabled`
- `cost_unknown`
- `spend_cap_exceeded`
- `role_call_capacity_exceeded`
- `secret_unavailable_or_changed`
- `grant_not_current`
- `lease_not_current`
- `pr_not_current`

Completed invalid-output classes:

- `schema_invalid`
- `oversized_output`
- `wrong_head_output`
- `scope_invalid_output`
- `usage_invalid`
- `deterministic_no_change_rejected`

Ambiguity/integrity classes:

- `provider_ambiguous`
- `work_head_ambiguous`
- `work_branch_ambiguous`
- `pr_ambiguous`
- `control_integrity_failure`
- `security_signal`

A precise class is mandatory; generic `unknown`, `provider_error`, or `failed` is forbidden when a closed class applies.

## 7. Authorization lifecycle

### 7.1 Maintainer commands and grant

Readiness bootstraps one control issue and allow-listed maintainer numeric IDs. Commands must be newly created, exactly formatted, repository/issue/author validated, and rechecked against current SHAs/facts. Comments are inputs, not authority.

The grant binds repository ID, three-digit spec, bounded slice, `master` and exact base SHA, normalized allow/deny globs with deny precedence, file/line caps, distinct approved adapter IDs, budget policy, max fix rounds 0–2, optional future expiry within 30 days, and bounded reason. Scope produces `scope_digest`; work branch is derived as `jarvis-work/<run_id>`.

V0 never infers a grant from a row, branch, PR, label, schedule, chat, prior run, or model recommendation.

### 7.2 Currency, expiry, and revocation

Every branch/PR/workflow/provider/reservation side-effect event proves grant present, unrevoked, and unexpired at commit time.

At expiry:

- no new side-effect event;
- from non-halted state, `authorization_expired` -> `awaiting_maintainer`;
- from `halted`, `authorization_expired_while_halted` -> `halted`, preserving primary stop and adding expiry overlay;
- accepted work is reconciled without follow-on work;
- ownership/history are never released automatically.

Revocation:

- from non-halted state, `authorization_revoked` -> `awaiting_maintainer` or factually justified terminal;
- from `halted`, `authorization_revoked_while_halted` -> `halted`, preserving primary stop and adding revoked overlay.

Revocation never acts as recovery or clears a halt.

### 7.3 Recovery and release

Recovery binds exact control head, run, action (`resume` or `terminalize`), target/outcome, reason, and independent reconciliation of repository, control history, work ref, PR, workflows, provider requests, reservations, usage/cost, lease/grant overlays, security, and integrity. Security/integrity recovery references remediation evidence.

Release is allowed only from `terminal` after all external actions, reservations, cancellations, provider ambiguity, integrity/security stops, PR/ref facts, and overlays reconcile. For `completed_without_pr`, it proves no PR and no branch delta.

`front_released` returns to `idle` while preserving complete run, outcome, PR/ref when present, findings, usage/cost, event chain, and Git history. Duplicate release is no-op; later run requires a new grant.

## 8. Canonical snapshot

Snapshot binds state/run, grant/expiry/revocation/overlays, claim/lease, work branch/head, optional PR/base/head branch/state, ancestry/diff/scope, gates, review round/head/identity/request/verdict/findings/dispositions, integer-micro-USD reservations and finalized/released usage, role call counts, next action, primary stop/overlays, terminal outcome, and last completed run.

Before PR creation, `pr_number=null` and `pr_expected_absent=true` are explicit.

## 9. Claim, work ref, and lease

`claim_acquired` requires current grant, eligible registry/dependencies, repository-wide vacancy, no competing owner/PR/run, exact base, current policies, and no stop. One CAS records claim and initial 60-minute lease. Losers/ambiguity produce zero side effects.

After claim, Control App may create only `refs/heads/jarvis-work/<run_id>` at exact grant base while state/claim/lease match. Existing exact ref is idempotent. App cannot later update/force/delete/commit. A mismatched or ambiguous operation writes `work_branch_ambiguous` and halts. Later engineering writes are implementer-only under lease.

Lease duration is 60 minutes, renewal window final 20 minutes, one mutation request at a time, and renewal cannot alter grant/scope/round/adapter/provider/budget. Expiry never releases; it records pending reconciliation and blocks mutation until facts reconcile and renewal commits.

## 10. Exact-head Git CAS

Every authority transition reads exact control ref/parent/tree/blob, validates schema/chains/snapshot, rereads preconditions, computes one event, creates blob/tree/commit with sole exact parent, and updates ref with `force=false`.

Contents API blob update is forbidden as CAS. Rejection, timeout, disconnect, or ambiguity permits no external side effect. Reread ref/ancestry/event ID: event present exactly once means committed, absent means lost, unresolved ambiguity halts. Same idempotency key never creates a different event.

## 11. Closed state machine

### 11.1 Dispatch authority and blocked dispatches

Only `implementation_requested`, `gate_repair_authorized`, `review_fix_authorized`, and `review_dispatch_authorized` authorize model calls.

Every dispatch event binds current grant/claim/no-stop, exact repository/work ref/base/head, role identity/capacity, adapter/provider policy, canonical cost/quota reservation even at marginal zero, idempotency key, and valid lease/scope for mutation.

Conditional PR binding:

- initial `implementation_requested` requires `pr_number=null`, `pr_expected_absent=true`, and live proof no PR exists for the derived branch;
- gate repair, review fix, and every review dispatch require the recorded PR and exact current PR head;
- no other no-PR model dispatch is permitted.

When deterministic preconditions fail before any call, append `dispatch_blocked`, finalize or release any provisional reservation, record the precise blocked class, make zero external call, and enter `awaiting_maintainer`. Expiry, revocation, security, or integrity use their more specific events instead.

### 11.2 Transition table

| Current state | Event | Binding preconditions | Next state | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid maintainer command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9 and CAS | `claimed` | create/reconcile work ref |
| `claimed` | `work_branch_recorded` | exact derived ref at base; PR absent | `claimed` | none |
| `claimed` | `work_branch_ambiguous` | ref mismatch or unresolved create outcome | `halted` | none |
| active non-halted | `lease_renewed` | current grant/lease/reconciliation/window | same | none |
| dispatch-eligible non-halted state | `dispatch_blocked` | closed pre-dispatch failure; no call made | `awaiting_maintainer` | none |
| `claimed` | `implementation_requested` | section 11.1 initial no-PR authority | `implementing` | one initial implementer request |
| `implementing` | `initial_work_head_recorded` | initial request; strict descendant; non-empty in-scope diff | `awaiting_pr` | none |
| `implementing` | `initial_no_change_completed` | section 11.3 verified no-change | `terminal` | none |
| `implementing` | `initial_no_change_needs_human` | section 11.3 closed human-boundary rejection | `awaiting_maintainer` | none |
| `implementing` | `initial_no_change_invalid` | malformed, unverifiable, ambiguous, integrity, scope, head, or usage rejection | `halted` | none |
| `implementing` | `implementation_invalid` | completed response invalid after usage reconciliation | `halted` | none |
| `implementing` | `repair_work_head_recorded` | repair/fix; strict descendant; in-scope diff; PR exists | `awaiting_pr` | none |
| `implementing` | `repair_no_change_recorded` | repair/fix; exact prior head; PR exists; bounded evidence | `awaiting_pr` | none |
| `implementing` | `provider_ambiguous` | accepted unresolved request or charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | delta or PR rebind; exact branch/head/base; grant current | `awaiting_pr` | create/reconcile one PR |
| `awaiting_pr` | `pr_recorded` | one matching open PR and exact head | `awaiting_gates` | observe/request gates only |
| `awaiting_pr` | `pr_needs_human` | deterministic duplicate/mismatch/closed-state conflict | `awaiting_maintainer` | none |
| `awaiting_pr` | `pr_ambiguous` | unresolved API, identity, fork, or state ambiguity | `halted` | none |
| `awaiting_gates` | `gates_passed` | all required exact-head gates green | `awaiting_review` or `awaiting_re_review` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope defect | `fix_required` | none |
| `fix_required` | `gate_repair_authorized` | section 11.1 PR/lease/dispatch authority | `implementing` | one repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale/flaky/cancelled/missing/action-required/infra | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` or `awaiting_re_review` | `review_dispatch_authorized` | section 11.1 PR/gate/review authority | same | one reviewer request |
| `awaiting_review` or `awaiting_re_review` | `provider_ambiguous` | accepted unresolved review or charge | `halted` | none |
| `awaiting_review` | `review_clean` | valid response; usage/reservation finalized | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid normalized findings; usage finalized | `fix_required` | triage only |
| `awaiting_review` or `awaiting_re_review` | `review_inconclusive` | valid inconclusive response; usage finalized | `awaiting_maintainer` | none |
| `awaiting_review` or `awaiting_re_review` | `review_invalid` | completed invalid response; usage/reservation finalized | `awaiting_maintainer` | none |
| `fix_required` | `findings_disposed_no_change` | evidence-backed false/superseded | `awaiting_re_review` | none |
| `fix_required` | `review_fix_authorized` | genuine blocker, section 11.1, round remains | `implementing` | one fix |
| `fix_required` | `finding_requires_human` | scope/security/ambiguity/dependency/round | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid response; usage finalized | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings; usage finalized; rounds remain | `fix_required` | triage only |
| `awaiting_re_review` | `maximum_rounds_reached` | negative result after round two | `awaiting_maintainer` | none |
| any PR-bound active state without active/ambiguous external request | `work_head_changed` | valid scoped descendant differs from recorded head | `awaiting_pr` | none |
| any PR-bound active state | `work_head_ambiguous` | non-descendant, force-push, scope violation, or concurrent ambiguity | `halted` | none |
| any PR-bound active state | `human_merge_observed` | human action reconciled; no active/ambiguous request | `terminal` | none |
| any PR-bound active state | `human_close_observed` | human action reconciled; no active/ambiguous request | `terminal` | none |
| active non-halted | `authorization_expired` | expiry reached | `awaiting_maintainer` | reconcile accepted work only |
| `halted` | `authorization_expired_while_halted` | expiry reached | `halted` | preserve primary stop |
| active non-halted | `authorization_revoked` | valid revoke | `awaiting_maintainer` or justified `terminal` | safe cancellation only |
| `halted` | `authorization_revoked_while_halted` | valid revoke | `halted` | preserve primary stop |
| any non-terminal | `security_halt` | authenticated verified anomaly | `halted` | none |
| `halted` | `human_recovery_recorded` | valid command and complete reconciliation | reachable safe state or `terminal` | recovery only |
| `terminal` | `front_released` | section 7.3 | `idle` | none |

A PR-bound state contains a recorded PR, including `awaiting_pr` during rebinding, `awaiting_gates`, `awaiting_review`, `fix_required`, `awaiting_re_review`, and `awaiting_maintainer`.

An active request must be reconciled before head-change or human-outcome transitions. Unresolved result writes provider/work-head ambiguity and halts.

### 11.3 Initial no-change classification

`initial_no_change_completed` requires:

1. first implementation request only;
2. provider completed, not ambiguous;
3. work ref equals exact grant base;
4. zero changed files and diff lines;
5. no PR and no PR-creation event;
6. usage/reservation finalized;
7. bounded structured reason and evidence digest;
8. deterministic verifier confirms the authorized slice is already satisfied at the base;
9. no active request, reservation, lease ambiguity, security, or integrity stop.

It terminalizes as `completed_without_pr`, `evidence_status=not_applicable`.

If zero diff is confirmed but the deterministic verifier concludes that implementation requires a known human/governance/scope decision rather than proving the slice already satisfied, append `initial_no_change_needs_human` and enter `awaiting_maintainer`.

If the no-change response or evidence is malformed, unverifiable, internally inconsistent, wrong-head, scope-invalid, usage-invalid, provider-ambiguous, or associated with integrity/security concern, append `initial_no_change_invalid` and halt. This split deterministically selects human decision versus halt.

Provider assertion alone is never sufficient. Repair/fix no-change never uses `completed_without_pr`; it retains the existing PR, records `repair_no_change_recorded`, reruns gates, and receives re-review.

### 11.4 Completed invalid responses

`implementation_invalid` and `review_invalid` are for completed, non-ambiguous requests whose returned material fails deterministic contract validation.

Before either event:

- finalize actual usage and release unused reservation;
- store safe request/response digests and precise invalid class;
- prove no retry or second charge is authorized;
- invalidate any output-derived authority.

`review_invalid` enters `awaiting_maintainer` because the request outcome and charge are known but no valid verdict exists. A coupled security/integrity signal uses `security_halt` instead. `implementation_invalid` halts because branch/scope/head/usage validity required for safe continuation could not be established.

### 11.5 Human outcomes and merge SHA semantics

The maintainer may merge or close a recorded PR from any PR-bound state. Reconcile accepted requests/reservations first; unresolved ambiguity halts and recovery later records the observed human outcome.

A merge terminal event records `pr_head_at_merge_boundary`, `merge_result_sha`, merge method, actor, timestamp, prior state, and evidence bound to the PR head.

`current_clean` requires the PR head at the merge boundary to equal the exact head that passed required gates and current clean review, with no later invalidation and matching PR/base/branch/scope/policy. The merge-result SHA is separate and may differ for merge, squash, or rebase. Otherwise record `stale_or_incomplete`; outcome remains factually `merged_by_maintainer` without claiming system-prepared readiness.

Close/supersede records actual facts and creates no replacement PR.

### 11.6 Head invalidation and PR lifecycle

Any PR-head change invalidates gates, review, presentation, and clean eligibility. A valid scoped descendant from any PR-bound state, with no active/ambiguous request, writes `work_head_changed` and returns to `awaiting_pr`. Non-descendant, force-push, scope violation, unexpected actor, or concurrency ambiguity writes `work_head_ambiguous` and halts.

PR creation is eligible after `initial_work_head_recorded` proves strict non-empty delta. It is forbidden after initial no-change outcomes.

`pr_creation_authorized` binds repo/run/branch/head/base/scope/version. Zero matching PR creates one non-draft PR; one exact open PR is reused; deterministic duplicate/mismatch/closed conflict writes `pr_needs_human`; unresolved API/identity/fork/state writes `pr_ambiguous`; timeout searches before retry and never creates a second PR.

`pr_recorded` binds PR ID/repo/base/head branch/current head/operation/state. Gates/review are forbidden before it. Every repair delta or repair no-change rebinds the same PR; second PR forbidden.

## 12. Branch and scope

One work branch; App creates once; implementer commits later; no automated force/delete; base master; forks unsupported.

Before/after mutation verify normalized paths, deny precedence, file/line limits, linear ancestry, submodules, LFS, symlink escapes, binaries, secret risks, and bind scope digest.

Denied absent separate authority: `AGENTS.md`, workflows/CODEOWNERS, settings/rulesets, secrets/keys/tokens/env, protected conformance tests, vendored dependencies/lockfiles, and canonical authority file.

## 13. Deterministic gates

Readiness freezes exact checks/action pins/path conditions: registry, manual-review offline boundary, BLUECAD license boundary, Ruff, full Pytest, canary, frontend build if needed, strict real-tool proof where relevant, and 079 service unit/integration/conformance/reconstruction tests.

Eligible means success on exact repo/head/policy, not stale, skipped-required, cancelled, action-required, or superseded. One zero-model-cost infra rerun per collection absent source/assertion defect; further ambiguity halts. Never weaken tests/workflows.

## 14. Reviewer and finding identity

Reviewer is read-only, cannot dispatch/merge/settings/secrets/ref/ruleset, and differs effectively from implementer.

Request binds repo/spec/slice/scope/non-goals/base/head/diff/PR/gates/round/prior findings/fixes/content/provider/reservation/idempotency.

Response contains exact head, verdict `clean|findings|inconclusive`, bounded summary, and findings with severity/category/path/line/claim/reproduction/resolution. Reviewer cannot provide authoritative IDs. Control App validates/normalizes and derives `finding_<32 hex>` from round, head, normalized finding digest, and occurrence index. Model `finding_id` is unknown-field invalid.

Max 50 findings, 2,000 chars per field. Malformed, oversized, wrong-head, unknown-field, or non-JSON output writes `review_invalid` after usage reconciliation. Inconclusive writes `review_inconclusive`. P0/P1 block; P2 only when independently reproduced as binding violation; P3 advisory.

## 15. Disposition and rounds

Dispositions: `reproduced`, `accepted_without_reproduction`, `false_positive`, `superseded`, `needs_human`, all evidence-bound.

Initial review round zero; max two fix rounds, three reviewer calls, three implementer calls, one fix per negative round. Every code change returns through PR/gates/review. No-change rebuttal re-reviews. Negative after round two stops. Scope/destructive/governance/secret/dependency expansion stops.

## 16. Adapters and execution-spine block

Adapter requests bind repo/install, branch/head, conditional PR, spec/slice, scope/non-goals, task/findings, provider/budget/reservation/idempotency. Responses bind request/status, resulting head/no-change, safe digests/summary, usage/cost/idempotency/error.

Initial task permits `pr_number=null` only under section 11.1. Repair/review requires recorded PR.

Adapters cannot change authority; implementer writes work branch only; neither actor merges/approves/force-deletes/settings/secrets/control. Accepted ambiguity halts without retry absent proven idempotency/reconciliation. Completed invalid output follows section 11.4.

Current `AGENTS.md` requires all AI calls through product `run_ai_task` and `ai_jobs`; selected service does not share product SQLite/egress. Live 079 calls are blocked.

Proposed v0 governance route: narrow repository-development exception allowing approved 079 adapters outside product spine only with committed grant/claim/exact branch/head/conditional PR/scope/identity/provider/reservation/idempotency and durable usage/cost evidence. It requires separate `AGENTS.md` PR and readiness. Otherwise amend spec to use an authenticated product spine. Until then no live dispatch.

## 17. Spend

Separate development budget, integer micro-USD, defaults zero. Hard maxima: 5,000,000/request; 20,000,000/run; 25,000,000/UTC day; 100,000,000/month. `cost_unknown` stops.

Every model call reserves amount/quota/call count before dispatch. Missing reservation, stale price, exceeded cap/capacity, unknown cost/quota, or fallback means `dispatch_blocked` and zero call. Final usage finalizes/releases. No fallback. Marginal zero requires current plan/entitlement/quota/timestamp. Hosting/Actions tracked separately.

## 18. Content and secrets

External material is limited to exact spec/scope/diff/findings/PR when present/gates. Exclude secrets, credentials, env, keys, tokens, headers, unrelated records. All repo/model text is untrusted and cannot change authority. Deterministic policy constructs requests. No raw provider body in authority; safe digests/summaries/IDs/usage/cost only. S4/secret content denied absent later egress spec.

## 19. Permissions and rulesets

Candidate App: metadata read; contents read/write; PR read/write; checks/status/actions read; issues read/write. Actions write only if readiness proves need. No admin/environments/secrets/members/deployments/packages/security-alert/hook/ruleset bypass.

Capability wrapper allow-lists repo/endpoint/method/ref/path/state/schema and audits denials. Separate Control/implementer/reviewer/maintainer credentials.

Rulesets: master PR/checks/no force-delete/no automated bypass/human merge; control App/human recovery only/linear/no force-delete; work App create-only then implementer/maintainer write/reviewer read-only/base master. Abuse tests cover merge/approval/force-delete/out-of-scope/settings/secrets/post-create ref update/PR mutation.

## 20. Webhook, queue, service

Events: new issue comments, pushes on master/control/work, PR/review/review-comment/workflow-run, installation suspension/deletion. Edited authorization comments ignored.

Webhook verifies raw-body signature constant-time before JSON. Missing/invalid: auth failure, edge/app rate-limit, redacted log, no trusted delivery/queue/canonical event/security halt, no disclosure. Authenticated processing validates install/repo/event, stores digest, acknowledges under 10 seconds, queues reconciliation, no request-thread side effect.

Canonical security halt only for authenticated/verified anomaly: signed delivery-ID digest mismatch, identity contradiction, history tamper, credential misuse/unauthorized API success, scope/secret escape, independently confirmed compromise.

Endpoints only health, readiness, webhook. Queue operational; duplicate converges; pure reads retry bounded; side-effect retry requires committed event/proven idempotency; webhook order untrusted.

Retention delivery 30d, queue/projection 90d, logs 30d; no raw model/secrets/headers. Canonical RPO zero, DB RPO 24h, RTO target 4h; GitHub uncertainty stops.

## 21. Presentation

One non-authoritative check, sticky PR comment, control-issue status, weekly digest. Idempotent after canonical change. Between weekly reviews notify only human decision, authenticated security signal, or budget overrun/disabled authority. Digest Europe/Rome Monday 08:00, max weekly, omitted without change, never grants authority.

## 22. Security and supply chain

Short-lived tokens, managed secrets, rotation, immutable pins/digests, SBOM, dependency/container scans, outbound allow-list, repo/SHA validation, no untrusted fork with write/secrets, webhook process never executes PR code. Invalid unsigned traffic does not halt; verified authenticated compromise does.

## 23. Verification

### 23.1 Offline tests

Prove canonical encoding/chains/reconstruction/idempotency/schema; all state edges; grant/expiry/revoke/halted overlays/recover/release; claim/lease; work-ref create/ambiguity; initial PR absence; strict delta and PR creation; verified no-change terminal; human-boundary no-change; invalid no-change halt; implementer invalid halt; repair no-change; PR human/ambiguous failure; dispatch blocked zero-call; every dispatch reservation/capacity/lease; gate/review invalidation; review clean/findings/inconclusive/invalid with usage finalization; provider ambiguity; deterministic finding IDs; human outcomes all PR states; PR-head versus merge-result semantics; release after PR/no-PR; invalid webhook no state; inactivity silent.

### 23.2 Disposable proofs before readiness

All architecture-closure proofs remain mandatory, including races/CAS/timeouts/replay/reconstruction/tamper; lease; create-only ref and ambiguity; initial no-PR dispatch; strict delta PR; verified/no-human/invalid no-change paths; one PR and PR failure transitions; grant/lease/reservation/capacity; blocked dispatch zero call; head changes all PR states; active-request ambiguity; merge/squash/rebase SHA semantics; human outcomes; halted overlays; invalid implementer/reviewer output with finalized usage; provider ambiguity; finding IDs; release/sequential run; credential abuse; actor separation; fork/prompt injection; cost/duplicate charge; outage/kill switches; invalid unsigned no halt/authenticated anomaly halt; inactivity/noise.

### 23.3 Repository and conformance

Implementation passes repository Pytest/Ruff/status/canaries and deterministic service tests; no live/paid/production CI. Readiness freezes maintainer-owned vectors for every authority property. Implementation agents cannot weaken them.

## 24. Governance, rollout, readiness

### 24.1 Required `AGENTS.md` amendment

Separate PR explicitly amends manual/explicit-only dispatch and hard `run_ai_task`/`ai_jobs` invariant with narrow 079 repository-development exception described in section 16. It continues to forbid auto selection/merge/priority/bypass/force-delete/settings/secrets/destructive/scope expansion/fallback/work after expiry/revocation/security/cost/integrity/ambiguity/human stop. Until governance and readiness merge, no live calls.

### 24.2 Rollout

1. Human merge of this PR accepts documentary full spec and section 2.1 ordering amendment; 079 stays `planned`, mechanisms unavailable.
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

Canonical halt, App suspension, key/secret/provider revocation, service/queue stop, caps zero, dispatch workflow disable, human recovery. Rollback never force-pushes or erases.

Readiness proves merged dependencies/architecture/full spec/governance; every proof; exact permissions/rulesets/wrapper/IDs; execution exception; abuse denials; all initial/no-change/invalid/blocked/ambiguous transitions; work-ref/PR lifecycle; grant/lease/budget; head and human outcomes; merge SHA semantics; halted overlays; provider/finding/release; host/DB/secrets/adapters/pricing/caps/gates/vectors/owners/first slice; no unresolved P0/P1. Only readiness PR sets `ready`.

## 25. Compatibility

No product SQLite migration. Product execution/budget/Hermes/MemoryStore/BLUECAD/events do not become authority. Hosted DB rebuildable. Bootstrap new protected control branch explicitly; no chat/old PR/ref imported. Existing work needs exact grant/reconciliation and normally fresh branch. Review remains manual until governance/readiness. Authority versions require additive migration proof. No force-push migration.

## 26. Likely implementation scope

After readiness: `services/devloop/`, pinned service manifest/container, fake fixtures, secret-free deployment docs, normal `STATUS.md` transition, CI only for offline tests. Not in implementation: `AGENTS.md` amendment, live settings/App/rulesets/secrets, credentials/account data, product runtime, Hermes/MCP/MemoryStore/BLUECAD/process kernel/078. Dependencies pinned/justified/scanned/service-limited; no agent framework.

## 27. Non-goals

No automatic next-spec selection; simultaneous fronts/branches/actors/PRs; autonomous merge/approval/release/deploy/priority/governance/settings; force-delete/history rewrite/protected-test mutation; arbitrary shell; provider fallback/bidding/swarm; unbounded loops; untrusted fork execution; replacement of runtime 059b/Hermes/Actions; raw model/secret canonical storage; outage availability guarantee; or 078/other frozen work.

## 28. Definition result

Ready for maintainer merge decision when one-document diff keeps 079 planned; section 2.1 remains proposed until merge; architecture/state/auth/expiry/branch/PR/dispatch/lease/no-change/invalid/blocked/ambiguous/review/head/human/merge/provider/finding/permission/cost/test/rollout contracts are explicit; every proof remains readiness blocker; execution-spine conflict remains blocked; no mechanism claimed operational; no runtime/workflow/App/provider/secret/ruleset/dependency/setting change; exact-head gates pass; all current P0/P1 findings are absent; and PR stops for human merge.

Merge does not authorize governance, proofs against live JarvisOS, readiness, implementation, provider calls, or automated merge.
