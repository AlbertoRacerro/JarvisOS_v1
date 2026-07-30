# Spec 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: durable bounded development continuation

**Definition status:** planning kernel; registry remains `planned`.

**Depends on:** 004, 017, 019, 022

**Target path:** `docs/specs/079-autonomous-development-loop-0.md`

---

## 1. Purpose

Define the smallest safe control-plane direction that lets an already authorized JarvisOS development slice continue across agent-session termination without requiring the maintainer to repeatedly write `continue` or `proceed`.

The intended system coordinates implementing and reviewing agents through durable GitHub-owned state. It may resume reversible work on the same authorized spec, branch, pull request, and exact head; collect deterministic gate evidence; request bounded review; drive a bounded fix/re-review cycle; and stop at every authority boundary already owned by the maintainer.

This document is a planning kernel, not an implementation contract. It does not authorize a workflow, GitHub App, daemon, external provider call, automatic Codex request, branch mutation, or merge. It identifies the current authority, the minimum state machine, candidate hosting choices, hard safety invariants, and the decisions that must be closed before a full specification may be promoted.

## 2. Maintainer decision and current freeze

On 2026-07-30 the maintainer explicitly authorized this definition-only S4 step after merge of spec 077 implementation PR #198. The authorization is limited to:

1. reconciling the canonical registry with the merged 077 implementation;
2. recording one `planned` 079 backlog row;
3. writing this planning kernel and its pinned source-evidence map.

The authorization does **not** lift the freeze for autonomous-control implementation. It does not activate any previously removed automatic review/fix pipeline. It does not permit a second implementation front, automatic external review, automatic Codex actuation, auto-merge, or agent-owned merge authority.

## 3. Current repository facts that must remain true

Each fact is mapped in `079-autonomous-development-loop-source-evidence.md` and was re-read against pinned baseline `64d598ef99f6dcd6f5afe7caec7a1e7062f78c45` on 2026-07-30.

1. `docs/specs/STATUS.md` is the single live source of truth for spec state and near-term priority. Planning PRs do not occupy the `Implementation PR` column and do not move a row to `in_review`. `RT-01`
2. Only one product or implementation front may be active. Frozen work remains `planned`, and restart requires an explicit maintainer decision plus re-derivation from current `master`. `RT-02`
3. The maintainer normally reviews JarvisOS once per week and should be contacted between reviews only for a human decision, security problem, or budget overrun. `RT-03`
4. Automated review output is advisory. Deterministic gates and a human maintainer decision own merge authority. `RT-04`
5. External review workflows are manual-only and may not invoke Codex, push changes, modify readiness labels, dispatch another review tier, or merge. `RT-05`
6. Agents may not merge their own pull requests or enable auto-merge. `RT-06`
7. Model findings must be independently reproduced or traced. Genuine defects are fixed on the same PR branch; false findings receive a concise evidence-backed rebuttal. `RT-07`
8. Codex is explicit-only. No current workflow sends an automatic fix request. `RT-08`
9. Within an assigned slice, an implementing agent may proceed through inspection, implementation, tests, CI diagnosis, and evidence collection without waiting between reversible steps. It must stop at external spending, destructive or irreversible actions, secret changes, paid workflow dispatches, and merge. `RT-09`
10. Spec 022 preserves a bounded same-branch Codex actuator only for explicit maintainer-requested work and explicitly excludes automatic workflow dispatch. `RT-10`
11. Specs 017 and 019 preserve historical review infrastructure only as manually dispatched advisory review. Spec 020 is cancelled because the prior automatic review/fix pipeline was removed. `RT-11`
12. Spec 077 implementation PR #198 is merged, while the pinned baseline registry still records it as `in_review`; this S4 planning PR must reconcile that factual drift. `RT-12`
13. Spec 078 is a merged planning definition but remains `planned`; its full-spec promotion and implementation are not authorized during the maintainer freeze. `RT-13`

Any future implementation that weakens these facts without an explicit, reviewed governance amendment is outside 079.

## 4. Problem statement

The current process can execute a bounded assigned slice safely, but continuity is conversational rather than durable. When an agent session ends, the next agent must reconstruct:

- which spec and branch were authorized;
- the exact base and head commits;
- the current implementation/review round;
- which deterministic gates ran on which head;
- which review findings are open, genuine, false, superseded, or fixed;
- whether a fix request was explicitly authorized;
- which action is next and which authority boundary requires the maintainer.

