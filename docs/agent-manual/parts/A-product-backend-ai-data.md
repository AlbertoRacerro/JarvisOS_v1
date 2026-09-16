# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline inspected from fresh `master` at `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Labels below describe executable source/runtime contracts, not merged-spec intent. Issue #656 common schema is compressed into dense bullets.

> File-coverage recovery note (2026-09-16): the capability map below was previously complete at subsystem level, but issue #656 now requires literal tracked-file accounting. Completion is reopened until every owned tracked file is represented in the explicit ledger and each `READ` row has been content-inspected from fresh repository source.

## FastAPI composition + process startup — REAL
- **What/when:** canonical backend composition root; start here to discover mounted product surfaces and lifecycle owners.
- **Canonical files:** `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/spa_static.py`.
- **Invoke/reuse:** `create_app`, exported `app`; lifespan creates local-AI lifecycle, captures Coding runtime truth, reconciles stranded runner jobs and schedules live-owner rechecks.
- **I/O/persistence:** `app.state` runtime snapshot; reconciliation may mutate runner persistence; SPA serves `frontend/dist` only when present.
- **Preconditions:** settings/data-root/SQLite; runtime snapshot deliberately fails open to unavailable; transient SQLite locks are retried for abandoned owners.
- **Authority/risk:** composition is authoritative wiring; a module existing does not prove a route is mounted.
- **Evidence:** `backend/app/main.py` plus startup/domain route tests.
- **Limitations:** Coding repository truth is mounted through Coding runtime router, not a separate root router.
- **Do not reinvent:** mount through existing router/service boundaries and this composition root.
- **Search anchors:** `create_app`, `lifespan`, `_reconcile_after_live_owners_exit`, `_SPA_RESERVED_ROOT_CLIENT_ROUTES`.

## Data root + SQLite + migrations — REAL
- **What/when:** single local-first product-data root and SQLite/bootstrap owner.
- **Canonical files:** `backend/app/core/paths.py`, `backend/app/core/database.py`, `backend/app/core/*_schema.py`.
- **Invoke/reuse:** `build_paths`, `ensure_data_directories`, `get_database_path`, `open_sqlite_connection`, `initialize_database`, `get_database_info`.
- **I/O/persistence:** `JarvisPaths` owns DB/workspaces/artifacts/logs/secrets directories; SQLite enables foreign keys, 5s busy timeout and WAL. Bootstrap composes base + CAD-link, sensitivity, egress, token-flow, grade, AI-thread, Project Knowledge, Literature, Development and Brainstorm schema/migrations; FTS5 is conditional/backfilled.
- **Preconditions:** writable data root; SQLite; FTS optional.
- **Authority/risk:** high persistence authority; application-managed migrations record IDs and tolerate only duplicate-column ALTER conflicts.
- **Evidence:** database/bootstrap/domain persistence tests.
- **Limitations:** no Alembic; FTS availability varies by SQLite build.
- **Do not reinvent:** no second product DB/data-root; reuse connection/bootstrap/schema registry.
- **Search anchors:** `open_sqlite_connection`, `initialize_database`, `_record_schema_migrations`, `SCHEMA_MIGRATION_RECORDS`.

## Canonical engineering MemoryStore — REAL
- **What/when:** lifecycle owner for engineering assumptions/parameters/decisions and AI-origin proposals.
- **Canonical files:** `backend/app/modules/memory/{service,models,routes,replacement}.py`, `backend/app/core/schema.py`.
- **Invoke/reuse:** Memory routes/service, especially `create_proposal`; `_TABLE_BY_KIND` maps record kinds to canonical tables.
- **I/O/persistence:** SQLite; proposed/accepted/rejected/superseded; AI proposals require existing `ai_jobs` provenance. Parameter replacement integrates freshness invalidation.
- **Preconditions:** workspace; valid provenance/replacement identities.
- **Authority/risk:** domain-authoritative lifecycle writes; replacement can invalidate downstream freshness; transactional `BEGIN IMMEDIATE` paths.
- **Evidence:** memory/replacement/freshness tests.
- **Limitations:** distinct owner from Project Knowledge and Literature.
- **Do not reinvent:** reuse lifecycle/replacement machinery for engineering records.
- **Search anchors:** `_TABLE_BY_KIND`, `_create_proposal_in_transaction`, `validate_parameter_replacement_proposal`, `persist_freshness_invalidation`.

