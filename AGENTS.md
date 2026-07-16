# AGENTS.md — Instructions for AI coding agents working on JarvisOS

This file governs AI coding and review agents acting on the JarvisOS repository
and delivery process. It does not directly govern models or agent processes running
inside JarvisOS or Hermes at runtime; those actors are governed by JarvisOS runtime
authority, sensitivity, routing, egress, budget, tool, and promotion policies. This
scope distinction never permits runtime code or models to bypass the deterministic
controls and hard invariants that repository changes must implement.

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
9. **No fabricated results.** Never stub, hard-code, or fake an output — a
   validator verdict, exported geometry, a metric, a test's expected value — to
   satisfy an acceptance criterion or turn CI green. If you cannot implement
   something, stop and report it. An undisclosed placeholder or simplification
   that makes checks pass is treated as a violation of this file, not as
   progress.
10. **Prefer the smallest sufficient change.** Before proposing or implementing a new
    subsystem, automation, parallel source of truth, refactor, or optimization,
    inspect the mechanisms that already exist and state whether a smaller change —
    or no new work — solves the actual need. Do not build or optimize infrastructure
    that is likely to be removed or replaced soon. Broader work requires a concrete,
    demonstrated gap and explicit maintainer confirmation.

If a spec appears to require violating one of these, stop and report instead of
implementing.

## Model economy (intended routing hierarchy)

The target steady state, once redaction and egress-policy flows exist (see
ADR-057 and ADR-059 in `docs/DECISIONS.md`):

- **Cheap external models** (e.g. GLM, Kimi, DeepSeek class) are the workhorse
  for the majority of compute.
- **Frontier models** (Opus / GPT frontier class) are for review, strategic
  documents, and hard tasks.
- **Local models** are the fallback for the rare cases where redaction is
  impossible or ambiguous (fail-closed) — this path must stay rare, not the norm.

Do not read "local-first" as "prefer local models". Hard invariant 1 remains
unchanged: `route_class="auto"` itself never executes an external provider. A
separate server-owned egress policy may allow an explicit external route only
after binding and validating the exact outbound packet through the shared
execution spine. Human confirmation is required only when a configured policy
trigger fires; models, frontend state, and caller-supplied flags never authorize
external execution.

## How work is assigned: spec-driven slices

- Work items live in `docs/specs/NNN-*.md`. Read `docs/specs/STATUS.md` first for
  the only live status/roadmap, then `docs/specs/README.md` and the selected spec.
- Implement **exactly one spec per session/branch**. Do not bundle extra improvements,
  refactors, or drive-by fixes — flag them in your summary instead.
- Each spec defines scope, acceptance criteria, required tests, and non-goals.
  Non-goals are binding.
- If the spec conflicts with the actual code you find, stop and report the conflict;
  do not guess.
- Do not infer live state from legacy `Status:` lines inside individual specs,
  strategy documents, README prose, or chat handoffs. Update `docs/specs/STATUS.md`.

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
| `docs/specs/` | work-item specs, workflow, and canonical `STATUS.md` registry |
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

Automated review output, Codex code review, and any other model-generated review
are **optional and advisory**. They never authorize a merge and are not required
for routine pull requests. Merge authority is, in order:

1. Deterministic gates: CI green, required tests and Ruff passing, and the hard
   invariants in this file intact.
2. Human maintainer decision, optionally informed by a manually requested external
   review for a high-risk or unusually difficult change.

External review workflows are manual-only:

- `Manual Cheap Review` and `Manual Senior Review` run only through
  `workflow_dispatch` from `master` with an explicit PR number.
- `Manual Expert Review` runs only when the maintainer explicitly applies the
  `expert-review` label.
- No review workflow may add or remove tier/readiness labels, invoke or mention
  `@codex`, dispatch another review tier, push changes, or merge.
- `ready-for-merge` is a maintainer-owned informational label, not a model verdict.

Never merge your own PR. Never enable auto-merge. Open the PR against `master`,
fill in the PR template completely, verify the current head and deterministic
gates, and leave the merge decision to the maintainer.

**Model findings are fallible.** A manually requested review is evidence to inspect,
not a command. For each finding, construct the concrete failing input or state,
check the current spec and head, and reproduce it where possible. Fix genuine
defects on the same PR branch. If a finding is false, record a concise rebuttal
backed by a test, reproduction, authoritative source, or precise code path. Never
change correct code merely to satisfy a reviewer.

**Codex is explicit-only.** No workflow sends automatic fix requests. Codex or any
other implementing agent acts only after an explicit maintainer request. A manual
request still does not waive verification: evaluate each finding independently,
respect the current branch and scope, and never merge, force-push, delete branches,
or change secrets without explicit authority.

**Autonomy of the implementing agent.** Within an assigned slice, proceed through
inspection, implementation, tests, CI diagnosis, and evidence collection without
waiting between reversible steps. When there is no active overlapping PR, an agent
may also pick up the lowest-numbered `ready` spec in `docs/specs/STATUS.md` whose
hard dependencies are `merged`, unless the maintainer has set a different priority.
This autonomy stops at external spending, destructive or irreversible actions,
secret changes, workflow dispatches that call paid models, and the merge boundary.

**Maintainer-owned conformance tests:** files matching
`backend/tests/**/test_*_conformance.py` are protected acceptance evidence. An
implementation agent must not add, modify, or delete them unless the maintainer
explicitly assigns that exact change. If one blocks the implementation and appears
wrong, stop and report rather than editing it to turn CI green.

## Definition of done

1. Spec acceptance criteria all met.
2. Required tests added and passing; full backend suite green.
3. Ruff clean on touched files.
4. No new dependency added (if truly unavoidable, add to requirements and call it out
   prominently in your summary).
5. Docs updated only where the spec says so.
6. Summary states: what changed, files touched, test results, anything deferred or
   discovered.
7. `docs/specs/STATUS.md` shows `in_review` with the PR number before review; the
   merge owner changes it to `merged` after merge.

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
- No new frameworks, ORMs, agent libraries, or vector databases unless an accepted
  ADR and an implementation-ready spec explicitly authorize that repository change.
  ADR-060 is direction-lock only; specs 066–068 must authorize any Hermes dependency
  or integration, and ADR-060 alone does not activate Hermes or install dependencies.
- No touching `backend/.venv`, `frontend/node_modules`, `reports/` history, or
  anything under the data root.
- No expanding `tools/` or `agents/` skeletons, no MCP servers, no background
  workers, no streaming — unless a spec explicitly asks.
- No speculative features "while you're in there".
