# DISCOVERY STATE KERNEL V8 — 2026-08-20
PURPOSE=AI_REHYDRATION;FORMAT=TOKEN_DENSE;AUTHORITY=AUDIT_ONLY;IMPLEMENTATION_AUTHORIZED=NO;SUPERSEDES_FOR_REHYDRATION=V7;BRANCH=audit/hermes-agent-2026-08-20

## RULES
SUNK_COST_ZERO;PIPPO_OS_TEST;REPLACE_NOT_LAYER;CODE_FIRST;AUTHORITY_SEPARATION;BACKEND_OVER_REWRITE;MULTIFIDELITY;ASSUMPTIONS_ARE_STATE;SERENDIPITY;AUDIT_BRANCH_ONLY.
LICENSE={DIRECT permissive;BOUNDARY adapter/LGPL/nonmodified;EXTERNAL GPL/AGPL/process;CLEAN_ROOM equations/idea/no-code;RESEARCH_ONLY NC/noncommercial;GAP none}.

## AI/JARVIS
AGENT_RUNTIME=HERMES_WINS;AUTHORITY=JARVIS_WINS;TARGET=HYBRID_DEEP_REPLACEMENT. Hermes-derived generic runtime/tool discovery/subagents; Jarvis keeps policy/egress/budget/confirmation/credentials/canonical engineering state/proposal-promotion/provenance. External runtimes/solvers never own accepted truth.

## BLUECAD NUMERICAL
SemanticModelIR->{nativeM0|PyBaMM/CasADi|Modelica/PyMoCa|FMU/FMPy|specialist|external}; adapters hide numerics; Jarvis owns semantic meaning/provenance/validation. Do not rewrite mature kernels.

## BLUEREV PBR
M0={X,effective attenuation,photoinhibition,decay};M1={X,DIC/pH,DO,CO2/O2 gas transfer,T};M2={distributed1D tube+mixed degasser};M3={3D optics/local CFD/Lagrangian histories/wave pose/fouling}.
PBR discovery now targeted only. Key refs: In@lgae/MGM architectures; UAL distributed/lumped+CFD light-history; Pruvost MCRT oracle with direct-angle bug; pvlib/Mitsuba/miepython; N.gaditana Palermo/Pfaffinger/Nikolaou/Bernardi; seawater TEOS/CO2SYS/Reali; fouling code GAP; ChEDL hydraulics.
Control: PC-Gym MIT ADOPT_CANDIDATE generic ControlBenchmark; UAL 2026 benchmark S oracle but p-code/no explicit software license. Pyomo.DoE basis; SmartBioTech experiment automation.

## MECHANICS FRONT-RUNNERS — V8
### marine/global
wavespectra MIT DIRECT sea-state input.
Project Chrono=BSD3 DIRECT S candidate. Flexible MBD+FEA+contact+Python+FSI-SPH; code contains actual wave-tank demo coupled to ANCF flexible cable/plate. Use global flexible dynamics and selected high-fidelity FSI; SPH not default whole-life due cost. FEA tests strong; FSI scientific regression needs BlueCAD augmentation.
HydroChrono=MIT code, S architecture BUT repo archived 2026-05-19; no successor yet located while current NLR pages still call it SEA-Stack backbone. Dependency status=BLOCKED_BY_MAINTENANCE_PROVENANCE. Code has BEMIO->Cummins, RIRF processing/convolution, radiation state-space fitter/model, Chrono MBD, MoorDyn, YAML/HDF5, unit/regression/verification with sphere/OSWEC/RM3/F3OF. If no successor, fork/extract spike before rewriting time-domain radiation.
pyHAMS=Apache2 DIRECT BEM candidate, packaging/CI strong but cylinder scientific asserts for added-mass/damping/excitation commented => validation debt.
Nemoh v2 Apache2 candidate; Capytaine full GPL EXTERNAL, libDelhommeau Apache subcomponent candidate.
OpenFAST/HydroDyn Apache2 oracle/load candidate; floating rigid6DOF limitation for full flexible BlueRev. WEC-Sim Apache2; MoorDynv2/MoorPy BSD3.

