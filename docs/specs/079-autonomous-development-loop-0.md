# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

Status: proposed full specification; it becomes merged authority only after an explicit human merge. `docs/specs/STATUS.md` remains authoritative and keeps 079 `planned`.

Depends on: 004, 017, 019, 022

Pinned full-spec baseline: `9c3c8ce90a9048c1797f2560025790162012d423`

Predecessor evidence:

- `079-autonomous-development-loop-source-evidence.md`
- `079-architecture-evidence-closure-2026-07-31.md`
- `079-architecture-source-evidence-2026-07-31.md`

## 1. Goal

Allow one explicitly authorized JarvisOS repository-development slice to continue safely across agent-session termination.

V0 may:

- reconstruct GitHub-owned authority;
- claim one repository-wide front;
- create one exact-base work branch;
- invoke one bounded implementer before a PR exists;
- create or reconcile one PR only after a real branch delta exists;
- terminalize a deterministically verified initial no-change result without creating an empty PR;
- collect exact-head gates;
- invoke exactly one reviewer request per review round and head;
- perform at most two bounded fix/re-review rounds;
- settle accepted calls before applying expiry or revocation;
- record every blocked, invalid, ambiguous, or human-required path canonically;
- record human merge or close actions truthfully from every PR-bound state;
- release a reconciled terminal front to `idle` without erasing history.

V0 may never merge, enable auto-merge, approve authoritatively, change roadmap priority, infer authorization from activity, create a second active front, or turn model output into authority.

## 2. Boundary and proposed sequencing amendment

This document specifies canonical state, authorization, claim, lease, branch/PR lifecycle, dispatch, gates, review, findings, spend, permissions, webhooks, proofs, rollout, kill switches, and compatibility.

It does not create or configure an App, service, database, queue, branch, ruleset, workflow, secret, provider, dependency, runtime change, governance amendment, readiness decision, implementation, or merge automation. It does not modify `AGENTS.md` or `STATUS.md` and invokes no model or paid service.

Current `AGENTS.md` remains binding. Live development-agent dispatch is prohibited until section 24's separate governance amendment and dated readiness decision merge.

### 2.1 Documentary ordering presented for human approval

The merged architecture closure required isolated race, CAS, credential, cost, PR, and recovery proofs before full-spec promotion. The maintainer subsequently instructed the full-spec drafting step to proceed.

Before this PR is merged, the prior ordering remains authoritative. Human merge of this PR would approve only this narrow ordering change:

- the complete documentary specification may merge while 079 remains `planned`;
- all mechanisms remain unproven and unavailable;
- every architecture-closure proof remains mandatory before readiness and implementation;
- no live App, JarvisOS proof prototype, governance exception, provider call, readiness promotion, or implementation is authorized.

No proof is waived, weakened, relabelled, or treated as complete.

## 3. Hard invariants

1. `STATUS.md` is the sole live roadmap/status authority.
2. At most one product or implementation front is active repository-wide.
3. Branches, PRs, labels, comments, reviews, checks, workflows, timers, and model text are not authorization.
4. V0 starts only from a maintainer command naming exact repository, spec, slice, base SHA, scope, adapters, and budget policy.
5. Every side-effect event rechecks grant currency, claim, GitHub facts, stop state, role capacity, provider policy, idempotency, and canonical reservation; mutation also requires a current reconciled lease.
6. Initial implementation binds verified PR absence. Repair and review requests bind the one recorded PR.
7. A PR is created only after a strict non-empty in-scope delta. Verified initial no-change may terminalize without a PR.
8. Exactly one active external request may exist. Exactly one reviewer request may be authorized for a given run, round, head, and adapter.
9. Expiry or revocation during an accepted request blocks follow-on work but does not change out of the request's response state until that request is settled or declared ambiguous.
10. Every completed invalid response reconciles usage/reservation and writes a canonical failure event. Every ambiguity writes a canonical halt. Every pre-dispatch denial writes a no-call blocked event.
11. Gates and review are exact-head evidence. Any head change invalidates them.
12. Reviewer cannot mutate; implementer cannot author the authoritative review verdict.
13. Automated actors cannot merge, auto-merge, force-push, delete protected refs, change settings/secrets, or bypass rulesets.
14. Revocation or expiry never clears a security, integrity, or ambiguity halt.
15. Human PR actions are recorded factually; observation never manufactures a clean verdict.
16. Safety dominates liveness.

## 4. Architecture

### 4.1 Service

The selected dispatcher class is an installed GitHub App operated by a stateless Python 3.11 FastAPI/ASGI service with a GitHub REST/Git Data client and PostgreSQL 16.

PostgreSQL is non-authoritative and may store delivery IDs/digests, queued reconciliation jobs, bounded retries, cached projections, provider correlations, notification deduplication, and operational health. It never owns the only grant, claim, lease, PR binding, gate/review verdict, request settlement, reservation, terminal outcome, or release.

One OCI image and multiple identical replicas are permitted. Redis, agent frameworks, vector databases, browser automation, and another orchestration engine are excluded.

The service is outside JarvisOS product runtime and does not share JarvisOS SQLite, runtime egress state, runtime provider secrets, or `C:\JarvisOS` data.

