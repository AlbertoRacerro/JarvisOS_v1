# Factual extraction, no decisions — input for spec 010 design

Source assumption rows: A5 asks whether the provider-call path supports a multi-step generate/build/validate/repair loop with an attempt ledger, and A6 asks whether the sandboxed runner can host build123d L2 scripts. `docs/strategy/BLUECAD_CORE_DESIGN.md:385`, `docs/strategy/BLUECAD_CORE_DESIGN.md:386`

## 1. Provider call execution path

### RouterPolicy / `auto` path

- Public entrypoint: `def run_ai_task_endpoint(payload: AITaskRunRequest) -> AITaskRunResponse:` calls `AIGateway().run_task(payload)`. `backend/app/modules/ai/routes.py:48`, `backend/app/modules/ai/routes.py:49`, `backend/app/modules/ai/routes.py:50`, `backend/app/modules/ai/routes.py:51`
- Request shape: `class AITaskRunRequest(BaseModel):` exposes `prompt`, `route_class`, `task_kind`, `max_tokens`, `context_blocks`, `include_project_context`, and `workspace_id`; it has no confirmation digest, consent token, or confirmed decision field. `backend/app/modules/ai/models.py:121`, `backend/app/modules/ai/models.py:124`, `backend/app/modules/ai/models.py:125`, `backend/app/modules/ai/models.py:126`, `backend/app/modules/ai/models.py:127`, `backend/app/modules/ai/models.py:128`, `backend/app/modules/ai/models.py:129`, `backend/app/modules/ai/models.py:130`
- `def run_task(self, request: AITaskRunRequest) -> AITaskRunResponse:` routes `route_class == "auto"` to `run_auto_task(request)` and returns immediately. `backend/app/modules/ai/gateway.py:58`, `backend/app/modules/ai/gateway.py:67`, `backend/app/modules/ai/gateway.py:71`, `backend/app/modules/ai/gateway.py:72`, `backend/app/modules/ai/gateway.py:74`
- `def build_auto_decision_bundle(...) -> AutoDecisionBundle:` classifies the request, maps capability to a local route, builds RouterPolicy input, calls `decide_router_policy(router_input, now=now)` when no control status exists, and returns an `AutoDecisionBundle`. `backend/app/modules/ai/routing/bridge.py:163`, `backend/app/modules/ai/routing/bridge.py:169`, `backend/app/modules/ai/routing/bridge.py:171`, `backend/app/modules/ai/routing/bridge.py:172`, `backend/app/modules/ai/routing/bridge.py:173`, `backend/app/modules/ai/routing/bridge.py:175`, `backend/app/modules/ai/routing/bridge.py:176`, `backend/app/modules/ai/routing/bridge.py:179`, `backend/app/modules/ai/routing/bridge.py:186`
- RouterPolicy producer scope is explicitly non-executing: the module docstring says it produces decision objects and "does not route chat, call providers or models, execute tools, browse, run terminal commands, write files or memory, or retrieve data." `backend/app/modules/ai/routing/decision.py:1`, `backend/app/modules/ai/routing/decision.py:3`, `backend/app/modules/ai/routing/decision.py:4`, `backend/app/modules/ai/routing/decision.py:5`
- RouterPolicy external candidate path sets `route_action = "ask_user_confirm"`, `provider_candidate = "none"`, `external_allowed = False`, and `allowed_execution_mode = "propose_only"`; when confirmation is required it adds a payload, `confirmation_options = ["allow_once", "deny", "view_details"]`, and a digest. `backend/app/modules/ai/routing/decision.py:502`, `backend/app/modules/ai/routing/decision.py:509`, `backend/app/modules/ai/routing/decision.py:511`, `backend/app/modules/ai/routing/decision.py:512`, `backend/app/modules/ai/routing/decision.py:513`, `backend/app/modules/ai/routing/decision.py:514`, `backend/app/modules/ai/routing/decision.py:516`, `backend/app/modules/ai/routing/decision.py:523`, `backend/app/modules/ai/routing/decision.py:524`, `backend/app/modules/ai/routing/decision.py:525`, `backend/app/modules/ai/routing/decision.py:526`, `backend/app/modules/ai/routing/decision.py:527`, `backend/app/modules/ai/routing/decision.py:528`
- Runtime invariant function exists: `def validate_router_decision_for_runtime(decision: dict[str, Any]) -> RouterDecisionInvariantResult:` rejects `ask_user_confirm` decisions that allow provider execution, rejects `propose_only` decisions that allow provider execution or state change, and rejects external candidate/proposal decisions that imply immediate provider or network execution. `backend/app/modules/ai/routing/invariants.py:24`, `backend/app/modules/ai/routing/invariants.py:47`, `backend/app/modules/ai/routing/invariants.py:48`, `backend/app/modules/ai/routing/invariants.py:50`, `backend/app/modules/ai/routing/invariants.py:51`, `backend/app/modules/ai/routing/invariants.py:52`, `backend/app/modules/ai/routing/invariants.py:53`, `backend/app/modules/ai/routing/invariants.py:54`, `backend/app/modules/ai/routing/invariants.py:71`, `backend/app/modules/ai/routing/invariants.py:72`, `backend/app/modules/ai/routing/invariants.py:73`
- Runtime use of that invariant in `AIGateway.run_task` does not exist: `run_task` either dispatches `auto` to `run_auto_task` or explicit routes to `run_ai_task`; it does not call `validate_router_decision_for_runtime`. `backend/app/modules/ai/gateway.py:58`, `backend/app/modules/ai/gateway.py:71`, `backend/app/modules/ai/gateway.py:74`, `backend/app/modules/ai/gateway.py:76`, `backend/app/modules/ai/gateway.py:103`, `backend/app/modules/ai/gateway.py:111`
- `auto` execution guard: `def _is_auto_local_safe(decision: dict) -> bool:` returns true only when route action/tier are local, no external target exists, `provider_call_allowed_now` and `external_network_allowed_now` are false, tool/state execution are false, and execution mode is answer/propose only. `backend/app/modules/ai/routing/bridge.py:521`, `backend/app/modules/ai/routing/bridge.py:529`, `backend/app/modules/ai/routing/bridge.py:531`, `backend/app/modules/ai/routing/bridge.py:532`, `backend/app/modules/ai/routing/bridge.py:533`, `backend/app/modules/ai/routing/bridge.py:536`, `backend/app/modules/ai/routing/bridge.py:537`, `backend/app/modules/ai/routing/bridge.py:538`, `backend/app/modules/ai/routing/bridge.py:539`, `backend/app/modules/ai/routing/bridge.py:543`
- If `_is_executable_auto_local(decision)` is true, `resolve_bridge_outcome_from_decision` calls `run_ai_task` with `route_class=selected_auto_route_class` or a local fallback; if false, it writes an auto control `ai_jobs` row and returns a control response with `provider_id=None`, `model_id=None`, and `usage=None`. `backend/app/modules/ai/routing/bridge.py:312`, `backend/app/modules/ai/routing/bridge.py:327`, `backend/app/modules/ai/routing/bridge.py:328`, `backend/app/modules/ai/routing/bridge.py:329`, `backend/app/modules/ai/routing/bridge.py:332`, `backend/app/modules/ai/routing/bridge.py:344`, `backend/app/modules/ai/routing/bridge.py:346`, `backend/app/modules/ai/routing/bridge.py:355`, `backend/app/modules/ai/routing/bridge.py:362`, `backend/app/modules/ai/routing/bridge.py:363`, `backend/app/modules/ai/routing/bridge.py:364`
- Therefore, an actual external HTTP call from a RouterPolicy `auto` decision does not exist in the inspected runtime path. `backend/app/modules/ai/routing/bridge.py:328`, `backend/app/modules/ai/routing/bridge.py:332`, `backend/app/modules/ai/routing/bridge.py:346`, `backend/app/modules/ai/routing/bridge.py:362`, `backend/app/modules/ai/routing/bridge.py:363`, `backend/app/modules/ai/routing/bridge.py:364`

