# 058c — SCENE-SEMANTICS-A1 fresh readiness

Date: 2026-08-20  
Exact base master: `ca2037f9537d457d64921bb13c0e999d28aac8a2`  
Definition: `docs/specs/058c-scene-semantics-a1-rederived.md`  
Model-choice amendment: `docs/specs/058c-definition-choice-amendment-2026-08-20.md`  
Prior closed readiness PR #315: evidence only, not authority  
Decision: **ready after this record merges and a separate registry reconciliation promotes `058c planned -> ready`**

## 1. Readiness decision

Fresh inspection of exact master after merged 092, 071b, the re-derived 058c definition, and the merged model-choice amendment proves one bounded production-real 058c V0 is implementable without a new durable semantic store, model-family database, provider path, scene authority, formula engine, general recomputation system, or second working-state owner.

The minimum implementation is:

1. an additive schema-v3 semantic envelope on the existing canonicalized model input-contract path;
2. one additive **semantic companion** registration for the already-reviewed bundled 047 geometry/hydraulics executable, preserving the existing legacy 047 registration/contract/label and CAD-LINK identity unchanged;
3. exact guarded-runner admission for that single server-known companion tuple;
4. a bounded extension of the existing 071b `EngineeringProperties` composition so the current 092 `bluecad-part` target filters object-applicable properties while generic required runner inputs remain reachable;
5. one deterministic linked-Parameter freshness guard so a superseded source cannot remain preview-ready or create a new run by bypassing the frontend.

The exact runtime still proves only one genuine production-authoritative same-family semantic option. Under the merged 058c model-choice amendment, V0 therefore shows truthful active engineering model identity and **does not fabricate an A/B selector, second option, inactive-option state machine, or impossible multi-active legacy state**. Full model-choice behavior remains mandatory if a later accepted slice introduces a genuine second mutually-incompatible same-family option.

The runtime still has no authoritative inspectable formula/output semantic contract. V0 therefore does not invent `fx`, equations, validity claims, or derived-property semantics from script text, hashes, output keys, labels, units, or engineering intuition.

## 2. Fresh exact-runtime findings

### 2.1 Merged 092 scene identity is sufficient and must remain sole target authority

`frontend/src/app/selection.ts` exposes resolved `bluecad-part` context with current workspace/candidate/artifact/viewer-session identity, exporter semantic key, canonical `partId`, and manifest-derived `partKind`.

`frontend/src/components/bluecad/sceneBinding.ts` and `sceneSelection.ts` resolve the semantic target against the exact current GLB digest and candidate-owned manifest binding, fail closed on unresolved/ambiguous cases, and reject renderer-order/name/material/colour/bounds identity shortcuts.

058c consumes this target. It does not modify scene identity, GLTF naming, scene binding, or manifest authority.

### 2.2 Merged 071b remains the sole mutable working-state/preflight owner

`frontend/src/components/engineering/EngineeringProperties.tsx` currently owns:

- selected model implementation ID;
- baseline and working binding maps;
- bounded Undo history;
- working revision;
- deterministic preview/preflight;
- field/revert-all operations;
- run request identity/retry reconciliation;
- successful-run baseline adoption.

The controller loads model implementations and Parameters through the existing API, builds the execution payload from the active implementation only, rejects stale preview responses by generation/revision/model identity, and creates a run only when preview state is `ready`.

058c must extend this owner rather than add a scene-owned or semantic-owned mutable store.

### 2.3 Current input-contract authority is schema v1/v2 and not object-semantic

`backend/app/modules/runner/input_contracts.py` currently accepts only schema versions 1 and 2.

Existing variable authority includes stable name, label, exact unit, required flag, broad category, description, optional numeric domain, and for v2 physical dimension/semantic basis. This is sufficient for generic 071b editing and unit/domain validation, but it does not authoritatively state:

- selected-object applicability;
- selected-object property group;
- semantic model family/option identity.

Those facts may not be inferred by the frontend from variable names, units, category, labels, implementation type, script path, model version order, or scene metadata.