### 4.2 Canonical location

Canonical authority lives on protected branch `jarvis-control` in exactly one file:

`.jarvis/development-loop/authority.json`

Comments, checks, workflow runs, database rows, dashboards, and digests are rebuildable projections only.

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

Every event contains sequence, deterministic event ID, closed event type, timestamp, effective actor/role, idempotency key, previous-event digest, payload/digest, and event digest.

Identical duplicate input is a no-op returning the existing event. Reuse of an idempotency key with different bytes is an integrity failure. Sequence and Git ancestry, not timestamps, own ordering.

Both the event hash chain and linear `jarvis-control` ancestry must validate. Missing, altered, reordered, duplicated, forked, force-pushed, or non-linear history causes `control_integrity_failure` and zero external side effects. V1 has no compaction and halts before event 4097 or 2,000,000 canonical bytes.

## 6. Closed IDs, roles, states, outcomes, and snapshot fields

### 6.1 IDs and roles

Control-App-derived prefixes:

- `run_`
- `grant_`
- `claim_`
- `lease_`
- `pr_`
- `gates_`
- `review_`
- `finding_`
- `fix_`
- `provider_`
- `human_`

Models/providers never choose authoritative IDs.

Closed roles:

- `maintainer`
- `control`
- `implementer`
- `reviewer`
- `gate_collector`
- `system_reconciler`

Effective credentials determine role.

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

The separate dispatch and response states prevent two reviewer requests from being authorized for one round.

### 6.3 Terminal outcomes

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `authorization_expired`
- `abandoned_after_human_decision`

`completed_without_pr` is allowed only for the first implementer request after section 11.5 verification.

A merge terminal event records separately:

- `prepared_state_at_human_action`;
- `pr_head_at_merge_boundary`;
- `merge_result_sha`;
- merge method (`merge`, `squash`, `rebase`, or `unknown`);
- actor and timestamp;
- `evidence_status` (`current_clean`, `stale_or_incomplete`, or `not_applicable`).

PR head and merge-result SHA are never assumed equal.

### 6.4 Active request and authority-stop overlay

The snapshot contains at most one `active_request`:

```json
{
  "request_id": "provider_<32 hex>",
  "kind": "review",
  "role": "reviewer",
  "round": 0,
  "head_sha": "<40 hex>",
  "adapter_id": "approved-reviewer-v1",
  "idempotency_key": "sha256:...",
  "reservation_id": "provider_<32 hex>",
  "status": "authorized"
}
```

`active_request` is null before dispatch and after exact settlement. A second request cannot be authorized while it is non-null.

The snapshot may also contain `authority_stop_pending`:

```json
{
  "kind": "authorization_expired",
  "occurred_at": "...Z",
  "follow_on_forbidden": true
}
```

This overlay is used only when expiry or revocation occurs after an external request has been accepted. It blocks all follow-on work while preserving the response state needed to settle that request.

### 6.5 Other snapshot fields

The snapshot binds run, grant/expiry/revocation, claim/lease, work branch/head, optional PR/base/head branch/state, ancestry/diff/scope, gates, review round/head/verdict/findings/dispositions, integer-micro-USD reservations/finalized/released usage, role call counts, next action, primary stop/overlays, outcome, and last completed run.

Before PR creation, `pr_number=null` and `pr_expected_absent=true` are explicit.

## 7. Authorization lifecycle

### 7.1 Grant

Readiness bootstraps one control issue and allow-listed maintainer numeric IDs. Commands must be newly created, exactly formatted, repository/issue/author validated, and rechecked against current SHAs/facts. Comments are inputs, not authority.

The grant binds repository ID, three-digit spec, bounded slice, `master` and exact base SHA, normalized allow/deny globs with deny precedence, file/line limits, distinct approved adapter IDs, budget policy, maximum fix rounds 0–2, optional expiry within 30 days, and bounded reason. Scope produces `scope_digest`; work branch derives as `jarvis-work/<run_id>`.

No grant is inferred from a row, branch, PR, label, schedule, chat, prior run, or model output.

### 7.2 Expiry or revocation with no active request

If `active_request=null`:

- from a non-halted active state, `authorization_expired` or `authorization_revoked` enters `awaiting_maintainer` and blocks new work;
- from `halted`, the corresponding `*_while_halted` event preserves `halted`, preserves the original primary stop, and adds the expiry/revocation overlay.

Ownership/history are never released automatically.

### 7.3 Expiry or revocation with an active request

If `active_request` is non-null:

1. append `authorization_stop_pending` with kind expiry or revocation;
2. remain in the same request response state (`implementing`, `reviewing`, or `re_reviewing`);
3. set `follow_on_forbidden=true`;
4. authorize no new request, retry, PR creation, gate run, fix, review, or presentation transition;
5. settle or safely cancel the accepted request through section 11.4.

Only after exact settlement may the state become `awaiting_maintainer` or `halted`. Thus the eventual head, usage, reservation, and response are never stranded in the wrong state.

### 7.4 Recovery and release

