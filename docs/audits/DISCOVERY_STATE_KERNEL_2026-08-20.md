# DISCOVERY STATE KERNEL — 2026-08-20

PURPOSE=AI_REHYDRATION; FORMAT=TOKEN_DENSE; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; TARGET_BRANCH=audit/hermes-agent-2026-08-20

## 0. OPERATING RULES

R0 SUNK_COST_ZERO: evaluate JarvisOS as if external. Existing internal work receives no preservation bonus.
R1 PIPPO_OS_TEST: for each capability ask: "If building Pippo OS from zero today, would we choose JarvisOS code, external repo code, hybrid, or clean-room?" Apply answer to JarvisOS.
R2 REPLACE_NOT_LAYER: when external implementation clearly wins, migrate behind equivalence tests, then delete superseded Jarvis code. Avoid parallel frameworks unless boundary/isolation is intentional.
R3 CODE_FIRST: README/paper claims are insufficient. Inspect implementation, tests, issue history, dependency chain, license, failure modes.
R4 AUTHORITY_SEPARATION: powerful runtime != authority. External agent/runtime/solver never owns accepted engineering truth, policy, egress, budget, promotion, or canonical state unless explicitly re-authorized.
R5 BACKEND_OVER_REWRITE: do not reimplement mature scientific kernels. Build BLUECAD/Jarvis semantic IR, adapters, policy, verification, provenance, coupling, UX.
R6 MULTIFIDELITY: smallest model that answers the current engineering question; add physics only when evidence/decision sensitivity justifies it.
R7 ASSUMPTIONS_ARE_STATE: every simplifying assumption should be explicit, sourced/confidence-tagged, replaceable, testable, supersedable.
R8 LICENSE_CLASS: DIRECT=permissive reusable; BOUNDARY=LGPL-like/stable adapter; EXTERNAL=GPL/AGPL/copyleft strong/separate process; CLEAN_ROOM=no reusable code/license/IP concern; RESEARCH_ONLY=NC or otherwise noncommercial; GAP=no adequate backend found.
R9 DISCOVERY_SERENDIPITY: search adjacent domains, labs, industrial orgs, author repos, standards, experimental automation; optimize for leverage not keyword similarity.
R10 AUDIT_BRANCH_ONLY: no master/spec/runtime changes from discovery. Branch may lag master; never merge blindly.

## 1. CURRENT STRATEGIC ARCHITECTURE

JARVIS_NATIVE_VALUE = {authority, policy, evidence/provenance, canonical engineering state, cross-domain semantics, orchestration, verification/promotion, UI/workflow}
EXTERNAL_VALUE = {agent runtime, numerical solvers, thermo, CAD/CAE, CFD/FEM, optics, hydrodynamics, fatigue, optimization, parameter estimation, standards/toolchains}

TARGET_SHAPE:
JarvisAuthority -> AgentRuntime(Hermes-derived candidate) -> Tool/BackendAdapters -> ScientificBackends
ScientificOutputs -> JarvisValidation/Evidence -> Proposal -> Promotion -> CanonicalEngineeringState

BLUECAD_MODEL_SHAPE:
SemanticModelIR -> {native M0 solver | PyBaMM/CasADi | Modelica/PyMoCa | FMU/FMPy | domain solvers | external process}
IR owns meaning/provenance; backend owns numerics.

## 2. JARVIS VS HERMES — CURRENT VERDICT

OVERALL_AGENT_RUNTIME=HERMES_WINS; OVERALL_AUTHORITY=JARVIS_WINS; ADOPTION=HYBRID_DEEP_REPLACEMENT

REPLACE_WITH_HERMES_OR_HERMES_DERIVED:
- generic agent loop/runtime
- tool registry/discovery
- toolset composition
- tool availability checks
- dynamic tool schemas
- progressive disclosure / Tool Search
- plugin/MCP discovery patterns
- subagent/delegation runtime patterns
- runtime memory-provider lifecycle/plumbing where not canonical engineering truth

KEEP_JARVIS:
- deterministic RouterPolicy/authority chain
- sensitivity/egress/network permission
- budget/economic execution policy
- confirmation + digest binding / side-effect authority
- provider credentials ownership
- canonical engineering state + proposal/promotion lifecycle
- ContextBundle-style provenance/digest and evidence binding
- engineering memory/state distinct from conversational/runtime memory

PROVIDER_LAYER=COMPARE_COMPONENT_BY_COMPONENT; no blanket preserve/replace.

