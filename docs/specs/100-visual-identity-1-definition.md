# 100 — VISUAL-IDENTITY-1

Status: **definition-only; implementation not authorized**  
Date: 2026-08-25  
Depends on: 097, 098, 058b, 058d

## 1. Purpose

Apply one coherent, independently removable global visual identity to the already-functional JarvisOS operator workstation without changing product authority, engineering semantics, route semantics, evaluator behavior or canonical data.

The visual system must make the workstation easier to scan and trust at medium-high engineering density while expressing the maintainer-approved identity of JarvisOS as a **living engineering instrument**: light-first mineral surfaces, restrained chlorophyll/microalgae accent, precise engineering structure, selectively softer bio-machined geometry, subtle real depth, restrained motion and Jarvis as an integrated expert colleague.

100 is not a redesign of the operator model. It styles and normalizes the merged functional surfaces produced through 058d and earlier operator-workstation slices.

Implementation remains unauthorized until a separate exact-master full-spec/readiness sequence proves the dependency/license choices, exact touched surfaces, semantic isolation of accent/theme state, deterministic tests and browser proof plan required by the maintainer Visual Identity Authority Pack.

## 2. Binding maintainer design authority

Definition, full spec, readiness and implementation must consume the following files from the exact `master` used for each lifecycle step:

- `docs/design/visual-identity-100/README.md`;
- `docs/design/visual-identity-100/VISUAL_DIRECTION.md`;
- `docs/design/visual-identity-100/DESIGN_SYSTEM_DECISIONS.md`;
- `docs/design/visual-identity-100/ICONOGRAPHY.md`;
- `docs/design/visual-identity-100/PROOF_AND_ACCEPTANCE.md`;
- `docs/audits/VISUAL_IDENTITY_REFERENCE_AUDIT_2026-08-25.md`.

Those documents are maintainer design authority for 100 but do not independently authorize runtime implementation. `docs/specs/STATUS.md` remains the sole live lifecycle/queue authority.

The visual direction may be tuned only where the required browser proof demonstrates a concrete readability, accessibility or semantic-confusion defect. The implementation must not silently substitute another aesthetic direction merely because the provisional UI differs.

## 3. Preserved product authority

100 must preserve, not reinterpret:

- **083 App Shell** routing, workspace ownership and stage composition;
- **095/096** Operate/Inspect/Audit hierarchy and Jarvis-over-Properties sidecar ownership;
- **071b** single mutable engineering working configuration, deterministic preflight and Run separation;
- **092/058c** BLUECAD scene selection and authoritative selected-object engineering semantics;
- **097** Jarvis structured engineering action/proposal authority;
- **098** Engineering Data lifecycle semantics;
- **088/089/058b** persisted Runs/results/comparison and Analysis Dock authority;
- **058d** Process-vs-Lineage distinction and inert Process scaffold semantics;
- **070** semantic-token/theme foundation where still useful as the implementation seam.

A visual control may expose existing state more clearly but cannot create a new engineering-state owner or redefine what any state means.

## 4. Visual thesis

The canonical visual character is:

- light-first, mineral and humanistic rather than black-first or corporate-blue;
- medium-high engineering density rather than legacy microtype or SaaS whitespace;
- structurally precise with selectively organic/bio-machined geometry;
- dimensional through fine borders and low-amplitude real elevation, not card spectacle;
- natural/aqueous/chlorophyll accent used as detail, not as a large filled brand wash;
- quietly advanced rather than cyberpunk, neon, gamer-HUD or glassmorphism-first;
- serious engineering first, unusual living/natural character second.

Atmospheric external references remain reference-only. No third-party brand asset, screenshot, proprietary typeface, copied layout or reverse-engineered font is authorized.

## 5. Light and dark appearance

**Light is canonical/default.**

100 must implement the identity from the light appearance first. Dark remains a complete supported alternative with equivalent hierarchy, state semantics, focus/readability and accent behavior.

Dark must read as the same instrument in low light, using charcoal/mineral darks rather than neon or pure-black brand styling. Scientific/3D viewports may remain darker where existing contrast requirements demand it.

The existing `system | light | dark` appearance preference remains the authoritative appearance model unless readiness finds a concrete current-runtime conflict. 100 must not create another theme-state owner.

## 6. Typography boundary

### Required candidates

- **Instrument Sans** — primary UI/body/control family, subject to real browser proof at engineering density;
- **IBM Plex Mono** — code, logs, paths, hashes and identifiers where character distinction materially helps;
- **Instrument Serif** — optional rare display/identity accent only if browser proof demonstrates clear benefit.

Instrument Serif is not required. If it looks editorial, weakens scanning or complicates hierarchy, omit it.

