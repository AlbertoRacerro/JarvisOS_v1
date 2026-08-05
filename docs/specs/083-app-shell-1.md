# Spec 083 — APP-SHELL-1

**Definition status:** complete specification; implementation remains unauthorized until a separate readiness decision promotes registry row 083.

**Registry status at definition:** `planned`

**Depends on:** 006, 070

**Authority:** `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, `docs/specs/081-frontend-beta-authority-0.md`, merged spec 070, and this full specification.

**Exact full-spec derivation baseline:**

```text
repository: AlbertoRacerro/JarvisOS_v1
branch: master
commit: 672e8182031aa2a2d26608ead222c50c0af038f6
merged definition kernel: PR #228
```

**Work architecture:** Route 2. The maintainer is developing the global visual identity independently in Penpot. That identity is a separate, independently removable lane and does not block the structural shell defined here. Spec 083 consumes the existing semantic contracts from 070 without changing global font, palette, component grammar, iconography, token values, or motion language.

---

## 1. Purpose

Implement the smallest durable desktop-first application shell that replaces the current component-state page switcher with URL-backed navigation while preserving every current operator capability and every backend authority boundary.

083 must add:

- canonical URL routes with direct-load, refresh, back, and forward continuity;
- a restrained primary rail and top bar;
- one dominant primary-stage region;
- a static compile-time registry containing exactly ModelStage, ResultsStage, ReviewStage, and FlowsheetStage;
- one contextual navigator;
- one contextual sidecar slot;
- one analysis dock closed by default;
- compatibility-mounted current BLUECAD inside ModelStage;
- explicit legacy diagnostic routes for current pages not yet migrated;
- honest unavailable and migration-pending states;
- keyboard, focus, reduced-motion, 200% zoom, compact-desktop, and overflow behavior built on 070.

083 must not change backend authority, engineering data, provider behavior, credentials, budget, ledger, egress, MemoryStore, BLUECAD lifecycle, Three.js internals, or the visual-identity lane.

## 2. Verified current state

At the exact baseline:

1. `frontend/src/App.tsx` uses `useState<AppPage>` to select six page components and owns no URL contract.
2. `frontend/src/components/Layout.tsx` renders a fixed sidebar, button navigation, and the 070 appearance selector.
3. `frontend/package.json` contains React, React DOM, Three.js, TypeScript, and Vite only. It contains no router, state framework, icon package, UI framework, CSS processor, or browser-test framework.
4. `frontend/src/main.tsx` applies stored appearance before mount and imports `tokens.css`, `global.css`, `foundation.css`, and `responsive.css` in that order.
5. 070 already owns semantic light/dark tokens, exactly `system`/`light`/`dark`, enum-only versioned appearance persistence, live system-theme response and cleanup, five shared primitives, visible focus, non-color state distinction, reduced motion, and responsive containment.
6. `BlueCAD.tsx` exposes real candidate creation, refresh, selection, archive, retry/duplicate, promotion, validation, attempt history, artifact links, and the real GLB viewer.
7. `BluecadGlbViewer.tsx` owns Three.js loading, orbit, pan, zoom, resize, and cleanup. It does not expose stable semantic component identity.
8. `DomainFoundation.tsx`, `AIDraft.tsx`, `SystemStatus.tsx`, `Dashboard.tsx`, and `DevLocalChat.tsx` remain current working pages with their existing API behavior.
9. `frontend/src/api/client.ts` remains the shared frontend HTTP/type surface.
10. No implementation branch or implementation PR for 083 exists at this full-spec baseline.

If master moves before readiness, the readiness audit must repeat this exact-state check and amend this specification when material drift exists.

## 3. Minimum-necessary decision

### 3.1 Router comparison

| Candidate | Advantages | Failure modes and cost | Decision |
| --- | --- | --- | --- |
| Native History API with one static typed route table | zero dependency; bounded static routes; direct control of legacy/dev behavior; independently removable; no package/license/transitive risk | bespoke `popstate`, link interception, normalization, title and focus handling must be tested | selected |
| Mature router package | established nested/dynamic route handling and test ecosystem | new dependency and transitive footprint; capabilities exceed this static slice; frontend has no router test stack; removal cost is higher | rejected for 083 |

083 has no dynamic path parameters, nested data loaders, route guards, server rendering, asynchronous route modules, or runtime-generated routes. A router dependency is therefore not minimum necessary.

### 3.2 Selected routing contract

The implementation must use:

- one compile-time route table;
- `window.history.pushState` and `replaceState`;
- one `popstate` subscription with cleanup;
- an internal link component that preserves native anchor semantics;
- a resolver that maps only canonical static paths;
- no URL-derived engineering authority;
- no query-string or hash state owned by 083.

The root route must use `replaceState` to canonicalize `/` to `/home` without creating a redundant history entry.

The internal link component may intercept navigation only for an unmodified primary-button click targeting the current browsing context. Modified clicks, download links, external origins, and non-`_self` targets retain browser-native behavior.

## 4. Canonical route model

The implementation must define a closed `RouteId` union equivalent to:

```ts
type RouteId =
  | "home"
  | "design-model"
  | "design-results"
  | "design-flowsheet"
  | "runs"
  | "engineering-data"
  | "review"
  | "settings"
  | "legacy-domain-foundation"
  | "legacy-ai-draft"
  | "legacy-system-status"
  | "legacy-dev-local-chat"
  | "not-found";
