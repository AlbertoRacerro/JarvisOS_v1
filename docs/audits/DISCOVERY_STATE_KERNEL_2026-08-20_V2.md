# DISCOVERY STATE KERNEL V2 — 2026-08-20
PURPOSE=AI_REHYDRATION; FORMAT=TOKEN_DENSE; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; SUPERSEDES_FOR_REHYDRATION=DISCOVERY_STATE_KERNEL_2026-08-20.md; BRANCH=audit/hermes-agent-2026-08-20

## RULES
R0 SUNK_COST_ZERO: Jarvis internal code gets no preservation bonus.
R1 PIPPO_OS_TEST: choose Jarvis/external/hybrid as if building from zero today.
R2 REPLACE_NOT_LAYER: external winner -> equivalence/migration tests -> delete superseded Jarvis; avoid duplicate frameworks.
R3 CODE_FIRST: inspect implementation/tests/issues/deps/license/failure modes; README/paper claims insufficient.
R4 AUTHORITY_SEPARATION: external runtime/solver never owns accepted engineering truth/policy/egress/budget/promotion.
R5 BACKEND_OVER_REWRITE: BLUECAD owns semantic IR/adapters/policy/provenance/verification/coupling/UX; reuse mature kernels.
R6 MULTIFIDELITY: smallest model answering current question; promote fidelity only on validation/decision need.
R7 ASSUMPTIONS_ARE_STATE: explicit/source/confidence/domain/test/supersession.
R8 LICENSE={DIRECT permissive; BOUNDARY stable adapter/LGPL-like/nonmodified; EXTERNAL GPL/AGPL/process; CLEAN_ROOM idea/equations/no code; RESEARCH_ONLY NC/noncommercial; GAP none}.
R9 SERENDIPITY: search labs/authors/industry/standards/supplements/tools, not GitHub keywords only.
R10 AUDIT_BRANCH_ONLY: no implementation/master/spec mutation from discovery.

## AI ARCHITECTURE
VERDICT_AGENT_RUNTIME=HERMES_WINS; VERDICT_AUTHORITY=JARVIS_WINS; TARGET=HYBRID_DEEP_REPLACEMENT.
REPLACE_WITH_HERMES_DERIVED={generic loop,tool registry/discovery,toolset composition,availability,dynamic schemas,ToolSearch/progressive disclosure,plugin/MCP discovery,subagents/delegation,runtime memory plumbing where noncanonical}.
KEEP_JARVIS={RouterPolicy,authority,sensitivity,network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}.
SECURITY=Hermes inside Jarvis authority; host/process sandbox required; YAML deny != sandbox.
MIGRATION=equivalence tests then delete replaced Jarvis modules.
OLD_ADR060=historical governance; 2026-08-20 audit broadens adoption but does not authorize change.

## BLUECAD EXECUTION ARCHITECTURE
NATIVE_VALUE={semantic engineering IR,assumptions/provenance,policy,verification,promotion,cross-domain coupling,workflow/UI}.
MODEL_PIPELINE=SemanticModelIR->{native M0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist solver|external process}.
ADAPTER_MODES={native_library,FMU,external_process,remote_service}.
GreenLight BSD-clear: KEEP ideas={declarative vars,unit,description,reference,override layering}; DO_NOT_COPY runtime defaults={generated exec,NaN->0,clipping}.
PyBaMM BSD3: BaseModel genuinely generic ODE/PDE/DAE + symbolic/discretization/solver/citations; BaseSubModel battery-domain ontology -> backend/reference, not BLUECAD ontology. Disable telemetry by policy if embedded.
ModelicaStandardLibrary BSD3 broad mature multi-domain assets; OpenModelica OSMC/AGPL -> EXTERNAL/BOUNDARY; PyMoCa BSD3 alpha Modelica->AST->instantiate->flatten->CasADi/SymPy candidate spike.
FMPy Dassault BSD2 FMI1/2/3, model descriptions/simulation/events/remoting/container/cross-check; FMI is strong backend contract; FMU native code still sandboxed.

## BLUEREV TARGET
SYSTEM=seawater+N.gaditana/Microchloropsis; transparent straight/U-bend tube network+pumps; outdoor solar+wave pose; growth/light/photoinhibition/self-shading/fouling; later DIC/pH/CO2/O2/nutrients; structure wave fatigue.

MODEL_LADDER:
M0_EMPIRICAL={X(t),effective attenuation,light saturation/photoinhibition,decay; fixed carbon/nutrients/T if justified}.
M1_LUMPED={X,DIC/pH,DO,gasCO2/O2,T,nutrient optional; gas transfer; photosynthesis; O2 inhibition; actuator dynamics; effective optics}.
M2_DISTRIBUTED_1D={axial tubular PFR cells + mixed degasser/bubble column; local light/DO/DIC/pH/T/X; circulation/gas transfer}.
M3_LOCAL_HIGH_FIDELITY={MCRT/3D radiative transfer,local CFD U-bend/degasser,particle trajectories/light histories,wave-varying pose,fouling field}.
PROMOTION=lower model fails validation/decision robustness OR question requires missing spatial/timescale physics.

