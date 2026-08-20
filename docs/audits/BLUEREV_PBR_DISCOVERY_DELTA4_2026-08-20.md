# BLUEREV PBR DISCOVERY DELTA4 — 2026-08-20
FORMAT=AI_FIRST; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; PREVIOUS={BLUEREV_PBR_DISCOVERY_2026-08-20.md,CONTINUATION,DELTA2,DELTA3}

## 0 DELTA
NEW_S_TIER={UAL 2026 benchmarkmicroalgae public repo; Pyomo.DoE direct MBDoE backend; DigitAlgaesation ESR5 robust model-discrimination prototype; ESR9 mass-balance sensor architecture; ESR15 adaptive/weather-aware control; ALBA-vs-ABACO2 cross-dataset benchmark; INRIA shape/mixing optimization precedent}.
PIPPO_IMPACT=HIGH for {control benchmark interface, experiment-design stack, measurement schema}. Physical UAL benchmark core remains opaque/unlicensed -> oracle not production backend.

## 1 UAL 2026 `guzmanjl/benchmarkmicroalgae` — CODE-FIRST AUDIT
PAPER=Rodríguez-Miranda/Otálora/González-Hernández/Guzmán/Berenguel, `A comprehensive benchmark platform for process control research of outdoor microalgae raceway reactors`, Control Engineering Practice 174 (Sep 2026 issue), article 107027, DOI 10.1016/j.conengprac.2026.107027. Preprint arXiv 2512.15916 dated 2025-12-17. Peer-reviewed article already available online/open access as of 2026-08-20 despite issue month being future.
REPO=https://github.com/guzmanjl/benchmarkmicroalgae; public; current audit root size ~7.6MB.
SPECIES_DEFAULT=Scenedesmus almeriensis, NOT N.gaditana; process/control architecture transferable, species params not.

### 1.1 Scope
Four coupled regulation tasks:
- pH via CO2 injection;
- DO via air bubbling;
- biomass/culture volume via coordinated harvest+dilution;
- T via spiral heat exchanger.
Plant model described as experimentally calibrated high-fidelity dynamic thermal+physicochemical+biological model; realistic actuator saturations, gas transport FIFO delays, stiff ODE integration, multi-day irradiance/T/RH/wind disturbances; baseline OnOff/PI/PID/EMPC; global performance combines tracking+control effort/resource use+biomass productivity.
IFAC World Congress 2026 benchmark challenge selected.

### 1.2 Repository exact structure
ROOT:
- `Data_Benchmark.mat` ~391593 bytes;
- `simulate_benchmark_model.p` ~7002 bytes MATLAB p-code;
- `load_data.m`;
- `show_results.m`;
- `player/` user examples;
- `IFAC_WC_player/` competition materials;
- `README.md`.
NO LICENSE file in root listing; GitHub code search for `license` returns none. README says "Licensing information is provided in repository" but audit cannot locate it. Therefore CODE_LICENSE=UNSPECIFIED. Paper CC/open access != software license. CLASS=CLEAN_ROOM/REFERENCE until explicit software license is added/obtained.

### 1.3 Critical opacity
Core process simulator distributed as `simulate_benchmark_model.p` MATLAB p-code, not `.m` source. Therefore:
- cannot inspect physical equations/bugs numerically from repo;
- cannot verify advertised high-fidelity implementation against paper source;
- cannot port/modify/audit for safety;
- executable benchmark still useful as black-box oracle if MATLAB available.
This alone prevents DIRECT production adoption even if future license becomes permissive unless source is released or black-box boundary is desired.

### 1.4 Data/interface
`load_data.m` expects `Data` array of daily structs:
- Date/t minute axis;
- u1 global solar W/m2;
- u2 PAR µE/m2/s;
- u3 ambient T C;
- u4 RH %;
- u5 wind m/s.
`Data_Benchmark.mat` is valid MATLAB 5.0 file (header visible through base64 fetch); full binary semantics not decoded in connector audit. No need to infer hidden variables.

