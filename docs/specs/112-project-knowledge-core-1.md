# 112 PROJECT-KNOWLEDGE-CORE-1

Exact source master: `c39933ce1cb379a42c22a738abad8ae4ff61c1c2`.

Authority: full specification only. This document does not authorize runtime implementation and does not move `112` from `planned`. Readiness remains a separate decision against the exact then-current head.

Binding definition authority:
- `docs/specs/112-project-knowledge-core-1-definition.md`;
- `docs/specs/112-definition-review-closure-2026-08-29.md`.

Preserved merged owners include 001/035/040/042/050/051/071b/098/111 plus current modeling, event, run/evidence and frontend owners. This slice coordinates Project Basis/model change sets and working revisions over those owners; it does not create a peer Project, engineering-record, dependency, freshness, run, proposal, provider, or Jarvis state engine.

## Exact-master owner audit

The following current-head evidence is binding for this specification.

### Parameters

`backend/app/modules/modeling/parameter_lifecycle.py` is the canonical stale-protected Parameter mutation/lifecycle seam. `update_parameter()` opens `BEGIN IMMEDIATE`, checks workspace-scoped identity, `expected_updated_at`, lifecycle state, downstream-dependency restrictions for authority-bearing value/unit changes, performs compare-and-set update, writes the existing event audit, and commits atomically. `transition_parameter()` applies the same stale/lifecycle protection.

112 MUST compose or refactor these internals transaction-safely rather than create a second Parameter writer or sequence protected HTTP calls.

### Requirements / acceptance criteria

`backend/app/modules/modeling/models.py` exposes `RequirementUpdate`, but it currently has no workspace or expected-revision token. `backend/app/modules/modeling/service.py::update_requirement()` performs an unscoped update by id, with no compare-and-set check and no event audit. That path is insufficient for a 112 protected working-revision or reconciliation boundary.

Therefore V0 MUST add the minimum internal Requirement mutation seam that:
- is workspace-scoped;
- requires the exact expected owner revision token (`updated_at` unless a narrower accepted revision token is introduced);
- executes under the caller's SQLite transaction when composed by final reconciliation;
- records the same class of immutable audit evidence as other canonical mutations;
- rejects stale, wrong-workspace and missing rows;
- preserves the existing `requirements` table as canonical identity; no `project_requirements` table is authorized.

The existing public behavior may be migrated to this safer primitive where compatible; 112 does not require a second Requirement API solely for architectural symmetry.

### Model specification / assumptions / methods

Current `backend/app/modules/modeling/service.py` provides create/list/get for `model_specs` and create/list for `assumptions`; there is no current stale-protected update/version seam equivalent to Parameter lifecycle. `ModelSpecCreate` already carries engineering question, scope, maturity, assumptions/input/output summaries and raw payload; `AssumptionCreate` carries statement/scope/confidence/status/source/notes. These current canonical rows remain the truth owner.

V0 disposition:
- **model definition/method fields:** reuse `model_specs` as canonical identity and add the minimum workspace-scoped stale-protected internal update/version operation needed by 112; no peer model-definition table;
- **assumptions:** reuse `assumptions` as canonical identity and add the minimum workspace-scoped stale-protected internal update operation needed by 112; no peer Project assumption table;
- **methods not represented as an independent canonical record:** remain model-spec fields or explicit model-version/source metadata already owned by current modeling. 112 MUST NOT invent a generic method entity merely to fill a form. If exact-master readiness finds a V0 method field that cannot be represented without duplicate truth, readiness blocks that field rather than silently claiming support.

### Remaining Project Basis field classes

For V0, field classes are disposed as follows:

| Project Basis class | Canonical owner / V0 disposition |
| --- | --- |
| Parameter values, units and metadata | existing `parameters`; compose 098 Parameter lifecycle/CAS |
| Requirements / acceptance criteria | existing `requirements`; add minimum CAS/audit internal mutation seam |
| Assumptions | existing `assumptions`; add minimum CAS/audit internal mutation seam |
| Model definition / engineering question / scope / summaries / method-bearing configuration | existing `model_specs`; add minimum CAS/audit internal mutation/version seam |
| Decisions | existing `decisions`; read/context/history only in 112 V0 unless an exact accepted 100c field requires mutation; no new Decision editor authority is created by this slice |
| Literature/source knowledge | not owned here; 114 remains the later structured Literature owner |
| Model dossier/search | not owned here; 113/115 remain read-only later owners |
| Run-oriented transient working configuration | not owned here; 071b remains the sole transient run-working owner |

Readiness MUST fail if fresh exact-master evidence shows another 100c-assigned mutable Project Basis field with neither a safe existing owner nor a minimum non-duplicate seam.

### Dependency/freshness graph

`backend/app/modules/flowsheet/service.py::build_flowsheet_graph_from_connection()` remains the persisted canonical graph projection. It loads current canonical rows, resolves canonical refs, emits bounded diagnostics and enforces graph bounds. 112 MUST NOT persist a second graph.

For a draft impact preview, 112 may build only a bounded ephemeral **proposed dependency projection** from:
1. the exact parent canonical graph snapshot;
2. the ordered draft operations;
3. proposed additions/removals/changed source bindings derivable from those operations.

The projection must reuse the current canonical ref parser/resolver and graph bounds where applicable. It must identify all proposed edge deltas and diagnostics. Unsupported/unrepresentable proposed relationships make impact `incomplete`; they never collapse to `no impact`.

### Simulation runs / result binding

`SimulationRunCreate` and the `simulation_runs` persistence currently bind a run to workspace and optional `model_version_id`, but contain no exact Project Knowledge working-revision identity. That is insufficient to prove that evidence from one sibling/chained working revision is valid for another even if both share a model version.

V0 MUST add the minimum nullable provenance binding from produced validation/recomputation evidence to the exact 112 working revision. For simulation runs, the preferred minimum seam is an additive nullable `project_knowledge_revision_id` (name may be adjusted by readiness only if an existing generic exact-revision provenance field is proven equivalent). Existing historical rows remain valid history with a null binding and are never retroactively attributed to a working revision.

Any domain-specific run/evidence/artifact consumed as mandatory reconciliation evidence must expose an equivalent exact producing/using working-revision ref, directly or through an existing immutable provenance chain. If an exact ref cannot be proven, that evidence is inadmissible for reconciliation of the working revision.

## V0 persistent coordination model

Add one narrowly-scoped Project Knowledge coordination schema. Names below are normative semantic roles; readiness may adjust SQL names only to fit current schema conventions without changing ownership.

### `project_knowledge_revisions`

One immutable identity per accepted working revision and one immutable identity per reconciled snapshot reference needed by 112 coordination.

Required fields:
- `id` — server-generated immutable id;
- `workspace_id`;
- `parent_revision_id` — exact reconciled or accepted-working parent identity;
- `parent_kind` — `reconciled` or `working`;
- `state` — at minimum `working`, `discarded`, `superseded`, `reconciled`;
- `change_set_digest` — digest of the ordered accepted operations;
- `created_at`;
- `accepted_at`;
- `superseded_by_revision_id` nullable;
- immutable creator/origin metadata sufficient to distinguish operator-approved from proposal-derived intent without storing model prose as authority.

This table stores coordination identity and immutable intent lineage only. It does not duplicate canonical values as a second Project database.

### `project_knowledge_drafts`

A mutable server-owned bounded draft intent before approval.

Required fields:
- `id`, `workspace_id`;
- exact `parent_revision_id` / `parent_kind`;
- `revision_token` or `updated_at` for draft CAS;
- ordered typed operations as bounded JSON or child rows;
- exact owner refs and expected owner revision tokens per operation;
- proposal identity/origin where applicable;
- `created_at`, `updated_at`.

