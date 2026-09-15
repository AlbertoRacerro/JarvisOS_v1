# Area C — Engineering / BLUECAD / process / scientific tooling

MAPPING_STATUS: IN_PROGRESS

Runtime/code/tests are primary evidence; STATUS/spec prose only classifies historical/deferred authority.

## GeometrySpec → CAD/export — REAL
- **What/when:** bounded typed GeometrySpec → build123d/OCP parts/assemblies → STEP/STL/GLB + manifest/validation. Use for trusted BLUECAD geometry.
- **Canonical:** `backend/app/modules/bluecad/{spec.py,builders.py,assembly.py,service.py,export.py,validate.py,models.py,cli.py}`.
- **Invoke:** `build_geometry_spec`, `build_geometry_spec_file`; spawned worker, hard timeout.
- **I/O/persistence:** filesystem artifacts; canonical manifest hashes/digest; no DB write in build API.
- **Preconditions:** build123d importable. Checked-in tool registry declares it disabled; direct CAD path imports it.
- **Risk:** local CAD process/files; structured spec/kernel/export/timeout failures.
- **Evidence:** `backend/tests/bluecad/` conformance, spawn, property/golden suites.
- **Limits:** bounded vocabulary; determinism only within pinned tool/kernel environment.
- **Do not reinvent:** reuse canonicalization/build/manifest/report.
- **Anchors:** `build_geometry_spec`, `canonicalize_geometry_spec`, `manifest_digest`.

## Scene-bound GLB / semantic part identity — REAL
- **What/when:** deterministic GLTF scene key ↔ canonical `part_id` binding for viewer selection.
- **Canonical:** `backend/app/modules/bluecad/export.py`; frontend viewer/Properties consumers.
- **Invoke/I/O:** automatic in export; `manifest.scene_binding`; collisions/non-bijection fail.
- **Authority/risk:** identity/context only; viewer hit does not mutate engineering state.
- **Evidence:** exporter + 092 scene-binding tests.
- **Limits:** semantic meaning beyond part identity separately gated.
- **Do not reinvent:** no second frontend object-ID map.
- **Anchors:** `SCENE_BINDING_VERSION`, `_validate_scene_binding_manifest`.

## Tool registry / health / hash-pinned execution — REAL framework; defaults DISABLED
- **What/when:** operator registry for CAD/mesh/FEM binaries; exact version/license/integration/hash enforcement.
- **Canonical:** `backend/app/modules/bluecad/registry.py`, `configs/bluecad_tools.yaml`.
- **Invoke:** `load_registry`, `resolve_tool`, `run_tool`, registry `check`; override `JARVISOS_BLUECAD_TOOL_REGISTRY`.
- **I/O:** reduced env, `shell=False`, bounded stdout/stderr/timeout.
- **Preconditions:** enabled external entries need entrypoint, SHA-256, provenance, license.
- **Risk:** native execution only after registry/hash checks.
- **Evidence:** `backend/tests/bluecad/test_registry.py`, hash-pinned fake executables.
- **Limits:** checked-in build123d/Gmsh/CalculiX entries disabled; Gmsh/CalculiX paths/hashes absent.
- **Do not reinvent:** no direct arbitrary solver subprocesses.
- **Anchors:** `UNHASHED_SUBPROCESS_TOOL`, `TOOL_HASH_MISMATCH`, `check_registry`.

## Gmsh mesh adapter — REAL adapter; external runtime opt-in
- **What/when:** AnalysisSpec STEP + manifest ports → deterministic `.geo`, tetra mesh, physical groups, quality evidence.
- **Canonical:** `backend/app/modules/bluecad/mesh_adapter.py`.
- **Invoke:** `mesh_analysis_spec`; always registry `run_tool("gmsh")`; one half-size retry only on `MESH_FAIL`.
- **I/O:** `mesh.geo/.inp/.msh`, log, structured result.
- **Preconditions:** safe port labels, resolved ports, enabled hash-pinned Gmsh; order-2 C3D10/Jacobian checks.
- **Risk:** local solver/files, no promotion authority.
- **Evidence:** mesh adapter/SIM-WIRE tests.
- **Limits:** tetrahedral bounded path; heuristic surface selection; default registry cannot run real Gmsh.
- **Anchors:** `mesh_analysis_spec`, `MESH_HIGH_ORDER_INVALID`, `MESH_GROUP_EMPTY`.

