# JarvisOS

JarvisOS is a local-first AI co-engineering workspace for building engineering model capital. It is Windows-first, backend-led, and intentionally architecture-strong before it becomes feature-broad.

Core principle:

> AI models propose. JarvisOS validates, gates, records, executes, and audits.

- The backend owns state, policy, validation, execution, and audit.
- Local models operate through explicit backend routes and advisory classification boundaries.
- External APIs are specialist reasoning providers behind explicit policy gates; they are never called automatically.
- The frontend is an operator interface over backend authority.

## Reading current state

This README is an onboarding document, not a live roadmap or runtime authority.

For current work state and priority, read `docs/specs/STATUS.md`. For agent execution and autonomous continuation, read `AGENTS.md` and `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`. For actual behavior, inspect current code and exact-head deterministic evidence.

The runtime summary below was originally verified against code on 2026-07-02 and is retained as orientation. Later merged specs and current code supersede any stale detail.

## Runtime orientation

**AI execution spine.** Product AI tasks go through `run_ai_task` and create an `ai_jobs` ledger row. Defaults remain safe: provider mode `fake`, paid AI disabled, budget zero, and tests use fake or mocked providers.

**Auto route.** `route_class="auto"` is local-only and advisory-classifier-assisted. RouterPolicy remains authoritative. Auto never executes an external provider; external intent returns a non-executing control state.

**Context.** Context levels are bounded posture and budget controls rather than semantic retrieval. Source selection is deterministic unless a later accepted spec changes that behavior.

**Domain Foundation.** Durable records include workspaces, entities, links, events, artifacts, model specs, assumptions, parameters, model versions, simulation runs, runner jobs and logs, decisions, and AI settings.

**Python Runner V0.** Bounded local execution of reviewed deterministic scripts with script pinning, policy preflight, path constraints, and SimulationRun integration. It is not a general execution platform.

**Frontend.** React, Vite, and TypeScript provide the operator UI. Current pages and workflow state must be verified from current code and the frontend-beta queue in `docs/specs/STATUS.md`.

**Dev-only paths.** Development and diagnostic endpoints remain non-production surfaces unless a later accepted spec explicitly promotes them.

## Development workflow

- `AGENTS.md` owns hard invariants, safety boundaries, tests, and general coding-agent conduct.
- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md` owns exact-SHA delivery, autonomous continuation, model collaboration, finding closure, post-beta deferral, and documentation-drift rules.
- Work items are specs in `docs/specs/`; the sole live status and roadmap authority is `docs/specs/STATUS.md`.
- One implementation branch and PR are used per spec, with one active writer and no overlapping runtime fronts.
- Automated and model reviews are advisory evidence. The assigned technical merge owner may merge with an expected-head SHA only after required deterministic gates and proof are green and no current blocking finding remains.
- Never enable GitHub auto-merge and never push directly to `master`.

## Canonical documents

- Agent invariants: `AGENTS.md`
- Agent execution and automation: `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`
- Documentation authority map: `docs/README.md`
- Spec status and roadmap: `docs/specs/STATUS.md`
- Spec workflow: `docs/specs/README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/DECISIONS.md`
- Runbooks: `docs/RUNBOOKS.md`
- UI start guide: `docs/UI_START.md`
- Local AI evidence: `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- Strategy review pack: `docs/strategy/FABLE_REVIEW_INDEX.md`

Architecture prose is descriptive, not an independent live roadmap. When a document conflicts with current code, accepted decisions, the active spec, or `docs/specs/STATUS.md`, use the authority procedure in `docs/README.md` and correct the stale document in a bounded change.

## Repository layout

```text
backend/    FastAPI application and backend tests
frontend/   React + Vite + TypeScript app
scripts/    Windows PowerShell startup scripts and local probe/smoke scripts
docs/       Canonical docs, specs, strategy pack, design material, evidence
schemas/    JSON schemas
reports/    Generated evaluation and smoke reports
```

The Git repository and runtime data root are separate. Runtime data defaults to:

```text
C:\JarvisOS
```

## Start JarvisOS

One-click local start on Windows:

```text
Start-JarvisOS.cmd
```

Separate launchers:

```text
Start-JarvisOS-Backend.cmd
Start-JarvisOS-Frontend.cmd
```

PowerShell scripts:

```powershell
.\scripts\init-database.ps1
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

Open `http://localhost:5173` for the frontend and `http://localhost:8000` for the backend.

## Recreate dependencies

Backend virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
```

Frontend dependencies:

```powershell
cd frontend
npm install
```

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check app tests
```

Frontend build check:

```powershell
cd frontend
npm run build
```

## Next milestones

The only live roadmap and spec-state registry is `docs/specs/STATUS.md`. Do not copy a current sequence into this README; update the registry when priorities, dependencies, PR state, or merge state change.
