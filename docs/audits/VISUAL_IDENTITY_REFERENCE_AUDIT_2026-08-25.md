# Visual Identity reference audit — 2026-08-25

Status: design/reference evidence for future `100 VISUAL-IDENTITY-1`; **not implementation authority by itself**  
Disposition: `REFERENCE_ONLY` for external brand/product references unless explicitly noted otherwise.

## Why this audit exists

The maintainer selected the visual direction for JarvisOS before the 100 definition lifecycle so automated builders would not derive identity from the provisional UI. This audit records provenance, what is useful, what is deliberately rejected and what can legally/technically be adopted as a dependency.

## Current JarvisOS baseline inspected

At master `3d75fb79cf903c27ad42213ec127b74f82d1e362`:

- 058d Process workspace scaffold is merged/reconciled;
- the frontend already has centralized `frontend/src/styles/tokens.css` for typography, spacing, radius, shadows, motion and light/dark colors;
- the existing tokens still use Inter/system typography and the provisional green/neutral UI-Foundation palette;
- `frontend/src/theme.ts` already implements safe best-effort local appearance preference (`system | light | dark`) and is the natural pattern for non-authoritative visual accent preference;
- no generic icon library is currently present in `frontend/package.json`;
- current production routes include Home, Design Model/Process/Results/Lineage, Runs, Engineering Data, Review, Settings and AI Threads.

This means 100 can remain a visual-system/application-surface slice instead of inventing a second UI architecture.

## Maintainer-rated external visual references

### Bioo — 8.5/10

Source: `https://www.biootech.com/`

Useful:

- living-technology atmosphere;
- biological/natural image color treatment;
- relationship between advanced technology and nature.

Do not import:

- black marketing-site composition as the canonical engineering application;
- white-on-black hero typography as workstation grammar;
- brand assets.

### Generate:Biomedicines — 6/10

Source: `https://generatebiomedicines.com/`

Useful only as broad biotech/scientific context. Maintainer found no typography/palette mechanism worth carrying into the JarvisOS identity.

### Recursion — 7.5/10

Source: `https://www.recursion.com/`

Useful:

- body-type calm/readability;
- serious scientific product tone.

Do not import the brand color system or logo.

### Heirloom Carbon — 9/10

Source: `https://www.heirloomcarbon.com/`

Strongest conceptual reference:

- “best of nature and engineering” atmosphere;
- mineral/natural material cues;
- quiet, serious typography character;
- restrained climate-tech palette.

The exact current Heirloom web typeface was not reliably established from authoritative source evidence in this audit. Therefore the typography is **style reference only**; do not guess/copy a font or vendor unverified files.

### AIR COMPANY — 8+/10

Sources:

- `https://www.aircompany.com/`
- design provenance reference: `https://designeverywhere.co/work/air-company`

Design references identify **Suisse Int'l by Swiss Typefaces** in AIR COMPANY identity/web work. That is a commercial typeface. JarvisOS may use the character as inspiration but must not add/copy it without a separately licensed asset and explicit reason. No such dependency is necessary for 100.

### Linear — 8.5/10

Source: `https://linear.app/`

Useful:

- high-density modern product craft;
- typography clarity;
- restrained hierarchy and interaction polish.

Do not make JarvisOS black-first or visually read as developer SaaS.

### Raycast — 9/10

Source: `https://www.raycast.com/`

Highest component-craft reference:

- button quality;
- floating/transient surface polish;
- microinteraction quality;
- strong sense of deliberate product design.

Reduce Apple resemblance, gloss/glow and dark-first composition. JarvisOS needs more natural, material, human and slightly archaic/heroic gravity.

### Vercel — 8.5/10

Source: `https://vercel.com/`

Useful:

- typography discipline;
- restrained high-quality motion.

Do not import the black/white-first brand identity or developer-brand austerity.

### Frontier — 6/10

Source: `https://frontierclimate.com/`

No material positive style mechanism selected by maintainer; retain only as climate-tech comparison context.

## Typeface candidates and license evidence

### Instrument Sans — selected primary UI candidate

Official upstream: `https://github.com/Instrument/instrument-sans`

Upstream description: variable sans-serif combining precision with subtle playfulness, with width/weight flexibility and stylistic sets. License: **SIL Open Font License 1.1**. It is also distributed through Google Fonts.