## Project Knowledge / Project Basis — REAL
- **What/when:** canonical curated project-basis/source/revision/apply owner.
- **Canonical files:** `backend/app/modules/project_knowledge/{service,apply,revision_lifecycle,routes,models}.py`, `backend/app/core/project_knowledge_schema.py`, `backend/app/modules/memory/project_knowledge_owner.py`.
- **Invoke/reuse:** `/project-knowledge` routes/services; explicit apply/revision lifecycle.
- **I/O/persistence:** SQLite records/revisions/backing-source metadata.
- **Preconditions:** workspace + valid lifecycle/version expectations.
- **Authority/risk:** curation/apply mutates canonical knowledge; revision expectations guard stale writes.
- **Evidence:** backend Project Knowledge tests and product proof fixtures.
- **Limitations:** not MemoryStore assumptions/parameters/decisions; integration is explicit.
- **Do not reinvent:** use this owner and `project_knowledge_owner.py` bridge.
- **Search anchors:** `project_knowledge/service.py`, `project_knowledge/apply.py`, `project_knowledge_owner.py`.

## Literature knowledge — REAL
- **What/when:** persistent literature/source curation, search, preview and backing-availability semantics.
- **Canonical files:** `backend/app/modules/memory/literature_{service,search,routes,models}.py`, `backend/app/core/literature_schema.py`.
- **Invoke/reuse:** Literature router/service/search.
- **I/O/persistence:** SQLite metadata/lifecycle/backing refs.
- **Preconditions:** workspace/source identity; backing availability is separate from curation state.
- **Authority/risk:** mutations persist; stale/unavailable backing must remain explicit.
- **Evidence:** backend Literature tests; browser-proof fixture/plan `114-literature.json`.
- **Limitations:** curated metadata can exist while backing/preview is unavailable.
- **Do not reinvent:** no second bibliography store.
- **Search anchors:** `literature_service.py`, `literature_search.py`, `LITERATURE_SCHEMA_*`.

## Model Dossier / model-version evidence projection — REAL
- **What/when:** bounded workspace-isolated read projection joining model/version identity to runs, artifacts and evidence; use for model dossier/index/search rather than a parallel model catalog.
- **Canonical files:** `backend/app/modules/modeling/model_dossier.py`, `model_dossier_search.py`, `dossier_models.py`, `routes.py`.
- **Invoke/reuse:** Modeling routes expose dossier index/detail/search; `model_dossier.py` performs SQLite joins/projections.
- **I/O/persistence:** read-only projection over canonical modeling/run/artifact/evidence persistence; returns explicit model/version identity and evidence refs/states.
- **Preconditions:** workspace/model identities exist; referenced evidence/artifacts may independently be missing/stale.
- **Authority/risk:** read/context authority only; workspace isolation is mandatory.
- **Evidence:** backend modeling/dossier tests plus `frontend/tests/113-model-dossier.mjs`; Jarvis knowledge adapter has sensitivity-authority tests.
- **Limitations:** unavailable/stale evidence is represented, not repaired or silently promoted to valid evidence.
- **Do not reinvent:** reuse dossier projection/search and canonical model-version identity.
- **Search anchors:** `ModelDossierDetail`, `ModelDossierVersionIdentity`, `model_dossier.py`, `model_dossier_search.py`.

