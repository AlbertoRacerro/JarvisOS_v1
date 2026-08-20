# BLUEREV PBR DISCOVERY DELTA3 — 2026-08-20
FORMAT=AI_FIRST; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; PREVIOUS={BLUEREV_PBR_DISCOVERY_2026-08-20.md,CONTINUATION,DELTA2}

## 0 DELTA
NEW_S_TIER={INRIA In@lgae historical process simulator; Freshkiss3D hydrodynamics/Lagrangian kernel; ODIN/ODIN+ lab supervision-control architecture; DigitAlgaesation MGM/digital-twin lineage; Fierro dynamic-light thesis; Saccardo2024/2025 PSU HTS->PBR scale-up; INRIA saline ionic-speciation model; ALBA/ABACO process-model architecture}.
PIPPO_TEST_IMPACT=HIGH: before implementing BLUECAD PBR biology/process/lab-control layers, compare against these existing architectures/code; no preservation bonus for Jarvis native plans.

## 1 INRIA IN@LGAE — CLOSEST HISTORICAL PRECURSOR TO BLUECAD-PBR FOUND
NAME=In@lgae; ORG=INRIA BIOCORE + ANGE; CONTACT=Olivier Bernard; participants historically Étienne Delclaux, Francis Mairet, Olivier Bernard, Quentin Béchet.
STATUS=software/platform repeatedly listed in INRIA annual reports 2016-2023; public source/license not found in current audit.
CLASS=REFERENCE/GAP until source+license obtained; do NOT infer openness from INRIA listing.

FUNCTIONAL_SCOPE:
- simulate microalgae productivity as function of process type + geographic location + season/year;
- process thermal dynamics + hydrodynamics;
- strain parameter sets for nitrogen limitation, temperature, light;
- outputs biomass, CO2/nitrogen fluxes, lipid/sugar accumulation;
- later key models rewritten C++ for speed;
- later light-spectrum composition included in growth computation;
- GUI + stored parameter sets for multiple species.

OLDER_ARCHITECTURE_REPORT_CRITICAL:
1. hydrodynamic module `Freshkiss` computes flow and reconstructs Lagrangian trajectories perceived by cells;
2. trajectories coupled to Han photosynthesis model -> overall photosynthesis yield;
3. GIS/meteo module handles arbitrary Earth location, culture temperature + solar flux;
4. productivity layer computes biomass/lipids/pigments + CO2/nutrients/water consumption;
5. productivity maps can be coupled with resource maps (CO2/nutrients/land).
INDUSTRY=La Compagnie du Vent contract used In@lgae to predict impact of large-scale raceway design on productivity.

BLUECAD_VERDICT:
- architecture is strikingly close to our converged target: weather->thermal/hydro->Lagrangian light history->physiology->productivity/resources;
- if code/license ever recovered and technically sound, apply PIPPO test vs building corresponding native solver pieces;
- even without code, treat as prior art/reference architecture and validation roadmap;
- BLUECAD differentiation remains semantic IR/provenance/cross-domain generalized coupling + multi-backend integration, not merely reimplementing this pipeline.

## 2 FRESHKISS3D — HYDRO/LAGRANGIAN KERNEL BEHIND IN@LGAE LINEAGE
NAME=FREe Surface Hydrodynamics using KInetic SchemeS in 3D; ORG=INRIA ANGE/UPMC/CNRS/CEREMA lineage.
SOURCE=GitLab INRIA repository exists but access explicitly gated: external account + request project administrator to add user to group.
LICENSE=NOT FOUND/NOT VERIFIED. CNRS code catalogue entry describes software but does not display license for Freshkiss3D at page end. Related channel packages have mixed GPL/BSD/etc and cannot establish core license.
CLASS=UNKNOWN-LICENSE/ACCESS-RESTRICTED => BOUNDARY/REFERENCE pending direct license audit.

