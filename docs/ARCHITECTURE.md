# Architecture

Milestone 0A establishes the JarvisOS architecture spine. Milestone 0B adds the first persistent domain foundation. The goal is still intentionally small: clear module boundaries, local-first runtime assumptions, and minimal records that future modeling workflows can build on.

## Architecture Spine

The backend is the durable system boundary. It owns configuration, paths, database access, module boundaries, and API routes. The frontend is a thin local operator interface that reads backend health and system status.

Initial backend layers:

- `app/core`: configuration, paths, database readiness, logging, and shared errors.
- `app/api`: HTTP entry points.
- `app/modules`: future feature modules with small boundaries.
- `app/schemas`: shared response and payload shapes.

The first mounted API surface is deliberately small:

- `/health`
- `/system/info`
- `/system/initialize`
- `/workspaces`
- `/workspaces/{workspace_id}/model-specs`
- `/workspaces/{workspace_id}/assumptions`
- `/workspaces/{workspace_id}/parameters`
- `/workspaces/{workspace_id}/simulation-runs`
- `/workspaces/{workspace_id}/decisions`
- `/ai/settings`
- `/ai/status`
- `/secrets/scaleway/status`
- `/secrets/scaleway/api-key`
- `/ai/modeling/draft`
- `/ai/smoke-tests/run`
- `/ai/smoke-console/run`
- `/ai/provider-smoke/run`
- `/ai/supervisor/public-test`
- `/workspaces/{workspace_id}/model-implementations`
- `/workspaces/{workspace_id}/runner-jobs`
- `/runner-jobs/{runner_job_id}/run`
- `/workspaces/{workspace_id}/simulation-runs/{simulation_run_id}`
- `/workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/logs`

## Module Boundaries

The milestone creates placeholders for the modules JarvisOS will need without implementing their full behavior.

### Workspaces

Workspaces will organize BlueRev and future engineering contexts. Milestone 0A only defines the boundary.

Milestone 0B stores workspaces in SQLite and seeds a default `bluerev` workspace during explicit initialization.

### Engineering

Engineering entities will eventually include model specifications, assumptions, parameters, versions, runs, decisions, and validation records. Milestone 0A avoids a premature schema.

Milestone 0B introduces minimal tables for those early objects, with status, timestamps, schema version, notes, and raw payload fields where useful. This is not yet the full Modeling Studio.

### Events

Events are part of the long-term bookkeeping layer. The initial service only defines a small event record shape so later milestones have a clear place to add persistence.

Milestone 0B persists creation events such as `WorkspaceCreated`, `ModelSpecCreated`, `AssumptionCreated`, `ParameterCreated`, `SimulationRunCreated`, and `DecisionCreated`. This is not event sourcing.

### Files and Artifacts

The Artifact Registry exists because engineering work produces datasets, documents, model outputs, reports, and generated files. Milestone 0A does not parse or analyze files.

Milestone 0B adds a record-only artifact table and internal service. It does not upload, copy, parse, or analyze files yet.

### AI Gateway

AI Gateway is mandatory even before real providers exist. It prevents provider-specific calls from leaking into feature modules and preserves future routing across OpenAI, Gemini, local models, and other providers.

Milestone 0C turns this boundary into a minimal guarded service. All AI draft requests pass through `app/modules/ai/gateway.py`. Routes and modeling services do not call providers directly.

The fake provider is mandatory and is the default. It produces deterministic structured modeling drafts without API keys or external calls.

Real provider modes are budget/key/token guarded. Scaleway live smoke calls are implemented only for fixed synthetic smoke tests and the narrow AI Smoke Console, and only after explicit live-smoke enablement.

Milestone 0C-B adds a Scaleway EU smoke-test boundary inside `app/modules/ai/providers/scaleway.py`. Milestone 0C-C adds a minimal live Scaleway chat-completions smoke call inside that provider layer. Routes and frontend code still talk only to the AI Gateway/API layer.

The fixed smoke-test mechanism lives in `app/modules/ai/smoke_tests.py`. It uses fixed synthetic cases and records `AISmokeTestStarted`, `AISmokeTestCompleted`, and `AISmokeTestBlocked` events. It has two modes: synthetic no-network mode and live Scaleway smoke mode. It must not be fed real BlueRev secrets or sensitive project data.

