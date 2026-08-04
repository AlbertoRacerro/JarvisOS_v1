# Spec 070 — UI-FOUNDATION-1

**Definition status:** complete implementation contract; registry remains `planned` until a separate readiness decision.

**Depends on:** 006, 082, 094

**Authority:** spec 081 FRONTEND-BETA-AUTHORITY-0 and the accepted 082/094 Windows checkpoint.

**Target path:** `docs/specs/070-ui-foundation-1.md`

**Historical input:** closed PR #132 and its retained branch are non-authoritative evidence only.

---

## 1. Purpose

Create the smallest durable visual and interaction foundation required by the JarvisOS frontend-beta queue without implementing the application shell owned by spec 083 or changing any backend authority.

After 070:

- foundational appearance values come from semantic design tokens rather than repeated literals;
- JarvisOS supports exactly `system`, `light`, and `dark` appearance preferences;
- the current operator interface has an accessible appearance control;
- a narrow set of repeated UI primitives has one typed implementation;
- current pages retain their actions, data, errors, evidence, BLUECAD lifecycle, and GLB rendering;
- later frontend slices can build on one visual contract rather than adding more feature-local foundation CSS.

070 is not a shell rewrite, navigation project, settings page, component platform, or product-workflow redesign.

## 2. Exact baseline and current facts

This definition is derived from:

```text
repository: AlbertoRacerro/JarvisOS_v1
branch: master
commit: 98063ab160562d7306e652c9586740ba641c95ff
```

The baseline has the accepted 082/094 checkpoint, with 082 and 094 `merged`. No other implementation front is active.

Current frontend facts verified on that baseline:

1. `frontend/package.json` contains React 18, React DOM, TypeScript, Vite, and Three.js only. There is no UI framework, router, state library, CSS processor, icon package, Storybook, or frontend test framework.
2. `frontend/src/main.tsx` mounts `App` and imports one stylesheet, `frontend/src/styles/global.css`.
3. `frontend/src/App.tsx` selects pages through component state. URL routing and deep-link authority do not exist and belong to 083.
4. `frontend/src/components/Layout.tsx` owns the current fixed sidebar and page buttons. Its navigation structure is transitional and must not be redesigned by 070.
5. `global.css` contains shell, page, form, table, AI, development-chat, scenario, BLUECAD, viewer-container, status, warning, and responsive rules in one file. Colors, borders, radii, spacing, typography, and interaction states are repeated extensively.
6. Current UI code contains no `localStorage` use. 070 therefore introduces only one narrowly typed appearance preference.
7. `BluecadGlbViewer.tsx` uses hard-coded Three.js scene, light, grid, and background values. Those renderer-internal values are technical rendering inputs, not ordinary CSS design tokens.
8. Existing pages already expose real backend data and workflows. 070 must preserve them rather than replacing them with mock content.
9. `PageErrorBoundary` and several page-local empty, warning, loading, disabled, and error states already exist, but their markup and styling are inconsistent.
10. The product remains Windows-first, local-first, single-user, loopback-first, and desktop-first.

Any material movement of `master` before readiness requires rechecking these facts and the likely file set in section 13.

## 3. Binding product direction

The visual language is a restrained engineering workspace:

- dark chlorophyll identity for shell-oriented surfaces;
- neutral technical work surfaces;
- high information density without cramped controls;
- restrained green/cyan accent use;
- semantic warning, danger, success, information, neutral, proposed, stale, unavailable, and archived states;
- explicit text, icons, borders, or patterns so state is never conveyed by hue alone;
- unit-bearing values and evidence remain more prominent than decoration;
- no neon glow, glassmorphism, fake holograms, animated background effects, ornamental charts, or consumer-dashboard styling.

Visual treatment must not make provisional, stale, synthetic, parked, failed, unpriced, unavailable, or unverified state appear canonical or successful.

## 4. Architecture boundary

070 reuses the existing React/Vite/TypeScript frontend and ordinary CSS.

It must not add:

