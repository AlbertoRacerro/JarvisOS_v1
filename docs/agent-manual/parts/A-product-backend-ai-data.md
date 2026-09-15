# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline inspected from fresh `master` at `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Status labels below describe executable code/runtime contracts, not merged-spec intent.

## FastAPI composition + process startup — REAL
- **What/when:** canonical backend composition root; use it to discover product routers, SPA reservation, startup/shutdown owners and cross-cutting recovery.
- **Canonical files:** `backend/app/main.py`; `backend/app/core/config.py`; `backend/app/core/spa_static.py`.
- **Invoke/reuse:** `app.main:create_app`; exported `app`; lifespan creates local-AI lifecycle, captures Coding runtime snapshot, reconciles stranded runner jobs and schedules recheck for still-live owners.
- **I/O/persistence:** startup runtime snapshot in `app.state`; runner reconciliation can mutate persisted runner state; SPA serves `frontend/dist` only when present.
- **Preconditions:** settings/CORS; local-AI lifecycle env; SQLite availability for runner reconciliation. Runtime-truth capture deliberately fails open to an unavailable snapshot; transient SQLite locks are retried for abandoned owners.
- **Side effects/risk:** composition is authoritative wiring. Routers currently include AI+sensitivity, Memory+Literature, Project Knowledge/Search, Coding Runtime, Development+Brainstorm plus engineering/runner/workspace/secrets domains.
- **Evidence:** `backend/app/main.py`; backend route/startup tests and domain tests.
- **Limitations:** repository-truth Coding routes are mounted through Coding runtime router rather than a separate top-level router. Do not infer a route merely from a module existing.
- **Do not reinvent:** add product backend surfaces through existing router/service boundaries and composition root.
- **Search anchors:** `create_app`, `lifespan`, `_reconcile_after_live_owners_exit`, `_SPA_RESERVED_ROOT_CLIENT_ROUTES`.

## Data root + SQLite + migrations — REAL
- **What/when:** one local-first data-root owner and SQLite connection/bootstrap owner for canonical product records.
- **Canonical files:** `backend/app/core/paths.py`, `backend/app/core/database.py`, schema modules under `backend/app/core/*_schema.py`.
- **Invoke/reuse:** `build_paths`, `ensure_data_directories`, `get_database_path`, `open_sqlite_connection`, `initialize_database`, `get_database_info`.
- **I/O/persistence:** `JarvisPaths` owns data root, SQLite DB, workspace/artifact/log dirs and secrets dir. Connections enable foreign keys, 5s busy timeout and WAL. Bootstrap composes base schema plus CAD link, sensitivity, egress, token-flow, grade, AI-thread, Project Knowledge, Literature, Development and Brainstorm schema/migrations/indexes; FTS5 is conditional and backfilled when available.
- **Preconditions:** writable configured data root; SQLite build (FTS optional).
- **Side effects/risk:** `initialize_database` creates/migrates tables and indexes and records migrations; migration ALTERs tolerate only duplicate-column errors. High authority over persistent state.
- **Evidence:** `backend/app/core/database.py`; database/bootstrap/domain persistence tests.
- **Limitations:** migrations are application-managed SQL constants, not Alembic. FTS capability varies by SQLite build.
- **Do not reinvent:** reuse `open_sqlite_connection` and schema migration registry; do not create another product DB/data-root.
- **Search anchors:** `open_sqlite_connection`, `initialize_database`, `_record_schema_migrations`, `SCHEMA_MIGRATION_RECORDS`.

## Canonical engineering MemoryStore (assumptions/parameters/decisions) — REAL
- **What/when:** canonical lifecycle owner for engineering memory records and AI-origin proposals; use for accepted/proposed assumptions, parameters and decisions rather than parallel memory tables.
- **Canonical files:** `backend/app/modules/memory/service.py`, `models.py`, `routes.py`, `replacement.py`; base schema in `backend/app/core/schema.py`.
- **Invoke/reuse:** Memory API routes and service functions such as `create_proposal`; service maps record kinds to canonical `assumptions`, `parameters`, `decisions` tables.
- **I/O/persistence:** SQLite; statuses normalize to proposed/accepted/rejected/superseded; AI proposals require an existing `ai_jobs` provenance row. Parameter replacement validates replacement semantics and integrates flowsheet freshness invalidation.
- **Preconditions:** existing workspace; AI proposals require valid `source_ai_job_id`.
- **Side effects/risk:** lifecycle mutations log events; accepted/replacement parameter operations can invalidate downstream freshness. Domain-authoritative writes, not advisory cache.
- **Evidence:** memory tests plus service transaction boundaries (`BEGIN IMMEDIATE`).
- **Limitations:** this is engineering canonical memory, distinct from Project Knowledge document/revision curation and Literature source curation.
- **Do not reinvent:** reuse MemoryStore lifecycle and replacement/freshness machinery for assumptions/parameters/decisions.
- **Search anchors:** `_TABLE_BY_KIND`, `_create_proposal_in_transaction`, `validate_parameter_replacement_proposal`, `persist_freshness_invalidation`.

