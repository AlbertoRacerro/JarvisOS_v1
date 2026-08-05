# Spec 083 visual-direction decision — 2026-08-05

**Decision status:** confirmed shell-level constraints plus unresolved global identity inputs.

**Applies to:** spec 083 APP-SHELL-1 definition only.

**Exact repository baseline:** `182ab0623d5cdd26c79e31171539e721762b45d7`

**Chosen route:** Route 3 — input incomplete for global visual identity; do not freeze unsupported font, palette, border, component, icon, or motion decisions and do not begin implementation.

---

## 1. Evidence inventory

The decision uses:

1. the exact-master frontend implementation and spec 070 foundation;
2. spec 081 frontend-beta authority;
3. the maintainer's textual design handoff describing product hierarchy, shell composition, desired engineering-tool character, and rejected cockpit/SaaS patterns;
4. PR #225's final finding that the current font, palette, border/line treatment, and generic web-app aesthetic were accepted only temporarily and belong to future visual-direction work.

No inspectable image, render, font specimen, palette sheet, component sheet, or asset pack was available in the material accessible during this definition pass. Therefore this record distinguishes evidence-backed shell principles from unsupported identity inference.

## 2. Confirmed product and interaction principles

The following are sufficiently repeated and compatible with repository authority to become binding shell-level constraints:

- one dominant primary object of attention;
- progressive disclosure rather than simultaneous permanent panels;
- thin/restrained primary navigation;
- contextual navigator rather than a permanently expanded tree;
- one right-side secondary slot shared by inspector/Jarvis modes rather than multiple columns;
- analysis dock closed by default;
- clear current workspace/route/stage/selection/mode;
- educational empty and unavailable states;
- real artifacts and backend state over conceptual renders or fake telemetry;
- explicit accepted/proposed/rejected/superseded/stale/invalid/running/failed/diagnostic distinctions;
- engineering density without cramped controls or unreadable metadata;
- accessible keyboard/focus/zoom behavior as a first-class requirement;
- visual restraint: no neon glow, fake holograms, glassmorphism, ornamental charts, or ambient animation;
- dark technical-workspace capability without sacrificing the required light/system modes from 070;
- premium engineering-tool character, not a generic SaaS dashboard, gaming HUD, consumer app, or corporate intranet.

## 3. Confirmed shell composition

The available direction supports:

```text
Top bar
Rail | contextual navigator | dominant primary stage | contextual sidecar
Analysis dock closed by default
```

This is a relationship contract, not a pixel-perfect composition.

Confirmed hierarchy:

1. primary stage;
2. rail and route context;
3. contextual navigator;
4. contextual sidecar;
5. analysis dock.

When space is constrained, lower-priority regions yield before the primary stage.

## 4. Typography

### Confirmed

- clear distinction among product identity, route/stage title, section title, control label, technical metadata, and monospaced identifiers/values;
- body and control text must remain readable at 200% zoom;
- technical density must not be achieved through undersized text;
- unit-bearing values, statuses, evidence, and identifiers outrank decorative copy.

### Unresolved

- primary sans family;
- whether a display/heading family exists;
- exact technical mono family;
- font source/licensing/delivery method;
- weight range;
- exact type scale and tracking;
- whether current system-font fallback remains the shipping baseline.

No font replacement is authorized by 083 on current evidence.

## 5. Palette and semantic color

### Confirmed

- semantic roles from 070 remain authoritative;
- light and dark must express the same state meanings;
- a technical viewport may remain darker than surrounding light-theme surfaces when justified by 3D readability;
- status is never color-only;
- accents are restrained and must not make provisional or unavailable state look canonical;
- fake live indicators and decorative telemetry colors are prohibited.

### Unresolved

- replacement for the current green-dominant identity;
- primary accent hue;
- neutral temperature;
- exact shell/canvas/surface relationships;
- exact technical viewport palette;
- selected/focus/accent relationship;
- exact state colors after a future identity pass.

The current token values are temporary implementation values, not final brand authority. Their semantic names and behavior remain reusable.

## 6. Surfaces, lines, borders, radii, and shadows

### Confirmed

- surface hierarchy must be legible without excessive elevation;
- separators must support navigation and information grouping rather than decorate every region;
- panel boundaries must remain visible in both themes;
- the primary stage should not be fragmented into generic dashboard cards;
- overlays must be sparse, purposeful, and dismissible/collapsible where secondary;
- technical tables and viewports may own local overflow.

### Unresolved

- line weight and contrast system;
- whether the final language is border-led, tonal, or mixed;
- corner-radius family;
- elevation/shadow family;
- card grammar;
- input/control silhouette;
- badge geometry;
- panel nesting treatment.

A global replacement of these values is category C and must not be hidden in 083.

## 7. Density and spacing

### Confirmed

- desktop-first and information-dense;
- controls remain comfortably targetable and keyboard-operable;
- progressive disclosure controls density;
- major stage space is protected before secondary panes;
- no permanent four-panel cockpit;
- no whitespace-heavy consumer landing-page treatment.

### Unresolved

