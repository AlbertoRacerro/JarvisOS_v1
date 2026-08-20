# 058c — SCENE-SEMANTICS-A1 readiness production-path correction

Date: 2026-08-20  
Applies to: `docs/specs/058c-readiness-2026-08-20.md`, `docs/specs/058c-readiness-corrections-2026-08-20.md`, and `docs/specs/058c-readiness-parameter-freshness-correction-2026-08-20.md`  
Reason: close exact-head review findings that the previous readiness could ship schema-v3 infrastructure without any normal bundled model exercising it, and left pre-first-run model-choice baseline/Revert-all semantics underspecified.

This file is part of the 058c readiness authority. Where it conflicts with an earlier readiness file, **this file wins**. All unrelated ownership, stale-safety, source-freshness, formula non-fabrication, migration, deferral and non-goal decisions remain unchanged.

## 1. Production V0 must include one real bundled schema-v3 path

Parser/types/tests alone are insufficient acceptance for 058c. The final implementation must make object-semantic Properties reachable through a normal server-owned bundled model registration path in a fresh workspace, without requiring a hand-authored API payload or test-only fixture.

The minimum production target is the existing reviewed 047 M0 geometry/hydraulics model because current authority proves an exact relationship between three of its inputs and the BLUECAD `tube_run` object produced by CAD-LINK-0:

- `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.contract.json` currently defines the reviewed nine-input 047 contract;
- `backend/app/modules/bluecad/cad_link.py` declares `GEOMETRY_INPUTS = ("tube_length", "tube_inner_diameter", "tube_outer_diameter")` and deterministically constructs one GeometrySpec part with `kind = "tube_run"` from exactly those three values;
- CAD-LINK-0 verifies the current legacy bundled-047 label/script/contract hash, so silently rewriting that existing contract or label would risk invalidating established CAD-link identity and is **not** authorized.

Therefore implementation must preserve the existing legacy 047 bundled registration, contract bytes, label and CAD-LINK verification unchanged, and add one **additive semantic companion registration** for the same reviewed 047 executable using a distinct version label and a distinct schema-v3 contract file. No existing model-version row is rewritten.

The companion registration may reuse the existing model spec and existing `calc_v0` script path/copy semantics. It must be exposed through the existing runner bundled-registration module/router pattern; one narrow additive bundled registration route/helper is authorized only because a production-reachable v3 implementation is otherwise absent. This is not a new semantic read service, state store, provider path or execution subsystem.

The implementation must remain idempotent by workspace + companion version label + exact contract/script digests, following the existing bundled registration discipline.

## 2. Authoritative first semantic mapping

For the semantic 047 companion:

`semantic_context`:

- `applicable_part_kinds = ["tube_run"]`;
- `model_family_key = "geometry_hydraulics"`;
- `model_family_label = "Geometry and hydraulics model"`;
- `model_option_label = "Reviewed 047 tubular-loop V0"`.

The three inputs whose object relationship is already proven by CAD-LINK-0 are object-semantic tube properties:

| Variable | Object applicability | Property group |
| --- | --- | --- |
| `tube_length` | `["tube_run"]` | `Geometry` |
| `tube_inner_diameter` | `["tube_run"]` | `Geometry` |
| `tube_outer_diameter` | `["tube_run"]` | `Geometry` |

No other 047 input may be presented as an intrinsic property of the selected tube merely because it participates in the same calculation. `reservoir_liquid_volume`, `target_liquid_velocity`, `liquid_density`, `dynamic_viscosity`, `minor_loss_coefficient`, and `pump_efficiency` remain required generic model-configuration inputs in this V0 unless a later accepted authority proves an exact selected-object relationship.

This is deliberately narrower than guessing object ownership from variable names or engineering intuition.

## 3. Variable applicability correction: empty means generic, not object-owned

The prior correction required every schema-v3 variable to carry 1–16 object part kinds. That prevents a truthful mixed contract from retaining required global/model inputs that are not properties of the selected object.

Corrected schema-v3 rule:

- `variables[*].applicable_part_kinds` remains **required** on every v3 variable so omission is never ambiguous;
- it is a deterministic list of **0–16** unique stable identifiers;
- non-empty entries must all be members of `semantic_context.applicable_part_kinds`;
- `[]` has one exact meaning: **generic/non-object-specific runner input**. It remains part of the active model contract and preflight/run input authority, but is never rendered inside selected-object property groups;
- non-empty exact matches mean the variable may render as a property of those selected object kinds;
- no wildcard, fuzzy match, substring, category/name/unit inference or frontend fallback is allowed.

For a resolved `tube_run`, the object-specific Properties groups therefore show only the three CAD-LINK-proven geometry inputs above. The remaining required 047 inputs stay reachable in the clearly separated generic model-configuration surface and remain required for preflight/run.

