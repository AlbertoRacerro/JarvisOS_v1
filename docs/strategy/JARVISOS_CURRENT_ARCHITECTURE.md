# JarvisOS Current Architecture

## Architectural Contract

JarvisOS is backend-led. The backend owns durable state, policy, execution, and
audit. The frontend is an operator interface. AI models do not own state changes,
provider permissions, retrieval authority, or tool execution.

Current architecture can be summarized as:

| Subsystem | Current role |
| --- | --- |
| Domain Foundation | Project knowledge editor and durable state surface |
| Modeling + Runner | Model specs, versions, simulation runs, local Python Runner V0 |
| AI Layer | AI task endpoint, route bindings, Auto bridge, context builder, providers |
| Routing Policy | Canonical RouterPolicy producer in backend runtime |
| Local Runtime | Ollama endpoint resolver, status/lifecycle helpers, local adapters |
| Frontend | AI console, Domain Foundation, modeling views, diagnostics |
| Storage | SQLite under `C:\JarvisOS`, local workspace directories |

## Backend Shape

The backend uses FastAPI modules under `backend/app/modules`. Important module
areas:

| Module area | Function |
| --- | --- |
| `domain` / foundation services | Workspaces, entities, links, events, artifacts, assumptions, parameters, decisions |
| `runner` | Bounded local Python execution for simulation runs |
| `ai` | Execution spine, providers, task endpoint, context builder, routing bridge |
| `ai/routing` | RouterPolicy producer, safe-local predicates, Auto bridge, route matrix |
| `local_ai` | Local classifier and local runtime support |
| `tools` | Minimal tool registry skeleton |
| `agents` | Minimal agent registry skeleton |
| `settings` / secrets / policy | AI settings, budget, token guard, provider status |

The current backend direction is deliberately modular: project knowledge,
simulation execution, AI execution, routing, and future tools are related but not
collapsed into one monolithic "agent".

## Domain Foundation

Domain Foundation is the editor and storage surface for project knowledge. It is
the single intended place for managing:

- Workspaces.
- Entities and entity links.
- Events.
- Artifacts.
- Model specs.
- Assumptions.
- Parameters.
- Model versions.
- Simulation runs.
- Runner jobs and logs.
- Decisions.
- AI settings.

This matters because the AI console should not become a duplicate editor. AI
can consume selected context from Domain Foundation, but editing project
knowledge remains a distinct workflow.

## Modeling and Runner

The modeling path links project knowledge to executable simulations:

| Concept | Role |
| --- | --- |
| `model_specs` | User-facing model definition and metadata |
| `model_versions` | Versioned implementation binding |
| `simulation_runs` | Execution attempt and result state |
| `runner_jobs` | Local execution lifecycle |
| `run_logs` and artifacts | Execution evidence |

Local Python Runner V0 is intentionally narrow. It validates input JSON, checks
required batch-growth parameters, pins scripts by path and workspace, blocks
network/subprocess/destructive markers, constrains working directories, and
enforces size/time limits.

This runner is not yet a general tool-execution substrate. It is a bounded
engineering execution primitive.

## AI Execution Spine

The AI spine centers on `run_ai_task` and `/ai/tasks/run`.

Core properties:

- Every normal AI task goes through the execution spine.
- Ledger rows are written to `ai_jobs`.
- Direct provider calls outside provider/adapters are not the normal backend
  execution path.
- `route_class=None` remains safe/dev and resolves to `local:fake`.
- Explicit routes bypass Auto classification.
- `route_class="auto"` enters the Auto bridge.

This spine is the current positive AI execution foundation: it is usable,
audited, and narrow enough to reason about.

## Auto Bridge

Auto is not "let the model decide everything." Current Auto behavior is:

1. Classify the prompt through a local classifier.
2. Convert classification to provider-agnostic capability.
3. Map capability to a local route.
4. Decide context level and budget.
5. Build project context only if execution is local-safe.
6. Ask RouterPolicy for the permission decision.
7. Execute only if the decision is local-safe.
8. Otherwise return a control-state response and ledger row.

Auto is local-only. It must never execute an external provider. External intent
returns a non-executing proposal/confirmation state.

## Frontend

The frontend currently provides:

- AI execution console with explicit route choices and Auto.
- Domain Foundation editor for project knowledge.
- Modeling and runner views.
- Diagnostics/status surfaces.

Frontend should continue to expose backend truth rather than inventing its own
routing, memory, or provider semantics.

## Current Architecture Limits

| Limit | Current handling |
| --- | --- |
| No semantic retrieval | Context builder uses deterministic/budgeted project context |
| No autonomous agents | Only registry skeletons exist |
| No broad tool execution | Runner is narrow and controlled |
| No external Auto | External proposal is non-executing |
| No model-quality feedback loop | Routing is rule/matrix based |
| No distributed inference | Local Ollama runtime is host-local |

## Representative AI Request Flow

Normal explicit route:

1. Frontend or API sends `/ai/tasks/run`.
2. Request includes prompt, route class, task kind, max tokens, and optional
   context blocks.
3. Gateway validates route constraints.
4. `run_ai_task` resolves binding and adapter.
5. Provider adapter returns response or fails closed.
6. `ai_jobs` receives status, route, provider/model, usage, latency, digests, and
   error metadata.
7. API returns response plus ledger id and context metadata.

Auto route:

1. Request uses `route_class="auto"`.
2. Bridge classifies the prompt locally.
3. Bridge maps classifier output to capability and local route.
4. Bridge decides context level and budget.
5. RouterPolicy determines whether local execution is safe.
6. If safe, the bridge calls `run_ai_task` with the selected local route.
7. If not safe, the bridge writes a control-state ledger row and does not call a
   provider.

This flow is the architectural backbone. Any future memory, tool, or agent work
should attach to it through explicit contracts, not bypass it.

## Architecture Smells To Avoid

| Smell | Why it would hurt JarvisOS |
| --- | --- |
| UI-specific routing logic | Splits truth between frontend and backend |
| Provider adapter deciding policy | Makes safety provider-dependent |
| Memory writes inside model adapters | Turns providers into hidden state writers |
| Agent loop calling tools directly | Bypasses deterministic gates and ledgers |
| Context builder doing semantic ranking implicitly | Makes retrieval untestable and opaque |
| External fallback from failed local route | Risks accidental data egress and cost |
| One "super agent" owning all behavior | Collapses inspectable system layers into prompts |
