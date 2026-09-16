# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Classifications below are executable-source/runtime claims, not spec-derived claims. Literal file accounting is authoritative for completion.

## Capability map

### FastAPI composition + startup — REAL
- **What/when:** canonical backend composition root and lifecycle owner.
- **Canonical files:** `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/spa_static.py`.
- **Invocation/reuse:** `create_app`, exported `app`, `lifespan`; mount new product routers here rather than creating a parallel app.
- **I/O/persistence:** `app.state` stores local-AI lifecycle and Coding startup runtime snapshot; startup also reconciles stranded runner jobs. SPA is mounted only when `frontend/dist` exists.
- **Preconditions:** settings/data root; local-AI lifecycle; runner persistence. Coding runtime observation deliberately fails open to an explicit unavailable snapshot.
- **Side effects/authority/risk:** composition determines which routes are actually live. Lifespan may reconcile runner persistence; transient SQLite locks are retried for startup-observed abandoned owners.
- **Tests/evidence:** direct source inspection; startup/domain route tests remain evidence targets.
- **Limitations:** module existence does not prove route mounting. Exact SPA client-route exceptions are explicitly enumerated.
- **Do not reinvent:** reuse this composition/lifespan and `SpaStaticFiles` boundary.
- **Search anchors:** `create_app`, `lifespan`, `_reconcile_after_live_owners_exit`, `_SPA_RESERVED_ROOT_CLIENT_ROUTES`, `derive_reserved_roots`.

### Settings + system/health projection — REAL
- **What/when:** environment-backed process settings plus product-safe health/system/bootstrap endpoints.
- **Canonical files:** `backend/app/core/config.py`, `backend/app/api/health.py`, `backend/app/api/system.py`.
- **Invocation/reuse:** cached `get_settings`; `GET /health`, `GET /system/info`, `POST /system/initialize`.
- **I/O/persistence:** settings read env vars; initialize delegates to storage bootstrap and AI settings owner. System info projects DB/schema and AI gateway status.
- **Preconditions:** `/system/info` tolerates uninitialized DB; initialization requires writable configured data root.
- **Side effects/authority/risk:** `POST /system/initialize` mutates product storage and seeds defaults; health/info are projections. Returned provider configuration is not proof of external provider health.
- **Tests/evidence:** direct source inspection plus API/bootstrap tests.
- **Limitations:** legacy `Settings.ai_provider` remains a process setting while canonical AI runtime status is projected from `AIGateway` once DB is initialized.
- **Do not reinvent:** consume these projections rather than exposing raw env/secrets.
- **Search anchors:** `get_settings`, `health_check`, `system_info`, `initialize_system`.

### Data root + SQLite + migrations — REAL
- **What/when:** single local-first product-data root and SQLite/bootstrap owner.
- **Canonical files:** `backend/app/core/paths.py`, `database.py`, `bootstrap.py`, `schema.py`, domain `*_schema.py` files.
- **Invocation/reuse:** `build_paths`, `ensure_data_directories`, `open_sqlite_connection`, `initialize_database`, `get_database_info`.
- **I/O/persistence:** canonical SQLite plus workspace/artifact/log/secret directories; application-managed migrations and conditional FTS5. SQLite connections enforce foreign keys, WAL and a 5 s busy timeout.
- **Preconditions:** writable data root and SQLite.
- **Side effects/authority/risk:** high persistence authority; schema bootstrap/migrations mutate canonical DB. `initialize_storage` also ensures AI settings and optionally seeds the default workspace.
- **Tests/evidence:** direct inspection of paths/bootstrap/database; domain schema/test files remain literal coverage targets.
- **Limitations:** no Alembic; FTS availability depends on SQLite build; initialization uses duplicate-column tolerance for additive migrations and explicit migration recording.
- **Do not reinvent:** no second product DB or data root.
- **Search anchors:** `SCHEMA_MIGRATION_RECORDS`, `initialize_database`, `open_sqlite_connection`, `_sqlite_fts5_available`, `initialize_storage`.

