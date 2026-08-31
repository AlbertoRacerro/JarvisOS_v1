# 127 CANONICAL-WRITE-PATH-1

Status: full specification / planning authority only

Exact source master: `872683a8077da00de9fff6f623e4c1f9f543254e`.

This document refines the accepted 127 definition. It does not authorize runtime implementation and does not change `docs/specs/STATUS.md`; `127=planned` remains the sole live work state until a separate fresh readiness decision is accepted and reconciled to `ready`.

## Purpose

Close public canonical-write ambiguity in the legacy modeling surface without creating a replacement domain store or a second lifecycle owner. Retained compatibility mutations must either delegate to the already accepted owner with equivalent workspace/CAS/audit/atomicity semantics, or reject caller attempts to manufacture server-owned state with stable machine-readable errors.

The implementation target is behavioral equivalence at the HTTP boundary, not merely a preferred internal function name.

## Fresh exact-master inventory

On source master, `backend/app/modules/modeling/routes.py` registers these public mutation routes:

1. `POST /workspaces/{workspace_id}/model-specs` -> `service.create_model_spec`;
2. `POST /workspaces/{workspace_id}/assumptions` -> `service.create_assumption`;
3. `POST /workspaces/{workspace_id}/parameters` -> `service.create_parameter`;
4. `PATCH /parameters/{parameter_id}` -> `parameter_lifecycle.update_parameter`;
5. `POST /parameters/{parameter_id}/lifecycle` -> `parameter_lifecycle.transition_parameter`;
6. `POST /workspaces/{workspace_id}/requirements` -> `service.create_requirement` -> `project_knowledge_owner.create_requirement_in_transaction`;
7. `PATCH /requirements/{requirement_id}` -> `service.update_requirement` -> direct SQL update;
8. `POST /workspaces/{workspace_id}/simulation-runs` -> `service.create_simulation_run`;
9. `POST /workspaces/{workspace_id}/decisions` -> `service.create_decision` -> `project_knowledge_owner.create_decision_in_transaction`.

The inventory must be regenerated at readiness if master moves. A deterministic inventory/meta-test must later fail when a newly registered modeling mutation route lacks a disposition entry.

## Frozen owner/disposition matrix

| Public route | Record class | Accepted owner | Disposition for 127 |
| --- | --- | --- | --- |
| `POST /workspaces/{workspace_id}/model-specs` | Project Knowledge canonical record creation | existing modeling creation path + Project Knowledge invariants | Retain creation behavior only if readiness proves caller fields below are legitimate creation intent; do not add a second edit owner. |
| `POST /workspaces/{workspace_id}/assumptions` | Project Knowledge canonical record creation | existing modeling creation path + Project Knowledge invariants | Retain creation behavior subject to field-authority proof; later edits remain Project Knowledge owner-mediated. |
| `POST /workspaces/{workspace_id}/parameters` | Parameter proposal/lifecycle truth | 098 Parameter lifecycle/replacement owners | Preserve 098. No Project Knowledge rewrite. Reject any field combination that would bypass accepted replacement/lifecycle rules. |
| `PATCH /parameters/{parameter_id}` | Parameter mutable attributes | 098 Parameter lifecycle owner | Retain as accepted 098 owner path. 127 must not duplicate CAS/lifecycle logic. |
| `POST /parameters/{parameter_id}/lifecycle` | Parameter lifecycle truth | 098 Parameter lifecycle owner | Retain unchanged except regression coverage proving 127 did not weaken it. |
| `POST /workspaces/{workspace_id}/requirements` | Project Knowledge Requirement creation | `project_knowledge_owner.create_requirement_in_transaction` | Retain owner-backed creation. Freeze legal creation intent below. |
| `PATCH /requirements/{requirement_id}` | Project Knowledge Requirement edit | `project_knowledge_owner.update_requirement_in_transaction` | Close current direct-SQL bypass. Compatibility PATCH may remain only as an equivalent owner delegate requiring workspace + expected revision token; otherwise remove/reject it. |
| `POST /workspaces/{workspace_id}/simulation-runs` | run/evidence state | existing SimulationRun service/evidence boundary | Retain as separate evidence owner. Do not absorb into Project Knowledge. Validate any referenced Project Knowledge revision as a working revision in the same workspace. |
| `POST /workspaces/{workspace_id}/decisions` | Project Knowledge Decision creation | `project_knowledge_owner.create_decision_in_transaction` | Retain owner-backed creation; freeze legal creation intent below. |