GitHub contains most underlying evidence, but no single bounded machine-readable run authority currently joins it into a resumable state machine. Ad hoc issue comments, labels, branch names, chat summaries, and workflow runs are not individually sufficient because they can be stale, edited, duplicated, or detached from the exact head.

The control-plane gap is therefore **durable authorization and continuation**, not another coding agent, another review model, another product orchestrator, or hidden browser-to-browser coordination.

## 5. Required control-plane properties

A future full specification must preserve all of the following.

### 5.1 GitHub-owned durable authority

The canonical continuation state must live in GitHub and be reconstructible without chat history or local process memory. Every transition must bind at least:

- repository identity;
- spec identifier and registry status;
- authorized slice and scope digest;
- base branch and exact base SHA;
- work branch and exact head SHA;
- pull request number when present;
- actor and actor role;
- transition kind and monotonic sequence;
- deterministic gate evidence tied to the exact head;
- review round, finding identities, and dispositions;
- next permitted action;
- stop reason or required human decision.

Mutable presentation may exist, but the authority history must be append-only or equivalently tamper-evident. A changed head invalidates head-bound gate and review evidence rather than silently carrying it forward.

### 5.2 Explicit authorization envelope

A run may start or resume only when all of these are true:

1. the maintainer has authorized the exact spec/slice or the row is the eligible lowest-numbered `ready` row under current priority;
2. all hard dependencies are `merged`;
3. no overlapping implementation PR owns the same files or runtime boundary;
4. the branch descends from the recorded base without force-push ambiguity;
5. requested actions remain inside the scope digest and current repository governance;
6. no stop condition is active.

The dispatcher must not infer permission from a branch merely existing, a PR being open, an issue label alone, a model comment, or a previous session having worked on the branch.

### 5.3 Exact bounded state machine

The full spec must freeze a closed state machine. The planning candidate is:

- `authorized`
- `claimed`
- `implementing`
- `awaiting_deterministic_gates`
- `awaiting_review`
- `fix_required`
- `awaiting_re_review`
- `awaiting_maintainer`
- `completed_without_merge`
- `halted`

Names may change, but every state and transition must define:

- required preconditions;
- allowed actor;
- idempotency key;
- exact-head requirements;
- durable evidence written;
- timeout/lease behavior;
- retry bound;
- fail-closed outcome.

No state may imply merge authority.

### 5.4 Implementer/reviewer separation

The implementing and reviewing roles must be independently identified even when both are model-backed. A reviewer may produce findings but may not mutate the implementation branch. An implementing agent may change the branch within scope but may not resolve a finding merely by assertion.

A clean review is evidence, not merge authorization.

### 5.5 Negative-review loop

The intended S4 behavior to evaluate and freeze in the full spec is:

1. a negative review creates durable finding records bound to the reviewed head;
2. each finding is triaged as `reproduced`, `accepted_without_reproduction`, `false_positive`, `superseded`, or another closed enum selected by the full spec;
3. every genuine blocking finding requires a bounded `codex_fix_attempt` or equivalent implementing-agent attempt on the same authorized branch;
4. the attempt must end in either a verified branch update or a structured evidence-backed no-change/false-positive decision;
5. deterministic gates rerun on the new exact head;
6. re-review occurs only after those gates pass;
7. the cycle stops on clean review, maximum rounds, non-reproducible infrastructure failure, scope expansion, security/budget boundary, or maintainer decision.

Current governance forbids automatic review dispatch and automatic Codex requests. Therefore this behavior is a target contract only; implementation requires a separate explicit amendment to `AGENTS.md` and a dated readiness decision.

### 5.6 Deterministic gates before model action

A model review or fix cycle may never substitute for CI. Before review or re-review, the control plane must establish that required deterministic gates completed successfully on the exact head. Stale success from another SHA is ineligible.

Infrastructure failure must remain distinguishable from a code defect and from a review finding. Automatic retries, if later authorized, must be bounded and must not rewrite code to mask flaky infrastructure.

### 5.7 Human merge boundary

The system must stop at a prepared, fully evidenced pull request. The maintainer alone decides whether to merge, close, defer, request changes, or alter priority.

No 079 implementation may:

