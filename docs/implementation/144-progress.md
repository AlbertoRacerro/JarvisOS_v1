# Spec 144 persistent implementation checkpoint

Updated 2026-09-15. **IN PROGRESS — NOT READY FOR MAINTAINER ACCEPTANCE.**

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