Recovery binds exact control head, run, action (`resume` or `terminalize`), target/outcome, reason, and independent reconciliation of control history, work ref, PR, workflows, active request, provider status, reservations, usage/cost, lease, grant overlays, security, and integrity.

Security/integrity recovery requires referenced remediation evidence.

Release is allowed only from `terminal` after all actions, reservations, cancellations, ambiguity, stops, PR/ref facts, and overlays reconcile. For `completed_without_pr`, release proves no PR and no branch delta.

`front_released` returns to `idle` while preserving complete history. A later run requires a new grant.

## 8. Repository-wide claim, work ref, and lease

`claim_acquired` requires current grant, eligible registry/dependencies, repository-wide vacancy, no competing owner/PR/run, exact base, current policies, and no stop. One CAS records claim and initial 60-minute lease. Losers or ambiguity produce zero side effects.

After claim, the Control App may create only `refs/heads/jarvis-work/<run_id>` at exact grant base while state/claim/lease match. Existing exact ref is idempotently accepted. The App cannot later update, force-update, delete, or commit on it. A mismatched or ambiguous operation records `work_branch_ambiguous` and halts.

Later engineering writes are implementer-only under the lease.

Lease duration is 60 minutes; renewal window is the final 20 minutes; one mutation request may be active; renewal cannot alter grant, scope, round, adapter, provider, or budget. Expiry never releases ownership and blocks mutation until all facts reconcile and a renewal commits.

## 9. Exact-head Git CAS

Every authority transition reads exact control ref/parent/tree/blob, validates schema/chains/snapshot, re-reads preconditions, computes one event, creates blob/tree/commit with sole exact parent, and updates the ref with `force=false`.

Contents API blob update is forbidden as authority CAS.

Rejection, timeout, disconnect, or ambiguity permits no external side effect. The service re-reads ref, ancestry, and event ID: exact occurrence means committed, absence means lost, unresolved ambiguity halts. The same idempotency key never creates a different event.

## 10. Dispatch contract

### 10.1 Dispatch-authorizing events

Only these events authorize model calls:

- `implementation_requested`;
- `gate_repair_authorized`;
- `review_fix_authorized`;
- `review_dispatch_authorized`.

Every dispatch event atomically binds:

- current unexpired/unrevoked grant;
- current claim and no stop/stop-pending overlay;
- `active_request=null`;
- exact repository, work ref, base, and head;
- approved role/adapter and remaining call capacity;
- provider policy;
- canonical amount/quota/call reservation, including marginal-zero calls;
- deterministic request idempotency key;
- valid lease/scope for mutation.

Conditional PR binding:

- initial implementation requires `pr_number=null`, `pr_expected_absent=true`, and a live search proving no PR exists for the derived branch;
- gate repair, review fix, and review dispatch require the one recorded PR and exact current PR head;
- review dispatch additionally requires exact eligible gates.

The dispatch event creates `active_request` before the external call.

### 10.2 Exactly one reviewer request per round/head

`review_dispatch_authorized` is permitted only from `awaiting_review_dispatch` or `awaiting_re_review_dispatch` and transitions to `reviewing` or `re_reviewing`.

Its deterministic key is derived from repository, run, PR, round, exact head, adapter, and request schema version.

- An identical repeated delivery returns the existing committed event/request and creates no new reservation or call.
- A different request key for the same run/round/head is an integrity failure.
- A later reviewer request requires a new round or a new exact head and a return to the corresponding dispatch state.

### 10.3 Blocked dispatch

If deterministic preconditions fail before any call, append `dispatch_blocked`, release any provisional reservation, record the precise reason, make zero external call, and enter `awaiting_maintainer`. Expiry, revocation, security, and integrity use their specific events instead.

## 11. Closed transition system

### 11.1 Main transitions

