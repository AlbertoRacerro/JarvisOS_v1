# 015 — PROVIDER-GW-1: provider gateway v1

Status: draft
Depends on: none

## Goal

JarvisOS has a small schema-validated provider gateway that loads provider,
model, route-class, and fallback-chain configuration from
`configs/ai_providers.yaml`, while preserving the existing `run_ai_task` execution
spine, provider-neutral adapter contract, safe defaults, and current default
runtime behavior exactly.

## Why

The current external route path is hardcoded around Scaleway bindings and a small
set of provider adapters. The platform plan requires multiple external providers
and data-driven model economy routing without adopting a large third-party gateway
or creating a parallel call path. This slice moves the existing binding table into
validated config and introduces a generic OpenAI-compatible adapter so cheap and
reasoning external providers can be selected by data, while budget and
RouterPolicy safety gates remain authoritative.

## Scope

In scope:
- Add a provider registry config file at `configs/ai_providers.yaml`, with a
  schema-validated loader and typed runtime objects for:
  - provider id;
  - OpenAI-compatible `base_url`;
  - `api_key_ref` pointing to the secrets module, never an inline secret;
  - model catalog entries;
  - per-model route classes;
  - default `max_tokens`;
  - timeout;
  - per-provider monthly token/cost caps;
  - ordered fallback chains per route class.
- Keep `run_ai_task(adapters=..., bindings=...)` injection and
  `AIProviderAdapter.complete(AIRequest) -> AIResponse` as the only execution
  spine for provider calls.
- Replace the hardcoded default route binding table with bindings derived from
  the loaded registry config, while retaining test injection of explicit
  `bindings` and `adapters`.
- Add one generic `OpenAICompatAdapter(base_url, key_ref, ...)` for
  OpenAI-compatible chat-completions providers, covering Scaleway, DeepSeek
  direct, GLM direct, and Kimi direct by config.
- Keep the existing Scaleway behavior reproducible from the default config,
  including model defaults, route-class defaults, max-token defaults, and blocking
  behavior under safe default settings.
- Make `external:cheap` and `external:reasoning` mappings data in the registry
  config instead of code constants.
- Add data-driven fallback chains for route classes, attempted only after provider
  errors or timeouts.
- Extend `evaluate_ai_status`/budget gating so provider-specific caps are checked
  before any external adapter call, without bypassing the existing paid-AI,
  budget, credential, and policy gates.
- Preserve existing fake/local routes and offline tests.

Out of scope (binding non-goals):
- No new provider call path outside `run_ai_task`.
- No frontend provider calls, direct filesystem access, direct Ollama access, or
  direct execution-tool access.
- No Anthropic adapter in this slice. Anthropic requires a later separate adapter;
  do not model it as OpenAI-compatible.
- No LiteLLM, LangChain, LangGraph, AutoGen, CrewAI, Temporal, Prefect, or other
  new gateway/orchestration dependency.
- No streaming.
- No background workers.
- No provider/model discovery via network.
- No changes that make `route_class="auto"` execute an external provider.
- No redaction engine and no relaxation of sensitivity policy. S3/S4 or pending
  redaction must never reach an external adapter.
- No new secret persistence format beyond references resolved through the existing
  secrets module unless a question below is answered by the maintainer first.

## Files likely touched

Verified against the current code before drafting: `run_ai_task` currently builds
hardcoded defaults in `backend/app/modules/ai/execution.py`; default adapters live
there; existing provider adapters live under `backend/app/modules/ai/providers/`;
Scaleway and DeepSeek each have provider-specific implementations today.

- `configs/ai_providers.yaml` (new default registry config)
- `backend/app/modules/ai/execution.py` (load registry-derived bindings,
  preserve injection seams, implement provider-error fallback loop in the spine)
- `backend/app/modules/ai/budget.py` (extend `evaluate_ai_status` for
  provider-specific registry caps without weakening current gates)
- `backend/app/modules/ai/contracts.py` (only if existing provider/registry
  contracts need typed additions for config-derived metadata or retry/fallback
  outcomes)
- `backend/app/modules/ai/providers/openai_compat_adapter.py` (new generic
  OpenAI-compatible adapter)
- `backend/app/modules/ai/providers/scaleway.py` and/or
  `backend/app/modules/ai/providers/scaleway_adapter.py` (adapt or retire
  Scaleway-specific HTTP envelope only if needed while preserving behavior)
- `backend/app/modules/ai/providers/deepseek.py` and/or
  `backend/app/modules/ai/providers/deepseek_adapter.py` (adapt config-driven
  DeepSeek direct support if needed; existing smoke-path behavior must remain
  covered)
- `backend/app/modules/secrets/storage.py` (only if required to resolve generic
  secret references; no inline secrets)
- New backend module under `backend/app/modules/ai/` for provider registry config
  loading/validation, if that is cleaner than putting it in `execution.py`
- `backend/tests/test_ai_execution_spine.py`
- `backend/tests/test_ai_gateway.py`
- `backend/tests/test_scaleway_adapter.py`
- `backend/tests/test_deepseek_adapter.py`
- New or existing backend tests for provider registry loading, migration parity,
  fallback behavior, and per-provider budget gates

## Design constraints

- **Evolve, do not replace:** `run_ai_task` remains the execution spine, still
  writes one `ai_jobs` row per attempt/result, and still accepts injected
  `adapters` and `bindings` for tests and controlled callers.
- **Adapter contract stays:** providers execute through
  `AIProviderAdapter.complete(AIRequest) -> AIResponse`. Do not introduce a new
  provider interface for this slice.
