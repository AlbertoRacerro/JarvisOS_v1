# 071 — MODEL-SCENARIO-DOF-0: editable bindings, scenario runs, and degree-of-freedom inspection

Status: planned full-spec draft. `docs/specs/STATUS.md` is authoritative. This
definition does not authorize implementation until the registry row is added and
promoted to `ready`.

Depends on: 040, 043, 047

## Goal

Make the merged 047 BlueRev calculation usable as an open engineering model rather
than a hidden script or a single closed calculation.

After this slice, an operator can:

- inspect the exact input-variable contract of a reviewed model implementation;
- enter or reference values without changing Python source;
- see total, bound, invalid, and unresolved input degrees of freedom;
- execute multiple labelled scenarios through the existing `calc_v0` runner;
- inspect the resulting unit-bearing outputs and run identity;
- preserve accepted project parameters while exploring temporary alternatives.

This is the first forward-model workbench slice. It does not add inverse solving,
target specifications, equation-oriented solving, optimization, or a generic process
simulator.

## Maintainer direction

Use the smallest existing mechanisms:

- `model_versions` remains the identity of a reviewed implementation;
- `simulation_runs` remains the persisted scenario/run record;
- the 043 runner remains the only calculation execution boundary;
- 040 remains the proposal/promotion authority for engineering records;
- the existing Domain Foundation frontend is extended with one bounded model-scenario
  panel rather than creating a second workspace or redesigning the product shell;
- every numerical design or operating value remains caller-authoritative and editable;
- numerical values used by tests remain fixtures only and never become product defaults.

Do not create a new equation framework, workflow engine, scenario database, unit
library, solver service, agent tool, or frontend state architecture.

## Current evidence

The repository already provides:

- model specs and model versions;
- reviewed `calc_v0` scripts with hash-bound artifacts;
- `RunnerJobCreate.input_set` and deterministic runner execution;
- persisted `simulation_runs.input_payload` and `output_payload`;
- parameter records with value, unit, status, source, and provenance fields;
- a Domain Foundation page that already lists model specs, parameters, and simulation
  runs;
- the merged 047 model with nine explicit caller-supplied inputs and no runtime product
  defaults.

The missing product contract is not another calculation engine. It is a trustworthy
bridge between a model version, editable bindings, DOF state, the existing runner,
and an operator-visible scenario result.

## Scope

### 1. Versioned model input contract

Extend a model version with an optional immutable input-contract document and digest.
The expected additive storage fields are:

- `input_contract_payload TEXT`;
- `input_contract_sha256 TEXT`.

The exact migration identifier must be selected from current master during
implementation and must follow the existing additive schema discipline.

`ModelImplementationCreate` may accept an optional `input_contract`. When present, the
service validates, canonicalizes, hashes, and stores it together with the model
version. `ModelImplementationRead` exposes the canonical contract and digest.

The contract schema is versioned and bounded:

```json
{
  "schema_version": 1,
  "evaluation_mode": "forward",
  "variables": [
    {
      "name": "tube_length",
      "label": "Tube length",
      "unit": "m",
      "required": true,
      "category": "design",
      "description": "Illuminated tube centreline length.",
      "domain": {"exclusive_min": 0.0}
    }
  ]
}
```

Required rules:

- `schema_version` is exactly `1`;
- `evaluation_mode` is exactly `forward`;
- variable names are unique, non-empty, and stable identifiers;
- units are exact non-empty canonical strings;
- `required` is boolean;
- category is one of `design`, `operating`, `property`, `model_parameter`, or
  `equipment`;
- descriptions and labels are bounded text;
- numeric domain metadata may use only `min`, `max`, `exclusive_min`, and
  `exclusive_max` with finite values;
- contradictory domain bounds are rejected;
- the contract contains no `value`, `default`, `recommended_value`, `initial_guess`,
  or hidden fallback field;
- unknown fields are rejected;
- canonical JSON bytes and SHA-256 are deterministic.

The 047 implementation contract declares exactly its nine existing inputs and exact
units. It does not embed the regression-fixture values.

A model implementation without an input contract remains executable through the
existing 043 API but is not eligible for the 071 scenario workbench.

### 2. Side-effect-free binding and DOF preview

Add one side-effect-free endpoint over an existing model implementation:

```text
POST /workspaces/{workspace_id}/model-implementations/{model_version_id}/binding-preview
```

Request:

```json
{
  "bindings": {
    "tube_length": {
      "value": 20.0,
      "unit": "m",
      "source_parameter_id": null
    }
  }
}
```

The preview performs no runner job, simulation run, artifact write, parameter write,
promotion, AI call, network call, or provider call.

