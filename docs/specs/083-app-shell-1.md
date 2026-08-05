# Spec 083 — APP-SHELL-1

**Definition status:** definition kernel; not a complete implementation contract and not readiness-authorizing.

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

**Definition route:** Route 3. Shell architecture and continuity are sufficiently evidenced. Global visual identity is not, because no inspectable image/font/palette asset pack was available in this definition pass. This kernel freezes no global font, palette, component grammar, icon system, or motion language.

---

## 1. Purpose

Define the smallest durable desktop-first shell that can replace the current component-state page switcher without changing backend authority, losing current functionality, or absorbing work assigned to specs 084–092 and re-derived 029, 035, 054, and 058c.

The eventual 083 implementation must provide:

- URL-backed navigation with refresh and browser-history continuity;
- one shell with rail, top bar, dominant stage, contextual navigator, one sidecar slot, and an analysis dock closed by default;
- a static registry containing exactly ModelStage, ResultsStage, ReviewStage, and FlowsheetStage;
- current real BLUECAD mounted inside ModelStage through a compatibility adapter until 085 replaces it;
- explicit legacy diagnostic routes for non-migrated current pages;
- honest unavailable or migration-pending states for later capabilities;
- keyboard, focus, reduced-motion, 200% zoom, compact-desktop, and overflow behavior built on 070;
- no backend, provider, credential, budget, ledger, egress, MemoryStore, BLUECAD lifecycle, or Three.js authority change.

This canonical target path is intentionally used for the kernel so the later full-spec revision is an auditable diff, not a parallel specification.

## 2. Exact-master facts

Verified on the exact baseline:

1. `frontend/src/App.tsx` uses `useState<AppPage>` to switch among six pages. No URL routing, refresh persistence, history, or deep-link contract exists.
2. `frontend/src/components/Layout.tsx` owns the transitional fixed sidebar, page buttons, and 070 appearance control.
3. `frontend/package.json` has React, React DOM, Three.js, TypeScript, and Vite only; no router, state library, UI framework, icon package, or frontend test framework.
4. `frontend/src/main.tsx` applies the stored appearance before mount and imports `tokens.css`, `global.css`, `foundation.css`, and `responsive.css` in that order.
5. `global.css` remains a large hard-coded legacy stylesheet; `foundation.css` and `responsive.css` provide bounded semantic and containment overlays.
6. Spec 070 provides semantic light/dark roles, exactly `system`/`light`/`dark`, enum-only versioned persistence, live system-theme updates and cleanup, five typed primitives, focus-visible treatment, non-color state distinctions, reduced motion, and responsive containment.
7. `BlueCAD.tsx` exposes real candidates, archive, retry/duplicate, promotion, validation, attempts, artifacts, and a real GLB viewer.
8. `BluecadGlbViewer.tsx` provides real Three.js loading, orbit, pan, zoom, resize handling, and cleanup, but no stable semantic part-selection contract.
9. `DomainFoundation.tsx` combines current workspace, record, scenario, binding, runner, run, and decision behavior.
10. `AIDraft.tsx` combines AI execution, routes, settings, credential status/actions, smoke diagnostics, escalation, and modeling draft behavior. It is not the future Jarvis sidecar.
11. `SystemStatus.tsx` exposes backend, storage, AI, provider, budget, and diagnostics.
12. `DevLocalChat.tsx` is development-only, non-production, and non-persistent.
13. `frontend/src/api/client.ts` remains the shared frontend HTTP/type surface.
14. PR #225 stopped before router/shell work. PR #227 reconciled 070 and left 083 as the next `planned` slice.
15. No full spec, readiness record, branch, PR, or open issue for 083 existed at derivation time.

Movement of `master` before the full-spec revision or readiness requires a fresh exact-SHA audit.

## 3. Authority and state boundaries

### 3.1 Backend authority

FastAPI + SQLite remain authoritative for durable engineering state, lifecycle/status, provider routing through `run_ai_task`, credentials, budget/spend/ledger/egress/audit, MemoryStore proposal/promotion boundaries, BLUECAD candidates/evidence/artifacts/promotion, and runner/simulation-run records.