## Project Knowledge / Project Basis — REAL
- **What/when:** canonical project-knowledge owner for curated project-basis records, sources/revisions and apply lifecycle.
- **Canonical files:** `backend/app/modules/project_knowledge/{service,apply,revision_lifecycle,routes,models}.py`; `backend/app/core/project_knowledge_schema.py`; ownership bridge `backend/app/modules/memory/project_knowledge_owner.py`.
- **Invoke/reuse:** `/project-knowledge` router/service; use service queries/mutations and explicit apply/revision lifecycle rather than writing tables directly.
- **I/O/persistence:** SQLite project-knowledge tables/revisions plus backing-source metadata; service is substantial persistent implementation, not UI fixture.
- **Preconditions:** workspace and valid lifecycle/version expectations; apply path is explicit.
- **Side effects/risk:** curation/apply changes canonical project knowledge; revision lifecycle and CAS-like expectations protect stale writes.
- **Evidence:** backend Project Knowledge tests and browser-proof fixtures/plans for Project Basis/knowledge actions.
- **Limitations:** Project Knowledge is not the same owner as MemoryStore assumptions/parameters/decisions; cross-owner integration is explicit.
- **Do not reinvent:** use this owner for Project Basis/knowledge revisions and `memory/project_knowledge_owner.py` for integration.
- **Search anchors:** `project_knowledge/service.py`, `project_knowledge/apply.py`, `project_knowledge_owner.py`.

## Literature knowledge — REAL
- **What/when:** persistent literature/source curation, search and preview/backing availability for Memory/Literature.
- **Canonical files:** `backend/app/modules/memory/literature_{service,search,routes,models}.py`; `backend/app/core/literature_schema.py`.
- **Invoke/reuse:** Literature router/service/search; reuse source lifecycle and search instead of a second bibliography store.
- **I/O/persistence:** SQLite literature metadata/lifecycle plus backing references; search is a dedicated service path.
- **Preconditions:** workspace/source validity; backing availability is distinct from curation state.
- **Side effects/risk:** curation mutations persist; unavailable/stale backing must remain visible rather than silently treated as usable evidence.
- **Evidence:** backend Literature tests; `.github/browser-proof/fixtures/literature_knowledge.py` and plan `114-literature.json` provide product proof support.
- **Limitations:** backing/preview support can be unavailable while metadata remains curated; do not collapse those states.
- **Do not reinvent:** reuse Literature service/search and schema.
- **Search anchors:** `literature_service.py`, `literature_search.py`, `LITERATURE_SCHEMA_*`.

## Project Search — REAL
- **What/when:** bounded project-wide search facade over canonical project information; use for search UX/context discovery rather than adding a new index owner.
- **Canonical files:** `backend/app/modules/project_search/{service,routes,models}.py`.
- **Invoke/reuse:** Project Search router/service.
- **I/O/persistence:** read-oriented results assembled from existing canonical owners; base DB can provide FTS5 `context_records_fts` when supported.
- **Preconditions:** initialized project data; search behavior can depend on FTS availability/fallback.
- **Side effects/risk:** read path; should not imply selection into Jarvis context.
- **Evidence:** backend Project Search tests; browser-proof fixture `project_search.py` and plan `115-project-search.json`.
- **Limitations:** search is not an autonomous semantic/vector store and must not become implicit Jarvis context.
- **Do not reinvent:** route project discovery through this facade/canonical owner queries.
- **Search anchors:** `project_search/service.py`, `context_records_fts`.

## AI threads — REAL
- **What/when:** persistent workspace-scoped conversational task threads with submit/idempotency and integration into the governed AI execution path.
- **Canonical files:** `backend/app/modules/ai/thread_{models,service,routes}.py`; `backend/app/core/ai_thread_schema.py`.
- **Invoke/reuse:** AI thread routes; `thread_service.submit_interaction`; submit can carry explicit common Jarvis-context request/binding.
- **I/O/persistence:** SQLite thread/interactions plus AI job/execution provenance; request IDs support idempotency and cross-workspace isolation.
- **Preconditions:** workspace; valid task/route/token semantics; explicit Jarvis context is optional and digest-bound when supplied.
- **Side effects/risk:** submit invokes governed `run_ai_task`; external routes remain subject to egress/budget/token-flow controls.
- **Evidence:** `backend/tests/test_ai_threads.py`, `test_jarvis_context.py`, route-default consistency test, `scripts/check_ai_threads.py`.
- **Limitations:** thread UI/sidecar presentation is Area B; backend thread is not an authority bypass for domain writes.
- **Do not reinvent:** reuse thread service and AI execution instead of creating chat-specific provider calls.
- **Search anchors:** `AIThreadSubmit`, `submit_interaction`, `thread_service.py`.

