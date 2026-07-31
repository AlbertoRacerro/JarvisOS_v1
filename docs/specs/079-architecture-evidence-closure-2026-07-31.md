# Spec 079 — architecture and evidence closure

**Date:** 2026-07-31  
**Pinned baseline:** `d5441f64b1b053d909a15817af70c38a07f6bd0c`  
**Registry status:** `planned`  
**Authority:** explicit maintainer instruction to proceed after merge of PR #204  
**Evidence companion:** `079-architecture-source-evidence-2026-07-31.md`

---

## 1. Decision boundary

This document performs only promotion-ladder step 2 for spec 079: select the primary state substrate and dispatcher class, document the trust, permission, cost, concurrency, and recovery boundaries, and reject unsafe alternatives.

It does **not** authorize:

- a GitHub App installation or hosted service;
- a workflow, scheduler, daemon, webhook endpoint, queue, database, or secret;
- automatic Codex, Claude, reviewer, or fix dispatch;
- a live model call or paid-service execution;
- repository-setting, ruleset, branch-protection, permission, label, or secret changes;
- the full 079 specification, governance amendment, readiness promotion, or implementation;
- auto-merge or agent-owned merge authority.

Spec 079 remains `planned`. A later full specification requires separate maintainer authorization and must preserve every blocker and mandatory proof recorded here.

## 2. Failure-mode-first conclusion

The primary failure is not loss of a chat session. It is **two actors both believing they own the one active development front** and performing mutation, review dispatch, or paid work from stale authority.

None of the following is sufficient authority by itself:

- a running GitHub Actions job;
- an issue label, comment, check run, or PR state;
- an open branch;
- a webhook delivery;
- a model verdict;
- an external queue or database row;
- a local lease;
- elapsed time or lease expiry.

The first externally visible side effect of a run is permitted only after one GitHub-owned repository-wide claim transition has succeeded against the exact current control-branch head. A losing or ambiguous writer must perform zero branch mutation, workflow dispatch, review request, model call, or spend.

## 3. Selected architecture

### 3.1 Primary dispatcher

Select an **installed GitHub App hosted as a small event-driven control service** as the primary dispatcher/resumer.

The App provides:

- an independently identifiable installation actor;
- short-lived installation tokens scoped to installed repositories and granted permissions;
- signed webhook deliveries and stable delivery identifiers;
- direct read access to commits, pull requests, checks, reviews, and workflow state;
- operation without a maintainer workstation remaining online.

The App is a dispatcher and deterministic policy enforcer. It is not an engineering authority and may invoke only the transition currently authorized by canonical state.

### 3.2 Canonical state location

Select a dedicated protected branch provisionally named:

`jarvis-control`

with one canonical authority file provisionally named:

`.jarvis/development-loop/authority.json`

The one-branch/one-file property minimizes partial multi-object transitions. Comments, checks, dashboards, queue records, and weekly digests are projections only and must be rebuildable from the control branch.

The authority file must contain at least:

- schema version and repository identity;
- monotonically increasing sequence;
- current derived snapshot;
- ordered hash-chained events;
- stable event ID, actor, role, transition, timestamp, idempotency key, payload digest, and previous-event digest;
- active spec/slice/front or explicit vacancy;
- scope digest;
- work-branch lease;
- exact base, control-head, work-head, and PR bindings;
- exact-head gate and review evidence references;
- budget and security stop state;
- next permitted action;
- terminal, paused, or human-decision reason.

### 3.3 Ref-level compare-and-swap candidate

The repository Contents API is **not** the selected authority transition primitive. A contents update can reject a stale file blob while still operating on a branch whose head advanced through another path. Blob identity alone therefore cannot enforce the required exact-head ownership rule.

The selected proof-gated candidate is a raw Git-object transition:

1. read and verify the exact current `jarvis-control` ref SHA;
2. read the canonical authority file and reconstruct its event chain;
3. compute one permitted transition deterministically;
4. create the replacement authority blob;
5. create a tree derived from the expected parent tree with only the authority path replaced;
6. create a commit whose **single parent is the exact expected control-head SHA**;
7. update `refs/heads/jarvis-control` to the candidate commit with `force=false`;
8. treat any non-fast-forward rejection, unexpected response, timeout, or ambiguous outcome as no authority gained;
9. reread the ref and canonical file before any retry or side effect.

