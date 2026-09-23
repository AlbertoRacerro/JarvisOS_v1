# 103 PROCESS-UPSTREAM-BAKEOFF-1 — targeted qualification evidence

Scope: REF-038, REF-039, REF-040, REF-042, REF-047 from `docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md`. This is an offline Linux feasibility probe of the installed q103 environment, not a validated BlueRev process model. The synthetic point is 298.15 K and 101325 Pa; the dynamic biomass variable and coefficients are arbitrary fixture values. No product dependency or solver adapter is added by 103.

## Reproduction and evidence

Run `MPLCONFIGDIR=/tmp/q103-mpl /home/thera/jarvis-control/work/venvs/q103/bin/python scripts/qualification/103/probe.py` from the repository root. The script writes one JSON per candidate to `scripts/qualification/103/results/`, with installed distribution version, distribution metadata license, elapsed wall time, measurements or the exact exception text. `error_source` distinguishes package exceptions from deliberate probe prerequisite checks; the `native_error` field preserves the precise raised exception in either case and does not imply a solver ran. The immutable environment freeze supplied for this run is `/home/thera/jarvis-control/work/out/q103-freeze.txt`. `backend/tests/test_process_upstream_103_results.py` checks artifact completeness without importing optional packages.

The measured overlap is narrow:

| Probe | Result | Interpretation |
| --- | --- | --- |
| CoolProp water | density 997.047636760347 kg/m3, viscosity 0.000890022489 Pa s, saturation pressure 3169.929 Pa | A usable single-fluid property path at this point; no saline-mixture qualification. |
| chemicals/thermo | IAPWS density 997.047636760344 kg/m3; thermo 3.5 mass-% NaCl brine density 1021.637 kg/m3 and liquid phase; thermo CO2 gas density 1.79885 kg/m3 | The brine number has no experimental comparator here. Thermo and CoolProp use distinct methods; agreement for pure water does not qualify salinity or phase boundaries. |
| fluids vs 047 `Pipe` | Re 56011.23596; upstream Darcy f 0.020371864, loss 2031.074843 Pa; incumbent Blasius f 0.020566846, loss 2050.514497 Pa | Pressure-loss difference is -0.9480%; neither correlation is proven preferable for BlueRev roughness/regime. Exact 047 identity would break if silently switched. |
| ht | Dittus-Boelter Nu 300.12569, h 3601.508 W/m2/K under assumed k=0.6 W/m/K and Pr=6.2 | 047 has no heat-transfer output. Range, wall heating/cooling assumptions and PBR calibration remain open. |
| scikit-sundae/CasADi | 48-hour day/night synthetic ODE final states 1.022560700726 and 1.022560698774; simple algebraic-inventory DAE endpoints 1.022560552328 (IDA) and 1.022980367620 (IDAS) | ODE relative agreement about 1.9e-9. DAE algebraic residuals are at most 9.1e-12 and 4.5e-16, but endpoints differ about 0.041% because the IDAS probe holds midpoint light for each 15-minute step. This proves solver feasibility for a toy, not plant conservation or biology. SUNDIALS CVODE/IDA and CasADi/RK4/IDAS run separately; each has one time/state owner. |
| OpenMDAO | SciPy driver selected flow 0.100000000001 at the lower bound; toy objective 1.25 | A tiny study loop runs. Feasibility, uncertainty, Pareto and real process objectives were not probed. |

The BioSTEAM recycle/mixer/splitter separator probe was attempted but package import fails: `Numba needs NumPy 2.0 or less. Got NumPy 2.4.` ThermoSTEAM and QSDsan share that blocker. Pyomo reports `ipopt`, `appsi_ipopt`, `glpk`, `cbc`, and `highs` unavailable. IDAES imports with a writable `IDAES_DATA` but IPOPT is absent; `idaes get-extensions` needs network and was not run. WaterTAP also lacks the IPOPT binary. do-mpc created a discrete state and three-step MPC setup, but no optimization/control step ran. FMPy has no packaged reference FMU and this host has neither `cmake` nor `omc`; no FMU round trip occurred. NeqSim cannot start its JVM because Java is absent. See each JSON for exact version, metadata license, timings and errors.

## Role decision matrix for 104 and later slices

These are bounded design choices, not declarations of scientific qualification or authorization to ship new runtime dependencies.

