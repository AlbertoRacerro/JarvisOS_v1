# 0E-D4 Strong Provider Smoke Path

## Purpose

0E-D4 adds exactly one additional strong provider behind the provider-neutral AI contracts: DeepSeek through an OpenAI-compatible chat-completions API shape.

This milestone validates that JarvisOS can call a stronger external LLM through the provider-neutral adapter pattern in `FAST_DEV` mode. It is still only a narrow smoke path.

## Provider Added

Provider:

```text
deepseek
```

Default model:

```text
deepseek-chat
```

Credential source:

```text
DEEPSEEK_API_KEY
```

Optional environment overrides:

```text
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
```

The key is environment-variable only for this milestone. It is not stored in SQLite, not accepted through frontend storage, and not saved in runtime-memory secret storage. A generalized credential UI can be designed later.

## Scope

Implemented:

- `DeepSeekProvider`;
- `DeepSeekProviderAdapter`;
- `POST /ai/provider-smoke/run`;
- mocked adapter and endpoint tests;
- provider-neutral status support for `provider_mode = deepseek`;
- documentation.

Not implemented:

- provider router;
- model routing policy;
- Supervisor AI;
- provider-specific bot UI;
- BlueRev modeling;
- Scientific Data Connectors;
- CAD, CFD, PFD, or geometry tooling;
- generalized credential store;
- frontend provider UI redesign.

## Smoke Path

Endpoint:

```text
POST /ai/provider-smoke/run
```

The endpoint is for short public/internal provider checks such as:

```text
Explain what a mass balance is in one paragraph.
Review this toy equation: X = X0 exp(mu t).
Summarize what an AI provider adapter does.
```

It is not general chat. It stores no conversation history and no prompt transcript.

## Required Gates

A DeepSeek smoke call requires:

- `policy_mode = FAST_DEV`;
- `provider_mode = deepseek`;
- `paid_ai_enabled = true`;
- monthly budget greater than zero and not exhausted;
- `DEEPSEEK_API_KEY` present in the backend environment;
- prompt length at or below `1000` characters;
- output request at or below `160` tokens;
- local policy allows the prompt.

In `FAST_DEV`, ordinary public/internal technical prompts are allowed. Structural secrets remain blocked before the provider call.

## Boundary Protections

DeepSeek smoke calls preserve the existing boundary rules:

- no raw API key in API responses;
- no raw API key in events;
- no Authorization header in events;
- no raw provider response metadata returned;
- no frontend localStorage/sessionStorage key handling;
- no automated network calls in tests;
- provider metadata is allowlisted.

## Adapter Behavior

The adapter maps:

```text
AIRequest -> OpenAI-compatible chat-completions request
provider response -> AIResponse
provider usage -> AIUsage
```

Usage source is:

- `actual` when both input and output tokens are returned;
- `mixed` when only one side is returned;
- `estimated` when usage is missing.

## Current Limitation

DeepSeek smoke usage is returned in the smoke response and event, but it does not yet have its own provider-neutral persistent monthly counter. The existing Scaleway smoke counters are not reused for DeepSeek to avoid misleading accounting. Provider-neutral usage storage remains a later milestone.

## Follow-up

0E-D5 adds a narrow Supervisor AI public/internal endpoint using the existing provider-neutral contracts, `FAST_DEV` mode, and smoke-only lessons without adding BlueRev proprietary workflows.