Verbatim signatures:

```python
def run_ai_task_endpoint(payload: AITaskRunRequest) -> AITaskRunResponse:
```

`backend/app/modules/ai/routes.py:49`

```python
def run_task(self, request: AITaskRunRequest) -> AITaskRunResponse:
```

`backend/app/modules/ai/gateway.py:58`

```python
def build_auto_decision_bundle(
    request: AITaskRunRequest,
    *,
    now: str | None = None,
    classifier_func: ClassifyFunc | None = None,
) -> AutoDecisionBundle:
```

`backend/app/modules/ai/routing/bridge.py:163`, `backend/app/modules/ai/routing/bridge.py:164`, `backend/app/modules/ai/routing/bridge.py:165`, `backend/app/modules/ai/routing/bridge.py:166`, `backend/app/modules/ai/routing/bridge.py:167`, `backend/app/modules/ai/routing/bridge.py:168`

```python
def decide_router_policy(input_obj: dict, now: str | None = None) -> dict:
```

`backend/app/modules/ai/routing/decision.py:572`

```python
def validate_router_decision_for_runtime(decision: dict[str, Any]) -> RouterDecisionInvariantResult:
```

`backend/app/modules/ai/routing/invariants.py:24`

### Explicit `external:*` provider path

- Explicit external routing is not a RouterPolicy approval replay: `AIGateway.run_task` checks `selected_route_class.startswith("external:")`, evaluates settings with `evaluate_ai_status(settings, "scaleway")`, sets `external_blocked_reason` when not allowed, and still calls `run_ai_task` with the selected route. `backend/app/modules/ai/gateway.py:67`, `backend/app/modules/ai/gateway.py:76`, `backend/app/modules/ai/gateway.py:77`, `backend/app/modules/ai/gateway.py:78`, `backend/app/modules/ai/gateway.py:79`, `backend/app/modules/ai/gateway.py:80`, `backend/app/modules/ai/gateway.py:103`, `backend/app/modules/ai/gateway.py:106`, `backend/app/modules/ai/gateway.py:109`
- Settings gate: `def evaluate_ai_status(settings: AISettingsRead, provider_mode: str | None = None) -> AIStatusRead:` allows Scaleway external calls only when Scaleway is enabled, smoke/live flags are enabled, key is present, paid AI and budget are enabled, token caps are positive and not exhausted, and `scaleway_live_smoke_test_enabled` is true. `backend/app/modules/ai/budget.py:15`, `backend/app/modules/ai/budget.py:27`, `backend/app/modules/ai/budget.py:28`, `backend/app/modules/ai/budget.py:30`, `backend/app/modules/ai/budget.py:32`, `backend/app/modules/ai/budget.py:34`, `backend/app/modules/ai/budget.py:36`, `backend/app/modules/ai/budget.py:38`, `backend/app/modules/ai/budget.py:40`, `backend/app/modules/ai/budget.py:42`, `backend/app/modules/ai/budget.py:44`, `backend/app/modules/ai/budget.py:46`, `backend/app/modules/ai/budget.py:48`, `backend/app/modules/ai/budget.py:49`
- `def run_ai_task(...) -> AiTaskOutcome:` normalizes context, resolves route binding, checks `external_blocked_reason`, checks Scaleway key readiness, builds an `AIRequest`, then calls `adapter.complete(request)`. `backend/app/modules/ai/execution.py:274`, `backend/app/modules/ai/execution.py:315`, `backend/app/modules/ai/execution.py:316`, `backend/app/modules/ai/execution.py:364`, `backend/app/modules/ai/execution.py:390`, `backend/app/modules/ai/execution.py:394`, `backend/app/modules/ai/execution.py:402`, `backend/app/modules/ai/execution.py:425`, `backend/app/modules/ai/execution.py:426`, `backend/app/modules/ai/execution.py:428`, `backend/app/modules/ai/execution.py:459`, `backend/app/modules/ai/execution.py:467`
- Binding table maps `external:cheap` and `external:reasoning` to `SCALEWAY_PROVIDER_ID`, marks them `requires_network=True`, and assigns model/max-token defaults. `backend/app/modules/ai/execution.py:142`, `backend/app/modules/ai/execution.py:143`, `backend/app/modules/ai/execution.py:144`, `backend/app/modules/ai/execution.py:145`, `backend/app/modules/ai/execution.py:146`, `backend/app/modules/ai/execution.py:149`, `backend/app/modules/ai/execution.py:150`, `backend/app/modules/ai/execution.py:151`, `backend/app/modules/ai/execution.py:152`, `backend/app/modules/ai/execution.py:153`
- Default adapters include `SCALEWAY_PROVIDER_ID: ScalewayProviderAdapter()`, not `DeepSeekProviderAdapter`. `backend/app/modules/ai/execution.py:159`, `backend/app/modules/ai/execution.py:160`, `backend/app/modules/ai/execution.py:161`, `backend/app/modules/ai/execution.py:162`, `backend/app/modules/ai/execution.py:163`
- `ScalewayProviderAdapter.complete` selects `create_work_completion` for synthesis/code_review/decision_support tasks, catches provider errors, and converts the provider result to `AIResponse`. `backend/app/modules/ai/providers/scaleway_adapter.py:27`, `backend/app/modules/ai/providers/scaleway_adapter.py:28`, `backend/app/modules/ai/providers/scaleway_adapter.py:29`, `backend/app/modules/ai/providers/scaleway_adapter.py:30`, `backend/app/modules/ai/providers/scaleway_adapter.py:53`, `backend/app/modules/ai/providers/scaleway_adapter.py:61`, `backend/app/modules/ai/providers/scaleway_adapter.py:62`, `backend/app/modules/ai/providers/scaleway_adapter.py:74`, `backend/app/modules/ai/providers/scaleway_adapter.py:75`, `backend/app/modules/ai/providers/scaleway_adapter.py:76`, `backend/app/modules/ai/providers/scaleway_adapter.py:88`
- Actual external HTTP call: `ScalewayProvider._create_chat_completion` builds an OpenAI-compatible payload and calls `httpx.post(self.chat_completions_url(), headers=..., json=payload, timeout=20)`. `backend/app/modules/ai/providers/scaleway.py:86`, `backend/app/modules/ai/providers/scaleway.py:94`, `backend/app/modules/ai/providers/scaleway.py:98`, `backend/app/modules/ai/providers/scaleway.py:99`, `backend/app/modules/ai/providers/scaleway.py:101`, `backend/app/modules/ai/providers/scaleway.py:108`, `backend/app/modules/ai/providers/scaleway.py:109`, `backend/app/modules/ai/providers/scaleway.py:110`, `backend/app/modules/ai/providers/scaleway.py:113`, `backend/app/modules/ai/providers/scaleway.py:114`, `backend/app/modules/ai/providers/scaleway.py:115`, `backend/app/modules/ai/providers/scaleway.py:119`, `backend/app/modules/ai/providers/scaleway.py:120`

