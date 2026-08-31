# Agent execution and automation protocol

Status: canonical operational process
Effective date: 2026-08-05
Amended: 2026-08-31 — ChatGPT direct implementation default and non-blocking optional model helpers

This document defines JarvisOS repository delivery, external model collaboration, exact-head evidence, finding closure, merge/reconciliation, and the controlled post-112 delivery exception. It governs repository-development actors only; it does not broaden JarvisOS runtime authority, provider policy, credentials, budgets, egress, schemas, or product behavior.

`AGENTS.md` remains authoritative for hard invariants, safety boundaries, general conduct, the exhaustive maintainer-interruption classes, and accepted specification-specific exceptions. `docs/specs/STATUS.md` remains the sole live authority for spec state, dependencies, queue order, and implementation-PR association. `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` is the subordinate canonical mechanics profile after its activation gate.

Spec 079 remains narrower than this protocol. Its repository-internal scheduled continuation is implementation-only and cannot review, repair findings, merge, select a new spec, or advance the queue. Nothing in this document broadens 079.

## 1. Minimal startup sequence

A coordinating ChatGPT session starts from exact Git state by reading:

1. `AGENTS.md`;
2. this document;
3. `docs/specs/STATUS.md`;
4. `docs/specs/README.md`;
5. the selected spec and readiness record;
6. the active PR body, exact head, diff, workflows, reviews, and unresolved threads;
7. after 112 is merged, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` before opening or resuming multiple lanes.

A continuation handoff should normally contain only repository, exact `master` SHA, active PR, exact PR-head SHA, and maintainer decisions not yet recorded canonically. Do not copy queue/spec/process text into every chat handoff.

## 2. Authority by question

1. Current code, runtime behavior, deterministic tests, and exact-head evidence describe actual behavior.
2. `AGENTS.md` defines hard invariants, safety boundaries, general conduct, and accepted narrow exceptions.
3. This protocol defines repository-development delivery mechanics.
4. After its activation gate, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` defines the narrower controlled-parallel mechanics.
5. `docs/specs/STATUS.md` is the sole live authority for spec state, dependencies, queue order, and implementation-PR association.
6. The selected spec and readiness record define slice scope, acceptance criteria, tests, and non-goals.
7. `docs/DECISIONS.md` records durable architecture decisions.
8. `docs/ARCHITECTURE.md` is descriptive only where consistent with current code, accepted decisions, and live spec state.
9. README files, strategy packs, milestone reports, model summaries, and chat handoffs are not independent runtime, roadmap, or merge authority.

When sources conflict, use runtime evidence for behavior, `STATUS.md` for work state, the active spec for slice scope, accepted ADRs for durable architecture, and the narrower accepted spec for an exception. Fix stale canonical prose in a bounded docs change; do not resolve by plausibility alone.

## 3. Exact-SHA and freshness rule

Branch names such as `master`, `latest`, or `current head` are not sufficient evidence.

Every implementation, review, acceptance decision, audit, lane-ownership decision, and merge decision records the full 40-character SHA examined. When a PR head changes, earlier CI and reviews remain evidence only for the old head and must be revalidated where affected. No merge relies on a gate from another head.

After one post-112 lane merges, every remaining lane resolves fresh `master` and revalidates ancestry-, shared-owner-, dependency-, or gate-sensitive conclusions before its own merge.

## 4. Delivery states

- `REMOTE_VERIFIED`: branch advanced; complete files are readable from GitHub; diff is authorized; evidence belongs to that exact head.
- `LOCAL_ONLY`: work exists only in an agent checkout, temporary filesystem, or unpushed commit.
- `DECLARED_NOT_VERIFIED`: an agent claims a result without independently verified remote evidence.
- `DELIVERY_FAILURE`: work was claimed or completed but no recoverable remote delivery exists.
- `BLOCKED`: no authorized practical route remains without maintainer action or prohibited risk.

A local commit SHA, task link, model report, or green workflow claim is not delivery by itself.

## 5. Serial execution through 112; controlled lanes after 112

