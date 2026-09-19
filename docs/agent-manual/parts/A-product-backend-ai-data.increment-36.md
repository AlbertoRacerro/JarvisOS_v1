# Area A file-coverage increment 36

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_cohort_store.py` | READ | Read-only SQLite cohort evidence loader: validates optional filters/limit, selects bounded terminal flows, batches attempts/current valid subjects/latest grade heads, counts revisions/withdrawals/invalidated subjects, and reports whether the flow result was truncated. |

## Failure-mode / boundary notes

- Cohort membership is capped at 5000 terminal flows and `truncated` is detected with a `limit + 1` probe; downstream aggregate consumers must preserve that signal rather than treating a truncated cohort as complete population evidence.
- The loader reads flows, jobs, subjects and events through one SQLite connection but does not explicitly begin a snapshot transaction. Cross-table consistency therefore relies on the connection/database concurrency semantics supplied by `open_sqlite_connection()` and the surrounding persistence design.
- Current valid subjects are projected into a dictionary keyed by `flow_id` without a local uniqueness assertion. Correctness relies on the schema/write path maintaining at most one valid subject per flow.
- The store performs structural selection/projection rather than semantic reconciliation: persisted token/spend/accounting/grade evidence is carried forward for higher-level cohort logic to validate or reconcile.

Canonical-file safety: the canonical ledger was not rewritten in this run. This additive shard preserves all previously credited canonical/increment paths and adds exactly the source file reopened from fresh master above.
