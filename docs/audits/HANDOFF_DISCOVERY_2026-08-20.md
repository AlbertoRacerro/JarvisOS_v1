HANDOFF_DISCOVERY_2026-08-20
REPO=AlbertoRacerro/JarvisOS_v1
BRANCH=audit/hermes-agent-2026-08-20
AUTHORITY=AUDIT_ONLY
IMPLEMENTATION_AUTHORIZED=NO
PRIMARY_ENTRYPOINT=docs/audits/DISCOVERY_STATE_KERNEL_2026-08-20_V8.md
READ_POLICY=V8_FIRST;OPEN_DETAIL_ONLY_IF_NEEDED;NEWER_DETAILED_AUDIT_WINS;DO_NOT_TOUCH_MASTER/STATUS/ACTIVE_SPEC.

MISSION
Continue broad code-first discovery for JarvisOS/BLUECAD/BlueRev. Goal is NOT immediate integration of every repo. Goal=map ecosystem, find hidden high-leverage code/algorithms/data, classify licensing/maturity/real code quality, preserve future implementation paths, and identify minimal M0/M1 infrastructure. Search creatively across adjacent fields, labs, universities, companies, supplementary code, low-star repos. README claims are insufficient; inspect code/tests/license/dependency chain. Sunk-cost zero: Jarvis code gets no preference because we wrote it.

OPERATING_RULES
SUNK_COST_ZERO;PIPPO_OS_TEST;REPLACE_NOT_LAYER;CODE_FIRST;BACKEND_OVER_REWRITE;MULTIFIDELITY;ASSUMPTIONS_ARE_STATE;SERENDIPITY;AUTHORITY_SEPARATION.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonmodified;EXTERNAL GPL/AGPL/separate process;CLEAN_ROOM equations/ideas/no reusable code;RESEARCH_ONLY NC/noncommercial/commercial permission;GAP none}.
For each candidate assess: PURPOSE;ACTUAL_CODE;PLACEHOLDERS;TESTS/CI;LICENSE;DEPENDENCIES;MAINTENANCE;VALIDATION;PIPPO_VERDICT={ADOPT/REPLACE/HYBRID/ORACLE/REFERENCE/REJECT};FIDELITY_STAGE={M0/M1/M2/M3/FUTURE};INTEGRATION_COST;FAILURE_MODES.
Persist material findings on audit branch. Update compact kernel only when decisions/priorities change. Documents optimized for AI/token density, not prose aesthetics.

AI/JARVIS DECISION
Hermes runtime wins over existing Jarvis agent runtime. Future target=deep replacement, not layering. Hermes-derived={agent loop,tool registry/discovery,toolsets,availability,dynamic schemas,ToolSearch,plugin/MCP,subagents/delegation,noncanonical runtime memory}. Jarvis keep={RouterPolicy deterministic authority,sensitivity/network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}. External model/agent never owns accepted truth. After equivalence/migration tests delete superseded Jarvis modules. Hermes is high-priority future implementation item, but current task remains discovery/audit unless explicitly authorized.

BLUECAD NUMERICAL DECISION
Do not invent monolithic simulator. BLUECAD owns SemanticModelIR/provenance/assumptions/validation; numerical backends swappable: nativeM0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist|external. FMI/FMPy BSD2 is high-leverage adapter path. GreenLight useful declarative/override ideas but unsafe exec-oriented runtime. PyBaMM generic numerical architecture useful; do not inherit battery ontology wholesale.

BLUEREV PBR FIDELITY
M0={homogeneous biomass X(t),effective attenuation/self-shading,light saturation+photoinhibition,decay; simple hydraulic pump/tube model; strong explicit assumptions};M1={lumped DIC/pH,DO,CO2/O2 transfer,T/actuators};M2={distributed1D tube+mixed degasser};M3={3D optics/local CFD/Lagrangian cell light histories,wave-dependent tube pose,fouling}. Do not implement M2/M3 now unless needed; preserve upgrade plan.
Key PBR refs/findings: In@lgae/MGM architecture near target; UAL distributed/lumped outdoor models and CFD->particle->light-history; Pruvost tubular MCRT no license/clean-room and direct-solar theta index bug; pvlib BSD3/Mitsuba BSD3/miepython MIT candidates; N.gaditana Palermo 2022 M0 parameters/dataset, Pfaffinger high-light, Nikolaou/Bernardi dynamic photoinhibition/photoacclimation; TotalEnergies iMgadit23 CC-BY-NC research-only; seawater TEOS/CO2SYS references; Reali/INRIA saline activity-ion pairing reference; fouling dynamic code remains GAP; ChEDL fluids hydraulics DIRECT. Effective attenuation fitted parameter must not be treated as intrinsic optical property. Light-history matters at higher fidelity; M0 can intentionally average light.
Control/experiments: PC-Gym MIT ADOPT_CANDIDATE generic ControlBenchmark/PolicyEvaluation; UAL 2026 benchmark is S oracle but core MATLAB p-code/no explicit software license; Pyomo.DoE revised-BSD basis; SmartBioTech PBR-ControlScripts MIT strong experiment automation/calibration reference; Phenobottle AGPL external reference.

