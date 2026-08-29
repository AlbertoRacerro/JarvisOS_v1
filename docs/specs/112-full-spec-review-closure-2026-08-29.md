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

The request key is independently unique within its workspace: `UNIQUE(workspace_id, approval_request_key)` is required. Draft id, draft revision token, parent identity and request digest are stored values checked on reuse, not part of the uniqueness scope. Reuse of the same workspace/key with the same exact draft/token/parent/digest returns the recorded terminal outcome and same working revision; reuse with any different bound value fails closed. Successful approval atomically creates/locks the request, materializes exactly one working revision, records success/result id, and commits. Failed approval preserves an immutable failure outcome outside the rolled-back mutation transaction or via an equivalently proven savepoint design.

Mandatory tests cover response loss after success, concurrent identical approvals producing at most one revision, same key against a different draft or draft revision failing closed, same key with a different digest failing closed, and deterministic stale-failure retry.

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

## 6. Freeze the 112-owned atomic apply seam

The phrase `transaction-capable canonical owner primitives` is now made executable rather than aspirational. V0 MUST introduce one 112-owned orchestration service boundary, `ProjectBasisApplyService` (repository-conventional class/module naming may differ, semantics may not), that owns **only** the final multi-owner transaction and dispatch. It is not a new truth store and may not implement owner business rules itself.

For one reconciliation request the service MUST:
1. receive the already-derived exact cumulative mutation plan plus exact workspace, target/revision/digest and idempotency identities;
2. open one caller-owned SQLite `BEGIN IMMEDIATE` transaction and retain the same connection for every owner mutation and 112 success-state mutation;
3. rerun the exact owner-token, lifecycle/replacement, proposal-eligibility and validation-binding checks inside that transaction;
4. dispatch each supported operation to a transaction-aware internal primitive owned by the canonical domain, passing the caller connection explicitly;
5. let each owner primitive perform its existing CAS/business/lifecycle/audit/freshness rules; the 112 service may sequence and aggregate but may not duplicate or weaken those rules;
6. update working-chain consumption plus the reconciliation-request terminal success in the same transaction;
7. commit once, only after every owner operation and success marker succeeds; any exception rolls back the whole mutation set.

Where an accepted current owner helper commits internally, implementation MUST perform the minimum refactor needed to expose a connection-taking primitive and preserve the existing public helper as a compatibility wrapper that opens/commits its own transaction. In particular, Parameter replacement/promotion behavior currently encapsulated by MemoryStore/098 may not be called through an auto-committing wrapper from `ProjectBasisApplyService`; its validation, replacement lineage, lifecycle transition, proposal lineage, audit and freshness effects must execute through an owner-owned transaction-aware primitive on the caller connection. Requirement, Assumption, ModelSpec and Global Decision receive the same minimum connection-taking CAS/audit seam where no such primitive exists today.

Proposal-origin operations remain proposal-governed: their current eligibility and lineage checks run inside this same transaction and proposal state cannot be committed separately before the rest of the cumulative plan succeeds. No protected HTTP call, nested independent commit, provider/solver/filesystem/network side effect, or best-effort compensating rollback is allowed in the canonical apply path.

Readiness MUST name the exact owner functions/files to be added or extracted from then-current master and prove a fault-injection test in which an earlier owner mutation has executed in-memory/inside the transaction, a later owner mutation fails, and **all** canonical owner rows, proposal/lifecycle/audit/freshness success effects, working-chain consumption and request-success state remain uncommitted after rollback. Existing public single-owner behavior must remain regression-covered.

## 7. Freeze the V0 machine-evaluable acceptance-criterion subset

Free-text `requirements.acceptance_criteria` remains human-readable evidence and MUST NOT be parsed heuristically into executable policy. A criterion participates in zero-rerun deterministic gating only when the existing Requirement identity is accompanied by explicit bounded typed metadata owned with that Requirement. The minimum typed V0 rule is a **single scalar comparison over one exact persisted run result**; there is no expression DSL.

Normative typed fields/semantics:
- criterion owner identity: exact `requirement_id` plus its exact owner revision token; no peer criterion identity is required for V0;
- target: exact persisted result selected by `run_id` + `output_name`, with exact working-revision/provenance binding required by the full spec;
- operator: exactly one of `<`, `<=`, `>`, `>=`, `==`;
- expected value: finite numeric decimal serialized in canonical JSON number/string form chosen by readiness, parsed by one deterministic server implementation; NaN/Inf are forbidden;
- expected unit: required non-empty unit string when the target result is unit-bearing, otherwise both sides must be explicitly unitless;
- rule version: one server-owned constant/version included in validation evidence so semantic changes invalidate older evidence.

