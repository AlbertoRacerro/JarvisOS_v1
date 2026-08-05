# Spec 083 — APP-SHELL-1

**Definition status:** definition kernel; not yet a complete implementation contract and not readiness-authorizing.

**Registry status:** `planned`

**Depends on:** 006, 070

**Authority:** `AGENTS.md`, `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`, `docs/specs/STATUS.md`, and spec 081 FRONTEND-BETA-AUTHORITY-0.

**Exact derivation baseline:**

```text
repository: AlbertoRacerro/JarvisOS_v1
branch: master
commit: 182ab0623d5cdd26c79e31171539e721762b45d7
last merged implementation: PR #225 — UI-FOUNDATION-1
last registry reconciliation: PR #227
```

**Definition route:** Route 3 — the application-shell architecture is sufficiently evidenced, while the maintainer's global visual identity is not yet specified by inspectable image/font/palette assets. This kernel freezes only confirmed shell, continuity, authority, accessibility, and scope decisions. It does not freeze a global font, palette, component grammar, icon system, or motion language.

---

## 1. Purpose

Define the smallest durable desktop-first application shell that can replace the current component-state page switcher without changing backend authority, duplicating existing frontend functionality, or absorbing page-specific work assigned to specs 084–092 and re-derived 029, 035, 054, and 058c.

The eventual 083 implementation must provide:

- URL-backed navigation and refresh/back/forward continuity;
- one application shell with a rail, top bar, dominant primary-stage region, contextual navigator, one sidecar slot, and an analysis dock closed by default;
- a static, compile-time PrimaryStage registry containing exactly ModelStage, ResultsStage, ReviewStage, and FlowsheetStage;
- the current real BLUECAD workbench mounted inside ModelStage through a compatibility adapter until spec 085 replaces it;
- honest unavailable states where later specifications own the real capability;
- explicit legacy diagnostic routes preserving current non-migrated pages;
- responsive containment, keyboard reachability, visible focus, and 200% zoom usability built on spec 070;
- no backend, provider, credential, budget, ledger, egress, MemoryStore, BLUECAD lifecycle, or Three.js authority change.

This file intentionally occupies the canonical target path for 083 so that the later full-spec revision is an auditable diff against this kernel rather than a parallel document.

## 2. Current exact-master facts

Verified on the exact baseline above:

1. `frontend/src/App.tsx` owns navigation through `useState<AppPage>` and conditionally renders six pages. There is no URL route authority, refresh persistence, browser-history integration, or deep-link contract.
2. `frontend/src/components/Layout.tsx` owns one fixed sidebar, page buttons, and the 070 appearance control. It is transitional and is the natural replacement seam for 083.
3. `frontend/package.json` contains React, React DOM, Three.js, TypeScript, and Vite only. It contains no router, state library, UI framework, icon package, or frontend test framework.
4. `frontend/src/main.tsx` applies the stored 070 appearance before React mount and imports `tokens.css`, legacy `global.css`, `foundation.css`, and `responsive.css` in that order.
5. `frontend/src/styles/global.css` remains a large legacy stylesheet with hard-coded page, form, table, AI, scenario, BLUECAD, and current-shell rules. `foundation.css` semantically overlays a bounded part of it.
6. The 070 foundation provides semantic light/dark token roles, exactly `system`/`light`/`dark`, enum-only versioned persistence, live system-theme updates and cleanup, five typed primitives, focus-visible treatment, non-color status distinctions, reduced-motion handling, and responsive containment.
7. `frontend/src/pages/BlueCAD.tsx` exposes real candidate listing/detail, archive, retry/duplicate, promotion, validation checks, attempt history, and a real GLB artifact viewer.
8. `frontend/src/components/BluecadGlbViewer.tsx` provides real Three.js GLB loading, orbit, pan, zoom, grid, resize handling, and cleanup. It has no stable semantic part-selection contract.
9. `frontend/src/pages/DomainFoundation.tsx` is a combined legacy operational/diagnostic surface for workspaces, model records, assumptions, parameters, decisions, bundled-model registration, binding preview, runner creation, and scenario execution.
10. `frontend/src/pages/AIDraft.tsx` combines AI task execution, route selection, settings, credential status/actions, smoke diagnostics, escalation, and modeling draft behavior. It is not the future Jarvis sidecar.
11. `frontend/src/pages/SystemStatus.tsx` exposes backend, storage, AI, provider, budget, and diagnostic state.
12. `frontend/src/pages/DevLocalChat.tsx` is development-only, non-production, non-persistent local-chat diagnostics.
13. `frontend/src/api/client.ts` remains the shared frontend HTTP/type surface. 083 does not replace it or create another client.
14. PR #225 changed 15 bounded 070 files and explicitly stopped before router/shell work. PR #227 changed only the registry reconciliation for 070 and confirmed 083 as the next `planned` slice.
15. No canonical full 083 specification, 083 readiness record, 083 branch, 083 PR, or open PR existed at derivation time.