| Current state | Event | Preconditions | Next state | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid command | `authorized` | none |
| `authorized` | `claim_acquired` | section 8 and CAS | `claimed` | create/reconcile work ref |
| `claimed` | `work_branch_recorded` | exact ref at base; PR absent | `claimed` | none |
| `claimed` | `work_branch_ambiguous` | ref mismatch/unresolved create | `halted` | none |
| active non-halted, no active request | `lease_renewed` | current grant/lease/reconciliation/window | same | none |
| dispatch-eligible state | `dispatch_blocked` | closed pre-call failure; zero call | `awaiting_maintainer` | none |
| `claimed` | `implementation_requested` | section 10 initial no-PR authority | `implementing` | one implementer call |
| `implementing` | `initial_work_head_recorded` | strict descendant; non-empty in-scope delta | `awaiting_pr` | none |
| `implementing` | `initial_no_change_completed` | section 11.5 satisfied | `terminal` | none |
| `implementing` | `initial_no_change_needs_human` | section 11.5 human-boundary class | `awaiting_maintainer` | none |
| `implementing` | `initial_no_change_invalid` | section 11.5 proof-rejection class | `halted` | none |
| `implementing` | `implementation_invalid` | completed invalid envelope/head/scope/usage | `halted` | none |
| `implementing` | `repair_work_head_recorded` | repair; strict descendant; PR exists | `awaiting_pr` | none |
| `implementing` | `repair_no_change_recorded` | repair; exact prior head; valid evidence; PR exists | `awaiting_pr` | none |
| `implementing` | `provider_ambiguous` | unresolved acceptance/result/charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | exact delta/rebind and grant | `awaiting_pr` | create/reconcile one PR |
| `awaiting_pr` | `pr_recorded` | one exact open PR/head | `awaiting_gates` | observe/request gates only |
| `awaiting_pr` | `pr_needs_human` | deterministic PR conflict | `awaiting_maintainer` | none |
| `awaiting_pr` | `pr_ambiguous` | unresolved PR API/identity/state | `halted` | none |
| `awaiting_gates` | `gates_passed` | all exact-head required gates green | `awaiting_review_dispatch` or `awaiting_re_review_dispatch` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope defect | `fix_required` | none |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale/flaky/cancelled/missing/action-required/infra | `halted` or `awaiting_maintainer` | none |
| `awaiting_review_dispatch` | `review_dispatch_authorized` | section 10, round/head unique | `reviewing` | one reviewer call |
| `awaiting_re_review_dispatch` | `review_dispatch_authorized` | section 10, round/head unique | `re_reviewing` | one reviewer call |
| `reviewing` or `re_reviewing` | `review_clean` | valid exact-head response; usage finalized | `awaiting_maintainer` | presentation only |
| `reviewing` or `re_reviewing` | `review_findings_recorded` | valid findings; usage finalized | `fix_required` | triage only |
| `reviewing` or `re_reviewing` | `review_inconclusive` | valid inconclusive; usage finalized | `awaiting_maintainer` | none |
| `reviewing` or `re_reviewing` | `review_invalid` | completed invalid output; usage finalized | `awaiting_maintainer` | none |
| `reviewing` or `re_reviewing` | `provider_ambiguous` | unresolved acceptance/result/charge | `halted` | none |
| `fix_required` | `findings_disposed_no_change` | evidence-backed false/superseded | `awaiting_re_review_dispatch` | none |
| `fix_required` | `gate_repair_authorized` or `review_fix_authorized` | section 10 mutation authority and round remains | `implementing` | one repair/fix call |
| `fix_required` | `finding_requires_human` | scope/security/ambiguity/dependency/round | `awaiting_maintainer` | none |
| `awaiting_re_review_dispatch` | `maximum_rounds_reached` | no further review allowed | `awaiting_maintainer` | none |
| any PR-bound active state, no active request | `work_head_changed` | valid scoped descendant | `awaiting_pr` | none |
| any PR-bound active state | `work_head_ambiguous` | non-descendant/force/scope/concurrency ambiguity | `halted` | none |
| any PR-bound active state, no active request | `human_merge_observed` | exact human action reconciled | `terminal` | none |
| any PR-bound active state, no active request | `human_close_observed` | exact human action reconciled | `terminal` | none |
| `awaiting_maintainer` | `human_decision_recorded` | section 11.6 | closed target state or `terminal` | none |
| `halted` | `human_recovery_recorded` | complete reconciliation/remediation | reachable safe state or `terminal` | recovery only |
| `terminal` | `front_released` | section 7.4 | `idle` | none |

A PR-bound state contains a recorded PR, including `awaiting_pr` during rebinding, `awaiting_gates`, both review-dispatch states, both reviewing states, `fix_required`, and `awaiting_maintainer` when its snapshot contains a PR.

### 11.2 Expiry/revocation and request settlement

| Current condition | Event | Next state | Rule |
| --- | --- | --- | --- |
| active non-halted, `active_request=null` | `authorization_expired` or `authorization_revoked` | `awaiting_maintainer` | no new work |
| `halted` | `authorization_expired_while_halted` or `authorization_revoked_while_halted` | `halted` | preserve primary stop |
| `implementing`, `reviewing`, or `re_reviewing` with active request | `authorization_stop_pending` | same | block follow-on; settle request |
| stop-pending + exact valid completed response | `request_settled_after_authority_stop` | `awaiting_maintainer` | record head/response/usage; no follow-on authority |
| stop-pending + proven safe cancellation | `request_cancelled_after_authority_stop` | `awaiting_maintainer` | finalize/release reservation |
| stop-pending + completed invalid implementer response | `implementation_invalid_after_authority_stop` | `halted` | preserve expiry/revoke overlay |
| stop-pending + completed invalid reviewer response | `review_invalid_after_authority_stop` | `awaiting_maintainer` | preserve overlay |
| stop-pending + unresolved result/charge | `provider_ambiguous` | `halted` | preserve overlay |

`request_settled_after_authority_stop` records the actual resulting work head/diff or reviewer response as forensic evidence, clears `active_request`, finalizes usage/reservation, and marks all output ineligible for automatic continuation. If a work result violates scope/ancestry or carries a security/integrity issue, the corresponding invalid/security halt is used instead.

An expired or revoked grant cannot be resumed. The maintainer must terminalize, release, and issue a new grant for later work.

### 11.3 Completed response classification priority

Classification order is mandatory and mutually exclusive:

