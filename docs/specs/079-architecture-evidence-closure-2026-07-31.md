# Spec 079 — architecture and evidence closure

**Date:** 2026-07-31  
**Pinned baseline:** `d5441f64b1b053d909a15817af70c38a07f6bd0c`  
**Registry status:** `planned`  
**Authority:** explicit maintainer instruction to proceed after merge of PR #204  
**Evidence companion:** `079-architecture-source-evidence-2026-07-31.md`

---

## 1. Decision boundary

This document performs only promotion-ladder step 2 for spec 079: choose the primary state substrate and dispatcher architecture, produce threat/cost/permission analyses, and reject unsafe alternatives.

It does **not** authorize:

- a GitHub App installation or hosted service;
- a workflow, scheduler, daemon, webhook endpoint, queue, database, or secret;
- automatic Codex, Claude, reviewer, or fix dispatch;
- a live model call or paid-service execution;
- repository-setting, ruleset, branch-protection, permission, label, or secret changes;
- the full 079 specification, governance amendment, readiness promotion, or implementation;
- auto-merge or agent-owned merge authority.

079 remains `planned`. The next ladder step is a separately authorized full specification after the proof gaps listed here are closed or explicitly carried as readiness blockers.

## 2. Failure-mode-first conclusion

The primary failure is not loss of a chat session. It is **two actors both believing they own the one active development front** and performing irreversible or paid work from stale authority.

A safe design therefore cannot treat any of these as authority by itself:

- a running GitHub Actions job;
- an issue label or sticky comment;
- an open branch or pull request;
- a webhook delivery;
- a model verdict;
- an external queue or database row;
- a local process lease;
- elapsed time or lease expiry.

The first externally visible action of a run must occur only after one GitHub-owned, repository-wide claim transition succeeds against the current canonical state. A loser in a race must perform no branch mutation, workflow dispatch, review request, model call, or spend.

## 3. Selected architecture

### 3.1 Primary dispatcher: installed GitHub App

Select an **installed GitHub App hosted as a small event-driven control service** as the primary dispatcher/resumer.

The App is selected because it provides:

- an independently identifiable installation actor;
- short-lived installation tokens with repository and permission scoping;
- signed webhook delivery and stable delivery identifiers;
- direct read access to pull requests, commits, checks, reviews, and workflow state;
- operation without a maintainer workstation remaining online.

The App is a dispatcher and policy enforcer, not an engineering authority. It may request or coordinate allowed actions only after canonical state authorizes the transition.

### 3.2 Canonical state substrate: one protected control branch and one authority file

Select a dedicated protected branch named provisionally:

`jarvis-control`

and one canonical file named provisionally:

`.jarvis/development-loop/authority.json`

The exact names may change in the full spec, but the one-branch/one-file property is binding unless later evidence disproves it.

The file must contain:

- schema version and repository identity;
- monotonically increasing sequence;
- current derived snapshot;
- an ordered event list;
- each event's stable ID, actor, transition, timestamp, idempotency key, payload digest, and previous-event digest;
- the globally claimed spec/slice/front, or explicit vacancy;
- work-branch lease state;
- exact base/head/PR bindings;
- gate and review evidence references;
- budget/security stop state;
- next permitted action or human decision;
- terminal or paused reason.

Each transition replaces the single file while presenting the current blob identity and expected control-branch head. The resulting commit becomes the durable transition evidence. Concurrent writers must be treated as a race: one succeeds; every stale writer rereads, replays, and re-evaluates from GitHub before doing anything else.

This is a **candidate compare-and-swap design, not yet a proven atomicity result**. The disposable-repository race proof in section 12 is mandatory before a full spec may claim that the GitHub endpoint and branch/ruleset configuration provide the required single-winner semantics.

### 3.3 Why one file

A transition must not require an independently updated event file, snapshot file, issue comment, database row, and lease record. Multi-object writes create partial-commit states and ambiguous recovery.

One canonical file makes the authoritative transition one repository write. Views, comments, check runs, dashboards, queue rows, and weekly summaries are projections only and must be rebuildable.

