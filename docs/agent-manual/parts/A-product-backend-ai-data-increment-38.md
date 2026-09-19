# Area A file-coverage increment 38

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/costs.py` | READ | Route-level cost estimation and escalation-proposal helper. Uses a fixed 4-chars/token approximation, default 1024 output-token budget, hard-coded external route prices, and `resolve_binding()` to expose provider/model identity. For confidential/sensitive-IP hints it emits a warning but does not itself enforce egress denial. Cost is therefore advisory/estimated rather than provider-billed truth. |

## Inspection note

Re-opened directly from fresh `master` before crediting. The helper can raise on an unknown `route_class` through direct registry indexing; `max_output_tokens=0` falls back to the 1024 default because the implementation uses `max_output_tokens or DEFAULT_OUTPUT_TOKENS`. No runtime/product code was changed.
