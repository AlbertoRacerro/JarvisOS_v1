# DISCOVERY STATE KERNEL V7 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;SUPERSEDES_FOR_REHYDRATION=V6;BRANCH=audit/hermes-agent-2026-08-20

## RULES
SUNK_COST_ZERO;PIPPO_OS_TEST;REPLACE_NOT_LAYER;CODE_FIRST;AUTHORITY_SEPARATION;BACKEND_OVER_REWRITE;MULTIFIDELITY;ASSUMPTIONS_ARE_STATE;SERENDIPITY;AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea/no-code;RESEARCH_ONLY NC/noncommercial;GAP none}.

## AI AGENT
AGENT_RUNTIME=HERMES_WINS;AUTHORITY=JARVIS_WINS;TARGET=HYBRID_DEEP_REPLACEMENT.
HERMES_DERIVED={loop,tool registry/discovery,toolsets,availability,dynamic schemas,ToolSearch,plugin/MCP,subagents/delegation,noncanonical runtime memory}.
JARVIS_KEEP={RouterPolicy,authority,sensitivity,network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}. Hermes inside sandbox/authority; equivalence tests then delete superseded Jarvis. ADR060 remains governance until formal supersession.

## BLUECAD NUMERICAL
SemanticModelIR->{nativeM0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist|external};adapter={native_library,FMU,external_process,remote_service}. GreenLight declarative ideas only;PyBaMM BSD3 generic backend;MSL BSD3;OpenModelica boundary;PyMoCa BSD3 alpha;FMPy BSD2 FMI strong boundary/native-code sandbox.

## BLUEREV FIDELITY
M0={X,effective attenuation,light saturation/photoinhibition,decay};M1={lumped X,DIC/pH,DO,gasCO2/O2,T,transfer/actuators};M2={distributed1D tube+mixed degasser};M3={3D optics/local CFD/Lagrangian histories/wave pose/fouling}. Promote on validation/decision need only.

## PHYSICAL PBR CORE
In@lgae historical INRIA source/license GAP; architecture near target weather/GIS->thermal/hydro/Freshkiss->Lagrangian->Han->products/resources. MGM/Fierro=dynamic photosynthesis+metabolism/storage->reduced twin/control; source/deliverable pending. UAL distributed/lumped outdoor models S reference. UAL2014 table has likely source typos; no blind import.
Optics:Pruvost MCRT oracle/direct-theta bug;pvlib/Mitsuba/miepython candidates; optical intrinsic/effective separation mandatory.
N.gaditana:Palermo2022 M0 data+params;Pfaffinger high-light;Nikolaou/Bernardi dynamic physiology. UAL tubular CFD/Gamma says trajectories can matter; Fierro laminar raceway says often marginal -> trajectory resolution regime-dependent.
Dynamic PSU=Camacho/Brindley/Saccardo; Saccardo HTS->PBR scale-up data/equations no source code. DTU fluxomic 10ODE oracle.
Seawater=TEOS/CO2SYS boundaries;Reali/INRIA saline activity+ion-pairing S reference source pending. ALBA balance/speciation/gas transfer useful architecture; ABACO2 clean-room.
Fouling code GAP;delta_f native cross-domain state. Hydraulics ChEDL initial.

## PBR PROCESS BENCHMARK
`guzmanjl/benchmarkmicroalgae` public 2026 UAL raceway control benchmark; S ORACLE NOT DIRECT: no software LICENSE found though README claims one; core `simulate_benchmark_model.p` opaque MATLAB p-code. Input weather={global solar,PAR,T,RH,wind}; outputs include pH/DO/T/X/depth,DIC species,gases,growth-limit factors,HX/resources/KPIs. Controller signature supplies time,obs,refs,environment,FORECAST,state; proposed actuator signals. Candidate general ControlStep pattern, but Jarvis authority inserted before side effect.

## CONTROL/AI
PC-Gym=`MaximilianB2/pc-gym`; MIT DIRECT; engineered alpha with CI/nightly/tests/coverage/oracle/policy evaluation. PIPPO=ADOPT_CANDIDATE generic ControlBenchmark/PolicyEvaluation. Target PlantEnvAdapter(SemanticModel)->PCGym-like env; evaluate PID/MPC/RL/ESC under same scenarios; Jarvis owns deployment authority.
CIRL MIT but research prototype; concept/small pieces only, NOT wholesale. Industrial PBR RL2026 no code; retain safety pattern demonstrations->offline train->simulation/shadow->authority-limited deploy->offline update->revalidate.
UAL MoD MPC/ESC/EMPC references no reusable source found. FIWARE UAL paper reference only.

