# 0E-C AI Provider Abstraction Design

## 1. Executive Judgement

JarvisOS should move toward one stable user-facing AI interface:

```text
Supervisor AI
```

The user should not choose between provider-branded bots such as GPT, Claude, DeepSeek, Scaleway, Sonnet, or future local models in normal modeling workflows. Provider and model choice should be internal, policy-driven, auditable, and reversible.

This milestone was design-only when written. Later, 0E-D4 added exactly one provider implementation, DeepSeek, as a narrow smoke-only adapter. 0E-D5 then added a narrow backend-only Supervisor public/internal test endpoint. JarvisOS is still not ready for OpenAI, Anthropic, Mistral, local/Ollama, broad provider routing, Supervisor UI, or a full Supervisor workflow.

Main judgement:

```text
Keep the current Scaleway smoke/live path.
Design provider-neutral abstractions now.
Implement no new provider until the abstractions and tests exist.
Keep BlueRev modeling paused.
```

## 2. Current AI Architecture Assessment

Current working AI pieces:

- `app/modules/ai/gateway.py`: single entry point for AI draft, smoke tests, and smoke console.
- `app/modules/ai/providers/fake.py`: deterministic fake provider for no-cost local work and tests.
- `app/modules/ai/providers/scaleway.py`: isolated live Scaleway chat-completions HTTP path for smoke use only.
- `app/modules/ai/privacy.py`: local privacy/IP classification and policy decisions.
- `app/modules/ai/budget.py`: AI status and Scaleway live smoke gate.
- `app/modules/ai/token_guard.py`: conservative token estimation and cap checks.
- `app/modules/ai/smoke_tests.py`: fixed synthetic smoke-test suite.
- `app/modules/ai/smoke_console.py`: narrow manual harmless prompt console.
- `app/modules/secrets`: runtime-memory Scaleway key entry and status.
- `app/modules/events/service.py`: event persistence with centralized redaction.

What is solid:

| Severity | Action | Area | Judgement |
| --- | --- | --- | --- |
| high | keep | AI Gateway | Routes and frontend do not call provider HTTP directly. |
| high | keep | Scaleway provider | Real HTTP logic is isolated in the provider module. |
| high | keep | Safety gates | Paid AI, provider mode, live smoke flag, privacy, token cap, and key checks exist. |
| medium | keep | Fake provider | Tests can run without network and without spending money. |
| medium | keep | Smoke console | Still a smoke surface, not chat. |
| medium | keep | Secrets | Runtime-memory key entry is honest and avoids plaintext persistence. |

What is structurally weak before multi-provider work:

| Severity | Action | Area | Problem |
| --- | --- | --- | --- |
| blocker | refactor during 0E-D1 | Provider abstraction | `AIProvider.generate` is modeling-draft-specific. |
| blocker | refactor during 0E-D1 | Registry | No provider registry or model registry exists. |
| high | refactor during 0E-D1 | Settings/status | AI settings and status are Scaleway-shaped. |
| high | refactor during 0E-D1 | Usage | Token/cost accounting is Scaleway-specific and smoke-test-specific. |
| high | refactor during 0E-D1 | Gates | Smoke tests and smoke console duplicate gate/accounting/event logic. |
| medium | refactor during 0E-D3 | Frontend | AI page and API client are too large for provider diagnostics plus Supervisor UI. |

## 3. Non-goals

Do not implement in 0E-C:

- new providers;
- OpenAI calls;
- Anthropic/Claude calls;
- DeepSeek calls;
- Mistral calls;
- local/Ollama calls;
- AI Supervisor UI;
- general chat;
- memory;
- RAG;
- agents;
- MCP;
- sidecars;
- desktop daemon behavior;
- screen, voice, browser, clipboard, or file-system automation;
- BlueRev scientific models;
- runner UI;
- AI-generated code execution;
- arbitrary Python execution;
- CAD, geometry, CFD, FEM;
- multi-agent debate;
- generic workflow builder.

