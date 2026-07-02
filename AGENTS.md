# AGENTS.md — Instructions for AI coding agents working on JarvisOS

JarvisOS is a single-user AI engineering workspace, local-first in state and
policy: backend (FastAPI + SQLite) owns state, policy, execution, and audit.
Frontend (React/Vite) is an operator interface. AI models propose; JarvisOS
validates, gates, records, and audits. Model routing is cost-aware and
predominantly external (see "Model economy" below); "local-first" describes
where authority and data live, not which models do the work.

## Hard invariants — never violate, never "temporarily" bypass

1. **Auto never executes external providers.** `route_class="auto"` may only execute
   local routes. External intent returns a non-executing proposal/control state.
2. **All AI calls go through the execution spine** (`run_ai_task`) and write a row to
   `ai_jobs`. No direct provider calls from routes, frontend, services, or tools.
3. **The frontend never calls providers, Ollama, the filesystem, or execution tools
   directly.** It only calls backend APIs.
4. **Safe defaults stay safe:** paid AI disabled, budget zero, provider mode `fake`,
   `route_class=None` resolves to `local:fake`. Tests use fake/mocked providers only.
5. **The local classifier is advisory.** It never owns permissions, provider selection,
   external calls, memory writes, or final sensitivity. Deterministic policy decides.
6. **No secrets** in logs, events, docs, test fixtures, commits, or frontend responses.
7. **Data-root paths** (`C:\JarvisOS`) go through `backend/app/core/paths.py`. The repo
   and the data root are separate; never write runtime data into the repo.
8. **AI/agent outputs are proposals.** Nothing model-generated becomes a canonical
   record without explicit user or deterministic-policy promotion.

If a spec appears to require violating one of these, stop and report instead of
implementing.

## Model economy (intended routing hierarchy)

The target steady state, once redaction and confirm flows exist (see ADR-057 in
`docs/DECISIONS.md`):

- **Cheap external models** (e.g. GLM, Kimi, DeepSeek class) are the workhorse
  for the majority of compute.
- **Frontier models** (Opus / GPT frontier class) are for review, strategic
  documents, and hard tasks.
- **Local models** are the fallback for the rare cases where redaction is
  impossible or ambiguous (fail-closed) — this path must stay rare, not the norm.

Do not read "local-first" as "prefer local models". The hard invariants above
still apply unchanged: external execution is gated by explicit user confirmation
and deterministic policy, regardless of how common it is.

## How work is assigned: spec-driven slices

- Work items live in `docs/specs/NNN-*.md`. Read `docs/specs/README.md` first.
- Implement **exactly one spec per session/branch**. Do not bundle extra improvements,
  refactors, or drive-by fixes — flag them in your summary instead.
- Each spec defines scope, acceptance criteria, required tests, and non-goals.
  Non-goals are binding.
- If the spec conflicts with the actual code you find, stop and report the conflict;
  do not guess.

## Repo map

| Path | Contents |
| --- | --- |
| `backend/app/core/` | config, paths, database, schema, logging, errors |
| `backend/app/modules/ai/` | execution spine, gateway, providers, routing, context builder |
| `backend/app/modules/ai/routing/` | RouterPolicy producer, Auto bridge, capability matrix |
| `backend/app/modules/local_ai/` | local classifier and local runtime support |
| `backend/app/modules/local_ai_eval/` | local model evaluation harness |
| `backend/app/modules/modeling/` | model specs, versions, simulation runs |
| `backend/app/modules/runner/` | bounded local Python runner |
| `backend/app/modules/engineering/`, `workspaces/`, `events/`, `files/` | domain foundation |
| `backend/app/modules/tools/`, `agents/` | registry skeletons only — do not expand without a spec |
| `backend/tests/` | pytest suite |
| `frontend/` | React/Vite operator UI |
| `docs/` | canonical docs; `docs/ARCHITECTURE.md` and `docs/DECISIONS.md` win conflicts |
| `docs/specs/` | work-item specs for agents |
| `reports/` | generated evaluation/smoke reports |

## Environments

This repo is developed in two environments. Detect which one you are in and use
the matching commands.

| | Local (maintainer) | Cloud container / CI (Codex cloud, GitHub Actions) |
| --- | --- | --- |
| OS | Windows 11, PowerShell | Linux |
| Python env | `backend/.venv` | system Python 3.11+, `pip install -r backend/requirements.txt -r backend/requirements-dev.txt` |
| Data root | `C:\JarvisOS` | none — tests isolate it automatically |

Cross-platform rules:
- Tests already isolate the data root via the `JARVISOS_DATA_ROOT` env var and
  `tmp_path` (see `backend/tests/conftest.py`). Never write a test that depends on
  `C:\JarvisOS`, drive letters, backslash paths, or a running Ollama/provider.
- Use `pathlib` for any new path handling; never hardcode OS-specific separators.
- Do not modify launcher scripts (`*.cmd`, `scripts/*.ps1`) from a Linux
  environment — you cannot test them there.

## Test gate (must pass before you consider work done)

From `backend/`, any OS (use `.\.venv\Scripts\python` instead of `python` on
local Windows):

```bash
python -m pytest -q
python -m ruff check app tests
```

If frontend files changed:

```bash
cd frontend
npm run build
```

Notes:
- The full backend suite must pass (baseline is green). If a failure looks unrelated
  to your change, report it; do not silence or skip tests.
- If broad ruff reports pre-existing issues outside your files, scope to the files you
  touched and note this in your summary.
- Tests must run offline. Never add a test that requires a live provider, network, or
  a running Ollama instance; use the fake provider and fixtures.

## Review authority

Automated review output (Codex code review, or any model-generated review) is
**advisory**. It never authorizes a merge by itself. Merge authority is, in order:

1. Deterministic gates: CI green (pytest + ruff), invariants in this file intact.
2. Human maintainer decision, informed by Claude review of the diff against the
   spec.

Review is tiered by cost (see ADR-057): a cheap external model reviews every
push and drives the fix iteration loop with the implementing agent; the frontier
(Claude) review runs once, on the stabilized diff, before merge. The cheap
tier's "no further changes" verdict is a *trigger* for the frontier review,
never an approval — it carries no merge authority.

Never merge your own PR. Never enable auto-merge. Open the PR against `master`
and stop; fill in the PR template completely.

## Definition of done

1. Spec acceptance criteria all met.
2. Required tests added and passing; full backend suite green.
3. Ruff clean on touched files.
4. No new dependency added (if truly unavoidable, add to requirements and call it out
   prominently in your summary).
5. Docs updated only where the spec says so.
6. Summary states: what changed, files touched, test results, anything deferred or
   discovered.

## Conventions

- Python: match existing style; type hints on new code; small pure functions where
  reasonable. English for all code, comments, docs, and commit messages.
- Follow existing module patterns (service/routes/models split) instead of inventing
  new layouts.
- SQLite schema changes: additive columns with safe defaults, following the existing
  pattern in `backend/app/core/schema.py`; bump the relevant schema version field.
  No Alembic.
- Commit messages: short imperative subject, one commit per logical change.

## What NOT to do

- No broad refactors, renames, or file moves unless the spec says so.
- No new design docs, README rewrites, or roadmap edits.
- No new frameworks, ORMs, agent libraries, or vector databases.
- No touching `backend/.venv`, `frontend/node_modules`, `reports/` history, or
  anything under the data root.
- No expanding `tools/` or `agents/` skeletons, no MCP servers, no background
  workers, no streaming — unless a spec explicitly asks.
- No speculative features "while you're in there".
