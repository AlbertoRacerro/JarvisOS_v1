# Area A file-coverage increment 45

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_persistence.py` | READ | Canonical 059b SQLite preparation/persistence boundary. Reopened from fresh `master`: projects immutable egress packets, atomically persists packet+decision under `BEGIN IMMEDIATE`, computes budget/provider hard blocks and confirmation triggers, creates confirmation tickets or silent-allow reservations, rejects unsupported structural-confirmation paths, and exposes non-mutating availability projection. Packet-digest reuse is fail-closed against immutable-field mismatch. Continuation authority is structurally validated and restricted to S0/S1. No provider adapter dispatch occurs here. |

### Runtime notes from direct inspection

- `prepare_egress_attempt()` expires stale active reservations and performs packet/decision/ticket-or-reservation creation inside one immediate SQLite transaction, limiting concurrent double-reservation races at this boundary.
- Existing packet digests are accepted only when the persisted immutable projection/material fields match; otherwise `EgressStateError` is raised as a digest-collision/state-corruption guard.
- `project_egress_availability()` is intentionally read-only: it counts active/in-flight reservations as stored and does not expire/reconcile them, persist state, or dispatch providers. Consequently it is a projection, not reservation authority.
- Global budget exhaustion combines configured month-to-date spend with persisted actual spend conservatively via `max(...)`, then includes persisted reserved cost.
- Provider execution is explicitly outside this file; dispatch/final accounting invariants must be assessed in the lifecycle/confirmation execution owners rather than inferred from successful preparation.
