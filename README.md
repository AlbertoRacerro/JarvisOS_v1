# JarvisOS

JarvisOS is a local-first AI co-engineering foundation for building engineering model capital. The first product focus is BlueRev Model Foundry: a small, technical workspace for progressively turning engineering questions, assumptions, models, runs, files, and decisions into traceable assets.

Milestones 0A and 0B create the architecture spine and first persistent domain foundation. The codebase is intentionally feature-thin, migration-friendly, and Windows-first.

## What Milestone 0A Includes

- FastAPI backend skeleton.
- React + Vite + TypeScript frontend shell.
- SQLite-ready backend structure.
- Central configuration and path layers.
- Windows-first data root concept at `C:\JarvisOS`.
- Placeholder boundaries for workspaces, engineering, files/artifacts, events, AI providers, tools, and agents.
- Basic `/health` and `/system/info` endpoints.
- PowerShell startup scripts.
- Initial architecture documentation and ADRs.
- Minimal backend tests.

## What Milestone 0B Adds

- SQLite-backed tables for Workspace, Entity, EntityLink, Event, Artifact, ModelSpec, Assumption, Parameter, ModelVersion, SimulationRun, and Decision.
- Migration-friendly metadata such as stable IDs, timestamps, status fields, schema version fields, notes, and raw payload fields where useful.
- Minimal create/list APIs for Workspaces, ModelSpecs, Assumptions, Parameters, SimulationRuns, and Decisions.
- Basic event logging for important object creation.
- Idempotent default BlueRev workspace initialization.
- A simple, temporary Domain Foundation frontend page for creating and viewing the first records.

## What Milestone 0C Adds

Milestone 0C-A added the safe fake-provider AI Gateway foundation. Milestone 0C-B added the Scaleway EU smoke-test guard layer. Milestone 0C-C adds a minimal live Scaleway EU smoke call behind explicit controls. Milestone 0C-D adds a narrow AI Smoke Console for short harmless manual provider checks through the same guarded path.

- A minimal AI Gateway service for structured AI Co-Engineering requests.
- A deterministic fake provider used by default for no-cost development and tests.
- Database-backed AI settings with default monthly API budget set to `0 USD`.
- Budget/status controls in the frontend AI Draft page.
- A structured modeling draft endpoint at `POST /ai/modeling/draft`.
- Event logging for AI draft requests, completions, failures, and blocked real-provider attempts.
- Scaleway status fields and key detection without storing raw secrets in SQLite.
- A Scaleway EU smoke-test boundary with synthetic no-network mode and an explicitly enabled live smoke-call mode.
- A small AI Smoke Console endpoint and UI panel for short harmless live Scaleway smoke prompts only.
- A local `PrivacyPolicyEngine` for synthetic smoke-test classification and routing decisions.
- A conservative token guard with month-to-date input/output counters and caps.
- A synthetic smoke-test endpoint at `POST /ai/smoke-tests/run`.

## What Milestone 0E-B1 Adds

- A narrow backend secret boundary at `app/modules/secrets`.
- UI entry for the Scaleway API key on the AI Draft page.
- Runtime-memory app key storage for the current backend process.
- Environment variable priority: `SCALEWAY_API_KEY` still wins over an app-entered key.
- Secret metadata endpoints that return only presence, source, safe masked preview, and update time.
- Metadata-only secret events; raw keys are not written to events, logs, docs, snapshots, SQLite AI settings, or frontend storage.

## What Milestone 0D Adds

Milestone 0D-A added the Python Runner design gate. Milestone 0D-B adds the first minimal local Python Runner V0.

- A reviewed deterministic batch-growth Python script.
- `model_versions` used as the first ModelImplementation record.
- Explicit queued runner jobs linked one-to-one with `SimulationRun`.
- Synchronous local execution only after the user calls the run endpoint.
- Bounded stdout/stderr logs.
- Script SHA-256 recording and validation.
- Minimal command and environment metadata without inherited secrets.
- Run artifacts registered through the existing artifact table.
- Runner lifecycle events.

