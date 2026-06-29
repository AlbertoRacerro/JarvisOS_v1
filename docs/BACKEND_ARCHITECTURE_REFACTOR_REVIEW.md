# Backend Architecture Refactor Review

Date: 2026-06-28

This review reverse-engineers the current JarvisOS backend architecture from
the canonical docs and source code, then defines behavior-preserving hardening
steps for modularity, scalability, and long-term maintainability.

## Scope

Inspected:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/nightly_upscale_review/*.md`
- `backend/app/core/`
- `backend/app/api/`
- `backend/app/modules/workspaces/`
- `backend/app/modules/modeling/`
- `backend/app/modules/files/`
- `backend/app/modules/runner/`
- `backend/app/modules/ai/`
- `backend/app/modules/secrets/`
- `backend/app/modules/events/`
- `backend/app/modules/dev_message_route/`
- representative backend and frontend tests/pages needed to understand API/UI pressure

Boundaries:

- Backend and documentation only.
- Frontend inspected for future API/UI architecture pressure; no frontend code
  should change in this slice.
- No behavior change.
- No routes/API added.
- No schema/migration added.
- No runtime memory, retrieval, provider routing, tool execution, MCP, browser,
  worker, or BlueRev modeling behavior added.

## Current Architecture

### System Spine

JarvisOS is a local-first FastAPI application with a React/Vite operator UI.
The backend owns durable state, policy gates, execution boundaries, audit
events, and provider access. The frontend is expected to call backend APIs only.

```text
frontend
-> FastAPI routes
-> feature services
-> SQLite/data root/providers/local runner
-> event/audit records
-> response DTOs
```

Core backend layers:

- `backend/app/main.py`: app construction, CORS, router registration.
- `backend/app/core/config.py`: environment-backed settings.
- `backend/app/core/paths.py`: data-root path construction.
- `backend/app/core/database.py`: SQLite connection setup, schema init, schema
  status.
- `backend/app/core/schema.py`: current SQL schema and manual migration
  statements.
- `backend/app/api/`: system, health, and dev-only API entry points.
- `backend/app/modules/`: feature modules.

### Startup And Storage Flow

```text
create_app()
-> get_settings()
-> configure_logging()
-> include routers

POST /system/initialize
-> initialize_storage()
-> initialize_database()
-> ensure_ai_settings()
-> seed_default_workspace()
```

SQLite is local-first and uses:

- `PRAGMA foreign_keys = ON`
- `PRAGMA busy_timeout = 5000`
- `PRAGMA journal_mode = WAL`

The schema is centralized but migration handling remains manual and local-first.

### Domain Data Flow

```text
POST /workspaces/{workspace_id}/model-specs
-> modeling.routes endpoint
-> modeling.service create function
-> open_sqlite_connection()
-> require workspace
-> INSERT domain record
-> log_event()
-> COMMIT
-> SELECT created row
-> Pydantic read model
```

The same basic pattern exists for workspaces, model specs, assumptions,
parameters, simulation runs, decisions, artifacts, and several runner records.

### AI Data Flow

```text
POST /ai/modeling/draft
-> AIGateway.create_modeling_draft()
-> get workspace
-> get AI settings
-> evaluate_ai_status()
-> fake provider or blocked response
-> log event
-> ModelingDraftResponse
```

Current external-provider behavior is intentionally narrow:

- Fake provider is the default.
- Scaleway and DeepSeek paths are smoke/diagnostic paths.
- Settings and status still include Scaleway-shaped fields.
- Provider calls require explicit gates.
- Broad routing, Supervisor AI, memory, retrieval, and BlueRev modeling are not
  approved runtime behavior.

### Dev Router/Local Chat Flow

```text
POST /api/dev/message-route-smoke or /api/dev/local-chat
-> env gate
-> request validation after disabled boundary
-> dev_message_route.smoke_adapter
-> scripts/router_policy_message_route_smoke.py
-> scripts/router_policy_local_route_probe.py
-> is_safe_local_execution(decision)
-> optional localhost responder only after safe-local authorization
```

The current backend import seam into `scripts/` is explicitly dev-only and must
not become a production integration pattern.

### Runner Flow

```text
create model implementation
-> copy reviewed deterministic script under data root
-> hash script
-> register artifact/model_version

create runner job
-> validate input
-> validate registered script hash
-> create simulation_run and runner_job

run runner job
-> atomically claim queued job
-> validate paths/hash/policy
-> execute Python with shell=False and minimal env
-> capture bounded logs
-> parse bounded result.json
-> register declared artifacts
-> update SimulationRun and RunnerJob
```

Runner V0 is acceptable for one reviewed deterministic script. It should not be
expanded by adding conditional branches for unrelated scripts.

### Future Frontend/UI Pressure

Current UI is a verification surface, not a production Workbench. Backend API
contracts will need to support a future UI system with:

- stable response envelopes;
- typed machine-readable error codes;
- paginated list/read endpoints;
- provider-neutral status and diagnostics;
- artifact metadata rather than raw path dependency;
- explicit audit and trace identifiers;
- generated frontend types or a stable OpenAPI contract.

Frontend component architecture should be planned around reusable, accessible
application primitives, but backend contract shape should be hardened first.

## Critical Problem Areas

### 1. Persistence Logic Is Repeated In Feature Services

Observed:

- `WorkspaceRead(**dict(row))`, `ModelSpecRead(**dict(row))`, and similar row
  projections were repeated across services.
- Workspace existence checks are repeated in modeling and runner.
- SQL, event logging, transaction boundaries, and response mapping are mixed in
  service functions.

Risk:

- Every new table duplicates the same persistence pattern.
- Later migration to repository boundaries or PostgreSQL becomes more expensive.
- Row-to-model behavior can drift between modules.

Current hardening:

- Added `backend/app/core/repository.py`.
- Applied shared row projection helpers to direct CRUD-style workspace,
  modeling, and file/artifact services.

### 2. Manual SQLite Migration Strategy Will Not Scale Far

Observed:

- `core/schema.py` stores table creation and manual `ALTER TABLE` statements.
- Duplicate-column errors are intentionally tolerated for compatibility.
- No old-database snapshot tests are currently enforcing upgrade behavior.

Risk:

- Future schema-heavy milestones can silently break existing local databases.
- Backfills, renames, and PostgreSQL readiness will be hard to reason about.

Strategy:

- Keep manual migrations for small local-first changes.
- Add old SQLite snapshot tests before the next schema-heavy milestone.
- Add formal migration tooling when fields are renamed/removed, backfills are
  required, or PostgreSQL compatibility starts.

### 3. AI Settings And Budget Logic Are Still Provider-shaped

Observed:

- `ai_settings` stores Scaleway-specific counters and caps.
- `evaluate_ai_status()` directly checks Scaleway and DeepSeek specifics.
- `ai/budget.py` imports `DeepSeekProvider` directly for status checks.

Risk:

- A second provider will duplicate flags, usage counters, and UI wording.
- Provider-neutral routing and audit will be difficult.

Strategy:

- Define provider-neutral status/settings concepts before adding a provider.
- Move usage accounting to provider-neutral records when real usage paths grow.
- Keep provider-specific compatibility fields until migration is safe.

### 4. Event Payloads Are Useful But Free-form

Observed:

- Event redaction is centralized and good.
- Event payload shapes are arbitrary dictionaries.
- AI, runner, and artifact events do not yet carry typed schema identifiers.

Risk:

- Audit screens and exports become unreliable as event types grow.
- It becomes hard to compare routing proposals, authority decisions, provider
  attempts, and final results.

Strategy:

- Add minimal typed audit payload helpers for gate, route, authority, provider
  attempt, usage, runner lifecycle, and artifact registration events.
- Keep redaction central and fail closed on sensitive keys.

### 5. Runner Service Is A Future Monolith

Observed:

- `runner/service.py` owns implementation registration, job creation, execution,
  log capture, artifact registration, event logging, and readback.

Risk:

- Adding a second script kind will produce branches around safety behavior.
- Queue/worker/cancellation concerns will be hard to isolate later.

Strategy:

- Freeze V0 to the reviewed deterministic script.
- Before the second script, add a manifest design and split responsibilities:
  registry, job repository, executor, artifact registrar, safety policy.

### 6. Artifact Identity Stores Absolute Paths

Observed:

- Artifact records persist `stored_path`.
- Runner readback derives safety from data-root checks at response time.

Risk:

- Data-root moves, backups, restore, and object-storage migration become brittle.
- Frontend artifact viewers may accidentally depend on raw filesystem paths.

Strategy:

- Add data-root-relative storage keys for new artifact writes.
- Derive absolute paths only inside backend storage services.
- Add artifact taxonomy and safe preview policy before artifact UI.

### 7. API Error Shapes Vary By Module

Observed:

- Modeling maps `ValueError`/`sqlite3.IntegrityError`.
- Runner returns `detail: {code, message}`.
- Frontend currently often sees `Request failed with <status>`.

Risk:

- UI cannot provide accessible, specific error states consistently.
- Future reusable UI components need stable error codes and safe messages.

Strategy:

- Introduce shared API error envelopes after current dev endpoint contracts
  stabilize.
- Preserve legacy response behavior where tests or UI depend on it.

### 8. UI-System Backend Contract Is Not Ready For Workbench

Observed:

- Frontend API client is a single mixed-domain file.
- AI page combines settings, secret entry, smoke tests, smoke console, token
  meter, and draft request.
- Domain Foundation is still a temporary verification page.

Risk:

- A production UI system cannot be cleanly joined to backend contracts if list
  endpoints, error envelopes, audit metadata, and entity shapes keep changing.

Strategy:

- Backend first: stable contracts, pagination, typed errors, trace IDs, and
  provider-neutral status.
- Frontend later: split API clients by domain, then build reusable form, table,
  status, alert, disclosure, dialog, and navigation primitives.

## Duplicate Logic

Confirmed duplication:

- Direct row-to-Pydantic conversion across services.
- Workspace existence checks.
- Creation patterns: timestamp, UUID, insert, event, commit, select.
- Route-level exception mapping.
- Provider/budget gate checks repeated across AI smoke paths.
- API fetch/error handling in frontend client.

Behavior-preserving first step:

- Shared repository row projection helper now removes the lowest-risk duplicate
  mapping pattern.

Do not centralize yet:

- Runner row mappers that compute derived artifact safety fields.
- AI provider gates until provider-neutral status/settings are designed.
- Dev route validation responses until current dev endpoint contracts finish.

## Performance Bottlenecks

Current bottlenecks are acceptable for V0 but should not be ignored:

- List endpoints have no pagination.
- Dashboard/workbench-style aggregate reads would require many small queries.
- `system_info()` opens several database reads and evaluates AI status each
  request.
- SQLite single-writer behavior is mitigated by WAL/busy timeout but not a
  queue/worker substitute.
- Runner execution is synchronous and blocks the request until completion.
- Event table can grow without retention/export policy.
- Frontend pages refresh multiple endpoint groups after writes.

Immediate action:

- No performance behavior changed in this slice.

Next backend actions:

- Add pagination before artifact/run/event lists become large.
- Add aggregate read models for dashboard/workbench screens rather than forcing
  the UI to fan out across many endpoints.
- Add event retention/export policy when event volume becomes measurable.

## Scalability Risks

High-risk scale-up points:

- Provider-specific `ai_settings` fields before provider-neutral contracts.
- Free-form event payloads before router/provider complexity.
- Absolute artifact paths before artifact viewer or backup/restore work.
- Synchronous runner execution before long-running jobs or cancellation.
- Manual migrations before schema-heavy Workbench or artifact/source features.
- Temporary frontend verification pages before production UI workflows.

Preferred scale-up posture:

```text
Design authority contracts first.
Then add narrow helpers.
Then refactor hot paths.
Then add product features.
```

## Maintainability Issues

Primary maintainability issues:

- Service functions mix orchestration, persistence, event writing, and DTO
  projection.
- Manual SQL is readable but has no repository boundary.
- Provider status/budget code is understandable but not provider-neutral.
- Frontend types are manually duplicated from backend Pydantic models.
- Historical docs are extensive; current-state docs must stay canonical and
  navigable.

## Production-grade Code Upgrade In This Slice

Added:

- `backend/app/core/repository.py`

The helper provides:

```text
row_to_model(row, model_type)
optional_row_to_model(row, model_type)
rows_to_models(rows, model_type)
```

Applied to:

- `backend/app/modules/workspaces/service.py`
- `backend/app/modules/modeling/service.py`
- `backend/app/modules/files/service.py`

Tested by:

- `backend/tests/test_data_infrastructure.py`

Why this is production-grade:

- It creates one reviewed projection seam for direct SQLite row to Pydantic
  response mapping.
- It reduces copy/paste in feature services without changing SQL, transactions,
  routes, schemas, or responses.
- It leaves complex custom mappers in place where they compute derived/safe
  fields.

## Refactoring Strategy

### Phase 1: Behavior-preserving Backend Hygiene

Target:

- Centralize repeated low-risk helpers.
- Keep feature services readable.
- Add tests for helper seams.

Candidate changes:

- Shared row projection helper. Complete for direct CRUD-style services.
- Shared workspace existence helper with module-specific error adapters.
- Shared route error envelope only after endpoint compatibility is clear.

### Phase 2: Repository Boundaries

Target:

```text
routes -> application service -> repository -> SQLite
                          -> event/audit helper
```

Rules:

- Repositories own SQL.
- Services own workflow and policy.
- Routes own HTTP status mapping only.
- Event helpers own typed audit payload shape and redaction.

Start with:

- workspaces repository;
- modeling repository;
- artifacts repository;
- runner job repository only before runner expansion.

### Phase 3: Provider-neutral AI Contracts

Target:

- provider-neutral settings/status read model;
- provider-neutral usage records;
- authority decision object;
- typed AI audit events;
- no direct route or UI provider calls.

Do not add:

- new provider;
- AI-assisted router;
- Supervisor endpoint;
- broad Gemma orchestration;
- BlueRev modeling.

### Phase 4: Artifact Storage Hardening

Target:

- data-root-relative storage keys;
- artifact taxonomy;
- immutable metadata;
- backend-controlled open/download endpoint;
- relocation tests.

### Phase 5: Runner V1 Gate

Target:

- script manifest;
- input/output schema per manifest;
- dependency policy;
- artifact registration policy alignment;
- runner service split.

### Phase 6: UI-system Backend Readiness

Backend contracts needed before frontend production UI:

- domain-specific API clients can be generated or hand-split cleanly;
- typed error envelope with safe message and machine code;
- pagination and sort/filter metadata for lists;
- trace/audit IDs in operations that need diagnostics;
- stable provider-neutral status model;
- artifact metadata model with no raw absolute path dependency;
- OpenAPI contract review after each route family change.

Frontend architecture later:

- `api/http` transport core;
- domain API modules;
- accessible form controls;
- reusable field validation surfaces;
- table/list primitives with empty/loading/error states;
- status chips and audit detail panels;
- modal/dialog/disclosure primitives;
- Workbench panels composed from domain primitives, not one large page.

## Suggested Roadmap

### ARCH-BE-1: Repository Helper Expansion

- Extend helper usage only where mapping is direct.
- Add workspace existence helper with error adapters.
- Keep behavior unchanged.

### ARCH-BE-2: Typed Audit Event Envelope

- Define minimal event payload schema names.
- Add tests for redaction and event shape.
- Apply first to AI and runner lifecycle events.

### AI-BE-1: Provider-neutral Status And Settings Design

- Separate provider-neutral status from Scaleway compatibility fields.
- Keep fake default.
- No new provider.

### AI-BE-2: AuthorityPolicy Design And Tests

- Define deterministic authority decision object.
- Prove router/provider proposal cannot authorize itself.
- Prove secrets/sensitive/unknown content blocks before external egress.

### ART-BE-1: Relative Artifact Storage Key

- Add backend-derived absolute path from relative key.
- Preserve legacy read compatibility.
- Add relocation/path traversal tests.

### DB-BE-1: Old SQLite Snapshot Tests

- Add representative old DB fixtures.
- Verify initialize/upgrade path.
- Add formal migration trigger rule to docs.

### RUN-BE-1: Runner Manifest Design Gate

- Do not add second script before manifest.
- Define input/output/artifact/dependency policy.

### UI-CONTRACT-1: API Contract Readiness

- Define typed errors, pagination, trace IDs, and generated type strategy.
- No frontend redesign required in this backend milestone.

## Deferred Items

- Frontend code/component split.
- UI visual redesign.
- New routes.
- New database schema.
- External provider addition.
- AI router implementation.
- Supervisor endpoint.
- Memory/retrieval runtime.
- Tool/MCP/browser/terminal execution.
- BlueRev modeling behavior.
