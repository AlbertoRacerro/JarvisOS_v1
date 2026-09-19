# Area A file-coverage increment 31

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_cohort_distributions.py` | READ | Small deterministic numeric-distribution helper used by flow-grade cohort reporting. Empty input returns count 0 with null min/p50/p95/max; non-empty input sorts integer evidence and reports min/max plus nearest-rank p50 and p95 (`ceil(percentile * n)`, one-based rank). It performs no domain/range validation itself, so semantic validity of values is an upstream contract. |

## Inspection note

Re-opened the complete source directly from fresh `master` SHA `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`; credit is based on actual content inspection, not PR #660 history. The protected canonical Area-A file was intentionally not rewritten in this increment.
