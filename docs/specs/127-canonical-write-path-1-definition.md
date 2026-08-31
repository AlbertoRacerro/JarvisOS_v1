# 127 CANONICAL-WRITE-PATH-1 — definition

Exact source master: `db022a4664586fb24698f08b1576da18a890b3b9`.

Authority: definition only. This document does not authorize runtime implementation and does not change the live `127` registry row from `planned`.

Governing authority:
- `AGENTS.md`;
- `docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md`;
- `docs/POST_112_PARALLEL_DELIVERY_PROFILE.md`;
- `docs/specs/STATUS.md`;
- `docs/specs/POST_112_HARDENING_BACKLOG_127_134.md`;
- merged `112 PROJECT-KNOWLEDGE-CORE-1`, including its accepted Project Knowledge working-revision/reconciliation ownership;
- merged `098 PARAMETER-LIFECYCLE-1`, which remains the Parameter lifecycle/CAS owner.

## Problem

After 112, JarvisOS has a server-owned Project Knowledge reconciliation path, but public legacy modeling routes still expose mutation surfaces whose authority semantics are not uniformly equivalent to the accepted canonical owner contracts.

The failure mode is not merely duplicate functions. A public compatibility route can become a second canonical writer when it accepts lifecycle/status/origin-like state directly, mutates a canonical record without the accepted workspace/CAS/audit/reconciliation behavior, or silently normalizes authoritative state instead of rejecting an unauthorized write.

127 closes that ambiguity. It must classify every registered public modeling mutation surface by behavior and either make it an equivalent delegate to the accepted canonical owner, reject caller attempts to manufacture server-owned authoritative state, or prove that the surface owns non-canonical evidence rather than Project Basis/model truth.

## Exact-master inventory at definition

On exact source master, `backend/app/modules/modeling/routes.py` registers these public mutation surfaces:

1. `POST /workspaces/{workspace_id}/model-specs` -> `create_model_spec`;
2. `POST /workspaces/{workspace_id}/assumptions` -> `create_assumption`;
3. `POST /workspaces/{workspace_id}/parameters` -> `create_parameter`;
4. `PATCH /parameters/{parameter_id}` -> Parameter lifecycle-owner `update_parameter`;
5. `POST /parameters/{parameter_id}/lifecycle` -> Parameter lifecycle-owner `transition_parameter`;
6. `POST /workspaces/{workspace_id}/requirements` -> `create_requirement`;
7. `PATCH /requirements/{requirement_id}` -> legacy `update_requirement`;
8. `POST /workspaces/{workspace_id}/simulation-runs` -> `create_simulation_run`;
9. `POST /workspaces/{workspace_id}/decisions` -> `create_decision`.

This list is evidence for the definition base only. The full spec and readiness must regenerate the registered-surface inventory from their own exact master rather than copy this list as permanent truth.

### Confirmed owner overlap

`backend/app/modules/modeling/project_knowledge_owner.py` already contains transaction-capable owner primitives for Requirement creation/update/retirement, Decision creation/update/retirement, Assumption update and ModelSpec update. Its `_cas_update` checks workspace-scoped owner identity, requires `expected_updated_at`, performs a guarded update, and emits canonical edit audit evidence.

The legacy `create_requirement` and `create_decision` service functions already reuse owner transaction primitives. Therefore 127 must not replace those merely because they live behind the legacy modeling router; behavioral equivalence is the criterion.

### Confirmed Requirement PATCH bypass

The public `PATCH /requirements/{requirement_id}` accepts `RequirementUpdate`, which does not require `workspace_id` or `expected_updated_at`. Its service implementation dynamically updates the `requirements` row directly and commits without the Project Knowledge owner `_cas_update` contract. It can also accept `status`, `basis_kind` and `reconciliation_gate` directly.

This is an explicit 127 closure target unless a separately accepted change removes it before implementation.

### Caller-supplied authoritative-looking fields

Current create/request models expose several fields that require explicit ownership classification before readiness, including:

- ModelSpec: `status`, `maturity_status`;
- Assumption: `status`;
- Parameter create: `value_status`, `status`, `supersedes_parameter_id`;
- Requirement create/update: `status`, `basis_kind`, `reconciliation_gate` and typed criterion metadata;
- SimulationRun create: `status`, `started_at`, `completed_at`, `project_knowledge_revision_id`;
- Decision create: `status`, `basis_lifecycle_state`.

Presence in a Pydantic request model is not proof that a field is legitimate caller authority. The full spec must classify each field by canonical owner and transition semantics. Where a value is server-owned authoritative lifecycle state, unauthorized caller supply must fail with a typed, coded error rather than be silently ignored or normalized.

### SimulationRun boundary

SimulationRun creation currently persists run/evidence-oriented data and may bind a `project_knowledge_revision_id` only when that revision exists in the workspace and is `working`. 127 must not absorb SimulationRun into Project Knowledge merely for uniformity. The full spec must identify its canonical evidence/run owner and decide whether the public create surface is legitimate separate evidence ownership or an authority bypass.