1. **Unresolved acceptance, completion, result, or charge** -> `provider_ambiguous`.
2. **Completed response with invalid envelope/schema, wrong bound head, invalid usage, invalid scope/ancestry, or unknown required field** -> `implementation_invalid` or `review_invalid` according to role.
3. **Completed, valid initial implementation response with strict non-empty in-scope delta** -> `initial_work_head_recorded`.
4. **Completed, valid initial implementation response with a valid no-change envelope, exact base head, zero diff, and finalized usage** -> apply section 11.5 verifier and select exactly one of `initial_no_change_completed`, `initial_no_change_needs_human`, or `initial_no_change_invalid`.
5. **Completed valid repair/fix response** -> `repair_work_head_recorded` or `repair_no_change_recorded`.

Thus malformed, wrong-head, usage-invalid, scope-invalid, or ambiguous responses can never also be `initial_no_change_invalid`.

### 11.4 Completed invalid responses

Before any completed-invalid event:

- finalize actual usage and release unused reservation;
- store safe request/response digests and the precise invalid class;
- clear `active_request`;
- prove no retry or second charge is authorized;
- invalidate output-derived authority.

`implementation_invalid` halts because safe branch/head/scope continuation cannot be established. `review_invalid` enters `awaiting_maintainer` because the branch remains known but no valid verdict exists. A security/integrity signal uses the specific halt instead.

### 11.5 Initial no-change verifier

The no-change branch is entered only after section 11.3 has established a completed, valid no-change envelope, exact base head, zero diff, no PR, finalized usage, and no ambiguity.

The deterministic verifier then selects exactly one outcome:

- `initial_no_change_completed`: repository facts prove the authorized slice's acceptance conditions are already satisfied at the pinned base.
- `initial_no_change_needs_human`: facts prove progress requires a specific human governance, scope, dependency, secret, permission, or destructive-action decision that the current grant cannot authorize.
- `initial_no_change_invalid`: the valid no-change claim is contradicted or unsupported by deterministic repository facts, but there is no provider ambiguity and no separately classified envelope/head/scope/usage/security failure.

`initial_no_change_completed` terminalizes as `completed_without_pr` with no PR creation. `initial_no_change_needs_human` enters no-PR `awaiting_maintainer`. `initial_no_change_invalid` halts for recovery. Provider assertion alone is never sufficient.

A repair/fix no-change never uses these events; it retains the recorded PR, rebinds the same head, reruns gates, and receives re-review.

### 11.6 Human decision from `awaiting_maintainer`, including no-PR states

`human_decision_recorded` is valid whether or not a PR exists. It binds an allow-listed maintainer, exact control head, exact repository/work/PR facts, no active request/reservation ambiguity, current stop overlays, action, target, and reason.

Closed actions:

- `abandon` -> `terminal` with `abandoned_after_human_decision`;
- `supersede` -> `terminal` with `superseded_by_maintainer`;
- `resume_pre_pr` -> `claimed` only when no PR exists, work head equals grant base, grant remains current, no authority-stop overlay exists, policies remain current, and lease has been reconciled/renewed;
- `resume_pr_reconciliation` -> `awaiting_pr` only when a valid branch delta or recorded PR exists and the exact deterministic PR conflict has been resolved;
- `resume_gates` -> `awaiting_gates` only when the recorded PR/head is exact and the prior human stop did not invalidate gates;
- `resume_review` -> `awaiting_review_dispatch` or `awaiting_re_review_dispatch` only when PR/head/gates/round remain exact and no prior review request is active;
- `terminalize_expired_or_revoked` -> `terminal` with the matching expiry/revocation outcome after all accepted requests settle.

Resume is forbidden for expired/revoked grants, unresolved security/integrity/provider ambiguity, active requests, stale heads, or scope expansion. Those cases require recovery or terminalization followed by release and a new grant.

### 11.7 Head changes and human PR outcomes

Any PR-head change invalidates gates, review, presentation, and clean-merge eligibility.

With no active request, a valid scoped descendant from any PR-bound state records `work_head_changed` and returns to `awaiting_pr`. Non-descendant, force-push, unexpected actor, scope violation, or concurrent ambiguity records `work_head_ambiguous` and halts.

If a request is active, settle it first. Unresolved settlement halts; no head-change event silently ignores an in-flight request.

The maintainer may merge or close from any PR-bound state after requests/reservations settle. A merge terminal event records PR head at merge boundary, separate merge-result SHA, merge method, actor, timestamp, prior state, and head-bound evidence.

`evidence_status=current_clean` requires the PR head at the merge boundary to equal the exact current gated and clean-reviewed head with no later invalidation. Merge-result SHA is not compared to the reviewed PR head and may differ under merge, squash, or rebase. Otherwise evidence status is `stale_or_incomplete`; the factual outcome remains `merged_by_maintainer` without a system-ready claim.

Close/supersede records actual facts and creates no replacement PR.

### 11.8 Idempotent PR lifecycle

PR creation is eligible only after a strict non-empty in-scope initial delta. It is forbidden after any initial no-change outcome.

`pr_creation_authorized` binds repository, run, branch, exact head, base, scope, and version.