## 4. User-facing Supervisor AI Concept

The future user-facing interface should be:

```text
Jarvis Supervisor
```

The user sees:

- one AI collaborator inside engineering workflows;
- task-specific actions such as "Review assumptions", "Explain runner error", "Draft ModelSpec", "Summarize artifact";
- clear sensitivity and cost status;
- blocked reasons when content cannot leave the machine;
- optional diagnostics showing provider/model used after the fact.

The user should not see:

- provider-specific bot buttons;
- "Ask GPT";
- "Ask Claude";
- "Ask DeepSeek";
- "Ask Scaleway";
- model leaderboard choices in normal workflow screens.

The backend handles:

```text
Supervisor request
-> task classification
-> privacy/IP policy
-> authority policy
-> budget/token policy
-> provider/model routing
-> provider adapter
-> structured response
-> audit event
```

Provider/model details remain visible only in:

- admin/operator diagnostics;
- provider credential status;
- AI usage and cost status;
- audit logs;
- smoke-test tools.

The existing AI Smoke Console remains provider-adjacent because it is an operator diagnostic tool, not the normal modeling interface.

## 5. Provider Adapter Design

### Interface Shape

The future provider contract should be provider-neutral:

```python
class AIProviderAdapter(Protocol):
    provider_id: str

    def status(self) -> ProviderStatus: ...

    def complete(self, request: AIRequest) -> AIResponse: ...
```

V1 can be synchronous. Streaming should be modeled but postponed:

```python
class AIProviderAdapter(Protocol):
    supports_streaming: bool
    supports_structured_output: bool
```

Do not build streaming until a real UI workflow needs it.

### `AIRequest`

Provider-neutral request fields:

| Field | Purpose |
| --- | --- |
| `request_id` | Stable trace id for audit. |
| `workspace_id` | Optional workspace scope. |
| `task_type` | One `AITaskType`. |
| `input_messages` | Normalized message list, not provider-native payload. |
| `structured_output_schema` | Optional JSON schema or named schema id. |
| `max_output_tokens` | Task cap. |
| `temperature` | Controlled generation setting. |
| `privacy_class` | Local privacy result. |
| `authority_context` | Whether external call is allowed and why. |
| `routing_context` | Chosen provider/model metadata. |
| `metadata` | Safe non-secret trace metadata. |

### `AIResponse`

Provider-neutral response fields:

| Field | Purpose |
| --- | --- |
| `request_id` | Correlates to request. |
| `provider_id` | Actual provider used. |
| `model_id` | Actual model used. |
| `task_type` | Task type served. |
| `text` | Optional text response. |
| `structured_output` | Optional validated structured output. |
| `usage` | `AIUsage`. |
| `finish_reason` | Normalized provider finish reason. |
| `success` | Boolean success flag. |
| `error` | Optional normalized `AIError`. |
| `provider_metadata` | Sanitized safe metadata only. |

### Error Normalization

Provider errors should normalize into:

```text
provider_unavailable
provider_auth_missing
provider_auth_failed
provider_rate_limited
provider_timeout
provider_bad_request
provider_response_invalid
provider_unknown_error
```

Raw provider error bodies should not be returned directly to the frontend. They may contain prompt fragments or account metadata.

### Initial Provider Categories

| Provider Category | Status | Action |
| --- | --- | --- |
| Existing Scaleway adapter | current path | migrate during 0E-D2 |
| DeepSeek OpenAI-compatible adapter | added in 0E-D4 | narrow smoke path only |
| Other OpenAI-compatible adapter | future | design only now |
| Anthropic adapter | future | design only now |
| Local/Ollama adapter | future placeholder | design only now |

## 6. Provider Registry Design

`ProviderRegistry` should describe available providers without performing provider calls.

Suggested fields:

```python
class ProviderDefinition(BaseModel):
    provider_id: str
    display_name: str
    adapter_kind: str
    enabled: bool
    credential_required: bool
    credential_status: CredentialStatus
    base_url_configurable: bool
    supports_chat: bool
    supports_structured_output: bool
    supports_streaming: bool
    supports_vision: bool
    locality: str
    notes: str | None
```

Provider locality examples:

- `local_only`;
- `eu_hosted`;
- `external`;
- `unknown`.

Current mapping:

| Current Item | Future Registry Mapping |
| --- | --- |
| `fake` | Provider `fake`, local deterministic, no credential. |
| `scaleway` | Provider `scaleway`, EU hosted, credential required. |
| `SCALEWAY_BASE_URL` | Provider connection config, not model registry. |
| `SCALEWAY_API_KEY` | Provider credential source. |

Provider registry should not store raw keys.

## 7. Model Registry Design

`ModelRegistry` should describe models separately from providers.

Suggested fields:

```python
class ModelDefinition(BaseModel):
    model_id: str
    provider_id: str
    provider_model_name: str
    display_name: str
    enabled: bool
    context_window_tokens: int | None
    max_output_tokens: int | None
    capabilities: set[ModelCapability]
    cost: ModelCostEstimate
    latency_class: str
    reasoning_class: str
    allowed_privacy_classes: set[str]
    default_task_types: set[AITaskType]
    notes: str | None
```

`ModelCapability` examples:

- `chat_text`;
- `structured_json`;
- `tool_calling`;
- `vision_input`;
- `long_context`;
- `code_reasoning`;
- `source_grounded_summary`;
- `low_latency`;
- `low_cost`;
- `high_reasoning`;

Cost fields:

```python
class ModelCostEstimate(BaseModel):
    input_cost_per_million_tokens_usd: float | None
    output_cost_per_million_tokens_usd: float | None
    free_tier_reference: str | None
    cost_source: str
```

Do not hardcode future provider model names now. The existing Scaleway model can be used as an example only.

0E-D4 adds one concrete OpenAI-compatible model reference, `deepseek-chat`, as the default for the DeepSeek smoke adapter. This is a narrow implementation detail, not dynamic model discovery or a broad provider strategy.

## 8. Task Type Routing Design

`AITaskType` should be explicit. It should replace loose strings and provider-specific mode names in future implementation.

Initial task types relevant to JarvisOS:

| Task Type | Intended Use | Default Sensitivity |
| --- | --- | --- |
| `smoke_console_test` | Operator provider check constrained by length, token, budget, credential, and policy mode gates. | public/internal in FAST_DEV |
| `smoke_test` | Fixed synthetic safety tests. | synthetic public/internal only |
| `model_spec_draft` | Draft structured ModelSpec from user prompt. | internal or public, no IP by default |
| `assumption_review` | Critique assumptions. | internal/confidential depending input |
| `equation_review` | Review formulas/equations. | internal/confidential |
| `literature_query_planning` | Plan external source search. | public/internal |
| `source_extraction` | Extract structured data from sources. | public/internal |
| `simulation_result_interpretation` | Explain SimulationRun outputs. | internal/confidential |
| `code_review` | Review reviewed script or error. | internal/confidential |
| `runner_error_explanation` | Explain runner logs/errors. | internal |
| `artifact_summary` | Summarize artifact metadata/content. | depends on artifact |
| `decision_support` | Draft decision candidate. | confidential by default |
| `critic_review` | Critique model/assumptions. | confidential by default |
| `synthesis` | Merge proposer/critic outputs later. | confidential by default |

Routing inputs:

- task type;
- privacy class;
- required output schema;
- max latency;
- cost ceiling;
- context length;
- model capabilities;
- credential availability;
- provider health;
- fallback policy.

Routing output:

```python
class RoutingDecision(BaseModel):
    provider_id: str | None
    model_id: str | None
    blocked: bool
    blocked_reason: str | None
    considered_models: list[str]
    decision_reason: str
```

