# Area B — Frontend / operator product / UX

MAPPING_STATUS: IN_PROGRESS

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` (2026-09-15). Runtime/source evidence is primary; specs are only cross-checks.

## Application shell and routing — REAL
- **What/when:** Single React/Vite operator shell; extend the route registry rather than adding another router/shell.
- **Canonical files:** `frontend/src/App.tsx`, `frontend/src/app/routes.ts`, `useAppRouter.ts`, `AppLink.tsx`, `components/Layout.tsx`, `stages/registry.ts`.
- **Invocation/reuse:** `useAppRouter()` + `resolveRoute()` own paths/redirects; `App` composes route/stage and shell contributions.
- **I/O/persistence:** URL path/query plus transient workspace/stage/model/shell selection. No second frontend router/store found.
- **Preconditions:** browser DOM/Vite; `/legacy/dev-local-chat` is DEV-only.
- **Side effects/authority/risk:** history/navigation and transient selection only; route change clears route-sensitive selection. Project Basis query refs are allowlisted/bounded.
- **Tests/evidence:** production routes cover Design Process/BLUECAD, Memory Basis/Models/Literature, Development Timeline/Calendar/Brainstorm, Coding Repository/Runtime, Settings; `/` and `/home` redirect to Process; old design model/results/lineage/flowsheet redirect to Models.
- **Limitations:** explicit legacy diagnostic routes remain; unknown paths show migration/not-found instead of guessed content.
- **Do not reinvent:** extend `routes.ts` and existing stage/shell composition.
- **Search anchors:** `PRODUCTION_ROUTES`, `PRIMARY_NAV_ITEMS`, `PEER_NAV_ITEMS`, `ROADMAP_STAGE_ITEMS`, `resolveRoute`, `PRIMARY_STAGES`.

## Shell regions, focus and panel disclosure — REAL
- **What/when:** `Layout` owns rail, main, contextual navigator, Jarvis sidecar and analysis dock; stages contribute content instead of mounting competing chrome.
- **Canonical files:** `frontend/src/components/Layout.tsx`, `components/shell/{Rail,TopBar,ContextualNavigator,ContextualSidecar,AnalysisDock}.tsx`, `App.tsx`.
- **Invocation/reuse:** `ShellRegionContributions`; `requestShellRegionOpen`; BLUECAD opens navigator+sidecar by default, Process/knowledge routes sidecar, other final routes closed until requested.
- **I/O/persistence:** panel-open state is transient. Route entry updates document title and moves focus to `main`.
- **Side effects/authority/risk:** presentation only. Toggle close restores focus to trigger via `requestAnimationFrame`; controls expose `aria-expanded`/`aria-controls`; skip link targets `#app-main`.
- **Tests/evidence:** shell/fusion tests plus production route tests; behavior is directly wired in `Layout.tsx`.
- **Limitations:** no generic modal/dialog framework was found in `components/ui`; destructive confirmation is page-owned where needed.
- **Do not reinvent:** use shell contributions and existing panel request/focus mechanics.
- **Search anchors:** `shell-skip-link`, `mainRef`, `requestShellRegionOpen`, `shellRegionRequest`, `closeNavigator`, `closeSidecar`, `closeDock`.

## Jarvis sidecar/context interaction — REAL, bounded
- **What/when:** Contextual Jarvis presentation/actions derived from explicit operator route/selection state.
- **Canonical files:** `App.tsx`, `components/ai/useJarvisSidecar.tsx`, `JarvisKnowledgeActions.tsx`, `engineering/JarvisEngineeringActions.tsx`.
- **Invocation/reuse:** `App` derives stable knowledge refs only from explicit Project Basis/Models/Literature refs/selections; engineering routes may add BLUECAD selection/actions.
- **I/O/persistence:** route/workspace/explicit selection -> sidecar context/actions; UI state transient.
- **Authority/risk:** CONTEXT/PROPOSE UX only where backend permits; sidecar is not domain commit authority. Settings intentionally suppresses Jarvis.
- **Limitations:** browse/open alone is not durable context mutation; knowledge routes suppress engineering semantic context.
- **Do not reinvent:** reuse sidecar hook/action components and stable-ref derivation.
- **Search anchors:** `effectiveShellRegions`, `knowledgeStableRef`, `useJarvisSidecar`, `JarvisKnowledgeActions`.

