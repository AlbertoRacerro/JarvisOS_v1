# 112 full-spec review closure — 2026-08-29

Authority: binding amendment to `docs/specs/112-project-knowledge-core-1.md` for the full-spec planning stage. Where this closure is more specific than the full spec, this closure supersedes the earlier clause. It does not authorize runtime implementation and does not move `112` from `planned`; a separate fresh exact-master readiness decision is still required.

Reviewed full-spec head: `50a3792cd822e9a6b8d0a1b45f2fbcfbb1a2d9b2`.

This closure resolves the material review findings on PR #429 without broadening 112 beyond the merged definition or creating a second project/model/engineering truth store.

## 1. Proposed-state impact includes the accepted working ancestor chain

A draft whose exact parent is an accepted working revision MUST project the complete accepted ancestor chain before applying the child's delta. Approval does not mutate the canonical 050 graph, so starting from reconciled truth plus only the child delta would lose accepted-but-unreconciled changes.

The projection basis is:
1. load the bounded exact current reconciled 050 graph under one read snapshot;
2. resolve the selected parent and walk its immutable parent chain back to the exact reconciled ancestor, rejecting cycles, missing parents, wrong-workspace refs, discarded/superseded invalid bases, or bound exhaustion;
3. replay ancestor-to-descendant every accepted working ancestor's exact ordered dependency/source-binding deltas onto an in-memory projection; an immutable cumulative materialization is acceptable only if readiness proves it is derivable from and exactly bound to that chain and is not a second dependency truth store;
4. verify cumulative-parent digest, parent identity, owner revision tokens and proposed-edge basis;
5. apply the current draft's explicit edge delta;
6. traverse the projected graph with existing 050 canonical-ref semantics and bounds;
7. return affected refs, validation/recomputation contracts, diagnostics, completeness, and a digest bound to reconciled base + complete ancestor chain + current draft token + owner tokens + applied deltas.

Approval and final reconciliation reject any preview when the reconciled base, ancestor chain, selected parent, owner token, or cumulative digest drifted.

Mandatory tests include parent `A -> B` plus unrelated child edit, two accepted ancestors with distinct edge changes, deliberate branch from an older parent excluding sibling-only changes, and missing/cyclic/wrong-workspace/over-bound chains failing closed.

## 2. Complete V0 disposition for every accepted Project Basis field class

V0 uses existing canonical owners and minimum additive seams:

| Accepted Project Basis class | Canonical V0 owner / minimum seam |
| --- | --- |
| Project objective/question | existing `requirements` plus bounded `basis_kind`; no peer objective table |
| Requirement | existing `requirements`, `basis_kind=requirement`; protected workspace/CAS/audit mutation seam |
| Acceptance criterion | existing `requirements`, `basis_kind=acceptance_criterion`; protected workspace/CAS/audit seam and minimum typed criterion metadata only if current fields are insufficient |
| Stable constraint | existing `requirements`, `basis_kind=stable_constraint`; protected workspace/CAS/audit seam |
| Boundary condition | existing `requirements`, `basis_kind=boundary_condition`; protected workspace/CAS/audit seam |
| Standard/regulation | existing `requirements`, `basis_kind=standard_regulation`; protected workspace/CAS/audit seam with provenance where supported/minimally extended |
| Resource/capability constraint | existing `requirements`, `basis_kind=resource_capability_constraint`; protected workspace/CAS/audit seam |
| Global decision | existing `decisions`; minimum workspace-scoped stale-protected CAS/audit internal update seam; no peer decision table |

`basis_kind` classifies the existing Requirement identity and does not create a second truth store. Historical rows default/migrate compatibly to `requirement`. Readiness must prove the migration, caller compatibility, transaction-capable Decision mutation, frontend mapping, and stale/wrong-workspace/concurrent tests for every mutable class.

Model-specific classes remain: Parameters -> existing `parameters` + 098; Assumptions -> existing `assumptions` + minimum CAS/audit seam; model definition/question/scope/summaries/method-bearing configuration -> existing `model_specs` + minimum CAS/audit/version seam; transient run config -> 071b; Literature -> 114; dossier/search -> 113/115.

## 3. Approval has a persistent unique retry identity

Add one coordination-only immutable/idempotent approval request/outcome record (repository-conventional SQL name permitted) containing server-owned request key, workspace, exact draft id/token, exact parent id/kind, request digest over ordered operations and owner tokens, state/outcome, nullable resulting working revision, timestamps, and bounded non-secret failure detail.

