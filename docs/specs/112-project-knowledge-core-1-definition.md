# 112 PROJECT-KNOWLEDGE-CORE-1 — definition

Exact source master: `870bb3f038e5d46af485435e20dafbf7d6c7baa4`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `112` registry row from `planned`.

Governing planning and merged runtime authority:
- `docs/specs/100c-queue-rederivation-2026-08-28.md` and the associated 100c overlap/capability ownership audits;
- merged 001 engineering-record schema foundation;
- merged 035 Engineering Data read-first navigator;
- merged 040 MemoryStore proposal/promotion boundary;
- merged 042 deterministic context-pack selection/preview;
- merged 050 derived dependency/provenance graph and canonical `<kind>:<id>` resolver;
- merged 051 deterministic freshness invalidation and replacement lineage;
- merged 071b single transient working-configuration owner and preflight semantics;
- merged 098 Parameter-first canonical lifecycle/CAS mutation authority;
- merged 111 common Jarvis exact-context/action foundation.

## Problem

The final Project Knowledge surface needs one truthful way to edit the project basis and reason about the consequences of a coordinated engineering change without creating another project/model database. Today the repository already has several deliberately separate owners:

- canonical engineering records and proposal/promotion behavior;
- Parameter lifecycle/CAS mutation;
- dependency/provenance and stale overlays;
- a transient run-oriented working configuration;
- read-first Engineering Data navigation;
- explicit Jarvis context/proposal contracts.

Those owners solve narrower problems, but none currently owns a multi-record Project Basis working revision that can stage a coherent change set, inspect deterministic impact, and reconcile accepted mutations atomically while preserving immutable parent/history identity.

112 therefore owns the **coordination layer over existing canonical engineering-record owners**, not a replacement for them. Its job is to make a Project Basis revision/change set a bounded server-owned transaction intent whose accepted operations are delegated to existing record/lifecycle authority and whose impact/revalidation evidence is derived from existing dependency/freshness truth.

## Current-owner audit and overlap disposition

### 001 / canonical engineering records

Existing engineering records remain the canonical data. 112 MUST NOT introduce peer `project_parameters`, `project_requirements`, `project_assumptions`, `project_decisions`, or a generic duplicate record table. A Project Basis revision references exact canonical owner identities and proposed operations against them.

### 040 / MemoryStore

040 remains the proposal/promotion boundary for AI- and calculation-originated engineering-record proposals. Model/Jarvis output cannot use 112 to bypass proposal status or silently become canonical state. Where a change-set item originates from AI, 112 must preserve the existing proposal identity/provenance and require the same explicit/deterministic promotion boundary before canonical mutation.

### 042 / context packs

042 remains deterministic read/context selection authority. A Project Basis working revision is not an alternate context store or retrieval index. 112 may expose exact revision/change-set refs for later 121 CONTEXT actions, but context materialization remains through accepted owner/context contracts.

### 050 / dependency graph

050 remains the read-derived dependency/provenance graph and canonical ref resolver. 112 MUST derive impact from this owner (or a narrowly factored equivalent current seam), not persist a second dependency graph/cache. Incomplete/bounded lineage must fail closed rather than claim complete impact.

### 051 / freshness invalidation

051 remains deterministic downstream stale/invalidation authority for canonical replacement lineage. 112 may coordinate when stale/revalidation evidence is produced or reconciled, but must not silently clear stale state, rewrite historical run status, or invent a second freshness system.

### 071b / transient working configuration

071b is the sole transient run-oriented working configuration and preflight owner. It is deliberately separate from canonical project records. 112 MUST NOT merge these concepts: changing a Project Basis working revision does not silently mutate the current 071b working configuration, and editing/running a 071b configuration does not silently commit Project Basis. Any future explicit handoff must preserve exact revision identity and remain separately authorized.

### 098 / Parameter lifecycle and canonical CAS

