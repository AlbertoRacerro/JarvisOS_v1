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
Persistent workspace AI threads/interactions, explicit digest-bound Jarvis context, adapter/capability registries and governed submit path exist. Context authority is separate from domain COMMIT/EXECUTE authority. `context_builder.py` is deterministic and intentionally non-retrieval: it validates caller blocks, separates PROJECT_CONTEXT data from instructions, emits canonical digests/source manifests, reads canonical modeling records, and bounds/drop-prioritizes context packs. Selected evidence integration crosses into Area-C BLUECAD evidence ownership; A does not claim that evidence implementation.

### AI gateway/provider/settings + sensitivity/egress/budget/token flow — REAL, external availability conditional
Canonical gateway/registry/adapters and provider/settings projections exist. Persisted sensitivity and fail-closed egress authority govern sanitization, budget reservations, token caps and usage reconciliation. `backend/app/core/token_flow_schema.py` makes flow identity/evidence durable: bounded direct-continuation policy snapshots, ordered attempt IDs, execution/external-dispatch/accounting aggregates, terminal/output/accounting digests, immutable flow segments with expiry/policy+guard digests, one record-capture per flow, and per-attempt execution/usage/accounting provenance on `ai_jobs`. `budget.py` evaluates the server-owned external-provider gate against policy mode, paid-AI switch, global monthly spend, registry enablement, credential presence, provider caps, and active egress reservations; status projections are not provider-health proof. `costs.py` is an estimate helper only (4 chars/token plus configured max output against a small route-price registry), not authoritative billing. `egress_policy.py` accepts only the canonical `configs/ai_egress_policy.json`, rejects missing/extra/invalid keys, and hashes the canonical policy. `egress_authority.py` is the prompt/manual-context admission boundary: S4 is denied before sanitizer invocation; S2/S3 require an already-approved derivative or one explicitly local sanitizer route; marker-free prompts default to S1 only in FAST_DEV; manual external context accepts only current approved derivative material and rechecks derivative authority after preview. `egress_persistence.py` owns atomic immutable packet/decision preparation and canonical next-attempt budget projection; confirmation-required attempts create pending tickets without reservations, silent eligible attempts reserve projected cost, hard denials reserve nothing. `egress_lifecycle.py` atomically consumes tickets, revalidates binding/policy/continuation authority, creates reservations and reconciles actual usage; stale/revoked continuation confirmations terminalize without provider dispatch. `egress_confirmation_core.py` executes an exact consumed ticket, rechecks provider budget/adapter/binding/dispatch state, and funnels success/failure through token-flow external-attempt finalization. Provider configuration is not credential/network/quota health; direct SDK bypass is not equivalent.

### Dev message-route / local-chat seam — PARTIAL, dev-only
`backend/app/api/dev_message_route.py` exposes bounded `/api/dev/message-route-smoke` and `/api/dev/local-chat` request surfaces with strict Pydantic validation, per-request trace IDs, disabled-by-default gating and sanitized error responses. `backend/app/modules/dev_message_route/smoke_adapter.py` is explicitly a narrow development seam into existing router-policy smoke/evaluation scripts, not a production dependency pattern. Local responder execution is separately gated, defaults to loopback Ollama, bounds message/history/prompt/output sizes, filters history conservatively for secret/private/external-provider/operational/tool intent, and must not be mistaken for persistent Jarvis context, memory or production AI routing.

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
- Exact context: `canonicalize_blocks`, `canonical_digest`, `context_sources_manifest`, `assemble_prompt`, `build_workspace_context_bundle`, and Jarvis context adapter/capability registry; do not add an implicit retrieval layer to the deterministic builder.
- AI routing/cost: gateway, provider/model registry contracts, provider registry/pricing, egress/budget/token-flow owners. Treat `estimate_route_cost` as estimate-only.
- Egress authority/lifecycle: reuse `authorize_prompt`, `authorize_manual_context`, `prepare_egress_attempt`, `project_egress_availability`, `consume_confirmation_ticket` and confirmed-ticket execution; do not reconstruct external-provider admission from settings alone or bypass persisted reservation/reconciliation state.
- Dev message route: reuse the bounded `dev_message_route` API/adapter only for development smoke/local-chat work; do not promote its script-import seam into production architecture.
- Repository safety: repository truth and Coding exact-target/path/diff validators.

