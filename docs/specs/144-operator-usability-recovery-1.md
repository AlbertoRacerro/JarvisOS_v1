# 144 — OPERATOR-USABILITY-RECOVERY-1

Status: **READY by explicit maintainer decision — 2026-09-15**

Exact derivation base: `5922d8c400d5638c34d5b2d0fcfdd4e0d0ae10f7`.

## Outcome

Make the already-shipped JarvisOS product genuinely usable by a human operator before adding Hermes or new engineering breadth.

This is not another narrow cosmetic pass. It is a product-completion recovery over the current operator-facing application. Existing backend/domain truth should be exposed through a coherent, intuitive, responsive frontend that an informed engineer can use without knowing repository internals, spec IDs, UUIDs or API shapes.

The accepted standard is:

`existing truthful backend capability -> obvious operator path -> real interaction -> useful feedback -> persisted/recoverable result`

A backend-only capability, an inert-looking control, a technically correct but unreadable projection, or a page that requires repository knowledge to operate is not complete.

## Working mode

This slice is intentionally optimized for one persistent senior implementation session rather than repeated coordinator handoffs.

The implementer should:

1. work from fresh `master` and own the result end-to-end in one implementation branch/worktree;
2. inspect the real backend/API owners and the canonical HTML references before changing UI;
3. run the application in a real browser repeatedly during implementation;
4. use an edit -> launch -> interact -> inspect/screenshot -> repair loop until the primary tasks feel coherent;
5. make ordinary reversible UX/frontend decisions autonomously rather than asking for approval after each component;
6. prefer one coherent implementation PR over page-by-page PR ceremony;
7. stop only for a genuinely material product decision, destructive migration, secret/egress/security change, or a missing backend capability that would require new domain authority.

Do not optimize for smallest diff. Optimize for the smallest coherent product that is actually pleasant and obvious to use.

## Design authority

The canonical HTML references and manifest under `docs/design-references/` are the primary visual/compositional references.

Use them as functional design targets, not as decorative screenshots. Preserve their hierarchy, density, major regions, navigation logic and interaction intent unless real runtime evidence shows a better implementation is needed.

The implementer may create, split, remove or reorganize frontend pages, routes, components, panels, buttons, controls and CSS when doing so makes existing capabilities easier to discover and use while staying in the same product/design language.

Do not force current production component structure to survive if it is the reason the product is awkward.

## Authorized scope

### Frontend

Broad frontend refactoring is authorized across already-shipped operator surfaces, including:

- application shell/navigation;
- Project Knowledge / Project Basis;
- Models / Model Dossier;
- Literature;
- Search;
- Development Roadmap;
- Calendar;
- Brainstorm;
- Coding Repository;
- Coding Runtime;
- Development Pipeline projection;
- Settings / AI/provider projections;
- Process workspace;
- BLUECAD and related inspector/result surfaces;
- shared Jarvis sidecar/context/proposal UX;
- shared design-system/components where consolidation improves usability.

### Backend

Small backend/API adapter work is authorized when required to expose an already-existing capability cleanly to the frontend.

Examples:

- combine or reshape existing read projections;
- add a bounded human-friendly search normalization layer;
- expose already-owned detail required by a disclosure/editor;
- add a thin endpoint that composes existing owners without creating new canonical state;
- correct a frontend-blocking contract bug.

Do **not** create a new domain store, new provider/egress authority, new arbitrary execution authority, Hermes runtime, engineering solver stack, self-update, PTY or unrelated product domain under this slice.

If a needed human workflow truly has no backend capability, document the missing owner and either implement the smallest adapter/owner extension that is clearly within existing semantics or surface it as unavailable rather than inventing fake state.

## Known failures that must be fixed

The 2026-09-15 local operator audit on real Windows hardware established at least these failures:

1. Project Knowledge search is too literal for normal human phrasing; `perdite carico` does not naturally match `perdite di carico`.
2. Project Knowledge Jarvis sidecar presents a composer but does not accept input.
3. Project Knowledge record rows show disclosure chevrons that do not open anything.
4. Development production composition is materially worse than the approved references: Roadmap/Timeline/Calendar are not presented as a coherent operator workspace and Brainstorm does not provide the obvious dominant RAW idea-entry experience that was approved.
5. Coding Repository file research/preview is poorly laid out, clipped/overlapping and materially diverges from the approved Repository Inspector reference.
6. The product as a whole is not sufficiently interactive or intuitive for a human operator despite backend capability existing.

These are minimum known failures, not a closed bug list. The implementer is expected to inspect all current operator surfaces and fix the same causal class wherever encountered.

## Required product behavior

### Human-first navigation and information architecture

- A first-time informed user should understand the main areas and primary action without reading docs.
- Human labels, state and actions are primary; IDs/SHA/digests/raw payloads are secondary Technical details.
- A page should not expose backend taxonomy merely because that taxonomy exists.
- Controls that look interactive must be interactive.
- Disabled/unavailable actions must explain why and must not masquerade as working UI.

### Project Knowledge / Memory

