# 088 — RUNS-WORKBENCH-1

Status: definition-complete; `docs/specs/STATUS.md` is authoritative.

Depends on: 038, 044, 083

Related merged foundations: 001, 040, 042, 047, 048, 049, 050, 051, 070, 075, 076, 077, 079, 087

## Goal

Replace the `/runs` migration placeholder with a real, read-first run workbench backed by the simulation-run and runner evidence that JarvisOS already persists.

088 lets the operator answer, without inventing execution truth:

- what runs exist in the selected workspace;
- which run is selected and what persisted lifecycle status it has;
- which model version, label and timestamps the persisted run actually records;
- what persisted input, parameter and output payloads belong to that run;
- which runner logs and artifacts exist for that run;
- whether a run is incomplete, failed, timed out or otherwise terminal according to stored state;
- which information is unavailable because the record is sparse, old, malformed, or has no runner evidence.

088 is an inspection surface. It does not create, queue, rerun, cancel, delete, retry, compare, promote, grade, recompute, edit inputs, infer progress, calculate analytics, or manufacture engineering conclusions.

## Product boundary

`/runs` is already a first-class 083 production route and primary-navigation item. 088 replaces only its `MigrationPendingSurface`; it does not turn Runs into a Design sub-stage and does not rename the existing `Results` design stage.

The minimum workstation composition is:

- one compact workspace control using the shell-owned workspace state;
- a bounded run list/filter pane;
- a dominant selected-run detail surface;
- compact tabs/disclosures for persisted inputs, parameters, outputs, logs and artifacts as evidence exists;
- no permanent telemetry dock and no fake progress strip.

The visual direction follows the maintainer-approved engineering-workstation hierarchy already used by 083/085/087: dense and desktop-first, light/off-white surfaces, natural leaf-green accent used selectively, thin separators and minimal shadows. 088 does not own global font, palette, radius, iconography, motion, component grammar or other visual-identity tokens.

## Existing runtime authority

088 consumes existing backend contracts. Runtime models and persistence win over historical documentation if they differ.

### Run list

```http
GET /workspaces/{workspace_id}/simulation-runs
```

Authority: `backend/app/modules/modeling/routes.py` and `SimulationRunRead` in `backend/app/modules/modeling/models.py`.

The current response carries, per run:

- `id`;
- `workspace_id`;
- nullable `model_version_id`;
- nullable `run_label`;
- persisted `status` as a string;
- nullable `input_payload`;
- nullable `parameter_payload`;
- nullable `output_payload`;
- nullable `started_at`;
- nullable `completed_at`;
- `created_at`;
- nullable `notes`.

The frontend must not narrow the persisted status to a closed enum because the modeling contract intentionally exposes a string and historical/manual rows may use statuses outside the runner's current execution enum.

### Run detail

```http
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}
```

Authority: runner route `get_simulation_run_endpoint` and `SimulationRunDetail` in `backend/app/modules/runner/models.py`.

This is workspace-scoped and returns the canonical persisted run record. The list row is useful for navigation, but the selected detail must be loaded from this endpoint rather than assuming the list copy remains current.

### Logs

```http
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/logs
```

Authority: `RunLogRead`.

Fields include stream, content, truncation flag and creation time. An empty list is a valid state and is distinct from a request failure.

### Artifacts

```http
GET /workspaces/{workspace_id}/simulation-runs/{simulation_run_id}/artifacts
```

Authority: `RunArtifactRead`.

The UI may render bounded operator-safe metadata such as filename, role, artifact type, size, MIME type, digest, status, source reference/module and creation time. It must not render `stored_path`, and should not expose filesystem-oriented path fields merely because the API returns them. Artifact download/open behavior is outside 088 unless an already-existing safe artifact-serving URL is proven during readiness and can be reused without expanding authority.

### Workspaces

```http
GET /workspaces
```

Reuse the existing workspace discovery contract. `App` remains the single owner of the transient selected workspace introduced for 087. Runs receives that state and `onWorkspaceChange`; it must not create a second durable or page-local workspace authority.

## No backend expansion by default

