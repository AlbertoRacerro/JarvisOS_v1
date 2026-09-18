# Area A durable coverage increment 11

Canonical ledger safety note: this shard is intentionally separate because the connector could not return the complete canonical ledger without truncation. Do not replace `A-product-backend-ai-data.md` from a partial read. Canonical branch head at shard creation followed supervisor repair `95c11df4607250e391bae31adfa81d1b49ac16bc`; supervisor-repaired canonical ledger has 65 credited rows.

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

## VERIFIED SOURCE INSPECTIONS

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/privacy.py` | READ | Local deterministic privacy policy engine. Classifies public/internal/confidential/sensitive-IP/secret/unknown text; smoke-test decisions fail closed for secret, sensitive-IP and unknown material; smoke-console policy has DISABLED blocking, structural-secret and jailbreak/bypass checks, a permissive FAST_DEV path that still blocks structural secrets, and a stricter greeting allowlist path. Provider suggestions are explicitly non-authoritative; JarvisOS owns routing enforcement. |
| `backend/app/modules/ai/provider_registry.py` | READ | Canonical YAML provider/model registry parser and route-binding authority. Validates registry version, provider IDs, execution-class/network/endpoint/credential contracts, model route uniqueness, context/output limits, concrete external-provider USD pricing/effective timestamps, fallback chains, and environment model overrides constrained to the same provider/route/execution class. Exposes provider/model/binding/fallback configuration; it is configuration/validation, not provider dispatch authority. |
| `backend/app/modules/ai/context_builder.py` | READ | Deterministic AI context assembly. Validates/canonicalizes caller blocks, hashes canonical JSON, separates SYSTEM/PROJECT_CONTEXT/USER_REQUEST so project content is reference data, and builds bounded workspace packs from decisions/assumptions/current parameters/requirements/evidence. Selection uses deterministic status/id/query limits and whole-block drop priority under the 20-block/character budget; no vector retrieval, embeddings, LLM ranking or summarization occurs here. |
| `backend/app/modules/ai/costs.py` | READ | Legacy/simple route-cost estimator and escalation-proposal builder. Uses a fixed 4-chars/token heuristic, default 1024 output tokens and hard-coded prices for `external:cheap`/`external:reasoning`; escalation proposals resolve the reasoning binding, expose outbound prompt text with context excluded, and add warnings for confidential/sensitive-IP hints. This is an estimate/proposal surface, not canonical accounting or egress authorization. |
| `backend/app/modules/ai/settings.py` | READ | SQLite-backed singleton AI settings and provider/status projection service. Seeds FAST_DEV/zero-budget/fake-provider defaults, reads and updates policy/provider/Scaleway/token-continuation settings, records Scaleway token counters, overlays canonical egress/accounting availability onto status, and projects provider credential presence/capabilities without exposing secret material. Credential truth delegates to the secrets owner; provider availability delegates to canonical egress persistence. |

## FAILURE-MODE NOTES

- `privacy.py` intentionally maps invalid/unrecognized policy-mode strings to `FAST_DEV`; callers must not treat malformed mode text as a fail-closed DISABLED state.
- FAST_DEV smoke-console handling allows non-structural-secret text and classifies most such text as internal. Structural secret regex/markers remain the deterministic guard; this is materially more permissive than the strict smoke-console allowlist path.
- Provider registry environment overrides can change the concrete model but only when the configured value resolves uniquely inside the already-bound provider and route; changing execution class is rejected.
- Enabled external-provider models require concrete pricing, and cache-read input price cannot exceed ordinary input price.
- `context_builder.py` preserves caller block order as priority and drops whole selected blocks rather than truncating content; selected evidence imports the BlueCAD evidence selector, but this file remains the AI context-pack seam rather than engineering-runtime authority.
- `costs.py` pricing is a separate hard-coded estimate registry and character heuristic. It must not be mistaken for provider-registry effective pricing, reservation/settlement, token-flow evidence, or actual billed cost.
- `settings.py` also maps malformed persisted policy-mode values to `FAST_DEV`; this is permissive recovery rather than fail-closed behavior. Its stored `api_spend_month_to_date_usd` is not used as canonical status spend: `project_canonical_ai_status` replaces spend/budget truth with the egress-persistence projection.

## MERGE-BACK REQUIREMENT

Before crediting these rows into `## EXPLICIT FILE COVERAGE LEDGER`, reopen this shard and all source files, fetch the COMPLETE canonical branch document, append monotonically, then refetch and assert all prior 65 canonical ledger paths remain present plus intended additions. Delete/retire this shard only after that verified merge-back.
