# 112 full-spec final closure — 2026-08-29

Authority: binding final amendment to `docs/specs/112-project-knowledge-core-1.md` and `docs/specs/112-full-spec-review-closure-2026-08-29.md` for the full-spec planning stage. Where this document is more specific, it supersedes the earlier clause. It remains planning-only: `112` stays `planned`, no runtime implementation is authorized, and a separate fresh exact-master readiness decision is mandatory.

Reviewed exact PR head before this amendment: `91ed6ca16fc32e9d490b065e8612a5c01887b666`.

Exact-master audit used for this closure additionally confirmed:
- `backend/app/modules/memory/service.py::_transition()` owns ordinary proposal lifecycle transition but opens/commits its own connection;
- `backend/app/modules/memory/service.py::promote_parameter_replacement()` owns replacement validation, supersession/lifecycle, freshness invalidation and audit, also under its own transaction;
- `requirements` and `decisions` currently have mutable in-place rows with `updated_at` and no immutable owner-version history;
- `simulation_runs.output_payload` is opaque and the prior scalar projection contract must not entangle immutable observed results with one consumer working revision.

This amendment closes the remaining material P1 gaps without creating a second live Project/model/dependency/run truth store.

## 1. Immutable reconciled snapshot manifest

A `reconciled` Project Knowledge revision MUST address an exact immutable reconstructable state. A revision id plus change-set digest is insufficient because current Requirement, Decision, Assumption, Parameter and ModelSpec owners mutate rows in place.

V0 therefore adds one coordination-history **reconciled snapshot manifest** committed atomically with every successful final reconciliation. It is historical evidence/branch basis, never mutable current truth.

The manifest MUST contain:
- immutable snapshot id, workspace id and reconciled revision id;
- exact parent reconciled snapshot id where applicable;
- exact canonical owner kind/id for every Project Basis/model record in the reconciled V0 scope;
- the owner revision token observed at reconciliation;
- a canonical bounded serialization of every field needed to reconstruct that owner's accepted V0 state, plus a digest of that serialization;
- lifecycle/replacement/proposal lineage refs needed to interpret that state;
- the bounded canonical dependency/source-binding edge set used by the 050 projection at reconciliation, plus graph digest and diagnostics/completeness identity;
- exact canonical ids allocated from provisional create operations;
- created/completed timestamp and schema/manifest version.

The serialized owner state is an immutable historical snapshot, not a peer mutable owner. It has no generic update API, no frontend write path and never replaces reads of current canonical tables. Current truth remains the canonical owner rows; the snapshot exists only because exact historical inspection, reproducibility and deliberate branching cannot otherwise survive later in-place mutation.

A deliberate branch from a historical reconciled revision MUST resolve its exact immutable snapshot manifest, reconstruct the bounded parent working projection from that manifest, and then apply new draft/working deltas. Missing, corrupt, wrong-workspace, version-unsupported or digest-mismatched snapshot evidence fails closed; the server must never silently substitute current canonical values for the requested historical basis.

Successful reconciliation MUST create the new snapshot manifest, mark the working chain consumed/reconciled, update the reconciliation request to terminal success and apply all canonical owner mutations in the same `BEGIN IMMEDIATE` transaction. A transaction may not expose a new current canonical state whose exact reconciled snapshot was not committed with it.

Mandatory tests:
- reconcile R1, then mutate/reconcile R2, and prove R1 still reconstructs the exact former values and dependency/source bindings;
- branch deliberately from R1 after R2 and prove the draft basis is R1, not current R2;
- corrupted/missing snapshot item or edge manifest rejects historical branch/inspection as incomplete rather than substituting current data;
- failure after canonical owner mutation but before snapshot success marker rolls back canonical state, snapshot, chain-consumption and request success together;
- snapshot serialization/digest is deterministic for identical canonical state.

## 2. Proposal-origin operations compose MemoryStore transactionally

Proposal-origin operations MUST pass through the existing MemoryStore promotion/replacement authority rather than merely copy the proposed value into canonical fields.

Implementation MUST extract minimum **connection-taking owner primitives** from `backend/app/modules/memory/service.py` while preserving current public wrappers:

1. an ordinary proposal transition primitive equivalent to `_transition()` that accepts the caller-owned SQLite connection, rereads the exact proposal, requires `proposed`, preserves kind-specific eligibility, updates status/promoted_at/updated_at and writes the existing Memory proposal event without committing independently;
2. a Parameter replacement-promotion primitive equivalent to the state-changing portion of `promote_parameter_replacement()` that accepts the caller connection and preserves `validate_parameter_replacement_proposal`, competing-replacement protection, superseded/accepted lifecycle transitions, `prepare_freshness_invalidation` / `persist_freshness_invalidation`, replacement lineage and `ParameterReplacementAccepted` audit without committing independently.

