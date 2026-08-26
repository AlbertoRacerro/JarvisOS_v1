# PD-05 — Settings contract

Status: future product direction; not implementation authority.

## Purpose

Define a stable operator-facing Settings structure that can survive provider/backend changes without redesigning the UI around today's implementation details.

## Settings navigation

Normal horizontal tabs are exactly:

- `Appearance`
- `AI`
- `System`

Settings does not require the persistent Jarvis sidecar used in engineering/coding workspaces.

The layout should be compact, row/divider driven and left-aligned. Avoid oversized dashboard cards and decorative previews that do not improve configuration clarity.

# Appearance

Appearance owns local visual preferences.

Required concepts:

- appearance/theme: System / Light / Dark;
- accent preset selection;
- custom HEX accent;
- future optional interface density/typeface/motion preferences only when product need exists.

Accent affects navigation/focus/selection emphasis. Engineering/scientific/status colors remain semantically independent of the selected accent.

# AI

AI Settings is provider-agnostic. It must not be designed around Scaleway or any single current model/provider.

The three stable conceptual groups are:

1. `Providers`
2. `Orchestration`
3. `Budget & limits`

## Providers

Each provider uses the same generic management pattern.

Conceptual provider fields/capabilities include:

- provider name/ID;
- connection/configuration status;
- endpoint when relevant;
- secure credential state;
- model/capability catalogue when discoverable;
- usage/cost capability when available;
- connect/manage/test/refresh actions.

The UI must not require one API-key field per model. Credentials belong to provider/integration scope.

Examples expected to fit this generic model include, without hardcoding architecture around them:

- DeepSeek;
- Z.AI;
- OpenAI;
- Anthropic;
- OpenRouter;
- local AI;
- Scaleway or other future/legacy providers.

A provider row may expand into a generic Manage view with actions conceptually similar to:

- update/replace API key;
- test connection;
- refresh available models;
- disconnect/remove persisted credential.

Never redisplay a full secret after storage. Credential changes must use the canonical secure-storage boundary rather than frontend/localStorage/repository persistence.

## Tool/integration identity vs provider API identity

Do not conflate a coding-agent integration with a generic provider API credential.

For example, the UI/data model should be able to represent separately when applicable:

- OpenAI API credential;
- Codex integration/authentication;
- Anthropic API credential;
- Claude Code integration/authentication.

The exact authentication mechanics belong to future backend/integration specs.

## OpenRouter/opportunistic gateways

The provider model must support gateway providers such as OpenRouter without making them mandatory intermediaries for providers that are already directly configured.

The product direction allows opportunistic use of temporary free/cheap models when policy permits, but this is an orchestration/policy decision, not a reason to route all traffic through a gateway.

Sensitive/private project context must remain subject to canonical egress/sensitivity policy regardless of zero price.

## Orchestration

Settings should expose stable policy/permission concepts rather than force the user to manually route every task to a fixed model.

Intended future shape includes status/controls conceptually similar to:

- routing mode: automatic/Hermes;
- orchestrator identity/status;
- fallback allowed;
- opportunistic free models allowed;
- deterministic validation required;
- sensitive-context restrictions;
- advanced policy link/details.

Hermes or a later accepted orchestrator may choose concrete models/tools dynamically. The UI configures limits/permissions and exposes state; it is not the orchestration engine.

Existing JarvisOS policy/determinism remains authoritative: model output is proposal, deterministic engineering/runtime checks own executable/scientific validation, and egress/budget policy is not bypassed by the orchestrator.

## Budget & limits

Expose global/operator-readable limits and usage without assuming every provider reports identical metrics.

Conceptual fields may include:

- monthly API budget;
- global/provider token limits where supported;
- hard-stop limits;
- current-month spend;
- current-month token usage;
- budget status.

Provider-specific fields belong inside provider management or Advanced details, not in the permanent top-level Settings information architecture.

# System

System is the normal home for diagnostics that do not justify a Home dashboard.

Use compact rows grouped conceptually under:

- `Application`;
- `Runtime`;
- `Data`;
- `Services`;
- `Advanced` (collapsible).

Examples include:

- JarvisOS version/environment;
- backend online/status/endpoint;
- local AI runtime state;
- data-root state;
- database engine/readiness/schema/path;
- provider configuration state;
- Process/BLUECAD service availability;
- migration/runtime diagnostic details;
- logs/reload-system-state actions.

Legacy diagnostic pages should not appear as normal primary settings destinations. Development-only diagnostics may remain under Advanced while they are still needed.

## Backend integration rule

The future frontend must prefer existing canonical backend boundaries and generalize them rather than creating parallel stores:

- provider gateway/registry capability should evolve rather than adding one-off provider plumbing per UI row;
- secure credential storage should evolve from the accepted secret-storage boundary;
- egress/sensitivity/budget policy remains canonical;
- system status should read canonical runtime/database/provider state;
- Hermes integration, if selected later, must sit behind JarvisOS authority rather than replace it implicitly.
