# 100f FINAL-OPERATOR-FRONTEND-FUSION-1

Status: maintainer-approved full specification; frontend-only. Implementation authority begins only after `docs/specs/STATUS.md` records this row as `ready` and all hard dependencies are merged.

## Purpose

Translate all eleven canonical operator HTML references into one coherent production React/Vite JarvisOS frontend that the maintainer can run and inspect before later backend/domain slices are implemented.

This is a **frontend integration/migration slice**, not backend emulation. It must preserve truthful current functionality and render future approved capabilities without fabricating their missing backend authority.

## Governing packet

Implementation MUST read and follow the exact current revisions of:

1. `AGENTS.md`;
2. `docs/specs/STATUS.md`;
3. `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`;
4. all eleven canonical HTML files and their manifest SHA-256/Git blob/reference viewport identities;
5. `docs/design-references/FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md`;
6. `docs/design-references/FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md`;
7. the most-specific approved Process, BLUECAD, Memory, Development, Coding and Settings reference documents;
8. `docs/design-references/FINAL_FRONTEND_FUSION_PRIORITY_2026-08-27.md`;
9. `docs/spec-drafts/FINAL_PRODUCT_SPEC_PROMOTION_CONTRACT_2026-08-27.md`;
10. PD-03, PD-04, PD-05, PD-07 and PD-08 where applicable;
11. exact current frontend code and existing API/read/action contracts.

When visual/composition sources conflict, use the precedence in the approved manifest. When implementation permission conflicts, live accepted spec/STATUS/ADR/current code authority wins.

## Exact canonical surfaces

The production frontend MUST expose all of the following in one shared shell:

| Surface | Canonical production route | Canonical HTML |
| --- | --- | --- |
| Design / Process | `/design/process` | `docs/design-references/process-beta/process-beta-approved-2026-08-26.html` |
| Design / BLUECAD | `/design/bluecad` | `docs/design-references/bluecad-beta/bluecad-beta-approved-2026-08-26.html` |
| Memory / Project Basis | `/memory/project-basis` | `docs/design-references/memory-beta/memory-project-basis-beta-approved-2026-08-26.html` |
| Memory / Models | `/memory/models` | `docs/design-references/memory-beta/memory-models-beta-approved-2026-08-26.html` |
| Memory / Literature | `/memory/literature` | `docs/design-references/memory-beta/memory-literature-beta-approved-2026-08-26.html` |
| Development / Roadmap / Timeline | `/development/roadmap/timeline` | `docs/design-references/development-beta/development-roadmap-timeline-beta-approved-2026-08-27.html` |
| Development / Roadmap / Calendar | `/development/roadmap/calendar` | `docs/design-references/development-beta/development-calendar-beta-approved-2026-08-27.html` |
| Development / Brainstorm | `/development/brainstorm` | `docs/design-references/development-beta/development-brainstorm-beta-approved-2026-08-27.html` |
| Coding / Repository | `/coding/repository` | `docs/design-references/coding-beta/coding-repository-beta-approved-2026-08-27.html` |
| Coding / Runtime | `/coding/runtime` | `docs/design-references/coding-beta/coding-runtime-beta-approved-2026-08-27.html` |
| Settings | `/settings/appearance`, `/settings/ai`, `/settings/system` | `docs/design-references/settings-beta/settings-beta-approved-2026-08-26.html` |

`/` MUST resolve to `/design/process`. `/settings` MUST resolve to `/settings/appearance`.

## Final information architecture

### Primary rail

Exactly:

`Design | Memory | Development | Coding | Settings`

No normal `Home`.

### Peer navigation

- Design: `Process | BLUECAD`.
- Memory: `Project Basis | Models | Literature`.
- Development: `Roadmap | Brainstorm`.
- Roadmap: `Timeline | Calendar`.
- Coding: `Repository | Runtime`.
- Settings: `Appearance | AI | System`.

No additional peer destination may be introduced by this slice.

## Current-master migration obligations

Exact pre-implementation master currently contains older route/IA authority in `frontend/src/app/routes.ts` and `frontend/src/App.tsx`, including Home, Runs, Engineering Data, Review and Design Model/Results/Lineage.

100f MUST migrate the visible normal IA without deleting useful existing backend/frontend capability merely because its old peer page disappears.

### Legacy route behavior

The following old paths MUST remain deterministic and must not become 404s during this slice:

- `/home` -> replace/redirect to `/design/process`;
- `/design/model` -> replace/redirect to `/memory/models`;
- `/design/results` -> replace/redirect to `/memory/models`;
- `/design/lineage` and legacy `/design/flowsheet` -> replace/redirect to `/memory/models` unless a more-specific existing contextual owner can be preserved without creating a peer page;
- `/runs`, `/engineering-data`, `/review`, `/ai-threads` -> remain non-primary compatibility/context routes or redirect to the truthful final owner only when the existing capability remains reachable. They MUST NOT reappear in the primary rail.