**Unit semantics for V0 are deliberately strict.** Exact-master audit found no accepted generic unit-conversion/normalization authority that 112 can safely reuse. Therefore V0 performs only deterministic textual normalization of unit identity: trim surrounding ASCII whitespace and require the resulting expected-unit string to equal the persisted result unit after the same trim. No case folding, alias map, dimensional inference, scale conversion, offset conversion or implicit SI conversion is authorized. A non-identical unit is `not_evaluable/unit_mismatch`, never PASS/FAIL. Introducing real conversion requires a separately accepted canonical unit authority or a fresh spec amendment; 112 must not invent one during implementation.

The evaluator returns one immutable result shape bound into `project_knowledge_validation`:
- `requirement_id` and exact requirement revision token;
- `rule_version`;
- exact target `{run_id, output_name}` plus producing working-revision/source/run provenance required by the full spec;
- observed `{value, unit}` exactly as admitted from persisted result evidence;
- expected `{operator, value, unit}`;
- `status`: exactly `pass`, `fail`, or `not_evaluable` for this evaluator;
- `reason_code`: deterministic bounded enum; at minimum `comparison_true`, `comparison_false`, `missing_target`, `stale_target`, `wrong_working_revision`, `unsupported_rule`, `non_finite_or_non_numeric`, `unit_mismatch`;
- validator identity/version and validated-input digest already required by the full spec.

Comparison is numeric and deterministic after the accepted parser has produced finite values. `==` is exact numeric equality under that representation; V0 defines no tolerance/epsilon. Approximate/tolerance criteria remain non-machine-evaluable until a later explicit rule version defines them. Boolean combinations, arithmetic expressions, wildcard/latest-run selection, cross-result formulas, string comparisons, user-supplied code and prose parsing are out of scope.

For a mandatory typed acceptance criterion, only `pass` satisfies the gate. `fail` preserves the known-FAIL path already defined by the full spec; `not_evaluable` is unresolved/missing evidence and blocks ordinary final reconciliation rather than being silently treated as failure or success. A free-text-only acceptance criterion has no machine PASS claim; when it is mandatory for reconciliation, readiness/UI must require explicit human resolution or an accepted typed rule rather than fabricate deterministic evaluation.

Mandatory tests include all five operators; equality with no tolerance; missing/non-numeric/non-finite targets; exact unit match; whitespace-only unit normalization; same-dimension-but-different unit strings rejecting as `unit_mismatch`; wrong sibling working revision; stale target/rule/requirement revision; unsupported/free-text rules never executing; and `not_evaluable` blocking ordinary reconciliation.

## 8. Freeze Project Basis create operations and provisional references

The accepted Project Basis CRUD/write scope includes creation; a draft operation cannot require an existing canonical owner id for every operation. V0 therefore supports an explicit `create` operation for the 112-owned Project Basis classes that are canonically represented by `requirements` and `decisions`.

A create operation MUST contain:
- server-generated immutable `operation_id` scoped to the draft;
- `owner_kind` (`requirement` or `decision` in this Project Basis create subset);
- `operation_kind=create`;
- no canonical owner id and no expected owner revision token;
- bounded typed create payload accepted by the canonical owner, including the exact Requirement `basis_kind` for Requirement-backed Project Basis classes;
- source/provenance/proposal origin required by the canonical owner;
- any dependency/source-binding delta expressible before canonical id allocation;
- a server-owned provisional reference exactly scoped to the draft operation, semantically `draft:<draft_id>:op:<operation_id>`. The concrete serialization may follow repository conventions, but it is never a canonical 050 ref and cannot escape as current canonical identity.

Draft update/delete/supersession of another create in the same draft or accepted ancestor chain addresses that provisional operation identity. Impact projection may resolve provisional refs only inside the bounded projected working state. Approval persists the ordered create intent unchanged; it still does not create a canonical Requirement or Decision.

Final reconciliation allocates the real canonical owner id exactly once inside the same `ProjectBasisApplyService` transaction by invoking the canonical owner's transaction-aware create primitive. The transaction maintains an in-memory/provenance mapping from provisional operation identity to resulting canonical id so later operations in the same cumulative plan can target the created owner deterministically. The resulting mapping is recorded in immutable reconciliation/working-chain outcome evidence and is included in the reconciled snapshot manifest; it is not a peer identity store.

