# DISCOVERY STATE KERNEL V3 — 2026-08-20
PURPOSE=AI_REHYDRATION; FORMAT=TOKEN_DENSE; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; SUPERSEDES_FOR_REHYDRATION=V2; BRANCH=audit/hermes-agent-2026-08-20

## RULES
SUNK_COST_ZERO; PIPPO_OS_TEST; REPLACE_NOT_LAYER; CODE_FIRST; AUTHORITY_SEPARATION; BACKEND_OVER_REWRITE; MULTIFIDELITY; ASSUMPTIONS_ARE_STATE; SERENDIPITY; AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL-like/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea only;RESEARCH_ONLY NC/noncommercial;GAP none}.

## AI
AGENT_RUNTIME=HERMES_WINS; AUTHORITY=JARVIS_WINS; TARGET=HYBRID_DEEP_REPLACEMENT.
HERMES_DERIVED={loop,tool registry/discovery,toolsets,availability,dynamic schemas,ToolSearch,plugin/MCP discovery,subagents/delegation,noncanonical runtime-memory plumbing}.
JARVIS_KEEP={RouterPolicy,authority,sensitivity,network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}.
Hermes runs inside Jarvis sandbox/authority; equivalence tests then delete superseded Jarvis. Old ADR060 remains governance until formally superseded.

## BLUECAD EXECUTION
SemanticModelIR->{native M0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist solver|external process}; adapter modes={native_library,FMU,external_process,remote_service}.
GreenLight BSD-clear: take declarative vars/unit/reference/override ideas, not `exec`/NaN->0/clipping runtime defaults.
PyBaMM BSD3 generic BaseModel ODE/PDE/DAE strong backend; battery-specific BaseSubModel ontology not BLUECAD ontology.
ModelicaStandardLibrary BSD3; OpenModelica OSMC/AGPL boundary; PyMoCa BSD3 alpha interoperability candidate.
FMPy Dassault BSD2 FMI1/2/3 strong standard boundary; FMUs native code still sandboxed.

## BLUEREV MODEL LADDER
TARGET=seawater+N.gaditana transparent tubular loop/U-bends/pumps,outdoor solar+wave pose,fouling; later DIC/pH/CO2/O2/nutrients; wave fatigue.
M0={X,effective attenuation,light saturation/photoinhibition,decay; fixed T/carbon/nutrients if justified}.
M1={lumped X,DIC/pH,DO,gasCO2/O2,T;gas transfer,photosynthesis,O2 inhibition,actuator dynamics}.
M2={distributed1D tube PFR cells+mixed degasser;local light/DO/DIC/pH/T/X}.
M3={3D optics,local CFD,particle light histories,wave pose,fouling field}.
PROMOTE only on validation/decision need.

## OPTICS
Pruvost2026 tubular MCRT no license=>oracle. Critical direct-solver bug theta_s=INPUTS(9)=Nrays instead of theta_z index10; diffuse correct. Other risks={MATLAB primary-name mismatch,sun||tube singularity,disp in 1e6-ray parfor,hardcoded n,Ea/Es units}.
pvlib BSD3 solar; Mitsuba3 BSD3 generalized 3D participating media candidate; miepython MIT approximate cell optics.
SEMANTICS separate intrinsic_spectral_absorption_scattering(state,lambda) vs biomass_specific_cross_section(state,spectrum) vs effective_reactor_attenuation(geometry,mixing,state,spectrum,fit_dataset).
N.gaditana optical state-dependence reported ~176±19->29±1.7 m2/kg under N starvation; Fv/Fm~.67->.40; photon-supply examples ~116 vs ~275/281. No universal extinction constant.

## N.GADITANA M0/M1
Palermo2022 25C data I={20,50,100,140,210,300,450}; mu[h-1]={.0117,.0184,.0228,.0237,.0249,.0246,.0243}; fit mu_max=.0256h-1,I_K=15.28,k_d=.0046h-1;k_a=.38m2/g flat vs .20 annular=>effective geometry parameter. Weak photoinhibition identification.
Pfaffinger2016/17 N.gaditana SAG2.99 high-light up to ~2750; prior µmax cited ~.037h-1, I_K~43±6; exact epsilon/KI/phi table pending. Day/night later invalidates stationary kinetics for outdoor M1.
Nikolaou2015 N.gaditana dynamic photoproduction+photoinhibition+qE/qI; Bernardi2017 photoacclimation.
Total Mgaditana-GEM CC-BY-NC=>RESEARCH_ONLY; BioModTool LGPL boundary.

## UAL/CIESOL S-TIER
Ecosystem={Guzmán,Acién,Fernández,Rodríguez,GarcíaGallardo; SABANA,DIGITALGAE,HYCO2BIO,AUTOALGAE,Padova links}; public biological tool/raceway Matlab/current RacewaySim/old tubular virtual lab. Current RacewaySim CC-BY-NC-SA=>reference.
2014 virtual lab Las Palmerillas: ~400m tube,0.09m dia + bubble column; distributed tube+mixed column; DO/photosynthesis/X/DIC/pH/T/gas balances+actuators. Direct BLUECAD decomposition benchmark.
UAL distributed 2012/2014 + lumped 2014 validated outdoor ~3m3; later hierarchical control uses distributed model as process + lumped model optimizer => direct M1/M2 precedent.
UAL N.gaditana outdoor carbon: optimum pH~8; productivity~.16g/L/d; CO2 efficiency~74.6%; CO2/X~2.42g/g; separate optimum specific CO2 flow order ~1.9mL/L/min.

