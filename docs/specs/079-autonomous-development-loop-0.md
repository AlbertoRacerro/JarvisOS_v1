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
- bind deterministic gates and review to an exact PR head;
- perform at most two bounded fix/re-review rounds;
- recover from duplicate delivery, process restart, stale local state, and ambiguous API responses;
- truthfully record human merge or close actions even when they occur before system-prepared readiness;
- release a fully reconciled terminal front back to canonical `idle` without erasing history.

The control plane may never merge, enable auto-merge, approve authoritatively, change roadmap priority, infer authorization from repository activity, create a second active front, or turn model output into authority.

## 2. Full-spec and sequencing boundary

This document freezes the proposed v0 contract for:

- canonical state and event integrity;
- authorization, expiry, revocation, recovery, terminalization, and release;
- repository-wide claim and work-branch lease;
- initial implementation before PR creation;
- verified no-change terminalization;
- exact-head branch and pull-request lifecycle;
- deterministic gate and review sequencing;
- implementer/reviewer adapter contracts;
- provider ambiguity, spend, content, secret, and permission boundaries;
- webhook, queue, notification, retention, and recovery behavior;
- isolated proofs, rollout, kill switches, and compatibility.

This PR does not:

- install or configure a GitHub App;
- create a service, database, queue, branch, ruleset, workflow, secret, provider route, or dependency;
- modify `AGENTS.md` or `STATUS.md`;
- invoke a model or paid service;
- authorize readiness, implementation, repository settings, merge, or auto-merge.

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
3. A branch, pull request, label, review, check, workflow, timer, comment, or model message is not authorization.
4. V0 starts only from a maintainer-authored command naming the exact spec, slice, base SHA, scope, adapters, and budget policy.
5. Every side-effect-authorizing transition rechecks grant currency, claim ownership, exact GitHub facts, stop state, role capacity, provider policy, and canonical reservation; mutation additionally requires a valid reconciled lease.
6. The initial implementer request binds the verified absence of a PR for the derived branch; all repair and review requests bind the one recorded PR.
7. A PR is created only after a valid branch delta exists. A verified initial no-change result terminalizes without a PR.
8. Deterministic gates and advisory review inform readiness; the maintainer alone owns merge.
9. Reviewer credentials cannot mutate code; implementer credentials cannot produce the authoritative review verdict.
10. Automated actors cannot merge, auto-merge, force-push, delete protected refs, change settings or secrets, or bypass rulesets.
11. Repository-development provider authority is separate from runtime policy 059b.
12. Planned, blocked, cancelled, dependency-incomplete, expired, or revoked work never starts or continues automatically.
13. Lease expiry, grant expiry, inactivity, process death, or a timer never releases ownership.
14. Any work-head change invalidates all prior head-bound gates, review, and presentation evidence.
15. Human PR actions are recorded factually from every PR-bound active state; observation never retroactively manufactures a clean verdict.
16. Revocation or expiry never clears an existing security, integrity, or ambiguity halt.
17. Safety dominates liveness; indefinite inactivity is valid.

## 4. Selected architecture

### 4.1 Control service

The primary dispatcher is an installed GitHub App operated by a small stateless Python 3.11 FastAPI/ASGI service.

Selected implementation class:

- one OCI container image;
- GitHub REST and Git Data client;
- PostgreSQL 16 for non-authoritative queueing, delivery deduplication, retries, and projections;
- one or more identical service replicas;
- no Redis, agent framework, vector database, browser automation, or second orchestration engine.

The service is outside the JarvisOS product runtime. It does not share JarvisOS SQLite, runtime egress state, runtime provider secrets, or `C:\JarvisOS` data.

### 4.2 Canonical state

Canonical authority lives on a protected branch provisionally named `jarvis-control` in exactly one file:

`.jarvis/development-loop/authority.json`

Comments, checks, workflow runs, PostgreSQL rows, dashboards, and digests are non-authoritative projections and must be rebuildable from the control branch.

### 4.3 Non-authoritative PostgreSQL

PostgreSQL may store:

- webhook delivery IDs and payload digests;
- queued reconciliation jobs and bounded retry metadata;
- cached authority projections;
- provider-request correlation metadata;
- notification deduplication;
- service health and operational audit summaries.

It must never contain the sole copy of a grant, claim, lease, PR binding, gate verdict, review verdict, finding disposition, reservation, terminal outcome, or release decision. Total database loss may delay work but cannot change authority.

## 5. Canonical encoding and integrity

`authority.json` uses deterministic UTF-8 JSON:

- lexicographically sorted object keys;
- compact separators with no insignificant whitespace;
- UTC RFC 3339 timestamps ending in `Z`;
- integer money, counters, durations, and sizes;
- no floating-point values, `NaN`, or infinity;
- lowercase SHA-256 identifiers.

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

Every event binds:

- monotonically increasing sequence;
- deterministic event ID;
- closed event type;
- timestamp;
- effective actor ID, login, and role;
- deterministic idempotency key;
- previous-event digest;
- canonical payload and payload digest;
- event digest.

An identical duplicate is a no-op returning the existing event. Reusing an idempotency key with different bytes is an integrity failure. Sequence and Git ancestry, not timestamps, own ordering.

A valid authority state requires both:

1. an intact in-file event hash chain; and
2. linear Git ancestry on `jarvis-control`.

Missing, reordered, altered, duplicated, forked, force-pushed, or non-linear history causes `control_integrity_failure` and permits no external side effect. V1 has no compaction. Before event 4097 or 2,000,000 canonical bytes, the control plane halts with `authority_capacity_reached` rather than truncating history.

