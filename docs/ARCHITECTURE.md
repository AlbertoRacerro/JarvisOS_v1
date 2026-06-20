# Architecture

This is the canonical architecture source for JarvisOS. Milestone reports remain historical evidence, but this document describes the current stable shape.

## Architecture Principle

JarvisOS is a local-first system for building engineering model capital. The backend owns durable state and policy. The frontend is an operator interface. AI models propose; JarvisOS validates, records, executes, and audits.

Stable role split:

```text
Gemma = local planner / context router / cheap classifier candidate
JarvisOS = state, memory, policy, validation, execution, audit
External APIs = specialist reasoning providers
Workbench = design interface
Foundry = model-capital system
Debate Mode = advanced critical reasoning layer
```

BlueRev modeling does not start until AI infrastructure, external API escalation, and the Modeling Workbench are strong enough to support real design work.

## Backend Spine

The FastAPI backend is the durable system boundary.

Core layers:

- `app/core`: configuration, paths, database readiness, logging, and shared errors.
- `app/api`: common HTTP entry points.
- `app/modules`: bounded feature modules.
- `app/schemas`: shared response and payload shapes.

The backend owns:

- configuration and path resolution;
- SQLite initialization;
- module boundaries;
- API routes;
- AI policy gates;
- local runner execution boundaries;
- event/audit records;
- artifact records.

The frontend must call backend APIs. It must not call providers, local model runtimes, filesystems, or execution tools directly.

## Local-First Storage

JarvisOS assumes a Windows-first local data root:

```text
C:\JarvisOS
```

The repository path and runtime data root are separate concepts:

- the repository stores source code and docs;
- the data root stores local runtime state, databases, workspaces, logs, and artifacts.

All data-root-derived paths must remain centralized through `app/core/paths.py`.

SQLite is the initial database. The schema is intentionally small and migration-friendly. Alembic is postponed until schema churn justifies formal migration tooling.

## Domain Foundation

Current persistent objects include:

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

These records are deliberately minimal. Early records use stable IDs, timestamps, status fields, schema version fields, notes, and raw payloads where useful.

`simulation_runs` remains the canonical run record. Runner-specific operational details live in runner tables and link back to SimulationRun.

## AI Gateway

All AI provider access must pass through the AI Gateway and provider adapter boundaries. Routes, frontend code, modeling services, runner code, and future workbench features must not call providers directly.

Defaults are safe:

- paid AI disabled;
- budget zero;
- provider mode `fake`;
- no external calls by default;
- tests use mocked/fake providers.

Provider calls require explicit settings, credential presence, budget approval, token/cost guard approval, local policy approval, and event/audit recording.

Current live-provider paths are narrow smoke/diagnostic paths only:

- Scaleway fixed synthetic smoke tests.
- Scaleway AI Smoke Console.
- DeepSeek provider-smoke path.
- Backend-only Supervisor public-test slice.

These are not chat, routing, BlueRev modeling, memory runtime, RAG, file ingestion, or autonomous agents.

## Local Policy And Gate Ordering

Raw user input must be inspected locally before any external provider is considered.

Future intended order:

```text
User input
-> deterministic local hard rules
-> optional local Gemma classifier
-> GateDecision
-> external tier/provider adapter only if allowed
-> AIResponse
-> event/audit
```

Cloud providers must not be used as the first privacy classifier. JarvisOS remains authoritative for policy.

Future logical gates include:

- `LOCAL_ONLY`
- `LOCAL_GEMMA`
- `USER_CONFIRM_REQUIRED`
- `CHEAP_GATE`
- `CHEAP_PLUS_GATE`
- `SCIENTIFIC_MEDIUM_GATE`
- `FRONTIER_GATE`
- `BLOCKED`

## Local Gemma Position

Local Gemma is not approved as a general operating brain.

Canonical evidence lives in:

```text
docs/LOCAL_AI_EVALUATION_EVIDENCE.md
```

Current conclusion:

- `gemma4:12b-it-qat` is viable only for classification-style local utilities.
- 12B is not approved for orchestration, local gatekeeping, chat, memory runtime, retrieval runtime, Context Pack Broker runtime, provider routing, autonomous tools, frontend UI, or BlueRev modeling.
- `gemma4:31b-it-qat` is only an occasional heavy local expert candidate.
- FunctionGemma remains future-track until tool catalog and dataset work exists.

Gemma may eventually propose small structured objects. JarvisOS validates those objects and decides what happens next.

