# Area C — Engineering / BLUECAD / process / scientific tooling

MAPPING_STATUS: IN_PROGRESS

Source-of-truth audit base: `master` at `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Runtime/code/tests are primary evidence; STATUS/spec prose below is used to classify historical/deferred authority, not to infer implementation.

## BLUECAD GeometrySpec → deterministic CAD/export — REAL
- **What/when:** Canonicalize a bounded GeometrySpec, construct typed parts/assemblies with build123d/OCP, export STEP/STL/GLB, and emit manifest + validation report. Reuse for any current trusted BLUECAD geometry build; do not bypass with ad-hoc CAD exporters.
- **Canonical files:** `backend/app/modules/bluecad/{spec.py,builders.py,assembly.py,service.py,export.py,validate.py,models.py,cli.py}`.
- **Invoke/reuse:** `build_geometry_spec(spec, out_dir, timeout_s=30)` or `build_geometry_spec_file(...)`; CLI imports the same service. Build runs in a spawned worker and is killed on timeout.
- **I/O/persistence:** input GeometrySpec dict/file; output `model.step`, `model.stl`, `model.glb`, `manifest.json`, `validation_report.json`. STEP wall-clock header is normalized; manifest hashes artifacts and has a canonical digest. No DB write in the build API itself.
- **Preconditions:** build123d importable in the execution environment. `configs/bluecad_tools.yaml` currently declares build123d `0.11.1` but leaves it disabled; the direct CAD path imports build123d rather than resolving it through the registry.
- **Side effects/risk:** filesystem writes and a local spawned CAD-kernel process only. Structured `SPEC_INVALID`, `KERNEL_ERROR`, `EXPORT_ERROR`, `TIMEOUT` evidence; partial artifact sizes/phase are retained on abnormal worker exit.
- **Tests/evidence:** `backend/tests/bluecad/test_adapter_stage2.py`, `test_005_conformance.py`, `test_build_service_spawn.py`, property/golden suites under `backend/tests/bluecad/`; spec-056 report documents the offline determinism net.
- **Limitations:** deterministic equivalence is same pinned kernel/tool environment, not a cross-version CAD guarantee. Geometry vocabulary is bounded typed builders, not arbitrary generated CAD code.
- **Do not reinvent:** reuse canonicalization + `build_geometry_spec` + manifest/report contract for new trusted primitives.
- **Search anchors:** `build_geometry_spec`, `build_artifacts`, `canonicalize_geometry_spec`, `ARTIFACT_NAMES`, `manifest_digest`.

## Scene-bound GLB / part identity — REAL
- **What/when:** Exports each manifest part as a deterministic GLTF-visible wrapper and records a bijective scene-key → canonical `part_id` map; use for viewer selection and semantic handoff.
- **Canonical files:** `backend/app/modules/bluecad/export.py`; downstream frontend selection/Properties composition uses the manifest binding.
- **Invoke/reuse:** automatic inside `build_artifacts`; `_scene_binding_key(part_id)` is SHA-256-derived and bounded rather than embedding arbitrary user IDs in node labels.
- **I/O/persistence:** `model.glb` plus `manifest.scene_binding={version,artifact,spec_id,objects}`.
- **Preconditions:** every built part must be selectable; empty/colliding/non-bijective bindings fail export.
- **Side effects/risk:** artifact generation only; scene hits carry identity but do not themselves mutate engineering records or working configuration.
- **Tests/evidence:** exporter validation plus merged scene-binding/runtime tests (092 family).
- **Limitations:** semantic meaning beyond canonical part identity is separately gated; geometry-only viewer hits are not engineering authority.
- **Do not reinvent:** never create a second frontend object-ID map when the manifest scene binding exists.
- **Search anchors:** `SCENE_BINDING_VERSION`, `_scene_bound_gltf_shape`, `_validate_scene_binding_manifest`, `bluecad-part-sha256-`.

## Tool registry, hash verification, health and execution — REAL framework / default tools DISABLED
- **What/when:** Operator-selected registry for CAD/mesher/FEM/etc metadata; validates exact versions/licenses/integration modes and fail-closes subprocess/container tools on missing/mismatched SHA-256 before execution.
- **Canonical files:** `backend/app/modules/bluecad/registry.py`, `configs/bluecad_tools.yaml`.
- **Invoke/reuse:** `load_registry`, `resolve_tool`, `run_tool`; `python -m app.modules.bluecad.registry check` via registry CLI. Override registry with explicit path or `JARVISOS_BLUECAD_TOOL_REGISTRY`.
- **I/O/persistence:** YAML registry in; captured returncode/stdout/stderr out. Subprocess env is reduced (`PATH`, UTF-8, `OMP_NUM_THREADS=1`); `shell=False`.
- **Preconditions:** enabled subprocess/container entries require entrypoint, exact `binary_sha256`, provenance URL and valid license metadata. Boundary C/D tools cannot be in-process.
- **Side effects/risk:** executes only registry-authored/hash-matched binary plus adapter-authored args. Timeout returns code 124. Health check for subprocess tools must begin with the registered entrypoint.
- **Tests/evidence:** `backend/tests/bluecad/test_registry.py`; mesh/FEM tests use hash-pinned fake executables.
- **Limitations:** checked-in registry currently has build123d, gmsh 4.13.1 and CalculiX 2.22 all `enabled: false`; gmsh/CalculiX entrypoint/hash/provenance are null. Real solver use therefore requires an operator-owned configured registry.
- **Do not reinvent:** external engineering binaries must use this hash/license boundary, not direct arbitrary subprocess calls.
- **Search anchors:** `resolve_tool`, `run_tool`, `check_registry`, `UNHASHED_SUBPROCESS_TOOL`, `TOOL_HASH_MISMATCH`.

## Gmsh mesh adapter — REAL adapter / external runtime opt-in
- **What/when:** Converts AnalysisSpec geometry STEP + BLUECAD manifest ports into deterministic Gmsh `.geo`, tetrahedral `.inp/.msh`, physical groups and bounded mesh-quality evidence.
- **Canonical files:** `backend/app/modules/bluecad/mesh_adapter.py`, registry above.
- **Invoke/reuse:** `mesh_analysis_spec(analysis_spec, out_dir, registry_path=..., timeout_s=60)`; always calls registry `run_tool("gmsh", ...)`.
- **I/O/persistence:** reads STEP/manifest; writes `mesh.geo`, `mesh.inp`, `mesh.msh`, `gmsh.log`; returns structured result/attempt/artifact maps. One automatic retry at half target size only for `MESH_FAIL`.
- **Preconditions:** safe alphanumeric/underscore port labels; manifest-resolved ports; enabled hash-pinned Gmsh. Supports element order 1/2; order 2 must yield C3D10 and no detected inverted/negative-Jacobian diagnostics.
- **Side effects/risk:** local external solver subprocess + files; no promotion authority.
- **Tests/evidence:** `backend/tests/bluecad/test_mesh_adapter.py`, SIM-WIRE tests, real-tool proof family where configured.
- **Limitations:** bounded tetrahedral path, heuristic bounding-box physical-surface selection; not a generic meshing platform. Default registry cannot run it.
- **Do not reinvent:** use this adapter and its physical-group/error contract for static BLUECAD FEM.
- **Search anchors:** `mesh_analysis_spec`, `_geo_text`, `_post_check`, `MESH_HIGH_ORDER_INVALID`, `MESH_GROUP_EMPTY`.

## CalculiX static FEM adapter — REAL adapter / external runtime opt-in
- **What/when:** Builds a bounded static CalculiX deck from AnalysisSpec + mesh result, maps solid-face pressure, runs ccx, parses FRD/DAT, reactions and criteria.
- **Canonical files:** `backend/app/modules/bluecad/fem_adapter.py`, `fem_adapter_base.py`, `fem_pressure_integration.py`, `fem_reactions.py`, `pressure_mapping.py`.
- **Invoke/reuse:** `solve_static_analysis(...)`; registry resolves/runs `calculix`.
- **I/O/persistence:** writes `analysis.inp`, log and solver outputs; returns `bluecad_result_summary_v0_1`, solver version/returncode, parsed fields, criteria and hashed artifacts.
- **Preconditions:** `analysis_type == static`; valid mesh groups; enabled hash-pinned CalculiX. Pressure mapping may generate a solid solver mesh.
- **Side effects/risk:** local solver subprocess/files only; TIMEOUT/divergence/parse/mapping failures are structured and advisory.
- **Tests/evidence:** `backend/tests/bluecad/test_fem_adapter.py`; 024 analytic C3D10 verification battery is merged and records deterministic reports.
- **Limitations:** production solve path supports static only. STATUS keeps modal/thermal as planned spec 027 even though registry capability metadata names them; metadata is not runtime support. Default CalculiX entry is disabled.
- **Do not reinvent:** extend only from this verified static boundary when a real analysis class is authorized.
- **Search anchors:** `solve_static_analysis`, `_prepare_pressure_mappings`, `_parse_outputs`, `SOLVE_DIVERGED`, `reaction_resultant`.

## Process kernel / exact 047 profile — REAL but HISTORICAL/INCUMBENT, not generic process-design authority
- **What/when:** Typed acyclic material/scalar flowsheet engine with streams, semantic units and unit-operation contracts; current bundled profile reproduces exact BlueRev 047 geometry/hydraulics identity.
- **Canonical files:** `backend/app/modules/process_kernel/{flowsheet.py,streams.py,contracts.py,units.py,profile_047.py,...}`, `backend/app/modules/runner/process_kernel_047.py`, `process_kernel_registration.py`, bundled example script.
- **Invoke/reuse:** `ProcessFlowsheet.validate()/execute(...)`; `execute_047_process_kernel`; bundled runner registration uses exact server-known profile identity.
- **I/O/persistence:** immutable typed streams/scalars in memory; runner layer persists normal simulation-run/job/artifact evidence. Flowsheet enforces max 64 blocks/256 connections, one driver per input, exact port/unit/semantic-basis compatibility and deterministic topological order.
- **Preconditions:** acyclic graph; exact external stream and caller-parameter sets; finite scalars; required stream fields/composition present.
- **Side effects/risk:** kernel itself pure/in-memory; runner execution is bounded by calc runner safety. No automatic engineering promotion.
- **Tests/evidence:** `backend/tests/test_process_kernel_075_*`, exact 047 identity tests, runner tests.
- **Limitations/authority:** STATUS explicitly classifies 075 as a **historical acyclic typed process-kernel experiment with exact 047 identity**, zero sunk-cost privilege; no generic solver expansion before future upstream bakeoff. It may later be wrapped/reduced/deleted. It is not proof that arbitrary process networks/recycles are supported.
- **Do not reinvent:** reuse equations/fixtures/semantic-unit helpers when appropriate, but do not treat the custom kernel as mandatory future architecture.
- **Search anchors:** `ProcessFlowsheet`, `execute_047_process_kernel`, `PROFILE_ID`, `semantic_registry_sha256`, `flowsheet_driver_duplicate`.

## Process/PBR 047–075 authority snapshot — MIXED
- **REAL/current bounded models:** 047 `BLUEREV-PROCESS-0` deterministic calc model (geometry/hydraulics/residence/turnover/pumping); 048 biomass/nutrients/gas/harvest/energy-cost KPIs with explicit preliminary-economic boundary; 049 buoyancy + light/transmittance proxies; 052 one-run 047→one-`tube_run` CAD link; 071 immutable input-contract/binding/DOF preview; 071b Properties owner; 072 deterministic symmetric parallel topology M1 **experiment/reference, not canonical default**; 073 capped branch-manifold CAD primitive; 074 072→multi-part CAD link **experiment, not process-design authority**; 075 process kernel as historical incumbent.
- **REAL provenance machinery:** 050 read-only dependency DAG; 051 deterministic stale propagation when accepted inputs change; no auto-recompute.
- **CANCELLED/DEFERRED:** 078 standalone PBR modeling implementation is cancelled/superseded; its planning/scientific evidence is historical reference only. STATUS assigns future integrated PBR evaluator authority to 107 after upstream bakeoff/evaluator work. 093 future serial topology waits for process bakeoff + typed handoff.
- **Critical warning:** `examples/batch_growth.py` is only a deterministic runner demo, not a qualified PBR biology model. Do not represent 078 prose or the batch-growth demo as current PBR runtime capability.
- **Search anchors:** STATUS rows `047`–`078`, `bluerev_geometry_hydraulics_v0`, `process_kernel_047`, `bluecad_cad_links`.

## Dependency/lineage graph — REAL read model
- **What/when:** Materializes workspace dependency/provenance graph from existing DB authority for model specs/versions, runs/jobs/artifacts, engineering records, BLUECAD candidates/attempts, evidence and CAD links. Use for lineage/freshness inspection, not as a recompute engine.
- **Canonical files:** `backend/app/modules/flowsheet/{service.py,models.py,routes.py}`.
- **Invoke/reuse:** `get_flowsheet_graph(workspace_id)`, `get_flowsheet_node`, connection-scoped builders/resolver.
- **I/O/persistence:** query-only SQLite transaction; derives canonical `<kind>:<id>` nodes/edges, authorities/source fields, unresolved-reference diagnostics, cycles and topological order. No graph table/store.
- **Preconditions:** workspace exists; bounded to 1000 nodes/3000 edges/200 diagnostics.
- **Side effects/risk:** none; `PRAGMA query_only`. Dangling/malformed/unsupported refs become diagnostics rather than invented nodes.
- **Tests/evidence:** flowsheet service/API tests and 087 frontend lineage workbench checks.
- **Limitations:** provenance/read model only; no graph-layout engine and no automatic recomputation. 051 owns stale propagation separately.
- **Do not reinvent:** add provenance at source records and let this projection derive the graph; do not create a second dependency DB.
- **Search anchors:** `build_flowsheet_graph_from_connection`, `_GraphBuilder`, `_CANONICAL_KINDS`, `bound_input`, `bluecad_cad_links`.

## Engineering Properties / transient working configuration — REAL frontend owner
- **What/when:** Single transient operator working configuration over authoritative model input contracts: baseline/effective bindings, Parameter selection, dirty state, max-20 Undo, field/all revert, deterministic preview/preflight, run-start snapshot/idempotency and semantic target/source composition.
- **Canonical files:** `frontend/src/components/engineering/EngineeringProperties.tsx`; composed by `frontend/src/App.tsx`; previous-run loading helper and Jarvis engineering actions reuse this controller.
- **Invoke/reuse:** `useEngineeringProperties` / `EngineeringPropertiesController`; API calls `listModelImplementations`, `listParameters`, `previewModelBindings`, `createRunnerJob`, `runRunnerJob`, plus guarded BLUECAD aggregate lookup for reviewed scene semantics.
- **I/O/persistence:** working/baseline/undo/revision are frontend transient state; Run creates normal server runner job/run state. `crypto.randomUUID()` supplies secure request identity.
- **Preconditions:** selected registered model/input contract and workspace; numeric finite bindings; semantic geometry is accepted only for the exact reviewed 047 tubular-loop option/part gate.
- **Side effects/risk:** edits are local until explicit Run or record lifecycle action. Scene selection supplies context only. Jarvis actions use compare-and-apply against workspace/model/contract/revision/fingerprint and cannot silently self-certify stale proposals.
- **Tests/evidence:** engineering-properties harness/check scripts, 071b/058c/097 deterministic frontend tests.
- **Limitations:** one transient owner, not a persistent design-configuration database. Current object-semantic geometry is deliberately narrow to reviewed 047 `illuminated_tube_proxy`/`tube_run`.
- **Do not reinvent:** all future engineering editing/preflight/run UI must compose this owner rather than a second working-state store.
- **Search anchors:** `EngineeringPropertiesController`, `buildPayload`, `reviewedContractForTarget`, `startRun`, `applyWorkingAction`.

## Engineering records/lifecycle — REAL, Parameter-first mutation boundary
- **What/when:** Engineering Data projects model-spec/assumption/parameter/decision records for search/inspection; lifecycle mutation is server-owned and, in current V0, Parameter-first.
- **Canonical files:** frontend `components/engineering-data/engineeringDataState.ts`, `pages/EngineeringData.tsx`; backend MemoryStore/record lifecycle services are shared with Area A.
- **Invoke/reuse:** use canonical Engineering Data projection/search/selection; mutate through server lifecycle endpoints/CAS rather than editing projected rows.
- **I/O/persistence:** canonical records persist in SQLite; frontend projection is derived. Parameter lifecycle tracks exact CAS/audit/dependency state, linked source revision and unit-normalized value identity.
- **Preconditions:** workspace/current revision; transitions are explicit operator authority.
- **Side effects/risk:** accepted record edits can trigger 051 stale propagation. Other record kinds remain read-only in the 098 lifecycle V0.
- **Tests/evidence:** `engineeringDataStateHarness.ts`, `scripts/check_engineering_data.py`, backend lifecycle/CAS/staleness tests.
- **Limitations:** do not infer symmetric edit support for every engineering record kind.
- **Do not reinvent:** MemoryStore/canonical records remain authority; Engineering Data is a projection/workbench, not another store.
- **Search anchors:** `EngineeringRecordProjection`, `projectEngineeringData`, `recordKey`, spec/STATUS 098.

## Remaining coverage
- BLUECAD candidate/attempt AI loop, evidence-guided repair (010/038/076/077), candidate aggregate/read model and lifecycle APIs.
- Calc runner execution/artifact/proposal details and bundled-only safety boundary.
- 047/048/049/072 runner implementations and exact tests; 051 stale service; 052/074 process→CAD code paths.
- Runs/evidence/lineage analytics/comparison implementation details (044/084/087/088/089/058b), artifact registration and viewer/workbench lifecycle.
- Deterministic/property/golden/cross-process test matrix and Windows/real-solver requirements/proof.
- Current custom-process limitations and explicit future upstream bakeoff boundary (103–109) from runtime/STATUS.
