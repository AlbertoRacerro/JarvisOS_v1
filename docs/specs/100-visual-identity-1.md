# 100 — VISUAL-IDENTITY-1 full specification

Status: **full spec; implementation not authorized**  
Date: 2026-08-25  
Definition authority: `docs/specs/100-visual-identity-1-definition.md`  
Depends on: 097, 098, 058b, 058d

## 1. Objective

Apply one coherent, independently removable global visual identity to the merged JarvisOS operator workstation while preserving all current product, engineering and execution authority.

The implementation target is the maintainer-approved **living engineering instrument** direction: canonical light appearance, medium-high engineering density, mineral working surfaces, chlorophyll/microalgae accent detail, precise engineering structure, bio-machined geometry, restrained real depth, short near-subliminal motion and Jarvis as an integrated expert colleague.

100 is a frontend visual-system/application-surface slice. It does not authorize product re-layout, backend work, process semantics, evaluator behavior, engineering-state changes or new AI execution paths.

## 2. Binding sources

Every readiness and implementation decision must be checked against the exact-master versions of:

- `docs/design/visual-identity-100/README.md`;
- `docs/design/visual-identity-100/VISUAL_DIRECTION.md`;
- `docs/design/visual-identity-100/DESIGN_SYSTEM_DECISIONS.md`;
- `docs/design/visual-identity-100/ICONOGRAPHY.md`;
- `docs/design/visual-identity-100/PROOF_AND_ACCEPTANCE.md`;
- `docs/audits/VISUAL_IDENTITY_REFERENCE_AUDIT_2026-08-25.md`;
- `docs/specs/100-visual-identity-1-definition.md`.

`docs/specs/STATUS.md` remains the sole lifecycle/queue authority.

## 3. Runtime baseline and implementation seams

Fresh inspection of exact post-definition master confirms:

- `frontend/src/theme.ts` already owns safe local `system | light | dark` appearance persistence/application and is the required pattern for visual-only accent preference;
- `frontend/src/styles/tokens.css` already centralizes typography, spacing, radii, motion and light/dark semantic colors;
- `frontend/src/App.tsx` already owns the single shell composition for stage content, Jarvis, Properties and the Analysis Dock;
- `frontend/src/pages/Settings.tsx` is the existing settings surface where appearance/accent controls belong;
- current dense proof candidates are `frontend/src/pages/EngineeringData.tsx` and `frontend/src/pages/RunsWorkbench.tsx`;
- BLUECAD remains the hard technical-viewport proof surface;
- `/design/process` already exists as the 058d inert Process scaffold and must remain semantically inert;
- no generic icon library is present in current `frontend/package.json`.

100 must extend these seams rather than introducing parallel theme, shell, selection, process, settings or state owners.

## 4. Mandatory visual system

### 4.1 Appearance

- Canonical/default visual design is light.
- Existing appearance choices remain exactly `system`, `light`, `dark`.
- Dark must have parity of hierarchy, state semantics, focus visibility and accent isolation.
- Dark uses charcoal/mineral darks, not neon/pure-black brand styling.

### 4.2 Typography

- Primary candidate: **Instrument Sans**.
- Technical mono: **IBM Plex Mono** only for code/log/path/hash/identifier contexts where character distinction helps.
- Ordinary engineering values stay in the primary UI family and use tabular numerals where repeated alignment matters.
- **Instrument Serif is optional and proof-gated** for a rare display/identity role only; omit if it adds editorial noise or reduces scanning.
- No required operating information below 12px.
- Initial target scale: 12px metadata, 13px labels, 14px ordinary body/table, 16px section title, 21–24px page/workbench title.
- Readiness must freeze exact local/bundled font delivery and license notice handling. Network-only font loading is not acceptable for the normal local operator experience unless readiness proves an explicit offline-safe fallback with equivalent identity.

### 4.3 Generic iconography

- Newly introduced/replaced generic application icons use **Phosphor only** through maintained `@phosphor-icons/react`.
- No Lucide/Tabler generic dependency may be added alongside it.
- Normal generic weight is coherent by control class; `regular` is default.
- Icons normally inherit `currentColor`.
- Changed icon-only controls require accessible names/tooltips as appropriate.
- `FlowArrow` or equivalent may identify the Process stage only; it cannot represent fake process equipment/streams.
- PFD/P&ID/unit-operation symbols remain outside 100.

### 4.4 Accent system

Settings exposes exactly:

1. Microalgae — default seed `#528B68`;
2. Leaf Chlorophyll — `#5F8F52`;
3. Lagoon — `#4F938A`;
4. Custom.

Custom minimum behavior:

- native color chooser plus editable validated HEX;
- immediate understandable application/preview;
- malformed/stale persisted values fail safely to Microalgae;
- Reset restores Microalgae;
- persistence is local visual preference only;
- no backend/canonical engineering persistence.