SECURITY_CONSTRAINT: Hermes runtime must sit INSIDE Jarvis authority, never above/beside it. Known current Hermes approval/security coverage is not uniform enough to delegate authority wholesale. Host/process sandbox remains required; config/YAML deny lists are not a sandbox.

MIGRATION_RULE: equivalence/migration tests first; once Hermes-derived component covers required contract, delete superseded Jarvis component. No nostalgia.

PRIOR_ADR_CAUTION: old ADR-060 treated Hermes largely as swappable passthrough with internals/memory noncanonical. New 2026-08-20 code-first audit materially broadens candidate adoption. Old ADR is historical until formally superseded; do not silently mutate governance from audit branch.

## 3. BLUECAD/BLUEREV PBR — TARGET PROBLEM

SYSTEM: seawater + Nannochloropsis gaditana/Microchloropsis lineage in transparent tube network with straight tubes, U-bends, pumps; outdoor solar; wave-driven pose/orientation; growth affected by radiation, photoinhibition, self-shading, fouling; later CO2/O2/nutrients; fouling changes optics + hydraulics; mechanical structure under wave fatigue.

M0_GOAL: minimal validated biomass/light model, not full digital twin.
M0_PHYSICS: X(t) + Beer-Lambert/self-shading + Haldane-like photoinhibition; constant/fixed seawater chemistry where possible; explicit assumptions.
M0_RATIONALE: independent 2025 Nannochloropsis outdoor-model comparison found simple Haldane + attenuation more robust than more complex Droop/nitrate model in tested datasets/configurations. Treat as evidence, not universal proof.
M1_CANDIDATES: species-specific N. gaditana photophysiology (Han + qE/qI + photoacclimation), nutrient/internal quota, carbonate/gas transfer, spatial/light-history coupling.

## 4. OPTICS/PBR FINDINGS

### 4.1 JeremyPruvost/MCRT-for-tubular-photobioreactor
CLASS=CLEAN_ROOM/reference (no license found)
VALUE=S for exact tubular PBR light-transfer reference/oracle.
PAPER=Hoeniges/Pilon/Dauchet/Pruvost, CEJ Advances 2026.
FEATURES={direct+diffuse solar, curved air/glass/culture interfaces, reflection/refraction, absorption/scattering, tube inclination/orientation, LRPA/MRPA/fluence/light fraction}
LIMITS={straight cylinder only, no whole serpentine/U-bend/pump network, hard-coded optical indices, MATLAB}
BUG_CRITICAL: collimated solver uses INPUTS(9) for theta_s while main stores Nrays at 9 and theta_z at 10; direct-solar orientation can be wrong. Diffuse uses index 10 correctly.
OTHER_RISKS={primary MATLAB function/file-name mismatch; singular cross-product geometry when sun parallel tube axis; disp inside parfor at 1e6 rays; Ea/Es unit ambiguity; hard-coded n_air/n_tube/n_medium}
USE=scientific reference/oracle after bug/unit audit, not production dependency.

### 4.2 General optics
pvlib: BSD-3 DIRECT; use solar position + DNI/DHI/GHI boundary conditions.
Mitsuba3: BSD-3 DIRECT; strong candidate generalized 3D spectral/participating-media optical backend for arbitrary tube geometry/fouling; must validate against Pruvost MCRT + experiments.
miepython: MIT DIRECT; approximate particle optical-property estimator; microalgae != perfect homogeneous spheres -> uncertainty explicit.
Radiance/PyRadiance: permissive; useful lighting reference, less directly matched to participating algal media.
Raysect: candidate; deeper audit pending.

## 5. NANNOCHLOROPSIS BIOLOGY/METABOLISM

### 5.1 N. gaditana photophysiology
Nikolaou et al. 2015 model calibrated/validated on N. gaditana: photoproduction + photoinhibition + qE/qI; dynamic variable-light capable.
Bernardi et al. 2017 extension: photoacclimation-dependent parameters.
STATUS=high-priority scientific baseline; reusable code not yet found/cleared.

### 5.2 MAGNUS / Imperial OMEGA
VALUE=S scientific/reference; INTEGRATION_COST=HIGH.
CRITICAL_FINDING: src/interface/bioreactor.py already contains parameter-estimation case for Nannochloropsis oceanica PBR (del Rio-Chanona 2018 family): biomass, nitrate, internal quota, FAME, I=I0*exp[-(eps0+epsX*X)z], Haldane photoinhibition, light averaging, experimental data, ~15 parameters.
STACK_RISK={MC++, CRONOS, CANON, SUNDIALS/HSL; default configs involving SNOPT/Gurobi/GAMS; IPOPT path exists but not default}
USE=oracle/reference or isolate lightweight parameter-estimation concepts before considering full MBDoE stack.