- a second frontend stack;
- a router or URL-state model;
- Redux, Zustand, MobX, XState, or another state framework;
- a UI/component framework;
- CSS-in-JS;
- Sass, Tailwind, PostCSS plugins, or a token build pipeline;
- Storybook or a visual-test platform;
- an icon dependency;
- a form library;
- a frontend test framework solely for this slice;
- backend routes, schemas, migrations, settings, secret handling, or provider calls;
- runtime plugin registration;
- direct provider, filesystem, SQLite, local-model, runner, or tool access from the frontend.

The initial implementation uses CSS custom properties, typed React components, native HTML semantics, and a dependency-free static checker.

## 5. Token contract

Add one authoritative token stylesheet:

```text
frontend/src/styles/tokens.css
```

It owns these layers:

1. primitive palette values;
2. semantic color roles;
3. typography roles;
4. spacing and control sizing;
5. radii and borders;
6. elevation;
7. current-layout measurements needed by existing surfaces;
8. motion duration and easing.

Token names express roles, never pages or features.

Required semantic roles include at least:

```text
--color-bg-canvas
--color-bg-shell
--color-bg-surface
--color-bg-surface-raised
--color-bg-subtle
--color-bg-technical-viewport
--color-text-primary
--color-text-secondary
--color-text-muted
--color-text-inverse
--color-border-default
--color-border-strong
--color-accent-primary
--color-accent-hover
--color-focus-ring
--color-status-info-bg
--color-status-info-text
--color-status-success-bg
--color-status-success-text
--color-status-warning-bg
--color-status-warning-text
--color-status-danger-bg
--color-status-danger-text
--color-status-neutral-bg
--color-status-neutral-text
--color-status-proposed-bg
--color-status-proposed-text
--color-status-stale-bg
--color-status-stale-text
--color-status-unavailable-bg
--color-status-unavailable-text
```

Required non-color roles include at least:

```text
--font-sans
--font-mono
--font-size-body
--font-size-label
--font-size-caption
--font-size-section-title
--font-size-page-title
--line-height-body
--space-1 through --space-8
--control-height-compact
--control-height-default
--radius-sm
--radius-md
--radius-pill
--border-width-default
--shadow-raised
--motion-fast
--motion-standard
--ease-standard
```

Rules:

- `tokens.css` may contain raw color, radius, shadow, duration, and easing values.
- migrated foundation styles and shared primitives consume semantic variables.
- no token may be named for BLUECAD, Settings, AI Draft, Dashboard, a specific status string, or another page.
- a zero-literal rewrite of all legacy feature CSS is not required.
- new raw design literals are forbidden in the files newly created by 070 and in selectors explicitly migrated by 070, except transparent values and documented Three.js rendering constants.

## 6. Appearance contract

Support exactly:

```ts
type AppearancePreference = "system" | "light" | "dark";
type ResolvedAppearance = "light" | "dark";
```

Expected utility:

```text
frontend/src/theme.ts
```

The utility owns:

- validation of stored values;
- safe default to `system`;
- resolution of `system` through `prefers-color-scheme`;
- one `data-theme="light|dark"` attribute on `document.documentElement`;
- consistent CSS `color-scheme`;
- system-preference subscription only while preference is `system`;
- complete listener cleanup;
- safe behavior when storage or `matchMedia` is absent, inaccessible, or throws;
- application before or at the initial React mount so the app does not deliberately flash the wrong theme.

Persistence is limited to one versioned local-storage key containing only the three-value enum.

It must never contain:

- secrets or key fragments;
- provider configuration;
- budgets or usage;
- prompts or responses;
- workspace, record, run, candidate, artifact, flow, ticket, or decision data;
- navigation authority;
- serialized component or shell state.

`system` is a preference, not a third palette.

## 7. Theme requirements

### 7.1 Dark

Dark appearance provides:

- chlorophyll/dark-green identity on shell-oriented surfaces;
- dark neutral canvas and technical surfaces;
- clearly distinguishable raised surfaces without excessive shadows;
- readable borders and muted text;
- restrained accents;
- status pairs that retain meaning and contrast;
- no pure-black large surface unless technically justified.

### 7.2 Light

Light appearance provides:

- neutral technical canvas;
- dark readable text;
- restrained chlorophyll identity;
- visible surface boundaries;
- the same semantic state meanings as dark appearance.

### 7.3 Technical viewport