## 9. Privacy/IP Policy Design

Privacy classes remain:

- `public`;
- `internal`;
- `confidential`;
- `sensitive_ip`;
- `secret`;
- `unknown`.

Policy modes now affect the default routing rules. `FAST_DEV` is the current default and intentionally allows normal public/internal technical material. `STRICT_IP` is a future stricter mode.

Default future `STRICT_IP` routing rules:

| Privacy Class | Default External AI Rule | Severity | Action |
| --- | --- | --- | --- |
| `secret` | Never external. | blocker | keep |
| `sensitive_ip` | Never external by default. | blocker | keep |
| `confidential` | Block external unless future explicit policy allows. | high | harden later |
| `unknown` | Block or require classification. | high | keep |
| `internal` | May route externally if task and policy allow. | medium | keep |
| `public` | May route externally if task and policy allow. | medium | keep |

Current behavior should remain pragmatic:

- Smoke Console allows short public/internal technical prompts in `FAST_DEV`.
- Fixed smoke tests use synthetic data only.
- Structural secrets such as API key fields, `.env` references, authorization headers, private keys, and explicit token/password assignments are blocked before provider calls.
- Broad keyword blocks for `patent`, `geometry`, `BlueRev`, `Smart Joint`, or `confidential` are not used in `FAST_DEV`.
- Future `STRICT_IP` can reintroduce sensitive-IP/confidential/unknown blocking when real proprietary content appears.

Future improvement:

```text
PrivacyPolicyEngine
-> PrivacyDecision
-> AuthorityPolicy
-> RoutingPolicy
```

Provider adapters must not decide whether content is allowed to leave the machine. They only execute approved calls.

## 10. Budget/Cost Policy Design

Current Scaleway-specific fields:

- `scaleway_monthly_token_cap`;
- `scaleway_hard_stop_token_cap`;
- `scaleway_input_tokens_month_to_date`;
- `scaleway_output_tokens_month_to_date`;
- `scaleway_free_tier_reference_tokens`.

Future provider-neutral accounting:

```python
class AIUsage(BaseModel):
    provider_id: str
    model_id: str
    task_type: AITaskType
    input_tokens_estimated: int
    output_tokens_estimated: int
    input_tokens_actual: int | None
    output_tokens_actual: int | None
    total_tokens_actual: int | None
    usage_source: Literal["estimated", "actual", "mixed"]
    estimated_cost_usd: float | None
    actual_cost_usd: float | None
    cost_source: str
    timestamp: str
```

Budget policy should support:

- global monthly budget;
- provider monthly token cap;
- provider hard stop;
- task max tokens;
- warning thresholds;
- free-tier references;
- per-task spend ceilings;
- estimated-before-call checks;
- actual-after-call reconciliation.

Future tables or settings should be provider-neutral:

```text
ai_provider_usage_monthly
provider_id
model_id
month
input_tokens
output_tokens
estimated_cost_usd
actual_cost_usd
```

Do not drop existing Scaleway fields immediately. Migrate gradually:

1. Keep existing Scaleway fields.
2. Introduce provider-neutral usage model.
3. Write new usage records for new paths.
4. Backfill or mirror Scaleway smoke usage if needed.
5. Deprecate Scaleway-specific counters after compatibility is proven.

## 11. Credential Management Design

Current state:

- environment source: `SCALEWAY_API_KEY`;
- runtime-memory app source;
- raw key never returned;
- no frontend storage;
- no plaintext SQLite;
- metadata-only events.

Future model:

```python
class ProviderCredential(BaseModel):
    provider_id: str
    credential_kind: str
    scope: str

class CredentialStatus(BaseModel):
    provider_id: str
    key_present: bool
    source: CredentialSource
    masked_preview: str | None
    last_updated_at: str | None
    storage_mode: str
```

`CredentialSource` values:

- `env`;
- `runtime_memory`;
- `os_credential_store`;
- `missing`;

