# Operator usability research — 2026-09-15

Status: research/audit evidence supporting `docs/design-references/OPERATOR_USABILITY_AND_FRONTEND_COMPLETION_CONTRACT_2026-09-15.md`; **not implementation authority**.

## Trigger

A real local Windows run of current `master` exposed a mismatch between backend/authority maturity and operator usability:

- Project Search truthfully implemented literal search, but natural shorthand such as `perdite carico` could miss a record containing `perdite di carico`;
- Project Basis rows visually presented chevrons but the rendered implementation had no disclosure interaction;
- the Project Basis Jarvis composer rendered as an input-like surface but was hard-disabled;
- Development backend state existed, but the production page composition was substantially less usable and less faithful to the approved Timeline/Calendar/Brainstorm mocks;
- Coding Repository showed real remote evidence, but the file-research/preview area was cramped/overlapping and materially different from the approved Repository Inspector;
- the overall workstation required too much knowledge of its own internal structure to use comfortably.

Repository inspection confirmed that some of these were implementation facts rather than local-environment problems. In particular, `frontend/src/components/fusion/FinalOperatorReadSurface.tsx` rendered Project Basis record arrows as non-interactive spans and rendered the Jarvis composer with `aria-disabled=true` and a disabled Send button.

## Existing JarvisOS authority already pointed in the right direction

The problem was not absence of visual product intent.

`FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md` already states that:

- canonical HTML is the implementation target at its reference viewport;
- panel order, hierarchy, density, control grouping and interactions are binding;
- visible interactions are product requirements, not decorative prototype behavior;
- a builder may not replace a missing backend function with a simpler unrelated UI;
- browser proof should compare production against canonical HTML and interaction authority.

`FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` already freezes action semantics such as PRESENTATION, READ, CONTEXT, PROPOSE, COMMIT, EXECUTE and NAVIGATE.

The missing piece was a strong enough **definition of usable completion and evidence**. Existing browser proofs were heavily optimized for authority/correctness: exact SHA, server/client agreement, safe-action absence, truthful labels and screenshot capture. Those are valuable but insufficient to prove that a human can actually operate the surface easily.

For example, `.github/browser-proof/plans/140-coding.json` checks server-owned repository truth, exact commit identities, semantic-delta schema, visible headings, forbidden direct-mutation buttons and screenshots. It does not assert that the Repository Inspector is readable, that the main preview occupies useful space, that text does not overlap, or that a normal file-inspection task can be completed intuitively.

## External guidance reviewed

### W3C WCAG 2.2

Sources:

- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/WAI/WCAG22/understanding/

Relevant principles for JarvisOS:

- keyboard accessibility and logical focus order;
- visible focus and focus not obscured;
- semantic name/role/value;
- status-message exposure;
- minimum pointer-target size;
- alternatives to drag-only interaction;
- consistent navigation/help;
- error prevention and redundant-entry reduction.

JarvisOS is a desktop-style technical web application, but accessibility rules also improve ordinary operator ergonomics: larger hit areas, visible state, predictable focus and semantic controls reduce mistakes for every user.

### WAI ARIA Authoring Practices Guide

Sources:

- https://www.w3.org/WAI/ARIA/apg/
- https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/
- https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/

Key lesson: a visual role is a behavioral promise. A disclosure indicator should be a real disclosure control with keyboard activation and `aria-expanded`; a div/span styled like an interactive widget without the corresponding semantics/keyboard behavior is not acceptable.

This directly maps to the observed Project Basis chevron defect.

### Nielsen Norman Group usability heuristics

Source:

- https://www.nngroup.com/articles/ten-usability-heuristics/

The most relevant heuristics for JarvisOS are:

- visibility of system status;
- match with the operator's real-world mental model;
- user control and freedom;
- consistency and standards;
- error prevention;
- recognition rather than recall;
- flexibility/efficiency;
- minimalist presentation of what matters now;
- understandable error recovery.

For JarvisOS, `recognition rather than recall` means the operator should not have to remember a backend taxonomy, exact sentence, UUID or hidden route to find a capability.

### GOV.UK service/design guidance

Sources:

- https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use
- https://www.gov.uk/service-manual/design/writing-for-user-interfaces
- https://www.gov.uk/guidance/government-design-principles
- https://www.gov.uk/service-manual/design/introduction-designing-government-services

Useful principles:

- a service should let a user complete the task simply, ideally first time and with minimal help;
- test actual user interaction frequently;
- internal services deserve the same usability standards as public services;
- use user language and reduce cognitive load;
- if substantial text is required to explain how a basic interface works, improve the interface rather than adding documentation;
- do the hard work in implementation so the complex underlying system feels simple to operate.

This is particularly applicable to JarvisOS because it is a highly custom single-user engineering system: there is no external manual/ecosystem the maintainer can rely on to compensate for opaque interaction design.

### GitHub Primer

Sources:

- https://primer.style/accessibility/design-guidance/
- https://primer.style/accessibility/design-guidance/focus-management/
- https://primer.style/product/getting-started/foundations/layout/
- https://primer.style/product/ui-patterns/navigation/
- https://primer.style/product/components/dialog/accessibility/

Relevant patterns:

- content-focused hierarchy and calm layout;
- predictable navigation and location awareness;
- keyboard/focus management as an explicit implementation concern;
- dialogs that trap/restore focus correctly;
- semantic links versus buttons;
- responsive behavior that does not remove capability.

### Visual Studio Code UX guidelines

Sources:

- https://code.visualstudio.com/api/ux-guidelines/overview
- https://code.visualstudio.com/api/ux-guidelines/sidebars
- https://code.visualstudio.com/api/ux-guidelines/panel
- https://code.visualstudio.com/api/ux-guidelines/views

VS Code is a useful reference because JarvisOS is also a dense workbench rather than a simple content site.

Useful lessons:

- major containers have distinct roles;
- the central editor/work area should retain useful space;
- sidebars contain grouped contextual views and should not proliferate;
- supporting panels belong where horizontal space helps them and should not dominate the primary task;
- actions should be contextual instead of permanently flooding the interface;
- custom UI is appropriate when native primitives cannot express the task, but must remain accessible and resize correctly.

These principles support the existing JarvisOS approved mocks: dominant Process/BLUECAD/Timeline/Inspector work areas with supporting Jarvis/properties/detail regions.

### Playwright

Sources:

- https://playwright.dev/docs/accessibility-testing
- https://playwright.dev/docs/test-snapshots
- https://playwright.dev/docs/aria-snapshots

Useful testing lessons:

- browser tests should simulate actual interactions and assert outcomes;
- `@axe-core/playwright` can catch common accessibility violations but cannot replace manual assessment;
- visual screenshot comparison can detect composition regressions when run in a deterministic environment;
- accessibility-tree snapshots can validate semantic structure/roles/states where stable.

The key implication for JarvisOS is that a browser proof that only checks text presence and then saves a screenshot is weaker than a task test plus visual comparison plus accessibility/layout assertions.

## Derived JarvisOS design/testing model

The product needs six complementary evidence layers for material operator-facing work:

1. **Authority/data correctness** — server state and action semantics are correct.
2. **Frontend wiring** — the operator can reach and exercise the capability through the app.
3. **Interaction correctness** — controls behave as they appear to behave.
4. **Visual/composition fidelity** — live UI remains faithful to the canonical HTML direction.
5. **Accessibility/layout integrity** — keyboard/focus/semantics and readable, non-overlapping layout hold.
6. **Human task success** — the maintainer can perform the primary task without needing to know implementation architecture.

No single layer replaces the others.

## Coding implications

The following implementation habits are preferred:

- use semantic native controls first;
- centralize repeated interactive patterns (buttons, tabs, disclosures, dialogs, form fields, context chips, error/loading states) so behavior stays consistent;
- keep local React state for presentation/draft state and server state authoritative for canonical records;
- use request-generation/cancellation guards for fast-changing selections;
- design long text/code/media preview containers explicitly rather than allowing default overflow to decide the layout;
- preserve canonical HTML-specific composition even when shared components are used;
- keep the Jarvis sidecar shared instead of implementing one disabled/fake variant per surface;
- prefer progressive disclosure over either hiding technical evidence completely or flooding the first screen with raw IDs/JSON.

## Proposed future repair direction

The local acceptance findings suggest one coherent operator-usability repair wave rather than isolated styling patches. Likely causal groups are:

1. shared Jarvis sidecar activation/integration;
2. Project Basis disclosure/detail interaction;
3. human-tolerant Project Search;
4. Development Timeline/Calendar/Brainstorm production composition restored to approved HTML while reusing existing backend 116/117 ownership;
5. Coding Repository Inspector layout/preview restored to approved HTML while keeping 118/123/140 authority;
6. a stronger browser/visual/accessibility/operator-acceptance gate for future user-facing work.

This audit does not authorize those runtime changes. A normal accepted spec/readiness slice must own the repair.