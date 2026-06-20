# Database Scale-up And Migration Strategy

## Current State

JarvisOS uses SQLite with centralized schema definitions in `backend/app/core/schema.py`. The schema includes:

- `schema_migrations`;
- workspaces and domain records;
- events;
- artifacts;
- model versions;
- simulation runs;
- runner jobs, logs, and run artifacts;
- decisions;
- AI settings.

Indexes already exist for core read paths such as events, artifacts, runs, runner jobs, and model versions.

## Invariants

### Object Identity

Every major durable object must have a stable UUID string primary key.

This applies to:

- workspaces;
- entities;
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
- future source records;
- future AI usage records.

### Workspace Policy

Every domain object that belongs to user work must carry `workspace_id`.

Exceptions:

- global AI settings;
- schema migrations;
- global local secret metadata, if ever persisted;
- app/system metadata.

### Timestamp Policy

Use ISO-8601 UTC strings consistently until a formal DB migration layer chooses database-native timestamp types. Required fields:

- `created_at` for durable records;
- `updated_at` for mutable records;
- `started_at` and `completed_at` for execution records.

### Schema Migration Policy

Current `schema_migrations` is enough for small local-first hardening. Formal migration tooling should be introduced when:

- a milestone changes more than two tables;
- a field is renamed or removed;
- backfill logic is required;
- multiple old SQLite states must be supported;
- PostgreSQL migration starts.

Do not add Alembic during this docs-only milestone.

### Payload JSON Versioning

Every JSON payload that may survive across versions should include or be paired with a schema version.

Priority payloads:

- `model_specs.raw_payload`;
- `simulation_runs.input_payload`;
- `simulation_runs.parameter_payload`;
- `simulation_runs.output_payload`;
- future AI review outputs;
- future source extraction outputs;
- runner manifests.

### Foreign Key Policy

Use foreign keys for core ownership and relationships. Ensure `PRAGMA foreign_keys = ON` remains enforced in connection creation.

Future high-value relationships:

- source document to extraction output;
- AI review to source artifact;
- Decision to SimulationRun, ModelSpec, artifact, or source record.

### Index Policy

Every list endpoint should have an index matching:

```text
(workspace_id, created_at)
```

or:

```text
(workspace_id, status)
```

Add targeted indexes when query patterns appear. Avoid indexing every column preemptively.

### Path Storage Policy

Durable path identity should become relative to the data root. Absolute paths may be runtime-derived but should not be the only persisted identity after the artifact storage hardening milestone.

### Artifact Metadata Policy

Artifact metadata must remain queryable in SQLite:

- type;
- role;
- hash;
- size;
- storage backend;
- logical key;
- source/provenance;
- status.

### Event Schema Policy

Events should stay append-only, but payload conventions need typed schemas for:

- AI gate decision;
- routing proposal;
- authority decision;
- provider attempt;
- provider result;
- token usage;
- runner lifecycle;
- artifact registration.

### Provider And Model ID Policy

Provider and model IDs should be stable strings. Provider-native model names can be stored separately from JarvisOS model IDs.

### Usage Accounting Future

Scaleway counters inside `ai_settings` are acceptable for smoke tests. Future provider usage should move into a provider-neutral `ai_usage_records` table with:

- provider id;
- model id;
- task type;
- input tokens;
- output tokens;
- usage source;
- cost estimate;
- currency;
- workspace id;
- request id;
- created at.

### Source And Provenance Future

Future scientific source ingestion needs source/provenance tables before parser implementation:

- source document;
- source artifact;
- extraction run;
- extracted claim/table;
- citation;
- confidence;
- human decision link.

### SimulationRun Canonical Rule

`simulation_runs` is the canonical execution record. Runner jobs are operational details. Workbench UI should treat SimulationRun as the user-facing run object.

### Decision Canonical Rule

`decisions` is the canonical human acceptance record. AI outputs and runner results remain suggestions/evidence until linked to a Decision.

## Proposer, Critic, Synthesizer

### Proposal v1

Keep all current tables and add fields directly whenever a milestone needs them.

### Critique v1

Direct field addition keeps momentum but risks creating tables shaped by the first feature that needs them. `ai_settings` already shows this with dormant legacy Scaleway token fields beside active monthly token fields.

### Improved Proposal v2

Use explicit migration triggers. Add tables only when a concrete workflow needs durable records, but define invariants before implementation. Keep compatibility fields until a migration can safely remove or deprecate them.

### Critique v2

This may leave some duplication in the short term.

### Final Synthesis

Accept short-term duplication where it preserves compatibility. Before scale-up features, introduce provider-neutral and artifact-neutral records rather than expanding feature-shaped fields.

Residual risk: schema docs and implementation can drift unless tests validate migration paths.

## Current Schema Critique

### Missing Or Future Indexes

Likely future indexes:

- `model_specs(workspace_id, updated_at)`;
- `assumptions(workspace_id, status)`;
- `parameters(workspace_id, status)`;
- `decisions(workspace_id, created_at)`;
- `run_logs(workspace_id, simulation_run_id, created_at)`;
- `events(event_type, created_at)`;
- future `artifacts(workspace_id, artifact_type, created_at)`;
- future `ai_usage_records(workspace_id, provider_id, created_at)`.

Do not add all now. Add as endpoints demand.

### Likely Slow Queries

Future slow paths:

- dashboard aggregations over many runs and artifacts;
- event audit screens filtered by type;
- artifact browser filtered by type and source;
- Workbench pages loading model specs, runs, decisions, and artifacts together.

### Tables That May Need Normalization Later

- `ai_settings`: provider-specific counters should move to provider-neutral usage records.
- `simulation_runs`: input/output payloads may require separate normalized output summaries.
- `artifacts`: storage metadata should split durable identity from display path.
- `events`: typed event payloads may need per-event schema names.

### JSON Payloads Needing Version Fields

- runner input sets;
- runner output sets;
- AI request contexts;
- AI responses;
- source extraction outputs;
- artifact manifests.

### SQLite-specific Concerns

Avoid:

- depending on dynamic typing quirks;
- relying on JSON text where PostgreSQL JSONB queries will later be expected;
- assuming no concurrent writes when runner queues grow;
- storing booleans without clear conversion conventions.

Current bool-as-integer usage is acceptable for SQLite V0 but should be mapped carefully in a future ORM/migration layer.

## Alembic Decision

Do not add Alembic now.

Add Alembic or an equivalent formal migration tool when:

- provider-neutral usage tables are introduced;
- artifact storage metadata fields are added;
- source/provenance tables are introduced;
- schema changes need data backfill;
- a PostgreSQL compatibility milestone begins.

## PostgreSQL Readiness Checklist

Before PostgreSQL:

- replace ad hoc SQL with repository boundaries for hot paths;
- define JSONB fields and schema versions;
- audit indexes;
- ensure foreign keys are portable;
- avoid SQLite-specific `INSERT OR IGNORE` where semantics matter;
- add migration tests;
- add database URL config;
- preserve local SQLite as default unless hosted/team mode appears.

