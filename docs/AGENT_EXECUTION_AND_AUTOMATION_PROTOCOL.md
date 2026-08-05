# Agent execution and automation protocol

Status: canonical operational process
Effective date: 2026-08-05

This document defines repository delivery, autonomous continuation, model collaboration, finding closure, post-beta deferral, and documentation-drift handling for JarvisOS coding and review agents.

`AGENTS.md` remains authoritative for hard invariants, safety boundaries, general conduct, and the exhaustive maintainer-interruption classes. This protocol adds execution detail without changing JarvisOS runtime authority, provider policy, credentials, budgets, egress, schemas, or product behavior.

## 1. Minimal startup sequence

A coordinating chat or agent session starts by reading, from exact Git SHAs:

1. `AGENTS.md`;
2. this document;
3. `docs/specs/STATUS.md`;
4. `docs/specs/README.md`;
5. the selected spec and readiness record;
6. the active PR body, exact head, diff, workflows, reviews, and unresolved threads.

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
2. `AGENTS.md` defines hard invariants, safety boundaries, and general agent conduct.
3. This document defines delivery and autonomous execution mechanics.
4. `docs/specs/STATUS.md` is the sole live authority for spec state, dependencies, queue order, and implementation-PR association.
5. The selected spec and readiness record define slice scope, acceptance criteria, tests, and non-goals.
6. `docs/DECISIONS.md` records durable architecture decisions.
7. `docs/ARCHITECTURE.md` describes stable architecture only where consistent with current code, accepted decisions, and current spec state.
8. README files are onboarding and navigation, not independent runtime, roadmap, or merge authority.
9. Strategy packs, design docs, milestone reports, model summaries, and chat handoffs are advisory or historical unless promoted by a canonical source.

When sources conflict:

- identify exact claims, dates, and SHAs;
- use runtime evidence for behavior, `STATUS.md` for work state, the active spec for slice scope, and accepted ADRs for durable architecture;
- do not resolve by plausibility alone;
- fix stale canonical prose in a bounded documentation change;
- preserve superseded history when it carries provenance.

## 3. Exact-SHA and freshness rule

Branch names such as `master`, `latest`, or `current head` are not sufficient evidence.

Every implementation, review, checkpoint, audit, and merge decision records the full 40-character SHA examined. A branch name may be used to discover an SHA, but conclusions are tied to the resolved commit.

When the PR head changes:

- earlier CI and reviews remain evidence only for the old head;
- findings are revalidated;
- conclusions are classified as still valid, resolved, superseded, or requiring revalidation;
- no merge relies on a gate from another head.

## 4. Delivery states

- `REMOTE_VERIFIED`: branch advanced; complete files are readable from GitHub; diff is authorized; evidence belongs to that exact head.
- `LOCAL_ONLY`: work exists only in an agent checkout, temporary filesystem, or unpushed commit.
- `DECLARED_NOT_VERIFIED`: an agent claims a result without independently verified remote evidence.
- `DELIVERY_FAILURE`: work was claimed or completed but no recoverable remote delivery exists.
- `BLOCKED`: no authorized practical route remains without maintainer action or prohibited risk.

A local commit SHA, task link, summary comment, or test claim is not delivery.

## 5. One active front and one writer

- Follow the queue in `STATUS.md`.
- Finish, verify, and merge the first authorized runtime slice before opening the next runtime front.
- Use one implementation branch and one implementation PR per spec.
- Allow one writer at a time on the active PR.
- Do not create concurrent implementations over the same files or runtime boundary.
- A failover writer uses an exact-head guard. The first valid remote write wins; stale writers stop.
- A maintainer-requested documentation reconciliation may temporarily become the active front. Resume the paused implementation after it is resolved.

## 6. Autonomous continuation roles

### Checkpoint

The checkpoint role:

- reads GitHub as source of truth;
- completes unfinished verification;
- maintains one PR comment marked `AUTONOMOUS_FRONTEND_CHECKPOINT_V1`;
- records exact SHAs, delivery state, gates, findings, blocker, owner, and next exact action;
- does not create another registry or duplicate status comments.

### Builder

The builder role:

- resumes from the checkpoint;
- acts like a maintainer command to continue;
- performs all sequential safe work available in the cycle instead of stopping after one micro-action;
- may implement, publish, verify, correct, consume CI/reviews, merge with an expected-head guard, reconcile status, and advance to the next authorized slice;
- stops at a real external gate, a valid maintainer interruption, or slice completion.

### Watchdog

The watchdog role:

- detects stalled delivery, abandoned agent tasks, completed but unconsumed CI/review, stale checkpoints, and executable next actions;
- does nothing while the pipeline is genuinely progressing;
- becomes failover writer only with an exact-head guard and no valid writer still active.