Because the candidate commit is built directly on the exact expected parent, a concurrent writer that advances the ref produces a divergent tip. A non-forced ref update must then reject the stale candidate rather than silently rebasing it onto the unexpected head.

This is still **PROPOSED_PENDING_PROOF**, not a claim of proven linearizability. The disposable-repository two-writer test must demonstrate exactly one winner, correct ambiguous-timeout reconciliation, and zero loser side effects under the actual API, App permissions, and ruleset configuration.

### 3.4 Event history and compaction

Each successful ref update creates one durable authority commit. The file contains the ordered logical event chain, while Git commit ancestry supplies a second tamper-evident sequence.

Compaction, if ever required, needs a separately specified checkpoint event that preserves the prior terminal digest and may run only with no active front. Silent truncation, force-push, history rewrite, or event deletion is forbidden.

### 3.5 External queue and database

The hosted service may use a durable queue and database for:

- asynchronous webhook processing;
- delivery-ID deduplication;
- bounded retries and backoff;
- observability;
- cached projections;
- short-lived worker coordination.

They are non-authoritative and rebuildable. Their loss may delay work but must never change ownership, authorization, or transition legality.

### 3.6 GitHub Actions role

GitHub Actions remains an ephemeral worker and deterministic-gate surface only:

- run repository tests and isolated proofs;
- expose conclusions bound to an exact commit;
- optionally execute a later bounded adapter after canonical authorization.

Actions concurrency groups are not the repository-wide mutex. Workflow order, queued state, cancellation, or replacement cannot claim, release, or transfer the active front.

### 3.7 Actor separation

The future system requires distinct effective identities:

1. **Control App** — reads GitHub state and writes canonical control transitions plus bounded presentation artifacts.
2. **Implementer actuator** — may mutate only the recorded work branch and scope; it cannot review or merge.
3. **Reviewer actuator** — read-only over code and evidence; it may emit findings but has no contents-write or merge capability.
4. **Maintainer** — owns priority, governance exceptions, secrets/settings, destructive actions, exceptional spending, and merge.

One credential must not combine control, implementation, review, and merge authority. The implementer and reviewer provider remain deliberately unselected.

## 4. Transition topology

1. GitHub emits a subscribed event.
2. The service validates transport, webhook signature, event type, installation, repository, and delivery ID.
3. The handler acknowledges quickly and queues work; it performs no model call or branch mutation in the request path.
4. A worker deduplicates delivery and reads the exact control ref and authority file.
5. It verifies commit ancestry, event hashes, schema, current repository facts, authorization, dependencies, active-front state, scope, lease, spend, and security stops.
6. Deterministic policy returns one permitted transition or a precise no-op/halt.
7. Claim and lease changes use the ref-level CAS candidate in section 3.3.
8. Only a verified successful ref transition permits the next bounded external action.
9. The action result is reconciled against live GitHub state and recorded by a new canonical transition.
10. Any work-head change invalidates all prior head-bound gate and review evidence.
11. Any ambiguity pauses or halts; timers never create authority.

## 5. Global claim, lease, and idempotency

### 5.1 Global front claim

The global claim transition must atomically establish:

- prior vacancy or explicitly reconciled recoverability;
- authorized spec and bounded slice;
- scope digest;
- exact base and intended work branch;
- claimant identity;
- sequence and idempotency key;
- reconciliation deadline;
- first permitted action.

No work-branch lease may exist without a valid global claim.

### 5.2 Work-branch lease

The lease serializes mutation within the already claimed front. It cannot authorize another front, broaden scope, or replace the global claim.

Expiry does not release ownership. Recovery first reconciles:

- current branch head and ancestry;
- open, closed, or merged PR state;
- queued, running, cancelled, and completed workflows;
- observable provider requests;
- unrecorded commits or review comments;
- security and budget stops.

Only an explicit canonical recovery, release, or terminal transition may change ownership.

### 5.3 Idempotency

Every transition and external request uses a deterministic idempotency key derived from repository, run, sequence, transition, target head, review/fix round, and adapter identity as applicable.

Duplicate delivery may inspect existing evidence but must not duplicate commits, comments, reviews, workflow dispatches, model calls, reservations, or charges.

## 6. Permission model

### 6.1 Candidate App permissions