## CalculiX static FEM — REAL adapter; external runtime opt-in
- **What/when:** bounded static deck, pressure mapping, ccx, FRD/DAT/reaction/criteria parsing.
- **Canonical:** `backend/app/modules/bluecad/{fem_adapter.py,fem_adapter_base.py,fem_pressure_integration.py,fem_reactions.py,pressure_mapping.py}`.
- **Invoke:** `solve_static_analysis`; registry resolves CalculiX.
- **I/O:** `analysis.inp`, logs/results → `bluecad_result_summary_v0_1` + hashed artifacts.
- **Preconditions:** static analysis, valid mesh groups, enabled hash-pinned CalculiX.
- **Risk:** timeout/divergence/parse/mapping failures advisory and structured.
- **Evidence:** FEM tests + analytic C3D10 verification battery.
- **Limits:** static only; modal/thermal DEFERRED despite registry metadata; default solver disabled.
- **Anchors:** `solve_static_analysis`, `SOLVE_DIVERGED`, `reaction_resultant`.

## Candidate/attempt generate-build-validate loop — REAL
- **What/when:** bounded tiered AI GeometrySpec generation/repair; deterministic parse/build/validate; attempt/evidence/artifact ledger; valid or parked candidate.
- **Canonical:** `backend/app/modules/bluecad/{loop.py,ledger.py,prompts.py,models.py,evidence.py}` + AI execution/budget/settings.
- **Invoke:** `create_bluecad_candidate`; tiers/attempt bounds from `BluecadLoopConfig`.
- **I/O/persistence:** `bluecad_candidates`, `bluecad_attempts`, registered spec/report/manifest/GLB, validation evidence.
- **Preconditions:** provider/budget/config allowed; strict GeometrySpec parse/canonicalization.
- **Risk:** provider calls + CAD process + DB/files. Malformed/provider/config failures never become valid geometry; candidates park fail-closed.
- **Evidence:** BLUECAD loop/ledger/provider tests.
- **Limits:** synchronous bounded loop, not arbitrary AI CAD coding.
- **Do not reinvent:** reuse candidate/attempt ledger.
- **Anchors:** `create_bluecad_candidate`, `start_attempt`, `finish_attempt`, `park_candidate`.

## Evidence-guided structural repair / egress — REAL, tightly bounded
- **What/when:** valid geometry that fails static criteria can enter bounded evidence-guided repair.
- **Canonical:** `bluecad/{loop.py,evidence_sight.py,evidence_egress.py,structural_ledger.py,evidence.py}`.
- **Invoke:** `_run_structural_repair_cycle`, `render_evidence_sight`, `prepare_external_structural_repair`, `start_structural_attempt`.
- **I/O/persistence:** evidence digest/prompt version recorded; speculative attempts do not replace candidate owner artifacts; commit only after rebuild + validation + simulation criteria pass.
- **Preconditions:** pass criteria + resolvable binding. Network preparation fail-closes before attempt insert.
- **Risk:** external prompt strips raw GeometrySpec, project identity, exact dimensions, unpublished parameters, credentials/secrets; lineage bound explicitly.
- **Evidence:** structural-ledger/evidence-sight/evidence-egress tests.
- **Limits:** bounded static repair, not optimizer; no automatic engineering promotion.
- **Do not reinvent:** reuse sanitized evidence path for network repair.
- **Anchors:** `bind_evidence_lineage`, `commit_structural_candidate_artifacts`.