- zero matching PRs -> create one non-draft PR;
- exactly one correct open PR -> reuse it;
- deterministic duplicate/mismatch/closed conflict -> `pr_needs_human`;
- unresolved API/identity/fork/state -> `pr_ambiguous`;
- timeout -> search/reconcile before retry; never create a second PR.

`pr_recorded` binds PR ID, repository, base, head branch, exact work head, operation key, and state. Gates/review are forbidden before it. Every repair delta or repair no-change rebinds the same PR; a second PR is forbidden.

## 12. Branch and scope

One work branch exists. The Control App creates it once; implementer writes later; automated force-push/deletion is denied; PR base is `master`; forks are unsupported.

Before and after mutation, verify normalized paths, deny precedence, file/line limits, linear ancestry, submodules, LFS pointers, symlink escapes, binaries, secret risks, and scope digest.

Denied absent separate authority:

- `AGENTS.md`;
- workflows and CODEOWNERS;
- settings/rulesets;
- secrets, keys, tokens, certificates, and environment files;
- maintainer-owned conformance tests;
- vendored dependencies/lockfiles;
- canonical authority file.

## 13. Deterministic gates

Readiness freezes exact checks, action pins, and path conditions: registry, manual-review offline boundary, BLUECAD license boundary, Ruff, full Pytest, canary, frontend build when required, strict real-tool proof when relevant, and 079 service unit/integration/conformance/reconstruction tests.

Eligible evidence is successful, exact-repository/head/policy, and not stale, required-but-skipped, cancelled, action-required, or superseded.

One zero-model-cost infrastructure rerun is allowed per collection absent source/assertion failure. Further or ambiguous infrastructure failure halts. Tests/workflows may not be weakened.

## 14. Reviewer and findings

Reviewer credentials are read-only and effectively distinct from implementer credentials. They have no write, workflow dispatch, merge, settings, secret, ref-delete, or ruleset authority.

A review request binds repository, spec, slice, scope/non-goals, base/head, diff, PR, gates, round, prior findings/fixes, content digest, provider policy, reservation, and idempotency.

Response contains exact reviewed head, verdict `clean|findings|inconclusive`, bounded summary, and findings with severity/category/path/line/claim/reproduction/resolution. Reviewer cannot provide authoritative finding IDs. The Control App validates/normalizes and derives each `finding_<32 hex>` from round, head, normalized finding digest, and occurrence index. Model-supplied `finding_id` is invalid.

Maximum 50 findings and 2,000 characters per text field. Malformed, oversized, wrong-head, unknown-field, or non-JSON output uses `review_invalid` after usage settlement. Inconclusive uses `review_inconclusive`. P0/P1 block; P2 blocks only if independently reproduced as a binding violation; P3 is advisory.

## 15. Findings and bounded rounds

Closed dispositions:

- `reproduced`
- `accepted_without_reproduction`
- `false_positive`
- `superseded`
- `needs_human`

All are evidence-bound.

Initial review is round zero. Maximums: two fix rounds, three reviewer calls, three implementer calls, and one fix per negative round. Every code change returns through PR rebinding, gates, and review. A no-change rebuttal still requires re-review. Negative result after round two stops. Scope, destructive, governance, secret, or dependency expansion requires human action.

## 16. Adapter and execution-spine governance block

Adapter requests bind repository/installation, branch/head, conditional PR, spec/slice, scope/non-goals, task/findings, provider/budget/reservation/idempotency. Responses bind request/status, resulting head/no-change, safe digests/summary, usage/cost/idempotency/error.

Initial implementation permits `pr_number=null` only under section 10. Repair and review require the recorded PR.

Adapters cannot change authority. Implementer writes only the work branch. Neither actor may merge, approve, force-push, delete refs, change settings/secrets, or write control authority. Accepted ambiguity halts without retry absent exact reconciliation.

Current `AGENTS.md` requires all AI calls through product `run_ai_task` and `ai_jobs`; the selected service does not share product SQLite/egress. Live 079 calls are blocked.

The proposed v0 governance route is a narrow repository-development exception allowing approved 079 adapters outside the product spine only with committed grant, claim, exact branch/head, conditional PR, scope, actor, provider, reservation, idempotency, and durable usage/cost evidence. It requires a separate `AGENTS.md` PR and readiness decision. Otherwise this spec must be amended to use an authenticated product execution-spine boundary.

## 17. Spend

Repository-development budget uses integer micro-USD and defaults to zero.

Hard maxima:

- 5,000,000 per request;
- 20,000,000 per run;
- 25,000,000 per UTC day;
- 100,000,000 per calendar month.

`cost_unknown` is a hard stop.

Every model call reserves amount, quota, and role-call count before dispatch. Missing reservation, stale price, exceeded cap/capacity, unknown cost/quota, or fallback means `dispatch_blocked` and zero call. Final usage finalizes/releases the reservation. V1 has no fallback. Marginal-zero use requires current plan, entitlement, quota, and timestamp evidence. Hosting/Actions costs are tracked separately.

## 18. Content and secrets

External material is limited to exact spec, scope, diff, findings, PR when present, and gates. Secrets, credentials, environment values, keys, tokens, headers, and unrelated records are excluded.

