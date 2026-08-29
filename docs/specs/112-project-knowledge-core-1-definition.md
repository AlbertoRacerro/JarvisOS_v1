# 112 PROJECT-KNOWLEDGE-CORE-1 — definition

Exact source master: `870bb3f038e5d46af485435e20dafbf7d6c7baa4`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `112` registry row from `planned`.

Governing planning and merged runtime authority:
- `docs/specs/100c-queue-rederivation-2026-08-28.md` and the associated 100c overlap/capability ownership audits;
- `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` and `docs/product-direction/07-model-change-validation-and-reconciliation.md` for accepted working-revision, validation, reconciliation and operator interaction semantics;
- merged 001 engineering-record schema foundation;
- merged 035 Engineering Data read-first navigator;
- merged 040 MemoryStore proposal/promotion boundary;
- merged 042 deterministic context-pack selection/preview;
- merged 050 dependency/provenance graph and canonical `<kind>:<id>` resolver;
- merged 051 deterministic freshness invalidation and replacement lineage;
- merged 071b single transient run-working-configuration owner and preflight semantics;
- merged 098 Parameter-first canonical lifecycle/CAS mutation authority;
- merged 111 common Jarvis exact-context/action foundation.

## Problem and ownership

112 must provide one truthful server-owned coordination boundary for Project Basis/model change sets and working revisions without creating a second project/model/engineering truth store. Existing owners remain authoritative for their narrower responsibilities: engineering records, proposal/promotion, Parameter lifecycle/CAS, dependency/provenance, freshness, run-working configuration, model/run/evidence artifacts and Jarvis context/proposal contracts.

112 owns the missing coordination layer: an exact change set can be staged against an exact reconciled **or accepted working** parent, approved into an inspectable working revision without overwriting reconciled truth, deterministically validated/revalidated, continued as a successor working revision, discarded/superseded safely, and only later promoted by explicit final reconciliation while immutable history remains inspectable.

112 is not a replacement for existing owners. It coordinates exact intents/revisions over them and must reuse their invariants.

## Current-owner audit and overlap disposition

### Canonical engineering records / 001

Existing engineering records remain canonical. 112 MUST NOT create peer `project_parameters`, `project_requirements`, `project_assumptions`, `project_decisions` or a generic duplicate engineering-record table. A working revision references exact canonical owner/type/id/revision identities and bounded intended operations.

### MemoryStore / 040

040 remains proposal/promotion authority for AI- and calculation-originated engineering-record proposals. Jarvis/model output cannot use 112 to bypass proposal status or silently become accepted state. Proposal identity/provenance and explicit/deterministic promotion requirements must survive inclusion in a 112 change set.

### Context packs / 042

042 remains deterministic read/context selection authority. A working revision is not an alternate context store or retrieval index. 112 may expose exact refs for later 121 actions, but context materialization remains with accepted context owners.

### Dependency and freshness / 050, 051

050 remains dependency/provenance graph and canonical-ref authority. 051 remains freshness invalidation/replacement-lineage authority. 112 derives bounded impact and coordinates validation from those owners; it does not persist a second graph/freshness engine, rewrite historical run status, or silently clear stale state. Incomplete graph traversal is explicit and fail-closed, never equivalent to `no impact`.

### Transient run working configuration / 071b

071b remains the sole transient run-oriented working configuration/preflight owner. Project Knowledge working revisions are deliberately separate. A 112 revision must not silently mutate 071b state, and a 071b edit/run must not silently reconcile Project Knowledge. Any later handoff must preserve exact revision identity and receive separate authority.

### Parameter lifecycle/CAS / 098

098 remains Parameter mutation/lifecycle authority, including workspace/current-state checks, exact revision/CAS semantics, replacement/lifecycle protection, audit evidence and transaction behavior. 112 must compose those semantics rather than add a peer Parameter writer. If cross-record atomicity needs refactoring, the full spec must identify the smallest transaction-capable internal seam that preserves 098 invariants.

### Model-definition / assumption / method ownership