Verbatim signatures:

```python
def run_ai_task(
    *,
    user_prompt: str,
    task_kind: str = "general",
    route_class: str | None = None,
    context_blocks: list[dict[str, object]] | None = None,
    max_output_tokens: int | None = None,
    adapters: dict[str, AIProviderAdapter] | None = None,
    bindings: dict[str, ProviderBinding] | None = None,
    external_blocked_reason: str | None = None,
    context_build_error: str | None = None,
) -> AiTaskOutcome:
```

`backend/app/modules/ai/execution.py:274`, `backend/app/modules/ai/execution.py:275`, `backend/app/modules/ai/execution.py:276`, `backend/app/modules/ai/execution.py:277`, `backend/app/modules/ai/execution.py:278`, `backend/app/modules/ai/execution.py:279`, `backend/app/modules/ai/execution.py:280`, `backend/app/modules/ai/execution.py:281`, `backend/app/modules/ai/execution.py:282`, `backend/app/modules/ai/execution.py:283`, `backend/app/modules/ai/execution.py:284`, `backend/app/modules/ai/execution.py:285`

```python
def complete(self, request: AIRequest) -> AIResponse:
```

`backend/app/modules/ai/providers/scaleway_adapter.py:53`

```python
def create_work_completion(self, *, prompt: str, estimated_output_tokens: int) -> ScalewayChatResult:
```

`backend/app/modules/ai/providers/scaleway.py:78`

```python
def _create_chat_completion(
    self,
    *,
    prompt: str,
    estimated_output_tokens: int,
    system_prompt: str,
    mode: str,
) -> ScalewayChatResult:
```

`backend/app/modules/ai/providers/scaleway.py:86`, `backend/app/modules/ai/providers/scaleway.py:87`, `backend/app/modules/ai/providers/scaleway.py:88`, `backend/app/modules/ai/providers/scaleway.py:89`, `backend/app/modules/ai/providers/scaleway.py:90`, `backend/app/modules/ai/providers/scaleway.py:91`, `backend/app/modules/ai/providers/scaleway.py:92`, `backend/app/modules/ai/providers/scaleway.py:93`

## 2. Multi-step orchestration

- Multi-step generate/execute/validate/retry infrastructure for BLUECAD does not exist in the inspected modules; the only BLUECAD generate/repair loop references are in the strategy document, not in `backend/app/modules`. `docs/strategy/BLUECAD_CORE_DESIGN.md:278`, `docs/strategy/BLUECAD_CORE_DESIGN.md:284`, `docs/strategy/BLUECAD_CORE_DESIGN.md:287`, `docs/strategy/BLUECAD_CORE_DESIGN.md:291`, `docs/strategy/BLUECAD_CORE_DESIGN.md:300`, `docs/strategy/BLUECAD_CORE_DESIGN.md:301`, `docs/strategy/BLUECAD_CORE_DESIGN.md:302`
- Agent infrastructure shape is only a protocol and name registry: `class Agent(Protocol):` has `name` and `capabilities`, and `class AgentRegistry:` only stores agents, registers by name, and lists names. `backend/app/modules/agents/base.py:5`, `backend/app/modules/agents/base.py:6`, `backend/app/modules/agents/base.py:11`, `backend/app/modules/agents/base.py:12`, `backend/app/modules/agents/base.py:13`, `backend/app/modules/agents/registry.py:6`, `backend/app/modules/agents/registry.py:7`, `backend/app/modules/agents/registry.py:8`, `backend/app/modules/agents/registry.py:10`, `backend/app/modules/agents/registry.py:13`
- Tool infrastructure shape is only a protocol and name registry: `class Tool(Protocol):` defines `name` and `run(payload)`, and `class ToolRegistry:` only stores, registers, and lists tools. `backend/app/modules/tools/base.py:5`, `backend/app/modules/tools/base.py:6`, `backend/app/modules/tools/base.py:11`, `backend/app/modules/tools/base.py:12`, `backend/app/modules/tools/base.py:14`, `backend/app/modules/tools/registry.py:6`, `backend/app/modules/tools/registry.py:7`, `backend/app/modules/tools/registry.py:8`, `backend/app/modules/tools/registry.py:10`, `backend/app/modules/tools/registry.py:13`
- Runner job lifecycle exists for one queued local Python execution, not for AI repair loops: `create_runner_job` creates one `simulation_runs` row and one `runner_jobs` row, and `run_runner_job` rejects jobs not in `queued` state. `backend/app/modules/runner/service.py:156`, `backend/app/modules/runner/service.py:171`, `backend/app/modules/runner/service.py:194`, `backend/app/modules/runner/service.py:255`, `backend/app/modules/runner/service.py:262`, `backend/app/modules/runner/service.py:263`
- Runner persistence records job status transitions, logs, output payload, and artifacts, but no retry counter, tier ladder, validation report link, repair prompt, or attempt graph field exists in `runner_jobs`, `simulation_runs`, or `run_artifacts` schema. `backend/app/core/schema.py:199`, `backend/app/core/schema.py:200`, `backend/app/core/schema.py:204`, `backend/app/core/schema.py:205`, `backend/app/core/schema.py:207`, `backend/app/core/schema.py:217`, `backend/app/core/schema.py:218`, `backend/app/core/schema.py:222`, `backend/app/core/schema.py:223`, `backend/app/core/schema.py:225`, `backend/app/core/schema.py:255`, `backend/app/core/schema.py:258`, `backend/app/core/schema.py:259`, `backend/app/core/schema.py:260`

