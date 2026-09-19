# Area A file-coverage increment 34

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_events.py` | READ | Transactional flow-grade mutation service: validates set/withdraw requests, materializes/checks the canonical subject, enforces optimistic head concurrency and idempotency, inserts immutable grade events, and returns decoded persisted evidence. |

## Runtime observations

- `_write_event` acquires `BEGIN IMMEDIATE` before subject materialization and keeps subject validation, replay detection, head checks, event insertion, and commit in one SQLite transaction; any exception rolls the transaction back.
- Idempotency is scoped to the materialized subject: an existing `(subject_id, idempotency_key)` replay is accepted only when its persisted `request_digest` exactly matches the canonical digest of the current request; key reuse with different content is a conflict.
- Subject version and `flow_outcome_digest` are explicit optimistic-concurrency guards. A stale outcome cannot silently receive a grade even if the flow ID is unchanged.
- `set` permits creation only when the caller expects no current grade; replacing an existing grade requires the exact current set-event ID. `withdraw` requires an existing current set event and its exact ID. A latest withdraw therefore leaves no current grade.
- The service delegates persisted event-chain correctness and uniqueness enforcement to `flow_grade_event_store`; this layer does not independently re-validate a row returned by `insert_event` beyond `decode_event`.

This increment is additive because the protected canonical Area-A ledger is not being rewritten without a complete monotonic-superset verification.