Any movement of `master` before a full-spec revision or readiness requires rechecking all facts above from the new exact SHA.

## 3. Authority and state boundaries

### 3.1 Backend remains authoritative

The FastAPI + SQLite backend remains authoritative for:

- durable engineering state;
- lifecycle and status values;
- provider routing and `run_ai_task`;
- credentials, budget, spend, ledger, egress, and audit;
- MemoryStore proposal/promotion boundaries;
- BLUECAD candidates, validation, attempts, evidence, artifacts, and promotion;
- runner and simulation-run records.

The shell may display or navigate to backend-owned state. It must not reinterpret, duplicate, persist, or mutate that state outside existing API contracts.

### 3.2 Frontend state allowed in 083

083 may own only transient operator-interface state such as:

- current URL route;
- rail/navigator/sidecar/dock open or closed state;
- current static stage kind derived from the URL;
- transient stage selection under the contract in section 8;
- focus restoration targets;
- temporary view state that has no engineering authority.

Only the 070 appearance enum may remain in browser storage. 083 must not persist shell layout, selected record, workspace, stage selection, prompts, results, secrets, engineering values, conversation state, or navigation authority in `localStorage`.

### 3.3 No second store

083 must not add Redux, Zustand, MobX, XState, another state framework, or a second store of engineering truth. A bounded React context is permitted only if ordinary prop composition becomes materially worse and the context owns transient shell state only. That necessity must be justified in the full spec/readiness record.

## 4. Current page inventory and transition ownership

The current application has page identities but no URL routes:

| Current page | Current behavior to preserve | 083 transition treatment |
| --- | --- | --- |
| `Dashboard` | backend health and current foundation summary | mounted as the initial `/home` compatibility content or replaced only by a proven equivalent shell home |
| `SystemStatus` | backend, storage, AI, provider, budget, diagnostics | required `/legacy/system-status` diagnostic route |
| `DomainFoundation` | combined records, scenarios, bindings, runs, decisions | required `/legacy/domain-foundation` diagnostic route |
| `BlueCAD` | complete current candidate lifecycle and real GLB viewer | mounted in ModelStage through a compatibility adapter; deep migration belongs to 085 |
| `AIDraft` | AI task/settings/credential/smoke/draft surface | required `/legacy/ai-draft` diagnostic route; not Jarvis sidecar |
| `DevLocalChat` | development-only local-chat diagnostic | development-only direct legacy route when `import.meta.env.DEV` is true |

083 must preserve each page component and its current API behavior. It may wrap a page in shell chrome and add an explicit legacy label. It must not silently rename a diagnostic surface into a finished product capability.

## 5. Canonical route contract

The full spec must retain or refine the following route classes without reducing continuity.

### 5.1 Shell and primary-navigation routes

```text
/                         -> deterministic redirect to /home
/home                     -> real current home/health compatibility content
/design/model             -> ModelStage with current BLUECAD compatibility adapter
/design/results           -> ResultsStage honest unavailable/legacy-handoff state
/runs                     -> honest migration-pending route with access to current run/scenario surface
/engineering-data         -> honest migration-pending route with access to current domain-record surface
/review                   -> ReviewStage honest unavailable/legacy-handoff state
/settings                 -> honest migration-pending route with access to current diagnostic surfaces
/design/flowsheet         -> FlowsheetStage honest unavailable state
```