The full spec must prove the smallest installation permission set. Initial candidates are:

- metadata: read;
- contents: read/write for raw Git objects and authorized work branches;
- pull requests: read/write only for bounded metadata, comments, and review requests;
- checks and commit statuses: read;
- actions: read, with write added only if a selected transition must dispatch or rerun a workflow;
- issues: read/write only if human-decision requests use issue or PR comments.

Do not grant administration, environments, secrets, organization membership, deployments, packages, security-alert mutation, repository-hook mutation, or ruleset bypass without separate proof of necessity.

### 6.2 Coarse-permission blocker

`contents: write` is not a path capability. It is broader than “write one control file” or “write one authorized branch.” Permissions alone cannot prove that a compromised App cannot alter another path or use a merge-capable endpoint.

The full design therefore requires all of:

- protected `master` with no App bypass;
- protected `jarvis-control`, no force-push, no deletion, and a narrowly allowed writer identity;
- a capability wrapper allow-listing exact repository IDs, refs, paths, Git-object operations, transition states, and request shapes;
- short-lived tokens issued only for the current transition;
- separate reviewer credentials with no contents write;
- denied-operation audit;
- abuse tests for merge, force-push, ref deletion, settings/secrets mutation, and out-of-scope writes.

Until those tests pass, “the App cannot merge or write outside scope” is a requirement, not a verified fact.

### 6.3 Untrusted input

Fork code, repository text, PR descriptions, comments, logs, artifacts, and model output are untrusted data. They may supply evidence but may never modify authority, role, scope, permissions, spend limits, or transition policy.

No secret-bearing or write-capable job may execute untrusted fork code.

## 7. Threat analysis

| Failure mode | Required control | Residual proof gap |
| --- | --- | --- |
| Two dispatchers race | Exact-parent candidate commit plus non-forced ref update | Disposable-repository single-winner proof |
| Ref advances without file change | Ref-level CAS; blob-only update forbidden | Ruleset/API integration proof |
| Timeout after ref update | Reread ref, candidate commit, and event ID before retry | Network-fault proof |
| Duplicate webhook | Signature, delivery dedupe, transition idempotency | Dedupe-store loss proof |
| Stale CI/review | Exact work-head binding | Provider evidence format proof |
| Force-push or branch replacement | Rulesets, ancestry checks, halt on ambiguity | Misconfiguration/admin compromise |
| Compromised App key | Short-lived tokens, capability wrapper, rotation, kill switch | Coarse contents permission |
| Prompt injection | Deterministic policy; untrusted text grants no authority | Model-context isolation proof |
| Reviewer mutates code | Read-only reviewer identity | Vendor credential verification |
| Implementer self-approves | Separate identities and role checks | Shared provider-account residual risk |
| Duplicate paid call | Reservation and adapter idempotency | Provider-specific behavior |
| Cost runaway | Hard caps, max rounds, no implicit fallback | Timely billing visibility |
| Supply-chain compromise | Immutable action pins and minimal permissions | Upstream compromise before pinning |
| External DB divergence | GitHub remains canonical | Temporary availability loss |
| GitHub outage | No action during uncertainty; reconcile later | Intentional loss of liveness |
| Ledger tampering | Protected ref, ancestry plus event hash chain | Maintainer/admin compromise |
| Lease expiry while actor runs | Reconcile, never automatic reassignment | Unobservable provider execution |
| Notification spam | State-change notices and weekly digest only | Grouping during repeated incidents |

## 8. Cost boundary

The architecture has independent cost surfaces for hosted control infrastructure, GitHub execution, and model/review providers.

No price is frozen into this decision. The full spec must provide:

- zero-provider-call idle behavior;
- projected, reserved, and final cost records;
- per-request, run, day, and month caps;
- atomic reservation before paid dispatch;
- maximum fix/re-review rounds;
- no implicit expensive fallback;
- independent emergency disable;
- separate reconciliation for hosting, Actions, and model spend;
- `cost_unknown` as a hard stop for paid action.

JarvisOS runtime policy 059b does not automatically govern GitHub-hosted agents. A later governance contract must establish the development-loop budget authority explicitly.

## 9. Availability, kill switches, and recovery

