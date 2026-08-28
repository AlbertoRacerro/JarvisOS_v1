# Post-112 controlled parallel delivery profile

Status: canonical operational profile, dormant until activation gate
Authorized: 2026-08-28
Maintainer acceleration amendment: 2026-08-28

This document defines the minimum controlled-parallel delivery exception to the repository's normal single-front execution rule. It changes repository-development process only. It does not change JarvisOS runtime authority, provider policy, product architecture, credentials, egress, schemas, or model-promotion rules.

`docs/specs/STATUS.md` remains the sole live source of truth for work state, dependencies, queue order, and implementation-PR association. This file is not a second roadmap. Where this profile records a maintainer-approved future ordering target, that target becomes executable only after the Integration Coordinator has reconciled the matching queue order into `STATUS.md` through the normal docs-only authority path.

## 1. Activation gate

The profile is **dormant** until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` with registry status `merged`.

Before that condition is true:

- specs 111 and 112 remain under the existing one-active-front / one-writer regime;
- no parallel runtime implementation lane is authorized by this document;
- no agent may treat this document as permission to skip a dependency, start a `planned` spec, or open a second implementation front.

At the first coordinating cycle after 112 is merged, the coordinator re-reads exact `master`, `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, the candidate specs/readiness records, and current code ownership. Activation is automatic and requires no maintainer checkpoint **only for lanes whose file, store, schema, migration, and authority boundaries are demonstrated to be sufficiently disjoint**.

If disjointness cannot be proved, only the conflicting slices remain serial. Independent lanes may still proceed. A maintainer interruption is required only for the four canonical interruption classes in `AGENTS.md`.

## 2. Maximum operating topology and scheduled work-stealing

The logical post-112 topology supports at most four ChatGPT coordination roles:

1. **Integration Coordinator** — sole owner of cross-lane integration, shared-file mutation, merge sequencing, registry reconciliation, and conflict resolution.
2. **Knowledge Builder** — Project Knowledge lane.
3. **Development Builder** — Development lane.
4. **Coding Builder** — Coding lane.

These are logical responsibilities, not permanent automation identities. A scheduled ChatGPT automation does not own one lane merely because of its name or wake-up minute.

The maintainer authorizes a stricter scheduled deployment with up to four staggered ChatGPT orchestrator automations, normally at `:00`, `:15`, `:30`, and `:45`. In this mode:

- the four automations are interchangeable scheduler replicas;
- **only one ChatGPT orchestrator may hold the coordinator/writer lock at a time**;
- on wake-up, the lock holder temporarily assumes the Integration Coordinator role and may service any currently authorized lane;
- the other scheduled instances exit without mutation when a fresh coordinator lock is already held;
- GLM or other bounded read-only/proposal subworkers may continue concurrently because they do not own GitHub merge/shared-state authority.

A work-stealing cycle must:

1. resolve fresh exact `master`, `STATUS.md`, active PR heads, terminal CI/review evidence, and currently running/finished subworkers;
2. consume already-terminal safe evidence first, including stale-result rejection;
3. advance any immediately actionable lane one bounded step at a time, acquiring the relevant lane/shared ownership before mutation;
4. launch the next bounded GLM subworker when useful, normally no more than one active worker per lane unless a fresh disjointness proof justifies more;
5. repeat across other ready lanes while useful work is immediately available;
6. exit as soon as the remaining next actions are only waits for GLM, CI, review, external availability, or a future scheduled wake-up.

The orchestrator must **not** sleep, poll, or remain alive merely to consume its available runtime. It must not continue until timeout by default. When the remaining wall-clock budget is too small for a complete safe mutation plus verification, it records the exact next action and exits cleanly.

This work-stealing mode intentionally concentrates GitHub write/merge authority in one ChatGPT process while allowing cheap subworkers to perform parallel bounded analysis/candidate work. It is therefore stricter than the maximum logical role topology and does not weaken any shared-file or exact-head rule.

