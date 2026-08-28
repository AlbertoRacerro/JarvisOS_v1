# Agent execution and automation protocol

Status: canonical operational process
Effective date: 2026-08-05
Amended: 2026-08-28 — dormant post-112 controlled-parallel profile and model-economy tightening

This document defines repository delivery, autonomous continuation, model collaboration, finding closure, post-beta deferral, and documentation-drift handling for JarvisOS coding and review agents.

`AGENTS.md` remains authoritative for hard invariants, safety boundaries, general conduct, the exhaustive maintainer-interruption classes, and every accepted specification-specific exception. This protocol adds execution detail without changing JarvisOS runtime authority, provider policy, credentials, budgets, egress, schemas, or product behavior.

In particular, this document does not expand spec 079. The repository-internal 079 scheduled continuation keeps its accepted implementation-only authority and cannot review, repair findings, merge, select a new spec, or advance the queue. The checkpoint/builder/watchdog roles described below are external coordinating automations acting through the maintainer-authorized ChatGPT/GitHub control plane, not the 079 workflow.

`docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` is a subordinate canonical execution profile for the controlled-parallel exception that becomes eligible only after its explicit activation gate. It is not a roadmap and never replaces `docs/specs/STATUS.md`.

## 1. Minimal startup sequence

A coordinating chat or agent session starts by reading, from exact Git SHAs:

1. `AGENTS.md`;
2. this document;
3. `docs/specs/STATUS.md`;
4. `docs/specs/README.md`;
5. the selected spec and readiness record;
6. the active PR body, exact head, diff, workflows, reviews, and unresolved threads.

After the post-112 profile becomes eligible, a coordinator also reads `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` before opening or resuming more than one implementation lane.

A continuation handoff should normally contain only:

- repository;
- exact `master` SHA;
- active PR;
- exact PR-head SHA;
- canonical checkpoint comment;
- maintainer decisions not yet recorded in the repository.

Do not copy the queue, spec text, or operating rules into every chat handoff.

## 2. Authority by question

1. Current code, runtime behavior, deterministic tests, and exact-head evidence describe actual behavior.
2. `AGENTS.md` defines hard invariants, safety boundaries, general agent conduct, and accepted spec-specific exceptions.
3. This document defines delivery and external coordinating-automation mechanics; after its activation gate, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` defines the narrower mechanics of controlled parallel delivery.
4. `docs/specs/STATUS.md` is the sole live authority for spec state, dependencies, queue order, and implementation-PR association.
5. The selected spec and readiness record define slice scope, acceptance criteria, tests, and non-goals.
6. `docs/DECISIONS.md` records durable architecture decisions.
7. `docs/ARCHITECTURE.md` describes stable architecture only where consistent with current code, accepted decisions, and current spec state.
8. README files are onboarding and navigation, not independent runtime, roadmap, or merge authority.
9. Strategy packs, design docs, milestone reports, model summaries, and chat handoffs are advisory or historical unless promoted by a canonical source.

When sources conflict:

- identify exact claims, dates, and SHAs;
- use runtime evidence for behavior, `STATUS.md` for work state, the active spec for slice scope, and accepted ADRs for durable architecture;
- use the narrower accepted spec for exceptions such as 079;
- use the post-112 profile only after its activation gate and only for delivery mechanics;
- do not resolve by plausibility alone;
- fix stale canonical prose in a bounded documentation change;
- preserve superseded history when it carries provenance.

## 3. Exact-SHA and freshness rule

Branch names such as `master`, `latest`, or `current head` are not sufficient evidence.

Every implementation, review, checkpoint, audit, lane-ownership decision, and merge decision records the full 40-character SHA examined. A branch name may be used to discover an SHA, but conclusions are tied to the resolved commit.

When the PR head changes:

- earlier CI and reviews remain evidence only for the old head;
- findings are revalidated;
- conclusions are classified as still valid, resolved, superseded, or requiring revalidation;
- no merge relies on a gate from another head.

After one parallel lane merges, the other lanes must resolve fresh `master` and revalidate any ancestry-, shared-owner-, or gate-sensitive conclusions before their own merge.

## 4. Delivery states

- `REMOTE_VERIFIED`: branch advanced; complete files are readable from GitHub; diff is authorized; evidence belongs to that exact head.
- `LOCAL_ONLY`: work exists only in an agent checkout, temporary filesystem, or unpushed commit.
- `DECLARED_NOT_VERIFIED`: an agent claims a result without independently verified remote evidence.
- `DELIVERY_FAILURE`: work was claimed or completed but no recoverable remote delivery exists.
- `BLOCKED`: no authorized practical route remains without maintainer action or prohibited risk.

A local commit SHA, task link, summary comment, or test claim is not delivery.

## 5. Serial execution before 112; controlled lanes after 112

### Pre-112 rule

Until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` as `merged`:

- follow the queue in `STATUS.md` serially;
- finish, verify, and merge the first authorized runtime slice before opening the next runtime front;
- use one implementation branch and one implementation PR per spec;
- allow one writer at a time on the active PR;
- do not create concurrent implementations over the same files or runtime boundary;
- a failover writer uses an exact-head guard; the first valid remote write wins and stale writers stop;
- a maintainer-requested documentation reconciliation may temporarily become the active front, after which the paused implementation resumes.

This rule remains absolute for 111 and 112. The presence of the post-112 profile in the repository is not permission to parallelize them.

### Post-112 exception

After exact `master` shows 112 as `merged`, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` becomes eligible automatically. The Integration Coordinator must first prove that candidate lanes are sufficiently disjoint in file, store, schema, migration, and authority ownership.

Only proved-disjoint lanes may run concurrently. The profile permits one Integration Coordinator plus up to three isolated domain builders, serializes all merges through the coordinator, reserves shared integration boundaries to the coordinator, and returns only conflicting slices to serial execution.

The queue in `STATUS.md`, per-spec readiness, hard dependencies, exact-head gates, and one-writer-per-PR rules remain binding. Parallelism is delivery scheduling, not new product authority.

## 6. External coordinating automation roles

The roles in this section describe maintainer-authorized external ChatGPT automations that inspect and mutate the repository through the GitHub control plane. They are not the repository-internal spec 079 workflow.

A job running under spec 079 must ignore any broader capability described here and remain within 079's implementation-only, no-review, no-repair, no-merge, no-new-spec boundary.

### Checkpoint

The external checkpoint role:

- reads GitHub as source of truth;
- completes unfinished verification;
- maintains one PR comment marked `AUTONOMOUS_FRONTEND_CHECKPOINT_V1` when that checkpoint mechanism is actually in use;
- records exact SHAs, delivery state, gates, findings, blocker, owner, and next exact action;
- does not create another registry or duplicate status comments.

A checkpoint or comment that adds no new evidence or authority should not be created merely as ceremony.

### Builder

The external builder role:

- resumes from canonical repository state rather than relying on chat memory;
- acts like a maintainer command to continue;
- performs all sequential safe work available in the cycle instead of stopping after one micro-action;
- may implement, publish, verify, correct, consume CI and reviews, merge with an expected-head guard, reconcile status, and advance to the next authorized slice because it acts under the general assigned technical merge-owner regime in `AGENTS.md`;
- stops at a real external gate, a valid maintainer interruption, or slice completion.

A 079 continuation job may use only the implementation, local patch production, deterministic validation, and permitted same-branch delivery subset authorized by spec 079. It must stop before review handling, correction authority, merge, registry reconciliation beyond the active row, or next-slice selection.

### Post-112 Integration Coordinator and domain builders

After the post-112 activation gate:

- the **Integration Coordinator** is the sole normal owner of `STATUS.md`, shared integration boundaries, merge sequencing, registry reconciliation, and cross-lane conflicts;
- each **domain builder** owns only its isolated branch/PR and accepted domain slice;
- a domain builder that reaches a shared boundary produces a bounded integration request rather than racing another writer;
- multiple implementation PRs may exist only when their lanes satisfy the ownership/disjointness rules in the canonical post-112 profile;
- no automation slot is assumed to exist merely because the role is defined, and unrelated maintainer automations are never disabled automatically.

### Watchdog

The external watchdog role:

- detects stalled delivery, abandoned agent tasks, completed but unconsumed CI or review, stale checkpoints, and executable next actions;
- does nothing while the pipeline is genuinely progressing;
- becomes failover writer only with an exact-head guard and no valid writer still active.

A 079 job is never a watchdog for review, merge, or queue advancement.

### Historical time-bounded frontend sprint profile

For 2026-08-05 through 2026-08-15, the repository used the earlier external checkpoint/builder/watchdog cadence documented by the historical sprint profile. That cadence is no longer an instruction to recreate redundant checkpoint/watchdog jobs after the post-112 profile activates.

## 7. Work allocation and model economy

The coordinating chat is the primary reasoning and orchestration layer. It directly performs work that does not require a specialist coding environment or plugin, including:

- repository and diff analysis;
- spec, readiness, PR, and documentation drafting;
- architecture and scope reasoning;
- CI and review consumption;
- finding consolidation;
- contrast and deterministic evidence analysis;
- patch reconstruction and integrity checks;
- bounded mechanical GitHub writes and exact-head merge decisions;
- checkpoint and handoff maintenance only when they add necessary evidence.

External model capacity is finite. Minimize delegation, but do not impose numerical iteration budgets or stop a necessary correction because a call count was reached.

### Review-resource priority

For repository-development work, the default resource order is:

1. the coordinating ChatGPT session performs all work it can safely complete directly;
2. cheap/free bounded workers may perform read-only preflight, impact analysis, candidate review, or other low-authority work when useful;
3. Claude is the default independent specialist/reviewer for material exact-head code correctness, architecture, UX, API/schema-boundary, testing-strategy, and security critique;
4. Codex is a critical reserve for review and should be used only when Claude is genuinely unavailable or inadequate, an unresolved high-risk technical finding justifies a specialist second opinion, or the task has a concrete Codex-specific advantage.

Use Codex for material implementation or non-trivial correction when its coding environment provides a real advantage, but do not consume it for work the coordinator can safely perform directly.

Do **not** use Codex routinely for planning, broad repository reading, CI polling, recap, consolidation, documentation-only work, registry reconciliation, ordinary UI polish, small PRs, or a duplicate second review "for safety".

Do not ask Codex and Claude the same generic question. Do not duplicate independent review on the same immutable head without a material unresolved reason. A head mutation makes prior head-specific review stale where the changed evidence matters.

Cheap/free worker output is advisory. A green Hermes/GLM or similar worker workflow is not merge authority and cannot replace deterministic gates or required independent review.

Mutable PRs should remain draft when that avoids automatic Codex review. Freeze the candidate head and consume the minimum materially necessary review before changing draft state when a non-draft state is actually required.

## 8. Claude consultation and reversible decisions

For a reversible structural or specialist decision:

1. The coordinator inspects code, spec, constraints, and evidence and forms a preferred proposal.
2. If material ambiguity remains, it publishes or submits a SHA-bound review request.
3. Claude reads the same exact SHA and governing sources.
4. Claude returns concrete criticism, risks, minimal corrections, and optional improvements.
5. The coordinator challenges unsupported or over-broad recommendations.
6. Continue while each iteration adds evidence or materially reduces risk.
7. Stop when the result is stable, repetitive, marginal, or entering over-engineering.
8. The coordinator records and executes the final decision.

Recommended markers when PR comments are useful:

```text
CLAUDE_CONSULT_V1
CLAUDE_RESPONSE_V1
COORDINATOR_CRITIQUE_V1
CLAUDE_REVIEW_V2
COORDINATOR_DECISION_V1
```

Do not create these comments if the same evidence is already captured canonically and another comment would be ceremonial.

Reversible, bounded choices may proceed without the maintainer even when they concern UI structure, internal architecture, schemas, or APIs, provided they do not trigger one of the four interruption classes below and remain within accepted spec authority.

## 9. Maintainer interruption boundary

The four interruption classes in `AGENTS.md` are exhaustive:

1. real spending is required or a budget limit is at risk;
2. a required credential, account, repository, or organization does not exist;
3. a security issue, secret exposure, or material data-loss risk exists;
4. an obstacle has no two practicable safe routes forward.

Schema, migration, incompatible API, egress, credential-authority, destructive merge, or hard-to-reverse architecture questions require the maintainer only when they fall into one of those four classes. Otherwise choose the least-cost reversible route, use specialist critique when valuable, record the decision, and proceed.

Do not interrupt for ordinary implementation choices, reversible UI structure, naming, bounded required refactors, recoverable technical obstacles, the merge of 112 itself, or automatic activation of a proved-safe post-112 lane.

## 10. Finding severity and engineering closure

- `P0`: safety, secret exposure, data loss, destructive authority failure, or catastrophic behavior.
- `P1`: required acceptance criterion fails, main workflow is unusable, or a material regression exists.
- `P2`: real defect or weakness whose beta impact must be assessed.
- `P3`: optional refinement, polish, or future improvement.

A merge is blocked by:

- current P0 or P1;
- P2 that materially affects beta correctness, normal use, accessibility, inspectability, or regression risk;
- violated spec requirement;
- unresolved substantial review finding;
- missing required gate.

A merge is not automatically blocked by every P2, any P3, stylistic preference, theoretical refactor, premature generalization, or primarily post-beta improvement.

Evaluate each finding by probability, user impact, operational risk, reversibility, correction cost, regression risk, beta relevance, and value of another iteration.

Continue for as many iterations as necessary to resolve material defects. Stop when additional work becomes marginal polish, repeated argument, unnecessary abstraction, or over-engineering.

## 11. Planning compression, focused gates, and read-only prework

The detailed eligibility rules live in `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` and become applicable only after its activation gate unless a narrower accepted spec already authorizes the same behavior.

After activation:

- low-risk additive/reversible slices may combine definition, full specification, and readiness evidence into one planning PR when the combined artifact preserves exact-master inventory, scope, acceptance criteria, non-goals, failure modes, test plan, and an independently inspectable readiness decision;
- high-risk security, credential, egress, PTY, self-update, delicate migration, Process/solver/evaluator, destructive, or hard-to-reverse ownership work retains the full separate lifecycle;
- moving heads should use focused deterministic tests and minimum relevant gates for rapid iteration; the frozen candidate head must still satisfy every required merge gate;
- browser/screenshot proof is required for visible frontend/layout/interaction deltas or explicit spec requirements, not by default for backend/docs/schema-only changes with no visual delta;
- read-only ownership, source, dependency, threat-model, and future-slice research may happen early when it creates no premature implementation authority and is revalidated on fresh exact `master` before promotion.

A `planned` row remains non-implementable regardless of planning compression or prework.

## 12. Post-beta backlog

A real non-blocking finding is not silently discarded.

Maintain one canonical post-beta backlog rather than per-PR duplicate lists. Create it only when the first real deferred finding exists. Each entry records:

- stable finding ID;
- source PR and exact SHA;
- evidence and impact;
- reason for deferral;
- residual risk;
- concrete reopening condition.

The backlog is not a second `STATUS.md` and does not authorize implementation by itself.

## 13. Merge gate and reconciliation economy

Merge only when all hold on one exact head:

1. authorized diff and scope;
2. acceptance criteria satisfied;
3. required deterministic gates and proofs terminal and green;
4. no P0, P1, or beta-blocking P2;
5. no unresolved substantial review finding;
6. no secret, spending, dependency, schema, provider, or authority conflict;
7. registry state and implementation-PR association correct.

Use `expected_head_sha`. Never enable auto-merge. After merge, verify PR state, resulting commit, `master`, and registry reconciliation.

After the post-112 profile activates, the Integration Coordinator serializes all lane merges. Remaining lanes resolve fresh `master` and revalidate affected evidence after every preceding merge.

Post-merge registry reconciliation may be automated or applied mechanically when the merge SHA is exact and verified, the transition is deterministic, and the operation does not invent new product direction. Avoid separate PRs/checkpoints/comments that add no authority, evidence, or risk reduction. Do not remove an audit, review, or gate that closes a real security, scientific, migration, authority, regression, or acceptance risk.

## 14. Documentation drift review

At definition, readiness, implementation completion, and major queue transitions, compare claims touched by the work across:

- `README.md`;
- `AGENTS.md`;
- this document;
- `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` when post-112 delivery mechanics are implicated;
- `docs/README.md`;
- `docs/ARCHITECTURE.md`;
- `docs/DECISIONS.md`;
- `docs/specs/README.md`;
- `docs/specs/STATUS.md`.

Distinguish onboarding, process, live state, durable architecture, future design, and historical evidence. Correct stale canonical claims in the smallest bounded documentation change. Do not copy the live queue into another document.

### Audit performed on 2026-08-05

Against `master` `a86be9e7d18d6a8cbe2d60a71fdc0ce41ffe2786`:

1. Root `README.md` required human review and prohibited self-merge, while `AGENTS.md` authorized assigned-agent exact-head merge after gates and blocking-finding closure.
2. `docs/specs/README.md` described review as human-controlled, conflicting with current merge ownership.
3. `docs/ARCHITECTURE.md` called `docs/specs/README.md` the live roadmap and copied an obsolete early sequence; `docs/specs/STATUS.md` is the sole live roadmap.
4. `docs/ARCHITECTURE.md` still described Scaleway app-entered credentials as runtime-memory-only, while secure Windows DPAPI persistence is merged and evidenced by specs 082 and 094.
5. `docs/README.md` did not separate live work-state authority, agent process authority, durable decisions, and descriptive architecture.

The entry-point documents now resolve those authority conflicts. Until the stale passages in `docs/ARCHITECTURE.md` receive a direct bounded refresh, they are superseded for roadmap, delivery process, and credential-persistence status by current code, accepted specs and decisions, `STATUS.md`, `AGENTS.md`, and this protocol.

## 15. Minimal continuation handoff

```text
JARVISOS_CONTINUATION_V1

REPOSITORY: AlbertoRacerro/JarvisOS_v1
MASTER_SHA:
ACTIVE_PR:
ACTIVE_HEAD_SHA:
CHECKPOINT_COMMENT:
MAINTAINER_DECISIONS_NOT_YET_IN_REPO: none / ...

Read AGENTS.md, docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md,
docs/specs/STATUS.md, the active spec/readiness record, and the active PR at the
exact SHAs above. After 112 is merged, also read
docs/POST_112_PARALLEL_DELIVERY_PROFILE.md before resuming multiple lanes.
Verify remote state and continue autonomously.
```

Do not add a narrative recap unless repository state cannot express an essential fact.