## UI foundation / theme / shared primitives — REAL
- **What/when:** Semantic CSS/theme plus small shared primitive set.
- **Canonical files:** `frontend/src/theme.ts`, `styles/tokens.css`, `styles/global.css`, `main.tsx`; `components/ui/{Button,Field,InlineNotice,StatusBadge,Surface}.tsx`.
- **Invocation/reuse:** semantic tokens/classes; primitives wrap common button/form/notice/status/surface semantics. Theme supports `system|light|dark` plus accent presets/custom.
- **I/O/persistence:** visual preferences are browser-local; CSS variables/document theme are updated and subscribed across shell/settings.
- **Authority/risk:** local visual state only.
- **Tests/evidence:** `100*`, `100f*`, `100g*`, eyebrow-contrast tests run in production build.
- **Limitations:** intentionally small primitive library; no evidence of a generic dialog/disclosure/form-state framework. Do not infer one.
- **Do not reinvent:** use tokens/theme/primitives before page-local equivalents.
- **Search anchors:** `theme.ts`, `tokens.css`, `Button`, `Field`, `InlineNotice`, `StatusBadge`, `Surface`.

## Approved HTML references + interaction contract — REAL canonical design authority
- **What/when:** Byte-identified approved HTMLs define composition/visual target; interaction contract separately defines user-visible state transitions. Use both when changing production frontend.
- **Canonical files:** `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`, `FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md`, `FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md`, approved HTMLs under `memory-beta/`, `coding-beta/`, `process-beta/` and sibling design-reference directories; `OPERATOR_USABILITY_AND_FRONTEND_COMPLETION_CONTRACT_2026-09-15.md` is a later usability constraint.
- **Invocation/reuse:** compare implementation to manifest-selected HTML and interaction contract; accessibility improvements are allowed when semantics/composition remain preserved.
- **I/O/persistence:** docs/reference assets only.
- **Authority/risk:** visual matching alone is insufficient if interaction semantics differ.
- **Tests/evidence:** 100f/100g visual-conformance tests encode selected invariants; browser proofs provide runtime evidence for several final surfaces.
- **Limitations:** HTML is reference, not runtime; never infer wiring from a reference control.
- **Do not reinvent:** start from manifest/interaction contract rather than inventing another design source.
- **Search anchors:** `APPROVED_OPERATOR_UI_MANIFEST`, `FINAL_OPERATOR_INTERACTION_CONTRACT`, `FRONTEND_CONFORMANCE_CONTRACT`, `*-beta-approved-*.html`.

## Final operator fusion primitives — REAL
- **What/when:** Shared production presentation for workspace headers, Project Basis read/unavailable states, Settings, Project Knowledge and Search.
- **Canonical files:** `components/fusion/FinalOperatorReadSurface.tsx`, `FinalOperatorUnavailableSurface.tsx`, `FinalWorkspaceHeader.tsx`, `FinalSettingsSurface.tsx`, `ProjectKnowledgePanel.tsx`, `ProjectSearchPanel.tsx`.
- **Invocation/reuse:** mounted by `App.tsx`/domain pages; mutations use existing API wrappers.
- **I/O/persistence:** typed backend data + transient workspace/selection.
- **Risk:** unavailable states must remain explicit; some controls perform real backend writes.
- **Tests/evidence:** `100f-final-operator-frontend-fusion.mjs`, visual conformance, `100g-final-operator-ui-repair.mjs`, domain tests.
- **Do not reinvent:** reuse fusion surfaces.
- **Search anchors:** `FinalOperatorReadSurface`, `FinalOperatorUnavailableSurface`, `FinalWorkspaceHeader`.