### Canonical engineering MemoryStore — REAL
- **What/when:** assumptions/parameters/decisions and AI-origin proposal lifecycle.
- **Canonical files:** `backend/app/modules/memory/service.py`, `models.py`, `routes.py`, `replacement.py`, `backend/app/core/schema.py`.
- **Invocation/reuse:** Memory service/routes, especially proposal/replacement lifecycle.
- **I/O/persistence:** canonical SQLite lifecycle records; AI proposals bind `ai_jobs` provenance.
- **Preconditions:** workspace and valid provenance/replacement identities.
- **Side effects/authority/risk:** domain-authoritative writes; replacement can invalidate downstream freshness.
- **Tests/evidence:** memory/replacement/freshness tests.
- **Limitations:** distinct owner from Project Knowledge and Literature.
- **Do not reinvent:** reuse canonical lifecycle/replacement machinery.
- **Search anchors:** `_TABLE_BY_KIND`, `_create_proposal_in_transaction`, `persist_freshness_invalidation`.

### Project Knowledge / Project Basis — REAL
- **What/when:** curated project-basis/source/revision/apply owner.
- **Canonical files:** `backend/app/modules/project_knowledge/*`, `backend/app/core/project_knowledge_schema.py`, `backend/app/modules/memory/project_knowledge_owner.py`.
- **Invocation/reuse:** Project Knowledge router/service/apply/revision lifecycle.
- **I/O/persistence:** SQLite records, revisions, backing-source metadata.
- **Preconditions:** workspace and exact lifecycle/version expectations.
- **Side effects/authority/risk:** apply/revision operations mutate canonical knowledge; stale-write guards matter.
- **Tests/evidence:** Project Knowledge backend tests.
- **Limitations:** not MemoryStore engineering-record ownership.
- **Do not reinvent:** reuse owner and explicit memory bridge.
- **Search anchors:** `project_knowledge/service.py`, `apply.py`, `revision_lifecycle.py`.

### Literature knowledge — REAL
Persistent literature/source curation, search, preview and backing-availability semantics. Canonical implementation is under `backend/app/modules/memory/literature_*` with `backend/app/core/literature_schema.py`. Curated metadata may remain valid while backing content is unavailable; do not create a second bibliography store.

### Model Dossier — REAL
Workspace-isolated read projection joining canonical model/version identity to runs, artifacts and evidence. Canonical implementation: `backend/app/modules/modeling/model_dossier.py`, `model_dossier_search.py`, `dossier_models.py`, `routes.py`. Missing/stale evidence is represented explicitly rather than repaired or silently promoted.

### Project Search — REAL
Bounded read/search facade over canonical owners in `backend/app/modules/project_search/*`; uses FTS5 where available with fallback behavior. Search/open is discovery only and does not implicitly bind Jarvis context.

### AI threads + Jarvis sidecar backend seam — REAL
Persistent workspace-scoped threads/interactions under `backend/app/modules/ai/thread_*`; optional explicit digest-bound Jarvis context; submit enters governed AI execution. No second sidecar thread/backend store was found.

### Common Jarvis context + capability/action foundation — REAL
`jarvis_context*.py` provides explicit context preview/binding, adapter/capability registries, source manifests and digests. Context authority is separate from domain COMMIT/EXECUTE authority; browse/open does not implicitly select context.

### AI gateway + provider registry/routing/adapters — REAL, availability conditional
Canonical execution facade is `AIGateway`/`run_ai_task` with validated provider registry and bindings. Concrete adapters are execution paths; fake/synthetic adapters are test/development seams. Registry configuration is not credential/network/quota health. Historical foundation prose claiming ProviderRegistry is absent is stale.

### Provider/settings/status projections — REAL
`/ai/settings`, `/ai/status`, `/ai/provider-settings` project the canonical settings/gateway/registry authority. Settings mutation is bounded; projections must not expose provider secrets.

### Sensitivity + governed egress/budget/token flow — REAL
Persisted sensitivity labels/sanitized derivatives feed a fail-closed external-egress policy spine. External provider transmission and cost require current authority, sanitization, budget/token caps, persistence and usage reconciliation. Missing/inconsistent actual usage is handled conservatively rather than inventing lower spend. Do not bypass this spine with direct SDK calls.

### Development Roadmap + Calendar + Brainstorm — REAL
Development storage/routes/services own roadmap/calendar/reconciliation records and links; Brainstorm owns persistent ideation linked to Development. Brainstorm content is not automatically canonical project/engineering knowledge; promotion remains explicit.

