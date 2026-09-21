# Spec 144 persistent implementation checkpoint

## Existing surface recovery — 2026-09-21

Continued draft PR #661 from `21b1384d47979673d463eb861a3ab69beb76da2b`.
Fresh master remains `f49d2203943cc85cf772401faa198fa930c10a4c`; used its
capability manual for routing without merging master. Parent exact-head CI and
PR Attention Evidence passed. The spec-144 automation remains paused; checked
for concurrent implementation before shared mutations. Two Luna workers owned
separate Memory and Calendar files; parent reviewed and integrated their changes.

- Models now offers **+ New model** using the existing `createModelSpec` client
  and modeling owner. Title/question/scope produce a saved draft definition,
  explicitly not an executable model version. Selection, reload and failure
  feedback use real persisted state. Async creation cannot inject an old
  workspace's results after switching workspace. Successful POST closes/clears
  the form before list refresh; a failed refresh reports the saved definition
  rather than inviting another identical submission.
- Models and Literature filter loaded records with accent-normalized, unordered
  search tokens. This does not claim full-server search beyond loaded records.
- Calendar Day/Week opens near the earliest rendered event segment across the
  visible columns, in the display timezone. Overnight segments correctly focus
  midnight; empty grids start at 08:00. Empty feedback remains visible above
  the scrollable grid. Existing calendar persistence/authority is unchanged.
- BLUECAD candidate headings show a bounded human brief. Exact candidate ID and
  full brief remain available through an explicit **Candidate details** disclosure.
  Real archive/reload/restart and Settings failure recovery were re-exercised.
- Updated the old frontend 113 read-only source guard transparently for the
  spec-144 draft creation path through the canonical client. Direct fetch and
  generic mutation helpers remain forbidden; the gate remains in the build.
  No frozen backend conformance tests were changed.

Verification:

- Integrated `cd frontend && npm run build`: PASS, including all existing frontend
  gates, TypeScript and production Vite build. Existing bundle-size warning remains.
- Real FastAPI/SQLite/Vite/Chromium Memory smoke: UI citation, claim/datum and
  draft model creation; token search; exact Literature context preview/digest and
  removal; explicit browser fault injection for rejected POST (422) and failed
  post-save list refresh (503); reload/restart and no duplicate draft; compact
  overflow checks. Fault injection tests error feedback, not a backend outage.
- Roadmap browser smoke: real create/edit, done_when refusal, linked calendar
  event, Day/Week/Month/Agenda, overnight focus assertions, compact widths and
  backend restart persistence. No browser page errors.
- BLUECAD/Settings browser smoke: real parked candidate create/read/archive,
  disclosure open/close, reload/restart, Settings failure/retry; desktop and
  compact inspection. No generated geometry is claimed by this fixture.
- Screenshots in `docs/implementation/144-evidence/` show the actual rendered
  model definition, overnight Calendar and compact BLUECAD candidate. These
  complement interaction checks; they are not proof of full mission acceptance.

Environment and next work: cloud Browser refuses localhost; the real repository
Chromium harness works with the restored installed executable. The existing
local model previously returned `failed_terminal / localrespondertransporterror`;
no successful inference is claimed. BLUECAD candidate remains budget-blocked
without generated geometry; paid/provider/privacy/budget defaults were preserved.
Next: continue populated approved-reference comparison and existing workflows,
particularly Coding live repository reads/proposal flow and Models version
inspection with real populated data. Successful local inference and generated
geometry require the corresponding existing services to be available. No new
Process authoring, arbitrary execution, Hermes or provider authority was added.
PR #661 remains draft; this checkpoint is not maintainer-acceptance readiness.

## Workspace and Brainstorm recovery — 2026-09-20

Continued PR #661 from `5b334ef64ae7d1798bc0340d888eebdfca848d32`.
Fresh master: `f49d2203943cc85cf772401faa198fa930c10a4c`. Read the merged
capability manual as the routing map; no mapping manifest rediscovery or master
merge. Parent CI and PR Attention Evidence both passed. No other active
implementation automation was present; the spec-144 automation remains paused.

- Fixed a real first-install dead end: the production shell now offers workspace
  creation through the existing workspace API when a successful discovery is empty.
  A name is sufficient; slug/description are optional advanced presentation.
  Failed discovery exposes Retry and does not pretend the database is empty.
- Retain the selected workspace across reload only after fresh backend validation.
  Browser storage contains the selected ID, not domain records or permission.
  Invalid selections cannot reach workspace-scoped requests before validation.
  Browser testing exposed a competing automatic selection in Engineering Properties;
  removed that duplicate discovery now that App owns bootstrap. Settings stays reachable.