The shell may display or navigate to backend-owned state. It must not reinterpret, duplicate, persist, or mutate it outside existing API contracts.

### 3.2 Allowed transient shell state

083 may own only:

- current URL route;
- rail/navigator/sidecar/dock open state;
- stage kind derived from the URL;
- transient `StageSelection`;
- focus restoration targets;
- non-authoritative temporary view state.

Only the 070 appearance enum may remain in browser storage. 083 must not persist shell layout, workspace, record selection, geometry selection, prompts, results, secrets, engineering values, conversation state, or navigation authority in `localStorage`.

### 3.3 No second store

No Redux, Zustand, MobX, XState, second engineering store, or backend mirror. A bounded React context is permitted only if the full spec proves that ordinary composition is materially worse and the context owns transient shell state only.

## 4. Current page transition map

| Current page | Behavior to preserve | 083 treatment |
| --- | --- | --- |
| `Dashboard` | backend health and current foundation summary | `/home` compatibility content or a proven equivalent using the same real inputs |
| `SystemStatus` | backend/storage/AI/provider/budget diagnostics | `/legacy/system-status` |
| `DomainFoundation` | combined records/scenarios/bindings/runs/decisions | `/legacy/domain-foundation` |
| `BlueCAD` | complete current lifecycle and real GLB viewer | compatibility-mounted inside ModelStage |
| `AIDraft` | AI task/settings/credential/smoke/draft surface | `/legacy/ai-draft`; never Jarvis sidecar |
| `DevLocalChat` | development-only local-chat diagnostic | development-only legacy route |

Current components and API behavior remain intact. Wrapping and explicit transitional labels are allowed; silent product relabelling is not.

## 5. Route contract

### 5.1 Shell and primary-navigation routes

```text
/                         -> deterministic redirect to /home
/home                     -> real current home/health compatibility content
/design/model             -> ModelStage + current BLUECAD compatibility adapter
/design/results           -> ResultsStage honest unavailable/legacy handoff
/runs                     -> migration-pending product route with access to current scenario/run surface
/engineering-data         -> migration-pending product route with access to current domain-record surface
/review                   -> ReviewStage honest unavailable/legacy handoff
/settings                 -> migration-pending product route with access to current diagnostics
/design/flowsheet         -> FlowsheetStage honest unavailable state
```

Primary navigation is limited to:

```text
Home
Design
Runs
Engineering Data
Review
Settings
```

Legacy route names are not primary-navigation destinations. Migration and availability status must be visible in text, not color alone.

### 5.2 Required legacy diagnostic routes

Spec 081 requires:

```text
/legacy/domain-foundation
/legacy/ai-draft
/legacy/system-status
```

Each route must:

- display the exact visible label `Legacy diagnostic surface`;
- remain directly URL-reachable;
- stay outside primary navigation;
- remain inside the application shell and `PageErrorBoundary`;
- preserve current backend authority;
- be removed only by the competent replacement spec.

Additional current-page continuity may expose:

```text
/legacy/dev-local-chat    -> development-only; absent or explicitly unavailable in production
```

A `/legacy/bluecad` compatibility alias may redirect to `/design/model` only if existing-link or browser evidence requires it. It must never create a second independently evolving BLUECAD implementation.

No migrated function may remain indefinitely in two primary-navigation locations.

### 5.3 Route behavior

- direct load and refresh preserve the requested production route;
- back/forward works across shell and legacy routes;
- unknown routes render a bounded not-found state with recovery links;
- development-only routes do not leak a production capability;
- no route bypasses `PageErrorBoundary`;
- route changes do not reset the 070 appearance preference;
- geometry-hit selection never enters the URL.

### 5.4 Router decision boundary

URL behavior is required; no router dependency is authorized yet.

The full definition/readiness cycle must compare:

1. a small static route table using native History API + `popstate`;
2. one mature router dependency.

