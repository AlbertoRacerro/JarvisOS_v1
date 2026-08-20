MECHANICAL_WAVE_FEM_DISCOVERY_DELTA2
DATE=2026-08-20
BRANCH=audit/hermes-agent-2026-08-20
AUTHORITY=AUDIT_ONLY
FORMAT=AI_DENSE

SCOPE=global marine dynamics alternatives; HydroChrono/Chrono; reduced-order rods; solver comparison; joint-specific fatigue.

1 STRUCTURAL SOLVER COMPARISON
KRATOS=DIRECT/permissive strong batteries-included structural FEM; current preferred detailed/local structural solver.
MFEM=BSD3 DIRECT; HPC finite-element library. Tribol=MIT DIRECT contact library with search/detection/enforcement; requires MFEM+Axom+MPI, optional GPU stack. MFEM+Tribol good specialist/custom HPC/contact candidate, higher assembly/integration burden than Kratos/Chrono for BlueRev global mechanics.
OPENSEES=NOT_DIRECT. COPYRIGHT permits noncommercial education/research, other entities internal use; incorporation into commercially distributed product requires UC Berkeley permission. Class=RESEARCH_ONLY/COMMERCIAL_LICENSE_REQUIRED for embedded BlueCAD.
CALCULIX=GPL2 core => EXTERNAL; permissive examples do not change solver license.
FENICSX=general PDE platform; structural high-level ecosystem fragmented/experimental; no current advantage over Kratos/Chrono.
SFEPY=BSD general PDE/FE; lower priority for BlueRev structure.

2 PROJECT CHRONO — PROMOTED S DIRECT CANDIDATE
repo=projectchrono/chrono
license=BSD3 DIRECT.
capability={rigid+flexible multibody, FEA beams/cables/shells/solids, contact, modal/dynamics, Python, FSI-SPH}.
code-first tests found for ANCF cable, ANCF beam formulations, shell/hexa and modal eigensolver.

CRITICAL EXACT BLUEREV-ADJACENT DEMO:
`src/demos/fsi/sph/demo_FSI-SPH_WaveTank.cpp` constructs free-surface wave tank + wavemaker + SPH fluid and can directly add ANCF flexible cable or ANCF flexible plate to FSI system. Cable has diameter/E/density/Rayleigh damping; plate uses ANCF shell + contact surface. Thus permissive stack already implements `wave/free-surface -> flexible structure` coupling, not merely abstract FSI claims.

ROLE:
- global flexible multibody/member dynamics candidate;
- high-fidelity selected SPH-FSI cases/oracle/calibration/surrogate generation;
- not default whole-life SPH because computational cost likely high.
VALIDATION_NOTE=FEA unit coverage exists; FSI unit search surfaced mainly setter-guard, so BlueCAD must add scientific FSI validation/regression. External literature validates Chrono-coupled flexible beam/vegetation and hydroelastic cases experimentally/analytically.
PIPPO=SPIKE_BEFORE_BUILDING_GLOBAL_FLEXIBLE_SOLVER.

3 HYDROCHRONO / SEA-STACK
repo=Project-SEA-Stack/HydroChrono (GitHub redirects legacy NREL/HydroChrono)
license=MIT DIRECT code.
STATUS=ARCHIVED_BY_OWNER_2026-05-19; latest release v0.7.0 2026-03-02. No public successor located yet. NLR current pages/newsletter still describe HydroChrono as SEA-Stack backbone, creating maintenance/provenance ambiguity.
CLASS=MIT_FORKABLE_ARCHITECTURE_S; ACTIVE_DEPENDENCY_BLOCKED_BY_MAINTENANCE_PROVENANCE.

ARCHITECTURE:
- input BEMIO HDF5 hydrodynamic coeffs (e.g. Capytaine outputs)
- Cummins time-domain formulation
- Project Chrono multibody system
- first-order hydro
- MoorDyn coupling
- YAML model/simulation/hydro separation
- HDF5 output
- regression cases sphere, OSWEC, RM3, F3OF
- distinct unit/regression/verification trees.

CODE-FIRST KEY FINDING:
`src/hydro/radiation/` includes `radiation_rirf_convolution`, `radiation_rirf_processing`, `radiation_ss_fitter`, `radiation_ss_model`. Therefore RIRF convolution and radiation state-space machinery already exists under MIT. Rewriting Cummins/state-space from zero is unjustified before fork/spike assessment.

PIPPO DECISION:
- search successor/archival reason remains P0;
- if no successor, evaluate selective MIT fork/extraction of radiation+BEMIO/time-domain modules;
- do not blindly depend on archived full app.

IMPORTANT PHYSICS LIMIT=potential-flow BEM/Cummins normally rigid-body hydrodynamics. Continuous flexible hydroelastic member requires explicit approximation: articulated rigid modules + joints, externally distributed loads/Morison, or high-fidelity FSI/hydroelastic method. Assumption must be provenance-tagged.

4 EXUDYN
repo=jgerstmayr/EXUDYN
license=custom permissive BSD-like; bundled third-party notices include MPL2 Eigen etc.
VALUE=flexible multibody/reduced global candidate; general contact, ANCF cable/contact/friction examples, Python+C++ core, large test/example corpus.
CRITICAL_MATURITY_FINDING=`geometricallyExactBeam3Dtest.py` header explicitly says UNDER DEVELOPMENT and final testError/testResult assertions are commented. Therefore exact 3D geometrically-exact-beam path not currently a trusted regression anchor.
VERDICT=DIRECT candidate but behind Chrono for 3D marine/global BlueRev today.