## Memory — Project Basis / Project Knowledge / Search — REAL
- **What/when:** Requirements/parameters/assumptions/decisions read surface, lifecycle panel and project-local search.
- **Canonical files:** fusion read/knowledge/search components; `api/projectKnowledge.ts`, `api/knowledgeActions.ts`; App route wiring.
- **Invocation/reuse:** `/memory/project-basis`, optional bounded `recordKind`/`recordId`; search navigates to stable targets.
- **I/O/persistence:** backend-owned records/search; frontend workspace/ref transient.
- **Authority/risk:** lifecycle mutations are real backend writes; Jarvis knowledge actions remain bounded proposal/action UX.
- **Tests/evidence:** tests 112/115; browser plans 115/121.
- **Limitations:** stable Project Basis refs allow only requirement/parameter/assumption/decision.
- **Do not reinvent:** reuse projectKnowledge/knowledgeActions + fusion panels.
- **Search anchors:** `PROJECT_BASIS_RECORD_KINDS`, `requestedRecordRef`, `ProjectKnowledgePanel`, `ProjectSearchPanel`.

## Memory — Models — REAL
- **What/when:** Model dossier/version selection with explicit version propagated to Jarvis context.
- **Canonical files:** `pages/ModelDossier.tsx`, `api/modelDossier.ts`, `App.tsx`.
- **Invocation/reuse:** `/memory/models`, optional `modelVersionId`.
- **I/O/persistence:** backend dossier/version data; selected version transient.
- **Tests/evidence:** `113-model-dossier.mjs`, browser plan `113-memory-models.json` + fixture.
- **Limitations:** old Design model/results/lineage/flowsheet routes redirect here.
- **Do not reinvent:** reuse dossier/client.
- **Search anchors:** `ModelDossier`, `selectedModelVersionId`, `model_version:`.

## Memory — Literature — REAL with explicit unsupported states
- **What/when:** Source/entry UI with deep links and backing availability.
- **Canonical files:** `pages/LiteratureKnowledge.tsx`, `api/literature.ts`, App wiring.
- **Invocation/reuse:** `/memory/literature`, optional `sourceId`/`entryId`.
- **I/O/persistence:** backend-owned literature/source availability; explicit selection becomes stable Jarvis ref.
- **Tests/evidence:** `114-literature-knowledge.mjs`, browser plan/fixture 114.
- **Limitations:** unsupported/missing backing is surfaced rather than fabricated as readable evidence.
- **Do not reinvent:** reuse LiteratureKnowledge/client.
- **Search anchors:** `LiteratureKnowledge`, `requestedLiteratureSourceId`, `requestedLiteratureEntryId`.

## Development — Roadmap Timeline / Calendar — REAL
- **What/when:** Two views over one backend Development Roadmap domain.
- **Canonical files:** `pages/DevelopmentRoadmap.tsx`, `api/development.ts`, routes.
- **Invocation/reuse:** `/development/roadmap/timeline` or `/calendar`; same component `mode`.
- **I/O/persistence:** workspace-scoped backend state; UI mode/selection transient.
- **Authority/risk:** real bounded Development API operations; no frontend schedule store.
- **Tests/evidence:** test/browser proof 116.
- **Do not reinvent:** reuse DevelopmentRoadmap/development API.
- **Search anchors:** `DevelopmentRoadmap`, `mode="timeline"`, `mode="calendar"`.

## Development — Brainstorm — REAL
- **What/when:** Workspace Brainstorm surface for backend-owned Development records/actions.
- **Canonical files:** `pages/DevelopmentBrainstorm.tsx`, `api/development.ts`.
- **Invocation/reuse:** `/development/brainstorm`.
- **I/O/persistence:** backend records; transient workspace/UI state.
- **Tests/evidence:** test/browser proof 117.
- **Do not reinvent:** reuse Brainstorm/development client.
- **Search anchors:** `DevelopmentBrainstorm`, `development.ts`.