098 remains the current Parameter edit/lifecycle authority, including exact workspace/current-state/`updated_at` checks, `BEGIN IMMEDIATE` mutation, audit evidence, replacement semantics, lifecycle-current filtering and dependent protection. 112 must reuse those semantics for Parameter operations rather than adding a peer Parameter writer. Where 112 needs multi-record atomicity, the full spec must identify the smallest transaction-capable internal service seam that can compose accepted owner operations without weakening their validation.

### 035 / Engineering Data

035 remains read-first navigation and 098 already activates bounded server-backed Parameter edit/lifecycle controls there. 112 may activate the truthful Project Basis controls reserved by 100f/100g, but must not create a second generic Engineering Data navigator or redesign the canonical surfaces.

### 111 / Jarvis

111 provides exact, inspectable, stale-safe CONTEXT/PROPOSE contracts only. 112 owns domain COMMIT for Project Knowledge; Jarvis does not. Later 121 may propose Project Knowledge operations against exact 112 refs, but acceptance/reconciliation stays 112/domain-owned.

## Definition boundary

112 owns one server-side **Project Basis change-set / working-revision coordination contract** over existing canonical records.

It MUST define:

1. **Exact immutable parent identity** — every working revision starts from one exact server-resolved Project Basis parent snapshot/revision identity. Unknown or incomplete identity fails closed; the browser cannot declare the canonical parent.
2. **Bounded change set** — a working revision contains an ordered, typed set of intended record operations against exact owner/type/id/current-revision tokens. The change set stores intent and evidence references, not duplicate canonical engineering values as a peer truth store.
3. **Optimistic stale/CAS protection** — each operation carries the exact owner revision token available from that owner (`updated_at`, lifecycle state, replacement/source revision, or later equivalent). Parent or target drift invalidates acceptance until explicitly rebased/reviewed.
4. **Proposal vs operator mutation distinction** — origin and authority are explicit. AI/Jarvis/calculation proposals remain proposals; operator-authored direct changes may use only domain operations already authorized for that record kind. 112 cannot promote unsupported kinds merely because they appear in a change set.
5. **Deterministic impact preview** — before commit, derive bounded downstream impact/revalidation requirements from current canonical refs plus 050/051 truth. The preview records exact source/target refs, completeness/bounds and current revision identity; it cannot claim freshness when lineage is incomplete.
6. **Explicit validation/revalidation state** — classify each intended operation and impacted dependency as current/needs-review/needs-revalidation/unavailable using deterministic owner evidence. Do not perform hidden solver/model/provider work and do not equate “stale” with “recomputed”.
7. **Atomic reconciliation** — accepting a working revision must either apply the entire supported canonical mutation set plus required audit/freshness/replacement evidence atomically, or apply none. Partial canonical Project Basis commits are forbidden.
8. **Immutable revision/history evidence** — accepted, rejected, superseded/rebased and failed reconciliation attempts retain inspectable parent/change-set/outcome identity. History is audit evidence, not a mutable alternate canonical record store.
9. **Idempotent retry / response-loss safety** — one accepted reconciliation intent must have one server-owned request/revision identity. Replaying the same exact accepted intent returns the existing outcome; a conflicting payload under the same identity fails closed.
10. **Bounded activation on Project Basis** — expose only controls backed by real 112 authority and current owner capabilities. Unsupported record-kind mutation remains visibly unavailable/read-only rather than simulated in frontend state.

## Working-revision state model to freeze in the full spec

The full spec must derive the smallest state model necessary from current code, but it must preserve these semantic distinctions:

- **parent revision**: immutable exact basis from which the working revision was derived;
- **draft intent**: mutable server-owned change-set intent that has no canonical effect;
- **impact preview**: deterministic evidence bound to the exact draft/parent/owner revisions;
- **accepted reconciliation intent**: immutable commit request after operator acceptance;
- **terminal outcome**: applied atomically, rejected/conflicted, or failed without partial canonical effect;
- **successor/rebase relationship**: a new working revision may supersede an obsolete draft but never rewrites the old parent/history evidence.

