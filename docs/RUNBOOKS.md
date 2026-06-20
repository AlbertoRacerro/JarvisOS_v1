# JarvisOS Runbooks

These runbooks are for the local Windows-first developer build. They do not make JarvisOS a hosted service, installer, or production system.

## Bootstrap And Status Check

From the repository root:

```powershell
.\scripts\init-database.ps1
```

This initializes the configured SQLite database and seeds the default BlueRev workspace if needed. The default data root is:

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

Expected storage fields after initialization:

- `database.initialized = true`
- `database.ready = true`
- `database.schema.current_migration_id = 0002_data_infrastructure_hardening`
- `database.bootstrap_required = false`

If the database is not initialized, call:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/system/initialize
```

## Scaleway API Key Entry

Use this only for the narrow Scaleway smoke-test paths. Do not paste secrets into chat, docs, logs, smoke prompts, model fields, or Python runner inputs.

### UI Flow

1. Start the backend and frontend.
2. Open:

```text
http://localhost:5173
```

3. Go to the AI Draft page.
4. Paste the key into `Scaleway API Key`.
5. Click `Save Key`.
6. Confirm `Key present = true`.

The app-entered key is stored only in backend runtime memory for the current backend process. It is forgotten after backend restart. The API returns only metadata:

- `key_present`;
- `source`;
- `masked_preview`;
- `last_updated_at`;
- `storage_mode`.

The raw key is not stored in SQLite AI settings and is not returned by the API.

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

Runtime-memory storage avoids silently writing plaintext secrets to disk. A future milestone can add a Windows Credential Manager or DPAPI-backed store after a separate design/review step.

## 0D-B Batch-Growth Manual Validation

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
- no run logs yet

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

The expected final biomass comes from:

```text
0.15 * exp(0.6 * 24)
```

### 5. Read Back Run, Logs, And Artifacts

```powershell
$detail = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)"
$logs = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)/logs"
$artifacts = Invoke-RestMethod "http://localhost:8000/workspaces/bluerev/simulation-runs/$($job.simulation_run.id)/artifacts"
```

Expected logs:

```text
Batch growth completed with 25 points.
```

Expected artifact metadata:

- one CSV artifact;
- `filename = timeseries.csv`;
- `under_data_root = true`;
- `size_bytes` is nonzero;
- path is under `C:\JarvisOS`.

### 6. Negative Check

`dt = 0` should fail before execution:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/workspaces/bluerev/runner-jobs" `
  -ContentType "application/json" `
  -Body (@{
    model_version_id = $implementation.id
    run_label = "manual-negative-dt-zero"
    timeout_seconds = 10
    input_set = @{
      schema_version = 1
      parameters = @{
        mu_max = 0.6
        X0 = 0.15
        t_final = 24
        dt = 0
      }
      input_artifact_ids = @()
    }
  } | ConvertTo-Json -Depth 8)
```

Expected HTTP status:

```text
400
```

Expected error:

```json
{
  "detail": {
    "code": "runner_input_invalid",
    "message": "dt must be greater than zero."
  }
}
```
