# BLUEREV PBR DISCOVERY CONTINUATION — 2026-08-20

FORMAT=AI_FIRST; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; PREVIOUS=BLUEREV_PBR_DISCOVERY_2026-08-20.md

## 0. DELTA SUMMARY

NEW_HIGH_VALUE={UAL/CIESOL simulator+model ecosystem, exact M0-ish N.gaditana parameters from Palermo2022, optical-property state-dependence evidence, TUM/OpenFOAM reproducible CFD benchmark, UAL outdoor tubular CO2/pH validation datasets}
ARCHITECTURE_CHANGE=YES: UAL literature provides explicit validated reduced-vs-distributed model hierarchy matching BLUECAD multifidelity plan.
LICENSE_CHANGE=YES: current UAL RacewaySim explicitly CC BY-NC-SA 4.0 => RESEARCH_ONLY/reference, not DIRECT.

## 1. TUM THIN-LAYER CASCADE OPENFOAM BENCHMARK

SOURCE=Severin T.; Brück T.; Weuster-Botz D. "Validated numerical fluid simulation of a thin-layer cascade photobioreactor in OpenFOAM", Eng Life Sci, 2019 (online 2018), DOI 10.1002/elsc.201800097; PMCID PMC6999291.
VALUE=A+/S validation/reference for hydrodynamics + future cell light-history coupling.

MODEL:
- OpenFOAM 2.3.x `interFoam`: transient two-phase water/air free-surface CFD.
- authors modified solver into `interSpeciesFoam` to transport passive dissolved species/tracer.
- validated against experimental fluid height, velocity, conductivity/salinity tracer response.
- representative geometry: inlet width ~0.83 m; channel width ~1 m; length ~4 m; fluid layer <~1 cm.
- representative meshes: inlet tank ~2e6 cells; channel ~1.56e6 cells.
- reported sensitivities/validation order: fluid height mesh sensitivity ~3%; weir velocity ~10%; measured-vs-CFD max velocity deviation ~6%; fluid-height deviation <~2%; Manning-style cross-check ~12%.

REPRODUCIBILITY_CRITICAL:
- paper supplementary information exposes complete adjustable OpenFOAM cases, STL geometry, tracer-validation assets, MATLAB post-processing; SI includes ~14.8 MB ZIP + ~162 KB ZIP + PDF.
- authors explicitly identify future extension: radiative transfer + Lagrangian algae particles -> individual light/flow histories.

LICENSE:
- OpenFOAM GPL => solver/runtime EXTERNAL.
- supplementary package license not yet located/audited. Availability != reuse license. Treat SI code/data CLEAN_ROOM/EXTERNAL reference until explicit grant.

BLUECAD_USE:
1. hydrodynamic validation oracle / regression fixture if data licensing permits;
2. architecture reference for CFD->Lagrangian trajectories->light histories;
3. do NOT make full-loop CFD baseline; use local high-fidelity sections and derive reduced correlations/surrogates.

UNRESOLVED=download/extract SI; identify exact license; inspect interSpeciesFoam patch and case structure; determine whether passive-species solver code is separately licensed.

## 2. N. GADITANA OPTICAL PROPERTIES ARE STATE-DEPENDENT

### 2.1 Markerless trait-stacking / FIRe methodology
Open literature on Nannochloropsis gaditana reports:
- absorption spectra measured with integrating sphere;
- chlorophyll-specific absorption cross-section `a_chl` derived from OD/Chl;
- functional PSII absorption cross-section `sigma_PSII` measured by FIRe at multiple excitation colors;
- source-weighted optical cross-sections obtained by weighting spectral OD/absorption by illumination spectrum.

VALUE=methodology for intrinsic/spectral optical characterization; supports future experimental schema.

### 2.2 Nitrogen-starvation/photoacclimation evidence
Wageningen/Janssen-line studies report strong dry-weight-specific optical cross-section changes with physiological state:
- approximately 176 ± 19 -> 29 ± 1.7 m²/kg over first ~5 days N starvation in one study;
- Fv/Fm approximately 0.67 -> 0.40;
- photon-supply study initial optical cross-sections around 116 m²/kg under high biomass-specific photon supply vs ~275/281 m²/kg low/intermediate photon supply.