Ordinary engineering values should normally remain in Instrument Sans with tabular numerals rather than becoming monospace by default.

Initial type-density direction from maintainer authority:

- metadata/caption: about 12px;
- control labels: about 13px;
- ordinary body/table content: about 14px;
- section title: about 16px;
- page/workbench title: about 21–24px.

No required operating information may depend on text below 12px.

Readiness must verify exact font delivery method, OFL notices and browser-loading behavior before implementation.

## 7. Generic iconography

100 uses **Phosphor only** for newly introduced/replaced generic application icons through the maintained `@phosphor-icons/react` package.

Rules:

- no Lucide/Tabler alongside Phosphor for isolated gaps;
- normal generic icon weight is coherent per control class, with `regular` the default;
- icon color normally inherits `currentColor`;
- icon-only controls retain accessible names/tooltips where required;
- iconography cannot make engineering/status meaning depend on hue alone;
- `FlowArrow` or equivalent may identify the Process stage only; it must not imply real process equipment or stream semantics.

Future process/PFD/unit-operation symbols are engineering notation, not generic application icons, and remain outside 100.

## 8. Accent architecture

100 must expose four visual accent choices:

1. **Microalgae** — default seed `#528B68`;
2. **Leaf Chlorophyll** — `#5F8F52`;
3. **Lagoon** — `#4F938A`;
4. **Custom**.

The seed generates a bounded tonal family for subtle background/surface, border/strong border, primary accent, hover/pressed, focus/selection and accessible on-accent treatment where required.

Prefer dependency-free CSS variable/perceptual derivation such as OKLCH + `color-mix()` if the actual supported browser matrix and deterministic fallback proof pass. Do not add a third-party color library without readiness evidence that the native/CSS approach fails.

Custom minimum behavior:

- native color chooser plus editable validated HEX field;
- immediate understandable visual application/preview;
- invalid or stale persisted values fail safely to Microalgae;
- Reset restores Microalgae;
- visual preference is local-only and follows the existing appearance-preference pattern where practical;
- no backend persistence or canonical engineering record.

## 9. Accent semantic isolation

User accent may style:

- current navigation/selection;
- focus/active borders where contrast remains valid;
- selected geometry/row non-physical emphasis already allowed by current semantics;
- restrained structural detail/surface tint;
- Jarvis presence and real-waiting detail;
- selected/primary graph series only where no engineering meaning is overwritten.

User accent must **never** replace or recolor authoritative semantic channels such as:

- danger/error;
- warning;
- success/valid;
- proposed;
- stale;
- unavailable/disabled;
- scientific/physical field colormaps;
- categorical series whose identities must remain distinct.

The required adversarial proof includes a warm/orange Custom seed. If orange accent turns warnings, validation, scientific data or other semantic channels orange, the implementation fails.

## 10. Density and control rhythm

Target: **high-information, medium-density engineering workstation**.

100 should improve density primarily through hierarchy, alignment, grouping and restrained spacing rather than shrinking text.

Initial control targets:

- compact control: roughly 30px high;
- normal engineering control: roughly 34–36px high.

The current navigator/canvas/sidecar/Analysis-Dock product architecture remains intact. Visual identity may refine proportions only when that is necessary for readability and does not re-author semantic ownership or route structure.

## 11. Bio-machined geometry

Geometry communicates surface role rather than applying one radius everywhere.

Initial direction:

- structural panels, tables, canvas frames, Properties and Analysis Dock: low/moderate radius, approximately 6–8px;
- normal controls/inputs: approximately 6–8px;
- floating/transient/Jarvis assistive surfaces: approximately 10–12px where appropriate;
- pills only when chip/tag/toggle/segmented semantics justify the shape.

Universal large-radius SaaS cards are forbidden.

## 12. Surfaces, borders, elevation and glass

Canonical light surfaces use mineral/warm-neutral intent: mineral canvas, near-white working surfaces, warm graphite text and slightly organic neutrals. Exact seed values are provided by the maintainer authority pack and may move only for concrete proof failures.

Depth model should remain small and meaningful:

- canvas/background: no shadow;
- structural panels: fine border + very small soft elevation;
- raised/floating controls: slightly stronger restrained elevation;
- modal/popover/command/floating surfaces: highest ordinary UI elevation.

Glass/translucency is **optional and proof-gated**, never a mandatory signature.

Potentially acceptable only on bounded floating/transient surfaces such as command palette, popovers, selected floating tools or a bounded Jarvis transient surface.

Normally forbidden on dense tables, navigator, Properties body, Analysis Dock grids and large structural engineering canvas frames.

Every translucent candidate requires an opaque fallback. If glass adds visual noise or weakens contrast, omit it.

