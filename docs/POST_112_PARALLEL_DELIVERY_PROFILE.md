# Post-112 controlled parallel delivery profile

Status: canonical operational profile, dormant until activation gate
Authorized: 2026-08-28
Maintainer acceleration amendment: 2026-08-28
Final role-split reconciliation: 2026-08-28
Maintainer hardening-priority amendment: 2026-08-30
Delivery-efficiency amendment: 2026-08-31

This document defines the minimum controlled-parallel delivery exception to the repository's normal serial execution rule. It changes repository-development mechanics only. It does not change JarvisOS runtime authority, provider policy, product architecture, credentials, egress, schemas, or model-promotion rules.

`docs/specs/STATUS.md` remains the sole live source of truth for work state, dependencies, queue order, and implementation-PR association. This file is not a second roadmap. A future ordering described here becomes executable only when matching live registry authority exists in `STATUS.md`.

## 1. Activation gate

The profile is **dormant** until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` with registry status `merged`.

Before that condition is true:

- implementation remains serial through 112;
- no parallel runtime implementation lane is authorized by this document;
- no agent may use this document to skip a dependency, start a `planned` spec, or open a second implementation front.

At the first coordinating cycle after 112 is merged, ChatGPT re-reads exact `master`, `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, candidate specs/readiness, current PRs/evidence, and current ownership. Activation is automatic only for lanes whose file, store, schema, migration, and authority boundaries are demonstrated to be sufficiently disjoint.

If disjointness cannot be proved, only the conflicting slices remain serial. Independent lanes may proceed. Maintainer interruption is required only for the four canonical classes in `AGENTS.md`.

### 1A. Temporary hardening-first priority — 2026-08-30

The maintainer has temporarily overridden normal post-112 lane scheduling order to front-load architecture/reliability hardening before the broader 113–126 roadmap resumes. This is a **scheduling priority override only**: it does not convert a `planned` row into implementation authority and it does not invalidate an already accepted readiness decision.

At the time of this amendment, PR #434 is the only active JarvisOS PR. Finish and reconcile that already-started planning work first. Do not resurrect stale branches merely because they predate this amendment.

After #434 closes cleanly, the first new front is `128 ARCHITECTURE-ENFORCEMENT-GATE-1`, which must complete its normal definition/full-spec/readiness/implementation lifecycle. After 128 is accepted and merged, the next priority is one separately accepted JarvisOS integration slice for `jarvis-pr-attention` V1.11, preserving the tool as read-only, advisory, stateless exact-head evidence only and never as semantic acceptance, approval/comment, merge, queue, persistence, or source-of-truth authority.

After that integration is accepted, continue hardening in this order:

`127 -> (129 / 130 / 132 when fresh disjointness permits) -> 131 -> 133 -> 134`

Until `134 MERGE-AUTHORITY-HARDENING-1` is merged:

- do not start 113 implementation;
- do not start new 114–126 planning or implementation fronts;
- 113 may remain technically `ready`, but that readiness is intentionally held by this scheduling priority;
- the hardening sequence above overrides the normal Knowledge/Development/Coding/provider lane scheduling priority.

After 134 merges, this temporary hold is lifted automatically. Resume 113 plus 114+ and the other canonical post-112 lanes in controlled parallel according to then-current `STATUS.md`, dependencies, accepted readiness, disjointness, and exact-head evidence.

## 2. Scheduler identities, logical locks, and global writer mutex

Scheduler identities are generic ChatGPT compute slots. Integration, Knowledge, Development, and Coding are **logical responsibilities acquired dynamically**, not permanent automation identities.

The normal post-112 scheduler topology is four interchangeable ChatGPT replicas staggered at `:00`, `:15`, `:30`, and `:45`. They reduce reaction latency; they do **not** authorize concurrent ChatGPT writers.

Every replica uses the same global ChatGPT writer-mutex protocol through the automation control plane before any GitHub/shared-authority mutation:

1. read the live automation topology with `automations.peek`;
2. if any other JarvisOS Roadmap Builder A/B/C/D title is `[BUSY <UTC-ISO>]` and that timestamp is less than **20 minutes** old, do not mutate shared authority;
3. otherwise rename only itself to its base title plus `[BUSY <UTC-ISO>]`;
4. immediately re-read the automation topology;
5. if another fresh A/B/C/D BUSY marker is now present, restore the base title and exit mutation mode; otherwise this replica is the sole ChatGPT coordinator/writer for the run;
6. before every later mutation boundary, if the replica has held the lease for **10 minutes or more** since the timestamp currently in its title, refresh only its own BUSY timestamp and immediately re-peek; if a competing fresh writer now exists, restore the base title and abort the mutation;
7. before returning, always restore its base title, including after a failure path.

No GitHub/shared-authority mutation occurs before the post-rename re-check. A BUSY marker **20 minutes or older is stale and is not ownership evidence**. A writer that resumes after a stall may not rely on its previous title: before any new mutation it must refresh its own timestamp and re-peek, so a safe takeover that happened during the stall wins. This bounds a crashed/stalled writer's normal throughput penalty while preserving fail-closed exclusion at every mutation boundary.

The title lease remains an anti-waste coordination mechanism only. Exact SHA/CAS, current branch/head state, and revalidation remain correctness. The four schedulers may all remain enabled; mutual exclusion is achieved by this peek/mark/re-peek/heartbeat protocol rather than by fixed lane affinity.

While one replica owns the writer role:

- **only one ChatGPT coordinator/writer may mutate GitHub/shared authority at a time**;
- the owner temporarily holds Integration responsibilities and may service any currently authorized lane;
- logical lane ownership is acquired for the current bounded action and released when that action is complete;
- no two writers may mutate the same PR/head or shared authority concurrently.

Shared integration boundaries remain Integration-owned, including `STATUS.md`, shared routers/registries, migration/schema sequencing, common Jarvis/AI infrastructure, shared API clients/global frontend integration, root configuration, repository-wide workflows/control files, and any path a fresh ownership audit shows is shared.

A domain lane that needs a shared mutation produces a bounded integration request/candidate and does not race the coordinator for the shared file.

## 3. Normative model-role split

The only current live repository-development pipeline is:

`ChatGPT spec/plan/packet -> GLM candidate implementation -> ChatGPT acceptance -> GLM REPAIR ONLY when needed -> Claude independent terminal review when required/useful -> ChatGPT exact-head merge/reconcile`

### ChatGPT — Tech Lead / Architect / Maintainer

ChatGPT owns fresh repo/context reading, architecture/ownership, definition/full spec/readiness, implementation packets, scope/non-goals/acceptance criteria, semantic candidate review, integration, shared authority, `STATUS.md`, exact-head merge, and reconciliation.

### GLM-5.3-Flash — default bounded coding and repair implementer

For non-trivial READY code slices, GLM-5.3-Flash is the default bounded coding implementer. Each task receives exact target/base SHA, allowed paths/boundaries, preloaded authority/context, required behavior, non-goals, and acceptance tests/checks.

GLM:

- writes candidate patches only in an ephemeral checkout;
- owns no GitHub write, merge, queue, spec, architecture, policy, provider, credential, promotion, or shared-authority role;
- is not the default broad/general/adversarial reviewer;
- may run in parallel with other GLM candidate workers only on demonstrably disjoint exact-head tasks/lanes;
- should normally have at most one active candidate worker per lane/head unless a fresh disjointness/value proof justifies more.

Completion-first applies: give a bounded task enough budget to complete instead of preferring a cheap failed attempt, while keeping path, exploration, tool, and authority scope narrow.

### ChatGPT acceptance and GLM repair

