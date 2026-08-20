MECHANICAL_FATIGUE_MATERIALS_DISCOVERY_DELTA3
DATE=2026-08-20
BRANCH=audit/hermes-agent-2026-08-20
AUTHORITY=AUDIT_ONLY
FORMAT=AI_DENSE

SCOPE=wave/spectral fatigue; marine design-code oracles; crack growth; cohesive/composite fatigue; corrosion-fatigue gap.

1 FLIFE — PROMOTE DIRECT STRONG
repo=ladisk/FLife
license=MIT DIRECT.
role=spectral/vibration fatigue from PSD; exact fit for stochastic wave-driven stress histories.
methods>{Narrowband,WirschingLight,OrtizChen,Alpha075,TovoBenasciutti,Dirlik,ZhaoBaker,Park,JunPark,JiaoMoan,SakaiOkamura,FuCebon,ModifiedFuCebon,Low,Low2014,GaoMoan,Lotsberg,HuangMoan,SingleMoment,Bands}; rainflow references; multiaxial equivalent-stress criteria.
scientific support=2023 review paper explicitly provides open-source side-by-side benchmark/reproducible notebook for >20 spectral methods; 2026 multiaxial review also tied to package.
CODE_FIRST:
- tests/test_basic.py hard-codes reference fatigue lives for Rainflow + spectral methods and checks PDFs integrate to 1; compares integrated-PDF life vs closed methods.
- tests/multiaxial_test.py hard-codes reference outputs for EVMS,max-normal,max-shear,critical-plane,multiaxial-rainflow,thermoelastic,LiWI,coin-LiWI,Nieslony,Lemaitre; optimizer methods use explicit rtol; plane-stress equivalence tested.
VERDICT=PIPPO_ADOPT_CANDIDATE.
ARCHITECTURE=wavespectra/structural transfer functions -> stress PSD -> FLife -> spectral damage/life. Use pyLife/rainflow time-domain as cross-check on selected synthesized histories.
LIMIT=validity assumptions of each spectral estimator (stationarity/Gaussianity/bandwidth/multiaxial criterion) must be explicit ModelValidity state; do not auto-use Dirlik universally.

2 PYLIFE / FATPACK / RAINFLOW
pyLife=Apache2 DIRECT generic engineering fatigue/lifetime; default time-domain/FKM/SN/rainflow-oriented backend.
fatpack=ISC DIRECT (license now confirmed); independent lightweight rainflow/endurance/Miner oracle; useful cross-check against pyLife.
iamlikeme/rainflow=MIT ASTM E1049 cycle-count implementation; optional third independent counter.
DECISION=do not write native rainflow/Miner.

3 ANYSTRUCTURE
repo=audunarn/ANYstructure
license=GPL-3-or-later => EXTERNAL oracle only.
value=naval/offshore structural screening with DNV-derived rule logic; code includes actual S-N tables B1...W3 and corresponding `c` variants with different intercept/knee, plus fatigue tests.
role=design-code regression/oracle, never embedded proprietary code.
IP/standards caution=code license does not grant rights to reproduce proprietary standard text/tables beyond what is legally distributable; BlueCAD must source design rules/licensed standards separately.

4 NASA COMPDAM_DGD / CF20
repo=nasa/CompDam_DGD
license=NASA Open Source Agreement 1.3, not ordinary permissive. Larger Work allowed, but Subject Software/modifications remain under OSA and binary redistribution triggers source-availability obligations. CLASS=BOUNDARY/REFERENCE; avoid direct embedding absent legal review.

