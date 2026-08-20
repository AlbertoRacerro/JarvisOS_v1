# DISCOVERY STATE KERNEL V5 — 2026-08-20
PURPOSE=AI_REHYDRATION; FORMAT=TOKEN_DENSE; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; SUPERSEDES_FOR_REHYDRATION=V4; BRANCH=audit/hermes-agent-2026-08-20

## RULES
SUNK_COST_ZERO;PIPPO_OS_TEST;REPLACE_NOT_LAYER;CODE_FIRST;AUTHORITY_SEPARATION;BACKEND_OVER_REWRITE;MULTIFIDELITY;ASSUMPTIONS_ARE_STATE;SERENDIPITY;AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea/no-code;RESEARCH_ONLY NC/noncommercial;GAP none}.

## AI
AGENT_RUNTIME=HERMES_WINS;AUTHORITY=JARVIS_WINS;TARGET=HYBRID_DEEP_REPLACEMENT.
HERMES_DERIVED={loop,tool registry/discovery,toolsets,availability,dynamic schemas,ToolSearch,plugin/MCP,subagents/delegation,noncanonical runtime-memory plumbing}.
JARVIS_KEEP={RouterPolicy,authority,sensitivity,network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}. Hermes inside sandbox/authority; equivalence tests then delete superseded Jarvis. ADR060 governance until formal supersession.

## BLUECAD EXECUTION
SemanticModelIR->{nativeM0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist|external_process}; adapters={native_library,FMU,external_process,remote_service}.
GreenLight BSD-clear take declarative unit/reference/override ideas not exec/NaN-zero/clipping runtime. PyBaMM BSD3 generic BaseModel strong; battery submodel ontology not native IR. ModelicaStandardLibrary BSD3;OpenModelica OSMC/AGPL boundary;PyMoCa BSD3 alpha. FMPy BSD2 FMI1/2/3 strong standard boundary; FMUs sandboxed.

## BLUEREV LADDER
TARGET=seawater+N.gaditana transparent tubes/U-bends/pumps,outdoor solar+wave pose,fouling;later DIC/pH/CO2/O2/N;wave fatigue.
M0={X,effective attenuation,light saturation/photoinhibition,decay;fixed T/C/N if justified}.
M1={lumped X,DIC/pH,DO,gasCO2/O2,T;gas transfer,photosynthesis,O2 inhibition,actuators}.
M2={distributed1D tube PFR+mixed degasser;local light/DO/DIC/pH/T/X}.
M3={3D optics,local CFD,Lagrangian light histories,wave pose,fouling}.
PROMOTE only validation/decision need.

## EXISTING PBR ARCHITECTURES
INRIA In@lgae source/license GAP; near-target pipeline location/season->thermal/hydro(Freshkiss)->Lagrangian trajectories->Han->biomass/products/resources; later C++/spectral light/GUI/species sets; industrial LaCompagnieDuVent use. Exhaust before rebuilding same.
DigitAlgaesation MGM/Fierro: dynamic photosynthesis+DRUM/dFBA+C/N storage under fast/diurnal light -> reduced online models + DL. Thesis tel-04779495 landing audited; PDF not visually audited due fetch limitation. 2025 Han+hydro raceway result shows trajectory effect regime-dependent (<~10% static approx error studied laminar cases), unlike UAL tubular mixing -> fidelity validation-driven.
UAL distributed2012/2014+lumped2014 outdoor validated ~3m3; direct M1/M2 precedent. Current RacewaySim NC-SA reference. UAL2014 light Eq1 and table audited; table has likely typos (CO2/O2 MW swap,etc), no blind import.

