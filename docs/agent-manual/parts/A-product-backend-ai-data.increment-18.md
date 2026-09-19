# Area A capability-map increment 18

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard preserves the repaired canonical Area-A ledger and all earlier increments; it exists because a complete safe canonical-file replacement was not attempted in this run.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/egress_rejected_continuation.py` | READ | Transactionally consumes an already expired/revoked continuation confirmation without provider dispatch: requires persisted continuation authority and a flow still in `confirmation_required`, derives terminal reason from expiry/revocation, delegates terminalization to token-flow confirmation-resume logic, and returns lifecycle consumption evidence. Failure boundaries: missing ticket, non-rejected state, absent continuation authority, or missing/non-paused flow fail closed with `EgressStateError`; it intentionally depends on private persistence/lifecycle helpers and executes under `_immediate_transaction`. |
