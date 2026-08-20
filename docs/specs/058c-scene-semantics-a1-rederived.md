# 058c — SCENE-SEMANTICS-A1 (operator-first re-derivation)

Status: **definition only**  
Date: 2026-08-20  
Depends on: 044, 071b, 085, 092

## 1. Purpose

Define the engineering semantics layer that sits on top of merged 092 scene binding and merged 071b Properties/working-configuration authority.

092 answers **which authoritative engineering object did the operator select?** 058c answers **which engineering model semantics, property groups, active model choices, linked values, derived values, formulas and dependencies are valid for that selected object?**

This definition is operator-first and does not reopen scene identity. Stable semantic target identity remains owned by 092 and canonical backend/domain records. Renderer mesh order, GLTF traversal order, raw node names, color, material and visual similarity remain non-authoritative.

This PR is definition only. It authorizes no runtime mutation. A separate exact-master readiness record must inspect the actual post-092 runtime contracts and prove the minimum authoritative data seam before 058c can become `ready`.

## 2. Current-runtime gap this slice closes

Merged 071b intentionally provides a generic contract-driven Properties editor over registered model input contracts. Its current runtime groups variables by broad categories (`Design`, `Operating`, `Properties`, `Model parameters`, `Equipment`), lets the operator choose a registered model implementation, edits numeric bindings, links compatible parameters by unit, and reuses deterministic preview/preflight.

Merged 092 now supplies stable scene-hit → canonical `part_id` engineering context for the selected object.

What is still deliberately absent is an authoritative object-semantic contract that can tell the UI, for the selected engineering object:

- which property groups are applicable;
- which fields are intrinsic geometry, operating values, linked values, model inputs or derived outputs;
- which mutually exclusive engineering model is active;
- which inactive-model values must be preserved but hidden;
- which values are read-only derived quantities;
- which formula/model/effective inputs may be shown under `fx`/Inspect;
- which dependency/source relationship owns a linked value;
- which validity/domain evidence is authoritative;
- which legacy states are inconsistent and must become blockers.

058c closes only that semantic gap. It does not create a second working-state owner, a new scene identity system or a general flowsheet editor.

## 3. Product contract

For a resolved 092 engineering selection, Properties must present the object's engineering meaning before machine metadata.

Normal L0 OPERATE presentation is:

- human engineering tag/name;
- object kind/type;
- relevant property groups only;
- effective value and declared unit;
- semantic source;
- editability/derived state;
- active model selector where one exists;
- real blocker/warning state from deterministic authority;
- direct operator actions already authorized by 071b.

L1 INSPECT may add:

- semantic provenance/source relationship;
- dependencies;
- formula/model identity;
- effective formula inputs and units;
- validity/domain evidence when authoritative;
- source navigation.

L2 AUDIT remains secondary/collapsed and may contain UUIDs, digests, exact record IDs, schema keys and raw technical metadata.

A selected object with no semantic contract remains truthfully inspectable as an identified engineering object; the frontend must not fabricate groups, formulas or model choices to avoid an empty Properties surface.

## 4. Authority and state ownership

058c must preserve the ownership boundaries already merged:

1. **092** owns stable scene-hit → semantic engineering target binding.
2. **071b** owns mutable working configuration, revision/Undo/Revert, deterministic preflight and run-start semantics.
3. Existing backend engineering/modeling/process/CAD records own engineering truth, units, record provenance and relationships.
4. Existing evidence/dependency authority owns lineage and evidence relationships.
5. **058c** may add only the minimum server-owned semantic contract/read projection required to describe applicable groups/model choices/formulas/dependencies where current authority is insufficient.
6. The frontend renders and edits through 071b; it does not persist its own object-model taxonomy, formula source of truth, model-activation truth or duplicate linked values.

A semantic contract may reference existing working bindings and source records. It must not copy canonical engineering truth into scene-owned or frontend-owned state.

## 5. Object property groups

The semantic contract must permit bounded engineering groups such as:

- Geometry;
- Operating;
- Hydraulics;
- Thermal;
- Optical;
- Fouling;
- Equipment;
- Material/property data;
- other domain groups only when readiness proves existing authority and a real current product need.

Group names are semantic presentation metadata, not justification for a new database taxonomy. Readiness must map them onto existing runtime fields/records/model contracts wherever possible.