The existing public `_transition`/`promote_record` and `promote_parameter_replacement` behavior remains available as wrappers that open their own transaction and invoke the owner primitive. `ProjectBasisApplyService` MUST invoke the connection-taking MemoryStore primitive whenever a cumulative operation is proposal-originated.

For proposal-origin Assumption/Decision/ordinary Parameter acceptance, proposal status and canonical accepted effect are one atomic reconciliation outcome. For a configured Parameter replacement, the replacement-promotion primitive is mandatory; raw Parameter CAS/update cannot bypass it. Proposal eligibility/status is rechecked inside the reconciliation transaction.

No proposal may remain `proposed` after its value was reconciled as accepted current truth, and no proposal may be marked accepted if a later owner mutation causes the reconciliation transaction to roll back.

Mandatory tests:
- proposal-origin Assumption and Decision reconcile with proposal lifecycle/event in the same transaction;
- configured Parameter replacement uses the replacement path and persists supersession + freshness exactly once;
- inject a later owner failure after proposal transition/replacement work and prove proposal status, Parameter lifecycle, freshness rows/events, canonical owners, working-chain consumption and request success all roll back;
- response-loss retry returns the same committed promotion/replacement outcome without replay;
- a non-proposed or wrong-workspace proposal fails before canonical success.

## 3. Revision-neutral scalar result; revision-specific validation binding

The immutable admitted scalar projection MUST represent the observed result itself, not ownership by exactly one Project Knowledge working revision.

Therefore `simulation_run_scalar_results` is revision-neutral and its identity remains `UNIQUE(run_id, output_name)`. Each row stores:
- run id and workspace identity through the canonical run;
- exact output name;
- finite numeric value and exact/unitless unit representation;
- source payload digest;
- trusted extractor id/version;
- immutable created timestamp.

`project_knowledge_revision_id` is **not** a required ownership column of this scalar row. If the producing run already carries an exact working-revision provenance binding, that provenance remains part of the run/evidence chain and is verified; it does not make the scalar projection single-consumer.

The consumer binding belongs to immutable `project_knowledge_validation`: every evaluation row stores the target working revision, exact scalar-result identity, exact source run/result digest, criterion/rule/validator identity and the target working revision's validated-input/basis digest.

The same admitted scalar may therefore support separate validation rows for multiple working revisions only when the server proves that the observed output remains admissible for each target revision: same workspace, exact immutable source run/result identity, unchanged source/output digest, compatible exact input/source basis, and no changed dependency/criterion that requires recomputation. A sibling revision whose working inputs would change the observed result is rejected as stale/incompatible even though it references the same model version.

This supersedes the earlier requirement that scalar lookup itself require equality to a scalar-row `project_knowledge_revision_id`.

Mandatory tests:
- two criterion-only sibling revisions with identical admissible source basis reuse one scalar row and receive two distinct revision-bound validation rows;
- a sibling changing a source input cannot reuse that scalar and becomes `recomputation_required` or `not_evaluable/stale_target` according to the accepted validation contract;
- one scalar row remains unique per `(run_id, output_name)` and no duplicate is created per consumer revision;
- wrong workspace, payload-digest drift, unsupported extractor or incompatible basis fails closed.

## 4. Acceptance-criterion applicability and mandatory gate ownership

Whether an acceptance criterion blocks reconciliation MUST be persisted on the existing Requirement owner; it may not be inferred from prose, UI placement or presence of typed comparator fields.

For `basis_kind=acceptance_criterion`, V0 adds one bounded Requirement-owned field:

`reconciliation_gate = required | advisory`

Semantics:
- `required`: criterion belongs to the mandatory validation set whenever the proposed-state impact says it is applicable to the working revision; ordinary final reconciliation requires terminal admissible evidence for it. Machine-evaluable required criteria require `pass`, except the separately specified explicit known-FAIL acknowledgement path. `not_evaluable` remains unresolved and blocks ordinary reconciliation.
- `advisory`: criterion may be evaluated and displayed but its absence/failure alone does not block reconciliation.

The field is updated only through the same workspace-scoped stale-protected Requirement CAS/audit owner seam. It is included in owner revision identity, impact/validation digests and reconciled snapshot history. A working change that alters this field invalidates previous criterion-set/validation evidence.