Prefer CSS variables plus perceptual `oklch()`/`color-mix()` tonal derivation if the supported browser matrix passes. Do not add a color-library dependency unless readiness proves native/CSS derivation insufficient.

### 4.5 Semantic color isolation

Accent may style navigation/selection/focus/active borders, restrained structural tint, Jarvis presence and non-physical selection emphasis where current semantics already allow it.

Accent must not replace or recolor:

- danger/error;
- warning;
- success/valid;
- proposed;
- stale;
- unavailable/disabled;
- scientific/physical field colormaps;
- categorical series identities that must remain distinct.

A warm/orange Custom seed is a mandatory adversarial proof.

### 4.6 Density and geometry

- Target is high-information, medium-density engineering UI.
- Improve density through hierarchy, alignment, grouping and restrained spacing before shrinking text.
- Compact controls target roughly 30px; normal engineering controls roughly 34–36px.
- Structural panels/tables/canvas frames/Properties/Analysis Dock use low-to-moderate 6–8px geometry.
- Normal controls use roughly 6–8px.
- Floating/transient/Jarvis assistive surfaces may use roughly 10–12px.
- Pills only for actual chip/tag/toggle/segmented semantics.
- Universal large-radius SaaS card language is forbidden.

### 4.7 Surfaces and depth

Canonical light direction starts from the maintainer seeds:

- mineral canvas `#F2F3ED`;
- main surface `#FBFCF8`;
- raised surface `#FFFFFF`;
- subtle chlorophyll-neutral surface `#E9EEE7`;
- primary text `#20251F`;
- secondary text `#59645B`;
- muted text `#758078`;
- quiet border `#CFD8CE`;
- strong border `#AAB7AA`;
- technical viewport dark mineral `#121A16`.

Exact values may move only for concrete browser/contrast failures.

Depth remains low-amplitude: no canvas shadow; fine-border + small structural elevation; slightly stronger floating elevation; highest normal elevation reserved for modal/popover/transient surfaces.

Glass/translucency is optional and proof-gated. It is normally forbidden on dense tables, navigator, Properties body, Analysis Dock grids and large structural canvas frames. Every translucent candidate requires an opaque fallback.

### 4.8 Motion

- ordinary hover/press/focus/selection: about 80–140ms;
- panel/tab/popover transitions: about 120–180ms;
- no action waits for animation completion;
- reduced-motion collapses non-essential motion to effectively immediate behavior;
- indefinite/richer animation exists only while real work is pending and stops when pending ends;
- no fake percentage/progress.

### 4.9 Jarvis

Jarvis uses the same typography, icon family, spacing and core surfaces as the workstation. It may receive slightly softer geometry, restrained accent modulation/elevation/translucency and a distinct real-pending animation only where proof passes.

Forbidden: purple gradients, sparkle/magic AI motifs, separate AI-brand chrome or any visual affordance that blurs proposal versus executed engineering change.

## 5. Product-authority invariants

100 must preserve exactly:

- 083 routing/workspace/stage composition;
- 095/096 Operate/Inspect/Audit hierarchy and Jarvis-over-Properties sidecar ownership;
- 071b single mutable working configuration, preflight and Run separation;
- 092/058c BLUECAD selection and selected-object semantics;
- 097 structured Jarvis action authority;
- 098 Engineering Data lifecycle semantics;
- 088/089/058b persisted run/result/comparison authority;
- 058d Process-vs-Lineage distinction and inert Process scaffold;
- frontend-only provider/tool/runner isolation.

A purely visual interaction must not create backend, provider, runner or canonical mutation side effects.

## 6. Implementation boundary

Implementation is expected to remain frontend-only except for repository package/license/notice metadata required by selected open-source fonts/icons.

### Allowed implementation surface classes

Readiness must freeze the exact file list from these existing seams only:

- `frontend/package.json` and lockfile for the single Phosphor dependency;
- open-source font assets and the repository notice/license metadata required to redistribute them;
- `frontend/src/theme.ts` for one visual-preference owner covering appearance plus accent without changing appearance semantics;
- `frontend/src/main.tsx` only if required for local font/token initialization;
- `frontend/src/styles/tokens.css` and bounded existing shared/surface CSS under `frontend/src/styles/` required to apply the system coherently;
- existing shared UI primitives/components under `frontend/src/components/` only where their visual contract is used across proof surfaces;
- `frontend/src/components/Layout.tsx` / current shell component only for visual/icon adoption, never shell authority changes;
- `frontend/src/pages/Settings.tsx` for accent controls;
- the existing BLUECAD, Engineering Data or Runs, Process-stage and Jarvis/Properties/Analysis-Dock components only where direct visual/icon adoption cannot be achieved through shared tokens/CSS;
- product-owned deterministic 100 frontend test/harness files and evidence-only workflow/fixture files required by readiness.

