# 070 — UI-FOUNDATION-0: design tokens, appearance themes, and shared primitives

Status: planned full-spec draft. `docs/specs/STATUS.md` is authoritative. The
registry row will be added after the active 062 definition PR no longer owns
`STATUS.md`; this draft does not authorize implementation.

Depends on: 006

## Goal

Create the smallest stable visual foundation needed for subsequent JarvisOS
operator surfaces without redesigning product workflows or building a parallel
frontend architecture.

After this slice:

- foundational colors, typography, spacing, radii, borders, elevations, and
  layout measurements come from named CSS custom properties rather than repeated
  hard-coded literals;
- JarvisOS supports explicit `dark`, `light`, and `system` appearance preferences;
- dark mode uses the approved chlorophyll/technical-workspace direction while
  retaining readable neutral engineering surfaces;
- a narrow set of shared React primitives replaces repeated foundational markup
  and styling;
- existing pages remain functionally equivalent and build offline;
- future specs 037, 029, 058, and 054 can reuse one visual contract rather than
  adding more page-specific CSS.

This is a foundation slice, not the unified workspace redesign.

## Current evidence

The current frontend already has a functioning React/Vite shell, BLUECAD page,
3D viewer, system status, AI draft, domain foundation, and development-only local
chat. It also has one large global stylesheet whose foundational values are
repeated as literal hex colors, radii, paddings, and component states.

The implementation must preserve current runtime behavior and use the existing
React/Vite stack. No design-system dependency is justified.

## Product direction

The visual language is technical rather than decorative:

- dark chlorophyll shell and navigation;
- neutral technical work surfaces;
- restrained cyan/green accents for active or healthy states;
- semantic warning/error colors with sufficient contrast;
- compact, information-dense controls;
- clear separation among canonical state, proposals, warnings, unavailable data,
  and execution status;
- no neon glow, glassmorphism, fake holographic effects, or consumer-dashboard
  styling that obscures engineering evidence.

BLUECAD geometry and evidence remain the product focus. Visual polish may not
hide missing, provisional, unpriced, stale, or failed state.

## Scope

### 1. Token layers

Add one authoritative token stylesheet, expected path:

- `frontend/src/styles/tokens.css`.

Organize CSS custom properties into these layers:

1. primitive palette values;
2. semantic color roles;
3. typography;
4. spacing and sizing;
5. radii, borders, and elevation;
6. shell/workspace layout dimensions;
7. motion durations and easing.

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
```

Token names express roles, not page names. Do not create tokens such as
`--bluecad-card-blue` or `--settings-button-green`.

Foundation files and migrated shared primitives may not introduce new raw hex,
RGB/HSL, radius, or shadow literals outside `tokens.css`, except transparent
values and technically justified 3D-canvas values documented inline.

### 2. Appearance modes

Support exactly:

- `system`;
- `light`;
- `dark`.

Use a small typed frontend utility, expected path:

- `frontend/src/theme.ts`.

The utility owns:

- validation of stored preference;
- resolution of `system` against `prefers-color-scheme`;
- application through one `data-theme` attribute on the document root;
- subscription cleanup when system preference changes;
- storage of appearance preference only.

`localStorage` may contain only the appearance enum under one versioned key. It
must never contain provider keys, secrets, budgets, prompts, canonical data,
workspace records, or execution authority.

Invalid, missing, inaccessible, or throwing storage falls back safely to
`system`. Rendering must not crash when `window`, `matchMedia`, or storage is
unavailable.

Apply the preference before or at initial React mount so the application does
not deliberately render the wrong theme first. A brief browser-level color
transition may not be used to mask an initial-theme flash.

Set the CSS `color-scheme` consistently so native controls follow the resolved
appearance.

### 3. Operator control

Add one accessible appearance control to the existing shell. It may be a compact
three-state selector or menu; it must not create a settings page owned by 029.

Requirements:

- keyboard operable;
- explicit accessible name;
- current preference visible in text or accessible state, not color alone;
- no icon-only ambiguity;
- no network or backend call;
- changing preference updates the root theme immediately;
- system-mode changes follow OS preference while the page is open;
- event listeners are removed correctly.

### 4. Shared primitives

Create only the primitives already repeated across the current product. Expected
minimal set:

- `Button` with `primary`, `secondary`, `ghost`, and `danger` variants;
- `Panel` or `Surface`;
- `StatusBadge`;
- `Field` wrapper for label, control, hint, and error association;
- `InlineNotice` for info/warning/error states.

Expected location:

- `frontend/src/components/ui/`.

Each primitive:

- forwards appropriate native HTML attributes;
- preserves semantic native elements;
- supports keyboard focus visibly;
- does not own application state, API calls, routing, or business rules;
- does not invent generic polymorphic APIs or a component framework;
- uses shared tokens and bounded class names;
- has no dependency beyond React.

Do not add a generic table, modal, command palette, tooltip framework, form
library, icon package, or Storybook in this slice.

### 5. Bounded migration

Migrate only the foundation surfaces needed to prove the contract:

- application shell/sidebar/navigation;
- page canvas and common page header;
- common panels/cards;
- shared buttons and status pills used by at least two existing pages;
- common form labels/inputs where migration is mechanical and behavior-preserving;
- BLUECAD viewer container background/border tokens without changing viewer
  controls or Three.js rendering.

Do not rewrite every feature-specific selector merely to achieve a zero-literal
metric. Existing feature CSS may remain temporarily when it does not define a
foundation role. Record unmigrated categories as implementation notes rather
than expanding scope.

No page may lose an action, status, warning, field, table, artifact view, or
candidate workflow during migration.

## Theme contracts

### Dark

Dark mode is the default resolved appearance only when the stored preference or
OS preference selects dark. It must provide:

- dark green/chlorophyll shell;
- dark neutral canvas;
- elevated surfaces distinguishable without excessive shadow;
- technical viewport allowed to remain a lighter neutral when required for CAD
  legibility;
- no pure black large surfaces unless justified;
- no radioactive green text or borders;
- semantic statuses readable against dark surfaces.

### Light

Light mode retains:

- neutral technical canvas;
- clear dark text;
- restrained green/chlorophyll shell identity;
- visible borders and focus states;
- the same semantic status meanings as dark mode.

### System

`system` is a preference, not a third palette. It resolves to current light or
dark and updates when the OS preference changes.

## Typography

Use a local/system stack only. The preferred stack may begin with `Geist` when
installed locally, followed by existing system sans-serif fallbacks. Do not fetch
fonts from a CDN, add font binaries to the repository, or add a package solely
for typography.

Define named roles for:

- application title;
- page title;
- section title;
- body;
- compact UI label;
- metadata/caption;
- engineering monospace data.

The implementation must not reduce numerical readability or replace unit-bearing
values with decorative typography.

## Accessibility and interaction

Required minimum behavior:

- visible `:focus-visible` state for interactive primitives in both themes;
- text and essential controls meet WCAG AA contrast targets under normal states;
- status is never encoded only by hue;
- disabled controls remain legible and are not represented only by reduced
  opacity;
- hover is not required to discover an action;
- respect `prefers-reduced-motion`;
- motion is limited to bounded interaction feedback and never delays an action;
- the shell remains usable at 320 px width and current responsive breakpoints;
- browser zoom to 200% does not hide the appearance control or primary
  navigation.

Automated contrast tooling is not added in V0. The implementation PR must record
manual contrast calculations or browser-audit evidence for the core text,
accent, focus, warning, and danger pairs in both themes.

## Economic and evidence honesty

This visual layer cannot reinterpret backend economics or execution evidence.
Where cost is surfaced by later/current pages:

- local compute with no model is rendered as `unpriced`, never `$0.00` or free;
- unavailable totals remain unavailable/null;
- estimated/conservative external spend remains distinguishable from exact;
- synthetic evidence cannot look like real provider consumption;
- visual success colors cannot override deterministic failure, stale, parked,
  or proposal state.

No new spend calculation belongs in 070.

## Files likely touched

Verify against current code before implementation and stop on conflict.

Expected bounded set:

- `frontend/src/styles/tokens.css` (new);
- `frontend/src/styles/global.css`;
- `frontend/src/theme.ts` (new);
- `frontend/src/main.tsx`;
- `frontend/src/components/Layout.tsx`;
- `frontend/src/components/ui/*` for the approved primitives;
- a small set of existing pages/components only where required for the bounded
  migration;
- `frontend/package.json` only to add a dependency-free check script if needed;
- `scripts/check_ui_foundation.py` or `frontend/scripts/check-ui-foundation.mjs`
  only if a static contract check cannot fit existing tests;
- `docs/specs/STATUS.md` for normal implementation lifecycle state;
- this spec only for real implementation notes.

No backend file is expected to change.

## Deterministic verification

The current frontend has no test framework. Do not add one solely for this slice.
Use the existing TypeScript/Vite build plus one dependency-free static contract
checker if needed.

The checker must fail on at least:

- missing required token names;
- missing light or dark semantic overrides;
- invalid appearance enum drift;
- raw color literals newly introduced in foundation/primitives outside the token
  file;
- a shared primitive importing API clients, application services, or business
  modules;
- the appearance storage key containing anything beyond the appearance enum
  contract.

Do not claim this static check proves visual quality or contrast.

Required verification:

```text
cd frontend
npm run build
```

plus the repository-standard backend/status/BLUECAD CI gates because this is a
repository PR, even though backend runtime should be unchanged.

## Acceptance criteria

1. One token stylesheet defines the required semantic roles for light and dark
   appearances, with no page-specific token naming.
2. `system`, `light`, and `dark` are the only accepted preferences; invalid or
   inaccessible storage safely resolves to `system` without crashing.
3. Theme application is centralized on the document root and system-mode listener
   lifecycle is correct.
4. The shell provides an accessible, immediate appearance control without a
   backend call or a new settings page.
5. The approved shared primitives exist, retain native semantics, expose visible
   focus, and contain no API/business authority.
6. The shell, common panels, shared buttons/status badges, common form roles, and
   BLUECAD viewer container use semantic tokens without workflow changes.
7. Existing pages preserve actions, status text, warnings, forms, candidate
   details, artifacts, and 3D rendering behavior.
8. Dark and light core text/accent/focus/warning/danger pairs have recorded WCAG
   AA contrast evidence; status meaning is not color-only.
9. Reduced-motion and responsive behavior remain valid at the current smallest
   supported viewport and 200% zoom.
10. No dependency, font binary, CDN font, UI framework, Storybook, backend route,
    database field, secret storage, or economic calculation is added.
11. Local compute is never visually represented as free or `$0.00` when its cost
    is unavailable.
12. The dependency-free foundation checker and `npm run build` pass; repository
    CI remains green.

## Non-goals

- No unified workspace/home layout; 058 owns that product composition.
- No chat-to-BLUECAD behavior; 037 owns it.
- No provider settings, secrets, budgets, counters, or operator settings page;
  029 owns those surfaces.
- No proposal-review workflow; 054 owns it.
- No redesign of BLUECAD interaction, Three.js scene, geometry, evidence, or
  candidate lifecycle.
- No backend-persisted user profile or multi-user theme synchronization.
- No new router, state-management library, CSS framework, component library,
  icon library, form framework, testing framework, Storybook, or build tool.
- No full rewrite of the global stylesheet or every feature selector.
- No animation system, brand campaign, logo redesign, marketing page, or visual
  effects that imply engineering capability.
- No claim that a successful build proves accessibility or visual correctness.

## Promotion gate

070 may become `ready` only after:

1. its registry row and downstream dependency ordering are merged without
   conflicting with active 061/062 status work;
2. the implementation diff can stay frontend-only except for an optional
   dependency-free static checker;
3. the exact primitive set and bounded migration surfaces above still match the
   current frontend;
4. no active PR overlaps the same foundational CSS, Layout, theme, or primitive
   files;
5. manual contrast pairs and responsive acceptance evidence are defined for both
   themes;
6. exact-head CI and independent review find no unresolved blocker.
