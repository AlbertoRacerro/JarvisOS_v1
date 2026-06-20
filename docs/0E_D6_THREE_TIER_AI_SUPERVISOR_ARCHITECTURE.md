# 0E-D6 Three-Tier AI Supervisor Architecture

## D6B Correction Notice

0E-D6 is useful but incomplete. 0E-D6B corrects the ordering: the first decision layer must be a local gatekeeper, not an external provider tier. Raw user input must pass deterministic local hard rules and, later, an optional local Gemma classifier before any cloud provider is considered.

0E-D6C adds one more prerequisite: before implementing local gate contracts, JarvisOS must evaluate whether local Gemma can use context, memory, deterministic tools, and structured outputs reliably.

The D6 and D6B contract recommendations are superseded by:

```text
0E-D7 - Local Gemma Evaluation Harness and Golden Set
```

## 1. Executive Judgement

JarvisOS should grow toward one stable Supervisor AI interface backed by logical provider tiers:

- `cheap`;
- `medium`;
- `frontier`;
- optional future `local_offline`.

The user should not choose provider-specific bots. Provider and model names should stay internal, diagnostic, or admin/config-only.

The current provider-neutral contracts are a good start, but they do not yet represent provider tiers. The current `provider_mode` setting is acceptable for smoke paths, but it is not the right long-term abstraction for Supervisor AI routing.

Updated recommendation after 0E-D6C: evaluate local Gemma with a golden set before adding local gate or external tier contracts. Do not add a medium provider yet. After local evaluation clarifies Gemma's quality bar, add local gate/external tier contracts, then harden event/audit envelopes before any medium or frontier provider is integrated.

## 2. Current AI Architecture Assessment

Inspected backend files:

- `backend/app/modules/ai/contracts.py`;
- `backend/app/modules/ai/supervisor.py`;
- `backend/app/modules/ai/provider_smoke.py`;
- `backend/app/modules/ai/gateway.py`;
- `backend/app/modules/ai/settings.py`;
- `backend/app/modules/ai/budget.py`;
- `backend/app/modules/ai/privacy.py`;
- `backend/app/modules/ai/providers/deepseek.py`;
- `backend/app/modules/ai/providers/deepseek_adapter.py`;
- `backend/app/modules/ai/providers/scaleway_adapter.py`;
- AI tests under `backend/tests`;
- `docs/ARCHITECTURE.md`;
- `docs/DECISIONS.md`;
- relevant 0E docs.

Current strengths:

- AI calls enter through `AIGateway`.
- Provider HTTP logic is isolated in provider modules.
- Scaleway and DeepSeek both have provider-neutral adapters.
- `AIRequest`, `AIResponse`, `AIUsage`, provider registry, model registry, task types, privacy classes, and capabilities already exist.
- `FAST_DEV` protects structural secrets without blocking normal public/internal technical work.
- DeepSeek and Supervisor tests mock providers and do not require network.
- Request models reject user-supplied provider/model override fields for narrow smoke/Supervisor paths.

Current limits:

- Contracts lack `AIProviderTier`.
- `ModelRegistryEntry` describes capability and reasoning class, but not logical tier.
- `RoutingDecision` has provider/model fields, but no tier, fallback, or selection reason.
- `provider_mode` is still the main setting for concrete provider selection.
- Supervisor provider selection is temporary and hardcoded to DeepSeek or Scaleway.
- Provider smoke is deliberately DeepSeek-specific.
- Events record provider/model but not requested tier, selected tier, fallback reason, or considered tiers.
- DeepSeek usage is response/event-only and is not yet persisted in provider-neutral monthly usage records.

## 3. Three-Tier Provider Model

### cheap tier

Likely current mapping: DeepSeek or equivalent.

Role:

- FAST_DEV public/internal technical work;
- extraction and summarization;
- first drafts;
- generic code and debugging;
- low-risk technical reasoning;
- quick smoke checks.

Allowed content in early milestones:

- public;
- internal;
- no secret, sensitive IP, confidential, or unknown content unless a future stricter policy explicitly permits it.

### medium tier

Likely future mapping: Grok 4.3 or equivalent.

Role:

- stronger technical reasoning;
- review of cheap-tier output;
- model critique;
- serious coding/debugging;
- preliminary semi-sensitive work only after policy/authority design exists.

