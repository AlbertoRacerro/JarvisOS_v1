# 112 PROJECT-KNOWLEDGE-CORE-1 — definition

Exact source master: `870bb3f038e5d46af485435e20dafbf7d6c7baa4`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `112` registry row from `planned`.

Governing planning and merged runtime authority:
- `docs/specs/100c-queue-rederivation-2026-08-28.md` and the associated 100c overlap/capability ownership audits;
- `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` for the accepted working-revision, final-reconciliation, and deterministic revalidation semantics;
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

The final Project Knowledge surface needs one truthful way to edit the project basis and stage accepted Project Basis/model changes while reasoning about the consequences of a coordinated engineering change without creating another project/model database. Today the repository already has several deliberately separate owners:

- canonical engineering records and proposal/promotion behavior;
- Parameter lifecycle/CAS mutation;
- dependency/provenance and stale overlays;
- model/run/evidence artifacts whose existing ownership must be audited rather than duplicated;
- a transient run-oriented working configuration;
- read-first Engineering Data navigation;
- explicit Jarvis context/proposal contracts.

Those owners solve narrower problems, but none currently owns the Project Basis/model working-revision boundary required by the merged 100c queue: a coherent change set can be staged against an immutable parent, accepted into an inspectable working revision without overwriting the reconciled parent, deterministically validated/revalidated, discarded if necessary, and only then promoted by explicit final reconciliation while preserving immutable history.

112 therefore owns the **coordination and working-revision layer over existing canonical engineering/model owners**, not a replacement for them. Its job is to make Project Basis/model change sets bounded server-owned intents/revisions whose accepted operations preserve existing owner authority, whose impact/revalidation evidence is derived from current dependency/freshness/output truth, and whose final promotion is a separate explicit reconciliation transition.

## Current-owner audit and overlap disposition

### 001 / canonical engineering records

Existing engineering records remain the canonical data. 112 MUST NOT introduce peer `project_parameters`, `project_requirements`, `project_assumptions`, `project_decisions`, or a generic duplicate record table. A Project Basis revision references exact canonical owner identities and proposed operations against them.

### 040 / MemoryStore

040 remains the proposal/promotion boundary for AI- and calculation-originated engineering-record proposals. Model/Jarvis output cannot use 112 to bypass proposal status or silently become canonical state. Where a change-set item originates from AI, 112 must preserve the existing proposal identity/provenance and require the same explicit/deterministic promotion boundary before it may become an accepted working change.

### 042 / context packs

042 remains deterministic read/context selection authority. A Project Basis/model working revision is not an alternate context store or retrieval index. 112 may expose exact revision/change-set refs for later 121 CONTEXT actions, but context materialization remains through accepted owner/context contracts.

### 050 / dependency graph

050 remains the read-derived dependency/provenance graph and canonical ref resolver. 112 MUST derive impact from this owner (or a narrowly factored equivalent current seam), not persist a second dependency graph/cache. Incomplete/bounded lineage must fail closed rather than claim complete impact.

### 051 / freshness invalidation

051 remains deterministic downstream stale/invalidation authority for canonical replacement lineage. 112 may coordinate when stale/revalidation evidence is produced or reconciled, but must not silently clear stale state, rewrite historical run status, or invent a second freshness system.

### 071b / transient working configuration

071b is the sole transient run-oriented working configuration and preflight owner. It is deliberately separate from canonical Project Knowledge working revisions. 112 MUST NOT merge these concepts: changing a Project Basis/model working revision does not silently mutate the current 071b working configuration, and editing/running a 071b configuration does not silently reconcile Project Knowledge. Any future explicit handoff must preserve exact revision identity and remain separately authorized.

### 098 / Parameter lifecycle and canonical CAS

098 remains the current Parameter edit/lifecycle authority, including exact workspace/current-state/`updated_at` checks, `BEGIN IMMEDIATE` mutation, audit evidence, replacement semantics, lifecycle-current filtering and dependent protection. 112 must reuse those semantics for Parameter operations rather than adding a peer Parameter writer. Where 112 needs multi-record atomicity, the full spec must identify the smallest transaction-capable internal service seam that can compose accepted owner operations without weakening their validation.

### Model-definition / assumption / method ownership