Primary navigation may contain only the product destinations defined by 081:

```text
Home
Design
Runs
Engineering Data
Review
Settings
```

Legacy route names are not primary-navigation destinations.

The labels `Runs`, `Engineering Data`, `Review`, and `Settings` must not imply that future workbenches already exist. Availability and migration status must be visible in text, not color alone.

### 5.2 Required explicit legacy diagnostic routes

Spec 081 requires:

```text
/legacy/domain-foundation
/legacy/ai-draft
/legacy/system-status
```

Each route must:

- carry the visible text label `Legacy diagnostic surface`;
- remain directly reachable by URL;
- stay outside primary navigation;
- retain current backend authority boundaries;
- remain inside the application shell and `PageErrorBoundary`;
- be removed only by the competent spec after functional replacement is proved.

Additional transition route permitted by current-page continuity:

```text
/legacy/dev-local-chat    -> development-only; absent or explicitly unavailable in production
```

A compatibility alias `/legacy/bluecad` may redirect deterministically to `/design/model` if browser evidence or existing links require it. It must not create a second independently evolving BLUECAD surface. The authoritative transition behavior is the compatibility-mounted current workbench inside ModelStage.

No migrated function may remain indefinitely in two primary-navigation locations.

### 5.3 Route behavior requirements

- refresh on every production route renders the same route rather than an unrelated page;
- browser back/forward works;
- unknown routes render a bounded not-found state with routes back to `/home` and relevant product destinations;
- the development-only route does not leak a hidden production capability;
- route labels identify legacy/diagnostic/migration-pending status honestly;
- no route bypasses `PageErrorBoundary`;
- shell route transitions must not reset the 070 appearance preference;
- geometry-hit selection never enters the URL.

### 5.4 Router implementation boundary

URL behavior is required; a specific router package is not yet authorized.

The full definition/readiness cycle must compare:

1. a small static route table over the native History API and `popstate`;
2. one mature router dependency.

The default is no new dependency. A router package may be approved only when exact code evidence shows that the native approach would create materially more bespoke state, parsing, history, accessibility, or test complexity, and when the dependency/version/license/transitive footprint is recorded. A package must not be added merely because routing libraries are conventional.

## 6. Shell layout contract

The shell has one structural hierarchy:

```text
ApplicationShell
├── SkipLink
├── TopBar
├── Rail
├── WorkspaceRegion
│   ├── ContextualNavigator (closed or compact by default)
│   ├── PrimaryStageRegion (dominant)
│   └── ContextualSidecar (one slot; closed when no applicable context)
└── AnalysisDock (closed by default)
```

### 6.1 Top bar

083 may show only real, current, shell-level information:

- JarvisOS product identity;
- current route/stage title;
- selected record label only when a real record selection exists;
- backend `checking`, `available`, or `unavailable` derived from an existing health contract;
- the existing 070 appearance preference control or an equivalent accessible placement.

083 must not add fake live-agent presence, invented telemetry, decorative budget meters, synthetic online indicators, or status derived from assumptions. AI/provider/budget detail remains on current legacy diagnostics until the competent future surface is specified.

### 6.2 Rail

The rail must:

- use links or link-equivalent native navigation semantics;
- expose the current route with `aria-current="page"` where applicable;
- retain visible text at compact desktop sizes unless a reviewed icon system with accessible names exists;
- not require hover to discover a destination;
- exclude `/legacy/*` destinations from primary navigation;
- avoid provider/model-specific navigation.

Legacy routes may be linked contextually from migration-pending content or a secondary diagnostics index, never as peer primary destinations.

### 6.3 Contextual navigator

The navigator is a shell container, not an 083 data browser.

083 may implement:

- open/close behavior;
- focus management;
- title and empty/unavailable state;
- route-aware handoff links;
- a compact default.

083 must not implement candidate aggregates, lineage trees, run browsers, engineering-data search, assembly trees, or scene semantics. Those belong to 084, 087, 088, re-derived 035, 092, or other competent page specs.

