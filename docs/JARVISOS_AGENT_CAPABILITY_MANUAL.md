# JarvisOS agent capability manual

Issue: #656
Baseline inspected: master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb
Canonical file accounting: docs/agent-manual/FILE_COVERAGE_MANIFEST.tsv

This is an operational map for coding agents. Runtime/code and deterministic tests outrank historical specifications and prose. A capability marked REAL is implemented in the inspected baseline; PARTIAL means a bounded seam exists; PLACEHOLDER means visible scaffolding is intentionally inert; DEFERRED means no executable authority was found. The manual does not grant authority to models, providers, browsers, GitHub, or the frontend.

## If you need X, use Y

| Need | Start here |
|---|---|
| Compose/start the backend or inspect API mounting | backend/app/main.py; backend/app/core/bootstrap.py; backend/app/core/config.py; backend/app/core/paths.py |
| Use the canonical SQLite/data-root layer | backend/app/core/database.py; backend/app/core/schema.py; backend/app/core/repository.py; backend/app/core/paths.py |
| Execute a product AI task | backend/app/modules/ai/gateway.py → execution.py → token_flow_runtime.py; explicit auto requests are normalized by gateway.py; do not call providers directly |
| Understand provider, route, budget, privacy or egress admission | backend/app/modules/ai/provider_registry.py; egress_policy.py; egress_authority.py; egress_persistence.py; egress_lifecycle.py; egress_revalidation.py |
| Continue or account for bounded AI output | backend/app/modules/ai/token_flow_service.py; token_flow_continuation.py; token_flow_external_runtime.py; token_flow_segments.py; token_flow_evidence.py |
| Use local AI classification/evaluation | backend/app/modules/local_ai/; backend/app/modules/local_ai_eval/; scripts/local_model_*.py; scripts/router_policy_*.py |
| Read/write Project Knowledge or engineering records | backend/app/modules/project_knowledge/; backend/app/modules/memory/; backend/app/modules/modeling/; backend/app/core/*_schema.py |
| Search literature, models or project evidence | backend/app/modules/memory/literature_*.py; backend/app/modules/modeling/model_dossier_search.py; backend/app/modules/modeling/project_search_owner.py |
| Use roadmap, calendar or brainstorm | backend/app/modules/development/; frontend/src/pages/DevelopmentRoadmap.tsx; frontend/src/pages/DevelopmentBrainstorm.tsx |
| Inspect coding repository/runtime truth | backend/app/modules/coding/; frontend/src/pages/CodingWorkbench.tsx; frontend/src/api/coding.ts |
| Review AI-origin proposals | backend/app/modules/memory/replacement.py; frontend/src/stages/ReviewStage.tsx; frontend/src/components/review/reviewState.ts |
| Preview/execute Jarvis context actions | backend/app/modules/ai/jarvis_context.py; jarvis_context_models.py; jarvis_context_routes.py; frontend/src/components/ai/useJarvisSidecar.tsx |
| Use BLUECAD geometry/evidence | backend/app/modules/bluecad/; backend/app/modules/runner/; backend/app/modules/engineering/ |
| Use process kernel or bundled engineering calculations | backend/app/modules/process_kernel/; backend/app/modules/runner/ |
| Use 047–049 BlueRev screening | backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.py; bluerev_biomass_nutrients_harvest_v0.py; bluerev_buoyancy_optical_screening_v0.py |
| Link process outputs to CAD | backend/app/modules/bluecad/cad_link.py; cad_link_topology*.py; backend/app/core/cad_link_schema.py |
| Inspect runs and evidence | backend/app/modules/runner/service.py; backend/app/modules/bluecad/evidence.py; frontend/src/pages/RunsWorkbench.tsx |
| Run local tests/contract checkers | backend/tests/; tests/; scripts/check_*.py; .github/browser-proof/ |
| Run trusted browser proof | .github/browser-proof/ plans/fixtures/run.mjs; .github/workflows/exact-head-browser-proof.yml |
| Deliver a branch/PR safely | docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md; scripts/repository_delivery.py; scripts/cloud_delivery_bridge.py; .github/local_worktree_actuator_core.py |
| Understand CI/merge/security authority | .github/workflows/ci.yml; merge-authority-verify.yml; exact-head-browser-proof-command.yml; AGENTS.md |
| Recover local product data | scripts/data_root_recovery/; docs/DATA_ROOT_RECOVERY.md |
| Inspect provider/model evaluation evidence | backend/app/modules/local_ai_eval/; scripts/local_*probe.py; reports/; docs/LOCAL_AI_EVALUATION_EVIDENCE.md |
| Inspect persistent AI threads and cohort accounting | backend/app/modules/ai/thread_routes.py; thread_service.py; flow_grade_cohort_routes.py; flow_grade_cohorts.py |

## System contract and authority order

1. Actual runtime code, deterministic validators and tests.
2. AGENTS.md for hard invariants.
3. docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md for delivery mechanics.
4. docs/specs/STATUS.md for live spec state; a specification does not prove implementation.
5. Accepted spec/readiness and design references for intended scope and UI contract.

Hard invariants that constrain every agent:

- route_class=auto never executes an external provider.
- Product AI calls use run_ai_task and create an ai_jobs row.
- Frontend never calls providers, filesystems or execution tools directly.
- Safe defaults are paid AI disabled, zero budget, fake provider and fake/mocked providers in tests.
- Local classification is advisory and cannot decide permissions, privacy, routing, memory or sensitivity.
- No secrets in logs, events, docs, fixtures, commits, model context or frontend responses.
- Data-root paths go through backend/app/core/paths.py; runtime data stays out of the repository.
- Model output is a proposal until explicit user or deterministic-policy promotion.
- Never fabricate tests, screenshots, artifacts, metrics or outputs to pass a gate.

## Backend / product capability map

### Composition, data and persistence — REAL

backend/app/main.py is the FastAPI composition/lifecycle root. The core layer owns environment-backed settings, the C:\JarvisOS data root, SQLite connection/bootstrap/migrations, shared schema registration, row-to-Pydantic conversion and safe SPA fallback. Reuse open_sqlite_connection, schema registries and repository conversion helpers; do not create another database, data root or row mapper.

The product domains are persistent and workspace-scoped:

- MemoryStore owns assumptions, parameters, decisions and AI-origin proposal/replacement lifecycle. Parameter lifecycle transitions require freshness/dependency handling.
- Project Knowledge owns curated source/revision/apply/reconciliation state and is distinct from MemoryStore.
- Literature owns sources, entries/claims/data and explicit backing/availability.
- Modeling owns model dossiers/versions, project-search owner seams and domain-fundamental data.
- Development owns roadmap, calendar and brainstorm records/promotion.
- Coding owns repository/runtime truth and bounded proposal actions; it does not give the frontend arbitrary shell/GitHub authority.
- Events/files/secrets/tools/workspaces provide typed support registries and workspace-scoped boundaries; they are not interchangeable stores.

Useful anchors: open_sqlite_connection, initialize_database, build_workspace_context_pack, deterministic_topological_order, repository row mappers, current/revision/superseded lifecycle fields.

### AI execution, routing and egress — REAL, bounded by policy

Use gateway.py for product-facing entry. Normal tasks reach run_ai_task/execution.py and persist attempt/token-flow evidence; an explicit `route_class=auto` request is first handled by gateway.py's `run_auto_task` policy path. Local adapters execute through the provider-neutral contract. External routes pass through egress_runtime.py and the persisted packet/ticket/reservation lifecycle; no direct provider call is a valid product path.

Important seams:

- provider_registry.py is the strict YAML-backed provider/model/route/fallback/pricing authority.
- routing/decision.py, capability_route_matrix.py, invariants.py and safe_local.py classify route/task/provider relationships; `routing/decision.py` is explicitly a provider-free contract/probe producer, while `invariants.py` validates permission fields. Their recommendations are advisory until the governed gateway/egress path promotes them; neither module calls providers or grants network permission.
- privacy.py, sensitivity.py and sensitivity_routes.py classify/label context; deterministic floors only raise sensitivity and never grant permission.
- egress_authority.py and egress_revalidation.py prepare and re-check eligible prompt/context authority against exact source digests and policy versions.
- egress_policy.py only accepts the canonical policy file. egress_persistence.py, egress_lifecycle.py and egress_confirmation_core.py own tickets, reservations, CAS transitions, dispatch-state, accounting and conservative reconciliation.
- token_flow_* owns durable flow/segment/continuation state. A length-limited output becomes a bounded continuation, not a fabricated complete result.
- egress_spine.py records body-free pre-packet deny/pause decisions, creates the single queued `ai_jobs` row, and CAS-finalizes its binding, output digest, usage and terminal status. flow_record_capture.py atomically/idempotently turns eligible terminal outputs into canonical MemoryStore proposals.
- thread_service.py owns workspace-scoped AI threads and interaction capture. It binds retries to a canonical request digest, reserves/dispatches through `run_ai_task`, captures bounded assistant text, and records proposal IDs; it is transcript/interaction state, not domain promotion authority.
- flow_grade_cohort_routes.py exposes bounded, read-only cohort reconciliation: terminal flows, grades, execution composition, dispatch quality, provider accounting basis, token/latency distributions and conservative-spend invariants. It is evaluation/observability, not permission to execute.
- providers/*.py and *_adapter.py implement adapters; they are not routing, secret storage, budget or egress authority.
- fake_adapter.py is deterministic test/provider-mode behavior. local_ollama_adapter.py is loopback/local only when configured. Scaleway/DeepSeek/OpenAI-compatible adapters can be externally capable, but canonical execution and policy still govern product dispatch.

State and outputs include ai_jobs, token flows, protected segments, immutable packet/decision/ticket/reservation/attempt evidence, provider/model/usage bindings and sanitized events. External availability is conditional on credentials, policy, budget and route binding. Tests in backend/tests/test_ai_*, test_token_flow_*, test_scaleway_*, test_provider_registry.py and egress fixtures are the main evidence.

Failure modes:

- A configured provider is not proof of credentials, quota or network health.
- Directly calling an adapter bypasses governed egress and is not equivalent to product execution.
- Malformed policy, context drift, missing credentials, budget exhaustion, sensitivity uncertainty or binding mismatch must fail closed.
- Settings projections and legacy cost estimates are not canonical accounting.
- In FAST_DEV, marker-free text is treated more permissively; structural secrets remain blocked. Do not describe this as universal fail-closed classification.
- Local fallback does not authorize external fallback.
- Duplicate or stale token/egress state must be reconciled conservatively, not guessed away.

### Local AI classification — PARTIAL; evaluation harness — REAL

`local_ai` is an advisory local classifier/intake/runtime seam with deterministic contracts and bounded Ollama loopback lifecycle/status. It depends on a configured local runtime/model and does not become usable merely because the adapter exists; it has no external-network authority and cannot own permission, provider, memory or sensitivity decisions. `local_ai_eval` and `scripts/local_*` provide real dry-run/replay, holdout scoring and evidence capture, but model output remains advisory and semantic truth is not implied. The evaluation harness is not a provider permission gate.



Structured tool/agent boundary: backend/app/modules/agents/ and backend/app/modules/tools/ currently provide only small in-memory `register`/`names` containers. They are not a general agent scheduler, structured tool-calling exchange, sandbox, or authority layer. The current provider-neutral AI path is text-oriented; Hermes/tool-calling integration remains planned documentation, not an implemented runtime. Do not build a second orchestration or tool-permission path by treating these registries as one.

### Jarvis context/actions — REAL, explicit and non-domain-authoritative

jarvis_context.py plus jarvis_context_models.py/routes.py implement digest-bound READ/CONTEXT previews with route/ref allowlists, bounded refs/blocks and stale-source rejection. Registered adapters cannot expose COMMIT or EXECUTE. Dispatch requires an exact expected digest after rebuild. The sidecar and knowledge-action components are a presentation/action proposal surface; they do not become a second thread store or canonical domain commit path.

### Development/coding — REAL but bounded

Development services persist roadmap/calendar/brainstorm records and explicit promotions with workspace, dependency-cycle, revision and done-when checks. Coding services expose read-only repository/ref/commit/path/search/check/review truth and bounded AI proposals. `CodingActionsService` freezes an exact base SHA, admits at most 16 non-binary paths, rejects protected targets, validates a closed proposal schema and rechecks the ref after generation. Proposals do not apply patches, commit or push; use delivery authority and exact-head/CAS workflows for repository mutation.

## Engineering / scientific capability map

### BLUECAD candidate loop — REAL, evidence-bound

backend/app/modules/bluecad/loop.py coordinates candidate creation, AI proposal, deterministic build, validation, repair and simulation/evidence registration. ledger.py persists candidate/attempt/artifact state. builders.py/assembly.py build deterministic primitives and placements; spec.py/models.py/validate.py enforce GeometrySpec/port/part contracts; export.py writes STEP/GLB and deterministic manifests.

The loop is not unrestricted CAD authoring. It is bounded by workspace paths, exact specs, model/proposal limits and deterministic validation. Structural repair requires authorized evidence context; evidence_egress.py prevents structural source leakage and binds prompts/derivatives to exact evidence lineage.

### Mesh/FEM — REAL, configuration-dependent

mesh_adapter.py calls only the registered Gmsh tool boundary and validates labels/manifest/geometry references. fem_adapter.py and fem_adapter_base.py integrate pressure loads and parse CalculiX results; FEM verification includes analytic benchmarks, parser/fixture checks, reaction/pressure audits and deterministic evidence. External executables are not guaranteed installed, so proof is configuration-dependent. Never present analytic or synthetic proof as successful real-tool proof.

### Runner and process kernel — REAL, exact-profile bounded

runner/service.py and guarded_service.py register and execute only exact server-known/bundled implementations. safety.py enforces input/path/script-hash/AST/import/network/process/output bounds; _execution_owner.py/_execution_child.py serialize and supervise a local child; linked_parameters.py enforces workspace ownership, active lifecycle, revision and physical-value freshness. Registration, run, logs, artifacts and recovery are persisted.

Process kernel 075 is a typed acyclic graph of components/streams/units with explicit material requirements, immutable stream semantics, validation, deterministic execution and exact 047 profile registration. It is not a general process simulator.

### Current BlueRev models — REAL bounded screening

- 047 geometry/hydraulics: nine unit-bearing inputs; areas/volumes, circulation, turnover, Reynolds, Darcy loss/head/pump power. Uses 64/Re in laminar and Blasius only in qualified turbulent range; transitional/unqualified correlation fails closed.
- 048 biomass/nutrients/harvest: deterministic inventory/productivity, nutrient/carbon incorporation, stock dosing, gas-equivalent benchmark, harvest/filter sizing and pump-electricity-only economics. Productivity is imposed; no full TEA, gas transfer or CAPEX.
- 049 buoyancy/optical: static Archimedes screening and Beer-Lambert-like transmission/fouling proxies. No wave/mooring/stability/freeboard/PAR/scattering/growth coupling.
- 050/051: dependency graph and stale propagation after accepted parameter replacement; they do not auto-recompute results.
- 052/072/074: bounded process-to-CAD and topology-to-CAD links with exact manifests/digests; 072/074 remain experiment/reference authority, not general CAD authority.
- 071/071b: input contract, binding/DOF preview and Engineering Properties.
- 073: capped branch-manifold primitive.
- 075: typed acyclic process-kernel profile, historical/incumbent exact 047 path.
- No current qualified integrated PBR model, general recycle convergence, broad thermodynamics/property package or arbitrary unit-operation simulator was found. Standalone 078 is deferred/cancelled planning evidence.

## Frontend / operator capability map

### Shell, routing and shared presentation — REAL

frontend/src/App.tsx, app/routes.ts, useAppRouter.ts, components/Layout.tsx and stages/registry.ts are the single shell/router/stage composition. Use resolveRoute, PRIMARY_STAGES and existing shell contributions; do not add a second router or page-owned chrome.

Layout owns rail, main, contextual navigator, Jarvis sidecar and analysis dock. Shell region requests, focus restoration, skip link, native disclosure and responsive containment are already present. The shared foundation is theme.ts, tokens/global/foundation/responsive CSS and small primitives Button, Field, InlineNotice, StatusBadge and Surface. There is no generic modal/form/disclosure framework to assume.

Approved HTML references and interaction contracts under docs/design-references/ define visual/interaction targets, not runtime truth. Compare against the manifest-selected references, but do not infer a wired control from a screenshot or inert reference control.

### Domain surfaces — REAL unless noted

- Project Basis/Knowledge/Search: backend-owned records and bounded search; explicit lifecycle actions use the existing API clients and stable record refs.
- Models: ModelDossier and modelDossier.ts expose model/version selection; old model/results/lineage routes redirect.
- Literature: LiteratureKnowledge and literature.ts expose source/entry/deep-link/backing states; missing backing is explicit, never fabricated.
- Development: DevelopmentRoadmap serves timeline/calendar modes; DevelopmentBrainstorm uses the Development API.
- Coding: CodingWorkbench exposes repository/runtime/pipeline projections and bounded actions; no arbitrary shell or GitHub token authority.
- Settings: appearance/accent are browser-local; AI/provider/budget/credential controls are real server mutations with canonical reread, uncertain-state blocking and no raw credential projection.
- AI Threads: create/list/submit through api/threads.ts; advisory transcript and request/generation guards are visible; it is not direct domain commit authority.
- ReviewStage: real proposal accept/reject and Parameter replacement promotion through memory APIs; stale workspace/filter/record completions fail closed.
- RunsWorkbench: real run/log/artifact inspection and previous-successful-run handoff into Engineering Properties; it does not execute arbitrary runs.
- EngineeringData: unified inspection; Parameter edit/lifecycle is real, other record kinds are not automatically equal mutation authority.
- BLUECAD: real inspect/select/viewer/property handoff; the visible authoring toolbar is PLACEHOLDER/inert until backend authority exists.
- ProcessStage: PARTIAL; accepted process/basis/handoff context is visible, authoring is explicitly unavailable.

Key frontend clients are handwritten domain wrappers under frontend/src/api plus generated model dossier client where present. Pure state helpers provide request-generation/stale-response and selection guards; reuse them.

### High-risk UI boundaries

- The frontend never calls providers, Ollama, filesystems or execution tools directly.
- A visual control can be intentionally unavailable or diagnostic-only; inspect disabled state and unavailable reason before extending it.
- Browser proof is plan-driven and exact-head-bound; source/build success is not rendered-browser proof.
- Settings secret mutations require backend capability flags, confirmation and canonical reread; uncertain state blocks further writes.
- Browse/open actions do not automatically add Jarvis context; explicit stable refs and route allowlists govern that.

## Delivery, security and operations

### Repository delivery — REAL, exact-head/CAS governed

Use docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md and scripts/repository_delivery.py/cloud_delivery_bridge.py. The delivery path validates repository identity, branch/base/expected head, protected refs, worktree containment, git config/include escapes, force/non-fast-forward refusal and post-push SHA. Cloud bridge treats PR comments as untrusted input, binds exact comment body digests and dispatches guarded patch materialization.

.github/local_worktree_actuator_core.py provides capabilities for reviewer reads, local worktree creation, scoped writer leases and recovery; local worker offline does not erase cloud capabilities. Never substitute model claims or green CI for exact-head evidence.

### CI and browser proof — REAL, layered

.github/workflows/ci.yml is the broad gate; scope classification selects relevant checks but is not semantic acceptance. browser-proof/ validates closed plans, fixtures, request policies, mutation windows and artifact modes; exact-head-browser-proof-command.yml dispatches only trusted master workflow code for same-repo open PRs with fresh head SHA. Individual plans cover models, literature, project search, roadmap/calendar, brainstorm, knowledge actions, settings and coding.

cheap-review, project-knowledge-fast and senior-review are advisory/diagnostic/manual surfaces; senior-review is a legacy GLM/provider seam and must not be treated as vendor-neutral authority. post-merge-status-reconcile.yml is narrow and event-driven; it creates only a fresh-master reconciliation branch and uses stale-write refusal, never pushing master.

### Launch, backup, diagnostics — REAL but operationally imperfect

scripts/start-backend.ps1, start-frontend.ps1 and start-dev.ps1 launch/supervise local services. The silent Windows launcher uses readiness polling, but logging is hardcoded to C:\JarvisOS\jarvis.log and stop uses a broad uvicorn/app.main command-line match. start-backend installs/upgrades dependencies on each launch; start-frontend has a fixed browser delay rather than readiness-driven open.

scripts/data_root_recovery/ plus docs/DATA_ROOT_RECOVERY.md snapshot, verify and restore local data-root files with manifest/hash/SQLite integrity checks. It is not cloud backup.

### Security boundaries

AGENTS.md is the stable constitution. Secrets live through the secrets/data-root owners and must not appear in logs/docs/fixtures/frontend. Provider credentials are not capability proof. Local AI classifiers and model suggestions are advisory. Model output is proposal until deterministic/user promotion. Use exact path/data-root/sensitive-control-path guards and no direct provider or shell authority from the frontend.

## What not to reinvent

- Another SQLite connection/data root, row-mapper, MemoryStore, Project Knowledge owner, or frontend router.
- Another provider gateway, budget calculator, sensitivity classifier, egress ticket/reservation lifecycle, token-flow continuation store, or direct adapter dispatch path.
- Another BLUECAD GeometrySpec/manifest/evidence ledger, FEM parser, runner sandbox/runner registration path, or process-kernel execution path.
- Another frontend shell, generic modal/form framework, Jarvis sidecar/context store, review queue, run state machine or API client for an existing domain.
- Another delivery actuator, exact-head/CAS guard, browser-proof runner, local recovery/backup mechanism or fake “semantic acceptance” layer.

## Search anchors and high-value tests

backend/tests/test_ai_*.py, test_token_flow_*.py, test_egress_*.py, test_local_ai_*.py, test_memory_store.py, test_parameter_lifecycle.py, test_project_knowledge_*.py, test_coding_*.py, test_runner_*.py, tests/fixtures/, scripts/check_*.py, .github/browser-proof/test-*.mjs, frontend/src/components/*/state*.ts, frontend/src/api/, and the exact symbols named in the routing table.

High-value commands from repository context:

- Backend: cd backend && pytest
- Frontend: cd frontend && npm run build
- Browser plans: node .github/browser-proof/validate-contract.mjs
- Coverage: python3 scripts/validate_agent_manual_coverage.py --base-ref master

## Report provenance and generated evidence

The report tree is mixed. Markdown summaries are human-authored operational provenance and were inspected as READ evidence when they contain implementation boundaries, acceptance criteria, failure modes or status decisions. JSON, text logs, CAD/mesh binaries and other machine-produced outputs remain GENERATED/ASSET when they do not add standalone capability semantics. A report can support a claim, but it never outranks current runtime code or deterministic tests.

## Coverage manifest

The exhaustive file-level accounting is intentionally outside this prose document. Use docs/agent-manual/FILE_COVERAGE_MANIFEST.tsv as the single normalized source. Its terminal statuses are READ and GENERATED/ASSET only; each master path occurs exactly once. See docs/agent-manual/FILE_COVERAGE_AUDIT.md for counters and provenance.
