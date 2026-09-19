# Area A capability-map increment 19

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard preserves the repaired canonical Area-A ledger and all earlier increments; it exists because a complete safe canonical-file replacement was not attempted in this run.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
| --- | --- | --- |
| `backend/app/modules/ai/egress_sanitizer.py` | READ | Transactional sanitizer/provenance boundary for prompt and canonical derivatives. Auto-approval is restricted to S0/S1 output that passes deterministic-floor checks; S4 raw prompt markers are rejected. Model-backed sanitization must bind a successful dedicated local-route `ai_job` whose output digest matches the derivative, and canonical model sanitization additionally requires pre-call source digests to detect source drift. Reuse verifies immutable content/provenance and revoked derivatives fail closed. Deterministic weekly sampling creates audit items; rejecting an audit revokes the derivative, pending dependent confirmation tickets, and active pre-start reservations atomically. Important boundary: canonical dependent-packet discovery scans/parses every stored `included_manifest_json` and fails the whole rejection transaction on malformed stored manifest; prompt-derivative lookup/reuse is policy-version scoped. Uses `BEGIN IMMEDIATE` with rollback/commit and records audit/approval events. |