No two writers may mutate the same PR/head concurrently.

## 3. Authorized post-112 lanes and Hermes acceleration target

Inside each lane, work remains sequential and normal dependency/readiness rules still apply.

### Knowledge

`113 MODEL-DOSSIER-1 -> 114 LITERATURE-KNOWLEDGE-1 -> 115 PROJECT-SEARCH-1`

### Development

`116 ROADMAP-CALENDAR-1 -> 117 BRAINSTORM-1`

### Coding — pre-Hermes foundation

The maintainer-approved acceleration target is:

`118 CODING-REPOSITORY-TRUTH-1 -> 119 CODING-RUNTIME-TRUTH-1 -> 120 DEVELOPMENT-PIPELINE-STATE-1 -> 123 JARVIS-CODING-ACTIONS-1`

`123` is intentionally pulled forward once its own hard dependencies (`111`, `118`, `119`, `120`) are merged. `124`, `121`, `122`, `125`, and `126` are not prerequisites for this early Coding foundation.

Because `STATUS.md` is the sole live queue authority, the changed position of `123` must be reconciled there through a docs-only queue amendment before an agent acts on this ordering. Until that reconciliation is merged, the current `STATUS.md` order wins.

### Hermes V1 acceleration gate

After `123` is actually merged and the queue has been reconciled accordingly, the next Coding objective is a **fresh Hermes V1 re-derivation/release gate**, before the remaining post-foundation slices.

This gate does **not** authorize direct implementation of the legacy 066–068 kernels. Instead it must re-derive the Hermes boundary from then-current exact `master`, the accepted 111/118/119/120/123 contracts, the live AI execution/egress/budget spine, the pinned Hermes identity actually chosen for production, and the evidence collected by temporary GLM/Hermes experiments.

The first useful Hermes release should be the minimum coding-capable dogfood profile that proves all of the following:

- JarvisOS remains policy, credential, sensitivity, budget, egress, ledger, context, and promotion authority;
- Hermes is an untrusted advisory orchestrator, never a second authority process;
- every Hermes model path reaches a JarvisOS-owned model gateway or is disabled; no provider API key is given directly to Hermes;
- Coding context/actions are obtained through JarvisOS-owned bounded capabilities rather than unrestricted direct repository/database/data-root authority;
- the generic 111 capability/action registry is reused rather than creating one bespoke Hermes adapter per screen;
- exact repository/runtime/pipeline truth comes from 118/119/120 owners;
- suggested code changes remain proposals/candidate patches until the accepted development authority validates and applies them;
- the temporary GitHub/OpenAI-Agents-SDK GLM harness is not retired until Hermes has parity evidence for the work it is replacing.

Knowledge and Development base lanes do not wait for Hermes and may continue in parallel while the Coding lane reaches this gate.

After Hermes V1 is proven, the remaining operator-domain slices continue under the then-current registry, with Hermes dogfooding used where appropriate. The intended post-Hermes remainder includes `124`, `121`, `122`, `125`, and `126`, subject to their own dependencies, readiness, security, and authority gates. No later slice becomes ready merely because Hermes exists.

This profile does **not** automatically parallelize 125, 126, 102, the late Process/Design sequence 103–110, or 093. Those slices retain their own dependency, security, scientific, evidence, and readiness gates.

## 4. Shared-file and authority ownership

During parallel delivery, the Integration Coordinator is the only normal writer for shared integration boundaries, including when applicable:

- `docs/specs/STATUS.md`;
- global routers and registries;
- migration/schema registries and shared migration sequencing;
- shared API clients or global frontend integration points;
- common Jarvis/AI infrastructure;
- root configuration and repository-wide workflow/control files;
- any other path or authority that a fresh ownership audit shows is shared by more than one active lane.

A domain lane that needs a shared mutation must stop at that boundary and provide a bounded integration request or candidate patch to the coordinator. It must not race another lane for the shared file.

