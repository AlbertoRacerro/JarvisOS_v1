# Area A file-coverage increment 26

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/egress_confirmation.py` | READ | Thin public confirmation wrapper over `egress_confirmation_core`: re-exports the execution type/budget gate/proposed-record helper, synchronizes patchable bindings into core, loads persisted ticket metadata, routes expired/revoked continuation-authority tickets through rejected-continuation cleanup and returns a blocked `config_error` outcome, otherwise delegates normal execution to core. |

## Inspection notes

- Fresh source inspected from master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` before crediting.
- Failure/maintenance boundary: `_sync_patchable_bindings()` mutates module-level symbols in `egress_confirmation_core` immediately before execution. This deliberately preserves patchability/test seams but means concurrent callers/tests that monkey-patch these globals share process-wide mutable bindings rather than request-local dependencies.
- Rejected continuation handling is selected only when persisted metadata is already `expired`/`revoked` **and** has non-null continuation authority; all other states delegate to the canonical core path.
- No runtime/product code was modified.
