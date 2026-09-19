# Area A coverage increment 21

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard exists to preserve the repaired canonical ledger without risking destructive replacement. Prior canonical ledger and increment shards remain authoritative evidence and are not superseded.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_lifecycle.py` | READ | Transactional confirmation/reservation/attempt lifecycle for external egress. Atomically consumes pending confirmation tickets, revalidates packet/policy/authority and hard budget/provider gates, creates reservations, binds reservations to exact `ai_jobs`, and reconciles immutable `egress_attempts`. Continuation tickets additionally validate/reactivate or terminalize paused token flows in the same SQLite transaction. CAS/version predicates prevent duplicate state transitions. Reconciliation is deliberately conservative: pre-network failures record zero usage; missing/unverified/mismatched usage or pricing drift takes maxima across reserved, reported, verified and recomputed cost/token evidence rather than under-accounting. Important failure boundaries: persisted packet/manifests are JSON-decoded during ticket projection rebuild and malformed persisted JSON fails the transaction; ticket expiration is checked at consumption and reservation expiration at start; provider-reported usage is only accepted as `actual` when it exactly matches persisted non-queued `ai_jobs` actual usage and matching pricing identity. |