All repository and model text is untrusted and cannot change authority. Deterministic policy constructs requests. No raw provider body enters canonical authority; safe digests, summaries, IDs, usage, and cost are permitted. S4/secret-bearing content remains denied absent a later repository-development egress specification.

## 19. Permissions and rulesets

Candidate App permissions:

- metadata read;
- contents read/write;
- PR read/write;
- checks/status/Actions read;
- issues read/write.

Actions write is absent unless readiness proves exact need. Administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, and ruleset bypass are denied.

A capability wrapper allow-lists repository, endpoint, method, ref, path, state, and schema and audits denials. Separate Control, implementer, reviewer, and maintainer credentials are required.

Rulesets:

- `master`: PR/checks required, no automated bypass, no force-push/delete, human-only merge;
- `jarvis-control`: Control App or explicit human recovery only, linear, no force-push/delete;
- `jarvis-work/*`: App create-only at exact base, then implementer/maintainer write, reviewer read-only, no automated force-push/delete, base `master`.

Abuse tests cover merge, approval, force-push, deletion, out-of-scope write, settings/secrets, post-create App ref mutation, and unauthorized PR mutation.

## 20. Webhook, queue, and service API

Subscribed events are new issue comments, pushes on master/control/work, PR/review/review-comment/workflow-run, and installation suspension/deletion. Edited authorization comments are ignored.

Webhook verifies the raw-body signature in constant time before JSON parsing.

Missing/invalid signatures return authentication failure, are edge/application rate-limited and redacted in logs, create no trusted delivery, queue item, canonical event, security signal, or halt, and reveal no repository/install/command existence.

Authenticated processing validates installation/repository/event, stores delivery digest, acknowledges within 10 seconds, performs no request-thread side effect, and queues reconciliation.

Canonical security halt is reserved for authenticated or independently verified anomaly: signed delivery-ID digest mismatch, identity contradiction, history tamper, credential misuse/unauthorized API success, or verified scope/secret escape.

Other endpoints are health/readiness probes only. Queue ownership is operational; duplicate jobs converge canonically; pure reconciliation retries are bounded; side-effect retry requires committed authority and proven idempotency; webhook order is untrusted.

Retention: delivery 30 days, queue/projections 90 days, logs 30 days; no raw model bodies, secrets, or headers. Canonical RPO zero, database RPO 24 hours, service RTO target four hours; GitHub uncertainty stops indefinitely.

## 21. Presentation and notifications

At most one non-authoritative check, sticky PR comment, control-issue status, and weekly digest. Updates are idempotent after canonical changes.

Between weekly reviews, direct notification is limited to human decision, authenticated security signal, or budget overrun/disabled cost authority.

Digest: Europe/Rome, Monday 08:00 local, at most weekly, omitted without state change, and never grants authority.

## 22. Security and supply chain

Use short-lived tokens, managed secrets, rotation, immutable pins/digests, SBOM, dependency/container scans, outbound allow-listing, repository/SHA validation, and no untrusted fork execution with write/secrets. Webhook processing never executes PR code. Invalid unsigned traffic does not halt; verified authenticated compromise does.

## 23. Verification

### 23.1 Offline tests

With fake GitHub, PostgreSQL, implementer, and reviewer actors, prove:

- canonical encoding/chains/reconstruction/idempotency/schema;
- every state-table edge;
- grant, expiry/revocation with and without active requests, stop-pending settlement/cancellation/ambiguity, recovery, release;
- claim/lease and create-only work ref;
- initial PR absence and strict-delta PR creation;
- mutually exclusive response classification priority;
- valid, human-boundary, and proof-rejected initial no-change paths;
- completed invalid implementer/reviewer settlement;
- exactly one reviewer request per round/head under concurrent workers;
- duplicate review authorization returns the existing request without new reservation/call;
- no-PR human decision resume/terminalization;
- PR conflict/ambiguity paths;
- every dispatch reservation/capacity/lease check;
- exact-head gate/review invalidation;
- provider ambiguity and deterministic finding IDs;
- human merge/close from every PR-bound state;
- PR head versus merge-result SHA semantics;
- release after PR and no-PR outcomes;
- invalid webhook no canonical change;
- inactivity creates no repeated work.

### 23.2 Disposable-repository proofs before readiness

All architecture-closure proofs remain mandatory, including:

1. multi-dispatcher single-winner CAS;
2. stale parent/ref rejection even with unchanged blob;
3. timeout reconciliation exactly once;
4. replay after database loss and full reconstruction;
5. history-tamper halt;
6. lease expiry never transfers ownership;
7. create-only ref and denial of later App mutation;
8. initial no-PR dispatch and strict-delta one-PR creation;
9. mutually exclusive no-change/invalid/ambiguity classification;
10. human resolution of pre-PR stops;
11. exactly one reviewer request per round/head under races;
12. expiry/revocation pending settlement of accepted implementer and reviewer calls;
13. PR timeout, mismatch, fork, duplicate, closed, and ambiguity behavior;
14. grant/lease/reservation/capacity enforcement;
15. head changes from every PR-bound state;
16. human merge/close and merge/squash/rebase SHA semantics;
17. invalid output usage settlement and no retry;
18. provider ambiguity, finding IDs, release, and sequential runs;
19. credential abuse denials and role separation;
20. fork/prompt-injection resistance;
21. cost and duplicate-charge stops;
22. outage and kill switches;
23. invalid unsigned traffic no halt, authenticated anomaly halt;
24. inactivity/replay no noise or duplicate calls.