After GLM output, ChatGPT reviews diff, scope, semantics, invariants, and test evidence. Workflow green alone is not semantic PASS. If materially fixable, ChatGPT normally issues a narrow GLM `REPAIR ONLY` packet with numbered findings rather than discard/reimplement the candidate.

ChatGPT codes directly only for trivial/mechanical fixes, minimal delivery plumbing, or proven GLM failure where another delegation is not worthwhile.

### Claude — independent terminal reviewer

Claude is the normal independent terminal reviewer when required by the accepted slice/policy or materially useful for risk reduction. Claude is a reviewer, not the default implementer.

### Codex — scarce specialist/high-risk reserve

Codex is used only when there is a concrete material advantage or unresolved high-risk need. Do not use it routinely for planning, docs-only work, reconciliation, ordinary UI polish, small PRs, CI watching, or duplicate review.

Deterministic repo/runtime evidence and accepted authority outrank all model claims.

## 4. Work-stealing cycle

A ChatGPT lock holder must:

1. resolve fresh exact `master`, `STATUS.md`, current PR heads, workflow/review evidence, and terminal/running candidate-worker state;
2. reject stale model/workflow results whose target head is no longer authoritative;
3. consume already-terminal safe evidence first, using an exact-current-head validated `PR Attention Evidence` manifest/artifact as the first compact **mechanical index** when available;
4. fetch raw GitHub state wherever semantic review, unresolved findings/threads, missing fields, mutation verification, or a canonical gate requires it; the helper artifact never substitutes for those decisions;
5. scan all currently authorized lanes rather than assuming a scheduler-specific lane;
6. advance an immediately actionable lane one bounded step at a time while preserving lane/shared ownership;
7. launch the next bounded GLM candidate/repair task when useful and authorized;
8. continue across other ready lanes while there is immediate safe work;
9. exit when the remaining next actions are only waits for GLM, CI, independent review, provider/external availability, or a future scheduler wake-up.

The coordinator must **not sleep or poll** merely to consume runtime. When insufficient wall-clock budget remains for a complete safe mutation plus verification, record the exact next action and exit cleanly.

A `PR Attention Evidence` artifact is advisory and exact-head-bound. It may eliminate repeated mechanical collection, but it may not establish semantic PASS, queue/readiness state, review/approval authority, or merge permission. If the artifact predates terminal required gates, the writer may refresh/recollect gate state once when terminal rather than repeatedly polling it.

## 5. Canonical post-112 lanes

Inside each lane, work remains sequential and normal dependency/readiness rules apply. While section 1A is active, its temporary hardening-first hold overrides the scheduling order in this section without changing the underlying lane definitions.

### Knowledge

`113 MODEL-DOSSIER-1 -> 114 LITERATURE-KNOWLEDGE-1 -> 115 PROJECT-SEARCH-1`

After those foundations, `121 JARVIS-PROJECT-KNOWLEDGE-ACTIONS-1` may proceed only when its own dependencies/readiness are satisfied.

### Development

`116 ROADMAP-CALENDAR-1 -> 117 BRAINSTORM-1`

After those foundations, `122 JARVIS-DEVELOPMENT-ACTIONS-1` may proceed only when its own dependencies/readiness are satisfied.

### Coding acceleration

`118 CODING-REPOSITORY-TRUTH-1 -> 119 CODING-RUNTIME-TRUTH-1 -> 120 DEVELOPMENT-PIPELINE-STATE-1 -> 123 JARVIS-CODING-ACTIONS-1 -> fresh Hermes V1 re-derivation/release gate`

`123` may proceed only when its hard dependencies are merged and its own spec/readiness authorizes implementation.

### Provider/settings owner

`124 PROVIDER-SETTINGS-GENERIC-1` is an independent provider/settings owner once its dependencies and readiness are satisfied. It may be scheduled post-112 without blocking unrelated Knowledge/Development/Coding work when section 1A is not holding those lanes.

### Separately gated later work