Draft payload bounds MUST be explicit and tested. The browser never authors canonical revision identity.

### `project_knowledge_validation`

Immutable validation/revalidation evidence bound to one exact working revision.

Required fields:
- exact `working_revision_id`;
- criterion/rule identity and version;
- validator identity/version;
- exact source refs/revisions;
- exact run/evidence/artifact refs where used;
- outcome `pass`, `fail`, `no_material_effect`, or `recomputation_required`;
- for recomputation-required, required domain/chain and exact missing evidence contract;
- digest of the validated input basis;
- created_at.

Evidence rows are append-only. A newer row never rewrites prior evidence.

### `project_knowledge_reconciliation_requests`

Immutable idempotent request/outcome record for final reconciliation.

Required fields:
- server-owned request id / idempotency key;
- workspace id;
- exact working revision id;
- exact still-current reconciled target identity/digest;
- known-fail acknowledgement/policy identity where applicable;
- request digest;
- state/outcome;
- created/completed timestamps;
- failure code/detail sufficient for deterministic retry/audit without secrets.

Canonical writes from a successful reconciliation are not duplicated here; the request records coordination/audit only.

## Draft operation contract

Each ordered draft operation MUST include:
- canonical owner kind and id;
- exact expected owner revision token;
- operation kind (`update`, supported lifecycle transition, or the minimum model/assumption/requirement mutation kind accepted by readiness);
- bounded field delta;
- proposal id/origin if the operation derives from 040/Jarvis/model output;
- source/provenance refs required by the canonical owner;
- dependency-edge delta if the changed field affects source/dependency bindings and the delta can be represented canonically.

Unsupported fields fail at draft validation; they are not silently carried as generic JSON to reconciliation.

## API/service boundary

Add one `project_knowledge` backend module/service owning coordination only. Exact route names may follow current conventions, but the capability boundary MUST include:

1. **create/read/update draft** against an exact parent and draft CAS token;
2. **impact preview** over exact parent + ordered proposed projection;
3. **approve exact draft** into one immutable working revision;
4. **read/list working revision history/chain** for the current workspace;
5. **validate/revalidate** using deterministic zero-rerun logic where sufficient exact outputs exist, otherwise return truthful recomputation-required state;
6. **bind completed domain validation evidence** only after exact working-revision/source/run/evidence checks;
7. **discard/supersede/rebase/explicit branch** without deleting history;
8. **final reconcile** one exact terminally validated working revision with idempotent request semantics.

No endpoint performs provider/LLM calls. No endpoint invokes a solver inside the canonical reconciliation transaction.

## Approve-all transaction semantics

`Approve all` is not final reconciliation.

Approval MUST:
1. begin one SQLite write transaction;
2. reread the draft, exact parent identity and every referenced canonical owner row;
3. reject stale owner tokens, stale parent, changed lifecycle/replacement state, proposal eligibility drift, malformed/incomplete proposed dependency projection or exceeded bounds;
4. materialize one immutable working-revision coordination row plus the exact accepted ordered change set;
5. commit without mutating reconciled canonical records;
6. trigger only deterministic zero-rerun validation that is safe outside any canonical-final-reconciliation mutation boundary, recording exact working-revision-bound evidence.

Same exact idempotent approval retry returns the existing working revision. Conflicting request reuse fails closed.

## Proposed-state impact preview

Impact preview MUST operate on the proposed state, not merely the persisted graph.

Required algorithmic contract:
1. load the bounded exact current 050 graph under one read snapshot;
2. verify parent/owner tokens;
3. derive explicit edge delta from the ordered draft operations;
4. apply the delta ephemerally to the in-memory projection;
5. traverse the projected dependency graph using current 050 semantics/bounds;
6. return affected refs, required validation/recomputation contracts, diagnostics, completeness and a digest bound to parent + draft revision token + owner tokens + projected edge delta;
7. approval/reconciliation rejects the preview if any bound identity has drifted.

