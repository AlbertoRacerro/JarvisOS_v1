# Agent execution and automation protocol

Status: canonical operational process
Effective date: 2026-08-05

This document defines how AI coding agents, review agents, scheduled continuations, and coordinating chats execute JarvisOS repository work. It complements `AGENTS.md`: hard invariants and repository safety remain owned by `AGENTS.md`; this file owns the detailed delivery, collaboration, continuation, finding, and documentation-drift process.

It does not change JarvisOS runtime authority, provider policy, credentials, budgets, egress, schemas, or product behavior.

## 1. Minimal startup sequence

A new coordinating chat or agent session must begin by reading, from exact Git SHAs:

1. `AGENTS.md`;
2. this document;
3. `docs/specs/STATUS.md`;
4. `docs/specs/README.md`;
5. the selected specification and its readiness record, if any;
6. the active pull request body, exact head, diff, workflow results, reviews, and unresolved threads.

A minimal handoff should normally contain only:

- repository name;
- active PR number;
- exact `master` SHA;
- exact PR-head SHA;
- the current checkpoint marker;
- any maintainer decision that is not yet recorded in the repository.

Do not reproduce the queue, full spec, or operating rules in chat handoffs. Read them from the repository.

## 2. Authority and conflict resolution

Use the following authority hierarchy for the specific question being answered:

1. Current code, runtime behavior, deterministic tests, and exact-head evidence describe what the system actually does.
2. `AGENTS.md` defines hard invariants, safety boundaries, and general agent conduct.
3. This document defines repository delivery, autonomous continuation, collaboration, finding closure, and documentation-drift handling.
4. `docs/specs/STATUS.md` is the sole live authority for spec state, dependencies, queue order, and implementation PR association.
5. The selected spec and readiness record define the current slice's scope, acceptance criteria, tests, and non-goals.
6. `docs/DECISIONS.md` records durable architecture decisions.
7. `docs/ARCHITECTURE.md` describes current stable architecture only where it is consistent with current code, accepted decisions, and current spec state.
8. Root and directory README files are onboarding and navigation documents, not independent runtime, roadmap, or merge authority.
9. Strategy packs, design documents, milestone reports, task summaries, model comments, and chat handoffs are advisory or historical unless promoted by a canonical source.

When two canonical sources appear to conflict:

- do not resolve by plausibility;
- identify the exact claims and their dates or SHAs;
- prefer current runtime for behavior, `STATUS.md` for work state, the selected spec for slice scope, and accepted ADRs for durable architecture;
- fix the stale canonical document in a bounded documentation change;
- preserve superseded history rather than silently deleting provenance.

## 3. Exact-SHA and freshness rule

Branch names such as `master`, `latest`, or `current head` are not sufficient evidence.

Every implementation, review, checkpoint, audit, and merge decision must record the full 40-character SHA it examined. Reading a file by branch name is acceptable only to discover an SHA; conclusions must be tied to the resolved commit.

When an active PR head changes:

- prior CI and reviews become evidence for the old head only;
- revalidate findings against the new head;
- mark conclusions as still valid, resolved, superseded, or requiring revalidation;
- never merge using a review or gate that belongs to a different head.

## 4. Delivery states

Use these terms precisely:

- `REMOTE_VERIFIED`: the branch advanced, complete files are readable from GitHub, the diff is authorized, and evidence belongs to that exact head.
- `LOCAL_ONLY`: work exists only in an agent checkout, temporary filesystem, or unpushed commit.
- `DECLARED_NOT_VERIFIED`: an agent claims a result, but the remote artifact or evidence has not been independently verified.
- `DELIVERY_FAILURE`: an agent completed or claimed work but failed to make a recoverable remote delivery.
- `BLOCKED`: no authorized practical route remains without maintainer action or a prohibited risk.

A local commit SHA, task link, summary comment, digest of an unavailable artifact, or statement that tests passed is not delivery.

## 5. One active front and one writer

- Follow the binding queue in `STATUS.md`.
- Finish, verify, and merge the first authorized implementation slice before opening the next runtime front.
- Use one implementation branch and one implementation PR per spec.
- Allow only one writer at a time on the active PR.
- Read-only audits may run in parallel only when explicitly useful and must not become competing coordination systems.
- Never create concurrent implementations that touch the same files or runtime boundary.
- If a failover writer is needed, it must use an exact-head guard. The first valid remote write wins; every stale writer stops.