### structural/global-local
Kratos core+StructuralMechanics=permissive DIRECT; strong detailed FEM/local-joint candidate; corotational beams,cable/truss,shell/solid,contact,dynamics,eigen/harmonic,sensitivity/tests.
Kratos CoSimulation+CoSimIO permissive DIRECT; standalone C++11 C/Python MPI detached coupling bus; try before custom numeric coupling.
PyElastica MIT DIRECT specialized reduced Cosserat-rod candidate for actual PBR tubes; joints/external-force tests. Role=fast TubeRodModel emitting centerline/directors/curvature/pose to optics; no native marine hydro found.
Exudyn permissive flexible MBD candidate but GeometricallyExactBeam3D test explicitly UNDER DEVELOPMENT with final regression assertions commented; behind Chrono today.
MFEM BSD3 + Tribol MIT strong HPC/contact specialist but lower-level/heavier assembly than Kratos/Chrono.
OpenSees NOT_DIRECT: commercial distribution requires UC Berkeley permission; research oracle only. CalculiX GPL2 EXTERNAL. FEniCSx/SfePy lower priority for this use.

### current target stack
FAST_M0=wavespectra -> reduced hydro/Morison -> PyElastica or Chrono beams -> tube_pose/member_load histories.
GLOBAL_M1=BEM(pyHAMS/Nemoh) -> HydroChrono-derived maintained Cummins/state-space path -> Chrono flexible/MBD -> MoorDyn.
HIGH_M2=Chrono FSI-SPH or external CFD-FSI selected cases.
LOCAL=Kratos nonlinear 3D joint submodel.
FATIGUE=pyLife + material/joint-specific law.
CROSS_DOMAIN=mechanics emits tube_pose(s,t), director(s,t), curvature(s,t) -> optics/growth.

## JOINTS/FATIGUE
OpenBoltRF GPL3 EXTERNAL reference: explicit preload step -> bolt/nut lock -> Coulomb flange contact -> nonlinear external load -> stress -> EN1993/Miner. Key native contract: JointSubmodel must distinguish assembly/preload state from service-load state.
bjsfm MIT DIRECT Beta; unit+integration+Fortran comparison; analytical anisotropic composite bolted-hole bearing+bypass/max-strain. Candidate only if composite bolted joints.
pyLife Apache2 DIRECT generic fatigue default.
py_fatigue GPL EXTERNAL DNV oracle.
CrackPy DLR MIT but authors prohibit production/spec use by guidance/prototype status; experiment/fracture-analysis only (DIC crack tip, J/interaction/Williams/CJP).
CORROSION_FATIGUE=GAP for mature permissive production solver. Marine fatigue environment/frequency/pitting/crack growth must be explicit; dry-air S-N cannot silently stand in.
ADHESIVE_FATIGUE=GAP; POLYMER_STRUCTURAL_FATIGUE=GAP; COMPOSITE_PROGRESSIVE_FATIGUE=no single promoted permissive backend.

## PIPPO MECHANICAL DECISION
DO_NOT_BUILD={generic MBD,beam/cable FEA,3D structural FEM,contact engine,rainflow/SN,Cummins/RIRF/state-space from zero}.
BLUECAD_OWN={MarineMechanicsIR,fidelity policy,rigid-vs-flex approximation provenance,adapter contracts,global-local mapping,load-history evidence,joint assembly/preload state,material/environment validity,solver cross-validation,mechanics-optics coupling}.

## NEXT
P0 HydroChrono/SEA-Stack successor/archive reason.
P0 Chrono distributed wave-load/flexible-network practical model + FSI validation.
P0 PyElastica-vs-Chrono TubeRod canonical spike design.
P0 welded/corrosion fatigue permissive code/data + adhesive/polymer search.
P1 JointSubmodel schema and global->local load mapping.
P1 Nemoh/libDelhommeau second BEM validation backend.

## DETAIL MAP
Read V8 first. Detailed evidence: MECHANICAL_WAVE_FEM_DISCOVERY_DELTA1_2026-08-20.md;MECHANICAL_WAVE_FEM_DISCOVERY_DELTA2_2026-08-20.md;BLUEREV_* audits;MODEL_* audits;SEAWATER_AND_NANNOCHLOROPSIS_FOUNDATIONS;HERMES_AGENT_CODE_FIRST_AUDIT;../IDEA_INTAKE_AND_CANDIDATE_INTEGRATIONS.md. Newer/detailed audit wins; merged governance authority remains separate.