MECHANICS CURRENT DECISION
Target architecture is multifidelity/global-local, not one solver.
SeaState=wavespectra MIT.
Hydro BEM=pyHAMS Apache2 DIRECT candidate but scientific regression debt (truth comparisons commented in cylinder tests); Nemoh v2 Apache2 candidate; Capytaine full GPL EXTERNAL, libDelhommeau Apache subcomponent candidate.
Global dynamics front-runner=Project Chrono BSD3 S DIRECT: flexible multibody+ANCF FEA+contact+Python; actual repository demo couples free-surface SPH wave tank directly to flexible ANCF cable/plate. Use likely for global nonlinear dynamics and selected high-fidelity FSI, not routine whole-life SPH.
HydroChrono=MIT S architecture: BEMIO->Cummins time-domain, RIRF convolution/processing, radiation state-space fitter/model, Chrono, MoorDyn, YAML/HDF5, regression/verification cases; BUT repo archived 2026-05-19 while NLR 2026 material still calls it SEA-Stack backbone. P0 find successor/archive rationale; if none, selective MIT fork/extraction before rewriting Cummins/radiation.
Fast tube mechanics=PyElastica MIT candidate Cosserat-rod TubeRodModel; emits centerline/directors/curvature/pose useful to optics; no native marine hydro found. Compare against Chrono ANCF.
Exudyn permissive candidate but geometricallyExactBeam3D test says UNDER DEVELOPMENT and assertions commented; behind Chrono currently.
Detailed/local FEM=Kratos StructuralMechanics permissive DIRECT; corotational beam/truss/cable/shell/solid/contact/dynamics/eigen/harmonic/sensitivity/tests. CoSimulation/CoSimIO permissive detached C++11 C/Python MPI bus; try before custom solver coupling.
MFEM BSD3+Tribol MIT specialist HPC/contact; lower priority than Kratos/Chrono.
OpenSees NOT DIRECT: noncommercial/internal use; commercial distribution requires UC Berkeley permission. CalculiX GPL2 EXTERNAL.
Fatigue=pyLife Apache2 generic default. py_fatigue GPL oracle. Corrosion-fatigue/adhesive-fatigue/polymer structural fatigue remain GAPs for mature permissive production backend.
OpenBoltRF GPL3 EXTERNAL reference establishes bolted JointSubmodel pattern: preload/assembly phase -> lock/contact/friction -> service load -> local stresses -> fatigue. bjsfm MIT candidate for composite bolted-hole stress screening if composite joints used.
Mechanics->PBR cross-domain output must include tube_pose(s,t),director(s,t),curvature(s,t) for optical incidence/light model.

PIPPO_MECHANICAL
DO_NOT_BUILD={generic multibody dynamics,generic beam/cable FEA,generic 3D FEM,generic contact engine,generic rainflow/SN,Cummins/RIRF/state-space from zero}.
BLUECAD_OWN={MarineMechanicsIR,fidelity selection,assumption/provenance,hydro/structure adapters,global-local mapping,load-history evidence,joint assembly/preload state,material/environment validity domains,solver cross-validation,mechanics-optics coupling}.

NEXT_QUEUE
P0 continue mechanical discovery: locate HydroChrono/SEA-Stack successor/archive reason; inspect Chrono FSI scientific validation and practical distributed wave-loading on flexible tube network; design PyElastica-vs-Chrono canonical TubeRod comparison; search welded/corrosion fatigue permissive code/data; adhesive/polymer/composite fatigue hidden repos/data; define JointSubmodel/global-local mapping.
P1 verify Nemoh/libDelhommeau as independent permissive BEM/backend oracle; define cross-solver validation matrix.
P1 continue targeted PBR source recovery only when high leverage: MGM/In@lgae/Reali saline/JAX-ALBA/N.gaditana spectral coefficients; broad PBR discovery already near diminishing returns.
P1 continue creative serendipity outside obvious domains when likely to uncover reusable architecture/code.
Do NOT begin mass integration. MVP implementation later should be narrow; future Jarvis/Hermes AI expected to progressively remove strong assumptions and integrate higher-fidelity backends.

REHYDRATION_STEPS_FOR_NEXT_CHAT
1 read `docs/audits/DISCOVERY_STATE_KERNEL_2026-08-20_V8.md` from branch `audit/hermes-agent-2026-08-20`.
2 if mechanics task, read `MECHANICAL_WAVE_FEM_DISCOVERY_DELTA1_2026-08-20.md` + `DELTA2`.
3 if PBR task, open BLUEREV_PBR_DISCOVERY* + SEAWATER/NANNOCHLOROPSIS audit only as needed.
4 if AI task, open HERMES_AGENT_CODE_FIRST_AUDIT and AI_* deltas; retain sunk-cost-zero rule.
5 inspect repo current master/active spec before any implementation; audit branch does not authorize writes to canonical implementation state.
6 continue code-first discovery and persist deltas/kernel updates.

LATEST_CANONICAL_DISCOVERY_KERNEL=V8;V8_SUPERSEDES_V7_FOR_REHYDRATION.