### Development multi-record Jarvis actions (spec-122 target) — DEFERRED on inspected master
No executable spec-122 multi-record Development CONTEXT/PROPOSE action service was found on the inspected master. Underlying Development storage and generic Jarvis foundation are REAL. Re-check fresh runtime before assuming continued absence; do not infer implementation from spec prose.

### Coding repository truth / runtime truth / pipeline projection — REAL
`backend/app/modules/coding/{repository_truth,runtime_truth,runtime_routes,pipeline_state}.py` provide repository/host/runtime observations and projection of existing delivery state. Pipeline state is not a second canonical delivery queue.

### Coding inspect + modification proposal actions — REAL, PROPOSE-only
`CodingActionsService` freezes exact repository/base SHA/target evidence, invokes governed coder AI, validates closed output/diff constraints, then rechecks head before returning a proposal. It does not apply patches, commit or push. Model output remains advisory until deterministic validation.

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
- Configured provider/model does not prove credentials/network/quota/provider health.
- Fake adapters do not prove external-provider execution.
- Jarvis sidecar does not own a second backend/thread store.
- Coding pipeline projection is not canonical delivery authority.
- Local data-root recovery is not cloud backup.

## EXPLICIT FILE COVERAGE LEDGER

`READ` means contents were opened and inspected directly from fresh `master` during file-coverage recovery. PR #660 is hints-only and confers no coverage.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/main.py` | READ | FastAPI composition root; mounts live routers, owns local-AI lifecycle, Coding startup runtime snapshot, stranded-runner reconciliation and guarded SPA mount. |
| `backend/app/core/__init__.py` | READ | Tiny core package marker/docstring only; no hidden imports or startup behavior. |
| `backend/app/core/bootstrap.py` | READ | Storage bootstrap wrapper: initializes canonical DB, ensures AI settings, optionally seeds default workspace; executable CLI entry prints initialized DB location. |
| `backend/app/core/config.py` | READ | Cached env-backed process settings for data root/DB/CORS/default AI-provider string and allowed Coding repositories. |
| `backend/app/core/database.py` | READ | Canonical SQLite connection/bootstrap/migration orchestrator; WAL+FK+busy-timeout, domain schema/index registration, conditional FTS5, migration recording and readiness projection. |
| `backend/app/core/errors.py` | READ | Shared immutable `AppError` plus canonical structured workspace-not-found HTTP error helper. |
| `backend/app/core/logging.py` | READ | Minimal process logging configurator using INFO and a fixed timestamp/level/logger/message format. |
| `backend/app/core/paths.py` | READ | Canonical `JarvisPaths` derivation and directory creation for DB/workspaces/artifacts/logs/secrets; includes compatibility `resolve_paths` alias. |
| `backend/app/core/spa_static.py` | READ | Safe SPA static/fallback server; derives reserved API roots, validates exact client-route exceptions, requires HTML negotiation and rejects unsafe/asset/API fallback. |
| `backend/app/api/health.py` | READ | Read-only `/health` projection of app identity/environment and resolved data root. |
| `backend/app/api/system.py` | READ | `/system/info` projects DB/schema + canonical gateway status; `/system/initialize` bootstraps storage and AI settings. |
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary; no hidden runtime behavior. |
| `backend/app/modules/agents/base.py` | READ | Immutable `AgentCapability` metadata and minimal `Agent` protocol; no execution loop/persistence. |
| `backend/app/modules/agents/registry.py` | READ | In-memory name-keyed `AgentRegistry` with overwrite-by-name and deterministic sorted listing; no persistence/provider authority. |

### Remaining coverage
- Literal owned-scope enumeration remains incomplete. Continue remaining `app/api` and `app/core` schema files, then every file in owned module families `ai`, `coding`, `dev_message_route`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`, followed by their owned tests/configs/schemas/helpers/fixtures/migrations.
- PR #660 remains hints-only; every imported row requires reopening the source file.
- Final completion requires a fresh tracked-tree rescan and a defensible exact zero count.

UNACCOUNTED_FILES: >0 (exact count pending complete owned-scope enumeration)