The BLUECAD viewer container uses `--color-bg-technical-viewport` and shared border/radius roles.

The Three.js scene background, lights, grid, camera, materials, and renderer behavior remain unchanged in 070. A later viewer specification may deliberately theme renderer internals only with visual and geometry-regression evidence.

## 8. Operator appearance control

Add one compact accessible appearance control to the current `Layout` without redesigning navigation.

It may be a native select, radio group, or three-state menu. It must:

- expose an explicit accessible name;
- show the current preference in text or programmatic state;
- be keyboard operable;
- avoid icon-only ambiguity;
- update immediately;
- perform no backend or network call;
- preserve current page selection;
- follow live OS changes in `system` mode;
- remain reachable at compact desktop widths and 200% browser zoom.

It is not the Settings page owned by spec 029.

## 9. Shared primitives

Create only primitives justified by repeated current markup.

Required initial set:

```text
Button
Surface
StatusBadge
Field
InlineNotice
```

Expected location:

```text
frontend/src/components/ui/
```

### 9.1 Button

Variants:

```text
primary
secondary
ghost
danger
```

It renders a native `button`, forwards standard attributes and refs where needed, preserves `type`, disabled semantics, and visible focus, and owns no loading state beyond presentation supplied by the caller.

### 9.2 Surface

A bounded panel/card wrapper with native element selection limited to justified semantic cases. It must not become a generic polymorphic component system.

### 9.3 StatusBadge

Represents semantic state with visible text and a semantic tone. Tone and backend status value remain separate: callers map their domain state explicitly rather than passing arbitrary class names.

### 9.4 Field

Associates label, native control, hint, required state, and error text through stable IDs and ARIA relationships. It does not own form validation or form state.

### 9.5 InlineNotice

Tones:

```text
info
success
warning
danger
neutral
```

It preserves text content and may use a fixed non-decorative prefix or icon only when meaning remains available to assistive technology.

Each primitive:

- uses native semantics;
- forwards appropriate native attributes;
- exposes visible `:focus-visible` behavior where interactive;
- imports no API client, service, router, page, backend type, or business rule;
- owns no application state or persistence;
- adds no dependency beyond React.

Not authorized in 070:

- modal/dialog framework;
- generic table abstraction;
- tooltip system;
- command palette;
- tabs framework;
- toast queue;
- data grid;
- icon library;
- design-system documentation site.

## 10. Bounded migration

Migrate only enough current surfaces to prove the contract while preserving behavior.

Required migration targets:

1. root/body canvas and typography;
2. current sidebar colors, text, nav buttons, borders, and focus treatment without changing its structure;
3. page canvas, page header, common panel/surface, and metric-card foundation roles;
4. repeated primary and secondary button styling used by at least two current pages;
5. repeated input/select/textarea and label roles used by at least two current pages;
6. repeated error and warning banners through `InlineNotice` where replacement is behavior-preserving;
7. repeated status pill/badge presentation through `StatusBadge` for at least one real backend status family;
8. BLUECAD viewer container CSS only;
9. `PageErrorBoundary` visual treatment without changing error capture or logging behavior;
10. one existing empty, loading, or unavailable state using shared roles.

The implementation must not:

- rewrite every selector in `global.css`;
- rename feature classes without need;
- remove any action, field, status text, warning, table, diagnostic value, candidate detail, artifact, attempt, validation, scenario, or GLB viewer;
- change API calls or response handling;
- alter BLUECAD selection, archive, retry, promotion, or evidence behavior;
- turn current diagnostic pages into primary product navigation;
- implement router, rail, top bar, navigator, sidecar, dock, stages, or legacy routes owned by 083.

Unmigrated feature CSS remains valid technical debt and must be recorded in the implementation PR rather than absorbed into 070.

## 11. Accessibility and interaction baseline

Required behavior:

- visible `:focus-visible` treatment in both resolved themes;
- no global removal of outlines without an equivalent visible replacement;
- normal text, controls, focus rings, warning, danger, and success pairs meet WCAG 2.2 AA contrast targets;
- status meaning is not color-only;
- disabled controls remain readable and expose native disabled state;
- hover is not required to discover or operate an action;
- labels and errors remain associated with controls;
- native table, details/summary, button, input, select, and textarea semantics are preserved;
- `prefers-reduced-motion` removes nonessential transitions and animation;
- motion never delays an operation or hides state;
- content remains usable at 200% browser zoom;
- current compact desktop breakpoints remain usable without introducing horizontal page-level scrolling, except bounded data tables and technical viewports that already own overflow.

