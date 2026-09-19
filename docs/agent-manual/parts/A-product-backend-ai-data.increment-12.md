# Area A durable coverage increment 12

Canonical ledger safety note: this shard is intentionally separate because the connector cannot safely return the complete canonical ledger without truncation. Do not replace `A-product-backend-ai-data.md` from a partial read. The supervisor-repaired canonical ledger remains the protected baseline; increment 11 remains additive prior evidence.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/models.py` | READ | Pydantic API/schema boundary for AI settings/status/provider credential projections, modeling drafts, generic task execution/context-pack preview, escalation confirmation, smoke/provider/supervisor test surfaces. It forbids extras on key write/request contracts, bounds context-block count/serialized size and token fields, but is schema/validation only: it does not authorize egress, settle usage, dispatch providers, or store credentials. |

## FAILURE-MODE NOTES

- `AISettingsUpdate` deliberately accepts several legacy Scaleway token-cap/counter aliases even though the settings service ignores them; successful request validation therefore does not imply those legacy fields mutate canonical state.
- `AITaskRunRequest` bounds caller `context_blocks` by both item count and canonical serialized character size before execution, but does not itself establish sensitivity/egress authority for those blocks.
- Several diagnostic response models expose provider metadata as generic dictionaries; schema validity alone does not establish that provider metadata is sanitized or authoritative accounting evidence.
