# 0D Python Runner Design Gate

## 1. Purpose

Milestone 0D introduces the design for a minimal local Python Runner that can execute controlled, deterministic modeling scripts and persist reproducible `SimulationRun` records.

The runner is for local engineering models, not arbitrary automation. The first implementation milestone, 0D-B, should support only:

- one approved local Python script;
- numeric/JSON input parameters;
- structured JSON output;
- optional generated run artifacts such as a plot image or CSV;
- a `SimulationRun` linked to a workspace and model implementation.

No runner execution behavior is implemented in 0D-A.

## 0D-B Implementation Note

0D-B implements the V0 slice described here:

- `app/modules/runner` module boundary;
- `runner_jobs`, `run_logs`, and `run_artifacts` tables;
- `model_versions` as ModelImplementation;
- explicit queued job creation;
- explicit synchronous local execution;
- reviewed deterministic `batch_growth_v0` script;
- bounded logs and output JSON;
- artifact registration through existing artifact records;
- script SHA-256 validation;
- minimal subprocess environment with no inherited secrets.

The implementation remains backend-only. No frontend runner panel is added in 0D-B.

## 2. Non-Goals

0D-A and the first 0D-B implementation must not add:

- arbitrary code execution;
- notebook execution;
- AI-generated code execution;
- automatic execution from an AI response;
- background workers or hidden daemons;
- Docker or cloud sandboxing;
- network-capable scientific connectors;
- CAD, CFD, geometry kernels, FEM, or feasibility screening;
- agents, MCP, RAG, memory, or chat workflows;
- file upload/parsing;
- a polished Modeling Studio UI.

## 3. Architecture

The runner should fit the existing module boundaries.

### Existing Boundaries To Reuse

- `app/modules/modeling`: owns model specs, model versions, simulation runs, and decisions.
- `app/modules/files`: owns artifact records.
- `app/modules/events`: owns structured event logging.
- `app/core/paths`: owns data-root-derived paths.
- `app/core/database`: owns SQLite initialization and migrations.

### New Boundary For 0D-B

Add a small runner module:

```text
backend/app/modules/runner/
  models.py
  routes.py
  service.py
  safety.py
  local_python.py
```

Responsibilities:

- `models.py`: request/response shapes for runner jobs, input sets, output sets, logs, and artifacts.
- `routes.py`: thin FastAPI endpoints only; no subprocess logic.
- `service.py`: job creation, lifecycle transitions, SimulationRun integration, event logging.
- `safety.py`: V0 policy checks for approved script metadata, paths, input size, output size, timeout, and blocked obvious risky imports/patterns.
- `local_python.py`: the only future module that may invoke a local Python subprocess. It must never be called by routes directly.

The runner module must not own model specs, raw artifact persistence, or event storage. It coordinates existing services.

## 4. Concept Mapping

Use existing objects where they already fit.

| Required concept | 0D-B mapping |
| --- | --- |
| `ModelImplementation` | Existing `model_versions` row. `model_versions.implementation_artifact_id` points to the script artifact. `version_label` is the implementation version. |
| `RunnerJob` | New `runner_jobs` row, one-to-one with a `simulation_runs` row. It stores operational execution metadata. |
| `InputSet` | JSON object stored in `simulation_runs.input_payload` and `simulation_runs.parameter_payload`. No separate table in 0D-B. |
| `OutputSet` | Structured JSON stored in `simulation_runs.output_payload`. No separate table in 0D-B. |
| `SimulationRun` | Existing `simulation_runs` table. This remains the canonical domain run record and status owner. |
| `RunArtifact` | Existing `artifacts` row plus a new `run_artifacts` join table. |
| `RunLog` | New bounded `run_logs` rows for stdout, stderr, and system messages. |
| `RunStatus` | `simulation_runs.status`, using `draft`, `queued`, `running`, `succeeded`, `failed`, `cancelled`, `timed_out`. |
| script hash/version | Script artifact `sha256` plus `model_versions.version_label`. |
| environment metadata | `runner_jobs.environment_json`, redacted and allow-listed. |

## 5. Data Model

Keep schema additions small and migration-friendly.

### Existing Tables

`model_specs` already represents the model definition.

`model_versions` should be used as the first `ModelImplementation` table. For 0D-B:

- `model_spec_id` links implementation to a model spec.
- `version_label` is the human-readable implementation version.
- `implementation_artifact_id` points to the approved Python script artifact.
- `changelog`/`notes` can describe the script version.

`simulation_runs` already has:

- `workspace_id`;
- `model_version_id`;
- `status`;
- `input_payload`;
- `parameter_payload`;
- `output_payload`;
- `started_at`;
- `completed_at`;
- `notes`.

0D-B should use these fields rather than creating duplicate run result tables.

### Proposed New Tables

#### `runner_jobs`

Operational envelope for one local runner attempt. `simulation_runs.status` remains canonical.

```text
id TEXT PRIMARY KEY
workspace_id TEXT NOT NULL
simulation_run_id TEXT NOT NULL UNIQUE
runner_type TEXT NOT NULL              -- python_local
requested_by TEXT NOT NULL             -- local-user
command_json TEXT                      -- redacted command metadata
environment_json TEXT                  -- redacted allow-listed environment metadata
working_dir TEXT NOT NULL
timeout_seconds INTEGER NOT NULL
max_stdout_bytes INTEGER NOT NULL
max_stderr_bytes INTEGER NOT NULL
max_output_json_bytes INTEGER NOT NULL
max_artifact_bytes INTEGER NOT NULL
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id)
```

No API keys, full process environment, or raw secret values may be stored.

#### `run_artifacts`

Join table between domain run and artifact records.

```text
id TEXT PRIMARY KEY
workspace_id TEXT NOT NULL
simulation_run_id TEXT NOT NULL
artifact_id TEXT NOT NULL
role TEXT NOT NULL                     -- result_json, plot, csv, log, other
created_at TEXT NOT NULL
notes TEXT
FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id)
FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
```

#### `run_logs`

Bounded log records for local execution.

```text
id TEXT PRIMARY KEY
workspace_id TEXT NOT NULL
simulation_run_id TEXT NOT NULL
stream TEXT NOT NULL                   -- stdout, stderr, system
content TEXT NOT NULL
truncated INTEGER NOT NULL DEFAULT 0
created_at TEXT NOT NULL
FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
FOREIGN KEY (simulation_run_id) REFERENCES simulation_runs(id)
```

### Status Vocabulary

Use only:

- `draft`;
- `queued`;
- `running`;
- `succeeded`;
- `failed`;
- `cancelled`;
- `timed_out`.

The existing `planned` status should remain readable for old records, but new runner-created records should use `queued` or `draft`.

## 6. API Design

Routes should be thin and should call runner service functions.

### Register A Model Implementation

0D-B may expose this only if needed for the first deterministic example.

```text
POST /workspaces/{workspace_id}/model-implementations
GET  /workspaces/{workspace_id}/model-implementations
```

Request:

```json
{
  "model_spec_id": "model-spec-id",
  "version_label": "batch-growth-v0",
  "implementation_artifact_id": "artifact-id",
  "notes": "Deterministic batch growth model."
}
```

Implementation detail: create a `model_versions` row. Do not create a separate `model_implementations` table in 0D-B.

### Create A Runner Job

```text
POST /workspaces/{workspace_id}/runner-jobs
```

Creates:

- a `simulation_runs` record with status `queued`;
- a `runner_jobs` record;
- a `RunnerJobCreated` event.

It must not execute the script.

Request:

```json
{
  "model_version_id": "model-version-id",
  "run_label": "batch growth smoke run",
  "input_set": {
    "schema_version": 1,
    "parameters": {
      "mu_max": 0.4,
      "X0": 0.05,
      "t_final": 24,
      "dt": 0.5
    },
    "input_artifact_ids": []
  },
  "timeout_seconds": 10
}
```

Response:

```json
{
  "runner_job_id": "job-id",
  "simulation_run_id": "run-id",
  "status": "queued"
}
```

### Explicitly Run A Queued Job

```text
POST /runner-jobs/{runner_job_id}/run
```

This is the explicit execution step. It should run synchronously in 0D-B and return after success, failure, timeout, or cancellation. There is no hidden background worker.

### Read Run State

```text
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/artifacts
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/logs
```

### Cancel

```text
POST /runner-jobs/{runner_job_id}/cancel
```

In 0D-B this may only support queued jobs or best-effort cancellation of the current synchronous process. If cancellation is not reliable in V0, return a clear `409` with `runner_cancel_not_supported_for_state`.

## 7. Runner Lifecycle

Lifecycle transitions:

```text
draft -> queued -> running -> succeeded
                       |       failed
                       |       timed_out
                       |       cancelled
```

Expected events:

- `RunnerJobCreated`;
- `RunnerJobStarted`;
- `RunnerJobSucceeded`;
- `RunnerJobFailed`;
- `RunnerJobTimedOut`;
- `RunnerJobCancelled`;
- `RunArtifactRegistered`;
- `RunLogCaptured`.