The existing input-contract JSON is already canonicalized, hash-bound, persisted with each model version, validated on read/preview, and returned through the normal model-implementation read path. It is therefore the minimum sufficient location for additive semantic metadata; no new table/service is justified.

### 2.4 Existing reviewed 047 + CAD-LINK authority proves exactly one useful selected-object semantic relationship

`backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.contract.json` is the existing nine-input reviewed 047 contract.

`backend/app/modules/bluecad/cad_link.py` defines:

`GEOMETRY_INPUTS = ("tube_length", "tube_inner_diameter", "tube_outer_diameter")`

and deterministically creates the linked one-part BLUECAD tube proxy from those exact source inputs, with canonical `tube_run` part kind and exact legacy bundled-047 model identity checks.

Therefore the first production semantic companion may truthfully expose only:

| Variable | Selected-object applicability | Property group |
| --- | --- | --- |
| `tube_length` | `tube_run` | `Geometry` |
| `tube_inner_diameter` | `tube_run` | `Geometry` |
| `tube_outer_diameter` | `tube_run` | `Geometry` |

The remaining six reviewed 047 inputs — `reservoir_liquid_volume`, `target_liquid_velocity`, `liquid_density`, `dynamic_viscosity`, `minor_loss_coefficient`, and `pump_efficiency` — remain required generic model configuration in this V0. They are not intrinsic `tube_run` properties merely because they participate in the same calculation.

No other object kind or field is promoted into selected-object semantics in V0 without separate exact authority.

### 2.5 The semantic companion must be accepted by the normal guarded execution path

`backend/app/modules/runner/guarded_service.py` admits reviewed calc implementations through exact server-owned tuples, including version label, script digest and canonical input-contract digest.

A semantic companion has a distinct label and schema-v3 contract digest, so list/preview support alone would create a false capability: it could render in Properties yet fail at normal create/run.

Implementation must therefore add one exact server-known companion tuple to the existing guarded boundary. Admission may depend only on the readiness-authorized distinct companion label + exact reviewed 047 script digest + exact checked-in schema-v3 contract digest + expected implementation kind. Arbitrary schema-v3 `calc_v0`, label-only, family-only, schema-version-only, near-miss script/contract, or frontend-controlled admission remains rejected.

A successful normal create + run through `guarded_service` is merge-blocking acceptance.

### 2.6 Current linked-Parameter preview misses replacement freshness

`backend/app/modules/runner/service.py::preview_model_bindings` currently loads referenced Parameters with only `id`, `workspace_id`, `value`, and `unit`.

The input-contract validator can therefore prove existence/value/unit but cannot distinguish an accepted source from a row that replacement authority has retained for lineage after supersession.

Existing replacement authority already treats accepted/superseded lifecycle as real server-owned state. A superseded source must therefore fail closed for new preview/execution use; row existence is not freshness.

The old Parameter remains inspectable lineage and is never silently rewritten/relinked to its replacement. The operator must explicitly relink the working binding.

The same source-usability rule must be enforced before new run/job persistence in the direct runner-create path, because frontend preflight alone is not an integrity boundary.

This is a narrow consumption of already-existing lifecycle authority, not 098 lifecycle implementation.

### 2.7 Current formula/output authority is insufficient

Current input contracts describe inputs and domains; runner output JSON is not an accepted object-property/formula schema. Script source and script/model hashes are technical evidence, not operator-facing equations.

V0 therefore exposes no new derived/formula property contract. `fx` is absent where no authoritative formula semantics exist. `Formula unavailable` may be shown only where that truthful limitation improves comprehension.

### 2.8 Current model-choice availability is exactly one genuine semantic option

Fresh runtime inspection finds one justified production semantic companion: reviewed 047 M0 for the `geometry_hydraulics` family. There is no second genuine same-family alternative that is both authoritative and production-reachable through the guarded runner boundary.

Do not:

- clone the same executable under another label;
- group process1/process2/topology or unrelated implementations into the same family;
- admit arbitrary public `calc_v0` merely to create a selector;
- synthesize multiple-active legacy state that the exact authoritative state shape cannot represent.

