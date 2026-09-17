# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Classifications are executable-source/runtime claims, not spec-derived claims. Literal file accounting is authoritative for completion.

## Capability map

### FastAPI composition + startup — REAL
- **What/when:** canonical backend composition root and lifecycle owner.
- **Canonical files:** `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/spa_static.py`.
- **Invocation/reuse:** `create_app`, exported `app`, `lifespan`; mount product routers here rather than creating a parallel app.
- **I/O/persistence:** `app.state` carries local-AI lifecycle and Coding startup runtime snapshot; startup reconciles stranded runner jobs; SPA mounts only when `frontend/dist` exists.
- **Preconditions / side effects / risk:** configured data root and runtime dependencies; composition determines which routes are live; startup reconciliation mutates runner persistence.
- **Evidence / limitations:** direct source inspection; module existence alone does not prove route mounting.
- **Do not reinvent / anchors:** reuse composition/lifespan and `SpaStaticFiles`; `create_app`, `lifespan`, `_reconcile_after_live_owners_exit`, `derive_reserved_roots`.

### Settings + system/health projection — REAL
- **What/when:** environment-backed process settings and safe health/system/bootstrap endpoints.
- **Canonical files:** `backend/app/core/config.py`, `backend/app/api/health.py`, `backend/app/api/system.py`.
- **Invocation/reuse:** `get_settings`; `GET /health`, `GET /system/info`, `POST /system/initialize`.
- **I/O/persistence / authority:** initialization bootstraps canonical storage and AI settings; health/info are projections. Provider configuration is not proof of credential/network/quota health.
- **Do not reinvent / anchors:** consume projections instead of exposing raw env/secrets; `get_settings`, `system_info`, `initialize_system`.

### Data root + SQLite + migrations — REAL
- **What/when:** single local-first product-data root and SQLite/bootstrap owner.
- **Canonical files:** `backend/app/core/paths.py`, `database.py`, `bootstrap.py`, `schema.py`, domain `*_schema.py` files.
- **Invocation/reuse:** `build_paths`, `ensure_data_directories`, `open_sqlite_connection`, `initialize_database`, `get_database_info`.
- **I/O/persistence:** canonical SQLite plus workspace/artifact/log/secret directories; app-managed migrations and conditional FTS5; SQLite uses foreign keys, WAL and 5 s busy timeout.
- **Authority/risk:** schema bootstrap/migrations mutate canonical DB; `initialize_storage` also ensures AI settings and may seed default workspace.
- **Limitations:** no Alembic; FTS depends on SQLite build; additive migrations tolerate duplicate-column cases and record migrations explicitly.
- **Do not reinvent / anchors:** no second product DB/data root; `SCHEMA_MIGRATION_RECORDS`, `initialize_database`, `_sqlite_fts5_available`.

### Canonical engineering MemoryStore — REAL
Canonical assumptions/parameters/decisions and AI-origin proposal/replacement lifecycle in `backend/app/modules/memory/*` plus `backend/app/core/schema.py`. Domain-authoritative writes can invalidate downstream freshness. Reuse proposal/replacement machinery; do not create a second engineering-record store.

### Project Knowledge / Project Basis — REAL
Curated source/revision/apply owner in `backend/app/modules/project_knowledge/*`, `backend/app/core/project_knowledge_schema.py`, and the explicit Memory bridge. Apply/revision operations mutate canonical knowledge with stale-write guards. This is distinct from MemoryStore engineering-record ownership.

### Literature knowledge — REAL
Persistent literature source/claim/datum curation under `backend/app/modules/memory/literature_*` and `backend/app/core/literature_schema.py`. Source states are `raw/review/accepted`; entries are typed `claim/datum`, support locators/context, and can bind artifacts. Curated metadata can remain valid while backing content is unavailable; do not create another bibliography store.

### Model Dossier — REAL
Workspace-isolated read projection joining canonical model/version identity to runs, artifacts and evidence under `backend/app/modules/modeling/*`. Missing/stale evidence is represented explicitly rather than silently repaired/promoted.