PHYSICS VALUE=S for composite/cohesive fatigue.
Current v2.6.0 updates cohesive fatigue to Davila CF20 and extends fatigue to solid-element matrix cracks.
`for/cohesive.for` localizes key law:
- mixed-mode bilinear traction-separation + BK mode mixity
- endurance corrected by mode mixity + load ratio/Goodman
- normalized relative displacement jump
- CF20 incremental normalized energy-dissipation damage
- no-healing/cap R<=1
- adaptive cycles-per-increment.
Paper NASA/AIAA 2021 explicitly separates verification (traction-separation, stress-life) and validation (DCB + 3PB doubler); NASA TP 2020 evaluates CF20 vs alternatives and reports strong experimental correlation with minimal data.
TESTS=abaverify compares Abaqus vs Python extension state variables with tolerances; parametric stress-life class exists. Stress-life generator itself is not independent experimental validation; paper supplies physics validation.
KRATOS_SEARCH=no equivalent cohesive-fatigue/delamination law found in targeted searches.
PIPPO_DECISION=if BlueRev material/joint requires adhesive/composite delamination fatigue, do NOT add CompDam wholesale. Implement a small clean-room CF20-like ConstitutiveLaw in Kratos from public NASA technical equations, then regression against NASA DCB/MMB/3PB benchmark data; maintain independent derivation/equation provenance.
CAVEAT=CF20 validated for composite interfaces/delamination; do not assume arbitrary structural adhesive/polymer validity without calibration.

5 CRACKPY
repo=dlr-wf/crackpy
license=MIT but authors explicitly state research only/prototype/not production or specification.
role=experimental fracture-mechanics post-processing/DIC: crack tip/path, J/interaction/conjugate integrals, Williams/CJP parameters. Use experiment/calibration pipeline only, not design acceptance.

6 EASIGROW
repo=needsglasses/easigrow
license=MIT DIRECT; Rust CLI+library; Commonwealth of Australia provenance.
capability=crack growth simulation; beta/geometry models; material da/dN laws; coefficient optimization; variable-amplitude sequences.
validation debt=repo tests directory mostly manual comparison tables prediction-vs-rainflow/fractography; several prediction/experiment discrepancies substantial; not FLife-level automated regression.
role=experimental/direct crack-growth model-fitting engine behind explicit material validity domain; cross-validate with BlueRev material data and alternate crack-growth tools before design use.
DO_NOT call universal residual-life oracle.

7 CORROSION FATIGUE
STATUS=GAP for mature permissive production-ready coupled seawater-corrosion fatigue solver.
Literature confirms offshore corrosion can materially reduce fatigue life and dependence on environment/frequency/pitting/crack growth matters. Recent corroded-chain frameworks explicitly integrate pit/weld corrosion, cyclic plasticity and crack propagation; not found as reusable permissive production package.
ARCHITECTURE REQUIREMENT=EnvironmentState={medium,seawater chemistry,T,oxygen,flow,protection/coating,exposure_time,corrosion_rate/pit distribution,frequency_domain}; FatigueLaw validity domain binds to environment.
RULE=dry-air S-N curve cannot silently stand in for seawater/corrosive service.

8 UPDATED FATIGUE STACK
FAST_SPECTRAL=stress_PSD -> FLife(method selected by PSD diagnostics/validity) -> damage/life.
TIME_DOMAIN=stress_history -> pyLife; fatpack/rainflow independent count check.
CRACK_GROWTH=detected/assumed crack -> easigrow candidate + calibrated da/dN model; CrackPy experimental identification support.
COMPOSITE/INTERFACE=Kratos host + future clean-room CF20-like law if justified; NASA CompDam oracle/reference.
CODE_ORACLE=ANYstructure external DNV-like screening.
CORROSION=explicit modifier/model family, currently GAP not fake multiplier.

9 BLUECAD NATIVE CONTRACTS
FatigueAssessmentInput={stress representation(time/PSD),material_id,joint/detail_category,mean_stress/load_ratio,environment,temperature,surface/size,weld/bolt/adhesive state,uncertainty,validity_domain}.
FatigueAssessmentOutput={method,damage/life,confidence,dominant bands/cycles,assumptions,standard/model provenance,validation evidence}.
ModelSelector chooses spectral vs time-domain vs crack-growth based on input regime and validity; never one universal fatigue solver.

10 NEXT
P0 search corrosion-fatigue open datasets/models/code for welded steel/marine polymers/composites; prefer DNV/NREL/OWI/academic benchmark data.
P0 audit FLife dependency/license chain + CI/release health before formal integration spec.
P1 obtain public CF20 benchmark datasets/geometry/material params from NASA TP/CompDam examples and define clean-room test vectors.
P1 search Kratos ConstitutiveLawsApplication host patterns for custom interface/cohesive material law even if no fatigue law exists.
P1 determine actual BlueRev joint/material choices; without them no final fatigue model can be selected.