Names/storage representation are not authorized by this definition. The full spec must prove whether persistence is minimum-necessary and, if so, use the smallest additive schema instead of creating a generalized Project store.

## Atomicity and owner-composition requirements

The hardest 112 failure mode is cross-owner partial success. The future full spec/readiness therefore MUST prove an implementation route that:

- resolves all exact target rows and authority checks before canonical mutation;
- validates workspace, lifecycle/current state, owner revision/CAS tokens and proposal eligibility on the same transaction snapshot used for commit;
- opens one SQLite write transaction at the composition boundary when all affected canonical owners share the existing database;
- invokes/refactors existing owner validation/mutation primitives so their invariants are preserved inside that transaction rather than calling HTTP endpoints sequentially;
- persists required audit/replacement/freshness evidence within the same atomic outcome;
- rolls back every canonical mutation and reconciliation outcome if any supported operation fails;
- never performs provider, solver, filesystem or network side effects inside the canonical database transaction;
- explicitly rejects a change set containing record kinds whose current owner cannot participate safely in the atomic contract.

If fresh exact-master audit shows atomic composition cannot be achieved without weakening an existing owner, readiness MUST block or narrow V0 rather than authorize best-effort multi-step commits.

## Revalidation semantics

112 owns **coordination of revalidation requirements**, not a generic recompute engine.

- Impact is derived from exact current 050 graph/provenance evidence and 051 stale overlays.
- Existing results/runs remain historical evidence; 112 does not rewrite them to look current.
- A commit may mark/retain affected outputs stale through existing authority, but cannot clear stale solely because the operator accepted the basis change.
- Actual recomputation remains with the relevant runner/evaluator/domain owner and must be an explicit later action.
- Revalidation completion must be evidenced by exact new owner/run/result identity; no timestamp-only or frontend-only “validated” flag.
- Incomplete graph traversal, missing owner identity, unsupported relation, bound exhaustion or stale preview invalidates the commit preview or yields explicit incomplete impact according to the full-spec contract; it never becomes silent “no impact”.

## Concurrency and stale behavior

The full spec/readiness must cover at least:

- two working revisions from the same parent;
- canonical target mutation after preview but before acceptance;
- target lifecycle change/deletion/supersession during editing;
- replacement lineage changing while a revision is open;
- proposal promoted/rejected independently after it was referenced;
- same reconciliation request retried after response loss;
- competing acceptance of two revisions touching the same canonical target;
- workspace switch / stale frontend response;
- bounded impact graph becoming incomplete or changing between preview and commit.

All cases must fail closed or return the already-committed idempotent outcome; none may partially apply a new Project Basis.

## Required invariants

- No second project/model/engineering-record store.
- No duplicate dependency graph, freshness engine, proposal store or transient working-configuration owner.
- No direct canonical mutation from model/Jarvis output.
- No frontend-owned canonical Project Basis revision or fake optimistic commit.
- No silent merge/rebase when exact parent/target revision changed.
- No partial multi-record commit.
- No automatic solver/provider/model execution as part of reconciliation.
- No automatic clearing of stale/revalidation state.
- No fabricated impact, readiness, freshness, provenance, unit compatibility or successful reconciliation evidence.
- Existing unit normalization, lifecycle/replacement, dependency/provenance, event/audit and workspace isolation rules remain authoritative.
- `route_class="auto"` never becomes an external-provider path; Product AI remains behind the current AI execution/policy/ledger spine.

## V0 scope narrowing

112 is not required to make every engineering-record kind mutable immediately. Current exact-master evidence shows 098 has strong canonical Parameter edit/lifecycle/CAS authority while other kinds may remain read-only or have different promotion owners. The full spec should therefore prefer a **Parameter-first atomic Project Basis V0**, plus exact read/reference/impact treatment for other canonical kinds, unless fresh owner audit proves another kind can participate without adding a second mutation engine.

This narrowing is intentional: Project Basis coordination is only truthful where the underlying domain owner already supports the required mutation semantics.

## Frontend obligation

User-facing work, if required by the full spec, is limited to activating existing canonical Project Basis composition:

- show exact parent/working revision identity;
- stage supported changes through server-owned draft intent;
- show proposal/operator origin and unsupported read-only kinds truthfully;
- preview deterministic impact/revalidation evidence before acceptance;
- present stale/conflict/incomplete-impact failures explicitly;
- require explicit operator acceptance for reconciliation;
- after commit, reload canonical server truth rather than trusting optimistic local state.

No global visual redesign, alternate Project page, client-side canonical store, hidden context addition or invented model dossier/literature/search behavior is authorized.

## Full-spec exact-master audit obligations

Before 112 can become `ready`, the full-spec pass must inspect then-current code and name the exact seams for:

- canonical record reads and Parameter mutation/lifecycle transaction logic;
- MemoryStore proposal promotion/rejection and replacement promotion;
- dependency graph construction/canonical ref resolution;
- freshness invalidation persistence and stale reads;
- event/audit persistence;
- current unit normalization and linked-source revision checks;
- existing 071b working configuration and the explicit non-overlap boundary;
- current Project Basis/Engineering Data frontend composition and API client seams;
- 111 exact context/action contracts for future 121 integration.

For each proposed new persistent structure, endpoint or service, the full spec must state why an existing owner cannot satisfy the requirement and why the additive seam is minimum-necessary.

## Acceptance criteria for future full spec/readiness

Before implementation authority exists, exact-master full spec/readiness must prove:

1. one canonical owner for every mutable engineering field and no second Project/record truth store;
2. exact parent and target revision/CAS semantics with stale rejection;
3. bounded server-owned change-set identity separated from canonical records and 071b transient run configuration;
4. proposal-origin changes cannot bypass 040/record-owner promotion authority;
5. deterministic impact uses 050/051 authority and represents incomplete bounds explicitly;
6. one all-or-nothing transaction route for every V0-supported canonical mutation, audit and freshness effect;
7. idempotent response-loss retry and competing-revision protection;
8. no provider/solver/network/filesystem side effect inside reconciliation and no automatic recompute/unstale behavior;
9. immutable parent/history/outcome evidence survives rebase, conflict and failure;
10. deterministic tests cover dirty/stale targets, lifecycle drift, concurrent revisions, proposal drift, incomplete impact, mid-transaction failure rollback, idempotent replay and cross-workspace isolation;
11. existing unit/provenance/replacement semantics remain intact under coordinated change;
12. visible work, if any, preserves 100f/100g composition and receives exact-head browser proof for normal, stale/conflict, incomplete-impact, unsupported-kind and successful-reload states;
13. every non-112 Project Knowledge control is explicitly deferred to 113–115/121 or another canonical owner.

## Non-goals

- A second canonical project/model/engineering-record database.
- General mutable CRUD for record kinds whose current owner is read-only or lacks safe atomic semantics.
- Model dossier aggregation (`113`).
- Literature/source knowledge ingestion (`114`).
- Cross-project search (`115`).
- Jarvis Project Knowledge domain actions (`121`).
- Roadmap/Calendar/Brainstorm (`116/117/122`).
- Repository/runtime/development pipeline truth (`118–120/123`).
- Provider/settings expansion (`124`).
- Self-update or PTY (`125/126`).
- Semantic/vector retrieval.
- Process solver/topology/CAD reimplementation.
- Hermes runtime or reopening 066–068/080.

## Minimum-necessary test

Criterion: provide one atomic, stale-safe, auditable Project Basis change/revision coordination boundary over existing canonical engineering-record owners so operators can change the project basis without duplicate truth or partial reconciliation.

The need is not satisfied by 098 alone because 098 deliberately owns single-Parameter lifecycle/edit behavior, nor by 071b because that owner is transient run configuration, nor by 040 because proposals are not a coordinated canonical commit. The minimum viable new responsibility is therefore the coordination/revision/change-set boundary above. This definition remains documentation-only; exact schema/API/service choices must be re-derived in the full-spec/readiness steps from then-current master.