### 6.4 Contextual sidecar

There is exactly one right-side secondary slot. It may host an inspector in future or Jarvis in spec 091; it must not create separate simultaneous Inspector and Jarvis columns.

083 may implement:

- closed state by default when no applicable selection exists;
- one accessible toggle;
- a selected-record summary only when sourced from an existing typed record reference;
- honest empty/unavailable content;
- replacement semantics for future sidecar modes.

083 must not implement conversation threads, role profiles, context packaging, provider selection, AI presence, autonomous behavior, proposal creation, or full Jarvis behavior.

### 6.5 Analysis dock

The dock is closed on initial load and after a fresh route load unless the later full spec proves a different accessible URL-backed behavior.

083 may implement only shell chrome, toggle behavior, focus management, and an honest migration-pending state. Charts, widgets, run comparison, analytics persistence, and metric semantics belong to 089.

## 7. Static PrimaryStage contract

The registry is compile-time and contains exactly four stage kinds:

```ts
type StageKind = "model" | "results" | "review" | "flowsheet";

type PrimaryStageProps = {
  workspaceId: string | null;
  selection: StageSelection | null;
  onSelectionChange(next: StageSelection | null): void;
};

type StageDefinition = {
  kind: StageKind;
  label: string;
  render: React.ComponentType<PrimaryStageProps>;
};

const PRIMARY_STAGES: Readonly<Record<StageKind, StageDefinition>> = {
  model: /* ModelStage */,
  results: /* ResultsStage */,
  review: /* ReviewStage */,
  flowsheet: /* FlowsheetStage */
};
```

The exact exported names may change in the full spec if TypeScript evidence justifies it, but these invariants are binding:

- no runtime registration;
- no plugin loader;
- no dynamic provider-owned stage;
- no arbitrary stage IDs from backend data;
- no stage-specific engineering store;
- stage kind is URL-derived;
- toolbar/status-strip chrome is shell-owned or passed through explicit typed slots, not discovered through DOM inspection;
- stage-specific view state remains local until a later spec proves a shared contract is necessary.

### 7.1 ModelStage

083 must mount the current working `BlueCAD` page through a bounded compatibility adapter inside ModelStage.

The adapter must:

- preserve every current BLUECAD action and API call;
- preserve real GLB rendering and current viewer internals;
- preserve validation, attempts, archive, retry/duplicate, and promotion behavior;
- add only shell/compatibility boundaries and explicit transitional labelling where needed;
- remain independently removable by spec 085;
- not create a second BLUECAD page implementation or state store;
- not implement inspection A0, read-model aggregation, or scene semantics.

### 7.2 ResultsStage

083 establishes only the stage frame and an honest unavailable/legacy-handoff state. Run result browsing and comparison belong to 088/089.

### 7.3 ReviewStage

083 establishes only the stage frame and an honest unavailable/legacy-handoff state. Proposal review requires re-derived 054 and must not bypass blocked operator-design work.

### 7.4 FlowsheetStage

FlowsheetStage must state plainly that an editable flowsheet is unavailable. It must direct the operator to the real Runs surface and identify Lineage as future work under 087.

It must not render draggable fake nodes, simulated stream values, editable connections, fake solver status, or an Aspen-like canvas. Process-kernel records in 075 do not authorize an editable flowsheet product.

## 8. Selection contract

083 adopts the 081 A0 boundary:

```ts
type RecordRef = {
  kind: string;
  id: string;
  workspaceId: string;
};

type StageSelection =
  | { kind: "record"; ref: RecordRef }
  | {
      kind: "geometry-hit";
      viewerSessionId: string;
      ephemeralObjectId: string;
      point?: readonly [number, number, number];
    };
```

Binding rules:

- `record` means a real typed backend record reference;
- `geometry-hit` is session-scoped and ephemeral;
- a geometry hit is not a RecordRef, scene component, part identity, evidence target, promotion target, or persistence key;
- geometry selection must be cleared when its viewer session is disposed, its artifact reloads, or its viewer is replaced;
- 083 must not infer semantic identity from a Three.js object name, UUID, traversal index, material, mesh order, or pointer hit;
- 083 must not persist selection in browser storage;
- URL deep links may include real record IDs only after the full spec defines validation and not-found behavior; geometry hits never enter the URL;
- consumers must discriminate the union exhaustively;
- 092 and re-derived 058c own stable scene binding and semantic selection.

## 9. Visual scope classification

### A — owned by 083

- shell spatial organization;
- rail and top-bar hierarchy;
- dominant primary-stage geometry;
- contextual navigator/sidecar/dock placement and closed defaults;
- route/stage current-state indication;
- shell-level typographic hierarchy using existing semantic roles;
- shell chrome necessary to distinguish primary and secondary regions;
- compact-desktop and 200%-zoom shell behavior;
- honest unavailable, migration-pending, and legacy-route presentation.

### B — reuse from 070

- semantic token naming and theme resolution;
- exactly system/light/dark appearance;
- versioned enum-only persistence;
- pre-mount application and live system changes;
- visible focus and keyboard operation;
- reduced motion;
- Button, Surface, StatusBadge, Field, InlineNotice;
- semantic status distinctions not dependent on color alone;
- responsive containment and local overflow ownership.

083 may consume existing token roles and may request narrowly justified shell-specific semantic roles in the later full spec. It must not destroy or bypass the 070 contracts.

### C — separate visual-identity lane

Not owned by this kernel or by 083 implementation unless a later queue re-derivation explicitly changes that decision:

- global font replacement;
- new cross-page palette values;
- global redesign of borders, lines, radii, shadows, surfaces, controls, tables, and badges;
- icon/asset system;
- global motion language;
- page redesign outside shell-owned chrome;
- global removal of legacy foundation styling.

### D — future page specifications

- candidate aggregate/read model: 084;
- full BLUECAD workbench: 085;
- geometry inspection A0: 086;
- lineage: 087;
- runs: 088;
- engineering-data navigation: re-derived 035;
- analytics: 089;
- AI threads: 090;
- Jarvis sidecar behavior: 091;
- stable scene binding: 092;
- Settings: re-derived 029;
- proposal review: re-derived 054;
- semantic scene tools: re-derived 058c.

## 10. Confirmed shell-level visual direction

The available maintainer handoff supports these shell-level decisions:

- the primary stage is visually dominant;
- the rail is restrained and secondary to the work object;
- the sidecar and dock yield space rather than remaining permanently expanded;
- technical overlays must be sober and information-bearing;
- an engineering grid, callout, or instrument tag is permitted only when tied to real stage data or clearly labelled diagnostic scaffolding;
- the shell must feel like a premium engineering tool, not a generic SaaS dashboard, gaming HUD, consumer app, or corporate portal;
- comprehension, workflow correctness, prevention of operator error, and accessibility outrank decoration;
- glow, glassmorphism, ornamental charts, fake telemetry, cockpit density, tiny text, and permanently open dashboards are excluded.

The companion visual decision record lists unresolved identity inputs. Those unresolved values must not be guessed in implementation.

## 11. Accessibility contract

The eventual implementation must provide:

- one skip link to the main stage/content region;
- semantic landmarks for header, primary navigation, main content, complementary sidecar, and dock where open;
- link semantics for URL navigation;
- `aria-current` for the active primary destination;
- visible text labels for navigation and panel toggles;
- visible `:focus-visible` treatment using 070 roles in both themes;
- deterministic focus restoration after route changes, panel close, and not-found recovery;
- keyboard reachability of rail, stage controls, navigator, sidecar, dock, appearance control, and all direct legacy links;
- no hover-only action or state explanation;
- status and availability meaning conveyed with text/shape/pattern, not color alone;
- reduced-motion behavior for rail/panel transitions;
- no focus trapped in closed or inert shell regions;
- no automatic sidecar/dock opening that steals focus;
- document title and main heading updated for the current route;
- route changes announced through ordinary heading/focus behavior rather than a noisy global live region.

## 12. Responsive and zoom contract

083 remains desktop-first, not mobile-first.

