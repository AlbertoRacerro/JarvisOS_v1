# DISCOVERY STATE KERNEL V4 — 2026-08-20
PURPOSE=AI_REHYDRATION; FORMAT=TOKEN_DENSE; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; SUPERSEDES_FOR_REHYDRATION=V3; BRANCH=audit/hermes-agent-2026-08-20

## RULES
SUNK_COST_ZERO; PIPPO_OS_TEST; REPLACE_NOT_LAYER; CODE_FIRST; AUTHORITY_SEPARATION; BACKEND_OVER_REWRITE; MULTIFIDELITY; ASSUMPTIONS_ARE_STATE; SERENDIPITY; AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea;RESEARCH_ONLY NC/noncommercial;GAP none}.

## AI
AGENT_RUNTIME=HERMES_WINS; AUTHORITY=JARVIS_WINS; TARGET=HYBRID_DEEP_REPLACEMENT.
HERMES_DERIVED={loop,tool registry/discovery,toolsets,availability,dynamic schemas,ToolSearch,plugin/MCP discovery,subagents/delegation,noncanonical runtime-memory plumbing}.
JARVIS_KEEP={RouterPolicy,authority,sensitivity,network/egress,budget,confirmation/digest,credentials,canonical engineering state,proposal/promotion,ContextBundle provenance/evidence,engineering memory}.
Hermes inside Jarvis sandbox/authority; equivalence tests then delete superseded Jarvis. ADR060 historical governance until formal supersession.

## BLUECAD EXECUTION
SemanticModelIR->{native M0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist solver|external process}; adapter={native_library,FMU,external_process,remote_service}.
GreenLight BSD-clear take declarative unit/reference/override ideas, not exec/NaN->0/clipping runtime. PyBaMM BSD3 generic BaseModel strong backend; battery submodel ontology not native IR. ModelicaStandardLibrary BSD3; OpenModelica OSMC/AGPL boundary; PyMoCa BSD3 alpha. FMPy BSD2 FMI1/2/3 strong standard boundary; FMUs sandboxed.

## BLUEREV MODEL LADDER
TARGET=seawater+N.gaditana transparent tubes/U-bends/pumps,outdoor solar+wave pose,fouling; later DIC/pH/CO2/O2/nutrients; wave fatigue.
M0={X,effective attenuation,light saturation/photoinhibition,decay;fixed T/carbon/nutrients if justified}.
M1={lumped X,DIC/pH,DO,gasCO2/O2,T;gas transfer,photosynthesis,O2 inhibition,actuators}.
M2={distributed1D tube PFR cells+mixed degasser;local light/DO/DIC/pH/T/X}.
M3={3D optics,local CFD,Lagrangian light histories,wave pose,fouling field}.
PROMOTE only validation/decision need.

## S-TIER EXISTING PBR ARCHITECTURES
### INRIA In@lgae
HISTORICAL SOFTWARE; public source/license not found => REFERENCE/GAP.
Pipeline=process+location+season -> thermal+hydrodynamics(Freshkiss) -> Lagrangian cell trajectories -> Han photosynthesis -> GIS/meteo/solar+T -> biomass/lipids/pigments+CO2/N/water -> productivity/resource maps. Key models later C++, spectral light added, GUI+species parameter sets. Used industrially with La Compagnie du Vent for large-scale raceway design.
PIPPO_IMPACT=before building equivalent native PBR pipeline, exhaust source/license; architecture is near-direct predecessor of target.