- exact spacing scale changes beyond 070;
- exact rail width, sidecar width, navigator width, top-bar height, and dock height;
- exact compact-desktop breakpoint behavior;
- whether panel resizing is needed in 083 or deferred.

The full 083 spec must freeze measurable responsive outcomes, not infer a visual grid from absent images.

## 8. Navigation and shell chrome

### Category A — 083

- rail structure and current-route indication;
- top-bar hierarchy;
- dominant primary-stage frame;
- contextual navigator placement;
- one contextual sidecar slot;
- analysis dock closed by default;
- explicit legacy-route labels;
- unavailable-state grammar at shell level;
- shell-level type hierarchy using semantic roles;
- compact-desktop and 200%-zoom behavior.

### Category B — reuse 070

- theme mechanism and semantic tokens;
- visible focus;
- keyboard reachability;
- reduced motion;
- shared primitives;
- semantic states;
- responsive containment.

### Category C — separate visual-identity lane

- global typography replacement;
- cross-page palette replacement;
- global border/radius/surface/control grammar;
- icon and asset system;
- global motion language;
- cross-page table/badge/input redesign;
- redesign of current pages unrelated to shell geometry.

### Category D — competent future page spec

- BLUECAD workbench detail: 085;
- candidate aggregate: 084;
- model inspection: 086;
- lineage: 087;
- runs: 088;
- analytics: 089;
- AI threads: 090;
- Jarvis behavior: 091;
- scene binding: 092;
- Settings: re-derived 029;
- proposal review: re-derived 054.

## 9. Stage chrome and technical graphics

### Confirmed

- stage chrome must expose route/stage identity and availability honestly;
- grids, callouts, tags, axes, and technical overlays are allowed only when tied to real data, real viewer behavior, or clearly labelled diagnostic scaffolding;
- the actual GLB remains the artifact in BLUECAD; a conceptual ocean render cannot be presented as backend output;
- future exploded view and semantic callouts require the competent scene-binding spec.

### Prohibited in 083

- fake node canvas;
- fake stream animation;
- fake sensor telemetry;
- fake agent status;
- ornamental graph wallpaper;
- simulated numerical readouts;
- semantic part labels inferred from Three.js mesh order or names;
- speculative instrument tags detached from backend records.

## 10. Controls, badges, tables, and forms

### Confirmed

- reuse the 070 primitives and native semantics;
- status labels remain textual and structurally distinct;
- controls must not become icon-only because no icon system is authorized;
- dense technical tables keep local horizontal overflow;
- unavailable, diagnostic-only, proposed, stale, synthetic, archived, success, warning, and danger states must remain distinguishable without hue alone.

### Unresolved / category C or D

- global control restyle;
- new table abstraction;
- global data-grid behavior;
- icon button language;
- tooltip system;
- compact badge redesign;
- page-specific form restructuring.

## 11. Light/dark relationship

The shell must support all 070 preferences:

```text
system
light
dark
```

Dark-first reference language does not authorize dark-only product behavior.

Binding relationship:

- same information hierarchy and status semantics in both themes;
- no content or action available only in one theme;
- technical viewport contrast may be intentionally asymmetric when the real GLB/viewer requires it;
- focus remains visible against controls and adjacent surfaces;
- theme changes do not reset route, stage, or current transient selection;
- no new theme persistence key.

Exact palettes remain unresolved.

## 12. Motion

### Confirmed

- motion is restrained and functional;
- panel transitions must not delay access or hide state;
- reduced-motion removes nonessential movement;
- no ambient, looping, glowing, parallax, or ornamental animation;
- focus and route transitions must not create motion-dependent comprehension.

### Unresolved / category C

- global easing language;
- panel transition style;
- duration changes beyond 070;
- stage transition treatment;
- data-update animation.

083 may use existing 070 motion roles only after the full spec defines the minimum shell transitions required.

## 13. Distinctiveness without “generic SaaS”

Distinctiveness must come from product structure and truthful engineering behavior, not decorative excess.

Evidence-backed differentiators:

- one artifact/stage as the focal object;
- explicit authority and lifecycle states;
- engineering identifiers, units, evidence, and provenance in the correct context;
- contextual rather than dashboard-style secondary information;
- honest unavailable capability boundaries;
- real GLB/validation/run surfaces retained during migration;
- stage-specific technical chrome only when real data supports it.

Avoid:

- repeated generic metric cards as the primary composition;
- marketing-style hero copy;
- generic green/blue SaaS accents as the sole identity;
- card grids that flatten workflow hierarchy;
- excessive pills and rounded rectangles;
- decorative analytics;
- universal “online” dots;
- interchangeable admin-dashboard navigation.

## 14. Contradictions and resolutions

### Dark-first reference vs system/light/dark foundation

Resolution: preserve all three appearance preferences. Dark may be a preferred visual reference, not the only supported mode.

### Jarvis on the right vs inspector on the right

Resolution: one sidecar slot with future modes. Never add two permanent right columns.

### Technical overlays vs no fake telemetry

Resolution: overlays require real stage data or explicit diagnostic/unavailable labelling. Decorative instrumentation is rejected.