Merged 100c assigns **model change sets and working revisions** to 112, while 113 is read-only dossier aggregation and 121 is proposal/context only. Therefore 112 cannot narrow its definition so far that accepted model-definition, assumption, or method changes have no implementation owner. The full-spec exact-master audit MUST identify the current canonical source/version seams for those model-level fields and either compose their existing mutation/version authority or define the minimum additive 112 working-revision/reconciliation seam necessary to satisfy the accepted model-change contract. It MUST NOT create a second peer model truth store merely for convenience.

### 035 / Engineering Data

035 remains read-first navigation and 098 already activates bounded server-backed Parameter edit/lifecycle controls there. 112 may activate the truthful Project Basis/Models controls reserved by 100f/100g, but must not create a second generic Engineering Data navigator or redesign the canonical surfaces.

### 111 / Jarvis

111 provides exact, inspectable, stale-safe CONTEXT/PROPOSE contracts only. 112 owns domain working-revision acceptance, deterministic validation/revalidation coordination, and final reconciliation for Project Knowledge; Jarvis does not. Later 121 may propose Project Knowledge operations against exact 112 refs, but acceptance/reconciliation stays 112/domain-owned.

## Definition boundary

112 owns one server-side **Project Basis/model change-set and working-revision coordination contract** over existing canonical owners.

It MUST define:

1. **Exact immutable parent identity** — every working revision starts from one exact server-resolved Project Basis/model parent snapshot/revision identity. Unknown or incomplete identity fails closed; the browser cannot declare the canonical parent.
2. **Bounded change set** — a draft contains an ordered, typed set of intended record/model operations against exact owner/type/id/current-revision tokens. The change set stores bounded intent and evidence references, not duplicate canonical engineering/model values as a peer truth store.
3. **Optimistic stale/CAS protection** — each operation carries the exact owner revision token available from that owner (`updated_at`, lifecycle state, replacement/source revision, model/version identity, or later equivalent). Parent or target drift invalidates acceptance until explicitly rebased/reviewed.
4. **Proposal vs operator mutation distinction** — origin and authority are explicit. AI/Jarvis/calculation proposals remain proposals; operator-authored direct changes may use only domain operations authorized by the owning contract. 112 cannot promote unsupported kinds merely because they appear in a change set.
5. **Deterministic impact preview** — before approval, derive bounded downstream impact/revalidation requirements from current canonical refs plus 050/051 and exact stored-output evidence. The preview records exact source/target refs, completeness/bounds and current revision identity; it cannot claim freshness when lineage is incomplete.
6. **Accepted working revision, separate from final reconciliation** — operator approval of the exact displayed bounded batch atomically creates/advances an immutable, inspectable working revision. Approval MUST NOT overwrite the reconciled parent in place. The accepted working revision remains available for deterministic validation/test/review or discard before any later promotion to current reconciled truth.
7. **Deterministic validation/revalidation execution** — when exact stored outputs are sufficient for a changed rule/criterion, 112 MUST actually invoke the accepted deterministic acceptance logic and persist PASS/FAIL (or the contract's explicit deterministic outcome) evidence bound to the accepted working revision, changed basis/rule identity, source-output identities and validator/version identity. It must not stop at a generic `needs-revalidation` classification when zero-rerun deterministic evaluation is possible. When recomputation is genuinely required, 112 records the truthful required domain/chain and does not fabricate completion.
8. **Explicit final reconciliation** — only a later explicit action may promote a validated exact working revision to current reconciled truth. That transition applies every supported canonical mutation plus required audit/freshness/replacement/validation evidence atomically, or applies none. Partial final reconciliation is forbidden.
9. **Immutable revision/history evidence** — draft, accepted, discarded, rejected, superseded/rebased, validation and failed reconciliation attempts retain inspectable parent/change-set/outcome identity. History is audit evidence, not a mutable alternate canonical record store.
10. **Idempotent retry / response-loss safety** — accepted-working-revision and final-reconciliation transitions each have server-owned request/revision identity. Replaying the same exact intent returns the existing outcome; a conflicting payload under the same identity fails closed.
11. **Bounded activation on Project Basis/Models** — expose only controls backed by real 112 authority and current owner capabilities. Unsupported mutation remains visibly unavailable/read-only rather than simulated in frontend state, but full-spec ownership may not silently omit model-level working changes assigned to 112 by 100c.

## Working-revision state model to freeze in the full spec

The full spec must derive the smallest state model necessary from current code, but it must preserve these semantic distinctions:

- **reconciled parent revision**: immutable exact current basis/model revision from which the draft was derived;
- **draft intent**: mutable server-owned change-set intent that has no reconciled-parent effect;
- **impact preview**: deterministic evidence bound to the exact draft/parent/owner revisions;
- **accepted working revision**: immutable exact approved batch materialized as an inspectable working revision while the reconciled parent remains unchanged;
- **validation/revalidation evidence**: deterministic PASS/FAIL/no-material-effect evidence when exact outputs suffice, or explicit recomputation-required state/domain chain when they do not;
- **discarded/superseded working outcome**: immutable terminal evidence that leaves the reconciled parent unchanged;
- **final reconciliation intent**: immutable explicit promotion request against one exact validated working revision and one still-current reconciled parent;
- **final reconciliation outcome**: promoted atomically, rejected/conflicted, or failed without partial canonical effect;
- **successor/rebase relationship**: a new draft/working revision may supersede an obsolete one but never rewrites prior parent/history/validation evidence.

Names/storage representation are not authorized by this definition. The full spec must prove whether persistence is minimum-necessary and, if so, use the smallest additive schema instead of creating a generalized Project/model store.

## Atomicity and owner-composition requirements

The hardest 112 failure mode is cross-owner partial success. The future full spec/readiness therefore MUST prove an implementation route that:

- resolves all exact target rows and authority checks before either accepted-working-revision creation or final canonical promotion;
- validates workspace, lifecycle/current state, owner revision/CAS tokens and proposal eligibility on the transaction snapshot appropriate to the transition;
- keeps `Approve all` atomic for the exact displayed batch while leaving the reconciled parent unchanged;
- for final reconciliation, opens one SQLite write transaction at the composition boundary when all affected canonical owners share the existing database;
- invokes/refactors existing owner validation/mutation primitives so their invariants are preserved inside that transaction rather than calling HTTP endpoints sequentially;
- persists required canonical audit/replacement/freshness/validation success effects within the same successful final-reconciliation outcome;
- rolls back every canonical mutation and success effect if any supported final-reconciliation operation fails, then records the immutable failed reconciliation/idempotency outcome outside the rolled-back transaction (or through an equivalent savepoint/transaction design) so response-loss retry cannot confuse a prior failure with an unseen request;
- never performs provider, solver, filesystem or network side effects inside the canonical database transaction;
- explicitly rejects a change set containing a field whose current owner cannot participate safely in the accepted-working or final-reconciliation contract, unless the full spec establishes the minimum additive 112-owned revision seam required by the 100c model-change authority.

If fresh exact-master audit shows required atomic composition or the assigned model working-revision ownership cannot be achieved without weakening an existing owner or creating duplicate truth, readiness MUST block and re-derive the minimum safe boundary rather than authorize best-effort multi-step commits or silently orphan the capability.

## Revalidation semantics

112 owns **deterministic Project Knowledge revalidation orchestration**, not a generic recompute engine.

- Impact is derived from exact current 050 graph/provenance evidence, 051 stale overlays and exact source-output identity.
- Existing results/runs remain historical evidence; 112 does not rewrite them to look current.
- If exact stored outputs are sufficient for the changed rule/criterion, 112 executes the deterministic acceptance/evaluation logic without rerunning the underlying solver/model, and records new validation evidence bound to the accepted working revision, changed basis/rule and exact source outputs. A PASS/FAIL outcome is evidence; a generic `current`/`needs-revalidation` label is not a substitute.
- If Process, BLUECAD or another domain recomputation is genuinely required, the working revision records truthful recomputation-required/STALE state and the required domain/chain. `STALE` is not used when exact deterministic re-evaluation is sufficient.
- Actual recomputation remains with the relevant runner/evaluator/domain owner and must be an explicit later action; 112 does not invent a generic solver execution engine.
- Final reconciliation may promote only according to the full-spec validation policy; it cannot clear stale solely because the operator accepted the change.
- Revalidation completion must be evidenced by exact validator/result/run/source identity as appropriate; no timestamp-only or frontend-only “validated” flag.
- Incomplete graph traversal, missing owner identity, unsupported relation, bound exhaustion or stale preview invalidates the affected transition or yields explicit incomplete impact according to the full-spec contract; it never becomes silent “no impact”.

## Concurrency and stale behavior

The full spec/readiness must cover at least:

- two drafts/working revisions from the same reconciled parent;
- canonical target mutation after preview but before approval;
- canonical target or reconciled-parent drift after working-revision acceptance but before final reconciliation;
- target lifecycle change/deletion/supersession during editing;
- replacement lineage changing while a revision is open;
- proposal promoted/rejected independently after it was referenced;
- accepted-working-revision request retried after response loss;
- final-reconciliation request retried after response loss;
- competing final reconciliation of two validated revisions derived from the same parent;
- deterministic validation evidence becoming stale because bound source/rule/validator identity changed;
- workspace switch / stale frontend response;
- bounded impact graph becoming incomplete or changing between preview, approval, validation and final reconciliation.

All cases must fail closed or return the already-recorded idempotent outcome; none may partially overwrite the reconciled parent.

## Required invariants

- No second project/model/engineering-record truth store.
- No duplicate dependency graph, freshness engine, proposal store or 071b transient working-configuration owner.
- No direct reconciled canonical mutation from model/Jarvis output.
- `Approve all` creates/advances the exact inspectable working revision; it does not overwrite the reconciled parent in place.
- Final reconciliation is a separate explicit promotion transition over a validated exact working revision.
- No frontend-owned canonical Project Knowledge revision or fake optimistic reconciliation.
- No silent merge/rebase when exact parent/target revision changed.
- No partial multi-record/model final reconciliation.
- No automatic provider/LLM or hidden solver execution as part of reconciliation.
- Deterministic zero-rerun validation MUST execute when exact stored outputs suffice; required recomputation must remain truthful and explicit.
- No automatic clearing of stale/revalidation state without bound validation evidence.
- Failed final reconciliation rolls back canonical mutations while retaining an immutable failed request/outcome for audit and idempotent retry.
- No fabricated impact, readiness, freshness, provenance, unit compatibility, validation or successful reconciliation evidence.
- Existing unit normalization, lifecycle/replacement, dependency/provenance, event/audit and workspace isolation rules remain authoritative.
- `route_class="auto"` never becomes an external-provider path; Product AI remains behind the current AI execution/policy/ledger spine.

## V0 scope and owner proof

112 is not required to invent unsafe generic CRUD for every engineering-record field, but it **is** required to cover the Project Basis/model working-revision responsibilities assigned by merged 100c. Current exact-master evidence shows 098 already supplies strong canonical Parameter edit/lifecycle/CAS semantics, so Parameter operations are a proven reusable owner seam rather than the entire 112 product boundary.

Before readiness, the full spec MUST separately prove the minimum safe owner/mutation/version route for model-definition, assumption and method changes. If an existing canonical owner can be composed, 112 reuses it. If no current mutable owner exists, the full spec may define only the minimum additive version/revision seam necessary for 112's accepted model working changes and reconciliation, with explicit proof that it is not a peer model truth store. If neither route is safe, readiness blocks and re-derives ownership; it must not silently defer those accepted changes to read-only 113 or proposal-only 121.

## Frontend obligation

User-facing work, if required by the full spec, is limited to activating existing canonical Project Basis/Models composition:

- show exact reconciled-parent and working-revision identity;
- stage supported changes through server-owned draft intent;
- show proposal/operator origin and unsupported read-only fields truthfully;
- preview deterministic impact/revalidation evidence before approval;
- `Approve all` only the exact displayed bounded batch into an inspectable working revision;
- display deterministic validation PASS/FAIL/no-material-effect evidence or truthful recomputation-required states;
- allow discard/supersede without destroying prior reconciled snapshots/evidence;
- require a separate explicit final reconciliation for promotion of a validated exact working revision;
- present stale/conflict/incomplete-impact/failure states explicitly;
- after final reconciliation, reload canonical server truth rather than trusting optimistic local state.

No global visual redesign, alternate Project page, client-side canonical store, hidden context addition or invented model dossier/literature/search behavior is authorized.

## Full-spec exact-master audit obligations

Before 112 can become `ready`, the full-spec pass must inspect then-current code and name the exact seams for:

- canonical record reads and Parameter mutation/lifecycle transaction logic;
- current canonical model-definition/version/source ownership for definition, assumptions and methods, including the minimum mutation/version seam required by 100c;
- MemoryStore proposal promotion/rejection and replacement promotion;
- dependency graph construction/canonical ref resolution;
- freshness invalidation persistence and stale reads;
- deterministic validator/acceptance logic capable of re-evaluating changed criteria/rules from exact stored outputs without a solver rerun;
- validation evidence persistence and exact source/rule/validator binding;
- event/audit persistence, including failed reconciliation outcomes that must survive canonical transaction rollback;
- current unit normalization and linked-source revision checks;
- existing 071b working configuration and the explicit non-overlap boundary;
- current Project Basis/Models/Engineering Data frontend composition and API client seams;
- 111 exact context/action contracts for future 121 integration.

For each proposed new persistent structure, endpoint or service, the full spec must state why an existing owner cannot satisfy the requirement and why the additive seam is minimum-necessary.

## Acceptance criteria for future full spec/readiness

Before implementation authority exists, exact-master full spec/readiness must prove:

1. one canonical owner for every V0-supported mutable engineering/model field and no second Project/record/model truth store;
2. exact reconciled-parent and target revision/CAS semantics with stale rejection;
3. bounded server-owned draft identity separated from canonical records and 071b transient run configuration;
4. exact `Approve all` transition that creates/advances an inspectable accepted working revision without overwriting the reconciled parent;
5. proposal-origin changes cannot bypass 040/record-owner promotion authority;
6. deterministic impact uses 050/051/current output authority and represents incomplete bounds explicitly;
7. exact stored outputs trigger actual deterministic re-evaluation with bound PASS/FAIL/no-material-effect evidence; genuine recomputation requirements identify the required domain/chain without fake completion;
8. separate explicit final reconciliation promotes only the exact validated working revision and uses one all-or-nothing transaction route for every V0-supported canonical mutation, audit, freshness and validation effect;
9. failed final reconciliation rolls back canonical success effects but preserves an immutable failed request/outcome outside that rollback for audit/idempotent retry;
10. idempotent response-loss retry and competing-revision protection for both approval and final reconciliation;
11. no provider/LLM/network/filesystem side effect inside reconciliation and no hidden solver recompute/unstale behavior;
12. immutable parent/working/history/validation/outcome evidence survives discard, rebase, conflict and failure;
13. deterministic tests cover dirty/stale targets, lifecycle drift, concurrent revisions, proposal drift, incomplete impact, zero-rerun PASS/FAIL revalidation, recomputation-required classification, mid-transaction failure rollback with surviving failure outcome, idempotent replay and cross-workspace isolation;
14. existing unit/provenance/replacement semantics remain intact under coordinated change;
15. model-definition/assumption/method working changes assigned to 112 have a proven canonical owner/minimum revision seam and are not silently orphaned to 113/121;
16. visible work, if any, preserves 100f/100g composition and receives exact-head browser proof for draft, accepted-working, validation, discard, stale/conflict, incomplete-impact, unsupported-field, failed reconciliation and successful final-reload states;
17. every non-112 Project Knowledge control is explicitly deferred to 113–115/121 or another canonical owner.

## Non-goals

- A second canonical project/model/engineering-record database.
- Unsafe generic mutable CRUD for fields whose ownership/version semantics cannot satisfy the 112 working-revision contract.
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
- A new generic recompute engine; 112 only executes deterministic acceptance logic when exact stored outputs suffice and coordinates explicit domain recomputation otherwise.
- Hermes runtime or reopening 066–068/080.

## Minimum-necessary test

Criterion: provide one atomic, stale-safe, auditable Project Basis/model change and working-revision boundary over existing canonical owners so operators can approve an exact batch into an inspectable working revision, deterministically validate/revalidate it, discard it safely, and explicitly reconcile only a validated exact revision without duplicate truth or partial canonical promotion.

The need is not satisfied by 098 alone because 098 deliberately owns Parameter lifecycle/edit behavior, nor by 071b because that owner is transient run configuration, nor by 040 because proposals are not an accepted Project Knowledge working revision, nor by 113/121 because they are read/proposal surfaces rather than model working-revision/reconciliation owners. The minimum viable new responsibility is therefore the coordination/revision/change-set/validation/reconciliation boundary above, including the model-level working changes assigned by 100c. This definition remains documentation-only; exact schema/API/service choices must be re-derived in the full-spec/readiness steps from then-current master.