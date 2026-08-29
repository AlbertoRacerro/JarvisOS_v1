# 112 full-spec terminal closure — 2026-08-29

Authority: binding terminal amendment to `docs/specs/112-project-knowledge-core-1.md`, `docs/specs/112-full-spec-review-closure-2026-08-29.md`, and `docs/specs/112-full-spec-final-closure-2026-08-29.md` for the full-spec planning stage. Where this document is more specific, it supersedes those earlier clauses. It remains planning-only: `112` stays `planned`; no runtime implementation is authorized; a separate fresh exact-master readiness decision remains mandatory.

Reviewed exact PR head before this amendment: `bf9cd22dd393607c23119e3ab74be221343a7828`.

Exact-master evidence used here includes `backend/app/modules/modeling/models.py`, `backend/app/modules/modeling/service.py`, and `backend/app/core/schema.py`: `ModelSpecCreate` exposes `title`, `engineering_question`, `scope`, `status`, `maturity_status`, `assumptions_summary`, `inputs_summary`, `outputs_summary`, and `raw_payload`; `model_specs` has mutable `updated_at`; `model_versions` is already a distinct canonical table for executable/versioned implementation identity; and `simulation_runs` bind to `model_version_id` while their `output_payload` remains opaque.

This amendment closes the remaining material review gaps without creating a second live Project/model/run truth store.

## 1. Acceptance-criterion rule identity is stable and run-neutral

A Requirement-owned machine-evaluable acceptance-criterion rule MUST NOT name one concrete `run_id` as part of the criterion definition. A criterion describes the stable quantity/rule to evaluate; a validation event chooses the exact observed result that satisfies that rule for one exact working revision.

For `basis_kind=acceptance_criterion`, the minimum typed V0 rule therefore stores only stable criterion identity:

- exact `output_name` (or an existing canonical output-key field proven equivalent by readiness);
- comparator in the already frozen V0 set `< | <= | > | >= | ==`;
- finite target scalar;
- exact expected unit identity, including explicit unitless identity;
- rule/schema version.

No `run_id`, scalar-row id, simulation-run revision, or other concrete evidence instance belongs in the Requirement-owned rule. Changing the comparator, target, output name, expected unit, gate policy, or applicability changes the Requirement owner revision and invalidates older validation evidence as already specified.

Each immutable `project_knowledge_validation` row instead binds the stable rule to the exact evidence instance used for that evaluation:

- exact target working revision;
- exact Requirement/rule revision;
- exact `simulation_runs.id`;
- exact revision-neutral `simulation_run_scalar_results` identity;
- exact source payload/result digest and trusted extractor identity/version;
- exact validated input/source-basis digest;
- exact applicability-set digest and validator identity/version;
- outcome.

The validator selects a candidate run/scalar only through deterministic server-owned evidence lookup constrained by the target working revision's admissible model/version/input/source basis. It MUST NOT rewrite the criterion merely because a replacement run was produced. If no unique admissible exact result exists, evaluation returns the already accepted fail-closed `not_evaluable`/`recomputation_required` state rather than guessing.

Mandatory tests:

- one required criterion applies to two model versions and is evaluated against two different exact runs without mutating the Requirement/rule;
- a replacement run for the same working basis yields a new validation row bound to the replacement run while the criterion owner revision is unchanged;
- changed-output-name/comparator/target/unit changes the rule revision and makes old validation inadmissible;
- ambiguous or missing admissible runs do not choose an arbitrary run;
- wrong-workspace, stale-basis, source-digest drift, or incompatible model-version evidence fails closed.

## 2. Requirement applicability has explicit polarity and deterministic specificity

The previously frozen `requirement_applicability` relationship seam gains one required field:

`effect = include | exclude`

The relation remains applicability-only. Requirement text/gate/rule remains owned by `requirements`; model truth remains owned by `model_specs`/`model_versions`.

Each current relation is stale-protected and identified by workspace, Requirement, target kind, target id, effect, lifecycle/current-state, and exact revision token/audit. Active contradictory rows at the same exact `(workspace_id, requirement_id, target_kind, target_id)` are forbidden by the owner seam; migration/reads fail closed if contradictory current rows are found.

Applicability for one exact model version is resolved by specificity:

1. exact `model_version` relation, when present;
2. otherwise its parent `model_spec` relation, when present;
3. otherwise a `workspace` relation, when present;
4. otherwise not applicable.

At each specificity, `include` means applicable and `exclude` means not applicable. A more-specific active relation deliberately overrides a less-specific one. Therefore:

- workspace `include` + model-spec `exclude` => excluded for all versions of that spec unless a version has a more-specific override;
- model-spec `include` + model-version `exclude` => excluded for that exact version;
- model-spec `exclude` + model-version `include` => included only for that exact version;
- no relation => never inferred from prose, title, UI grouping, workspace co-residence, or graph proximity.

