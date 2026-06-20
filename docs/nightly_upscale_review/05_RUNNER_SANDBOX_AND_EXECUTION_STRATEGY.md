# Runner Sandbox And Execution Strategy

## Current Runner V0

Python Runner V0 supports one reviewed deterministic script:

```text
batch_growth_v0
```

Current protections:

- explicit model implementation creation;
- explicit queued runner job creation;
- explicit run endpoint;
- local execution only;
- `shell=False`;
- minimal non-secret environment;
- controlled working directory under data root;
- explicit input file and output directory;
- timeout;
- bounded stdout/stderr;
- bounded result JSON;
- bounded artifacts;
- script SHA-256 record and validation;
- preflight marker checks for obvious network, subprocess, destructive-file, `.env`, and secret access;
- SimulationRun as canonical execution record.

## What V0 Is Not

V0 is not:

- a hostile-code sandbox;
- arbitrary Python execution;
- notebook execution;
- AI-generated code execution;
- a plugin runtime;
- a remote execution platform;
- a general workflow engine.

## Proposer, Critic, Synthesizer

### Proposal v1

Keep adding reviewed scripts using the current `runner/service.py` pattern.

### Critique v1

This would centralize too much behavior in one file: script registration, validation, lifecycle, subprocess execution, artifact parsing, logs, events, and readback. The second or third script kind would likely add conditional branches around safety.

### Improved Proposal v2

Before adding a second script kind, add a V1 script manifest and split runner responsibilities:

- implementation registration;
- job creation;
- execution orchestration;
- artifact registration;
- repositories;
- safety policy.

### Critique v2

Splitting too early could produce unused abstractions.

### Final Synthesis

Freeze V0 for one reviewed script. Introduce a small manifest only when a second reviewed script is approved. Keep the split minimal and driven by real responsibilities, not plugin ambition.

Residual risk: local Python can still perform unwanted operations if a reviewed script is malicious or marker checks miss something.

## Staged Hardening Plan

### V0: Reviewed Scripts Only

Current state.

Rules:

- only reviewed deterministic scripts;
- no user-uploaded code;
- no AI-generated code execution;
- no automatic execution from AI response;
- no notebook execution;
- no network;
- no inherited secrets.

### V1: Script Manifest

Add a manifest per reviewed script:

```json
{
  "implementation_kind": "batch_growth_v0",
  "entrypoint": "batch_growth.py",
  "script_sha256": "...",
  "input_schema_version": 1,
  "output_schema_version": 1,
  "allowed_artifact_types": ["csv_timeseries"],
  "timeout_seconds_max": 60,
  "deterministic": true,
  "requires_network": false,
  "dependencies": ["python-stdlib"],
  "reviewed_by": "local-user",
  "reviewed_at": "iso-8601"
}
```

### V2: Sandbox Or Container Option

Only if justified by broader scripts:

- Windows sandbox policy;
- container profile;
- no network by default;
- read-only script mount;
- explicit input/output mount;
- CPU/memory limits.

Do not implement until V1 proves insufficient.

### V3: Queue/Worker

Only if run duration or concurrency requires it:

- persistent queue;
- cancellation;
- process supervision;
- worker heartbeat;
- retry policy;
- run locking.

### V4: Remote Execution

Only if local execution cannot meet engineering needs:

- remote worker authority policy;
- data egress classification;
- artifact sync;
- signed manifests;
- encrypted transport;
- explicit human confirmation.

## Allowed Script Manifest

Required fields:

- implementation kind;
- entrypoint;
- script hash;
- input schema version;
- output schema version;
- timeout max;
- output size max;
- allowed artifact types;
- dependency policy;
- deterministic flag;
- no-network flag;
- review metadata.

## Input Schema Validation

Current batch-growth validation is hardcoded and good for V0. Future V1 should:

- validate against a named schema;
- reject unknown fields unless manifest allows them;
- enforce finite numeric inputs;
- enforce artifact id references exist and belong to workspace;
- record normalized input payload.

## Output Schema Validation

Runner outputs should include:

- schema version;
- status;
- outputs object;
- artifacts list;
- warnings list;
- deterministic seed if relevant;
- model implementation id;
- run metadata.

Reject:

- non-object JSON;
- oversized JSON;
- undeclared artifact paths;
- absolute artifact paths;
- artifact types outside manifest.

## Reproducibility

Record:

- script SHA-256;
- manifest SHA-256;
- Python executable name and version;
- command metadata;
- environment metadata;
- input payload;
- output payload;
- dependency policy;
- deterministic seed if used.

## Dependency Policy

V0 uses stdlib only for the reviewed example. Future policies:

- `stdlib_only`;
- `pinned_requirements`;
- `managed_environment`;
- `container_image_digest`.

Do not allow arbitrary `pip install` during run.

## Resource Limits

Current:

- timeout;
- stdout/stderr bytes;
- output JSON bytes;
- artifact bytes.

Future:

- CPU time;
- memory;
- number of files;
- total output directory size;
- process count;
- network disabled enforcement.

## Artifact Registration

Runner should never assume an output file is safe just because it exists. It must be:

- declared in result JSON;
- relative path only;
- inside output dir;
- within max size;
- allowed type by manifest;
- hashed;
- linked to SimulationRun.

## Run Cancellation Future

Current synchronous V0 cannot cancel a process from another request. Add cancellation only with V3 queue/worker. Do not fake cancellation in the API before process supervision exists.

## AI-generated Code Rule

AI may suggest code in a future review workflow, but:

- generated code is never executed automatically;
- generated code must become a reviewed script artifact;
- manifest and hash must be recorded;
- human approval is required before any run.