### DigitAlgaesation MGM / Fierro
ESR4 objective=generic Microalgae Growth Model/digital twin: dynamic photosynthesis + DRUM/metabolic flux + C/N storage under diurnal/hydrodynamic light + dynamic FBA -> reduced models for online control/monitoring + DL integration. CORDIS lists deliverable `Digital twin based on reference process model (MGM)` + weather-uncertainty framework; payload not recovered. Fierro thesis 2024-10-29 `Modelling and control of photobioreactors under dynamic light regimes`; HAL file/source not yet recovered. S PRIORITY.
Outputs include Han flashing-light theory, photoinhibition+photoacclimation optimal control, 2025 Han+hydrodynamics study. Important regime result: in studied predominantly laminar raceway, static average-growth approximation <~10% error and hydro effect marginal; contrast UAL tubular mixing literature where trajectory/mixing materially changes design. Therefore trajectory-resolved light is optional validation-driven fidelity, not universal default.

### UAL/CIESOL
Current RacewaySim NC-SA reference; old tubular lab ~400m tube/0.09m + mixed bubble column; distributed2012/2014+ lumped2014 validated outdoor ~3m3; hierarchical-control precedent uses distributed process + lumped optimizer. UAL2014 light Eq1 Iav=I0*alpha/(Ka*Cb*d)*(1-exp(-Ka*Cb*d)); key Ka=133.0324m2/kg, Ki=173.9504µE/m2/s; table has serious likely typos (M_CO2/O2 swapped,etc), no blind import. Exact Eq2 algebraic transcription still requires visual source.

## LIGHT/MIXING MODELS
Pruvost2026 MCRT no license/oracle; direct theta index bug. pvlib BSD3; Mitsuba3 BSD3; miepython MIT approximate.
OPTICAL_SEMANTICS={intrinsic_spectral(state,lambda),biomass_cross_section(state,spectrum),effective_reactor_attenuation(geometry,mixing,state,spectrum,fit)}; N.gaditana cross-section changes strongly with physiology.
Palermo2022 N.gaditana M0: I={20,50,100,140,210,300,450};mu[h-1]={.0117,.0184,.0228,.0237,.0249,.0246,.0243};mumax=.0256h-1;IK=15.28;kd=.0046h-1;ka=.38m2/g flat vs .20 annular.
Pfaffinger N.gaditana high light ~2750, prior mumax~.037h-1/IK~43±6; exact high-light table pending.
Nikolaou2015/Bernardi2017 species-specific dynamic photoinhibition/qE/qI/photoacclimation.
UAL2022 tubular CFD->particles->I(t)->dynamic photosynthesis, D14-84mm,v.4-1m/s,Gamma; 2024 mixing-intensity design shows perfect-light-integration can materially distort optimum. Raceway contrast Gamma~0.
Camacho-Rubio2003 PSU dynamic foundation; Brindley2016 arbitrary real I(t); 2018 reduced frequency characterization.
Saccardo2024/2025=HTS pulsed data -> PSU dynamic model -> PBR individual light-history -> validated scale-up. 2025 supplement declares HTS data+PBR equations; gPROMS used for fit; no code repo found; license treated RESEARCH_ONLY/CLEAN_ROOM pending exact file terms. Indexed fit approx ka=1.53e-4,kc=.0154,kd=5.8286,kp=.1702,kr=5.4119e-5; species-specific. Analytic within-cycle reduction is strong fast-model pattern.
DTU2026 fluxomic 10ODE CC-BY paper, no code/data; mechanistic oracle only until implementation available.

## HYDRO/LAB EXECUTION
Freshkiss3D: gated GitLab, license not verified; 3D hydrostatic free-surface NS, variable density, Python+Cython, tracers,Lagrangian particles,VTK,tests/examples. Candidate raceway trajectory backend if license; closed tube fit uncertain.
TUM2019 OpenFOAM TLC complete SI cases/STL/MATLAB; OpenFOAM GPL external; local CFD oracle.
ODIN/ODIN+: source/license not found; current architecture Erlang robust core+MQTT+web+Python plugins; sensor acquisition,control/optimization/state estimation,process simulator,hardware/intermodule diagnosis,actuator calibration,priority arbitration; real Phytopulse use. Historical C++/Scilab/CORBA with confidence indexes. A+/S architecture for Jarvis lab execution; compare rather than reinvent.