## Coding — Repository / Runtime / Pipeline projection — REAL, bounded
- **What/when:** Shared workbench renders repository/runtime truth and accepted pipeline/action projections without giving browser arbitrary GitHub/shell authority.
- **Canonical files:** `pages/CodingWorkbench.tsx`, `api/coding.ts`, App wiring, `operatorSemantics.ts`.
- **Invocation/reuse:** `/coding/repository` and `/coding/runtime`; same component with mode.
- **I/O/persistence:** backend Coding repository/runtime/pipeline projections/actions; frontend workspace/ref state.
- **Authority/risk:** real bounded backend actions may be proposed; frontend has no arbitrary shell, local filesystem or direct GitHub-token authority.
- **Tests/evidence:** `140-coding-frontend-integration.mjs`, `143-operator-semantic-ux.mjs`, browser plan 140.
- **Limitations:** no separate `/coding/pipeline` primary route found; pipeline is presented through accepted Coding workbench semantics.
- **Do not reinvent:** reuse CodingWorkbench/coding client/operator semantic helpers.
- **Search anchors:** `CodingWorkbench`, `RepositoryTruthResult`, `RuntimeTruth`, `pullRequestEvidenceSummary`, `runtimeDeltaSummary`.

## Settings — Appearance — REAL local
- **What/when:** Appearance and accent operator controls.
- **Canonical files:** `pages/Settings.tsx`, `theme.ts`, final/settings CSS.
- **Invocation/reuse:** Settings appearance route/surface; `read/write/applyAppearancePreference`, accent equivalents.
- **I/O/persistence:** browser-local visual preference; no server write.
- **Side effects/risk:** document CSS/theme only.
- **Tests/evidence:** visual tests and Settings contract coverage.
- **Limitations:** local preference is intentionally separate from canonical server AI settings.
- **Do not reinvent:** reuse theme API.
- **Search anchors:** `APPEARANCE_OPTIONS`, `ACCENT_OPTIONS`, `setVisualAppearance`, `setVisualAccent`.

## Settings — AI/provider/credential controls — REAL, security-sensitive and fail-safe
- **What/when:** Canonical AI budgets/provider permissions/status plus bounded Scaleway credential replace/delete.
- **Canonical files:** `pages/Settings.tsx`, `api/settings.ts`, `operatorSemantics.ts`.
- **Invocation/reuse:** loads AI settings/status, provider settings, secret status and system info concurrently; writes through `saveAISetting`, `replaceScalewayCredential`, `removeScalewayCredential`.
- **I/O/persistence:** server-owned settings/secret metadata; raw submitted credential is not projected back into UI.
- **Preconditions:** backend/settings endpoints and provider capability projection.
- **Side effects/authority/risk:** REAL server mutations; high sensitivity. After every mutation UI rereads canonical state. Failed reread sets `State uncertain` and blocks further mutation until reload. Credential delete is explicitly confirmed and focus-managed.
- **Tests/evidence:** `124-provider-settings.mjs`, browser proof `124-settings-ai.json`, `143-operator-semantic-ux.mjs`.
- **Limitations:** UI enables credential operations only when backend capability flags permit; provider availability labels are projections, not proof of successful inference.
- **Do not reinvent:** use settings API and canonical reread/uncertain-state pattern.
- **Search anchors:** `loadCanonical`, `refreshAfterMutation`, `uncertain`, `credential_capabilities`, `credentialMeaning`, `providerLocation`, `savedPaidAiSummary`.

## Operator semantic helpers — REAL
- **What/when:** Central wording/projection helpers prevent misleading status/credential/runtime/PR semantics on dense operator surfaces.
- **Canonical files:** `frontend/src/operatorSemantics.ts`, consumers `Settings.tsx`, `CodingWorkbench.tsx`, `ModelDossier.tsx`.
- **Invocation/reuse:** import semantic summary helpers instead of reconstructing labels ad hoc.
- **I/O/persistence:** pure projection; no persistence.
- **Tests/evidence:** `frontend/tests/143-operator-semantic-ux.mjs`, plus Settings 124 coverage.
- **Limitations:** semantic helpers do not make underlying capability real; they only render returned truth.
- **Do not reinvent:** reuse helpers for equivalent evidence states.
- **Search anchors:** `credentialMeaning`, `providerLocation`, `savedPaidAiSummary`, `pullRequestEvidenceSummary`, `runtimeDeltaSummary`.