### 5.3 Total-RD/Mgaditana-GEM
MODEL=iMgadit23; genome-scale metabolic model Microchloropsis gaditana (formerly Nannochloropsis gaditana); 2330 rxns/1977 metabolites/889 genes; SBML etc.
LICENSE=CC BY-NC 4.0 => RESEARCH_ONLY / commercial license required.
USE=later metabolic feasibility/composition layer, not dynamic PBR core.
POSSIBLE_COUPLING=PBR dynamics -> photon/nutrient/CO2 constraints -> GEM -> flux/composition feasibility.

### 5.4 Total-RD/BioModTool
USE=biomass objective-function generation from measured biomass composition; later calibration utility.
LICENSE=LGPL per paper => BOUNDARY.

### 5.5 fmairet/photoacclimation
VALUE=photoacclimation/resource-allocation reference; no license detected => CLEAN_ROOM/reference.

## 6. EXPERIMENT -> PARAMETER IDENTIFICATION -> MODEL PROMOTION

TARGET_LOOP:
uncertain assumption -> information gap -> optimal experiment -> automated experiment -> measurements -> parameter estimation/UQ -> model discrimination -> propose replacement -> validation -> promotion.

SmartBioTech/CzechGlobe FINDING: MIT automation code for real P-I curves via O2, photosynthesis vs respiration, regression/R2, growth-stability/turbidostat logic, optimizer altering light/temp/gas/stirring/OD only after quantitative stability gates. VALUE=A+/S for experiment/calibration workflow.
Phenobottle: OJIP chlorophyll-a fluorometer + growth/photophysiology tracking; software AGPL => EXTERNAL/reference; hardware/CAD separate ShareAlike. Useful validation-bench inspiration.
pyPESTO: BSD-3 candidate parameter estimation/UQ backend; likely lower integration cost than full MAGNUS.
BoFire: BSD-3 candidate DoE/Bayesian optimization backend.
huckgroup/OED: lightweight ODE OED reference; audit pending.
DECISION: do not adopt MAGNUS merely because it contains the exact algae-adjacent example; compare capability/integration ratio.

## 7. SEAWATER FOUNDATION

GSW-Python/TEOS-10: scientific reference for seawater thermodynamics. License permits redistribution without modification; classify BOUNDARY/nonmodified dependency rather than ordinary DIRECT until legal review.
PyCO2SYS: strong carbonate chemistry reference/validation; GPL => EXTERNAL/oracle.
cbsyst: MIT-claimed lightweight carbonate system implementation with tests/SciPy root solving; candidate DIRECT only after license-hygiene check + numerical cross-validation against CO2SYS across BlueRev domain.
M0=freeze/fix seawater properties/pH/carbon availability where justified; do not block first biomass model.
M1+=TEOS-10 + carbonate speciation + gas-liquid CO2/O2 transfer + biological uptake.

## 8. FOULING

LITERATURE_FOUND=N. gaditana-specific marine biofouling studies using CFD Eulerian-Lagrangian/DPM + XDLVO-temporal adhesion; PMMA/PETG/PC/PVC; shear/flow/salinity/EPS effects.
PUBLIC_REUSABLE_CODE=GAP.
BLUECAD_NATIVE_STATE_CANDIDATE=delta_f(s,t) or surface_coverage.
COUPLING:
- optical transmittance T_lambda(delta_f)
- D_eff=D_clean-2*delta_f
- roughness epsilon(delta_f)
- d(delta_f)/dt=r_attach(X,EPS,material,salinity,...)-r_detach(tau_wall,...)
VALUE=high because same state couples optics + hydraulics + maintenance.

## 9. HYDRAULICS

ChEDL fluids: MIT DIRECT; reduced-order tube/bend/pump/friction/control-valve calculations. Preferred initial backend for small PBR loop.
EPANET: MIT; pressure-network/pump/valve solver; useful if network complexity grows, but not a PBR simulator.
WNTR: Revised BSD + EPANET MIT portions; Python network interface/simulation.
CFD: use local high-fidelity U-bend/mixing/shear/particle studies only; do not CFD entire loop by default. OpenFOAM as EXTERNAL GPL candidate.

## 10. MECHANICAL/WAVE/FATIGUE

