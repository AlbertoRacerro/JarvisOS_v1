# Area A file-coverage increment 35

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_event_store.py` | READ | Low-level SQLite grade-event store: replay lookup by subject/idempotency key, latest/list ordering by event index, and append insertion with UUID/time/schema/policy metadata plus supersession link; caller owns transaction/concurrency and semantic validation. |

## Failure-mode / boundary notes

- `insert_event()` derives `event_index` from the caller-supplied `latest` row and performs no local stale-head or concurrency check. Correct serialization and optimistic-concurrency protection therefore depend on the higher-level transactional mutation path.
- `find_replay()` scopes idempotency to `(subject_id, idempotency_key)` and returns persisted evidence without independently checking request-digest equivalence; replay semantic validation belongs to the caller.
- The store canonicalizes `reason_codes` before persistence and verifies the inserted row can be read back, but it does not commit. Transaction ownership remains external.

Canonical-file safety: `docs/agent-manual/parts/A-product-backend-ai-data.md` was fetched this run but the connector response was truncated, so it was deliberately not rewritten. This additive shard preserves all previously credited canonical paths and adds exactly the inspected path above.
