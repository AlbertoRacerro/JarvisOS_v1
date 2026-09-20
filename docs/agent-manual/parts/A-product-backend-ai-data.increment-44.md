# Area A file-coverage increment 44

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard exists to preserve the canonical Area-A ledger after the prior destructive-replacement incident. It adds only source files reopened directly from fresh `master`; consolidation into the canonical ledger must remain monotonic.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_lifecycle.py` | READ | Transactional confirmation-ticket/reservation lifecycle: atomically consumes or revokes/expirs pending tickets with CAS and continuation-flow handling, rebuilds and revalidates persisted packet/policy bindings, creates budget reservations, binds reservations to matching `ai_jobs`, records immutable egress attempts, and reconciles usage/cost conservatively when usage evidence is missing/unverified/mismatched or pricing drifts. Pre-network reconciliation is forced to zero provider usage; network reconciliation requires an in-flight reservation. |

### Runtime notes from direct inspection

- Ticket consumption runs under the persistence immediate transaction, expires stale reservations first, validates continuation authority when present, rebuilds the packet projection from persisted material, revalidates ticket/policy/config digests and hard budget blocking, then CAS-transitions the ticket and inserts the reservation in the same transaction.
- `start_reserved_attempt()` validates the existing `ai_job` provider/model/route binding before CAS-moving an active reservation to `in_flight`; an expired reservation is persisted as expired before the function raises.
- `reconcile_reserved_attempt()` accepts network attempts only from `in_flight`; a failed-before-network path may reconcile `active` or `in_flight` and must report zero provider usage. It inserts an immutable `egress_attempts` row and CAS-terminalizes the reservation in the same transaction.
- Usage accounting fails conservative rather than optimistic: missing/unverified/mismatched usage or pricing/cost drift takes maxima against reserved/verified/reported evidence as applicable. Exact `actual` accounting requires matching actual token evidence and matching pricing identity/cost.