```

Each canonical route definition must contain:

```ts
type AppRouteDefinition = Readonly<{
  id: RouteId;
  path: string;
  title: string;
  primaryNav?: "home" | "design" | "runs" | "engineering-data" | "review" | "settings";
  stageKind?: StageKind;
  legacy?: true;
  devOnly?: true;
}>;
```

No route may be registered at runtime or supplied by backend/provider data.

### 4.1 Production route table

```text
/                         -> replace with /home
/home                     -> current Dashboard compatibility content
/design/model             -> ModelStage with current BLUECAD compatibility adapter
/design/results           -> ResultsStage honest unavailable/migration state
/design/flowsheet         -> FlowsheetStage honest unavailable state
/runs                     -> migration-pending Runs destination
/engineering-data         -> migration-pending Engineering Data destination
/review                   -> ReviewStage honest unavailable/migration state
/settings                 -> migration-pending Settings destination
/legacy/domain-foundation -> current DomainFoundation
/legacy/ai-draft          -> current AIDraft
/legacy/system-status     -> current SystemStatus
```

### 4.2 Development-only route

```text
/legacy/dev-local-chat    -> current DevLocalChat only when import.meta.env.DEV is true
```

A production build must resolve this path as not found. It must not render or reveal a hidden production chat capability.

### 4.3 Unknown and normalization behavior

- `/home/` and any other canonical route with one or more trailing slashes normalize to the no-trailing-slash path, except `/`.
- Matching is case-sensitive.
- Unknown paths render the bounded not-found surface; they do not silently fall back to Home.
- The not-found surface provides real links to Home and the relevant primary destinations.
- Geometry-hit selection never appears in path, query, or hash.
- 083 does not introduce record deep links. A later competent spec may add validated record paths.

## 5. Primary navigation and legacy continuity

Primary navigation contains exactly these visible product destinations:

```text
Home
Design
Runs
Engineering Data
Review
Settings
```

Rules:

- primary entries are anchors or link-equivalent anchors, not button-based page switches;
- the current primary destination uses `aria-current="page"`;
- visible text remains present at compact desktop and at 200% zoom;
- no legacy route appears as a peer primary destination;
- no provider, model, budget, credential, AI route, or diagnostic item appears in the primary rail;
- stage links Model, Results, and Flowsheet belong to the contextual Design navigator, not the primary rail.

The required legacy routes are:

```text
/legacy/domain-foundation
/legacy/ai-draft
/legacy/system-status
```

Each required legacy route must:

- render the exact visible label `Legacy diagnostic surface` before the current page content;
- remain directly loadable and refreshable;
- remain inside the application shell and `PageErrorBoundary`;
- preserve all existing page behavior and API calls;
- remain outside the primary navigation;
- be removed only by the specification that proves equivalent replacement.

No `/legacy/bluecad` page is implemented. Current BLUECAD has one authoritative frontend instance mounted inside ModelStage. A compatibility redirect from `/legacy/bluecad` is not authorized unless readiness discovers a real existing-link requirement and amends this spec.

## 6. Current-page transition map

| Current page | 083 treatment | Preserved behavior |
| --- | --- | --- |
| Dashboard | `/home` compatibility content | real backend health/foundation summary |
| BlueCAD | mounted once inside ModelStage at `/design/model` | candidate lifecycle, validation, attempts, artifacts, promotion, GLB |
| DomainFoundation | `/legacy/domain-foundation` | records, scenarios, bindings, runs, decisions |
| AIDraft | `/legacy/ai-draft` | AI execution/settings/credential/smoke/draft behavior |
| SystemStatus | `/legacy/system-status` | backend/storage/provider/budget diagnostics |
| DevLocalChat | dev-only `/legacy/dev-local-chat` | current local diagnostic behavior only |

The migration-pending routes `/runs`, `/engineering-data`, and `/settings` may contain explanatory text and explicit links to the appropriate legacy diagnostic surfaces. They must not embed or clone those pages as second product implementations.

## 7. Shell layout contract

The shell hierarchy is:

```text
Layout
├── SkipLink
├── TopBar
├── Rail
├── WorkspaceRegion
│   ├── ContextualNavigator
│   ├── PrimaryStageRegion
│   └── ContextualSidecar
└── AnalysisDock
```

### 7.1 TopBar

The top bar may show only:

- JarvisOS product identity;
- current route/stage title;
- the existing 070 appearance preference control;
- shell panel toggles with accessible names and expanded state.

083 does not add backend status, provider status, budgets, agent presence, telemetry, or selected-record labels to the top bar. Those are unnecessary for this slice and would increase data and failure surface.

### 7.2 Rail

The rail:

- contains only the six primary destinations;
- uses visible text and native link semantics;
- identifies current location with `aria-current` and non-color styling;
- does not collapse to icon-only behavior;
- does not require hover;
- may become an in-flow wrapping navigation region at compact widths.

### 7.3 ContextualNavigator

The navigator is closed on first load and after a fresh route load.

When opened on a Design route it contains only the static stage links:

```text
Model
Results
Flowsheet
```

On other routes it renders an honest context-specific empty or migration state. It must not implement candidate aggregates, lineage trees, run browsers, Engineering Data search, assembly trees, or scene semantics.

### 7.4 ContextualSidecar

There is one right-side slot. It is closed by default and may be opened to an honest `No record selected` state.

083 produces no record selection and no geometry selection from the current BLUECAD viewer. Therefore the sidecar must not synthesize record identity from current page state, DOM content, Three.js objects, text labels, or route names.

083 does not implement Jarvis, threads, role profiles, context packaging, provider selection, AI presence, autonomous behavior, proposal creation, or full inspector behavior.

### 7.5 AnalysisDock

The analysis dock is closed by default and may be opened to an honest migration-pending state.

083 does not implement charts, metrics, run comparison, analytics persistence, or metric semantics. Those belong to 089.

### 7.6 Panel state and focus

Navigator, sidecar, and dock state are transient React state only.

For each panel:

- the toggle exposes `aria-expanded` and `aria-controls`;
- closed content is not mounted and cannot receive focus;
- opening places focus on the panel heading after render;
- Escape closes the focused panel;
- closing returns focus to the initiating toggle;
- route changes close all three panels;
- no panel auto-opens from inferred context.

## 8. Static PrimaryStage registry

The implementation must contain exactly four stage kinds:

```ts
type StageKind = "model" | "results" | "review" | "flowsheet";

