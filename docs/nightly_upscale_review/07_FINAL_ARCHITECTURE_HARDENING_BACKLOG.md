# Final Architecture Hardening Backlog

## Priority Backlog

| # | Title | Severity | Action Type | Affected Files/Modules | Reason | Risk If Skipped | Recommended Milestone | Change Type | Test Requirements |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Deterministic AuthorityPolicy design | blocker | refactor before next provider | `backend/app/modules/ai/` | AI router must recommend, not decide. | Sensitive content may reach providers through router/provider shortcuts. | 0E-D3 | docs then code | policy unit tests, blocked-before-provider tests |
| 2 | Provider-neutral AI settings/status | blocker | refactor during provider-neutral status/settings | `ai/settings.py`, `ai/budget.py`, `ai/models.py`, frontend AI page | Current settings are Scaleway-shaped. | Second provider creates duplicate flags and unclear UI. | 0E-D3 | code | full AI tests, frontend build |
| 3 | Provider-neutral usage records | high | refactor before next provider | `ai/settings.py`, schema, events | Counters are Scaleway smoke-specific. | Costs and tokens become inconsistent across providers. | 0E-D3 or 0E-D4 | code/schema | migration tests, usage accounting tests |
| 4 | AI audit event schema helpers | high | refactor before next provider | `events`, `ai` | Event payloads are free-form. | Audit becomes untraceable as router/provider paths multiply. | 0E-D4 | code | event redaction and schema tests |
| 5 | Artifact relative storage key policy | high | refactor before BlueRev workbench | `files`, `runner`, schema | Absolute path identity will break data-root moves and object storage migration. | Artifact viewer and backups become fragile. | 0E-E | code/schema | path relocation tests |
| 6 | Artifact taxonomy and metadata fields | high | refactor before file/artifact viewer | `files`, `runner`, docs | File types need safe handling rules. | Unsafe or useless previews/parsers. | 0E-E | code/schema | artifact metadata tests |
| 7 | Runner V1 manifest design | high | refactor before runner expansion | `runner` | Multiple scripts need declared inputs, outputs, dependencies, limits. | New scripts weaken V0 safety. | 0F-A | docs first | manifest validation tests later |
| 8 | Split runner service before second script | high | refactor before runner expansion | `runner/service.py` | It already orchestrates many concerns. | Runner becomes monolith. | 0F-B | code | full runner tests |
| 9 | Formal migration trigger and old DB tests | high | refactor before BlueRev workbench | `core/schema.py`, `core/database.py`, tests | Local users keep old SQLite files. | New releases break existing data. | next schema-heavy milestone | code/tests | migration snapshot tests |
| 10 | Frontend API client split | medium | refactor during provider-neutral status/settings | `frontend/src/api/client.ts` | Single file mixes all domains. | UI changes become risky. | 0E-F | code | frontend build |
| 11 | Split AI page panels | medium | refactor during provider-neutral status/settings | `AIDraft.tsx` | Page mixes many responsibilities. | Supervisor/provider UI becomes unmaintainable. | 0E-F | code | frontend build |
| 12 | Shared API error envelope | medium | refactor later | `core/errors.py`, routes | Error shapes vary by module. | Frontend must branch by endpoint. | 0E-F or 0F | code | endpoint error tests |
| 13 | Generic credential concepts | medium | refactor before next provider | `secrets`, `ai` | Secrets are Scaleway-only. | New provider duplicates key endpoints. | 0E-D3 | docs then code | secret redaction tests |
| 14 | Source/provenance schema design | high | refactor before Scientific Data Connectors | future source modules, artifacts | Source ingestion needs citation and extraction provenance. | Extracted claims become untraceable. | later design gate | docs | none initially |
| 15 | Artifact viewer design gate | medium | refactor before file/artifact viewer | frontend, files | Viewer must not expose unsafe parsers or absolute paths. | UI encourages unsafe file handling. | 0F | docs | frontend build after implementation |
| 16 | CAD/PFD opaque artifact policy | high | refactor before CAD/PFD outputs | files, runner, future CAD/PFD | Complex files need safe no-parser defaults. | Unsafe converters or false validation. | later design gate | docs | file metadata tests later |
| 17 | Workbench design gate | blocker | refactor before BlueRev workbench | backend domain, frontend | Workbench combines all subsystems. | Product UI builds on unstable foundations. | 0F-B | docs | none initially |
| 18 | Event retention and export policy | medium | refactor later | events, backup docs | Events will grow with AI and runner usage. | DB bloat and unclear backups. | later | docs/code | event list tests |
| 19 | No-network automated test fixture | medium | harden now | backend tests | AI tests rely on local monkeypatch patterns. | Future provider tests could accidentally call network. | next AI code milestone | code/tests | no-network fixture tests |
| 20 | Current operating model page | low | document only | docs | README is milestone-heavy. | New contributors read history instead of current state. | any docs milestone | docs | none |

## Before Adding A Second Provider

Must complete:

- AuthorityPolicy design and tests.
- Provider-neutral settings/status.
- Provider-neutral usage records or compatibility mirror.
- Generic credential abstraction.
- Typed AI audit events.
- No-network test fixture.

Do not add OpenAI, Claude, DeepSeek, Ollama, or Mistral before these are done.

## Before Implementing AI-assisted Router

Must complete:

- local hard prefilter policy;
- router input minimization policy;
- `AIRoutingProposal`;
- `AuthorityDecision`;
- provider selection reason codes;
- audit of proposal versus final decision;
- tests proving secret, sensitive_ip, unknown, and confidential content do not reach router.

## Before Supervisor AI Endpoint

Must complete:

- task policy registry;
- authority decision pipeline;
- provider-neutral response envelope;
- audit event helpers;
- UI wording that avoids provider-specific bots.

## Before BlueRev Models

Must complete:

- Workbench design gate;
- artifact taxonomy;
- SimulationRun/Decision provenance policy;
- runner manifest design;
- AI authority policy.

## Before File/Artifact Viewer

Must complete:

- relative storage key implementation;
- artifact type taxonomy;
- safe preview policy;
- backend open/download endpoint design;
- no raw absolute path dependency in frontend.

## Before Scientific Data Connectors

Must complete:

- source/provenance schema;
- parser sandbox policy;
- copyright/citation policy;
- extraction output artifact type;
- authority policy for source-grounded AI tasks.

## Before CAD/PFD Outputs

Must complete:

- opaque artifact policy;
- converter/parser design gate;
- file size limits by type;
- preview strategy;
- provenance link to run/model.

## Before Expanding Python Runner

Must complete:

- V1 script manifest;
- input/output schema validation by manifest;
- dependency policy;
- service split;
- artifact policy alignment;
- reviewed-script approval workflow.

## Near-term Milestone Recommendation

Next best milestone:

```text
0E-D3 Provider-neutral AI Status, Settings, Usage, and Authority Design
```

Scope:

- design only or very small contracts;
- no new provider;
- no router implementation;
- no Supervisor endpoint;
- no UI redesign;
- tests only if small contract code is added.

Second best milestone:

```text
0E-E Artifact Relative Storage And Taxonomy Design
```

Use this if storage is prioritized before AI expansion.