A shared-file rule does not prohibit a domain spec from owning a shared-path change when its accepted specification explicitly requires it. It changes **who applies and sequences** that mutation while lanes are concurrent.

## 5. Parallel status and merge coordination

After activation, more than one implementation PR may be `in_progress` or `in_review` only when they belong to demonstrated-disjoint lanes and each spec has passed its normal authorization/readiness requirements.

The Integration Coordinator:

1. verifies each candidate PR against its exact head;
2. serializes merges to `master` with an expected-head guard;
3. verifies the resulting `master` commit;
4. reconciles `STATUS.md`;
5. requires every remaining lane to resolve fresh `master`, check ancestry/conflicts, and revalidate any evidence invalidated by the preceding merge before its own merge.

A successful merge in one lane never makes another lane's old exact-head evidence current automatically.

`STATUS.md` remains one registry and may represent multiple active lane rows after activation. No per-lane shadow status file is allowed.

## 6. Low-risk planning compression

To remove ceremonial latency, a single planning PR may combine definition, full specification, and readiness evidence when **all** of the following are true:

- the slice is additive or reversible;
- no new security or credential authority is introduced;
- no provider/egress authority is introduced or broadened;
- no new durable store or delicate migration sequence is required;
- no destructive behavior or hard-to-reverse external effect is introduced;
- no cross-domain ownership boundary is being invented or reassigned;
- exact-master inventory, scope, acceptance criteria, non-goals, failure modes, test plan, and a clear readiness decision remain independently inspectable in the combined artifact.

Compression is forbidden when it would reduce evidence or blur independently removable specifications.

High-risk work retains the full separate lifecycle. This includes, by default, security/credentials/egress, Hermes isolation/model-call closure, PTY, self-update, delicate schema migrations, Process/solver/evaluator authority, destructive actions, and hard-to-reverse cross-domain ownership.

`planned` never becomes implementation authority merely because planning is compressed.

## 7. Two-speed deterministic gating

While a PR head is still moving:

- run focused deterministic tests and the minimum relevant gates needed to guide the current change;
- do not repeatedly spend time on repository-wide gates that the current micro-change cannot affect unless the active specification or CI policy explicitly requires them.

On the frozen candidate merge head:

- run every deterministic gate and proof required by the specification, repository policy, and affected boundaries;
- run full repository CI when required by those authorities;
- treat every subsequent head mutation as invalidating head-specific evidence that may have been affected.

BLUECAD proof, browser/evidence matrices, and other expensive domain-specific gates are required only when the active spec or affected boundary requires them.

## 8. Browser-proof relevance

Browser or screenshot proof is required for a visible frontend/layout/interaction delta, or whenever the governing specification explicitly requires it.

A backend-only, schema-only, test-only, or documentation-only change with no visible delta does not require an eleven-surface screenshot pass merely as ceremony. Existing deterministic frontend gates still apply when required by the touched boundary.

## 9. Work allocation and model economy

The coordinating ChatGPT session is the default reasoning and orchestration layer and should directly perform work that does not require a specialist execution environment. This includes repository reading, planning, documentation, CI/review consumption, finding consolidation, bounded mechanical GitHub writes, exact-head verification, and small safe corrections.

External model use is evidence-driven:

- **GLM subworkers are the normal cheap implementation-analysis workhorse** while the temporary harness is active. They receive an exact target ref/SHA and a narrow task, and return advisory evidence/candidate patches only. Normally keep at most one active GLM worker per Knowledge, Development, and Coding lane; use additional same-lane fan-out only when the tasks are demonstrably disjoint and the expected value exceeds coordination cost.
- **Claude is the default independent reviewer/specialist** for material exact-head review, architecture, UX, API/schema-boundary, testing-strategy, and security critique when needed.
- **Codex is a critical reserve**, not a routine reviewer. Do not use it for ordinary planning, documentation-only work, reconciliation, UI polish, small PRs, or a duplicate second review "for safety". Use Codex review only when Claude is genuinely unavailable/inadequate, an unresolved high-risk technical finding justifies a specialist second opinion, or the diff has a material Codex-specific advantage. Codex implementation remains available when its coding environment provides a concrete advantage over direct work.
- Do not ask Claude and Codex the same generic question or duplicate reviews on one immutable head.
- No artificial numeric iteration cap replaces engineering judgment; continue useful review/correction iterations while they materially reduce risk.
- A green GLM/Hermes/other worker workflow is never, by itself, merge authority.