### High density vs accessibility

Resolution: density comes from hierarchy, progressive disclosure, and contextual panels, not tiny text or undersized targets.

### Premium feel vs minimal implementation scope

Resolution: 083 may establish spatial hierarchy and truthful shell chrome. Global visual identity remains independently removable and separately authorized.

### Stage-centered product vs legacy page continuity

Resolution: preserve legacy pages through explicit routes until competent page specs migrate equivalent functionality. Do not hide working features behind empty future stages.

## 15. Look-risk analysis

### Gaming/HUD risk

Triggers:

- glow, neon accents, dark-only palette, permanent graphs, animated grids, fake targeting reticles, dense overlays.

Control:

- restrained accents, real data only, visible text, no ambient motion, secondary panels closed by default.

### Consumer-app risk

Triggers:

- oversized cards, excessive whitespace, simplified status language, hidden technical detail, rounded-everything controls.

Control:

- preserve technical density, units, evidence, IDs, detailed legacy routes, and explicit state vocabulary.

### Corporate/admin risk

Triggers:

- generic sidebar + dashboard cards, uniform blue/green buttons, provider-centric settings, metric-card home page.

Control:

- stage-first layout, contextual navigation, workflow-specific state, real artifacts, non-generic route hierarchy.

### Engineering-legibility risk

Triggers:

- low-contrast separators, decorative fonts, tiny metadata, color-only state, global overflow, overlay collision.

Control:

- 070 accessibility contracts, measured contrast, visible focus, local overflow, 200% zoom and compact-desktop browser evidence.

## 16. Purely decorative elements not justified

The current evidence does not justify:

- background textures unrelated to stage function;
- animated grids;
- ocean imagery as normal application chrome;
- persistent concept renders;
- decorative waveform/spectrum widgets;
- synthetic live telemetry;
- generic avatar presence;
- ornamental gradients or glow;
- motion solely for brand character;
- fake instrument panels.

Such elements require a later explicit identity or page-spec decision plus accessibility/performance evidence.

## 17. Route decision

**Route 3 is selected.**

Reasons:

1. shell layout and behavior are repeatedly evidenced and can be recorded now;
2. global font, palette, line/border, radius, surface, icon, and motion decisions are not supported by inspectable assets;
3. spec 070 already provides a technically valid semantic foundation whose values can later change without destroying contracts;
4. guessing a new identity inside 083 would create a global rewrite hidden inside a routing/shell slice;
5. postponing all shell definition would discard useful confirmed architecture and delay continuity planning unnecessarily.

Result:

- merge a definition kernel and this decision record;
- keep 083 `planned`;
- do not begin runtime implementation;
- do not assign a new visual-identity spec number or reorder the queue silently;
- when sufficient visual evidence exists, either complete 083 with a shell-bounded contract or propose a separately removable identity lane under 081 re-derivation rules.

## 18. Exit conditions from Route 3

A later definition pass may leave Route 3 when one of these is true:

### Route 1 exit

The available reference pack is sufficient to specify only shell-owned hierarchy/chrome while global page identity remains outside 083. The full 083 spec then records measurable shell decisions and proceeds to readiness.

### Route 2 exit

The reference pack requires a global, independently removable rewrite of typography, palette, component grammar, borders/surfaces, iconography, or motion. A queue proposal is then documented without silently changing `STATUS.md`; 081 re-derivation decides whether it precedes, accompanies, or follows 083.

In both cases the later decision must cite exact assets and translate them into testable criteria rather than aesthetic adjectives.

## 19. Current unresolved decision register

| Decision | Current status | Why unresolved | Required evidence |
| --- | --- | --- | --- |
| Primary sans font | open | no inspectable specimen/license/source | named family or reference specimen plus delivery/license decision |
| Mono font | open | current system stack may be adequate | technical text specimen and readability evidence |
| Accent/palette | open | maintainer rejects current green but replacement not evidenced | palette/reference images and semantic-role mapping |
| Border/line grammar | open | rejection is clear; replacement is not | component/shell reference with measurable contrast/weight |
| Radius system | open | no consistent reference values | component reference or explicit range |
| Surface/elevation grammar | open | “premium engineering” is not measurable alone | shell/panel references and hierarchy criteria |
| Icon system | open | no asset/family selection | icon source/license/accessibility plan |
| Exact rail/topbar/sidecar dimensions | open | relationship known, dimensions not | measured reference or browser-layout study |
| Compact-desktop transformation | open | outcome known, composition not | exact target widths and browser proof plan |
| Shell motion | open | restraint known, behavior not | transition inventory and reduced-motion alternative |
| Light/dark palette relationship | open | semantic parity known, values not | paired theme reference or token proposal with contrast evidence |

## 20. Decision conclusion

The current evidence is sufficient to prevent the wrong architecture and insufficient to authorize a global visual identity.

083 may be defined further only by preserving the shell/authority/continuity contracts in `083-app-shell-1.md`. It must remain `planned` until the unresolved identity boundary is either narrowed to shell scope or separated through an explicit queue decision, and until the normal full-spec and readiness gates are complete.