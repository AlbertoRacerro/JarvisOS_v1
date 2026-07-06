# 018 — provider gateway v2: cap enforcement, fallback execution, Scaleway retirement

Status: implemented (pending review)
Depends on: 015

## Goal

Complete the provider gateway v2 work on top of spec 015 by fixing stage-1 review findings, enforcing registry-declared provider caps before external execution, executing registry fallback chains through the existing AI spine, and retiring Scaleway from the default runtime registry in favor of DeepSeek and GLM defaults.

## Scope

In scope:
- Fix stage-1 findings: close non-injected `httpx.Client` instances with a context manager, reject duplicate route classes within one model entry, and cover adapter timeouts in tests.
- Enforce each enabled provider's `monthly_token_cap` and `monthly_cost_cap_usd` from `configs/ai_providers.yaml` before any external adapter call. Cap value `0` means unlimited. Usage is computed from existing `ai_jobs` provider usage/cost fields; no new DB/settings fields are added.
- Change fallback-chain config entries to ordered `provider_id/model_id` entries and validate that each entry exists in the enabled model catalog, and that the first entry matches the route's primary binding.
- Execute fallback attempts only after retryable provider errors/timeouts, with one `ai_jobs` row per provider attempt and safe chain metadata in `route_reason_json`.
- Retire Scaleway from default runtime config only. The existing Scaleway modules, adapters, smoke paths, and tests remain in place for compatibility.
- Bind default `external:cheap` to DeepSeek `deepseek-v4-pro` and `external:reasoning` to GLM `glm-5.2`; include Kimi as disabled pending confirmed model ID/key.
- Remove hardcoded Scaleway provider-mode checks from external route gate calls, including the BLUECAD loop.

## Non-goals

- No streaming.
- No new dependencies.
- No Anthropic adapter.
- No deletion of Scaleway or DeepSeek compatibility modules or smoke tests.
- No relaxation of `route_class="auto"`, sensitivity, redaction, paid-AI, budget, or credential gates.
- No frontend provider calls and no provider execution outside `run_ai_task`.
- No new durable secret store.

## Acceptance criteria

1. The generic OpenAI-compatible adapter closes internally-created HTTP clients and maps mocked timeouts to `provider_timeout` with `retryable=True`.
2. The registry rejects duplicate route classes within a single model entry.
3. Disabled providers load but produce no bindings.
4. Fallback-chain validation rejects unknown/disabled entries and first-entry mismatches.
5. Provider token/cost caps block before adapter invocation and write a failed `ai_jobs` row; cap `0` remains unlimited; paid-AI-disabled behavior remains unchanged.
6. Retryable provider errors advance to the next configured fallback entry and write one safe ledger row per attempt; non-retryable errors and pre-provider blocks do not fallback.
7. Default config contains no Scaleway provider entry, binds DeepSeek to `external:cheap`, binds GLM to `external:reasoning`, and keeps safe defaults (`route_class=None` -> `local:fake`, paid AI off, zero budget) unchanged.
8. Existing Scaleway/DeepSeek compatibility tests continue to pass offline.
9. Full backend test gate is green and ruff is clean.