- Search must support human phrasing at least through normalized/token matching while retaining exact/literal paths where useful.
- Relevant results must be inspectable in-place or through an obvious detail surface.
- Disclosures must genuinely open/close and be keyboard accessible.
- Exact selected records can be added to Jarvis context explicitly.
- The Jarvis composer must be a real usable interaction wherever the page claims Jarvis interaction is available.
- Working revisions/proposals/approval state must be understandable without knowing internal record IDs.

### Development

- Roadmap and Calendar must be first-class obvious views, following the approved reference hierarchy.
- Calendar should expose the intended practical Day/Week/Month/Agenda workflow with Week as the natural planning view unless fresh product evidence justifies otherwise.
- Brainstorm must have one dominant free-form RAW input where the user can dump unstructured thoughts quickly.
- Jarvis categorization/reconciliation/promotion should happen after capture, not force the user to structure the idea before saving it.
- The operator should be able to move naturally from brainstorm -> discussion/reconciliation -> proposal/promotion -> roadmap/calendar without understanding backend objects.

### Coding

- The Repository Inspector must prioritize readable file content, not the file tree.
- Markdown should have a useful rendered view and raw/source access when appropriate.
- Code/config/text must use a proper scrollable readable viewport with no overlap/clipping.
- File/path/ref identity must remain inspectable but not dominate the page.
- Inspect / add to Jarvis context / suggest modification must be obvious and correctly bound to the selected exact file/ref.
- Repository truth and Runtime truth remain distinct, but the relationship must be understandable in normal language.

### Models / Literature / Settings / Process / BLUECAD

- Audit each shipped surface for the same failure family: fake affordances, raw-machine-first presentation, hidden primary actions, unnecessary forms, clipped content, poor hierarchy, dead controls, inconsistent sidecar behavior and divergence from approved references.
- Preserve real domain semantics and existing authority; improve the human path to them.

### Shared Jarvis sidecar

- Replace decorative/disabled placeholders with one coherent reusable interaction surface where underlying AI-thread/context capability exists.
- Keep explicit context visible and removable.
- Do not create Hermes in this slice; the recovered sidecar becomes the host surface Hermes will later power.

## Interaction and visual quality requirements

The implementation must satisfy `docs/design-references/OPERATOR_USABILITY_AND_FRONTEND_COMPLETION_CONTRACT_2026-09-15.md` and the approved UI manifest.

At minimum:

- no accidental text overlap or clipping at supported desktop viewports;
- no horizontal overflow in ordinary workspaces unless the content intrinsically requires it;
- dominant work area gets dominant screen space;
- loading, success, stale, unavailable and error state are visible and understandable;
- keyboard focus and native/ARIA semantics are correct for disclosures, dialogs, forms and buttons;
- primary targets are large enough and visually identifiable;
- Technical details are available without making machine data the default experience;
- visual styling remains within the existing approved JarvisOS language rather than becoming a generic SaaS dashboard.

## Testing philosophy

Automated tests are a feedback tool, not a substitute for product acceptance.

The persistent implementer should add/update only the tests that materially protect the recovered flows.

Required before final acceptance:

1. relevant backend/frontend tests and production build green;
2. real-browser interaction smoke for the primary repaired flows;
3. representative reference/visual inspection at the canonical desktop viewport and at least one compact desktop viewport;
4. no fake affordances in the repaired surfaces;
5. persistence/restart check for representative user-created data where persistence is expected;
6. final maintainer hands-on acceptance on the real local Windows installation.

Do not spend hours constructing a bespoke proof framework when the browser can directly demonstrate the behavior.

## Suggested operator acceptance journey

The final product should make this journey obvious:

1. open JarvisOS and understand where Project Knowledge, Development, Coding and Design live;
2. search Project Knowledge using normal language and inspect a relevant record;
3. add that record to Jarvis context and type a real question;
4. dump an unstructured idea into Brainstorm, save it, find it again, and understand its state;
5. open Roadmap and Calendar and understand what is planned and when;
6. open Coding, find a Markdown/source file, read it comfortably, add it to context and create a bounded modification proposal;
7. inspect model/literature/settings/process/BLUECAD surfaces without encountering fake controls, machine-first clutter or broken layout;
8. restart the app and confirm representative persisted data is still present.

If the maintainer cannot complete this naturally, 144 is not done even if CI is green.

## Hard stop boundaries

The implementer may make broad reversible frontend/product-composition changes without additional permission.

Stop and ask only before:

- destructive or non-additive persistent-data migration;
- changing credential/secret handling;
- weakening egress/privacy/budget enforcement;
- granting arbitrary filesystem/process/terminal execution;
- merging to `master`;
- creating new paid external usage;
- materially changing canonical engineering truth semantics rather than presentation/access to existing owners.

Everything else inside this spec should be resolved autonomously using engineering judgement and browser evidence.

## Completion

One coherent implementation PR is preferred.

Do not split work merely because multiple pages are touched. Split only if there is a real independent risk boundary or the implementation becomes too large to review coherently.

The final merge decision requires maintainer hands-on acceptance in addition to green CI and independent review.