For V0 the semantic family renders truthful active identity only. Existing generic 071b implementation selection must not regress, but unrelated generic implementations are not promoted into one semantic family by frontend inference.

## 3. Exact schema-v3 semantic envelope

Schema v3 is an additive extension of schema-v2 numeric/unit semantics. Schema-v1/v2 canonical bytes and validation behavior remain unchanged.

The V3 shape is:

```json
{
  "schema_version": 3,
  "evaluation_mode": "forward",
  "semantic_context": {
    "applicable_part_kinds": ["tube_run"],
    "model_family_key": "geometry_hydraulics",
    "model_family_label": "Geometry and hydraulics model",
    "model_option_label": "Reviewed 047 tubular-loop V0"
  },
  "variables": [
    {
      "name": "tube_length",
      "label": "Tube length",
      "unit": "m",
      "required": true,
      "category": "design",
      "property_group": "Geometry",
      "applicable_part_kinds": ["tube_run"],
      "description": "Illuminated tube centreline length.",
      "physical_dimension": "length"
    },
    {
      "name": "target_liquid_velocity",
      "label": "Target liquid velocity",
      "unit": "m/s",
      "required": true,
      "category": "operating",
      "property_group": "Operating",
      "applicable_part_kinds": [],
      "description": "Target mean liquid velocity inside the tube.",
      "physical_dimension": "velocity"
    }
  ]
}
```

### 3.1 Validation rules

`semantic_context` is required for schema v3.

- implementation-level `applicable_part_kinds`: 1–16 unique bounded stable identifiers; exact string matching only;
- `model_family_key`: stable bounded machine identifier;
- `model_family_label`: bounded non-empty human label with no edge whitespace;
- `model_option_label`: bounded non-empty human label with no edge whitespace;
- `variables[*].property_group`: required bounded non-empty human label;
- `variables[*].applicable_part_kinds`: required deterministic list of 0–16 unique stable identifiers;
- `[]` means **generic/non-object-specific runner input** and never selected-object property ownership;
- every non-empty variable-level part kind must be a member of implementation-level applicability;
- v3 retains v2 physical-dimension, semantic-basis, unit normalization, requiredness and numeric-domain behavior;
- duplicate variable names remain invalid;
- malformed/unknown semantic metadata fails closed;
- no wildcard, substring, fuzzy, category/name/unit, mesh, bounds or scene inference is permitted.

The semantic envelope is presentation/selection metadata only. It contains no executable expression, formula, HTML/Markdown renderer authority, arbitrary script, provider instruction or frontend event definition.

## 4. Production semantic companion

Implementation adds a distinct checked-in schema-v3 contract for the reviewed 047 executable and one idempotent bundled companion registration following the existing registration discipline.

The existing legacy 047 contract bytes, legacy version label, script, registration behavior, CAD-LINK model identity checks and existing model-version rows remain unchanged.

Required companion metadata:

- implementation-level applicability: `["tube_run"]`;
- family key: `geometry_hydraulics`;
- family label: `Geometry and hydraulics model`;
- option label: `Reviewed 047 tubular-loop V0`;
- object-specific `Geometry` variables: only the three CAD-LINK-proven geometry inputs;
- all six other reviewed 047 variables carry `applicable_part_kinds: []` and remain required generic inputs.

Registration is idempotent by workspace + distinct companion version label + exact script/contract digests. It may reuse the existing reviewed 047 model spec and executable copy semantics. No existing row is rewritten.

## 5. Properties presentation and ownership

For a resolved 092 `bluecad-part`:

1. v3 implementations whose implementation-level applicability exactly contains the current `partKind` are object-semantic candidates;
2. within the active applicable v3 implementation, only variables whose own non-empty applicability contains the exact current `partKind` render in selected-object property groups;
3. required/generic variables with `applicable_part_kinds: []` remain reachable in a clearly separated generic model-configuration section and continue to participate in preview/run;
4. v1/v2 implementations and non-matching v3 implementations remain valid generic 071b model configuration but never become selected-object models by frontend inference;
5. unsupported/null part kind shows the canonical selected object identity where available plus truthful limited/unavailable semantic state; generic 071b configuration remains usable.

