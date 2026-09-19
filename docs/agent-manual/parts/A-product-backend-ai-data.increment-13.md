# Area A durable coverage increment 13

Canonical ledger safety note: this shard is intentionally separate because the connector cannot safely return the complete canonical ledger without truncation. Do not replace `A-product-backend-ai-data.md` from a partial read. The supervisor-repaired canonical ledger remains the protected baseline; increment 12 remains additive prior evidence.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/contracts.py` | READ | Provider-neutral AI contract and in-memory registry definitions: provider/model/task/privacy/error/usage/dispatch enums; request/response, routing/gate/authority schemas; adapter protocol; provider/model registries and deterministic model filtering. `AIUsage` enforces exact total-token arithmetic, but these contracts do not themselves authorize egress, persist registry state, sanitize provider metadata, or dispatch network calls. |

## FAILURE-MODE NOTES

- `AIUsage.compute_or_validate_total_tokens` rejects a supplied `total_tokens` that differs from `input_tokens + output_tokens`, preventing internally inconsistent token totals at this schema boundary; it does not establish that provider-reported component counts are truthful.
- `ProviderRegistry.register_provider` rejects adapter/entry provider-id mismatch, but subsequent registration for the same provider id replaces the prior adapter and entry in memory rather than detecting duplicates.
- `ModelRegistry.register_model` likewise replaces an existing model id; uniqueness/provenance across configuration sources must therefore be guaranteed upstream if silent replacement is undesirable.
- `AIResponse.raw_provider_metadata`, `AIProviderError.safe_metadata`, request metadata and structured-output schemas are generic dictionaries here; successful Pydantic validation is not evidence that those dictionaries are sanitized, authoritative, or safe for egress/logging.
- `find_models` is a deterministic filter over the currently registered in-memory entries. It does not score models, validate provider health, credentials, budget, or policy, and must not be interpreted as final routing authority.