Documentation-only reconciliation requested by the maintainer may temporarily become the active front. Resume the paused implementation after the documentation change is merged or otherwise resolved.

## 6. Autonomous continuation loop

The current frontend sprint uses three cooperating scheduled roles. The roles are reusable even if the exact schedule later changes.

### Checkpoint

The checkpoint role:

- reads GitHub as the source of truth;
- completes unfinished verification from the prior cycle;
- updates one canonical PR comment marked `AUTONOMOUS_FRONTEND_CHECKPOINT_V1`;
- records exact master and PR-head SHAs, delivery state, gates, findings, blockers, owner, and next exact action;
- does not create duplicate status comments or a second live registry.

### Builder

The builder role:

- resumes from the canonical checkpoint;
- acts like a maintainer command to continue;
- performs all sequential safe work available in the current cycle rather than stopping after one micro-action;
- may implement, publish, verify, correct, consume CI/reviews, merge with an expected-head guard, reconcile status, and advance to the next authorized slice;
- stops only at a real external gate, a maintainer-owned decision, or completion of the slice.

### Watchdog

The watchdog role:

- detects stalled delivery, completed-but-unconsumed CI/review, abandoned agent tasks, stale checkpoints, or an executable next action;
- does nothing while the pipeline is genuinely progressing or a real gate is running;
- becomes a failover writer only with an exact-head guard and only when no valid writer remains active.

### Current time-bounded sprint profile

For the 2026-08-05 through 2026-08-15 frontend sprint:

- checkpoint: hourly at minute `00`;
- builder: hourly at minute `10`;
- watchdog: hourly at minute `40`;
- final inspection package: 2026-08-15 after the last operational cycle.

The schedule is an operational profile, not product architecture. Future schedules may change without changing the safety and delivery rules above.

## 7. Work allocation and model economy

The coordinating chat is the primary reasoning and orchestration layer. It should directly perform all work that does not require a specialized coding environment or specialist plugin, including:

- repository reading and diff analysis;
- spec, readiness, PR, and documentation drafting;
- architecture and scope reasoning;
- CI and review consumption;
- finding consolidation;
- contrast calculations and deterministic evidence analysis;
- patch reconstruction, integrity checks, and mechanical GitHub writes;
- exact-head merge decisions;
- handoff and checkpoint maintenance.

Codex and Claude have finite capacity. Minimize delegated work, but do not impose arbitrary numeric budgets or stop necessary correction because an iteration count was reached.

Use Codex when it adds material value for:

- implementation or non-trivial code correction;
- codebase-wide mechanical work that cannot be safely applied directly;
- exact-SHA technical review likely to find defects not covered by deterministic gates.

Do not use Codex for routine planning, general repository reading, CI polling, recap, finding consolidation, or simple documentation edits.

Use Claude when its specialist design, UX, accessibility, testing-strategy, or architecture critique adds material value. Claude is normally a read-only reviewer on the same PR and exact SHA, not a concurrent implementer.

Do not ask Codex and Claude the same generic question. Give each a distinct role.

## 8. Claude consultation protocol

For a reversible structural decision or specialist UI question:

1. The coordinator first inspects the code, spec, constraints, and evidence and forms a preferred proposal.
2. If material ambiguity remains, publish a SHA-bound request in the active PR.
3. Claude reads the same exact SHA, the governing sources, and only the files needed for the question.
4. Claude returns concrete criticism, risks, minimal corrections, and optional improvements.
5. The coordinator challenges unsupported or over-broad recommendations.
6. Continue only while each iteration adds new evidence or materially reduces risk.
7. Stop when the answer is stable, repetitive, or entering over-engineering.
8. The coordinator records the final decision and rationale.

Recommended markers:

```text
CLAUDE_CONSULT_V1
CLAUDE_RESPONSE_V1
COORDINATOR_CRITIQUE_V1
CLAUDE_REVIEW_V2
COORDINATOR_DECISION_V1
```

Claude may advise without the maintainer when the decision is reversible, bounded to the active spec, and does not change security, spending, credentials, egress, schemas, migrations, incompatible APIs, or destructive architecture.

## 9. Maintainer interruption boundary

Proceed autonomously through reversible repository work. Interrupt the maintainer for decisions involving any of the following:

- real spending, a new provider/account, or a budget risk;
- missing credentials, repository, organization, or external account;
- security exposure, secrets, or material data-loss risk;
- schema or migration choices with durable data consequences;
- new credential or egress authority;
- intentionally incompatible API changes;
- destructive merges, force pushes, or hard-to-reverse architecture changes;
- conflicting canonical authority that cannot be resolved from current evidence;
- an obstacle with no two practicable safe routes.

