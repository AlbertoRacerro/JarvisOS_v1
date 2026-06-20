# 0E-A Organic System Review And Architecture Hardening Plan

## 1. Executive Assessment

JarvisOS is strong enough to continue as a local-first engineering foundation, but it is not ready for BlueRev-specific modeling, Scientific Data Connectors, CAD/CFD, or multi-provider AI integrations.

The current system has three working foundations:

- a small local FastAPI/SQLite domain spine;
- a guarded AI smoke path with Scaleway live smoke support;
- a backend-only Python Runner V0 for one reviewed deterministic script.

The main architectural problem is no longer missing features. The problem is that the early proof-of-foundation code now needs consolidation before more capability is added. The highest-risk areas are data evolution, artifact/query access, runner service density, AI provider abstraction, and operator state clarity.

Main judgement: **pause BlueRev modeling and UI expansion. Do 0E-B Data Infrastructure Hardening next.**

Current readiness by area:

| Area | Status | Severity | Judgement |
| --- | --- | --- | --- |
| Repository structure | harden | medium | Boundaries exist, but large service/page files are emerging. |
| Data schema | harden | high | Schema is useful, but migration/version discipline is now too weak for further growth. |
| SimulationRun | keep | medium | It is the right canonical run record, but needs better query/read APIs and lifecycle indexing. |
| Artifacts | harden | high | Records exist, but query/API/path semantics are underdeveloped. |
| Events | harden | medium | Useful audit breadcrumbs, not yet a reliable audit model. |
| Python Runner V0 | harden | high | Validated for reviewed scripts, not safe for broader execution or AI-generated code. |
| AI Gateway | harden | high | Correct boundary, but provider abstraction is still Scaleway-specific in practice. |
| Frontend | postpone | medium | Adequate operator surface; do not expand until backend abstractions settle. |
| Scripts/startup | harden | low | Usable Windows-first path, but still developer-grade. |
| BlueRev modeling | postpone | high | Do not build models on the current infrastructure yet. |

## 2. Current Architecture Map

### Backend

```text
backend/app/
  main.py
  api/
    health.py
    system.py
  core/
    config.py
    paths.py
    database.py
    schema.py
    bootstrap.py
  modules/
    workspaces/
    modeling/
    events/
    files/
    ai/
      gateway.py
      budget.py
      privacy.py
      token_guard.py
      settings.py
      smoke_tests.py
      smoke_console.py
      providers/
        fake.py
        scaleway.py
    runner/
      routes.py
      service.py
      safety.py
      local_python.py
      examples/batch_growth.py
```

### Data

Runtime state is stored under the configured data root, defaulting to:

```text
C:\JarvisOS
```

SQLite currently stores:

- workspaces;
- entities and entity links;
- events;
- artifacts;
- model specs;
- assumptions;
- parameters;
- model versions;
- simulation runs;
- runner jobs;
- run logs;
- run artifacts;
- decisions;
- AI settings.

### Frontend

```text
frontend/src/
  api/client.ts
  pages/
    Dashboard.tsx
    DomainFoundation.tsx
    AIDraft.tsx
    SystemStatus.tsx
```

The frontend is currently an operator and verification surface, not a finished product UI.

### Scripts

```text
Start-JarvisOS.cmd
Start-JarvisOS-Backend.cmd
Start-JarvisOS-Frontend.cmd
scripts/start-backend.ps1
scripts/start-frontend.ps1
scripts/start-dev.ps1
scripts/init-database.ps1
```

Startup is Windows-first and works through PowerShell/.cmd wrappers.

## 3. What Is Solid

These items should be kept, not redesigned.

| Item | Status | Severity | Assessment |
| --- | --- | --- | --- |
| Local-first data root separation | keep | low | Repository path and runtime data root are cleanly separated. |
| FastAPI module layout | keep | low | Module boundaries exist and are understandable. |
| Explicit DB bootstrap | keep | medium | Initialization is visible and idempotent. |
| BlueRev default workspace seed | keep | low | Useful for local workflow and manually validated. |
| AI Gateway rule | keep | high | Real provider calls are not scattered through routes/frontend. |
| Safe fake AI provider | keep | medium | Tests and local use can run without external calls. |
| Scaleway smoke gates | keep | high | Live calls require explicit settings, key, privacy, and token gates. |
| AI Smoke Console narrowness | keep | medium | It remains a smoke surface, not chat. |
| Runner explicit execution split | keep | high | Creating a job does not execute code. |
| Runner subprocess boundary | keep | high | `local_python.py` is the only subprocess wrapper. |
| Runner manual API validation | keep | medium | The batch-growth API path has been manually exercised successfully. |

