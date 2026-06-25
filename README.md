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
1G-B2-F3-C1-R - Dev Message Route Endpoint Smoke Audit
```

`1G-B2-F3-B3` makes the existing offline B1 Phase B RouterHint bridge default-on
in the A5 real-message smoke path.

The integration order is:

```text
message
-> A5 smoke builder / Phase A overlay / A5-R1 operational gates
-> optional B1 Phase B RouterHint bridge
-> RouterPolicy decision
-> semantic validator
-> A3 safe-local guard
-> local responder only if safe
```

B3 changes only the default advisory plumbing. `--use-phase-b-hints` remains a
backward-compatible alias for default-on behavior, and `--no-phase-b-hints`
disables Phase B hints for baseline/debug smoke comparisons.

Default Phase B hints do not make messages executable. Benign local answer
smoke still requires `--assume-public-simple`, and real local responder
construction still requires `--run-local`. The A5 Phase B stub remains a smoke
placeholder, not live Qwen/Gemma/Ollama classification or a production Phase
A/B normalizer.

Manual local smoke, optional and local-only:

```powershell
python scripts\router_policy_message_route_smoke.py --message "Explain what a pump is" --assume-public-simple --run-local
```

B3 does not weaken B1 quality checks or A5/A3 authority. Phase A hard gates and
A5-R1 operational-intent gates dominate Phase B hints. A3 safe-local guard
remains final authority before a local responder receives only
`input_obj["message_text"]`.

B3 does not add production chat, external providers, non-localhost network
calls, tools, browser/terminal/MCP execution, memory, retrieval, file-write
runtime, backend routes, frontend UI, database migrations, live Qwen/Gemma/
Ollama classification, or BlueRev modeling. B3 does not remove
`--assume-public-simple`.

`1G-B2-F3-B3-R1` adds a pre-bridge structural validation boundary so malformed
safety-critical builder output is rejected before B1 can normalize it. B1/A5
must not mutate original malformed inputs in-place, malformed inputs must not
reach `_RUN_LOCAL_ROUTE`, and malformed inputs must not execute.

The pre/post validation boundary is part of the smoke contract: pre-B1
validation proves builder output is structurally valid enough for B1, B1 remains
advisory, and post-B1 validation checks enriched structure before RouterPolicy
and A3. Future live Phase B output must be adapted and validated before B1; B1
must not normalize arbitrary raw model output or authorize execution.

`1G-B2-F3-B4` adds an explicit offline panel path that replaces the fixed
benign Phase B stub with deterministic per-message Phase B soft-review output
from `local_phase_b_soft_review_probe.build_soft_review`. The default B3 stub
path remains unchanged. B4 adds no live model call and commits only synthetic or
sanitized report messages.

`1G-B2-F3-B4-live` adds an explicit gated local-only Qwen Phase B soft-review
smoke path. Qwen can produce advisory Phase B soft proposals only; deterministic
Phase A gates, B1 validation/clamp/leakage checks, RouterPolicy, and A3 remain
authority. The default stub path and deterministic B4 path remain unchanged.
This does not approve production chat/UI, memory, retrieval, provider routing,
tool execution, or removal of `--assume-public-simple`.

Manual Phase B live smoke, optional and local-only:

```powershell
python scripts\router_policy_message_route_smoke.py --message "Explain what a centrifugal pump is." --assume-public-simple --use-phase-b-hints --phase-b-source live-local-qwen --phase-b-source-case-id B4-LIVE-BENIGN --run-local-phase-b --phase-b-model qwen3:8b --phase-b-endpoint http://localhost:11434
```

B4-live-R1 fixes the live Phase B seam provenance boundary so `phase_a_case_id`
is added only after live proposal validation and leakage checks.

`1G-B2-F3-C1` adds a dev-only backend endpoint for message-route smoke testing:
`POST /api/dev/message-route-smoke`. It reuses the existing RouterPolicy/A3/A4
path, keeps `assume_public_simple` server-side and dev-gated, rejects
unsupported client fields, projects responses through `_safe_cli_result`, and
does not approve production chat, frontend UI, memory, retrieval, provider
routing, tools, MCP, browser/terminal execution, live Qwen Phase B exposure, or
BlueRev runtime behavior.

`1G-B2-F3-C1-R1` moves validation for the dev message-route endpoint behind the
dev gate, so schema-invalid requests do not bypass the disabled boundary or
return raw validation input. It also preserves a single route-generated
`trace_id` across disabled, validation, normal, and internal-error paths.

Do not start BlueRev modeling, Context Pack Broker runtime, local gatekeeper runtime, memory runtime, retrieval runtime, tool execution, or broad Gemma orchestration before the form/protocol/memory foundation and reliability gates are complete.