Do not interrupt for ordinary implementation choices, reversible UI structure, naming, bounded refactors required by the spec, or recoverable technical obstacles.

## 10. Finding severity and engineering closure

Severity labels guide analysis but do not replace engineering judgment.

- `P0`: safety, secret exposure, data loss, destructive authority failure, or catastrophic behavior.
- `P1`: a required acceptance criterion fails, a main workflow is unusable, or a material regression exists.
- `P2`: a real defect or weakness whose beta impact must be assessed.
- `P3`: optional refinement, polish, or future improvement.

A merge is blocked by:

- any current P0 or P1;
- a P2 that materially affects beta correctness, normal use, accessibility, inspectability, or regression risk;
- a violated spec requirement;
- an unresolved substantial review thread;
- a missing required gate.

A merge is not automatically blocked by every P2, any P3, stylistic preference, theoretical refactor, premature generalization, or improvement whose value is predominantly post-beta.

Evaluate each finding by:

- probability and user impact;
- operational and security risk;
- reversibility;
- correction cost and regression risk;
- beta relevance;
- value gained by another iteration.

Continue for as many iterations as necessary to resolve material defects. Stop when further work becomes marginal polish, repeated argument, unnecessary abstraction, or over-engineering.

## 11. Post-beta backlog

A real non-blocking finding must not be silently discarded.

Maintain one canonical post-beta backlog rather than per-PR duplicate lists. Each entry must record:

- stable finding ID;
- source PR and exact SHA;
- evidence;
- user or operational impact;
- reason for deferral;
- residual risk;
- concrete condition for reopening.

The backlog is not a second `STATUS.md`, does not change spec state, and does not authorize implementation by itself.

Create the backlog file only when the first real deferred finding exists. Until then, the active PR may record that no canonical backlog entry was necessary.

## 12. Merge gate

Merge only when all of the following hold on one exact head:

1. authorized diff and scope;
2. acceptance criteria satisfied;
3. required deterministic gates and proofs terminal and green;
4. no P0, P1, or beta-blocking P2;
5. no unresolved substantial review finding;
6. no secret, spending, dependency, schema, provider, or authority conflict;
7. registry state and implementation PR association are correct.

Use `expected_head_sha`. Never enable auto-merge. After merge, verify the PR state, resulting commit, `master`, and registry reconciliation.

## 13. Documentation drift review

Canonical documents must be treated as maintained interfaces, not static prose.

At definition, readiness, implementation completion, and major queue transitions:

- compare `README.md`, `AGENTS.md`, this document, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/specs/README.md`, and `docs/specs/STATUS.md` for claims touched by the work;
- distinguish onboarding, process, live state, durable architecture, future design, and historical evidence;
- correct stale canonical claims in the smallest bounded documentation change;
- do not copy the current queue into another document;
- date time-sensitive assertions and identify their source SHA or PR.

### Audit performed on 2026-08-05

The following conflicts were confirmed against `master` `a86be9e7d18d6a8cbe2d60a71fdc0ce41ffe2786`:

1. Root `README.md` stated that merge authority required human review and prohibited self-merge. `AGENTS.md` had already superseded that rule with assigned-agent exact-head merge authority after deterministic gates and blocking-finding closure.
2. `docs/specs/README.md` described review as human-controlled. The current process uses advisory model review plus an assigned technical merge owner under `AGENTS.md` and this protocol.
3. `docs/ARCHITECTURE.md` called `docs/specs/README.md` the live roadmap and copied an obsolete early sequence. `docs/specs/STATUS.md` is the sole live roadmap and must not be duplicated.
4. `docs/ARCHITECTURE.md` still described Scaleway app-entered credentials as runtime-memory-only. Secure Windows DPAPI persistence is merged and evidenced by specs 082 and 094 and their Windows checkpoint.
5. `docs/README.md` did not define separate authority for live work state, agent execution process, and descriptive architecture, allowing stale architectural prose to appear stronger than current code or `STATUS.md`.

The entry-point documents are updated with this protocol. Until the stale descriptive passages in `docs/ARCHITECTURE.md` are directly refreshed, they are explicitly superseded for roadmap, delivery process, and credential-persistence status by current code, accepted specs/decisions, `STATUS.md`, `AGENTS.md`, and this document.

## 14. Minimal continuation handoff

Use this format when opening a new coordinating chat:

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