## 4. What Is Fragile

These items should be hardened before adding major features.

| Item | Status | Severity | Assessment |
| --- | --- | --- | --- |
| Schema evolution | harden | high | The schema has grown past the comfort zone for ad hoc `CREATE TABLE IF NOT EXISTS` plus targeted `ALTER TABLE`. |
| Existing local DB state | harden | high | A local data root can retain live AI settings from prior sessions, which may surprise operators even if budget gates still block. |
| Artifact access | harden | high | Artifacts are recorded but not first-class enough for future runner/UI workflows. |
| Event model | harden | medium | Events are shallow JSON payloads without central redaction/schema discipline. |
| Runner service size | refactor later | high | One service file handles too many responsibilities for future model kinds. |
| AI smoke module duplication | refactor later | medium | Smoke tests and console duplicate gate/event/accounting patterns. |
| Provider abstraction | harden | high | The interface is not ready for OpenAI, Anthropic, DeepSeek, or model capability routing. |
| Frontend API client size | refactor later | medium | API types and calls are accumulating in one file. |
| Frontend page size | refactor later | medium | `AIDraft.tsx` is already too large for more workflow UI. |
| Migration to PostgreSQL | postpone | high | Still possible, but every unversioned schema change raises migration cost. |

## 5. Data Infrastructure Assessment

### Current State

The current SQLite schema is adequate for a local proof foundation. `SimulationRun` is correctly treated as the canonical run record. `runner_jobs` stores orchestration metadata and links one-to-one to `simulation_runs`. `run_logs` and `run_artifacts` are focused and small.

The schema still avoids advanced relational complexity. That has been useful, but the next feature set will put pressure on the data layer.

### Problems

| Problem | Severity | Status | Detail |
| --- | --- | --- | --- |
| No schema version table | high | harden | There is no durable record of which schema version a DB is on. |
| Ad hoc migrations | high | harden | Only AI settings has targeted `ALTER TABLE` migrations; runner tables rely on initialization statements. |
| No migration tests for older DB snapshots | high | harden | Tests create fresh temp DBs. They do not prove upgrades from previous local DB shapes. |
| Artifact API is incomplete | high | harden | Generated artifacts can be stored, but there is no focused read/list/download API for run artifacts. |
| Absolute path storage unresolved | medium | harden | `stored_path` is absolute today. That is convenient locally but awkward for portability/backups. |
| Event payload schema is informal | medium | harden | Events are useful, but event types do not have typed payload contracts. |
| AI settings retains operational state | medium | harden | Local DB state persists toggles and token counters across sessions. This is expected but needs clearer operator reset/status tooling. |
| No indexes beyond primary/unique keys | medium | harden | Lists are small today; run/event/artifact queries will need indexes before scale. |

### Recommendations

For 0E-B, do not jump straight to a full enterprise migration system. Do add enough structure to stop drift:

1. Add a `schema_migrations` or `schema_version` table.
2. Assign named migration IDs for all schema changes so far.
3. Make initialization call migrations in order.
4. Add migration tests from minimal old DB shapes.
5. Add explicit read APIs for artifacts and run artifacts.
6. Decide whether stored artifact paths are absolute or data-root-relative.
7. Add indexes for common workspace-scoped lists.
8. Add an operator-safe AI settings reset path or at least a documented safe-local reset procedure.

Do not add PostgreSQL yet. Keep PostgreSQL compatibility in mind, but harden SQLite first.

## 6. Runner Assessment

### Current State

Python Runner V0 is correctly scoped:

- reviewed deterministic script only;
- queued job creation;
- explicit synchronous execution endpoint;
- no shell invocation;
- no inherited secret environment;
- timeout;
- bounded logs/output/artifacts;
- script hash recording;
- path checks;
- lifecycle events;
- manual API validation passed.

### Problems

| Problem | Severity | Status | Detail |
| --- | --- | --- | --- |
| `service.py` is too broad for expansion | high | refactor later | It handles model implementation creation, job lifecycle, execution orchestration, log capture, output parsing, and artifact registration. |
| No worker/job abstraction | medium | postpone | Synchronous execution is acceptable for V0, but future cancellation/background execution will require a separate design. |
| No hostile-code sandbox | high | postpone | This is documented and acceptable now. Do not run unreviewed scripts. |
| No dependency/runtime manifest | medium | harden | The runner records command/env metadata, but not a robust Python/package environment manifest. |
| Artifact API missing | high | harden | Runner artifacts are DB-linked but not easy to retrieve through API. |
| ModelImplementation is overloaded onto `model_versions` | medium | harden | Adequate for V0; future multiple-file implementations may need a dedicated table. |