## Design — Process operator surface — PARTIAL / deliberately unavailable authoring
- **What/when:** Production Process workspace presents accepted process/basis context and handoff state; unsupported authoring remains visibly unavailable.
- **Canonical files:** `stages/ProcessStage.tsx`, `App.tsx`, process styles; Project Knowledge handoff helpers.
- **Invocation/reuse:** `/design/process`; stage registry mounts it.
- **I/O/persistence:** reads project-knowledge handoff/accepted server data where wired; page state transient.
- **Authority/risk:** no server-owned topology/evaluator authoring authority exists at this frontend boundary; controls requiring it must remain disabled.
- **Tests/evidence:** `058d-process-workspace.mjs`, 100/100f/100g visual tests.
- **Limitations/fake paths:** source explicitly labels future Process authoring controls unavailable until server-owned topology/evaluator authority is integrated. Do not mistake approved visual controls for working authoring.
- **Do not reinvent:** extend ProcessStage only when matching backend authority exists.
- **Search anchors:** `ProcessStage`, `unavailableReason`, `readProjectKnowledgeHandoff`.

## Design — BLUECAD operator boundary — REAL inspection/selection + PLACEHOLDER authoring toolbar
- **What/when:** Real server-owned geometry workbench/viewer and selection context; visual authoring toolbar is intentionally inert.
- **Canonical files:** `stages/ModelStage.tsx`, `components/bluecad/BluecadWorkbench.tsx`, `components/BluecadGlbViewer.tsx`, engineering Properties/Jarvis action components.
- **Invocation/reuse:** `/design/bluecad`; `BluecadWorkbench` contributes selection and shell regions.
- **I/O/persistence:** existing geometry/evidence -> viewer/selection; selected part feeds Properties/Jarvis context.
- **Authority/risk:** inspect/select only at this boundary. Every toolbar item Select/Orbit/Pan/Measure/Sketch/Circle/Extrude/Pattern/Fit view/Zoom/Undo/Redo/Section/Inspect/Export in `ModelStage` is `disabled` with an unavailable reason; do not wire it to invented client-side CAD authority.
- **Tests/evidence:** visual/fusion tests; engineering/BLUECAD tests elsewhere; browser boundary covered through accepted frontend proofs where configured.
- **Limitations:** authoring toolbar is PLACEHOLDER by design even though workbench inspection is real.
- **Do not reinvent:** reuse BluecadWorkbench/viewer/selection and await/consume server authority for authoring.
- **Search anchors:** `bluecadPresentationTools`, `futureReason`, `BluecadWorkbench`, `BluecadGlbViewer`.

## Frontend API clients / types — REAL, mixed handwritten + generated
- **What/when:** Typed React-to-backend boundary.
- **Canonical files:** `api/client.ts`; domain wrappers `coding.ts`, `development.ts`, `knowledgeActions.ts`, `literature.ts`, `memory.ts`, `modelDossier.ts`, `parameterLifecycle.ts`, `projectKnowledge.ts`, `settings.ts`; `api/generated/`.
- **Invocation/reuse:** search/import domain wrapper before adding fetch logic in components.
- **I/O/persistence:** JSON HTTP; backend remains persistence owner except visual prefs.
- **Authority/risk:** wrappers can perform real mutations; types do not grant authority.
- **Limitations:** generated and handwritten boundaries coexist; regeneration/check path still requires final inventory before COMPLETE.
- **Do not reinvent:** search `frontend/src/api` first.
- **Search anchors:** `api/client.ts`, `api/generated`, domain API filenames.

