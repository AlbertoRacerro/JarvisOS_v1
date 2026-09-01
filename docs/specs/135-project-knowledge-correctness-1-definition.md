# 135 PROJECT-KNOWLEDGE-CORRECTNESS-1 — definition

Status: planning authority only until the live registry/readiness gate authorizes implementation.

## Problem

Fresh post-134 `master` still exposes three bounded correctness gaps in the merged `112 PROJECT-KNOWLEDGE-CORE-1` boundary:

1. approving an already-approved draft under a different approval key can create a second working revision for the same draft;
2. a small set of Project Knowledge request/command models accept unknown fields instead of failing closed;
3. canonical Project Knowledge JSON serialization accepts non-finite floats (`NaN`, `Infinity`, `-Infinity`), permitting non-standard JSON and unstable/invalid digest inputs.

These are corrective repairs to the existing Project Knowledge owner, not a new product capability.

## Scope

- Enforce at most one immutable working revision produced from one approved draft while preserving same-key idempotent replay and concurrency/CAS correctness.
- Add `extra="forbid"` only to the actual Project Knowledge request/command models that remain permissive.
- Reject non-finite numeric values at the Project Knowledge canonical JSON boundary using a typed domain/client failure while keeping finite canonical serialization bytes and digests unchanged.
- Add deterministic regression tests for each failure mode.

## Expected affected area

- `backend/app/modules/project_knowledge/service.py`
- `backend/app/modules/project_knowledge/models.py`
- existing Project Knowledge persistence/repository code only if required for race-safe uniqueness
- Project Knowledge API/service tests

## Non-goals

- no second Project Knowledge store or ownership layer;
- no broad schema/model redesign;
- no changes to retained Assumption/Parameter create-time semantics accepted by 127;
- no global JSON framework rewrite;
- no new approval workflow, UI, provider, credential, egress, or routing authority;
- no migration unless race-safe uniqueness cannot be achieved with the existing persisted identity/CAS boundary.

## Dependencies

Hard dependencies: `112`, `134` merged.

## Lifecycle

This definition establishes only the corrective planning identity. Implementation remains forbidden until full specification, readiness, and a live `STATUS.md` state of `ready` are merged.