## PBR OPTICS
Pruvost2026 tubular MCRT: no license=>CLEAN_ROOM/oracle; direct+diffuse/curved interfaces/scattering. CRITICAL_BUG direct solver theta_s=INPUTS(9) while main 9=Nrays,10=theta_z; diffuse uses 10. Other risks={MATLAB primary-name mismatch,sun||tube singularity,disp in 1e6-ray parfor,hardcoded refractive indices,Ea/Es units ambiguous}. Validate/fix only as oracle.
pvlib BSD3 DIRECT solar boundary; Mitsuba3 BSD3 candidate arbitrary 3D participating media; miepython MIT approximate cell optics with uncertainty.
OPTICAL_SEMANTICS_DECISION: distinguish intrinsic_spectral_absorption_scattering(state,lambda), biomass_specific_cross_section(state,spectrum), effective_reactor_attenuation(geometry,mixing,state,spectrum,fit_dataset).
N.gaditana state dependence: reported dry-weight-specific optical cross-section ~176±19 -> 29±1.7 m2/kg during ~5d N starvation; Fv/Fm ~0.67->0.40; other photon-supply conditions ~116 vs ~275/281 m2/kg. Therefore no universal extinction constant.

## N.GADITANA BIOLOGY / M0 DATA
Nikolaou2015=N.gaditana photoproduction+photoinhibition+qE/qI dynamic model; Bernardi2017 adds photoacclimation; high-priority M1 science, reusable code not cleared.
Palermo2022 direct M0 fixture: 25C, ~4mm quasi-isoactinic, incident I={20,50,100,140,210,300,450}; mu[h-1]={.0117,.0184,.0228,.0237,.0249,.0246,.0243}; fitted mu_max=.0256 h-1 (~.61d-1), I_K=15.28, k_d=.0046h-1; effective k_a=.38m2/g flat vs .20m2/g annular. Geometry dependence proves fitted k_a != intrinsic material property. Range did not strongly identify photoinhibition.
Pfaffinger2016/2017: N.gaditana SAG2.99 high-light to ~2750umol m-2s-1; identifies limitation/optimum/inhibition via mean-integral PFD; exact kinetic table still to extract. 2019 scale-up to ~8m2 TLC; dynamic day/night shows stationary kinetics insufficient -> M1 dynamic physiology.
Total-RD/Mgaditana-GEM iMgadit23 CC BY-NC=>RESEARCH_ONLY; later metabolism layer. BioModTool LGPL=>BOUNDARY. fmairet/photoacclimation no license=>reference.

## UAL/CIESOL S-TIER ECOSYSTEM
WHY=closest discovered public ecosystem to desired Aspen-like PBR: validated outdoor models + virtual labs + control + real data + current digitalization.
AUTHORS/ROUTES={JoséLuisGuzmán,FranciscoGabrielAcién,Fernández,Rodríguez,GarcíaGallardo,UAL/CIESOL,SABANA,DIGITALGAE/HYCO2BIO/AUTOALGAE,Padova collaborators}.
Public tools include biological-model tool, Matlab dynamic raceway simulator (time+space balances, seasonal open-loop, pH/DO on-off/PID/selective control), current RacewaySim, old tubular-PBR virtual lab.
RacewaySim current: arbitrary strain params, geolocation solar model,dilution/harvesting,pH/DO,ASCII export; LICENSE=CC BY-NC-SA4=>RESEARCH_ONLY/reference.
2014 tubular virtual lab reference plant: Las Palmerillas/CAJAMAR; ~10 fence PBRs; each ~400m tube,0.09m dia; bubble column ~3.5m x0.4m. Architecture=tubular loop distributed/PFR cells + bubble-column CSTR; states/balances DO,photosynthesis,X,DIC,pH,T,gasO2/CO2,CO2 loss; O2 inhibition; identified actuator dynamics. This decomposition is direct BLUECAD benchmark.
UAL distributed models: 2012 Bioresource Technology + 2014 IECR first-principles; fluid/mass-transfer/biology/spatial+temporal gradients/DO/CO2/photosynthesis/X/gas/pH/T; calibrated+validated outdoor ~3m3 tubular PBR; BLUECAD role=M2 high-fidelity 1D oracle.
UAL 2014 CES lumped nonlinear model: reduced complexity for optimization/control, validated outdoor; BLUECAD role=M1. Later hierarchical control explicitly uses distributed PDE as real-process simulator and lumped ODE inside optimizer => direct precedent for our multifidelity architecture.
UAL N.gaditana carbon validation: outdoor ~3m3 pH6-10 via CO2; optimum ~pH8; productivity ~0.16g/L/d; CO2 efficiency ~74.6%; CO2/biomass ~2.42g/g. Separate study artificial seawater ~30g/L NaCl reports optimum CO2-specific flow order ~1.9mL CO2/Lculture/min. Use M1 calibration/sanity.