The UI renders only groups/fields applicable to the selected object and active model contract. It must not display every field from every possible model as a giant sparse form.

For every exposed property, the authoritative contract must distinguish at least:

- semantic key;
- human label;
- declared unit or explicit unitless status;
- group/category;
- effective value state;
- required/optional state where relevant;
- editability/read-only state;
- semantic source kind;
- linked-source reference when applicable;
- active-model applicability;
- derived/formula availability when applicable.

Readiness may reduce this shape if exact runtime proves some field is unnecessary, but it may not shift authority into frontend heuristics.

## 6. Effective value and semantic source

The primary value shown is the value effective for the current working configuration/model.

Operator-facing source vocabulary reuses the 095 authority and may include, only when true:

- `User`;
- `Measured`;
- `CAD` / `CAD geometry`;
- `Linked stream` or another named linked engineering source;
- `Calculated`;
- `Scenario override` / working override;
- `Previous successful run` where later authority supplies that baseline;
- `Jarvis proposal` only after 097;
- `Material DB` or equivalent only where a real source exists.

The frontend must not infer source kind from record shape, label or route. Raw source IDs remain Inspect/Audit.

Linked values remain authoritative at their source. 058c may project them contextually into Properties but must not duplicate them into a new selected-object record merely for rendering convenience.

## 7. Empty, required and inactive semantics

`Empty` is explicit state, not a rendering failure.

- Optional empty for the active contract/model is neutral and non-blocking.
- Required empty for the active contract/model is a deterministic blocker under 071b/preflight authority.
- Fields that belong only to an inactive model are normally hidden from L0 rather than shown as empty.
- A value may remain stored for an inactive model without being effective in the current model.

058c must not create a frontend-only requiredness table. Requiredness comes from authoritative model/property contract data.

## 8. Mutually exclusive model choice

When two or more alternatives are incompatible descriptions of the same engineering behavior, they form one **model choice**, not independent booleans or competing assumption rows.

Examples may include a pressure-drop choice such as `Constant pressure` versus `Ergun equation`, but readiness must use only model alternatives actually represented by current backend/runtime authority.

Required semantics:

1. exactly one model is active in normal valid state;
2. the selector is human-readable and engineering-facing;
3. the active model determines which input sub-contract is effective/visible;
4. values belonging to inactive models are preserved and restored if the operator switches back;
5. inactive-model values do not participate in preflight/run input unless the authoritative active contract references them;
6. legacy/imported state with multiple mutually exclusive models active is a blocker, not silently normalized by array order;
7. legacy state with no required model selected is a blocker when the governing contract requires one;
8. model switching mutates the same 071b working configuration and participates in Undo/Revert/revision semantics;
9. model switching does not silently mutate canonical project data;
10. 058c does not authorize automatic AI model selection.

If current runtime has no authoritative representation capable of preserving inactive-model values, readiness must identify the smallest additive seam and prove why it is needed before implementation.

## 9. Derived values and `fx` Inspect semantics

A derived/calculated property is read-only in normal editing unless its authoritative contract explicitly says otherwise.

When formula evidence exists, an `fx` or equivalent Inspect affordance may expose:

- human model/formula name;
- authoritative equation or expression representation suitable for operator inspection;
- effective inputs by semantic label;
- each input's effective value and unit;
- output value and unit;
- source/dependency references;
- validity/domain evidence and warning state when real authority exists.

The frontend must never reconstruct an engineering formula from a model version hash, variable names, code source or guessed mathematical relationship.

A hash, script digest, implementation ID or model-version UUID is Audit metadata and never substitutes for the engineering equation.

If exact runtime can prove only a model name and dependency set but not an inspectable formula, the UI must show only that truthful subset. `Formula unavailable` is preferable to invented mathematics.

## 10. Dependency semantics

058c may project dependencies relevant to understanding the selected property, reusing existing dependency/lineage authority.

A dependency edge shown at L1 must have a semantic relationship the backend can justify, for example:

- linked process stream supplies pressure/temperature;
- CAD geometry supplies diameter/length;
- parameter record supplies an input value;
- calculated output depends on named effective inputs;
- selected model activates a specific sub-contract.

Dependency presentation does not create recomputation authority. Existing 050/051 lineage/staleness and 071b preflight remain authoritative where applicable.