Merged 100c assigns **model change sets and working revisions** to 112, while 113 is read-only dossier aggregation and 121 is context/proposal only. Therefore 112 cannot narrow to Parameters alone. Before readiness, the full spec must identify current canonical source/version/mutation seams for model-definition, assumption and method changes, or define only the minimum additive revision seam needed to satisfy 100c without creating a peer model truth store. If neither route is safe, readiness blocks rather than orphaning the capability.

### Engineering Data / 035

035 remains read-first navigation and 098 already backs bounded Parameter controls. 112 may activate only truthful Project Basis/Models controls backed by accepted authority; it must not create another generic navigator or alternate Project page.

### Jarvis / 111

111 supplies exact, inspectable, stale-safe CONTEXT/PROPOSE contracts. 112 owns Project Knowledge working-revision approval, deterministic validation coordination and final reconciliation. Later 121 may propose operations against exact 112 refs; acceptance/reconciliation remain domain-owned.

## Definition boundary

112 owns one server-side **Project Basis/model change-set and working-revision coordination contract** over current canonical owners.

It MUST define:

1. **Exact parent identity and chaining** — every draft/working revision has one immutable server-resolved parent that may be either a reconciled revision or an accepted working revision. By default, a subsequent accepted modification derives from the exact selected/immediately previous accepted working revision; branching from another exact revision must be deliberate and explicit. Unknown/incomplete parent identity fails closed and the browser cannot declare it.
2. **Bounded change set** — an ordered typed set of intended record/model operations against exact owner/type/id/revision tokens. It stores bounded intent/evidence references, not peer canonical truth.
3. **Optimistic stale/CAS protection** — owner revision tokens, parent identity, lifecycle/replacement state and proposal eligibility must still match at every protected transition; drift requires explicit review/rebase.
4. **Proposal vs operator distinction** — AI/Jarvis/calculation proposals remain proposals. Operator-authored changes may use only mutations authorized by current domain owners. Unsupported kinds cannot become mutable merely because they appear in a batch.
5. **Deterministic impact preview** — before approval, derive bounded impact/revalidation requirements from exact current refs, 050/051 and exact stored-output evidence. Record completeness/bounds and revision identity; missing/incomplete lineage never becomes silent `no impact`.
6. **Accepted working revision separate from final reconciliation** — `Approve all` applies only to the exact displayed batch and atomically creates/advances an immutable inspectable working revision. It MUST NOT overwrite the reconciled parent. The revision remains available for validation/test/compare/continuation/discard before promotion.
7. **Deterministic validation/revalidation execution** — when exact stored outputs suffice for a changed rule/criterion, actually invoke accepted deterministic acceptance logic and persist bound PASS/FAIL/no-material-effect evidence with exact working revision, changed rule/basis, source-output and validator/version identity. A generic `needs-revalidation` label is insufficient.
8. **Truthful recomputation-required state and Validate route** — when Process, BLUECAD or another domain must recalculate, record the exact required domain/chain and expose a clear `Validate` action. Until batch validation exists, that action may deep-link to the relevant `Design > Process` or `Design > BLUECAD` workspace with the affected exact working revision selected and required context/action visible. Actual solver/domain execution remains with its canonical owner; 112 does not fabricate completion or create a generic recompute engine.
9. **Explicit final reconciliation** — only a later deliberate action may make one exact terminally validated working revision current. All supported canonical mutations plus required audit/freshness/replacement/validation effects are atomic or none apply.
10. **Known FAIL acknowledgement** — reconciliation requires mandatory validation/recalculation work to reach a terminal known state; unknown/missing/unresolved required evidence blocks ordinary reconciliation. Actual PASS/FAIL results are preserved. A known mandatory FAIL may be reconciled only under explicit acknowledgement or accepted policy; it may neither be silently promoted nor made permanently unreconcilable merely because the truthful state is FAIL.
11. **Immutable history** — parent/change-set/approval/validation/discard/supersede/rebase/reconciliation/failure outcomes remain inspectable and are never rewritten into current truth.
12. **Idempotent retry / response-loss safety** — approval and final reconciliation each use server-owned request/revision identity. Same exact retry returns the existing outcome; conflicting reuse fails closed.
13. **Bounded frontend activation** — only controls backed by current 112/owner authority are enabled. Unsupported mutation remains visibly unavailable/read-only; frontend state never becomes canonical authority.