The selected-object header uses canonical `partId` and `partKind`; raw UUID-like technical IDs and scene metadata remain secondary/Audit according to 095.

Source display is conservative and derived only from real binding state:

- manual non-empty working value without parameter link: `Working override`;
- parameter-backed value: `Linked parameter`, with actual source identity/status/provenance available in Inspect;
- empty: `Empty`.

Do not relabel arbitrary linked values as Measured, CAD, Material DB, Previous run, Validated, or Jarvis-suggested unless an accepted authority actually supplies that source meaning.

## 6. Model-choice behavior under the merged amendment

For the current exactly-one-option family:

- show active engineering model identity/label;
- no fake dropdown or disabled A/B control suggesting alternatives that do not exist;
- no new inactive-option cache, per-family baseline machinery, model-family Undo/Revert state, or synthetic multiple-active state is required for V0;
- existing generic 071b implementation switching behavior must remain usable and must not lose existing dirty/preflight/run semantics;
- generic implementation switching is not advertised as semantic same-family choice.

If a future accepted runtime slice adds a second genuine mutually incompatible option in the same family, the full 095 + 058c definition behavior becomes mandatory before exposure: one active option, option-specific sub-contract, inactive-value retention, A→B→A restoration, model choice in the same 071b revision/Undo/Revert semantics, and fail-closed handling of representable invalid legacy states.

## 7. Linked Parameter freshness

For executable bindings containing `source_parameter_id`:

- current authoritative source row must exist in the same workspace and satisfy existing value/unit/domain rules;
- `status='superseded'` is invalid for new working preview/execution use;
- no frontend cached value overrides server freshness;
- no silent substitution to a replacement Parameter;
- explicit operator relink is required;
- direct runner create with a superseded source fails before a new `simulation_runs` or `runner_jobs` row is persisted;
- immutable historical run snapshots are not rewritten.

No broader Parameter lifecycle redesign is authorized.

## 8. Stale-safety integration

Semantic presentation is bound to the existing authoritative context:

- workspace ID;
- current 092 selection state;
- candidate ID;
- artifact ID;
- viewer session ID;
- semantic key;
- canonical `partId` / `partKind`;
- active model implementation ID;
- current 071b working revision.

No new backend semantic fetch is required: model semantic metadata arrives via existing model implementation reads and selected-object identity via 092.

Required behavior:

- workspace change clears old semantic applicability before accepting new workspace model data;
- resolving/unresolved/ambiguous/stale scene states never become editable semantic targets;
- candidate/artifact/viewer-session change invalidates the prior semantic target immediately;
- model/value changes continue to invalidate stale preview through existing 071b revision/model guards;
- late model-list data from an older workspace cannot populate current semantics;
- semantic selection/presentation triggers no provider call, Jarvis mutation, canonical promotion or implicit Run.

## 9. Formula/derived behavior

Implementation-now: no new formula/output semantic contract.

- no `fx` solely because a variable has a domain or belongs to a model;
- no parsing Python source into equations;
- no inferred formulas from output keys or names;
- no script/model hash presented as engineering formula;
- no invented validity range beyond existing authoritative input-domain validation.

The definition remains forward-compatible with a later accepted formula/output semantic authority.

## 10. Migration and rollback

No SQLite migration is authorized or required.

- schema-v1/v2 model contract bytes and behavior remain unchanged;
- new semantic companion uses the existing model-version input-contract storage path;
- existing BLUECAD candidates/manifests remain unchanged;
- existing legacy 047 registration/CAD-LINK identity remains unchanged;
- unknown contract versions remain fail-closed;
- removal of frontend 058c rendering leaves merged 092 scene binding and generic 071b working configuration usable.

Once schema-v3 rows are created, v3 parsing remains part of backward-compatible runner read/validation support even if semantic UI is rolled back.

## 11. Exact implementation allow-list

Implementation may touch only the following minimum area unless a concrete exact-head failure proves one additional path necessary and the PR documents the minimum-necessary reason.