Stale or unavailable linked sources must fail closed according to existing deterministic authority; 058c must not substitute a cached frontend value as authoritative merely because it is still visible.

## 11. Scene selection integration

058c consumes the semantic target from 092.

Required states:

- no selection → existing neutral Properties behavior;
- resolved semantic selection with supported contract → render object semantics;
- resolved semantic selection without supported semantic contract → show identified object plus truthful limited/unavailable semantics;
- unresolved/ambiguous/stale 092 selection → no semantic editing target;
- candidate/workspace/viewer-session change → any semantic read tied to the old target is stale and cannot overwrite the current Properties state.

A late semantic-contract response may not replace a newer target/model/working revision context.

058c may use the canonical `part_id`/semantic target as a lookup key, but it must not treat GLTF names or scene node metadata as model/property authority.

## 12. Working configuration integration

All editable semantic values and model-choice changes must flow through the same 071b working configuration.

Required behavior:

- effective working value updates immediately after a valid edit;
- dirty/Undo/Revert semantics remain coherent across ordinary values and model choices;
- changing model choice increments/invalidates the same working revision used by preflight;
- stale preflight cannot authorize a later model/value state;
- successful run may establish the next working baseline according to 071b;
- failed execution preserves working edits;
- no 058c edit auto-promotes canonical Parameters/Assumptions/Decisions;
- no separate scene/object local store becomes a second source of truth.

Readiness must inspect the current 071b `EngineeringProperties` controller and determine the minimum change necessary to support object-specific semantics without recreating its state machine.

## 13. Blockers and warnings

058c supplies semantic context to deterministic validation; it does not invent severity.

Examples of blocker classes that readiness must test where supported:

- required active-model property missing;
- multiple incompatible models active;
- required model not selected;
- unit mismatch against the authoritative contract;
- linked authoritative source missing/stale where execution requires it;
- derived value unavailable because required inputs/model are invalid;
- semantic target stale/unavailable.

When valid, normal UI remains quiet (`Ready`/`Valid`). Do not add permanent rows of model/unit/dependency PASS states.

## 14. Legacy and migration behavior

058c must be additive and fail-safe.

Existing post-092 candidates remain viewable even if no new semantic contract exists for their object kind. Historical candidates are not rewritten merely to satisfy new UI semantics.

Legacy model state is handled explicitly:

- multiple mutually exclusive active models → blocker;
- unsupported/unknown model identifier → unresolved semantic model state, not silent fallback;
- missing optional inactive-model values → acceptable;
- malformed semantic metadata → inert/error state, no execution or script interpretation in frontend;
- stale semantic-contract revision → re-read/fail closed rather than silently applying outdated edits.

Any schema migration proposed by readiness must be additive and minimum necessary. Definition does not pre-authorize a migration.

## 15. Responsive, containment and accessibility

058c must preserve merged 096 sidecar behavior and merged 092 selection context.

- Properties remains internally scrollable and does not increase page height.
- Effective 200%/compact width may use the existing `Jarvis | Properties` degradation.
- Model selectors, `fx`, source links, blockers and field controls are keyboard reachable.
- Focus remains predictable after model switch, field error navigation and scene-selection changes.
- Selection/model/source state is not communicated by color alone.
- Long labels, formulas, units and technical identifiers cannot create page-level horizontal overflow.
- Reduced-motion and system/light/dark invariants remain intact.
- No global visual-identity redesign is authorized.

## 16. Failure modes readiness must prove

The separate readiness record must inspect exact runtime and freeze deterministic/browser acceptance for at least:

1. selected scene object maps to the correct semantic property contract, never by mesh order;
2. two different object kinds do not receive the same property groups merely because they share labels/units;
3. inactive-model fields are not effective or submitted to execution;
4. switching model A → B → A restores preserved A values without canonical promotion;
5. legacy state with multiple incompatible active models blocks rather than silently picks one;
6. required empty active-model field blocks while optional empty remains neutral;
7. linked value remains source-owned and source navigation targets the real authority;
8. stale linked source cannot silently remain authoritative;
9. derived value is read-only and `fx` never invents equation/domain evidence;
10. formula Inspect shows only authoritative inputs/units/result and survives hostile/long labels safely;
11. stale semantic-contract response cannot overwrite a newer scene target/model/working revision;
12. candidate/workspace/viewer-session switch clears or re-resolves semantic context before edit;
13. semantic editing reuses 071b dirty/Undo/Revert and preflight rather than a second state owner;
14. model switch invalidates stale preflight and cannot execute an old normalized input set;
15. unsupported object/model yields truthful limited/unresolved semantics, not fabricated fields;
16. no selection/model interaction triggers provider calls or Jarvis mutation authority;
17. effective-200%, keyboard/focus, light/dark/system, reduced-motion and overflow behavior remain usable;
18. rollback/removal of 058c semantics leaves merged 092 scene binding and 071b generic working configuration usable.