- Brainstorm reconciled rows are compact at rest, searchable by their loaded
  title/takeaway/synthesis, with lifecycle actions in an explicit disclosure.
  Synthesis precedes expandable provenance and technical IDs. Existing backend
  revision/idempotency/proposal-only semantics remain unchanged.

Verification on the final local code for this checkpoint:

- `cd frontend && npm run build`: PASS, including existing contract gates,
  TypeScript and Vite; existing bundle-size warning remains.
- `scripts/144-first-run-browser-smoke.mjs`: PASS with real FastAPI/SQLite/Vite/
  Chromium on isolated empty data. Covers UI-only first workspace creation,
  failed-list retry (explicit request-abort fault injection), originating route,
  two-workspace selection, reload and backend restart persistence, invalid cached
  ID refusal, and Settings access. No browser page errors.
- `scripts/144-operator-browser-smoke.mjs`: PASS again, extended for reconciled
  idea search and disclosed promotion actions. Existing RAW/manual synthesis/
  proposal, search/reconciliation, thread/context controls, reload/restart and
  12 surfaces at desktop/compact remain exercised. No document horizontal overflow.
- Visually inspected first-workspace and compact populated Brainstorm screenshots;
  compared Brainstorm hierarchy with its approved HTML. Screenshots are checked
  into `docs/implementation/144-evidence/`; they complement the interaction proof.

Environment: cloud Browser still refuses localhost (`ERR_BLOCKED_BY_CLIENT`).
The repository's real Chromium harness works after restoring the truncated
scratch executable from its installed npm Brotli package. Local inference still
returns `failed_terminal / localrespondertransporterror`; no provider or policy
configuration was changed. No new live Coding or generated BLUECAD geometry proof.

Remaining: complete populated visual/interaction comparison for the other
surfaces; exercise real Coding provider reads and successful local inference in
an environment where those existing services are available; generated BLUECAD
geometry remains unexercised. Run CI on the published checkpoint. PR stays draft;
this is not maintainer acceptance readiness.

## CI repair checkpoint — 2026-09-16

PR #661 remains draft and not ready for maintainer acceptance. Fresh review of
head `6865c0cee53410f1827ae78ae83ab6d785e9f901` found the full frontend build,
all sharded backend tests, BLUECAD canary, architecture and governance gates
green; the aggregate CI failed only Ruff import formatting in
`backend/app/modules/ai/thread_service.py`. Commit
`865e3a88ef99f70f03bf8221baf4b1337e8b3363` applies Ruff's multiline import
layout with no behavioral or authority change. Fresh exact-head CI is pending.
No review threads or maintainer reviews were present when checked. Remaining
product acceptance gaps and environment limits below are unchanged.


Updated 2026-09-16. **IN PROGRESS — NOT READY FOR MAINTAINER ACCEPTANCE.**

## Latest checkpoint — 2026-09-16

This section supersedes the older implementation/next-work details below where
they differ. Fresh remote master was `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`;
branch parent was `8d8acc28c1f90bd7d0c0e27ea39aff0386c13553`. Issue #655 remains
the mission contract. No implementation PR existed on the fresh branch lookup.
No master merge or status promotion was performed.

Recovered and integrated the prior uncommitted implementation rather than
discarding/restarting it. Other active mapping tasks were confined to separate
documentation branches; no other live implementation child was present.

### Implemented and exercised

- Shared Jarvis exposes existing configured local routes plus an explicitly
  synthetic test responder. Configuration is not advertised as runtime health.
  Transcript entries expose actual persisted execution class/model and failure.
  Default provider config, paid-disabled/zero budget and egress are unchanged.
- Memory exact context is passed with its inspected digest. Thread dispatch now
  reuses the Memory owner's semantic restrictions before reservation/dispatch;
  Project Basis semantic discussion remains refused, including local routes.
  Model/Literature secret-bearing context or intent is refused. This does not
  weaken sensitivity authority to make a button appear functional.
- Independent bounded review found a delayed initial thread-list race. Sending
  is now blocked while conversation ownership loads; auto-create completion also
  checks submit ownership. Browser regression delays the REAL list response,
  presses Enter, verifies no thread write, then releases it and verifies draft
  and conversation identity. A source guard is also included in normal build.
- Timeline/Calendar now have actual time-grid/day/week/month/agenda composition,
  navigation, selected-item/event editing and readable feedback. Existing owner,
  timezone conversion, revision and done-when checks remain authoritative.
- Brainstorm has inline expandable synthesis, saved-note organization and human
  promotion source labels. Browser exercised manual discussion, reconciliation,
  disclosure and proposal-only promotion through real owners and after restart.
  AI reconciliation is still unavailable; manual synthesis is not AI evidence.