The manual smoke-console mechanism lives in `app/modules/ai/smoke_console.py`. It caps prompts at 500 characters, caps output at 80 tokens, preserves budget/provider/token/key gates, and records `AISmokeConsoleStarted`, `AISmokeConsoleCompleted`, and `AISmokeConsoleBlocked` events without storing raw prompt text. In the default `FAST_DEV` policy mode, it allows normal public/internal technical prompts and blocks only structural secret or prompt-evasion patterns. It is not chat, RAG, memory, an agent, or a BlueRev modeling assistant.

`app/modules/ai/privacy.py` contains a small local `PrivacyPolicyEngine`. Fixed synthetic smoke tests still exercise `public`, `internal`, `confidential`, `sensitive_ip`, `secret`, and `unknown` classes. Manual smoke-console prompts use the current AI policy mode: `FAST_DEV` avoids broad technical-content blocking, while `STRICT_IP` is reserved for future stricter behavior. Providers may recommend classifications in the future, but JarvisOS enforces routing locally.

`app/modules/ai/token_guard.py` contains conservative token estimation and cap checks. It tracks estimated input/output tokens, reported usage from live Scaleway smoke calls when available, month-to-date input/output counters, the monthly smoke-test cap, and a hard stop cap.

Milestone 0E-D1 adds provider-neutral AI contracts in `app/modules/ai/contracts.py`. These define future-facing request, response, usage, provider, model, routing, gate, authority, and registry types. They do not add a new provider or change current user-facing behavior.

Milestone 0E-D2 migrates the existing live Scaleway smoke path behind `app/modules/ai/providers/scaleway_adapter.py`. The adapter conforms to the provider-neutral `AIProviderAdapter` contract and statically exposes the configured Scaleway smoke model through the new model registry shape. It wraps the existing `scaleway.py` HTTP boundary; it does not add another provider, dynamic model discovery, routing policy, Supervisor AI, or new frontend controls.

Milestone 0E-D3 adds a pragmatic AI policy mode foundation. The default `policy_mode` is `FAST_DEV`, which allows ordinary public/internal technical prompts while preserving credential redaction, no plaintext key storage, provider metadata allowlisting, budget gates, token gates, provider-mode gates, and no-network automated tests. `STRICT_IP` is retained as a future stricter mode, not the default blocker for early development.

Milestone 0E-D4 adds exactly one additional strong provider: DeepSeek through `app/modules/ai/providers/deepseek.py` and `app/modules/ai/providers/deepseek_adapter.py`. It is env-var-only through `DEEPSEEK_API_KEY` and is exposed only through the narrow `POST /ai/provider-smoke/run` path. This is not routing, Supervisor AI, general chat, or BlueRev modeling.

Milestone 0E-D5 adds the first narrow Supervisor AI endpoint at `POST /ai/supervisor/public-test`. It is backend-only, accepts public/internal non-sensitive technical prompts, runs only in `FAST_DEV`, and returns a structured response with provider-neutral usage. Provider choice is temporary and internal: DeepSeek is preferred when `provider_mode = deepseek` and configured; Scaleway is fallback only when explicitly configured for live smoke. This is not full chat, provider routing, file processing, runner execution, or BlueRev modeling.

Milestone 0E-D6 is a docs-only architecture review for the future three-tier Supervisor AI model. JarvisOS should evolve toward one user-facing Supervisor backed by logical `cheap`, `medium`, and `frontier` tiers, with provider/model details kept internal or admin/config-only. The current `provider_mode` field remains a compatibility control for existing smoke paths, but future Supervisor routing should use tier assignments and auditable route plans instead of provider-specific bot choices.

Milestone 0E-D6B corrects the D6 ordering: the first decision layer must be a local gatekeeper, not an external provider tier. Raw user input must be inspected by deterministic local hard rules and, later, an optional local Gemma classifier before any cloud provider is considered. Logical gates such as `LOCAL_ONLY`, `LOCAL_GEMMA`, `USER_CONFIRM_REQUIRED`, `CHEAP_GATE`, `CHEAP_PLUS_GATE`, `SCIENTIFIC_MEDIUM_GATE`, `FRONTIER_GATE`, and `BLOCKED` come before concrete provider adapters.