## Context Pack Broker Future Role

The Context Pack Broker is a future JarvisOS service, not a model-controlled runtime.

It should:

- maintain a bounded context package taxonomy;
- assemble source-grounded context packages;
- preserve provenance and freshness metadata;
- detect gaps, contradictions, and stale evidence;
- feed validated context into local or external AI paths.

Gemma may request context packages from a controlled vocabulary only after reliability work proves that behavior. It must not retrieve arbitrary files or database records directly.

## External API Role

External APIs are future specialist reasoning providers.

They should be reached only after:

- local policy allows the request;
- sensitivity/redaction rules pass;
- budget and token/cost guards pass;
- provider credentials are available through approved secret handling;
- the request is packaged with bounded context and provenance;
- events record the route decision and provider result without raw secrets.

Normal users should interact with one Supervisor/Workbench interface. Provider ids, model ids, tier assignments, fallback chains, credentials, and diagnostic smoke targets remain internal or admin/config-only.

## Modeling Workbench Future Role

The Modeling Workbench is the future design interface. It should not be a generic chat UI.

Expected workbench responsibilities:

- structured model design input;
- assumption and equation editing;
- evidence/literature panel;
- AI review panel;
- simulation runner integration;
- run comparison view;
- explicit save/accept/reject decisions.

The current Domain Foundation page is a temporary verification surface and should be split before real workflows grow.

## BlueRev Foundry Future Role

BlueRev Foundry is the future model-capital system.

Expected responsibilities:

- ModelSpec records;
- SimulationRun tracking;
- artifact tracking;
- parameter and assumption library;
- validation and decision loop.

Do not start real BlueRev modeling until local AI classification utilities, external API escalation, Context Pack Broker design, and Modeling Workbench foundations are ready.

## R&D Debate Mode Future Role

R&D Debate Mode is a later critical reasoning layer.

It should come after:

- provider abstraction hardening;
- context packaging;
- provenance and redaction policy;
- Modeling Workbench surfaces;
- model/run/artifact tracking.

It must not be implemented as an ungated multi-agent loop over sensitive BlueRev content.

## Python Runner V0

The current Python Runner is a minimal local runner for reviewed deterministic scripts only.

It provides:

- explicit queued job creation;
- explicit synchronous run call;
- no shell invocation;
- no inherited API keys or secrets;
- controlled working directory under the data root;
- script SHA-256 recording and validation;
- timeout;
- bounded stdout/stderr;
- bounded output and artifact registration;
- SimulationRun integration.

It is not a hostile-code sandbox, notebook executor, general Python execution platform, or AI-generated code runner.

## Secrets

Current secret handling is intentionally narrow.

- Scaleway app-entered key storage is runtime memory only.
- Environment variables can provide provider keys.
- Raw keys must not be returned to the frontend, written to events, stored in AI settings, logged, or copied into docs.

A persistent Windows credential store or DPAPI-backed store requires a separate design/review milestone.

## Current Roadmap

```text
0F-F  AI/local_ai module boundary audit

1A    Classification-only Gemma 12B utility
1B    Thinking/token budget control
1C    Flat schema reliability harness
1D    Context request reliability
1E    Sensitivity check reliability
1F    Tool proposal reliability

2A    Context Pack taxonomy
2B    Source vault structure
2C    Context Pack Broker V0
2D    Evidence/provenance layer
2E    Gaps/contradictions/stale evidence detection

3A    External prompt package format
3B    Redaction/sensitivity policy
3C    Provider abstraction hardening
3D    DeepSeek
3E    Grok
3F    Gemini Pro 3
3G    GPT-5.5
3H    Provider selection policy

4A    Modeling Workbench architecture
4B    Structured model design input
4C    Assumption/equation editor
4D    Evidence/literature panel
4E    AI review panel
4F    Simulation runner integration
4G    Run comparison view

5A    BlueRev Foundry ModelSpec
5B    SimulationRun tracking
5C    Artifact tracking
5D    Parameter/assumption library
5E    Validation and decision loop

6A    R&D Debate Mode design
6B    Multi-agent review prototype
6C    BlueRev advanced design debates
```

## Canonical References

- Decisions: `docs/DECISIONS.md`
- Runbooks: `docs/RUNBOOKS.md`
- Local AI evidence: `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- UI startup: `docs/UI_START.md`

Milestone documents remain historical evidence. If a milestone document conflicts with this file or `DECISIONS.md`, prefer the canonical docs.