| Role | Selected direction | Fallback / hold | Rejected or deferred and reason |
| --- | --- | --- | --- |
| Pure-water/CO2 properties | WRAP CoolProp behind a property evaluator for supported substances and states | WRAP ChEDL `thermo`/`chemicals` for mixture/flash candidates after property-basis and reference checks | No single universal package. Brine values have no measured reference; no replacement of 071b/047 inputs yet. |
| Pipe loss and heat transfer | WRAP `fluids`/`ht` as optional correlation evaluators with explicit correlation name, roughness, geometry, regime and validity | KEEP 047 Blasius screening fixture | REPLACE of 047 correlation rejected on current evidence: measured 0.948% difference and no experimental truth. |
| Steady recycle and separations | Evaluate BioSTEAM first after an isolated compatible NumPy/Numba environment is available | KEEP 075 acyclic profile solely as 047 fixture; use Pyomo/IDAES for equation-oriented problems once a solver is installed | No recycle-capable upstream winner proven; do not claim BioSTEAM or IDAES run. |
| Water/wastewater specialist | QSDsan/WaterTAP only for their native validated domains after import/solver repair | Direct lower-level property/flowsheet adapters | Their names and imports do not validate Nannochloropsis/PBR biology. |
| Dynamic integration | WRAP SUNDIALS CVODE for ODE time integration; evaluate IDA for DAE/holdup later | CasADi symbolic dynamics and derivatives, with exactly one integrating controller | No DAE, event, restart or stiff plant case proven. |
| MPC/estimation | do-mpc model/setup candidate behind a controller boundary | CasADi-based bespoke control only if measured need | No closed-loop MPC or estimator solve without IPOPT. |
| FMU/co-simulation | FMPy as future FMU runner if a real offline FMU is supplied | Native evaluator coupling with one time/state owner | OpenModelica/OMSimulator not evaluated on this platform; `omc` absent, no installable .NET/sudo environment. No FMU round trip. |
| Studies | WRAP OpenMDAO driver around evaluator calls, with 102 validity/uncertainty records | Direct bounded study loop for simple sweeps | The tiny optimizer is not evidence for process feasibility or multi-objective quality. |
| Java specialist | NeqSim only after Java availability and chemistry/domain comparison | CoolProp/ChEDL candidates above | Current JVM failure and no PBR-specific comparator. |
| DWSIM/DTL/CAPE-OPEN | None chosen here | Reconsider on supported Windows host | Not evaluated here: DWSIM/.NET and COM/CAPE-OPEN runtime are unavailable; no inferred result. |

## Adapter and authority boundary

Any 104+ adapter implements frozen `backend/app/modules/engineering/evaluator_contracts.py` `EngineeringEvaluator`: `descriptor`, truthful `availability`, and typed `evaluate`. It consumes frozen 145 project/subject/quantity refs and 102 `FidelityTier`/`ScientificQualificationRecord`; backend-native case bundles live in `backend_case_ref`, with bounded `backend_options`. The result records native failure code and shared category, numerical diagnostics, artifacts, validity and evidence references. `available` means runnable here; `converged` means solver health; neither means qualified or validated. This 103 probe does not itself emit product `EvaluationResult` or create a 102 qualification record.

047 is **screening** fidelity. The static property/pipe/recycle probes do not establish `steady_state_detailed` until balances, physical assumptions and a reference dataset are checked. The day/night fixture does not establish `dynamic_detailed` scientific qualification. The controller/study layer may request evaluations but must not silently promote fidelity or validity. Product AI, if later used for interpretation, still runs only through `run_ai_task` with an `ai_jobs` row; solvers never receive policy, provider, promotion or canonical-store authority.

For each dynamic simulation one orchestrator owns advancing time and accepting state. CVODE, IDA, an FMU master, or a selected process simulator can take that role for a run. CasADi may supply expressions/Jacobians and do-mpc may propose controls at synchronization points, but they cannot concurrently advance the authoritative state. A co-simulation must name its master, event/step contract, restart snapshot, and balance reconciliation before being treated as a plant run.

## Incumbent disposition for 104

No incumbent code is deleted in 103. `REPLACE` and `DELETE` below are only evidence-backed candidates for 104 after exact 047 identity and supported-consumer checks; current probes prove no generic solver replacement equal or better across the accepted domain.