## Project Search — REAL
- **What/when:** bounded project-wide search facade over canonical owners; use for discovery/context selection.
- **Canonical files:** `backend/app/modules/project_search/{service,routes,models}.py`.
- **Invoke/reuse:** Project Search router/service.
- **I/O/persistence:** read projection; FTS5 `context_records_fts` when available with fallback behavior.
- **Preconditions:** initialized project data; SQLite FTS capability may vary.
- **Authority/risk:** read-only; search/open does not imply Jarvis-context selection.
- **Evidence:** backend Project Search tests; browser-proof `115-project-search.json`.
- **Limitations:** not a vector/semantic-store owner.
- **Do not reinvent:** query canonical owners through this facade.
- **Search anchors:** `project_search/service.py`, `context_records_fts`.

## AI threads + Jarvis sidecar backend seam — REAL
- **What/when:** persistent workspace-scoped conversational threads/interactions; this is also the backend seam consumed by the Jarvis sidecar rather than a second sidecar chat backend.
- **Canonical files:** `backend/app/modules/ai/thread_{models,service,routes}.py`, `backend/app/core/ai_thread_schema.py`, `backend/app/modules/ai/jarvis_context*.py`.
- **Invoke/reuse:** thread routes; `submit_interaction`; optional explicit digest-bound common Jarvis context.
- **I/O/persistence:** SQLite threads/interactions + AI job/execution provenance; request IDs provide idempotency and workspace isolation.
- **Preconditions:** workspace + valid task/route/context identities.
- **Authority/risk:** submit invokes governed AI execution; sidecar does not bypass domain mutation authority.
- **Evidence:** `backend/tests/test_ai_threads.py`, `test_jarvis_context.py`, route-default consistency tests, `scripts/check_ai_threads.py`.
- **Limitations:** presentation/UX belongs Area B; no separate sidecar backend/store was found.
- **Do not reinvent:** sidecar/chat features should reuse threads + common context + governed execution.
- **Search anchors:** `AIThreadSubmit`, `submit_interaction`, `thread_service.py`, `jarvis_context_routes.py`.

## Common Jarvis context + capability/action foundation — REAL
- **What/when:** explicit context preview/binding and capability registry shared by threads, knowledge and Coding actions.
- **Canonical files:** `backend/app/modules/ai/jarvis_context.py`, `jarvis_context_models.py`, `jarvis_context_routes.py`; consumers `memory/jarvis_knowledge_actions.py`, `coding/actions.py`.
- **Invoke/reuse:** `build_jarvis_context_preview`, `require_dispatchable_preview`, `PRODUCTION_ADAPTER_REGISTRY`, `PRODUCTION_CAPABILITY_REGISTRY`.
- **I/O/persistence:** bounded context blocks + digest/source manifest; preview is non-mutating, actions remain separate owners.
- **Preconditions:** registered adapter/capability, workspace, exact refs; dispatch requires expected digest where defined.
- **Authority/risk:** context authority only; adapters must not become COMMIT/EXECUTE authority.
- **Evidence:** Jarvis context, AI-thread, knowledge-action and Coding-action tests.
- **Limitations:** no implicit context on browse/open.
- **Do not reinvent:** register adapters/capabilities here instead of feature-local context formats.
- **Search anchors:** `JarvisContextAdapterRegistry`, `JarvisCapabilityRegistry`, `build_jarvis_context_preview`, `require_dispatchable_preview`.