No direct `service.update_requirement` SQL write may remain reachable from a public runtime route after 127 acceptance. If the helper remains for migration/test compatibility, it must be non-public, explicitly bounded, and not a new consumer path.

## Field-level authority matrix

Field presence in a Pydantic request is not authority. Readiness must re-verify these fields against fresh owner semantics; implementation must reject forbidden caller authority rather than silently drop or normalize it.

### ModelSpec creation

- legal caller intent: `title`, `engineering_question`, `scope`, summaries and raw descriptive payload;
- `status` and `maturity_status` are authoritative-looking fields. They may remain caller-supplied only if readiness proves creation semantics intentionally permit the currently accepted initial domain values. They must not become an unrestricted lifecycle-transition surface merely because they exist on `ModelSpecCreate`;
- later mutation remains Project Knowledge owner/CAS territory.

### Assumption creation

- legal caller intent: statement, scope, confidence, source and notes;
- `status` is allowed only as an explicitly frozen creation-state intent among accepted initial states. Later canonical edits must use the Project Knowledge owner contract.

### Parameter creation and lifecycle

- `name`, value/unit/evidence fields are proposal input subject to 098 validation;
- `supersedes_parameter_id` is replacement intent and remains governed by the 098 replacement contract;
- `status`, `value_status`, and lifecycle transitions must not be reinterpreted by 127. Readiness must confirm accepted creation defaults/intent and preserve `parameter_lifecycle` as the sole edit/lifecycle owner;
- 127 must not expose lifecycle state as a generic Requirement/Project Knowledge-style patch field.

### Requirement creation/edit

- ordinary canonical content: `statement`, `rationale`, `notes`;
- `status` is lifecycle-like. Generic edit must not manufacture retirement or activation if the accepted owner defines a guarded transition; retirement remains the dedicated owner operation where applicable;
- `basis_kind`, `reconciliation_gate`, and typed criterion metadata are canonical Project Knowledge semantics and may be changed only through the Project Knowledge owner under workspace/CAS/audit control;
- a compatibility edit request must carry `workspace_id` and `expected_updated_at` (or the exact owner-equivalent token frozen at readiness); an ID-only write is not equivalent;
- forbidden lifecycle authority must receive a stable coded error rather than success with ignored/normalized input.

### SimulationRun creation

- run label, model binding, inputs/parameters/outputs, timestamps/notes and run status remain evidence/run-owner concerns, not Project Knowledge owner fields;
- `project_knowledge_revision_id` is a reference, not authority to create/promote/reconcile Project Knowledge. It is valid only when the referenced revision exists in the same workspace and is `working`;
- 127 must not add a Project Knowledge mutation as a side effect of creating a run.

### Decision creation

- title/text/rationale/link/notes are creation intent;
- `status` and `basis_lifecycle_state` are authoritative-looking. Readiness must freeze which values are legal creation state versus owner-only lifecycle transition; retirement/update stays Project Knowledge owner-mediated.

## Critical merged-state invariant

Current `RequirementCreate`/`RequirementRead` enforce a cross-field typed-criterion invariant, but `RequirementUpdate` does not. Therefore routing the legacy PATCH through `RequirementProjectUpdate` and the existing `_cas_update` is not by itself sufficient.

A partial patch can be syntactically valid while the post-merge Requirement is semantically invalid. Examples:

- a non-criterion Requirement changes `basis_kind` to `acceptance_criterion` while supplying only part of the typed criterion tuple;
- an acceptance criterion changes `basis_kind` away from `acceptance_criterion` while stale `criterion_*` values remain;
- the database commit can succeed and only subsequent `RequirementRead` response validation detect the invalid row.

127 therefore freezes this rule: **the Project Knowledge Requirement mutation path must validate the complete post-merge Requirement state before any durable update or audit event is committed.** Response-model validation after persistence is never the first semantic guard.

The smallest acceptable implementation may merge the current row plus requested changes into the existing canonical Requirement schema and validate that candidate before `_cas_update`; it must not invent a second Requirement schema or duplicate domain rules in the route.

Failure must be atomic: rejected invariant transitions leave row contents, `updated_at`, and audit/event history unchanged.

## Canonical Requirement compatibility contract

If `PATCH /requirements/{requirement_id}` is retained, its minimum accepted request contract is owner-equivalent:

- `workspace_id` required;
- `expected_updated_at` required;
- only the exact allowed canonical edit fields exposed;
- lifecycle transitions that have dedicated owner commands are not writable through generic edit;
- full post-merge Requirement validation before update;
- stale token -> coded conflict;
- wrong workspace / absent owner -> stable coded not-found/isolation response without cross-workspace disclosure;
- successful material edit -> exactly one owner audit event with prior/result evidence;
- no-op edit -> owner-defined no-op behavior, without fabricated audit or timestamp churn;
- transaction atomicity across validation, CAS mutation and audit emission.

The implementation may replace the old request model with an owner-equivalent compatibility model or remove the legacy PATCH if no accepted consumer requires it. It must not keep the current weaker ID-only body for compatibility convenience.

## Typed error contract

127 does not authorize a repository-wide error taxonomy refactor. It requires only stable machine-readable codes at affected public compatibility boundaries:

- stale optimistic-concurrency token -> `409`, owner code equivalent to `owner_stale`;
- record absent from supplied workspace -> owner-coded not-found/isolation result; implementation must not leak that the same ID exists elsewhere;
- forbidden authoritative/lifecycle input -> `400`/`422` with a stable 127-scoped or existing owner code;
- invalid post-merge Requirement semantic state -> `400`/`422` with stable code and no mutation;
- invalid Project Knowledge revision reference on SimulationRun -> existing typed/coded validation response or minimum local adapter, without changing the run owner.

FastAPI/Pydantic transport validation may remain `422`; owner/domain failures must not collapse into generic `500` or free-text-only success/failure where deterministic tests need to distinguish authority violations.

## Frontend/client compatibility boundary

Fresh readiness must inventory all first-party consumers of the mutation routes before changing a contract. No new consumer may be added to the legacy direct-write Requirement path.

If the current frontend calls `PATCH /requirements/{id}`, the minimum client adjustment is to send the owner-equivalent workspace/CAS token and surface stale/authority errors. A frontend redesign, new editor workflow, optimistic local authority, or silent retry is outside 127.

A stale response must not be automatically replayed against a newer `updated_at`; the caller must re-read/reconcile before a new user-authorized attempt.

## Migration and reconciliation viability

127 closes public runtime ambiguity; it must not disable accepted internal migration or reconciliation work merely because those paths mutate canonical tables.

Readiness must identify every direct canonical-table writer that remains after public-route closure and classify it as one of:

1. accepted owner primitive;
2. schema/migration/bootstrap operation not reachable as a product API;
3. explicit reconciliation primitive already accepted by 112/098;
4. legacy debt that must be removed in 127.

No broad `backend/app/modules/modeling/**` exemption is acceptable. Each retained non-owner writer must have an exact symbol/path rationale and proof it cannot become a public second writer.

## Deterministic behavioral proof

Readiness must bind concrete test files and commands. Implementation acceptance must include at least:

| Case | Expected |
| --- | --- |
| Requirement compatibility edit with current workspace/token and ordinary content | success through Project Knowledge owner; persisted value and one audit event |
| stale Requirement token | `409` coded conflict; row/audit unchanged |
| Requirement ID paired with wrong workspace | no mutation and no cross-workspace disclosure |
| generic Requirement edit attempts forbidden lifecycle transition | coded rejection; no mutation/audit |
| non-criterion -> acceptance criterion with incomplete typed metadata | reject before commit; row/timestamp/audit unchanged |
| acceptance criterion -> non-criterion while criterion metadata would remain | reject, unless the frozen request explicitly clears all criterion fields atomically; no stale metadata allowed |
| valid atomic criterion transition with complete metadata | succeeds exactly once and remains `RequirementRead`-valid |
| response serialization after successful Requirement mutation | cannot be the first detector of a domain invariant failure |
| no-op Requirement owner edit | no fabricated audit/timestamp change if current owner contract defines no-op |
| Parameter edit/lifecycle regression | continues through 098 owner with existing stale/workspace rules |
| SimulationRun with foreign/non-working Project Knowledge revision | reject without Project Knowledge mutation |
| SimulationRun with valid same-workspace working revision | create run evidence only |
| newly registered modeling mutation route absent from disposition inventory | deterministic meta-test fails |

Static import/call checks may supplement but cannot substitute for these HTTP/integration behaviors.

## Minimum implementation paths

Readiness may authorize only paths demonstrated necessary by the fresh inventory, expected to be a subset of:

- `backend/app/modules/modeling/models.py` for the minimum owner-equivalent compatibility request / shared merged-state validation shape;
- `backend/app/modules/modeling/routes.py` for compatibility routing and typed owner error mapping;
- `backend/app/modules/modeling/service.py` only to remove/retire the public direct Requirement write or preserve a strictly non-public bounded helper;
- `backend/app/modules/modeling/project_knowledge_owner.py` for pre-commit merged-state validation if that is the narrowest canonical seam;
- focused backend HTTP/owner tests and one deterministic mutation-route inventory/meta-test;
- `frontend/lib/api.ts` or the exact fresh consumer path only if the retained compatibility request contract needs workspace/CAS tokens;
- `docs/specs/STATUS.md` only for normal lifecycle bookkeeping.

No schema migration, new table/store, provider, egress, AI routing, general frontend redesign, or unrelated domain refactor is authorized.

## Acceptance criteria

1. Fresh registered mutation-route inventory is complete and deterministically guarded against omissions.
2. Every route has an explicit record class, accepted owner and retained/redirected/rejected disposition.
3. Public Requirement editing no longer reaches the current direct SQL update path.
4. Every retained Project Knowledge edit route is behaviorally equivalent for workspace isolation, optimistic concurrency, audit/provenance and atomicity.
5. Requirement edits validate the complete post-merge canonical state before durable mutation; invalid cross-field transitions cannot commit and then fail only during response validation.
6. Caller attempts to manufacture owner-only lifecycle/authoritative state fail with stable machine-readable errors; no silent laundering/normalization.
7. 098 Parameter lifecycle/replacement ownership remains unchanged and regression-green.
8. SimulationRun remains a separate run/evidence owner and cannot manufacture Project Knowledge authority; revision references remain same-workspace + working-only.
9. Legitimate migration/reconciliation primitives remain viable and are individually classified; no broad direct-write exemption is introduced.
10. Existing required backend/frontend/BLUECAD/architecture/PR-attention terminal gates remain green on the frozen implementation head.
11. No new store, migration, provider, egress behavior, product workflow or 113–126 work is introduced.

## Failure modes to prevent

- stale overwrite through a compatibility path;
- ID-only cross-workspace canonical mutation;
- lifecycle/status manufacture through generic payload fields;
- silent dropping/defaulting of unauthorized fields;
- owner delegate that omits audit or CAS;
- post-commit response validation discovering a corrupted Requirement row;
- partial typed-criterion transition leaving semantically impossible metadata;
- automatic stale retry that launders a conflict into a last-write-wins update;
- migration/reconciliation broken by an overbroad direct-write ban;
- SimulationRun falsely unified into Project Knowledge;
- a new route added after readiness without owner/disposition review;
- 127 accidentally becoming a second Parameter lifecycle owner.

## Non-goals

- no historical-row backfill;
- no broad API versioning/renaming;
- no global error framework;
- no new Project Knowledge or engineering-record store;
- no Parameter lifecycle redesign;
- no SimulationRun redesign;
- no frontend visual redesign;
- no AI/provider/egress work;
- no reopening 113–126;
- no implementation before separate readiness acceptance and `STATUS.md=ready`.

## Required readiness packet

Before 127 may become `ready`, readiness must bind to a fresh exact master and provide:

- regenerated route and first-party consumer inventory;
- exact endpoint -> service -> persistence/owner trace;
- final field-authority matrix, including initial creation values versus guarded transitions;
- exact disposition of the current Requirement direct-write helper;
- exact merged-state validation seam and typed error mapping;
- migration/reconciliation direct-writer classification;
- concrete allowed implementation paths;
- concrete test files/commands mapped to every acceptance criterion;
- proof that 040/098/112 invariants remain intact;
- terminal gate plan and residual risks.

If fresh evidence shows a retained compatibility route cannot achieve owner equivalence without weakening an accepted invariant or inventing a new owner, readiness must block and choose removal/rejection rather than authorize a best-effort delegate.

## Minimum-necessary test

The closure criterion is one canonical write authority per canonical record class while preserving legitimate owners and compatibility where semantics are genuinely equivalent.

The minimum sufficient 127 implementation is therefore a narrow Requirement compatibility closure plus deterministic proof over all existing mutation surfaces. It does not justify architecture-wide rewrites, new persistence abstractions, or cleanup of unrelated legacy code.