## 6. Closed identifiers, roles, states, and outcomes

### 6.1 IDs

Deterministic prefixes:

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

The Control App derives all authoritative IDs from canonical idempotency inputs. Models and providers never choose them.

### 6.2 Roles

Closed roles:

- `maintainer`
- `control`
- `implementer`
- `reviewer`
- `gate_collector`
- `system_reconciler`

Effective credentials determine role; text cannot self-assert authority.

### 6.3 States

Closed states:

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

### 6.4 Terminal outcomes

- `merged_by_maintainer`
- `closed_without_merge`
- `superseded_by_maintainer`
- `completed_without_pr`
- `authorization_revoked`
- `authorization_expired`
- `abandoned_after_human_decision`

A `completed_without_pr` terminal record is allowed only for the initial implementation request when all section 11.3 no-change conditions pass. It is never used to bypass a required repair, review, or PR.

A human-merge terminal event records separately:

- `prepared_state_at_human_action`;
- `pr_head_at_merge_boundary` — the PR head SHA observed immediately before GitHub applied the merge operation;
- `merge_result_sha` — the resulting merge, squash, or rebased commit SHA reported by GitHub;
- `merge_method` — `merge`, `squash`, `rebase`, or `unknown`;
- actor and timestamp;
- `evidence_status` — `current_clean`, `stale_or_incomplete`, or `not_applicable`.

`pr_head_at_merge_boundary` and `merge_result_sha` are not assumed equal. A normal merge commit, squash merge, or rebase merge usually produces a different result SHA.

### 6.5 Stop reasons

Closed reasons include:

- authorization missing, invalid, expired, or revoked;
- registry/dependency/front conflict;
- claim race lost;
- control integrity or capacity failure;
- scope, base, work-head, or PR mismatch/ambiguity;
- invalid initial no-change claim;
- work head changed after review;
- lease expired pending reconciliation;
- gate missing, stale, cancelled, action-required, infrastructure-failed, flaky, or ambiguous;
- review invalid or inconclusive;
- finding needs human or maximum rounds reached;
- provider disabled or ambiguous;
- cost unknown or cap exceeded;
- secret unavailable or changed;
- security signal;
- destructive action, governance decision, merge boundary, or human decision required.

Generic `unknown`, `provider_error`, or `failed` is forbidden when a precise reason exists.

## 7. Authorization lifecycle

### 7.1 Maintainer commands

Readiness bootstraps one control issue and an allow-list of maintainer numeric GitHub user IDs. An eligible command is:

- newly created, not edited into eligibility;
- authored by an allow-listed numeric ID;
- in the configured repository and control issue;
- exactly formatted as one closed command object;
- revalidated against current SHAs and repository facts.

Comments are command inputs, never canonical authority.

### 7.2 Authorization grant

The authorization command binds:

- repository numeric ID;
- three-digit spec ID;
- bounded slice ID;
- base branch `master` and exact current base SHA;
- normalized allow/deny path globs with deny precedence;
- maximum changed files and diff lines;
- distinct approved implementer and reviewer adapter IDs;
- budget policy ID;
- maximum fix rounds from zero through two;
- optional future expiry no more than 30 days from issue;
- bounded reason.

The normalized scope produces `scope_digest`. The work branch is deterministically derived as `jarvis-work/<run_id>`.

V0 never infers a grant from a `ready` row, branch, PR, label, schedule, chat, previous run, or model recommendation.

### 7.3 Currency and expiry

Every branch, PR, workflow, provider, or reservation side-effect event proves that the grant is present, unrevoked, and unexpired at event commit time.

When expiry is reached:

- no new side-effect-authorizing event may commit;
- if the run is not halted, append `authorization_expired` and enter `awaiting_maintainer`;
- if the run is already halted, append `authorization_expired_while_halted`, preserve `halted`, preserve the original primary stop, and add expiry as an overlay;
- already accepted external work is reconciled and recorded without authorizing follow-on work;
- expiry never releases the claim, lease, branch, PR, reservations, or history.

### 7.4 Revocation

A valid revocation blocks all new work and permits only proven-safe bounded cancellation.

- From a non-halted active state, append `authorization_revoked` and enter `awaiting_maintainer` or a factually justified terminal outcome.
- From `halted`, append `authorization_revoked_while_halted`, remain `halted`, retain the original security/integrity/ambiguity stop as primary, and mark the grant revoked as an additional overlay.

Revocation never functions as recovery, never clears a halt, and never makes terminal release eligible while the original halt remains unresolved.

### 7.5 Recovery

A recovery command binds the exact control head, run, action (`resume` or `terminalize`), target state or outcome, and reason. The system independently reconciles:

- repository and control history;
- work ref and ancestry;
- PR state and head;
- workflows and checks;
- implementer and reviewer requests;
- reservations, usage, and costs;
- lease, grant, and stop overlays;
- security and integrity evidence.

Security or integrity recovery requires referenced remediation evidence. The target must be reachable under the state table.

### 7.6 Release

Release is eligible only from `terminal` after proving:

- no external request, workflow dispatch, reservation, cancellation, integrity anomaly, security anomaly, or provider ambiguity remains active or unresolved;
- work-ref and PR facts match the terminal record, or the terminal outcome is a verified `completed_without_pr` with no PR and no branch delta;
- every halt overlay has been resolved through recovery;
- the expected control head is current.