## 4. Initial baseline exists before the first successful run

The first successful run is **not** the origin of working-configuration baseline semantics. A fresh working context needs a deterministic baseline immediately so model-choice Undo/Revert is defined before any execution.

Corrected behavior inside the single 071b controller:

1. on a new workspace working context, once the eligible implementation list is accepted and the initial implementation is selected, that exact implementation ID becomes the **initial baseline selected implementation**;
2. its initial working binding map (normally the contract-shaped empty bindings before operator edits) becomes its initial per-implementation baseline map;
3. other implementation baseline maps are initialized from their own contract-shaped initial state when first activated, without changing the baseline selected implementation;
4. A → B before any successful run is one working mutation; `Undo` restores A selection + A pre-switch working values;
5. A → B → `Revert all` before any successful run restores initial baseline model A and all cached working maps to their corresponding initial baseline states;
6. later successful-run baseline adoption supersedes the current baseline selected implementation and the active implementation's baseline map only under the existing revision/model stale guard; it does not erase other cached per-implementation baselines;
7. a later model-list refresh must not silently move the baseline selection merely because another eligible implementation appears; workspace/context reset may establish a new initial baseline;
8. if the baseline implementation becomes unavailable, the controller fails closed/refreshes context rather than silently choosing another model as if it were the same baseline.

No SQL/localStorage persistence or second state owner is introduced.

## 5. Corrected implementation allow-list additions

The earlier allow-list is extended only for the production companion path:

Backend may additionally touch:

- one new schema-v3 bundled 047 semantic companion contract under `backend/app/modules/runner/examples/`;
- the existing runner bundled registration service/module and `routes.py` only as needed for one idempotent semantic-companion registration path;
- focused registration tests proving legacy bundled-047/CAD-LINK identity is unchanged and the companion is production-reachable.

The implementation must **not** modify the existing `bluerev_geometry_hydraulics_v0.contract.json` bytes, existing bundled-047 version label, or CAD-LINK-0 model-identity rules to make the semantic companion fit.

Frontend may add the smallest client registration affordance only if fresh runtime proves there is no existing normal way to invoke the new bundled route. Do not add a general model-management UI under 058c.

All previous allow-list entries, including the superseded-Parameter source-usability guard, remain authorized as already corrected.

## 6. Corrected deterministic acceptance

In addition to all previous readiness acceptance, implementation must prove:

1. a fresh workspace can register the semantic 047 companion through the server-owned bundled registration path and `list_model_implementations` returns a valid schema-v3 contract;
2. the legacy 047 bundled registration still produces the same legacy contract digest/identity expected by CAD-LINK-0 and remains usable;
3. the semantic companion has a distinct version identity and does not rewrite/deduplicate into the legacy model row;
4. exact selected `tube_run` + semantic companion renders only `tube_length`, `tube_inner_diameter`, and `tube_outer_diameter` as object-specific `Geometry` properties;
5. the six remaining required 047 inputs have `applicable_part_kinds = []`, remain reachable in generic model configuration, and still participate in preflight/run;
6. a v3 variable with omitted applicability is invalid; `[]` is valid generic semantics; non-empty kinds outside implementation-level applicability are invalid;
7. no non-object input becomes a tube property through category/name/unit inference;
8. before any successful run, initial A → B → Undo restores A and its values;
9. before any successful run, initial A → B → `Revert all` restores baseline model A and all initial baseline values;
10. a later successful Run B may establish B as the new baseline model under the existing stale guard, after which `Revert all` returns to B rather than the original startup A;
11. model-list refresh does not silently change an established baseline selection.

## 7. Corrected browser acceptance

Final implementation browser evidence must include a production-reachable semantic path, not only mocked v3 data:

- register/use the real semantic 047 companion in a fresh/isolated workspace;
- select a real resolved `tube_run` target and show the three authoritative Geometry rows only in the selected-object group;
- verify the six generic required inputs remain reachable outside the object-specific group;
- perform pre-run A → B → Undo;
- perform pre-run A → B → `Revert all` and verify return to initial baseline A;
- after a successful baseline-changing run, verify `Revert all` follows the successful baseline semantics already frozen by the prior correction.

These are merge-blocking V0 acceptance cases.

## 8. Scope boundary remains unchanged

This correction does not authorize:

- modification of 092 scene identity or CAD-LINK identity heuristics;
- migration/rewrite of existing model-version rows;
- a semantic database/service/cache;
- compositional simultaneous runner models;
- inferred formulas or `fx` content;
- automatic AI model choice or provider/Jarvis execution;
- 097, 098, 006b, 058b, Notes, routine 062 grading or global visual identity work.

The production companion exists solely to make the bounded schema-v3/Properties semantics demonstrably useful in the normal product while preserving all pre-058c execution and CAD-link authority.