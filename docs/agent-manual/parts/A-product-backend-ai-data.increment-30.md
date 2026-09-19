# Area A coverage increment 30

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_subjects.py` | READ | Transactional flow-grade subject materializer/versioner; hashes canonical terminal evidence, reuses exact-current subjects, invalidates changed evidence, versions replacements, and rejects reversion to previously invalidated outcome evidence. |

## Inspection notes

The public entrypoint uses an immediate SQLite transaction with commit/rollback around subject materialization. The in-transaction helper loads canonical terminal evidence, builds and hashes the outcome payload, returns the current valid subject on exact digest equality, otherwise invalidates it and inserts the next version.

Failure boundary: terminal-evidence validity is delegated to the evidence loader/builder. Reuse of a previously invalidated outcome digest raises a conflict instead of reviving historical state. Callers of the in-transaction helper must provide appropriate transaction discipline.