## OPTICS/LIGHT
Pruvost2026 MCRT no license/oracle; critical direct theta index bug. pvlib BSD3;Mitsuba3 BSD3;miepython MIT approximate.
SEMANTICS={intrinsic_spectral(state,lambda),biomass_cross_section(state,spectrum),effective_attenuation(geometry,mixing,state,spectrum,fit)}; N.gaditana optical properties vary strongly with state.
Palermo2022 N.gaditana fixture I={20,50,100,140,210,300,450},mu[h-1]={.0117,.0184,.0228,.0237,.0249,.0246,.0243},mumax=.0256,IK=15.28,kd=.0046,ka=.38flat/.20annular m2/g.
Pfaffinger N.gaditana high-light ~2750; exact table pending. Nikolaou/Bernardi species-specific dynamic photoinhibition/photoacclimation.
UAL2022/2024 tubular CFD->particles->I(t)->dynamic photosynthesis,Gamma; perfect integration can distort design. Camacho2003/Brindley2016/2018 dynamic PSU lineage. Saccardo2024/25 HTS pulsed->PSU->PBR light-history scale-up, supplement data/equations but no code/license clear; analytic within-cycle reduction valuable. DTU2026 10ODE fluxomic CC-BY paper/no code/data -> oracle.
Fraunhofer2023 light-history ML: Monod/Haldane vs SVR/LSTM with ~12h light history; data/fulltext Zenodo embargo until 2027-06-23. Use learned residual/history optional, not replace physics.

## UAL 2026 CONTROL BENCHMARK — NEW PRIMARY ORACLE
REPO=`guzmanjl/benchmarkmicroalgae`; paper CEP174:107027, arXiv2512.15916; online now, Sep2026 issue. Species=Scenedesmus almeriensis.
SCOPE={pH->CO2,DO->air,X/depth->harvest+dilution,T->HX}; multi-day weather, actuator saturation/FIFO gas delays, stiff ODE, OnOff/PI/PID/EMPC, global KPI tracking+resources+biomass. IFACWC2026 challenge.
CODE STRUCTURE={Data_Benchmark.mat,simulate_benchmark_model.p,load_data.m,show_results.m,player/,IFAC_WC_player/}.
CRITICAL LIMITS: no LICENSE file/text located although README claims license info; core simulator is MATLAB `.p` p-code, not inspectable source; no visible automated test suite. CLASS=CLEAN_ROOM/REFERENCE/S_ORACLE, NOT DIRECT.
DATA input={global solar,PAR,ambientT,RH,wind minute trajectories}. Output semantics include pH,DO,T,X,Depth,DIC/HCO3/CO3/CO2,limitation factors,P,mu,maintenance,gas/harvest/HX/KPIs.
CONTROLLER CONTRACT=`ControlStep(Timeline,obs,refs,env,future,state,signals)->proposed signals+state`; forecast first-class. Candidate Jarvis/BLUECAD abstraction, BUT Jarvis authority/safety inserted after proposed actuation before hardware.

## EXPERIMENT DESIGN / CALIBRATION
SmartBioTech MIT auto P-I/O2;pyPESTO BSD3;BoFire BSD3;MAGNUS exact N.oceanica case but heavy/commercial configs;Phenobottle AGPL ref.
Pyomo/pyomo license revised BSD DIRECT; `pyomo.contrib.doe` current maintained/tests={build,error,solve,greybox,initialization}; dynamic/multiple experiments/parameter uncertainty/FIM; official current scope=parameter precision, not model discrimination. PIPPO=use Pyomo.DoE foundation, don't build FIM MBDoE ourselves.
DigitAlgaesation ESR5 Marco Sandrin prototype no public repo found: Python+Pyomo.DAE+SUNDIALS+SciPy trust-region, >=2 rival models, design duration/IC/time-varying inputs/sample times, uncertainty scenarios; criteria worst-case/expected/CVaR maximize model-prediction divergence. Candidate plugin atop Pyomo.DoE if code never released.
TARGET_LOOP=assumption gap->MBDoE->automated experiment->data->PE/UQ->model discrimination->proposal->validation/promotion.