## What It Does Not Include

- General Python execution platform.
- Notebook execution.
- AI-generated code execution.
- General real-provider workflows outside the guarded Scaleway smoke-test paths.
- General chat, conversation history, RAG, memory, agents, multi-agent orchestration, or arbitrary system prompts.
- Advanced Modeling Studio workflows.
- Authentication.
- Electron or desktop packaging.
- Telegram, Slack, voice, CRM, email, CAD, CFD, FEM, or other integrations.
- Complex database schema.
- Full Modeling Studio workflows.
- File upload or advanced file parsing.

## Repository Layout

```text
backend/    FastAPI application and backend tests
frontend/   React + Vite + TypeScript app
scripts/    Windows PowerShell startup scripts
docs/       Architecture notes and decision records
```

The repository can live anywhere. Runtime data is a separate concept and is designed to live under `C:\JarvisOS` by default. Do not put assumptions about the repository path into backend storage code.

## Start The Local UI

On Windows, double-click this file from File Explorer:

```text
Start-JarvisOS.cmd
```

It starts the backend and frontend in separate command windows and opens the browser to:

```text
http://localhost:5173
```

Separate launchers are also available:

```text
Start-JarvisOS-Backend.cmd
Start-JarvisOS-Frontend.cmd
```

The `.cmd` launchers are convenience wrappers around the existing PowerShell scripts. See `docs/UI_START.md` for the short operator guide.

## Backend

Prerequisites:

- Python 3.11 or newer.

From PowerShell:

```powershell
.\scripts\start-backend.ps1
```

The script creates `backend\.venv` if needed, installs `backend\requirements.txt`, and starts FastAPI at:

```text
http://127.0.0.1:8000
```

Useful endpoints:

- `GET /health`
- `GET /system/info`
- `POST /system/initialize`
- `GET/POST /workspaces`
- `GET/POST /workspaces/{workspace_id}/model-specs`
- `GET/POST /workspaces/{workspace_id}/assumptions`
- `GET/POST /workspaces/{workspace_id}/parameters`
- `GET/POST /workspaces/{workspace_id}/simulation-runs`
- `GET/POST /workspaces/{workspace_id}/decisions`
- `GET /ai/settings`
- `PUT /ai/settings`
- `GET /ai/status`
- `GET /secrets/scaleway/status`
- `POST /secrets/scaleway/api-key`
- `DELETE /secrets/scaleway/api-key`
- `POST /ai/modeling/draft`
- `POST /ai/smoke-tests/run`
- `POST /ai/smoke-console/run`
- `GET/POST /workspaces/{workspace_id}/model-implementations`
- `POST /workspaces/{workspace_id}/runner-jobs`
- `POST /runner-jobs/{runner_job_id}/run`
- `GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}`
- `GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/logs`
- `GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/artifacts`

`start-backend.ps1` runs database initialization before starting the server.

Repeatable local validation steps live in `docs/RUNBOOKS.md`.

## Frontend

Prerequisites:

- Node.js LTS and npm.

If Node.js or npm is missing, the Windows launchers show a clear message and stop. Install Node.js LTS from the official website:

```text
https://nodejs.org/
```

Then reopen File Explorer or a fresh terminal and start JarvisOS again. The project does not download Node.js, run installers, or modify system PATH automatically.

From a second PowerShell window:

```powershell
.\scripts\start-frontend.ps1
```

The frontend starts at:

```text
http://127.0.0.1:5173
```

The frontend expects the backend at `http://127.0.0.1:8000`. Override with `VITE_API_BASE_URL` if needed.

When the frontend script starts, it opens `http://localhost:5173` in the browser after a short delay.

During Milestone 0A review, Codex verified the frontend build with its bundled Node runtime because global `node` and `npm` were not on this machine's PowerShell `PATH`. Normal project use still expects a standard Node.js installation with npm available globally.

