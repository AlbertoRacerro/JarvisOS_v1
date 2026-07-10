# JarvisOS

JarvisOS is a local-first AI co-engineering workspace for building engineering
model capital. It is Windows-first, backend-led, and intentionally
architecture-strong before it becomes feature-broad.

Core principle:

> AI models propose. JarvisOS validates, gates, records, executes, and audits.

- The backend owns state, policy, validation, execution, and audit.
- Local models (via Ollama) do most of the work through an explicit route matrix;
  a local classifier (Gemma) provides advisory semantic hints for the Auto route.
- External APIs are specialist reasoning providers behind explicit policy gates;
  they are never called automatically.
- The Modeling Workbench is the future design interface; BlueRev Foundry is the
  future model-capital system.

## Current Runtime Status

Verified against code as of 2026-07-02.

**AI execution spine.** Every AI task goes through `run_ai_task` and
`POST /ai/tasks/run`; every call writes a ledger row to `ai_jobs` (route,
provider/model, usage, latency, digests, errors). Defaults are safe: provider
mode `fake`, paid AI disabled, budget zero; `route_class=None` resolves to
`local:fake`.

**Route bindings** (`backend/app/modules/ai/execution.py`, env-overridable):

| Route class | Provider | Default model | Access |
| --- | --- | --- | --- |
| `local:fake` | fake | `fake-deterministic-v1` | default, tests |
| `local:fast` | Ollama | `qwen3:8b` | explicit or Auto |
| `local:general` / `local:gemma` | Ollama | `gemma4:12b-it-qat` | explicit or Auto |
| `local:coder` | Ollama | `deepseek-coder-v2:16b` | explicit or Auto |
| `local:coder_heavy` | Ollama | `qwen3-coder:30b` | explicit or Auto |
| `external:cheap` | Scaleway | `llama-3.1-8b-instruct` | explicit/manual only |
| `external:reasoning` | Scaleway | `qwen3-235b-a22b-instruct-2507` | explicit/manual only |

**Auto route** (`route_class="auto"`): a local classifier (default
`gemma4:12b-it-qat`, advisory-only, with a conservative deterministic fallback)
maps the prompt to a capability row and a local route; RouterPolicy — the
canonical deterministic producer in the backend — decides whether local execution
is safe. Auto never executes an external provider; external intent returns a
non-executing control state. Confidential/sensitive-IP content can be answered
locally when no external/tool/state action is requested; `secret` stays blocked.

**Context.** Context levels (`none`/`light`/`standard`/`deep`) are budget/posture
controls with route-aware character budgets — not semantic retrieval. Manual
context blocks are preserved and counted before workspace context. Source
selection is deterministic (`budget_only`).

**Domain Foundation.** Durable records: workspaces, entities, links, events,
artifacts, model specs, assumptions, parameters, model versions, simulation
runs, runner jobs/logs, decisions, AI settings — in SQLite under the data root.

**Python Runner V0.** Bounded local execution of reviewed deterministic scripts
(batch-growth), with script pinning, policy preflight, path constraints, and
SimulationRun integration. Not a general execution platform.

**Frontend** (React + Vite + TS): Dashboard, AI console (`AIDraft`), Domain
Foundation editor, dev-only Local Chat, System Status.

**Dev-only paths.** `POST /api/dev/message-route-smoke` and
`POST /api/dev/local-chat` are gated development/diagnostic surfaces, not
production chat.

**Not built yet** (by design, see roadmap): semantic retrieval/memory runtime,
external Auto execution, tool execution from AI, agent orchestration, streaming,
adaptive routing.

## Development Workflow

- `AGENTS.md` is the single source of instructions for AI coding agents:
  invariants, environments (Windows local vs Linux CI/cloud), test gate,
  conventions.
- Work items are specs in `docs/specs/`; the live status and roadmap are in
  `docs/specs/STATUS.md`, and the execution workflow is in
  `docs/specs/README.md`.
- CI (GitHub Actions) runs ruff + the full backend pytest suite on every PR.
  Automated code review is advisory; merge authority is CI green plus human
  review. No self-merge, no auto-merge, no direct pushes to `master`.

## Canonical Docs

- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/DECISIONS.md`
- Runbooks: `docs/RUNBOOKS.md`
- UI start guide: `docs/UI_START.md`
- Local AI evidence: `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- Spec status and roadmap: `docs/specs/STATUS.md`
- Spec workflow: `docs/specs/README.md`
- Strategy review pack: `docs/strategy/FABLE_REVIEW_INDEX.md`

Everything else under `docs/` is design material or historical milestone
evidence (see `docs/README.md`). When an older milestone doc conflicts with the
files above or with current code, the canonical docs and code win.

## Repository Layout

```text
backend/    FastAPI application and backend tests
frontend/   React + Vite + TypeScript app
scripts/    Windows PowerShell startup scripts and local probe/smoke scripts
docs/       Canonical docs, specs, strategy pack, historical milestone evidence
schemas/    JSON schemas (design-time)
reports/    Generated evaluation/smoke reports
```

The Git repository and the runtime data root are separate. Runtime data
defaults to:

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

Open `http://localhost:5173` (frontend) and `http://localhost:8000` (backend).

## Recreate Dependencies

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

## Next Milestones

The only live roadmap and spec-state registry is `docs/specs/STATUS.md`. Do not
copy a current sequence into this README; update the registry when priorities,
dependencies, PR state, or merge state change.