## Definition boundary

127 owns the closure of **public canonical-write ambiguity at legacy modeling compatibility surfaces**.

The future full spec must:

1. enumerate every registered public modeling mutation endpoint on its exact base and trace it to the actual mutation owner;
2. classify the mutated record as canonical Project Knowledge/model truth, Parameter lifecycle truth, run/evidence state, or another already accepted owner;
3. classify every caller-supplied lifecycle/status/origin/revision-like field as legal intent, guarded transition input, server-owned output, or forbidden caller authority;
4. require typed, machine-readable rejection for forbidden authoritative inputs;
5. make retained compatibility routes behaviorally equivalent delegates to accepted owner primitives, including workspace isolation, stale/CAS behavior, provenance/audit and atomicity where those are owner invariants;
6. close the Requirement PATCH direct-update bypass unless fresh accepted runtime has already removed it;
7. preserve 098 as Parameter lifecycle/CAS authority rather than building a second Parameter writer;
8. classify SimulationRun against its real evidence/run owner and preserve separation when it is legitimately non-canonical evidence;
9. prove the public HTTP behavior, not merely the internal call graph;
10. avoid opportunistic schema redesign, historical-row backfill or unrelated error-taxonomy refactoring.

## Failure modes that must be closed

- **stale overwrite:** a compatibility PATCH bypasses owner CAS and overwrites a record changed since the caller reviewed it;
- **cross-workspace mutation:** an ID-only route updates a canonical record without proving the caller's workspace context against the owner contract;
- **lifecycle manufacture:** a request body directly sets a canonical lifecycle/status value that should only be produced by a guarded server transition;
- **silent authority laundering:** an unauthorized field is ignored/defaulted/normalized and the request succeeds, making it impossible for callers/tests to detect invalid authority assumptions;
- **audit/provenance loss:** a compatibility route changes canonical truth without the event/evidence emitted by the accepted owner;
- **partial-equivalence delegate:** a route calls a similarly named helper but omits one of workspace/CAS/audit/atomicity/reconciliation semantics;
- **false unification:** SimulationRun or another evidence surface is moved into Project Knowledge despite having a legitimate separate owner;
- **static-proof blind spot:** tests assert a call path or function name while public HTTP behavior still permits canonical-state manufacture.

## Required proof shape for full spec/readiness

The full spec must freeze an exact endpoint/field/owner disposition matrix. Readiness must then name deterministic behavioral tests over the registered HTTP mutation surface.

At minimum, the later acceptance plan must include:

- stale-token conflict tests for every retained canonical edit compatibility route whose owner uses optimistic concurrency;
- workspace-isolation tests for ID-addressed canonical mutations;
- negative request tests proving forbidden authoritative lifecycle/status/origin fields return stable typed/coded errors;
- audit/provenance assertions for retained delegates;
- positive compatibility tests proving allowed ordinary edits still work through the canonical owner;
- Requirement PATCH regression proof against the current direct-update failure mode;
- SimulationRun tests that prove its chosen owner boundary without fabricating Project Knowledge authority;
- an inventory/meta-test or equivalent deterministic check that fails if a newly registered public modeling mutation route is omitted from the disposition matrix.

Static AST/call-graph checks may supplement this evidence but cannot replace behavioral HTTP/integration proof.

## Non-goals

127 does not authorize:

- a new canonical Project/model/engineering-record store;
- a second Parameter lifecycle mechanism;
- broad API versioning or endpoint renaming for aesthetics;
- historical data migration/backfill unrelated to the minimum closure;
- a codebase-wide exception/error-contract refactor reserved for later hardening;
- SimulationRun absorption into Project Knowledge without evidence that its existing owner is wrong;
- new consumers of the legacy direct-write endpoints while closure is incomplete;
- frontend redesign or new product behavior beyond any minimum client adjustment strictly required by a changed typed error/request contract.

## Full-spec obligations before readiness

Before 127 may become `ready`, the full spec must re-read fresh exact master and freeze:

1. the complete registered mutation-route inventory;
2. the endpoint -> service -> persistence/owner trace for every route;
3. the exact field-level authority matrix;
4. the exact retained/redirected/rejected disposition for every route;
5. the minimum code paths to change and the owners explicitly left untouched;
6. the typed error contract for unauthorized canonical-state input and stale/conflict cases within this slice;
7. deterministic behavioral test files/commands and inventory-regression proof;
8. confirmation that no migration, new store, provider/egress behavior or unrelated architecture owner is introduced;
9. explicit proof that 040/098/112 invariants and run/evidence ownership remain intact.

If exact-master inventory shows that a mutation surface cannot be made equivalent without inventing a new owner or weakening an accepted owner invariant, readiness must block and re-derive rather than authorize a best-effort compatibility path.
