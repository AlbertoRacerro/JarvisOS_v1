# Area A file-coverage increment 42

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| Path | Status | Concise role / reason |
|---|---|---|
| `backend/app/modules/ai/egress_confirmation_core.py` | READ | Core 059b confirmation-ticket execution path: reloads server-owned ticket metadata, consumes confirmation authority, detects persisted ticket/consumption drift, rechecks provider budget and adapter availability, creates the queued job, starts the reserved attempt, validates immutable packet/binding identity, invokes the external adapter, validates response binding/dispatch evidence, finalizes external accounting, and transitions/terminalizes token-flow state including confirmed length continuations. Failure paths distinguish pre-dispatch config/start failures from provider calls whose dispatch state is unknown. |

## Runtime notes from direct inspection

- Confirmation is not a blind replay: ticket state must still be `pending`; consumption is revalidated against persisted packet/provider/model/route/fallback/output-ceiling metadata before execution.
- The provider budget gate is re-evaluated after ticket consumption and before adapter invocation; adapter absence terminalizes without dispatch.
- After reservation start, persisted packet JSON and provider/model/route/fallback/output-ceiling identity are compared again before constructing the request.
- Adapter exceptions are conservatively finalized with `external_dispatch_state=unknown`; successful responses reporting `not_started`, or responses/usage whose provider/model disagree with the bound ticket, are rejected as provider errors.
- Continuation confirmation can persist protected output segments and terminalize an assembled output at the authority's expected sensitivity level; a successful `length` finish may enter `continue_after_confirmed_length` rather than immediately terminalizing.
- This module depends on transaction/lifecycle guarantees in the imported egress/token-flow services; inspection of this file alone does not prove atomicity across those lower-level boundaries.

Source inspected directly from fresh `master` at `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.