- merge a PR;
- enable auto-merge;
- synthesize maintainer approval;
- treat a label, model verdict, CI success, elapsed time, or weekly-review schedule as merge consent;
- bypass branch protection or use a privileged token to cross the merge boundary.

### 5.8 Spend, secrets, and destructive-action boundaries

The full spec must identify every action that can spend money, expose repository content to an external model, use or modify a secret, alter repository settings, delete refs, force-push, cancel authoritative runs, or change protected evidence.

Such actions require explicit authority and auditable attribution. The control plane must not assume that JarvisOS runtime egress policy 059b governs GitHub-hosted Codex, Claude, or third-party review services; their authorization and accounting boundary must be stated separately and honestly.

### 5.9 Concurrency, leases, and idempotency

At most one active claimant may mutate an authorized work branch at a time. Claims require bounded leases with explicit renewal and expiry semantics. Duplicate delivery, scheduler retries, webhook replay, and concurrent agents must converge without duplicate fix attempts, duplicate reviews, conflicting pushes, or lost state.

A lease must not grant authority beyond the recorded slice and must not survive branch/head replacement without revalidation.

### 5.10 Honest inactivity

The system must tolerate days of inactivity. It must not create noise merely to prove liveness, repeatedly call models while no eligible transition exists, or contact the maintainer for routine progress. A weekly digest may summarize durable state, but it cannot become a hidden scheduling authority or merge signal.

## 6. Candidate architecture

The smallest candidate architecture has six logical roles. These are authority roles, not necessarily six services or six models.

1. **Run authority store** — durable GitHub-owned append-only events plus a derived current snapshot.
2. **Dispatcher/resumer** — reads authority, acquires a bounded lease, and invokes only the next permitted transition.
3. **Implementing actuator** — modifies the authorized branch within the scope digest and reports the resulting exact head.
4. **Deterministic gate collector** — records required workflow/check conclusions for that exact head.
5. **Independent reviewer** — emits structured findings tied to the reviewed head and cannot push.
6. **Maintainer boundary** — owns priority changes, governance exceptions, external-spend exceptions, secrets, destructive actions, and merge.

The preferred interaction is GitHub-to-GitHub. Agents must not depend on shared browser tabs, hidden chat context, mutable local scratch state, or one vendor's conversation memory.

## 7. Hosting options to decide

The full spec must compare at least these options against the safety properties above.

### Option A — GitHub Actions plus issue/check state

Advantages:

- repository-native identity and audit trail;
- direct access to PR, head, check, and review events;
- no always-on local machine.

Risks/open questions:

- workflow permission escalation;
- event recursion and duplicate delivery;
- limited durable locking;
- cost and secret handling for external agents;
- current repository prohibition on automatic review/fix workflows.

### Option B — installed GitHub App control plane

Advantages:

- explicit installation permissions;
- webhook-driven state transitions;
- stronger independent service identity and lease storage.

Risks/open questions:

- new hosted service and operational burden;
- webhook security and replay handling;
- secret custody;
- availability and cost;
- broader attack surface.

### Option C — maintainer-owned scheduled local dispatcher

Advantages:

- local custody and potentially lower hosted complexity;
- direct control over credentials and shutdown.

Risks/open questions:

- not 24/7 unless a machine is maintained;
- local state drift;
- weaker availability;
- harder independent audit and recovery.

The planning kernel does not select a host. A full spec must choose one primary architecture and reject the others with recorded evidence.

## 8. Minimum durable records

The full spec must define closed schemas for at least:

- `development_run`
- `authorization_grant`
- `work_claim`
- `checkpoint_event`
- `gate_evidence`
- `review_round`
- `review_finding`
- `finding_disposition`
- `fix_attempt`
- `human_decision_request`
- `terminal_outcome`

Every record must carry stable identity, timestamps, repository/spec/PR linkage, actor provenance, exact-head binding where applicable, and a content digest or equivalent tamper-evident identity.

Derived dashboards or sticky summaries are non-authoritative. Append-only events own history.

## 9. Fail-closed stop conditions

A future implementation must stop without branch mutation when any of the following is true:

- missing or ambiguous authorization;
- registry row absent, frozen without explicit restart, or not eligible;
- unmerged hard dependency;
- overlapping active PR or conflicting branch owner;
- base/head mismatch, force-push ambiguity, or untrusted fork;
- required gate missing, stale, cancelled, action-required, or failed;
- finding requires scope expansion;
- maximum review/fix rounds reached;
- lease conflict or replay ambiguity;
- external-spend authorization absent;
- required secret unavailable or changed;
- destructive action required;
- security signal or suspected prompt/repository-content exfiltration;
- merge or governance decision required.