Mandatory deterministic cases:
- dependency source changes A -> B: B becomes current impact source, obsolete A-derived impact is not represented as current projected truth;
- add edge;
- remove edge;
- stale parent/owner after preview;
- dangling/unrepresentable proposed edge -> incomplete impact, never `no impact`;
- graph bound exhaustion -> incomplete/rejected, never truncated success.

## Working revision and chaining semantics

An accepted working revision is immutable.

- Default continuation selects the exact currently selected/latest accepted working revision as parent.
- Deliberate branching requires the client to select an exact historical reconciled/working parent; server verifies it belongs to the workspace and remains a valid branch basis.
- Rebase creates a successor draft/revision; it never rewrites the original branch.
- Discard/supersede is an immutable terminal outcome and leaves reconciled canonical truth unchanged.
- Two siblings may share a model version and still be distinct validation authorities because their working-revision identities and input bases differ.

## Validation and recomputation contract

### Zero-rerun deterministic validation

When exact stored outputs are sufficient, 112 invokes accepted deterministic criterion logic and writes a new validation row bound to:
- exact working revision;
- changed criterion/rule and version;
- exact input/source refs and revision tokens;
- exact stored output/run/evidence identities;
- validator/version;
- outcome.

A generic `needs_revalidation=true` flag is insufficient acceptance evidence.

### Recomputation-required

If exact outputs are insufficient, validation state is `recomputation_required` with:
- required domain (`Process`, `BLUECAD`, or another already-authorized owner);
- exact working revision;
- required input/criterion contract;
- exact missing or stale evidence refs;
- operator navigation target.

The `Validate` action deep-links/routes to the canonical domain owner with the exact working revision selected. 112 does not pretend that navigation completed the calculation.

### Evidence admission

Evidence is admissible for final reconciliation only when the server proves:
- same workspace;
- same exact working revision;
- same required source/input basis digest;
- same criterion/rule identity/version;
- same validator identity/version;
- exact producing run/evidence/artifact refs;
- no stale owner/replacement/source drift.

Mandatory test: two sibling/chained revisions share one `model_version_id` but differ in working inputs; evidence produced for revision A MUST be rejected for revision B.

## Final reconciliation

Final reconciliation is a separate explicit promotion operation and is the only 112 transition that changes current canonical Project Basis/model truth.

Preconditions:
- exact working revision exists and is not discarded/superseded;
- exact reconciled target is still current;
- every canonical owner expected token still matches the basis accepted by the working revision or a deliberate rebase has produced a successor;
- every mandatory validation contract is terminal and exactly bound;
- unresolved/missing/incomplete evidence blocks ordinary reconciliation;
- known mandatory FAIL is preserved and requires explicit acknowledgement/policy identity.

Transaction contract:
1. create/read the immutable reconciliation request and verify idempotency;
2. open one SQLite `BEGIN IMMEDIATE` transaction at the coordination boundary;
3. reread all owner rows, lifecycle/replacement/proposal eligibility, parent/target identity and validation bindings;
4. call transaction-capable canonical owner primitives for Parameter, Requirement, Assumption and ModelSpec mutations; do not call protected HTTP routes;
5. apply required canonical audit/replacement/freshness effects using current owners;
6. mark the exact 112 revision reconciled and commit all canonical effects together;
7. on any exception, roll back every canonical mutation/success effect;
8. outside the rolled-back transaction (or via a proven savepoint pattern), persist immutable failed-request outcome so a response-loss retry is deterministic and auditable.

No provider, solver, filesystem or network side effect occurs inside this transaction.

## Frontend scope

Activate only existing canonical Project Basis / Models composition. No new peer Project page or redesign.

