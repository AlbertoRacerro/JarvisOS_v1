# BLUEREV CONTROL/AI DISCOVERY DELTA5 — 2026-08-20
FORMAT=AI_FIRST; AUTHORITY=AUDIT_ONLY; IMPLEMENTATION_AUTHORIZED=NO; CONTEXT=PBR discovery control/telemetry/AI layer.

## 0 DELTA
NEW_HIGH_VALUE={UAL FIWARE IoT architecture; UAL 3DoF-KF MoD MPC; UAL extremum seeking; UAL economic MPC; industrial PBR behavior-cloning RL; OptiMaL CIRL MIT code audit; PC-Gym MIT code audit; multi-fidelity bioprocess BO open-code claim}. 
PIPPO_VERDICTS={PC-Gym=ADOPT_CANDIDATE_DIRECT; CIRL=IDEA/PARTIAL_NOT_WHOLESALE; exact PBR-RL=REFERENCE_NO_CODE; UAL controllers=REFERENCE unless code found; UAL IoT=REFERENCE architecture/no source found}.

## 1 UAL FIWARE IOT PLATFORM 2025
PAPER=Muñoz/Torres/Gil/Guzmán, J Network Computer Applications 240 (2025) 104197, DOI 10.1016/j.jnca.2025.104197.
ZENODO=record 15337470; only article PDF found; Zenodo file license CC BY 4.0. No source/deployment package in record.
ARTICLE_ABSTRACT_ARCH:
- agro-industrial IoT platform;
- interoperability core;
- open technologies;
- OMA NGSI interoperable data model within FIWARE;
- scalable integration of heterogeneous devices/scenarios;
- industrial models (climate/production etc.) encapsulated as services;
- ETL for heterogeneous data;
- cloud load testing concurrent requests/resource use;
- validated in three scenarios.
SECURITY_LIMITS article mentions DDoS, firmware-update security, identity spoofing as continuing challenges.
CLASS=REFERENCE; source repo/deployment not found. Paper license != software license.

BLUECAD/JARVIS TAKE:
- `DeviceAdapter -> canonical measurement/event schema -> NGSI-like context entities -> model services` is useful interoperability pattern;
- do NOT let FIWARE become authority/canonical engineering truth by default;
- compare FIWARE components against Jarvis native event/state architecture if/when implementation authorized;
- ETL/protocol adapters may be external, canonical engineering provenance remains Jarvis.

## 2 UAL 3DoF-KF MODEL-ON-DEMAND MPC 2026
PAPER=Otálora/Banerjee/El Mistiri/Khan/Rivera/Guzmán, CEP168 (Mar2026) 106742; DOI 10.1016/j.conengprac.2025.106742. Zenodo record 18246257 contains PDF only, CC BY 4.0 file; no code/data package found.
METHOD:
- pH control in microalgae raceway;
- Three-Degree-of-Freedom MPC + real-time Model-on-Demand (MoD) local data-driven estimation;
- database generated with control-relevant multisine excitation capturing integrating behavior;
- MoD vs ARX across prediction horizons; MoD reportedly more accurate;
- separate tuning for setpoint tracking / measured disturbance rejection / unmeasured disturbance rejection;
- pilot experimental validation.
CLASS=CLEAN_ROOM/REFERENCE unless code appears.

BLUECAD PATTERN=`ExcitationCampaign -> trajectory database -> query local operating neighborhood -> local dynamic model -> MPC`; candidate alternative when full mechanistic M1 is inaccurate/time-varying. Model-on-demand should retain training-data domain/provenance and never silently replace mechanistic model globally.

## 3 UAL EXTREMUM SEEKING 2026
PAPER=González-Hernández/Dewasme/Guzmán/Moreno/VandeWouwer, CEP170 (May2026)106835, DOI 10.1016/j.conengprac.2026.106835. Open access; ResearchGate indexed license CC BY-NC for its copy. Code repo not found.
EXPERIMENT=80m2 semi-industrial outdoor raceway, pH real-time optimization.
METHOD:
- classical modulation/demodulation ESC;
- dither deliberately outside dominant process bandwidth -> enough daylight excitation cycles despite slow dynamics/transport delay;
- washout HPF tuned for drift rejection + phase lead;
- explicit transport-delay demodulation/phase compensation;
- static data-driven solar-radiation feedforward cancels predictable photosynthesis disturbance;
- bounded ripple/fast convergence clear/cloudy;
- full implementation figure reportedly adds slew-limited integrator, guard-band saturation, anti-windup, daily reset.
CLASS=CLEAN_ROOM/REFERENCE.
BLUECAD_USE=model-free/self-optimizing control plugin candidate for uncertain/time-varying process; actuator safety/limits remain Jarvis/plant authority, not optimizer.