type PrimaryStageProps = Readonly<{
  workspaceId: string | null;
  selection: StageSelection | null;
  onSelectionChange(next: StageSelection | null): void;
}>;

type StageDefinition = Readonly<{
  kind: StageKind;
  label: string;
  render: React.ComponentType<PrimaryStageProps>;
}>;
```

The compile-time registry contains exactly:

```text
model     -> ModelStage
results   -> ResultsStage
review    -> ReviewStage
flowsheet -> FlowsheetStage
```

Binding rules:

- no runtime registration, plugin loader, dynamic import registry, provider-owned stage, or backend-supplied stage identifier;
- stage kind is derived only from the canonical route definition;
- no stage-specific engineering store;
- stage toolbar/status chrome uses explicit typed composition, never DOM inspection;
- the registry and all stage definitions are exhaustively checked.

### 8.1 ModelStage

ModelStage mounts the current `BlueCAD` component exactly once through a thin compatibility boundary.

The boundary may add only:

- a stage heading/description;
- containment classes;
- explicit transition wording.

It must not:

- fork BLUECAD state;
- intercept or reinterpret candidate IDs/statuses;
- change API calls;
- change archive/retry/promotion behavior;
- alter validation or attempt evidence;
- alter artifact URLs;
- alter Three.js internals, scene constants, lighting, grid, controls, loading, resize, or cleanup;
- add geometry picking or semantic selection.

### 8.2 ResultsStage

ResultsStage renders an honest unavailable/migration state and links to Runs. It does not show fake results, metrics, tables, charts, or simulations.

### 8.3 ReviewStage

ReviewStage renders an honest unavailable/migration state. It does not implement proposal review or bypass re-derived 054 and the operator-design boundary.

### 8.4 FlowsheetStage

FlowsheetStage states plainly that editable flowsheets are unavailable and directs the operator to Runs. It identifies Lineage as future work under 087.

It must not render draggable nodes, simulated stream values, editable connections, fake solver state, an empty canvas represented as a product, a runtime plugin system, or a second graph store.

## 9. Selection contract

083 defines only the typed seam required by 081:

```ts
type RecordResource =
  | "workspace"
  | "model-spec"
  | "assumption"
  | "parameter"
  | "simulation-run"
  | "decision"
  | "bluecad-candidate";