Verbatim signatures:

```python
class Agent(Protocol):
```

`backend/app/modules/agents/base.py:11`

```python
class AgentRegistry:
```

`backend/app/modules/agents/registry.py:7`

```python
class Tool(Protocol):
```

`backend/app/modules/tools/base.py:11`

```python
def run(self, payload: dict[str, object]) -> ToolResult:
```

`backend/app/modules/tools/base.py:14`

```python
class ToolRegistry:
```

`backend/app/modules/tools/registry.py:7`

## 3. Attempt/cost ledger

- `ai_jobs` is the AI execution ledger table: fields are `id`, `created_at`, `status`, `task_kind`, requested/selected route, provider/model, route reason JSON, prompt/context/output digests, token counts, cost estimate, latency, and error type. `backend/app/core/schema.py:285`, `backend/app/core/schema.py:286`, `backend/app/core/schema.py:287`, `backend/app/core/schema.py:288`, `backend/app/core/schema.py:289`, `backend/app/core/schema.py:290`, `backend/app/core/schema.py:291`, `backend/app/core/schema.py:292`, `backend/app/core/schema.py:293`, `backend/app/core/schema.py:294`, `backend/app/core/schema.py:295`, `backend/app/core/schema.py:296`, `backend/app/core/schema.py:297`, `backend/app/core/schema.py:298`, `backend/app/core/schema.py:299`, `backend/app/core/schema.py:300`, `backend/app/core/schema.py:301`, `backend/app/core/schema.py:302`, `backend/app/core/schema.py:303`
- Write path: `def _write_ai_job(...) -> str:` inserts one `ai_jobs` row with provider/model, digests, input/output tokens, cost estimate, latency, and error type. `backend/app/modules/ai/execution.py:204`, `backend/app/modules/ai/execution.py:218`, `backend/app/modules/ai/execution.py:219`, `backend/app/modules/ai/execution.py:220`, `backend/app/modules/ai/execution.py:221`, `backend/app/modules/ai/execution.py:224`, `backend/app/modules/ai/execution.py:225`, `backend/app/modules/ai/execution.py:226`, `backend/app/modules/ai/execution.py:231`, `backend/app/modules/ai/execution.py:234`, `backend/app/modules/ai/execution.py:237`, `backend/app/modules/ai/execution.py:255`, `backend/app/modules/ai/execution.py:256`, `backend/app/modules/ai/execution.py:257`
- `run_ai_task` writes ledger rows for context build errors, malformed context, context budget errors, route failures, external config blocks, provider exceptions, and successful/provider-error responses. `backend/app/modules/ai/execution.py:298`, `backend/app/modules/ai/execution.py:319`, `backend/app/modules/ai/execution.py:343`, `backend/app/modules/ai/execution.py:367`, `backend/app/modules/ai/execution.py:402`, `backend/app/modules/ai/execution.py:436`, `backend/app/modules/ai/execution.py:472`, `backend/app/modules/ai/execution.py:501`
- Auto control/proposal states write `ai_jobs` rows through `def _write_auto_control_job(...) -> str:` with `requested_route_class` and `selected_route_class` both set to `"auto"`, no provider/model, no tokens, no cost, and `error_type=status`. `backend/app/modules/ai/routing/bridge.py:606`, `backend/app/modules/ai/routing/bridge.py:616`, `backend/app/modules/ai/routing/bridge.py:639`, `backend/app/modules/ai/routing/bridge.py:642`, `backend/app/modules/ai/routing/bridge.py:653`, `backend/app/modules/ai/routing/bridge.py:654`, `backend/app/modules/ai/routing/bridge.py:655`, `backend/app/modules/ai/routing/bridge.py:656`, `backend/app/modules/ai/routing/bridge.py:657`, `backend/app/modules/ai/routing/bridge.py:663`, `backend/app/modules/ai/routing/bridge.py:664`, `backend/app/modules/ai/routing/bridge.py:665`, `backend/app/modules/ai/routing/bridge.py:667`
- `AIUsage` supports `provider_cost_estimate`, but current Scaleway success response builds `AIUsage` with provider/model/input/output/usage_source only; therefore `_write_ai_job` receives no provider cost estimate from that path. `backend/app/modules/ai/contracts.py:102`, `backend/app/modules/ai/contracts.py:103`, `backend/app/modules/ai/contracts.py:104`, `backend/app/modules/ai/contracts.py:105`, `backend/app/modules/ai/contracts.py:106`, `backend/app/modules/ai/contracts.py:109`, `backend/app/modules/ai/providers/scaleway_adapter.py:226`, `backend/app/modules/ai/providers/scaleway_adapter.py:227`, `backend/app/modules/ai/providers/scaleway_adapter.py:228`, `backend/app/modules/ai/providers/scaleway_adapter.py:229`, `backend/app/modules/ai/providers/scaleway_adapter.py:230`, `backend/app/modules/ai/providers/scaleway_adapter.py:231`
- Monthly Scaleway token counters live in `ai_settings` and are updated by `record_scaleway_token_usage`, not by `_write_ai_job`. `backend/app/core/schema.py:307`, `backend/app/core/schema.py:325`, `backend/app/core/schema.py:326`, `backend/app/modules/ai/settings.py:131`, `backend/app/modules/ai/settings.py:133`, `backend/app/modules/ai/settings.py:136`, `backend/app/modules/ai/settings.py:137`, `backend/app/modules/ai/settings.py:141`
- There is no per-candidate BLUECAD attempt ledger schema with fields for candidate id, attempt number, validation report, retry tier, or repair status in `ai_jobs`. `backend/app/core/schema.py:285`, `backend/app/core/schema.py:286`, `backend/app/core/schema.py:289`, `backend/app/core/schema.py:290`, `backend/app/core/schema.py:291`, `backend/app/core/schema.py:294`, `backend/app/core/schema.py:295`, `backend/app/core/schema.py:296`, `backend/app/core/schema.py:297`, `backend/app/core/schema.py:298`, `backend/app/core/schema.py:299`, `backend/app/core/schema.py:300`, `backend/app/core/schema.py:301`, `backend/app/core/schema.py:302`, `backend/app/core/schema.py:303`

Verbatim signatures:

```python
def _write_ai_job(
    *,
    status: str,
    task_kind: str,
    requested_route_class: str | None,
    selected_route_class: str | None,
    decision: RoutingDecision,
    prompt_digest: str | None,
    context_digest: str | None,
    context_sources: list[dict] | None,
    response: AIResponse | None,
    latency_ms: int,
    error_type: str | None,
) -> str:
```

`backend/app/modules/ai/execution.py:204`, `backend/app/modules/ai/execution.py:205`, `backend/app/modules/ai/execution.py:206`, `backend/app/modules/ai/execution.py:207`, `backend/app/modules/ai/execution.py:208`, `backend/app/modules/ai/execution.py:209`, `backend/app/modules/ai/execution.py:210`, `backend/app/modules/ai/execution.py:211`, `backend/app/modules/ai/execution.py:212`, `backend/app/modules/ai/execution.py:213`, `backend/app/modules/ai/execution.py:214`, `backend/app/modules/ai/execution.py:215`, `backend/app/modules/ai/execution.py:216`, `backend/app/modules/ai/execution.py:217`

```python
def _write_auto_control_job(
    *,
    status: str,
    task_kind: str,
    prompt: str,
    decision: dict,
    context_blocks: list[dict] | None,
    latency_ms: int,
    auto_metadata: dict[str, object] | None,
) -> str:
```

`backend/app/modules/ai/routing/bridge.py:606`, `backend/app/modules/ai/routing/bridge.py:607`, `backend/app/modules/ai/routing/bridge.py:608`, `backend/app/modules/ai/routing/bridge.py:609`, `backend/app/modules/ai/routing/bridge.py:610`, `backend/app/modules/ai/routing/bridge.py:611`, `backend/app/modules/ai/routing/bridge.py:612`, `backend/app/modules/ai/routing/bridge.py:613`, `backend/app/modules/ai/routing/bridge.py:614`, `backend/app/modules/ai/routing/bridge.py:615`

```python
def record_scaleway_token_usage(*, input_tokens: int, output_tokens: int) -> AISettingsRead:
```

`backend/app/modules/ai/settings.py:131`

## 4. Sandboxed runner (A6)

### Current registration and execution shape

- Registration entrypoint: `def create_model_implementation(workspace_id: str, payload: ModelImplementationCreate) -> ModelImplementationRead:` only accepts `implementation_kind == "batch_growth_v0"` and rejects other kinds. `backend/app/modules/runner/service.py:40`, `backend/app/modules/runner/service.py:41`, `backend/app/modules/runner/service.py:44`, `backend/app/modules/runner/service.py:45`, `backend/app/modules/runner/service.py:46`
- Registration copies the bundled example script to `<data_root>/workspaces/{workspace_id}/model_implementations/{model_version_id}/batch_growth.py`, hashes it, inserts an `artifacts` row, and inserts a `model_versions` row pointing at that artifact. `backend/app/modules/runner/safety.py:139`, `backend/app/modules/runner/safety.py:140`, `backend/app/modules/runner/service.py:60`, `backend/app/modules/runner/service.py:61`, `backend/app/modules/runner/service.py:62`, `backend/app/modules/runner/service.py:63`, `backend/app/modules/runner/service.py:64`, `backend/app/modules/runner/service.py:67`, `backend/app/modules/runner/service.py:69`, `backend/app/modules/runner/service.py:78`, `backend/app/modules/runner/service.py:79`, `backend/app/modules/runner/service.py:88`, `backend/app/modules/runner/service.py:90`, `backend/app/modules/runner/service.py:100`
- Job creation validates the batch-growth input, loads the model version/artifact, validates script path, verifies script SHA, creates a queued `simulation_runs` row, and creates a queued `runner_jobs` row. `backend/app/modules/runner/service.py:156`, `backend/app/modules/runner/service.py:157`, `backend/app/modules/runner/service.py:162`, `backend/app/modules/runner/service.py:164`, `backend/app/modules/runner/service.py:165`, `backend/app/modules/runner/service.py:166`, `backend/app/modules/runner/service.py:167`, `backend/app/modules/runner/service.py:171`, `backend/app/modules/runner/service.py:173`, `backend/app/modules/runner/service.py:184`, `backend/app/modules/runner/service.py:194`, `backend/app/modules/runner/service.py:196`, `backend/app/modules/runner/service.py:209`
- Execution validates the script path again, runs text-marker preflight, re-checks SHA, validates run paths, writes `input.json`, atomically claims queued status, and executes the Python subprocess. `backend/app/modules/runner/service.py:255`, `backend/app/modules/runner/service.py:262`, `backend/app/modules/runner/service.py:265`, `backend/app/modules/runner/service.py:266`, `backend/app/modules/runner/service.py:267`, `backend/app/modules/runner/service.py:268`, `backend/app/modules/runner/service.py:271`, `backend/app/modules/runner/service.py:281`, `backend/app/modules/runner/service.py:284`, `backend/app/modules/runner/service.py:287`, `backend/app/modules/runner/service.py:292`

### Path constraints

- Script path must be inside `model_implementation_root(workspace_id)`, must end in `.py`, and must exist. `backend/app/modules/runner/safety.py:147`, `backend/app/modules/runner/safety.py:148`, `backend/app/modules/runner/safety.py:149`, `backend/app/modules/runner/safety.py:150`, `backend/app/modules/runner/safety.py:151`, `backend/app/modules/runner/safety.py:153`, `backend/app/modules/runner/safety.py:155`
- Run working directory, output directory, and input file must be inside `run_root(workspace_id, simulation_run_id)`; working dir and output dir must equal the run root, and input must equal `input.json` in that root. `backend/app/modules/runner/safety.py:160`, `backend/app/modules/runner/safety.py:168`, `backend/app/modules/runner/safety.py:170`, `backend/app/modules/runner/safety.py:175`, `backend/app/modules/runner/safety.py:180`, `backend/app/modules/runner/safety.py:182`, `backend/app/modules/runner/safety.py:188`, `backend/app/modules/runner/safety.py:190`, `backend/app/modules/runner/safety.py:192`
- Declared artifact paths must be relative and under `output_dir`. `backend/app/modules/runner/safety.py:206`, `backend/app/modules/runner/safety.py:207`, `backend/app/modules/runner/safety.py:209`, `backend/app/modules/runner/safety.py:210`, `backend/app/modules/runner/safety.py:211`, `backend/app/modules/runner/safety.py:212`

### Import/subprocess/network policy

