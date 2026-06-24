# JarvisOS

JarvisOS is a local-first AI co-engineering foundation for building engineering model capital. It is Windows-first, backend-led, and intentionally architecture-strong before it becomes feature-broad.

Current product direction:

- JarvisOS owns state, memory, policy, validation, execution, and audit.
- Gemma is the local semantic brain inside bounded forms and protocols.
- JarvisOS is the deterministic structure around Gemma: schemas, indexes, permissions, retries, persistence, and audit.
- External APIs are future specialist reasoning providers behind explicit policy gates.
- The Modeling Workbench is the future design interface.
- BlueRev Foundry is the future model-capital system, not the current implementation focus.

BlueRev modeling remains paused until AI infrastructure, external API escalation, and the Modeling Workbench are strong enough to support real design work.

## Current Status

The current codebase includes:

- FastAPI backend.
- React + Vite + TypeScript frontend.
- SQLite local persistence under the JarvisOS data root.
- Windows launch scripts.
- AI Gateway with fake-provider default and guarded smoke paths.
- Runtime-memory Scaleway key entry for smoke tests.
- Narrow DeepSeek provider-smoke path.
- Backend-only Supervisor public-test slice.
- Minimal local Python Runner V0 for one reviewed deterministic batch-growth script.
- Local Gemma evaluation/probe harnesses.

The current local Gemma conclusion is:

- `gemma4:12b-it-qat` is viable only for non-critical advisory semantic hints inside bounded diagnostics and future forms.
- 12B is not approved for orchestration, local gatekeeping, chat, memory, retrieval, Context Pack Broker runtime, provider routing, or BlueRev modeling.
- `gemma4:31b-it-qat` remains only an occasional heavy local expert candidate.
- Future Gemma work should be form-driven: Gemma performs local semantic reasoning, while JarvisOS validates structure only and decides what can be saved, retried, promoted, or executed.
- Memory intake is staged: write fast, preserve raw input and broad signals, enrich later only when retrieval, decisions, conflicts, sensitivity, promotion, or context packs justify deeper reasoning.

## Canonical Docs

- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/DECISIONS.md`
- Runbooks: `docs/RUNBOOKS.md`
- UI start guide: `docs/UI_START.md`
- Local AI evidence: `docs/LOCAL_AI_EVALUATION_EVIDENCE.md`
- Form-driven local intelligence: `docs/FORM_DRIVEN_LOCAL_INTELLIGENCE.md`
- Form protocol catalog: `docs/FORM_PROTOCOL_CATALOG.md`
- Structural validator retry loop design: `docs/STRUCTURAL_VALIDATOR_RETRY_LOOP_DESIGN.md`
- Local model form-fill smoke harness: `docs/LOCAL_MODEL_FORM_FILL_SMOKE_HARNESS.md`
- Two-phase secretary analysis: `docs/TWO_PHASE_SECRETARY_ANALYSIS_DESIGN_1G_B2_F2_R.md`
- Fast secretary policy-gate overlay design: `docs/FAST_SECRETARY_POLICY_GATE_OVERLAY_DESIGN.md`
- Staged memory intake: `docs/STAGED_MEMORY_INTAKE.md`
- Cavemem/Caveman reference audit: `docs/CAVEMEM_CAVEMAN_REFERENCE_AUDIT.md`
- Local-model-facing showcase files: `docs/LOCAL_MODEL_SHOWCASE_FILES.md`
- Micro-context design: `docs/MICRO_CONTEXT_DESIGN.md`
- MemoryStore facade design: `docs/MEMORYSTORE_FACADE_DESIGN.md`
- Internal compression policy tests: `docs/INTERNAL_COMPRESSION_POLICY_TESTS.md`
- SQLite/FTS memory schema design: `docs/SQLITE_FTS_MEMORY_SCHEMA_DESIGN.md`
- Progressive retrieval contract design: `docs/PROGRESSIVE_RETRIEVAL_CONTRACT_DESIGN.md`
- Holdout intake generalization set: `docs/HOLDOUT_INTAKE_GENERALIZATION_SET.md`

Milestone docs remain in `docs/` as historical evidence. Do not treat older milestone docs as current canon when they conflict with the files above.

## Repository Layout

```text
backend/    FastAPI application and backend tests
frontend/   React + Vite + TypeScript app
scripts/    Windows PowerShell startup scripts
docs/       Canonical docs, ADRs, and historical milestone evidence
```

The Git repository location and runtime data root are separate concepts. The repository contains source code. Runtime data defaults to:

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

Open:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

## Recreate Dependencies

Generated dependencies are intentionally not canonical source. Recreate them when needed.

Backend virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
```

Frontend dependencies:

```powershell
cd frontend
npm install
```

Node.js LTS and npm are required for normal frontend use. Install them from:

```text
https://nodejs.org/
```

## Tests

After recreating `backend/.venv`:

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
```

After recreating `frontend/node_modules`:

```powershell
cd frontend
npm run build
```

## Current Next Milestone

Recommended next milestone:

```text
1G-B2-F3-A4-R - Approved local responder adapter audit
```

`1G-B2-F3-A4` adds the first approved localhost-only Ollama responder adapter
for the A3 local-route smoke path. The adapter is injectable as
`Callable[[str], str]`, uses Python standard library HTTP only, rejects
non-localhost endpoints with URL parsing, bounds prompt/output length, and keeps
`build_local_responder` side-effect free.

The library default remains offline-safe: `run_local_route(..., responder=None)`
does not call a model. Real local model execution is available only through
explicit CLI `--run-local`, only after RouterPolicy decision production,
semantic validation, and the A3 safe-local guard pass. Unit tests use fake
clients and do not require Ollama or Gemma. Manual smoke requires Ollama running
and the selected model already pulled locally.

Manual local smoke, optional:

```powershell
python scripts\router_policy_local_route_probe.py --fixture tests\fixtures\router_policy\base_router_policy_fixture.json --run-local
```

A4 does not add external provider routing, tools/browser/terminal/MCP, memory,
retrieval, backend routes, frontend UI, database migrations, or BlueRev
modeling.

Do not start BlueRev modeling, Context Pack Broker runtime, local gatekeeper runtime, memory runtime, retrieval runtime, tool execution, or broad Gemma orchestration before the form/protocol/memory foundation and reliability gates are complete.