Do not delete existing backend routes, records, tests or service capability in 100f.

## Organic shared-shell implementation

The eleven canonical surfaces MUST be production React/Vite views. They MUST NOT be implemented by iframe/static HTML embedding.

The implementation MUST have one shared application shell for semantically shared elements, including at minimum:

- primary rail;
- global appearance/theme/token system;
- workspace heading/peer-tab language;
- shared typography and Phosphor icon rules;
- shared Jarvis visual language where the canonical surface includes Jarvis;
- the Process/BLUECAD Jarvis-over-Properties inspector as one structural component family rather than two disconnected copies;
- common loading/error/unavailable treatment.

Do not mechanically force every screen through one generic dashboard/card layout. Surface-specific regions and proportions remain controlled by the canonical HTML.

## Visual contract

At each manifest reference viewport the rendered production surface MUST retain:

- canonical major panel geometry/order;
- canonical density and dominant/subordinate surfaces;
- canonical typography roles;
- warm light-first limestone/near-white visual system;
- restrained chlorophyll/accent behavior;
- near-square/small-radius language;
- Phosphor generic icons;
- IBM Plex Mono only for code/log/path/hash/terminal-style technical text;
- Roadmap condensed/light workstream type treatment only where approved;
- no broad green canvas wash;
- no generic SaaS dashboard reinterpretation.

Pixel-perfect raster identity is not required, but composition-changing drift is a failure.

## Truth and staged-functionality rule

Fixture values in canonical HTML are layout evidence only and MUST NOT appear as production facts unless the current backend independently returns the same value.

For every displayed data field/control:

1. if a current accepted backend/read contract exists, use it;
2. if a current frontend-only presentation behavior is sufficient, implement that behavior without canonical mutation;
3. if the approved action requires a missing backend owner, render the canonical affordance only as truthful disabled/read-only/unavailable/future state;
4. never create a private React truth store or fake API solely to make the UI appear populated;
5. unknown/failure remains unknown/failure and is not converted into `Healthy`, `PASS`, `Ready`, `Current`, `Aligned`, fake counts or fake metrics.

## Action-class gate

The semantic action class from `FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md` is binding.

### PRESENTATION

May be implemented in this slice where it changes no canonical state, including:

- route/tab selection;
- disclosure expand/collapse;
- local presentation filters;
- Timeline/Calendar view switching when it does not invent data;
- Repository preview tab switching;
- bounded panel collapse/expand;
- selection/highlight/zoom/pan where an existing component already supports it safely.

### READ

May be wired only to existing truthful API/read-model owners. Empty/unavailable responses must render truthfully.

### CONTEXT

May be active only where existing Jarvis context authority can bind the exact target identity safely. Otherwise show the approved control disabled/unavailable; selection alone never implies context insertion.

### PROPOSE

May be active only where an existing accepted proposal path already owns the exact target/action. Otherwise disabled/unavailable.

### COMMIT / EXECUTE

No new COMMIT or EXECUTE backend authority is created by 100f. Existing accepted operations may remain usable when they fit the final surface. Missing operations remain disabled/unavailable.

### NAVIGATE

Internal final routes and truthful external GitHub/file links may be wired when exact destinations already exist.

## Surface-specific frontend requirements

### Design / Process

- reproduce canonical equipment navigator / dominant warm-grid canvas / Jarvis-over-Properties composition;
- retain compact icon-first toolbar and visible future process affordances;
- existing `058d` Process scaffold remains the safe base where applicable;
- no process topology/node/stream/equipment canonical store may be invented;
- missing Add/Connect/Disconnect/Solve semantics remain visibly unavailable;
- existing truthful analytics/Jarvis/Properties capability may be reused only under its current authority.

### Design / BLUECAD

- dominant real 3D viewport remains the core surface;
- reuse existing THREE/BLUECAD viewer, semantic selection and existing engineering Properties where already accepted;
- use model/feature navigator semantics, not Process equipment;
- technical dock remains subordinate;
- do not fabricate CAD validation/results/export state;
- shared Process-compatible inspector structure is mandatory.

### Memory / Project Basis

- render canonical `Project search | Project Basis | Jarvis` composition;
- Project search can use only existing truthful search/read capability; otherwise show empty/unavailable state;
- preserve disclosure and compact engineering-row layout;
- working-revision/Approve-all/revalidation controls are visible only with truthful unavailable states unless current accepted backend authority already supports the exact action;
- no frontend-created Project Basis records.