No dependency is the default. A router package requires exact evidence that native routing would create materially more bespoke parsing, history, accessibility, or test complexity, plus recorded version, license, and transitive footprint.

## 6. Shell layout contract

```text
ApplicationShell
├── SkipLink
├── TopBar
├── Rail
├── WorkspaceRegion
│   ├── ContextualNavigator (closed or compact by default)
│   ├── PrimaryStageRegion (dominant)
│   └── ContextualSidecar (one slot; closed without applicable context)
└── AnalysisDock (closed by default)
```

### 6.1 Top bar

Allowed real shell-level information:

- JarvisOS identity;
- current route/stage title;
- selected record label only for a real record selection;
- backend checking/available/unavailable derived from an existing health contract;
- the existing 070 appearance control or an equivalent accessible placement.

Forbidden: fake agent presence, invented telemetry, decorative budget meters, synthetic online indicators, provider/model selection, or assumed status.

### 6.2 Rail

The rail must use link semantics, expose the current destination with `aria-current="page"`, keep visible text at compact desktop unless a later reviewed icon system exists, require no hover, exclude `/legacy/*`, and avoid provider/model navigation.

Legacy routes may be linked from migration-pending content or a secondary diagnostics index, never as peer primary destinations.

### 6.3 Contextual navigator

083 owns only container behavior: open/close, focus management, title, compact default, empty/unavailable state, and route-aware handoffs.

It must not implement candidate aggregates, lineage trees, run browsers, Engineering Data search, assembly trees, or scene semantics. Those belong to 084, 087, 088, re-derived 035, 092, or other competent specs.

### 6.4 Contextual sidecar

There is exactly one right-side secondary slot for future inspector or Jarvis modes, never two permanent right columns.

083 may implement closed state, one accessible toggle, honest empty/unavailable content, and a selected-record summary only from a real typed record reference.

It must not implement threads, role profiles, context packaging, provider selection, AI presence, autonomous behavior, proposals, or full Jarvis behavior.

### 6.5 Analysis dock

Closed on initial and fresh route load. 083 owns only shell chrome, toggle, focus management, and honest migration-pending content. Charts, comparisons, analytics persistence, and metric semantics belong to 089.

## 7. Static PrimaryStage contract

The compile-time registry contains exactly:

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
```

Binding invariants:

- exactly ModelStage, ResultsStage, ReviewStage, FlowsheetStage;
- no runtime registration or plugin loader;
- no backend/provider-owned stage IDs;
- no stage-specific engineering store;
- stage kind is URL-derived;
- toolbar/status chrome uses explicit typed composition, not DOM discovery;
- stage-specific view state remains local until a later spec proves a shared contract.

### 7.1 ModelStage

083 mounts current `BlueCAD` through one bounded compatibility adapter.

The adapter preserves all current actions/API calls, real GLB behavior, viewer internals, validation, attempts, archive, retry/duplicate, artifacts, and promotion. It adds only shell/compatibility boundaries, creates no second BLUECAD state/page, remains removable by 085, and implements no 084/086/092 behavior.

### 7.2 ResultsStage

Stage frame plus honest unavailable/legacy handoff only. Real run result browsing and comparison belong to 088/089.

### 7.3 ReviewStage

Stage frame plus honest unavailable/legacy handoff only. Proposal review belongs to re-derived 054 and must not bypass the operator-design boundary.

### 7.4 FlowsheetStage

Must state that editable flowsheets are unavailable, direct the operator to the real Runs surface, and identify Lineage as future 087 work.

No draggable fake nodes, simulated streams, editable connections, fake solver status, blank product canvas, runtime plugin system, or second graph store.

## 8. Selection contract

083 adopts the exact 081 A0 distinction:

```ts
type StageSelection =
  | {
      kind: "record";
      ref: RecordRef;
    }
  | {
      kind: "geometry-hit";
      viewerSessionId: string;
      ephemeralObjectId: string;
      point?: [number, number, number];
    };