`125 SAFE-SELF-UPDATE-1` and `126 LOCAL-TERMINAL-PTY-1` remain separately gated and are not automatically parallelized.

`102 ENGINEERING-EVIDENCE-CONTRACT-1` remains later work. After it is eligible and merged, the engineering/Process sequence is explicitly `103 -> 104 -> 105 -> 106 -> 107 -> 108 -> 109 -> 093 -> 110`, subject to each row's then-current dependencies/readiness and fresh authority. This profile does not pull that sequence forward.

## 6. Hermes V1 re-derivation gate

Legacy 066–068 remain frozen and are not direct implementation authority. Spec 080 also remains frozen/planned unless explicitly re-derived later.

After 123 is actually merged, Hermes requires a **fresh derivation from then-current exact `master`** before implementation. The derivation must use accepted 111/118/119/120/123 contracts, the live AI execution/egress/budget spine, the pinned Hermes identity actually selected, and current evidence.

The first Hermes release must preserve JarvisOS ownership of:

- context and exact refs;
- policy and provider credentials;
- sensitivity and egress;
- budget and usage ledger;
- proposal/promotion authority;
- repository/database/service/domain authority.

Hermes remains an untrusted advisory orchestrator/runtime. It must not become a second authority process, receive provider credentials directly, bypass the JarvisOS model gateway, own unrestricted repository/database/data-root access, or invent page-specific parallel action stores.

Suggested code changes remain candidate proposals until accepted development authority validates/applies them. The temporary GLM harness remains rollback until Hermes parity is evidenced for the work it replaces.

Knowledge and Development do not wait for Hermes when their own lanes are independently ready and section 1A is no longer active.

## 7. Parallel status and merge coordination

After activation, multiple implementation PRs may be active only for demonstrated-disjoint lanes whose normal readiness/dependency authority is already valid.

The single ChatGPT Integration writer:

1. verifies each candidate PR against exact head;
2. serializes merges to `master` with `expected_head_sha`;
3. verifies the resulting fresh `master`;
4. reconciles `STATUS.md`;
5. requires remaining lanes to refresh `master`, ancestry/conflicts, and affected evidence before their own merge.

A merge in one lane never makes another lane's old evidence current automatically. `STATUS.md` remains the one registry; no per-lane shadow status file is allowed.

## 8. Low-risk planning compression

A single planning PR may combine definition, full specification, and readiness only when all are true:

- slice is additive/reversible;
- no new security/credential/provider/egress authority;
- no new durable store or delicate migration sequence;
- no destructive behavior or hard-to-reverse external effect;
- no cross-domain ownership boundary is invented/reassigned;
- exact-master inventory, scope, acceptance criteria, non-goals, failure modes, test plan, and readiness decision remain independently inspectable.

High-risk security/credentials/egress, Hermes isolation/model-call closure, PTY, self-update, delicate migrations, Process/solver/evaluator authority, destructive actions, and hard-to-reverse ownership retain the full lifecycle.

`planned` never becomes implementation authority through compression.

### 8A. Atomic readiness registry transition

A separate `planned -> ready` reconciliation PR is **not required by ceremony** after an accepted readiness decision. A post-112 readiness PR may atomically include both the readiness artifact and that same spec's sole `STATUS.md` transition from `planned` or `blocked` to `ready` when all are true:

- the readiness evidence and decision are explicitly inspectable in that PR;
- the changed registry row is the same spec and contains no implementation PR association;
- the deterministic spec-status definition gate accepts the resulting registry;
- no unrelated registry, dependency, queue, product, schema, provider, or authority change is bundled;
- the readiness decision itself satisfies the active spec and canonical dependency/ownership rules.

Until that PR merges, remote `STATUS.md` remains non-ready and implementation remains forbidden. After it merges, the readiness decision and registry authority become current atomically, eliminating a redundant follow-up PR without weakening the lifecycle.

