# DISCOVERY STATE KERNEL V9 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;SUPERSEDES_FOR_REHYDRATION=V8;BRANCH=audit/hermes-agent-2026-08-20

RULES=SUNK_COST_ZERO|PIPPO_OS_TEST|REPLACE_NOT_LAYER|CODE_FIRST|AUTHORITY_SEPARATION|BACKEND_OVER_REWRITE|MULTIFIDELITY|ASSUMPTIONS_ARE_STATE|SERENDIPITY|AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonstandard obligations;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea/no-code;RESEARCH_ONLY NC/commercial-license;GAP none}.

AI: Hermes wins generic agent runtime; Jarvis keeps authority/policy/egress/budget/confirmation/credentials/canonical engineering state/proposal-promotion/provenance. External runtime/solver never owns accepted truth.
BLUECAD: SemanticModelIR + adapters + evidence/validation/model-selection/coupling/UX native; mature numerics external.

PBR: M0 X+light;M1 carbonate/DO/gas/T;M2 distributed1D;M3 3D optics/CFD/light-history/waves/fouling. Discovery broad phase mostly saturated; retain In@lgae/MGM/UAL/Pruvost/N.gaditana/seawater/fouling findings in detailed audits. PC-Gym MIT adopt candidate control benchmark; UAL2026 benchmark S oracle p-code/no explicit software license.

MECHANICS GLOBAL:
- ProjectChrono BSD3 S DIRECT: flexible MBD+FEA+contact+Python+FSI-SPH; actual wave-tank SPH + ANCF flexible cable/plate demo. Candidate global flexible dynamics + selected FSI.
- HydroChrono MIT S architecture but archived 2026-05-19; maintenance provenance unresolved. Contains BEMIO->Cummins,RIRF convolution/processing,state-space fit/model,Chrono,MoorDyn,YAML/HDF5,unit/regression/verification(sphere/OSWEC/RM3/F3OF). Fork/extract before rewriting radiation layer.
- pyHAMS Apache2 strong BEM candidate but numerical added-mass/damping/excitation asserts commented in cylinder regression -> BlueCAD validation debt.
- Nemohv2 Apache candidate;Capytaine GPL external/libDelhommeau Apache subcomponent.
- wavespectra MIT sea-state;OpenFAST/WEC-Sim oracles;MoorDynv2/MoorPy BSD.

STRUCTURAL:
- Kratos permissive DIRECT detailed/local FEM: beams/cables/shell/solid/contact/dynamics/sensitivity/tests.
- CoSimIO permissive detached C++11 C/Python MPI coupling; try before custom bus.
- PyElastica MIT TubeRod reduced model candidate; emits centerline/directors/curvature/pose to optics; loads external.
- Exudyn permissive but exact3Dbeam test under-development/asserts commented; behind Chrono.
- MFEM BSD3+Tribol MIT specialist HPC/contact; lower-level.
- OpenSees commercial-distribution permission needed;CalculiX GPL external;FEniCSx/SfePy lower priority.

TARGET MECH FIDELITY:
FAST=wavespectra->reduced hydro/Morison->PyElastica/Chrono beams->pose/load histories.
GLOBAL=BEM(pyHAMS/Nemoh)->HydroChrono-derived maintained Cummins/state-space->Chrono flexible/MBD->MoorDyn.
HIGH=Chrono FSI-SPH/external CFD-FSI selected cases.
LOCAL=Kratos nonlinear 3D joint.
CROSS=mechanics emits tube_pose(s,t),director(s,t),curvature(s,t)->optics.

JOINTS:
- OpenBoltRF GPL external reference: preload -> lock assembly -> Coulomb contact -> service load -> EN1993/Miner. Native JointSubmodel must distinguish assembly/preload vs service state.
- bjsfm MIT DIRECT fast anisotropic composite bolted-hole bearing+bypass stress; tests+Fortran comparisons; only if composite bolted joints.

FATIGUE V9:
- pyLife Apache2 DIRECT general/time-domain default.
- FLife MIT DIRECT STRONG for wave/stochastic spectral fatigue. Tests hard-code numerical lives for Rainflow+~20 spectral estimators, PDF normalization, multiaxial reference outputs/tolerances. Adopt candidate. Pipeline=stressPSD->method validity diagnostics->FLife; synthesize selected histories and cross-check pyLife/rainflow.
- fatpack ISC DIRECT independent lightweight rainflow/endurance/Miner oracle. iamlikeme/rainflow MIT ASTM E1049 optional third counter.
- ANYstructure GPL3 EXTERNAL DNV-like naval/offshore oracle; actual B1..W3 + corrosive `c` S-N tables and fatigue tests. Do not copy standard text/tables absent rights.
- CrackPy MIT but research/prototype-only per authors; experimental DIC/fracture postprocessing not design criterion.
- easigrow MIT Rust crack-growth/model-fit candidate; tests mostly manual experimental comparison tables with nontrivial discrepancies -> validity-domain only, not universal oracle.

COMPOSITE/COHESIVE FATIGUE:
NASA CompDam_DGD uses NASA OSA1.3 => BOUNDARY/REFERENCE not ordinary DIRECT. Current code localizes Davila CF20 cohesive fatigue: mixed-mode BK traction separation, endurance+R-ratio, normalized relative jump, incremental normalized energy-dissipation damage, adaptive cycles/increment. NASA 2020/2021 papers provide verification+DCB/3PB validation. Target if needed=clean-room CF20-like Kratos ConstitutiveLaw from public equations + NASA regression data, NOT wholesale CompDam dependency. Do not generalize composite delamination calibration to arbitrary adhesive.

CORROSION FATIGUE=GAP for mature permissive production solver. Environment/frequency/pitting/crack-growth explicitly matter. Fatigue law validity must bind EnvironmentState; dry-air S-N cannot silently stand in for seawater.
ADHESIVE_FATIGUE=still GAP generic validated package; CF20 is possible physics reference only.
POLYMER_STRUCTURAL_FATIGUE=GAP.

PIPPO MECH DO_NOT_BUILD={generic MBD,beam/cable FEA,3D FEM,contact,rainflow/Miner,spectral estimators,Cummins/RIRF/state-space}. BLUECAD_OWN={MarineMechanicsIR,fidelity selection,hydro-flex approximation provenance,global-local map,joint assembly state,environment/material validity,solver cross-validation,mechanics-optics coupling}.

NEXT=P0 corrosion-fatigue datasets/models/code welded steel+marine polymers/composites;P0 HydroChrono successor;P0 Chrono distributed flexible wave-load practical model;P0 actual BlueRev joint/material selection eventually required;P1 FLife integration/license dependency audit;P1 CF20 benchmark test vectors;P1 JointSubmodel schema.

DETAIL_MAP=MECHANICAL_WAVE_FEM_DISCOVERY_DELTA1_2026-08-20.md;MECHANICAL_WAVE_FEM_DISCOVERY_DELTA2_2026-08-20.md;MECHANICAL_FATIGUE_MATERIALS_DISCOVERY_DELTA3_2026-08-20.md;BLUEREV_*;MODEL_*;SEAWATER_*;HERMES_*;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md. Read V9 first; newer/detailed audit wins; merged governance remains authority.
