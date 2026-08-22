# 058d — PROCESS-WORKSPACE-SCAFFOLD-0

Status: draft planning kernel; `docs/specs/STATUS.md` remains the sole live queue/status authority.
Depends on: 083, 087, 089, 091, 058b

## Goal

Before global visual identity is applied, establish a backend-agnostic Process workspace shell that is visibly and semantically distinct from the existing lineage/provenance surface. The slice gives Visual Identity a stable process-workstation structure to style without pretending that a process-topology backend, Aspen/HYSYS-like editor, or integrated photobioreactor solver already exists.

## Why

The current `/design/flowsheet` surface is a dependency/provenance/lineage view, not an engineering process flowsheet. The product direction requires a future process-design workbench for the microalgae photobioreactor, but the authoritative process topology/evaluator contracts will only be selected and generalized in the post-visual-identity process/evaluator queue. Implementing React-owned nodes, streams or process semantics now would freeze a speculative frontend domain model and create avoidable rework after the upstream bake-off.

The correct pre-visual-identity move is therefore structural only: reserve the right workstation shape, separate Lineage from Process in the user model, and reuse the already implemented shell/Jarvis/Properties/analysis regions.

## Scope

In scope:
- separate the user-facing Lineage/Dependency/Provenance concept from the future Process/Flowsheet concept;
- preserve the existing read-only lineage functionality while removing any UI wording that implies it is the editable process flowsheet;
- introduce a distinct Process route/stage/workspace entry using the existing application-shell architecture;
- provide a canvas-first Process workspace scaffold suitable for later process-authoring integration;
- provide only clearly inert structural slots/empty states for a future process tool strip/palette and process canvas when useful for layout validation;
- reuse the current Jarvis/Properties sidecar and Analysis Dock contracts rather than creating parallel panels;
- keep route migration minimal and compatibility-safe; exact `/design/process` versus compatible repurposing/redirect of `/design/flowsheet` must be re-derived from current master during definition/readiness;
- add deterministic frontend tests proving route/label separation, accessibility and absence of process mutations/network calls from the inert scaffold.

Out of scope (binding non-goals):
- no new backend API, schema, migration, state store or canonical process record;
- no changes that expand `app/modules/process_kernel` or choose a process-solver upstream;
- no React-owned process topology or persistence model;
- no invented `TubeNode`, `JointNode`, `PumpNode`, `StreamNode`, unit-operation vocabulary or semantic contract merely to populate the screen;
- no functional drag-and-drop, stream connection, recycle solving, controller authoring or solver execution;
- no fake process results, telemetry, engineering quantities or placeholder numerical data presented as real;
- no CAD-authoring expansion;
- no final typography, chlorophyll palette, glass effects, icon system or other Visual Identity work owned by 100;
- no pre-emption of 103–107 process upstream/evaluator decisions, 108 DesignStudy semantics, or 109 Process-CAD handoff semantics.

## Files likely touched

Verify against actual code before starting; report conflicts instead of guessing.

- `frontend/src/app/routes.ts`
- `frontend/src/stages/registry.ts`
- `frontend/src/stages/FlowsheetStage.tsx` or its compatibility-preserving successor
- a new bounded Process stage component under `frontend/src/stages/` if current routing warrants it
- `frontend/src/components/shell/ContextualNavigator.tsx` only if required for the stage labels/navigation contract
- focused frontend route/stage tests and minimal identity-independent structural styles

Do not broaden the implementation to backend modules or unrelated pages merely to make the scaffold appear populated.

## Design constraints

- `docs/specs/STATUS.md` must register 058d between freshly re-derived 058b and 100 before implementation is authorized; 100 must depend on merged/reconciled 058d.
- The normal backlog row → definition/full spec → readiness → implementation → exact-head gates → review → merge → reconciliation lifecycle remains mandatory.
- Existing lineage data and behavior remain read-only and must not be silently reinterpreted as process topology.
- The Process scaffold must not create canonical or durable engineering state.
- Frontend must not call providers, solvers or engineering executables directly.
- Empty/inactive process-authoring regions must be visibly honest about capability: structural preview is allowed; simulated functionality is not.
- Use the current application shell. Do not create a second Rail, Jarvis surface, Properties system or Analysis Dock.
- Keep the main canvas as the dominant work area so 100 can style a realistic engineering workstation rather than a dashboard of placeholder cards.
- Preserve keyboard navigation, focus handling and current compact/collapsible shell behavior.
- Visual Identity must remain independently removable: 058d establishes semantic/layout structure only.

## Acceptance criteria

1. A user can navigate to a distinct Process workspace/stage without confusing it with Lineage/Dependency/Provenance.
2. The existing lineage view remains functional and is labelled as lineage/dependency/provenance rather than an editable engineering flowsheet.
3. The Process surface is canvas-first and visibly reserves the correct workstation regions for future tools while clearly stating that process-model authoring is not yet available.
4. Jarvis/Properties and Analysis Dock remain the shared shell regions for the Process stage; no duplicate assistant/inspector/dock implementation is introduced.
5. The Process scaffold performs no process-topology persistence or process-solver execution and introduces no new backend endpoint/schema/store.
6. No process engineering object vocabulary is invented solely in the frontend.
7. Route and stage tests prove Lineage and Process are distinct and compatibility behavior is deterministic.
8. Accessibility checks cover stage navigation and empty-state semantics.
9. The implementation remains identity-independent so 100 can apply the final visual system afterward.

## Required tests

- route-resolution tests for the final Lineage and Process routes/aliases;
- stage-registry/navigation tests proving Lineage and Process are distinct destinations;
- render/smoke test for the Process scaffold and its honest unavailable/empty-state messaging;
- regression test that the existing lineage stage still loads its current read model;
- assertion or harness evidence that mounting/using the inert Process scaffold does not dispatch process mutation or solver requests;
- existing frontend build/typecheck/test gates required by `AGENTS.md`.

## Later evolution

This slice is intentionally not the real Aspen/HYSYS-like editor. Once 103–107 establish the selected process stack and common evaluator contracts, a separately re-derived Process Workbench slice should add real backend-owned topology, nodes/streams, selection-specific Properties and executable process actions. After 108/109, that workbench can expose DesignStudy variables, feasibility/Pareto state and process-driving geometry/physical-layout handoff without making the frontend or CAD layer the owner of process physics.

## Definition of done

The slice is done only after `docs/specs/STATUS.md` has been reconciled, the full spec/readiness generated from current master has authorized implementation, the required exact-head frontend gates are green, Lineage and Process are semantically separated, the Process workspace scaffold is real but inert, and the implementation has been merged/reconciled before 100 begins.