Milestone 0E-D6C adds a docs-only local AI foundation review before implementing local gate contracts. The next proof point is not whether Gemma can choose an external provider; it is whether local Gemma can use JarvisOS context, memory, deterministic tools, structured outputs, and evaluation correctly. The recommended next milestone is a local Gemma evaluation harness and golden set, not Gemma runtime, local gate runtime, provider routing, or external API expansion.

Milestone 0E-D7 adds that local Gemma evaluation foundation without adding Gemma runtime. The `app/modules/local_ai_eval` module defines a 65-case golden set, a strict future `GemmaEvalOutput` schema, fixture validation, and deterministic scoring helpers for category matches, required/forbidden strings, TODO/decision coverage, missing-context flags, tool-result grounding, schema validity, and critical safety failures. It does not call local models, provider APIs, Ollama, llama.cpp, LiteLLM, or frontend code.

Milestone 0E-D7B extends the same harness for the future local operating-brain role. The golden set now includes 95 cases and checks whether Gemma can request bounded context packages, handle partial context, distinguish stale docs from canonical decisions, select safe tool packages, refuse to answer when context is missing, and prepare external prompts without executing external calls. The schema now includes state, context sufficiency, requested context packages, bounded tool requests, and external-call intent fields. It still does not add Gemma runtime, model-server integration, routing, UI, memory runtime, file ingestion, or provider calls.

Milestone 0E-D7C hardens the harness before runtime by tightening fixture validation and false-pass detection. Context-request cases require reasons, forbidden tool requests must be explicitly marked, premature external prompts/calls are critical failures, missing context cannot produce final answers, invalid prose/JSON-like output cannot be accepted as scoreable success, and duplicate/invalid golden cases are rejected. It remains offline and deterministic.

Milestone 0E-D8 adds a bounded local Gemma runtime adapter dry run. It supports only explicitly configured localhost OpenAI-compatible endpoints, defaults to the local Ollama-compatible endpoint shape, uses no API keys, and feeds local output into the D7/D7B/D7C schema and scorer. It has no FastAPI route, no frontend, no chat, no memory runtime, no file/database retrieval, no context broker runtime, no local gate enforcement, no autonomous tools, no provider routing, and no external API calls.

### Secrets

Milestone 0E-B1 adds a narrow local secret boundary in `app/modules/secrets` for the Scaleway API key. It is not a general secrets manager.

V0 storage is runtime memory only. The app-entered key is usable until the backend process exits, then it must be entered again. This avoids silently storing plaintext API keys in SQLite or local files and postpones Windows Credential Manager or DPAPI-backed persistence to a separate design step.

Scaleway key resolution order is:

1. `SCALEWAY_API_KEY` environment variable.
2. App-entered runtime-memory key.
3. Missing key.

Secret endpoints return only metadata: key presence, source, safe masked preview, update time, and storage mode. Raw keys must not be returned to the frontend, written to events, stored in AI settings, or logged.

### Tool Registry

Tool Registry exists before broader executable capabilities are added through one extension point. The Python Runner V0 is implemented as a narrow local runner module rather than a general tool system.

### Python Runner

Milestone 0D-B adds the first minimal local Python Runner V0. It is designed for reviewed deterministic scripts, not arbitrary code execution.

The runner boundary lives in `app/modules/runner`:

- `models.py`: request and response schemas.
- `routes.py`: thin HTTP endpoints.
- `service.py`: job creation, lifecycle transitions, SimulationRun integration, event logging, and artifact registration.
- `safety.py`: V0 path, input, script, timeout, output, and artifact guardrails.
- `local_python.py`: the only subprocess boundary.

The runner reuses existing domain objects:

- `model_versions` is the V0 ModelImplementation record.
- `simulation_runs` is the authoritative run record and status owner.
- `artifacts` stores script and generated file records.
- `events` stores runner lifecycle events.

New runner tables are deliberately small:

- `runner_jobs` stores operational metadata and one-to-one links to `simulation_runs`.
- `run_logs` stores bounded stdout/stderr.
- `run_artifacts` links run records to generated artifacts.

The V0 executor is synchronous and explicit. Creating a runner job does not execute it. Execution starts only through `POST /runner-jobs/{runner_job_id}/run`.

V0 safety is a guardrail, not a hostile-code sandbox. It uses local execution only, no shell invocation, a minimal non-secret environment, controlled data-root working directories, explicit input/output files, timeout, bounded logs/output/artifact sizes, script SHA-256 checks, and simple preflight blocks for obvious network/subprocess/destructive-file and `.env`/secret-access markers.