Disposition: `DIRECT_DEPENDENCY`/bundled-font candidate for 100 after normal readiness/license-notice verification. Preferred primary UI family.

Reason: closer to the maintainer's humanistic-natural + rational-engineering target than simply retaining Inter, while remaining open and practical for application embedding.

### IBM Plex Mono — selected technical mono candidate

Official upstream: `https://github.com/IBM/plex`

IBM Plex is open-source under **SIL Open Font License 1.1** and includes Sans/Mono/other families; IBM documents UI/technical use.

Disposition: direct/bundled font candidate for technical strings only.

### Instrument Serif — optional proof-gated display accent

Official upstream: `https://github.com/Instrument/instrument-serif`

License: **SIL Open Font License 1.1**. Upstream describes it as a condensed display serif for large sizes.

Disposition: optional reference/direct candidate only for rare brand/display usage. It must not become ordinary engineering UI type. Omit if proof adds editorial noise.

### Commercial reference fonts

Suisse Int'l and any unidentified Heirloom/Linear/Raycast brand fonts remain reference-only unless a later change establishes exact license, need and distribution requirements. 100 does not need them.

## Icon-family audit

### Phosphor — selected

Official upstreams:

- `https://github.com/phosphor-icons/react`
- `https://github.com/phosphor-icons/core`

License: **MIT**.

The maintained React package is `@phosphor-icons/react`; upstream recommends it over legacy `phosphor-react`. It supports tree-shaking and six styles/weights (`thin`, `light`, `regular`, `bold`, `fill`, `duotone`). The core catalog exposes over twelve hundred icon concepts and tags.

Current JarvisOS semantic coverage was explicitly checked for navigation, data, runs, settings, Jarvis/chat, graph/lineage, process-stage flow, selection/3D inspection, measure/angle, parameters, validation/status, file actions, filtering/sorting, console, chart types and common CRUD/navigation actions. Sufficient candidates exist.

One literal generic `Axis` icon was not found, but current UI need is adequately represented by `Crosshair`/`BoundingBox`; a future actual CAD axis gizmo is not a generic app-icon requirement.

Important upstream capability: Phosphor documents extending the React package with custom icons through its `IconBase` abstraction and 256×256 SVG grid. That creates a coherent future path for custom process/PFD symbols without mixing generic icon families.

Disposition: `DIRECT_DEPENDENCY` candidate for spec 100. Generic family decision passes the maintainer rule: Phosphor first because current coverage is sufficient.

### Lucide / Tabler

Maintainer preference ranking places Lucide second and Tabler third. Because Phosphor passes current generic coverage, neither should be added by 100. Retain them only as future complete-family fallbacks if a later generic vocabulary expansion proves a real gap.

## Color-system technology evidence

Modern CSS support makes a dependency-free perceptual accent scale viable:

- MDN documents `oklch()` as broadly available across modern browsers since 2023;
- MDN documents `color-mix()` as broadly available since 2023 and supports interpolation in OKLCH;
- therefore a CSS-variable accent seed can derive bounded tonal variants without introducing a third-party color library, subject to the repository's actual supported-browser proof/fallback policy.

For Custom color input, native `<input type="color">` + validated HEX input is the minimum-necessary first implementation. A third-party color-picker dependency is not justified unless browser proof shows the native control fails product requirements.

`prefers-reduced-transparency` has incomplete browser support and may be used only as an enhancement; structural opacity/fallback must exist independently. `prefers-reduced-motion` remains the dependable motion accessibility boundary.

References:

- `https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/oklch`
- `https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/color-mix`
- `https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-transparency`

## Selected disposition

The design reference set is now sufficiently saturated for spec 100. More moodboard browsing is unlikely to improve the implementation boundary.

Proceed with:

- Visual direction: `docs/design/visual-identity-100/`;
- Primary UI type candidate: Instrument Sans;
- Technical mono: IBM Plex Mono;
- Generic icon family: Phosphor only;
- Accent architecture: three curated seeds + Custom, perceptually derived and semantically isolated;
- light-first mineral surface system;
- restrained depth/glass/motion as specified in the authority pack.

Do **not** spend another design cycle enumerating aesthetic sites unless the 100 browser proof exposes a specific unresolved visual failure.
