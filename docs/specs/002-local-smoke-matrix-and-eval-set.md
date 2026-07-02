# 002 — Local route smoke matrix + routing eval set

Status: ready
Depends on: none

## Goal

Two measurement assets exist: (a) a repeatable script that measures real latency,
model load/swap cost, and output sanity for every local route on this machine,
writing a report to `reports/`; (b) a versioned routing eval set of ~30 labeled
prompts that can score the Auto classifier + capability matrix offline-style.

## Why

Routing, context budgets, and the capability matrix are currently unvalidated
guesses. Every future decision (route stickiness, whether `local:coder_heavy` is
usable, matrix tuning, adaptive routing) is blocked on these measurements. Cost on
this hardware is latency and VRAM swap, not only money. (Strategy reference:
`docs/strategy/JARVISOS_AI_ROUTING_AND_MODEL_ECONOMY.md`.)

## Scope

In scope:
- A manual smoke script (invoked explicitly, never in CI) that exercises each real
  local route (`local:fast`, `local:general`, `local:coder`, `local:coder_heavy`)
  through the normal execution spine (`run_ai_task`), NOT through direct Ollama calls.
- Per route: N=3 fixed short prompts, measuring cold-start (model not loaded) vs
  warm latency where detectable, total wall time, and reported token usage. Record a
  swap sequence too: fast → general → fast, to measure reload cost.
- Report output: JSON + human-readable markdown summary under
  `reports/local_route_smoke/<YYYY-MM-DD>/`.
- A routing eval set file: ~30 prompts with expected labels (`capability` row and
  `context_level`), stored under `backend/app/modules/local_ai_eval/` fixtures or
  `configs/` — follow where existing eval fixtures live.
- A manual eval script that runs the Auto classifier + capability matrix over the
  eval set and reports agreement per label, using the same report output pattern.
- Prompts must be synthetic/generic engineering prompts — no project-sensitive
  content in the eval set (it may reach cloud models someday).

Out of scope (binding non-goals):
- No CI/pytest tests that require Ollama or any live model (the scripts are manual
  gates; unit-test only the pure helpers, e.g. report formatting, label comparison).
- No changes to routing behavior, capability matrix, context budgets, or bindings —
  this slice measures, it does not tune.
- No frontend.
- No background scheduling.

## Files likely touched

- `backend/app/modules/local_ai_eval/` (extend existing harness patterns — inspect
  what exists; `local_eval_reports/` and `reports/local_model_smoke/` show prior art)
- `scripts/` (thin PowerShell or Python entry point, matching existing script style)
- New fixture file for the eval set
- `backend/tests/` (offline unit tests for pure helpers only)

## Design constraints

- All model calls go through the execution spine so `ai_jobs` rows are written —
  the ledger is part of the measurement.
- Script must fail gracefully (clear message, nonzero exit) when Ollama is not
  running or a model is missing; never auto-pull models.
- Eval set format: one JSON/JSONL file, each entry: `id`, `prompt`,
  `expected_capability`, `expected_context_level`, optional `notes`. Keep it
  hand-editable.
- Report must include: machine timestamp, model list actually resolved per route,
  per-prompt timings, and a summary table.

## Acceptance criteria

1. Running the smoke script with Ollama up produces the JSON + markdown report with
   per-route timings and the swap-cost measurement.
2. Running it with Ollama down produces a clear failure, no partial garbage report.
3. The eval set file exists with ≥30 entries covering all capability rows (including
   several intended `deep_reasoning` cases) and all four context levels.
4. The eval script produces an agreement report (per-label accuracy + confusion
   listing of mismatches).
5. `ai_jobs` receives ledger rows for smoke executions (verifiable in the report via
   ledger ids).
6. Full backend suite still green; no test depends on live models.

## Required tests

- Unit tests for report formatting and eval-agreement computation with fixture data
  (no model calls).

## Definition of done

Test gate green (see `AGENTS.md`), acceptance criteria met, spec status updated,
summary written. The maintainer runs both scripts manually once and commits the
first real report.