## Candidate aggregate / artifacts / viewer — REAL read projection
- **What/when:** candidate-scoped aggregate of attempts, artifacts, evidence and CAD-link provenance for workbench/viewer.
- **Canonical:** `backend/app/modules/bluecad/read_model.py`, routes/models; `frontend/src/pages/BlueCAD.tsx`.
- **Invoke/I/O:** aggregate/read endpoints; registered GLB + manifest scene binding.
- **Risk:** read-only; no repair/promote/recompute/provider/filesystem scan.
- **Evidence:** 084 read-model + BLUECAD frontend tests.
- **Limits:** cannot infer current viewer selection/session/generation from candidate provenance.
- **Do not reinvent:** no frontend N+1 authority reconstruction.
- **Anchors:** `read_model.py`, `bluecad_cad_links`, `BlueCAD.tsx`.

## Guarded calc/Python runner — REAL, exact-bundled only
- **What/when:** persist/execute reviewed server-known Python models with immutable script identity, contracts, run/job evidence, logs/artifacts and idempotent request keys.
- **Canonical:** `backend/app/modules/runner/{guarded_service.py,service.py,local_python.py,_execution_owner.py,_execution_child.py,safety.py,input_contracts.py,linked_parameters.py}`.
- **Invoke:** guarded `create_runner_job` → `run_runner_job`; bundled registration helpers for reviewed process/topology/kernel profiles.
- **I/O/persistence:** `simulation_runs`, `runner_jobs`, logs, `result.json`/artifacts/events; schema-v1 unit-bearing scalar result envelope.
- **Preconditions:** exact server-known script path/hash/contract; linked Parameters currently usable; timeout ≤60 s.
- **Risk:** child Python process under single-owner cross-process lock; reduced non-inherited env, shell false, byte/time bounds.
- **Evidence:** runner safety/idempotency/input-contract/profile/process-kernel tests.
- **Limits:** NOT arbitrary user/model-authored Python. Non-bundled implementations rejected; batch-growth is demo, not qualified PBR.
- **Do not reinvent:** engineering calculations reuse guarded run lifecycle.
- **Anchors:** `_require_exact_bundled`, `_is_exact_bundled`, `prepare_execution_owner`, `RUNNER_SCRIPT_POLICY_VIOLATION`.

## Process/PBR 047–075 family — MIXED
- **REAL bounded:** 047 geometry/hydraulics/residence/turnover/pumping; 048 biomass/nutrients/gas/harvest/energy-cost KPIs with preliminary-economic boundary; 049 buoyancy + light/transmittance proxies; 052 exact 047→single-tube CAD; 071 input-contract/binding/DOF preview; 071b Properties; 072 symmetric parallel topology M1 **experiment/reference**; 073 capped branch-manifold CAD; 074 topology→multi-part CAD **experiment**; 075 typed acyclic process kernel **historical incumbent**.
- **REAL provenance:** 050 dependency DAG; 051 deterministic stale propagation, no auto-recompute.
- **DEFERRED/CANCELLED:** standalone 078 PBR implementation cancelled/superseded; its scientific planning is historical reference. Future integrated PBR/general process direction waits upstream bakeoff/evaluator authority. Serial topology also waits that boundary.
- **Critical warning:** `runner/examples/batch_growth.py` is a deterministic runner demo, not PBR biology authority.
- **Evidence:** exact bundled runner/golden tests, process-kernel exact-047 identity, topology/CAD-link tests.
- **Limits:** no general recycle convergence, broad thermo/property package, arbitrary unit-op library or qualified integrated PBR biology.
- **Do not reinvent:** reuse exact reviewed models now; do not grow 075 by sunk-cost preference.
- **Anchors:** `bluerev_geometry_hydraulics_v0`, `bluerev_process1`, `bluerev_process2`, `bluerev_topology_m1`, `execute_047_process_kernel`.