Until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` as `merged`:

- follow `STATUS.md` serially;
- finish, verify, and merge the first authorized runtime slice before opening the next runtime front;
- use one implementation branch and one implementation PR per spec;
- allow one writer at a time on the active PR;
- do not create concurrent implementations over the same files or authority boundary;
- a failover writer uses an exact-head guard; stale writers stop;
- a maintainer-requested docs/governance reconciliation may temporarily become the active front.

This rule is absolute through 112. Presence of the post-112 profile is not pre-112 implementation authority.

After exact `master` shows 112 merged, `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` becomes the canonical scheduling exception. Only demonstrated-disjoint lanes may run concurrently; `STATUS.md`, readiness, hard dependencies, exact-head gates, and one-writer-per-PR remain binding.

## 6. Normative repository-development role split

This is the only current live external-model collaboration policy for normal repository delivery:

### ChatGPT — default direct implementer / Tech Lead / Architect / Maintainer

ChatGPT owns:

- fresh repo/context reading;
- architecture and ownership decisions;
- definition, full spec, and readiness;
- direct implementation and repair of authorized READY work by default;
- acceptance criteria, scope, non-goals, invariants, and required checks;
- semantic review of exact diffs and candidate evidence;
- integration, shared authority, `STATUS.md`, exact-head merge, and registry reconciliation.

ChatGPT does not delegate governance/spec/queue authority to coding models and does not require an external candidate before implementing or repairing work it can safely complete itself.

### External/model workers — optional proposal-only helpers

GLM, Codex, Claude, or another model worker may be used only when fresh authority permits a genuinely bounded/disjoint task and delegation has a concrete throughput or risk-reduction advantage. A helper packet must include, as applicable:

- exact target SHA and exact base SHA;
- allowed paths/boundaries;
- a bounded set of preloaded authority/context files;
- required behavior;
- explicit non-goals;
- acceptance tests/checks;
- any path, tool, exploration, or authority restrictions.

External/model workers produce proposal-only candidate evidence or patches. They own no GitHub write, merge, shared-authority, queue, spec, architecture, provider, credential, policy, or promotion decision. Delegation must not duplicate the active implementation, replace direct progress that ChatGPT can safely make, or become a session wait/stop condition.

### ChatGPT acceptance and repair

ChatGPT reviews exact diff, scope, semantics, invariants, and test evidence. A green worker workflow alone is not semantic PASS.

ChatGPT repairs directly by default. If a useful external candidate is already terminal, ChatGPT may consume and minimally repair it rather than discard it, but no external candidate or repair hop is required before direct progress continues.

### Claude — independent terminal reviewer

Claude is an independent terminal reviewer when independent review is required by the accepted slice/policy or materially useful for risk reduction. Claude is reviewer, not a required implementation hop.

### Codex — scarce specialist/high-risk reserve

Codex is used only where a concrete material advantage or unresolved high-risk need justifies it. Do not spend Codex routinely on docs/planning/reconciliation, small PRs, ordinary UI polish, CI watching, or duplicate review. Do not ask Claude and Codex the same generic question on one immutable head without a material unresolved reason.

### Evidence precedence

Deterministic repository/runtime evidence and accepted authority outrank every model claim. Workflow green does not establish semantic correctness. Head mutation invalidates head-specific acceptance/review evidence where the changed content matters.

## 7. Post-112 scheduler and lane mechanics

After 112 merges, scheduler identities are generic ChatGPT compute slots. Integration/Knowledge/Development/Coding are logical responsibilities acquired dynamically under the post-112 profile, not permanent automation identities.

Only one ChatGPT coordinator/writer may own GitHub/shared-authority mutation at a time. Optional external/model helpers may execute concurrently only on demonstrably disjoint exact-head tasks/lanes and remain proposal-only. Shared boundaries remain Integration-owned.

The coordinator consumes terminal evidence, advances immediately actionable work directly, and may launch bounded optional helper work when useful. Active non-terminal CI/checks/reviews are normal in-session waits: the coordinator uses that interval for useful non-conflicting work and re-checks them at a reasonable cadence until terminal when the session remains active. External/model-worker availability or completion never blocks direct work that can otherwise proceed. The coordinator does not sleep or poll merely to consume runtime, but it also does not treat an ordinary active CI/review wait as an automatic session exit while useful in-session progress or timely terminal consumption remains possible.

## 8. Spec 079 boundary

A job running under spec 079 must ignore any broader capability described here and remain inside 079's accepted implementation-only boundary:

- reconstruct authority from exact PR-head repository state;
- produce only an untrusted local patch artifact;
- use the separately bounded no-secret actuator for permitted deterministic validation and non-forced same-branch push;
- no review, review-repair, merge, labels, new-spec selection, queue advancement, settings/secrets mutation, or provider dispatch beyond 079's accepted path;
- no broadening from this protocol or from post-112 external scheduling.

Spec 080, while frozen/planned, grants no live review/repair automation authority.

## 9. Maintainer interruption boundary

The four interruption classes in `AGENTS.md` are exhaustive:

1. real spending is required or a budget limit is at risk;
2. a required credential, account, repository, or organization does not exist;
3. a security issue, secret exposure, or material data-loss risk exists;
4. an obstacle has no two practicable safe routes forward.

Otherwise choose the least-cost reversible route, use independent critique where valuable, record the decision, and proceed within accepted spec authority.

## 10. Finding severity and engineering closure

- `P0`: safety, secret exposure, data loss, destructive authority failure, or catastrophic behavior.
- `P1`: required acceptance criterion fails, main workflow is unusable, or a material regression exists.
- `P2`: real defect or weakness whose current-slice impact must be assessed.
- `P3`: optional refinement, polish, or future improvement.

A merge is blocked by current P0/P1; a P2 that materially affects required correctness, accessibility, inspectability, or regression risk; violated spec requirements; unresolved substantial review findings; or a missing required gate.

A merge is not automatically blocked by every P2, any P3, stylistic preference, theoretical refactor, premature generalization, or future improvement. Continue correction while it materially reduces risk; stop when work becomes marginal polish or over-engineering.

## 11. Planning compression, focused gates, and read-only prework

Detailed eligibility rules live in `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md` and apply only after its activation gate unless a narrower accepted spec already authorizes the same behavior.

After activation:

- low-risk additive/reversible slices may combine definition, full specification, and readiness evidence into one planning PR only when exact-master inventory, scope, acceptance criteria, non-goals, failure modes, test plan, and an independently inspectable readiness decision remain explicit;
- high-risk security, credential, egress, PTY, self-update, delicate migration, Hermes isolation/model-call closure, Process/solver/evaluator, destructive, or hard-to-reverse ownership work retains the full separate lifecycle;
- moving heads use focused deterministic tests; frozen candidate heads satisfy every required merge gate;
- browser proof is required for visible frontend/layout/interaction deltas or explicit spec requirements, not by ceremony for docs/backend-only changes;
- read-only ownership/source/dependency/threat-model research may happen early only without premature implementation authority and must be revalidated on fresh exact `master` before promotion.

A `planned` row remains non-implementable regardless of planning compression or prework.

## 12. Merge gate and reconciliation

Merge only when all hold on one exact head:

1. authorized diff and scope;
2. acceptance criteria satisfied;
3. required deterministic gates and proofs terminal and green;
4. no P0, P1, or blocking P2;
5. no unresolved substantial review finding;
6. no secret, spending, dependency, schema, provider, or authority conflict;
7. registry state and implementation-PR association correct.

Use `expected_head_sha`. Never enable auto-merge. After merge, verify PR state, resulting commit, fresh `master`, and registry reconciliation.

After post-112 activation, the single ChatGPT Integration writer serializes shared mutations and merges. Remaining lanes refresh `master` and affected evidence after each merge.

Avoid separate PRs, comments, checkpoints, screenshot passes, or repeated gates that add no authority, evidence, or risk reduction.

## 13. Documentation drift review

At definition, readiness, implementation completion, and major queue transitions, compare touched claims across `README.md`, `AGENTS.md`, this protocol, the post-112 profile when relevant, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/specs/README.md`, and `docs/specs/STATUS.md`.

