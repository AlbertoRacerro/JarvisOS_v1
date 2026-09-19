# Area A capability-map increment 25

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard preserves the protected canonical ledger while recording newly reopened source coverage from fresh `master`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/deepseek_provider_smoke.py` | READ | DeepSeek-only diagnostic smoke surface. Applies settings/provider-mode, prompt-size/output-token and privacy gates before delegating actual external execution to canonical `run_ai_task`; translates execution outcomes into smoke responses and persists started/blocked/completed event telemetry. |

## Runtime notes / failure boundaries

- The smoke surface is diagnostic rather than an independent provider-routing or egress implementation: `run_ai_task` remains the external-dispatch authority.
- It fails closed before dispatch when AI policy is disabled, provider mode is not `deepseek`, the prompt is empty/over 1000 characters, requested output exceeds 160 tokens, or privacy policy does not allow a `public`/`internal` prompt.
- Route identity is resolved from the canonical `external:deepseek` binding, but absence of a binding falls back to display identity `deepseek` / `deepseek-v4-pro`; actual execution still goes through `run_ai_task`, so that fallback does not itself create a dispatch binding.
- Started, blocked and completed events are each written through a fresh SQLite connection and committed independently. Event persistence is therefore not transactionally coupled to provider execution; logging failure can surface separately from the external-call result.
- `external_call_attempted` defaults to true for a non-null AI response unless provider metadata explicitly says otherwise. This is an observability convention, not direct proof that network dispatch occurred.
- Reported token metadata is converted with `int()` and malformed values degrade to `None`; usage-source and estimated counts remain available in the response/event payload.

Canonical `docs/agent-manual/parts/A-product-backend-ai-data.md` intentionally unchanged in this increment.