Response includes at least:

```json
{
  "model_version_id": "...",
  "contract_sha256": "...",
  "evaluation_mode": "forward",
  "structural_input_dof": 9,
  "bound_input_dof": 1,
  "unresolved_input_dof": 8,
  "invalid_binding_count": 0,
  "state": "incomplete",
  "variables": [],
  "normalized_input_set": null
}
```

`state` is exactly one of:

- `incomplete`: no invalid bindings, but one or more required inputs are missing;
- `ready`: all required inputs are valid and a normalized runner input set is
  returned;
- `invalid`: at least one supplied binding is invalid.

Each variable result reports:

- name, label, unit, category, and description from the immutable contract;
- binding state: `missing`, `manual`, `parameter`, or `invalid`;
- supplied value only when present;
- `source_parameter_id` only when present;
- one or more stable error codes without echoing unsafe payloads.

Required invalid cases include:

- unknown variable name;
- non-finite or boolean value;
- wrong unit;
- domain violation;
- malformed binding object;
- source parameter not found or outside the workspace;
- source parameter with non-numeric value;
- source parameter value/unit mismatch with the submitted binding;
- contract missing, malformed, or digest-inconsistent.

No unit conversion occurs in 071.

### 3. Degree-of-freedom semantics

For `evaluation_mode = "forward"`:

```text
structural_input_dof = number of required input variables
bound_input_dof = number of required variables with one valid binding
unresolved_input_dof = structural_input_dof - bound_input_dof
```

Invalid bindings do not count as bound.

Outputs are deterministic consequences of the model and do not consume or create
input DOF. Optional display metadata, result values, and parameter provenance do not
change the count.

The UI and API must not claim equation-oriented DOF analysis. Terms such as
`overspecified`, `target`, `design specification`, `tear stream`, or `solver unknown`
are not authorized in this slice. A request containing unknown output bindings or
unsupported target semantics is `invalid`, not an inverse problem.

### 4. Scenario execution through the existing runner

071 adds no second execution endpoint. When preview state is `ready`, the frontend
uses the returned `normalized_input_set` with the existing flow:

```text
create runner job -> run runner job -> inspect simulation run/output
```

Each execution requires an operator-supplied run label or a deterministic UI-generated
label that is visible before execution. The resulting `simulation_run` is the
persistent scenario evidence.

Required behavior:

- two different binding sets create two distinct simulation runs;
- changing a binding never mutates an earlier run;
- running a scenario never mutates or promotes a Parameter record;
- manual scenario values carry no fabricated `source_parameter_id`;
- parameter-backed values preserve the verified parameter reference;
- the runner remains authoritative for script-specific validation and failure;
- preview `ready` does not guarantee physical success when a script correlation later
  rejects an otherwise contract-valid point;
- failed runs remain inspectable as failed runs and produce no successful output
  artifact or parameter proposals beyond existing 043 behavior.

### 5. Minimal operator panel

Extend the existing Domain Foundation page with one bounded `Model scenario` panel.
Do not create a new top-level page in this slice.

The panel:

- lists model implementations that expose a valid input contract;
- renders one control per contract variable;
- displays exact units beside every value;
- groups or labels variables by contract category without changing their semantics;
- permits a manual value or an exact compatible Parameter reference;
- displays source state as `manual scenario override` or the referenced parameter;
- shows `structural`, `bound`, `unresolved`, and `invalid` counts;
- lists missing or invalid variables explicitly;
- disables Run unless preview state is `ready`;
- displays the current run ID, status, unit-bearing outputs, and bounded error;
- allows editing and running another scenario without overwriting the prior run;
- stores temporary form state only in React memory, not localStorage;
- does not silently seed regression values or a selected Mark-1 design.

A fixture-fill convenience button is forbidden. Tests may use fixtures through test
helpers only.

The panel may be visually plain. 070/058 own the broader design-system and workspace
composition.

### 6. Future chat compatibility without chat authority

The binding-preview request and normalized input-set response are the stable backend
contract that a future approved chat/MCP slice may use.

071 itself adds no chat command, model call, MCP tool, autonomous scenario execution,
or natural-language parser. AI-originated values remain proposals and require the same
explicit operator-visible binding and run action as manual values.

## Persistence and authority

- The immutable input contract belongs to the model version.
- Temporary form edits are not canonical records.
- A simulation run preserves the executed input and output evidence.
- Parameter records remain independent canonical/proposed engineering records under
  existing authority.
- No scenario value is promoted automatically.
- No result is accepted as a design decision automatically.
- Contract metadata may describe permitted values but may not select a design value.