The event list can grow. Compaction, if ever needed, requires a separately specified checkpoint event that preserves the previous terminal digest and cannot occur during an active front. Silent truncation is forbidden.

### 3.4 External queue and database

The hosted dispatcher may use a durable queue and database for:

- asynchronous webhook processing;
- `X-GitHub-Delivery` deduplication;
- bounded retries and backoff;
- observability;
- cached projections;
- short-lived worker coordination.

They are **non-authoritative and rebuildable**. Losing them may delay work but must not change who owns the active front or which transition is legal.

### 3.5 GitHub Actions role

GitHub Actions is retained only as an ephemeral worker and deterministic-gate surface:

- run repository tests and proofs;
- expose check/workflow conclusions tied to an exact commit;
- optionally run a later bounded adapter after canonical authorization.

Actions concurrency groups are not the global authority lock. Workflow ordering is not assumed. A queued/running workflow does not prove authorization, and cancelling or replacing a pending workflow cannot release the repository-wide front.

### 3.6 Actor separation

The future system requires distinct effective identities:

1. **Control App** — reads GitHub state and writes only canonical control transitions and bounded presentation artifacts.
2. **Implementer actuator** — may mutate only the recorded work branch and scope; it cannot review or merge.
3. **Reviewer actuator** — read-only over code and evidence; it may emit structured findings but has no contents-write capability.
4. **Maintainer** — owns priority, governance exceptions, secret/settings changes, destructive actions, external-spend exceptions, and merge.

A single vendor may supply more than one model, but one credential or actor must not simultaneously possess implementer, reviewer, and merge authority.

The exact implementer/reviewer provider is deliberately not selected here. Selecting a dispatcher does not authorize an external model.

## 4. Transition topology

The selected control flow is:

1. GitHub emits a subscribed event.
2. The service validates HTTPS transport, webhook signature, event type, repository/installation identity, and delivery ID.
3. The handler acknowledges quickly and enqueues the delivery; it performs no model call or branch mutation in the webhook request path.
4. A worker deduplicates the delivery, reads the canonical control branch/file, verifies the event hash chain, and reconstructs current state.
5. Deterministic policy computes either one permitted transition or a precise no-op/stop.
6. For a claim or lease transition, the worker attempts the single canonical conditional write.
7. Only after that write succeeds may it invoke the next bounded action.
8. The action result is reconciled against live GitHub state and written as another canonical event.
9. A changed implementation head invalidates all previous head-bound gate and review evidence.
10. Any ambiguity writes or preserves a paused/halted state and requests human action only when required by repository rules.

A scheduler may wake the dispatcher for lease reconciliation or a weekly digest, but a timer is never authorization.

## 5. Repository-wide front claim and lease semantics

### 5.1 Global front claim

The global claim transition must atomically establish:

- previously vacant or explicitly recoverable front state;
- authorized spec and bounded slice;
- scope digest;
- base branch and exact base SHA;
- intended work branch;
- claimant identity;
- claim sequence and idempotency key;
- maximum lifetime and reconciliation deadline;
- first permitted action.

No work-branch lease may exist without a valid global claim.

### 5.2 Work-branch lease

The branch lease serializes mutation inside the already claimed front. It does not authorize another front, broaden scope, or replace the global claim.

A lease expiry does not automatically free the front. Recovery must first reconcile:

- work branch and current head;
- open/closed/merged pull requests;
- running, queued, cancelled, or completed workflows;
- outstanding model/provider requests where observable;
- unrecorded commits or review comments;
- security and budget stops.

Only an explicit canonical `lease_recovered`, `front_released`, or terminal event may change ownership.

### 5.3 Idempotency

Every side-effecting transition and external request must carry a deterministic idempotency key derived from at least:

- repository identity;
- development-run ID;
- transition kind;
- canonical sequence;
- exact target head where applicable;
- review/fix round;
- provider/adapter identity where applicable.

Duplicate delivery must converge to the existing result. A retry may inspect but must not duplicate commits, comments, reviews, workflow dispatches, model calls, or charges.

## 6. Permission model

### 6.1 Candidate minimum App permissions

The full spec must validate a minimal installation permission set. The starting candidate is:

- metadata: read;
- contents: read/write, required for the control file and only later for explicitly authorized branch operations;
- pull requests: read/write, for bounded metadata, comments, and review requests;
- checks: read;
- commit statuses: read;
- actions: read, plus narrowly justified write only if workflow dispatch/rerun is selected;
- issues: read/write only if human-decision requests use issue/PR comments.

Do not grant administration, environments, secrets, organization members, deployments, packages, security-alert mutation, repository-hook mutation, or ruleset bypass unless a later proof demonstrates an unavoidable requirement. No such requirement is established here.

### 6.2 Blocker: GitHub permissions are not path capabilities

`contents: write` is broader than “append the control file” or “write one authorized work branch.” Permissions alone cannot prove that a compromised dispatcher is incapable of modifying another path or calling a merge-capable endpoint.

The full spec must therefore combine:

- repository rulesets/branch protection with no App bypass for `master`;
- a dedicated control branch with its own narrow writer policy;
- a capability wrapper that exposes only an allow-listed set of API operations, repositories, branches, paths, and transition states;
- short-lived installation tokens generated only when a transition needs them;
- separate reviewer credentials with no contents write;
- audit of every issued token scope and attempted denied operation;
- abuse tests proving that the App cannot merge, force-push, delete protected refs, modify settings/secrets, or write outside authorized branches through supported paths.

Until those tests pass, “the App cannot merge” is a requirement, not a verified fact.

### 6.3 Untrusted pull requests

No secret-bearing or write-capable job may execute untrusted fork code. Repository content, issue text, PR descriptions, comments, test logs, and model output are untrusted data. They may propose actions but may not alter policy, scope, permissions, spend limits, or state-machine transitions.

## 7. Threat analysis

| Threat/failure mode | Required control | Residual risk before proof |
| --- | --- | --- |
| Duplicate or replayed webhook | Signature verification, delivery-ID dedupe, transition idempotency | Redelivery after dedupe-store loss must still converge via canonical events |
| Two dispatcher instances race | One-file conditional canonical write; loser rereads before any side effect | GitHub single-winner semantics require disposable-repo proof |
| Pending Actions run replaced/cancelled | Actions is worker only; authority remains in control branch | Delayed reconciliation during GitHub incident |
| Stale gate/review result | Exact-head binding; head change invalidates evidence | Provider comments may omit strong head identity |
| Force-push or branch replacement | Protected refs; recorded base/head ancestry; halt on ambiguity | Ruleset misconfiguration or privileged human action |
| Compromised App private key | Short-lived scoped tokens, rotation/revocation, allow-listed proxy, kill switch | Contents permission remains coarse |
| Prompt injection in repo/PR/logs | Deterministic parser and policy; content never grants authority | Model may still leak or follow malicious text if context boundaries fail |
| Reviewer mutates code | Read-only reviewer credential and API surface | Vendor-side identity/permission claims require verification |
| Implementer approves its own work | Actor-role checks and distinct credentials | Shared underlying provider account may weaken independence |
| Provider call duplicated or charged twice | Durable request idempotency and reservation before dispatch | Some providers may not support idempotency; adapter-specific proof needed |
| Cost runaway | Per-run/per-day caps, projected reservation, maximum rounds, hard halt | GitHub-hosted model billing may not expose real-time final cost |
| Action/dependency supply-chain compromise | Pin immutable action SHAs, minimal permissions, offline fixtures | Upstream compromise before pinning or malicious maintained release |
| External DB divergence | Database is cache only; rebuild from GitHub | Temporary availability loss and delayed recovery |
| GitHub outage or delayed webhook | No action during uncertainty; reconcile after recovery | Work pauses; availability is intentionally sacrificed for safety |
| Control ledger tampering | Protected branch, hash chain, commit ancestry verification, alert/halt | Maintainer/admin compromise remains outside software-only prevention |
| Lease expires while actor still runs | Expiry triggers reconciliation, not reassignment | Provider execution may be unobservable or uncancellable |
| Notification spam | State-change-only notices and weekly digest; no liveness noise | Repeated infrastructure incidents may still require grouped reporting |

