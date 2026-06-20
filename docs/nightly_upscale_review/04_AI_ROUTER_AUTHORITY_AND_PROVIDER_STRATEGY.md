# AI Router, Authority, And Provider Strategy

> 0E-D6D supersession note: this nightly review is historical. Its Scaleway router proposal must not be used as the current architecture. D6B and D6C require local deterministic rules and a local Gemma evaluation foundation before any AI-assisted gate or external provider routing work. Scaleway remains a smoke provider, optional simulation/fallback candidate, and adapter example, not the local privacy classifier or core router.

## Prime Rule

```text
The AI router may recommend.
The deterministic AuthorityPolicy must decide.
```

No AI provider, including Scaleway, may authorize its own access to sensitive content.

## Future Pipeline

```text
Local deterministic hard prefilter
-> optional AI-assisted router/classifier
-> deterministic AuthorityPolicy enforcement
-> provider-neutral adapter call
-> structured AIResponse
-> audit/usage event
```

## Current State

What exists:

- `AIProviderAdapter`;
- `AIRequest`;
- `AIResponse`;
- `AIUsage`;
- `ProviderRegistry`;
- `ModelRegistry`;
- `RoutingDecision`;
- `GateDecision`;
- `AuthorityDecision`;
- Scaleway provider-neutral adapter for smoke paths;
- fake provider for deterministic modeling draft;
- local privacy policy;
- token guard;
- budget guard;
- runtime-memory Scaleway key.

What is still missing:

- provider-neutral settings/status;
- provider-neutral usage table;
- deterministic AuthorityPolicy service;
- router proposal object;
- task policy registry;
- audit event schemas;
- generic credential abstraction.

## Proposer, Critic, Synthesizer

### Superseded Proposal v1

The historical v1 proposal attempted to put Scaleway in the first AI-assisted routing role because it is EU-hosted and already integrated.

### Critique v1

If router AI sees raw prompts before local filtering, it becomes an egress path. That would violate the core safety model. A router can leak the very content it is meant to classify.

### Improved Proposal v2

Only allow router AI after local deterministic prefilter removes or blocks:

- secrets;
- `sensitive_ip`;
- unknown content;
- raw BlueRev confidential content;
- files;
- code;
- `.env` content;
- proprietary geometry;
- patent text;
- private strategy.

Router AI receives only minimized metadata or sanitized excerpts explicitly allowed by policy.

### Critique v2

Over-minimization may reduce routing quality.

### Final Synthesis

Prefer safe under-routing over unsafe egress. If metadata is insufficient, block or route to local/fake handling. Router output is a proposal, not a decision.

Residual risk: even sanitized metadata can reveal project intent. AuthorityPolicy must define allowed metadata by task.

## Superseded Historical Scaleway Router Concept

The following section is retained as historical review material only. It is not current guidance.

Scaleway Router AI may be considered only for:

- public or internal content approved by local prefilter;
- synthetic smoke diagnostics;
- provider selection among remote providers when content is already egress-approved;
- low-risk classification of task type or response format.

It must not be used for:

- secrets;
- raw credentials;
- `sensitive_ip`;
- unknown content;
- raw confidential BlueRev modeling content;
- source documents before source policy exists;
- runner scripts;
- private strategy;
- proprietary geometry;
- patent-sensitive text.

## Router Input Policy

Allowed router inputs:

- task type;
- coarse privacy class from local deterministic classifier;
- workspace-safe metadata such as `workspace_kind = engineering`;
- token estimate;
- requested output format;
- provider availability metadata;
- sanitized short text only when local policy says public/internal.

Disallowed router inputs:

- API keys;
- Authorization headers;
- raw secrets;
- raw files;
- code;
- private keys;
- raw runner logs with possible secrets;
- proprietary geometry;
- BlueRev sensitive design content.

## Future Objects

### `AIRequestContext`

Purpose: normalized request context before routing.

Fields:

- request id;
- workspace id;
- task type;
- local sensitivity classification;
- content summary or safe excerpt;
- token estimate;
- user-visible intent;
- allowed egress classes;
- artifact/source references;
- schema version.

### `SensitivityClassification`

Purpose: deterministic local classification record.

Fields:

- privacy class;
- classifier version;
- matched rule ids;
- confidence or certainty class;
- blocked by hard prefilter;
- safe explanation.

### `AIRoutingProposal`

Purpose: optional AI or deterministic routing recommendation.

Fields:

- proposal id;
- request id;
- proposed provider id;
- proposed model id;
- candidate providers;
- reason codes;
- expected capability match;
- expected cost class;
- input sent to router flag;
- router provider id if AI-assisted;
- safe router metadata.

### `AuthorityDecision`

Purpose: final deterministic allow/block decision.

Fields:

- allowed;
- blocked reason;
- allowed provider id;
- allowed model id;
- task type;
- privacy class;
- egress allowed;
- requires human confirmation;
- policy version;
- reason codes.

### `ProviderSelectionReason`

Purpose: explain why a provider/model was selected.

Examples:

- `task_capability_match`;
- `eu_hosted_preferred`;
- `local_only_required`;
- `budget_cap`;
- `low_cost`;
- `structured_output_required`;
- `provider_disabled`;
- `missing_credentials`.

### `BlockedReason`

Purpose: stable machine-readable blocking code.

Examples:

- `privacy_secret_blocked`;
- `privacy_sensitive_ip_blocked`;
- `privacy_unknown_blocked`;
- `provider_credentials_missing`;
- `budget_zero`;
- `token_cap_exceeded`;
- `authority_requires_local_only`;
- `task_not_supported_by_provider`.

### `AIUsageRecord`

Purpose: durable provider-neutral accounting.

Fields:

- request id;
- workspace id;
- provider id;
- model id;
- task type;
- input tokens;
- output tokens;
- total tokens;
- usage source;
- estimated cost;
- currency;
- created at.

## Audit Requirements

Every real or attempted AI route should produce safe audit data:

- local classification;
- routing proposal if any;
- final authority decision;
- provider adapter called or not;
- external call attempted;
- external call succeeded;
- usage estimate and actual usage;
- no raw secrets;
- no raw authorization headers;
- no raw provider responses.

## Avoiding Provider-specific Bot UI

The UI should expose:

- one Supervisor AI surface for workflows;
- settings/status diagnostics for providers;
- smoke-test tools for operators.

The UI should not expose:

- "Ask GPT";
- "Ask Claude";
- "Ask Scaleway";
- model pickers in normal modeling flows.

Provider/model used can be shown after the fact in diagnostics and audit.

## Avoiding Magical Routing

Routing must be explainable through reason codes and audit trails. A user should be able to inspect:

- why a request was blocked;
- why a provider was selected;
- whether any router AI was used;
- what class of data left the machine;
- what tokens were used.

## Next Implementation Sequence

1. Design and test `AuthorityPolicy`.
2. Add provider-neutral status/settings concepts.
3. Add provider-neutral usage records or a compatibility mirror.
4. Add typed AI audit payload helpers.
5. Only then consider AI-assisted router design.
6. Only after that consider a second provider.
