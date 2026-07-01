# Semantic Routing Giants Reference Audit

## Status

Docs-only reference audit.

This document does not add runtime authority, provider execution, retrieval,
memory injection, UI, database schema, external calls, or dependencies.

## Inspected Sources

All sources are local checkouts under
`C:\Users\thera\Documents\JarvisOS_external_refs`.

| Reference | Local path | Commit | License finding | Reuse stance |
| --- | --- | --- | --- | --- |
| RouteLLM | `routing\RouteLLM` | `0b64fdafe049e596a3f5657c219329f24af24198` | Apache-2.0 | Adapt scoring/evaluation contracts, not runtime dispatch |
| LiteLLM | `litellm` | `84c1414aef6732254d7ec17c544b6b77cb90d460` | MIT outside `enterprise/` | Strongest source for routing-strategy seams and metadata patterns |
| AutoGen | `autogen` | `027ecf0a379bcc1d09956d46d12d44a3ad9cee14` | MIT for code via `LICENSE-CODE` | Adapt classifier/registry separation |
| LlamaIndex | `llama_index` | `9f66e8a649856524ef0ff081a23d58cd071b6ae4` | MIT | Adapt selector result/reason metadata pattern |
| Open WebUI | `open-webui` | `02dc3e689ceac915a870b373318b99c029ddf603` | Multi-license with current Open WebUI License restrictions | Architecture reference only; do not copy current code |
| DSPy | `dspy` | `498760149b230f402c56bece2aa45df6e1ba946b` | Apache-2.0 in root license | Future eval/optimization reference only |

## Executive Verdict

The useful architecture is not "one smart router decides everything".

The useful architecture is a pipeline of narrow contracts:

```text
prompt extraction
-> semantic classification
-> capability row
-> policy/safety gate
-> local/external eligibility
-> context permission and budget
-> concrete provider/model execution
-> metadata and feedback
```

For JarvisOS, the classifier must remain advisory. RouterPolicy and existing
provider gates remain the authority for safety and execution permission.

## RouteLLM Findings

Relevant files:

- `routellm/controller.py`
- `routellm/routers/routers.py`
- `routellm/calibrate_threshold.py`
- `routellm/evals/evaluate.py`
- `examples/routing_to_local_models.md`
- `LICENSE`

Transferable patterns:

- Separate `route(prompt)` from `completion(...)`.
- Keep strong/weak model selection behind a narrow router interface.
- Treat thresholds as calibrated operating points, not magic constants.
- Benchmark routers as curves against baselines.
- Preserve route counts by model/router for later calibration.

Non-transferable patterns:

- Strong/weak external model routing cannot bypass JarvisOS policy gates.
- `model="router-name-threshold"` should not become a JarvisOS API contract.
- MF/BERT/causal/embedding routers pull in model checkpoints, Hugging Face
  datasets, or OpenAI embeddings. That is too heavy for the current Auto bridge.

JarvisOS adaptation:

- Keep the current `capability -> local_route_class` matrix small and explicit.
- Add calibration later using JarvisOS success/failure evidence.
- Do not add threshold routing until there is an offline benchmark harness.

## LiteLLM Findings

Relevant files:

- `litellm/router_strategy/complexity_router/config.py`
- `litellm/router_strategy/complexity_router/complexity_router.py`
- `litellm/router_strategy/auto_router/auto_router.py`
- `litellm/router_strategy/adaptive_router/classifier.py`
- `litellm/router_strategy/adaptive_router/adaptive_router.py`
- `litellm/router_strategy/adaptive_router/bandit.py`
- `litellm/router_strategy/adaptive_router/signals.py`
- `litellm/types/router.py`
- `tests/test_litellm/router_strategy/test_complexity_router.py`
- `tests/test_litellm/router_strategy/adaptive_router/test_classifier.py`
- `tests/test_litellm/router_strategy/test_auto_router.py`
- `LICENSE`

Transferable patterns:

- `PreRoutingHookResponse` changes only `model` and `messages`. This is a clean
  seam: routing mutates the intended target, not provider internals.
- `RequestType` taxonomy is fixed and versionable.
- `AdaptiveRouterPreferences` separates model quality tier from model strengths.
- Complexity routing returns a tier, score, and triggered signals. The signals
  are important because they make a route inspectable.
- The adaptive router separates pre-routing choice from post-call feedback.
- Bandit feedback uses cold-start priors and bounded updates, not instant
  self-trust.
- Signal detection is intentionally O(1) per turn and bounded by small state.
- Tests cover classifier determinism, input truncation, exact request type, and
  no-dependency text extraction.

Copy/adapt candidates:

- Fixed taxonomy shape:

```text
RequestType:
  code_generation
  code_understanding
  technical_design
  analytical_reasoning
  writing
  factual_lookup
  general
```

- Model preference shape:

```text
model_name
quality_tier
strengths: list[RequestType]
cost estimate
```

- Classifier output should include:

```text
request_type
confidence
signals
reason
source
```

Do not copy now:

- Redis/Postgres update queues.
- Proxy lifecycle.
- Multi-tenant budget sync.
- Enterprise code under `enterprise/`.
- Adaptive bandit updates before JarvisOS has reliable success signals.

JarvisOS adaptation:

- Use LiteLLM's taxonomy/metadata style to harden `auto_metadata`.
- Keep bandit/adaptive routing as a future milestone after grading/success
  signals exist.
- Add tests for:
  - deterministic classification;
  - long input truncation/fallback;
  - last user message extraction;
  - route metadata includes signals and reasons;
  - control states never execute.

## AutoGen Findings

Relevant files:

- `python/samples/core_semantic_router/README.md`
- `python/samples/core_semantic_router/_semantic_router_components.py`
- `python/samples/core_semantic_router/_semantic_router_agent.py`
- `LICENSE-CODE`

Transferable patterns:

- `IntentClassifierBase` is separate from `AgentRegistryBase`.
- The router identifies intent, then looks up the target in a registry.
- Missing target routes to termination/control state, not silent fallback.
- The semantic router is a replaceable worker component, not embedded in every
  agent.

Non-transferable patterns:

- The sample classifier is keyword-only and too simple.
- The distributed runtime/event topology is unnecessary for JarvisOS Auto now.

JarvisOS adaptation:

```text
SemanticClassifier
-> CapabilityRegistry
-> PolicyGate
-> ExecutionBridge
```

Missing capability or external proposal should produce a non-executing control
state, not a hidden generic local answer.

## LlamaIndex Findings

Relevant files:

- `llama-index-core/llama_index/core/base/base_selector.py`
- `llama-index-core/llama_index/core/selectors/llm_selectors.py`
- `llama-index-core/llama_index/core/selectors/pydantic_selectors.py`
- `llama-index-core/llama_index/core/query_engine/router_query_engine.py`
- `llama-index-core/llama_index/core/retrievers/router_retriever.py`
- `LICENSE`

Transferable patterns:

- Candidates are described through metadata before selection.
- Selector output carries selected index plus reason.
- Router execution stores `selector_result` in final response metadata.
- Single-select and multi-select are distinct interfaces.
- Source/tool selection is a separate concern from final response synthesis.

Critical JarvisOS lesson:

`context_level` is not intelligent memory selection.

It is only a budget/posture selector unless JarvisOS also has:

- candidate source metadata;
- a selector contract;
- selection reasons;
- tests proving irrelevant sources are not injected.

JarvisOS adaptation:

- For `ROUTER-MATRIX-0`, add context level and budget metadata only.
- Defer real source selection to a later source-selector milestone.
- When source selection arrives, use a LlamaIndex-like contract:

```text
ContextCandidate:
  id
  kind
  workspace_id
  description
  estimated_chars
  freshness
  sensitivity

ContextSelection:
  candidate_id
  reason
```

## Open WebUI Findings

Relevant files:

- `backend/open_webui/routers/ollama.py`
- `backend/open_webui/routers/openai.py`
- `backend/open_webui/routers/models.py`
- `LICENSE`
- `LICENSE_NOTICE`
- `LICENSE_HISTORY`

Transferable patterns:

- Backend owns provider/model inventory. Frontend does not call Ollama/OpenAI
  directly.
- Model lists can be merged from multiple backends while preserving origin.
- Loaded model status is read separately from installed model tags.
- Access control and model availability are separate gates.

Non-transferable patterns:

- Do not copy current Open WebUI code because the current license is restrictive
  and multi-phase.
- Do not add pull/unload/lifecycle endpoints in this milestone.
- Do not expose provider secrets or provider base URL editing in the Auto UI.

JarvisOS adaptation:

- Keep local runtime status read-only until lifecycle is explicitly approved.
- If multi-Ollama support is ever added, copy the concept of preserving source
  backend identity, not Open WebUI implementation.

## DSPy Finding

Relevant files:

- `dspy/clients/_litellm.py`
- `dspy/clients/provider.py`

Transferable pattern:

- Optional dependencies should be lazy-loaded behind a helper and configured once.
- Provider/client abstractions should stay resilient when optional runtimes are
  absent.

JarvisOS adaptation:

- DSPy is not a current JarvisOS dependency or routing architecture.
- Treat DSPy as a possible future reference for evaluation/optimization only.
- If `semantic_router`, LiteLLM, DSPy, or other optional routing packages are
  tested later, keep them out of import-time paths and behind explicit adapters.

## Critique of Current BRIDGE-1b Direction

Current BRIDGE-1b is directionally good because it:

- keeps Auto local-only;
- routes control states without provider calls;
- separates semantic classification from RouterPolicy execution permission;
- exposes metadata.

Weaknesses to address before stabilizing:

- `capability -> route` exists, but `capability + route -> context_budget` does
  not.
- `context_level` is not yet a first-class field.
- `deep` context must not be selected by `complexity_hint` alone.
- Manual context blocks must remain preserved and separately bounded.
- There is no source selector yet; do not present budget scaling as memory
  intelligence.
- Classifier confidence/fallback should downgrade context ambition.
- External API/provider intent must remain a control state, not a local answer.

## Recommended JarvisOS Contract

Use a three-axis routing result:

```text
semantic:
  request_type
  project_area
  complexity_hint
  confidence
  signals

capability:
  row
  local_route_class
  would_benefit_from_external

context:
  permission
  level
  budget_chars
  reason
  source_selection_status
```

Provider-agnostic semantic routing should select a capability row. A separate
policy gate should select whether any external provider is allowed. A separate
context policy should decide how much workspace context can be added.

## Code Reuse Decision

No external code is copied by this audit.

Future code copying is allowed only in an explicit implementation slice and must
include:

- exact upstream file path and commit;
- license compatibility check;
- retained copyright/license notice where required;
- modification note;
- JarvisOS-specific tests;
- no import-time provider/network behavior.

At this milestone, adaptation is safer than vendoring.

## Next Slice

Implement `ROUTER-MATRIX-0` as a small JarvisOS-owned contract:

- semantic capability matrix;
- context level policy;
- model-aware context budget;
- metadata fields;
- offline tests;
- no source selection;
- no external execution;
- no adaptive learning.