### Project Search — REAL
Bounded read/search facade over canonical owners under `backend/app/modules/project_search/*`; FTS5 where available with fallback behavior. Search/open is discovery only and does not implicitly bind Jarvis context.

### AI threads + Jarvis sidecar backend seam — REAL
Persistent workspace-scoped threads/interactions under `backend/app/modules/ai/thread_*`; optional explicit digest-bound Jarvis context; submit enters governed AI execution. Schema binds every interaction uniquely to an `ai_flows` row and tracks `reserved/dispatching/captured/capture_failed`. No second sidecar thread/backend store found.

### Common Jarvis context + capability/action foundation — REAL
`jarvis_context*.py` provides explicit context preview/binding, adapter/capability registries, source manifests and digests. Context authority is separate from domain COMMIT/EXECUTE authority; browse/open does not implicitly select context.

### AI gateway + provider registry/routing/adapters — REAL, availability conditional
`AIGateway`/`run_ai_task` plus validated provider registry/bindings are canonical execution. Concrete adapters are execution paths; fake/synthetic adapters are test/development seams. Registry configuration is not provider health. Historical prose claiming ProviderRegistry is absent is stale.

### Provider/settings/status projections — REAL
`/ai/settings`, `/ai/status`, `/ai/provider-settings` project canonical settings/gateway/registry authority. Settings mutation is bounded; projections must not expose provider secrets.

### Sensitivity + governed egress/budget/token flow — REAL
Persisted sensitivity labels/sanitized derivatives feed fail-closed external-egress policy. External transmission/cost require current authority, sanitization, budget/token caps, persistence and usage reconciliation. Missing/inconsistent actual usage is handled conservatively. Do not bypass with direct SDK calls.

### Development Roadmap + Calendar + Brainstorm — REAL
Roadmap schema persists typed items, lifecycle/status/priority, date constraints, dependencies and object links; calendar allocations enforce positive intervals and may bind roadmap items. Brainstorm persists raw records, versioned ideas, discussions, explicit promotions and idempotency. Brainstorm content is not automatically canonical engineering knowledge; promotion remains explicit.

### Development multi-record Jarvis actions (spec-122 target) — DEFERRED on inspected baseline
No executable spec-122 multi-record Development CONTEXT/PROPOSE service was found on the inspected baseline. Underlying Development storage and generic Jarvis foundation are REAL. Re-check fresh runtime before assuming continued absence; do not infer implementation from spec prose.

### Coding repository truth / runtime truth / pipeline projection — REAL
`backend/app/modules/coding/{repository_truth,runtime_truth,runtime_routes,pipeline_state}.py` provide repository/host/runtime observations and projection of existing delivery state. Pipeline state is not a second canonical delivery queue.

### Coding inspect + modification proposal actions — REAL, PROPOSE-only
`CodingActionsService` freezes exact repository/base SHA/target evidence, invokes governed coder AI, validates closed output/diff constraints, then rechecks head before returning a proposal. It does not apply patches, commit or push; model output remains advisory until deterministic validation.

### Product-data backup / verify / restore — REAL local recovery primitive
`scripts/jarvisos_data_root.py` and data-root recovery helpers snapshot, verify and restore local product data with manifest/hash/path-safety behavior. This is not cloud backup/replication; restore has high local-data authority.

## Reusable helpers / do-not-reinvent index
- SQLite/data root: `open_sqlite_connection`, `build_paths`, schema registries.
- Exact context: `JarvisContextAdapterRegistry`, `require_dispatchable_preview`, context digests/source manifests.
- AI routing/cost: `AIGateway`, `run_ai_task`, `ProviderRegistry`, `resolve_model_pricing`.
- Safety/cost: sensitivity owner, egress authority/sanitizer, budget reservations, token-flow transaction/continuation.
- Development: `development/time.py`, `development/links.py`.
- Repository safety: `RepositoryTruthService`, Coding exact-target/path/diff validators.
- Recovery: data-root snapshot/verify/restore helpers.