## 13. Motion

Ordinary motion must be near-subliminal and must never delay the action it accompanies.

Direction:

- hover/press/focus/selection: about 80–140ms;
- panel/tab/popover transitions: about 120–180ms;
- `prefers-reduced-motion` collapses non-essential motion to effectively immediate behavior.

Indefinite/richer animation is authorized only while real work is actually pending, such as AI response, solver run, artifact load or other genuine wait. It cannot fabricate percentage completion or continue after the pending state ends.

Jarvis may receive a more organic pending animation than ordinary loaders, but it remains bounded, same-product and non-distracting.

## 14. Jarvis visual language

Jarvis is an integrated expert colleague/butler presence, not a separate chatbot brand.

It uses the same core typography, icon family, spacing, surfaces and interaction grammar as the workstation. It may receive:

- slightly softer floating geometry;
- subtle accent-surface modulation;
- restrained elevation/translucency where proof passes;
- a distinct real-pending animation;
- clearer proposal/confirm/reject hierarchy using existing deterministic authority.

Forbidden: purple gradients, sparkle/magic AI motifs, independent AI-brand chrome, or affordances that blur proposal versus executed engineering change.

## 15. Required canonical proof surfaces

The final implementation must be judged on real product surfaces, not a styleguide-only page.

### Proof A — BLUECAD / Model

Use real shell/navigation with BLUECAD viewport visible, an object/part selected, populated Properties, Jarvis content/action structure and Analysis Dock where current semantics allow it.

### Proof B — Process scaffold

Use `/design/process` with the merged 058d inert scaffold, shell, sidecar and Analysis Dock relationship visible. 100 must style the form without inventing nodes, streams, unit operations or process truth.

### Proof C — dense data

Use the denser real Engineering Data or Runs state on the exact implementation head, with realistic rows, metadata, status and actions.

### Proof D — Settings

Show appearance controls plus Microalgae, Leaf Chlorophyll, Lagoon and Custom accent; native chooser/HEX; Reset/default behavior; and immediately understandable application/preview.

All A–D are required in canonical light. Dark parity must additionally prove shell/navigation, at least one dense engineering screen, Settings accent controls and focus/selected/status states.

## 16. Proof-gated optional decisions

The following are deliberately not mandatory:

- Instrument Serif display accent;
- glass/translucent treatment;
- Phosphor duotone top-level/Jarvis emphasis;
- richer Jarvis waiting animation beyond a minimal coherent pending state.

Keep them only when browser proof demonstrates clearer hierarchy/identity without harming density, readability, contrast or product seriousness. Omit them rather than forcing visual effects to satisfy the concept.

## 17. Accessibility and readability invariants

100 must preserve or improve:

- WCAG AA ordinary-text contrast against actual surfaces (target 4.5:1);
- clearly visible keyboard focus in light and dark;
- non-color status signaling;
- distinguishable disabled/unavailable state;
- hover/focus/selected distinction;
- reduced-motion behavior;
- dense 12/13/14px hierarchy without destructive truncation;
- tabular-numeral alignment for repeated engineering values;
- accent-independent scientific/status meaning;
- opaque readability fallback for any translucent treatment.

Visual polish that weakens engineering comprehension is a failed implementation.

## 18. Semantic regression boundary

100 performs zero redefinition of:

- route/stage meaning;
- canonical versus working/run/result authority;
- Jarvis proposal/confirm/reject authority;
- Engineering Data lifecycle semantics;
- BLUECAD selection/scene semantics;
- Process/Lineage semantics;
- process topology/equipment/stream semantics;
- evaluator/solver behavior;
- backend API/schema/persistence;
- provider/tool/runner execution paths.

If visual implementation appears to require one of these changes, narrow or re-derive 100 rather than hiding the semantic change in styling.

## 19. Explicit non-goals

100 does not implement:

- new backend routes, tables, schema, stores or services;
- process nodes/streams/equipment or editable process topology;
- process/PFD engineering-symbol vocabulary;
- new solver/evaluator behavior;
- new Jarvis action types or AI execution paths;
- a new theme framework/state manager;
- a generic animation framework;
- a third-party color picker unless readiness proves native controls insufficient;
- a styleguide-only replacement for real-screen proof;
- broad product re-layout;
- Notes/scratchpad;
- routine 062 grading UI;
- 100a/100b codebase cleanup;
- any 101–110 architecture/evaluator work.

## 20. Readiness questions

A separate exact-master full-spec/readiness sequence must answer at least:

1. What exact frontend files/tokens/components form the minimum implementation allow-list?
2. How are Instrument Sans and IBM Plex Mono delivered and licensed, and are bundled font files preferable to network loading for the local operator product?
3. Is Instrument Serif omitted or retained after proving one exact rare display role?
4. What exact `@phosphor-icons/react` version/license is acceptable, and which existing text/symbol affordances should be replaced in 100 without unnecessary churn?
5. Can accent derivation remain dependency-free through CSS variables/OKLCH/`color-mix()` across the actual supported browser matrix?
6. What deterministic fallback is used when stored accent/custom values are invalid or unsupported?
7. What existing appearance utility/storage seam should own accent preference without creating a second visual-state owner?
8. Which semantic status/chart/viewport colors must be explicitly isolated from accent variables?
9. Which CSS selectors/surfaces currently violate the target density/radius/elevation language and are in scope for bounded migration?
10. Does any glass candidate pass the hardest real content proof, or should implementation remain opaque?
11. Does Instrument Serif improve the exact canonical screens, or should it be omitted?
12. Which real pending states already exist and may receive motion without fabricating work or progress?
13. What deterministic tests prove theme/accent persistence, safe fallback, reduced motion, icon-family consistency and semantic isolation?
14. What browser harness/evidence flow can prove A–D in light plus required dark parity without creating synthetic product semantics?
15. Which exact current dense screen is harder between Engineering Data and Runs and therefore becomes Proof C?
16. How will the implementation prove no page-level overflow/regression at effective 200% and compact desktop widths?
17. What license/notice changes are required for the selected open-source fonts/icons?
18. Can the entire slice remain frontend-only except repository license/notice metadata? If not, stop and narrow rather than adding backend authority.

## 21. Deterministic acceptance requirements

The full spec/readiness must translate current runtime into exact-head deterministic tests for at least:

1. appearance remains exactly the accepted `system | light | dark` contract and defaults safely;
2. accent choices are exactly Microalgae, Leaf Chlorophyll, Lagoon and Custom;
3. invalid/stale accent persistence fails to Microalgae;
4. Reset restores Microalgae;
5. Custom HEX validation rejects malformed values without leaking them into CSS/application state;
6. user accent changes only accent-owned channels and cannot replace semantic status/scientific colors;
7. warm/orange Custom accent leaves warning/error/success/proposed/stale/unavailable/scientific channels unchanged;
8. `prefers-reduced-motion` removes/collapses non-essential motion;
9. indefinite animation is tied to a real pending state and stops when pending ends;
10. only Phosphor is introduced as the generic icon family;
11. icon-only controls added/changed by 100 have accessible names;
12. generic icons do not imply process unit-operation semantics;
13. font-family use follows UI-vs-technical context boundaries;
14. no required information drops below 12px;
15. no new backend/provider/runner/canonical mutation path appears;
16. route/stage/selection/lifecycle/Jarvis-action semantics remain unchanged;
17. existing light/dark/reduced-motion/keyboard semantics and 058d scaffold behavior remain intact.

## 22. Browser acceptance matrix

The eventual implementation requires real-browser evidence for:

- Proof A, B, C and D in canonical light;
- shell/navigation + at least one dense engineering screen + Settings accent + focus/selected/status in dark;
- all three curated accents;
- at least two materially different Custom seeds including warm/orange;
- invalid stored Custom fallback and Reset;
- keyboard-only navigation/focus on the touched surfaces;
- reduced-motion behavior;
- effective 200% / compact desktop no page-level horizontal overflow;
- dense typography/readability and long-label behavior;
- structural surface alignment/elevation without detached-card dominance;
- optional glass only if retained, over the hardest permitted content and with opaque fallback;
- no semantic recoloring of status/scientific channels;
- no fake process semantics in `/design/process`;
- no provider/runner/backend/canonical side effect produced by purely visual interactions.

Screenshots alone are insufficient; state/effect assertions are required where semantics could regress.

## 23. Migration and rollback

100 should be an independently removable visual layer over the existing workstation.

Expected migration is limited to frontend visual dependencies/assets, semantic token values/roles, visual-preference state, bounded shared components and per-surface CSS/component adoption required to make the identity coherent.

No backend/data migration exists.

Rollback restores the prior visual tokens/components/assets while leaving project data, routes, engineering state, run history, process scaffold and backend authority unchanged. Accent preference must fail safely if the implementation is removed or its stored shape changes.

## 24. Downstream hold

After 100 implementation merges and is registry-reconciled, the maintainer requires a visual inspection checkpoint before any 100a/100b or later slice begins.

The queue must stop at that point with a remote checkpoint containing:

- exact 100 merge SHA;
- principal frontend files changed;
- browser/evidence locations;
- minimum instructions to run/view the merged UI;
- any proof-gated options deliberately omitted or compromises retained.

No post-100 slice is authorized by this definition.