Binding outcomes:

- the primary stage uses `minmax(0, 1fr)` or equivalent shrink-safe layout behavior;
- rail, navigator, sidecar, and dock must not force document-level horizontal overflow;
- wide tables and technical viewports retain local overflow ownership;
- at 200% browser zoom, all production shell and legacy routes remain reachable and operable;
- at one compact desktop width, visible-text navigation remains available without an icon-only dependency;
- when horizontal space is insufficient, secondary regions collapse, overlay, or stack according to an explicit priority: primary stage first, rail/navigation second, contextual sidecar third, analysis dock last;
- no content is clipped solely to preserve the desktop composition;
- the real BLUECAD compatibility-mounted page and GLB viewer remain usable without page-level horizontal overflow;
- open/close controls remain reachable after reflow.

Exact breakpoints and dimensions are intentionally not frozen by this kernel because the visual reference pack is incomplete. The full spec must define measured acceptance widths without inventing a global identity system.

## 13. Transition and continuity contract

The 083 implementation is acceptable only if all current behavior remains reachable during migration.

Required continuity:

- current page components remain in the repository;
- current API calls and response handling remain unchanged unless the full spec identifies a proven shell-only correction;
- current BLUECAD is mounted through the ModelStage compatibility adapter;
- all current BLUECAD actions, validation/attempt data, archive, retry, promotion, artifacts, and real GLB behavior remain available;
- current Domain Foundation records/scenario/run behavior remains available under `/legacy/domain-foundation`;
- current AI task, settings, secret-status, smoke, and draft behavior remains available under `/legacy/ai-draft` with `Legacy diagnostic surface` labelling;
- current System Status remains available under `/legacy/system-status` with `Legacy diagnostic surface` labelling;
- development-only chat remains development-only;
- legacy routes stay outside primary navigation;
- no working function is hidden behind an unavailable future stage;
- no fake replacement is presented as equivalent to a working current page;
- removal of a legacy route requires the competent page spec to prove equivalent or better behavior.

## 14. Security, privacy, and economic boundaries

083 must not:

- add secrets to frontend state, browser storage, logs, URLs, screenshots, fixtures, or repository files;
- render raw credential values;
- call providers directly;
- add provider/model selection to shell chrome;
- change `run_ai_task`, egress, budget, reservation, ledger, confirmation, or policy behavior;
- infer zero cost when cost is unavailable;
- display fake online/agent presence;
- serialize selected engineering records or conversation content into browser storage;
- add analytics or telemetry egress;
- add a service worker or offline cache of sensitive responses;
- add a second API client or backend.

## 15. Non-goals

083 does not implement:

- a global visual identity rewrite;
- page redesign beyond shell wrapping, compatibility mounting, and explicit legacy labels;
- full BLUECAD migration;
- candidate aggregate endpoints;
- model inspection tools;
- semantic scene selection;
- lineage graph;
- run workbench;
- engineering-data search/navigation;
- analytics widgets;
- AI threads or persistence;
- Jarvis conversational behavior;
- Settings migration;
- proposal review workflow;
- editable flowsheet;
- runtime plugin system;
- command palette;
- global state framework;
- new backend endpoints, schema, migrations, services, or stores;
- provider, credential, budget, ledger, or egress changes;
- mobile-first redesign;
- GRADE-0;
- changes to frozen specs 066–068 or 080.

## 16. Definition acceptance criteria

This kernel may be considered successfully merged when:

1. it records the exact derivation SHA;
2. it records the current page/transition inventory;
3. it defines shell, stage, selection, legacy continuity, accessibility, responsive, security, non-goal, and rollback boundaries;
4. it preserves the exact 081 legacy diagnostic route names and visible label requirement;
5. it mounts current BLUECAD through a ModelStage compatibility adapter rather than replacing it with a handoff;
6. it classifies visual requirements A/B/C/D;
7. it records Route 3 and does not freeze unsupported identity values;
8. it does not modify runtime code or mark 083 ready;
9. it does not place a definition PR in the registry's Implementation PR column;
10. it does not alter another spec row or queue order.