### Split Before More Model Kinds

Before adding a second model kind, split the runner into:

- `implementation_service.py`: reviewed script registration and model implementation records;
- `job_service.py`: job creation and SimulationRun lifecycle;
- `execution_service.py`: execution orchestration and status transitions;
- `artifact_service.py`: run artifact validation/registration;
- keep `local_python.py` as the only subprocess module;
- keep `safety.py` as shared V0 policy utilities.

Do not add AI-generated code execution. If AI-generated code is ever considered, it needs a separate design gate, explicit user approval, and stronger isolation than this V0 runner provides.

## 7. AI Infrastructure Assessment

### Current State

The AI system has good safety posture for its current scope:

- fake provider by default;
- monthly budget defaults to zero;
- paid AI disabled by default;
- Scaleway requires explicit mode and smoke flags;
- API key comes from environment, not SQLite;
- privacy policy blocks secret, sensitive IP, confidential, and unknown classes where required;
- token counters and caps exist;
- tests mock live providers.

### Problems

| Problem | Severity | Status | Detail |
| --- | --- | --- | --- |
| Provider interface is too modeling-draft-specific | high | harden | `AIProvider.generate` is shaped around modeling drafts, while Scaleway smoke calls use separate methods. |
| No provider registry | high | harden | Adding OpenAI/Anthropic/DeepSeek directly now would create branching and duplication. |
| No model registry/capability map | high | harden | There is no durable place to express model capabilities, context windows, cost rules, privacy limits, or task suitability. |
| Token/cost accounting is Scaleway-specific | high | harden | Multi-provider accounting needs provider-neutral usage records. |
| Gate logic is duplicated | medium | refactor later | Smoke tests and smoke console repeat provider/budget/privacy/token event patterns. |
| Spend accounting is incomplete | medium | harden | Token counters update; USD spend is not realistically estimated for live Scaleway calls. |
| Local DB can persist live settings | high | harden | Safe defaults exist for fresh DBs, but existing local settings can remain live-enabled from manual validation. |

### Required Direction Before New Providers

0E-C should design:

- provider registry;
- model registry;
- provider adapter interface for chat/completions and structured tasks;
- per-provider API key environment mapping;
- provider-neutral usage accounting;
- provider/model capability metadata;
- task routing policy;
- shared budget/privacy/token gate;
- mocked provider tests;
- explicit rule that routes/frontend never call provider modules.

Do not integrate OpenAI, Anthropic, DeepSeek, Mistral, or other providers until that design is accepted.

## 8. Security And Privacy Assessment

### Current Controls

- API keys are read from environment variables.
- API keys are not stored in SQLite.
- Provider calls are behind the AI Gateway/smoke layers.
- Smoke Console does not store raw prompt text in events.
- Runner subprocess does not inherit the normal process environment.
- Runner preflight blocks obvious unsafe script markers.
- Runner paths are constrained to data-root workspace paths.
- `.gitignore` excludes `.env`, DB files, venv, node modules, caches, and logs.

### Gaps

| Gap | Severity | Status | Detail |
| --- | --- | --- | --- |
| No authentication | later | postpone | Acceptable for local-only use. Blocking if remote/LAN exposure appears. |
| No centralized redaction utility | high | harden | Each module avoids secrets manually; this should become shared policy. |
| Event payloads are free-form | medium | harden | A future mistake could log sensitive content without schema review. |
| Absolute paths in API responses | medium | harden | Useful locally, but leaks local usernames/paths if remote access is ever added. |
| Runner is not a sandbox | high | postpone | Reviewed scripts only. Do not relax this. |
| Live AI state can persist | high | harden | Operator should be able to see and reset live-capable AI settings clearly. |
| No network isolation for runner | high | postpone | Preflight blocks obvious imports but cannot guarantee no network. |

## 9. Testing Assessment

### Current Coverage

Backend test coverage is meaningful for the current milestones:

- health/system endpoints;
- domain creation/list flows;
- AI gateway fake provider;
- AI smoke tests and live-call guards with mocked providers;
- AI Smoke Console guard behavior and token counter;
- Python Runner success/failure/timeout/path/log/artifact behavior.

Known recent results before this docs-only review:

- focused runner tests: 29 passed;
- full backend tests: 85 passed;
- backend compile check: passed.

### Gaps