5 PYELASTICA
repo=GazzolaLab/PyElastica
license=MIT DIRECT.
role=specialized Cosserat-rod/slender-structure reduced model; promising for actual transparent PBR tubes because pose/orientation/curvature along arclength can feed optics.
engineering signals=tests for rod initialization, joints, external forcing; recent v1 ecosystem.
NO_NATIVE_MARINE_HYDRO found in audit; feed distributed hydrodynamic loads externally.
TARGET USE=`TubeRodModel` reduced fidelity: supports/wave-motion -> centerline/directors/curvature/stress proxies -> optical theta_tube(s,t); not replacement for high-fidelity hydro/3D joint FEM.

6 EMERGING MULTIFIDELITY GLOBAL/LOCAL STACK
M0/fast mechanics: wavespectra -> reduced hydrodynamic/Morison load model -> PyElastica OR Chrono beams/MBD -> pose/member-force histories.
M1/global offshore: BEM coefficients(pyHAMS/Nemoh) -> HydroChrono-derived Cummins/state-space OR equivalent maintained path -> Chrono multibody/flexible model -> MoorDyn.
M2/high fidelity selected: Chrono FSI-SPH wave tank/flexible structure OR external validated CFD-FSI.
LOCAL joints: Kratos detailed 3D nonlinear contact/material submodel.
FATIGUE: pyLife generic + joint/material-specific law; CrackPy experimental fracture-analysis support.
OPTICS CROSS-COUPLING=global mechanics emits `tube_pose(s,t), director(s,t), curvature(s,t)` for PBR optics/light-history.

7 BOLTED JOINTS — OPENBOLTRF REFERENCE
repo=jhjorg/OpenBoltRF
license=GPL3 EXTERNAL/reference.
workflow=parametric geometry/imperfections -> 3D Code_Aster nonlinear FE -> preload -> bolt/nut constraint state -> Coulomb flange-face contact(mu=0.2) -> external pressure/moment -> stress/strain extraction -> EN1993 fatigue/Miner.
IMPORTANT CONTRACT IDEA=`JointSubmodel` explicitly separates assembly/preload state from service-load state. This is essential for bolted/clamped BlueRev joints.
fatigue.py uses EN1993 detail categories/size correction/S-N slopes/Miner; GPL reference only.

8 COMPOSITE BOLTED JOINTS — BJSFM
repo=BenjaminETaylor/bjsfm
license=MIT DIRECT; PyPI Beta 0.5.2.
method=pure-Python port of classic Bolted Joint Stress Field Model; Lekhnitskii anisotropic elasticity; loaded/unloaded hole; bearing+bypass; DeJong correction; max strain analysis.
engineering evidence=repo has unit+integration tests and Fortran comparison assets.
role=fast analytical composite bolted-hole stress field/screening before 3D FEM; NOT a fatigue/damage solver.
PIPPO=ADOPT_CANDIDATE only if BlueRev uses composite bolted panels/joints.

9 FATIGUE / CRACK / CORROSION
pyLife=Apache2 DIRECT generic fatigue/lifetime backend remains default.
py_fatigue=GPL3 EXTERNAL/oracle; includes DNV-RP-C203-related corrections.
CrackPy(DLR)=MIT code but authors explicitly research/prototype/no production/specification; computes crack tip/path from DIC, J/interaction/conjugate integrals, Williams/CJP, fracture parameters. Role=experiment/data-reduction/validation tool, NOT certification criterion.
PyFAT=MIT experimental polymer/composite test-data analysis; not structural fatigue solver.
PRISMS-Fatigue=LGPL CPFEM research, likely overkill.
CORROSION_FATIGUE: literature confirms offshore corrosion can dominate and modern approaches require environment/frequency/pitting/crack-growth effects. No mature permissive production corrosion-fatigue solver found yet => GAP. Treat seawater/corrosion state as explicit modifier/uncertainty; do not silently use dry-air S-N curve.

10 MATERIAL/JOINING STATUS
WELDED_STEEL: generic S-N/hotspot feasible; corrosion/environment model still gap; standards/IP boundaries required.
BOLTED_METAL: OpenBoltRF gives strong reference workflow; need permissive fast preload/load-distribution model if desired.
BOLTED_COMPOSITE: bjsfm DIRECT fast stress-screening + local 3D progressive damage as higher fidelity.
ADHESIVE: reusable validated fatigue backend GAP.
POLYMER: reusable validated structural fatigue backend GAP; PyFAT only data analysis.
COMPOSITE_FATIGUE: many research progressive-damage models; no single permissive production-ready backend found yet.

11 PIPPO_OS CURRENT MECHANICAL VERDICT
DO_NOT_BUILD={generic multibody dynamics,generic beam/cable FEA,generic 3D structural FEM,generic contact engine,generic rainflow/SN machinery,Cummins/RIRF/state-space from scratch}.
OWN_BLUECAD={MarineMechanicsIR,fidelity selection,rigid-vs-flexible approximation provenance,hydro/structure adapter contracts,global-local mapping,load-history evidence,joint assembly state,material/environment validity domains,solver cross-validation,mechanics->optics coupling}.

12 NEXT
P0 locate HydroChrono/SEA-Stack successor or archival rationale.
P0 audit Chrono FSI validation + determine practical path for distributed wave loads on flexible tube network.
P0 define fast `TubeRodModel` spike comparing PyElastica vs Chrono ANCF on canonical beam/rod cases.
P0 search welded/corrosion fatigue data+permissive code and adhesive/polymer fatigue.
P1 define `JointSubmodel` schema={joint_type,materials,preload/contact/friction,assembly_state,local_geometry,load_mapping,failure_modes,environment,life_model,validation_domain}.