Credential store interfaces:

```python
class CredentialStore(Protocol):
    def status(provider_id: str) -> CredentialStatus: ...
    def get_secret(provider_id: str) -> str | None: ...
    def set_secret(provider_id: str, value: str) -> CredentialStatus: ...
    def delete_secret(provider_id: str) -> CredentialStatus: ...
```

Rules:

- Environment variables remain supported.
- Env source wins over app-entered source.
- Runtime memory remains safe V0.
- Future Windows persistence must use DPAPI or Windows Credential Manager.
- Never store plaintext provider keys in SQLite.
- Never store raw keys in frontend storage.
- Never include raw keys in events, logs, docs, tests, or API responses.

Current Scaleway module maps to the future design as:

| Current | Future |
| --- | --- |
| `get_effective_scaleway_api_key()` | `CredentialResolver.resolve(provider_id)` |
| `/secrets/scaleway/status` | `/credentials/providers/{provider_id}/status` later |
| runtime dict keyed by data root | `RuntimeCredentialStore` |
| `SCALEWAY_API_KEY` | env source mapping for provider `scaleway` |

Do not implement the generic credential route until provider registry design is accepted.

## 12. Authority/Audit Design

`AuthorityPolicy` decides whether an action requires approval, is allowed, or is blocked.

Actions that need authority gates:

| Action | Default |
| --- | --- |
| External AI call | gated by privacy, budget, credentials, task policy |
| Local Python run | explicit user run only |
| Future code generation | draft only, no execution |
| Future file read/write | explicit approval |
| Future file delete | blocked or high-friction approval |
| Future CAD/script generation | review before use |
| Future source fetch | source policy and privacy gate |
| Future assumption acceptance | explicit user decision |
| Future model patch apply | explicit user acceptance |

Authority result:

```python
class AuthorityDecision(BaseModel):
    allowed: bool
    requires_confirmation: bool
    blocked_reason: str | None
    risk_level: Literal["low", "medium", "high", "blocked"]
    policy_notes: list[str]
```

Audit events for AI provider flow:

- `AIRequestReceived`;
- `AIRequestClassified`;
- `AIProviderRouteSelected`;
- `AIProviderRouteBlocked`;
- `AIProviderCallStarted`;
- `AIProviderCallCompleted`;
- `AIProviderCallFailed`;
- `AIUsageRecorded`;
- `AIStructuredOutputValidated`;
- `AIStructuredOutputRejected`;
- `AIModelPatchProposed`;
- `AIModelPatchAccepted`;
- `AIModelPatchRejected`.

Event payload conventions:

- include `request_id`;
- include `workspace_id` if relevant;
- include `task_type`;
- include `privacy_class`;
- include `authority_decision`;
- include provider/model only after routing;
- include estimated/actual usage;
- include blocked reason;
- include no raw prompt if content may be sensitive;
- include no API key, auth header, raw provider payload, raw provider error, or raw sensitive content.

Current events should remain. Future AI events can coexist and gradually replace smoke-specific event payloads.

## 13. Frontend Direction

Normal workflows should show:

```text
Supervisor AI
```

Provider-specific UI should be limited to:

- settings;
- diagnostics;
- key status;
- smoke tests;
- usage/cost monitoring;
- audit/debug views.

Recommended future split:

```text
frontend/src/api/
  http.ts
  ai.ts
  secrets.ts
  system.ts
  domain.ts

frontend/src/pages/ai/
  AIDraft.tsx
  AICostGuardPanel.tsx
  ProviderDiagnosticsPanel.tsx
  ProviderCredentialsPanel.tsx
  SmokeTestsPanel.tsx
  SmokeConsolePanel.tsx
  DraftRequestPanel.tsx
  SupervisorPanel.tsx later
```

Near-term UI rules:

- Do not redesign the UI in 0E-C.
- Do not add Supervisor panel until backend route/policy is ready.
- Keep provider details out of normal modeling actions.
- Keep AI Smoke Console visibly diagnostic and narrow.
- Split the frontend before adding provider-neutral settings/status UI.

## 14. Migration Plan From Current Scaleway-shaped Code

### 0E-D1: Provider-neutral data models and interfaces, no new provider

Create backend-only contracts:

- `AIProviderAdapter`;
- `ProviderDefinition`;
- `ModelDefinition`;
- `ModelCapability`;
- `AITaskType`;
- `AIRequest`;
- `AIResponse`;
- `AIUsage`;
- `AIError`;
- `RoutingDecision`;
- `AuthorityDecision`;
- `CredentialStatus`.

No new provider calls.

### 0E-D2: Migrate existing Scaleway path into provider-neutral interface

Wrap current `ScalewayProvider` behind `AIProviderAdapter`.

Keep:

- existing fixed smoke tests;
- AI Smoke Console;
- runtime-memory key path;
- privacy/token/budget gates;
- no-network automated tests.

Change:

- smoke paths call adapter through registry;
- usage metadata becomes `AIUsage`;
- provider-specific status is derived from registry;
- blocked call events use `AIEvent` conventions.

### 0E-D3: Provider-neutral settings/status UI

Split frontend:

- AI status panel;
- provider diagnostics;
- credentials panel;
- smoke panels.

Keep user-facing workflow language provider-neutral.

### 0E-D4: Add one new provider with mocked tests first

Only after D1-D3:

- add one provider adapter;
- mocked tests prove no network by default;
- credential status works;
- provider cannot bypass privacy/budget/token gates;
- provider errors normalize.

Do not add multiple providers at once.

### 0E-D5: Add narrow Supervisor public/internal endpoint

Actual later milestone: `POST /ai/supervisor/public-test`.

It uses temporary internal provider selection instead of a full routing policy:

- DeepSeek when `provider_mode = deepseek` and configured;
- Scaleway fallback only when explicitly configured;
- public/internal `FAST_DEV` tasks only.

### Later: Routing policy

Implement `RoutingPolicy` only after the narrow endpoint has proven useful:

- task type;
- privacy class;
- capability;
- credential availability;
- budget/token state;
- provider status.

No ML-based routing yet.

It should accept task-specific structured requests, not become general chat.

## 15. Test Strategy

Required test layers:

### Contract Tests

- every adapter implements `status`;
- missing credential produces normalized auth error;
- provider call accepts `AIRequest` and returns `AIResponse`;
- provider response usage maps to `AIUsage`;
- provider error bodies are sanitized.

### Routing Tests

- secret blocks before provider selection;
- sensitive IP blocks before provider selection;
- structural secrets block before provider selection in `FAST_DEV`;
- unknown/sensitive/confidential blocking belongs to future `STRICT_IP` behavior;
- public/internal can route when budget/credentials allow;
- no model with missing capability is selected;
- disabled model/provider is not selected;
- fallback is deterministic and audited.

### Budget/Usage Tests

- estimated usage checked before call;
- actual usage recorded after call;
- missing usage falls back to estimate;
- provider cap cannot be bypassed;
- task max tokens are enforced.

### Credential Tests

- env source takes priority;
- runtime-memory source works;
- missing key blocks provider call;
- raw key never appears in response/event/log;
- wrong-shaped key requests do not echo submitted value.

### Event/Audit Tests

- request classified event is redacted;
- provider selected event includes model/provider but not raw prompt;
- blocked event includes reason;
- completed event includes usage;
- failed event normalizes provider error.

### No-network Tests

Automated tests must not call real providers by default. Use:

- provider mocks;
- adapter fakes;
- optional monkeypatch guard around HTTP calls;
- no real API keys in test fixtures.

## 16. Risks And Open Questions