## 17. Implementation scope to be frozen by readiness

Readiness must derive the exact allow-list from fresh master. The expected minimum implementation area is likely bounded to:

- existing engineering Properties controller/panel composition;
- existing BLUECAD semantic selection/context projection;
- existing API client types/reads;
- the smallest backend model/property semantic read seam if current contracts cannot express the required semantics;
- focused deterministic tests and evidence-only browser harness.

This list is not authorization to touch all of those paths. Readiness must prove each changed path is necessary.

No new provider route, durable scene store, frontend state framework, agent runtime, package family or general recomputation engine is authorized.

## 18. Non-goals

058c does **not** implement:

- scene identity/binding already owned by 092;
- 097 Jarvis engineering mutations, safe-fix execution or structured AI change-sets;
- 098 Edit/Active-Inactive/Archive/Supersede/Delete record lifecycle authority;
- 006b parametric variants or load-prior-run behavior;
- 058b variant comparison/history;
- a general Aspen-like editable process flowsheet;
- automatic engineering-model selection by AI;
- automatic canonical promotion of working values;
- new solver/recomputation authority;
- Notes/scratchpad;
- 062 routine grading UI;
- spreadsheet/bulk-edit implementation;
- global visual identity.

## 19. Readiness requirements

Before runtime authorization, a separate 058c readiness record from fresh master must:

1. inspect post-092 semantic target shape and current Properties integration;
2. inspect actual model input-contract/runtime metadata and existing engineering/modeling records;
3. inspect current parameter/source/provenance and dependency/evidence relationships;
4. inventory which object kinds currently have enough authority for semantic groups and which must remain limited/unresolved;
5. identify whether mutually exclusive model choice already has a server-owned representation; if not, prove the minimum additive representation needed;
6. identify whether inactive-model value retention can reuse 071b working state or needs a bounded extension;
7. identify which calculated values have authoritative formula/model/dependency evidence and explicitly reject invented formulas;
8. freeze exact semantic contract/request-response shape;
9. freeze exact file allow-list and migration decision;
10. prove 071b remains the sole mutable working-state owner;
11. freeze stale/candidate/workspace/model-revision behavior;
12. freeze deterministic tests and browser matrix covering §16;
13. document backward compatibility and rollback;
14. preserve 097/098/006b/058b, Notes, 062 and visual-identity boundaries.

If current runtime cannot support a required semantic behavior without a broad new subsystem, readiness must stop and report the gap rather than silently broadening 058c.

## 20. Acceptance criteria for eventual implementation

058c is complete only when exact-head evidence proves:

- a resolved 092 engineering target receives only authoritative applicable property groups;
- effective values/units/source semantics are truthful and source-owned;
- mutually exclusive model choice is explicit and exactly one active model governs effective inputs;
- inactive-model values are preserved without becoming effective;
- required/optional empty semantics remain deterministic;
- derived values are read-only and formula/dependency Inspect content is authoritative or explicitly unavailable;
- semantic edits/model switches reuse 071b working configuration, revision, Undo/Revert and preflight;
- stale semantic/model/preflight responses fail closed;
- no canonical project promotion, provider call or Jarvis mutation occurs implicitly;
- legacy/unsupported object/model states remain viewable and truthfully unresolved/blocked;
- 096 containment, accessibility, effective-200%, theme and overflow invariants remain intact;
- no 097/098/006b/058b behavior is smuggled into this slice.

## 21. Downstream seam

After 058c implementation is merged and registry-reconciled, 097 may define structured Jarvis Engineering Actions against the same stable semantic target and 071b working revision.

058c supplies the typed semantic target/model/property contract that 097 needs for stale-safe `old → proposed` change-sets. It does not itself grant Jarvis mutation authority.