Backend:

- `backend/app/modules/runner/input_contracts.py` — additive schema-v3 parsing/canonicalization and source-status consumption where shared validation belongs;
- one new checked-in schema-v3 semantic 047 companion contract under `backend/app/modules/runner/examples/`;
- existing bundled registration code in `backend/app/modules/runner/service.py` and `backend/app/modules/runner/routes.py` only for the one idempotent semantic-companion registration path;
- `backend/app/modules/runner/guarded_service.py` only for the exact single-companion server-known execution tuple and pre-persistence superseded-source enforcement where the guarded path owns creation;
- focused runner/input-contract/registration/guarded execution tests.

Frontend:

- `frontend/src/api/client.ts` — additive schema-v3 semantic types and the narrow companion registration call if the current product has no existing normal registration call;
- `frontend/src/App.tsx` only to pass the current `StageSelection`/semantic target into the existing Properties owner;
- `frontend/src/components/engineering/EngineeringProperties.tsx` — exact object applicability/grouping, one-option active identity, conservative source display and same-owner stale behavior;
- `frontend/src/components/shell/ContextualSidecar.tsx` only if the existing sidecar composition requires a pass-through prop;
- focused frontend/source-contract tests or existing checker extension.

Evidence:

- smallest browser/evidence harness necessary for the frozen matrix below. Evidence-only workflow changes must not be merged into product scope unless independently required by an accepted infrastructure spec.

Explicitly excluded:

- 092 scene-binding/export code unless an actual regression proves a separate defect;
- new database table/migration;
- semantic service/endpoint/cache;
- new state framework;
- generic model registry expansion;
- arbitrary `calc_v0` admission;
- second fake 047 option;
- formula/expression/output-schema engine;
- provider/Jarvis path;
- 097/098/006b/058b behavior;
- Notes, routine 062 grading or global visual identity.

## 12. Deterministic acceptance

Exact-head implementation gates must prove at least:

1. schema-v1/v2 canonicalization, hashes and validation remain unchanged;
2. valid schema-v3 canonicalization is deterministic and retains v2 unit/domain semantics;
3. malformed semantic context, duplicate/empty invalid identifiers, omitted variable applicability, and non-subset object kinds fail closed;
4. `applicable_part_kinds: []` is accepted only as explicit generic/non-object-owned input semantics;
5. a fresh workspace can register the semantic 047 companion through the normal server-owned bundled path;
6. the companion is returned by normal model-implementation reads with its exact schema-v3 contract;
7. legacy bundled 047 registration preserves existing label/contract digest/script identity and CAD-LINK checks;
8. companion and legacy model remain distinct rows/identities; no rewrite/deduplication destroys legacy authority;
9. guarded runner accepts only the exact companion label + reviewed script digest + checked-in v3 contract digest + expected kind;
10. near-miss/arbitrary schema-v3 `calc_v0` remains rejected;
11. one normal companion job can be created and successfully run through `guarded_service`;
12. exact selected `tube_run` renders only `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` as object-specific `Geometry` properties;
13. the six remaining 047 inputs remain reachable as generic configuration and remain required by preview/run;
14. no variable becomes selected-object property through category/name/unit/mesh/scene inference;
15. one-option semantic family renders truthful active identity and no fabricated selector/alternative;
16. required/optional empty and domain/unit blocker semantics remain owned by existing input-contract/preflight authority;
17. valid non-superseded Parameter links preserve existing 071b validation behavior;
18. superseded linked Parameter is preview-invalid/not-ready; no silent replacement occurs;
19. direct runner create with superseded source fails before run/job persistence, while explicit relink to a valid replacement may recover readiness;
20. historical run snapshots are not rewritten;
21. stale workspace/scene/model/revision context fails closed and cannot overwrite current Properties;
22. no formula/`fx` evidence is fabricated;
23. semantic selection/presentation dispatches no provider/Jarvis action/run and promotes no canonical data;
24. removing the 058c frontend semantic layer leaves merged 092 identity and generic 071b Properties usable.

