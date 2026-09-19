# Area B — Frontend / operator product / UX

MAPPING_STATUS: COMPLETE

Evidence baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb` (2026-09-15). Runtime/source evidence is primary; specs/design prose are cross-checks only.

## Application shell and routing — REAL
- **What/when:** Single React/Vite operator shell. Extend the existing registry/router rather than adding another shell or route store.
- **Canonical files:** `frontend/src/App.tsx`, `frontend/src/app/{routes.ts,useAppRouter.ts,AppLink.tsx}`, `components/Layout.tsx`, `stages/registry.ts`.
- **Invocation/reuse:** `useAppRouter()` + `resolveRoute()`; `App` composes route/stage and shell contributions.
- **I/O/persistence:** URL path/query + transient workspace/stage/selection/panel state; no second frontend router/store found.
- **Preconditions:** browser DOM/Vite; `/legacy/dev-local-chat` is DEV-only.
- **Side effects/authority/risk:** navigation/transient selection only; route change clears route-sensitive selection; Project Basis query refs are bounded/allowlisted.
- **Tests/evidence:** production route/fusion tests; `/` and `/home` redirect to Process; old design model/results/lineage/flowsheet routes redirect to Models.
- **Limitations:** legacy diagnostics remain; unknown routes show migration/not-found rather than guessed content.
- **Do not reinvent:** extend `routes.ts`, `PRIMARY_STAGES`, and existing shell composition.
- **Search anchors:** `PRODUCTION_ROUTES`, `PRIMARY_NAV_ITEMS`, `PEER_NAV_ITEMS`, `ROADMAP_STAGE_ITEMS`, `resolveRoute`, `PRIMARY_STAGES`.

## Shell regions, layout, focus, disclosure and responsive containment — REAL
- **What/when:** `Layout` owns rail/main/contextual navigator/Jarvis sidecar/analysis dock; stages contribute regions instead of mounting competing chrome. Responsive CSS collapses shell below 60rem and gives technical/table viewports local containment.
- **Canonical files:** `components/Layout.tsx`, `components/shell/*`, `styles/{global.css,responsive.css,foundation.css,final-fusion*.css}`.
- **Invocation/reuse:** `ShellRegionContributions`, `requestShellRegionOpen`; shell toggles expose `aria-expanded`/`aria-controls`; route entry focuses `main`; close restores trigger focus.
- **I/O/persistence:** transient panel/open/focus state only.
- **Side effects/authority/risk:** presentation only; `min-width:0`, `overflow-wrap:anywhere`, one-column responsive shell prevent document-width blowout.
- **Tests/evidence:** 100/100f/100g contracts and source wiring; skip link targets `#app-main`.
- **Limitations:** no generic modal/dialog/form-state framework found; native `<details>` and page-owned confirmation/focus logic are used where needed.
- **Do not reinvent:** use shell contributions, existing focus mechanics, native disclosure and responsive containment.
- **Search anchors:** `shell-skip-link`, `mainRef`, `requestShellRegionOpen`, `closeNavigator`, `closeSidecar`, `closeDock`, `@media (max-width: 60rem)`.

## UI foundation / theme / shared primitives — REAL
- **What/when:** Semantic tokens/theme plus intentionally small shared primitive set.
- **Canonical files:** `theme.ts`, `styles/{tokens.css,global.css}`, `main.tsx`, `components/ui/{Button,Field,InlineNotice,StatusBadge,Surface}.tsx`.
- **Invocation/reuse:** semantic CSS variables/classes and primitives; theme supports `system|light|dark` plus accent presets/custom.
- **I/O/persistence:** appearance/accent are browser-local and applied to document CSS/theme.
- **Authority/risk:** visual state only.
- **Tests/evidence:** 100*, 100f*, 100g*, eyebrow-contrast tests run in production build.
- **Limitations:** small library; do not infer a generic dialog/disclosure/form framework.
- **Do not reinvent:** reuse tokens/theme/primitives before page-local equivalents.
- **Search anchors:** `theme.ts`, `tokens.css`, `Button`, `Field`, `InlineNotice`, `StatusBadge`, `Surface`.

## Approved HTML references + interaction contract — REAL design authority, not runtime
- **What/when:** Byte-identified approved HTMLs define composition/visual target; interaction contract defines user-visible state transitions.
- **Canonical files:** `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md`, `FINAL_OPERATOR_INTERACTION_CONTRACT_2026-08-27.md`, `FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md`, approved `*-beta-approved-*.html`; later usability contract is an additional constraint.
- **Invocation/reuse:** compare implementation to manifest-selected HTML and interaction contract; preserve semantics while allowing accessibility fixes.
- **I/O/persistence:** docs/assets only.
- **Authority/risk:** visual match alone is not evidence that a control is wired.
- **Tests/evidence:** 100f/100g encode selected invariants; trusted browser plans provide runtime evidence for selected surfaces.
- **Limitations:** reference controls may be intentionally unavailable in product.
- **Do not reinvent:** start from manifest + interaction contract, never from screenshot inference alone.
- **Search anchors:** `APPROVED_OPERATOR_UI_MANIFEST`, `FINAL_OPERATOR_INTERACTION_CONTRACT`, `FRONTEND_CONFORMANCE_CONTRACT`.

## Final operator fusion primitives — REAL
- **What/when:** Shared production presentation for workspace headers, Project Basis read/unavailable states, Settings, Project Knowledge and Search.
- **Canonical files:** `components/fusion/{FinalOperatorReadSurface,FinalOperatorUnavailableSurface,FinalWorkspaceHeader,FinalSettingsSurface,ProjectKnowledgePanel,ProjectSearchPanel}.tsx`.
- **Invocation/reuse:** mounted by `App`/domain pages; mutations call domain API wrappers.
- **I/O/persistence:** typed backend data + transient selection.
- **Authority/risk:** some controls perform real backend writes; unavailable state must remain explicit.
- **Tests/evidence:** 100f/100g + domain contracts.
- **Do not reinvent:** reuse fusion surfaces.
- **Search anchors:** `FinalOperatorReadSurface`, `FinalOperatorUnavailableSurface`, `FinalWorkspaceHeader`.

## Jarvis sidecar / explicit context interaction — REAL, bounded
- **What/when:** Contextual Jarvis presentation/actions derived from explicit route/selection state.
- **Canonical files:** `App.tsx`, `components/ai/useJarvisSidecar.tsx`, `JarvisKnowledgeActions.tsx`, `engineering/JarvisEngineeringActions.tsx`.
- **Invocation/reuse:** stable refs derive from explicit Project Basis/Models/Literature selections; engineering routes may add BLUECAD selection/actions.
- **I/O/persistence:** route/workspace/selection -> transient sidecar context/actions.
- **Authority/risk:** CONTEXT/PROPOSE UX only where backend permits; sidecar is not domain COMMIT authority; Settings suppresses Jarvis.
- **Limitations:** browse/open alone is not durable context mutation; knowledge routes suppress engineering semantic context.
- **Do not reinvent:** reuse sidecar hook/action components and stable-ref derivation.
- **Search anchors:** `effectiveShellRegions`, `knowledgeStableRef`, `useJarvisSidecar`, `JarvisKnowledgeActions`.

## Memory — Project Basis / Project Knowledge / Search — REAL
- **What/when:** Requirements/parameters/assumptions/decisions read surface, lifecycle panel and project-local search.
- **Canonical files:** fusion read/knowledge/search components; `api/{projectKnowledge,knowledgeActions}.ts`; App wiring.
- **Invocation/reuse:** `/memory/project-basis`, optional bounded `recordKind`/`recordId`; search navigates stable targets.
- **I/O/persistence:** backend-owned records/search; workspace/ref transient.
- **Authority/risk:** lifecycle mutations are real backend writes; Jarvis actions remain bounded proposal/action UX.
- **Tests/evidence:** tests 112/115; browser plans 115/121.
- **Limitations:** stable Project Basis refs allow only requirement/parameter/assumption/decision.
- **Do not reinvent:** reuse Project Knowledge/Search panels and clients.
- **Search anchors:** `PROJECT_BASIS_RECORD_KINDS`, `requestedRecordRef`, `ProjectKnowledgePanel`, `ProjectSearchPanel`.

## Memory — Models — REAL
- **What/when:** Model dossier/version selection with explicit selected version propagated to Jarvis context.
- **Canonical files:** `pages/ModelDossier.tsx`, `api/modelDossier.ts`, `App.tsx`.
- **Invocation/reuse:** `/memory/models`, optional `modelVersionId`.
- **I/O/persistence:** backend dossier/version data; selection transient.
- **Tests/evidence:** `113-model-dossier.mjs`, browser plan/fixture 113.
- **Limitations:** old Design model/results/lineage/flowsheet routes redirect here.
- **Do not reinvent:** reuse dossier/client.
- **Search anchors:** `ModelDossier`, `selectedModelVersionId`, `model_version:`.

## Memory — Literature — REAL with explicit unsupported states
- **What/when:** Source/entry UI with deep links and backing availability.
- **Canonical files:** `pages/LiteratureKnowledge.tsx`, `api/literature.ts`, App wiring.
- **Invocation/reuse:** `/memory/literature`, optional `sourceId`/`entryId`.
- **I/O/persistence:** backend-owned literature/source availability; explicit selection becomes stable Jarvis ref.
- **Tests/evidence:** `114-literature-knowledge.mjs`, browser plan/fixture 114.
- **Limitations:** unsupported/missing backing is surfaced, never fabricated as readable evidence.
- **Do not reinvent:** reuse LiteratureKnowledge/client.
- **Search anchors:** `LiteratureKnowledge`, `requestedLiteratureSourceId`, `requestedLiteratureEntryId`.

## Development — Roadmap Timeline / Calendar — REAL
- **What/when:** Two views over one backend Development Roadmap domain.
- **Canonical files:** `pages/DevelopmentRoadmap.tsx`, `api/development.ts`, routes.
- **Invocation/reuse:** `/development/roadmap/timeline` or `/calendar`; same component with `mode`.
- **I/O/persistence:** workspace-scoped backend state; UI mode/selection transient.
- **Authority/risk:** real bounded Development operations; no frontend schedule store.
- **Tests/evidence:** test/browser proof 116.
- **Do not reinvent:** reuse DevelopmentRoadmap/development API.
- **Search anchors:** `DevelopmentRoadmap`, `mode="timeline"`, `mode="calendar"`.

## Development — Brainstorm — REAL
- **What/when:** Workspace Brainstorm surface over backend-owned Development records/actions.
- **Canonical files:** `pages/DevelopmentBrainstorm.tsx`, `api/development.ts`.
- **Invocation/reuse:** `/development/brainstorm`.
- **I/O/persistence:** backend records; transient workspace/UI state.
- **Tests/evidence:** test/browser proof 117.
- **Do not reinvent:** reuse Brainstorm/development client.
- **Search anchors:** `DevelopmentBrainstorm`, `development.ts`.

## Coding — Repository / Runtime / Pipeline projection — REAL, bounded
- **What/when:** Shared workbench renders repository/runtime truth and accepted pipeline/action projections without browser shell/GitHub authority.
- **Canonical files:** `pages/CodingWorkbench.tsx`, `api/coding.ts`, `operatorSemantics.ts`, App wiring.
- **Invocation/reuse:** `/coding/repository` and `/coding/runtime`; same component with mode.
- **I/O/persistence:** backend Coding projections/actions; workspace/ref transient.
- **Authority/risk:** bounded backend actions may be proposed; no arbitrary shell/filesystem/direct GitHub-token authority.
- **Tests/evidence:** 140/143 tests; browser plan 140.
- **Limitations:** no separate primary `/coding/pipeline` route; pipeline is projected through the workbench.
- **Do not reinvent:** reuse CodingWorkbench/coding client/semantic helpers.
- **Search anchors:** `CodingWorkbench`, `RepositoryTruthResult`, `RuntimeTruth`, `pullRequestEvidenceSummary`, `runtimeDeltaSummary`.

## Settings — Appearance — REAL local
- **What/when:** Appearance/accent controls.
- **Canonical files:** `pages/Settings.tsx`, `theme.ts`, `styles/final-settings.css`.
- **Invocation/reuse:** theme read/write/apply helpers.
- **I/O/persistence:** browser-local only.
- **Side effects/risk:** document CSS/theme only.
- **Tests/evidence:** visual/Settings contracts.
- **Limitations:** intentionally separate from canonical server AI settings.
- **Do not reinvent:** reuse theme API.
- **Search anchors:** `APPEARANCE_OPTIONS`, `ACCENT_OPTIONS`, `setVisualAppearance`, `setVisualAccent`.

## Settings — AI/provider/credential controls — REAL, security-sensitive
- **What/when:** Canonical AI budgets/provider permissions/status and bounded Scaleway credential replace/delete.
- **Canonical files:** `pages/Settings.tsx`, `api/settings.ts`, `operatorSemantics.ts`.
- **Invocation/reuse:** canonical load + `saveAISetting`, `replaceScalewayCredential`, `removeScalewayCredential`.
- **I/O/persistence:** server settings/secret metadata; raw submitted credential is never projected back.
- **Preconditions:** backend capability projection.
- **Side effects/authority/risk:** real sensitive server mutations; UI rereads canonical state after mutation. Failed reread sets `State uncertain` and blocks further mutation until reload; delete is confirmed/focus-managed.
- **Tests/evidence:** 124/143; browser plan 124.
- **Limitations:** controls enabled only when backend capability flags permit; availability labels are projections, not inference proof.
- **Do not reinvent:** reuse settings API + canonical-reread/uncertain-state pattern.
- **Search anchors:** `loadCanonical`, `refreshAfterMutation`, `uncertain`, `credential_capabilities`, `credentialMeaning`.

## Operator semantic helpers — REAL
- **What/when:** Pure projection helpers prevent misleading credential/provider/runtime/PR wording.
- **Canonical files:** `operatorSemantics.ts`; consumers Settings/CodingWorkbench/ModelDossier.
- **Invocation/reuse:** import helpers instead of reconstructing labels.
- **I/O/persistence:** pure; none.
- **Tests/evidence:** `143-operator-semantic-ux.mjs` + 124.
- **Limitations:** helpers render truth; they do not create capability.
- **Do not reinvent:** reuse for equivalent evidence states.
- **Search anchors:** `credentialMeaning`, `providerLocation`, `savedPaidAiSummary`, `pullRequestEvidenceSummary`, `runtimeDeltaSummary`.

## Design — Process operator surface — PARTIAL / authoring unavailable
- **What/when:** Production Process workspace presents accepted process/basis context and handoff state; unsupported authoring stays visibly unavailable.
- **Canonical files:** `stages/ProcessStage.tsx`, App wiring, process styles, Project Knowledge handoff helpers.
- **Invocation/reuse:** `/design/process` via stage registry.
- **I/O/persistence:** reads accepted/handoff server data where wired; page state transient.
- **Authority/risk:** no server-owned topology/evaluator authoring authority at this frontend boundary.
- **Tests/evidence:** 058d + 100/100f/100g.
- **Limitations/fake paths:** future Process authoring controls are unavailable until server authority exists.
- **Do not reinvent:** extend only when matching backend authority exists.
- **Search anchors:** `ProcessStage`, `unavailableReason`, `readProjectKnowledgeHandoff`.

## Design — BLUECAD operator boundary — REAL inspect/select + PLACEHOLDER authoring toolbar
- **What/when:** Real server-owned geometry workbench/viewer/selection; presentation authoring toolbar is intentionally inert.
- **Canonical files:** `stages/ModelStage.tsx`, `components/bluecad/BluecadWorkbench.tsx`, `components/BluecadGlbViewer.tsx`, engineering Properties/Jarvis components.
- **Invocation/reuse:** `/design/bluecad`; workbench contributes selection/shell regions.
- **I/O/persistence:** geometry/evidence -> viewer/selection; selected part -> Properties/Jarvis context.
- **Authority/risk:** inspect/select only. Select/Orbit/Pan/Measure/Sketch/Circle/Extrude/Pattern/Fit/Zoom/Undo/Redo/Section/Inspect/Export presentation tools in `ModelStage` are disabled with unavailable reason.
- **Tests/evidence:** fusion/visual + BLUECAD/engineering evidence elsewhere.
- **Limitations:** toolbar appearance is not CAD-authoring capability.
- **Do not reinvent:** reuse viewer/workbench/selection; do not invent client-side CAD authority.
- **Search anchors:** `bluecadPresentationTools`, `futureReason`, `BluecadWorkbench`, `BluecadGlbViewer`.

## Runs operator workbench — REAL evidence/inspection, not execution authority
- **What/when:** Lists simulation runs, detail/logs/artifacts, filtering and source-run deep-link restoration.
- **Canonical files:** `pages/RunsWorkbench.tsx`, `api/runs.ts`, `components/runs/state.ts`, analytics source-run navigation helper.
- **Invocation/reuse:** routed workbench with workspace; `listRuns/getRun/listRunLogs/listRunArtifacts`.
- **I/O/persistence:** backend run/evidence data; filters/selection transient.
- **Preconditions:** workspace and run APIs.
- **Side effects/authority/risk:** read/restore/navigation behavior only at this boundary; generation/identity guards reject stale async responses.
- **Tests/evidence:** run state helpers and source-run navigation are explicit source seams; no production build contract proving arbitrary execution exists.
- **Limitations:** do not infer solver/run launch authority from this inspection surface.
- **Do not reinvent:** reuse run state projection, deep-link parsing and stale-response guards.
- **Search anchors:** `RunsWorkbench`, `acceptsResponse`, `chooseSelection`, `parseSourceRunTarget`, `listRunArtifacts`.

## Engineering Data operator surface — REAL mixed authority
- **What/when:** Unified operator inspection for model specs, assumptions, canonical parameters and decisions; canonical Parameter editing/lifecycle is genuinely wired.
- **Canonical files:** `pages/EngineeringData.tsx`, `api/parameterLifecycle.ts`, `components/engineering-data/engineeringDataState.ts`, base API list functions.
- **Invocation/reuse:** load four record kinds per workspace; `updateCanonicalParameter` and `transitionCanonicalParameter` for Parameters.
- **I/O/persistence:** backend-owned records; query/filter/selection transient; Parameter mutations persist server-side.
- **Side effects/authority/risk:** REAL Parameter mutation with stale/dependent-record/lifecycle guards; other record kinds are primarily inspection at this surface.
- **Tests/evidence:** explicit `ParameterLifecycleApiError` handling and workspace-generation guards in source.
- **Limitations:** unified display must not be mistaken for equal mutation authority across all kinds.
- **Do not reinvent:** reuse engineering-data projection/state and Parameter lifecycle client.
- **Search anchors:** `EngineeringData`, `ENGINEERING_KINDS`, `acceptsWorkspaceResponse`, `parameter_stale`, `parameter_lifecycle_dependents_require_reconciliation`.

## Review proposal authority — REAL
- **What/when:** Stage-owned review queue for proposed MemoryStore records; accept/reject and Parameter replacement promotion are real operator transitions.
- **Canonical files:** `stages/ReviewStage.tsx`, `api/memory.ts`, `components/review/reviewState.ts`.
- **Invocation/reuse:** `listMemoryProposals`; `promoteMemoryRecord`, `promoteParameterReplacement`, `rejectMemoryRecord`.
- **I/O/persistence:** backend proposal records and canonical transitions; filter/selection transient.
- **Side effects/authority/risk:** real canonical mutation; exact workspace/filter/record generation contexts reject stale loads/mutations; post-mutation reload restores focus.
- **Tests/evidence:** source contains `acceptsReviewRequest/acceptsReviewMutation`, replacement invalidation notice and actionable-state gating.
- **Limitations:** historical records are read-only; only proposed records transition.
- **Do not reinvent:** reuse review state/transition path rather than building another proposal queue.
- **Search anchors:** `ReviewStage`, `isActionable`, `promotionRoute`, `acceptsReviewMutation`, `promoteParameterReplacement`.

## AI Threads — REAL bounded advisory interaction
- **What/when:** Workspace thread list/detail/create and prompt submission over the AI-thread backend.
- **Canonical files:** `pages/AIThreads.tsx`, `api/threads.ts`, `components/threads/threadState.ts`.
- **Invocation/reuse:** `listThreads/createThread/getThread/submitThreadInteraction`.
- **I/O/persistence:** backend threads/interactions; selected thread/prompt transient.
- **Side effects/authority/risk:** creates durable thread/interactions; request IDs are generated once and reused when retrying an unchanged failed prompt; context guards drop stale workspace/thread responses.
- **Tests/evidence:** source explicitly uses `contextMatches`, captured list/detail/submit contexts and retry-stable `pendingSubmitRef`.
- **Limitations:** advisory/thread UX is not evidence of domain commit authority.
- **Do not reinvent:** reuse thread state/context and request-id retry pattern.
- **Search anchors:** `AIThreads`, `makeRequestId`, `pendingSubmitRef`, `contextMatches`, `submitThreadInteraction`.

## Legacy/diagnostic pages — PARTIAL / LEGACY; Dev Local Chat — DEFERRED DEV-ONLY
- **What/when:** `AIDraft`, `DomainFoundation`, `Dashboard/SystemStatus` and related pages expose diagnostics/older seams; `DevLocalChat` is development-only.
- **Canonical files:** `pages/{AIDraft,DomainFoundation,Dashboard,DevLocalChat}.tsx`, route registry.
- **Invocation/reuse:** only use when explicitly working on diagnostics/legacy compatibility; primary product work should use current production routes.
- **I/O/persistence:** mixed real diagnostic API calls; AIDraft includes an explicitly fake deterministic route alongside real AI/settings/modeling seams.
- **Authority/risk:** presence of a real API call in a legacy page does not make it primary operator UX.
- **Tests/evidence:** route registry/DEV gating.
- **Limitations/fake paths:** diagnostic/fake paths must not be advertised as production capability.
- **Do not reinvent:** prefer primary surfaces; retain legacy only for its explicit diagnostic role.
- **Search anchors:** `AIDraft`, `DomainFoundation`, `DevLocalChat`, `import.meta.env.DEV`.

## Frontend API clients / types / generated artifact — REAL mixed handwritten + one generated file
- **What/when:** Typed React-to-backend boundary; search it before adding component-local fetch logic.
- **Canonical files:** `api/client.ts`; domain wrappers including `coding.ts`, `development.ts`, `knowledgeActions.ts`, `literature.ts`, `memory.ts`, `modelDossier.ts`, `parameterLifecycle.ts`, `projectKnowledge.ts`, `runs.ts`, `settings.ts`, `threads.ts`; `api/generated/modeling.ts`.
- **Invocation/reuse:** import domain wrapper/types.
- **I/O/persistence:** JSON HTTP; backend remains persistence owner except visual prefs.
- **Authority/risk:** wrappers can perform real mutations; types do not grant authority.
- **Tests/evidence:** current `api/generated/` directory contains exactly `modeling.ts`.
- **Limitations:** no repository evidence of a generic frontend-wide generated-client/codegen command in `frontend/package.json`; do not infer one from the directory name.
- **Do not reinvent:** search `frontend/src/api` first; treat `generated/modeling.ts` as a narrow generated artifact unless provenance is explicitly found.
- **Search anchors:** `frontend/src/api`, `api/generated/modeling.ts`.

## Browser-proof / visual / accessibility helpers — REAL verification primitives
- **What/when:** Source-contract tests plus declarative trusted Chromium plans for operator behavior.
- **Canonical files:** `frontend/tests/*`; `.github/browser-proof/{run.mjs,plan-lib.mjs,request-policy.mjs,fixture-registry.mjs,plans/,fixtures/}`; `browser-proof-contract.yml`.
- **Invocation/reuse:** frontend build runs source contracts; browser proof uses declarative plans/fixtures for 113/114/115/116/117/121/124/140.
- **I/O/persistence:** actions/assertions/screenshots/evidence artifacts; bounded fixture setup.
- **Authority/risk:** verification only; browser proof is distinct from Node/source-test success.
- **Tests/evidence:** `test-plan-lib.mjs`, `test-request-policy.mjs`, `test-mutation-window.mjs`, validators.
- **Limitations:** not every surface has trusted-browser proof; source tests are not rendered proof.
- **Do not reinvent:** add declarative proof plans rather than spec-hard-coded controller logic.
- **Search anchors:** `.github/browser-proof/plans`, `validate-plan.mjs`, `run.mjs`, `frontend/tests`.

## Frontend build / dev / production gate — REAL
- **What/when:** Vite dev/preview plus production contract gate.
- **Canonical files:** `frontend/package.json`, Vite config, `frontend/tests/*`.
- **Invocation/reuse:** `npm run dev` and `npm run preview` bind `127.0.0.1`; `npm run build` runs 058d, 100, 100f, 100g, 112, 113, 114, 115, 116, 117, 124, 140, 143, eyebrow contrast, then `tsc` and Vite build.
- **Preconditions:** Node/npm; current package pins React 18.3.1, Vite 6.0.5, TypeScript 5.7.2, Three 0.171.0.
- **Side effects/risk:** build output only; no product authority.
- **Limitations:** contract scripts are mostly source/deterministic checks; they do not replace trusted rendered browser evidence where required.
- **Do not reinvent:** extend existing scripts/gates.
- **Search anchors:** `frontend/package.json`, `vite.config.*`, `npm run build`.

## Status matrix
| Surface | Status | Runtime evidence / caveat |
|---|---|---|
| App shell/routes | REAL | explicit production registry, redirects, not-found |
| Shell/focus/responsive/a11y basics | REAL | skip link, focus restore, aria toggles, 60rem collapse/local overflow |
| Theme/tokens/primitives | REAL | central theme/tokens; intentionally small shared UI set |
| Approved design references | REAL authority docs | references are not runtime wiring |
| Project Basis/Knowledge/Search | REAL | routed clients/components + tests/proofs |
| Models | REAL | dossier + explicit version selection |
| Literature | REAL | source/entry + unavailable backing handling |
| Roadmap Timeline/Calendar | REAL | one backend domain, two modes |
| Brainstorm | REAL | routed component/API |
| Coding Repository/Runtime | REAL | bounded workbench/API |
| Coding pipeline | PARTIAL | projected in workbench; no separate primary route |
| Settings appearance | REAL | local-only |
| Settings AI/provider/credential | REAL | sensitive server writes + canonical reread/fail-safe |
| Process | PARTIAL | read/handoff; authoring unavailable |
| BLUECAD inspect/select | REAL | viewer/workbench + explicit selection |
| BLUECAD authoring toolbar | PLACEHOLDER | presentation tools disabled |
| Runs | REAL inspection | evidence/log/artifact/restore UX; not run-execution authority |
| Engineering Data | REAL mixed | real Parameter mutation; other kinds primarily inspection |
| Review | REAL | proposal accept/reject/replacement authority |
| AI Threads | REAL bounded | durable advisory threads; retry-stable request IDs |
| Legacy diagnostics | PARTIAL / LEGACY | some real APIs plus diagnostic/fake seams; not primary UX |
| Dev Local Chat | DEFERRED / DEV-ONLY | DEV-gated |
| Generated frontend client | PARTIAL | only `generated/modeling.ts`; no generic codegen pipeline evidenced |

## Gaps / duplication discovered
- No generic modal/dialog/form-state framework: destructive confirmations and async form/focus behavior remain page-owned.
- Frontend async stale-response protection is implemented repeatedly through domain-specific generation/context helpers (`runs`, Engineering Data, Review, AI Threads); these are real reusable local seams but not one generic framework.
- Legacy pages can expose real backend calls and fake/diagnostic routes beside the primary product; route presence/source wiring must be checked before advertising operator capability.
- BLUECAD and Process approved visuals include controls beyond current frontend authority; disabled/unavailable presentation must remain distinguishable from wired behavior.
- Generated-client naming overstates current breadth: only modeling has a generated artifact; no generic regeneration/check command is evidenced in the frontend package scripts.
- Trusted Chromium coverage is selective; build/source-contract success must not be treated as proof for unplanned rendered interactions.

## Final fake/inert-control sweep
- **Confirmed PLACEHOLDER:** BLUECAD presentation authoring toolbar in `ModelStage` is disabled with explicit unavailable reason.
- **Confirmed PARTIAL/unavailable:** Process authoring controls lack server topology/evaluator authority and must remain unavailable.
- **Confirmed LEGACY/fake seam:** `AIDraft` includes an explicitly fake deterministic route among diagnostic operations; do not route production UX through it.
- **Backend capability without equivalent primary wiring:** some diagnostics/legacy APIs and historical stage files (`ResultsStage`, `LineageStage`) exist without being independent primary production routes; file existence is not operator availability.
- **Not fake:** Review mutations, canonical Parameter mutations, Settings credential/settings writes, Development operations and AI Thread interactions are real backend writes and require their existing guards.

No major Area B subsystem remains uninspected at the repository/frontend boundary: shell/routes, design authority, shared primitives/theme/styles/responsive behavior, primary Memory/Development/Coding/Settings/Jarvis/Design surfaces, Runs/Engineering Data/Review/AI Threads, legacy/dev-only surfaces, API/generated boundary, tests/browser-proof helpers and build/dev scripts have all been inspected.