Required UI behavior:
- show current reconciled revision identity and selected working parent/chain;
- stage only server-supported fields;
- distinguish operator-authored intent from proposal/model/Jarvis-originated intent;
- show exact expected owner revisions and explicit stale/conflict states;
- preview proposed-state impact before approval;
- `Approve all` applies exactly the displayed batch into one inspectable working revision and never implies final reconciliation;
- display bound PASS/FAIL/no-material-effect or recomputation-required state;
- `Validate` navigates to the truthful canonical domain owner with exact working-revision context;
- allow continuation, deliberate branch, discard/supersede and rebase without rewriting history;
- final reconciliation is a separate explicit action;
- known mandatory FAIL promotion requires explicit acknowledgement/policy UI;
- after every protected transition reload server truth; frontend state is never canonical.

No 113 dossier, 114 literature, 115 search, 121 Jarvis domain action, new global visual identity, generic solver UI or alternate client-side working store.

## Security / provider / budget boundary

112 is local deterministic repository/product state work.
- no provider calls are required;
- `route_class="auto"` remains non-external;
- no new credentials or external account;
- no secret-bearing fields in coordination/audit tables or API responses;
- Product AI remains behind existing `run_ai_task` + `ai_jobs`; model/Jarvis output enters 112 only as proposal-originated bounded intent and cannot reconcile itself;
- no paid-AI or budget behavior changes.

## Failure modes that MUST be deterministic

1. wrong workspace owner ref;
2. stale draft token;
3. stale Parameter/Requirement/Assumption/ModelSpec owner token;
4. lifecycle/replacement/proposal eligibility drift;
5. stale parent before approval;
6. stale reconciled target before final reconciliation;
7. competing approval/final-reconciliation retry;
8. sibling branch evidence substitution;
9. incomplete/dangling/unrepresentable proposed dependency edge;
10. graph bound exhaustion;
11. mandatory evidence missing or stale;
12. known FAIL without required acknowledgement;
13. unsupported field kind;
14. domain run exists but has no provable exact working-revision binding;
15. canonical mutation fails midway: entire reconciliation rolls back, immutable failure outcome remains;
16. workspace switch or stale frontend response;
17. proposal rejected/promoted differently after draft preview;
18. source/rule/validator identity changes after validation;
19. response loss followed by same idempotent retry;
20. conflicting reuse of an idempotency key.

None may produce partial canonical truth, fabricated success, silent rebase, implicit `no impact`, or frontend-only acceptance.

## Implementation shape and minimum-necessary file ownership

Expected bounded implementation areas, subject to readiness exact-head confirmation:
- new `backend/app/modules/project_knowledge/` models/service/routes for coordination only;
- minimum additive schema/migration registration in current core schema mechanism;
- small transaction-capable internal owner seams in `backend/app/modules/modeling/parameter_lifecycle.py` and/or `service.py` for Requirement/Assumption/ModelSpec protected mutations while preserving their canonical tables;
- minimum additive exact working-revision provenance binding for simulation/domain result evidence where current provenance cannot already prove it;
- reuse/refactor of flowsheet graph helpers for an in-memory proposed-edge projection, without persisted graph duplication;
- bounded API client/types and existing Project Basis/Models UI activation;
- deterministic backend/frontend tests.

Do not add a generic workflow engine, event-sourcing framework, second model store, second dependency graph, generic project database, provider integration, background queue, WebSocket channel or new state-management framework.

## Deterministic acceptance tests

### Owner/CAS and atomicity

- Parameter update uses existing 098 CAS semantics and rejects stale/lifecycle-invalid rows.
- Requirement working mutation is workspace-scoped and stale-protected; two concurrent expected revisions cannot both reconcile.
- Assumption and ModelSpec supported V0 mutations are stale-protected and audited.
- final reconciliation of multiple supported owners is all-or-nothing under injected failure after at least one attempted owner mutation.
- failed reconciliation records immutable failure evidence after rollback.

### Draft / working revision

- approval does not mutate reconciled canonical rows;
- same approval retry returns the same working revision;
- conflicting idempotency reuse rejects;
- successor defaults to exact selected working parent;
- deliberate branch preserves both histories;
- discard/supersede preserves prior rows and reconciled truth.

### Proposed impact