## Common Jarvis context + capability/action foundation — REAL
- **What/when:** common explicit context preview/binding owner and capability registry used by threads, Coding and knowledge actions.
- **Canonical files:** `backend/app/modules/ai/jarvis_context.py`, `jarvis_context_models.py`, `jarvis_context_routes.py`; action consumers `memory/jarvis_knowledge_actions.py`, `coding/actions.py`.
- **Invoke/reuse:** `build_jarvis_context_preview`, `require_dispatchable_preview`, `PRODUCTION_ADAPTER_REGISTRY`, `PRODUCTION_CAPABILITY_REGISTRY`.
- **I/O/persistence:** builds bounded context packs from route descriptors/exact refs and returns digest/outcomes; context preview itself is read/context authority, while separate action services own bounded proposals/actions.
- **Preconditions:** registered adapter/capability, workspace, valid exact refs and expected digest for dispatch where required.
- **Side effects/risk:** context assembly is non-mutating; capability registry intentionally separates context from mutation authority. Coding/knowledge action services may create proposals through their domain owners but must not use context adapters as COMMIT/EXECUTE authority.
- **Evidence:** `backend/tests/test_jarvis_context.py`, `test_jarvis_coding_actions_123.py`, AI-thread tests.
- **Limitations:** no implicit context on browse/open; adapters are explicit and bounded.
- **Do not reinvent:** register/reuse the common context/capability foundation rather than feature-local context payloads.
- **Search anchors:** `JarvisContextAdapterRegistry`, `JarvisCapabilityRegistry`, `build_jarvis_context_preview`, `require_dispatchable_preview`.

## Provider registry / routing — REAL, with stale historical docs
- **What/when:** validated provider/model/route/fallback registry; use for all AI route resolution and concrete pricing lookup.
- **Canonical files:** `backend/app/modules/ai/provider_registry.py`, `execution_types.py`, `configs/ai_providers.yaml`.
- **Invoke/reuse:** `load_default_provider_registry`, `registry_bindings`, `resolve_model_pricing`; route classes bind to enabled models and execution classes (`synthetic`, `local_compute`, `external_provider`).
- **I/O/persistence:** YAML config + bounded environment overrides; no provider call is performed by registry parsing.
- **Preconditions:** registry version 1; valid provider/model IDs, context/output token limits, network/execution consistency; enabled external models require concrete pricing.
- **Side effects/risk:** read/config path, but route bindings determine downstream network/cost authority.
- **Evidence:** provider registry tests and consumers throughout egress/token-flow/settings.
- **Limitations:** historical `docs/0E_B2_FOUNDATION_REFACTOR_READINESS.md` says ProviderRegistry missing; this is stale relative to executable `provider_registry.py`.
- **Do not reinvent:** add provider/model configuration through the existing registry and route classes.
- **Search anchors:** `ProviderRegistry`, `parse_provider_registry`, `registry_bindings`, `configs/ai_providers.yaml`.

## Governed external AI egress / sensitivity / budget / token-flow — REAL
- **What/when:** policy spine around any external-provider execution: authority, sanitization, confirmation/revalidation, persistence, budget/pricing, continuation and usage/token-flow accounting.
- **Canonical files:** `backend/app/modules/ai/egress_{authority,policy,sanitizer,confirmation_core,lifecycle,persistence,runtime,service,spine}.py`; `budget.py`, `costs.py`; `token_flow_*.py`; `backend/app/core/{egress_schema,token_flow_schema,sensitivity_schema}.py`.
- **Invoke/reuse:** AI execution/egress service and token-flow transaction/continuation helpers; provider registry supplies concrete bindings/pricing.
- **I/O/persistence:** SQLite egress/token-flow/usage lifecycle plus AI jobs/events; provider calls only after closed checks. Pricing is concrete per external model.
- **Preconditions:** enabled external binding, network authority, sensitivity/egress policy, secret ref resolution where required, budget/token caps and any required confirmation/revalidation.
- **Side effects/risk:** HIGH: can transmit sanitized content externally and incur cost; persistence/audit is part of the control path, not optional logging.
- **Evidence:** extensive backend egress/token-flow/budget tests and provider smoke utilities.
- **Limitations:** provider availability is runtime-dependent; registry presence does not prove credentials/network/provider health. Never treat JSON validity as semantic authorization.
- **Do not reinvent:** no direct SDK/provider calls from product features; route through this governed spine.
- **Search anchors:** `egress_runtime.py`, `egress_authority.py`, `token_flow_external_transaction.py`, `resolve_model_pricing`, `usage`.