## Browser-proof / visual / accessibility evidence — REAL verification primitives
- **What/when:** Deterministic source-contract tests plus declarative trusted Chromium proof plans for operator behavior.
- **Canonical files:** `frontend/tests/*`; `.github/browser-proof/{run.mjs,plan-lib.mjs,request-policy.mjs,fixture-registry.mjs,plans/,fixtures/}`; workflow `browser-proof-contract.yml`.
- **Invocation/reuse:** frontend build executes contract tests; browser proof uses declarative plans/fixtures for 113/114/115/116/117/121/124/140. Add a plan rather than spec-hard-coded browser controller logic.
- **I/O/persistence:** browser actions/assertions/screenshots/evidence artifacts; fixture state is bounded test setup.
- **Authority/risk:** verification only; browser proof is separate from Node/source-contract success.
- **Tests/evidence:** self-tests `test-plan-lib.mjs`, `test-request-policy.mjs`, `test-mutation-window.mjs`, contract validators.
- **Limitations:** not every frontend surface has a trusted-browser plan; source tests are not equivalent to rendered proof.
- **Do not reinvent:** reuse declarative browser-proof executor and frontend test chain.
- **Search anchors:** `.github/browser-proof/plans`, `validate-plan.mjs`, `run.mjs`, `frontend/tests`.

## Frontend build / dev — REAL
- **What/when:** Vite dev/preview and production gate.
- **Canonical files:** `frontend/package.json`, Vite config, tests.
- **Invocation/reuse:** `npm run dev` and `npm run preview` bind loopback; `npm run build` runs frontend contracts then `tsc` + Vite build.
- **Preconditions:** Node/npm; React 18.3.1, Vite 6.0.5, TypeScript 5.7.2, Three 0.171.0, Phosphor icons in current lock/package evidence.
- **Side effects/risk:** build output only; no product authority.
- **Do not reinvent:** extend existing build/test scripts.
- **Search anchors:** `frontend/package.json`, `vite.config.*`.

## Status matrix
| Surface | Status | Runtime evidence / caveat |
|---|---|---|
| App shell/routes | REAL | Explicit production registry, redirects, not-found |
| Shell panel/focus/a11y basics | REAL | skip link, focus-on-route, aria panel toggles, focus restore |
| Theme/tokens/primitives | REAL | central theme/tokens; small shared UI set |
| Approved design references | REAL authority docs | references are not runtime wiring |
| Project Basis/Knowledge/Search | REAL | routed clients/components + tests/proofs |
| Models | REAL | dossier + explicit version selection |
| Literature | REAL | source/entry + unavailable backing handling |
| Roadmap Timeline/Calendar | REAL | one backend domain, two modes |
| Brainstorm | REAL | routed real component/API |
| Coding Repository/Runtime | REAL | bounded workbench/API |
| Coding pipeline | PARTIAL | projected in workbench; no separate primary pipeline route |
| Settings appearance | REAL | local-only |
| Settings AI/provider/credential | REAL | server-owned, reread/fail-safe mutation UX |
| Process | PARTIAL | read/handoff surface; authoring unavailable |
| BLUECAD inspect/select | REAL | workbench/viewer + explicit selection |
| BLUECAD authoring toolbar | PLACEHOLDER | every presentation tool disabled |
| Legacy Domain/AI Draft/System Status | PARTIAL / LEGACY | diagnostics, not primary product navigation |
| Dev Local Chat | DEFERRED / DEV-ONLY | lazy-imported only in DEV |

## Remaining coverage
- Inspect Runs, Engineering Data, Review and AI Threads operator pages/components and classify their frontend-boundary status without duplicating Area C/A internals.
- Enumerate remaining `api/`, `components/`, `pages/`, `stages/`, `styles/`, `tests/` files for unmounted clients, fake controls or overlooked major surfaces.
- Inspect `api/generated/` provenance and exact regeneration/check commands.
- Check responsive/scroll CSS and remaining disclosure/form helpers for notable reusable mechanics or accessibility gaps.
- Rebase evidence baseline if master moves materially before final COMPLETE; then perform final fake/inert-control search and only then mark COMPLETE.
