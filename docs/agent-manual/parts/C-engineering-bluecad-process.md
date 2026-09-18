# Area C — Engineering / BLUECAD / process / scientific tooling

MAPPING_STATUS: IN_PROGRESS

Runtime/code/tests are primary evidence; STATUS/spec prose is used only to classify historical/deferred authority.

## GeometrySpec → CAD/export — REAL
- **What/when:** bounded typed GeometrySpec → build123d/OCP parts/assemblies → STEP/STL/GLB + manifest/validation. Use for trusted BLUECAD geometry.
- **Canonical:** `backend/app/modules/bluecad/{spec.py,builders.py,assembly.py,service.py,export.py,validate.py,models.py,cli.py}`; `schemas/bluecad_geometry_spec_v0_1.schema.json`.
- **Invoke/reuse:** `build_geometry_spec`, `build_geometry_spec_file`; spawned worker with hard timeout; `build_part` for reviewed primitives.
- **I/O/persistence:** filesystem artifacts plus canonical manifest hashes/digest; build API itself does not create product DB authority.
- **Preconditions:** build123d/OCP available; valid bounded GeometrySpec.
- **Side effects/risk:** local CAD process/files; structured spec/kernel/export/timeout failures.
- **Tests/evidence:** `backend/tests/bluecad/` conformance, spawn, property and golden suites.
- **Limits:** bounded vocabulary, not generic CAD; determinism is tied to pinned kernel/tool environment.
- **Do not reinvent:** reuse canonicalization/build/export/manifest/report and existing part kinds.
- **Anchors:** `build_geometry_spec`, `canonicalize_geometry_spec`, `manifest_digest`, `build_part`.

## Capped branch manifold primitive (073) — REAL
- **What/when:** deterministic fluid-open capped header with one common opening and 1–12 open branch bores; reusable when a topology needs an honest split/merge geometry.
- **Canonical:** `backend/app/modules/bluecad/capped_manifold.py`, `builders.py`, `spec.py`.
- **Invoke/reuse:** `build_capped_manifold`; `build_capped_manifold_kernel` exposes the exact shared solid/outer/void construction used by 074 preflight.
- **I/O:** `BuiltPart` with common/branch port frames, positive solid and cavity volumes; no persistence by primitive itself.
- **Preconditions:** validated dimensions/walls/gaps/count; build123d.
- **Risk:** pure deterministic geometry construction; invalid/non-positive cavity fails.
- **Evidence:** `backend/tests/bluecad/test_capped_manifold.py`, property invariants, topology preflight/execute tests.
- **Limits:** fixed straight capped-header family; not routing, fabrication design, clearance solver, or complete loop geometry.
- **Do not reinvent:** use the shared kernel for geometry/preflight consistency instead of a second manifold solid implementation.
- **Anchors:** `CappedManifoldKernelGeometry`, `build_capped_manifold_kernel`, `PART_KIND = "capped_manifold"`.

## Scene-bound GLB / semantic part identity — REAL
- **What/when:** deterministic GLTF scene key ↔ canonical `part_id` binding for viewer selection and engineering context.
- **Canonical:** `backend/app/modules/bluecad/export.py`; frontend viewer/Properties consumers.
- **Invoke/I/O:** automatic in export via `manifest.scene_binding`; collisions/non-bijection fail.
- **Authority/risk:** identity/context only; viewer hit does not mutate engineering state.
- **Evidence:** exporter + 092 scene-binding tests.
- **Limits:** semantic meaning beyond part identity is separately gated and currently narrow.
- **Do not reinvent:** no second frontend object-ID map.
- **Anchors:** `SCENE_BINDING_VERSION`, `_validate_scene_binding_manifest`.

## Tool registry / health / hash-pinned execution — REAL framework; checked-in external tools DISABLED
- **What/when:** operator registry for CAD/mesh/FEM binaries with exact version/license/integration/hash enforcement.
- **Canonical:** `backend/app/modules/bluecad/registry.py`, `configs/bluecad_tools.yaml`.
- **Invoke:** `load_registry`, `resolve_tool`, `run_tool`, registry `check`; override `JARVISOS_BLUECAD_TOOL_REGISTRY`.
- **I/O:** reduced env, `shell=False`, bounded stdout/stderr/timeout.
- **Preconditions:** enabled external entries need entrypoint, SHA-256, provenance and license metadata.
- **Risk:** native execution only after registry/hash checks.
- **Evidence:** `backend/tests/bluecad/test_registry.py`, hash-pinned fake executables.
- **Limits:** checked-in build123d/Gmsh/CalculiX entries are disabled; Gmsh/CalculiX machine paths/hashes are intentionally absent.
- **Do not reinvent:** never add direct arbitrary solver subprocesses around this registry.
- **Anchors:** `UNHASHED_SUBPROCESS_TOOL`, `TOOL_HASH_MISMATCH`, `check_registry`.