## Working-revision state model to freeze in the full spec

The full spec must derive the minimum persistent representation from then-current code while preserving these semantic distinctions:

- **reconciled revision**: immutable exact canonical current snapshot;
- **exact parent revision**: reconciled or accepted-working identity selected for a draft;
- **draft intent**: mutable server-owned bounded change-set intent with no reconciled effect;
- **impact preview**: deterministic evidence bound to exact draft/parent/owner revisions;
- **accepted working revision**: immutable exact approved batch whose parent may be reconciled or another accepted working revision;
- **working-revision chain/branch relation**: exact successor lineage; later accepted changes normally chain from the selected/immediately previous working revision unless explicit branching is requested;
- **validation evidence**: bound PASS/FAIL/no-material-effect evidence, or explicit recomputation-required state/domain chain;
- **discarded/superseded outcome**: immutable terminal evidence that leaves reconciled truth unchanged;
- **final reconciliation intent**: immutable promotion request for one exact working revision against one still-current reconciled target;
- **final reconciliation outcome**: promoted atomically, rejected/conflicted, acknowledged-known-failure promotion, or failed without partial canonical effect;
- **rebase/successor relation**: a successor may replace an obsolete draft/working branch as the active candidate but never rewrites prior lineage/evidence.

Names/storage representation are not authorized by this definition. Persistence, if needed, must be the smallest additive schema rather than a generalized Project/model store.

## Atomicity and owner-composition requirements

The future full spec/readiness MUST prove a route that:

- resolves exact parent/target rows and authority before protected transitions;
- validates workspace, lifecycle/current state, proposal eligibility and all owner revision/CAS tokens on the correct transaction snapshot;
- keeps `Approve all` atomic for its exact batch while reconciled truth remains unchanged;
- for final reconciliation, opens one SQLite write transaction at the composition boundary when affected owners share the current database;
- invokes/refactors existing owner validation/mutation primitives inside that boundary rather than sequencing HTTP mutations;
- persists required success audit/replacement/freshness/validation effects with the same successful final outcome;
- on any final-reconciliation failure, rolls back every canonical mutation/success effect, then records an immutable failed request/outcome outside the rolled-back transaction (or equivalent savepoint design) so audit/idempotent retry survives response loss;
- performs no provider, solver, filesystem or network side effects inside the canonical DB transaction;
- rejects unsupported fields unless the full spec proves the minimum additive 112 revision seam required by 100c.

If safe owner composition or model working-revision ownership cannot be proven without duplicate truth or weakened invariants, readiness MUST block and re-derive rather than authorize best-effort partial commits.

## Revalidation semantics

112 owns deterministic Project Knowledge **validation orchestration**, not a generic recompute engine.

- Impact comes from exact 050 graph/provenance, 051 freshness and exact source-output identity.
- Historical results/runs remain historical; 112 never rewrites them to look current.
- If stored outputs suffice, deterministic validation executes immediately after approval and records new bound PASS/FAIL/no-material-effect evidence.
- If recomputation is genuinely required, state is explicitly validation/recalculation-required and names the affected domain/chain. A `Validate` control routes the operator to the relevant domain with the affected exact working revision selected; Process/BLUECAD/other domain owners perform the actual calculation.
- When calculations finish, validation state resolves to actual terminal outcomes and exact run/evidence refs rather than a permanent generic stale badge.
- Final reconciliation requires terminal known required outcomes. Known mandatory failures require explicit acknowledgement/policy; unresolved stale/unknown/missing evidence blocks ordinary reconciliation.
- Incomplete graph traversal, missing owner identity, unsupported relation, bound exhaustion or stale preview yields explicit incomplete impact or rejection; never `no impact`.

## Concurrency and stale behavior

The full spec/readiness must cover at least:

- two drafts from one exact reconciled or working parent;
- successive accepted working revisions chained from the immediately previous selected working revision;
- deliberate branching from another exact reconciled/working revision;
- target mutation after preview but before approval;
- target/reconciled-parent drift after working approval but before final reconciliation;
- lifecycle/deletion/supersession or replacement-lineage drift;
- proposal promotion/rejection drift;
- approval retry and final-reconciliation retry after response loss;
- competing final reconciliation from the same reconciled target;
- validation evidence becoming stale because source/rule/validator identity changed;
- known FAIL with and without explicit acknowledgement/policy;
- workspace switch / stale frontend response;
- bounded impact graph changing between preview, approval, validation and reconciliation.