The `simulation_runs.status` field is the canonical run status. The runner service must update it in the same transaction as important lifecycle events when practical.

## 8. Input Representation

0D-B should accept JSON only.

Allowed values:

- numbers;
- strings for labels/units only where explicitly expected;
- booleans;
- arrays/objects;
- `null` only where explicitly allowed.

For the first BlueRev-safe example:

```json
{
  "schema_version": 1,
  "parameters": {
    "mu_max": 0.4,
    "X0": 0.05,
    "t_final": 24,
    "dt": 0.5
  },
  "input_artifact_ids": []
}
```

Validation requirements:

- reject payloads over a small limit, for example 64 KB;
- reject non-JSON;
- reject NaN/Infinity;
- reject path strings unless they reference explicitly registered input artifact IDs;
- reject missing required parameters for the selected implementation.

`input_payload` should store the full input set JSON. `parameter_payload` may store only the normalized parameter dictionary for list/table display.

## 9. Output Representation

The script must write a single structured JSON result file in the explicit output directory.

Recommended V0 filename:

```text
result.json
```

Recommended schema:

```json
{
  "schema_version": 1,
  "status": "succeeded",
  "outputs": {
    "final_biomass_concentration": 1.23
  },
  "series": [
    {"t": 0, "X": 0.05},
    {"t": 0.5, "X": 0.061}
  ],
  "artifacts": [
    {
      "path": "outputs/biomass_curve.png",
      "role": "plot",
      "artifact_type": "image",
      "mime_type": "image/png"
    }
  ],
  "warnings": []
}
```

The runner service should:

- enforce maximum `result.json` size;
- parse JSON strictly;
- record parsed JSON in `simulation_runs.output_payload`;
- register declared artifacts only if they are inside the explicit output folder;
- mark the run `failed` if result JSON is missing, malformed, too large, or references files outside the output folder.

## 10. Artifact Model

V0 run directory:

```text
C:\JarvisOS\workspaces\{workspace_id}\runs\{simulation_run_id}\
  input.json
  result.json
  logs\
  outputs\
```

Only the runner service may write inside this run directory.

Artifacts:

- must be created inside `outputs`;
- must be registered through `app/modules/files/service.py`;
- must have a SHA-256 hash recorded when possible;
- must have a `run_artifacts` join row;
- must not overwrite existing files outside the run directory;
- must not be written into the Git repository.

Existing `artifacts.source_ref` can store a readable pointer such as:

```text
simulation_run:{simulation_run_id}
```

The join table remains the queryable relationship.

## 11. Safety Model

The V0 runner is a local convenience execution boundary, not a hardened security sandbox.

Required controls:

- local execution only;
- no cloud execution;
- no hidden background execution;
- no shell invocation; use argument arrays;
- controlled working directory under data root;
- explicit output directory;
- explicit input JSON file;
- no inherited secrets in environment;
- minimal allow-listed environment variables;
- timeout with process termination;
- maximum stdout/stderr capture;
- maximum result JSON size;
- maximum artifact size;
- script SHA-256 recorded before execution;
- command metadata recorded with secrets redacted;
- environment metadata recorded with secrets redacted;
- errors captured as structured run output;
- no AI-generated code execution without explicit user approval;
- no automatic execution from AI draft/smoke-console responses;
- no silent modification/deletion of repo files.

V0 should also add a light preflight policy check for obvious dangerous patterns in the approved script:

- network imports such as `socket`, `requests`, `httpx`, `urllib`;
- child process imports such as `subprocess`;
- shell/process calls such as `os.system` and `os.popen`;
- destructive filesystem calls such as `shutil.rmtree`, `os.remove`, `os.unlink`, `Path.unlink`;
- `.env`, environment, and obvious secret-access markers;
- attempts to write outside the output directory.

This preflight is a guardrail, not a security guarantee. The 0D-B documentation and UI should say that only reviewed local scripts should be run.

## 12. Logging And Error Handling

Structured errors should be stable strings, for example:

- `runner_workspace_not_found`;
- `runner_model_version_not_found`;
- `runner_script_artifact_missing`;
- `runner_script_hash_mismatch`;
- `runner_input_invalid`;
- `runner_policy_blocked`;
- `runner_timeout`;
- `runner_result_missing`;
- `runner_result_invalid_json`;
- `runner_output_too_large`;
- `runner_artifact_path_outside_output_dir`;
- `runner_process_failed`.

