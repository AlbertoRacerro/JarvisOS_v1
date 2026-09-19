# Area A file-coverage increment 33

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/flow_grade_contracts.py` | READ | Flow-grade contract vocabulary and validation/decoding helpers: terminal/final status sets, grade/source/reason enums, ID/digest validation, canonical JSON, note/reason normalization, and SQLite subject/event projection. |

## Runtime observations

- `safe_id` is the strict external identifier validator (1–128 characters under `ID_RE`); malformed identifiers are contract errors.
- `required_digest` and `optional_digest` deliberately classify malformed/unfinalized persisted digests as conflicts rather than request-contract failures, preserving the distinction between caller input and inconsistent canonical evidence.
- `normalize_reason_codes` permits at most five supplied values, rejects unknown codes, and de-duplicates while preserving first-seen order.
- `normalize_note` trims whitespace, collapses empty text to `None`, caps notes at 1000 characters, and rejects NUL.
- `decode_subject`/`decode_event` are projections rather than full persisted-row validators: they coerce several fields and `decode_event` validates `reason_codes_json` only as a JSON list. Semantic row integrity therefore remains dependent on the write path/database invariants.

This increment is additive because the protected canonical Area-A ledger is not being rewritten without a complete monotonic-superset verification.