CAPABILITIES:
- 3D hydrostatic incompressible free-surface Navier-Stokes, variable density;
- layer-averaged/multilayer shallow-water style models;
- high-level Python API around compiled Cython core;
- tracer/species convection-diffusion;
- Lagrangian particle tracking API;
- VTK outputs;
- examples/tutorials/tests/build instructions visible in public docs;
- source supports Linux/macOS; dependencies include SWIG/METIS.

BLUECAD_USE_IF_LICENSE_OK:
- candidate local/raceway hydrodynamics + trajectory backend;
- possibly a better fit than generic CFD for free-surface raceways; less obviously suited to closed pressurized tubular loops/U-bends;
- trajectory interface architecture useful even if code unusable.

## 3 ODIN / ODIN+ — BIOPROCESS SUPERVISION ARCHITECTURE
ORG=INRIA BIOCORE/MICROCOSME; platform active in annual reports through 2025; source/license not found in current audit.
CLASS=REFERENCE/GAP until source/license.

CURRENT_ARCHITECTURE:
- distributed application;
- Erlang core for robustness/fault tolerance;
- MQTT broker module communication;
- web GUI/remote supervision;
- sensor acquisition online/offline;
- Python plugins for control/optimization/state estimation without recompiling core;
- process simulator for experimentation/training;
- modular plant adaptation;
- explicit diagnosis modules for hardware/inter-module faults;
- actuator calibration module;
- priority-access management for shared platform elements.

HISTORICAL_EVOLUTION:
2017 version=C++ + Scilab + CORBA/component isolation + explicit confidence indexes.
2020+ redesign=Erlang+MQTT+Python plugins.

REAL_USE=Phytopulse continuous PBR experimental platform driven by ODIN+; BlueEdge project says data-driven/AI supervision algorithms can be implemented through ODIN+.

PIPPO/JARVIS RELEVANCE:
- strong reference for future Jarvis lab/plant execution plane: separate robust acquisition/actuation core from replaceable Python algorithms;
- MQTT/event bus + hardware diagnosis + actuator calibration + priority arbitration are likely more mature patterns than writing ad-hoc device loops;
- do not adopt wholesale without source/security/license audit;
- compare against Jarvis capability policy: ODIN operational robustness != Jarvis authority/provenance. Hybrid boundary likely.

## 4 DIGITalGAESATION MGM — DIRECT DIGITAL-TWIN PRECEDENT
PROJECT=H2020 MSCA ITN DigitAlgaesation 955520; 2021-03-01..2025-02-28; coordinator Padova; broad academic/industrial consortium.
ESR4=Development and analysis of a digital twin for monitoring/control/optimization in microalgae: Microalgae Growth Model (MGM), hosted INRIA; PhD Joel Ignacio Fierro Ulloa.
CORDIS lists public deliverable title `Digital twin based on reference process model (MGM)` and `Embedded framework for control under weather uncertainty`; dynamic download payload not recovered/audited yet.

ORIGINAL_ESR4_OBJECTIVES:
- metabolic model dealing with light variations;
- integrate state-of-art dynamic photosynthesis models + DRUM metabolic-flux approaches;
- investigate N/C storage under variable light, including diurnal and rapid hydrodynamic light changes, via dynamic flux balance analysis;
- derive reduced models for online monitoring/control;
- integrate with deep learning;
- aim generic MGM as standard monitoring/control/optimization model;
- validate single/multi-layer cultivation.

ARCHITECTURE=MECHANISTIC_HIGH_FIDELITY -> REDUCED_ONLINE_MODEL -> DIGITAL_TWIN/CONTROL; exactly our M2->M1 reduction concept.

## 5 FIERRO ULLLOA THESIS / DYNAMIC-LIGHT MODEL LINEAGE
THESIS=Joel Ignacio Fierro Ulloa, `Modelling and control of photobioreactors under dynamic light regimes`, Université Côte d'Azur, defended 2024-10-29; reported as DigitAlgaesation MGM/digital-twin PhD. HAL landing/file not recovered by generic search yet; annual report confirms thesis.
PRIORITY=S: exhaust thesis/HAL/CORDIS before implementing MGM-like layer.