070 is desktop-first. It does not promise a complete 320-pixel touch-first experience. Controls must not become pathologically small, and existing narrower behavior must not regress, but mobile redesign belongs outside this slice.

Automated contrast tooling is not required. The implementation PR must record computed contrast ratios or browser-audit evidence for core pairs in both themes.

## 12. Evidence and economic honesty

070 cannot reinterpret backend evidence.

Where current or migrated surfaces display execution classes or cost:

- `local_compute` means a real local invocation;
- a real local invocation without a cost model is `unpriced`;
- no-execution, fake, synthetic, local-compute, and external-provider evidence remain distinct;
- unavailable totals remain unavailable, not zero;
- estimated or conservative external spend remains distinguishable from exact provider usage;
- visual success cannot override deterministic failed, stale, parked, archived, proposed, or blocked state.

No spend calculation, route evaluation, grading, provider selection, or accounting transformation belongs in 070.

## 13. Expected implementation files

Verify against exact `master` before readiness and coding.

Expected bounded set:

```text
frontend/src/styles/tokens.css                    new
frontend/src/styles/global.css                    bounded migration
frontend/src/theme.ts                             new
frontend/src/main.tsx                             initial theme application
frontend/src/components/Layout.tsx                appearance control only
frontend/src/components/PageErrorBoundary.tsx     shared notice migration
frontend/src/components/ui/*                      approved primitives only
frontend/src/pages/*                              only bounded mechanical migrations
scripts/check_ui_foundation.py                    new dependency-free checker
docs/specs/STATUS.md                              normal lifecycle transitions
```

Potentially touched only if current code proves it necessary:

```text
frontend/src/components/BluecadGlbViewer.tsx
```

That file may change only to replace a container-facing CSS hook or to document why renderer constants remain outside token enforcement. Scene behavior and numeric rendering constants must remain unchanged.

Not expected:

```text
frontend/package.json
frontend/package-lock.json
backend/**
.github/**
```

A package-file change requires separate minimum-necessary evidence and is presumed unnecessary.

## 14. Deterministic verification

Add exactly one dependency-free checker:

```text
python scripts/check_ui_foundation.py
```

It must validate at least:

1. required token names exist;
2. light and dark semantic token definitions exist;
3. appearance enums are exactly `system`, `light`, and `dark`;
4. only the approved versioned key is used for appearance persistence;
5. `localStorage` use in 070 files cannot serialize arbitrary values;
6. `data-theme` is applied only as `light` or `dark`;
7. required primitives exist;
8. primitive files do not import API clients, services, pages, routing, or business modules;
9. new foundation/primitives do not introduce raw color literals outside `tokens.css`;
10. the checker itself uses only the Python standard library.

The checker does not prove visual quality, semantics at runtime, contrast, or browser behavior.

Required implementation gates:

```text
python scripts/check_ui_foundation.py
cd frontend
npm ci
npm run build
```

plus repository-standard registry, backend, Ruff, geometry canary, and real-tool proof gates.

Because the repository has no frontend test framework, the implementation PR must also record a bounded manual browser matrix covering:

- initial load in system/light/dark;
- invalid and unavailable storage;
- live OS-theme change while in system mode;
- keyboard operation and visible focus;
- 200% zoom;
- one compact desktop width;
- current Dashboard, System Status, Domain Foundation, AI Draft, BLUECAD, and development-only chat reachability;
- one real BLUECAD candidate and GLB artifact when available;
- one error, warning, loading, empty, or unavailable state.

No live provider call or new spend is required.

## 15. Acceptance criteria