For V0, `service.py` intentionally centralizes orchestration, lifecycle transitions, and artifact registration. If the runner grows beyond reviewed deterministic scripts, split it into smaller lifecycle, artifact, and execution orchestration services before adding broader workflows.

### Agent Registry

Agent Registry exists before agents so future AI roles or assistants have a boundary. Milestone 0A does not implement agent behavior.

## Local-First Storage

JarvisOS assumes a Windows-first local data root:

```text
C:\JarvisOS
```

All filesystem paths are centralized in `app/core/paths.py`. Large artifacts should eventually live in managed filesystem storage, while structured truth lives in the database.

The Git repository location and the runtime data root are separate concepts. The repository contains source code; the data root contains local JarvisOS runtime state, databases, logs, workspaces, and artifacts.

## Database Direction

SQLite is the initial database because it fits local-first development. The data layer is intentionally small and should be evolved in a way that keeps a future PostgreSQL migration possible. Milestone 0A reports whether the database path is configured and whether its parent directory currently exists; it does not create a schema.

Milestone 0B creates the schema through an idempotent initialization function, exposed by `scripts/init-database.ps1` and `POST /system/initialize`. The frontend exposes initialization as an explicit local-development action rather than doing it silently. Alembic is intentionally postponed until the schema starts changing often enough to justify migration tooling.

## Domain Foundation

The first persistent objects are:

- Workspace
- Entity
- EntityLink
- Event
- Artifact
- ModelSpec
- Assumption
- Parameter
- ModelVersion
- SimulationRun
- RunnerJob
- RunLog
- RunArtifact
- Decision
- AISettings

These tables are deliberately minimal. Early rough records should be stored without pretending that every field is already final or fully validated.

## Why Feature-Thin

This milestone is not trying to prove the whole product. It creates the rails for later modeling, execution, AI assistance, event logging, and artifacts without building fake complexity. The correct outcome is architecture-strong, feature-thin, and migration-friendly.

Milestone 0B proves persistence and simple APIs. It still excludes the Python Runner, real AI calls, agents, advanced file parsing, authentication, and full Modeling Studio workflows.

The Domain Foundation page is temporary and intentionally thin. It is allowed to be a single straightforward page for this milestone, but it should be split when real workflows begin to appear.

## AI Co-Engineering Draft Flow

Milestone 0C adds a structured draft endpoint:

```text
POST /ai/modeling/draft
```

The response contains:

- engineering question;
- model title suggestion;
- model scope;
- assumptions;
- parameters;
- expected inputs and outputs;
- missing information;
- weaknesses;
- next step;
- AI metadata.

This is not chat. There is no streaming, chat history, tool execution, agent loop, Python execution, or automatic saving of AI output.

## AI Budget Guard

The AI settings table defaults to:

- `monthly_api_budget_usd = 0`
- `api_spend_month_to_date_usd = 0`
- `paid_ai_enabled = false`
- `provider_mode = fake`
- `policy_mode = FAST_DEV`
- `use_fake_provider_when_budget_zero = true`

External paid calls are blocked unless the user explicitly changes settings and a future real provider implementation passes all guard checks. Missing API keys, zero budget, exhausted budget, disabled paid AI, and token-cap problems return structured blocked responses instead of stack traces.

## Scaleway Smoke-Test Guard

Scaleway was the first real-provider smoke candidate. The current implementation proves that the gateway, settings, privacy rules, token cap, and event logging can safely control a narrow EU-hosted live smoke call. It is not the local privacy classifier, local gatekeeper, or core Supervisor router.

Default Scaleway settings are disabled and conservative:

- `scaleway_enabled = false`
- `scaleway_smoke_test_enabled = false`
- `scaleway_live_smoke_test_enabled = false`
- `scaleway_monthly_token_cap = 500000`
- `scaleway_hard_stop_token_cap = 800000`
- `scaleway_free_tier_reference_tokens = 1000000`
- `scaleway_input_tokens_month_to_date = 0`
- `scaleway_output_tokens_month_to_date = 0`

The monthly cap remains below the free-tier reference during smoke testing. The live Scaleway smoke implementation updates reported token counters from provider usage metadata when available, falling back to conservative estimates when usage metadata is missing.

