# Area A capability-map increment 24

MAPPING_STATUS: IN_PROGRESS
UNACCOUNTED_FILES: >0

This additive shard preserves the protected canonical ledger while recording newly reopened source coverage from fresh `master`.

## EXPLICIT FILE COVERAGE LEDGER

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/ai/gateway.py` | READ | Public AI gateway/facade. Resolves task route class, delegates `auto` routing, prechecks external-provider status, optionally assembles workspace context within the remaining character budget, then delegates execution to `run_ai_task`; also exposes smoke/public-test entrypoints and a legacy modeling-draft path using the fake provider with event logging and budget-aware blocking/fallback. |

## Runtime notes / failure boundaries

- `run_task` defaults project-context workspace to `bluerev` only when project context is requested. Explicit/manual context is serialized to estimate consumed character budget; workspace context receives only the remainder and is appended after manual blocks.
- Workspace-context construction exceptions are converted to a `workspace_context_build_failed: <ExceptionType>` signal passed into `run_ai_task`, rather than leaking the exception directly from the gateway.
- External routes are status-prechecked here, but the gateway is not the final egress authority: binding/policy/sanitization/confirmation/accounting enforcement remains downstream.
- The legacy `create_modeling_draft` path is structurally separate from `run_task`: it validates workspace existence, evaluates provider/budget status, can fall back from blocked Scaleway to the fake provider when configured, and records attempt/completion/block events.
- Failure/maintenance boundary: broad exception capture around workspace-context construction intentionally degrades to an error signal, so the concrete underlying exception is reduced to its type at this layer; diagnosis depends on downstream/logging observability rather than a propagated traceback.

Canonical `docs/agent-manual/parts/A-product-backend-ai-data.md` intentionally unchanged in this increment.