## MEASUREMENT / LAB CONTROL
ESR6 continuous micro-PBR reference: gradients,long-term,differentT,complex light,HTS replicates,imaging,fast environmental changes.
ESR9 Wageningen measurement target={CO2 consumption,O2 production,biomass,N consumption,PAM,VIS,pH,T,salinity/conductivity}+sensor drift auto-recalibration. Candidate MeasurementSchema; derived estimates retain raw provenance.
ODIN+ source/license GAP; Erlang core+MQTT+web+Python plugins, acquisition/control/optimization/state estimation/simulator/fault diagnosis/actuator calibration/priority arbitration. A+/S architecture ref for Jarvis lab execution.

## TEMPERATURE/WEATHER CONTROL
Ali Gharib SATHE 2024: minimal identifiable auto-tuning heat model derived from full models, recalibrates recent T data, works multiple seasons/configs, especially robust vs fixed complex model winter. Integrated MPC/optimal control; culture depth impacts inertia; known weather forecasts improve control. Pattern=adaptive replaceable T submodel + forecast-aware control.

## MODEL BENCHMARKING
ALBA2021 vs ABACO2 2024 cross-dataset benchmark 2025: Narbonne56m2/443d synthetic wastewater + Milan3.8m2 digestate + Almeria80m2 urban wastewater. Both good cross-domain; ABACO2 stronger biomass overall but winter weakness + simplified nitrification/NH4 limitation; ALBA stronger nitrogen/BSMO tracking. NO UNIVERSAL WINNER; applicability depends climate/medium/reactor/objective. Native BLUECAD workflow=rival models+validity domains+objective scorecard+cross-dataset validation.
ABACO2 Python/NumPy+SciPy/NelderMead reported, but no public repo found => CLEAN_ROOM ref.
ALBA balance architecture={COD/C/N/P/H/O,Petersen matrix,Haldane+BeerLambert,Liebig,pH equilibria,kLa CO2/NH3/O2,cardinal pH/T}; JAX hybrid package reported but public repo not found.

## DESIGN OPTIMIZATION
INRIA 2025 topography optimization=Han+Saint-Venant+geometry optimal control; periodic regime flat bottom numerically optimal, nontrivial shapes only some scenarios/mixing devices. Earlier mixing preprints exploit periodicity/permutation to cut computational cost. Native design loop=`DesignVariable->geometry/backend->physics->objective/constraints->optimizer->verification`; must allow simpler design to win. No public code found.

## SEAWATER/FOULING/HYDRO/MECH
GSW/TEOS boundary;PyCO2SYS GPL oracle;cbsyst MIT-claimed pending cross-validation. INRIA/Reali saline speciation S ref activities+ion-pairing ~40 algebraic->5ODE,PHREEQC+Total+LOV validation, Matlab source not found.
Fouling public code GAP;delta_f state couples optics+hydraulics. ChEDL fluids MIT initial loop.
Freshkiss3D gated GitLab/license unknown, free-surface hydro+Lagrangian trajectories; TUM OpenFOAM benchmark external.
wavespectra MIT;OpenFAST Apache2 HydroDyn strong wave loads but floating rigid6DOF limitation;WEC-Sim Apache2;MoorDynv2/MoorPy BSD3;OASIS GPL;pyLife Apache2 fatigue. Need actual joint/material.
NATIVE_CROSS_DOMAIN=wave->pose->optics->light-history->growth + wave->stress->fatigue + fouling->optics/hydro/maintenance.

## NEXT
P0 monitor/audit benchmarkmicroalgae issues/commit/license/source; use only oracle currently.
P0 search Pyomo.DoE/model-discrimination open ecosystem before custom plugin; locate Sandrin source/thesis.
P0 UAL 2026 EMPC/extremum-seeking/model-on-demand + IoT platform code/license for Jarvis lab/control.
P0 recover MGM/In@lgae/Reali saline/JAX-ALBA code/deliverables.
P1 dynamic-light family same-trajectory benchmark; exact UAL lumped equations; N.gaditana spectra.
P2 mechanical/wave/fatigue deeper after PBR diminishing returns.

## DETAILS
HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;BLUEREV_PBR_DISCOVERY_2026-08-20.md;BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA2_2026-08-20.md;DELTA3;DELTA4;MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V5 first; details on demand. Newer/detailed audit wins; merged governance remains authority.