## Development Roadmap + Calendar — REAL
- **What/when:** Development-domain roadmap/scheduling/reconciliation views and mutations over the existing Development owner.
- **Canonical files:** `backend/app/modules/development/{service,routes,models,time,links}.py`; `backend/app/core/development_schema.py`.
- **Invoke/reuse:** Development router/service; roadmap timeline/calendar are reserved SPA routes but backend data comes from Development service.
- **I/O/persistence:** SQLite development records/links; time normalization helper centralizes date/time behavior.
- **Preconditions:** initialized workspace/development schema and valid lifecycle/link references.
- **Side effects/risk:** domain mutations persist; scheduling/reconciliation must use this owner, not a parallel calendar store.
- **Evidence:** backend Development/Roadmap/Calendar tests; browser-proof `116-roadmap-calendar.json`.
- **Limitations:** external calendar-provider sync is not established by these modules; treat product calendar as JarvisOS Development data unless runtime evidence says otherwise.
- **Do not reinvent:** reuse Development service/time/link helpers.
- **Search anchors:** `development/service.py`, `development/time.py`, `development/links.py`.

## Brainstorm backend — REAL
- **What/when:** persistent Development brainstorm sessions/items and promotion/linkage foundation.
- **Canonical files:** `backend/app/modules/development/brainstorm_{service,routes,models}.py`; `backend/app/core/brainstorm_schema.py`.
- **Invoke/reuse:** Brainstorm router/service.
- **I/O/persistence:** SQLite brainstorm schema with Development linkage.
- **Preconditions:** workspace and valid linked Development records where used.
- **Side effects/risk:** brainstorm mutations persist but remain distinct from authoritative promotion targets until explicit promotion/action path.
- **Evidence:** backend brainstorm tests; browser-proof `117-brainstorm.json`.
- **Limitations:** brainstorm content is not automatically canonical engineering/project knowledge.
- **Do not reinvent:** reuse brainstorm owner and explicit promotion/link paths.
- **Search anchors:** `brainstorm_service.py`, `BRAINSTORM_SCHEMA_*`.

## Coding repository truth / runtime truth / pipeline state / bounded actions — REAL
- **What/when:** product-facing Coding backend for repository observation, local runtime observation, delivery-pipeline projection and bounded Jarvis Coding actions.
- **Canonical files:** `backend/app/modules/coding/{repository_truth,runtime_truth,runtime_routes,pipeline_state,actions}.py`.
- **Invoke/reuse:** Coding runtime router exposes repository/runtime surfaces; startup calls `capture_runtime_snapshot`; actions consume common Jarvis context and governed AI execution.
- **I/O/persistence:** repository truth reads Git/repo state; runtime truth captures host/process/service observations and startup snapshot; pipeline state projects existing delivery state rather than owning a second queue; action service may produce bounded proposals/actions under existing authority.
- **Preconditions:** repository/runtime paths and tools available; common context/action validation for Jarvis actions.
- **Side effects/risk:** observation paths are read-oriented; action paths must preserve exact authority and do not replace GitHub/STATUS/delivery control-plane ownership.
- **Evidence:** Coding backend tests including repository/runtime/pipeline/action suites; browser-proof `140-coding.json`; `test_jarvis_coding_actions_123.py`.
- **Limitations:** runtime snapshot failure is intentionally represented as unavailable and never blocks app startup. Product pipeline projection is not a canonical scheduler/store.
- **Do not reinvent:** use repository_truth/runtime_truth/pipeline_state and common Coding actions rather than new repo/runtime/pipeline owners.
- **Search anchors:** `capture_runtime_snapshot`, `repository_truth.py`, `pipeline_state.py`, `coding/actions.py`.

## Remaining coverage
- Inspect AI `routes.py`/`execution.py` and provider adapters deeply enough to map the exact gateway execution seam and REAL/PARTIAL adapters.
- Inspect settings/provider projections and sidecar backend/thread integration contracts.
- Inspect Model Dossier/model-version selection implementation and tests.
- Inspect backup/restore/product-data ownership and explicitly classify absence/partial paths.
- Inspect full token-flow usage-ledger symbols/tests and sensitivity routes for precise persisted state/limitations.
- Inspect Development/Coding action-service details and any spec-122 implementation that lands on fresh master in later runs.
- Cross-check backend test inventory for every mapped capability; then flag additional stale docs/gaps and only then mark COMPLETE.