## CFD/LIGHT HISTORY
TUM Severin/Brück/Weuster-Botz TLC OpenFOAM benchmark: interFoam + modified interSpeciesFoam passive species; validated tracer/fluid height/velocity; supplementary has complete adjustable OpenFOAM cases+STL+MATLAB postproc (~14.8MB ZIP etc). Authors explicitly propose radiative transfer + Lagrangian algae particles for cell light histories. OpenFOAM GPL=>EXTERNAL; supplement license pending. Use oracle/fixture, local CFD only.

## EXPERIMENT/CALIBRATION
TARGET_LOOP=assumption gap->optimal experiment->automation->measurement->parameter estimation/UQ->model discrimination->replacement proposal->validation/promotion.
SmartBioTech/CzechGlobe MIT: automated O2 P-I curves, photosynthesis/respiration, R2/stability/turbidostat, adaptive light/T/gas/stirring/OD. A+/S experimental backend/reference.
Phenobottle OJIP/growth tracking AGPL=>EXTERNAL/reference.
MAGNUS Imperial: contains N.oceanica PBR PE case with X,nitrate,quota,FAME,attenuation,Haldane/light averaging/data; S science but heavy deps/commercial solver configs. Prefer compare pyPESTO BSD3 + BoFire BSD3 + lighter OED before integrating full MAGNUS.

## SEAWATER/CARBON
GSW/TEOS10 BOUNDARY/nonmodified pending legal; PyCO2SYS GPL=>EXTERNAL oracle; cbsyst MIT-claimed candidate after license hygiene + numerical cross-validation.
M0 may freeze pH/carbon/seawater props; M1+=TEOS10+carbonate+kLa CO2/O2+biological uptake.

## FOULING/HYDRAULICS
N.gaditana-specific fouling literature exists (XDLVO/DPM,materials,shear,salinity,EPS), PUBLIC_CODE=GAP.
Native state candidate delta_f(s,t): Tlambda(delta_f); D_eff=D_clean-2delta_f; roughness(delta_f); ddelta/dt=attach-detach(tau_wall...). High native cross-domain value.
ChEDL fluids MIT DIRECT initial hydraulic network; EPANET MIT/WNTR BSD if network grows; local CFD only.

## MECHANICS
wavespectra MIT sea-state input; OpenFAST Apache2 HydroDyn best current standalone wave-load candidate but floating ElastoDyn platform normally rigid6DOF -> not full flexible BlueRev; WEC-Sim Apache2 second oracle; MoorDynv2/MoorPy BSD3; OASIS GPL EXTERNAL; pyLife Apache2 strong fatigue backend; fatpack license pending.
PIPELINE=sea spectrum->hydro loads->global structural model->local joint submodel->stress history->material-specific fatigue.
BLOCKER=actual joint/material class (welded/bolted/polymer/adhesive/composite) determines fatigue formulation.
NATIVE_CROSS_DOMAIN=wave->pose->tube orientation->optics->cell light history->growth AND wave->stress->fatigue AND fouling->optics+hydraulics+maintenance.

## DISCOVERY PRIORITY
S1 extract UAL2012/2014 exact equations/parameter tables/code/supplements/licenses; audit downloadable UAL virtual-lab packages.
S1 extract Pfaffinger thesis exact high-light kinetic params (PDF visual audit required).
S1 locate raw N.gaditana spectra/cross-section datasets + physiological state metadata.
S1 locate Lagrangian cell trajectory/light-history PBR code/data.
S1 locate seawater carbonate+kLa+Nannochloropsis source/data.
S2 Hermes component-by-component replacement matrix + security/equivalence slices.
S3 PyBaMM generic feasibility, PyMoCa/Modelica subset, FMI paths.
S4 mechanical deeper: HAMS/pyHAMS, Capytaine license split, Nemoh, flexible FEM, actual-joint fatigue.
DEFER={process safety,materials/corrosion,industrial protocols,reaction/catalysis,electrochemistry,meshing,P&ID auto-layout,heat integration,costing,broad UQ} until S1-S4 advance.

## DETAIL MAP
- HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md
- BLUEREV_PBR_DISCOVERY_2026-08-20.md
- BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md
- MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md
- MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md
- SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md
- ../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md

REHYDRATION_RULE=read V2 first; open detail only for exact evidence. Detailed/newer audit overrides kernel. Governance authority remains merged specs/ADRs until formally superseded.