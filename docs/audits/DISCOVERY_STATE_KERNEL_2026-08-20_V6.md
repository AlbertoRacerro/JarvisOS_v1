# DISCOVERY STATE KERNEL V6 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;SUPERSEDES_FOR_REHYDRATION=V5;BRANCH=audit/hermes-agent-2026-08-20

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

## CONTROL/AI — NEW
### PC-Gym
`MaximilianB2/pc-gym`; MIT DIRECT; package v0.1.8, alpha but engineered: pyproject,CI+nightly,ruff,pytest,coverage branch/fail>=45,pyright,pip-audit; tests model/environment/NMPC-oracle/policy-evaluation. Standard process-control RL envs, disturbances,constraints,rewards,policy evaluation,NMPC oracle. PIPPO=ADOPT_CANDIDATE for generic `ControlBenchmark/PolicyEvaluation`; do not rebuild generic layer before spike.
Target=`PlantEnvAdapter(SemanticModel backend)->PCGym-like env`; evaluate PID/MPC/RL/ESC/etc under same scenarios/metrics; Jarvis owns deployment authority.

### CIRL
`OptiMaL-PSE-Lab/CIRL` MIT DIRECT but research prototype, NOT wholesale. Simple PyTorch policy; constructor PID arg unused; training uses random search+PSO, globals/pickle/scripts; no mature test/package architecture found. Take concept/control-informed RL or small pieces only. Related 2025 paper CC-BY demonstrates PID structure inside RL.

### Industrial PBR RL 2026
UAL+Imperial behavior-cloning RL paper/Zenodo PDF CC-BY; no code/weights/data found. Offline from trusted PID trajectories -> daytime deployment -> nightly fine-tune -> 8-day validation. Safety pattern=`demonstrations->offline train->simulation/shadow->authority-limited deploy->data->offline update->revalidate/promote`; online-trained policy never silently canonical.

### UAL controller references
3DoF-KF MoD MPC 2026: multisine excitation database->local MoD model, stronger vs ARX across horizons, separate tracking/measured/unmeasured disturbance tuning, pilot validation; PDF only.
ESC 2026: 80m2 outdoor; out-of-band dither, washout HPF+delay demodulation, solar feedforward; model-free online optimizer; no code.
EMPC 2026 UAL+Skogestad: climate-aware centralized economic MPC, CC-BY-NC paper/data request/no code. Economics separate from physics/controller contract.

## IOT/LAB
UAL IoT 2025: FIWARE+OMA-NGSI, ETL, heterogeneous devices, industrial models-as-services, cloud load tests; Zenodo PDF CC-BY only, no source. Reference architecture, not current backend.
ODIN+ source/license GAP: Erlang+MQTT+web+Python plugins, acquisition/control/optimization/state estimation/simulator/fault diagnosis/calibration/priority arbitration; A+/S reference.
ESR9 measurement schema={CO2 use,O2,biomass,N,PAM,VIS,pH,T,salinity}+calibration/drift/provenance.
SATHE adaptive thermal model: online re-ID, weather forecast; replaceable adaptive T submodel.

## EXPERIMENT DESIGN
Pyomo.DoE DIRECT revised BSD; maintained/tests; use generic FIM/parameter-precision foundation. ESR5 robust rival-model design no repo: Pyomo.DAE+SUNDIALS+SciPy, worst/expected/CVaR prediction divergence; implement plugin only if no source emerges. pyPESTO+BoFire complementary. SmartBioTech MIT automation.
Multi-fidelity BO Martens2025: paper says code/data accompanying GitHub but exact repo not found yet; GP batch BO across MTP/MBR/pilot + experiment cost; potentially key `ExperimentFidelity` optimizer. Search source before classification.

## MODEL SELECTION/DESIGN
ALBA↔ABACO cross-dataset benchmark: neither universal winner; validity depends climate/medium/reactor/objective. Native BLUECAD rival models+domains+objective scorecards+cross-validation.
INRIA topography optimization Han+Saint-Venant: added geometry can lose; design loop may recommend simpler solution.

## MECHANICS
wavespectra MIT;OpenFAST Apache2 HydroDyn wave loads but floating rigid6DOF limitation;WEC-Sim Apache2;MoorDynv2/MoorPy BSD3;OASIS GPL;pyLife Apache2 fatigue. Need actual joint/material. Native coupling=wave->pose->optics/growth and wave->stress/fatigue; fouling->optics/hydraulics/maintenance.

## NEXT PRIORITY
P0 finish PC-Gym environment/oracle contract + integration spike design; locate Martens MFBO repo.
P0 author-repo search for UAL MoD/ESC/EMPC exact code; FIWARE deployment source opportunistic.
P1 unresolved source recovery={MGM/In@lgae/Reali saline/JAX-ALBA/N.gaditana spectra/exact UAL lumped equations}.
P2 PBR discovery approaching diminishing returns: begin deeper MECHANICAL/WAVE/FATIGUE audit {HAMS/pyHAMS,Capytaine license split,Nemoh,flexible FE/global-local joints,polymer/adhesive/composite fatigue} while continuing targeted PBR finds.

## DETAIL MAP
HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;BLUEREV_PBR_DISCOVERY_2026-08-20.md;CONTINUATION;DELTA2;DELTA3;DELTA4;BLUEREV_CONTROL_AI_DISCOVERY_DELTA5_2026-08-20.md;MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V6 first; details only as needed; newer/detailed audit wins; merged governance authority.