DECISION:
- NEVER model a fitted extinction/attenuation coefficient as universal species material constant.
- IR should distinguish:
  `intrinsic_spectral_absorption/scattering(state,lambda)`;
  `biomass_specific_optical_cross_section(state,spectrum)`;
  `effective_reactor_attenuation(geometry,mixing,state,spectrum,fit_dataset)`.
- M0 may use one effective coefficient but metadata must state reactor geometry, spectrum, physiological state, fitting source, confidence/domain.

## 3. PALERMO 2022 — DIRECT M0 PARAMETER SOURCE

SOURCE="Modelling Nannochloropsis gaditana Growth in Reactors with Different Geometries...", Applied Sciences, 2022.
EXPERIMENT:
- quasi-isoactinic flat PBR ~4 mm optical depth;
- 25 °C;
- incident photon levels 20, 50, 100, 140, 210, 300, 450 µmol photons m^-2 s^-1 (paper writes µE-equivalent units);
- growth model fitted to light saturation; tested range considered below significant photoinhibition.

PARAMETERS:
- mu_max = 0.0256 h^-1 ≈ 0.61 d^-1
- I_K = 15.28 µmol photons m^-2 s^-1
- k_d = 0.0046 h^-1
- fitted attenuation k_a = 0.38 m²/g for flat reactors
- fitted attenuation k_a = 0.20 m²/g for annular reactor

OBSERVED_SPECIFIC_GROWTH_RATES_H-1:
20 -> 0.0117
50 -> 0.0184
100 -> 0.0228
140 -> 0.0237
210 -> 0.0249
300 -> 0.0246
450 -> 0.0243

VALIDATION_GEOMETRIES≈flat15mm; flat30mm; annular35.5mm.

DECISION:
- excellent first numerical regression fixture for M0.
- use growth-rate table as data points, not only fitted parameters.
- geometry-dependent fitted `k_a` is direct evidence for optical-property semantic split in §2.
- not enough to parameterize photoinhibition because tested range did not show strong inhibition; use Pfaffinger/high-light dataset for Ki/Iopt.
- equations may be clean-room reimplemented from scientific publication; no source-code license/repo found yet.

## 4. PFAFFINGER/TUM — HIGH-LIGHT N. GADITANA KINETICS

SOURCES=Pfaffinger et al. 2016 Algal Research "Model-based optimization..."; Pfaffinger thesis 2017; 2019 J Biotechnology "Light-dependent growth kinetics enable scale-up...".

KNOWN:
- N. gaditana SAG 2.99 + N. salina studied;
- flat-plate gas-lift optical depth ~2 cm;
- photon flux experiments extend to ~2750 µmol m^-2 s^-1, enabling identification of limitation/optimum/photoinhibition rather than saturation only;
- model uses mean integral photon-flux density and a photoinhibition-type kinetic relation plus extinction coefficient;
- optimized radiation profiles improve biomass/lipid productivity;
- scale-up work transfers mean-integral PFD kinetics to ~8 m² thin-layer cascade.

IMPORTANT_DYNAMIC_CAVEAT:
- later work shows day/night or dynamic illumination changes apparent kinetics; stationary light-growth kinetics are insufficient for realistic outdoor transient operation. M0 may be stationary; M1 must represent dynamic physiology/light history.

UNRESOLVED=extract exact parameter table from thesis/paper: epsilon, mu_max, K_s/K_I or equivalent, I_opt, maintenance/decay; PDF must be visually inspected when retrieved.

## 5. UAL/CIESOL / GUZMÁN-ACIÉN ECOSYSTEM — S-TIER SOURCE

WHY_S=closest discovered open/public research ecosystem to desired BLUECAD PBR function: validated outdoor photobioreactor models + virtual labs + controls + real plant data + current digitalization projects.

### 5.1 Public simulator suite
José Luis Guzmán / UAL pages expose multiple microalgae simulators/tools:
1. production-capacity map;
2. online raceway virtual simulator;
3. interactive biological-model tool;
4. Matlab-based dynamic raceway PBR simulator.

SABANA data center describes:
- free downloadable biological model tool (Win/Mac);
- inputs including time,pH,DO,temperature,solar radiation;
- Matlab raceway simulator for whole dynamic behavior;
- open-loop seasonal-data operation;
- closed-loop on/off/PID/selective pH and dissolved-O2 control;
- balances along time AND space;
- Matlab App + standalone packages.