## Stale/duplication warnings
- Historical ProviderRegistry-missing prose is stale versus executable runtime; `contracts.py` contains concrete in-memory provider/model registry contracts and filtering.
- Configured provider/model does not prove credentials/network/quota health.
- Jarvis sidecar does not own a second backend/thread store; Coding pipeline projection is not canonical delivery authority.
- Dev local-chat is deliberately non-persistent and lacks memory/retrieval/files/browser/tools/external-provider/project-store authority; its loopback responder is not evidence of production Jarvis integration.
- `context_builder.py` explicitly says it performs no retrieval/vector search/embeddings/LLM ranking; do not infer those capabilities from its context-bundle seam.
- Egress confirmation is not a thin UI acknowledgement: ticket consumption revalidates expiry, continuation authority, binding/policy drift and budget state before any external dispatch.

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
| `backend/app/core/token_flow_schema.py` | READ | Token-flow migration: durable flow/capture/segment state plus per-attempt execution, dispatch, usage and accounting provenance; bounded continuation policy. |
| `backend/app/core/topology.py` | READ | Bounded deterministic topological sort with structured fail-closed validation. |
| `backend/app/api/__init__.py` | READ | Tiny HTTP-router package marker; no hidden runtime behavior. |
| `backend/app/api/dev_message_route.py` | READ | Dev-only smoke/local-chat HTTP boundary; strict bounded validation, trace IDs, disabled gating and sanitized errors. |
| `backend/app/api/health.py` | READ | Read-only health projection. |
| `backend/app/api/system.py` | READ | System info plus explicit storage initialization endpoint. |
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary. |
| `backend/app/modules/agents/base.py` | READ | Agent capability metadata and minimal protocol. |
| `backend/app/modules/agents/registry.py` | READ | In-memory name-keyed registry; no persistence/provider authority. |
| `backend/app/modules/ai/__init__.py` | READ | Tiny AI gateway module marker; no hidden runtime behavior. |
| `backend/app/modules/ai/budget.py` | READ | Server-owned external-provider/budget gate and AI-status projection; accounts routed usage plus active reservations and provider caps/credentials. |
| `backend/app/modules/ai/context_builder.py` | READ | Deterministic bounded context assembly/selection, prompt data-instruction separation, digests/manifests; no retrieval/vector/LLM ranking. |
| `backend/app/modules/ai/contracts.py` | READ | Provider-neutral request/response/usage/error/routing/gate contracts plus in-memory provider/model registries and adapter protocol. |
| `backend/app/modules/ai/costs.py` | READ | Heuristic route-cost estimator and external-reasoning escalation proposal helper; estimate-only, context excluded. |
| `backend/app/modules/ai/egress_authority.py` | READ | Prompt/manual-context authority: deterministic sensitivity floor, approved-derivative/local-only sanitization path, FAST_DEV default, and fail-closed manual derivative revalidation. |
| `backend/app/modules/ai/egress_confirmation.py` | READ | Thin confirmation execution facade; synchronizes patchable core bindings and consumes persisted rejected continuation for expired/revoked tickets. |
| `backend/app/modules/ai/egress_confirmation_core.py` | READ | Exact confirmed-ticket execution owner; consumes/rechecks ticket, provider gate/adapter/binding/dispatch state, external attempt accounting and continuation handling. |
| `backend/app/modules/ai/egress_lifecycle.py` | READ | Atomic ticket consumption/revalidation, reservation start and usage reconciliation lifecycle; rejected continuation confirmation terminalizes without dispatch. |
| `backend/app/modules/ai/egress_persistence.py` | READ | SQLite egress preparation/availability owner; immutable packets/decisions, tickets/reservations, budget snapshots and fail-closed transactional state. |
| `backend/app/modules/ai/egress_policy.py` | READ | Strict canonical egress-policy JSON loader/parser/digest with bounded fields and supported-operation/trigger validation. |
| `backend/app/modules/dev_message_route/__init__.py` | READ | Tiny package marker explicitly identifying the dev-only smoke adapter. |
| `backend/app/modules/dev_message_route/smoke_adapter.py` | READ | Dev-only RouterPolicy/script import seam; env-gated loopback local responder, conservative history filtering and bounded non-persistent local chat. |

### Remaining coverage
- `backend/app/core`, `backend/app/api`, `backend/app/modules/agents`, and `backend/app/modules/dev_message_route` are fully accounted on the inspected master baseline except future fresh-tree additions.
- AI module coverage now includes authority, confirmation facade/core, lifecycle and persistence. Continue every remaining `backend/app/modules/ai` file (including rejected-continuation/revalidation/runtime/service/spine/sanitizer, execution/gateway/provider registry/providers, settings, token-flow and thread/service surfaces) before leaving the family.
- Then continue all files in `coding`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`, followed by owned tests/configs/schemas/helpers/fixtures/migrations.
- Scientific/CAD-only files must be directly inspected then marked `OUT_OF_SCOPE`; `cad_link_schema.py` is explicitly accounted.
- PR #660 remains hints-only; every imported row requires reopening source.
- Final completion requires a fresh tracked-tree rescan and defensible exact zero.

UNACCOUNTED_FILES: >0 (exact count pending complete owned-scope enumeration)