- Literature supports source metadata and raw claim/datum entry; Models expose
  versionless definitions and in-panel revision history. Exact selection has a
  human label and removable context. See the bounded Memory note as history.
- Coding has bounded scrolling, readable deterministic inspection/proposal
  output, context removal and stale-proposal invalidation. Actual provider was
  unavailable; simulated successful file/proposal results are explicitly only
  supplementary component tests, never backend/provider-success evidence.
- Process distinguishes its unavailable visual authoring from existing kernel,
  model and run inspection. Navigation-only tests were updated to allow the
  exact four read/navigation destinations, not arbitrary click handlers.
- BLUECAD exposes existing inspector/interaction controls truthfully; Settings
  separates enabled/configured from reachable and provides failed-read recovery.
  Actual BLUECAD candidate remained `parked` / `budget_blocked`; no paid generation.

### Fresh verification

- `cd frontend && npm run build`: PASS (contract gates, TypeScript, Vite).
  Existing >500 kB bundle warning remains. `git diff --check`: PASS.
- Backend pytest: 132 passed across AI threads/conversation options (37),
  knowledge actions/security/review/sensitivity/context/Literature (58), and
  Development/calendar/done authority/Brainstorm/human search owners (37).
- `scripts/144-operator-browser-smoke.mjs`: PASS against real FastAPI/Vite/Chromium,
  fresh isolated data, no synthetic app responses. Covers RAW, manual idea and
  promotion, first thread, delayed list race, requirement reconcile/search/
  disclosure, exact-context refusal/removal, restart persistence, 12 surfaces at
  1600x1000 and 1280x800. No page errors/document horizontal overflow. Actual
  local model returned `failed_terminal` / `localrespondertransporterror`.
- `scripts/144-roadmap-browser-smoke.mjs`: PASS create/edit window, done-when
  refusal, linked event create/edit, four calendar projections, compact widths
  and backend restart. No fabricated completed roadmap item.
- `scripts/144-memory-browser-smoke.mjs`: PASS source/raw findings and exact
  preview/removal, versionless model, reload/restart, compact overflow. Extended
  run also PASS: real thread submission accepts exactly the inspected Literature
  refs/digest, persists across restart, and reports the responder as synthetic
  (not inference proof). Evidence: `/tmp/jarvis-144-B3Xc12/evidence`.
- `scripts/144-bluecad-settings-browser-smoke.mjs`: PASS real parked candidate
  create/archive/reload/restart. Settings failed-read recovery uses explicitly
  labeled request-abort fault injection, not a claimed real outage.
- `scripts/144-coding-browser-smoke.mjs`: PASS actual unavailable state/runtime
  checks and separately labeled fixture-only reader/context/proposal regressions.
- All five browser harnesses are now checked in and use repository-relative
  roots and explicit Python/Playwright/Chromium overrides. Successful runs do not
  substitute for maintainer hands-on acceptance or full visual-reference review.

Fresh local evidence directories (not published artifacts):
`/tmp/jarvis-144-k99czx/evidence` (main),
`/tmp/jarvis-144-Us9JDh/evidence` (roadmap),
`/tmp/jarvis-144-9l2ZMD/evidence` (Memory before exact-submit extension),
`/tmp/jarvis-144-xbodWr/evidence` (BLUECAD/Settings),
`/tmp/jarvis-coding-144-vy9UOE/evidence` (Coding actual/fixture separated).
Main compact Brainstorm and populated compact Calendar screenshots were visually
inspected in this run; no claim of full approved-reference fidelity is made.

### Environment and exact next work

Cloud Browser again refused loopback with `ERR_BLOCKED_BY_CLIENT`. The persisted
Chromium binary had been truncated (ELF missing sections); regenerated from the
already-installed official npm package's Brotli archive. SwiftShader libraries
must sit beside the restored executable. Python venv executable was absent;
existing 3.12 packages work through the installed Python with explicit PYTHONPATH.
No policy/network bypass, provider credentials or repository dependencies changed.

Example reproduction environment for this checkpoint: `PYTHONPATH` points to
`/workspace/scratch/61bf444950e2/venv/lib/python3.12/site-packages`,
`JARVIS_PLAYWRIGHT_MODULE` to the primary-runtime `playwright/index.mjs`,
`JARVIS_CHROMIUM_EXECUTABLE=/tmp/chromium-144-restored`, `LD_LIBRARY_PATH=/tmp`.
These are disposable environment paths; normal environments can use installed
Python/Playwright/Chromium. Run main and roadmap serially (both use 8000/5173).