```

`RecordRef` is an existing/future canonical typed reference boundary, not defined ad hoc by this kernel. The full spec must identify its authoritative frontend source or define the minimum typed reference from existing backend contracts without creating a parallel record schema.

Rules:

- geometry hits have no `RecordRef` or `sceneComponentId`;
- they are session-scoped, non-persistent, non-evidence, non-promotion, and non-semantic;
- clear them when the viewer session ends or the artifact reloads;
- never infer identity from Three.js UUID, object name, traversal index, material, mesh order, or pointer hit;
- consumers exhaustively discriminate the union;
- 092 and re-derived 058c own stable scene binding and semantic selection.

## 9. Visual scope and Route 3

### A — 083

Shell geometry, rail/top-bar hierarchy, dominant stage, navigator/sidecar/dock placement and closed defaults, route/stage indication, shell-level semantic type hierarchy, shell chrome, responsive/zoom behavior, BLUECAD compatibility mounting, and honest legacy/unavailable/migration states.

### B — reuse 070

Semantic tokens, system/light/dark, enum-only persistence, pre-mount/live theme behavior, focus, keyboard access, reduced motion, Button/Surface/StatusBadge/Field/InlineNotice, non-color states, and containment/local overflow.

### C — separate visual-identity lane

Global font, cross-page palette, border/line/radius/shadow/surface/control/table/badge grammar, icon/assets, global motion, non-shell page redesign, and wholesale legacy-style removal.

### D — future page specs

084 candidate read model; 085 BLUECAD workbench; 086 inspection; 087 lineage; 088 runs; re-derived 035 Engineering Data; 089 analytics; 090 threads; 091 Jarvis; 092 scene binding; re-derived 029 Settings; re-derived 054 proposal review; re-derived 058c semantic scene tools.

### Confirmed shell direction

Dominant stage, restrained rail, secondary regions that yield space, sober information-bearing overlays, premium engineering-tool character, workflow/error/accessibility priority, and no glow, glassmorphism, ornamental charts, fake telemetry, cockpit density, tiny text, or permanently open dashboards.

The companion visual decision record contains unresolved identity inputs. Implementation must not guess them.

## 10. Accessibility and responsive contract

Required:

- skip link;
- semantic header/navigation/main/complementary landmarks;
- link semantics and `aria-current`;
- visible text labels and 070 `:focus-visible` in both themes;
- deterministic focus restoration after route change, panel close, and not-found recovery;
- keyboard reachability of all shell controls and direct legacy links;
- no hover-only behavior or color-only meaning;
- reduced-motion panel behavior;
- no focus in closed/inert regions and no focus-stealing auto-open;
- route-specific document title and main heading;
- `minmax(0, 1fr)` or equivalent shrink-safe stage layout;
- no document-level horizontal overflow;
- local overflow for wide tables and technical viewports;
- production shell/legacy usability at 200% zoom;
- one compact desktop width with visible-text navigation;
- reflow priority: stage, rail/navigation, sidecar, dock;
- real compatibility-mounted BLUECAD/GLB usability after reflow.

Exact dimensions and breakpoints remain for the full spec because the visual asset pack is incomplete.

## 11. Transition continuity

- current page components remain;
- current API calls/response handling remain unless a proven shell-only correction is specified later;
- current BLUECAD mounts in ModelStage and preserves every real lifecycle/viewer behavior;
- `/legacy/domain-foundation`, `/legacy/ai-draft`, and `/legacy/system-status` preserve current behavior with the exact legacy label;
- dev chat stays development-only;
- legacy routes stay outside primary navigation;
- no working function is hidden behind an unavailable future stage;
- no fake replacement is equivalent to a working current page;
- only the competent page spec may remove a legacy route after replacement proof.

## 12. Security, privacy, and economic boundaries

083 must not add secrets to frontend state/storage/logs/URLs/screenshots/fixtures/repository; render raw credentials; call providers directly; add shell provider/model selection; change `run_ai_task`, egress, budget, reservation, ledger, confirmation, or policy; represent unavailable cost as zero; persist engineering or conversation state; add telemetry egress/service-worker sensitive caches; or create a second API client/backend.

## 13. Non-goals

No global identity rewrite, deep page redesign, full BLUECAD migration, candidate aggregate endpoint, inspection, semantic selection, lineage, run workbench, Engineering Data search, analytics, threads, Jarvis behavior, Settings migration, proposal review, editable flowsheet, plugin system, command palette, global state framework, backend/schema/migration/service/store work, provider/credential/budget/ledger/egress work, mobile-first redesign, GRADE-0, or changes to frozen 066–068/080.

## 14. Kernel acceptance criteria

This definition PR is acceptable only if it:

1. records exact derivation authority;
2. inventories current pages and transition ownership;
3. defines route, shell, stage, selection, continuity, accessibility, responsive, security, non-goal, and rollback boundaries;
4. preserves exact 081 legacy route names and `Legacy diagnostic surface` label;
5. mounts current BLUECAD through ModelStage compatibility rather than replacing it with a handoff;
6. uses 081's type distinction without inventing a canonical `RecordRef` shape;
7. classifies visual scope A/B/C/D and records Route 3;
8. changes no runtime or registry state;
9. places no definition PR in the Implementation PR column;
10. changes no other queue row or order.

## 15. Full-spec requirements before readiness

A later exact-master definition revision must:

- resolve visual identity as shell-bounded Route 1 or separately authorized Route 2;
- choose native routing or justify one router dependency;
- freeze routes, redirects/aliases, not-found and dev behavior;
- bind the authoritative `RecordRef` source;
- freeze shell state/component ownership and BLUECAD compatibility seam;
- define exact compact width, zoom procedure, focus restoration, and top-bar data calls;
- define exact implementation files and a deterministic checker/evidence strategy;
- define route-by-route browser acceptance;
- prove no 084–092 or re-derived 029/035/054/058c scope absorption;
- re-confirm 006 and 070 merged;
- keep 083 `planned` until separate readiness promotion.

## 16. Preliminary evidence plan

### Static/deterministic

- exact route and required legacy inventory;
- exact legacy label;
- no `/legacy/*` primary-navigation item;
- current BLUECAD imported once through the compatibility seam;
- exactly four static stage kinds;
- no disallowed dependency/store/backend/provider import;
- FlowsheetStage unavailable and no fake canvas;
- only 070 appearance storage;
- frontend production build;
- repository-standard backend and BLUECAD gates.

### Browser

- direct load/refresh/back/forward/unknown-route recovery;
- keyboard/focus in system/light/dark and live system-theme continuity;
- navigator/sidecar/dock initial defaults and close-focus restoration;
- 200% zoom and compact desktop on home, stages, BLUECAD, and one dense legacy diagnostic page;
- no global overflow and preserved local table/viewer overflow;
- real BLUECAD candidate/validation/attempt/GLB when runtime data exists;
- honest backend-unavailable state;
- dev route absent/unavailable in production.

No screenshot may expose secrets, provider responses, private engineering content, or credential-derived values.

## 17. Rollback and readiness

A compliant rollback restores prior `App.tsx` page switching and `Layout.tsx`, removes shell/route/stage/panel/adapter code, retains all current pages/API/070/BLUECAD/backend behavior, requires no database migration, and leaves no shell browser-storage migration.

Stop and return 083 to `planned` or `blocked` if implementation requires backend/store authority change, behavior loss, semantic promotion of geometry hits, fake capability, unreviewed global identity, unjustified dependency, non-backend persistence, Three.js/BLUECAD lifecycle change, or 084–092/re-derived-scope absorption.

**Readiness: not ready.**

Current definition blockers:

1. global visual identity is not supported by inspectable assets or explicitly separated by a queue decision;
2. router choice lacks bounded evidence;
3. implementation file set and deterministic shell check are not frozen;
4. exact responsive widths and route-by-route browser matrix are not frozen.

No runtime implementation is authorized by this kernel.