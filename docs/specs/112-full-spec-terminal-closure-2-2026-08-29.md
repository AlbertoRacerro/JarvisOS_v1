# 112 full-spec terminal closure 2 — 2026-08-29

Authority: binding final amendment to `docs/specs/112-project-knowledge-core-1.md` and its 2026-08-29 closure documents for the full-spec planning stage. Where this document is more specific, it supersedes the earlier clause. It remains planning-only: `112` stays `planned`; no runtime implementation is authorized; a separate fresh exact-master readiness decision is mandatory.

Reviewed exact PR head before this amendment: `ce9e073925bdd99dc5ca7c571e18545e127265e2`.

This amendment closes the two remaining material P1 findings on that exact head without broadening runtime, provider, credential, queue, or shared-authority scope.

## 1. Reconciliation idempotency key has one independent workspace uniqueness scope

`project_knowledge_reconciliation_requests` MUST enforce one independently unique caller retry identity per workspace:

`UNIQUE(workspace_id, idempotency_key)`

The idempotency key is not scoped by working revision, target revision, acknowledgement, or request digest. Those values are immutable **bound values** of the unique key and MUST be checked on every reuse.

On first use, the server atomically persists the key together with workspace id, exact working revision id, exact still-current reconciled target identity/digest, known-fail acknowledgement/policy identity where applicable, canonical request digest, state/outcome, and timestamps. On retry with the same `(workspace_id, idempotency_key)`, the server rereads that one row and compares every bound value. Exact match returns the already-recorded terminal or in-progress request identity/outcome without replay. Any mismatch is a deterministic idempotency conflict and fails closed before canonical mutation. The same key can therefore never name two reconciliation attempts in one workspace, including attempts against different working revisions.

The successful request outcome remains committed in the same transaction as canonical owner mutations, reconciled snapshot creation, working-chain consumption, and reconciled-revision transition. A response-loss retry therefore resolves one unique committed outcome. Failed attempts follow the already-specified failure recording semantics but cannot free/recycle the key for different bound values.

Mandatory tests:
- same workspace + same key + exact same bound values returns the same request/outcome and performs no second canonical mutation;
- same workspace + same key + different working revision rejects as idempotency conflict;
- same workspace + same key + changed target digest, acknowledgement/policy identity, or request digest rejects as idempotency conflict;
- different workspaces may use the same opaque key without collision;
- concurrent first-use attempts for one workspace/key yield exactly one persisted request identity; the loser resolves that row and either returns the matching outcome or rejects conflicting bound values;
- response loss after successful commit followed by exact retry returns the same success and does not replay owner mutation, proposal promotion, snapshot creation, validation selection, or audit effects.

## 2. Append-only validation has explicit current/superseded evidence selection

`project_knowledge_validation` remains append-only, but append-only history MUST NOT leave final reconciliation free to choose an older PASS after newer admissible evidence exists.

Each validation row MUST have immutable identity plus an explicit append-only supersession relation sufficient to determine one current row for a validation slot. The minimum V0 contract is:

- immutable validation `id`;
- exact `working_revision_id`;
- exact criterion/rule identity and rule revision/version;
- exact validated-input/basis digest;
- immutable source run/scalar/result identity and digest where applicable;
- outcome and validator identity/version;
- `supersedes_validation_id` nullable, pointing only to the immediately previous current row in the same validation slot;
- created timestamp.

The **validation slot** is the tuple `(working_revision_id, criterion/rule identity, rule revision/version, validated-input/basis digest)`. A replacement validation for the same slot MUST atomically reread the current terminal row, require its exact id as the expected predecessor, and append the new row with `supersedes_validation_id = previous.id`. Two competing replacements against the same predecessor cannot both become current; stale predecessor CAS fails closed. Historical rows are never updated or deleted.

Current-selection semantics are deterministic: for each mandatory validation slot, the current row is the unique terminal row in that slot that is not superseded by another valid row in the same slot. Missing current evidence, more than one unsuperseded current candidate, a broken/cyclic/cross-slot supersession link, source/basis incompatibility, or stale criterion/rule identity makes the evidence set incomplete/ambiguous and blocks ordinary reconciliation.

A replacement run that changes PASS to FAIL therefore appends a FAIL that supersedes the prior PASS; final reconciliation MUST evaluate the FAIL and may use only the separately specified explicit known-FAIL acknowledgement path. A later admissible PASS may supersede that FAIL and then becomes current. `not_evaluable` and other terminal outcomes follow the same supersession rule and cannot be bypassed by selecting older evidence.

Before final reconciliation mutates canonical owners, the server MUST materialize and digest the exact selected current validation set: ordered validation ids, slot identities, rule revisions, validated-basis digests, source result/run digests, outcomes, validator versions, and supersession predecessors. The reconciliation request binds this `selected_validation_set_digest`. Inside the final `BEGIN IMMEDIATE` transaction the server rereads the selected rows, recomputes current-selection and the digest, and rejects drift, a newly appended replacement, ambiguity, stale basis/rule/applicability, or digest mismatch. Successful request outcome and reconciled snapshot evidence record that exact selected validation-set digest.

Mandatory tests:
- PASS then replacement FAIL in the same slot makes FAIL uniquely current and ordinary reconciliation cannot select the historical PASS;
- FAIL then admissible replacement PASS makes the later PASS uniquely current;
- concurrent replacement attempts against one predecessor produce one current successor and one stale-predecessor rejection;
- two unsuperseded rows in one slot, broken/cyclic/cross-slot supersession, or missing current row fails closed as ambiguous/incomplete;
- a replacement appended after preview/request creation changes the selected-validation-set digest and causes final reconciliation to reject stale evidence;
- exact response-loss retry after successful reconciliation returns the originally committed selected validation set/outcome and performs no replay;
- historical superseded validation rows remain inspectable and immutable.

## Closure rule

Readiness MUST verify these two contracts against the then-current exact master and the complete 112 authority chain. It may adjust SQL/index names to repository conventions, but it may not weaken independent workspace-key uniqueness, bound-value conflict detection, append-only validation history, one-current-row-per-slot selection, stale-predecessor protection, or final reconciliation binding to the exact current validation set.