## Start Both

```powershell
.\scripts\start-dev.ps1
```

This starts backend and frontend jobs in the same PowerShell session and streams their output.

## Initialize Database

To initialize SQLite and seed the default BlueRev workspace without starting the server:

```powershell
.\scripts\init-database.ps1
```

Initialization creates the configured data root, creates the SQLite tables if needed, and inserts the default workspace with id `bluerev` only if it does not already exist. The Domain Foundation page also has an explicit `Initialize Storage` control for local development, but backend startup scripts remain the normal initialization path.

## Tests

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

## Data Root

JarvisOS is Windows-first and local-first. The default data root is:

```text
C:\JarvisOS
```

The backend centralizes data-root-derived paths in `backend/app/core/paths.py`. Do not scatter filesystem paths across modules, and do not confuse the Git repository folder with the runtime data root. Override the data root during development with:

```powershell
$env:JARVISOS_DATA_ROOT = "D:\JarvisOS"
```

## Configuration

Basic configuration lives in `backend/app/core/config.py`.

Initial environment variables:

- `JARVISOS_APP_NAME`
- `JARVISOS_APP_VERSION`
- `JARVISOS_ENV`
- `JARVISOS_DATA_ROOT`
- `JARVISOS_AI_PROVIDER`
- `SCALEWAY_API_KEY`
- `SCALEWAY_BASE_URL`
- `SCALEWAY_MODEL`

AI settings such as monthly budget and provider mode are stored in SQLite. API keys are not stored in SQLite. A Scaleway key can come from `SCALEWAY_API_KEY` or from the AI Draft page's runtime-memory key entry. The environment variable takes priority.

## AI Gateway And Budget Guard

JarvisOS AI is a technical co-engineering assistant, not a generic chatbot. Milestone 0C implements a structured modeling draft flow plus narrow smoke-test controls:

```text
informal engineering idea -> AI Gateway -> structured modeling draft
```

The default budget is:

```text
0 USD
```

By default:

- provider mode is `fake`;
- paid AI is disabled;
- monthly API budget is `0`;
- spend month-to-date is `0`;
- external paid calls are not allowed;
- the fake provider returns deterministic structured drafts.

No paid API calls happen by default. Tests use the fake provider only.

The AI Draft page lets you view and update budget settings. Paid AI still remains blocked unless all guard conditions are satisfied: paid AI enabled, real provider selected, API key configured in the environment, monthly budget above zero, and token/budget caps available.

### Scaleway EU Smoke-Test Layer

Milestone 0C-B added a safe Scaleway EU smoke-test layer. Milestone 0C-C adds the first minimal live Scaleway smoke call through the AI Gateway provider layer.

Safe defaults:

- `provider_mode = fake`
- `paid_ai_enabled = false`
- `monthly_api_budget_usd = 0`
- `scaleway_enabled = false`
- `scaleway_smoke_test_enabled = false`
- `scaleway_live_smoke_test_enabled = false`
- `scaleway_monthly_token_cap = 500000`
- `scaleway_hard_stop_token_cap = 800000`
- `scaleway_free_tier_reference_tokens = 1000000`
- `scaleway_input_tokens_month_to_date = 0`
- `scaleway_output_tokens_month_to_date = 0`

No external call may be attempted unless paid AI is enabled, provider mode is explicitly set to `scaleway`, Scaleway smoke tests are enabled, live Scaleway smoke calls are enabled, a Scaleway API key is present, budget guards pass, local privacy policy allows the synthetic request, token caps pass, and the user explicitly runs the live smoke test.

Preferred local UI flow:

1. Open the AI Draft page.
2. Paste the key only into `Scaleway API Key`.
3. Click `Save Key`.
4. Confirm `Key present = true`.