- Import/network/process restrictions are a text-marker denylist, not an AST parser or import allowlist: `FORBIDDEN_SCRIPT_MARKERS` includes socket, requests, httpx, urllib, subprocess, os.system/popen, deletion APIs, `.env`, environment access, and secret-marker strings. `backend/app/modules/runner/safety.py:18`, `backend/app/modules/runner/safety.py:19`, `backend/app/modules/runner/safety.py:20`, `backend/app/modules/runner/safety.py:21`, `backend/app/modules/runner/safety.py:22`, `backend/app/modules/runner/safety.py:23`, `backend/app/modules/runner/safety.py:24`, `backend/app/modules/runner/safety.py:25`, `backend/app/modules/runner/safety.py:26`, `backend/app/modules/runner/safety.py:27`, `backend/app/modules/runner/safety.py:28`, `backend/app/modules/runner/safety.py:29`, `backend/app/modules/runner/safety.py:30`, `backend/app/modules/runner/safety.py:31`, `backend/app/modules/runner/safety.py:32`, `backend/app/modules/runner/safety.py:33`, `backend/app/modules/runner/safety.py:34`, `backend/app/modules/runner/safety.py:35`, `backend/app/modules/runner/safety.py:38`, `backend/app/modules/runner/safety.py:39`, `backend/app/modules/runner/safety.py:40`, `backend/app/modules/runner/safety.py:41`, `backend/app/modules/runner/safety.py:42`, `backend/app/modules/runner/safety.py:43`, `backend/app/modules/runner/safety.py:44`, `backend/app/modules/runner/safety.py:45`, `backend/app/modules/runner/safety.py:46`, `backend/app/modules/runner/safety.py:47`
- `def preflight_script_policy(script_path: Path) -> None:` lowercases script text and raises `runner_policy_blocked` when any forbidden marker appears. `backend/app/modules/runner/safety.py:198`, `backend/app/modules/runner/safety.py:199`, `backend/app/modules/runner/safety.py:200`, `backend/app/modules/runner/safety.py:201`, `backend/app/modules/runner/safety.py:202`, `backend/app/modules/runner/safety.py:203`
- Subprocess execution uses `[sys.executable, script_path, input_file, output_dir]`, `shell=False`, timeout, captured output, and an environment containing only `PYTHONIOENCODING=utf-8`. `backend/app/modules/runner/local_python.py:19`, `backend/app/modules/runner/local_python.py:29`, `backend/app/modules/runner/local_python.py:30`, `backend/app/modules/runner/local_python.py:31`, `backend/app/modules/runner/local_python.py:36`, `backend/app/modules/runner/local_python.py:37`, `backend/app/modules/runner/local_python.py:38`, `backend/app/modules/runner/local_python.py:42`, `backend/app/modules/runner/local_python.py:44`, `backend/app/modules/runner/local_python.py:45`, `backend/app/modules/runner/local_python.py:46`, `backend/app/modules/runner/local_python.py:48`, `backend/app/modules/runner/local_python.py:49`
- Network is not blocked by OS/container policy in `execute_python_script`; the present network restriction is the script-text denylist for socket/requests/httpx/urllib markers. `backend/app/modules/runner/local_python.py:42`, `backend/app/modules/runner/local_python.py:45`, `backend/app/modules/runner/local_python.py:49`, `backend/app/modules/runner/safety.py:18`, `backend/app/modules/runner/safety.py:19`, `backend/app/modules/runner/safety.py:20`, `backend/app/modules/runner/safety.py:21`, `backend/app/modules/runner/safety.py:22`, `backend/app/modules/runner/safety.py:23`, `backend/app/modules/runner/safety.py:24`, `backend/app/modules/runner/safety.py:25`

### Input/output validation

- `validate_batch_growth_input` requires `parameters` to contain `mu_max`, `X0`, `t_final`, and `dt`; each must be numeric/finite, `dt > 0`, nonnegative parameters, and `t_final / dt <= 10000`. `backend/app/modules/runner/safety.py:17`, `backend/app/modules/runner/safety.py:66`, `backend/app/modules/runner/safety.py:79`, `backend/app/modules/runner/safety.py:80`, `backend/app/modules/runner/safety.py:87`, `backend/app/modules/runner/safety.py:88`, `backend/app/modules/runner/safety.py:89`, `backend/app/modules/runner/safety.py:94`, `backend/app/modules/runner/safety.py:98`, `backend/app/modules/runner/safety.py:102`, `backend/app/modules/runner/safety.py:104`, `backend/app/modules/runner/safety.py:106`, `backend/app/modules/runner/safety.py:108`, `backend/app/modules/runner/safety.py:110`
- Successful runner output must include `result.json` as an object under the working directory and any declared artifacts must be objects with existing relative paths under the output directory and size at most `max_artifact_bytes`. `backend/app/modules/runner/service.py:323`, `backend/app/modules/runner/service.py:324`, `backend/app/modules/runner/service.py:325`, `backend/app/modules/runner/service.py:326`, `backend/app/modules/runner/service.py:330`, `backend/app/modules/runner/service.py:575`, `backend/app/modules/runner/service.py:576`, `backend/app/modules/runner/service.py:577`, `backend/app/modules/runner/service.py:579`, `backend/app/modules/runner/service.py:585`, `backend/app/modules/runner/service.py:590`, `backend/app/modules/runner/service.py:599`, `backend/app/modules/runner/service.py:600`, `backend/app/modules/runner/service.py:602`, `backend/app/modules/runner/service.py:603`, `backend/app/modules/runner/service.py:604`, `backend/app/modules/runner/service.py:606`

### Concrete blockers for a build123d script today