Every case must fail closed, require deliberate rebase/branch/acknowledgement where applicable, or return an already-recorded idempotent outcome; none may partially overwrite reconciled truth.

## Required invariants

- No second project/model/engineering-record truth store.
- No duplicate dependency graph, freshness engine, proposal store or 071b run-working owner.
- No direct reconciled mutation from Jarvis/model output.
- `Approve all` creates/advances an exact inspectable working revision; it does not overwrite reconciled truth.
- Later working revisions preserve exact parent chaining unless explicit branching selects another exact revision.
- Final reconciliation is a separate explicit promotion transition.
- Unknown/missing required validation blocks ordinary reconciliation; truthful known FAIL is preserved and requires explicit acknowledgement/policy if promoted.
- No frontend-owned canonical revision or optimistic fake reconciliation.
- No silent merge/rebase after parent/target drift.
- No partial multi-record/model final reconciliation.
- No hidden provider/LLM/solver execution inside reconciliation.
- Zero-rerun deterministic validation executes when exact outputs suffice; genuine recomputation stays truthful and explicit with a usable Validate route.
- No clearing stale/revalidation state without bound evidence.
- Failed final reconciliation rolls back canonical effects while preserving immutable failure evidence.
- No fabricated impact, readiness, freshness, provenance, unit compatibility, validation or successful reconciliation evidence.
- Existing unit/provenance/replacement/workspace isolation and AI policy invariants remain authoritative, including `route_class="auto"` never external and Product AI remaining behind the current execution/policy/ledger spine.

## V0 scope and owner proof

112 need not invent unsafe generic CRUD for every engineering field, but it MUST cover the Project Basis/model working-revision responsibilities assigned by 100c. 098 is a proven reusable Parameter mutation seam, not the whole 112 boundary.

Before readiness, the full spec MUST prove the minimum safe owner/mutation/version route for model-definition, assumption and method changes. Reuse an existing canonical owner where possible; otherwise define only the minimum additive revision seam required by 112. If neither is safe, readiness blocks rather than silently deferring those changes to read-only 113 or proposal-only 121.

## Frontend obligation

If the full spec requires user-facing work, it is limited to activating existing canonical Project Basis/Models composition:

- show exact reconciled and selected parent/working-revision identity and chain;
- stage supported changes through server-owned draft intent;
- show proposal/operator origin and unsupported read-only fields truthfully;
- preview bounded deterministic impact/revalidation evidence before approval;
- `Approve all` only the exact displayed batch into an inspectable working revision;
- display bound PASS/FAIL/no-material-effect evidence or truthful recomputation-required state;
- for recomputation-required state, expose `Validate` navigation to the relevant domain with the affected exact working revision selected;
- allow safe continuation from the selected/immediately previous working revision, deliberate exact branching, and discard/supersede without destroying history;
- require separate explicit final reconciliation;
- require explicit acknowledgement/policy for known mandatory FAIL promotion;
- present stale/conflict/incomplete-impact/failure states explicitly;
- after reconciliation, reload canonical server truth rather than trusting local state.

No global visual redesign, alternate Project page, client-side canonical store, hidden context addition, model dossier/literature/search behavior or generic recompute UI is authorized.

## Full-spec exact-master audit obligations

Before 112 can become `ready`, the full-spec pass must inspect then-current code and name exact seams for:

- canonical record reads and Parameter mutation/lifecycle transaction logic;
- canonical model-definition/version/source ownership for definition, assumptions and methods;
- proposal promotion/rejection and replacement promotion;
- dependency graph/ref resolution and freshness invalidation;
- deterministic validator logic capable of zero-rerun re-evaluation;
- validation evidence persistence and exact source/rule/validator binding;
- event/audit persistence, including failed reconciliation outcomes that survive canonical rollback;
- current unit normalization and linked-source revision checks;
- 071b run-working configuration and explicit non-overlap;
- current Project Basis/Models/Engineering Data frontend/API seams, including exact-revision Validate navigation;
- 111 exact context/action contracts for future 121 integration.