## AI gateway + provider registry/routing/adapters — REAL, runtime availability conditional
- **What/when:** canonical AI execution facade and validated provider/model/route/fallback registry; all product AI execution should enter here/governed execution, not direct SDK calls.
- **Canonical files:** `backend/app/modules/ai/gateway.py`, `execution.py`, `provider_registry.py`, `execution_types.py`, provider adapter modules under `backend/app/modules/ai/`, `configs/ai_providers.yaml`.
- **Invoke/reuse:** `AIGateway.run_task`, `run_ai_task`, `load_default_provider_registry`, `registry_bindings`, `resolve_model_pricing`; concrete provider adapters execute selected bindings. Fake/synthetic adapters are test/development seams, not production-provider evidence.
- **I/O/persistence:** registry YAML + bounded env overrides; execution produces `ai_jobs`/route provenance and downstream egress/token-flow records as applicable.
- **Preconditions:** valid enabled binding; local compute or external network/credentials according to execution class; external models require concrete pricing.
- **Authority/risk:** route binding selects compute/network/cost path; registry parse itself performs no provider call.
- **Evidence:** provider-registry/gateway/execution tests and provider smoke utilities.
- **Limitations:** configured provider/model != healthy credentials/network/quota. Synthetic success != external provider health.
- **Stale docs:** `docs/0E_B2_FOUNDATION_REFACTOR_READINESS.md` states ProviderRegistry missing; executable `provider_registry.py` supersedes that claim.
- **Do not reinvent:** no feature-local provider routing or direct SDK calls.
- **Search anchors:** `AIGateway`, `run_ai_task`, `ProviderRegistry`, `parse_provider_registry`, `registry_bindings`, `configs/ai_providers.yaml`.

## Provider/settings/status projections — REAL
- **What/when:** product-safe AI settings and canonical provider/status projection over the same gateway/registry authority.
- **Canonical files:** `backend/app/modules/ai/routes.py`, `settings.py`, `models.py`, `gateway.py`.
- **Invoke/reuse:** `GET /ai/settings`, `PUT /ai/settings`, `GET /ai/status`, `GET /ai/provider-settings`; `ensure_ai_settings`, `update_ai_settings`, `project_canonical_ai_status`, `get_provider_settings`.
- **I/O/persistence:** settings owner persists/configures allowed AI settings; status/provider-settings are projections from `AIGateway().status()` and canonical settings/registry.
- **Preconditions:** initialized settings/registry; runtime provider health may be unavailable.
- **Authority/risk:** settings mutation changes routing/runtime policy within its bounded schema; projection must not expose provider secrets.
- **Evidence:** route/settings/status tests; routes explicitly call gateway status rather than a second provider owner.
- **Limitations:** status normalizes product-facing blocking reasons; it is not proof of external entitlement beyond observed runtime state.
- **Do not reinvent:** Settings UI/services should consume these projections.
- **Search anchors:** `read_ai_settings`, `read_ai_status`, `read_ai_provider_settings`, `project_canonical_ai_status`.

## Sensitivity labels + sanitization authority — REAL
- **What/when:** persisted content-sensitivity authority used by context/egress to fail closed on unknown or disallowed data and to track sanitized derivatives.
- **Canonical files:** `backend/app/modules/ai/sensitivity.py`, `backend/app/core/sensitivity_schema.py`, egress sanitizer/policy modules.
- **Invoke/reuse:** sensitivity service functions and egress/context consumers; labels are tied to workspace, subject ref and content digest with prior-label lineage.
- **I/O/persistence:** SQLite `sensitivity_labels` and `sanitized_derivatives`; labels are immutable/history-oriented rather than an untracked boolean flag.
- **Preconditions:** workspace + exact subject/content digest; legacy unlabelled records resolve conservatively.
- **Authority/risk:** HIGH privacy boundary: unknown/unlabelled data is withheld rather than assumed safe; sanitization derivatives carry provenance.
- **Evidence:** `backend/tests/test_ai_sensitivity_context.py`, egress schema/policy tests, Jarvis knowledge sensitivity-authority tests.
- **Limitations:** label presence is content-version specific; changed content requires current authority.
- **Do not reinvent:** reuse sensitivity owner and sanitizer; never infer sensitivity from UI state or model output.
- **Search anchors:** `sensitivity_labels`, `sanitized_derivatives`, `sensitivity.py`, `test_legacy_unlabelled_record_is_unknown_and_withheld`.