## EXPERIMENT/IDENTIFICATION
Pyomo.DoE DIRECT revised BSD; generic FIM foundation. ESR5 robust rival-model design no repo; plugin candidate only. pyPESTO+BoFire complementary;SmartBioTech MIT automation. ALBA↔ABACO cross-dataset benchmark supports rival-model validity domains, not single canonical model.

## MECHANICS — UPDATED V7
wavespectra MIT DIRECT canonical sea-state spectrum candidate.
OpenFAST Apache2; HydroDyn useful wave-load/global hydro reference; floating ElastoDyn normally rigid 6DOF => do not assume fully flexible floating BlueRev.
WEC-Sim Apache2 second global oracle; MoorDynv2/MoorPy BSD3; OASIS GPL EXTERNAL.

### hydrodynamic BEM
pyHAMS=`NLRWindSystems/pyHAMS`; Apache2 DIRECT; Beta; Python/Fortran; Win/Linux/macOS; CI/wheels; simple deps. Strong integration candidate for potential-flow hydrodynamic coefficients. CRITICAL validation debt: cylinder regression truth files exist but added-mass/damping/excitation numerical asserts are commented; current test mostly execution/read/frequency. BlueCAD must add analytic+cross-solver regressions before trust.
Capytaine full=GPLv3 EXTERNAL. Internal libDelhommeau Apache2 candidate if isolated/license-chain verified. Nemoh v2 lineage Apache2 candidate; deeper audit pending.

### structural FEM
Kratos core + StructuralMechanicsApplication=permissive BSD-like with advertising acknowledgement; DIRECT candidate. Capabilities={corotational beam,truss,cable,shell,solid,contact,dynamics,eigen,harmonic,adjoint/sensitivity,large tests}. PIPPO=strong candidate; do NOT build native FEM before spike.

### co-simulation
Kratos CoSimulationApplication + CoSimIO=permissive BSD-like. CoSimIO detached, independent of Kratos, C++11, C/Python, sequential+MPI, zero-copy-oriented data exchange. PIPPO=TRY_BEFORE_CUSTOM_COUPLING_BUS. Candidate chain=wavespectra->pyHAMS/HydroDyn->CoSimIO->Kratos->stress histories->pyLife.
Caveat=frequency-domain BEM coefficients != distributed time-dependent member loads; need load reconstruction/radiation-state-space/Morison path depending fidelity.

### fatigue
pyLife Apache2 DIRECT remains strongest generic fatigue/lifetime backend. Material/joint remains blocker: welded steel != bolted != polymer != adhesive != composite.

### validation contract
Hydro/FEM promotion requires analytic cases; cross-solver agreement; mesh/frequency/time-step convergence; reciprocity/energy/conservation where applicable; exact-input regression; provenance of coefficients/material laws/load reconstruction.

## NEXT PRIORITY
P0 compare Kratos vs MFEM/OpenSees/CalculiX/FEniCSx/SfePy on nonlinear structural dynamics, beams/contact/joints, Python integration, tests, commercial-compatible license.
P0 audit joint-specific fatigue/damage: welded, bolted, polymer, adhesive, composite; identify public implementations/data and standards boundaries.
P1 verify Nemoh/libDelhommeau as second DIRECT hydro backend; define validation matrix vs pyHAMS/Capytaine oracle.
P1 define BlueRev global-local mechanics contract: GlobalMemberModel->JointSubmodel->StressHistory->FatigueAssessment.
P2 return only targeted PBR source recovery if high leverage; broad PBR discovery now diminishing returns.

## DETAIL MAP
HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;BLUEREV_PBR_DISCOVERY_2026-08-20.md;BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA2_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA3_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA4_2026-08-20.md;BLUEREV_CONTROL_AI_DISCOVERY_DELTA5_2026-08-20.md;MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md;MECHANICAL_WAVE_FEM_DISCOVERY_DELTA1_2026-08-20.md;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V7 first; details only as needed; newer/detailed audit wins; merged governance authority.
