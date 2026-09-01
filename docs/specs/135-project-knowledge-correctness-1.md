# 135 PROJECT-KNOWLEDGE-CORRECTNESS-1

## Objective

Close three concrete post-134 correctness gaps inside the existing Project Knowledge authority without expanding product scope: draft-approval uniqueness, fail-closed request models, and standards-compliant finite canonical JSON.

## Accepted behavior

### AC1 — one working revision per approved draft

- A draft approval may create at most one working revision for that draft.
- Replaying the same approval key returns the already-created result without mutation.
- Re-approving the same already-approved draft with a different approval key must not create a second working revision.
- Concurrent approvals under different keys must converge to one persisted working revision; application-only check-then-create behavior that can race is insufficient.
- Existing revision immutability and existing CAS/staleness semantics remain intact.
- The API/service must return an existing typed idempotent/conflict outcome rather than silently duplicating canonical state.

### AC2 — request/command models reject unknown fields

Close only the currently-live permissive request/command gap. The known candidates to revalidate immediately before implementation are:

- `ApprovalRequest`
- `ScalarAdmissionRequest`
- `ValidationRequest`
- `ReconcileRequest`
- `RevisionStateCommand`

Unknown fields must be rejected by model validation; representative HTTP entry points must surface the existing validation failure response (normally 422). Models already configured fail-closed and read/projection models are not widened into this repair.

### AC3 — non-finite canonical JSON rejected

- `NaN`, positive infinity and negative infinity are rejected anywhere within values that cross the Project Knowledge canonical JSON/digest/size boundary, including nested containers.
- Failure is translated into the existing typed Project Knowledge/domain/client validation vocabulary; raw `ValueError` must not escape as an accidental 500.
- Finite values retain byte-identical canonical JSON, digest inputs, ordering, separators and `ensure_ascii` behavior relative to pre-135 behavior.
- Existing payload-size enforcement remains effective and deterministic.

## Implementation constraints

- Reuse the existing Project Knowledge owner/store and persistence transaction/CAS boundary.
- Prefer a persisted uniqueness invariant already representable by the current schema. If no existing persisted identity can make AC1 race-safe, the implementation must stop and re-derive the smallest migration authority rather than pretending an application-level pre-check is concurrency-safe.
- For AC2 use Pydantic's existing strict-extra mechanism; do not redesign fields.
- For AC3 use the smallest canonical serialization change (for example `allow_nan=False`) plus typed translation at the domain boundary; do not introduce a repository-wide serializer framework.

## Deterministic tests

1. same approval key replay returns the same working revision and does not add rows;
2. different approval key against an already-approved draft does not add another working revision;
3. concurrent/double approval path proves one persisted working revision or exercises the existing atomic uniqueness/CAS primitive;
4. each newly-strict request/command model rejects an extra key;
5. at least one representative HTTP endpoint returns validation failure for an unknown key;
6. `NaN`, `Infinity`, and `-Infinity`, including nested occurrence, are rejected with the typed Project Knowledge/client failure;
7. a finite canonical fixture proves canonical bytes/digest are unchanged;
8. existing Project Knowledge test suite remains green.

## Security and authority invariants

No new network/provider/credential/egress surface. No frontend authority. No new store. No broad record-lifecycle semantics. No 113+ capability is pulled forward.

## Non-goals

- Assumption/Parameter legacy create-time semantics retained by accepted 127.
- broad Project Knowledge refactor;
- new approval UX/workflow;
- global Pydantic strictness migration;
- whole-API JSON generation/serialization redesign;
- unrelated cleanup.

## Dependencies

`112 PROJECT-KNOWLEDGE-CORE-1` and `134 MERGE-AUTHORITY-HARDENING-1` must remain merged on the implementation base.