`player/Benchmark_main.m` is minimal deterministic harness (`rng(42,'twister')`) selecting four controller function handles -> `simulate_benchmark_model(Data,ctrl)` -> `show_results`.

### 1.5 Controller contract — HIGH VALUE
Example pH function signature:
`[st_CtrlSignals,state] = controller_pH_OnOff(Timeline,obs,refs,env,future,st_CtrlSignals,state)`
Input schemas documented:
Timeline={dt,index,time,time_secday,hour,min}
obs={pH,DO,Depth,Xalg_gL,T}
refs={pH,DO,T}
env={RadGlobal,RadPAR,Temp_ext,RH,Wind}
future={t_future,RadGlobal,RadPAR,Temp_ext,RH,Wind} forecast trajectories
state=persistent arbitrary controller state/tuning
actuator outputs={Qco2,Qair,Qd_bin,Qh_bin,Qhx,Tin_hx}
Plant applies saturation/delay outside controller.

BLUECAD/JARVIS REFERENCE CONTRACT:
`ControlStep(time, observation, reference, environment, forecast, controller_state, actuator_state) -> proposed_actuation + new_controller_state`
Jarvis authority/safety should sit AFTER proposed actuation and BEFORE plant adapter; controller should not directly own hardware side effects. Forecast is first-class, not hidden global.
This contract is more reusable than the benchmark's physical model.

### 1.6 Outputs
README exposes structured results including:
pH,DO,T,X,Depth; command/delivered gas; dilution/harvest; cumulative CO2/air/biomass; productivity/harvest metrics; light/T/pH/DO growth limitation factors; gross P/net µ/maintenance; DIC,strong cation,HCO3,CO3,CO2; HX Q/Tin/Tout/UA/Q/limits.
This output schema is an excellent target for BLUECAD M1/M2 result semantics/regression fixtures.

### 1.7 Quality limits
- no visible automated tests/CI/test vectors in root/player listing during audit;
- deterministic harness helps reproducibility but p-code prevents equation-level unit tests;
- MATLAB dependency; no additional toolboxes claimed;
- software licensing inconsistency must be resolved before any reuse.

VERDICT=S_ORACLE_CONTROL_BENCHMARK; NOT_DIRECT_BACKEND.
ACTION=future: request/monitor explicit license + source `.m`; create BLUECAD adapter only as external black-box oracle if useful; reproduce public paper equations independently if needed.

## 2 PYOMO.DOE — DIRECT GENERAL MBDoE BACKEND
REPO=Pyomo/pyomo; current main; LICENSE=revised BSD-style permissive; DIRECT.
MODULE=pyomo.contrib.doe; maintained documentation current 6.10.1; extensive tests present including build/errors/solve/greybox/initialization.
PURPOSE=science-based model MBDoE; Experiment abstraction; dynamic models; multiple experiments; parameter uncertainty; FIM objectives; direct optimization/enumeration; integrates Pyomo ecosystem/Parmest.
CURRENT_LIMIT=official docs explicitly say focus is increasing parameter precision; NOT general rival-model discrimination currently.

PIPPO_VERDICT:
- do NOT implement generic Fisher-information MBDoE foundation ourselves;
- candidate DIRECT backend for parameter-precision design and common experiment schema;
- extend/wrap with model-discrimination criteria only where missing;
- compare integration cost vs BoFire/pyPESTO, but roles differ: Pyomo.DoE is first-principles experiment design, pyPESTO PE/UQ, BoFire broader DoE/BO.

BLUECAD experiment abstraction can map:
`experiment_inputs, experiment_outputs, measurement_error, unknown_parameters, design bounds/time grid/prior information` -> backend-specific model.