| Gap | Severity | Status | Detail |
| --- | --- | --- | --- |
| No migration-from-old-DB tests | high | harden | Fresh temp DB tests are not enough now. |
| No frontend test stack | medium | postpone | Build checks exist, but no UI behavior tests. |
| No manual validation script | medium | harden | Manual runner validation was done but not captured as a repeatable script. |
| No provider contract tests | high | harden | Needed before multiple AI providers. |
| No redaction regression suite | high | harden | Required before real analysis workflows or more providers. |
| No artifact retrieval tests | medium | harden | Artifact API does not exist yet. |

### Minimum Next Test Investments

For 0E-B:

- migration tests from prior schema snapshots;
- artifact list/read endpoint tests;
- event payload redaction tests;
- DB bootstrap idempotence tests against non-empty DB;
- safe reset/status tests for AI settings if added.

For 0E-C:

- provider registry unit tests;
- provider adapter contract tests;
- no-network tests for automated suite;
- cost/token normalization tests.

## 10. UX And Operator Assessment

The current UI should remain an operator surface.

### What Works

- System Status shows backend, storage, DB, and AI status.
- Domain Foundation can initialize storage and create basic records.
- AI Draft page exposes settings, smoke tests, and Smoke Console.
- Windows launchers reduce startup friction.

### Problems

| Problem | Severity | Status | Detail |
| --- | --- | --- | --- |
| AI settings UI is powerful for its maturity | medium | harden | It can persist live-capable state; operator reset/status wording should improve before broader AI. |
| No runner UI | low | postpone | Acceptable now. Do not add it before data/artifact hardening. |
| AIDraft page is too large | medium | refactor later | Split before adding more AI workflows. |
| API client is too large | medium | refactor later | Split by domain before adding runner UI or provider management. |
| DB initialization can surprise | medium | harden | `/health` can be OK while DB is uninitialized; `/system/info` shows the truth, but launch scripts should keep this obvious. |

## 11. Documentation Assessment

### Good Enough

- README states repository/data-root separation.
- README documents safe defaults and missing features.
- Architecture docs explain AI Gateway, runner, data root, and local-first assumptions.
- ADRs record the major decisions through 0D-B.
- UI start guide is practical for Windows.
- Runner design honestly says V0 is not a hostile-code sandbox.

### Needs Work

| Issue | Severity | Status | Detail |
| --- | --- | --- | --- |
| Docs are milestone-accumulative | medium | harden | README is becoming a historical log. It needs a current-state quickstart plus archived milestone detail. |
| Runner design includes postponed endpoints | low | harden | Design text references artifacts/cancel concepts not implemented in V0. It is mostly clear, but should be annotated before UI work. |
| No operator reset guide | medium | harden | Need a safe guide for resetting local DB/AI settings without deleting source. |
| No manual validation runbook | medium | harden | The 0D-B manual API smoke exercise should become repeatable documentation or a script. |

## 12. Technical Debt List

| Debt | Severity | Status | Owner Area |
| --- | --- | --- | --- |
| Add schema migration/version tracking | high | harden | data |
| Add migration tests from old DB shapes | high | harden | data/tests |
| Add artifact list/read APIs | high | harden | data/runner |
| Decide absolute vs data-root-relative artifact paths | medium | harden | data/files |
| Add event payload conventions and redaction helpers | high | harden | events/security |
| Split runner service before adding more model kinds | high | refactor later | runner |
| Add environment/runtime manifest for runner jobs | medium | harden | runner |
| Add provider/model registry design | high | harden | AI |
| Normalize provider-neutral token/cost usage records | high | harden | AI/data |
| Split AI smoke gate/accounting primitives | medium | refactor later | AI |
| Split frontend API client by domain | medium | refactor later | frontend |
| Split AI page into smaller panels | medium | refactor later | frontend |
| Add safe local reset/operator runbook | medium | harden | docs/scripts |
| Add frontend build verification to regular workflow | low | harden | frontend/tests |
| Add auth only if non-local access appears | later | postpone | security |

## 13. Risk Ranking

1. **high / harden** - Schema evolution without migration/version tracking.
2. **high / harden** - Existing local DB can retain live-capable AI settings across sessions.
3. **high / harden** - Artifact records are not queryable enough for runner/UI workflows.
4. **high / harden** - Provider abstraction is not ready for multi-provider integrations.
5. **high / postpone** - Python Runner is not a sandbox and cannot run arbitrary or AI-generated code.
6. **high / harden** - No centralized redaction policy for events/API payloads.
7. **high / refactor later** - Runner service will become a monolith if another model kind is added directly.
8. **medium / harden** - Event payloads are useful but too informal for audit/compliance.
9. **medium / refactor later** - AI smoke code duplicates gate/accounting concepts.
10. **medium / refactor later** - Frontend AI page and API client are at the edge of temporary maintainability.
11. **medium / harden** - Startup/operator state can be confusing when DB is uninitialized or retains prior settings.
12. **medium / harden** - Absolute path exposure is acceptable locally but risky for any remote/LAN mode.
13. **medium / harden** - No repeatable manual validation runbook/script for runner smoke.
14. **low / keep** - Windows launchers are sufficient for now but are not packaging.
15. **later / postpone** - Authentication is intentionally absent, but becomes mandatory before non-local use.

