# 0E-D5 Narrow Supervisor AI Endpoint

## Purpose

0E-D5 adds the first minimal Supervisor AI vertical slice:

```text
POST /ai/supervisor/public-test
```

This endpoint proves that JarvisOS can receive a public/internal technical task, apply `FAST_DEV` policy, choose an available provider internally, call through provider-neutral contracts, return a structured response, and record redacted events.

It is not the full JarvisOS Supervisor.

## Scope

Implemented:

- `SupervisorPublicTestRequest`;
- `SupervisorPublicTestResponse`;
- backend-only endpoint;
- internal temporary provider selection;
- DeepSeek-first provider path when configured;
- Scaleway fallback only when explicitly configured for live smoke;
- structured usage in the response;
- redacted lifecycle events.

Not implemented:

- general chat;
- streaming;
- conversation history or memory;
- user-selectable provider/model;
- provider router;
- Supervisor UI;
- BlueRev modeling;
- source-grounded literature mode;
- file upload or file parsing;
- runner execution;
- CAD, CFD, PFD, or geometry tooling;
- agents, MCP, sidecars, or desktop automation.

## Request

```text
SupervisorPublicTestRequest
```

Fields:

- `prompt`;
- optional `task_type`;
- optional `workspace_id`;
- optional `max_output_tokens`;
- optional safe `metadata`.

The request intentionally does not accept provider id or model id. Unknown extra fields such as `provider_id` or `model_id` are rejected by the request model and cannot force provider selection.

## Response

```text
SupervisorPublicTestResponse
```

Fields include:

- `answer`;
- `task_type`;
- `policy_mode`;
- `provider_id`;
- `model_id`;
- `usage`;
- `safety_status`;
- `blocked_reason`;
- `event_id`;
- `request_id`;
- `correlation_id`;
- `external_call_attempted`;
- `external_call_succeeded`;
- `limitations`.

## Temporary Provider Selection

This milestone does not implement a router.

Temporary rule:

1. If `provider_mode = deepseek`, paid AI is enabled, budget is available, and `DEEPSEEK_API_KEY` is present, use the DeepSeek adapter.
2. If `provider_mode = scaleway`, Scaleway smoke/live settings are enabled, an API key is present, and token cap allows the request, use the Scaleway adapter as fallback.
3. Otherwise return `provider_unavailable` or the specific gate reason.

The user cannot choose a provider or model in the endpoint request.

## FAST_DEV Policy

The endpoint only runs in `FAST_DEV`.

Allowed:

- public/internal technical prompts;
- toy equations;
- generic engineering explanations;
- generic runner error explanations;
- non-sensitive software architecture notes.

Blocked before provider:

- empty prompts;
- prompts longer than `2000` characters;
- output requests above `240` tokens;
- unsupported task types;
- file path/file read requests;
- structural secret patterns such as API key fields, `.env`, `Authorization: Bearer ...`, private keys, explicit token/password assignments.

It does not add broad semantic keyword blocks for engineering terms.

## Events And Usage

The endpoint records events for:

- request started;
- provider selected;
- provider failed;
- provider completed;
- blocked request.

Event payloads include:

- `policy_mode`;
- `task_type`;
- `provider_id`;
- `model_id`;
- privacy class;
- blocked reason;
- external call attempted/succeeded flags;
- provider-neutral usage;
- request/correlation ids;
- prompt length.

Event payloads do not store the raw prompt, raw API keys, Authorization headers, or raw provider metadata.

DeepSeek usage is returned as provider-neutral `AIUsage` in the response and event. Scaleway fallback usage also updates the existing Scaleway monthly token counters. Provider-neutral monthly usage persistence remains a later milestone.

## Next Step

JarvisOS is now ready for a first practical public/internal AI workflow design, provided it remains narrow and uses this Supervisor endpoint pattern. It is still not ready for BlueRev proprietary modeling, file ingestion, source-grounded research, autonomous agents, or broad provider routing.