KNOWN_OUTPUTS:
- 2023 Journal Mathematical Biology: theoretical growth under high/low flashing light using Han model;
- 2024 ADCHEM/IFAC: optimal control accounting for photoinhibition + photoacclimation with controls irradiance+dilution; BOCOP numerical work and turnpike behavior;
- 2025 SIAM J Applied Mathematics: Han + hydrodynamics; in predominantly laminar raceway regime hydrodynamic contribution to average growth marginal; static average-light approximation reported <10% error in studied cases. HAL v2 is CC BY 4.0.

IMPORTANT_MODEL_SELECTION_CONCLUSION:
- hydrodynamic light histories matter strongly in some geometries/regimes (UAL tubular CFD/Gamma literature) but can be marginal in laminar raceways (Fierro2025).
- therefore `trajectory_resolved_light_required` must be a regime-dependent validation decision, NOT a universal architecture mandate.
- BLUECAD should support static/mean-light fast model + optional trajectory-resolved backend, selected by error criterion.

## 6 CAMACHO-RUBIO / BRINDLEY DYNAMIC PSU FAMILY
### 6.1 Camacho-Rubio 2003
MODEL=mechanistic dynamic photosynthesis/photoinhibition under variable/flashing/diurnal light; PSU state family {resting/open, activated/closed, inhibited}; stored-energy/activated state; Michaelis-Menten-type utilization; photoinhibition + repair; photo-adaptation concepts.
USE=foundational dynamic physiology reference.

### 6.2 Brindley 2016
Algal Research 16:399-408, DOI 10.1016/j.algal.2016.03.033; validates dynamic model for arbitrary real I(t), not only square-wave cycles; Scenedesmus almeriensis.
USE=bridge from synthetic flashing-light to actual hydrodynamic cell histories.

### 6.3 Brindley/Fernández-Sevilla 2018 reduced frequency characterization
Algal Research 35:479-487 DOI 10.1016/j.algal.2018.09.026; algebraic approximation when photoinhibition neglected; Muriellopsis example Pmax≈8.22e-7 molO2 g^-1 s^-1, alpha≈1.82e-4 mol photon m^-2 s^-1, beta≈15.3 s^-1, kappa≈0.0402, 25C. Numbers species-specific; use methodology not transfer.

## 7 SACCARDO/WOLF/HANKAMER/BEZZO 2024-2025 — HTS -> PSU MODEL -> PBR SCALE-UP
VALUE=S for experiment->parameter fit->dynamic light history->scale-up pipeline.
CODE_REPO=not found in current GitHub/web search.
LICENSE=Padova repo marks full text `Creative commons`; ResearchGate states CC BY-NC-ND 4.0 for 2024 paper. Until exact publisher/repository file license verified, classify RESEARCH_ONLY/CLEAN_ROOM science.

### 7.1 2024 CEJ 490:151684
Chlorella sp.; reformulates Camacho-Rubio for second-scale pulsed light; simultaneous PSU dynamics + biomass.
DATA=48 pulsed conditions calibration +16 continuous validation; OD750 error ~8% pulsed/~15% continuous; OD680/OD750 ~8%.
PDF machine-index excerpt provides equations but direct PDF open returned 403, so no visual screenshot verification possible in this audit; exact transcription should be rechecked before implementation.
INDEXED_CORE:
- total PSU `a_t` depends on photoacclimation/light through rate constants;
- growth `mu = k_p * [r_m*a2/(k_s+a2)] - M` (transcription from indexed PDF; VERIFY visually/source before coding);
- light phase dimensionless time tau=t/tc: `(1/tc) da2/dtau = k_a I (a_f-a2) - k_d a2`;
- dark: `(1/tc) da2/dtau = -k_d a2`;
- periodic boundary conditions; analytic a2,max/a2,min avoid second-scale numerical integration over long cultivation.