## Files likely touched

Verify against current master before implementation and stop on conflict.

Expected bounded scope:

- `backend/app/core/schema.py` for additive model-version contract fields;
- `backend/app/modules/runner/models.py`;
- `backend/app/modules/runner/service.py`;
- `backend/app/modules/runner/routes.py`;
- a small runner contract/DOF helper module if separation is justified;
- focused backend tests for contract validation, preview, provenance, and execution;
- `frontend/src/api/client.ts`;
- `frontend/src/pages/DomainFoundation.tsx`;
- existing CSS only for the bounded panel;
- `docs/specs/STATUS.md` for the normal implementation lifecycle;
- this spec only for real implementation notes.

Do not modify the 047 calculation script or its existing numerical tests unless a
concrete incompatibility is found and reported before implementation.

## Required verification

### Contract tests

1. Canonical contract bytes and SHA-256 are deterministic.
2. Duplicate names, unknown fields, values/defaults, invalid units, invalid categories,
   non-finite bounds, and contradictory bounds are rejected.
3. Existing model implementations without contracts remain readable and executable.
4. The exact 047 contract contains nine variables and no numerical value/default.

### Preview tests

5. Empty bindings report `9/0/9`, state `incomplete` for 047.
6. One valid binding reports `9/1/8`.
7. Nine valid bindings report `9/9/0`, state `ready`, and return the exact normalized
   input set.
8. Wrong unit, unknown variable, non-finite value, domain violation, and malformed
   source reference report `invalid` without side effects.
9. A valid parameter reference is verified against workspace, numeric value, and exact
   unit.
10. Preview creates no runner job, simulation run, artifact, proposal, parameter,
    event implying execution, or AI job.

### Execution tests

11. The normalized ready payload executes the real merged 047 script through
    `create_runner_job` and `run_runner_job`.
12. Two different scenarios create distinct runs and different dependent outputs where
    physically expected.
13. Neither run mutates the source Parameter or promotes any output automatically.
14. Script-level correlation failure remains a failed runner result even after a valid
    contract preview.

### Frontend verification

15. The panel renders all nine variables from server contract metadata rather than a
    hard-coded field list.
16. Missing and invalid fields are visible; Run is disabled until `ready`.
17. Units and source state are visible without relying on colour.
18. A ready scenario executes through the existing runner APIs and renders unit-bearing
    outputs.
19. No regression values appear in production frontend source.
20. `npm run build`, Ruff, full backend Pytest, spec-status gate, and existing BLUECAD
    canaries pass offline.

## Acceptance criteria

1. Model versions can carry a canonical immutable input contract and digest without
   breaking legacy versions.
2. The merged 047 model is registered with exactly nine editable input definitions and
   no product defaults.
3. A side-effect-free preview reports honest forward input DOF and normalized bindings.
4. Parameter-backed bindings are verified; manual overrides remain explicit and do not
   fabricate provenance.
5. Ready scenarios execute only through the existing 043 runner and persist as distinct
   simulation runs.
6. The Domain Foundation panel is contract-driven, unit-visible, DOF-visible, and does
   not overwrite earlier runs or canonical parameters.
7. No model, provider, Ollama, filesystem, or external solver is called by preview or
   frontend code.
8. No automatic promotion, design selection, target solving, or optimization is added.
9. Existing 047 numerical behavior and deterministic evidence remain unchanged.
10. Required backend tests, frontend build, and repository CI are green.

## Non-goals

- No equation-oriented solver or simultaneous-equation engine.
- No targets, constraints, inverse solving, design specifications, or optimizer.
- No automatic choice of which variable to free or solve.
- No unit conversion library or alternate unit strings.
- No persistent draft-scenario table, scenario branching tree, or variant comparison.
- No dependency DAG or stale propagation; 050 and 051 own those capabilities.
- No process-to-CAD binding; 052 owns that bridge.
- No chat, Hermes, MCP, autonomous agent, or natural-language binding parser.
- No new top-level page, unified workspace, or broad UI redesign.
- No automatic import of workbook values.
- No default, recommended, baseline, or Mark-1 numerical design embedded in production
  contract or frontend code.

## Stop conditions

Stop and report before implementation if:

- current runner persistence cannot preserve the exact executed input set;
- adding contract fields would require destructive migration behavior;
- the only path requires changing 047 equations or weakening its input validation;
- the frontend would need to call execution tools, files, providers, or Ollama directly;
- a proposed implementation introduces a generic equation/solver framework;
- another open PR owns the same runner models, schema fields, or Domain Foundation
  surface.