## 8. Cost analysis

The architecture has three independent cost surfaces:

1. **Control service** — hosted compute, queue, database, logs, and network traffic.
2. **GitHub execution** — Actions runners, artifact retention, and API usage.
3. **Model/review providers** — tokens, jobs, seats, or hosted coding-agent charges.

No current vendor price is frozen into this architecture decision. Prices and included quotas are time-sensitive and cannot be a safety boundary.

The full spec must define:

- a zero-provider-call idle path;
- projected and final cost records per transition/provider;
- per-request, per-run, per-day, and per-month hard caps;
- atomic budget reservation before every paid dispatch;
- maximum fix/re-review rounds;
- no fallback to a more expensive provider without explicit policy and available reservation;
- a manual emergency disable independent of provider availability;
- cost reconciliation that distinguishes GitHub Actions, hosting, and model spend;
- `cost_unknown` as a hard stop for a paid action rather than an assumed zero.

JarvisOS runtime policy 059b is not automatically authoritative for GitHub-hosted agents. The later governance/full-spec work must either define a separate repository-development budget authority or deliberately reuse 059b semantics through a proven boundary without pretending they already apply.

## 9. Availability and operational model

The control plane is allowed to stop. Safety dominates liveness.

Expected behavior:

- no eligible transition: no model call, no repeated comments, no branch mutation;
- webhook missed or service down: reconcile from GitHub on restart;
- external database lost: rebuild projections, retain canonical authority;
- GitHub uncertain/unavailable: halt and retry bounded reads later;
- provider unavailable: record precise blocked outcome; do not silently switch provider;
- maintainer absent: wait at `awaiting_maintainer` without periodic spend.

A weekly digest is presentation only. It cannot release a lease, authorize a slice, select a provider, or imply merge consent.

## 10. Kill switches and rollback

The full spec must provide independent kill paths:

1. canonical `halted` event preventing all non-recovery transitions;
2. disable or suspend the GitHub App installation;
3. revoke/rotate the App private key and provider credentials;
4. disable the hosting service or dispatcher queue consumers;
5. set provider spend caps to zero;
6. disable selected repository workflows;
7. human-only recovery procedure from the last verified control-branch commit.

A repository variable such as `DEVLOOP_ENABLED=false` may be a defense-in-depth switch, but a mutable variable alone is not canonical authority.

Rollback means stop and reconstruct. It does not mean deleting canonical events, force-pushing the control branch, rewriting findings, or erasing spend evidence.

## 11. Rejected alternatives

### 11.1 Pure GitHub Actions control plane — rejected as authority

Rejected because documented concurrency behavior permits at most one running and one pending item per group, may replace a pending item, and does not guarantee ordering. That is useful execution serialization, not a durable FIFO authority ledger or repository-wide compare-and-swap.

The normal repository `GITHUB_TOKEN` also intentionally suppresses many recursively triggered workflow runs. Building continuation from self-triggering workflow side effects would create special-case dispatch paths and ambiguous liveness.

Actions remains suitable for deterministic workers after authorization.

### 11.2 Issue/check/comment state — rejected as authority

Issues, labels, comments, check runs, and sticky summaries are mutable presentation surfaces with weak multi-object atomicity. They may display current state or request a human decision but cannot own claim, lease, budget, or transition history.

### 11.3 External database as canonical state — rejected

A database can provide strong transactions, but making it authoritative violates the GitHub-owned and chat-independent recovery requirement. It also creates an invisible state that repository reviewers cannot reconstruct from GitHub.

The database is retained only as queue/deduplication/cache infrastructure.

### 11.4 Maintainer-local scheduled dispatcher — rejected as primary

A local process is easy to stop but depends on a maintained workstation, long-lived credential custody, local state, network availability, and manual recovery. It is retained only as a possible read-only disaster-recovery inspector or manual operator tool, not the 24/7 authority.

### 11.5 Model/vendor-native conversation state — rejected

A coding-agent thread, browser conversation, or vendor task ID cannot own repository authority. It may be referenced as evidence, but it is not guaranteed to be durable, independently replayable, repository-visible, or permission-complete.