## 14. Recommended Hardening Roadmap

### 0E-B Data Infrastructure Hardening

Goal: make SQLite evolution, artifacts, events, and operator state reliable enough for the next feature layer.

Scope:

- add schema version/migration table;
- name and apply migrations in order;
- add migration tests from previous schema snapshots;
- add artifact list/read APIs, especially run artifacts;
- decide path storage convention;
- add indexes for workspace-scoped lists;
- add event redaction helper and typed event payload guidelines;
- add local DB/AI settings reset documentation or safe endpoint/script;
- document current DB state management clearly.

Do not add BlueRev models.

### 0E-C AI Provider Abstraction Design

Goal: design the provider layer before adding OpenAI, Anthropic, DeepSeek, or more Scaleway workflows.

Scope:

- provider registry design;
- model registry design;
- provider capability model;
- provider-neutral usage/cost model;
- task routing policy;
- key environment naming conventions;
- shared gate pipeline;
- provider contract tests;
- no-network automated test policy.

Do not integrate new providers in this milestone.

### 0E-D Multi-provider AI Integration

Goal: implement one provider at a time only after 0E-C is accepted.

Scope:

- add provider adapter behind the registry;
- add mocked tests first;
- require same privacy/budget/token gates;
- add provider-specific cost/token normalization;
- keep UI minimal and operator-oriented.

Do not add broad AI analysis workflows yet.

### 0E-E AI Analysis Workflow Gate

Goal: decide what AI-assisted analysis can safely do after provider abstraction exists.

Scope:

- define allowed analysis tasks;
- define what content classes can be sent externally;
- define storage/redaction rules;
- define how outputs become draft records, not automatic truth;
- define manual approval before any runner/code execution.

Do not execute AI-generated code.

### Later BlueRev Modeling

BlueRev-specific modeling should wait until:

- data migration/versioning is stable;
- artifacts are queryable;
- runner boundaries are split for more model kinds;
- provider registry exists;
- privacy/redaction policy is centralized;
- operator reset/status story is clear.

## 15. Explicit Non-goals For The Next Phase

For 0E-B and 0E-C, do not add:

- BlueRev-specific scientific models;
- runner UI;
- general Python execution;
- notebook execution;
- AI-generated code execution;
- Scientific Data Connectors;
- CAD, geometry, CFD, FEM;
- agents or MCP;
- R&D Debate Mode;
- new provider integrations before provider abstraction design;
- generalized chat;
- file upload/parsing;
- Electron or installer packaging;
- authentication unless local-only assumptions change.

## 16. Proposed Next Milestones

### 0E-B Data Infrastructure Hardening

Recommended next milestone.

Acceptance criteria:

- schema version/migration table exists;
- initialization applies migrations safely;
- tests prove old DB shapes upgrade;
- artifact list/read APIs exist for workspace and run artifacts;
- events have redaction helper/guidelines;
- docs explain reset/bootstrap/state clearly;
- no BlueRev modeling is added.

### 0E-C AI Provider Abstraction Design

Design-only milestone after 0E-B.

Acceptance criteria:

- provider registry design documented;
- model capability registry documented;
- provider-neutral usage/cost model documented;
- privacy/budget/token gate reuse documented;
- tests required for provider adapters are specified.

### 0E-D Multi-provider AI Integration

Implementation milestone after 0E-C.

Acceptance criteria:

- one new provider adapter only;
- mocked tests prove no network by default;
- no direct provider calls from routes/frontend;
- usage accounting works through the provider-neutral layer.

### 0E-E AI Analysis Workflow Gate

Design gate before any serious AI-assisted analysis.

Acceptance criteria:

- allowed tasks defined;
- redaction/storage policy defined;
- manual approval boundaries defined;
- no automatic runner/code execution.

### Later BlueRev Modeling

Postpone until infrastructure hardening is complete.

Acceptance criteria before starting:

- data migrations are stable;
- artifact APIs are usable;
- runner service is split enough for multiple model kinds;
- AI provider abstraction is real;
- privacy policy is centralized and tested;
- operator UI clearly shows runtime state and reset options.

