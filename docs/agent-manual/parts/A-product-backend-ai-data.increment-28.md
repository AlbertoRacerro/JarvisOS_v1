# Area A file-coverage increment 28

MAPPING_STATUS: IN_PROGRESS

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_evidence.py` | READ | Terminal-flow grading evidence loader/projector: requires terminal flow state and canonical accounting/output digests, loads ordered AI-job attempts, verifies persisted attempt count/identity/contiguous indexes and finalized attempt statuses, then emits deterministic flow/attempt evidence including per-attempt canonical digests. |

## Failure-mode notes

- Grade evidence construction fails closed when persisted flow attempt count, ordered attempt IDs, or contiguous attempt indexes disagree with canonical `ai_jobs`; a terminal flow row alone is therefore insufficient grading evidence.
- Every attempt must already be in `FINAL_ATTEMPT_STATUSES`; one non-finalized attempt rejects the entire evidence projection rather than silently grading partial execution.
- The projector preserves persisted usage/accounting/provider/model fields and computes an `attempt_evidence_digest` over each projected attempt. It does not independently recompute provider usage or spend, so those values remain dependent on upstream terminalization/accounting invariants.

UNACCOUNTED_FILES: >0