One exact `(workspace, draft_id, draft_revision_token, approval_request_key)` identity is unique. Same key + same digest returns the recorded terminal outcome and same working revision; conflicting reuse fails closed. Successful approval atomically creates/locks the request, materializes exactly one working revision, records success/result id, and commits. Failed approval preserves an immutable failure outcome outside the rolled-back mutation transaction or via an equivalently proven savepoint design.

Mandatory tests cover response loss after success, concurrent identical approvals producing at most one revision, conflicting key reuse, and deterministic stale-failure retry.

## 4. Successful final reconciliation records request outcome atomically

The normative success path is:
1. create/read and lock the immutable reconciliation request and verify exact key/digest;
2. open/hold one SQLite `BEGIN IMMEDIATE` coordination transaction;
3. reread owner rows, lifecycle/replacement/proposal eligibility, exact working parent/target identity and validation bindings;
4. call transaction-capable canonical owner primitives for supported Parameter, Requirement, Assumption, ModelSpec and Global Decision mutations, never protected HTTP routes;
5. apply required canonical audit/replacement/freshness effects using current owners;
6. mark the exact 112 working revision reconciled;
7. mark the same reconciliation request terminal `success`, bind resulting reconciled target identity/digest, and record completion time;
8. commit steps 3-7 atomically;
9. only then return the response.

Any pre-commit exception rolls back canonical effects, working-revision reconciliation state, and success-request outcome together. Failed-request evidence is persisted outside that rollback (or equivalent savepoint). Mandatory tests inject failures before/after success-request update, test response loss after committed success, and prove canonical truth cannot commit while its request remains pending/unknown.

## 5. Final reconciliation applies the complete accepted working chain

A terminal working revision whose parent is another unreconciled accepted working revision represents the cumulative accepted working state, not only its own local delta. Final reconciliation MUST therefore derive and apply the same exact ancestor-to-descendant working chain that was used to establish proposed-state impact and validation.

Before canonical mutation, the reconciliation transaction MUST:
1. resolve the terminal working revision and walk its immutable accepted parent chain back to the exact reconciled ancestor under the same bounded/cycle/workspace validity rules used by impact projection;
2. verify that the exact reconciled base, complete ancestor sequence, each revision token/change-set digest, owner tokens, projected-state digest, and mandatory validation evidence still match the terminal validated state;
3. flatten/replay the ordered operations from oldest accepted ancestor through the terminal child into one deterministic cumulative mutation plan, preserving operation order and explicit supersession semantics;
4. reject ambiguous/conflicting duplicate operations that cannot be deterministically resolved by the accepted ordered-change semantics rather than silently choosing a value;
5. apply that cumulative plan exactly once through the transaction-capable canonical owner primitives inside the atomic success transaction in section 4;
6. mark every chain member consumed by that successful reconciliation with immutable lineage/outcome evidence sufficient to prove that its changes are represented in the reconciled result, without rewriting historical working revisions.

A deliberate branch reconciles only the selected terminal revision's ancestor chain; sibling-only changes are not imported. A chain member that is discarded, superseded as an invalid base, missing, cyclic, wrong-workspace, over-bound, or whose exact digest/token no longer matches causes reconciliation to fail closed before canonical mutation.

Additional mandatory deterministic tests:
- accepted parent changes dependency/value `A -> B`, child makes an unrelated accepted change, terminal-child reconciliation commits both parent and child effects atomically;
- two accepted ancestors modify different canonical owners and the terminal child adds a third change: all three appear exactly once after reconciliation;
- child explicitly supersedes an ancestor operation on the same owner/field: deterministic ordered semantics produce the child value without double-application;
- reconciling one branch excludes sibling-only accepted changes;
- stale/missing/cyclic/wrong-workspace/over-bound ancestor chain rejects with zero canonical partial effect;
- response loss after cumulative-chain success retries to the same terminal request outcome without replaying any ancestor mutation.

This section supersedes any earlier wording that could be read as applying only the terminal working revision's local change set during final reconciliation.

## Readiness consequence

PR #429 remains planning-only. Before readiness may accept 112, the fresh exact-master audit must verify all closure obligations together: cumulative accepted-ancestor projection; complete Project Basis owner/additive seams; approval response-loss idempotency; atomic reconciliation-request success; and cumulative ancestor-chain reconciliation through current canonical owner primitives. If any proof fails, 112 remains not ready and readiness names the exact gap rather than weakening the contract.