DISCOVERED_DOWNLOADS:
- `Reactor-Simulation-Tool.mlappinstall.zip`
- `Biological_Model_Win.zip`
- current `raceway_virtual_lab.zip`
Runtime environment could identify URLs but did not retrieve packages yet. Need local/package audit later.

### 5.2 RacewaySim current virtual lab
AUTHORS=José García Gallardo; José Luis Guzmán; Enrique Rodríguez; Francisco Gabriel Acién.
TECH=Easy Java/JavaScript Simulations (EJS 6.0); offline package available; results can be exported ASCII.
FEATURES:
- arbitrary microalgae strain through biological parameters;
- solar model for arbitrary geographic location;
- manual/automatic dilution/harvesting;
- pH and DO control;
- user-facing dynamic reactor experiment environment.
LICENSE=CC BY-NC-SA 4.0 => RESEARCH_ONLY/reference, NOT commercial embed/copy.
VALUE=S UI/model-decomposition/validation oracle despite license.

### 5.3 2014 tubular-PBR virtual lab
REAL_PLANT_REFERENCE=Las Palmerillas/CAJAMAR, Almería.
FACILITY≈10 tubular fence-type PBRs.
PER_PBR≈400 m tube length; 0.09 m tube diameter; bubble column ~3.5 m high, 0.4 m diameter.
ARCHITECTURE:
- tubular loop = solar receiver; modeled as plug-flow/distributed differential elements, number of elements user-adjustable;
- bubble column = mixed/degassing/heat-exchange section; approximated CSTR/perfect mixing;
- liquid O2 balance = gas transfer + photosynthetic production;
- biomass growth tied to photosynthetic rate;
- inorganic-carbon balance;
- gas-phase O2 + CO2 balances;
- outputs/states include DO,pH,biomass,T,total inorganic carbon,gas O2/CO2 fractions,CO2 loss;
- photosynthesis includes dissolved-O2 inhibition;
- actuator dynamics identified from plant: cooling valve first-order+delay; CO2 valve first-order with zero; circulation pump second-order;
- UI exposes geometry, location/solar profile, pH,biomass,DO,CO2,circulation,T,harvesting/control.
LIMITATION_OLD=horizontal solar radiation assumption/no arbitrary tube tilt.

VALUE=direct benchmark for desired BLUECAD tubular-PBR system decomposition.
LICENSE_NOT_ASSUMED: EJS engine open source does not imply model/app permissive. Current RacewaySim NC-SA suggests conservative RESEARCH_ONLY/reference until exact package license found.

## 6. UAL VALIDATED TUBULAR MODEL HIERARCHY — ARCHITECTURE-CHANGING FINDING

### 6.1 Distributed first-principles model
KEY_SOURCES:
- 2012 Bioresource Technology 126:172–181, "Dynamic model of microalgal production in tubular photobioreactors".
- 2014 Industrial & Engineering Chemistry Research 53(27):11121–11136, "First Principles Model of a Tubular Photobioreactor for Microalgal Production".

CAPABILITIES:
- fundamental/dynamic model;
- fluid/mass transfer/biology;
- spatial + temporal gradients;
- DO,CO2,photosynthesis,biomass;
- gas O2/CO2,CO2 losses,pH,T;
- calibration + validation against real outdoor pilot tubular PBR ~3.0 m³;
- can reveal local harmful pH/O2/CO2 gradients;
- intended design/operation/control; 2014 model includes temperature dynamics.

BLUECAD_ROLE=HIGH_FIDELITY_1D_DISTRIBUTED_ORACLE/M2 before CFD.

### 6.2 Lumped nonlinear model
SOURCE=2014 Chemical Engineering Science 112:116–129, "A lumped parameter chemical–physical model for tubular photobioreactors".
PURPOSE=reduce distributed model complexity while preserving nonlinear behavior for optimization/control.
VALIDATED=real outdoor tubular data; compared against distributed/linear/NARMAX approaches.
BLUECAD_ROLE=FAST_M1/MPC/optimization model.

