# 113 — MODEL-DOSSIER-1

**Spec gate:** definition 113

## Purpose

Add one read-only, exact-identity model dossier surface over the model/run/evidence/artifact owners already present on exact source master `c590afddeec39393074600a91ddf23d14abdfbfd`.

This slice must make the existing `/memory/models` operator surface useful without creating a second model store, a frontend-owned canonical model, a write path, or inferred health/currentness claims.

## Exact-master inventory

At the planning base:

- `backend/app/core/schema.py` already owns `model_specs`, `model_versions`, `simulation_runs`, `run_artifacts`, `artifacts`, freshness/evidence tables, and the 112 `project_knowledge_revision_id` run binding.
- `backend/app/modules/modeling/models.py` exposes ModelSpec and SimulationRun read contracts but has no bounded exact-version dossier aggregate.
- `backend/app/modules/modeling/service.py` owns ModelSpec/SimulationRun persistence and Project Knowledge composition. 113 must compose those owners rather than add another model truth.
- `backend/app/modules/modeling/routes.py` exposes model-spec and simulation-run reads but no exact model-version dossier read endpoint.
- 050/051 remain dependency/freshness authority; 077 remains canonical evidence provenance/classification authority; 112 remains Project Knowledge write/revision authority.
- The final operator frontend already reserves `/memory/models`; 113 may bind it to truthful dossier data but may not introduce model mutation.

## Scope

Implement a bounded read projection that can answer, for an exact workspace/model/model-version selection where evidence exists:

1. model identity: `model_spec_id`, exact `model_version_id`, version label, implementation kind, status, created-at, and immutable stored input-contract digest when present;
2. descriptive ModelSpec fields already owned by `model_specs`;
3. exact-version run summary derived only from persisted `simulation_runs` rows bound to that model version;
4. bounded artifact references from existing `run_artifacts`/`artifacts`, preserving exact IDs/roles/digests/source refs where persisted;
5. bounded evidence/freshness disclosures from the existing 044/051/077 owners where exact record linkage can be proven;
6. Project Knowledge revision identity for runs where 112 persisted `project_knowledge_revision_id`;
7. explicit `unknown`/empty disclosures when the current store does not prove a field.

A minimal server-owned aggregate endpoint is authorized if current individual endpoints cannot produce the dossier without frontend N+1 joins or direct knowledge of SQLite ownership. The aggregate is a projection only and must not persist/cache its own canonical state.

## Identity and boundedness contract

- Every detail dossier is keyed by an exact existing `model_version_id`; never infer a version from “latest”, title, recency, route state, or frontend selection history.
- Workspace ownership must be verified server-side for every returned row.
- All child collections are deterministically ordered and bounded. Default and maximum bounds must be explicit in code/tests; no unbounded run/artifact/evidence fan-out.
- Missing/corrupt optional JSON/payload fields fail closed to an explicit unavailable/invalid disclosure; do not fabricate normalized values.
- Do not label a model `Healthy`, `PASS`, `Ready`, `Current`, `Aligned`, or equivalent unless that exact semantic claim already exists as persisted authority owned by the relevant subsystem.
- Run status is returned as stored run status, not converted into model quality.
- Freshness/staleness is returned only from existing 051 evidence that can be bound to the exact relevant record.

## API contract

The implementation may choose the smallest current-code-compatible route shape, but the resulting server contract must provide:

- a bounded workspace dossier index suitable for selecting exact model/version identities;
- an exact-version dossier detail read;
- structured fields rather than frontend parsing of `raw_payload`/free-form notes;
- safe artifact/source references as identifiers/metadata only; no arbitrary filesystem path disclosure;
- 404 for missing exact model/version or cross-workspace identity mismatch;
- no POST/PATCH/DELETE and no hidden write side effect.

If one endpoint can cleanly serve both index and detail without semantic ambiguity, do not add two merely for symmetry.

## Frontend contract

Bind `/memory/models` to the server-owned read projection while preserving the accepted 100f/100g composition:

- compact model/version selection from real returned identities;
- exact-version dossier sections for scope/question, assumptions/input/output summary, contract/version identity, persisted run history, artifacts/evidence, and provenance disclosures where present;
- multiple exact versions must remain distinguishable;
- empty/unknown/unavailable states are explicit and non-alarming;
- no edit/save/approve/run/provider/filesystem/GitHub action is added;
- no production fixture values and no React-owned canonical model/dossier store.

The frontend may keep local presentation/selection state only.

## Files likely touched

Expected implementation boundary, subject to fresh verification before coding:

- `backend/app/modules/modeling/models.py`
- one existing modeling/read service module or one small cohesive read-projection module under `backend/app/modules/modeling/`
- `backend/app/modules/modeling/routes.py`
- focused backend tests
- existing frontend API client/read helpers
- existing `/memory/models` surface/components
- focused frontend conformance/browser harness where already used

No schema/migration file is expected. Touching `backend/app/core/schema.py` requires stopping and re-deriving readiness because this planning decision assumes zero new durable store/migration.

## Non-goals

- canonical model or assumption mutation;
- new model-version creation/versioning authority;
- “latest/current/best” promotion policy;
- solver execution, rerun, validation or recomputation;
- new evidence/freshness semantics;
- semantic search/RAG;
- Literature work from 114;
- Project Search work from 115;
- Jarvis context/propose actions from 121;
- direct filesystem/provider/GitHub/frontend execution authority;
- closure/refactor of legacy modeling write endpoints.

## Failure modes to prove

1. cross-workspace model-version probing returns no dossier;
2. a ModelSpec with no model versions produces a truthful empty index state, not a synthetic version;
3. a version with zero runs returns an empty run collection;
4. many runs/artifacts/evidence rows are deterministically bounded;
5. malformed optional payload/metadata cannot crash the dossier or become fabricated structured truth;
6. missing artifact rows or stale foreign references degrade to explicit unavailable evidence without filesystem probing;
7. exact version A never leaks runs/artifacts from sibling version B;
8. 051 freshness state is not invented from run timestamps/status;
9. frontend route renders unknown/empty states without fixture metrics;
10. browser-visible selection of two versions preserves exact identity and changes only presentation/context of the selected dossier.

## Acceptance criteria

- Server returns a bounded exact-version dossier entirely from existing authoritative owners with no persistence side effect.
- Workspace and exact-version isolation are deterministic and tested.
- No new schema/table/migration/cache/canonical store exists.
- `/memory/models` displays real exact-version identity and bounded truthful detail without mutation affordances or fabricated status/metrics.
- Production frontend defaults contain no dossier fixture data.
- Existing 112 Project Knowledge and 050/051/077 authority is composed, not duplicated.
- Full backend tests and Ruff pass on the frozen implementation head.
- Frontend build passes on the frozen implementation head.
- Because this slice changes a visible frontend surface, exact-head browser proof is required for `/memory/models`, including empty state and at least two-version selection using proof-only harness data if production data is unavailable.
- No current P0/P1/blocking P2 or unresolved material review finding remains.

## Deterministic test plan

Focused backend tests must cover exact identity/isolation, bounded ordering, zero-run, missing-artifact, malformed optional metadata, and no-write behavior. Focused frontend tests must cover truthful empty state, exact-version switching, and absence/disabled state of unauthorized actions. Terminal gates are the repository-required backend suite/Ruff plus frontend build and browser proof for the visible delta.

## Planning-compression eligibility

113 is eligible for the post-112 low-risk planning-compression path because the accepted boundary is read-only, additive/reversible, introduces no credential/provider/egress authority, no new durable store, no migration, no destructive action, and no owner reassignment. Definition, full specification, and a separate readiness decision may therefore be reviewed in one planning PR while remaining independently inspectable.

## Minimum-necessary test

The existing model-spec/run endpoints do not provide one bounded exact-version projection and would otherwise force the frontend to know multiple persistence owners and perform unbounded/N+1 joins. A server-owned read aggregate is therefore justified only to centralize exact identity, workspace isolation and bounded disclosure; a new table/cache/model store is not justified.