### 7.2 2025 Algal Research 89:104073
TITLE=`Scaling-up information from high-throughput pulsed light data to predict microalgae growth dynamics in photobioreactors`.
HIGHLIGHT=HTS pulsed-light calibration -> model individual-cell PBR light-history/mixing cycles -> validate scaled PBR simulation.
SUPPLEMENT_CONTENT_DECLARED={S1 HTS,S2 mathematical reformulation,S3 performance,S4 PBR equations,spreadsheet Sheet1 pulsed calibration+Sheet2 continuous validation}; data enclosed.
IMPLEMENTATION=parameter estimation in gPROMS v7.0.7 (commercial dependency for authors' fit; equations are independent scientific content).
FIXED_M≈0.01 h^-1; photoinhibition constant k_i≈1.85e-5 with paper-specific units; exact unit transcription must be checked.
FITTED_TABLE_FROM_INDEX:
- k_a≈1.5300e-4 m2 µmol^-1 ±5.7381e-5
- k_c≈0.0154 cell molPSU^-1 ±5.0040e-4
- k_d≈5.8286 s^-1 ±0.0951
- k_p≈0.1702 s cell h^-1 molPSU^-1 ±0.0390
- k_r≈5.4119e-5 s^-1 ±1.9407e-5
All are species/strain/setup-specific; use as regression for reproducing paper, not N.gaditana transfer.

BLUECAD_USE:
- excellent validation fixture for future dynamic-light model calibration pipeline;
- analytic within-cycle reduction is valuable architecture pattern: preserve fast long-timescale integration while retaining fast-light physics;
- use clean-room equations/data per applicable license, not copy code absent license.

## 8 INRIA/POLIMI SALINE IONIC SPECIATION MODEL — S-TIER SEAWATER FOUNDATION CANDIDATE
ORIGIN=2024 BIOCORE result; main subject of Annalisa/Analisa Reali master thesis, Politecnico di Milano, supervised Francesca Casagli + Olivier Bernard, ANR BARRIER.
PUBLIC_CODE/THESIS=not located in current search.
CLASS=CLEAN_ROOM/REFERENCE until source/license recovered.

SCIENCE:
- highly saline ionic equilibria using activities, not concentration-only approximations;
- includes ionic strength + ion-pairing;
- transforms ~40-unknown algebraic equilibrium system into 5-unknown differential-equation system;
- significant ion pairs selected using TotalEnergies pilot data + PHREEQC;
- MATLAB implementation;
- dedicated experiments + pH measurements at Laboratoire d'Océanographie de Villefranche;
- validation against experimental data + PHREEQC; report states good pH/ionic-strength/pairing/composition accuracy.

2025 ALBA extension confirms why this matters: saline ion-pairing materially changes pH and inorganic-carbon bioavailability; extended ALBA was validated in synthetic seawater with copper and pilot outdoor raceways with saline digestate.

BLUECAD_VERDICT:
- potentially more appropriate M1 seawater chemistry oracle than carbon-only CO2SYS because it handles nonideal ionic activities + pairing;
- do not replace TEOS-10/CO2SYS blindly: compare scopes. TEOS=water thermodynamics; CO2SYS=carbonate standard; this model=broader saline reaction/speciation.
- candidate architecture: `SeawaterState -> activity/speciation oracle -> DIC species/pH/free-ion activities -> biology/gas-transfer/precipitation`.

## 9 ALBA / ABACO FAMILY — PROCESS-MODEL REFERENCE ARCHITECTURE
### 9.1 ALBA 2021
ORG=Politecnico Milano + INRAE + INRIA.
VALIDATION=443 days original outdoor data; later independent multi-month/pilot validations.
MODEL:
- mass balances COD,C,N,P,H,O; stoichiometric/Petersen matrix verifies elemental/conservation constraints;
- algae + heterotrophs + AOB/NOB;
- Haldane-like photosynthesis + Beer-Lambert;
- Liebig/minimum multi-substrate limitation C/N/P;
- pH acid/base equilibria + ionic-species balances (ADM1-derived in original);
- CO2,NH3,O2 gas transfer via kLa;
- Cardinal pH Model; Cardinal Temperature Model with Inflection; Arrhenius decay;
- weather/light/T forcing.
SUPPLEMENT=complete ALBA description, kLa experiment, parameter uncertainty/error propagation, weather, pH/alkalinity etc publicly listed by ACS paper.
ARTICLE LICENSE=ACS page indicates CC terms permitting commercial sharing/adaptation with attribution for that article; exact SI license should still be checked separately before data reuse.

### 9.2 Recent hybrid/JAX work
2024 BIOCORE reports hybrid mechanistic+ANN ALBA method preserving mechanistic constraints while learning data-dependent parts; calibrated/validated pilot-scale; implemented as Python package based on JAX. Public package/repository not found yet.
VALUE=strong architecture candidate for future BLUECAD `mechanistic core + learned residual/submodel` while preserving mass balances/positivity/bounds.

### 9.3 ABACO-2
2024 Water Research 248:120837, UAL/INRIA/Padova-linked consortium model, outdoor pilot-scale validation. Deep audit pending.
VALUE=potential modern competitor/reference to ALBA for consortia; less immediate for pure N.gaditana BlueRev but useful IR/process-model architecture.

## 10 UAL2014 EQ2 STATUS
ACS open page machine-retrieval confirms model context/parameter table but equation rendering remains inaccessible in exact text through current retriever; prior session identified Eq2 structure as photosynthesis combining irradiance, photoinhibition, dissolved-O2, pH, temperature, respiration. DO NOT persist an unverified exact algebraic transcription. Need screenshot/visual audit from accessible PDF before implementation.

## 11 NEW DECISION MATRIX
PBR_PROCESS_CORE:
- In@lgae architecture: S reference; code/license GAP.
- MGM/Fierro: S scientific/digital-twin reference; deliverable/source recovery pending.
- UAL M1/M2: S validated process-model equations/reference.
- ALBA: A+/S architecture for stoichiometric balance/speciation/gas transfer; pure-alga scope adaptation needed.
DYNAMIC_LIGHT:
- N.gaditana Nikolaou/Bernardi: species-specific science.
- Han/Fierro: analytically tractable mechanistic dynamic-light route.
- Camacho/Brindley/Saccardo: PSU/HTS route with real light-history support.
SEAWATER:
- TEOS/CO2SYS standards remain oracle boundaries;
- INRIA/Reali saline speciation promoted S reference candidate because nonideal activity/ion-pairing directly relevant.
LAB_EXECUTION:
- ODIN+ promoted A+/S architecture reference pending source/license.
HYDRO_TRAJECTORY:
- Freshkiss3D promoted A+ candidate for free-surface/raceway trajectories; closed-tube relevance lower; license/access unresolved.

## 12 NEXT SEARCH
P0 recover Fierro thesis/HAL/MGM deliverable and any source/package.
P0 locate In@lgae source/archive/license or prove unavailable.
P0 ODIN source/license; compare architecture vs Jarvis plant/lab execution.
P0 locate Reali thesis/Matlab saline model or follow-up publication/source.
P0 locate JAX hybrid ALBA package and ABACO-2 supplementary/source.
P1 visually audit Saccardo supplementary/PDF if accessible and collect spreadsheet data/license.
P1 exact UAL lumped model equations + UAL2014 Eq2 via accessible visual source.
P1 compare dynamic-light model families using same benchmark/trajectory: Han vs Camacho/Saccardo vs Nikolaou/Bernardi; choose backend by accuracy/state-cost/identifiability.