- Supported registration blocks arbitrary build123d scripts because `create_model_implementation` accepts only `batch_growth_v0` and copies the bundled `batch_growth.py`; no API parameter accepts caller-supplied script text/path. `backend/app/modules/runner/models.py:8`, `backend/app/modules/runner/models.py:11`, `backend/app/modules/runner/service.py:44`, `backend/app/modules/runner/service.py:45`, `backend/app/modules/runner/service.py:46`, `backend/app/modules/runner/service.py:60`, `backend/app/modules/runner/service.py:62`, `backend/app/modules/runner/service.py:63`
- Hash checks block post-registration script replacement because job creation and execution compare the current script hash to the stored artifact/job SHA. `backend/app/modules/runner/service.py:164`, `backend/app/modules/runner/service.py:165`, `backend/app/modules/runner/service.py:166`, `backend/app/modules/runner/service.py:167`, `backend/app/modules/runner/service.py:265`, `backend/app/modules/runner/service.py:267`, `backend/app/modules/runner/service.py:268`
- Current input contract blocks GeometrySpec/L2 CAD payloads because runner job creation always calls `validate_batch_growth_input(payload.input_set)`, which requires batch-growth parameters. `backend/app/modules/runner/service.py:156`, `backend/app/modules/runner/service.py:157`, `backend/app/modules/runner/safety.py:17`, `backend/app/modules/runner/safety.py:79`, `backend/app/modules/runner/safety.py:88`
- The string `build123d` is not a forbidden marker; the current policy does not block `import build123d` by name. `backend/app/modules/runner/safety.py:18`, `backend/app/modules/runner/safety.py:19`, `backend/app/modules/runner/safety.py:20`, `backend/app/modules/runner/safety.py:21`, `backend/app/modules/runner/safety.py:22`, `backend/app/modules/runner/safety.py:23`, `backend/app/modules/runner/safety.py:24`, `backend/app/modules/runner/safety.py:25`, `backend/app/modules/runner/safety.py:26`, `backend/app/modules/runner/safety.py:27`, `backend/app/modules/runner/safety.py:28`, `backend/app/modules/runner/safety.py:29`, `backend/app/modules/runner/safety.py:30`, `backend/app/modules/runner/safety.py:31`, `backend/app/modules/runner/safety.py:32`, `backend/app/modules/runner/safety.py:33`, `backend/app/modules/runner/safety.py:34`, `backend/app/modules/runner/safety.py:35`, `backend/app/modules/runner/safety.py:38`, `backend/app/modules/runner/safety.py:39`, `backend/app/modules/runner/safety.py:40`, `backend/app/modules/runner/safety.py:41`, `backend/app/modules/runner/safety.py:42`, `backend/app/modules/runner/safety.py:43`, `backend/app/modules/runner/safety.py:44`, `backend/app/modules/runner/safety.py:45`, `backend/app/modules/runner/safety.py:46`, `backend/app/modules/runner/safety.py:47`
- CAD-specific artifact roles or required STEP/STL/GLB/manifest semantics do not exist in runner validation; artifact registration accepts caller-declared `path`, `role`, `mime_type`, and `artifact_type` after path/existence/size checks. `backend/app/modules/runner/service.py:590`, `backend/app/modules/runner/service.py:599`, `backend/app/modules/runner/service.py:602`, `backend/app/modules/runner/service.py:603`, `backend/app/modules/runner/service.py:604`, `backend/app/modules/runner/service.py:606`, `backend/app/modules/runner/service.py:610`, `backend/app/modules/runner/service.py:611`, `backend/app/modules/runner/service.py:624`

Verbatim signatures:

```python
def create_model_implementation(workspace_id: str, payload: ModelImplementationCreate) -> ModelImplementationRead:
```

`backend/app/modules/runner/service.py:44`

```python
def create_runner_job(workspace_id: str, payload: RunnerJobCreate) -> RunnerJobCreateResponse:
```

`backend/app/modules/runner/service.py:156`

```python
def run_runner_job(runner_job_id: str) -> RunnerJobRunResponse:
```

`backend/app/modules/runner/service.py:255`

```python
def validate_batch_growth_input(input_set: dict[str, Any]) -> tuple[str, str]:
```

`backend/app/modules/runner/safety.py:66`

```python
def validate_script_path(workspace_id: str, script_path: str) -> Path:
```

`backend/app/modules/runner/safety.py:147`

```python
def validate_run_paths(
    workspace_id: str,
    simulation_run_id: str,
    *,
    working_dir: str,
    input_file: str | None,
    output_dir: str,
) -> tuple[Path, Path, Path]:
```

`backend/app/modules/runner/safety.py:160`, `backend/app/modules/runner/safety.py:161`, `backend/app/modules/runner/safety.py:162`, `backend/app/modules/runner/safety.py:163`, `backend/app/modules/runner/safety.py:164`, `backend/app/modules/runner/safety.py:165`, `backend/app/modules/runner/safety.py:166`, `backend/app/modules/runner/safety.py:167`

```python
def execute_python_script(
    *,
    script_path: Path,
    input_file: Path,
    output_dir: Path,
    working_dir: Path,
    timeout_seconds: int,
    max_stdout_bytes: int,
    max_stderr_bytes: int,
) -> LocalPythonResult:
```

`backend/app/modules/runner/local_python.py:19`, `backend/app/modules/runner/local_python.py:20`, `backend/app/modules/runner/local_python.py:21`, `backend/app/modules/runner/local_python.py:22`, `backend/app/modules/runner/local_python.py:23`, `backend/app/modules/runner/local_python.py:24`, `backend/app/modules/runner/local_python.py:25`, `backend/app/modules/runner/local_python.py:26`, `backend/app/modules/runner/local_python.py:27`, `backend/app/modules/runner/local_python.py:28`

## 5. Workspace artifacts