Draft/working operations may add, change, retire, or replace applicability relations only through exact stale-protected relation deltas. The cumulative accepted-ancestor + draft proposed-state projection applies those deltas before mandatory-set calculation. Preview/validation digests bind the exact relation revisions/effects used. Drift, contradictory rows, unsupported target identity, or incomplete ancestry makes mandatory-set calculation incomplete and blocks ordinary reconciliation.

Mandatory tests:

- model-spec include with one model-version exclude removes only the excluded version;
- model-spec exclude with one model-version include restores only the explicitly included version;
- workspace include overridden by model-spec exclude behaves deterministically;
- same-specificity contradictory current effects are rejected rather than resolved by insertion order;
- a parent working revision's include/exclude delta is inherited by an unrelated child change;
- stale relation effect after preview invalidates criterion membership and validation evidence.

## 3. ModelSpec mutation is exact in-place CAS; executable versions remain `model_versions`

The earlier phrase "update/version operation" is superseded. 112 V0 does **not** create a new `model_specs` row or `model_versions` row merely to edit Project Knowledge model-definition metadata.

For an existing canonical `model_specs` owner, 112 freezes one minimum connection-taking **in-place workspace-scoped CAS update primitive** using `model_specs.updated_at` as the owner revision token. It executes inside the caller-owned reconciliation transaction, writes immutable audit evidence, and updates `updated_at` exactly once on a material change.

The only ModelSpec fields mutable through 112 V0 are the existing descriptive/configuration fields:

- `title`;
- `engineering_question`;
- `scope`;
- `status`;
- `maturity_status`;
- `assumptions_summary`;
- `inputs_summary`;
- `outputs_summary`;
- `raw_payload`.

The following are never mutable through that operation:

- `id`;
- `workspace_id`;
- `schema_version` except through an independently accepted schema migration;
- `created_at`.

`model_versions` remains the sole canonical executable/versioned implementation owner. 112 MUST NOT silently create a model version, change `model_versions` rows, relabel an implementation, or treat a ModelSpec metadata edit as executable-version creation. If a proposed change actually requires a new executable model version or implementation artifact, the 112 change is impact/recomputation work that must route to the already-authorized modeling/version owner or remain unavailable until that owner has an accepted mutation path; final reconciliation cannot synthesize that version.

A ModelSpec CAS update is admissible only when the exact model-spec owner token, workspace, lifecycle/status assumptions, cumulative working-chain basis, and dependent validation/impact evidence still match. Any stale token or concurrent owner drift fails the whole reconciliation transaction closed.

Historical reconstruction remains provided by the already frozen reconciled snapshot manifest; that history evidence does not turn snapshots into a second live ModelSpec owner.

Mandatory tests:

- update each authorized ModelSpec field under exact workspace + `expected_updated_at` CAS and verify one audit/update-token transition;
- stale token, wrong workspace, missing id, or concurrent drift rejects without partial mutation;
- `id`, `workspace_id`, `schema_version`, and `created_at` cannot be changed through 112;
- a metadata-only ModelSpec reconciliation creates no `model_versions` row;
- a proposed executable/version-changing intent is not silently converted into a ModelSpec metadata edit or a new model version;
- multi-owner rollback restores ModelSpec state/audit together with every other 112 canonical effect.

## 4. Prior Requirement prose finding is closed by exact owner evidence

For avoidance of doubt, the human-readable Requirement/criterion content is the existing `requirements.statement`, with optional `requirements.rationale`. V0 MUST NOT read, add, or infer a `requirements.acceptance_criteria` prose column. Typed comparator/output/unit fields supplement this existing prose and do not replace it.

## Consolidated readiness consequence

PR #429 remains planning-only. Fresh readiness may advance 112 only if it proves all earlier full-spec obligations plus these terminal closures against then-current exact `master`:

1. criterion rules are stable/run-neutral and exact run/scalar evidence is bound only in immutable per-working-revision validation rows;
2. applicability relations carry explicit `include | exclude` polarity with deterministic `model_version > model_spec > workspace` specificity and fail-closed contradiction handling;
3. ModelSpec edits use the exact in-place workspace/CAS/audit primitive over the frozen existing field set, while executable/version identity remains exclusively `model_versions`;
4. Requirement prose remains `statement`/optional `rationale`;
5. all earlier immutable-snapshot, cumulative-chain, proposal-promotion, approval-idempotency, provisional-create, scalar-admission, required/advisory gate, retirement, atomic reconciliation, evidence-admission, and proposed-state impact obligations still hold.

If any of these proofs would require duplicate current truth, guessed ownership, an implicit run/applicability choice, or an executable-model mutation seam not already accepted, readiness MUST keep that capability unavailable rather than inventing semantics.