### 6.3 Explicit multifidelity precedent
Later hierarchical-control UAL work uses:
- distributed first-principles PDE model as high-fidelity "real process" simulator;
- lumped ODE model inside computational optimization loop to derive optimal pH reference.

DECISION=strong independent precedent for BLUECAD architecture:
M0 simple empirical growth/light -> M1 lumped process model -> M2 distributed 1D first-principles -> M3 local CFD/optical high fidelity.
Do not jump directly M0->3D CFD.

## 7. UAL N. GADITANA OUTDOOR CO2/pH VALIDATION DATA

### 7.1 pH study
SYSTEM=outdoor tubular PBR ~3.0 m³, N. gaditana; pH 6–10 controlled via pure CO2 on demand.
REPORTED:
- optimum near pH~8;
- biomass productivity ~0.16 g L^-1 d^-1;
- CO2-use efficiency ~74.6%;
- CO2 consumed/biomass ~2.42 g/g, near theoretical stoichiometric requirement.
USE=M1 carbon/pH validation fixture.

### 7.2 CO2 flow-rate study
CONDITIONS include artificial seawater ~30 g/L NaCl + fertilizer formulation; diel DO/T/pH measured.
REPORTED optimum CO2-specific flow order ~1.9 mL CO2 L_culture^-1 min^-1.
USE=gas-transfer/control calibration + sanity bounds.

RELATED_REFERENCES:
- N. oculata pH-profile/carbonate-equilibrium + overall CO2 mass-transfer work estimates stripping/consumption;
- Tamburic et al. continuous pH/DO diel monitoring demonstrates carbon limitation/gas-transfer importance;
- 2022 ACS carbon-transfer/growth model includes online kLa;
- 2026 Nannochloropsis pH-stat/pulsed-CO2 strategy is a current follow-up candidate.

## 8. UAL CURRENT PROJECTS — DISCOVERY ROUTES

DIGITALGAE/DigitAlgaesation: microalgae digitalization, light conversion, AI/model-based control; UAL + University of Padova.
HYCO2BIO: hybrid/data-driven control optimization.
AUTOALGAE (2025/2026 current): industrial-scale automation/process optimization with Biorizon.
NAMOR and related current projects: search authors/repositories/data, not just project pages.

DECISION=systematically crawl authors/project outputs {Guzmán,Acién,Fernández,Rodríguez,García Gallardo,Padova collaborators} for code/data/theses/supplementary packages.

## 9. UPDATED BLUECAD PBR MODEL LADDER

M0_EMPIRICAL:
X(t); effective light attenuation; light saturation/photoinhibition; decay; constant carbon/nutrients/T where justified. Validation={Palermo growth table + Pfaffinger high-light parameters/data}.

M1_LUMPED_PROCESS:
well-mixed/segmented reactor states={X,DIC/pH,DO,gas CO2/O2,T,nutrient optional}; gas transfer; photosynthesis; O2 inhibition; pump/CO2/cooling actuator dynamics; effective optics. Reference=UAL lumped model + current N.gaditana data.

M2_DISTRIBUTED_1D:
tubular loop axial cells/PFR + mixed degasser/bubble column; local irradiance; local DO/DIC/pH/T/X; circulation; external gas-liquid transfer. Reference=UAL 2012/2014 first-principles model.

M3_LOCAL_HIGH_FIDELITY:
MCRT/general 3D radiative transfer; local CFD of U-bends/degasser/thin layers; Lagrangian trajectories/light histories; wave-varying geometry/orientation; fouling spatial field.

PROMOTION_RULE=only increase fidelity when lower model fails validation/decision robustness or when design question requires unresolved spatial/time-scale physics.

## 10. NEXT SEARCHES

P0 extract exact UAL 2012/2014 equations, parameter tables, code/supplements/license.
P0 extract exact Pfaffinger high-light kinetic parameter table via thesis/PDF visual audit.
P0 locate downloadable source/package contents for UAL virtual labs and inspect license/code/model files.
P1 locate raw N.gaditana optical spectra/cross-section datasets and state variables.
P1 locate Lagrangian cell-trajectory/light-history implementations for tubular PBRs.
P1 locate carbonate+kLa+growth source implementations/datasets suitable for seawater Nannochloropsis.
P2 update mechanical audit after PBR foundation reaches diminishing returns.