### 23.3 Repository/conformance

Implementation must pass repository Pytest, Ruff, status checks, existing canaries, and deterministic service tests. CI may not call live models, paid services, or production settings.

Readiness freezes maintainer-owned conformance vectors for every authority property. Implementation agents cannot weaken them.

## 24. Governance, rollout, readiness, and kill switches

### 24.1 Required `AGENTS.md` amendment

A separate PR must amend manual/explicit-only development dispatch and the hard `run_ai_task`/`ai_jobs` invariant with the narrow 079 repository-development exception described in section 16.

The exception continues to forbid automatic spec selection, merge, auto-merge, priority change, workflow/ruleset bypass, force-push, branch deletion, settings/secrets, destructive action, scope expansion, fallback, or work after expiry, revocation, security, cost, integrity, ambiguity, or human-decision stop.

Until governance and readiness merge, no live model call is authorized.

### 24.2 Rollout

1. Human merge of this PR accepts the documentary full spec and section 2.1 ordering amendment; 079 remains `planned` and mechanisms unavailable.
2. Merge the dormant governance amendment.
3. Build the proof prototype only in a disposable repository/separate fixture with fake actors and zero paid calls.
4. Execute every architecture proof before readiness.
5. Optionally run an explicitly approved read-only JarvisOS shadow with no claim/ref/PR/workflow/provider writes.
6. Dated readiness records host, App/actors, rulesets, adapters, prices/caps, proof outputs, vectors, owners, and rollback; only then set `ready`.
7. Implement in one bounded PR after readiness.
8. Use a separate operational grant for one low-risk documentation-only activation with human merge.
9. Broader use requires separate approval after first-run evidence.

No implementation skeleton enters JarvisOS while 079 is `planned`.

### 24.3 Kill switches and readiness evidence

Kill switches: canonical halt, App suspension, App/webhook/provider credential revocation, service/queue stop, caps zero, dispatch-workflow disable if later authorized, and protected human recovery. Rollback never force-pushes or erases evidence.

Readiness proves merged dependencies, architecture, full spec, governance; every mandatory proof; exact permissions/rulesets/wrapper/IDs; execution-spine exception; abuse denials; mutually exclusive classifications; no-PR human decisions; reviewer single-flight; authority-stop settlement; branch/PR lifecycle; grant/lease/budget/head/human/merge/provider/finding/release behavior; host/database/secrets/adapters/pricing/caps/gates/vectors/owners/first slice; and no unresolved P0/P1 authority or security blocker. Only readiness may set `ready`.

## 25. Compatibility

No product SQLite migration. Product execution/budget/Hermes/MemoryStore/BLUECAD/events do not become authority. Hosted database is rebuildable. Bootstrap creates a new protected control branch explicitly; no chat/old PR/ref is imported. Existing work requires exact grant/reconciliation and normally a fresh branch. Review remains manual until governance/readiness. Authority versions require additive migration proof. Force-push is never migration.

## 26. Likely implementation scope

After readiness: `services/devloop/`, pinned service manifest/container, fake fixtures, secret-free deployment docs, normal `STATUS.md` transition, and CI only for offline tests.

Not in implementation: `AGENTS.md` amendment, live App/settings/rulesets/secrets, credentials/account data, product runtime, Hermes/MCP/MemoryStore/BLUECAD/process kernel/078. Dependencies must be pinned, justified, scanned, and service-limited; no agent framework.

## 27. Non-goals

No automatic next-spec selection; simultaneous fronts/branches/actors/PRs; autonomous merge/approval/release/deploy/priority/governance/settings; force-push/delete/history rewrite/protected-test mutation; arbitrary shell; provider fallback/bidding/swarm; unbounded loops; untrusted-fork execution; replacement of runtime 059b/Hermes/Actions; raw model/secret canonical storage; outage availability guarantee; or 078/other frozen work.

## 28. Definition result

Ready for the maintainer's merge decision when:

- the diff remains one planning document and 079 remains `planned`;
- section 2.1 remains proposed until merge;
- all transitions are closed and mutually exclusive;
- no-PR human stops have a decision path;
- reviewer dispatch is single-flight per round/head;
- expiry/revocation settles accepted calls before leaving their response state;
- every mandatory proof remains a readiness blocker;
- the execution-spine conflict remains blocked pending governance;
- no mechanism is claimed operational;
- no runtime, workflow, App, provider, secret, ruleset, dependency, or setting is changed;
- exact-head gates pass;
- no current P0/P1 review finding remains;
- the PR stops for explicit human merge.

Merge does not authorize governance, proofs against live JarvisOS, readiness, implementation, provider calls, or automated merge.