This key is held in backend runtime memory only and is forgotten when the backend process restarts. It is never shown again and is not stored in frontend `localStorage`, `sessionStorage`, SQLite AI settings, events, or docs.

Environment fallback:

```powershell
$env:SCALEWAY_API_KEY = "..."
```

If both are set, `SCALEWAY_API_KEY` wins over the app-entered runtime key. Use `Delete Saved Key` in the AI Draft page to clear only the app-entered runtime key.

Optional environment variables:

```powershell
$env:SCALEWAY_BASE_URL = "..."
$env:SCALEWAY_MODEL = "..."
```

For the 0E-D4 strong-provider smoke path, DeepSeek is configured by environment only:

```powershell
$env:DEEPSEEK_API_KEY = "..."
```

Optional overrides:

```powershell
$env:DEEPSEEK_BASE_URL = "..."
$env:DEEPSEEK_MODEL = "..."
```

JarvisOS does not provide a DeepSeek key UI yet and does not store this key in SQLite, runtime-memory secret storage, localStorage, or sessionStorage.

The raw key is never returned by the API. Secret status returns only `key_present`, `source`, `last_updated_at`, and a safe masked preview such as `sk-...abcd`. The smoke tests use synthetic examples only: public research, generic engineering note, proprietary Smart Joint geometry, fake `.env`/password text, and ambiguous BlueRev brainstorming. Do not use real BlueRev secrets, proprietary geometry, or sensitive project material in smoke tests.

The local policy classes are `public`, `internal`, `confidential`, `sensitive_ip`, `secret`, and `unknown`. Providers may recommend a class in future milestones, but JarvisOS enforces the routing decision locally.

Live smoke mode for the fixed synthetic suite sends only the harmless public/internal synthetic cases. Secret, `sensitive_ip`, confidential BlueRev brainstorming, and unknown synthetic cases remain blocked there so the harness can prove local gates. Automated tests mock the Scaleway provider and never call the network.

Manual live smoke checklist:

1. Start the backend and frontend.
2. In AI Draft, enter the Scaleway API key or set `SCALEWAY_API_KEY` before backend startup.
3. Optionally set `SCALEWAY_BASE_URL`; default is `https://api.scaleway.ai/v1`.
4. Optionally set `SCALEWAY_MODEL`; default is `llama-3.1-8b-instruct`.
5. In AI Draft settings, set provider mode to `scaleway`.
6. Enable paid AI, Scaleway mode, Scaleway smoke tests, and live Scaleway smoke call.
7. Keep the monthly budget and token caps low.
8. Run `Run Live Scaleway Smoke Test`.

### AI Smoke Console

Milestone 0C-D adds a small manual AI Smoke Console near the AI Cost Guard. In the default `FAST_DEV` policy mode, it is for short public/internal provider checks, such as:

```text
ciao
come va?
say hello in one sentence
reply with a short harmless greeting
summarize this public batch-growth equation in one sentence
```

It is not general chat and does not store conversation history. Do not paste API keys, Authorization headers, `.env` content, private keys, real credentials, proprietary BlueRev IP, or sensitive private strategy.

The console endpoint is:

```text
POST /ai/smoke-console/run
```

The console sends a live Scaleway request only when all existing gates pass: paid AI enabled, provider mode set to `scaleway`, Scaleway smoke tests enabled, live Scaleway smoke calls enabled, a Scaleway API key is present from the environment or runtime-memory app entry, policy mode allows the prompt, and token caps allow the request. Automated tests mock the provider and do not call the network.

`FAST_DEV` allows normal public/internal technical prompts and avoids broad keyword blocking for terms such as BlueRev, geometry, patent, modeling, or architecture. It still blocks structural secret patterns such as API key fields, `.env` references, `Authorization: Bearer ...`, private keys, and explicit token/password assignments. Future `STRICT_IP` mode can become stricter when real proprietary IP enters the system.

