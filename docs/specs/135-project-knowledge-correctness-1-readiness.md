# 135 PROJECT-KNOWLEDGE-CORRECTNESS-1 — readiness

## Decision

READY only when this document, the full spec, and a live `docs/specs/STATUS.md` row for 135 are merged with status `ready`, and dependencies `112` and `134` remain `merged`.

This readiness packet does not by itself authorize product implementation while the registry row is absent or non-ready.

## Frozen implementation envelope

Implementation is limited to the three accepted behaviors in `135-project-knowledge-correctness-1.md`:

1. one race-safe immutable working revision per approved draft with same-key replay preserved;
2. fail-closed unknown-field handling on the revalidated permissive Project Knowledge request/command models only;
3. rejection of non-finite canonical JSON values with typed failure and byte-identical finite serialization/digests.

## Pre-implementation revalidation

Before editing product code, the writer must verify on fresh exact master:

- the duplicate-revision failure mode is still reachable and identify the persisted field/constraint that can enforce race-safe uniqueness;
- the five candidate request/command models are still the only live strict-extra gap in this bounded repair;
- `_canonical_json` / size serialization still permit non-finite numbers;
- no newer merged slice already closes any acceptance criterion.

If race-safe AC1 requires a new migration/constraint not already authorized by the existing Project Knowledge persistence boundary, stop product implementation and derive the minimum migration authority instead of shipping a race-prone pre-check.

## Required deterministic evidence

- targeted Project Knowledge service/repository tests covering same-key replay, different-key reapproval and concurrency/atomic uniqueness;
- direct model validation tests for every newly-strict request/command type;
- representative HTTP validation test for unknown input fields;
- nested `NaN`/`+Inf`/`-Inf` rejection tests with typed error mapping;
- finite canonical JSON/digest regression fixture;
- relevant existing backend Project Knowledge suite;
- repository-required architecture/registry/CI gates.

## Independent review

The implementation PR is MATERIAL because it changes canonical Project Knowledge write correctness. It requires an independent exact-head semantic review: Claude primary with a consumable exact-head verdict/findings; immediate single manual `@codex review` fallback if Claude terminates without consumable semantic evidence.

## PROUD gate

Merge only when objective gates are green on the exact current head, the independent review is acceptable, no material finding remains, and the accepted three-item envelope is complete. Do not expand scope for elegance or unrelated cleanup.

## Non-goals

No second store, no broad schema/model redesign, no 127b, no provider/egress/routing changes, no global serializer framework, no 113+ product capability.