This tier should not be added until tier contracts, tier audit fields, provider-neutral usage records, and credential abstractions are ready.

### frontier tier

Likely future mapping examples: GPT-5.5, Gemini 3 / Deep Think, Claude Opus/Sonnet depending on later evaluation.

Role:

- final supervision;
- hard reasoning;
- architecture review;
- scientific and engineering validation;
- important decisions;
- synthesis and critique.

This tier should be the most tightly gated. It should not be the default path for ordinary cheap-tier work.

### optional local/offline tier

Future use:

- offline/private draft or classification assistance;
- local pre-screening;
- low-risk fallback when external calls are disabled.

This is optional and should not be implemented in 0E-D6.

## 4. Why Tier Semantics Are Better Than Provider-Specific Bots

Provider-specific bot UX creates the wrong mental model:

- users start choosing brands instead of asking for help;
- policy and privacy decisions become user-visible guesswork;
- provider churn leaks into product workflows;
- safety and cost behavior become harder to audit;
- adding a new provider risks adding a new button instead of improving the Supervisor.

Tier semantics keep the product stable:

```text
User
-> Supervisor AI
-> task/policy classification
-> cheap / medium / frontier tier choice
-> provider adapter
-> structured response
-> event/audit
```

The stable user-facing concept is "JarvisOS Supervisor". The internal implementation can change providers, models, or fallbacks without teaching users new provider-specific workflows.

## 5. Problems With Current `provider_mode`

`provider_mode` is useful for V0 smoke controls, but it is too concrete for future Supervisor AI.

Problems:

- It names concrete providers (`fake`, `scaleway`, `deepseek`) instead of logical provider roles.
- It cannot express "use cheap tier for draft and frontier tier for final review".
- It cannot express fallback policies per task.
- It couples operator settings to implementation details.
- It forces status/budget code to branch by provider name.
- It encourages tests to assert specific provider ids rather than tier behavior.

Keep `provider_mode` temporarily for compatibility with existing smoke paths. Do not use it as the main Supervisor AI routing abstraction.

## 6. Proposed Future Configuration Model

Use tier assignments, not one global provider mode.

Future admin/config shape:

```text
AIProviderTier:
  cheap
  medium
  frontier
  local_offline

TierAssignment:
  tier
  primary_provider_id
  primary_model_id
  fallback_provider_ids
  enabled
  max_privacy_class
  allowed_task_types
  monthly_token_cap
  monthly_budget_cap_usd
  require_user_confirmation
  notes
```

Recommended semantics:

- `tier_assignments` are admin/config-only.
- `default_provider` is not enough; it becomes ambiguous once tasks need different tiers.
- `provider_mode` remains a compatibility field for current smoke/manual controls until migrated.
- Provider/model names can appear in diagnostics and audit logs, not as normal user-facing choices.

## 7. Proposed Future Contracts

Add these concepts in a future contracts-only milestone before adding a medium provider:

```text
AIProviderTier:
  cheap
  medium
  frontier
  local_offline

TierSelectionReason:
  default_for_task
  explicit_admin_assignment
  capability_required
  policy_required
  budget_constrained
  provider_unavailable
  fallback_after_failure
  manual_admin_override

TierFallbackPolicy:
  none
  same_tier_only
  allow_downgrade
  allow_upgrade_with_confirmation
  allow_admin_configured_chain

ProviderRole:
  primary
  fallback
  diagnostic
  disabled

ProviderCapability:
  chat_text
  structured_json
  code_reasoning
  long_context
  source_grounded_summary
  vision_input
  low_cost
  low_latency
  high_reasoning
  frontier_reasoning
```

Existing `AITaskType` can remain the low-level enum, but Supervisor should introduce a clearer workflow layer:

```text
SupervisorTaskType:
  quick_explanation
  extraction
  summarization
  first_draft
  equation_review
  assumption_review
  code_review
  runner_error_explanation
  simulation_result_interpretation
  architecture_review
  scientific_validation
  decision_support
  synthesis

SupervisorDecisionMode:
  deterministic_only
  cheap_first
  medium_review
  frontier_review
  cascade_review
  human_confirmed
```

Future route planning records:

```text
SupervisorRoutePlan:
  request_id
  workspace_id
  policy_mode
  task_type
  privacy_class
  requested_tier
  selected_tier
  tier_selection_reason
  fallback_policy
  considered_tiers
  provider_id
  model_id
  blocked_reason

SupervisorExecutionRecord:
  request_id
  correlation_id
  route_plan
  provider_id
  model_id
  adapter_interface
  external_call_attempted
  external_call_succeeded
  usage
  safe_metadata
  event_ids
  created_at
```

Do not implement these in 0E-D6. The original D6 sequence started with `AIProviderTier`, but 0E-D6C supersedes that ordering: evaluate local Gemma with a golden set before adding local gate or external tier contracts.

## 8. Supervisor Request Flow

Future target flow:

```text
SupervisorRequest
-> parse request and assign request_id/correlation_id
-> settings/budget high-level gate
-> policy mode
-> local privacy classification
-> task type classification
-> requested/selected tier
-> provider tier resolver
-> provider adapter
-> AIResponse
-> event/audit
```

Important rules:

- Secret content is blocked before tier/provider resolution.
- Unknown content is not treated as public.
- Tier choice is internal unless an admin-only diagnostic endpoint exposes it.
- User requests cannot directly force provider/model.
- A future optional user-facing "quality" or "review depth" control may map to tier policy, but it must not be a provider picker.

## 9. Provider Smoke Flow

Current provider smoke is DeepSeek-specific and that is acceptable for 0E-D4.

Future provider smoke should become tier/provider diagnostic tooling, not product chat:

```text
ProviderSmokeRequest
-> admin-selected diagnostic target: provider_id or tier
-> same budget/policy/key gates
-> adapter
-> redacted smoke result
-> audit event with tier + concrete provider/model
```

Normal users should not see provider smoke as a provider menu. It is an operator/admin verification surface.

Keep current `/ai/provider-smoke/run` as a DeepSeek smoke path until the tier contracts exist. Do not broaden it ad hoc.

## 10. Event/Audit Requirements

Future AI events should include both logical tier and concrete provider/model:

- `policy_mode`;
- `task_type`;
- `supervisor_task_type`;
- `decision_mode`;
- `requested_tier`;
- `selected_tier`;
- `tier_selection_reason`;
- `fallback_policy`;
- `fallback_attempt_index`;
- `considered_tiers`;
- `provider_id`;
- `model_id`;
- `adapter_interface`;
- `privacy_class`;
- `blocked_reason`;
- `external_call_attempted`;
- `external_call_succeeded`;
- `usage`;
- `usage_source`;
- `request_id`;
- `correlation_id`;
- `timestamp`.

Events must not include:

- raw prompts;
- raw API keys;
- Authorization headers;
- raw provider responses;
- unredacted proprietary content;
- file contents.

Before adding a medium provider, event payloads should be normalized enough that cheap/medium/frontier attempts can be compared without provider-specific parsing.

## 11. Fallback Rules

Fallback should be deterministic and auditable.

Recommended rules:

- Default fallback policy is `none`.
- A failed provider call does not automatically escalate to a more expensive or more permissive tier.
- Downgrade fallback may be allowed for low-risk tasks when the result can be marked degraded.
- Upgrade fallback requires an explicit policy, budget allowance, and often user confirmation.
- Frontier tasks may fall back to medium only as "degraded review", not as equivalent final supervision.
- Fallback never bypasses privacy, budget, credential, token, or task-policy gates.
- Every fallback attempt gets its own event with attempt index and reason.

## 12. What Must Remain User-Facing

User-facing:

- one Supervisor AI interface;
- task intent;
- quality/depth labels if needed;
- safety status;
- whether external AI was used;
- high-level cost/token warning;
- limitations and blocked reasons in plain language;
- references to local policy and privacy boundaries.

User-facing wording should avoid:

- "Ask DeepSeek";
- "Ask Grok";
- "Ask GPT";
- "Ask Claude";
- provider-specific bot buttons.

## 13. What Must Remain Admin/Config-Only

Admin/config-only:

- provider ids;
- model ids;
- tier assignments;
- fallback chains;
- provider credentials;
- provider health;
- model capability registry;
- monthly budget caps per provider/tier;
- token caps per provider/tier;
- diagnostic smoke endpoints;
- raw provider error classes.

Concrete provider/model details may appear in admin diagnostics and audit records, not ordinary workflow prompts.

