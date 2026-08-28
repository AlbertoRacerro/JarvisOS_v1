# Post-112 controlled parallel delivery profile

Status: canonical operational profile, dormant until activation gate
Authorized: 2026-08-28

This document defines the minimum controlled-parallel delivery exception to the repository's normal single-front execution rule. It changes repository-development process only. It does not change JarvisOS runtime authority, provider policy, product architecture, specification scope, queue order, credentials, egress, schemas, or model-promotion rules.

`docs/specs/STATUS.md` remains the sole live source of truth for work state, dependencies, queue order, and implementation-PR association. This file is not a second roadmap.

## 1. Activation gate

The profile is **dormant** until fresh exact `master` shows `112 PROJECT-KNOWLEDGE-CORE-1` with registry status `merged`.

Before that condition is true:

- specs 111 and 112 remain under the existing one-active-front / one-writer regime;
- no parallel runtime implementation lane is authorized by this document;
- no agent may treat this document as permission to skip a dependency, start a `planned` spec, or open a second implementation front.

At the first coordinating cycle after 112 is merged, the coordinator re-reads exact `master`, `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, the candidate specs/readiness records, and current code ownership. Activation is automatic and requires no maintainer checkpoint **only for lanes whose file, store, schema, migration, and authority boundaries are demonstrated to be sufficiently disjoint**.

If disjointness cannot be proved, only the conflicting slices remain serial. Independent lanes may still proceed. A maintainer interruption is required only for the four canonical interruption classes in `AGENTS.md`.

## 2. Maximum operating topology

The post-112 profile supports at most four ChatGPT coordination roles:

1. **Integration Coordinator** — sole owner of cross-lane integration, shared-file mutation, merge sequencing, registry reconciliation, and conflict resolution.
2. **Knowledge Builder** — Project Knowledge lane.
3. **Development Builder** — Development lane.
4. **Coding Builder** — Coding lane.

The profile defines roles, not guaranteed automation capacity. It must not disable or repurpose unrelated maintainer automations automatically. If only two JarvisOS builder slots are available, operate as coordinator + one lane and add lanes only after the maintainer explicitly makes additional slots available.

No two writers may mutate the same PR/head concurrently.

## 3. Authorized post-112 lanes

Inside each lane, work remains sequential and normal dependency/readiness rules still apply.

### Knowledge

`113 MODEL-DOSSIER-1 -> 114 LITERATURE-KNOWLEDGE-1 -> 115 PROJECT-SEARCH-1`

### Development

`116 ROADMAP-CALENDAR-1 -> 117 BRAINSTORM-1`

### Coding

`118 CODING-REPOSITORY-TRUTH-1 -> 119 CODING-RUNTIME-TRUTH-1 -> 120 DEVELOPMENT-PIPELINE-STATE-1 -> 124 PROVIDER-SETTINGS-GENERIC-1`

After the underlying domain owners are merged and the 111 common contract remains compatible, these domain-specific Jarvis adapter slices may also run as three independent lanes:

- Knowledge: `121 JARVIS-PROJECT-KNOWLEDGE-ACTIONS-1`
- Development: `122 JARVIS-DEVELOPMENT-ACTIONS-1`
- Coding: `123 JARVIS-CODING-ACTIONS-1`

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

High-risk work retains the full separate lifecycle. This includes, by default, security/credentials/egress, PTY, self-update, delicate schema migrations, Process/solver/evaluator authority, destructive actions, and hard-to-reverse cross-domain ownership.

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

- **Claude is the default independent reviewer/specialist** for material exact-head review, architecture, UX, API/schema-boundary, testing-strategy, and security critique when needed.
- **Codex is a critical reserve**, not a routine reviewer. Do not use it for ordinary planning, documentation-only work, reconciliation, UI polish, small PRs, or a duplicate second review "for safety". Use Codex review only when Claude is genuinely unavailable/inadequate, an unresolved high-risk technical finding justifies a specialist second opinion, or the diff has a material Codex-specific advantage. Codex implementation remains available when its coding environment provides a concrete advantage over direct work.
- Do not ask Claude and Codex the same generic question or duplicate reviews on one immutable head.
- No artificial numeric iteration cap replaces engineering judgment; continue useful review/correction iterations while they materially reduce risk.
- Cheap/free workers such as an isolated Hermes+GLM experiment may perform read-only preflight, impact analysis, candidate review, or other bounded work. Their output remains untrusted advisory evidence. A green worker workflow is never, by itself, merge authority.

Mutable PRs should remain draft when doing so prevents automatic Codex review. Freeze the head and consume the minimum required independent review before changing draft state when a non-draft state is actually needed.

## 10. Future read-only prework

Read-only analysis may be performed ahead of the active implementation frontier when it reduces later idle time without creating premature authority. Examples include:

- ownership and dependency inventories for later domain lanes;
- read-only research for 103 upstream Process bakeoff;
- threat-model and boundary inventory for 125 self-update and 126 PTY;
- solver/adapter source audits for later Process/engineering work.

Prework may not mutate product/runtime authority, open an unauthorized implementation front, or be treated as fresh implementation evidence indefinitely. It must be revalidated against fresh exact `master` when promoted into an accepted slice.

## 11. Reconciliation and ceremony reduction

Avoid PRs, checkpoint comments, review requests, screenshot passes, or repeated gates that add no new authority, evidence, or risk reduction.

Post-merge registry reconciliation may be automated or mechanically applied when:

- the merge SHA is exact and verified;
- the transition is deterministic;
- no new product direction or next-slice authority is being invented;
- the operation preserves `STATUS.md` as the single live work-state authority.

Do not remove an audit, review, or gate that closes a real security, scientific, migration, authority, regression, or acceptance risk merely to reduce elapsed time.

## 12. Conflict fallback

A conflict involving a shared owner, migration/schema sequencing, security/egress authority, cross-lane invariant, or overlapping runtime boundary returns **only the affected slices** to serial execution until the conflict is resolved.

Independent lanes remain eligible to continue if their own hard dependencies, readiness, and ownership audits remain green.

If the only safe resolution would require one of the four maintainer interruption classes, stop and contact the maintainer. Otherwise the Integration Coordinator chooses the least-cost reversible route and proceeds.

## 13. Safety invariants preserved

This profile never authorizes:

- implementation of a `planned` row;
- skipping a hard dependency;
- two writers on one PR/head;
- concurrent mutation of one shared authority;
- stale-head merge evidence;
- a model or worker to become domain COMMIT/EXECUTE authority by inference;
- frontend direct provider/filesystem/shell/GitHub authority;
- bypass of existing egress, budget, credential, secret, or promotion boundaries;
- automatic activation before 112 is merged.

When this profile conflicts with a narrower accepted specification or a hard invariant in `AGENTS.md`, the narrower/higher authority wins.