1. One semantic token stylesheet supplies required light and dark roles without page-specific token names.
2. `system`, `light`, and `dark` are the only accepted preferences; invalid or unavailable storage fails safely to `system`.
3. Theme resolution is centralized, applied without deliberate wrong-theme rendering, and cleans system listeners correctly.
4. Only the appearance enum is persisted; no authority, secret, provider, budget, prompt, workspace, record, run, candidate, or shell state enters browser storage.
5. The current layout exposes an accessible immediate appearance control without becoming a Settings surface or altering navigation structure.
6. The five approved primitives exist, preserve native semantics, and import no API or business authority.
7. Required bounded migration targets use semantic roles while all existing pages and workflows remain functionally available.
8. BLUECAD renderer behavior and scene constants remain unchanged; only the viewer container may adopt shared CSS roles.
9. Visible focus, non-color-only state, reduced motion, 200% zoom, and compact desktop behavior are demonstrated.
10. Core text, accent, focus, warning, danger, and success pairs meet recorded WCAG AA contrast targets in both themes.
11. No dependency, UI framework, state library, router, icon package, font binary, CDN asset, Storybook, frontend test framework, backend change, schema, migration, or new provider call is introduced.
12. `local_compute`, no-execution, synthetic/fake, and external-provider evidence remain distinct; only real local invocation without a cost model is labelled `unpriced`.
13. The dependency-free checker and frontend production build pass on exact head.
14. Full repository deterministic gates remain green.
15. No runtime screenshot is required for 070 alone; Phase-1 screenshot evidence is produced only after 083 completes the shell, as required by 081.

## 16. Readiness requirements

A separate readiness decision may promote 070 from `planned` to `ready` only after confirming:

1. this complete definition is merged;
2. 006, 082, and 094 remain `merged`;
3. no open implementation PR owns the same frontend files;
4. current frontend package and build commands remain as described;
5. current `global.css`, `main.tsx`, `App.tsx`, `Layout.tsx`, `PageErrorBoundary.tsx`, and `BluecadGlbViewer.tsx` have been reread;
6. implementation can remain dependency-free;
7. expected file set remains one reviewable medium slice;
8. 083 shell, routing, stage, sidecar, navigator, dock, and legacy-route work remains excluded;
9. manual browser evidence is assigned to a Windows-capable operator environment;
10. implementation branch and merge owner are named.

The readiness PR must not modify frontend runtime.

## 17. Non-goals

070 does not implement:

- spec 083 application shell, router, deep links, stage registry, rail, top bar, navigator, sidecar, analysis dock, or legacy routes;
- spec 084 read model;
- spec 085 BLUECAD workbench migration;
- spec 086 model inspection;
- spec 087 lineage;
- spec 088 runs workbench;
- Engineering Data, Analytics, Review, Threads, Jarvis sidecar, Settings, scene binding, scene semantics, variants, or comparison;
- 062 grading;
- Hermes, MCP, autonomous agents, or fake online presence;
- provider configuration, secret persistence, egress, budgets, accounting, or live calls;
- new statuses or reinterpretation of backend states;
- a responsive/mobile product redesign;
- full feature-CSS normalization;
- theming of Three.js scene internals;
- screenshots for the completed Phase-1 shell.

## 18. Stop conditions

Stop implementation and report if:

1. current code requires a router, global store, UI framework, CSS processor, or frontend test framework to satisfy an acceptance criterion;
2. the implementation would need to change a backend response or authority boundary;
3. shared primitives would need feature-specific business behavior;
4. theme persistence would contain anything beyond the appearance enum;
5. renderer-internal changes are required to make themes usable;
6. existing BLUECAD, AI, scenario, system-status, domain-foundation, or diagnostic behavior cannot be preserved within the bounded migration;
7. 070 and 083 cannot remain independently removable;
8. accessibility targets cannot be met without a material product-layout decision owned by 083;
9. a secret, key-derived value, local runtime data, or provider response would enter frontend source, logs, fixtures, screenshots, or browser storage.

## 19. Definition of done

The 070 implementation is complete only when:

1. all acceptance criteria pass;
2. exact-head frontend and repository gates are green;
3. manual browser evidence is recorded without secrets or sensitive project data;
4. review has no unresolved blocking finding;
5. the implementation PR remains within the bounded file and authority set;
6. merge is exact-head guarded;
7. `STATUS.md` is reconciled immediately after merge;
8. the next authorized front becomes definition/readiness work for 083, not additional unscoped UI cleanup.