## 3 DIGITalGAESATION ESR5 — ROBUST MODEL DISCRIMINATION PROTOTYPE
PUBLIC_DESCRIPTION=2024 Marco Sandrin blog/project output; direct public code repo not found.
STACK=Python + Pyomo.DAE + SUNDIALS integrators + SciPy trust-region.
USER_CAN_PROVIDE=>=2 dynamic models; design variables can include experiment duration, ICs, constant/time-varying inputs, measurement sample times.
UNCERTAINTY=scenarios from prior distribution/space-filling.
CRITERIA_IMPLEMENTED:
- worst-case information;
- expected-value information;
- CVaR/tail-risk design.
Goal=maximize divergence among rival model predictions, unlike FIM parameter-precision objective.
Reported tested/promising; future parallel experiment campaigns.
CLASS=CLEAN_ROOM/reference until source published.

ARCHITECTURE_DECISION:
`BLUECAD MBDoE service = Pyomo.DoE DIRECT common foundation + optional model-discrimination plugin implementing robust divergence/CVaR inspired by ESR5 literature`, unless Sandrin source later becomes available permissively.
Avoid making MAGNUS full stack default merely because it has MBDoE.

## 4 DIGITalGAESATION ESR6/9/15 — EXPERIMENT+MEASUREMENT+CONTROL SCHEMA
### ESR6 continuous micro-PBR
Goal hardware designed for rapid model identification:
- multiple concentration gradients;
- long-term culture;
- different T + complex light dynamics;
- HTS many replicates;
- online imaging/standard analytics;
- fast dynamic environmental signals.
VALUE=reference hardware spec for BLUECAD automated identification bench. No public code audited yet.

### ESR9 Wageningen sensor fusion
Project explicitly targets online mass balancing using:
- CO2 consumption;
- O2 production;
- biomass production;
- nitrogen consumption;
plus PAM fluorescence + VIS absorption spectroscopy.
WUR follow-up adds charge/pH-derived nitrogen uptake, T/salinity, automatic sensor drift recalibration, lab-workflow automation and pilot scale.

BLUECAD `MeasurementSchema` candidate minimum fields:
raw sensor + unit + timestamp + calibration state + uncertainty/drift;
CO2 in/out/use rate; O2 production/DO; biomass estimate; N uptake/speciation; pH; T; salinity/conductivity; PAM fluorescence; VIS spectrum; optional imaging/flow cytometry.
Derived mass-balance estimates must retain provenance from raw sensors.

### ESR15 Ali Gharib / weather-aware control
2024 SATHE `Adaptive temperature model for microalgae cultivation systems`:
- simplified auto-tuning heat exchange model derived from comprehensive models;
- identifiable minimal parameter set;
- online use;
- self-retunes using last days of T measurements;
- demonstrated across seasons/reactor configurations;
- reports better robustness than more complex fixed model especially winter.
2024/2025 BIOCORE reports SATHE integrated into optimal control/MPC; culture depth affects thermal inertia; future weather forecasts materially improve control efficiency.
2025 validation extends to closed cultivation systems.

DECISION=temperature submodel should be replaceable/adaptive; do not freeze one full heat-transfer parameter set as truth. Forecast-aware controller contract from UAL benchmark aligns directly with this lineage.

## 5 ALBA vs ABACO-2 CROSS-DATASET BENCHMARK 2025
PAPER=Nordio/Casagli/Rodríguez-Miranda/Guzmán/Bernard/Acién, Algal Research 89 (2025) 104049.
METHOD=exchange original validation datasets:
- ALBA Narbonne: 56m2/~17m3, synthetic municipal wastewater, 443d;
- ALBA Milan: 3.8m2, liquid digestate;
- ABACO-2 Almería: 80m2, untreated urban wastewater;
run both models across all 3.
RESULT_DIRECTION from publisher section snippets:
- both retain good predictive capacity despite structural differences;
- ABACO-2 stronger biomass-concentration prediction overall but winter can improve;
- ALBA stronger nitrogen evolution + bacterial/BSMO-related tracking;
- ABACO-2 simplified nitrification can limit NH4 dynamics;
- model purpose/objective drove state/process choices and performance.
CONCLUSION=NO_UNIVERSAL_WINNER; applicability depends on climate, medium, reactor, objective; main scale-up blockers data management/calibration/monitoring.