### Forbidden implementation surface

- backend application/tests/schema/API files;
- provider, runner, tool or AI execution code;
- canonical engineering stores/models;
- router/stage semantics;
- new process topology/state;
- new theme/state framework;
- new color-picker library unless readiness records native-control failure;
- generic animation framework;
- 100a/100b cleanup or any 101–110 work.

If implementation needs a forbidden surface, stop and narrow/re-derive rather than expanding 100.

## 7. Proof surfaces

### Proof A — BLUECAD / Model

Real shell/navigation + BLUECAD viewport + selected part/object + populated Properties + Jarvis content/action structure + Analysis Dock where existing semantics permit it.

### Proof B — Process

`/design/process` with 058d inert scaffold, shell, sidecar and dock relationship visible. No nodes, streams, equipment or process truth may be fabricated.

### Proof C — dense data

Use whichever is denser on the final implementation head: Engineering Data or Runs. Readiness must choose the harder exact state. It must include realistic rows, metadata, statuses and actions.

### Proof D — Settings

Existing appearance controls plus all four accent choices, Custom chooser/HEX, Reset/default and immediately understandable visual application.

A–D are required in canonical light. Dark parity additionally covers shell/navigation, one dense engineering screen, Settings accent controls and focus/selected/status states.

## 8. Deterministic acceptance

The implementation head must prove at least:

1. appearance remains exactly `system | light | dark` and safely defaults;
2. accent choices are exactly Microalgae, Leaf Chlorophyll, Lagoon, Custom;
3. invalid/stale accent persistence fails to Microalgae;
4. Reset restores Microalgae;
5. malformed Custom HEX never reaches CSS/application state;
6. accent-owned variables are separate from semantic/scientific variables;
7. warm/orange Custom leaves warning/error/success/proposed/stale/unavailable/scientific channels unchanged;
8. reduced motion collapses non-essential motion;
9. indefinite animation is tied to a real pending state and terminates with it;
10. only Phosphor is introduced as generic icon family;
11. changed icon-only controls have accessible names;
12. generic icons do not imply process unit-operation semantics;
13. typography follows UI-vs-technical context boundaries;
14. required information does not depend on sub-12px text;
15. route/stage/selection/lifecycle/Jarvis-action semantics remain unchanged;
16. no backend/provider/runner/canonical mutation path is added;
17. 058d Process scaffold remains inert;
18. frontend production build and existing deterministic suites remain green.

## 9. Browser acceptance

Real browser/evidence must cover:

- A, B, C and D in canonical light;
- required dark parity;
- all three curated accents;
- at least two materially different Custom seeds including warm/orange;
- invalid stored Custom fallback and Reset;
- keyboard-only focus/navigation on touched surfaces;
- reduced-motion behavior;
- effective 200% and compact desktop with no page-level horizontal overflow;
- 12/13/14px hierarchy, long labels and tabular engineering values;
- structural panel alignment/depth without detached-card dominance;
- optional glass only if retained over the hardest permitted content plus opaque fallback;
- semantic/scientific colors unchanged across accent changes;
- no fake process semantics in `/design/process`;
- no backend/provider/runner/canonical side effect from visual controls.

Screenshots alone do not satisfy semantic-effect assertions.

## 10. Proof-gated optional choices

The following may be omitted without failing 100:

- Instrument Serif;
- glass/translucency;
- Phosphor duotone top-level/Jarvis emphasis;
- richer Jarvis pending animation beyond a minimal coherent pending state.

Retain one only if browser proof shows a clear hierarchy/identity benefit without harming engineering density, readability, contrast or seriousness.

## 11. Licensing and dependency gate

Readiness must verify before implementation:

- exact pinned `@phosphor-icons/react` version and MIT license/notice obligations;
- exact Instrument Sans and IBM Plex Mono upstream files/versions and SIL OFL 1.1 redistribution notices;
- optional Instrument Serif only if retained for proof;
- no commercial/reverse-engineered font assets;
- no network requirement for normal local font rendering;
- no additional icon, color, theme, animation or picker library unless separately justified by minimum-necessary evidence.

## 12. Rollback

100 is independently removable. Rollback restores prior visual tokens/assets/components/preferences while preserving routes, project data, engineering state, run history, BLUECAD/process semantics and backend authority.

Stored accent data must be versioned/fail-safe so removal or shape changes degrade to default rather than breaking startup.

## 13. Post-100 hold

After implementation merges and registry reconciliation records `100=merged`, no 100a/100b or later slice may start until the maintainer visually inspects the first pass.

The remote checkpoint must record:

- exact 100 merge SHA;
- principal frontend files changed;
- browser/evidence locations;
- minimum instructions to run/view merged UI;
- proof-gated options omitted or compromises retained.

At that point both frontend builders are disabled and the queue stops.