This compression does **not** apply to the later `in_review -> merged` transition, which necessarily depends on a verified exact implementation merge and therefore remains a post-merge mechanical reconciliation unless a future canonical mechanism makes that transition atomic without predeclaring success.

## 9. Two-speed deterministic gating and browser proof

While a PR head moves, use focused deterministic tests and minimum relevant gates. On the frozen candidate merge head, run every gate/proof required by repository policy, the active spec, and affected boundaries. Any later head mutation invalidates affected head-specific evidence.

For a pull request whose deterministic changed-path classifier proves that **every changed repository path is under `docs/`**, CI may use a governance-only terminal fast path and skip dependency installation, architecture/runtime/import gates, backend lint/tests, frontend build, and BLUECAD runtime canaries. The fast path must still run the deterministic registry/spec gate and repository-development governance/anti-authority self-tests that require only the standard-library environment. It fails closed to normal CI for an empty/unknown diff, classifier failure, any changed path outside `docs/`, or any non-PR event.

Pushes to `master` always run full CI, including after a docs-only merge. The PR fast path therefore removes redundant pre-merge runtime work without eliminating the repository-wide regression pass on the resulting master commit.

This docs-only fast path is evidence economy, not a correctness waiver: no executable, workflow, configuration, schema, fixture, or product/runtime file changed on the pull request, while the executable tree is identical to the already validated base. Any non-`docs/` change receives normal required terminal gates.

Browser/screenshot proof is required for visible frontend/layout/interaction deltas or explicit spec requirements. It is not required by ceremony for docs-only/backend-only/schema-only changes with no visible delta.

## 10. Read-only prework

Read-only ownership, dependency, source, threat-model, upstream bakeoff, or future-slice research may happen ahead of implementation when it creates no premature authority and is revalidated against fresh exact `master` before promotion.

Prework may not mutate product/runtime authority, start a `planned` implementation, or be treated as indefinitely fresh evidence.

## 11. Reconciliation economy

Avoid PRs, comments, checkpoint artifacts, screenshot passes, or repeated gates that add no authority, evidence, or risk reduction.

Prefer the atomic readiness transition in section 8A whenever its fail-closed conditions hold. Do not create a second PR merely to copy an already accepted readiness decision into `STATUS.md`.

Post-merge registry reconciliation may be applied mechanically when merge SHA is exact and verified, the transition is deterministic, no new product direction is invented, and `STATUS.md` remains the sole live work-state authority. A docs-only reconciliation should use the section 9 PR governance fast path rather than rerunning unrelated runtime suites before merge; the resulting master push still receives full CI.

Do not remove a gate/review/audit that closes a real security, scientific, migration, authority, regression, or acceptance risk merely to reduce elapsed time.

## 12. Conflict fallback

A conflict involving a shared owner, schema/migration sequencing, security/egress authority, cross-lane invariant, or overlapping runtime boundary returns **only the affected slices** to serial execution until resolved.

Independent lanes remain eligible if their own dependencies, readiness, and ownership audits remain green and section 1A is not holding them.

If safe resolution requires one of the four maintainer interruption classes, stop and contact the maintainer. Otherwise ChatGPT chooses the least-cost reversible route within accepted authority.

## 13. Safety invariants preserved

This profile never authorizes:

- implementation of a `planned` row;
- skipping a hard dependency;
- two ChatGPT writers on one PR/head or shared authority;
- stale-head merge evidence;
- GLM/Claude/Codex to become GitHub, queue, architecture, domain COMMIT/EXECUTE, provider, credential, or promotion authority by inference;
- frontend direct provider/filesystem/shell/GitHub authority;
- bypass of egress, budget, credential, secret, or promotion boundaries;
- direct provider credentials in Hermes;
- direct implementation of stale 066–068 kernels without fresh re-derivation;
- automatic activation before 112 is merged.

When this profile conflicts with a narrower accepted specification or a hard invariant in `AGENTS.md`, the narrower/higher authority wins.