- Data-root path layout defines `workspaces_dir = data_root / "workspaces"` and `artifacts_dir = data_root / "artifacts"`. `backend/app/core/paths.py:7`, `backend/app/core/paths.py:9`, `backend/app/core/paths.py:11`, `backend/app/core/paths.py:12`, `backend/app/core/paths.py:29`, `backend/app/core/paths.py:31`, `backend/app/core/paths.py:34`, `backend/app/core/paths.py:35`
- Workspace API surface is create/list/get only: `POST /workspaces`, `GET /workspaces`, and `GET /workspaces/{workspace_id}`. `backend/app/modules/workspaces/routes.py:8`, `backend/app/modules/workspaces/routes.py:12`, `backend/app/modules/workspaces/routes.py:20`, `backend/app/modules/workspaces/routes.py:24`, `backend/app/modules/workspaces/routes.py:25`
- Workspace persistence writes `workspaces` and a `WorkspaceCreated` event; default `bluerev` workspace can be seeded. `backend/app/modules/workspaces/service.py:16`, `backend/app/modules/workspaces/service.py:20`, `backend/app/modules/workspaces/service.py:22`, `backend/app/modules/workspaces/service.py:36`, `backend/app/modules/workspaces/service.py:38`, `backend/app/modules/workspaces/service.py:68`, `backend/app/modules/workspaces/service.py:75`, `backend/app/modules/workspaces/service.py:82`, `backend/app/modules/workspaces/service.py:91`, `backend/app/modules/workspaces/service.py:93`
- Modeling API surface exposes workspace-scoped model specs, assumptions, parameters, requirements, simulation runs, and decisions. `backend/app/modules/modeling/routes.py:49`, `backend/app/modules/modeling/routes.py:57`, `backend/app/modules/modeling/routes.py:73`, `backend/app/modules/modeling/routes.py:81`, `backend/app/modules/modeling/routes.py:89`, `backend/app/modules/modeling/routes.py:97`, `backend/app/modules/modeling/routes.py:105`, `backend/app/modules/modeling/routes.py:113`, `backend/app/modules/modeling/routes.py:137`, `backend/app/modules/modeling/routes.py:145`, `backend/app/modules/modeling/routes.py:153`, `backend/app/modules/modeling/routes.py:161`
- Simulation run record shape includes optional `model_version_id`, `run_label`, `status`, input/parameter/output payload strings, timestamps, and notes. `backend/app/modules/modeling/models.py:91`, `backend/app/modules/modeling/models.py:92`, `backend/app/modules/modeling/models.py:93`, `backend/app/modules/modeling/models.py:94`, `backend/app/modules/modeling/models.py:95`, `backend/app/modules/modeling/models.py:96`, `backend/app/modules/modeling/models.py:97`, `backend/app/modules/modeling/models.py:98`, `backend/app/modules/modeling/models.py:99`, `backend/app/modules/modeling/models.py:100`
- Decision record shape includes title, decision text, rationale, status, optional linked run id, and notes. `backend/app/modules/modeling/models.py:109`, `backend/app/modules/modeling/models.py:110`, `backend/app/modules/modeling/models.py:111`, `backend/app/modules/modeling/models.py:112`, `backend/app/modules/modeling/models.py:113`, `backend/app/modules/modeling/models.py:114`, `backend/app/modules/modeling/models.py:115`
- Runner API surface creates model implementations, creates runner jobs, runs runner jobs, reads simulation run details, lists logs, and lists run artifacts. `backend/app/modules/runner/routes.py:40`, `backend/app/modules/runner/routes.py:45`, `backend/app/modules/runner/routes.py:55`, `backend/app/modules/runner/routes.py:63`, `backend/app/modules/runner/routes.py:71`, `backend/app/modules/runner/routes.py:79`, `backend/app/modules/runner/routes.py:87`, `backend/app/modules/runner/routes.py:95`, `backend/app/modules/runner/routes.py:99`
- Artifact schema stores id, workspace, filename, stored path, artifact type, MIME type, SHA-256, source ref, status, created time, and notes. `backend/app/core/schema.py:98`, `backend/app/core/schema.py:99`, `backend/app/core/schema.py:100`, `backend/app/core/schema.py:101`, `backend/app/core/schema.py:102`, `backend/app/core/schema.py:103`, `backend/app/core/schema.py:104`, `backend/app/core/schema.py:105`, `backend/app/core/schema.py:106`, `backend/app/core/schema.py:107`, `backend/app/core/schema.py:108`, `backend/app/core/schema.py:109`
- Run artifact linkage schema stores workspace, simulation run, artifact id, role, created time, and notes. `backend/app/core/schema.py:255`, `backend/app/core/schema.py:256`, `backend/app/core/schema.py:257`, `backend/app/core/schema.py:258`, `backend/app/core/schema.py:259`, `backend/app/core/schema.py:260`, `backend/app/core/schema.py:261`, `backend/app/core/schema.py:262`
- Model implementation artifacts are created during `create_model_implementation` as `python_script` artifacts with `source_ref = model_spec:{payload.model_spec_id}` and linked from `model_versions.implementation_artifact_id`. `backend/app/modules/runner/service.py:67`, `backend/app/modules/runner/service.py:69`, `backend/app/modules/runner/service.py:78`, `backend/app/modules/runner/service.py:79`, `backend/app/modules/runner/service.py:80`, `backend/app/modules/runner/service.py:81`, `backend/app/modules/runner/service.py:82`, `backend/app/modules/runner/service.py:88`, `backend/app/modules/runner/service.py:90`, `backend/app/modules/runner/service.py:100`
- Run artifacts are created from `result.json` declarations, inserted into `artifacts`, linked through `run_artifacts`, and exposed through `list_run_artifacts`. `backend/app/modules/runner/service.py:323`, `backend/app/modules/runner/service.py:325`, `backend/app/modules/runner/service.py:330`, `backend/app/modules/runner/service.py:590`, `backend/app/modules/runner/service.py:612`, `backend/app/modules/runner/service.py:614`, `backend/app/modules/runner/service.py:627`, `backend/app/modules/runner/service.py:633`, `backend/app/modules/runner/service.py:635`, `backend/app/modules/runner/service.py:643`, `backend/app/modules/runner/service.py:429`, `backend/app/modules/runner/service.py:438`, `backend/app/modules/runner/service.py:453`, `backend/app/modules/runner/service.py:454`, `backend/app/modules/runner/service.py:455`
- Readback redacts unsafe stored paths by returning `stored_path` and file size only when the artifact path is under `data_root`; it always returns `artifact_id`, `relative_path`, `source_ref`, `source_module`, MIME type, SHA-256, status, and `under_data_root`. `backend/app/modules/runner/service.py:714`, `backend/app/modules/runner/service.py:716`, `backend/app/modules/runner/service.py:723`, `backend/app/modules/runner/service.py:724`, `backend/app/modules/runner/service.py:729`, `backend/app/modules/runner/service.py:730`, `backend/app/modules/runner/service.py:731`, `backend/app/modules/runner/service.py:734`, `backend/app/modules/runner/service.py:735`, `backend/app/modules/runner/service.py:736`, `backend/app/modules/runner/service.py:737`, `backend/app/modules/runner/service.py:743`, `backend/app/modules/runner/service.py:744`, `backend/app/modules/runner/service.py:745`, `backend/app/modules/runner/service.py:747`, `backend/app/modules/runner/service.py:748`, `backend/app/modules/runner/service.py:749`, `backend/app/modules/runner/service.py:750`, `backend/app/modules/runner/service.py:751`, `backend/app/modules/runner/service.py:752`
- Generic artifact upload, generic artifact download, CAD artifact manifest API, and workspace Decision promotion from AI output do not exist in the inspected `workspaces`, `modeling`, and `runner` route surfaces. `backend/app/modules/workspaces/routes.py:12`, `backend/app/modules/workspaces/routes.py:20`, `backend/app/modules/workspaces/routes.py:25`, `backend/app/modules/modeling/routes.py:153`, `backend/app/modules/modeling/routes.py:161`, `backend/app/modules/runner/routes.py:95`, `backend/app/modules/runner/routes.py:99`

Verbatim signatures:

```python
def create_workspace(payload: WorkspaceCreate, *, actor: str = "local-user") -> WorkspaceRead:
```

`backend/app/modules/workspaces/service.py:16`

```python
def create_simulation_run(workspace_id: str, payload: SimulationRunCreate) -> SimulationRunRead:
```

`backend/app/modules/modeling/service.py:311`

```python
def create_decision(workspace_id: str, payload: DecisionCreate) -> DecisionRead:
```

`backend/app/modules/modeling/service.py:362`

```python
def list_run_artifacts(workspace_id: str, simulation_run_id: str) -> list[RunArtifactRead]:
```

`backend/app/modules/runner/service.py:429`