Safety dominates liveness. No eligible transition means no model call, repeated comment, or mutation. GitHub uncertainty, provider ambiguity, stale evidence, or lost local state causes a pause and reconstruction from canonical GitHub state.

Independent kill paths must include:

1. canonical `halted` event;
2. suspend the App installation;
3. revoke or rotate App and provider credentials;
4. stop hosting workers and queue consumers;
5. set provider caps to zero;
6. disable selected workflows;
7. human-only recovery from the last verified control commit.

Rollback means stop and reconstruct. It never means force-pushing the control branch, deleting events, rewriting findings, or erasing spend evidence.

## 10. Rejected alternatives

- **Pure GitHub Actions authority:** rejected because concurrency is execution serialization, not an ordered durable repository-wide claim ledger.
- **Contents API blob update as CAS:** rejected because blob identity does not assert the exact branch head.
- **Issue/check/comment authority:** rejected because state is mutable and transitions span multiple objects.
- **External database authority:** rejected because repository reviewers could not reconstruct canonical authorization from GitHub.
- **Maintainer-local scheduler as primary:** rejected because availability, credentials, and recovery depend on one workstation.
- **Model/vendor conversation state:** rejected because it is vendor-specific, non-canonical, and not independently replayable.

## 11. Mandatory proofs before full-spec promotion

Use only a disposable repository or isolated organization fixture. Do not mutate live `master`, current secrets, paid providers, or production rulesets.

1. Two or more dispatchers race from the same vacant ref; exactly one ref update wins and every loser produces zero side effects.
2. An unrelated commit advances `jarvis-control` without changing the authority blob; the stale candidate ref update is rejected.
3. Stale authority blob, tree, parent commit, and ref identities all fail closed.
4. A timeout after a successful ref update is reconciled without a second event or action.
5. Duplicate and replayed webhook deliveries converge across process and database restarts.
6. Deleting all external cache/database state still permits exact snapshot reconstruction.
7. Reordered, removed, changed, or forked events/commits trigger a precise integrity halt.
8. Lease expiry while a worker remains active never starts a new claimant before reconciliation.
9. A changed work-head invalidates previous green CI and clean review.
10. Every dispatcher/actor credential is denied merge, force-push, ref deletion, settings/secrets mutation, and out-of-scope writes.
11. Reviewer credentials cannot write, approve authoritatively, or merge; implementer cannot supply the authoritative review verdict.
12. Untrusted fork code and text cannot access secrets or alter authority.
13. Prompt-injection fixtures cannot change scope, spend, role, tests, or merge authority.
14. Exceeded or unknown cost prevents provider dispatch.
15. Timeout after provider acceptance cannot create an untracked duplicate charge.
16. GitHub outage and delayed webhook recovery produce no duplicate action.
17. Every kill switch stops new side effects and requires explicit maintainer recovery.
18. Actions cancellation or concurrency behavior cannot release or transfer canonical authority.
19. Inactivity and duplicate events create no repeated comments or model calls.

## 12. Decisions closed and remaining blockers

Closed, subject to proof:

- installed GitHub App as dispatcher class;
- GitHub protected control branch as canonical location;
- one authority file with hash-chained events and derived snapshot;
- raw Git-object commit built on exact expected parent plus non-forced ref update as the CAS candidate;
- queue/database as non-authoritative infrastructure;
- Actions as deterministic worker only;
- global claim before lease and every side effect;
- human-only merge, governance, destructive action, and exceptional spend.

Still blocked before full-spec promotion:

- runtime proof of ref-level single-winner and timeout reconciliation;
- exact ruleset and branch-protection configuration;
- credential denial proofs;
- closed schemas and transition table;
- deployment host, queue/database, retention, and recovery objectives;
- provider-independent implementer/reviewer adapter contract;
- deterministic gate and infrastructure-flake policy;
- spend source of truth and numerical caps;
- maximum review/fix rounds;
- notification contract;
- governance amendment text;
- isolated proof plan and owner.

## 13. Closure result

Architecture/evidence closure is complete when this document and its evidence map merge while:

- 079 remains `planned` with no Implementation PR;
- no workflow, App, service, secret, provider, runtime, dependency, test, or repository setting is created or changed;
- the ref-level CAS design remains explicitly proof-gated;
- deterministic documentation and repository gates pass on the exact PR head;
- the PR stops for the maintainer’s explicit merge decision.
