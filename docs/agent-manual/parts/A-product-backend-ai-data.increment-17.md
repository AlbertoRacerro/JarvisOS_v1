# Area A file-coverage increment 17

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This is an additive evidence shard for issue #656 / PR #658. The protected canonical ledger is intentionally not rewritten here because a complete safe canonical replacement is not required for this increment. Prior canonical and increment rows remain authoritative evidence and must be preserved.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/egress_policy.py` | READ | Canonical AI-egress policy loader/parser. Restricts loading to `configs/ai_egress_policy.json`, rejects missing/extra schema keys, enforces schema v1, positive limits/TTLs, sample-rate bounds, nonnegative soft spend, unique confirmable triggers restricted to t1/t2/t5, and exactly the external-provider operation; computes a SHA-256 digest over canonicalized raw JSON. `load_default_egress_policy` is process-cached, so on-disk policy changes are not observed until cache clear/process restart. Numeric validation permits non-finite positive floats such as `inf` for `daily_soft_spend_usd` if supplied programmatically (JSON itself normally cannot represent this portably), because only type and `< 0` are checked. |

### Inspection note

Source was reopened and read completely from fresh master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` before crediting this row. No runtime/product code, STATUS, spec144, Hermes direction, secrets, or another owner's documentation was modified.