## SEAWATER/CHEMISTRY
GSW/TEOS10 boundary; PyCO2SYS GPL oracle; cbsyst MIT-claimed candidate after validation.
INRIA/Reali2024 saline speciation S reference: activities+ionic strength+ion pairing; transforms ~40 algebraic unknowns -> 5-unknown ODE system; significant pairs selected via TotalEnergies pilot+PHREEQC; MATLAB; LOV experiments/pH; validated pH/ionic strength/pairs/composition. Thesis Polimi/ANR BARRIER; code not found. 2025 ALBA extension confirms ion pairing controls pH/inorganic-C availability under salinity. Candidate broader speciation oracle complementary to TEOS/CO2SYS.

## ALBA/CONSORTIA PROCESS ARCHITECTURE
ALBA2021 Polimi/INRAE/INRIA: 443d outdoor calibration/validation; balances COD/C/N/P/H/O, Petersen stoichiometric matrix, algae+heterotroph+AOB/NOB, Haldane+Beer-Lambert, Liebig C/N/P, pH equilibria, CO2/NH3/O2 kLa, cardinal pH/T, Arrhenius decay; complete SI incl kLa+uncertainty. Useful M1 balance/speciation/gas-transfer architecture, not wholesale pure-algae model.
2024 reports mechanistic+ANN ALBA Python/JAX package preserving physical constraints; public repo not found. ABACO-2 2024 outdoor pilot modern consortium model deep audit pending.

## CALIBRATION
SmartBioTech/CzechGlobe MIT automated P-I/O2; pyPESTO BSD3; BoFire BSD3; MAGNUS exact N.oceanica PBR PE but heavy stack/commercial solver configs; Phenobottle AGPL reference.
TARGET_LOOP=assumption gap->optimal experiment->automation->data->PE/UQ->model discrimination->replacement proposal->validation/promotion.

## FOULING/HYDRAULICS/MECHANICS
Fouling public code GAP; native delta_f(s,t) couples optics+diameter+roughness+attach/detach. ChEDL fluids MIT initial closed-loop hydraulic network.
wavespectra MIT; OpenFAST Apache2 HydroDyn strong wave loads but rigid6DOF floating limitation; WEC-Sim Apache2; MoorDynv2/MoorPy BSD3; OASIS GPL; pyLife Apache2 fatigue. Need actual joint/material.
NATIVE_CROSS_DOMAIN=wave->pose->optics->light history->growth + wave->stress->fatigue + fouling->optics/hydraulics/maintenance.

## NEXT
P0 recover Fierro thesis/HAL + MGM deliverable/source/package.
P0 locate In@lgae source/archive/license or establish unavailable.
P0 ODIN source/license/security architecture.
P0 Reali saline thesis/Matlab source/follow-up paper.
P0 JAX hybrid ALBA package + ABACO-2 source/SI.
P1 Saccardo supplementary/data exact license + visual equation audit.
P1 exact UAL lumped equations + UAL2014 Eq2 visual source.
P1 dynamic model benchmark: Han vs Camacho/Saccardo vs Nikolaou/Bernardi on same light trajectories.
P2 Hermes migration/model interchange/mechanics after PBR diminishing returns.

## DETAILS
HERMES_AGENT_CODE_FIRST_AUDIT_2026-08-20.md;BLUEREV_PBR_DISCOVERY_2026-08-20.md;BLUEREV_PBR_DISCOVERY_CONTINUATION_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA2_2026-08-20.md;BLUEREV_PBR_DISCOVERY_DELTA3_2026-08-20.md;MODEL_CALIBRATION_AND_OED_DISCOVERY_2026-08-20.md;MODEL_IR_AND_INTERCHANGE_AUDIT_2026-08-20.md;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS_2026-08-20.md;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md.
REHYDRATION=read V4 only first; details on demand. Detailed/newer audit wins; merged governance remains authority.