## 13. Browser acceptance matrix

Final implementation browser evidence must use the real production semantic companion and cover:

1. no semantic scene target: generic 071b Properties remains usable;
2. resolving/unresolved/ambiguous/stale 092 target: no editable selected-object semantic claim;
3. real resolved `tube_run` + semantic companion: canonical object header plus exactly three authoritative Geometry rows;
4. the six other required 047 inputs remain reachable in a clearly separated generic configuration area;
5. one-option semantic family displays active model identity without fake dropdown/alternative;
6. selected object with no applicable semantic implementation remains truthfully limited while generic configuration remains usable;
7. workspace/candidate/artifact/viewer-session switch clears old semantic context before editing the new target;
8. linked Parameter exposes conservative linked-source state; manual edit becomes working override rather than mutating the Parameter;
9. after that source is superseded, the binding becomes blocker/not-ready, old source remains inspectable, replacement is not auto-selected, explicit relink can recover readiness, and no Run is created while stale;
10. required empty remains blocker and generic required inputs cannot be hidden by object filtering;
11. malformed/unsupported semantic metadata fails safely without guessed grouping;
12. no authoritative formula metadata => no fake `fx` equation;
13. effective 200%/compact width preserves existing `Jarvis | Properties` behavior/internal scrolling;
14. keyboard/focus reaches relevant Properties controls and blocker navigation; selection changes do not strand focus;
15. long property/group/source labels contain/wrap without page-level horizontal overflow;
16. system/light/dark and reduced-motion invariants remain usable;
17. no semantic selection/model presentation causes provider/Jarvis mutation or implicit execution.

No browser fixture may fabricate a second engineering option solely to demonstrate A/B behavior.

## 14. Prepared but not implementation-now

The definition remains compatible with, but this V0 deliberately does not implement:

- two-plus semantic-family exclusive choice/inactive-option retention until a real second option exists;
- formula/derived-output `fx` contract;
- process-stream/CAD automatic value links beyond the exact object applicability metadata above;
- nominal geometry reverse-engineering from mesh/bounds;
- compositional simultaneous model families in one runner execution;
- persistent working drafts across restart;
- prior-run working baseline loading (006b);
- Jarvis engineering mutations/safe fixes (097);
- engineering-record lifecycle mutation (098);
- variant comparison/history (058b);
- Notes or routine 062 grading UI.

These deferrals must not be advertised as current capability.

## 15. Minimum-necessary test

### Test del minimo necessario

Criterio di accettazione della spec:
A resolved 092 engineering object must receive truthful object-applicable model/property semantics through a production-executable reviewed model path while 071b remains the sole mutable working/preflight owner, linked stale authority fails closed, and absent model alternatives/formula authority are not fabricated.

Questo lavoro serve a soddisfarlo? **sì** — current v1/v2 contracts cannot express exact selected-object applicability/property grouping; the existing 047/CAD-LINK relationship proves one useful production semantic mapping; current Parameter preview misses supersession status; and the guarded runner would reject a distinct semantic companion unless the exact server-known tuple is extended.

Il criterio è raggiungibile senza di esso? **no** for truthful selected-object semantics on the normal product path. It is reachable without a semantic database/service, second working store, formula engine, fake A/B option or broad runner redesign.

No broader infrastructure is authorized.

## 16. Merge and reconciliation sequence

This readiness PR is documentation only. `docs/specs/STATUS.md` remains `058c=planned` while this record is under review.

After exact-head deterministic gates and one independent exact-head PASS:

1. merge this readiness with `expected_head_sha`;
2. verify fresh master;
3. open one docs-only registry reconciliation that changes only current 058c lifecycle truth: `planned -> ready`, Implementation PR remains `—`, and the merged definition + amendment + this readiness are recorded;
4. gate/review/merge that reconciliation;
5. only then open exactly one bounded 058c runtime implementation PR and set `058c=in_review` with that PR;
6. after 058c implementation merge/reconciliation, advance to 097. No 097 runtime work is authorized before that point.

Closed PR #315 remains evidence only and must not be reopened or merged.