## Gmsh mesh adapter — REAL adapter; external runtime opt-in
- **What/when:** AnalysisSpec STEP + manifest ports → deterministic `.geo`, tetra mesh, physical groups and mesh-quality evidence.
- **Canonical:** `backend/app/modules/bluecad/mesh_adapter.py`.
- **Invoke:** `mesh_analysis_spec`; registry `run_tool("gmsh")`; one half-size retry only on `MESH_FAIL`.
- **I/O:** `mesh.geo/.inp/.msh`, log, structured `bluecad_mesh_result_v0_1` result.
- **Preconditions:** safe port labels/resolved ports, enabled hash-pinned Gmsh; order-2 C3D10/Jacobian checks where requested.
- **Risk:** local solver/files; no promotion authority.
- **Evidence:** mesh adapter/SIM-WIRE tests and optional real-tool proof.
- **Limits:** bounded tetra path and heuristic surface selection; default registry cannot run real Gmsh.
- **Do not reinvent:** reuse AnalysisSpec/registry/evidence path.
- **Anchors:** `mesh_analysis_spec`, `MESH_HIGH_ORDER_INVALID`, `MESH_GROUP_EMPTY`.

## CalculiX static FEM — REAL adapter; external runtime opt-in
- **What/when:** bounded static deck, pressure mapping, ccx execution, FRD/DAT/reaction/criteria parsing.
- **Canonical:** `backend/app/modules/bluecad/{fem_adapter.py,fem_adapter_base.py,fem_pressure_integration.py,fem_reactions.py,pressure_mapping.py}`.
- **Invoke:** `solve_static_analysis`; registry resolves CalculiX.
- **I/O:** `analysis.inp`, logs/results → `bluecad_result_summary_v0_1` plus hashed artifacts.
- **Preconditions:** static analysis, valid mesh groups, enabled hash-pinned CalculiX.
- **Risk:** timeout/divergence/parse/mapping failures remain advisory and structured.
- **Evidence:** FEM tests + analytic C3D10 verification battery + optional real-tool proof.
- **Limits:** static only; modal/thermal are DEFERRED despite registry metadata; default solver disabled.
- **Do not reinvent:** extend static adapter/typed evidence before adding solver-specific execution paths.
- **Anchors:** `solve_static_analysis`, `SOLVE_DIVERGED`, `reaction_resultant`.

## Candidate/attempt generate-build-validate loop — REAL
- **What/when:** bounded tiered AI GeometrySpec generation/repair; deterministic parse/build/validate; attempt/evidence/artifact ledger; valid or parked candidate.
- **Canonical:** `backend/app/modules/bluecad/{loop.py,ledger.py,prompts.py,models.py,evidence.py}` plus AI execution/budget/settings.
- **Invoke:** `create_bluecad_candidate`; tiers/attempt bounds from `BluecadLoopConfig`.
- **I/O/persistence:** `bluecad_candidates`, `bluecad_attempts`, registered spec/report/manifest/GLB, validation evidence.
- **Preconditions:** provider/budget/config allowed; strict GeometrySpec parse/canonicalization.
- **Risk:** provider calls + CAD process + DB/files; malformed/provider/config failures never become valid geometry and candidates park fail-closed.
- **Evidence:** BLUECAD loop/ledger/provider tests.
- **Limits:** synchronous bounded loop, not arbitrary AI CAD coding.
- **Do not reinvent:** reuse candidate/attempt ledger and deterministic validation gates.
- **Anchors:** `create_bluecad_candidate`, `start_attempt`, `finish_attempt`, `park_candidate`.