## Typed process kernel / exact 047 profile — REAL but HISTORICAL/INCUMBENT
- **What/when:** acyclic typed material/scalar flowsheet with semantic units and unit-operation contracts; exact 047 compatibility profile.
- **Canonical:** `backend/app/modules/process_kernel/**`, `runner/process_kernel_047.py`, `process_kernel_registration.py`.
- **Invoke:** `ProcessFlowsheet.validate()/execute`, `execute_047_process_kernel`.
- **I/O:** immutable in-memory streams/scalars; runner persists evidence. Bounds 64 blocks/256 connections; deterministic topological order.
- **Preconditions:** acyclic, exact external streams/parameters, semantic unit/port compatibility.
- **Risk:** kernel pure; no promotion.
- **Evidence:** `test_process_kernel_075_*`, exact 047 identity.
- **Limits:** not general recycle/network solver; zero sunk-cost privilege pending upstream bakeoff.
- **Anchors:** `ProcessFlowsheet`, `PROFILE_ID`, `semantic_registry_sha256`.

## Dependency/lineage graph — REAL read model
- **What/when:** projects DB authority into provenance graph for models, runs/jobs/artifacts, records, BLUECAD candidates/attempts/evidence/CAD links.
- **Canonical:** `backend/app/modules/flowsheet/{service.py,models.py,routes.py}`.
- **Invoke:** `get_flowsheet_graph`, `get_flowsheet_node`, connection-scoped builder/resolver.
- **I/O:** query-only derived `<kind>:<id>` graph; unresolved refs/cycles/topological order; no graph store. Bounds 1000/3000/200.
- **Risk:** none; malformed/dangling refs become diagnostics.
- **Evidence:** flowsheet API/service + 087 frontend tests.
- **Limits:** lineage, not process simulation/recompute.
- **Do not reinvent:** add provenance to source rows; no second dependency DB.
- **Anchors:** `build_flowsheet_graph_from_connection`, `_GraphBuilder`, `_CANONICAL_KINDS`.

## Freshness/staleness — REAL append-only invalidation evidence
- **What/when:** accepted Parameter replacement computes deterministic downstream closure and stale marks.
- **Canonical:** `backend/app/modules/flowsheet/freshness.py`; Parameter lifecycle transactional caller.
- **Invoke:** `prepare_freshness_invalidation`, `persist_freshness_invalidation`; reads `get_node_freshness`, `get_freshness_invalidation`.
- **I/O/persistence:** `freshness_invalidations` + `freshness_marks`, canonical path/digest + graph digest; path ≤100, marks ≤1000.
- **Preconditions:** source Parameter resolves; unresolved supported lineage in closure fails closed.
- **Risk:** marks only; never auto-mutates/recomputes downstream values.
- **Evidence:** 051 lifecycle/CAD-link staleness tests.
- **Limits:** freshness is provenance state, not scientific validity.
- **Do not reinvent:** reuse graph + marks.
- **Anchors:** `PreparedFreshnessInvalidation`, `upstream_parameter_superseded`.

## Process → CAD handoff — REAL, bounded transformations
- **What/when:** succeeded process run → deterministic BLUECAD child. 052 exact 047 M0 single `tube_run`; 074 topology-M1 multi-part experiment.
- **Canonical:** `backend/app/modules/bluecad/cad_link.py`, `cad_link_topology_execute.py`, topology preview/build modules, CAD-link schema.
- **Invoke:** `preview_cad_link_047` → digest-bound `execute_cad_link_047`; topology path uses same preview-digest lifecycle.
- **I/O/persistence:** immutable source snapshot/model identity/reconciliation/digests in `bluecad_cad_links`, child candidate/attempt/artifacts/evidence; `(workspace_id, preview_digest)` idempotent.
- **Preconditions:** exact recognized succeeded source run; execute rechecks preview transactionally.
- **Risk:** deterministic candidate/artifact creation; no AI for 047 link.
- **Evidence:** `test_cad_link.py`, `test_cad_link_topology_execute.py`.
- **Limits:** 047 is one proxy; M1 is experiment, not general process→CAD synthesis.
- **Do not reinvent:** reuse preview digest + immutable snapshot/link lifecycle.
- **Anchors:** `TRANSFORMATION_VERSION`, `preview_digest`, `bluecad_cad_links`.