`front_released` clears active snapshot fields and returns to `idle` while preserving completed-run identity, terminal outcome, PR/ref bindings when present, findings, usage, cost, events, and Git history. Duplicate identical release is a no-op. A later run needs a new authorization grant from `idle`.

## 8. Canonical snapshot

The derived snapshot binds:

- state and active run;
- authorization grant, expiry, revocation, and overlays;
- global claim and branch lease;
- work branch, exact head, optional PR number, PR base/head branch, PR state, ancestry, diff limits, and scope digest;
- exact-head gates;
- review round, reviewed head, reviewer identity, request, verdict, findings, and dispositions;
- integer-micro-USD budget, reservations, finalized/released usage, and role call counts;
- next permitted action;
- primary stop and stop overlays;
- active terminal outcome and last completed run.

Before PR creation, the work snapshot explicitly records `pr_number=null` and `pr_expected_absent=true`.

## 9. Claim, work ref, and lease

### 9.1 Repository-wide claim

`claim_acquired` requires:

- state `authorized`;
- current grant;
- eligible registry and merged dependencies;
- repository-wide vacancy;
- no competing branch owner, PR, or run;
- exact base head equal to grant base SHA;
- current scope, adapter, gate, provider, and budget policies;
- no stop.

One control-branch CAS atomically records the global claim and initial 60-minute lease. Losing or ambiguous writers perform zero external side effects.

### 9.2 Create-only work ref

After claim, the Control App may create only `refs/heads/jarvis-work/<run_id>`:

- in the exact repository;
- at the exact grant base SHA;
- only while canonical state, claim, and lease match;
- only when absent, or idempotently reconcile an existing exact ref.

The App cannot subsequently update, force-update, delete, or author engineering commits on that ref. A mismatched or ambiguous ref halts. Later commits are implementer-only under the lease, with maintainer emergency authority.

### 9.3 Lease

V1 lease:

- duration 60 minutes;
- renewal window begins with 20 minutes or less remaining;
- one active mutation request at a time;
- renewal cannot change grant, scope, round, adapter, provider, or budget.

Every renewal is canonical and requires a current grant plus fully reconciled facts. Lease expiry never releases ownership. It records `lease_expired_pending_reconciliation` and blocks mutation until branch, PR, workflow, provider, reservation, budget, and security facts are reconciled and a renewal commits.

## 10. Exact-head Git CAS

Every canonical transition:

1. reads the exact `jarvis-control` ref;
2. reads the expected parent commit, tree, and authority blob;
3. validates schema, event chain, snapshot, and Git ancestry;
4. re-reads all transition preconditions;
5. computes one deterministic event and replacement file;
6. creates replacement blob and tree from the expected parent tree;
7. creates a commit whose sole parent is the exact expected control head;
8. updates the ref with `force=false`;
9. accepts only an unambiguous update to the candidate commit;
10. on rejection, timeout, disconnect, or ambiguity, performs no external side effect and reconciles.

The Contents API blob update is forbidden as authority CAS.

After ambiguous update, the service rereads ref, ancestry, and event ID. Candidate/event present exactly once means committed; absent means it lost; unresolved ambiguity halts. The same idempotency key never creates a different event.

## 11. Closed state machine

### 11.1 Dispatch authority and conditional PR binding

Only these events authorize model calls:

- `implementation_requested`;
- `gate_repair_authorized`;
- `review_fix_authorized`;
- `review_dispatch_authorized`.

Every dispatch event atomically binds:

- current unexpired and unrevoked grant;
- current claim and no stop;
- exact repository, work ref, base, and head;
- approved role identity and remaining role-call capacity;
- current adapter and provider policy;
- canonical cost/quota reservation, even when projected marginal cost is zero;
- deterministic request idempotency key;
- valid reconciled lease and scope for mutations.

PR binding is conditional and closed:

- the initial `implementation_requested` from `claimed` requires `pr_number=null`, `pr_expected_absent=true`, and a live GitHub search proving that no PR exists for the derived work branch;
- `gate_repair_authorized`, `review_fix_authorized`, and every `review_dispatch_authorized` require the one recorded PR, exact PR base/head branch, and exact current PR head;
- no other no-PR model dispatch is permitted.

Review dispatch additionally binds exact eligible gates on the recorded PR head.

No other event or prose authorizes a model call.

### 11.2 Transition table