wavespectra: MIT DIRECT; ocean wave spectra, ERA5/SWAN/WW3/NDBC readers, JONSWAP/TMA/PM/directional spectra. Candidate canonical SeaStateSpectrum input.
OpenFAST: Apache-2 DIRECT candidate modules={SeaState,HydroDyn,SubDyn,BeamDyn,MoorDyn}; strong regression tests. Important limitation: floating platform normally rigid 6DOF in ElastoDyn; do not assume full flexible floating BlueRev framework. Best candidate use=HydroDyn standalone wave-load generator -> canonical loads -> separate structural FEM.
WEC-Sim: Apache-2; second global wave/body oracle; MATLAB/Simulink dependency.
MoorDyn v2: BSD-3 (current; v1 historical GPL); dynamic moorings.
MoorPy: BSD-3; quasi-static moorings.
RAFT/WISDEM: reduced-order floating/offshore references; deeper audit pending.
IHCantabria OASIS: capable new offshore simulator but GPL-3 => EXTERNAL.
Bosch pyLife: Apache-2 DIRECT; fatigue/lifetime, rainflow, S-N, FKM/nonlinear, stress gradients/FEM mapping/hotspots. Strong candidate fatigue assessment backend.
fatpack: useful independent fatigue oracle; license not yet verified -> NOT_DIRECT_YET.
DNV sesam-time-domain-examples: MIT examples but requires proprietary Sesam; industrial workflow reference only.
DNV vista-sdk: MIT industrial vessel sensor semantics; later digital-twin telemetry relevance.

MECH_TARGET_PIPELINE:
wavespectra -> wave kinematics/loads(HydroDyn/WEC-Sim/other) -> global structural model -> local joint submodel -> stress/strain histories -> pyLife/material-specific fatigue.
JOINT_MATERIAL_BLOCKER: fatigue model depends strongly on joint type. welded steel != bolted != polymer != adhesive != composite. Need actual materials/joints before final fatigue backend selection.

CROSS_DOMAIN_BLUECAD_VALUE:
wave -> pose/deformation -> tube orientation theta_tube(s,t) -> optical transport -> cell light history -> photophysiology/growth
AND
wave -> structural loads -> local stress -> fatigue
AND
fouling -> optics + hydraulics + maintenance.
No audited repo provides this end-to-end; coupling/provenance/verification is native BLUECAD differentiation.

## 11. MODEL IR / EXECUTION DISCOVERY

### 11.1 Current Jarvis ModelSpec
Jarvis modeling schemas already capture engineering_question/scope/status/maturity/assumptions/parameters/uncertainty/source/requirements/runs/decisions. KEEP as governance/provenance concept; do not assume it should become numerical engine.

### 11.2 GreenLight (Wageningen)
LICENSE=BSD-3-Clause-Clear DIRECT.
GOOD_IDEAS={declarative ODE model; per-variable definition/unit/description/reference; dependency mapping; explicit processing order; model layering/override; unit tests}
VERY_RELEVANT_PATTERN=newer definition can replace older law while rest of model remains unchanged; logs override.
DO_NOT_COPY_RUNTIME_BLINDLY: default execution builds Python function strings and exec(); defaults can replace NaNs with zero and clip huge numbers. Bad safety/numerical transparency defaults for BLUECAD.
USE=IR/layering/provenance architecture reference; possibly parser subset after threat model.

### 11.3 PyBaMM
LICENSE=BSD-3 DIRECT; project classifies Production/Stable.
KEY_FINDING=BaseModel is genuinely generic enough to express arbitrary ODE/PDE/DAE: rhs, algebraic, IC, BC, variables, geometry, discretization, events; example builds non-battery PDE from zero.
STRONG_IDEAS={symbolic expression tree; CasADi/Python/JAX conversions; solver/discretization pipeline; parameter info; serialization; citations registered by functionality; modular submodel build}
LIMIT=BaseSubModel ontology still hard-codes battery domains negative/separator/positive; do not make BLUECAD ontology inherit battery assumptions.
USE=backend + architecture source; candidate generic numerical engine for some models.
PRIVACY=telemetry exists but is opt-in/disableable; if embedded, disable by policy/default in Jarvis environment.