## Governed external egress + budget + token-flow/usage ledger — REAL
- **What/when:** closed policy spine for external-provider transmission/cost: authority, sanitization, confirmation/revalidation, persistence, budget reservation, continuation and usage reconciliation.
- **Canonical files:** `backend/app/modules/ai/egress_{authority,policy,sanitizer,confirmation_core,lifecycle,persistence,runtime,service,spine}.py`, `budget.py`, `costs.py`, `token_flow_*.py`, `backend/app/core/{egress_schema,token_flow_schema,sensitivity_schema}.py`.
- **Invoke/reuse:** governed AI execution/egress service; token-flow external transaction/continuation helpers; pricing via provider registry.
- **I/O/persistence:** SQLite egress packets/decisions/attempts, budget reservations, token-flow/usage and `ai_jobs` route provenance. Verified provider token usage is priced against concrete registry pricing and reconciled to persisted attempts/jobs; missing/inconsistent actual usage fails conservatively to reserved upper bounds rather than inventing lower spend.
- **Preconditions:** enabled external binding, network authority, current sensitivity/egress decision, secret ref resolution, budget/token caps and required confirmation/revalidation.
- **Authority/risk:** HIGH: may transmit sanitized content and incur cost; persistence/audit is part of authorization, not optional logging.
- **Evidence:** extensive egress/token-flow/budget/schema/continuation tests and provider smoke utilities.
- **Limitations:** provider availability/quota is runtime dependent; JSON/schema validity alone is not semantic authorization.
- **Do not reinvent:** all external AI calls must traverse this spine.
- **Search anchors:** `egress_runtime.py`, `egress_authority.py`, `token_flow_external_transaction.py`, `resolve_model_pricing`, `egress_attempts`, `ai_jobs`.

## Development Roadmap + Calendar — REAL
- **What/when:** Development-domain roadmap, scheduling/reconciliation views and mutations over one Development owner.
- **Canonical files:** `backend/app/modules/development/{service,routes,models,time,links}.py`, `backend/app/core/development_schema.py`.
- **Invoke/reuse:** Development router/service; `time.py` normalizes time semantics; `links.py` owns relationships.
- **I/O/persistence:** SQLite Development records/links.
- **Preconditions:** workspace/schema + valid lifecycle/link refs.
- **Authority/risk:** mutations persist; no parallel calendar store.
- **Evidence:** backend Development/Roadmap/Calendar tests; browser-proof `116-roadmap-calendar.json`.
- **Limitations:** no evidence of external calendar-provider sync; product Calendar is JarvisOS Development data.
- **Do not reinvent:** reuse Development service/time/link helpers.
- **Search anchors:** `development/service.py`, `development/time.py`, `development/links.py`.

## Brainstorm backend — REAL
- **What/when:** persistent Development brainstorm sessions/items and explicit promotion/linkage foundation.
- **Canonical files:** `backend/app/modules/development/brainstorm_{service,routes,models}.py`, `backend/app/core/brainstorm_schema.py`.
- **Invoke/reuse:** Brainstorm router/service.
- **I/O/persistence:** SQLite brainstorm records with Development linkage.
- **Preconditions:** workspace and valid linked records.
- **Authority/risk:** brainstorm writes persist but are not automatically canonical project/engineering knowledge.
- **Evidence:** backend Brainstorm tests; browser-proof `117-brainstorm.json`.
- **Limitations:** promotion remains explicit.
- **Do not reinvent:** reuse brainstorm owner/link/promotion seams.
- **Search anchors:** `brainstorm_service.py`, `BRAINSTORM_SCHEMA_*`.