## Engineering Properties / working configuration / preflight / run creation — REAL frontend owner
- **What/when:** one transient operator configuration: baseline/effective bindings, Parameter selection, dirty state, max-20 Undo, revert, deterministic preview/preflight, run snapshot/idempotency, semantic target/source composition.
- **Canonical:** `frontend/src/components/engineering/EngineeringProperties.tsx`; App composition + previous-run/Jarvis engineering helpers.
- **Invoke:** `useEngineeringProperties` / controller; model/parameter/binding-preview/runner APIs.
- **I/O:** frontend transient state; explicit Run creates server job/run; `crypto.randomUUID()` request identity.
- **Preconditions:** registered model/contract/workspace; finite numeric bindings; scene semantics currently narrow to reviewed 047 tubular-loop part.
- **Risk:** edits local until explicit Run/lifecycle action; Jarvis compare-and-apply guards workspace/model/contract/revision/fingerprint.
- **Evidence:** Properties harness/check scripts, 071b/058c/097 tests.
- **Limits:** not persistent design-config DB.
- **Do not reinvent:** compose this owner.
- **Anchors:** `EngineeringPropertiesController`, `reviewedContractForTarget`, `startRun`.

## Runs / evidence / previous-run reuse — REAL
- **What/when:** persisted run history/detail/input/output/log/artifact workbench; explicit successful-run reload into transient Properties.
- **Canonical:** `frontend/src/pages/RunsWorkbench.tsx`, `components/runs/{state.ts,stateHarness.ts}`, `api/runs.ts`; runner reads.
- **Invoke:** `listRuns`, `getRun`, `listRunLogs`, `listRunArtifacts`.
- **I/O:** read persisted run evidence; previous-run load changes only transient Properties.
- **Preconditions:** exact workspace/run; compatible model contract for reload.
- **Risk:** dirty config requires confirmation/revision match; async generation+identity guards reject stale responses.
- **Evidence:** runs harness + `scripts/check_runs_workbench.py`.
- **Limits:** no live stream; run success is execution evidence, not accepted engineering truth.
- **Anchors:** `RunsWorkbench`, `loadPreviousSuccessfulRun`, `acceptsResponse`.

## Analytics / comparison — REAL bounded frontend analysis
- **What/when:** compare persisted succeeded run outputs and exact engineering input configurations.
- **Canonical:** `frontend/src/components/analytics/{analyticsState.ts,AnalyticsDockContent.tsx,analyticsStateHarness.ts,variantComparisonNavigation.ts}`.
- **Invoke:** `projectAnalyticsRun`, `compareAnalyticsRuns`, `compareEngineeringConfigurations`; max 6 runs.
- **I/O:** read-only; schema-v1 output extraction bounded to 1 MiB/128 keys; exact units; no conversion.
- **Preconditions:** succeeded runs; direct comparison requires same exact model version.
- **Risk:** malformed/non-finite/missing/oversized data reject rather than silently truncate.
- **Evidence:** analytics harness/checker.
- **Limits:** scalar unit-bearing outputs only; no uncertainty/statistics/general plotting/unit conversion.
- **Do not reinvent:** reuse bounded comparison helpers.
- **Anchors:** `MAX_SELECTED_RUNS`, `compareAnalyticsRuns`, `compareEngineeringConfigurations`.

