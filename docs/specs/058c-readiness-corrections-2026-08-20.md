# 058c — SCENE-SEMANTICS-A1 readiness corrections

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20.md`  
Reason: close exact-head review findings on per-property object applicability and model-choice/baseline Undo/Revert semantics before readiness can merge.

This correction record is part of the 058c readiness authority. Where it conflicts with the original readiness text, **this file wins**. All untouched readiness constraints, allow-lists, deferrals, stale-safety rules, migration decisions and non-goals remain unchanged.

## 1. Per-variable object applicability is required in schema v3

The original readiness made `semantic_context.applicable_part_kinds` implementation-wide. That is insufficient for a model contract containing variables that belong to different engineering object kinds: it could make every variable appear object-specific for every implementation-level part kind, violating the merged 058c definition requirement that Properties show only fields applicable to the selected object.

Schema-v3 therefore has two distinct applicability levels:

- `semantic_context.applicable_part_kinds` = the exact part kinds for which the **model implementation/family option** may be presented as object-applicable;
- `variables[*].applicable_part_kinds` = the exact part kinds for which that **individual property/input** may be rendered as belonging to the selected object.

The corrected V3 shape is:

```json
{
  "schema_version": 3,
  "evaluation_mode": "forward",
  "semantic_context": {
    "applicable_part_kinds": ["tube", "reservoir"],
    "model_family_key": "pressure_drop",
    "model_family_label": "Pressure drop model",
    "model_option_label": "Ergun equation"
  },
  "variables": [
    {
      "name": "void_fraction",
      "label": "Void fraction",
      "unit": "1",
      "required": true,
      "category": "model_parameter",
      "property_group": "Hydraulics",
      "applicable_part_kinds": ["tube"],
      "description": "...",
      "physical_dimension": "dimensionless"
    }
  ]
}
```

Corrected validation rules:

- implementation-level `applicable_part_kinds`: 1–16 unique non-empty stable identifiers, exact matching only;
- variable-level `applicable_part_kinds`: required on every schema-v3 variable, 1–16 unique non-empty stable identifiers, exact matching only;
- every variable-level kind must be a member of the enclosing implementation-level set; otherwise the v3 contract is invalid;
- no wildcard, fuzzy match, substring match, mesh/name/material/bounds inference or frontend category/name mapping is permitted;
- `property_group` still supplies grouping only; it does **not** imply applicability;
- a variable may intentionally apply to multiple listed kinds by naming each explicitly;
- schema-v1/v2 remain generic and unchanged.

Corrected rendering rule for a resolved 092 object:

1. an implementation is an object-applicable option only when the exact selected `partKind` is in its `semantic_context.applicable_part_kinds`;
2. inside that implementation, Properties renders as selected-object properties only variables whose own `applicable_part_kinds` contain that same exact `partKind`;
3. other variables remain part of the generic model contract/run input authority but must not be presented as properties of the selected object;
4. the implementation must preserve access to those non-object-specific required inputs through the clearly separated generic model-configuration surface when they are needed for preflight/run. Object filtering must never make required runner inputs impossible to supply.

This keeps one canonical input contract and one 071b working state; it does not create an object-property database or second semantic service.

## 2. Model choice is part of the working configuration Undo/Revert history

The merged 058c definition explicitly requires model switching to mutate the same 071b working configuration and participate in Undo/Revert/revision semantics. The original readiness wording that `Undo/Revert operate on the active implementation` was too weak because it allowed the selected implementation itself to remain outside history.

Corrected behavior:

- every model-choice switch is one working-configuration mutation;
- an Undo entry for a switch must contain enough transient state to restore the prior selected implementation **and** the affected per-implementation working values;
- `Undo` immediately after A → B restores A as selected and restores A's pre-switch working values;
- ordinary field Undo continues to restore the previous active-model field state;
- field-level `Revert` remains scoped to the active field and does not change model choice;
- `Revert all` restores the complete current working configuration to the successful/current baseline: baseline selected implementation plus cached per-implementation baseline values, clearing unsaved model-choice/value changes;
- switching model increments the existing working revision exactly once for that operator mutation and invalidates stale preflight;
- no second persisted active-model field, store, SQL row or localStorage state is added.

The internal frontend representation may remain compact, but the single 071b controller's history cannot be only `BindingMap[]` once model choice is a working-config mutation. It must represent the selected implementation and the minimum per-implementation working state needed to restore the prior configuration.

## 3. Preserve per-implementation baselines as well as working values

Inactive-value retention is incomplete if only working bindings are cached. A successful run can establish an implementation-specific baseline; switching away and back must not erase that baseline or make unchanged restored values appear dirty.

The same transient 071b owner therefore maintains, in-memory only:

- current selected implementation ID;
- current per-implementation working binding maps;
- per-implementation baseline binding maps;
- the baseline selected implementation ID established by the current successful-run baseline;
- bounded Undo history sufficient to restore model choice plus working state.

Required semantics:

- A → B preserves both A working values and A baseline;
- B → A restores A working values and compares them against A's preserved baseline;
- a successful run updates the baseline binding map for the active implementation and sets that implementation as the current baseline model choice, subject to the existing revision/model stale guard;
- a successful run for B does not destroy the cached baseline map for A;
- only the active implementation's working values enter preview/run payload;
- inactive baseline/working caches are never execution inputs;
- workspace change clears all incompatible working/baseline/model-choice caches;
- `Revert all` restores the baseline selected implementation and each cached working map to its corresponding baseline state, so the overall working configuration is clean;
- no SQL migration or durable persistence is introduced.

## 4. Corrected deterministic acceptance

In addition to all original readiness acceptance, the implementation must prove:

1. variable-level v3 `applicable_part_kinds` is required, canonicalized deterministically and validated as a subset of implementation-level applicability;
2. selecting a `tube` never renders a `reservoir`-only variable as a tube property, and vice versa;
3. non-object-specific variables required by the active runner contract remain reachable through generic model configuration and are not silently omitted from preflight/run;
4. A → B → Undo restores A selection and A pre-switch working values;
5. A → B → A restores A working values **and** A baseline/dirty comparison;
6. successful Run A → switch B → switch A preserves A's successful baseline; unchanged A values are not falsely dirty and active-field Revert returns to A's baseline rather than empty state;
7. after successful Run A, switching/editing B and invoking `Revert all` restores baseline model A and all cached working maps to their baseline states;
8. model-choice switch uses the existing working revision/preflight invalidation; an old A preview cannot authorize B or a later restored A revision;
9. only the active selected implementation contributes normalized execution input despite retained inactive working/baseline caches.

## 5. Corrected browser acceptance additions

The final implementation browser evidence must additionally cover:

- a mixed v3 contract where a selected tube shows only tube-applicable semantic rows while a reservoir-only row is absent from the object-property groups but remains reachable when required in generic model configuration;
- A → B → Undo returning the selector and values to A;
- successful Run A → B → A preserving A baseline/clean state;
- `Revert all` after model-choice/value edits returning to the baseline selected model and baseline values.

These cases are merge-blocking acceptance for 058c V0, not optional polish.

## 6. Scope and downstream boundary remain unchanged

These corrections do not authorize:

- a second working-state store;
- SQL/localStorage persistence for inactive values or baselines;
- compositional simultaneous runner models;
- formula parsing or invented `fx` content;
- any 092 scene-binding rewrite;
- provider/Jarvis execution;
- 097, 098, 006b or 058b implementation;
- Notes, routine 062 grading UI or global visual identity work.

The minimum implementation remains schema-v3 metadata on the existing input-contract path plus a bounded extension of the existing `EngineeringProperties` owner.