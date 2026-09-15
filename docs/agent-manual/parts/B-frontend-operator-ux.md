# Area B — Frontend / operator product / UX

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` (2026-09-15). Runtime/source evidence is primary; specs are only cross-checks.

## Application shell and routing — REAL
- **What/when:** Single React/Vite operator shell. Use route registry/navigation instead of introducing another router or parallel shell.
- **Canonical files:** `frontend/src/App.tsx`, `frontend/src/app/routes.ts`, `frontend/src/app/useAppRouter.ts`, `frontend/src/app/AppLink.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/stages/registry.ts`.
- **Invocation/reuse:** `useAppRouter()` resolves `window.location`; `resolveRoute()` owns canonical paths/redirects; `App` selects route/stage and composes shell contributions.
- **I/O/persistence:** URL path/query; transient `workspaceId`, stage selection, selected model version, shell-region state. No evidence of a second frontend router/store.
- **Preconditions:** browser DOM; Vite env. `/legacy/dev-local-chat` is DEV-only.
- **Side effects/authority/risk:** navigation/history and transient selection only; route changes clear selection/shell contributions/model selection. Query refs are bounded to 200 chars and Project Basis kinds are allowlisted.
- **Evidence:** production routes include Design Process/BLUECAD, Memory Project Basis/Models/Literature, Development Roadmap Timeline/Calendar/Brainstorm, Coding Repository/Runtime, Settings Appearance/AI/System plus Runs/Engineering Data/Review/AI Threads and explicit legacy diagnostics. `/`, `/home` -> Process; old design model/results/lineage/flowsheet -> Models.
- **Limitations/status:** legacy pages remain reachable as diagnostics; unknown paths render a migration-pending/not-found surface rather than guessed content.
- **Do not reinvent:** extend `routes.ts` + existing stage/shell composition.
- **Search anchors:** `PRODUCTION_ROUTES`, `PRIMARY_NAV_ITEMS`, `PEER_NAV_ITEMS`, `ROADMAP_STAGE_ITEMS`, `resolveRoute`, `PRIMARY_STAGES`.

## Shell regions, Jarvis sidecar, Properties and Analytics dock — REAL
- **What/when:** `App` is the composition owner for route content plus contextual Jarvis sidecar, engineering Properties and Analytics dock.
- **Canonical files:** `frontend/src/App.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/components/ai/useJarvisSidecar.tsx`, `frontend/src/components/ai/JarvisKnowledgeActions.tsx`, `frontend/src/components/engineering/EngineeringProperties.tsx`, `frontend/src/components/engineering/JarvisEngineeringActions.tsx`, `frontend/src/components/analytics/AnalyticsDockContent.tsx`.
- **Invocation/reuse:** stages contribute `ShellRegionContributions`; `App` overlays Jarvis sidecar except Settings; dock is mounted on Runs/Engineering Data/Process. Stable knowledge refs are derived only from explicit Project Basis/Models/Literature selections/query refs.
- **I/O/persistence:** workspace/selection/route -> sidecar context and actions; UI state is transient. Knowledge routes suppress engineering semantic context; non-knowledge routes can include BLUECAD part selection + engineering actions.
- **Authority/risk:** frontend proposes/contextualizes; do not treat sidecar display as domain commit authority.
- **Limitations:** Settings deliberately has no Jarvis sidecar. Context is route/explicit-selection based; browse/open alone should not be treated as durable context mutation.
- **Do not reinvent:** contribute through shell regions and existing Jarvis action components.
- **Search anchors:** `effectiveShellRegions`, `knowledgeStableRef`, `useJarvisSidecar`, `requestShellRegionOpen`.

## UI foundation / theme / visual identity — REAL
- **What/when:** Shared semantic theme and CSS foundation for production UI.
- **Canonical files:** `frontend/src/theme.ts`, `frontend/src/styles/tokens.css`, `frontend/src/styles/global.css`, `frontend/src/main.tsx`; visual contract tests under `frontend/tests/100*` and `100f*`/`100g*`.
- **Invocation/reuse:** use semantic CSS tokens/classes and theme helpers rather than page-local palette systems. Theme owns local `system | light | dark` appearance behavior; visual identity tests are part of every production build.
- **I/O/persistence:** browser-local visual preferences; CSS variables applied to document/theme state.
- **Side effects/risk:** visual/local only; no backend authority.
- **Evidence:** `npm run build` runs visual identity, final-operator fusion/repair and eyebrow-contrast tests before `tsc` + Vite build.
- **Do not reinvent:** reuse tokens/theme and fusion surfaces.
- **Search anchors:** `theme.ts`, `tokens.css`, `global.css`, `test:100`, `test:100f`, `test:100g`.

## Final operator fusion primitives — REAL
- **What/when:** Shared production presentation for workspace headers, Project Basis read surface, unavailable states, Settings shell, Project Knowledge and Search.
- **Canonical files:** `frontend/src/components/fusion/FinalOperatorReadSurface.tsx`, `FinalOperatorUnavailableSurface.tsx`, `FinalWorkspaceHeader.tsx`, `FinalSettingsSurface.tsx`, `ProjectKnowledgePanel.tsx`, `ProjectSearchPanel.tsx`.
- **Invocation/reuse:** `App.tsx` mounts these directly for Memory/Development/Coding/Settings routes.
- **I/O/persistence:** typed API data + workspace selection -> cards/forms/disclosures/search results; mutations flow through existing API wrappers.
- **Risk:** some components expose real mutations; unavailable surfaces must remain explicit rather than fake enabled controls.
- **Evidence:** `frontend/tests/100f-final-operator-frontend-fusion.mjs`, `100f-visual-conformance.mjs`, `100g-final-operator-ui-repair.mjs`, plus domain tests 112/115.
- **Do not reinvent:** reuse fusion primitives for production operator semantics.
- **Search anchors:** `FinalOperatorReadSurface`, `FinalOperatorUnavailableSurface`, `FinalWorkspaceHeader`, `ProjectKnowledgePanel`, `ProjectSearchPanel`.

## Memory — Project Basis / Project Knowledge / Search — REAL
- **What/when:** Project Basis route provides requirements/parameters/assumptions/decisions read/operator surface, Project Knowledge lifecycle panel and project-local search.
- **Canonical files:** `frontend/src/components/fusion/FinalOperatorReadSurface.tsx`, `ProjectKnowledgePanel.tsx`, `ProjectSearchPanel.tsx`; `frontend/src/api/projectKnowledge.ts`, `frontend/src/api/knowledgeActions.ts`; App route wiring.
- **Invocation/reuse:** `/memory/project-basis`; optional bounded `recordKind` + `recordId`; Search receives current workspace and navigates to stable targets.
- **I/O/persistence:** backend-owned records/search results; frontend keeps workspace transient and invokes typed API wrappers for real lifecycle operations.
- **Authority/risk:** record mutations are real backend writes; Jarvis knowledge actions are bounded action/proposal UX, not a parallel store.
- **Evidence:** `frontend/tests/112-project-knowledge-lifecycle.mjs`, `115-project-search.mjs`, browser-proof plans `115-project-search.json`, `121-knowledge-actions.json`.
- **Limitations:** only requirement/parameter/assumption/decision query refs are accepted as Project Basis stable refs.
- **Do not reinvent:** use projectKnowledge/knowledgeActions clients + fusion panels.
- **Search anchors:** `PROJECT_BASIS_RECORD_KINDS`, `requestedRecordRef`, `ProjectKnowledgePanel`, `ProjectSearchPanel`.

## Memory — Models — REAL
- **What/when:** Model dossier/version selection UI with explicit selected version propagated to Jarvis stable context.
- **Canonical files:** `frontend/src/pages/ModelDossier.tsx`, `frontend/src/api/modelDossier.ts`, `App.tsx`.
- **Invocation/reuse:** `/memory/models`; optional `modelVersionId`; selection callback updates `selectedModelVersionId`.
- **I/O/persistence:** backend dossier/version data; frontend selection transient.
- **Evidence:** `frontend/tests/113-model-dossier.mjs`; browser proof `113-memory-models.json` + fixture `model_version_selection.py`.
- **Limitations:** selection/context is explicit; old Design model/results/lineage/flowsheet URLs redirect here rather than preserving old separate surfaces.
- **Do not reinvent:** reuse ModelDossier + modelDossier API.
- **Search anchors:** `ModelDossier`, `selectedModelVersionId`, `model_version:`.

## Memory — Literature — REAL with explicit unsupported states
- **What/when:** Literature source/entry operator UI with explicit source/entry deep links and backing availability handling.
- **Canonical files:** `frontend/src/pages/LiteratureKnowledge.tsx`, `frontend/src/api/literature.ts`, App route wiring.
- **Invocation/reuse:** `/memory/literature`; optional `sourceId`/`entryId`; selected entry/source becomes a stable Jarvis ref.
- **I/O/persistence:** backend-owned literature records and source availability.
- **Evidence:** `frontend/tests/114-literature-knowledge.mjs`; browser proof `114-literature.json` + `fixtures/literature_knowledge.py`.
- **Limitations:** unsupported/missing backing is surfaced rather than fabricated as readable evidence.
- **Do not reinvent:** use LiteratureKnowledge/literature API.
- **Search anchors:** `LiteratureKnowledge`, `requestedLiteratureSourceId`, `requestedLiteratureEntryId`.

## Development — Roadmap Timeline/Calendar — REAL
- **What/when:** Two views over the same Development Roadmap domain.
- **Canonical files:** `frontend/src/pages/DevelopmentRoadmap.tsx`, `frontend/src/api/development.ts`, `frontend/src/app/routes.ts`.
- **Invocation/reuse:** `/development/roadmap/timeline` or `/development/roadmap/calendar`; same component with `mode`.
- **I/O/persistence:** workspace-scoped backend roadmap/calendar state; frontend mode/selection transient.
- **Authority/risk:** operator controls call backend Development APIs; do not fork a separate frontend schedule store.
- **Evidence:** `frontend/tests/116-roadmap-calendar.mjs`; browser proof `116-roadmap-calendar.json`.
- **Do not reinvent:** reuse DevelopmentRoadmap/development API and `ROADMAP_STAGE_ITEMS`.
- **Search anchors:** `DevelopmentRoadmap`, `mode="timeline"`, `mode="calendar"`.

## Development — Brainstorm — REAL
- **What/when:** Workspace Brainstorm surface for real Development records/actions.
- **Canonical files:** `frontend/src/pages/DevelopmentBrainstorm.tsx`, `frontend/src/api/development.ts`.
- **Invocation/reuse:** `/development/brainstorm`.
- **I/O/persistence:** backend-owned brainstorm records; workspace selection transient.
- **Evidence:** `frontend/tests/117-brainstorm.mjs`; browser proof `117-brainstorm.json`.
- **Do not reinvent:** reuse DevelopmentBrainstorm and Development API types/actions.
- **Search anchors:** `DevelopmentBrainstorm`, `development.ts`.

## Coding — Repository / Runtime — REAL, bounded operator surface
- **What/when:** Shared Coding workbench renders repository and runtime modes.
- **Canonical files:** `frontend/src/pages/CodingWorkbench.tsx`, `frontend/src/api/coding.ts`, App route wiring.
- **Invocation/reuse:** `/coding/repository` and `/coding/runtime`; same component with mode.
- **I/O/persistence:** backend Coding repository/runtime/pipeline projections/actions; frontend workspace context.
- **Authority/risk:** controls can represent real bounded backend actions; never infer arbitrary shell/code execution from UI presence.
- **Evidence:** `frontend/tests/140-coding-frontend-integration.mjs`; browser proof `140-coding.json`.
- **Do not reinvent:** use CodingWorkbench + coding API wrappers.
- **Search anchors:** `CodingWorkbench`, `mode="repository"`, `mode="runtime"`, `coding.ts`.

## Frontend API clients / types — REAL, mixed handwritten + generated
- **What/when:** Typed boundary from React surfaces to backend APIs.
- **Canonical files:** `frontend/src/api/client.ts` (large shared client), domain wrappers `coding.ts`, `development.ts`, `knowledgeActions.ts`, `literature.ts`, `memory.ts`, `modelDossier.ts`, `parameterLifecycle.ts`, `projectKnowledge.ts`, plus `frontend/src/api/generated/`.
- **Invocation/reuse:** import existing domain wrapper before adding fetch logic to components. Generated types live under `api/generated` and should not be shadow-copied.
- **I/O/persistence:** JSON HTTP requests/responses; persistence remains backend-owned except local visual prefs.
- **Risk:** API wrappers may mutate real backend state; preserve backend authority and typed contracts.
- **Do not reinvent:** search `frontend/src/api` first for every backend capability.
- **Search anchors:** `api/client.ts`, `api/generated`, domain API filenames above.

## Frontend build / production verification — REAL
- **What/when:** Vite development/preview and a build gate that executes frontend contract tests before TypeScript/build.
- **Canonical files:** `frontend/package.json`, `frontend/tests/*`, `vite.config.*`, `.github/browser-proof/*` for trusted browser evidence.
- **Invocation/reuse:** `npm run dev` binds `127.0.0.1`; `npm run build` runs tests 058d, 100, 100f/g, 112–117, 124, 140, 143, contrast, then `tsc && vite build`; `npm run preview` binds loopback.
- **Dependencies:** React 18.3.1, Vite 6.0.5, TypeScript 5.7.2, Three 0.171.0, Phosphor icons.
- **Evidence:** build script itself is the deterministic frontend gate; browser-proof plans exist for 113/114/115/116/117/121/124/140.
- **Limitations:** Node contract tests are not equivalent to trusted Chromium proof; browser proof is separate evidence.
- **Do not reinvent:** add focused contract coverage to the existing build chain and declarative browser-proof stack.
- **Search anchors:** `frontend/package.json`, `.github/browser-proof/plans`, `.github/browser-proof/run.mjs`.

## Status matrix (inspected so far)
| Surface | Status | Runtime evidence / caveat |
|---|---|---|
| App shell/routes | REAL | Explicit production registry + canonical redirects + not-found |
| Theme/tokens | REAL | Central theme/tokens; build-gated visual tests |
| Project Basis/Knowledge/Search | REAL | Routed components + typed clients + tests/proofs |
| Models | REAL | Routed dossier + explicit version selection + proof |
| Literature | REAL | Routed source/entry UI + unavailable handling + proof |
| Roadmap Timeline/Calendar | REAL | Same real component/domain API in two modes |
| Brainstorm | REAL | Routed real component/API + proof |
| Coding Repository/Runtime | REAL | Routed shared workbench + API + proof |
| Legacy Domain/AI Draft/System Status | PARTIAL / LEGACY | Explicit diagnostic routes, not primary product navigation |
| Dev Local Chat | DEFERRED / DEV-ONLY | Lazy-imported only under `import.meta.env.DEV` |

## Remaining coverage
- Inspect `Layout.tsx` and all shell/shared UI helper directories in detail: disclosure/dialog/form/scroll/focus/accessibility behavior and fake/inert controls.
- Inspect Settings Appearance/AI/System implementations and provider projections; classify any placeholder/inert controls.
- Inspect `operatorSemantics.ts` and 143 tests for semantic labels/disabled-state guarantees.
- Inspect Design Process stage and BLUECAD frontend boundary (viewer, selection, Properties, candidate actions) without duplicating Area C internals.
- Inspect Runs/Engineering Data/Review/AI Threads and decide which operator-boundary capabilities belong in Area B.
- Inspect approved HTML/design reference assets and canonical conformance scripts.
- Enumerate remaining `api/`, `components/`, `pages/`, `stages/`, `styles/`, `tests/` files and check for unmounted backend clients, fake controls or major uninspected frontend subsystems.
- Inspect generated API/codegen source + regeneration/check commands.
