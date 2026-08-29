# 112 full-spec review closure — 2026-08-29

Authority: binding amendment to `docs/specs/112-project-knowledge-core-1.md` for the full-spec planning stage. Where this closure is more specific than the full spec, this closure supersedes the earlier clause. It does not authorize runtime implementation and does not move `112` from `planned`; a separate fresh exact-master readiness decision is still required.

Reviewed full-spec head: `50a3792cd822e9a6b8d0a1b45f2fbcfbb1a2d9b2`.

This closure resolves the four material review findings on PR #429 without broadening 112 beyond the merged definition or creating a second project/model/engineering truth store.

## 1. Proposed-state impact includes the accepted working ancestor chain

The full spec's proposed dependency projection is amended as follows.

A draft whose exact parent is an accepted working revision MUST NOT start from the current reconciled 050 graph and apply only the child's edge delta. Approval does not mutate the reconciled graph, so doing that would lose accepted-but-unreconciled ancestor changes.

The projection basis is instead the exact cumulative working state for the selected parent:

1. load the bounded exact current reconciled 050 graph under one read snapshot;
2. resolve the selected parent and walk its immutable parent chain back to the exact reconciled ancestor, rejecting cycles, missing parents, wrong-workspace refs, discarded/superseded invalid bases, or bound exhaustion;
3. replay, in ancestor-to-descendant order, every accepted working ancestor's exact ordered dependency/source-binding deltas onto an in-memory projection; equivalently, an implementation may load a persisted immutable cumulative digest/materialization only if readiness proves it is derivable from and exactly bound to that same chain and is not a second dependency truth store;
4. verify the resulting cumulative-parent digest, parent identity, owner revision tokens and proposed-edge basis;
5. derive and apply the current draft's explicit edge delta;
6. traverse the resulting projected graph with existing 050 canonical-ref semantics and bounds;
7. return affected refs, validation/recomputation contracts, diagnostics, completeness, and a digest bound to the reconciled base + complete accepted ancestor chain + current draft revision token + owner tokens + all applied edge deltas.

Approval and final reconciliation reject any preview when the reconciled base, ancestor chain, selected parent, owner token, or cumulative digest has drifted.

Additional mandatory deterministic tests:

- parent accepted revision changes dependency `A -> B`, child makes an unrelated edit: child preview preserves `B` as current projected truth and does not resurrect `A`;
- two accepted ancestors each change different edges: child preview includes both deltas in exact lineage order;
- deliberate branch from an older accepted parent excludes changes that exist only on a sibling branch;
- missing/cyclic/wrong-workspace/over-bound ancestor chain fails closed as incomplete/rejected, never as `no impact`.

This amendment supersedes the original proposed-impact algorithm wherever that algorithm could be read as applying only the current draft delta to the reconciled graph.

## 2. Complete V0 disposition for every accepted Project Basis field class

The accepted operator interaction contract assigns Project Basis ownership of:

- project objective/question;
- requirements;
- acceptance criteria;
- stable constraints;
- global decisions;
- boundary conditions;
- standards/regulations;
- resource/capability constraints.

The full spec is amended to dispose every class explicitly. V0 MUST use existing canonical owners and the minimum additive fields/seams below; it may not defer these accepted classes to unspecified future work.

| Accepted Project Basis class | Canonical V0 owner / minimum seam |
| --- | --- |
| Project objective/question | existing `requirements` canonical table, with one additive bounded `basis_kind` discriminator; no peer objective table |
| Requirement | existing `requirements`, `basis_kind=requirement`; protected workspace/CAS/audit mutation seam |
| Acceptance criterion | existing `requirements`, `basis_kind=acceptance_criterion`; protected workspace/CAS/audit mutation seam; deterministic rule/target representation must reuse current fields where sufficient or add only the minimum typed metadata required by readiness |
| Stable constraint | existing `requirements`, `basis_kind=stable_constraint`; protected workspace/CAS/audit mutation seam |
| Boundary condition | existing `requirements`, `basis_kind=boundary_condition`; protected workspace/CAS/audit mutation seam |
| Standard/regulation | existing `requirements`, `basis_kind=standard_regulation`; protected workspace/CAS/audit mutation seam; source/provenance remains required where the canonical owner supports or readiness minimally extends it |
| Resource/capability constraint | existing `requirements`, `basis_kind=resource_capability_constraint`; protected workspace/CAS/audit mutation seam |
| Global decision | existing `decisions` canonical table; add the minimum workspace-scoped stale-protected CAS/audit internal update seam needed by 112; no `project_decisions` table |

`basis_kind` is an additive classification on the existing Requirement identity, not a second truth store. Existing historical Requirement rows may default/migrate to `requirement`; readiness must choose the additive migration shape and prove compatibility with existing callers and tests.

The existing `DecisionCreate`/`DecisionRead` identity remains canonical. Because current code has no Decision update model/seam, readiness must prove the minimum transaction-capable `Decision` mutation primitive with workspace scope, expected owner revision token, immutable audit evidence, and caller-owned transaction support before 112 can become `ready`.

The model-specific field classes already covered by the full spec remain unchanged:

- Parameter values/units/metadata -> existing `parameters` + 098;
- Assumptions -> existing `assumptions` + minimum CAS/audit seam;
- Model definition/engineering question/scope/summaries/method-bearing configuration -> existing `model_specs` + minimum CAS/audit/version seam;
- transient run working configuration -> 071b, not 112;
- Literature -> 114;
- dossier/search -> 113/115.

Readiness checklist item 9 is strengthened: readiness MUST verify that every accepted Project Basis class in the table above has its exact canonical owner, additive representation, mutation/CAS/audit route, transaction composition route, frontend field mapping, and deterministic tests named. Any missing class keeps 112 `planned`/not ready.

Required deterministic tests are extended to cover stale/wrong-workspace/concurrent mutation for each mutable Requirement `basis_kind` and Global Decision, plus migration/read compatibility for historical requirements.

This amendment supersedes the earlier `Remaining Project Basis field classes` table insofar as that table omitted accepted classes or treated Global Decisions as read-only.

## 3. Approval has a persistent unique retry identity

The full spec's claim that an identical approval retry returns the existing working revision is amended with an explicit persistence contract.

Add one coordination-only immutable/idempotent approval request/outcome record, preferably `project_knowledge_approval_requests` (SQL naming may change only for repository convention without semantic change).

Required fields:

- server-owned approval request/idempotency key;
- workspace id;
- exact draft id;
- exact draft revision token;
- exact parent revision id/kind;
- request digest covering the exact ordered draft operations and bound owner tokens;
- state/outcome;
- resulting working revision id nullable;
- created/completed timestamps;
- failure code/detail sufficient for deterministic retry/audit without secrets.

Required uniqueness/idempotency semantics:

- one exact `(workspace, draft_id, draft_revision_token, approval_request_key)` identity is unique;
- same key + same exact request digest returns the already-recorded terminal outcome and, on success, the same working revision id;
- same key with a different request digest fails closed;
- the successful approval transaction creates/locks the approval request, materializes exactly one working revision, records the request's successful terminal outcome and resulting revision id, and commits them atomically;
- a response loss after commit therefore cannot create a duplicate working revision on retry;
- a failed approval that rolls back working-revision creation records an immutable failed request outcome outside the rolled-back mutation transaction, or through an equivalently proven savepoint pattern, so retry behavior is deterministic.

Additional mandatory tests:

- response lost after successful approval commit -> retry returns the same working revision id;
- concurrent identical approval requests -> at most one working revision is created;
- conflicting key reuse -> rejected;
- failed stale approval -> no working revision is created and exact retry returns the recorded failure unless a new request/rebase is deliberately issued.

This approval-request table stores coordination/idempotency only and does not duplicate canonical Project Basis values.

## 4. Successful final reconciliation records request outcome atomically

The full spec's final-reconciliation transaction contract is amended so successful request completion is part of the same canonical transaction.

The normative success path is:

1. create/read and lock the immutable reconciliation request; verify exact idempotency key/digest and reject conflicting reuse;
2. open/hold the one SQLite `BEGIN IMMEDIATE` coordination transaction;
3. reread all owner rows, lifecycle/replacement/proposal eligibility, exact working parent/target identity and validation bindings;
4. call transaction-capable canonical owner primitives for every supported Parameter, Requirement, Assumption, ModelSpec and Global Decision mutation; do not call protected HTTP routes;
5. apply required canonical audit/replacement/freshness effects using current owners;
6. mark the exact 112 working revision reconciled;
7. mark the same reconciliation request terminal `success`, bind its resulting reconciled revision/target identity or digest, and record completion timestamp;
8. commit steps 3-7 atomically;
9. only after that commit may the response be returned.

On any exception before commit, all canonical success effects, working-revision reconciliation state, and success-request outcome roll back together. The immutable failed-request outcome is then persisted outside the rolled-back transaction (or by an equivalently proven savepoint design), as already required by the full spec.

Additional mandatory tests:

- injected crash/failure after owner mutations but before request-success update -> transaction rolls back all canonical mutations;
- injected failure after request-success update but before commit -> transaction rolls back request success and canonical mutations together;
- response loss after committed success -> retry reads the already-terminal success outcome and does not reapply canonical mutations;
- no state exists in which canonical truth is committed while the corresponding reconciliation request remains pending/unknown.

This amendment supersedes the original success transaction step that could be read as committing immediately after marking only the working revision reconciled.

## Readiness consequence

PR #429 remains planning-only. Before readiness may accept 112, the fresh exact-master audit must explicitly verify all four closure areas above in addition to the original full-spec checklist:

1. cumulative accepted-ancestor projection is implementable with current 050/ref bounds without persisting a second graph;
2. every accepted Project Basis field class has the exact non-duplicate owner/additive seam and transaction-capable protected mutation route stated above;
3. approval request/outcome persistence can guarantee response-loss idempotency and exactly-one working revision;
4. reconciliation request success can be committed atomically with canonical owner mutations and revision reconciliation state.

If any proof fails, 112 remains not ready and the readiness record must name the exact gap rather than weakening the contract.