## 17. Requirements for the later full-spec revision

Before 083 can enter readiness, a later definition revision must:

- re-read exact `master` and all open PRs/branches;
- resolve the remaining visual decision items in the companion record or explicitly assign them to a separately authorized visual-identity lane;
- choose and justify native routing versus a router dependency;
- freeze the exact route table, redirects/aliases, not-found behavior, and development-route behavior;
- freeze the shell component/state ownership map and BLUECAD compatibility-adapter seam;
- define exact responsive evidence widths and 200% zoom procedure;
- define exact focus restoration behavior;
- define which existing health/status calls, if any, top-bar chrome may use;
- define the complete implementation file set;
- define a deterministic shell checker or equivalent evidence strategy;
- define exact acceptance tests for browser history, refresh, unknown routes, legacy continuity, sidecar/dock defaults, and no global overflow;
- confirm no 084–092 or re-derived 029/035/054/058c scope has entered the implementation;
- confirm dependencies 006 and 070 remain merged;
- keep 083 `planned` until a separate readiness audit promotes it.

## 18. Preliminary implementation evidence plan

The later full spec must require at least:

### Deterministic/static evidence

- exact primary route table and required legacy diagnostic route inventory check;
- exact visible `Legacy diagnostic surface` labelling for required legacy pages;
- no `/legacy/*` route in primary navigation;
- current BLUECAD imported exactly once through the ModelStage compatibility seam;
- no disallowed dependency/store/backend/provider imports;
- static stage registry contains exactly four allowed stage kinds;
- FlowsheetStage contains an explicit unavailable state and no editable canvas behavior;
- appearance storage remains the only browser-storage contract;
- production build succeeds;
- repository-standard backend/BLUECAD gates remain green because frontend changes must not regress them.

### Browser evidence

- direct load and refresh of every production shell and required legacy diagnostic route;
- browser back/forward across shell and legacy routes;
- unknown-route recovery;
- keyboard-only navigation and visible focus in system/light/dark;
- live system theme behavior remains intact;
- navigator, sidecar, and dock initial closed/compact states;
- no focus loss when panels close;
- 200% zoom on shell home, each stage route, compatibility-mounted BLUECAD, and one dense legacy diagnostic page;
- compact desktop width on the same set;
- no document-level horizontal overflow; local table/viewer overflow remains local;
- real BLUECAD candidate, validation/attempt data, and real GLB viewer available in ModelStage when runtime data exists;
- backend unavailable state without false success;
- development-only route absent/unavailable in a production build.

No screenshot may contain secrets, provider responses, private engineering content, or credential-derived values.

## 19. Rollback and removability boundary

083 must be independently removable.

A compliant rollback can:

1. restore the prior `App.tsx` component-state page switcher and `Layout.tsx` sidebar;
2. remove shell-only route, stage, navigator, sidecar, dock, and compatibility-adapter components;
3. retain all current pages, API client functions, 070 appearance/theme utilities, 070 primitives, BLUECAD viewer, and backend behavior;
4. remove no database record and require no backend migration;
5. leave no browser-stored shell state to migrate.

Stop and return 083 to `planned` or `blocked` if implementation would require:

- changing backend authority or adding a second store;
- losing any current legacy or BLUECAD behavior;
- treating geometry hits as stable records;
- faking a future stage capability;
- adding unreviewed global visual identity changes;
- adding a dependency without minimum-necessary evidence;
- persisting shell or engineering state outside the backend;
- changing Three.js internals or BLUECAD lifecycle before the competent spec;
- absorbing 084–092 or re-derived 029/035/054/058c work.

## 20. Readiness status

**Not ready.**

The current blockers are definition blockers, not implementation defects:

1. the available visual handoff does not contain inspectable image/font/palette assets sufficient to freeze a global identity or explicitly separate it from 083 through a queue decision;
2. the routing implementation choice has not yet been justified by a bounded comparison;
3. the exact implementation file set and deterministic shell-check strategy are not yet frozen;
4. the full browser evidence matrix still needs exact widths and route-by-route acceptance steps.

No runtime implementation is authorized by this kernel.