Next: inspect populated surface screenshots against every approved reference;
complete usable-path audit for unexercised existing owners, generated BLUECAD
geometry and live Coding reads where the real provider is available. Prove
successful local inference on the actual operator machine without changing safe
defaults or claiming synthetic output as inference. Review first-run workspace
creation and long/partial/stale task paths. Exact Memory submission must not be
extended around the Project Basis refusal. Only after remaining acceptance gaps
are closed, open/reuse the single implementation PR, reconcile STATUS to that
PR, run exact-head checks/review and report READY. Do not merge master.

---

## Earlier checkpoint — 2026-09-15 (historical)

Mission: issue #655; branch `impl/144-operator-usability-recovery`. Do not merge.
Accepted starting master: `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`.
First mechanical registry commit: `5c367064c8be7d602014413ffcce651a6ecf2056`.
Spec 144 is `in_progress`. No implementation PR existed at this checkpoint.
Use the commit containing this note as the checkpoint identity; inspect subsequent
branch commits, PR state and checks before continuing. Do not restart analysis.

## Implemented in this checkpoint

- Human Project Search: case/diacritic normalization and token matching across
  existing Project Basis, Model Dossier and Literature owners. Exact matches
  retain priority. SQL ranks eligible matches before the bounded owner limit.
  The query `perdite carico` finds `perdite di carico` without altering identity.
- Project Basis: real expandable record rows, human fields, exact technical
  disclosure, selection binding, and revision workflow inside the main panel.
  The first requirement can be created without an existing revision. Proposed
  fields and revision operations are visible before approval/reconciliation.
- One embedded reusable Jarvis sidecar in Basis, Models, Literature and
  Brainstorm replaces decorative composers/duplicate shell columns. First
  submit creates a real thread. Context is opt-in; exact proposal context remains
  a separate, explicitly named action path. This is NOT yet the final shared UX.
- Brainstorm: large free-form RAW input, real save/reload, saved-note search,
  optional references and manual organization behind disclosures. Three columns
  follow RAW / reconciled ideas / Jarvis at desktop and compact desktop sizes.
- Repository: supporting tree/search at left, dominant scrollable file viewport,
  Markdown Rendered / Raw using react-markdown and remark-gfm, clickable search
  results, and explicit inspect/context/proposal actions. Markdown images do not
  automatically request external content. Provider/credential authority stays
  in the backend.
- Recovery CSS repairs missing fusion variables on the actual application shell,
  readable controls, scroll ownership and compact layout. Further consolidation
  with older overlays is still warranted.

## Backend reality (do not turn these into success claims)

1. Project Knowledge drafts, preview, approve, revalidate, reconcile and canonical
   Requirement writes are real. Browser created/reconciled a requirement and
   searched it through the real API. Representative data survived process restart.
2. Brainstorm RAW writes and reads are real and persisted through restart.
   Manual reconciliation/discussion/promotion endpoints exist but their complete
   browser workflow is NOT verified in this checkpoint. Development AI actions
   spec 122 remains planned; no AI reconciliation was fabricated.
3. Thread creation/interactions/transcripts are real persistent storage.
   **The current composer omits route_class, whose execution default is
   `local:fake` in `backend/app/modules/ai/execution.py`. Its answer is synthetic.**
   The composer says so before submission. Browser send/restart tests prove
   storage, NOT useful AI inference. Existing local model routes are configured
   in `configs/ai_providers.yaml`, but their runtime availability has not been
   proven or connected to this composer. No new provider/model was integrated.
4. `backend/app/modules/memory/jarvis_knowledge_actions.py` defaults to a
   deterministic proposal template. UI now labels it a draft of the instruction,
   not an AI answer. Its semantic Project Basis path rejects sensitive context;
   preserve that safety boundary. No privacy/egress/budget policy was changed.
5. Thread submit models also accept `jarvis_context` plus expected digest. Do not
   assume that means Memory/Brainstorm exact refs are resolvable: inspect actual
   adapters and sensitivity checks before wiring it. The current sidecar's
   generic project-pack checkbox and exact proposal basket are separate paths.
6. Coding backend in this isolated runtime returns `provider_unavailable`.
   Unavailability is visibly exposed. Live file read/context/proposal workflow
   has NOT been proven. Do not count empty-state screenshots or connector access
   as proof of the app's repository provider. Do not modify credential handling.
7. Process/BLUECAD/Models/Literature/Settings were opened at both viewport sizes.
   Their meaningful end-to-end workflows still require audit and repair.

## Verification performed