Every proposed persistent structure, endpoint or service must state why existing owners cannot satisfy the requirement and why the additive seam is minimum necessary.

## Acceptance criteria for future full spec/readiness

Before implementation authority exists, exact-master full spec/readiness must prove:

1. one canonical owner for every V0-supported mutable engineering/model field and no second Project/record/model truth store;
2. exact parent semantics supporting reconciled or accepted-working parents, default successor chaining and deliberate exact branching;
3. exact target revision/CAS semantics with stale rejection;
4. bounded server-owned draft identity separated from canonical records and 071b state;
5. exact `Approve all` creating/advancing an inspectable working revision without overwriting reconciled truth;
6. proposal-origin changes cannot bypass 040/current owner promotion authority;
7. deterministic impact uses 050/051/current output authority and represents incomplete bounds explicitly;
8. exact stored outputs trigger actual deterministic PASS/FAIL/no-material-effect re-evaluation; genuine recomputation names the required domain/chain and provides exact-working-revision Validate navigation without fake completion;
9. final reconciliation promotes one exact terminally validated working revision atomically; unresolved required state blocks, while known mandatory FAIL requires explicit acknowledgement/policy and preserves the FAIL evidence;
10. failed final reconciliation rolls back canonical success effects but preserves immutable failure outcome/audit/idempotency evidence;
11. idempotent response-loss retry and competing-revision protection for approval and reconciliation;
12. no provider/LLM/network/filesystem side effect inside reconciliation and no hidden solver recompute/unstale behavior;
13. immutable parent/working/history/validation/outcome evidence survives continuation, branching, discard, rebase, conflict and failure;
14. deterministic tests cover stale/dirty targets, lifecycle/proposal drift, chained and branched revisions, incomplete impact, zero-rerun PASS/FAIL, Validate deep-link for recomputation-required work, known FAIL acknowledgement/no-ack behavior, rollback with surviving failure outcome, idempotent replay and cross-workspace isolation;
15. unit/provenance/replacement semantics remain intact under coordinated change;
16. model-definition/assumption/method changes assigned to 112 have a proven canonical owner/minimum revision seam;
17. visible work, if any, preserves 100f/100g composition and receives exact-head browser proof for draft, chained working revision, validation, Validate navigation, discard, conflict, incomplete impact, known FAIL acknowledgement, failed reconciliation and successful final reload;
18. every non-112 Project Knowledge control is explicitly deferred to 113–115/121 or another canonical owner.

## Non-goals

- A second canonical project/model/engineering-record database.
- Unsafe generic mutable CRUD for fields whose ownership/version semantics cannot satisfy this contract.
- Model dossier aggregation (`113`).
- Literature/source ingestion (`114`).
- Cross-project search (`115`).
- Jarvis Project Knowledge domain actions (`121`).
- Roadmap/Calendar/Brainstorm (`116/117/122`).
- Repository/runtime/development-pipeline truth (`118–120/123`).
- Provider/settings expansion (`124`).
- Self-update or PTY (`125/126`).
- Semantic/vector retrieval.
- Process solver/topology/CAD reimplementation.
- A new generic recompute engine.
- Hermes runtime or reopening 066–068/080.

## Minimum-necessary test

Criterion: provide one atomic, stale-safe, auditable Project Basis/model change and working-revision boundary over existing owners so operators can approve an exact batch into an inspectable working revision, continue from or deliberately branch that exact revision, deterministically validate/revalidate it, navigate to required domain validation, preserve truthful PASS/FAIL including acknowledged known failures, discard it safely, and explicitly reconcile only one exact terminally known revision without duplicate truth or partial canonical promotion.

The need is not satisfied by 098 alone because it deliberately owns Parameter lifecycle/edit behavior, nor by 071b because that owner is transient run configuration, nor by 040 because proposals are not an accepted Project Knowledge working revision, nor by 113/121 because they are read/proposal surfaces. The minimum new responsibility is the coordination/revision/change-set/validation/reconciliation boundary above, including model-level working changes assigned by 100c. Exact schema/API/service choices remain for then-current full-spec/readiness derivation.