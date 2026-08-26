# PD-07 — Model change validation and reconciliation

Status: future product direction; not implementation authority.

## Purpose

Define how JarvisOS should handle accepted project/model changes without leaving affected model versions indefinitely in a weak generic `stale` state, while preserving deterministic engineering validation, explicit promotion, reversible iteration, and inspectable lineage.

This contract complements PD-03. It does not authorize runtime implementation.

# 1. Change impact must be classified, not treated uniformly

When an accepted Project Basis or model-level change affects an existing model/version, JarvisOS must determine whether the existing stored outputs are sufficient to evaluate the new condition or whether authoritative calculations must actually be rerun.

The product must distinguish at least these cases.

## 1.1 Deterministically re-evaluable without rerunning the model

Examples include a changed acceptance threshold, requirement, comparison rule, or other condition that can be evaluated against exact already-stored outputs/evidence without changing the model calculation itself.

Required behavior:

- do not leave the model merely `stale`;
- immediately run the deterministic acceptance/validation logic against the exact stored outputs and the new accepted condition;
- record new validation evidence bound to the changed rule/basis revision and the exact source outputs;
- surface the resulting current state such as PASS/FAIL/DEGRADED according to the future authoritative validation contract;
- preserve the old validation evidence as historical evidence for the previous basis/revision.

A change in acceptance criteria is not, by itself, a reason to rerun an expensive solver if all inputs needed to evaluate the new criterion already exist.

## 1.2 Recalculation required

If the accepted change modifies an input, equation, method, geometry, Process configuration, BLUECAD configuration, property basis, boundary condition, or other dependency that can change authoritative outputs, the previous outputs are no longer sufficient.

Required behavior:

- mark the affected working/model revision explicitly as requiring validation/recalculation; `STALE` may be used only with this precise meaning;
- surface the reason and affected calculation/domain;
- expose a clear `Validate` action beside the stale/recalculation-required state;
- `Validate` eventually launches all deterministic calculations required to produce a complete current validation state for that change set;
- until a direct batch-validation capability exists, the first frontend may deep-link the user to the relevant `Design > Process` or `Design > BLUECAD` workspace with the affected working revision selected and the required action/context visible;
- after deterministic calculations finish, replace unresolved stale state with the actual validation outcomes and exact run/evidence references.

Do not use `stale` as a terminal informational badge when JarvisOS already has enough information to deterministically resolve the impact.

# 2. Jarvis proposals and one-click acceptance

Jarvis may prepare multiple related changes across Project Basis, model definition, assumptions, parameters, requirements, Process/BLUECAD references, or other canonical records.

The UI must support both individual review and a deliberate batch action conceptually equivalent to:

`Approve all`

Required semantics:

- the button applies only to the explicitly presented current proposal/change set;
- the user must be able to inspect the proposed records and impact before approval;
- approval must not silently overwrite the currently reconciled model revision in place;
- approved changes become an inspectable working revision/change branch with provenance to the proposal set and parent canonical revision;
- any deterministic validation that can be performed immediately should run automatically after approval;
- recalculation-required dependencies enter the explicit validation-required state described above.

`Approve all` is an authority shortcut for a known bounded change set, not blanket standing permission for Jarvis to mutate future records.

# 3. Working model revisions

JarvisOS should support a lightweight engineering analogue of a pull-request branch for model development.

Example user-facing progression:

`v13` — current reconciled model  
`v13.01` — first accepted working change set  
`v13.02` — subsequent accepted modification while testing  
`v13.03` — later working revision

These working revision labels are intended to let the user test, validate, compare and continue editing without prematurely replacing the current reconciled model.

Required semantics:

- every working revision has an exact parent and exact change set;
- later working revisions derive from the immediately previous accepted working revision unless the user explicitly branches from another exact revision;
- runs, artifacts, validation evidence, assumptions, parameters and source references remain bound to the exact revision that produced/used them;
- a working revision may be discarded without deleting the reconciled parent or historical evidence;
- Jarvis may propose a working revision but only an authorized user/policy action creates/promotes it.

The decimal notation is a product-facing convention, not permission to use floating-point numbers as version identity. Backend identity must be stable and exact.

# 4. Reconciliation / promotion

When the user is satisfied that the working revision represents the intended change, JarvisOS exposes a deliberate reconciliation action conceptually equivalent to:

`Reconcile` / `Make current`

Reconciliation must:

1. bind the exact working revision being promoted;
2. require all mandatory recalculation/validation work to have reached a terminal known state; unresolved `STALE`, unknown or missing required evidence blocks ordinary reconciliation;
3. preserve actual PASS/FAIL results rather than requiring every criterion to pass merely to record a known current engineering state;
4. if mandatory acceptance criteria are known to FAIL, require explicit acknowledgement/policy rather than hiding the failure;
5. preserve the previous reconciled revision as immutable historical lineage;
6. make the selected working revision the new current reconciled state atomically with its provenance/lineage references.

The UI may continue to present the stable model family label as `v13` / `v13 · Updated` if that is the clearest mental model, but the backend must not destroy the prior canonical snapshot. Internally, reconciled revisions require immutable exact identity so historical results remain reproducible.

# 5. Project Basis propagation

An accepted Project Basis change must produce an explicit dependency-impact set over affected model revisions.

For each affected model/revision JarvisOS must classify the impact as:

- `re-evaluate existing outputs` — deterministic validation can run immediately;
- `recalculate Process`;
- `recalculate BLUECAD`;
- `recalculate multiple domains`;
- `no material effect`, with deterministic evidence/reason where the dependency graph can prove this.

The UI should summarize the impact before approval and then automatically execute all zero-rerun deterministic evaluations after approval.

# 6. UX direction

Memory pages remain overview-first/detail-on-demand as defined by PD-03.

Useful compact states include, conceptually:

`CURRENT`  
`WORKING v13.02`  
`VALIDATING`  
`STALE · Process recalculation required   [Validate]`  
`FAIL · evaluated against PB-08`  
`PASS · evaluated against PB-08`

Do not rely on color alone.

A model dossier should make it obvious which exact working/reconciled revision is selected and which basis revision, runs and evidence its validation state refers to.

# 7. Future implementation boundary

A future backend specification must determine how to implement this behavior using/expanding existing canonical proposal, promotion, replacement, freshness/invalidation, run, evidence and model-version infrastructure rather than creating a second competing state system.

Candidate future capabilities include:

- deterministic impact classifier over dependency/freshness relations;
- immediate re-evaluation jobs for criterion-only changes;
- model working-revision/change-set domain;
- batch proposal approval;
- validation orchestration over Process/BLUECAD/evaluator dependencies;
- atomic reconciliation/promotion with immutable lineage;
- frontend deep links to current Process/BLUECAD validation until one-click validation orchestration is implemented.

The future specification must explicitly reconcile this contract with existing freshness invalidation and model-version semantics before implementation.

# 8. Hard lines

- No generic indefinite `stale` state when the new condition can already be evaluated deterministically from stored outputs.
- No expensive model rerun solely because an acceptance criterion changed if existing authoritative outputs are sufficient.
- No silent in-place overwrite of the reconciled model when approving Jarvis proposals.
- No `Approve all` as perpetual autonomous mutation permission.
- No reconciliation that destroys previous exact model snapshots, run evidence or provenance.
- No model/LLM confidence replacing deterministic validation.
- No frontend-only invented validation state.