The terminal or paused reason must be durable and precise. `provider_error`, `unknown`, or generic failure is not sufficient when a deterministic authority gate caused the stop.

## 10. Verification direction for a later implementation

A full spec must define offline deterministic tests using fixtures and fake actors. At minimum it must prove:

1. restart reconstructs the same current state from durable events;
2. duplicate event delivery is idempotent;
3. two claimants cannot both mutate the branch;
4. stale CI/review evidence from another head is rejected;
5. a changed head invalidates previous clean review;
6. a genuine negative finding creates one bounded fix attempt;
7. a structured false-positive decision requires evidence and no branch mutation;
8. re-review waits for exact-head deterministic gates;
9. maximum rounds halt without further model calls;
10. frozen/planned/blocked work is never selected without explicit authority;
11. external spending, secrets, destructive actions, and merge always stop for human authority;
12. no automatic path invokes a live provider in CI;
13. no actor can approve and merge its own work;
14. interrupted execution resumes without duplicate commits, comments, reviews, or charges;
15. inactivity produces no repeated calls or noise.

A later real-tool proof must use a disposable repository or equivalent isolated fixture. It must not experiment on `master`, repository secrets, branch protection, or live paid models.

## 11. Decisions required before full specification

079 must remain `planned` until all of these are closed with recorded evidence:

1. canonical GitHub state substrate and append-only/tamper-evident representation;
2. dispatcher host and trust boundary;
3. exact authorization-grant format and revocation semantics;
4. branch lease, concurrency, replay, and idempotency model;
5. exact state machine and transition table;
6. deterministic gate set and infrastructure-retry policy;
7. review provider, structured finding schema, and reviewer independence;
8. genuine-finding, false-positive, and no-change decision rules;
9. maximum fix/re-review rounds and escalation policy;
10. external-model content, spend, credential, and audit authority;
11. maintainer notification and weekly digest contract;
12. threat model for malicious code, prompt injection, compromised actor, and supply-chain action;
13. governance amendment required to replace the current manual-only/explicit-only rules;
14. isolated end-to-end proof environment;
15. rollback and kill-switch authority.

## 12. Promotion ladder

1. **Planning kernel — this PR:** identify facts, target behavior, options, invariants, and unresolved decisions; keep 079 `planned`.
2. **Architecture/evidence closure:** choose the state substrate and dispatcher, produce threat/cost/permission analyses, and record rejected alternatives.
3. **Full specification:** freeze schemas, state machine, APIs/events, permissions, tests, rollout, kill switch, and migration/compatibility policy.
4. **Governance amendment:** explicitly revise `AGENTS.md` only where the accepted full spec requires it; preserve human merge authority.
5. **Dated readiness decision:** prove dependencies, test environment, security boundaries, cost controls, and implementation ownership.
6. **Implementation:** only after 079 is `ready`; set `in_progress`, then `in_review` with the implementation PR number.

## 13. Non-goals for this planning PR

This PR does not:

- implement a dispatcher, bot, GitHub App, scheduler, daemon, MCP server, or agent framework;
- create or modify a GitHub Actions workflow;
- invoke Codex, Claude, another model, or a paid service;
- alter repository secrets, permissions, branch protection, labels, or settings;
- authorize automatic review or automatic fix dispatch;
- authorize auto-merge or any agent merge;
- change product runtime, backend, frontend, schema, dependencies, or tests;
- activate Hermes or any second orchestration engine;
- choose a new product/implementation front;
- promote 078 or another frozen row;
- treat an AI team, persona, or reviewer as an independent authority;
- duplicate `STATUS.md` as a second live roadmap.

## 14. Definition result

S4 is complete at the definition boundary when:

- this planning kernel and its source-evidence map are reviewable;
- `STATUS.md` truthfully records 077 as merged and 079 as planned;
- the 2026-07-30 definition-only maintainer exception is explicit;
- 078 remains planned and frozen from promotion/implementation;
- no runtime, workflow, dependency, test, or repository-setting change is present;
- deterministic documentation gates pass on the exact PR head;
- the PR stops for the maintainer's merge decision.
