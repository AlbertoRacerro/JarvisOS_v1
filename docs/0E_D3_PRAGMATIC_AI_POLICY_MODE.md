# 0E-D3 Pragmatic AI Policy Mode

## Purpose

0E-D3 corrects the AI roadmap for the current stage of JarvisOS.

JarvisOS is still early-stage. The system currently contains mostly public physics, generic code, toy models, architecture notes, and non-proprietary design exploration. The AI boundary should protect structural secrets and provider credentials, but it should not block ordinary technical prompts just because they mention modeling, geometry, patents, BlueRev, or architecture.

## Policy Modes

### `FAST_DEV`

`FAST_DEV` is the default mode.

It allows early development to move quickly:

- public/internal technical prompts may go to approved external AI paths;
- generic physics, literature-derived formulas, toy models, generic Python, software architecture, and early non-proprietary BlueRev reasoning are allowed;
- token, budget, provider-mode, live-smoke, and credential gates still apply;
- API keys, authorization headers, env var content, raw provider metadata, logs, events, responses, and frontend storage remain protected;
- raw prompt text is not stored in smoke-console events.

In `FAST_DEV`, the local content policy is intentionally minimal. It blocks structural secret patterns such as API key fields, `.env` references, `Authorization: Bearer ...`, private keys, and explicit token/password assignments. It does not use broad keyword blocking for terms such as `patent`, `geometry`, `BlueRev`, `Smart Joint`, or `confidential`.

### `STRICT_IP`

`STRICT_IP` is a future stricter mode. It exists as a policy-mode value now, but it is not the default operating model.

Future `STRICT_IP` behavior may include:

- stronger local classification;
- sensitive-IP blocking;
- confidential-content approval flows;
- AI router prefiltering;
- deterministic AuthorityPolicy final decisions.

Do not treat `STRICT_IP` as a blocker for current early development.

### `DISABLED`

`DISABLED` is an explicit policy mode for turning AI policy status off at the policy layer. Existing paid-AI, budget, provider, token, and credential gates still remain separate controls.

## Boundary Protections That Remain Mandatory

Even in `FAST_DEV`:

- API keys are never returned by API responses;
- raw Scaleway keys are runtime-memory only unless supplied by environment variable;
- raw keys are not written into SQLite `ai_settings`;
- events do not include raw keys or raw smoke-console prompts;
- provider metadata remains allowlisted;
- frontend code must not store API keys in `localStorage` or `sessionStorage`;
- automated tests must not call real providers.

## Provider-neutral Status Foundation

The backend now exposes policy/provider-neutral status concepts alongside the current Scaleway-specific fields:

- `policy_mode`;
- `ai_enabled`;
- `provider_mode`;
- `provider_id`;
- `adapter_enabled`;
- `usage_total_tokens`;
- `budget_status`;
- `credential_status`.

The Scaleway-specific counters remain the active V0 storage fields. They should be generalized before adding a second provider.

## What This Does Not Implement

0E-D3 does not add:

- a new provider;
- an AI router;
- Supervisor AI;
- BlueRev Workbench;
- Scientific Data Connectors;
- CAD, CFD, or geometry tooling;
- runner expansion;
- strict IP classifier;
- long-term credential vault.

## Future Direction

The future AI architecture can still add deterministic AuthorityPolicy and stricter IP protection. The correction is about timing: AuthorityPolicy should not become a premature blocker while JarvisOS is still exploring public/internal technical material.

The likely next provider-neutral milestone is to continue generalizing status, settings, usage accounting, and audit events without adding a second provider yet.
