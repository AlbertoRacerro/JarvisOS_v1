# JarvisOS Runbooks

These runbooks are for the local Windows-first developer build. They do not make JarvisOS a hosted service, installer, or production system.

## Recreate Backend Virtual Environment

Use this after generated cleanup removes `backend/.venv`.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
```

Run backend tests after recreating the environment:

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Recreate Frontend Dependencies

Use this after generated cleanup removes `frontend/node_modules`.

```powershell
cd frontend
npm install
```

Run the frontend build after dependencies are installed:

```powershell
npm run build
```

Node.js LTS and npm are required for normal frontend use.

## Bootstrap And Status Check

From the repository root:

```powershell
.\scripts\init-database.ps1
```

This initializes SQLite and seeds the default BlueRev workspace if needed. The default data root is:

```text
C:\JarvisOS
```

Start the backend:

```powershell
.\scripts\start-backend.ps1
```

Check health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Check system status:

```powershell
Invoke-RestMethod http://localhost:8000/system/info
```

If the database is not initialized, call:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/system/initialize
```

Expected storage fields after initialization:

- `database.initialized = true`
- `database.ready = true`
- `database.bootstrap_required = false`

## Start Local UI

From File Explorer, double-click:

```text
Start-JarvisOS.cmd
```

Or start services separately:

```text
Start-JarvisOS-Backend.cmd
Start-JarvisOS-Frontend.cmd
```

Open:

```text
http://localhost:5173
```

Detailed UI startup notes live in `docs/UI_START.md`.

## Scaleway API Key Entry

Use this only for narrow Scaleway smoke-test paths. Do not paste secrets into chat, docs, logs, smoke prompts, model fields, or Python runner inputs.

### UI Flow

1. Start backend and frontend.
2. Open `http://localhost:5173`.
3. Go to the AI Draft page.
4. Paste the key into `Scaleway API Key`.
5. Click `Save Key`.
6. Confirm `Key present = true`.

The app-entered key is stored only in backend runtime memory for the current backend process. It is forgotten after backend restart. The raw key is not stored in SQLite AI settings and is not returned by the API.

### Delete The App-Entered Key

From the AI Draft page, click `Delete Saved Key`. This clears only the runtime-memory key. If `SCALEWAY_API_KEY` is set in the backend environment, status still reports `source = env`.

### PowerShell Fallback

Set the key before starting the backend:

```powershell
$env:SCALEWAY_API_KEY = "..."
.\scripts\start-backend.ps1
```

Source priority:

1. `SCALEWAY_API_KEY` environment variable.
2. App-entered runtime-memory key.
3. Missing key.

## Python Runner V0 Batch-Growth Validation

This validates the architecture path for Python Runner V0. It is not scientific BlueRev validation.

Warnings:

- Run only the reviewed deterministic `batch_growth_v0` script.
- Do not paste secrets, API keys, `.env` content, BlueRev proprietary content, or arbitrary scripts.
- Python Runner V0 is not a hostile-code sandbox.

### 1. Create A Model Spec

```powershell
$modelSpec = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/workspaces/bluerev/model-specs" `
  -ContentType "application/json" `
  -Body (@{
    title = "Manual API smoke - batch growth V0"
    engineering_question = "Can the reviewed deterministic batch-growth runner execute through the backend API?"
    scope = "Manual architecture smoke exercise."
  } | ConvertTo-Json)
```

### 2. Register Reviewed Model Implementation

```powershell
$implementation = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/workspaces/bluerev/model-implementations" `
  -ContentType "application/json" `
  -Body (@{
    model_spec_id = $modelSpec.id
    version_label = "manual-smoke-batch-growth-v0"
    implementation_kind = "batch_growth_v0"
    notes = "Manual runner validation."
  } | ConvertTo-Json)
```

### 3. Create A Queued Runner Job

```powershell
$job = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/workspaces/bluerev/runner-jobs" `
  -ContentType "application/json" `
  -Body (@{
    model_version_id = $implementation.id
    run_label = "manual-api-smoke-batch-growth"
    timeout_seconds = 10
    input_set = @{
      schema_version = 1
      parameters = @{
        mu_max = 0.6
        X0 = 0.15
        t_final = 24
        dt = 1
      }
      input_artifact_ids = @()
    }
  } | ConvertTo-Json -Depth 8)
```

Expected:

- `runner_job.status = queued`
- `simulation_run.status = queued`
- no model execution until the explicit run call

### 4. Execute Explicitly

```powershell
$run = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/runner-jobs/$($job.runner_job.id)/run"
```

Expected:

- `runner_job.status = succeeded`
- `simulation_run.status = succeeded`
- `output.outputs.point_count = 25`
- `output.outputs.final_biomass_concentration = 269111.2158909318`

### 5. Read Back Run, Logs, And Artifacts

```powershell
$detail = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)"
$logs = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)/logs"
$artifacts = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)/artifacts"
```

Expected log:

```text
Batch growth completed with 25 points.
```

Expected artifact metadata:

- one CSV artifact;
- `filename = timeseries.csv`;
- `under_data_root = true`;
- path under `C:\JarvisOS`.

### 6. Negative Check

`dt = 0` should fail before execution with HTTP `400` and code `runner_input_invalid`.

## Local Evaluation Report Retention

Raw local Gemma evaluation reports are evidence artifacts.

Current rule:

- Keep raw D9, D9R, D10B, D10B-R, and D10C reports until their conclusions are preserved in `docs/LOCAL_AI_EVALUATION_EVIDENCE.md` and `docs/DECISIONS.md`.
- Do not paste large JSON reports into docs.
- Do not delete D10B, D10B-R, or D10C evidence during documentation cleanup.
- Zero-byte stderr files may be removed only in a later cleanup milestone after confirming they contain no unique diagnostic information.