## 4 UAL/NTNU ECONOMIC MPC 2026
PAPER=Otálora/Skogestad/Guzmán/Berenguel, Computers & Chemical Engineering 212 (Sep2026)109714, available online 2026-05-25; DOI 10.1016/j.compchemeng.2026.109714; arXiv2512.15668. Publisher PDF says CC BY-NC; data on request. No source repo found.
METHOD=centralized EMPC with dynamic process model, anticipated disturbances/climate scenarios, economic objective; compares optimized vs typical industrial operation; reports economic improvements + stable dynamic operation.
CLASS=RESEARCH_ONLY/CLEAN_ROOM reference for equations; not software backend.
BLUECAD_USE=future EconomicObjective layer should be independent from controller/plant model; controller consumes model+forecast+economic metric and returns proposed actuation. Do not hard-wire economics into PBR physics.

## 5 INDUSTRIAL PBR BEHAVIOR-CLONING RL 2026
PAPER=Gil/delRioChanona/Guzmán/Berenguel, Engineering Applications of AI 164B (Jan2026)113326, DOI 10.1016/j.engappai.2025.113326; arXiv2509.06853; Zenodo17776806 contains paper PDF CC BY4, no code/weights/data package found in audit.
METHOD:
- pH RL controller for open industrial PBR;
- offline behavior cloning/training from trajectories generated by nominal PID -> avoids direct unsafe exploration on plant;
- deployed agent collects daytime data and is fine-tuned nightly -> adaptation to evolving process dynamics;
- 8-day real experiment;
- reported simulation IAE reductions vs PID/MPC/standard off-policy RL and control-effort reductions; exact claims belong to paper domain only.
CLASS=REFERENCE_NO_CODE.

BLUECAD/JARVIS SAFETY PATTERN:
`trusted_controller demonstrations -> offline policy -> simulation/oracle validation -> shadow mode -> authority-limited deployment -> logged data -> offline/nightly update -> re-validation -> promotion`.
Never permit online weight updates to bypass Jarvis model/policy promotion. A newly fine-tuned policy is a proposal/artifact version requiring validation/rollback, not silently canonical controller.

## 6 OPTIMAL-PSE CIRL REPO — CODE-FIRST
REPO=OptiMaL-PSE-Lab/CIRL; public; MIT license; research code for 2025 IECR `Control-Informed Reinforcement Learning for Chemical Processes`.
CONCEPT=embed PID/control knowledge into deep RL to improve sample efficiency/tracking/disturbance robustness.

CODE FINDINGS:
- root has research scripts/data/plots, not package/test architecture;
- `CIRL/cirl_policy.py`: `Net` is simple PyTorch MLP; constructor accepts `PID` argument but never uses it; also hardcodes `self.device=torch.device("cuda")` without using device in forward; `F.tanh` legacy-ish call;
- CIRL/RL distinction is orchestrated by training/environment, not encapsulated policy abstraction;
- `training_CIRL.py`: random search then ParticleSwarmOptimizer; global mutable `r_list/r_list_i/p_list`; repeated environment rollouts; pickle/state-dict outputs; no clear reproducibility seed inside main training code; research-script structure;
- repo tree/code search did not surface automated unit/integration test suite or CI equivalent.
LICENSE=DIRECT; MATURITY=RESEARCH_PROTOTYPE.
PIPPO_VERDICT=DO_NOT_ADOPT_WHOLESALE. Reuse/derive idea or small clean modules if later useful; better production foundation exists for process RL evaluation.