- **Default config parity:** with the default registry config and no special test
  injection, current default behavior must be reproduced exactly. In particular:
  - `route_class=None` still resolves to `local:fake` for current default task
    kinds;
  - safe defaults still avoid paid external calls;
  - `external:cheap` and `external:reasoning` still resolve to the same effective
    provider/model/max-token defaults as the current hardcoded table, including
    current environment-variable overrides where those overrides are part of
    current behavior;
  - blocked/config-error behavior for missing external credentials and disabled
    paid AI remains unchanged unless the new per-provider cap adds an additional
    block after the old gates would have allowed execution.
- **Config is not secret storage:** `api_key_ref` may name a secret source, but
  the YAML file must never contain raw API keys or bearer tokens.
- **OpenAI-compatible means chat-completions envelope only:** the generic adapter
  should build and parse the existing non-streaming OpenAI-compatible
  chat-completions shape and sanitize metadata before returning `AIResponse`.
- **Fallbacks are narrow:** fallback chains are ordered provider/model choices per
  route class and are attempted only for provider errors/timeouts/retryable
  failures. They are never attempted for malformed route classes, unavailable
  routes, context failures, policy blocks, budget blocks, credential blocks,
  sensitivity/redaction blocks, or user-confirmation/control states.
- **Budget gates stay authoritative:** extend `evaluate_ai_status` or its helper
  path for per-provider caps; do not move budget decisions into adapters as the
  sole enforcement point.
- **Sensitivity gates stay authoritative:** existing RouterPolicy invariants and
  Auto bridge behavior remain unchanged. `route_class="auto"` may not execute an
  external provider, and S3/S4 or pending-redaction material may not reach an
  external adapter.
- **Offline tests only:** tests must use fake/mocked adapters and must not require
  network, live credentials, Ollama, or real external providers.
- **No broad refactor:** avoid renames, file moves, or unrelated provider cleanup
  beyond what is necessary to make registry-driven bindings and generic
  OpenAI-compatible execution work.

## Acceptance criteria

1. `configs/ai_providers.yaml` exists, contains no inline secrets, and defines the
   default fake/local/Scaleway-compatible route bindings needed to reproduce the
   current hardcoded defaults.
2. The provider registry loader validates required fields, rejects malformed route
   classes/provider ids/model entries/fallback references, and returns typed data
   used by the execution spine.
3. `run_ai_task` still accepts injected `adapters` and `bindings`; existing tests
   that rely on injection continue to work.
4. `route_class=None` and all current safe-default settings reproduce current
   behavior exactly, including selected route, provider/model choice, status, and
   no external call.
5. `external:cheap` and `external:reasoning` resolve from config rather than a
   hardcoded table and preserve the current default Scaleway provider/model and
   max-token behavior.
6. A generic OpenAI-compatible adapter can execute a mocked Scaleway/DeepSeek/GLM/Kimi
   style chat-completions response through the existing `AIRequest`/`AIResponse`
   contract without leaking secrets into metadata, logs, responses, or ledger rows.
7. Per-provider budget/token/cost caps block before any external adapter call and
   write the expected failed `ai_jobs` row.
8. Fallback chains attempt the next configured provider only after a retryable
   provider error/timeout, record the final outcome through the spine, and do not
   run on policy, budget, credential, malformed-route, context, sensitivity, or
   confirmation/control blocks.
9. `route_class="auto"` behavior is unchanged: external intent returns a
   non-executing proposal/control state and never invokes an external adapter.
10. Existing provider smoke/adapter tests continue to pass offline with fake or
    mocked providers.

## Required tests

- **Migration parity test:** with the default config and default environment,
  assert that current behavior is reproduced exactly for representative routes:
  `route_class=None`, `local:fake`, `external:cheap`, and `external:reasoning`.
  The test must cover selected route, provider id, model id, max-token default,
  status/blocking behavior, and whether an external adapter was or was not called.
- Registry loader unit tests: valid default config loads; missing required fields,
  malformed route classes, unknown fallback targets, and inline-looking secret
  values are rejected.
- Execution-spine injection test: explicit `adapters` and `bindings` still override
  config-derived defaults for tests.
- OpenAI-compatible adapter tests using mocked HTTP/client behavior: success,
  HTTP error, timeout, malformed response, usage parsing, and safe metadata with no
  secret values.
- Budget-gate tests: per-provider monthly token/cost caps block before adapter
  invocation; paid-AI-disabled and zero-budget behavior remains unchanged.
- Fallback-chain tests: retryable provider error advances to the next configured
  provider; non-retryable provider error and all pre-provider blocks do not
  fallback.
- Auto invariant regression test: an Auto decision with external intent remains
  non-executing and no external adapter is invoked.

## Questions

- The kernel requires `api_key_ref` to point to the secrets module, but the current
  secrets module exposes Scaleway-specific helpers. Should this slice add generic
  secret-ref resolution, or should the default config initially be limited to refs
  that map onto existing Scaleway/DeepSeek env/runtime helpers?
- The kernel requires per-provider monthly token/cost caps, while current persisted
  settings are Scaleway-specific plus global budget fields. Should provider-specific
  cap usage be read only from the YAML/defaults for this slice, or does the
  maintainer want additive settings/schema fields now?
- The kernel says default config must reproduce current behavior byte-for-byte. For
  fallback attempts, should multiple failed provider attempts produce one `ai_jobs`
  row for the final route outcome, one row per attempted provider, or one row with
  structured attempt metadata? Current `run_ai_task` writes one row per call.
- Should the generic OpenAI-compatible adapter replace the existing Scaleway and
  DeepSeek adapters immediately, or should those adapters remain as compatibility
  wrappers around the generic adapter for this slice?
- Which exact secret refs should be reserved in the default config for GLM and Kimi
  direct providers if no current secret-storage helpers exist for them?

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written. Implementation must not proceed from this draft until the
questions above are answered or explicitly accepted as deferred by the maintainer.
