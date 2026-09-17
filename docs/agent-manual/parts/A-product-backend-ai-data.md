# Area A — Product backend / AI / data / context

MAPPING_STATUS: IN_PROGRESS

Runtime/source baseline: fresh `master` `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Literal file accounting is authoritative for completion.

## Capability map

### FastAPI composition + startup — REAL
Canonical backend composition root/lifecycle owner in `backend/app/main.py` with settings/static support in `backend/app/core`.

### Data root + SQLite + migrations — REAL
Single local-first product-data root and SQLite/bootstrap owner. Reuse `open_sqlite_connection`, schema registries and the shared row conversion helpers in `backend/app/core/repository.py`; do not add a second DB/data root or duplicate row mapper.

### Deterministic dependency ordering — REAL
`backend/app/core/topology.py` provides bounded deterministic topological sorting and fails closed on malformed graph state.

### Canonical engineering MemoryStore — REAL
Canonical assumptions/parameters/decisions and AI-origin proposal/replacement lifecycle live in `backend/app/modules/memory/*` plus the shared schema. Do not create a second engineering-record store.

### Project Knowledge / Project Basis — REAL
Curated source/revision/apply owner under `backend/app/modules/project_knowledge/*` plus `project_knowledge_schema.py`; distinct from MemoryStore engineering-record ownership.

### Literature / Model Dossier / Project Search — REAL
Literature curation, model dossier projection and bounded project search are implemented in their canonical backend owners. Search/open remains discovery and does not implicitly bind Jarvis context.

### AI threads + Jarvis context/action foundation — REAL
Persistent workspace AI threads/interactions, explicit digest-bound Jarvis context, adapter/capability registries and governed submit path exist. Context authority is separate from domain COMMIT/EXECUTE authority. `context_builder.py` is deterministic and intentionally non-retrieval.

### AI gateway/provider/settings + sensitivity/egress/budget/token flow — REAL, external availability conditional
Canonical gateway/registry/adapters and provider/settings projections exist. Persisted sensitivity and fail-closed egress authority govern sanitization, budget reservations, token caps and usage reconciliation. `budget.py` evaluates the server-owned external-provider gate. `egress_policy.py` accepts only the canonical policy config. `egress_authority.py`, `egress_persistence.py`, `egress_lifecycle.py` and `egress_confirmation_core.py` form the governed external-dispatch boundary. `egress_revalidation.py` is the mutable-authority recheck inside confirmation consumption: packet/policy digests alone are insufficient, so prompt derivatives, direct-source labels/digests, canonical derivatives and source digests are re-resolved and stale/revoked/non-external-eligible authority fails closed. `egress_rejected_continuation.py` terminalizes only already-expired/revoked continuation tickets without provider dispatch. `egress_runtime.py` is the external-route orchestrator: it creates/validates flows, resolves provider binding/fallback chains, gates network/output ceilings/provider budget, authorizes prompt/context, persists prepacket stops, executes governed reserved attempts, reconciles/finalizes external attempts, and hands length-limited successful output to bounded continuation runtime. `egress_sanitizer.py` persists immutable provenance-bound S0/S1 prompt/canonical derivatives, rejects deterministic S4 secret material, binds model-local sanitizer output to canonical AI-job digests and source snapshots, and owns sampled audit/revocation consequences for sanitizer approvals. `egress_service.py` is the pure canonical packet-projection contract: it validates S0/S1-only effective packet levels, prompt/context/output policy ceilings, exact enabled network provider/model/fallback binding, safe metadata manifests and source digests, then binds packet/policy/pricing/source state into deterministic canonical JSON and SHA-256 digests with a projected cost upper bound; it performs no DB write, secret lookup, reservation, ticket transition or provider call. `deepseek_provider_smoke.py` is diagnostic-only: it adds strict DeepSeek-mode, prompt/output-size and public/internal privacy gates, but delegates any actual external dispatch to canonical `run_ai_task`; it is not a second provider router. `provider_registry.py` is the strict YAML-backed provider/model/binding/fallback/pricing authority: it validates execution-class/network/endpoint/credential-reference consistency, route uniqueness, context/output ceilings, enabled external pricing, fallback membership and constrained environment model overrides. `execution_types.py` defines the shared execution-class and provider-binding value contract; its compatibility backfill may enrich missing execution/context metadata from the enabled default registry but deliberately tolerates import/config lookup failure. `gateway.py` is the product-facing AI facade: generic task execution resolves effective route class, preflights external budget/provider state, optionally builds bounded workspace context, and delegates canonical execution to `run_ai_task`; its legacy modeling-draft path is separately fake-provider/budget/event oriented. `execution.py` is the canonical provider-neutral execution spine: it resolves local routes and fallback chains, persists every attempt plus token-flow evidence, fail-closes malformed context/config/provider failures, delegates network routes to governed egress runtime, drives bounded local continuation/terminalization, and only captures decision-support records from terminal successful output. `escalations.py` is a narrow confirmation-response adapter: it consumes a ticket only through `run_confirmation_ticket` and projects the resulting governed outcome back into the public task/escalation response contract; it does not create a parallel confirmation or dispatch path. The legacy modeling provider seam is deliberately narrow: `providers/base.py` defines the draft request/response protocol, `providers/fake.py` is deterministic and explicitly non-validating, while `providers/deepseek.py` is a concrete synchronous OpenAI-compatible HTTP adapter whose direct call requires `DEEPSEEK_API_KEY`, uses a 30-second timeout, and reports sanitized usage/finish metadata. These provider files are adapters, not independent egress authority; provider configuration is not credential/network/quota health and direct SDK/HTTP bypass is not equivalent to governed execution. `models.py` is the Pydantic HTTP/value-contract surface for AI settings/status/provider credentials, modeling drafts, bounded task/context-pack requests, escalation confirmation, smoke/provider tests and supervisor public tests; it forbids extras on sensitive request models and enforces explicit context-block count/serialized-character ceilings, but these schema checks are not execution or egress authority. Flow-grade cohort reporting exposes bounded GET-only cohort projections; its route converts contract/value errors to 422, response models make reconciliation/accounting-quality fields explicit, and numeric distributions use deterministic nearest-rank percentiles with explicit empty distributions.

### Dev message-route / local-chat seam — PARTIAL, dev-only
Dev-only bounded smoke/local-chat surfaces exist and must not be mistaken for production Jarvis integration.

### Development Roadmap + Calendar + Brainstorm — REAL
Canonical roadmap/calendar/brainstorm persistence exists. Brainstorm promotion is explicit.

### Development multi-record Jarvis actions — DEFERRED on inspected baseline
No executable spec-122 multi-record Development CONTEXT/PROPOSE service was found on the inspected baseline; do not infer implementation from spec prose.

### Coding repository/runtime truth + proposal actions — REAL, PROPOSE-only
Coding repository/runtime/pipeline projections and bounded inspect/modification proposals exist; proposals do not apply patches, commit or push.

### Product-data backup / verify / restore — REAL local recovery primitive
Data-root recovery helpers snapshot, verify and restore local product data; this is not cloud backup.

## Reusable helpers / do-not-reinvent index
- SQLite/data root: canonical database/path/schema/repository helpers.
- Dependency graphs: `deterministic_topological_order`, `TopologyError`.
- Exact context: canonical context builder/digest/source-manifest helpers; do not add implicit retrieval to deterministic context assembly.
- AI routing/cost: gateway, provider/model registry contracts, provider registry/pricing, egress/budget/token-flow owners.
- Egress authority/lifecycle: reuse canonical authority, persistence, revalidation, ticket consumption, reserved-attempt reconciliation and confirmed-ticket execution; do not reconstruct external-provider admission from settings alone.
- Repository safety: repository truth and Coding exact-target/path/diff validators.

## Stale/duplication warnings
- Configured provider/model does not prove credentials/network/quota health.
- Jarvis sidecar does not own a second backend/thread store.
- Dev local-chat is deliberately non-persistent and is not evidence of production Jarvis integration.
- DeepSeek provider smoke is diagnostic-only and routes execution through `run_ai_task`; do not copy its preflight gates into a competing gateway.
- Deterministic context assembly performs no retrieval/vector search/embeddings/LLM ranking.
- Egress confirmation is not a thin UI acknowledgement: mutable source/derivative authority is revalidated transactionally before dispatch.
- `egress_service.py` packet construction is pure validation/projection, not persistence, reservation, confirmation or dispatch authority.
- `providers/deepseek.py` can issue a synchronous external HTTP request directly when called; callers must not mistake that adapter-level capability for canonical egress authorization.
- `models.py` request validation bounds payload shape/size only; it must not be treated as provider, budget, sensitivity or egress authorization.

## EXPLICIT FILE COVERAGE LEDGER

`READ` means contents were opened and inspected directly from fresh `master` during file-coverage recovery. PR #660 is hints-only and confers no coverage.

| path | status | concise role/reason |
|---|---|---|
| `backend/app/main.py` | READ | FastAPI composition root; routers/lifecycle/startup reconciliation/SPA mount. |
| `backend/app/core/__init__.py` | READ | Tiny package marker/docstring; no hidden runtime behavior. |
| `backend/app/core/ai_thread_schema.py` | READ | AI-thread migration and flow-linked interaction persistence. |
| `backend/app/core/bootstrap.py` | READ | DB + AI-settings initialization and optional default workspace seed. |
| `backend/app/core/brainstorm_schema.py` | READ | Brainstorm records/revisions/discussions/promotion/idempotency persistence. |
| `backend/app/core/cad_link_schema.py` | OUT_OF_SCOPE | Directly inspected: process/simulation-to-BLUECAD migration; Area C semantics. |
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
| `backend/app/core/repository.py` | READ | Pure shared SQLite-row→Pydantic conversion helpers. |
| `backend/app/core/schema.py` | READ | Shared baseline schema/migration owner; Area-C semantics not claimed. |
| `backend/app/core/sensitivity_schema.py` | READ | Sensitivity labels and sanitized derivative provenance/revocation persistence. |
| `backend/app/core/spa_static.py` | READ | Safe SPA static/fallback boundary with reserved API-root protection. |
| `backend/app/core/token_flow_schema.py` | READ | Durable flow/capture/segment and per-attempt execution/usage/accounting provenance. |
| `backend/app/core/topology.py` | READ | Bounded deterministic topological sort with structured fail-closed validation. |
| `backend/app/api/__init__.py` | READ | Tiny HTTP-router package marker. |
| `backend/app/api/dev_message_route.py` | READ | Dev-only smoke/local-chat HTTP boundary. |
| `backend/app/api/health.py` | READ | Read-only health projection. |
| `backend/app/api/system.py` | READ | System info plus explicit storage initialization endpoint. |
| `backend/app/modules/agents/__init__.py` | READ | Tiny package boundary. |
| `backend/app/modules/agents/base.py` | READ | Agent capability metadata and minimal protocol. |
| `backend/app/modules/agents/registry.py` | READ | In-memory name-keyed registry. |
| `backend/app/modules/ai/__init__.py` | READ | Tiny AI gateway module marker. |
| `backend/app/modules/ai/budget.py` | READ | Server-owned external-provider/budget gate and AI-status projection. |
| `backend/app/modules/ai/context_builder.py` | READ | Deterministic bounded context assembly; no retrieval/vector/LLM ranking. |
| `backend/app/modules/ai/contracts.py` | READ | Provider-neutral contracts plus in-memory provider/model registries and adapter protocol. |
| `backend/app/modules/ai/costs.py` | READ | Heuristic route-cost estimator; estimate-only. |
| `backend/app/modules/ai/deepseek_provider_smoke.py` | READ | Diagnostic DeepSeek smoke wrapper: bounded prompt/output, policy/privacy preflight, canonical `run_ai_task` dispatch, event logging. |
| `backend/app/modules/ai/egress_authority.py` | READ | Prompt/manual-context sensitivity and derivative authority boundary. |
| `backend/app/modules/ai/egress_confirmation.py` | READ | Thin confirmation execution facade. |
| `backend/app/modules/ai/egress_confirmation_core.py` | READ | Exact confirmed-ticket execution owner. |
| `backend/app/modules/ai/egress_lifecycle.py` | READ | Atomic ticket consumption/revalidation, reservation start and reconciliation lifecycle. |
| `backend/app/modules/ai/egress_persistence.py` | READ | SQLite egress preparation/availability owner. |
| `backend/app/modules/ai/egress_policy.py` | READ | Strict canonical egress-policy loader/parser/digest. |
| `backend/app/modules/ai/egress_rejected_continuation.py` | READ | Terminalizes already-expired/revoked continuation confirmation inside an immediate transaction; no dispatch. |
| `backend/app/modules/ai/egress_revalidation.py` | READ | Transactional mutable-authority recheck for prompt derivatives, context source labels/digests, canonical derivatives and protected segment rules. |
| `backend/app/modules/ai/egress_runtime.py` | READ | Governed external-route/flow orchestrator with binding fallback, prepacket stops, provider gate, reserved dispatch/reconciliation and continuation handoff. |
| `backend/app/modules/ai/egress_sanitizer.py` | READ | Provenance-bound S0/S1 sanitizer derivative persistence, AI-job/source binding, sampled audit and revocation consequences. |
| `backend/app/modules/ai/egress_service.py` | READ | Pure canonical external-attempt packet projection: validates policy/binding/safe manifests/source digests and binds packet/policy/pricing state into deterministic digests/cost upper bound; no persistence or dispatch. |
| `backend/app/modules/ai/escalations.py` | READ | Narrow confirmation adapter; consumes ticket through canonical confirmation path and projects governed outcome into public task/escalation response. |
| `backend/app/modules/ai/execution.py` | READ | Canonical provider-neutral execution spine: local routing/fallback, attempt/evidence ledgering, governed external delegation, local continuation/terminalization and terminal record capture. |
| `backend/app/modules/ai/execution_types.py` | READ | Shared execution-class/ProviderBinding contract with tolerant default-registry metadata backfill for legacy callers. |
| `backend/app/modules/ai/flow_grade_cohort_distributions.py` | READ | Deterministic integer distribution helper with nearest-rank p50/p95 and explicit empty result. |
| `backend/app/modules/ai/flow_grade_cohort_models.py` | READ | Pydantic cohort projection contracts for grade coverage, execution/accounting quality, costs, mixes, distributions and reconciliation invariants. |
| `backend/app/modules/ai/flow_grade_cohort_routes.py` | READ | GET-only bounded `/grade-cohorts` route; delegates cohort computation and maps contract/value errors to HTTP 422. |
| `backend/app/modules/ai/gateway.py` | READ | Product AI facade: task routing/context preflight into canonical execution plus separate legacy fake-provider modeling-draft/event path. |
| `backend/app/modules/ai/models.py` | READ | Pydantic AI HTTP/value contracts; strict settings/task/context/escalation/smoke/supervisor request-response shapes with bounded explicit context payloads. |
| `backend/app/modules/ai/provider_registry.py` | READ | Strict provider/model registry, route bindings/fallbacks, execution-class contracts, pricing and constrained env overrides. |
| `backend/app/modules/ai/providers/__init__.py` | READ | Tiny provider-interface package marker; no runtime behavior. |
| `backend/app/modules/ai/providers/base.py` | READ | Legacy modeling-draft AIRequest/AIResponse value objects and minimal AIProvider protocol. |
| `backend/app/modules/ai/providers/deepseek.py` | READ | Concrete synchronous DeepSeek OpenAI-compatible HTTP adapter; env key/base/model, 30s request, usage/finish metadata; adapter itself is not egress authority. |
| `backend/app/modules/ai/providers/fake.py` | READ | Deterministic fake modeling-draft provider plus keyword-only smoke sensitivity classifier; explicitly non-validating. |
| `backend/app/modules/dev_message_route/__init__.py` | READ | Tiny dev-only package marker. |
| `backend/app/modules/dev_message_route/smoke_adapter.py` | READ | Dev-only RouterPolicy/script seam and bounded non-persistent local responder. |

### Remaining coverage
- `backend/app/core`, `backend/app/api`, `backend/app/modules/agents`, and `backend/app/modules/dev_message_route` are fully accounted on the inspected master baseline except future fresh-tree additions.
- Continue every remaining `backend/app/modules/ai` file, then all files in `coding`, `development`, `events`, `files`, `local_ai`, `local_ai_eval`, `memory`, `modeling`, `project_knowledge`, `project_search`, `secrets`, `tools`, `workspaces`, followed by owned tests/configs/schemas/helpers/fixtures/migrations.
- Scientific/CAD-only files must be directly inspected then marked `OUT_OF_SCOPE`.
- PR #660 remains hints-only; every imported row requires reopening source.
- Final completion requires a fresh tracked-tree rescan and defensible exact zero.

UNACCOUNTED_FILES: >0 (exact count pending complete owned-scope enumeration)