Current runtime already provides workspace-scoped run list, detail, logs and artifact reads. Therefore the default 088 implementation is frontend-only.

Do not add:

- a run-summary endpoint;
- a dashboard aggregation endpoint;
- polling infrastructure;
- websockets/SSE;
- a run search endpoint;
- a new state store or cache;
- a schema migration;
- new runner lifecycle mutations.

Readiness may authorize a narrower backend change only if exact current code proves one acceptance criterion cannot be satisfied through the existing contracts. Such a change requires the minimum-necessary test and must not be hidden inside implementation.

## Frontend read contracts

Add strict TypeScript models for the exact runtime responses rather than reusing the current legacy `SimulationRun` type, which intentionally exposes only a small subset of fields.

Illustrative minimum shapes:

```ts
type SimulationRunSummary = {
  id: string;
  workspace_id: string;
  model_version_id: string | null;
  run_label: string | null;
  status: string;
  input_payload: string | null;
  parameter_payload: string | null;
  output_payload: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  notes: string | null;
};

type SimulationRunDetail = SimulationRunSummary;

type RunLog = {
  id: string;
  workspace_id: string;
  simulation_run_id: string;
  stream: string;
  content: string;
  truncated: boolean;
  created_at: string;
};

type RunArtifact = {
  artifact_id: string;
  workspace_id: string;
  simulation_run_id: string;
  role: string;
  artifact_type: string;
  filename: string;
  size_bytes: number | null;
  created_at: string;
  source_ref: string | null;
  source_module: string | null;
  mime_type: string | null;
  sha256: string | null;
  status: string;
  under_data_root: boolean;
};
```

If merged backend models differ at implementation time, derive the TypeScript contract from the exact runtime model. Do not broaden stable fields to untyped `unknown` merely to make parsing easier.

Keep the legacy Domain Foundation client behavior intact. A dedicated `runs` client/module is preferred if adding full detail/log/artifact types to the legacy monolithic client would widen unrelated migration scope.

## State ownership and request races

`App` remains owner of `workspaceId`. The Runs workbench owns only run-local read/presentation state:

- workspace discovery load state when needed for the selector;
- run-list load state;
- selected run id or null;
- selected detail load state;
- selected logs load state;
- selected artifacts load state;
- bounded search/status filter state;
- bounded local disclosure/tab state.

Every asynchronous response must be guarded against stale completion.

Required race cases:

- workspace A → B → A while any run request is in flight;
- run X → Y → X while detail/log/artifact requests are in flight;
- list refresh while the selected run disappears;
- a late failed request from an old workspace/run must not replace the current success state with an error.

A generation/request token or equivalent deterministic context check must include the initiating workspace and selected run as appropriate. Comparing only React values captured before `await` is not sufficient for A → B → A races.

Changing workspace synchronously clears the prior workspace's run list, selection, detail, logs and artifacts before loading the new workspace.

## Run list and selection

The list is deterministic and read-only.

Default ordering:

1. newest `created_at` first;
2. stable `id` tie-break.

The frontend may provide:

- case-insensitive search over already-returned run label and id;
- exact persisted-status filter;
- a compact `All statuses` reset.

No backend search or analytics endpoint is needed.

Each row must expose at least:

- label, falling back to a bounded run-id presentation;
- exact persisted status text;
- created time;
- started/completed time only when present.

Status must not be communicated by colour alone. Unknown status strings remain visible verbatim and receive a neutral visual treatment rather than being coerced into success/failure.

Selection rules:

- when a successful list has rows and no valid selection exists, select the first deterministic row;
- after refresh, preserve the selected id if it still exists;
- if the selected run disappears, select the first remaining visible run or null when none remain;
- filtering may hide a selected run, but detail must not silently display an item that the operator cannot locate. The implementation should either preserve it with an explicit `selected run hidden by filter` state or deterministically move to the first visible row; readiness must choose one rule and test focus recovery.

## Selected-run detail

The central detail surface distinguishes persisted lifecycle status from the availability of evidence.

Header metadata may show:

- label/id;
- exact persisted status;
- model version id when present;
- created, started and completed timestamps when present;
- notes when present.

Do not infer duration if timestamps are malformed or missing. A simple duration derived from valid `started_at` and `completed_at` may be allowed during readiness only if it is explicitly labelled as derived and does not become analytics infrastructure.

The following are forbidden:

- fake percent complete;
- fake ETA;
- synthetic health/confidence/severity scores;
- treating `created_at` as `started_at`;
- treating a missing `completed_at` as `running`;
- turning missing logs/artifacts into a failure status;
- guessing model names from ids;
- claiming freshness unless an authoritative freshness contract is explicitly joined by a later spec.

## Input, parameter and output payloads

The persisted payload columns are strings and can contain JSON. They are authoritative historical evidence, but raw arbitrary payload dumps are not an acceptable default UI.

088 may parse a payload as JSON only when parsing succeeds. Render it through a bounded, non-editable structured viewer with limits chosen during readiness for:

- nesting depth;
- object/array item count;
- rendered string length;
- total rendered characters.

The viewer must preserve keys/values within those limits and visibly state when presentation is truncated. It must not execute HTML, Markdown, links, code, expressions or scripts from payload content.

If JSON parsing fails, present `Payload unavailable / malformed` plus a bounded diagnostic that does not dump the entire raw payload. The raw persisted string remains backend authority; 088 does not rewrite or repair it.

Input, parameter and output sections are semantically separate. Do not infer units, requirements, pass/fail, comparisons or analytics from values. Those responsibilities belong to later Engineering Data/Analytics slices.

A null payload is a normal `No persisted … payload` state, not an error.

## Logs

Logs are subordinate evidence, not the primary run state.

Requirements:

- preserve backend order or deterministically sort by `created_at` then `id` if runtime order is not contractual;
- identify stream textually;
- expose the backend `truncated` flag explicitly;
- constrain long lines/tokens without causing page-level horizontal overflow;
- render content as inert text only;
- provide an empty state when no logs exist;
- retain detail if the logs request fails and show a logs-only error with retry.

No live tailing, polling, ANSI execution, search indexing or download feature is required in 088.

## Artifacts

Artifacts are run evidence. The panel lists only metadata returned by the authoritative endpoint and safe for normal operator display.

At minimum:

- filename;
- role/type;
- status;
- size when present;
- MIME type when present;
- SHA-256 when present, with long-token containment;
- source ref/module when present;
- creation time;
- an explicit indication when `under_data_root` is false, without revealing filesystem location.

Do not render `stored_path`. Do not turn `relative_path` into an actionable filesystem link. Do not infer that artifact `status` means the run succeeded.

If safe artifact serving already exists and readiness proves exact workspace/run authorization, adding a normal application link may be considered; otherwise defer opening/downloading artifacts instead of inventing a route.

## Workspace behavior

Runs uses the same shell-owned workspace context as 087.

On first entry:

- if `workspaceId` is still valid, preserve it;
- otherwise choose the first returned workspace deterministically;
- no workspace is a valid empty state;
- workspace discovery failure is distinct from `no workspaces`.

Changing workspace through Runs updates the App-owned workspace id so later workspace-aware surfaces see the same transient context. No localStorage, URL persistence, context provider or new global store is introduced by 088.

## Loading, empty, error and sparse-record states

The workbench must distinguish at least:

1. workspace discovery loading;
2. workspace discovery failure;
3. no workspaces;
4. run-list loading;
5. run-list failure;
6. successful empty run list;
7. selected-detail loading;
8. selected run disappeared / 404 after list load;
9. selected-detail failure;
10. no logs;
11. logs failure;
12. no artifacts;
13. artifacts failure;
14. null input/parameter/output payload;
15. malformed payload;
16. known incomplete/failed/timed-out persisted status;
17. unknown persisted status.

A failure in logs or artifacts must not erase a valid selected-run detail. A detail failure must not erase the run list. A list failure must not retain another workspace's list.

Retry actions repeat only the failed read and respect the same stale-response guards.

## Accessibility and responsive behavior

