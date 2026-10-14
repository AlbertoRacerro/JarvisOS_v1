# Engineering Studio architecture record — 2026-10-13

Context for specs 187 to 192. Written under the maintainer directive of 2026-10-13. This file is evidence and rationale. `docs/specs/STATUS.md` and the accepted specs hold the authority.

## Principle

Repository work builds general engineering tools. Engineering users build project models with those tools. A new correlation, kinetic law, process unit, CAD geometry, procedure or study must not need a repository change. A specification is needed only for new general functionality, execution machinery, solver integration or security authority. BlueRev is the acceptance case, not the product boundary.

## Audit of master `c1e8f516`

Executed evidence: 301 runner and calculation tests pass. The findings below were traced to code by two independent audits and spot-checked.

| Capability | State | Evidence |
|---|---|---|
| Run reviewed bundled Python models | works | `runner/routes.py`, `runner/guarded_service.py` |
| Run user-authored Python | deliberately disabled | `runner/public_models.py`, `_require_exact_bundled`, `docs/runner-trust-boundary.md` |
| OS isolation for execution | missing in the runner; exists for agent CLIs only | `relay_gateway/sandbox.py` |
| Model identity and versions | works, no lifecycle | `model_specs`, `model_versions`, free-text status |
| Typed input contract, Parameter binding, freshness | works | `runner/input_contracts.py`, `runner/linked_parameters.py` |
| Run provenance, hashes, logs, artifacts | works | `runner/service.py` |
| Qualification ladder | works as a contract | `engineering/refs.py`, `engineering/evidence_contracts.py` |
| Evaluator plug-in protocol | works; registry hardcoded | `engineering/evaluator_contracts.py`, `engineering/operator_service.py` |
| Process unit types | hardcoded, 13 types | `UNIT_REGISTRY`, `mixed_runtime.py` |
| Rate laws | hardcoded templates (Monod, Haldane) | `kinetics.py` |
| Dynamic actions | hardcoded typed set | `dynamic_models.py` |
| BLUECAD parts | 8 hardcoded kinds; STEP, STL, GLB | `bluecad/builders.py`, `bluecad/export.py` |
| Arbitrary build123d | disabled (historical L2) | `guarded_service.py` |
| Sidecar actions | Process and BLUECAD edits only; none carries code | `workspace_actions/models.py` |
| GUI: declare a contract, edit code, test, publish | missing | `frontend/src/pages/ModelDossier.tsx` and the absence of any editor |
| GUI: bind inputs and run an existing implementation | works | `EngineeringProperties.tsx`, Runs |
| GUI: equations | native MathML from backend math trees | `MathTree` |

**Main blocker.** There is no boundary inside which user-authored Python may run. Every hardcoded registry above exists because code could only enter through the repository. Spec 187 creates that boundary. Everything else builds on it.

## Upstream decisions

Licence and release data were checked against the registries on 2026-10-13.

| Need | Decision | Note |
|---|---|---|
| Isolation on Linux and WSL2 | bubblewrap, adopt | Already used by `relay_gateway`; verified on the host with numpy and build123d |
| Isolation on native Windows | park | Job Objects cap resources but give no filesystem or network isolation |
| Code editor | CodeMirror 6 (MIT), adopt | Small, no web workers. Monaco is heavier with no benefit here |
| Units | Pint (already pinned), reuse the existing owner | No second unit system |
| Code to equations | own `ast` visitor to the existing math tree | No new dependency, no execution. `latexify_py` works but is archived upstream. `handcalcs` needs execution |
| Equation rendering | native MathML through `MathTree` | KaTeX only if LaTeX input is later required |
| CAD as code | build123d (already pinned), run inside 187 | CadQuery is redundant. FreeCAD is an exchange target only |
| Visual CAD | defer | CADCraft is 2D drafting only. JSketcher requires copyright assignment; do not adopt |
| Notebook | marimo (Apache-2.0), prototype in 192 | Pure `.py` storage fits "Python is the executable truth" |
| Spreadsheet | Univer (Apache-2.0), prototype in 192 | FortuneSheet maintenance has slowed. Handsontable is commercial |
| Procedure timeline | evaluate in 191 | Not needed before procedures exist |
| Block programming | reject | The directive rules out a block catalogue |

