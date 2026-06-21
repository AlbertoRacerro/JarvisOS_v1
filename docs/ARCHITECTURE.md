# Architecture

This is the canonical architecture source for JarvisOS. Milestone reports remain historical evidence, but this document describes the current stable shape.

## Architecture Principle

JarvisOS is a local-first system for building engineering model capital. The backend owns durable state and policy. The frontend is an operator interface. AI models propose; JarvisOS validates structure, records, executes, and audits.

Corrected local intelligence principle:

```text
Gemma = local semantic brain inside bounded forms and protocols
JarvisOS = deterministic structure, schemas, permissions, persistence, execution, audit
External APIs = specialist reasoning providers
Workbench = design interface
Foundry = model-capital system
Debate Mode = advanced critical reasoning layer
```

This is a form-driven local intelligence architecture. JarvisOS makes the system readable to Gemma through showcase files, indexes, forms, and source IDs. Gemma performs semantic reasoning locally inside those forms. JarvisOS validates structure only and decides what can be saved, retried, promoted, or executed.

Structural validation is not semantic validation. JarvisOS may validate schemas, required fields, enum values, booleans, field lengths, status values, source IDs, path existence, allowed roots, permitted save locations, valid state transitions, and obvious secrets. JarvisOS must not claim to validate semantic fidelity, strategic correctness, summary quality, technical truth of a design assumption, completeness of a memory card, or subtle sensitivity classification.

Memory intake follows a staged principle:

```text
write fast, enrich later, reason deeply only on retrieval
```

Initial memory intake preserves raw text, provenance, observable flags, broad uncertain buckets, and enrichment status. Full contextual interpretation is deferred until retrieval, decision use, conflict resolution, sensitivity review, high-value promotion, or full context-pack availability.

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
-> Gemma form fill inside bounded schemas
-> structural validation, retry, or clarification
-> policy decision
-> external tier/provider adapter only if allowed
-> AIResponse
-> event/audit
```

Cloud providers must not be used as the first privacy classifier. JarvisOS remains authoritative for policy and execution, but Gemma performs semantic assessment locally where deterministic hard rules are insufficient.

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

- `gemma4:12b-it-qat` is viable only for non-critical advisory semantic hints, such as task, project, topic, context-need, and confidence hints.
- 12B must not own risk, next action, permission, provider selection, tool execution, memory write, retrieval, route selection, external calls, final sensitivity, or safety decisions.
- 12B is not approved for orchestration, local gatekeeping, chat, memory runtime, retrieval runtime, Context Pack Broker runtime, provider routing, autonomous tools, frontend UI, or BlueRev modeling.
- `gemma4:31b-it-qat` is only an occasional heavy local expert candidate.
- FunctionGemma remains future-track until tool catalog and dataset work exists.

Gemma may eventually propose small structured objects through forms such as non-critical classification hints, context requests, memory cards, source cards, decision cards, sensitivity assessments, tool intent, provider intent, and clarification requests. JarvisOS validates those forms structurally, applies hard policy overrides, retries with machine-readable errors, saves proposed objects, and decides what happens next.

For the current 12B classification utility, model output is restricted to advisory semantic hints. Fields that look safety-critical in diagnostics, including risk, next action, provider/tool intent, memory, retrieval, route, external-call, and final-sensitivity decisions, are owned by JarvisOS policy, deterministic hard overrides, user confirmation, stronger local review, or future API review gates.

Canonical form-driven design lives in:

```text
docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md
```

### Gemma-Facing Showcase Files

Future JarvisOS should maintain a small set of Gemma-facing showcase files, such as:

```text
GEMMA_START_HERE.md
CURRENT_STATE.md
SYSTEM_MAP.md
MEMORY_INDEX.md
PROJECT_INDEX.md
FILE_CATALOG.md
DECISION_INDEX.md
OPEN_CLARIFICATIONS.md
TOOL_AND_PROVIDER_CATALOG.md
SAFETY_POLICY.md
```

Gemma should read these small files first, use them to request the right source files or context packages, and tolerate moderate over-fetch. Under-fetch on important tasks is a serious failure mode.

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

## Memory Staging

Future memory should move through explicit stages:

```text
raw_input
fast_intake
proposed_memory
enriched_memory
accepted_memory
canonical_state
superseded
```

Fast intake is intentionally cheap. `FastIntakeSignalForm` is not a final memory object; it is a source-linked signal envelope used to preserve potentially useful input without forcing fine-grained semantic interpretation at write time.

Gemma may propose broad intake signals or, during later enrichment, candidate memory cards. JarvisOS validates structure and source links, preserves raw input, and controls promotion through explicit policy such as deterministic validation, sampling review, stronger local 31B or API review, direct user decision, repeated use without contradiction, or source-grounded verification. The user should not be required to personally review every routine mechanical memory card once reliability evidence supports more autonomy.

Canonical staged memory intake design lives in:

```text
docs/STAGED_MEMORY_INTAKE.md
```

External memory implementation references were audited before 1D:

```text
docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md
```

Cavemem/Caveman inform future MemoryStore, progressive retrieval, compression
policy, hook, worker, and viewer design only as patterns. JarvisOS has not
vendored their code and has not added runtime memory, retrieval, compression,
MCP, hooks, worker, or viewer behavior from that audit.

## Current Roadmap

```text
0F-F  AI/local_ai module boundary audit

1A    Classification-only Gemma 12B utility
1B    Thinking/token budget control
1B-R-LIVE  Manual Gemma 12B classification probe
1C         Classification live probe analysis and roadmap rebase
1C-Y       Fast staged memory intake design
1C-Z-T     Cavemem/Caveman reference implementation audit
1D-A       Local-model-facing showcase files design
1D-B       Micro-context design
1D-C       MemoryStore facade design
1D-D       Internal compression policy tests
1D-E       SQLite/FTS schema design
1D-F       Progressive retrieval contract design
1D-G       Holdout intake generalization set
1E         Form protocol catalog design
1F         Structural validator + retry loop design
1G         Gemma form-fill smoke test harness
1H         Showcase files generator design
1I         Context access from showcase files
1J         Provider/tool intent form design

2A         Source-grounded review protocol
2B         Optional 31B/API sampling review
2C         Memory promotion policy
2D         Memory index generation
2E         Context package assembly

3A         External prompt package format
3B         Redaction/sensitivity policy
3C         Provider abstraction hardening
3D         DeepSeek
3E         Grok
3F         Gemini
3G         GPT-5.5
3H         Provider selection policy

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
- Form-driven local intelligence: `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- Cavemem/Caveman reference audit: `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- UI startup: `docs/UI_START.md`

Milestone documents remain historical evidence. If a milestone document conflicts with this file or `DECISIONS.md`, prefer the canonical docs.