088 preserves 070/083 accessibility and containment contracts.

Required behavior:

- all run selection is keyboard operable with native controls;
- visible focus in system/light/dark appearances;
- selected row/state is not colour-only;
- status is textual;
- section/tab/disclosure controls have accessible names and state;
- after filtering/refresh removes the focused selected row, focus moves predictably to the replacement selection or a stable list heading/control;
- long ids, digests, log lines, payload strings and filenames wrap or scroll only inside their bounded technical region;
- no page-level horizontal overflow at compact desktop or effective 200% zoom;
- reduced-motion preference remains respected;
- no focus trap is introduced.

The desktop workstation can collapse/reflow the run-list/detail composition at compact widths, but must preserve access to list, detail and retry controls without hiding them behind pointer-only interaction.

## Legacy continuity

The legacy Domain Foundation currently exposes run/scenario creation and basic run rows. 088 does not remove or rewrite those controls.

`/runs` becomes the canonical read/inspection surface. The legacy diagnostic route remains available for existing creation/scenario workflows until their owning future slices migrate them.

Do not copy scenario execution forms into 088 merely to make the page appear complete.

## Downstream contracts

088 deliberately establishes only the run read/inspection boundary needed by later Phase-3 work.

### Re-derived 035 — Engineering Data

035 may link engineering parameters/records to persisted run ids and back to `/runs`, but 088 does not pre-build engineering-record search, unit conversion or record mutation.

### 089 — Analytics Dock

089 may derive widgets from authoritative run/result data. 088 does not create aggregate metrics, chart abstractions or an analytics data store in anticipation.

### 054 / 090 / 091

Review and Jarvis surfaces may later cite runs as evidence/context. 088 provides a stable operator-readable run identity and evidence surface; it does not add proposal, AI or thread behavior.

## Likely implementation boundary

Readiness must confirm exact current paths before authorizing runtime. The expected minimum is frontend-only and approximately:

- `frontend/src/App.tsx` — replace the `/runs` placeholder and pass the existing workspace seam;
- `frontend/src/pages/RunsWorkbench.tsx` — run workbench owner/composition;
- `frontend/src/api/runs.ts` — strict read models and run/detail/log/artifact clients, if a dedicated module remains the smallest boundary;
- one bounded run-workbench stylesheet, or existing shell/component styles if adding selectors there is smaller and clearer;
- `scripts/check_runs_workbench.py` — dependency-free conformance checker;
- `docs/specs/STATUS.md` only during implementation lifecycle transitions.

If deterministic payload/race helpers benefit from isolated testing, one small helper/harness file is allowed. Do not create a generalized frontend data layer, state framework, table framework or test framework.

Existing 083/087 preservation checkers may need a narrowly scoped merged-preservation reconciliation only if their active-implementation path gates reject legitimate 088 paths. Such a checker change must preserve all runtime assertions and must be documented in readiness before implementation.

## Required deterministic evidence

Readiness freezes the exact command set. At minimum, implementation must prove on one unchanged exact remote head:

```bash
python scripts/check_spec_status.py --self-test
python scripts/check_ui_foundation.py
python scripts/check_app_shell.py
python scripts/check_runs_workbench.py --self-test
python scripts/check_runs_workbench.py
cd frontend && npm ci && npm run build
```

Also run every inherited checker whose merged-preservation contract covers touched shell/workspace seams, including 087 if `App` workspace ownership is modified.

Repository CI and BLUECAD Real Tool Proof must remain green on the exact implementation head.

### Browser proof

Use isolated real FastAPI/SQLite state or a deterministic fixture that exercises the real client contracts. The frozen matrix must include at least:

1. workspace with multiple runs, including succeeded and failed/incomplete status;
2. deterministic list selection and refresh preservation;
3. workspace A → B → A late-response race;
4. run X → Y → X late detail/log/artifact race;
5. valid persisted input/parameter/output payload rendering;
6. null and malformed payload states;
7. logs empty/failure/truncated states;
8. artifacts empty/failure, safe metadata and no filesystem path disclosure;
9. selected run disappearing between list and detail;
10. long ids/digests/log text at compact desktop/effective 200% width with no page-level horizontal overflow;
11. keyboard selection, visible focus and focus recovery after filter/refresh;
12. unknown status rendered neutrally and textually;
13. no uncaught browser errors.