Distinguish onboarding, process, live state, durable architecture, future design, and history. Correct stale canonical claims in the smallest bounded docs change. Do not copy the live queue into another policy document.

## 14. Historical / non-normative provenance

Earlier external checkpoint/builder/watchdog and time-bounded frontend-sprint arrangements were delivery mechanisms used during prior phases. They are historical provenance only and are not live instructions, role definitions, scheduler identities, or authority sources.

The 2026-08-05 documentation audit identified then-stale human-merge, roadmap, and credential-persistence prose. Those findings explain prior reconciliations but do not create current command authority.

## 15. Minimal continuation handoff

```text
JARVISOS_CONTINUATION_V1

REPOSITORY: AlbertoRacerro/JarvisOS_v1
MASTER_SHA:
ACTIVE_PR:
ACTIVE_HEAD_SHA:
MAINTAINER_DECISIONS_NOT_YET_IN_REPO: none / ...

Read AGENTS.md, docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md,
docs/specs/STATUS.md, the active spec/readiness record, and the active PR at the
exact SHAs above. After 112 is merged, also read
docs/POST_112_PARALLEL_DELIVERY_PROFILE.md before resuming multiple lanes.
Verify remote state and continue autonomously.
```

Do not add a narrative recap unless repository state cannot express an essential fact.