### 11.4 Modelica/OpenModelica/PyMoCa
QUESTION=are we reinventing acausal multi-domain modeling?
OpenModelica compiler: OSMC-PL/AGPL choices; proprietary source integration has licensing constraints => EXTERNAL/BOUNDARY, not DIRECT.
Modelica Standard Library: BSD-3; mature libraries {Fluid, Media, Thermal, Mechanics, Electrical, Blocks, Units...}; DIRECT library assets subject to compatibility/audit.
PyMoCa: BSD-3, alpha; Modelica->AST->instantiate->flatten->CAS; optional CasADi/SymPy; active work against Modelica 3.5 compliance/MSL. Core still incomplete/TODOs. Candidate compiler/interoperability layer, not immediate foundation.
USE=spike before inventing custom acausal language.

### 11.5 FMI / FMPy
FMPy: Dassault Systemes, BSD-2; supports FMI1/2/3, model description, simulation, input events, remoting, container FMUs, cross-check/tests.
STRATEGIC_VALUE=standard adapter boundary: backend can ship versioned FMU with inputs/outputs/parameters/events rather than deep Python coupling.
SECURITY=FMU contains native code; standardization != trust. Execute under Jarvis sandbox/capability policy.
TARGET_ADAPTER_MODES={native_library, FMU, external_process, remote_service}; FMI where available.

## 12. EXTERNAL REPO DECISION TEMPLATE

For every candidate record:
ID; domain; repo/org; exact commit/tag/date; license; class(DIRECT/BOUNDARY/EXTERNAL/CLEAN_ROOM/RESEARCH_ONLY/GAP); code maturity; tests; dependency risk; scientific validation; failure modes; Jarvis overlap; PIPPO_OS verdict(KEEP_JARVIS/REPLACE/HYBRID/ORACLE); integration boundary; required equivalence tests; deletion target if replacement; priority(S/A+/A/B); next action.

## 13. PRIORITY QUEUE — DISCOVERY

S1 PBR exact problem:
- N. gaditana spectral absorption/scattering coefficients vs biomass/state/wavelength; temperature/salinity dependence
- code/data from Pruvost/GEPEA/Nantes; INRAE/Ifremer; Padova CAPE/PAR; Imperial Chachuat/OMEGA; Almeria Molina-Grima/Sanchez-Miron
- cell trajectories/light-dark cycles in tubular PBRs; CFD/Lagrangian particle histories
- fouling attachment/detachment + optical penalty + seawater materials
- CO2/O2 mass transfer/carbonate coupling in seawater PBRs
- experimental datasets suitable for M0 validation

S2 agent architecture:
- Hermes component-by-component migration matrix vs Jarvis implementation/tests
- approvals/security gaps; sandbox boundary; tool registry; Tool Search; memory; subagents; MCP; provider abstractions
- produce replacement slices, not parallel runtime

S3 model execution/interchange:
- PyBaMM generic-model feasibility beyond batteries
- PyMoCa/Modelica subset needed by BLUECAD
- FMI/FMU export/import paths for likely backends
- alternative declarative equation IRs; unit systems; events; algebraic loops; provenance

S4 mechanical:
- hydrodynamics beyond OpenFAST/WEC-Sim: HAMS/pyHAMS, Capytaine licensing split, Nemoh, Kratos/FEniCSx/OpenSees/CalculiX boundaries
- flexible floating frame/global-local FEM
- joint-specific fatigue for actual BlueRev materials

DEFER_UNTIL_S1-S4_ADVANCE: process safety; materials/corrosion; industrial protocols; reaction/catalysis; electrochemistry; meshing; P&ID auto-layout; heat integration; costing; UQ broadening.

## 14. IMPLEMENTATION PRIORITY SIGNAL

HERMES_AGENT_RUNTIME is one of first external integration candidates because upgrading agent/tool infrastructure lowers cost of subsequent scientific integrations.
BUT discovery docs do not authorize implementation. Before implementation: reconcile audit branch with current master; formal spec/ADR supersession; exact migration/equivalence tests; maintainer authorization.

PBR M0 should remain small while data/validation discovery continues. Avoid waiting for full optics/fouling/carbonate/mechanics to answer first growth questions.

## 15. AUDIT FILE MAP

DETAILS:
- docs/audits/HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md
- docs/audits/BLUEREV_PBR_DISCOVERY_2026-08-20.md
- docs/audits/MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md
- docs/audits/MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md
- docs/audits/SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md
- docs/IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md

THIS_FILE=canonical compact rehydration kernel for discoveries through 2026-08-20T~11:00 Europe/Rome. Detailed audit wins over this kernel on exact code evidence; newer dated audit wins over older findings. Historical ADR/spec remains governance authority until formally superseded.