No live external provider call is permitted by evidence.

## Acceptance criteria

088 is complete only when all are true:

1. `/runs` renders the native run workbench instead of the migration placeholder.
2. The workbench uses the App-owned workspace state and existing workspace discovery; no second durable workspace authority exists.
3. Real workspace-scoped simulation runs load from the existing list endpoint with explicit loading/failure/empty states.
4. Selection is deterministic, keyboard-operable and safe across refresh/filter/disappearance.
5. Selected run detail is loaded from the authoritative workspace-scoped detail endpoint and stale completions cannot overwrite current context.
6. Persisted lifecycle status is displayed verbatim/textually; unknown values remain neutral; no progress/ETA/health/confidence is fabricated.
7. Persisted input, parameter and output payloads are rendered as bounded inert evidence, with separate null/malformed/truncated states and no inferred engineering meaning.
8. Logs load independently, show truncation explicitly, remain inert text and cannot create page-level overflow.
9. Artifact metadata loads independently; filesystem paths are not rendered and no unsafe open/download path is invented.
10. Log/artifact failures do not erase valid run detail; detail failure does not erase run navigation; workspace/list failure does not retain stale cross-workspace data.
11. A → B → A workspace and X → Y → X run races are deterministically covered.
12. Compact desktop/effective 200% zoom, keyboard focus, non-colour status semantics, reduced motion and no global horizontal overflow are proven.
13. Legacy Domain Foundation run/scenario controls remain reachable and behavior-preserved.
14. No backend/schema/migration/dependency/provider/credential/budget/egress/global visual-identity change is introduced unless separately justified and frozen by readiness.
15. Required exact-head checker/build/CI/proof/browser evidence is green with no material unresolved review finding.

## Non-goals

088 does not implement:

- run creation or scenario execution migration;
- rerun/retry/cancel/delete controls;
- live progress polling or streaming;
- charts, comparisons or aggregate analytics;
- unit conversion or engineering-data editing;
- proposal/review actions;
- AI summaries, Jarvis context assembly or external calls;
- freshness recomputation;
- artifact filesystem browsing;
- global visual-identity redesign;
- new backend state, schema or infrastructure by default.

## Failure modes that block merge

- stale response from another workspace/run becomes visible under current selection;
- filesystem paths are exposed;
- raw payload/log content is executed or interpreted as markup;
- unknown status is coerced into success/failure;
- missing completion time is presented as running/progress;
- old-workspace data remains after workspace switch failure;
- selected detail is silently mismatched with list selection;
- payload/log/digest tokens cause page-level horizontal overflow;
- legacy route or scenario controls regress;
- exact-head build/checker/browser evidence is missing or stale;
- scope expands into analytics, engineering data, proposal review, Jarvis, visual identity or runner mutations.

## Rollback

088 must be independently removable.

Rollback restores the `/runs` `MigrationPendingSurface` and removes only the dedicated read client/workbench/checker/styles introduced by 088. The existing App-owned workspace seam, runner/modeling backend, legacy Domain Foundation controls, 087 Lineage surface and all persisted run data remain untouched.

No data migration or cleanup is required for rollback.

## Readiness gate

Implementation remains unauthorized while registry row 088 is `planned`.

A separate readiness decision must re-read exact `master` and verify:

1. list/detail/log/artifact runtime schemas and route behavior;
2. current App-owned workspace seam and `/runs` route composition;
3. whether a dedicated client file is smaller than extending `api/client.ts`;
4. exact payload rendering bounds;
5. exact filter-hidden-selection/focus rule;
6. exact file allow-list and inherited preservation-checker implications;
7. exact deterministic/build/browser commands;
8. that no backend addition is actually required.

Only that readiness PR may promote row 088 from `planned` to `ready`; the Implementation PR column remains `—` until runtime work starts.