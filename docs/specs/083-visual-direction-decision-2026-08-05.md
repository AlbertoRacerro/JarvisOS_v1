# Spec 083 visual-direction decision — 2026-08-05

**Decision status:** Route 2 confirmed — global visual identity is an independently removable lane and does not block the structural APP-SHELL-1 implementation.

**Applies to:** spec 083 APP-SHELL-1 definition and readiness boundary.

**Exact decision baseline:** `672e8182031aa2a2d26608ead222c50c0af038f6`

**Maintainer input:** the global JarvisOS visual identity is being developed independently in Penpot while repository work continues on identity-independent shell contracts.

---

## 1. Decision

The prior kernel correctly refused to guess font, palette, borders, surfaces, iconography, or motion without inspectable assets. The maintainer has now clarified the work architecture: Penpot owns that identity work in parallel, while APP-SHELL-1 may proceed on structure, navigation, continuity, accessibility, and authority boundaries that do not depend on the final appearance.

The selected architecture is therefore:

```text
Route 2 — visual identity globally independent
```

This does not import or canonize unfinished Penpot output. It canonizes only the separation boundary.

## 2. Why the identity is independently removable

The Penpot lane can be implemented or removed without changing:

- canonical routes;
- browser history behavior;
- primary-navigation destinations;
- static PrimaryStage kinds;
- BLUECAD compatibility mounting;
- selection types;
- panel open/close state;
- focus management;
- backend/API authority;
- provider, credential, budget, ledger, egress, or MemoryStore behavior;
- current page continuity.

Conversely, 083 can be implemented using current 070 semantic roles and later restyled without changing shell behavior.

## 3. Queue treatment

Design activity may continue in Penpot in parallel because it does not mutate repository runtime or create a second implementation writer.

Repository implementation of the identity remains separate. It requires one of:

1. a numbered visual-identity specification; or
2. a canonical addendum with an explicit independently removable implementation boundary.

The identity implementation must remain serialized under the one-front/one-writer rule unless spec 081 is explicitly re-derived. This decision does not silently insert, reorder, or mark a queue item in `STATUS.md`.

Default sequencing is:

```text
complete and implement 083 structural shell
→ reconcile 083
→ canonize the Penpot identity contract
→ implement the identity lane at its authorized queue position
```

A later explicit 081 re-derivation may alter that sequence when the Penpot deliverable proves a technical dependency. No such dependency is currently evidenced.

## 4. Scope classification

### A — APP-SHELL-1 / spec 083

- History API routing and direct-load continuity;
- rail and top-bar structure;
- shell spatial hierarchy;
- static stage registry;
- Model/Results/Review/Flowsheet stage frames;
- BLUECAD compatibility mounting;
- contextual navigator;
- one contextual sidecar slot;
- analysis dock closed by default;
- route/stage/legacy/unavailable structural indication;
- shell responsive and 200%-zoom behavior;
- shell-level semantic hierarchy using existing 070 roles.

### B — foundation already available from 070

- semantic token names and current values;
- system/light/dark resolution;
- appearance persistence;
- pre-mount theme application;
- live system-theme updates and cleanup;
- visible focus;
- keyboard reachability;
- reduced motion;
- Button, Surface, StatusBadge, Field, InlineNotice;
- non-color state distinctions;
- responsive containment and local technical overflow.

### C — separate Penpot visual-identity lane

- global sans and mono typefaces;
- cross-page palette and semantic token-value replacement;
- complete border and separator grammar;
- global radii and elevation/shadow grammar;
- surface, control, table, card, panel, and badge language;
- iconography and asset system;
- global motion language;
- texture, pattern, grid, illustration, or brand assets;
- redesign of current/future pages beyond shell containment;
- removal of the temporary green and generic SaaS character.

### D — future page specifications

- candidate read model 084;
- BLUECAD workbench 085;
- model inspection 086;
- lineage 087;
- runs 088;
- Engineering Data re-derived 035;
- analytics 089;
- AI threads 090;
- Jarvis behavior 091;
- scene binding 092;
- Settings re-derived 029;
- proposal review re-derived 054;
- semantic scene tooling re-derived 058c.

## 5. Binding 083 visual constraints

Until the Penpot lane is canonized, 083 must:

- use existing semantic tokens rather than raw colors;
- retain current token values;
- retain the current font stacks;
- add no font, icon, image, texture, or illustration asset;
- add no icon package or design-system dependency;
- avoid global changes to borders, radii, shadows, controls, tables, cards, or badges;
- add only shell-layout CSS required for composition, containment, focus, route state, and responsive reflow;
- preserve system/light/dark behavior;
- remain readable and operable without decorative identity elements.

The structural shell must not attempt to look like a finished Penpot design.

## 6. Confirmed directional principles retained

The later identity should preserve, unless subsequent maintainer evidence explicitly changes them:

- one dominant primary object of attention;
- progressive disclosure rather than permanently open panels;
- restrained primary navigation;
- one right-side secondary slot rather than simultaneous Inspector and Jarvis columns;
- analysis dock closed by default;
- clear current route, stage, selection, mode, and migration status;
- engineering density without tiny text or cramped controls;
- real artifacts and backend state over conceptual renders or fake telemetry;
- no neon glow, glassmorphism, fake holograms, ornamental charts, cockpit density, or ambient animation;
- premium engineering-tool character rather than gaming HUD, consumer app, corporate intranet, or generic SaaS dashboard;
- full light/system/dark and accessibility compatibility.

These principles are constraints, not a complete visual specification.

## 7. Penpot handoff requirements

Before repository implementation of the identity, the canonical handoff must provide inspectable evidence for at least:

- named font families, weights, delivery method, fallback, and license;
- light/dark palette mapped to semantic roles;
- text and non-text contrast evidence;
- border/separator weights and contrast;
- radius and elevation rules;
- shell, surface, panel, card, table, input, button, badge, and unavailable-state examples;
- rail, top-bar, navigator, sidecar, dock, and stage dimensions or responsive relationships;
- icon/asset source, license, accessible naming, and fallback;
- motion inventory and reduced-motion alternatives;
- compact desktop and 200% zoom examples;
- explicit elements included and excluded;
- mapping of each visual requirement to A/B/C/D scope.

A screenshot or one Penpot frame is not sufficient by itself. The handoff must translate the design into testable roles and behavior.

## 8. Risks controlled by this separation

This decision prevents:

- delaying routing and continuity for unfinished aesthetics;
- embedding a global redesign in an already-large shell slice;
- hard-coding guessed Penpot values;
- duplicated or conflicting token systems;
- a shell implementation that becomes inseparable from one visual treatment;
- page redesign work leaking into 083;
- parallel repository writers touching the same frontend files;
- treating attractive static frames as proof of runtime, accessibility, or responsive behavior.

## 9. Exit state

For spec 083:

- global visual identity is no longer a readiness blocker;
- no Penpot value or asset is authorized in 083;
- 083 may proceed through full-spec, readiness, and implementation using 070 semantics;
- the Penpot lane remains open design work with no repository implementation authorization yet.

This record must be revisited when the Penpot handoff is ready or when it demonstrates a real technical dependency on the shell architecture.