Migration/default rule: historical Requirement rows default to `advisory`; the migration MUST NOT invent new blocking policy from old prose. A fresh readiness audit MUST identify any already-accepted repository authority that explicitly marks an existing criterion mandatory and migrate only such proven cases deliberately. Newly created or newly classified `basis_kind=acceptance_criterion` records MUST provide `reconciliation_gate` explicitly; the server does not infer it.

The mandatory set for one working revision is deterministic: exact active Requirement rows with `basis_kind=acceptance_criterion`, `reconciliation_gate=required`, and applicable membership under the exact proposed-state impact/revision basis. Retired criteria are excluded only through the retirement contract below; stale/incomplete applicability fails closed rather than silently dropping a required criterion.

Mandatory tests:
- required PASS satisfies its gate;
- required FAIL uses the known-FAIL acknowledgement rule and cannot silently pass;
- required `not_evaluable` blocks ordinary reconciliation;
- advisory missing/FAIL is preserved but not itself blocking;
- historical row migration does not become required without explicit accepted evidence;
- gate classification change invalidates prior validation digest;
- stale Requirement revision cannot change required/advisory state.

## 5. Existing Project Basis removal is retirement, never physical deletion

Project Basis CRUD removal of an already-canonical Requirement or Global Decision is represented in V0 as a stale-protected **retire** operation. Physical deletion of an accepted canonical owner is not authorized.

Requirements and Decisions gain the minimum owner-owned current-lifecycle field:

`basis_lifecycle_state = active | retired`

with default/migration `active` for existing rows and a nullable immutable-audit timestamp/reason if current repository conventions require it. This lifecycle is distinct from MemoryStore proposal `status`; retiring an accepted record must not masquerade as proposal rejection/supersession.

A draft `retire` operation against an existing Requirement/Decision MUST carry workspace, canonical owner id, exact expected owner revision token and bounded reason/provenance. Approval only records the working intent. Final reconciliation invokes the canonical Requirement/Decision connection-taking owner primitive inside `ProjectBasisApplyService`, CAS-checks the still-active row, marks it retired, updates owner revision/audit, and commits that change with the complete cumulative plan and snapshot.

Effects:
- retired rows remain immutable-addressable history and are excluded from the current active Project Basis projection/search/edit set unless history is requested;
- dependent/impact semantics are recomputed through the accepted proposed-state graph/freshness path; retirement never silently drops required dependency impact;
- exact historical reconciled snapshots preserve whether the owner was active or retired at that revision;
- a later reactivation is not implicitly authorized by `update`; it requires an explicit stale-protected `reactivate` operation if readiness includes it, otherwise remains a future extension;
- removing a provisional create before reconciliation still cancels/supersedes the provisional operation and creates no canonical owner.

Mandatory tests:
- retire each Requirement-backed Project Basis class and Global Decision with workspace/CAS protection;
- wrong workspace/stale token/already-retired conflict fails closed;
- retirement participates in projected dependency impact and mandatory-criterion set calculation;
- failed multi-owner reconciliation leaves the existing row active;
- successful retirement remains inspectable in historical snapshot and is excluded from current active projection;
- no implementation path physically deletes accepted Requirement/Decision rows.

## Consolidated readiness consequence

PR #429 remains planning-only. 112 cannot become `ready` until fresh exact-master readiness proves, together with the earlier full-spec/closure obligations:

1. immutable reconciled snapshot manifests are transactionally reconstructable and are historical evidence rather than a second live truth store;
2. MemoryStore ordinary proposal promotion and Parameter replacement promotion have named connection-taking owner primitives preserving current eligibility/lifecycle/freshness/audit semantics inside `ProjectBasisApplyService`;
3. scalar-result admission is revision-neutral while every validation use is exactly target-working-revision/basis bound;
4. Requirement-owned `reconciliation_gate` deterministically defines required vs advisory acceptance criteria without prose inference;
5. existing Requirement/Decision removal is stale-protected retirement, not physical deletion, and remains distinct from proposal lifecycle;
6. all earlier cumulative-chain, approval-idempotency, create/provisional-id, criterion evaluator, atomic success/failure and proposed-state impact obligations remain satisfied.

If any proof would require duplicate current truth, hidden provider/solver work, weakened CAS/proposal/lifecycle semantics, or unreconstructable historical revisions, readiness must remain not-ready and name the exact gap rather than weakening the contract.