| Severity | Action | Risk / Question |
| --- | --- | --- |
| high | refactor during 0E-D1 | How much of existing `AISettingsRead` should be migrated versus mirrored? |
| high | refactor during 0E-D1 | Should provider-neutral usage be table-backed immediately or in-memory/settings-backed first? |
| high | harden later | How should confidential content be allowed externally, if ever? |
| medium | refactor during 0E-D2 | Should fixed smoke tests stay special or become `AITaskType.smoke_test` through the full router? |
| medium | refactor during 0E-D3 | How much provider diagnostic detail should frontend expose without confusing normal users? |
| medium | postpone | When should DPAPI/Windows Credential Manager replace runtime memory? |
| medium | postpone | When does authentication become necessary for local UI? |
| later | postpone | How should local/Ollama models be labeled for privacy and capability? |

## 17. Explicit Do Not Implement Yet List

Do not implement yet:

- OpenAI adapter;
- Anthropic adapter;
- local/Ollama adapter;
- multi-provider router;
- broad Supervisor AI endpoint;
- Supervisor AI frontend panel;
- persistent credential vault;
- provider cost billing dashboard;
- source-grounded literature workflow;
- model patch application;
- AI-generated runner scripts;
- AI-generated code execution;
- multi-agent debate;
- sidecar bridge;
- workflow graph UI.

## 18. Recommended Next Milestone

Recommended next milestone:

```text
0E-D1 Provider-neutral AI Contracts
```

Scope:

- add provider-neutral backend models/interfaces;
- add registry skeletons with fake and Scaleway definitions only;
- add contract tests;
- keep existing behavior working;
- do not add any new provider;
- do not add Supervisor UI.

Acceptance criteria:

- `AIProviderAdapter` contract exists;
- `ProviderRegistry` and `ModelRegistry` can describe fake and Scaleway;
- `AIRequest`, `AIResponse`, `AIUsage`, and `AIError` exist;
- no live call path bypasses current gates;
- current smoke tests still pass;
- automated tests still use mocks/no network.

BlueRev modeling should remain paused until:

- provider-neutral AI layer exists;
- audit/gate events are clearer;
- artifact/workbench UX has a stable direction;
- runner remains reviewed-script-only.

## 19. 0E-D1 Implementation Note

Milestone 0E-D1 implements the first provider-neutral contracts in:

```text
backend/app/modules/ai/contracts.py
```

This is a contracts-only layer. It adds no new provider, no routing policy, no Supervisor AI endpoint, and no user-facing behavior change. The current Scaleway smoke-test and AI Smoke Console paths remain unchanged until a later migration milestone.

The next implementation milestone should be:

```text
0E-D2 Scaleway Adapter Migration
```

That milestone should wrap the existing Scaleway smoke path behind the provider-neutral adapter and registry contracts without changing safety gates or adding other providers.

## 20. 0E-D2 Implementation Note

Milestone 0E-D2 implements Scaleway as the first provider-neutral adapter in:

```text
backend/app/modules/ai/providers/scaleway_adapter.py
```

The adapter wraps the existing Scaleway smoke-call provider boundary in `providers/scaleway.py`. It maps provider-neutral `AIRequest` values for `smoke_test` and `smoke_console_test` into the existing live smoke completion methods, then maps sanitized Scaleway results into `AIResponse` and `AIUsage`.

This milestone does not add another provider, provider routing, dynamic model discovery, Supervisor AI, or frontend provider selection. The fixed smoke-test suite and AI Smoke Console keep their existing safety gates before the adapter is called:

```text
settings/budget/key gate
-> local privacy policy
-> token guard
-> Scaleway provider-neutral adapter
-> existing Scaleway HTTP provider module
```

Scaleway key resolution remains unchanged:

1. `SCALEWAY_API_KEY` environment variable.
2. Runtime-memory app-entered key.
3. Missing key.

The adapter statically exposes the configured Scaleway model through `ModelRegistryEntry`. It does not call Scaleway `/models`.

The next milestone should be:

```text
0E-D2 Review & Hardening
```