## 14. What To Harden Before Medium Provider

Before adding a medium provider:

1. Add `AIProviderTier` contracts and tier metadata on model/provider registry entries.
2. Add tier fields to AI route-plan/audit events.
3. Define a narrow `TierAssignment` settings shape, even if stored as static config initially.
4. Keep `provider_mode` as compatibility only and stop using it as Supervisor's conceptual selector.
5. Add provider-neutral usage records or at least a provider-neutral usage event envelope.
6. Add tests proving user requests cannot select provider/model/tier directly.
7. Add tests proving structural secrets block before tier/provider resolution.
8. Add diagnostic status that reports tier readiness without exposing secrets.

Do not add a medium provider before these are done.

## 15. What To Harden Before Frontier Provider

Before adding a frontier provider:

1. Implement explicit frontier task policies.
2. Require stronger confirmation or admin settings for high-cost/high-impact requests.
3. Add provider-neutral persistent usage accounting.
4. Add normalized audit records with tier, fallback, cost, and provider/model.
5. Add stricter privacy policy for confidential/sensitive IP paths.
6. Add output contract validation for scientific/engineering review tasks.
7. Add deterministic fallback and retry policy.
8. Define redaction rules for all event payloads and provider errors.
9. Add a review gate for any source-grounded, file, runner, or BlueRev workflow.

Frontier should not be introduced as a general chat button.

## 16. Recommended Next Milestones

Superseded D6 recommendation: an AIProviderTier contract skeleton. Do not treat this as the active next milestone.

Superseded D6B replacement: a local gate and external tier contract skeleton. Do not treat this as the active next milestone.

D6C corrected next milestone:

```text
0E-D7 - Local Gemma Evaluation Harness and Golden Set
```

Corrected scope:

- create a golden set for local Gemma evaluation;
- define expected structured outputs;
- define failure categories;
- evaluate context, memory, and deterministic tool grounding before gate contracts;
- no provider router;
- no new provider;
- no Supervisor expansion;
- no Gemma runtime;
- no UI.

Recommended after that:

```text
0E-D8 - AI Event/Audit Envelope For Tiered Supervisor
```

Scope:

- normalize provider/tier event fields;
- add tier fields to existing Supervisor/provider smoke events where available;
- keep concrete behavior unchanged;
- add redaction tests.

Do not pick option C, medium provider smoke-only, as the next implementation. JarvisOS is not ready for that yet.

## 17. Explicit Non-Goals

0E-D6 does not implement:

- new providers;
- Grok;
- OpenAI;
- Gemini;
- Claude;
- provider router;
- expanded Supervisor endpoint;
- Supervisor UI;
- chat;
- memory;
- streaming;
- BlueRev modeling;
- file upload;
- source ingestion;
- runner execution;
- CAD, CFD, PFD, or geometry workflows;
- MCP;
- agents;
- sidecars;
- desktop automation;
- multi-agent runtime.

## 18. Final Recommendation

JarvisOS should adopt tier semantics before adding any medium or frontier provider.

Decisive answers to the review questions:

1. Current contracts partially support provider-neutral routing, but not logical provider tiers.
2. Minimal later extension: add `AIProviderTier`, tier metadata on registry entries, and route-plan fields for requested/selected tier and selection reason.
3. Current Supervisor endpoint does not let the user select a provider, but internally it assumes concrete DeepSeek/Scaleway branches.
4. Current provider smoke path is intentionally DeepSeek-specific and should remain diagnostic until tier smoke design exists.
5. `provider_mode` is a bad long-term Supervisor abstraction; keep it only for compatibility.
6. Future configuration should use `tier_assignments`, not one `default_provider`.
7. Tasks should map to tiers through deterministic policy tables before any AI-assisted routing.
8. Fallback should be explicit, gated, audited, and disabled by default.
9. Events should record both tier and concrete provider/model.
10. Provider/model/tier assignment must remain admin/config-only; the user sees one Supervisor.
11. Before a medium provider, harden tier contracts, event/audit fields, usage accounting, and credential/status abstractions.
12. Before a frontier provider, harden confirmation, privacy, usage persistence, output validation, fallback, and audit policy.

JarvisOS is **not ready to add the medium provider**. It is ready for a local Gemma evaluation harness and golden set before local gate/external tier contracts.