type RecordRef = Readonly<{
  resource: RecordResource;
  workspaceId: string;
  recordId: string;
}>;

type StageSelection =
  | { kind: "record"; ref: RecordRef }
  | {
      kind: "geometry-hit";
      viewerSessionId: string;
      ephemeralObjectId: string;
      point?: readonly [number, number, number];
    };
```

`RecordRef` is a locator only. It contains no copied record payload, status, label, provenance, freshness, or mutable data.

083 has no current producer for either selection branch. The initial implementation keeps `selection === null` and the sidecar in its empty state.

Rules:

- a geometry hit has no `RecordRef` and no `sceneComponentId`;
- geometry hits are session-scoped, non-persistent, non-evidence, non-promotion, and non-semantic;
- no identity may be inferred from Three.js UUID, object name, traversal index, material, mesh order, or pointer hit;
- geometry selection must clear on viewer disposal or artifact reload when a future spec introduces a producer;
- consumers exhaustively discriminate the union;
- 092 and re-derived 058c own stable scene binding and semantic selection.

## 10. State and persistence

083 may own only:

- current resolved route;
- navigator/sidecar/dock open state;
- stage kind derived from the route;
- `StageSelection | null`;
- focus-return references;
- non-authoritative temporary shell state.

Only the existing 070 appearance enum may be persisted in browser storage.

083 must not write any shell state, route, workspace, selection, record, prompt, result, secret, engineering value, conversation, panel state, or migration state to `localStorage`, `sessionStorage`, IndexedDB, cookies, URL query, or URL hash.

No Redux, Zustand, MobX, XState, second store, backend mirror, or new React context is authorized. Prop composition and local component state are sufficient for this slice.

## 11. Visual-identity boundary

### 11.1 083-owned visual work

083 may add only structural shell CSS required for:

- grid/flex layout;
- region sizing and containment;
- open/closed panel composition;
- current-route and current-stage structural distinction;
- compact-desktop and 200%-zoom reflow;
- skip-link placement;
- local overflow behavior;
- visible legacy/unavailable/migration labels using existing 070 primitives and semantic roles.

### 11.2 Reused 070 contracts

083 must reuse:

- existing semantic token names and current values;
- exactly system/light/dark appearance;
- existing appearance storage and pre-mount behavior;
- existing focus treatment;
- existing reduced-motion variables;
- Button, Surface, StatusBadge, Field, and InlineNotice;
- non-color state distinctions;
- containment and local-overflow rules.

### 11.3 Penpot lane excluded from 083

The separately developed Penpot identity owns any future:

- global font replacement;
- global palette/token-value replacement;
- border, line, radius, shadow, surface, control, table, or badge grammar;
- iconography and asset system;
- global motion language;
- cross-page visual redesign;
- replacement of the temporary green/generic SaaS aesthetic.

083 must not change `tokens.css` values, import fonts/assets, add an icon package, add raw colors, or redesign existing pages. Penpot design work may proceed in parallel; repository implementation of that identity requires a separate canonical specification or addendum and remains serialized under the one-implementation-front rule unless 081 is explicitly re-derived.

The shell must remain functional when the later identity lane changes token values and component styling without changing route, stage, selection, or authority contracts.

## 12. Accessibility contract

The implementation must provide:

- a skip link targeting the primary main region;
- semantic `header`, `nav`, `main`, and complementary-region landmarks;
- one route-specific page title and one main heading;
- anchor semantics for navigation;
- `aria-current="page"` for current primary and stage links;
- visible text for every navigation destination and panel toggle;
- visible 070 focus treatment in system/light/dark;
- keyboard reachability for all shell controls and legacy links;
- no hover-only behavior or color-only meaning;
- deterministic focus movement after route change;
- deterministic focus restoration after panel close;
- no focus in closed regions;
- no focus-stealing panel auto-open;
- Escape close behavior for an opened panel;
- reduced-motion behavior through existing motion variables;
- no content conveyed only through shape, color, animation, or position.

On route change, focus must move to the new route's `main` heading or main container after the document title is updated. Browser back/forward must receive the same focus treatment.

## 13. Responsive and zoom contract

### 13.1 Structural behavior

The stage region must use `minmax(0, 1fr)` or equivalent shrink-safe layout.

No shell or page may create document-level horizontal overflow. Wide tables and the GLB technical viewport retain local overflow/containment.

At wide desktop widths, open navigator and sidecar may occupy bounded columns and the dock may span beneath the stage.

At effective viewport widths below `60rem`:

- the rail becomes an in-flow wrapping visible-text navigation region;
- navigator, sidecar, and dock render in normal document flow rather than fixed or off-screen columns;
- the primary stage appears before opened secondary content in reading order, except the navigator may precede the stage when open because it controls stage selection;
- no icon-only transformation occurs;
- all panel toggles remain reachable;
- no absolute positioning may obscure page controls.

### 13.2 Exact browser matrix

Readiness and implementation evidence must use at least:

| Case | Browser window / zoom | Required routes |
| --- | --- | --- |
| Wide desktop | 1440×900 at 100% | Home, ModelStage/BLUECAD, Results, Flowsheet, all three required legacy routes |
| Compact desktop | 1024×768 at 100% | Home, ModelStage/BLUECAD, Settings, one dense legacy route |
| Zoom reflow | 1440×900 at 200% | Home, ModelStage/BLUECAD, Flowsheet, Domain Foundation legacy |
| Short desktop | 1280×720 at 100% | ModelStage/BLUECAD with navigator, sidecar, and dock independently opened |

For every matrix case:

```js
document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1
```

must hold after layout settles, except local scroll containers whose overflow does not increase the document width.

The real GLB canvas must remain visible, bounded, and operable when a real artifact exists. The shell must not hide the viewer or rely on document clipping.

## 14. Error, unavailable, and migration behavior

- Every route renders inside `PageErrorBoundary` keyed by route ID or canonical path.
- Backend-unavailable states from current pages remain visible and honest.
- Shell unavailable/migration states use existing `InlineNotice`, `Surface`, and/or `StatusBadge` semantics.
- Unavailable, migration-pending, legacy, and development-only states use text labels and structural treatment, not hue alone.
- No fake success, fake loading completion, fake telemetry, or invented data is allowed.
- An unknown route remains distinguishable from a backend-unavailable page.

## 15. Security and authority preservation

083 makes no backend, API, schema, migration, provider, credential, budget, ledger, egress, audit, MemoryStore, runner, BLUECAD lifecycle, or artifact-contract change.

The frontend continues to be an operator interface. It must not:

- call providers or Ollama directly;
- access filesystem or execution tools directly;
- place secrets or provider responses in routes, storage, logs, screenshots, or shell state;
- create a second AI execution path;
- create a second engineering-data store;
- promote model output or engineering records;
- change `run_ai_task` authority;
- reinterpret backend status or lifecycle values.

## 16. Exact implementation file set

The single implementation PR is authorized to modify only:

```text
frontend/src/App.tsx
frontend/src/components/Layout.tsx
frontend/src/main.tsx
frontend/src/styles/responsive.css
docs/specs/STATUS.md
```

It is authorized to add only:

```text
frontend/src/app/AppLink.tsx
frontend/src/app/routes.ts
frontend/src/app/selection.ts
frontend/src/app/useAppRouter.ts
frontend/src/components/shell/AnalysisDock.tsx
frontend/src/components/shell/ContextualNavigator.tsx
frontend/src/components/shell/ContextualSidecar.tsx
frontend/src/components/shell/LegacyDiagnosticSurface.tsx
frontend/src/components/shell/MigrationPendingSurface.tsx
frontend/src/components/shell/Rail.tsx
frontend/src/components/shell/TopBar.tsx
frontend/src/stages/FlowsheetStage.tsx
frontend/src/stages/ModelStage.tsx
frontend/src/stages/ResultsStage.tsx
frontend/src/stages/ReviewStage.tsx
frontend/src/stages/registry.ts
frontend/src/styles/shell.css
scripts/check_app_shell.py
```

`frontend/src/main.tsx` may change only to import `shell.css` after `foundation.css` and before `responsive.css`.

`frontend/src/styles/responsive.css` may change only for shell and compatibility containment. It must not hide document overflow or redesign existing pages.

`docs/specs/STATUS.md` may change only in row 083 and the current-priority sentence, following lifecycle transitions. The implementation PR must not record itself while still document-only.

No current page, API client, theme utility, primitive, token value, package manifest, lockfile, backend file, workflow, Three.js viewer, or other specification may change. A newly discovered necessary file requires a full-spec amendment before implementation continues.

## 17. Deterministic checker

`scripts/check_app_shell.py` must be dependency-free and fail closed.

It must verify at minimum:

1. exact production and development route paths;
2. exact six primary navigation labels and absence of legacy routes from primary navigation;
3. exact `Legacy diagnostic surface` text for the three required routes;
4. exactly four stage kinds and exactly four stage registry entries;
5. current `BlueCAD` imported only by ModelStage among new shell/stage modules;
6. no router/state/icon/UI dependency added to `frontend/package.json`;
7. no `localStorage`, `sessionStorage`, IndexedDB, cookie, query, or hash persistence in 083 modules;
8. no raw hex/rgb/hsl/named color literals in `shell.css` or new TSX files;
9. no inline `style`, `dangerouslySetInnerHTML`, embedded SVG, or external asset URL in new shell/stage files;
10. `shell.css` uses semantic variables and contains shrink-safe stage layout;
11. skip link, landmarks, `aria-current`, `aria-expanded`, `aria-controls`, and panel focus hooks are present;
12. root canonicalization uses replace semantics;
13. one `popstate` subscription and cleanup exist;
14. dev-local-chat route is gated by `import.meta.env.DEV`;
15. no provider/Ollama/filesystem/tool endpoint or secret-related string is introduced in shell modules;
16. existing `tokens.css`, theme utilities, primitive files, API client, current pages, and `BluecadGlbViewer.tsx` remain outside the implementation diff;
17. checker self-cases reject representative whitespace, template, comment, color, inline-style, storage, route, and registry evasions.

The checker is evidence of structural compliance, not proof of browser semantics. Browser evidence remains mandatory.

## 18. Test and evidence plan

### 18.1 Deterministic local/CI gates

On the exact implementation head:

```text
python scripts/check_ui_foundation.py
python scripts/check_app_shell.py
cd frontend && npm ci && npm run build
cd backend && python -m ruff check app tests
cd backend && python -m pytest -q
repository-standard BLUECAD geometry canary/property/time gates
```

No test may make a live provider call or require a secret.

### 18.2 Route behavior evidence

Using the production build/preview, verify:

- direct load of every production route;
- refresh of every production route;
- `/` replace-canonicalization to `/home`;
- back and forward across at least Home → Model → legacy Domain Foundation → Settings;
- trailing-slash normalization;
- unknown-route recovery;
- production rejection of `/legacy/dev-local-chat`;
- development availability of `/legacy/dev-local-chat`;
- correct `document.title` and main heading;
- focus movement after push, replace, popstate, and not-found recovery.

### 18.3 Shell interaction evidence

In system/light/dark and reduced motion where supported, verify:

- primary navigation and stage navigation by keyboard;
- current-route and current-stage non-color indication;
- navigator, sidecar, and dock closed on first load;
- open focus, Escape close, and toggle-focus restoration for each panel;
- panels close on route change;
- sidecar shows no fabricated selection;
- dock and future stages show honest unavailable/migration text.

### 18.4 Continuity evidence

Verify all current functions remain available:

- Dashboard real health content;
- current BLUECAD candidate list and actions;
- validation and attempt data;
- real GLB viewer when an artifact exists;
- Domain Foundation legacy behavior;
- AIDraft legacy behavior without live provider dispatch;
- System Status legacy behavior;
- development local chat only in development;
- handled backend-unavailable states.

Browser screenshots must not contain secrets, provider outputs, private engineering content, credential-derived values, or unredacted identifiers unnecessary to the proof.

## 19. Acceptance criteria

083 is implementation-complete only when all are true on one exact head:

1. URL navigation replaces `AppPage` component-state switching.
2. Every production route direct-loads, refreshes, and participates in back/forward history.
3. `/` canonicalizes to `/home` with replace semantics.
4. Primary navigation contains exactly Home, Design, Runs, Engineering Data, Review, Settings.
5. Required legacy routes are direct, outside primary navigation, and visibly labelled `Legacy diagnostic surface`.
6. Current BLUECAD exists once inside ModelStage and retains all current behavior and real GLB rendering.
7. Registry contains exactly ModelStage, ResultsStage, ReviewStage, FlowsheetStage with no runtime registration.
8. Results, Review, and Flowsheet show honest unavailable/migration states and no fake capability.
9. Navigator, sidecar, and dock are closed by default and pass focus/keyboard/Escape behavior.
10. Sidecar receives no fabricated record or geometry selection.
11. Only 070 appearance is browser-persisted.
12. No dependency, state store, icon package, visual-identity asset, font, token-value change, backend change, or API change exists.
13. System/light/dark, live system appearance, focus, keyboard, reduced motion, and non-color state contracts from 070 remain intact.
14. All exact browser-matrix cases have no document-level horizontal overflow.
15. BLUECAD tables and technical viewport retain local containment at compact width and 200% zoom.
16. Production build excludes the dev local-chat route.
17. `check_ui_foundation.py`, `check_app_shell.py`, frontend build, backend Ruff/Pytest, CI, and BLUECAD proof are green.
18. No current P0/P1 or beta-blocking P2 remains open.
19. Exact-head review confirms route continuity, scope, authority, accessibility, and removability.
20. Registry row 083 is reconciled after merge without changing queue order.

## 20. Non-goals

083 does not implement:

- global visual identity from Penpot;
- token-value, font, icon, border, radius, shadow, or component-grammar redesign;
- candidate aggregate/read model 084;
- full BLUECAD migration 085;
- geometry inspection 086;
- lineage 087;
- Runs workbench 088;
- Engineering Data re-derived 035;
- analytics 089;
- AI threads 090;
- Jarvis sidecar behavior 091;
- scene binding 092;
- Settings re-derived 029;
- proposal review re-derived 054;
- semantic scene selection re-derived 058c;
- editable Aspen-like flowsheet;
- runtime plugins;
- dynamic routes;
- record deep links;
- mobile product redesign;
- provider, credential, budget, ledger, egress, MemoryStore, backend, schema, or migration work;
- Three.js picking or scene changes.

## 21. Rollback and removability

083 must remain independently removable.

A compliant rollback can:

1. restore baseline `App.tsx` component-state page switching;
2. restore baseline `Layout.tsx` sidebar/button navigation;
3. remove all files added by 083;
4. remove the `shell.css` import and 083 responsive rules;
5. retain every current page, API client, 070 theme/primitive/token contract, BLUECAD viewer, backend record, database, artifact, and workflow;
6. require no storage or database migration;
7. leave no shell browser state to migrate.

The future Penpot identity must be able to restyle or replace shell presentation without changing route, stage, selection, persistence, or backend contracts.

## 22. Readiness requirements

A separate readiness audit may promote 083 only after it verifies:

- dependencies 006 and 070 remain merged;
- this full spec is merged on current master;
- the Penpot identity is explicitly separate and no longer a blocker for structural shell work;
- the native router decision remains minimum necessary;
- the exact file set is sufficient;
- the deterministic checker plan is executable;
- browser widths and route steps are exact;
- every current page has a preservation path;
- BLUECAD compatibility mounting is independently removable by 085;
- no 084–092 or re-derived page behavior is absorbed;
- no backend-authority or visual-identity change is required;
- rollback is credible;
- no open blocker remains.

Until that audit is merged and `STATUS.md` records 083 as `ready`, no runtime implementation is authorized.