### Memory / Models

- render exact-version dossier shell with bounded disclosure sections and `Collapse all` presentation behavior;
- bind any currently available model/version/run/artifact data to exact identities;
- missing dossier families render truthful empty/unavailable sections rather than fixture counts;
- Results/Runs/Lineage remain contextual sections, not peer routes.

### Memory / Literature

- compact list-first center surface with inline multi-expand behavior;
- multiple records can remain expanded when real records exist;
- truthful preview/open behavior only for files actually supported by current backend routes;
- if Literature provenance backend is not yet complete, preserve the composition with explicit empty/unavailable content rather than fabricated sources.

### Development / Roadmap Timeline

- reproduce large Timeline composition plus collapsible `Execution status` underneath;
- no standalone Board;
- `Ready | In progress | Blocked` remain the primary execution snapshot headings;
- if canonical Roadmap domain storage is not implemented yet, bars/items may not be fabricated as production data: render the actual empty/unavailable domain state while preserving geometry and controls;
- Add/Edit/Delete/status mutation remain disabled until canonical owner exists unless an accepted current owner already supports the exact operation.

### Development / Calendar

- reproduce Day/Week/Month/Agenda shell with Week default;
- time grid, headers, add-event affordance and event-detail surfaces may exist as presentation structure;
- do not synthesize Calendar events from Roadmap spans or fixtures;
- mutation controls remain disabled until canonical scheduling owner exists.

### Development / Brainstorm

- reproduce Raw/Reconciled/Jarvis context layout;
- implement frontend-only expansion/collapse and context-selection presentation safely;
- do not fabricate IDEA/Raw records;
- attachment/microphone/promote/reconcile actions remain truthful unavailable where owners do not yet exist;
- opening a record never silently adds it to Jarvis context.

### Coding / Repository

- reproduce Repository Inspector-first composition;
- architecture is selectable/inspectable, not permanently pinned;
- where current repository backend/frontend integration can truthfully read data, bind exact repository/ref/path/SHA evidence;
- otherwise render truthful unavailable state;
- `Suggest modification` remains proposal-only and cannot save files directly;
- no frontend GitHub token/API authority.

### Coding / Runtime

- reproduce local-versus-GitHub identity hierarchy;
- never display fixture SHA/health/alignment values;
- if local runtime identity or remote compare is not available through accepted backend APIs, show explicit Unknown/Unavailable while preserving canonical comparison geometry;
- safe-update pipeline remains compact and disabled without its backend owner;
- future Terminal | Logs affordance may be represented only in the truthful state permitted by current authority; no browser shell/process execution.

### Settings

- preserve exactly Appearance | AI | System;
- Appearance uses existing canonical appearance state;
- AI must remain provider-agnostic and credentials provider/integration-scoped;
- use existing secure/provider/system APIs where available;
- do not expose secrets or create localStorage credential state;
- System statuses must be observed, never fixture Healthy/Ready.

## Frontend state rules

Presentation state may live in React when it has no canonical meaning, including selected tab, disclosure state, preview mode, non-authoritative filters and panel collapse.

Canonical/project/repository/runtime truth may not be created in React merely for 100f.

Route selection/history must remain deterministic. Back/forward navigation must preserve normal browser semantics.

## Loading / empty / unavailable / error contract

Every canonical surface MUST have production states for:

- loading;
- truthful empty;
- capability unavailable/not yet implemented;
- read failure;
- unauthorized/unsafe action if applicable;
- stale exact target where an existing action reports it.

These states should preserve the approved geometry where practical and must not substitute demo fixture content.

## Accessibility

- keyboard access for primary/peer navigation;
- visible focus treatment consistent with canonical accent language;
- disclosure controls expose appropriate expanded/collapsed semantics;
- icon-only controls have accessible names/tooltips where appropriate;
- green/orange/status meaning never relies on color alone;
- disabled/unavailable actions communicate why they are unavailable.

## No-go scope

100f MUST NOT:

- modify backend schema/domain/API solely to fill the new screens;
- add a fake backend or fixture API;
- implement Roadmap/Calendar/Brainstorm/Literature/Repository/Runtime domain stores that belong to later specs;
- implement Aspen-like editable process topology;
- add a PTY/terminal backend;
- add self-update authority;
- add provider/Hermes authority;
- perform 100a/100b cleanup;
- delete desired-but-unwired capabilities merely because old peer routes disappear;
- redesign any canonical HTML surface;
- iframe/embed canonical HTML in production.

## Expected implementation touch surface

The builder should prefer the minimum existing frontend boundaries. Likely authorized files include:

- `frontend/src/App.tsx`;
- `frontend/src/app/routes.ts` and router tests;
- `frontend/src/components/Layout*` / shell/navigation components;
- shared design/workspace components;
- new frontend page/workspace components for final Memory/Development/Coding surfaces;
- existing Settings/Process/BLUECAD components where migrated rather than duplicated;
- `frontend/src/styles/**`, `frontend/src/theme.ts` only as needed for canonical conformance;
- `frontend/tests/**` for 100f conformance;
- deterministic browser-proof harness/artifact metadata under the repository's existing proof conventions.

Backend files are out of scope unless a test-only fixture/mocking boundary already exists and the change does not alter runtime authority; any such exception must be justified in the PR body.

## Deterministic tests

The implementation MUST add a `100f` frontend conformance test and include it in `npm run build`.

The deterministic test suite MUST prove at minimum:

1. primary nav is exactly the five final destinations;
2. no Home/Runs/Engineering Data/Review peer nav remains;
3. Design peer nav is exactly Process/BLUECAD;
4. all final routes resolve and browser-history navigation works;
5. legacy routes deterministically redirect/remain compatibility-only rather than becoming primary peers;
6. all eleven canonical surface components exist in production React and are not iframe/static HTML embeddings;
7. missing backend capability states contain no canonical HTML fixture values presented as truth;
8. unsupported COMMIT/EXECUTE controls are disabled/unavailable rather than fake-working;
9. shared Process/BLUECAD inspector structure is reused;
10. Settings tabs are exactly Appearance/AI/System;
11. repository/runtime identity fixture SHAs/health are absent from production source/data defaults;
12. existing `058d` and `100` conformance tests remain green or are updated only where the final approved overlay explicitly supersedes an old assertion.

`cd frontend && npm run build` is mandatory.

## Browser proof gate

Before implementation can merge, exact-head browser evidence MUST exist for all eleven canonical references at their manifest viewports.

Minimum proof set:

1. Process 1365×768;
2. BLUECAD 1365×768;
3. Project Basis 1600×1000;
4. Models 1600×1000;
5. Literature 1600×1000, including at least one inline-expansion state when real data or a safe presentation-only test fixture in the browser proof harness can exercise layout without shipping it as production truth;
6. Roadmap Timeline 1600×1000 with Execution status expanded/collapsed proof;
7. Calendar 1600×1000 with Week/default and add-event unavailable/available state as current authority permits;
8. Brainstorm 1600×1000 including reconciled expansion/context control state as authority permits;
9. Coding Repository 1600×1000;
10. Coding Runtime 1600×1000;
11. Settings 1365×768 covering Appearance/AI/System tabs.

Proof harness data, if needed solely to exercise visual states, MUST be clearly test-only and must never enter production default runtime state.

Each proof record MUST identify exact PR head, route, viewport, canonical HTML path/hash and resulting screenshot/artifact.

## Review gate

- exact implementation head frozen before final review;
- deterministic build/tests green on that same head;
- all eleven browser proof records complete;
- no unresolved material conformance finding;
- no fabricated backend/runtime state;
- no backend/schema scope creep;
- merge only with `expected_head_sha`.

External model review is optional/advisory unless repository policy at execution time requires it. Do not trigger repeated automatic review merely to obtain a PASS; deterministic conformance and exact-head evidence remain authoritative.

## Definition of done

100f is done only when:

1. the production app exposes the complete final five-workspace IA;
2. all eleven canonical surfaces are organically integrated into that app;
3. existing truthful backed functionality is preserved/reused;
4. missing backend functionality is explicit unavailable/read-only rather than fabricated or silently removed;
5. all eleven browser references pass exact-head visual/conformance inspection;
6. `npm run build` and all required frontend tests pass;
7. implementation PR merges and `STATUS.md` is reconciled to `merged`;
8. the maintainer can run the merged frontend and inspect the complete workstation before later backend queue work begins.

## Queue continuation

After 100f is merged and registry-reconciled, resume with `100a CODEBASE-LEAN-AUDIT-1`, then `100b`, then the planned 100c authority re-derivation and later backend/domain queue, unless the maintainer records another explicit queue decision.

## Test del minimo necessario

Criterio di accettazione della spec:
Produce one inspectable real JarvisOS frontend matching the eleven final canonical references without inventing missing backend state.

Questo lavoro serve a soddisfarlo? **sì**.

Il criterio è raggiungibile senza una dedicated frontend fusion slice? **no** — current master still exposes the superseded primary IA and only a subset of the final surfaces; implementing later backend slices first would prevent the maintainer from inspecting the final integrated product shell now requested.

Se sì: perché lo aggiungo comunque: N/A.