| Path | Decision | Evidence and boundary |
| --- | --- | --- |
| `backend/app/modules/process_kernel/blocks.py` | KEEP 047 calculations as fixtures; WRAP selected correlations later | `fluids.json` measures a 0.948% pressure-loss difference; `ht.json` adds a correlation with no incumbent overlap. Reservoir/pipe/fitting/pump BlueRev equations and assumptions remain screening evidence, not validated equipment models. |
| `backend/app/modules/process_kernel/profile_047.py` | KEEP exact historical profile | `execute_047_process_kernel` and `assemble_047_result` define the 047 nine-input result/diagnostic identity. No upstream package reproduced the full contract. |
| `backend/app/modules/process_kernel/flowsheet.py` | KEEP for registered 047 profile; candidate to REPLACE generic acyclic execution only after recycle proof | The BioSTEAM recycle probe failed at import and IDAES has no solver. No safe DELETE claim. |
| `backend/app/modules/process_kernel/streams.py` | KEEP 047 stream fixture; WRAP property-basis mapping later | CoolProp/thermo property results show a possible upstream state owner but do not prove composition/flow/unknown-state semantics or exact 047 compatibility. |
| `backend/app/modules/process_kernel/components.py` | KEEP component/screening constants | Brine and CO2 property smokes do not prove BlueRev biomass/catalog equivalence. |
| `backend/app/modules/process_kernel/contracts.py`, `errors.py` | KEEP while 047 bundle uses them | No upstream block-port/error taxonomy equivalence established. 106 owns future evaluator errors. |
| `backend/app/modules/process_kernel/units.py` | KEEP semantic-unit boundary | No upstream probe tested Jarvis basis, provenance and exact 047 units; generic dimensional checking alone is insufficient. |
| `backend/app/modules/process_kernel/canonical.py`, `__init__.py` | KEEP bundle identity helpers | The 047 source manifest and digests depend on current file bytes. |
| `backend/app/modules/runner/process_kernel_047.py` and `process_kernel_registration.py` | KEEP registered bundle gate | Existing exact bundle hashing and runner safety have no tested replacement; changes could invalidate supported model versions. |
| `backend/app/modules/flowsheet/models.py`, `service.py`, `freshness.py`, `routes.py` | KEEP canonical repository graph/freshness owner | These files model Jarvis records and stale propagation, not numerical recycle solving; upstream packages do not replace this authority. |

## Platform, license and missing evidence

This run is Linux in an isolated Python 3.11 venv; Windows 11 and WSL2 import/solver/ABI smoke remains required before product selection. The optional candidates must stay out of `backend/requirements.txt` until a later accepted runtime slice. A future isolated environment needs compatible NumPy/Numba for BioSTEAM/ThermoSTEAM/QSDsan, solver binaries for IDAES/WaterTAP/do-mpc, Java 17+ for NeqSim, and a real FMU/toolchain for FMPy. Installation is via a separate pinned optional environment (`python -m venv ...` and `pip install` exact candidate versions from the supplied freeze, after dependency resolution); no installation or network access was used here.

License strings in the JSON are distribution metadata, not a legal determination. The measured stack includes MIT, BSD variants, Apache-2.0, UIUC (QSDsan), and LGPLv3+ (CasADi/do-mpc). FMPy and `watertap-solvers` metadata do not declare a license in the fields probed; inspect upstream license files before packaging. DWSIM/CAPE-OPEN have GPL/proprietary or platform integration boundaries that require separate legal and Windows review; no assumption of redistribution rights is made.

**Evidence not produced:** BioSTEAM recycle mass-balance run; Bioindustrial-Park exemplar; any IDAES/WaterTAP solved flowsheet or optimization; real do-mpc closed loop/estimator; FMU export/import round trip; open62541 telemetry coupling; PETSc parallel numerics; NeqSim property comparison; DWSIM/OpenModelica/OMSimulator execution; Windows/WSL smoke; saline property measurements; pump curves/NPSH; heat-transfer experiments; PBR kinetic calibration, organism/strain conditions, uncertainty, validity domain or benchmark; plant DAE/restart/conservation under changing holdup; 102 scientific qualification records. No result in this document is called validated.