Run failure response should include:

```json
{
  "status": "failed",
  "error": {
    "code": "runner_result_invalid_json",
    "message": "The runner did not produce valid result JSON."
  }
}
```

Log limits should be explicit. A reasonable V0 default:

- stdout: 64 KB;
- stderr: 64 KB;
- result JSON: 1 MB;
- individual artifact: 10 MB;
- timeout: 10 seconds for first example, configurable up to a conservative maximum such as 60 seconds.

## 13. SimulationRun Integration

`SimulationRun` remains the durable engineering record.

0D-B should:

- create a `SimulationRun` when a runner job is created;
- set `model_version_id`;
- store normalized input JSON in `input_payload`;
- store normalized parameters in `parameter_payload`;
- update `status` through the lifecycle;
- set `started_at` and `completed_at`;
- store parsed result JSON in `output_payload`;
- link artifacts through `run_artifacts`;
- log all lifecycle events.

Existing manually-created simulation runs should continue to work. Old `planned` runs should remain readable.

## 14. First Safe BlueRev Use Case

Use a deterministic batch growth model as the first example.

Parameters:

- `mu_max`;
- `X0`;
- `t_final`;
- `dt`.

Formula:

```text
X(t + dt) = X(t) * exp(mu_max * dt)
```

Outputs:

- time series;
- final biomass concentration;
- `result.json`;
- optional plot artifact.

This example is safe because it is deterministic, numeric, local, small, and does not require external files or network access.

Do not implement this example in 0D-A.

## 15. Minimal Frontend Surface

0D-B may add a thin local verification panel. It should not become Modeling Studio.

Minimum UI:

- select workspace;
- select model implementation;
- edit JSON parameters in a textarea;
- create queued runner job;
- explicit `Run` button;
- show status;
- show parsed JSON output;
- show bounded logs;
- list artifacts.

UI copy must state:

- local execution only;
- reviewed scripts only;
- no AI-generated code execution without user approval;
- no hidden background execution;
- files are written only under the JarvisOS data root run directory.

## 16. Testing Plan

0D-B backend tests should cover:

- schema initialization on fresh and existing SQLite databases;
- model implementation registration using `model_versions`;
- runner job creation creates a `SimulationRun` with `queued` status;
- run endpoint uses runner service, not route-level subprocess calls;
- invalid workspace/model version returns clear error;
- invalid JSON input rejected;
- over-size input rejected;
- timeout transitions to `timed_out`;
- process failure transitions to `failed`;
- missing result JSON transitions to `failed`;
- malformed result JSON transitions to `failed`;
- stdout/stderr are bounded and truncation is recorded;
- artifact path traversal is rejected;
- artifact registration creates both `artifacts` and `run_artifacts`;
- script hash is recorded/verified;
- command/environment metadata is redacted;
- no network is used in automated tests;
- no generated files are written outside a temporary data root.

Use a fake executor for most service tests. Add at most one subprocess integration test with a tiny deterministic local script if it is reliable on Windows.

## 17. 0D-B Implementation Plan

Implemented order:

1. Add schema initialization statements for `runner_jobs`, `run_artifacts`, and `run_logs`.
2. Add runner Pydantic models.
3. Add runner service methods for creating queued jobs without execution.
4. Add read endpoints for run detail and logs; generated artifacts are linked in storage for later UI/API work.
5. Add lifecycle transition helpers and event logging.
6. Add local path helpers for run directories under the data root.
7. Add `local_python.py` executor with no-shell subprocess invocation, timeout, bounded output, and redacted metadata.
8. Add safety preflight checks.
9. Add deterministic batch growth script only as an approved sample implementation.
10. Frontend panel was intentionally postponed to avoid expanding scope.
11. Run backend tests and compile checks.

## 18. Risks And Open Questions

- Python subprocess execution is not a strong sandbox. V0 depends on reviewed scripts, controlled paths, minimal environment, and time/output limits.
- Windows process termination must be tested carefully.
- A no-network guarantee is difficult without OS/container sandboxing. V0 should prevent credentials from entering the environment and block obvious network imports, but it cannot be treated as hostile-code isolation.
- The `model_versions` table is adequate as `ModelImplementation` for V0, but later milestones may need a dedicated model implementation table if multiple script files, dependency manifests, or runtime packages become first-class.
- Formal migrations are still postponed. If runner schema changes continue after 0D-B, Alembic should be reconsidered.
- Artifact storage should eventually standardize whether `stored_path` is absolute or data-root-relative.
