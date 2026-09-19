# Area A coverage increment 29

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_read.py` | READ | Read-side flow-grade state projector. Validates `flow_id`, ensures/materializes the canonical grading subject, reads and decodes its ordered event history, exposes latest event, and treats a latest `set` event as the current grade while a latest non-`set` action leaves `current_grade_event` null. |

## Inspection notes

`get_flow_grade_state()` is intentionally a thin composition boundary over subject materialization and event-store reads rather than an independent grading authority. A read can therefore have write-side effects through `ensure_flow_grade_subject(flow_id)` before event retrieval. The current grade is derived solely from the final decoded event: if the latest action is not `set`, `current_grade_event` is `None`, while `latest_event` and full history remain visible.

Failure/trust boundary: this module does not independently verify event ordering, schema semantics, or subject/evidence integrity; those guarantees are delegated to `ensure_flow_grade_subject`, `list_events`, and `decode_event`. Errors from those dependencies propagate rather than being converted to a partial state.