The prompt limit is 500 characters and the output limit is 80 tokens. The UI displays the existing monthly Scaleway input/output counters, the configured monthly Scaleway cap, and a fixed smoke-console display threshold of `500000` total tokens. Live calls may spend tokens, even for tiny prompts.

### Strong Provider Smoke Path

Milestone 0E-D4 adds one additional strong provider: DeepSeek.

Endpoint:

```text
POST /ai/provider-smoke/run
```

This path is backend/API-only for now. It requires `provider_mode = deepseek`, paid AI enabled, a positive monthly budget, `DEEPSEEK_API_KEY` in the backend environment, `FAST_DEV` policy approval, and small prompt/output limits. It is for short public/internal technical checks only, such as mass-balance explanations or toy equation review.

It is not routing, not Supervisor AI, not chat, and not BlueRev modeling. Usage is returned in the response and event, but provider-neutral monthly usage persistence is still future work.

### Narrow Supervisor AI Public Test

Milestone 0E-D5 adds the first backend-only Supervisor AI slice:

```text
POST /ai/supervisor/public-test
```

It accepts bounded public/internal technical prompts, such as reviewing a toy equation or explaining a generic runner error. It does not accept provider or model selection from the request. Provider choice is temporary and internal: DeepSeek is used when `provider_mode = deepseek` and configured; Scaleway is fallback only when explicitly configured for live smoke.

This endpoint is not chat, not a provider router, not source-grounded literature mode, not file upload/parsing, not runner execution, and not BlueRev proprietary modeling. Events store prompt length and usage metadata, not raw prompts or raw keys.

## Python Runner V0

Milestone 0D-B adds a minimal local runner for one reviewed deterministic batch-growth script. It is not a hostile-code sandbox and it is not a general Python execution platform. Only reviewed scripts should be run.

V0 safety boundaries:

- local execution only;
- explicit queued job creation followed by an explicit synchronous run call;
- no `shell=True`;
- no inherited API keys or secrets in the subprocess environment;
- controlled working directory under the JarvisOS data root;
- explicit `input.json` and output directory;
- timeout;
- bounded stdout/stderr capture;
- bounded result JSON and artifact sizes;
- script SHA-256 recorded and checked;
- obvious network/subprocess/destructive-file and `.env`/secret-access markers blocked by preflight;
- no automatic execution from AI responses.

The first deterministic example accepts:

```json
{
  "parameters": {
    "mu_max": 0.4,
    "X0": 0.05,
    "t_final": 24,
    "dt": 0.5
  }
}
```

Manual API flow:

1. Create or reuse a model spec.
2. `POST /workspaces/bluerev/model-implementations` with the model spec id and `implementation_kind = "batch_growth_v0"`.
3. `POST /workspaces/bluerev/runner-jobs` with the model implementation id and input parameters.
4. `POST /runner-jobs/{runner_job_id}/run`.
5. Read `GET /workspaces/bluerev/simulation-runs/{simulation_run_id}` and `/logs`.

### External Providers

DeepSeek is implemented only as the 0E-D4 narrow strong-provider smoke path. OpenAI, Mistral, Claude, and other real providers are not implemented. Future provider support must use safe credential handling, stay behind the AI Gateway/provider-neutral adapter interface, and pass the same budget, token, policy, and redaction guards before any external call.

## SQLite Database

The SQLite database is stored at:

```text
C:\JarvisOS\jarvisos.db
```

No Alembic migration setup is included yet. Milestone 0B uses a simple idempotent initialization function because the schema is still intentionally small. Future milestones should introduce formal migrations when schema changes become more frequent or when PostgreSQL migration work begins.

Milestone 0E-B adds a lightweight `schema_migrations` table so the current SQLite schema version is visible in `/system/info` and future lightweight migrations have an explicit ledger.

## Frontend Scope

The Domain Foundation page is a temporary thin verification surface, not the Modeling Studio. It intentionally uses simple forms, local component state, and direct API calls. It should be split into smaller components once workflows become more substantial.
