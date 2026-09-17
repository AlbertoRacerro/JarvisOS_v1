# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Literal file accounting is authoritative for completion.

## Capability map

### FastAPI composition + startup — REAL
Canonical backend composition root/lifecycle owner in `backend/app/main.py` with settings/static support in `backend/app/core`.

### Data root + SQLite + migrations — REAL
Single local-first product-data root and SQLite/bootstrap owner. Reuse `open_sqlite_connection`, schema registries and the shared `row_to_model`/`optional_row_to_model`/`rows_to_models` conversion helpers in `backend/app/core/repository.py`; do not add a second DB/data root or duplicate row mapper.

### Deterministic dependency ordering — REAL
`backend/app/core/topology.py` provides bounded deterministic topological sorting. It fails closed on invalid/duplicate node IDs, unknown edge endpoints, node/edge limits, self-cycles and residual cycles; duplicate edges are ignored idempotently and ready nodes are heap ordered. Reuse `deterministic_topological_order` and structured `TopologyError` rather than ad-hoc dependency sorting.

### Canonical engineering MemoryStore — REAL
Canonical assumptions/parameters/decisions and AI-origin proposal/replacement lifecycle live in `backend/app/modules/memory/*` plus the shared schema. Do not create a second engineering-record store.

### Project Knowledge / Project Basis — REAL
Curated source/revision/apply owner under `backend/app/modules/project_knowledge/*` plus `project_knowledge_schema.py`; distinct from MemoryStore engineering-record ownership.

### Literature / Model Dossier / Project Search — REAL
Literature curation, model dossier projection and bounded project search are implemented in their canonical backend owners. Search/open remains discovery and does not implicitly bind Jarvis context.

### AI threads + Jarvis context/action foundation — REAL
Persistent workspace AI threads/interactions, explicit digest-bound Jarvis context, adapter/capability registries and governed submit path exist. Context authority is separate from domain COMMIT/EXECUTE authority.

### AI gateway/provider/settings + sensitivity/egress/budget/token flow — REAL, external availability conditional
Canonical gateway/registry/adapters and provider/settings projections exist. Persisted sensitivity and fail-closed egress authority govern sanitization, budget reservations, token caps and usage reconciliation. Provider configuration is not credential/network/quota health; direct SDK bypass is not equivalent.

### Development Roadmap + Calendar + Brainstorm — REAL
Canonical roadmap/calendar/brainstorm persistence exists. Brainstorm promotion is explicit.

### Development multi-record Jarvis actions — DEFERRED on inspected baseline
No executable spec-122 multi-record Development CONTEXT/PROPOSE service was found on the inspected baseline; do not infer implementation from spec prose.

### Coding repository/runtime truth + proposal actions — REAL, PROPOSE-only
Coding repository/runtime/pipeline projections and bounded inspect/modification proposals exist; proposals do not apply patches, commit or push.

### Product-data backup / verify / restore — REAL local recovery primitive
Data-root recovery helpers snapshot, verify and restore local product data; this is not cloud backup.

## Reusable helpers / do-not-reinvent index
- SQLite/data root: `open_sqlite_connection`, path/schema registries, `row_to_model`, `optional_row_to_model`, `rows_to_models`.
- Dependency graphs: `deterministic_topological_order`, `TopologyError`.
- Exact context: Jarvis context adapter/capability registry and digest/source-manifest helpers.
- AI routing/cost: gateway, provider registry/pricing, egress/budget/token-flow owners.
- Repository safety: repository truth and Coding exact-target/path/diff validators.

## Stale/duplication warnings
- Historical ProviderRegistry-missing prose is stale versus executable runtime.
- Configured provider/model does not prove credentials/network/quota health.
- Jarvis sidecar does not own a second backend/thread store; Coding pipeline projection is not canonical delivery authority.

## EXPLICIT FILE COVERAGE LEDGER

`READ` means contents were opened and inspected directly from fresh `master` during file-coverage recovery. PR #660 is hints-only and confers no coverage.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/main.py` | READ | FastAPI composition root; routers/lifecycle/startup reconciliation/SPA mount. |
| `backend/app/core/__init__.py` | READ | Tiny package marker/docstring; no hidden runtime behavior. |
| `backend/app/core/ai_thread_schema.py` | READ | AI-thread migration and flow-linked interaction persistence. |
| `backend/app/core/bootstrap.py` | READ | DB + AI-settings initialization and optional default workspace seed. |
| `backend/app/core/brainstorm_schema.py` | READ | Brainstorm records/revisions/discussions/promotion/idempotency persistence. |
| `backend/app/core/cad_link_schema.py` | OUT_OF_SCOPE | Directly inspected: deterministic process/simulation-to-BLUECAD link migration `0015`; scientific/CAD semantics belong to Area C. |
| `backend/app/core/config.py` | READ | Cached environment-backed process settings. |
| `backend/app/core/database.py` | READ | Canonical SQLite connection/bootstrap/migration orchestrator. |
| `backend/app/core/development_schema.py` | READ | Roadmap/dependency/object-link/calendar persistence migration. |
| `backend/app/core/egress_schema.py` | READ | Governed egress/derivative/decision/reservation/ticket/attempt/audit persistence. |
| `backend/app/core/errors.py` | READ | Structured application/workspace HTTP error helper. |
| `backend/app/core/grade_schema.py` | READ | Versioned AI-flow grade subjects and append-only grade events. |
| `backend/app/core/literature_schema.py` | READ | Literature source + claim/datum persistence. |
| `backend/app/core/logging.py` | READ | Minimal process logging configurator. |
| `backend/app/core/paths.py` | READ | Canonical data-root/database/workspace/artifact/log/secret paths. |
| `backend/app/core/project_knowledge_schema.py` | READ | Project Knowledge drafts/revisions/approval/reconciliation persistence. |
| `backend/app/core/repository.py` | READ | Pure shared SQLite-row→Pydantic conversion helpers; no persistence authority. |
| `backend/app/core/schema.py` | READ | Shared baseline schema/migration owner; mixed Area-C scientific semantics not claimed by A. |
| `backend/app/core/sensitivity_schema.py` | READ | Sensitivity labels and sanitized derivative provenance/revocation persistence. |
| `backend/app/core/spa_static.py` | READ | Safe SPA static/fallback boundary with reserved API-root protection. |
| `backend/app/core/topology.py` | READ | Bounded deterministic topological sort with structured fail-closed validation. |
| `backend/app/api/health.py` | READ | Read-only health projection. |
| `backend/app/api/system.py` | READ | System info plus explicit storage initialization endpoint. |
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary. |
| `backend/app/modules/agents/base.py` | READ | Agent capability metadata and minimal protocol. |
| `backend/app/modules/agents/registry.py` | READ | In-memory name-keyed registry; no persistence/provider authority. |

### Remaining coverage
- Continue every unaccounted owned `app/core`/`app/api` file, then all files in `ai`, `coding`, `dev_message_route`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`, followed by owned tests/configs/schemas/helpers/fixtures/migrations.
- Scientific/CAD-only files must be directly inspected then marked `OUT_OF_SCOPE`; `cad_link_schema.py` is now explicitly accounted.
- PR #660 remains hints-only; every imported row requires reopening source.
- Final completion requires a fresh tracked-tree rescan and defensible exact zero.

UNACCOUNTED_FILES: >0 (exact count pending complete owned-scope enumeration)