- `cd frontend && npm run build`: PASS (all existing frontend contract gates,
  TypeScript, Vite production build). Existing large bundle warning remains.
  Some static gates required obsolete unavailable copy or old labels; updated
  those assertions for the recovered UI while retaining owner/CAS/stale-response
  and authority checks. No frozen backend conformance test was modified.
- `cd backend && python -m pytest -q tests/test_operator_human_search.py
  tests/test_project_search.py tests/test_project_search_owner_regressions.py
  tests/test_project_search_real_owners.py`: **19 passed**.
- `scripts/144-operator-browser-smoke.mjs`: real Chromium, Vite, FastAPI, isolated
  SQLite data; no mocked app endpoint. Saves RAW, reloads it, types/sends the first
  conversation (explicitly synthetic responder), stages/approves/reconciles a
  requirement, searches normal Italian words and expands a record. Restarts the
  backend and verifies RAW, canonical requirement and conversation persisted.
- Browser opens 12 routes at 1600×1000 and 1280×800, captures screenshots/text,
  checks page errors and reports horizontal document overflow. Zero reported
  horizontal document overflows; this does not prove every internal panel fits.
  Visual inspection found/fixed compact Brainstorm row compression and an
  inherited green record-button style. Screenshots in `144-evidence` are a
  checkpoint, not final acceptance proof.
- Approved Memory/Brainstorm/Coding/Timeline/Calendar HTML rendered in the same
  Chromium. Timeline screenshot comparison shows substantial outstanding work.

## Exact next work

1. Finish shared Jarvis truth and usability. Expose existing real local inference
   only after actual owner/runtime verification; otherwise retain clear
   unavailable/synthetic labels. Make selected context obvious and removable,
   bind row selection for Literature too, and verify submission/refusal/retry.
2. Recover Roadmap/Timeline/Calendar using approved HTML. Current
   `DevelopmentRoadmap.tsx` is essentially unstyled CRUD, no visible Timeline ↔
   Calendar secondary nav, bars are not a coherent timeline, and calendar modes
   filter a card list rather than showing day/week/month layouts. Preserve
   timezone-aware allocation ranges and done_when semantics. Add item/event,
   edit, reload and restart in the browser; inspect desktop and compact.
3. Finish Brainstorm interaction: select RAW should visibly open the organization
   form; concise inline multi-expand reconciled ideas; hide inapplicable
   supersede/promotion controls; verify manual discussion/promotion persistence.
4. Finish Memory: avoid machine-first search provenance; integrate Models'
   remaining out-of-panel revision history; provide useful Literature source
   registration through its existing owner instead of “use the API” empty copy;
   bind exact source/entry selection to context. Verify actual representative data.
5. Coding: verify actual provider reads where available, complete context removal
   and human proposal output. Exercise long code/Markdown and error/partial states.
6. Audit Settings, Process and BLUECAD against approved HTML; repair real paths or
   clearly expose unavailable capabilities. Remove unused legacy placeholder
   code in FinalOperatorReadSurface when the relevant static gates are updated.
7. Complete focused regression/browser review, durable evidence and independent
   review. Only then create the coherent implementation PR, set 144 `in_review`
   with exact PR number according to checker, and hand off for local acceptance.
   Never merge. Never report READY from this checkpoint.

## Reproduction / environment notes

Normal environment: backend dev requirements, frontend `npm ci`, installed
Playwright Chromium. Browser smoke uses fresh isolated temporary data and starts
both servers itself. It deliberately uses ports 8000 and 5173; stop conflicting
test servers first. Run `node scripts/144-operator-browser-smoke.mjs` with optional
`JARVIS_TEST_PYTHON`, `JARVIS_PLAYWRIGHT_MODULE`, `JARVIS_CHROMIUM_EXECUTABLE` and
`JARVIS_BROWSER_EVIDENCE` overrides. Test data is retained in the reported temp
folder for inspection; it never uses the operator's ordinary data directory.

This session's shell commands have isolated network namespaces, so backend,
frontend and Chromium must run as children of one command. Cloud browser cannot
reach loopback (`ERR_BLOCKED_BY_CLIENT`). Playwright's official browser download
was unreachable. Chromium 153 from scratch-installed `@sparticuz/chromium` works
with its bundled SwiftShader libraries and the harness flags. Dependencies can
be restored from npm registry; no browser binary is committed.

Direct Git transport was unreachable, but the authorized GitHub connector works.
A clean worktree was recovered from exact GitHub blobs and verified remote tree
objects. The unrelated old checkout was not modified. Commit tree and branch ref
updates use GitHub Git Data APIs, non-force only, after checking current head.
Do not assume an old scratch checkout reflects current GitHub state.