## Stale/duplication warnings
- ProviderRegistry-missing foundation documentation is stale versus executable runtime.
- Configured provider/model does not prove credentials/network/quota/provider health; fake adapters do not prove external execution.
- Jarvis sidecar does not own a second backend/thread store; Coding pipeline projection is not canonical delivery authority.
- Local data-root recovery is not cloud backup.

## EXPLICIT FILE COVERAGE LEDGER

`READ` means contents were opened and inspected directly from fresh `master` during file-coverage recovery. PR #660 is hints-only and confers no coverage.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/main.py` | READ | FastAPI composition root; live routers, local-AI lifecycle, Coding startup observation, stranded-runner reconciliation, guarded SPA mount. |
| `backend/app/core/__init__.py` | READ | Tiny core package marker/docstring; no hidden imports/startup behavior. |
| `backend/app/core/ai_thread_schema.py` | READ | Migration `0013_ai_threads_0`; workspace threads plus flow-linked interaction persistence with request/index/flow uniqueness and explicit capture-state lifecycle. |
| `backend/app/core/bootstrap.py` | READ | Initializes canonical DB, ensures AI settings, optionally seeds default workspace; CLI prints DB location. |
| `backend/app/core/brainstorm_schema.py` | READ | Migration `0020_brainstorm`; raw records, versioned ideas/revisions, discussions, revision links, explicit promotion state and idempotency tables/indexes. |
| `backend/app/core/config.py` | READ | Cached env-backed settings for data root/DB/CORS/default AI-provider string and allowed Coding repositories. |
| `backend/app/core/database.py` | READ | Canonical SQLite connection/bootstrap/migration orchestrator; WAL+FK+busy-timeout, domain schema/index registration, conditional FTS5 and migration recording. |
| `backend/app/core/development_schema.py` | READ | Migration `0019_roadmap_calendar`; roadmap items/dependencies/object links and calendar allocations with lifecycle, date, interval and FK constraints plus query indexes. |
| `backend/app/core/errors.py` | READ | Immutable `AppError` and structured workspace-not-found HTTP helper. |
| `backend/app/core/literature_schema.py` | READ | Migration `0018_literature_knowledge`; workspace literature sources and typed claim/datum entries with lifecycle, artifact/request uniqueness, locators and provenance indexes. |
| `backend/app/core/logging.py` | READ | Minimal INFO process logging configurator with fixed format. |
| `backend/app/core/paths.py` | READ | Canonical `JarvisPaths` derivation/directory creation for DB/workspaces/artifacts/logs/secrets; compatibility alias. |
| `backend/app/core/spa_static.py` | READ | Safe SPA static/fallback boundary; reserved API roots, exact client exceptions, HTML negotiation and unsafe/asset/API rejection. |
| `backend/app/api/health.py` | READ | Read-only `/health` app/environment/data-root projection. |
| `backend/app/api/system.py` | READ | `/system/info` DB/schema + gateway projection; `/system/initialize` storage/AI-settings bootstrap. |
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary; no hidden runtime behavior. |
| `backend/app/modules/agents/base.py` | READ | Immutable `AgentCapability` metadata and minimal `Agent` protocol; no execution loop/persistence. |
| `backend/app/modules/agents/registry.py` | READ | In-memory name-keyed registry with overwrite-by-name and deterministic listing; no persistence/provider authority. |

### Remaining coverage
- Continue remaining owned `app/core` schema files and any remaining `app/api`, then every file in `ai`, `coding`, `dev_message_route`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`, followed by owned tests/configs/schemas/helpers/fixtures/migrations.
- PR #660 remains hints-only; every imported row requires reopening the source file.
- Final completion requires fresh tracked-tree rescan and defensible exact zero.

UNACCOUNTED_FILES: >0 (exact count pending complete owned-scope enumeration)
