# 188 — Engineering Studio model authoring: create, test, publish, reuse

State: **accepted and ready**. Written under the maintainer directive of 2026-10-13 ("Engineering Studio / BlueRev R&D workstation", P0 and the first golden workflow). Reviewed against master `c1e8f516`. Architecture record: [Engineering Studio architecture](../implementation/engineering-studio-architecture-2026-10-13.md).

- **Hard dependency:** 187.

## Fresh evidence (master `c1e8f516`)

- **No authoring.** "+ New model" (`frontend/src/pages/ModelDossier.tsx`) saves a title, a question and a scope. Nothing in the GUI declares inputs or outputs, edits code, runs a test or publishes.
- **No lifecycle.** `model_specs.status` and `model_versions.status` are free text. `modeling/routes.py` offers create, list and get only.
- **Reusable owners.** `model_specs` and `model_versions` already give identity and versions. Input contract v2 (`runner/input_contracts.py`) gives typed variables with unit and physical dimension. The runner-job flow gives parameter bindings, linked-parameter freshness, run provenance and output-to-Parameter proposals. Project Basis (spec 112) already owns model impact and revalidation. Pint is owned by `process_kernel/units.py`.
- **Closed execution.** `runner/guarded_service.py` runs only server-known bundled scripts.
- **Equations.** The frontend renders backend math trees as native MathML (`MathTree`). There is no code editor dependency.

## Decision

1. **Category.** This slice delivers one executable category, `calculation`: a Python function with declared inputs and outputs. It covers independent calculations and algebraic correlations. The wizard also lists the other categories of the directive (steady unit operation, dynamic model, procedure, geometry, optimization, CFD/FEM) as not yet available, each with the reason. It never fakes them.
2. **Identity.** A Studio model is a `model_specs` row. Its identity is the row id, not the display name. Studio-only data lives in additive tables owned by a new `studio` backend module. No second project state is created.
3. **Wizard.** The default path asks for name, engineering question, inputs and outputs. Each variable has a Python identifier, a label, a unit that Pint can parse, a description and optional bounds. A custom path with no preset is always offered.
4. **Scaffold.** The backend turns the contract into Python source deterministically: the same contract gives byte-identical source. The scaffold has a typed `evaluate(...)` signature in the declared units, a docstring, a placeholder body that raises until edited, and metadata. No model writes or completes it.
5. **Editor.** The code is always editable in a Python editor (CodeMirror 6, MIT). Python is the executable truth.
6. **Derived documentation.** The backend parses the source with `ast` and never executes it for documentation. It emits the equations of `evaluate` and its helper functions as the existing math-tree type, plus the contract tables. Derived equations and values are read-only. A construct that cannot be rendered is shown as code and labelled as not rendered. Prose annotations and assumptions are editable and are stored with the source hash they were written against; when the hash changes they are flagged stale. There is no documentation-to-code path.
7. **Lifecycle.** Save Draft, Test, Publish.
   - A draft is mutable.
   - Test is an explicit action. It runs the user's test cases through the 187 runtime. A case gives input values and, optionally, expected outputs with a tolerance. The host also checks that every declared output is present and finite. The report is bound to the source hash and the contract hash.
   - Publish requires a passing report for the exact current hashes and at least one test case. It creates an immutable `model_versions` row of kind `studio_calc_v1` with a v2 input contract and a governed artifact that holds the source.
   - A published version is never edited. Revise opens a new draft from it. Publishing a new version does not alter existing runs.
8. **Not qualification.** A published version is recorded and shown as scientifically unqualified. Qualification stays with the spec 102 owner.
9. **Library and reuse.** Published versions appear in the Studio library and in the existing model-implementation listing. They are selected, bound and run through the existing runner-job flow: explicit bindings from each input to a value or a project Parameter, linked-parameter freshness, run provenance, and output-to-Parameter proposals.
10. **Execution.** A `studio_calc_v1` run executes only through the 187 runtime. The bundled-only guard keeps refusing every other non-bundled kind. If the runtime is disabled or unavailable, Test and Run are refused with the reason and the GUI says how to enable it.
11. **Stale and superseded.** A run whose bound Parameter changed is stale through the existing freshness owner. A run on a version that has a newer published version is shown as superseded. Neither is mutated.
12. **Surface.** A Studio route under Design holds the library, the wizard and the model workspace (Contract, Code, Documentation, Tests, Versions).

## Acceptance

1. **Golden workflow 1, real browser.** On the qualification host with the runtime enabled, an operator, using the GUI only:
   - creates a pipe pressure-loss correlation with the wizard and gets the scaffold;
   - edits the code and sees the derived equations;
   - adds a test case, runs Test and sees it pass;
   - publishes version 1;
   - selects it in the existing calculation surface, binds one input to a project Parameter and runs it;
   - changes the Parameter and sees the run flagged stale, then re-runs;
   - revises the model, publishes version 2 and sees the first run shown as superseded and otherwise unchanged.
   The workflow fails if any step needs a backend edit, a new spec, hand-written JSON or a terminal.
2. **Deterministic scaffold.** The same contract yields byte-identical source. The scaffold parses, and running it before any edit fails with the placeholder error.
3. **Publish gate.** Publish is refused without a passing report for the exact source and contract hashes, and after any later edit.
4. **Immutability.** No route changes the source, contract or hash of a published version.
5. **Units.** A unit that Pint cannot parse is rejected at the contract. A bound Parameter with an incompatible dimension is rejected by the existing v2 binding check.
6. **Execution boundary.** `studio_calc_v1` cannot run with the runtime disabled or unavailable. A row of that kind whose artifact hash does not match is refused. Other non-bundled kinds remain refused.
7. **Documentation safety.** Generating documentation for a source with side effects at import time executes nothing. An unsupported construct is labelled, not dropped.
8. **Stale annotations.** Editing the code flags annotations written against the old hash.
9. **Unsupported categories.** Each is visible, cannot be created, and states its reason.

## Required evidence

- Backend tests for criteria 2 to 9, with the 187 runtime real, not mocked, for the execution criteria.
- A frontend test file gating the build, as the repository requires for a new surface.
- A real-browser proof of criterion 1 with screenshots, on the exact head.
- Full backend suite, ruff, frontend build and the registry checks.

## Non-goals

- No Sidecar code proposals; no new workspace-action surface.
- No Process Studio flowsheet binding and no custom process unit (planned 190).
- No CAD-as-code (planned 189), procedures (planned 191), notebook or spreadsheet (planned 192).
- No visual block programming.
- No automatic qualification and no change to the spec 102 or spec 112 owners.
- No second parameter store. Spreadsheets and notebooks are not parameter authorities.