## The fourteen questions

1. **Creating a model.** The wizard collects a contract. The backend writes a `model_specs` row and a Studio draft with a deterministic scaffold. Nothing runs.
2. **Where code lives.** A draft's source is a row owned by the `studio` module. A published version's source is a governed artifact referenced by its `model_versions` row.
3. **Version owner.** `model_versions`. The version is identified by the source hash and the contract hash.
4. **Input binding.** Explicit, per input, to a value or a project Parameter, through the existing v2 binding owner. Names are never matched by convention.
5. **Output checks.** The host validates the typed result: declared outputs present, finite, within the size cap. Units are declared in the contract.
6. **Isolation.** Spec 187: one bubblewrap sandbox per run, no network, read-only system, one scratch directory, resource limits, fail closed, off by default.
7. **Solver invocation.** In this slice the caller is the runner-job flow. A solver may call a published model only through a declared adapter contract (planned 190). DWSIM IronPython never receives user Python.
8. **Discovery.** Published versions are listed by the existing model-implementation listing and by the Studio library. Palette registration for process units comes with 190.
9. **Documentation.** One way: `ast` to math tree, plus contract tables. Annotations are prose, bound to a source hash, flagged stale when it changes.
10. **Sidecar.** It may draft, explain and propose. A proposal is a draft edit the operator accepts. It gains no execution or publication authority. Planned with 189 onward as a new workspace-action surface.
11. **Staleness.** Changing a bound Parameter marks runs stale through the existing freshness owner. A new published version marks older-version runs superseded. No run is rewritten.
12. **Reuse.** Any consumer that takes a model version takes a published Studio version. Identity is the version id.
13. **Unsupported integration.** The category is visible, disabled, and states what is missing. Nothing is silently approximated.
14. **What needs the repository.** A new execution contract (a new category), a new solver adapter, a new isolation tier, or new authority. A new model, correlation, geometry or procedure within an existing category does not.

## Slices

| Spec | Outcome | State |
|---|---|---|
| 187 | Isolated runtime for user-authored Python | ready |
| 188 | Model authoring vertical slice: wizard, scaffold, editor, derived documentation, test, publish, reuse in a calculation | ready, after 187 |
| 189 | CAD as code: build123d scripts in the 187 runtime, preview in the BLUECAD viewer, STEP and STL with lineage (golden workflow 2) | planned |
| 190 | User-defined process unit: declared ports, parameters and a steady contract invoked by the mixed-engine solve, with palette registration and explicit stream bindings (golden workflow 3) | [ready](../specs/190-studio-process-custom-unit.md) |
| 191 | Procedure authoring: user-defined temporal procedures over the existing typed actions (golden workflow 4) | planned |
| 192 | Notebook and spreadsheet bakeoff prototype (marimo, Univer) as exploration surfaces that are not parameter authorities | planned |

## Disposition of existing planned work

| Spec | Disposition | Reason |
|---|---|---|
| 012 L2 free-script proposals | keep trigger-deferred | 187 is the isolation specification it waits for. AI-generated scripts still need their own decision |
| 013 domain-validator plugins | keep planned | Revisit after 188; a published model may serve as the validator |
| 033 reusable part-kind proposal | re-evaluate with 189 | CAD as code removes most of the need for new typed kinds |
| 165 print handoff | unchanged | Independent |
| 173 dynamic studio | keep; general capability | A GUI for existing general machinery |
| 174, 175 PBR optics, thermal and gas | re-evaluate after 190 | Mostly user-authorable models once custom units and dynamic contracts exist |
| 176 Process to BLUECAD PBR link | re-evaluate after 189 | The PBR array becomes a user CAD script |
| 177 harvest units | re-evaluate after 190 | Separator models are user-authorable; solver participation is the general part |
| 178 TEA worker | unchanged | General integration |
| 179 CFD surrogates | unchanged | Depends on 110 |

None of 173 to 179 is launched by this record.
