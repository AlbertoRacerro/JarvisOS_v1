# Area A product/backend/AI/data — additive coverage increment 22

This shard is additive evidence for issue #656. It intentionally does not replace `A-product-backend-ai-data.md`; the canonical ledger has a prior destructive-replacement incident and is left untouched unless a complete monotonic-safe rewrite can be verified.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_persistence.py` | READ | Canonical SQLite persistence/preparation boundary for immutable egress packets, decisions, confirmation tickets and projected-cost reservations. Builds packet projection before a `BEGIN IMMEDIATE` transaction; expires stale active reservations, snapshots budget state, applies hard provider/credential/budget blocks and confirmation triggers, then atomically persists deny/pause/allow state without dispatching a provider. Packet-digest reuse is accepted only when every persisted immutable field matches, otherwise fails closed as collision/drift. `project_egress_availability` is deliberately read-only and counts active/in-flight reservations exactly as stored. Continuation authority is range/type checked and limited to S0/S1. Failure boundary: global budget projection treats missing `ai_settings` as not exhausted, so correctness relies on the surrounding initialization/schema invariant; provider registry/policy and secret-ref resolution remain external authorities rather than being proven by this persistence layer. |

## Inspection note

Source was reopened directly from fresh `master` before crediting. No runtime/product code, STATUS, spec144, Hermes direction, secrets, canonical Area-A file, or another owner's documentation was modified.