BLUECAD_DECISION=store rival models + validity domains + objective-specific scorecards; model promotion is conditional on engineering question/domain, not global crown. Cross-dataset validation should be native workflow.

## 6 LIGHT-HISTORY ML 2023 — MECHANISTIC CORE + LEARNED HISTORY
PAPER=`Improving microalgae growth modeling of outdoor cultivation with light history data using machine learning models: A comparative study`, Bioresource Technology 390 (2023) 129882; Fraunhofer/partners.
COMPARE=Monod/Haldane vs SVR/LSTM; outdoor ~50d; ML explicitly consumes prior ~12h light history.
DATA/FULLTEXT=Zenodo record indexed but embargoed until 2027-06-23; no usable public training package today.
VERDICT=REFERENCE; not reason to replace M0/M1 with black-box ML.
ARCHITECTURE=optional learned residual/history encoder around mechanistic state model; physics fallback remains executable without ML; training provenance/domain required.

## 7 INRIA SHAPE/MIXING OPTIMIZATION — BLUECAD DESIGN LOOP PRECEDENT
2025 SIAM J Control Optim `Topography Optimization for Enhancing Microalgal Growth in Raceway Ponds`: Han biology + Saint-Venant hydrodynamics + bottom topography optimization via weak maximum principle; in periodic regime flat topography satisfies necessary condition and numerical experiments find flat optimal; nontrivial topography can help under alternative/mixing-device scenarios.
Earlier arXiv variants/mixing work consider layer permutation/mixing device and exploit periodic steady cycling to reduce repeated-lap computation.

BLUECAD DESIGN CONTRACT:
`DesignVariable(geometry/operation) -> geometry compiler/backend -> hydro/light/biology solver -> engineering objective+constraints -> optimizer -> verification`.
IMPORTANT=optimization may prove added geometric complexity useless; system must be allowed to recommend simpler design.
No public GitHub code found in current audit => CLEAN_ROOM reference.

## 8 NEW UAL CONTROL RESEARCH ROUTES
2026 UAL/AQUACONTROL listings also expose:
- Economic MPC for industrial microalgae production;
- experimental extremum-seeking control in semi-industrial raceway ponds;
- 3DoF-KF model-on-demand MPC for pH;
- IoT heterogeneous data integration platform (2025).
These are high-value follow-up routes for Jarvis plant execution after physical PBR model core; not yet code-audited.

## 9 UPDATED DECISIONS
CONTROL_BENCHMARK=`benchmarkmicroalgae` S ORACLE; cannot DIRECT due no software license + p-code core.
CONTROL_INTERFACE=adapt/generalize UAL contract as candidate BLUECAD/Jarvis pattern, with Jarvis authority between proposed command and actuator.
MBDOE=Pyomo.DoE DIRECT baseline; robust model-discrimination missing piece inspired by ESR5 or source if later found.
MEASUREMENT_SCHEMA=ESR9 mass balance + spectroscopy/PAM first-class.
TEMPERATURE=SATHE/adaptive reduced model pattern A+/S; online re-identification should be supported.
MODEL_SELECTION=cross-dataset/objective/domain score, not one canonical equation.
DESIGN_OPTIMIZATION=geometry can be an optimization variable, but complexity must justify measurable gain.

## 10 NEXT
P0 code-first inspect UAL benchmark commit history/issues/IFAC challenge as future oracle; monitor license/source release.
P0 search Pyomo.DoE extension ecosystem for model discrimination/CVaR before writing plugin.
P0 locate Marco Sandrin prototype repo/thesis/paper/source.
P0 audit UAL 2026 EMPC/extremum-seeking/model-on-demand + 2025 IoT platform for code/license; possible Jarvis lab/control integration.
P1 recover MGM/In@lgae/Reali saline code/deliverables.
P1 benchmark dynamic-light model families.
P2 once PBR software discovery reaches diminishing returns, resume mechanical/wave/fatigue search.