Older `scaleway_token_cap` and `scaleway_tokens_month_to_date` SQLite columns are retained only as dormant legacy storage from the first 0C-A/0C-B pass. They are not exposed by the API and are not used by the active token guard. The active fields are `scaleway_monthly_token_cap`, `scaleway_hard_stop_token_cap`, `scaleway_input_tokens_month_to_date`, and `scaleway_output_tokens_month_to_date`.

Live Scaleway smoke calls require this order:

```text
provider mode and paid/budget/settings gates
-> local privacy policy
-> token guard
-> Scaleway provider module
-> usage counter update
```

In `FAST_DEV`, public/internal technical smoke-console prompts can reach the live provider only after paid/budget/settings/key/token gates pass. Structural secrets such as API key fields, `.env` references, `Authorization: Bearer ...`, private keys, and explicit token/password assignments are blocked locally. Fixed synthetic smoke tests still include strict synthetic secret/IP/confidential cases to validate the safety harness. Events record provider, model, mode, policy mode, privacy class, blocked reason, attempted/succeeded flags, token usage, and timestamps, but not API keys or raw prompt/secret content.

The AI Smoke Console displays the same month-to-date Scaleway counters used by the token guard plus a fixed `500000` token smoke-console display threshold. This threshold is an operator visibility threshold, not a separate counter.

## DeepSeek Provider Smoke Path

DeepSeek is the first non-Scaleway strong provider adapter. It is used only for narrow public/internal smoke checks in `FAST_DEV`.

Configuration:

- `DEEPSEEK_API_KEY` is required for live calls.
- `DEEPSEEK_BASE_URL` is optional and defaults to `https://api.deepseek.com/v1`.
- `DEEPSEEK_MODEL` is optional and defaults to `deepseek-chat`.

The DeepSeek path requires `provider_mode = deepseek`, paid AI enabled, a positive monthly budget, the environment key, local policy approval, and small prompt/output limits. It maps `AIRequest` to an OpenAI-compatible chat-completions request and maps usage back into `AIUsage`.

DeepSeek usage is returned in the smoke response and event but is not yet persisted into provider-neutral monthly usage tables. Do not add another provider before provider-neutral usage storage and audit envelopes are designed.

## Narrow Supervisor AI Slice

The first Supervisor AI endpoint is:

```text
POST /ai/supervisor/public-test
```

It accepts bounded public/internal technical prompts and optional task types such as equation review, assumption review, runner error explanation, simulation result interpretation, and code review. The request does not accept provider or model selection.

The endpoint records redacted lifecycle events:

- `AISupervisorPublicTestStarted`;
- `AISupervisorPublicTestProviderSelected`;
- `AISupervisorPublicTestProviderFailed`;
- `AISupervisorPublicTestCompleted`;
- `AISupervisorPublicTestBlocked`.

Events include policy mode, task type, provider/model ids, privacy class, blocked reason, external call attempted/succeeded flags, request/correlation ids, prompt length, and provider-neutral usage. They do not include the raw prompt, raw API keys, Authorization headers, or raw provider metadata.

The 0E-D6 review established provider-tier semantics. The 0E-D6B correction places a local gatekeeper before those external tiers:

```text
User input
-> LocalGatekeeper
   -> deterministic hard rules
   -> optional local Gemma classifier
-> GateDecision
   -> selected logical gate
   -> sensitivity
   -> complexity
   -> task type
-> external tier/provider adapter only if allowed
-> AIResponse
-> event/audit
```

Future AI events should record the gate decision before provider attempts: selected gate, sensitivity class, complexity class, hard-rule matches, confirmation requirement, external-call policy, and then concrete provider/model only if an external adapter is reached. Normal users should interact with one Supervisor interface; provider ids, model ids, tier assignments, fallback chains, and provider smoke diagnostics should remain admin/config-only.

The 0E-D6C correction adds one earlier proof step:

```text
User message
-> local task intake
-> deterministic hard checks
-> context packer
   -> conversation summary
   -> project state
   -> decisions
   -> artifacts and files metadata
   -> memory snippets
   -> constraints
-> local Gemma evaluation
-> structured local response
-> validation and failure diagnosis
```

Only after local Gemma passes a golden evaluation set should JarvisOS implement local gate runtime or external routing.