## Evidence-guided structural repair / egress — REAL, tightly bounded
- **What/when:** valid geometry that fails static criteria can enter bounded evidence-guided repair.
- **Canonical:** `bluecad/{loop.py,evidence_sight.py,evidence_egress.py,structural_ledger.py,evidence.py}`.
- **Invoke:** `_run_structural_repair_cycle`, `render_evidence_sight`, `prepare_external_structural_repair`, `start_structural_attempt`.
- **I/O/persistence:** evidence digest/prompt version recorded; speculative attempts do not replace candidate owner artifacts; commit only after rebuild + validation + simulation criteria pass.
- **Preconditions:** pass criteria + resolvable binding; network preparation fails closed before attempt insert.
- **Risk:** external prompt strips raw GeometrySpec, project identity, exact dimensions, unpublished parameters and credentials/secrets; lineage is explicitly bound.
- **Evidence:** structural-ledger/evidence-sight/evidence-egress tests.
- **Limits:** bounded static repair, not optimizer; no automatic engineering promotion.
- **Do not reinvent:** reuse sanitized evidence path for network repair.
- **Anchors:** `bind_evidence_lineage`, `commit_structural_candidate_artifacts`.

## Typed BLUECAD evidence/artifact records — REAL
- **What/when:** normalize validation, mesh and static-FEM outputs into bounded evidence records linked to immutable report artifacts.
- **Canonical:** `backend/app/modules/bluecad/evidence.py`; artifact registration in `loop.py`; DB schema in `backend/app/core/schema.py`.
- **Invoke:** `map_*_evidence`, `record_*_evidence`, `create_evidence_record`; candidate-scoped selectors for read model/repair.
- **I/O/persistence:** `evidence_records` kinds are exactly `validation_v0`, `mesh_quality_v0`, `fem_static_v0`; each carries verdict, canonical metrics JSON, source/candidate/attempt refs and `report_artifact_id`. Artifacts carry stored path/type/MIME/SHA/source/status.
- **Preconditions:** typed result/report shape; report artifact already registered.
- **Risk:** append evidence only; does not make engineering acceptance truth. Malformed result mappings reject.
- **Evidence:** evidence mapper/ledger/read-model and topology evidence-fence tests.
- **Limits:** fixed evidence kinds/metrics; no uncertainty model or generic scientific evidence ontology.
- **Do not reinvent:** add evidence through typed records and immutable artifact hashes, not ad-hoc JSON blobs in UI state.
- **Anchors:** `EvidenceKind`, `EvidenceRecordCreate`, `map_mesh_quality_evidence`, `map_fem_static_evidence`, `map_validation_evidence`.

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
- **I/O/persistence:** `simulation_runs`, `runner_jobs`, logs, `result.json`/artifacts/events`; schema-v1 unit-bearing scalar result envelope.
- **Preconditions:** exact server-known script path/hash/contract; linked Parameters currently usable; timeout ≤60 s.
- **Risk:** child Python process under single-owner cross-process lock; reduced non-inherited env, shell false, byte/time bounds.
- **Evidence:** runner safety/idempotency/input-contract/profile/process-kernel tests.
- **Limits:** NOT arbitrary user/model-authored Python. Non-bundled implementations reject; `batch_growth.py` is a demo, not qualified PBR.
- **Do not reinvent:** engineering calculations reuse guarded run lifecycle.
- **Anchors:** `_require_exact_bundled`, `_is_exact_bundled`, `prepare_execution_owner`, `RUNNER_SCRIPT_POLICY_VIOLATION`.

## 047 geometry/hydraulics screening — REAL bounded scientific model
- **What/when:** M0 closed-loop tube geometry/hydraulics: areas/volumes, circulation, transit/turnover, Reynolds, Darcy pressure loss/head and pump power.
- **Canonical:** `runner/examples/bluerev_geometry_hydraulics_v0.py` + contract; exact process-kernel compatibility profile separately exists.
- **Invoke:** bundled registration/runner only.
- **I/O:** nine unit-bearing inputs; schema-v1 scalar outputs. Laminar `64/Re`; Blasius only for `4000 ≤ Re ≤ 100000`; transitional/out-of-qualified range fails.
- **Preconditions:** positive geometry/fluid inputs, OD≥ID, efficiency `(0,1]`.
- **Risk:** deterministic screening; no pump curve/NPSH/transient pressure; minor-loss coefficient provisional.
- **Evidence:** `test_bluerev_geometry_hydraulics_v0.py`, laminar tests, exact 075 identity tests.
- **Limits:** external illuminated area is proxy; no network topology or detailed pump selection.
- **Do not reinvent:** use exact bundled 047 when this M0 boundary fits.
- **Anchors:** `friction_correlation`, `correlation_not_qualified`, `bluerev_geometry_hydraulics_v0`.

## 048 biomass/nutrients/harvest/economics screening — REAL bounded model
- **What/when:** M0 biomass inventory/productivity, nutrient/carbon incorporation, stock dosing, gas-equivalent benchmarks, side-stream harvest sizing, filter area, pump-energy and preliminary variable-cost KPIs.
- **Canonical:** `runner/examples/bluerev_biomass_nutrients_harvest_v0.py` + contract.
- **Invoke:** bundled process1 registration/runner.
- **I/O:** explicit productive volume and biological/harvest/economic inputs; optional product price enables gross-margin proxy; input evidence records parameter/manual/missing-optional state.
- **Preconditions:** strict units/domains; operating days ≤366, hours/day ≤24, fractions ≤1, concentrate concentration > culture concentration.
- **Risk:** deterministic screening; mass-balance invariants fail closed.
- **Evidence:** process1 runner/model/golden tests.
- **Limits:** productivity imposed, upstream volume not auto-selected, incorporation-only nutrients, no gas transfer, pump-electricity-only OPEX, no CAPEX/full TEA; salt factors are rounded workbook screening constants.
- **Do not reinvent:** reuse this bounded model but do not present its economics as TEA.
- **Anchors:** `bluerev_biomass_nutrients_harvest_v0`, `economic_boundary`, `input_evidence`.

## 049 buoyancy/optical screening — REAL bounded model
- **What/when:** Archimedes static displacement screening plus tube/fouling/culture Beer-Lambert-like transmission proxies.
- **Canonical:** `runner/examples/bluerev_buoyancy_optical_screening_v0.py` + contract.
- **Invoke:** bundled process2 registration/runner.
- **I/O:** explicit masses/volumes/densities/safety factor and optical inputs; optional available flotation yields pass/fail margin.
- **Preconditions:** strict units/domains; safety factor ≥1, transmittance `(0,1]`, fouling fraction `<1`.
- **Risk:** deterministic screening with finite/result invariants.
- **Evidence:** process2 runner/model/golden tests.
- **Limits:** no freeboard/stability/CG/CB/waves/mooring/flooding/dynamic immersion; optical path caller-asserted, no PAR spectrum/scattering/radial field/light-growth coupling.
- **Do not reinvent:** use only as explicit M0 screening proxy.
- **Anchors:** `bluerev_buoyancy_optical_screening_v0`, `buoyancy_availability_check`, `beer_lambert_like_transmission_proxy`.

## 050/051 dependency + freshness — REAL provenance machinery
- **What/when:** project canonical rows into a lineage DAG and append deterministic downstream stale marks after accepted Parameter replacement.
- **Canonical:** `backend/app/modules/flowsheet/{service.py,models.py,routes.py,freshness.py}` plus Parameter lifecycle caller.
- **Invoke:** `get_flowsheet_graph`, `get_flowsheet_node`, `prepare_freshness_invalidation`, `persist_freshness_invalidation`.
- **I/O/persistence:** derived graph plus freshness invalidation records; read projection and stale evidence only.
- **Limits:** does not auto-recompute engineering results.

## Process/PBR 047–075 authority summary — MIXED
| Family | Current repository capability | Classification |
|---|---|---|
| 047 | geometry/hydraulics/residence/turnover/pumping M0 | REAL bounded |
| 048 | biomass/nutrients/gas benchmark/harvest/energy + pump-electricity economics | REAL bounded |
| 049 | static buoyancy + optical/transmittance proxies | REAL bounded |
| 050 | dependency/lineage DAG | REAL provenance |
| 051 | deterministic stale propagation after Parameter replacement | REAL provenance |
| 052 | exact 047 → single-tube CAD link | REAL bounded |
| 071/071b | input contract/binding/DOF preview + Properties owner | REAL |
| 072 | symmetric parallel topology M1 + canonical manifest | REAL code, EXPERIMENT/REFERENCE authority |
| 073 | capped branch-manifold GeometrySpec primitive | REAL |
| 074 | topology M1 → multi-part CAD | REAL code, EXPERIMENT authority |
| 075 | typed acyclic process kernel + exact 047 profile | REAL code, HISTORICAL/INCUMBENT |
| standalone 078 PBR | no current qualified integrated PBR implementation | DEFERRED/CANCELLED; historical planning only |

Critical warning: `runner/examples/batch_growth.py` is a deterministic runner demonstration, **not** PBR biology authority. No current runtime provides general recycle convergence, broad thermo/property packages, arbitrary unit operations, qualified integrated PBR biology, or a validated general process-design simulator.

## Gaps / duplication discovered
- External Gmsh/CalculiX execution is intentionally configuration-dependent: adapters/tests are real, checked-in executable entries are not operational defaults.
- Scientific evidence is strong on determinism/contracts/provenance but does not itself validate physical fidelity; 047–049 explicitly expose screening assumptions and omitted physics.
- 072/074 and 075 are useful implemented compatibility/experiment paths but must not be promoted by documentation into general process authority.
- The current evidence ontology is deliberately narrow (`validation_v0`, `mesh_quality_v0`, `fem_static_v0`); broader uncertainty/experimental-validation evidence is not present.

## EXPLICIT FILE COVERAGE LEDGER

Fresh-tree baseline for this incremental ledger: `master@240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`. Rows are added only after literal content inspection; absence from this ledger remains unaccounted until the final tree set-difference is zero.

| path | status | one-line role/reason |
|---|---|---|
| `backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.py` | READ | Exact bundled 072 symmetric-parallel topology calculation; validates cross-field geometry/hydraulics and emits canonical result/topology evidence. |
| `backend/app/modules/runner/examples/bluerev_process_topology_m1_v0.contract.json` | READ | Versioned 072 input contract defining 26 required topology, geometry, fluid, equipment and loss-coefficient variables with units/domains. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_process_kernel_v1.py` | READ | Exact 075/047 compatibility runner wrapper: requires the complete expected unit-bearing input set, rejects non-finite/unit-invalid values, delegates to `execute_047_process_kernel`, maps kernel errors to deterministic runner failure, and writes canonical finite JSON output. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_process_kernel_v1.contract.json` | READ | Schema-v2 forward contract for the process-kernel 047 profile: nine required design/operating/property/model/equipment variables with explicit physical dimensions, units and bounded domains. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.py` | READ | Exact bundled 047 M0 closed-loop geometry/hydraulics model: strict nine-input unit envelope, finite/domain checks, laminar 64/Re or qualified Blasius friction, Darcy pressure/head/power outputs, and explicit omitted-physics diagnostics. |
| `backend/app/modules/runner/examples/bluerev_geometry_hydraulics_v0.contract.json` | READ | Schema-v1 forward contract for 047: nine required design/operating/property/model/equipment variables with explicit units and bounded scalar domains. |
| `backend/app/modules/runner/__init__.py` | READ | Minimal runner package boundary; contains only the module docstring and no runtime/scientific logic. |
| `backend/app/modules/runner/_execution_owner.py` | READ | Cross-platform execution-owner supervisor: acquires the nonblocking owner lock, spawns the lock-owning child, enforces readiness and execution timeout, bounds stdout/stderr, reports deterministic busy/completed states, and deliberately retains ownership until the caller acknowledges durable result/failure persistence. |
| `backend/app/modules/runner/_execution_child.py` | READ | Cross-platform lock-owning execution child: acquires the same nonblocking file lock, signals readiness, waits for an explicit `run` command, executes the reviewed script via `runpy` with fixed argv/path context, and always removes readiness state and releases the lock. |
| `backend/app/modules/runner/process_kernel_047.py` | READ | Exact process-kernel bundle identity/install/validation boundary: hashes contract, semantic registry, component/profile constants and every bundled source; rejects symlinks, extra/missing/stale files or hash drift; recognizes only the exact reviewed calc_v0 profile and enforces schema-v2 normalization plus OD≥ID before execution. |
| `backend/tests/test_process_kernel_075_contracts.py` | READ | Process-kernel contract/invariant battery: pins semantic-unit registry and digest, exact same-basis conversions and fail-closed semantic/dimension mismatches, post-conversion domains, component/stream immutability and composition semantics, explicit flowsheet graph/port/driver/cycle/constant validation, pre-execution caller-scalar validation, and named-block ownership of 047 intermediates. |
| `backend/tests/test_process_kernel_075_block_domains.py` | READ | Block-domain failure battery: Reservoir, Pipe, Fitting and Pump reject negative/non-finite/bool or cross-field-invalid geometry, loss, efficiency and gravity inputs with deterministic error codes; pass-through blocks must return equal but distinct immutable stream records. |
| `backend/tests/test_process_kernel_075_material_preflight.py` | READ | Material-requirement preflight proof: a downstream required stream field missing from an externally supplied MaterialStream fails with `stream_requirement_missing` before any upstream or downstream block `solve` executes. |

UNACCOUNTED_FILES: >0