## Development multi-record Jarvis actions (spec-122 target) — DEFERRED on inspected master
- **What/when:** requested future explicit multi-record Development CONTEXT/PROPOSE scheduling/reconciliation/Roadmap/promotion action layer.
- **Canonical files:** none found in executable Development runtime on inspected master beyond existing Development/Brainstorm owners and generic Jarvis context foundation.
- **Invoke/reuse:** no executable spec-122 action service found; do not infer one from merged/planning/readiness prose.
- **I/O/persistence / authority:** N/A until runtime lands; underlying Development persistence remains REAL.
- **Evidence:** source search of Development/Jarvis action surfaces; existing action implementations are knowledge/Coding-specific.
- **Limitations:** DEFERRED means future builders must re-check fresh master before assuming absence.
- **Do not reinvent:** when implemented, it must reuse Development owner + common context/capability registry rather than a second queue/store.
- **Search anchors:** `backend/app/modules/development`, `PRODUCTION_CAPABILITY_REGISTRY`, `spec 122`.

## Coding repository truth / runtime truth / pipeline projection — REAL
- **What/when:** product-facing repository observation, host/runtime observation and projection of existing delivery state.
- **Canonical files:** `backend/app/modules/coding/{repository_truth,runtime_truth,runtime_routes,pipeline_state}.py`.
- **Invoke/reuse:** Coding runtime routes/services; startup `capture_runtime_snapshot`.
- **I/O/persistence:** repository truth reads Git/repo state; runtime truth captures host/process/service observations; pipeline state projects existing delivery state rather than owning a second queue.
- **Preconditions:** repository/runtime paths and required local tools.
- **Authority/risk:** read-oriented; runtime snapshot failure becomes explicit unavailable and does not block app startup.
- **Evidence:** repository/runtime/pipeline backend tests; browser-proof `140-coding.json`.
- **Limitations:** projection is not canonical scheduler/lifecycle authority; GitHub/STATUS/delivery control plane remain owners.
- **Do not reinvent:** reuse truth/projection services.
- **Search anchors:** `capture_runtime_snapshot`, `repository_truth.py`, `runtime_truth.py`, `pipeline_state.py`.

## Coding inspect + modification proposal actions — REAL, PROPOSE-only
- **What/when:** deterministic exact-head inspection and AI-assisted bounded code-change proposal generation; use when product Jarvis should inspect/suggest, not mutate repository state.
- **Canonical files:** `backend/app/modules/coding/actions.py`, `repository_truth.py`, common Jarvis context and AI execution.
- **Invoke/reuse:** `CodingActionsService.inspect`, `suggest_modification`; request freezes `repository/base_ref/base_sha/target_paths`, optionally digest-binds added Jarvis context.
- **I/O/persistence:** inspect returns exact file evidence; suggest calls governed `run_ai_task(route_class="local:coder")`, validates closed JSON schema/diffs, then rechecks ref SHA before returning `state=proposed` with AI-job provenance. No patch application/commit/push occurs here.
- **Preconditions:** exact 40-char base SHA must match repository truth; 1–16 bounded POSIX text targets; protected governance/data/secrets/binary paths denied; evidence must be complete/current.
- **Authority/risk:** PROPOSE only. Diff validator forbids creation/deletion, binary/mode/rename/copy/submodule changes and path escape; stale target/provider failure returns bounded refusal.
- **Evidence:** `backend/tests/test_jarvis_coding_actions_123.py` and repository-truth tests.
- **Limitations:** model output is advisory until deterministic schema/path/diff validation; no COMMIT/EXECUTE authority.
- **Do not reinvent:** use this service for code suggestions; delivery mutation belongs existing delivery control plane.
- **Search anchors:** `CodingActionsService`, `_freeze_target`, `_admit_paths`, `_validate_diff`, `_validate_generated`, `MAX_PROPOSAL_BYTES`.