### Current time-bounded frontend sprint profile

For 2026-08-05 through 2026-08-15:

- checkpoint: hourly at minute `00`;
- builder: hourly at minute `10`;
- watchdog: hourly at minute `40`;
- final inspection package: 2026-08-15 after the final operational cycle.

This schedule is an operational profile, not product architecture.

## 7. Work allocation and model economy

The coordinating chat is the primary reasoning and orchestration layer. It directly performs work that does not require a specialist coding environment or plugin, including:

- repository and diff analysis;
- spec, readiness, PR, and documentation drafting;
- architecture and scope reasoning;
- CI and review consumption;
- finding consolidation;
- contrast and deterministic evidence analysis;
- patch reconstruction and integrity checks;
- mechanical GitHub writes and exact-head merge decisions;
- checkpoint and handoff maintenance.

Codex and Claude have finite capacity. Minimize delegation, but do not impose numerical iteration budgets or stop a necessary correction because a call count was reached.

Use Codex for material implementation, non-trivial code correction, codebase-wide mechanical work that cannot be safely applied directly, or exact-SHA technical review likely to expose defects not covered by gates.

Do not use Codex for routine planning, broad repository reading, CI polling, recap, consolidation, or simple documentation edits.

Use Claude when specialist design, UX, accessibility, testing-strategy, or architecture critique adds material value. Claude is normally a read-only reviewer on the same PR and SHA, not a competing implementer.

Do not ask Codex and Claude the same generic question.

## 8. Claude consultation and reversible decisions

For a reversible structural or specialist UI decision:

1. The coordinator inspects code, spec, constraints, and evidence and forms a preferred proposal.
2. If material ambiguity remains, it publishes a SHA-bound request in the active PR.
3. Claude reads the same exact SHA and governing sources.
4. Claude returns concrete criticism, risks, minimal corrections, and optional improvements.
5. The coordinator challenges unsupported or over-broad recommendations.
6. Continue while each iteration adds evidence or materially reduces risk.
7. Stop when the result is stable, repetitive, marginal, or entering over-engineering.
8. The coordinator records and executes the final decision.

Recommended markers:

```text
CLAUDE_CONSULT_V1
CLAUDE_RESPONSE_V1
COORDINATOR_CRITIQUE_V1
CLAUDE_REVIEW_V2
COORDINATOR_DECISION_V1
```

Reversible, bounded choices may proceed without the maintainer even when they concern UI structure, internal architecture, schemas, or APIs, provided they do not trigger one of the four interruption classes below and remain within accepted spec authority.

## 9. Maintainer interruption boundary

The four interruption classes in `AGENTS.md` are exhaustive:

1. real spending is required or a budget limit is at risk;
2. a required credential, account, repository, or organization does not exist;
3. a security issue, secret exposure, or material data-loss risk exists;
4. an obstacle has no two practicable safe routes forward.

Schema, migration, incompatible API, egress, credential-authority, destructive merge, or hard-to-reverse architecture questions require the maintainer only when they fall into one of those four classes. Otherwise choose the least-cost reversible route, use Claude critique when valuable, record the decision, and proceed.

Do not interrupt for ordinary implementation choices, reversible UI structure, naming, bounded required refactors, or recoverable technical obstacles.

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

## 11. Post-beta backlog

A real non-blocking finding is not silently discarded.

Maintain one canonical post-beta backlog rather than per-PR duplicate lists. Create it only when the first real deferred finding exists. Each entry records:

- stable finding ID;
- source PR and exact SHA;
- evidence and impact;
- reason for deferral;
- residual risk;
- concrete reopening condition.

The backlog is not a second `STATUS.md` and does not authorize implementation by itself.

## 12. Merge gate

Merge only when all hold on one exact head:

1. authorized diff and scope;
2. acceptance criteria satisfied;
3. required deterministic gates and proofs terminal and green;
4. no P0, P1, or beta-blocking P2;
5. no unresolved substantial review finding;
6. no secret, spending, dependency, schema, provider, or authority conflict;
7. registry state and implementation-PR association correct.

Use `expected_head_sha`. Never enable auto-merge. After merge, verify PR state, resulting commit, `master`, and registry reconciliation.

## 13. Documentation drift review

At definition, readiness, implementation completion, and major queue transitions, compare claims touched by the work across:

- `README.md`;
- `AGENTS.md`;
- this document;
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

## 14. Minimal continuation handoff

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
exact SHAs above. Verify remote state and continue autonomously.
```

Do not add a narrative recap unless repository state cannot express an essential fact.
