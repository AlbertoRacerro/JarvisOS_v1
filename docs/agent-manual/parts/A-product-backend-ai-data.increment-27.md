# Area A file-coverage increment 27

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

Fresh baseline inspected: `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_cohorts.py` | READ | Read-only cohort aggregation/projection over terminal-flow evidence: computes grade/exclusion coverage, execution/dispatch/provider/accounting metrics, spend/mix/distributions and explicit reconciliation invariants; local compute remains deliberately unpriced in total-economic-cost output. |

## Failure-mode notes

- Cohort totals are evidence projections, not accounting authority: the function reports reconciliation booleans instead of failing when flow-level and attempt-level spend disagree, so consumers must inspect `reconciliation.accounting_spend_matches_flow_spend` before treating totals as internally consistent.
- `_count(value)` uses `int(value or 0)` without an explicit non-negative guard in this aggregation layer; correctness therefore depends on the persisted evidence/store contract preventing negative token/latency values.
- `total_economic_cost_per_useful_outcome_usd` is explicitly `None`; only external-provider spend per useful eligible outcome is priced, while local compute cost is counted/unpriced rather than silently monetized.