## UAL2014 FIRST-PRINCIPLES EXACT DELTA
Light Eq1:`I_av=I0*alpha/(Ka*Cb*d)*[1-exp(-Ka*Cb*d)]`.
MODEL=6 tube-loop mass balances+heat;5 column mass balances+heat; nonlinear photosynthesis/light+pH+T+DO factors; validated ~3m3. Mean errors pH~1.56%,X~2.81%,T~1-2%,DO position-dependent ~3.43/10.81%.
Key printed params include Ka=133.0324m2/kg; Ki=173.9504µE/m2/s; d_loop=.084m;L_loop=400m;d_col=.4m;L_col=3.2m; Vfluid=1m/s; H_CO2=38.36;H_O2=1.07; K_O2=.7202; P_O2,max=4.37e-5; alpha_loop=.9725;alpha_col=.1052.
SOURCE_ERRORS_TO_FLAG: prose/table h_c/h_l appear swapped; table prints M_CO2=32 and M_O2=44 (physically reversed); CO3^2- called bicarbonate; Cp printed suspicious 1 kcal/m3/C; activation-energy units suspicious. Never import table blindly; unit/sanity regression required.

## LIGHT-HISTORY / MIXING S-TIER
UAL Fernández-del-Olmo/Acién 2022 Bioresource Tech 344:126277: CFD particle tracking -> I(t) -> dynamic photosynthesis; D={14,24,44,64,84}mm; v=.4-1m/s; Lomb-Scargle; mixing factor Gamma; best reported Gamma~.199 D14/v1; larger tubes poor radial mixing. Code repo not found.
2024 CompElecAgric 226:109380: tracks 50 particles/cells (5µm,1000kg/m3); same D/v; dynamic photosynthesis->Gamma. Generic example D14: perfect integration Gamma=1 predicts dopt=.0315h-1,P=182.5g/m3/h vs mixing method dopt=.0125,P=362.3. Therefore perfect-light-integration can materially distort optimal design. Accessible SSRN all-rights-reserved=>research reference.
2021 raceway contrast reports Gamma~0/perfect segregation; more velocity not automatically useful.
GAP now=reconstruct existing Brindley/UAL dynamic model, beta/Gamma equations, CFD settings, data/license; do not invent from scratch.

## DYNAMIC RADIATIVE VALIDATION
2022 Limnospira 100L tubular methodology: time-dependent spectral absorption/scattering/phase function, MCRT, 19 tubes/connectors, MATLAB+GlobalSearch/fmincon, supplementary. Species values not transferable; methodology S for BlueRev optical experiment design.

## DTU 2026 FLUXOMIC
PazoVila/Norsker/Gernaey/Huusom AlgalResearch93:104440, CC-BY paper; 10-ODE first-principles molecular model={photon capture,electron transport,photoinhibition,lumen/stroma pH,ATP,NADPH,C fixation/photorespiration,O2/CO2 exchange}->macroscopic growth/O2/C. No repo found; data cannot be shared per paper. CLEAN_ROOM science/oracle. Compare against N.gaditana-specific lower-order models before complexity.

## OPEN PE BENCHMARK
2020 Nannochloropsis granulata pilot tubular open supplement:15 batches,I~19-836, mu_max=1.56d-1,Tmin=2.3,Topt=27.93,Tmax=32.59,MAPE~7.2%; model/dataset useful PE validation even species differs; supplementary license verify.

## CFD
TUM Severin 2019 OpenFOAM TLC benchmark: interFoam+modified interSpeciesFoam; validated tracer/height/velocity; SI complete cases+STL+MATLAB. OpenFOAM GPL external; SI license pending. Authors propose radiative transfer+Lagrangian cells. Use local CFD oracle only.

## CALIBRATION
SmartBioTech/CzechGlobe MIT automated P-I/O2 experiment/stability/adaptive conditions; pyPESTO BSD3 PE/UQ; BoFire BSD3 DoE; MAGNUS S science exact N.oceanica PBR case but heavy commercial-solver/dependency stack; Phenobottle AGPL reference.
TARGET_LOOP=assumption gap->optimal experiment->automation->data->PE/UQ->model discrimination->replacement proposal->validation/promotion.

## SEAWATER/FOULING/HYDRAULICS
GSW/TEOS10 boundary; PyCO2SYS GPL oracle;cbsyst MIT-claimed candidate after cross-validation.
Fouling public code GAP; native delta_f(s,t) couples Tlambda,D_eff,roughness,attach-detach.
ChEDL fluids MIT initial network; EPANET/WNTR later; local CFD only.

## MECHANICS
wavespectra MIT; OpenFAST Apache2 HydroDyn strong load backend but rigid6DOF floating limitation; WEC-Sim Apache2; MoorDynv2/MoorPy BSD3; OASIS GPL external; pyLife Apache2 fatigue. Need actual joint/material before fatigue formulation.
Cross-domain native value=wave->pose->optics->light history->growth + wave->stress->fatigue + fouling->optics/hydraulics/maintenance.

## NEXT
P0 exact Brindley dynamic photosynthesis + beta/Gamma + CFD settings/code/data/license.
P0 UAL2014 Eq2/mass balances + resolve table typos via independent sources/PDF.
P0 UAL lumped exact equations/params + virtual-lab package audit.
P1 N.gaditana raw spectral properties with state metadata.
P1 seawater carbonate+kLa+Nannochloropsis code/data.
P1 audit Limnospira supplementary methodology/code license.
P2 compare DTU fluxomic vs Nikolaou/Bernardi/UAL by fidelity-value-cost.
P3 Hermes migration matrix; model interchange; mechanics deepening after PBR diminishing returns.

## DETAILS
HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;BLUEREV_PBR_DISCOVERY_2026-08-20.md;BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA2_2026-08-20.md;MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V3; open detail only for evidence. Newer/detailed audit wins. Merged governance wins until formally superseded.