## 12. Mandatory proofs before full-spec promotion

Run these only in a disposable repository or isolated organization fixture. No test may mutate live `master`, current secrets, paid providers, or production rulesets.

1. **Atomic front race:** start at least two dispatchers from identical vacant state; exactly one canonical claim succeeds and every loser produces zero side effects.
2. **Stale blob/head:** attempt a transition with stale file/blob/control-head identities; it fails closed and does not invoke a worker.
3. **Replay:** deliver identical webhook IDs and semantically duplicate events across process/database restarts; one canonical effect results.
4. **Ledger reconstruction:** rebuild the same snapshot from event history after deleting all external cache/database state.
5. **Tamper detection:** reorder, remove, alter, or fork events/commits; reconstruction halts with a precise integrity reason.
6. **Lease recovery:** expire a lease while a workflow or simulated actor remains active; no new claimant starts before reconciliation.
7. **Exact-head invalidation:** change work-branch head after clean CI/review; prior evidence becomes ineligible.
8. **Permission abuse:** try merge, force-push, ref deletion, settings/secrets mutation, and out-of-scope path/branch writes using every dispatcher/actor credential; all are denied and audited.
9. **Reviewer separation:** reviewer credential cannot write contents or approve/merge; implementer cannot submit the authoritative review verdict.
10. **Untrusted fork:** malicious workflow/code/text cannot access secrets, gain write permission, or alter canonical authority.
11. **Prompt-injection corpus:** repository text attempts to change scope, spend, actor role, tests, or merge authority; deterministic policy ignores it.
12. **Budget stop:** projected cost exceeds each cap; no provider request occurs and reservation/accounting remain consistent.
13. **Duplicate paid request:** simulate timeout after provider acceptance; retry cannot create an untracked second charge.
14. **GitHub outage/recovery:** interrupt reads/writes/webhooks; system pauses and later reconstructs without duplicate action.
15. **Kill switches:** each independent switch stops new side effects; recovery requires explicit maintainer action.
16. **Actions behavior:** demonstrate that workflow concurrency/cancellation cannot release or transfer canonical authority.
17. **Notification behavior:** inactivity and duplicate events do not create repeated comments or model calls.

The Contents API's current-blob input and the proposed control-branch rules are evidence for a candidate design, not substitutes for these runtime proofs.

## 13. Decisions closed by this document

Closed for the next full-spec draft, subject to mandatory proof:

- primary dispatcher class: installed GitHub App hosted service;
- canonical state location: GitHub repository, separate protected control branch;
- canonical transition unit: one conditional update to one authority file;
- event history: ordered, hash-chained, tamper-evident logical append;
- external queue/database: non-authoritative cache and delivery infrastructure;
- Actions: deterministic worker only, never authority;
- global claim precedes branch lease and every side effect;
- lease expiry requires reconciliation, not automatic reassignment;
- maintainer remains sole merge/governance/destructive-action authority;
- provider/implementer/reviewer selection is deferred and grants no present authority.

## 14. Remaining blockers for a full specification

The architecture class is selected, but the full spec must not be drafted as settled fact until the following are resolved or explicitly represented as blocking acceptance criteria:

- disposable-repository proof of conditional single-winner writes;
- exact GitHub ruleset and branch-protection configuration;
- proof that each App/actor credential cannot merge or write outside scope;
- closed schemas and transition table;
- deployment host, queue/database technology, retention, and recovery objectives;
- provider-independent implementer/reviewer adapter contract;
- exact deterministic gate set and infrastructure-flake policy;
- spend source of truth and hard numerical caps;
- maximum fix/re-review rounds;
- notification/digest contract;
- governance amendment text;
- isolated end-to-end proof plan and owner.

## 15. Closure result

Architecture/evidence closure is complete when this document and its companion evidence map merge while:

- 079 remains `planned` with no Implementation PR;
- no workflow, App, service, secret, provider, runtime, dependency, test, or repository setting is created or changed;
- upstream claims are pinned and unsupported claims remain labelled as proposed or unverified;
- deterministic documentation gates pass on the exact PR head;
- the PR stops for the maintainer's explicit merge decision.