## Engineering records/lifecycle — REAL; Parameter-first mutation
- **What/when:** Engineering Data projection of model-spec/assumption/parameter/decision; server lifecycle/CAS for mutation.
- **Canonical:** `frontend/src/components/engineering-data/engineeringDataState.ts`, `pages/EngineeringData.tsx`; backend MemoryStore/modeling Parameter lifecycle.
- **I/O:** canonical SQLite records; frontend derived projection.
- **Preconditions:** current workspace/revision, explicit operator transition.
- **Risk:** accepted Parameter replacement may atomically trigger 051 staleness.
- **Evidence:** Engineering Data harness/check + lifecycle/CAS/staleness tests.
- **Limits:** other record kinds are not assumed symmetrically editable.
- **Do not reinvent:** canonical stores remain authority.
- **Anchors:** `EngineeringRecordProjection`, `parameter_lifecycle.py`.

## External solver / Windows-local seam — PARTIAL operational capability
- **What/when:** adapters are real; workstation solver availability is operator configuration.
- **Canonical:** registry/config + mesh/FEM adapters + real-tool proof tests.
- **Invoke:** install/configure exact binary path/hash/provenance/license; registry health before solve.
- **Preconditions:** compatible local Gmsh/CalculiX. Runner ownership supports Windows via `msvcrt` and POSIX via `fcntl`; repo does not embed machine paths/hashes.
- **Risk:** native executable; never weaken hash/license boundary.
- **Evidence:** fake-executable deterministic tests + optional real-tool proof.
- **Limits:** green default CI does not prove a specific Windows machine has working solvers.
- **Do not reinvent:** configure registry; no direct Windows solver subprocess seam.
- **Anchors:** `JARVISOS_BLUECAD_TOOL_REGISTRY`, `msvcrt.locking`.

## Deterministic/property/golden/cross-process verification — REAL, distributed
- **What/when:** regression net for geometry/export, spawn/timeout, registry, mesh/FEM, runner ownership/idempotency, process identity, CAD links, staleness and frontend engineering state.
- **Canonical:** `backend/tests/bluecad/**`, `backend/tests/test_{cad_link,cad_link_topology_execute,process_kernel_075_*,runner*,flowsheet*,freshness*}.py`, frontend engineering/runs/analytics harnesses.
- **Invoke:** targeted pytest + repository checker scripts; real-tool tests separately configured.
- **Risk:** test temp processes/files only.
- **Evidence:** property/golden BLUECAD, analytic C3D10, exact 047 identity, CAD-link replay/stale, cross-process ownership.
- **Limits:** deterministic equality ≠ scientific validity; real solver proof environment-dependent.
- **Do not reinvent:** extend nearest fixture/harness.
- **Anchors:** `backend/tests/bluecad`, `test_process_kernel_075`, `analyticsStateHarness`.

## Custom-process / future upstream bakeoff boundary — REAL limitation; DEFERRED decision
- **What/when:** custom equations/kernel are useful bounded incumbents, not authority for a proprietary general simulator.
- **Canonical:** process-kernel/runner runtime + canonical STATUS authority.
- **Reuse:** exact reviewed bundled models/fixtures only until separately authorized upstream bakeoff/evaluator decision.
- **Risk:** major architecture error would be treating 075 or 072/074 experiments as canonical general process-design authority.
- **Evidence:** exact 047 cross-implementation identity proves compatibility only for that profile.
- **Limits:** no general recycle convergence, broad thermo/property package, arbitrary unit-op library, or qualified integrated PBR biology.
- **Do not reinvent:** no custom-kernel/PBR expansion before bakeoff authority.
- **Anchors:** `process_kernel`, `bluerev_topology_m1`, STATUS upstream bakeoff/evaluator rows.

## Remaining coverage
- File-level audit of 047/048/049/072 bundled scripts/contracts and model-specific golden/property tests.
- File-level audit of topology-M1 preview/execute and 073 branch-manifold builder for additional reusable primitives/limits.
- Area-C artifact registration + typed evidence schema sweep for details not represented above.
- Final backend/frontend/test directory sweep for any major uninspected Area-C subsystem; only then mark COMPLETE.