For retry/idempotency, the same reconciliation request MUST return/reuse the canonical id mapping committed by the successful request and MUST NOT allocate another owner. A failed transaction exposes no canonical id or partially-created owner. Requirements created for objective/question, requirement, acceptance criterion, stable constraint, boundary condition, standard/regulation, or resource/capability constraint all use the existing `requirements` owner with their bounded `basis_kind`; global decisions use the existing `decisions` owner. No `project_*` peer owner table is authorized.

Mandatory deterministic tests include: create each accepted Requirement-backed `basis_kind`; create a Global Decision; two create operations followed by a same-plan update/reference; stale/failed reconciliation leaves zero created owners; response-loss retry returns the same canonical ids; conflicting provisional refs fail closed; and a provisional ref is rejected anywhere a current canonical ref is required.

## 9. Freeze the persisted scalar-result lookup seam

The audited runtime's `simulation_runs.output_payload` is opaque/domain-specific and does not by itself provide a canonical `output_name -> {value, unit}` lookup. V0 therefore adds one minimum **immutable admitted scalar projection** for zero-rerun criterion evaluation; the evaluator MUST NOT parse arbitrary `output_payload` ad hoc.

The additive child relation is semantically `simulation_run_scalar_results` (repository-conventional SQL naming may differ, semantics may not) with one immutable row per admitted scalar result and:
- `run_id` referencing the existing canonical simulation run;
- exact `output_name`, non-empty and unique within the run: `UNIQUE(run_id, output_name)`;
- finite numeric `value` in the same canonical decimal representation used by the criterion evaluator;
- `unit`, either a non-empty exact unit string or explicit unitless representation;
- exact `project_knowledge_revision_id` required for rows admitted for 112 validation;
- `source_payload_digest` of the exact canonical run output payload from which this scalar was admitted;
- bounded `extractor_id` and `extractor_version` identifying the trusted deterministic run-kind adapter/schema that admitted the scalar;
- immutable creation timestamp.

This relation is a materialized typed projection of an existing immutable run result, not a second mutable run/result authority. It has no general update API and no browser/client write path. New rows may be created only by a trusted server-side deterministic adapter at run-result persistence/finalization, or by an explicitly invoked deterministic admission operation that proves the exact immutable source payload digest, run kind/schema, workspace, working-revision binding, finite numeric value and unit. Historical runs without such an admitted row remain history but are `not_evaluable/missing_target`; they are never heuristically backfilled from opaque payloads.

The V0 criterion target `{run_id, output_name}` resolves **only** through this admitted scalar relation. Lookup additionally verifies same workspace, exact `project_knowledge_revision_id`, exact immutable run/result/source digest, extractor identity/version, and current validation input/source bindings. Missing row, duplicate/corrupt identity, wrong working revision, stale/digest mismatch, unsupported extractor, non-finite value, or malformed unit fails closed as `not_evaluable` with the bounded reason code family from section 7. No wildcard/latest-run lookup is allowed.

The admitted scalar row and its source run remain immutable. If a future run/result schema supports an equivalent already-canonical typed scalar record, a later fresh spec may reuse it; readiness for this V0 may adjust the SQL/module name only, not replace this contract with arbitrary payload parsing.

Mandatory tests include: exact run/name lookup; same output name on different runs remains distinct; duplicate same-run/name rejected; wrong workspace/revision rejected; payload digest drift rejected; unsupported extractor rejected; historical opaque-only run returns `missing_target`; unitless and exact-unit cases; NaN/Inf admission rejected; and no frontend/API path can author or mutate an admitted scalar row directly.

## Readiness consequence

PR #429 remains planning-only. Before readiness may accept 112, the fresh exact-master audit must verify all closure obligations together: cumulative accepted-ancestor projection; complete Project Basis owner/additive seams; independently unique approval retry keys; transaction-safe Project Basis create/provisional-reference semantics; approval response-loss idempotency; atomic reconciliation-request success; cumulative ancestor-chain reconciliation; the explicit `ProjectBasisApplyService` transaction/owner-primitive contract; and the exact V0 scalar criterion evaluator plus admitted scalar-result lookup semantics above. If any proof fails, 112 remains not ready and readiness names the exact gap rather than weakening the contract.