## 7 PC-GYM — STRONG DIRECT CANDIDATE
REPO=MaximilianB2/pc-gym; MIT; PyPI `pcgym`; version 0.1.8 current audited repo; development classifier Alpha but software engineering materially stronger than CIRL.
PAPER=PC-Gym: Benchmark environments for process control problems, Computers & Chemical Engineering 204 (Jan2026)109363.
CAPABILITIES:
- standardized Gym-style process-control environments;
- nonlinear process models;
- customizable disturbances;
- constraints;
- reward functions;
- RL policy evaluation;
- NMPC oracle/reference comparison;
- examples/training ecosystem.
CODE_QUALITY:
- package pyproject, Python>=3.11;
- dev tooling ruff/pytest/pytest-cov/xdist/nbmake/pyright/pre-commit/pip-audit/build/twine;
- pytest strict markers;
- coverage configured with branch=true and fail_under=45;
- code search confirms tests for model, environment, oracle, policy evaluation;
- GitHub CI and nightly workflows present.
DIRECT=YES (MIT).

PIPPO_VERDICT=ADOPT_CANDIDATE for future generic `ControlBenchmark/PolicyEvaluation` layer, subject to interface spike against Jarvis/BLUECAD canonical contracts. Do not duplicate generic RL/control benchmarking infrastructure without comparing against PC-Gym first.

TARGET INTEGRATION:
`BluecadPlantEnvAdapter` maps SemanticModel/Simulation backend -> PC-Gym-like observation/action/disturbance/constraint/reward environment.
`PolicyCandidate` may be PID/MPC/RL/ESC/other.
`EvaluationSuite` runs deterministic/scenario ensembles against common metrics + oracle.
Jarvis authority owns which candidate can operate physical plant.
Potentially contribute PBR benchmark environment upstream or maintain adapter rather than fork.

## 8 MULTI-FIDELITY BIOPROCESS BO 2025
PAPER=Martens/Neufang/Butté/vonStosch/delRioChanona/Helleckes, arXiv2508.10970 `Holistic Bioprocess Development Across Scales Using Multi-Fidelity Batch Bayesian Optimization`.
DATA_AVAILABILITY statement: all data+code openly available in accompanying GitHub repo, but exact repository URL/name not exposed by current indexed HTML/search and GitHub repo search by title/authors returned none. Therefore CODE_NOT_YET_AUDITED.
METHOD:
- GP multi-fidelity modeling across MTP/MBR/pilot scales;
- mixed categorical clone+continuous process variables;
- batch BO;
- acquisition variants GIBBON,qLogEI,qUCB;
- fidelity/experiment costs modeled explicitly;
- learns when to query cheap vs expensive scales;
- synthetic CHO benchmark.
Reported simulation examples: GIBBON strong when clone performance distribution diverse; qUCB/qLogEI can drastically lower cost in other distribution; key insight is strategic high-fidelity points earlier rather than only final scale.

BLUECAD VALUE=direct future `ExperimentFidelity` dimension: simulation/M0/bench micro-PBR/pilot BlueRev/full system each has cost, duration, confidence, scale-bias. Combine with Pyomo.DoE/model discrimination rather than force one algorithm to solve all experiment selection problems.
NEXT=find exact repository before candidate classification.

## 9 CONTROL STACK DECISION
BASELINE_EVALUATION=PC-Gym DIRECT candidate.
CONTROL_ALGORITHMS remain plugins/artifacts: PID/PI, MPC, EMPC, MoD-MPC, ESC, RL/CIRL.
TRAINING/ADAPTATION artifacts versioned + validated before promotion.
PLANT_SIDE_EFFECT boundary ALWAYS Jarvis authority/safety; controllers return proposed actuation only.
CONTROL_CONTEXT should include `{time,obs,refs,environment,forecast,state,uncertainty}`.
BENCHMARK should support `{constraints,disturbances,actuator dynamics/delays,objective/economic metric,oracle,scenario ensemble}`.

## 10 NEXT
P0 inspect PC-Gym environment/oracle/policy-evaluation contracts and map to BLUECAD ControlStep; audit dependencies/security/performance.
P0 locate exact Martens multi-fidelity BO GitHub repo.
P0 search UAL/ASU/UMONS author repos for MoD/ESC/EMPC code.
P0 search FIWARE implementation/deployment artifacts from UAL paper; compare existing FIWARE open-source components if Jarvis industrial protocol layer becomes priority.
P1 persist candidate register update for PC-Gym/CIRL/UAL benchmark if needed.
P2 PBR discovery now approaching diminishing returns; after above high-leverage control candidates, transition to mechanical/wave/fatigue deep audit while continuing targeted PBR source recovery opportunistically.
