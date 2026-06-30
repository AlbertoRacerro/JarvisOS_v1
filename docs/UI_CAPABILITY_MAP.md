# UI Capability Map (UI-MAP-1)

Inspection-only map of backend capabilities vs current UI exposure, to guide a
later UI redesign. No code changes in this slice.

Source of truth at time of writing: HEAD `ff9cef5` (POS-2B).
Backend routers registered in `backend/app/main.py`; frontend calls in
`frontend/src/api/client.ts`; UI lives almost entirely in
`frontend/src/pages/AIDraft.tsx`.

## Capability table

| Endpoint | Purpose | UI today | Proposed visibility | Writes | Provider | Ledger |
|---|---|---|---|---|---|---|
| `POST /ai/tasks/run` | real AI task (positive spine) | AIDraft "AI Task" | primary | ai_jobs | yes (explicit cloud) | yes |
| `GET/PUT /ai/settings`, `GET /ai/status` | AI config/status | AIDraft | settings | yes | no | no |
| `GET/POST/DELETE /secrets/scaleway/*` | key presence/set/remove | AIDraft | settings | yes | no | no |
| `POST /ai/modeling/draft` | model draft (fake) | AIDraft | advanced | no | fake | event |
| `POST /ai/smoke-tests/run` | synthetic smoke | AIDraft | diagnostics | no | smoke | no |
| `POST /ai/smoke-console/run` | smoke console | AIDraft | diagnostics | no | smoke | no |
| `POST /ai/provider-smoke/run` | provider smoke | NOT in UI | diagnostics | no | smoke | no |
| `POST /ai/supervisor/public-test` | supervisor test | NOT in UI | diagnostics | no | smoke | no |
| `GET/POST /workspaces`, `GET /workspaces/{id}` | workspace | partial | primary (selector) | yes | no | no |
| modeling CRUD: model-specs / assumptions / parameters / decisions / simulation-runs | project data | scattered/partial | primary (Project KB) | yes | no | no |
| runner: model-implementations / runner-jobs / run / logs / artifacts | local script execution | NONE in UI | advanced/backend | yes | no (local) | no |
| `GET /engineering/boundary`, `GET /system/info`, `POST /system/initialize`, `GET /health` | meta/diagnostics | partial | diagnostics | (initialize: yes) | no | no |

## Real gaps (evidence-based)

1. **No `ai_jobs` read endpoint.** The ledger is written but never read (no
   `GET /ai/jobs`). The future "Ledger/Runs" page cannot exist until this is
   added. Today the only way to inspect history is SQL on `C:\JarvisOS\jarvisos.db`.
2. **Runner has no UI at all.** model-implementations / runner-jobs / logs /
   artifacts are not in the frontend client. A whole capability is invisible.
3. **`AITaskRunResponse` does not expose context info.** No
   `include_project_context`, `workspace_id`, `context_digest`, or
   `context_sources_count`. From the UI you cannot tell whether/what context was
   used without querying SQL.
4. **Smoke partially exposed.** `smoke-tests` and `smoke-console` are in AIDraft;
   `provider-smoke` and `supervisor/public-test` exist but are not in the UI. A
   Diagnostics page should absorb the existing smoke panels, not invent new ones.

## Proposed UX grouping (pages)

- **Project Knowledge Base** — workspace selector + model-specs / assumptions /
  parameters (with units) / decisions / simulation-runs. The data that feeds AI
  context. *Primary.*
- **AI Task** — prompt, route/mode, context toggle, **visible context summary**
  (needs gap #3), response, ledger_id, usage. *Primary.*
- **Ledger / Runs** — filterable `ai_jobs` history. *Blocked by gap #1.*
- **Diagnostics / Dev** — absorbs smoke-tests/console/provider-smoke/supervisor +
  modeling-draft (+ optional runner). *Hidden by default.*
- **Settings / Providers** — AI settings, key presence (never the value), route
  bindings, budget guard.

## Recommended phasing

The map shows the UI redesign does not start with CSS — it starts with two small
backend gaps, without which two of the five pages cannot exist:

1. **OBS-1** (micro, high value): add context fields to `AITaskRunResponse`
   (`include_project_context`, `workspace_id`, `context_digest`,
   `context_sources_count`) so the AI Task panel is honest about context without
   SQL. Touches response model + gateway + a new field on the execution outcome +
   UI render. No provider, no schema change.
2. **LEDGER-READ-1**: `GET /ai/jobs` (read-only, paginated, redacted) to unblock
   the Ledger/Runs page.
3. **Only then** the visual UI redesign (page grouping).

Out of scope here: POS-3 grading, new providers, retrieval/vector, runner UI,
legacy smoke refactor, schema changes.