| Current state | Event | Binding preconditions | Next state | Side effect after commit |
| --- | --- | --- | --- | --- |
| `idle` | `authorization_recorded` | valid maintainer command | `authorized` | none |
| `authorized` | `claim_acquired` | section 9.1 and successful CAS | `claimed` | create/reconcile exact work ref |
| `claimed` | `work_branch_recorded` | exact derived ref at grant base; PR absent | `claimed` | none |
| active non-halted | `lease_renewed` | current grant, lease, reconciliation, renewal window | same | none |
| `claimed` | `implementation_requested` | section 11.1 initial no-PR authority | `implementing` | one initial implementer request |
| `implementing` | `initial_work_head_recorded` | initial request; strict descendant; non-empty in-scope diff | `awaiting_pr` | none |
| `implementing` | `initial_no_change_completed` | section 11.3 verified initial no-change | `terminal` | none |
| `implementing` | `repair_work_head_recorded` | repair/fix request; strict descendant; in-scope diff; recorded PR exists | `awaiting_pr` | none |
| `implementing` | `repair_no_change_recorded` | repair/fix request; exact prior head unchanged; recorded PR exists; bounded evidence | `awaiting_pr` | none |
| `implementing` | `provider_ambiguous` | accepted request with unresolved result or charge | `halted` | none |
| `awaiting_pr` | `pr_creation_authorized` | initial delta or recorded-PR rebind; exact branch/head/base; grant current | `awaiting_pr` | create/reconcile one PR |
| `awaiting_pr` | `pr_recorded` | exactly one matching open PR and exact head | `awaiting_gates` | observe/request deterministic gates only |
| `awaiting_gates` | `gates_passed` | all required exact-head gates green | `awaiting_review` or `awaiting_re_review` | none |
| `awaiting_gates` | `gate_defect_reproduced` | deterministic in-scope defect | `fix_required` | none |
| `fix_required` | `gate_repair_authorized` | gate defect plus section 11.1 PR/lease/dispatch authority | `implementing` | one implementer repair |
| `awaiting_gates` | `gate_ambiguous_or_infra` | stale, flaky, cancelled, missing, action-required, or infrastructure ambiguity | `halted` or `awaiting_maintainer` | none |
| `awaiting_review` or `awaiting_re_review` | `review_dispatch_authorized` | section 11.1 PR/gate/review authority | same | one reviewer request |
| `awaiting_review` or `awaiting_re_review` | `provider_ambiguous` | accepted review with unresolved result or charge | `halted` | none |
| `awaiting_review` | `review_clean` | valid structured response on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_review` | `review_findings_recorded` | valid normalized findings on exact head | `fix_required` | deterministic triage only |
| `awaiting_review` or `awaiting_re_review` | `review_inconclusive` | valid inconclusive response | `awaiting_maintainer` | none |
| `fix_required` | `findings_disposed_no_change` | evidence-backed false or superseded findings | `awaiting_re_review` | none |
| `fix_required` | `review_fix_authorized` | genuine blocker, section 11.1 PR/lease/dispatch authority, round remains | `implementing` | one implementer fix |
| `fix_required` | `finding_requires_human` | scope, security, ambiguity, dependency, or round boundary | `awaiting_maintainer` | none |
| `awaiting_re_review` | `review_clean` | valid structured response on exact head | `awaiting_maintainer` | presentation only |
| `awaiting_re_review` | `review_findings_recorded` | valid findings and rounds remain | `fix_required` | deterministic triage only |
| `awaiting_re_review` | `maximum_rounds_reached` | negative result after round two | `awaiting_maintainer` | none |
| any PR-bound active state without active/ambiguous external request | `work_head_changed` | current PR head is a valid scoped descendant different from recorded head | `awaiting_pr` | none |
| any PR-bound active state | `work_head_ambiguous` | non-descendant, force-push, scope violation, or unresolved concurrent request | `halted` | none |
| any PR-bound active state | `human_merge_observed` | human action reconciled; no active/ambiguous request remains | `terminal` | none |
| any PR-bound active state | `human_close_observed` | human action reconciled; no active/ambiguous request remains | `terminal` | none |
| active non-halted | `authorization_expired` | grant expiry reached | `awaiting_maintainer` | reconcile accepted work only |
| `halted` | `authorization_expired_while_halted` | grant expiry reached | `halted` | none; preserve primary stop |
| active non-halted | `authorization_revoked` | valid revocation | `awaiting_maintainer` or factually justified `terminal` | proven-safe cancellation only |
| `halted` | `authorization_revoked_while_halted` | valid revocation | `halted` | none; preserve primary stop |
| any non-terminal | `security_halt` | authenticated compromise evidence or verified anomaly | `halted` | none |
| `halted` | `human_recovery_recorded` | valid command and complete reconciliation | reachable safe state or `terminal` | recorded recovery action only |
| `terminal` | `front_released` | section 7.6 | `idle` | none |

A PR-bound active state is any active state whose snapshot contains a recorded PR, including `awaiting_pr` during rebinding, `awaiting_gates`, `awaiting_review`, `fix_required`, `awaiting_re_review`, and `awaiting_maintainer`.

If the work head changes while an implementer or reviewer request is active, the system first reconciles that request. If the outcome cannot be determined exactly, it records `provider_ambiguous` or `work_head_ambiguous` and halts. It never applies `work_head_changed` while silently ignoring an in-flight action.

### 11.3 Verified initial no-change terminalization

`initial_no_change_completed` is allowed only when all of the following are true:

1. the active request is the first `implementation_requested` for the run;
2. the provider reports completed, not ambiguous;
3. the work ref still equals the exact grant base SHA;
4. comparison against the grant base shows zero changed files and zero diff lines;
5. no PR exists for the derived branch and no PR-creation event was committed;
6. the implementer call consumed its canonical reservation and usage is finalized;
7. the adapter returns a bounded structured no-change reason and evidence digest;
8. a deterministic verifier confirms either that the authorized slice is already satisfied at the pinned base or that the requested implementation cannot produce an in-scope change without crossing a recorded human/governance boundary;
9. no active request, reservation, lease ambiguity, security signal, or integrity stop remains.

The event terminalizes with outcome `completed_without_pr`, records `evidence_status=not_applicable`, and preserves the claim and branch history until explicit `front_released`.

A provider assertion alone is insufficient. If the deterministic verifier cannot confirm the reason, record `initial_no_change_invalid` and enter `awaiting_maintainer` or `halted` with no PR creation.

A no-change result from a gate repair or review fix never uses `completed_without_pr`. It requires the already recorded PR, records `repair_no_change_recorded`, returns through the same PR, reruns exact-head gates, and receives re-review.

### 11.4 Human PR outcomes from every PR-bound state

The maintainer may merge or close the recorded PR at any time. The ledger must never strand the claim because the human acted before `awaiting_maintainer`.

Before terminalization, all accepted implementer/reviewer/workflow/provider requests and reservations are reconciled. Unresolved ambiguity causes a halt first; human recovery later records the already-observed PR outcome.

For a merge, record:

- the PR head SHA observed immediately before the merge operation: `pr_head_at_merge_boundary`;
- the resulting Git commit SHA: `merge_result_sha`;
- the merge method;
- actor, timestamp, and prior state;
- gate/review evidence bound to the PR head.

`evidence_status=current_clean` is valid only when:

1. `pr_head_at_merge_boundary` equals the exact current head that passed every required gate and received the current clean review;
2. no later head-change or invalidation event exists;
3. the PR identity, base, branch, scope, and gate/review policy all match.

The merge-result SHA is recorded separately and is not compared directly to the reviewed PR head. A merge commit, squash merge, or rebase merge may produce a different result SHA while still merging the exact reviewed PR head.

When the PR head at the merge boundary was not current-clean, record `evidence_status=stale_or_incomplete`. The terminal outcome remains factually `merged_by_maintainer`, but the ledger must not claim that the system prepared a clean merge.

For close or supersede, record the actual PR state, actor, timestamp, prior state, and corresponding terminal outcome. No replacement PR is created automatically.

### 11.5 Head invalidation

Any PR-head change invalidates gates, review, presentation, and clean-merge eligibility.

From every PR-bound active state with no active or ambiguous external request, a valid scoped descendant records `work_head_changed` and returns to `awaiting_pr`, where the same PR is rebound to the new exact head before gates and review.

A non-descendant, force-push, scope violation, unexpected actor, or unresolved concurrent request records `work_head_ambiguous` and halts.

### 11.6 Idempotent PR lifecycle

`pr_creation_authorized` binds repository, run, derived branch, exact head, base, scope, and operation version.

For the initial implementation, PR creation is eligible only after `initial_work_head_recorded` proves a strict descendant with a non-empty in-scope diff. It is forbidden after `initial_no_change_completed` or `initial_no_change_invalid`.

Reconciliation:

- zero matching PRs: create exactly one non-draft PR with base `master`, derived head, and bounded run/scope marker;
- exactly one correct open PR: reuse it;
- duplicate, wrong base/head/marker, fork, or unknown state: fail closed;
- previously recorded PR closed by the maintainer: never create a replacement;
- timeout after create: search and validate before retry; never create a second PR.

`pr_recorded` binds PR numeric ID, repository, base, head branch, exact current work head, operation key, and state. Gates and review are forbidden before it. Every code-changing repair and every repair no-change rebinds the same PR through `awaiting_pr`; a second PR is forbidden.

## 12. Branch and scope contract

Exactly one work branch exists. The Control App creates it once; the implementer authors later engineering commits; automated force-push and deletion are denied; PR base is `master`; forks are unsupported.

Before every mutation request and after every resulting head, verify:

- normalized paths and deny precedence;
- changed-file and diff-line limits;
- linear expected ancestry;
- submodules, Git LFS pointers, symlink escapes, binary additions, and generated-secret risks;
- scope-verification digest.

Denied absent exact separate authority:

- `AGENTS.md`;
- `.github/workflows/**` and `.github/CODEOWNERS`;
- repository settings or ruleset exports;
- secrets, credentials, keys, tokens, certificates, and environment files;
- maintainer-owned conformance tests;
- vendored dependencies and lockfiles;
- canonical authority file.

## 13. Deterministic gates

Readiness freezes exact check names, workflow/action pins, and path conditions. Initial gates include:

- spec-status registry;
- manual-review offline boundary;
- BLUECAD license boundary;
- Ruff;
- full backend Pytest;
- BLUECAD geometry canary;
- frontend build when required;
- strict real-tool proof when relevant;
- 079 service unit, integration, conformance, and reconstruction tests.

Eligible evidence is successful, repository-bound, exact-head, policy-matching, and not stale, required-but-skipped, cancelled, action-required, or superseded.

One zero-model-cost infrastructure rerun is allowed per collection only when no source or assertion defect is indicated. Further or ambiguous infrastructure failure halts. Tests and workflows may not be weakened to obtain green status.

## 14. Reviewer and finding identity

Reviewer credentials are read-only for repository, code, PR, checks, and statuses. They have no contents write, workflow dispatch, merge, settings, secret, ref-delete, or ruleset authority. Reviewer and implementer effective identities differ.

A review request binds repository, spec, slice, scope/non-goals, base/head, exact diff, PR, eligible gates, round, prior findings/fixes, content digest, provider policy, reservation, and idempotency key.

Response JSON contains:

- exact reviewed head;
- verdict `clean`, `findings`, or `inconclusive`;
- bounded summary;
- findings containing severity, category, path, line, claim, reproduction, and suggested resolution.

The reviewer must not provide authoritative finding IDs. After schema validation and deterministic normalization, the Control App derives each `finding_<32 hex>` from review round, exact head, normalized finding digest, and occurrence index. A model-supplied `finding_id` is rejected as an unknown field.

Maximum 50 findings and 2,000 characters per text field. Malformed, oversized, wrong-head, unknown-field, or non-JSON output is invalid. Inconclusive review records a canonical human stop. P0/P1 block; P2 blocks only if independently reproduced as a binding violation; P3 is advisory.

## 15. Finding disposition and bounded rounds

Closed dispositions:

- `reproduced`;
- `accepted_without_reproduction`;
- `false_positive`;
- `superseded`;
- `needs_human`.

Every disposition is evidence-bound. Initial review is round zero. Maximums:

- two fix rounds;
- three reviewer calls;
- three implementer calls;
- one fix attempt per negative round.

Every code change returns through PR rebinding, exact-head gates, and review. An evidence-backed no-change rebuttal still requires re-review. Negative review after round two stops. Scope expansion, destructive action, governance/secret change, or new dependency requires human action.

## 16. Adapter contract and execution-spine governance block

Adapter requests bind repository/installation, work branch/head, optional PR according to section 11.1, spec/slice, scope/non-goals, task or findings, provider/budget policy, reservation, and idempotency. Responses bind provider request/status, resulting head or no-change, safe summary/digests, usage/cost/idempotency, and error class.

The initial task kind permits `pr_number=null` only under the exact initial no-PR preconditions. Gate repair, review fix, and review tasks require the recorded PR.

Adapters cannot change authority. Implementer writes only the work branch. Neither actor may merge, approve, force-push, delete refs, change settings/secrets, or write control authority. An accepted ambiguous outcome halts without retry unless exact provider idempotency and reconciliation prove the result.

Current `AGENTS.md` requires all AI calls through product `run_ai_task` and `ai_jobs`. The selected hosted service does not share product SQLite or runtime egress state. Live 079 calls are therefore blocked under current governance.

The proposed v0 governance route is a narrow repository-development exception: approved 079 adapter calls may occur outside product `run_ai_task` only with committed grant, claim, exact branch/head, conditional PR binding, scope, actor identity, provider policy, reservation, idempotency, and durable 079 usage/cost evidence.

That exception requires a separate `AGENTS.md` PR and dated readiness evidence. Until both merge, no live implementer or reviewer dispatch is authorized. If the exception is rejected, this full spec must be amended to use a separately authenticated product execution-spine boundary.

## 17. Spend and provider authority

Repository-development budget is separate from runtime 059b and uses integer micro-USD.

Absolute v1 ceilings:

- 5,000,000 per request;
- 20,000,000 per run;
- 25,000,000 per UTC day;
- 100,000,000 per calendar month.

Defaults are zero. `cost_unknown` is a hard stop.

Every implementer or reviewer call reserves amount, quota, and role-call count canonically before dispatch. Missing reservation, stale pricing, exceeded cap/capacity, unknown cost/quota, or provider fallback produces zero call. Final usage finalizes or releases the reservation. V1 has no fallback provider.

Marginal zero requires current account/plan, entitlement, remaining quota, and timestamp evidence. Hosting and Actions costs are tracked separately.

## 18. Content, secrets, and prompt injection

External material is limited to the exact spec, scope, diff, findings, PR when present, and gates needed for the task. Secrets, credentials, environment values, keys, tokens, headers, and unrelated records are excluded.

Issue, PR, source, test, artifact, log, and model text is untrusted data. It cannot change policy, role, provider, budget, tests, scope, authority, or merge boundary. Deterministic policy constructs every request.

No raw provider body enters canonical authority. Safe digests, summaries, IDs, usage, and cost are permitted. S4 or secret-bearing content remains denied absent a later repository-development egress specification.

## 19. GitHub permissions and rulesets

Candidate App permissions:

- metadata read;
- contents read/write;
- pull requests read/write;
- checks, statuses, and Actions read;
- issues read/write.

Actions write is absent unless readiness proves an exact need. Administration, environments, secrets, members, deployments, packages, security-alert mutation, hook mutation, and ruleset bypass are denied.

A capability wrapper allow-lists repository ID, endpoint, method, ref, path, canonical state, and request schema, and audits denials.

Separate effective credentials are required for Control App, implementer, reviewer, and maintainer.

Rulesets must prove:

- `master`: PR and required checks, no automated bypass, no force-push/delete, human-only merge;
- `jarvis-control`: Control App or explicit human recovery only, linear history, no force-push/delete/non-fast-forward;
- `jarvis-work/*`: Control App create-only at exact base, then implementer/maintainer write, reviewer read-only, no automated force-push/delete, PR base `master`.

Abuse tests cover merge, approval, force-push, deletion, out-of-scope writes, settings/secrets, post-create App work-ref mutation, and unauthorized PR mutation.

## 20. Webhook, queue, and service API

Subscribed events are limited to:

- newly created issue comments;
- pushes on master, control branch, and active work branch;
- pull request, review, review-comment, and workflow-run events;
- installation suspension or deletion.

Edited authorization comments never create authority.

`POST /github/webhook` validates the signature over the raw body with constant-time comparison before JSON parsing.

Missing or invalid signatures:

- return authentication failure;
- are rate-limited at edge and application layers;
- are logged with redacted bounded metadata;
- create no trusted delivery row, queue item, canonical event, `security_signal`, or halt;
- reveal no repository, installation, or command existence.

Authenticated processing validates installation/repository/event, stores delivery digest, acknowledges within 10 seconds, performs no request-thread side effect, and queues reconciliation.

Canonical security halt is reserved for authenticated or independently verified anomalies, such as signed delivery-ID digest mismatch, authenticated identity contradiction, verified history tamper, verified credential misuse, unauthorized API success, or verified scope/secret escape.

Other endpoints are only health and readiness probes. There is no public admin mutation endpoint.

Queue ownership is operational only. Duplicate jobs converge canonically. Pure reconciliation retries are bounded. Side-effect retry requires a committed event and proven idempotency. Webhook order is never trusted.

Retention:

- delivery evidence 30 days;
- queue/projections 90 days;
- service logs 30 days;
- no raw model bodies, secrets, or authorization headers in logs.

Canonical GitHub RPO is zero committed events; database RPO is 24 hours; service RTO target is four hours. GitHub uncertainty stops indefinitely.

## 21. Presentation and notifications

The service may maintain at most:

- one non-authoritative check;
- one sticky PR status comment;
- one control-issue status comment;
- one weekly digest.

Updates occur only after canonical state changes and are idempotent.

Between weekly reviews, direct maintainer notification is limited to a human decision, authenticated security signal, or budget overrun/disabled cost authority.

Weekly digest:

- timezone `Europe/Rome`;
- Monday 08:00 local;
- at most one per seven days;
- omitted when no canonical state changed;
- never grants authority.

## 22. Security and supply chain

Implementation requires short-lived tokens, managed secret storage, credential rotation, immutable dependency/action pins, SBOM, dependency/container scanning, outbound allow-listing, repository/SHA validation, and denial of untrusted-fork execution with write-capable or secret-bearing credentials.

The webhook process never executes PR code. Invalid unauthenticated traffic does not canonically halt. Authenticated or independently verified compromise evidence does.

## 23. Verification and acceptance

### 23.1 Offline tests

With fake GitHub, PostgreSQL, implementer, and reviewer actors, prove:

- canonical encoding, event chains, reconstruction, schema rejection, and duplicate convergence;
- every state-table allow/deny edge;
- grant issue, expiry, revocation, halted overlays, recovery, terminalization, and release;
- repository-wide claim race and lease lifecycle;
- create-only work ref and denial of later App mutation;
- initial implementation dispatch with explicit PR absence;
- strict-delta initial result creates one PR before gates;
- verified initial no-change terminalizes as `completed_without_pr` and never creates a PR;
- invalid initial no-change stops and cannot create a PR;
- repair no-change retains and rebinds the existing PR;
- no duplicate PR after timeout/replay;
- same-PR rebinding after every head change;
- `work_head_changed` from every PR-bound active state;
- `work_head_ambiguous` while requests are active or ancestry is invalid;
- every dispatch requires current grant, role capacity, provider policy, reservation, and applicable lease;
- exact-head gate and review invalidation;
- inconclusive review and provider ambiguity stop states;
- deterministic Control-App finding IDs;
- human merge/close reconciliation from every PR-bound active state;
- `pr_head_at_merge_boundary` separate from `merge_result_sha` for merge, squash, and rebase strategies;
- `current_clean` based on the PR head, not the result commit SHA;
- revocation or expiry while halted preserves the original halt and recovery path;
- terminal release after PR and no-PR outcomes preserves history and permits a later authorization;
- invalid webhook signatures cause no canonical state change;
- inactivity creates no repeated calls or notifications.

### 23.2 Disposable-repository proofs before readiness

Every architecture-closure proof remains mandatory, including:

1. multi-dispatcher single-winner claim;
2. stale parent/ref rejection even with unchanged blob;
3. timeout-after-CAS reconciliation exactly once;
4. signed webhook replay convergence after database loss;
5. reconstruction after all external state is deleted;
6. history-tamper halt;
7. lease expiry never starts another claimant;
8. create-only exact-base work ref and denial of later App mutation;
9. initial no-PR implementer dispatch and verified PR absence;
10. strict-delta result creates one exact-head PR before gates;
11. verified no-change creates no PR and terminalizes; invalid no-change stops;
12. one PR only, including create timeout and repair rebinding;
13. PR mismatch, fork, duplicate, or closed-state fail-closed behavior;
14. grant expiry before each dispatch creates zero new calls;
15. reservation, role capacity, and valid lease gates;
16. head change from every PR-bound active state invalidates evidence;
17. active-request head ambiguity halts;
18. merge, squash, and rebase cases record PR head and result SHA separately;
19. clean evidence is determined from the PR head at the merge boundary;
20. human merge/close from every PR-bound active state terminalizes truthfully;
21. revocation/expiry while halted preserves the halt and recovery path;
22. inconclusive review, provider ambiguity, deterministic finding IDs, and release/sequential-run behavior;
23. automated credential denial for merge, approval, force-push, deletion, settings/secrets, and out-of-scope writes;
24. reviewer/implementer separation;
25. untrusted-fork and prompt-injection resistance;
26. cost and duplicate-charge stops;
27. GitHub outage and kill-switch recovery;
28. invalid unsigned traffic cannot halt, while authenticated verified anomaly does;
29. inactivity and replay create no noise or duplicate calls.

### 23.3 Repository gates and conformance

Implementation must pass repository Pytest, Ruff, status checks, existing canaries, and deterministic service tests. CI may not call a live model, paid service, or production repository setting.

Readiness freezes maintainer-owned conformance vectors for every authority property above. Implementation agents may not weaken those vectors.

## 24. Governance, rollout, readiness, and kill switches

### 24.1 Required `AGENTS.md` amendment

A separate PR must explicitly amend:

1. manual-only/explicit-only development review and Codex dispatch rules; and
2. the hard `run_ai_task`/`ai_jobs` invariant.

The narrow proposed exception permits repository-development model calls outside product `run_ai_task` only through the approved 079 adapter when a canonical run has a current grant, claim, exact branch/head, conditional PR binding, scope, actor identity, provider policy, reservation, idempotency, and durable 079 usage/cost evidence.

The exception continues to forbid automatic spec selection, merge, auto-merge, priority change, workflow/ruleset bypass, force-push, branch deletion, settings/secrets, destructive action, scope expansion, provider fallback, or work after expiry, revocation, security, cost, integrity, ambiguity, or human-decision stop.

Until that amendment and dated readiness merge, no live model dispatch is authorized.

### 24.2 Rollout and proof order

1. Human merge of this PR accepts the documentary full spec and section 2.1 sequencing amendment; 079 remains `planned` and all mechanisms remain unavailable.
2. Merge the narrow governance amendment, dormant until readiness.
3. Build the proof prototype only in a disposable repository or separate fixture, with fake actors and zero paid calls.
4. Execute every architecture-closure proof before readiness.
5. Optionally run an explicitly approved read-only JarvisOS shadow with no claims, ref/PR writes, workflows, or providers.
6. A dated readiness PR records host, App/actor IDs, rulesets, adapters, current pricing/caps, proof outputs, conformance vectors, owners, and rollback; only it may set 079 `ready`.
7. After readiness, implement in one bounded PR.
8. After implementation and a separate operational grant, run one low-risk documentation-only activation with human merge.
9. Broader use requires separate approval after first-run evidence.

No implementation skeleton enters JarvisOS while 079 is `planned`.

### 24.3 Kill switches

Required independent stops:

- canonical halt event;
- App installation suspension;
- App key and webhook-secret rotation or revocation;
- provider credential revocation;
- service and queue-consumer stop;
- provider caps set to zero;
- dispatch workflow disable if one is later authorized;
- protected human recovery from the last verified control commit.

Rollback means halt, reconstruct, and record. It never force-pushes or erases evidence.

### 24.4 Readiness evidence

079 remains `planned` until a dated readiness PR proves:

- dependencies and repository-wide vacancy;
- merged architecture, full spec, and governance amendment;
- every mandatory disposable-repository proof;
- exact App permissions, rulesets, capability wrapper, and actor IDs;
- execution-spine exception;
- automated credential abuse denials;
- initial no-PR dispatch and verified no-change terminalization;
- work-ref and PR lifecycle;
- grant/lease/reservation/call-capacity controls;
- head changes from every PR-bound state;
- human merge/close reconciliation and merge-method SHA semantics;
- halted revocation/expiry recovery;
- provider ambiguity, finding IDs, release, and sequential runs;
- selected host, database, secret custody, adapters, current pricing/quota, approved caps, gates, vectors, implementation owner, rollback owner, and bounded first activation;
- no unresolved P0/P1 authority or security blocker.

Only that PR may set `ready`.

## 25. Compatibility and migration

- No product SQLite migration is authorized.
- Product execution spine, runtime budget, Hermes, MemoryStore, BLUECAD, and product events do not become control-plane authority.
- Hosted PostgreSQL starts at schema v1 and remains rebuildable.
- Bootstrap creates a new protected control branch through explicit human action; no chat, old PR, or old branch is imported as authority.
- Existing work requires an exact grant and reconciliation and normally uses a fresh derived branch.
- Existing review workflows remain manual until governance and readiness authorize 079.
- Authority schema changes require additive versioning and migration proof.
- Force-push or history rewrite is never migration.

## 26. Likely implementation scope

After readiness, expected bounded paths are:

- `services/devloop/`;
- pinned service dependency/lock and OCI definitions;
- fake GitHub/implementer/reviewer fixtures;
- secret-free deployment documentation;
- normal `STATUS.md` implementation-state update;
- CI changes only for offline deterministic service tests.

Not part of implementation PR:

- the preceding `AGENTS.md` amendment;
- live App settings, rulesets, or secrets;
- provider credentials or raw account data;
- product backend, frontend, or runtime modules;
- Hermes, MCP, MemoryStore, BLUECAD, process-kernel, or 078 work.

New dependencies must be pinned, justified, scanned, and service-limited. No agent framework is authorized.

## 27. Binding non-goals

V0 does not provide:

- automatic next-spec selection;
- simultaneous fronts, branches, implementers, reviewers, or PRs;
- autonomous merge, approval, release, deployment, priority, governance, settings, or secrets;
- force-push, branch deletion, history rewrite, or protected-test mutation;
- arbitrary shell access beyond adapter and scope;
- provider fallback, bidding, routing, or AI swarm;
- unbounded review/fix loops;
- untrusted-fork execution;
- replacement of runtime 059b, Hermes, or GitHub Actions;
- canonical storage of raw model bodies or secrets;
- guaranteed liveness during outages;
- implementation of 078 or another frozen front.

## 28. Definition result

This full-spec PR is ready for the maintainer’s merge decision when:

- it remains a one-document planning diff;
- 079 remains `planned` with no Implementation PR;
- section 2.1 honestly presents the sequencing amendment for merge approval rather than treating it as already effective;
- architecture, authority, expiry/revocation overlays, initial no-PR dispatch, verified no-change terminalization, branch/PR lifecycle, dispatch, lease, head invalidation from every PR-bound state, human outcomes, merge-method SHA semantics, provider ambiguity, finding identity, permissions, cost, tests, rollout, compatibility, and kill switches are explicit;
- every mandatory proof remains a hard readiness blocker;
- the execution-spine conflict remains blocked pending governance;
- no unproven mechanism is claimed operational;
- no runtime, workflow, App, provider, secret, ruleset, dependency, or setting is created or changed;
- exact-head repository gates pass;
- all review threads are resolved or obsolete with no current P0/P1 finding;
- the PR stops for explicit human merge.

Merging this specification does not authorize the governance amendment, isolated proofs against live JarvisOS, readiness, implementation, external provider calls, or automated merge.
