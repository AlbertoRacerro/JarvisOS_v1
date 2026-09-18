# Area A durable coverage increment 11

Canonical ledger safety note: this shard is intentionally separate because the connector could not return the complete canonical ledger without truncation. Do not replace `A-product-backend-ai-data.md` from a partial read. Canonical branch head at run start: `95c11df4607250e391bae31adfa81d1b49ac16bc`; supervisor-repaired canonical ledger has 65 credited rows.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## VERIFIED SOURCE INSPECTIONS

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/privacy.py` | READ | Local deterministic privacy policy engine. Classifies public/internal/confidential/sensitive-IP/secret/unknown text; smoke-test decisions fail closed for secret, sensitive-IP and unknown material; smoke-console policy has DISABLED blocking, structural-secret and jailbreak/bypass checks, a permissive FAST_DEV path that still blocks structural secrets, and a stricter greeting allowlist path. Provider suggestions are explicitly non-authoritative; JarvisOS owns routing enforcement. |
| `backend/app/modules/ai/provider_registry.py` | READ | Canonical YAML provider/model registry parser and route-binding authority. Validates registry version, provider IDs, execution-class/network/endpoint/credential contracts, model route uniqueness, context/output limits, concrete external-provider USD pricing/effective timestamps, fallback chains, and environment model overrides constrained to the same provider/route/execution class. Exposes provider/model/binding/fallback configuration; it is configuration/validation, not provider dispatch authority. |

## FAILURE-MODE NOTES

- `privacy.py` intentionally maps invalid/unrecognized policy-mode strings to `FAST_DEV`; callers must not treat malformed mode text as a fail-closed DISABLED state.
- FAST_DEV smoke-console handling allows non-structural-secret text and classifies most such text as internal. Structural secret regex/markers remain the deterministic guard; this is materially more permissive than the strict smoke-console allowlist path.
- Provider registry environment overrides can change the concrete model but only when the configured value resolves uniquely inside the already-bound provider and route; changing execution class is rejected.
- Enabled external-provider models require concrete pricing, and cache-read input price cannot exceed ordinary input price.

## MERGE-BACK REQUIREMENT

Before crediting these rows into `## EXPLICIT FILE COVERAGE LEDGER`, reopen this shard and the two source files, fetch the COMPLETE canonical branch document, append monotonically, then refetch and assert all prior 65 ledger paths remain present plus these intended additions. Delete/retire this shard only after that verified merge-back.