## Product-data backup / verify / restore — REAL, operator/development primitive
- **What/when:** snapshot, verify and restore the JarvisOS data root, including SQLite-consistent data and path rebasing; use for product-data recovery rather than ad-hoc file copies.
- **Canonical files:** `scripts/jarvisos_data_root.py` and its `data_root_recovery` helpers/support.
- **Invoke/reuse:** CLI/helpers `create_snapshot`, verification functions, `restore_snapshot`, `rebase_absolute_path`, `sha256_file`.
- **I/O/persistence:** reads source data root, writes snapshot manifest/files, verifies hashes, restores into destination and rebases supported absolute paths.
- **Preconditions:** filesystem access, valid snapshot/manifest, safe destination; restore is destructive/high-authority relative to target data root.
- **Authority/risk:** HIGH local data authority; verification and path-safety checks must precede restore.
- **Evidence:** `backend/tests/test_data_root_restore_adversarial.py` and recovery support fixtures cover adversarial restore behavior.
- **Limitations:** this is data-root recovery, not a cloud backup service or DB replication system.
- **Do not reinvent:** use the recovery primitive for whole-product local data backup/restore.
- **Search anchors:** `scripts/jarvisos_data_root.py`, `create_snapshot`, `restore_snapshot`, `MANIFEST_NAME`, `test_data_root_restore_adversarial.py`.

## Reusable backend helpers worth routing to
- **SQLite/data root:** `open_sqlite_connection`, `build_paths`, schema registries.
- **Exact context:** `JarvisContextAdapterRegistry`, `require_dispatchable_preview`, context digests/source manifests.
- **AI routing/cost:** `AIGateway`, `run_ai_task`, `ProviderRegistry`, `resolve_model_pricing`.
- **Safety/cost:** sensitivity owner, egress authority/sanitizer, budget reservations, token-flow transaction/continuation.
- **Domain time/linking:** `development/time.py`, `development/links.py`.
- **Repository safety:** `RepositoryTruthService`, Coding `_freeze_target`/path+diff validators.
- **Recovery:** `jarvisos_data_root.py` / data-root recovery helpers.

## Gaps / duplication / stale documentation discovered
- Historical foundation prose claiming ProviderRegistry is missing is stale; executable registry/routing exists.
- Provider configuration is not provider health: credentials/network/quota remain runtime conditions.
- Synthetic/fake adapters are test/development seams and must not be cited as proof of external-provider execution.
- Development spec-122 multi-record Jarvis action service was not executable on the inspected master; existing Development storage plus generic Jarvis foundation are REAL, the specific action layer is DEFERRED.
- Jarvis sidecar does not own a second backend/thread store; it reuses AI threads/common context/governed execution.
- Coding pipeline state is a projection, not a second canonical delivery queue; Coding actions are bounded inspect/PROPOSE, not repository mutation authority.
- Product-data recovery exists as a local data-root snapshot/verify/restore primitive; do not describe it as cloud backup/replication.

## EXPLICIT FILE COVERAGE LEDGER

Literal file accounting is being rebuilt from fresh `master`. `READ` means the file contents were opened and inspected in this mapping pass; rows are not inferred from path names or prior PR #660.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary; docstring declares the agent-registry module boundary and exports no hidden runtime behavior. |
| `backend/app/modules/agents/base.py` | READ | Defines immutable `AgentCapability` metadata and the minimal `Agent` protocol (`name`, `capabilities`); no execution loop or persistence. |
| `backend/app/modules/agents/registry.py` | READ | In-memory `AgentRegistry`: name-keyed registration with overwrite-by-name semantics and deterministic sorted name listing; no persistence/provider authority. |

### Remaining coverage
- Fresh backend tree confirms additional owned files under `app/api`, `app/core`, and the owned module families (`ai`, `coding`, `dev_message_route`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`) plus owned tests/configs/schemas/helpers/fixtures/migrations. These must each be reopened and entered before completion.
- PR #660 remains hints-only: no A-scope row from it may be imported without reopening the corresponding source file.
- Re-scan fresh tracked tree after ledger expansion to compute the defensible exact final count.

UNACCOUNTED_FILES: >0 (exact count pending full owned-scope tree enumeration; completion is intentionally blocked)
