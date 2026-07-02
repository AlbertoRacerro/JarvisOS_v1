# JarvisOS AI Routing and Model Economy

## Current Routing Contract

JarvisOS has two routing modes:

| Mode | Behavior |
| --- | --- |
| Explicit route | User/API supplies a route class; execution bypasses Auto classifier |
| Auto route | Classifier plus RouterPolicy choose a local-only execution or control state |

Default behavior remains safe:

- `route_class=None` resolves to `local:fake`.
- Task-kind defaults remain `local:fake`.
- Cloud routes must be explicitly selected.
- Auto cannot execute external providers.

## Current Route Bindings

Current local bindings in `run_ai_task`:

| Route class | Provider | Default model | Override |
| --- | --- | --- | --- |
| `local:fake` | fake provider | `fake-deterministic-v1` | `AI_ROUTE_FAKE_MODEL` |
| `local:fast` | Ollama | `qwen3:8b` | `AI_ROUTE_LOCAL_FAST_MODEL` |
| `local:general` | Ollama | `gemma4:12b-it-qat` | `AI_ROUTE_LOCAL_GENERAL_MODEL`, else `AI_ROUTE_LOCAL_MODEL` |
| `local:gemma` | Ollama | `gemma4:12b-it-qat` | `AI_ROUTE_LOCAL_GENERAL_MODEL`, else `AI_ROUTE_LOCAL_MODEL` |
| `local:coder` | Ollama | `deepseek-coder-v2:16b` | `AI_ROUTE_LOCAL_CODER_MODEL` |
| `local:coder_heavy` | Ollama | `qwen3-coder:30b` | `AI_ROUTE_LOCAL_CODER_HEAVY_MODEL` |

Cloud bindings exist in execution code:

| Route class | Provider | Default model | Status |
| --- | --- | --- | --- |
| `external:cheap` | Scaleway | `llama-3.1-8b-instruct` or env override | Explicit/manual route only |
| `external:reasoning` | Scaleway | `qwen3-235b-a22b-instruct-2507` | Present binding; production readiness unknown / needs verification |

## Capability Matrix

Auto maps semantic capability to local route:

| Capability row | Local route |
| --- | --- |
| `simple` | `local:fast` |
| `general_reasoning` | `local:general` |
| `coding` | `local:coder` |
| `heavy_coding` | `local:coder_heavy` |
| `deep_reasoning` | `local:general` with `capability_exceeds_local=true` metadata |

Deep reasoning is not currently a trigger for external execution. It is surfaced
as metadata so a future redaction/confirmation path can decide whether cloud
escalation is justified.

## Auto Classifier Role

The local classifier currently outputs advisory fields:

- `task_type`.
- `project_area`.
- `complexity_hint`.
- `needs_context`.
- `sensitivity_hint`.
- `allowed_next_step`.
- `confidence`.

The classifier is explicitly non-authoritative for:

- Risk.
- Permission.
- Provider selection.
- Tool execution.
- Memory write.
- Retrieval.
- Route authority.
- External calls.
- Final sensitivity.
- Safety decisions.

This is a critical contract. The classifier improves usability, but policy and
execution gates remain deterministic JarvisOS responsibilities.

## Auto Permission Input Subtlety

Auto deliberately separates "which local model is useful" from "is execution
allowed." The classifier drives capability and local model selection through the
capability matrix. It does not directly feed RouterPolicy with semantic routing
authority.

Current `build_auto_router_input` is intentionally conservative:

- Router hint is flattened to a local answer posture.
- Task type is represented to RouterPolicy as `answer`.
- Complexity is represented as low.
- Tool, terminal, file-write, state-change, current-info, and provider-call
  needs are false.
- External routing is disabled.
- Provider tiers are limited to local tiers.
- Sensitivity is the main classifier-derived signal passed into the
  permission boundary.

So RouterPolicy is functioning as a deterministic local permission and
sensitivity gate for Auto, while the semantic classifier plus matrix selects the
local model route and records reasons in `auto_metadata`. This is stricter than
"the classifier routes everything" and should be preserved until external
redaction/confirmation exists.