Mutable PRs should remain draft when doing so prevents automatic Codex review. Freeze the head and consume the minimum required independent review before changing draft state when a non-draft state is actually needed.

## 10. Temporary-harness to Hermes transition

Until Hermes V1 passes its fresh compatibility, authority, isolation, and parity gates, the temporary GitHub Actions/OpenAI Agents SDK GLM harness remains an implementation accelerator rather than product runtime architecture.

The transition is evidence-based, not date-based:

1. prove the first Hermes profile on the accepted Coding owner surfaces;
2. compare exact task completion, candidate-patch quality, failure handling, model-call closure, cost/usage visibility, and stale-head behavior against the temporary harness;
3. dogfood Hermes on bounded real queue work while retaining the temporary harness as rollback;
4. retire or reduce the temporary harness only after the replacement path is observably sufficient.

Do not preserve duplicate orchestration infrastructure indefinitely merely because it once worked. Conversely, do not remove the rollback path before parity is proven.

## 11. Future read-only prework

Read-only analysis may be performed ahead of the active implementation frontier when it reduces later idle time without creating premature authority. Examples include:

- ownership and dependency inventories for later domain lanes;
- read-only research for 103 upstream Process bakeoff;
- threat-model and boundary inventory for 125 self-update and 126 PTY;
- solver/adapter source audits for later Process/engineering work;
- pinned-Hermes compatibility and effective-config inventory that does not mutate product/runtime authority.

Prework may not mutate product/runtime authority, open an unauthorized implementation front, or be treated as fresh implementation evidence indefinitely. It must be revalidated against fresh exact `master` when promoted into an accepted slice.

## 12. Reconciliation and ceremony reduction

Avoid PRs, checkpoint comments, review requests, screenshot passes, or repeated gates that add no new authority, evidence, or risk reduction.

Post-merge registry reconciliation may be automated or mechanically applied when:

- the merge SHA is exact and verified;
- the transition is deterministic;
- no new product direction or next-slice authority is being invented;
- the operation preserves `STATUS.md` as the single live work-state authority.

Do not remove an audit, review, or gate that closes a real security, scientific, migration, authority, regression, or acceptance risk merely to reduce elapsed time.

## 13. Conflict fallback

A conflict involving a shared owner, migration/schema sequencing, security/egress authority, cross-lane invariant, or overlapping runtime boundary returns **only the affected slices** to serial execution until the conflict is resolved.

Independent lanes remain eligible to continue if their own hard dependencies, readiness, and ownership audits remain green.

If the only safe resolution would require one of the four maintainer interruption classes, stop and contact the maintainer. Otherwise the Integration Coordinator chooses the least-cost reversible route and proceeds.

## 14. Safety invariants preserved

This profile never authorizes:

- implementation of a `planned` row;
- skipping a hard dependency;
- two writers on one PR/head;
- concurrent mutation of one shared authority;
- stale-head merge evidence;
- a model or worker to become domain COMMIT/EXECUTE authority by inference;
- frontend direct provider/filesystem/shell/GitHub authority;
- bypass of existing egress, budget, credential, secret, or promotion boundaries;
- direct provider credentials in Hermes;
- direct implementation of stale 066–068 kernels without fresh re-derivation;
- automatic activation before 112 is merged.

When this profile conflicts with a narrower accepted specification or a hard invariant in `AGENTS.md`, the narrower/higher authority wins.