- A -> B dependency change updates projected impact correctly;
- add edge and remove edge cases;
- stale preview after owner/parent drift rejects;
- incomplete/dangling/bound-exhausted proposed graph never returns complete `no impact`.

### Validation binding

- zero-rerun criterion executes against exact stored outputs and records rule/source/validator/working-revision refs;
- sibling/chained revisions sharing a model version cannot reuse each other's validation/run evidence;
- recomputation-required returns domain + exact revision + missing evidence contract;
- a completed run with wrong/no working revision binding is rejected;
- changed source/rule/validator invalidates prior evidence.

### Reconciliation

- unresolved mandatory validation blocks;
- PASS reconciles;
- known mandatory FAIL without acknowledgement blocks;
- known mandatory FAIL with accepted acknowledgement/policy may reconcile while preserving FAIL evidence;
- reconciled target drift blocks and requires deliberate rebase;
- competing final reconciliation from the same target cannot both succeed;
- response-loss retry returns the recorded outcome;
- success reloads canonical current truth and preserves immutable working/history records.

### Frontend

- only supported fields are editable;
- exact revision/working chain and stale/conflict state are visible;
- Approve all and Final reconcile are visually/semantically distinct;
- Validate navigation carries exact working-revision context;
- known-FAIL acknowledgement is explicit;
- stale async response/workspace switch cannot mutate local canonical presentation;
- no browser/provider/filesystem direct authority is introduced.

## Required gates for a frozen implementation head

Readiness MUST enumerate the exact commands from current repository conventions. At minimum the implementation candidate requires:
- targeted backend tests for project-knowledge coordination, owner CAS/rollback, proposed graph projection and validation binding;
- existing modeling/flowsheet/freshness/MemoryStore/Jarvis regression tests affected by the touched seams;
- relevant frontend tests/typecheck/build for Project Basis/Models activation;
- standard repository CI;
- browser proof only if the implementation visibly changes interaction/layout beyond already-covered deterministic component behavior.

Independent Claude terminal review is materially useful for the frozen implementation head because 112 composes multi-owner atomic mutation, stale semantics and provenance binding. Review is advisory evidence; deterministic tests/runtime ownership remain authoritative.

## Non-goals

- no second project/model/engineering truth store;
- no replacement of 040, 042, 050, 051, 071b, 098 or 111;
- no generic solver/recompute engine;
- no 113 dossier, 114 literature, 115 search or 121 Jarvis Project actions;
- no direct model/Jarvis reconciliation authority;
- no external provider/credential/budget changes;
- no generic workflow/event-sourcing platform;
- no new peer Project page or global visual redesign;
- no retroactive fabrication of working-revision provenance for historical runs;
- no permanent compatibility layer for hypothetical consumers.

## Readiness checklist

112 may move to `ready` only after a fresh exact-master readiness audit confirms all of the following:

1. the exact-master owner audit above still matches code;
2. Requirement, Assumption and ModelSpec minimum CAS/audit seams are implementable without duplicate canonical tables;
3. Parameter composition can reuse/refactor 098 transaction-safely;
4. the minimal additive 112 coordination schema does not duplicate canonical values or dependency state;
5. simulation/domain validation evidence can be bound to exact working revision with an additive non-duplicate provenance seam;
6. proposed dependency projection can reuse current 050 graph/ref semantics ephemerally;
7. one SQLite final-reconciliation transaction can compose all V0 supported owner mutations and freshness/audit effects without provider/solver/fs/network side effects;
8. immutable failed reconciliation outcome can survive rollback/idempotent retry;
9. all 100c-assigned V0 Project Basis field classes have an explicit safe owner/disposition;
10. deterministic test seams exist for every required failure mode and acceptance test above;
11. frontend activation can reuse current Project Basis/Models composition without a second client-side canonical store;
12. no new credential/account/spend/security exception is required.

If any item fails, readiness must remain blocked/planned and record the exact gap; implementation may not begin.