## RouterPolicy and Local Safety

RouterPolicy is the backend canonical producer. The script path is a shim.

Auto execution is allowed only when the bridge sees a safe local decision:

- `route_action` is `answer_local` or `route_local`.
- `route_tier` is `LOCAL_FAST` or `LOCAL_ONLY`.
- No proposed external target.
- Response allowed.
- External/network/tool/state permissions false.
- No side effect.
- Environment is chat.
- Execution mode is `answer_only` or local-only `propose_only`.

This distinction is important: `confidential` and `sensitive_ip` can still be
answered locally when there is no external target or side effect. `secret` stays
blocked. External provider intent stays non-executing.

## Context Economy

Context is budgeted by selected local route and context level:

| Route | None | Light | Standard | Deep |
| --- | ---: | ---: | ---: | ---: |
| `local:fast` | 0 | 4,000 | 6,000 | downgraded |
| `local:general` | 0 | 6,000 | 16,000 | 24,000 |
| `local:coder` | 0 | 4,000 | 10,000 | downgraded |
| `local:coder_heavy` | 0 | 6,000 | 16,000 | 32,000 |

`context_level` is budget/posture only. It is not semantic retrieval. Source
selection remains `budget_only`.

Manual `context_blocks` are preserved and counted before workspace context.
If manual blocks exhaust the budget, workspace context is not added.

## Model Economy View

The current economy is:

| Need | Cheapest acceptable route today |
| --- | --- |
| Safe dev/test | `local:fake` |
| Simple local response | `local:fast` |
| General project reasoning | `local:general` |
| Code review/change reasoning | `local:coder` |
| Heavy coding | `local:coder_heavy`, with local performance risk |
| Deep frontier reasoning | Not automatic; explicit future external escalation |

This is conservative. It prevents accidental cloud spend and data egress, but it
also means some hard tasks get best-effort local answers rather than escalation.

## Key Risks

| Risk | Current mitigation | Remaining gap |
| --- | --- | --- |
| Local model hallucination | Classifier advisory only; ledger metadata | Need grading/success signals |
| Poor model choice | Explicit capability matrix | Need calibration dataset |
| Excess context | Route-aware char budgets | Need semantic source selection |
| Cloud leakage | Auto external impossible | Need redaction and confirmation for future external |
| Cost drift | Default local/fake; explicit cloud | Need full provider cost registry |

## External Escalation Future Path

The right future design is not "if local fails, call cloud." It should be:

1. Detect that the task exceeds local capability.
2. Identify the minimum external capability tier.
3. Determine whether the task contains sensitive/project/IP context.
4. Redact or summarize only if policy allows.
5. Show a confirmation payload with target, cost estimate, context summary, and
   residual risk.
6. Execute only after explicit user or policy approval.
7. Store provider/model/usage/context digests in ledgers.

This preserves the current Auto invariant while still allowing JarvisOS to use
frontier models later.

## Model-Economy Anti-Patterns

| Anti-pattern | Better JarvisOS behavior |
| --- | --- |
| Route by complexity alone | Route by minimum capability, context need, sensitivity, and budget |
| Treat local failure as cloud permission | Return failure/control state; require escalation path |
| Let provider costs live in UI text | Store provider/model cost metadata in backend registry |
| Use one large local model for everything | Use local route matrix and keep fast route hot |
| Hide route choice from user | Return selected route, provider/model, and metadata |
| Optimize before success signals | Add grading/eval before adaptive routing |

The most important economy question is not only dollars. Local models cost time,
VRAM, latency, and user patience. Cloud models cost money, privacy risk, and
policy complexity. JarvisOS needs a route ledger that can compare all of these
costs over time.

## Minimum Useful Metrics

Before adaptive routing, collect:

- Selected route and model.
- Classification source/confidence.
- Context level and budget used.
- Input/output token usage when provider reports it.
- Latency.
- Error type and blocked/control-state reason.
- User correction or acceptance signal.
- Whether local capability was marked exceeded.

These metrics are enough to start evaluating model economy without granting the
router autonomous cost optimization.
